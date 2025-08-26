import json
import os
import time
from datetime import datetime, timezone
from random import randint
import polars as pl
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options as Chrome_Options
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as Firefox_Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
import argparse
import getpass
import sys
import time
import tracemalloc


def get_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(":", "-")


class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_path = self._get_config_path(config_file)
        self.config = self._load()

    def _get_config_path(self, filename):
        try:
            base_path = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            base_path = os.getcwd()
        return os.path.join(base_path, filename)

    def _load(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                return json.load(f)
        else:
            default_config = {
                "User": {"auto_login": False, "email": "", "password": ""},
                "Scraping": {
                    "detail_level": 2,
                    "retries": 3,
                    "timeout_seconds": 30,
                    "delay_seconds": [1, 4],
                },
            }
            self.save(default_config)
            return default_config

    def save(self, config_data=None):
        if config_data:
            self.config = config_data
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)

    def get(self, section, key, default=None):
        return self.config.get(section, {}).get(key, default)

    def set(self, section, key, value):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save()


class BrowserManager:
    def __init__(self, browser_choice="firefox"):
        if browser_choice not in ["firefox", "chrome"]:
            raise ValueError("Unsupported browser choice.")
        self.browser_choice = browser_choice
        self.driver = None

    def __enter__(self):
        print(f"\nInitializing {self.browser_choice.title()} session...")
        if self.browser_choice == "firefox":
            options = Firefox_Options()
            options.add_argument("--headless")
            options.set_preference(
                "general.useragent.override",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
            )
            self.driver = webdriver.Firefox(options=options)
        elif self.browser_choice == "chrome":
            options = Chrome_Options()
            options.add_argument("--headless")
            options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
            )
            options.add_experimental_option("excludeSwitches", ["enable-logging"])
            self.driver = webdriver.Chrome(options=options)
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            print("\nCleaning up resources...")
            self.driver.quit()
            print("Browser session terminated.")


class GlintsScraper:
    BASE_URL = "https://glints.com"

    def __init__(self, driver, config_manager):
        self.driver = driver
        self.max_retries = config_manager.get("Scraping", "retries", 3)
        self.timeout = config_manager.get("Scraping", "timeout_seconds", 30)
        delay_range = config_manager.get("Scraping", "delay_seconds", [1, 4])
        self.min_delay, self.max_delay = delay_range
        self.wait = WebDriverWait(self.driver, self.timeout)

    def login(self, username, password):
        print("\nAttempting to log in to Glints...")
        try:
            self.driver.get(f"{self.BASE_URL}/id/login")
            self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "a.LinkStyle__StyledLink-sc-usx229-0:nth-child(3)",
                    )
                )
            ).click()
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#login-form-email"))
            ).send_keys(username)
            self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#login-form-password")
                )
            ).send_keys(password)
            self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".ButtonStyle__SolidShadowBtn-sc-jyb3o2-3")
                )
            ).click()
            self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".UserMenuComponentssc__NameHolder-sc-ovl5x6-4")
                )
            )
            print("Login successful!")
            return True
        except TimeoutException:
            print("\nLogin failed. Check credentials or network connection.")
            return False
        except Exception as e:
            print(f"\nAn error occurred during login: {e}")
            return False

    def _get_page_soup(self, url):
        time.sleep(randint(self.min_delay, self.max_delay))
        self.driver.get(url)
        self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.JobCardsc__JobcardContainer-sc-hmqj50-0")
            )
        )
        return BeautifulSoup(self.driver.page_source, "lxml")

    def collect_job_links(self, job_title, detail_level):
        page_num = 1
        with tqdm(
            desc=f"Collecting '{job_title}' listings", colour="green", leave=False
        ) as pbar:
            while True:
                url = f"{self.BASE_URL}/id/opportunities/jobs/explore?keyword={job_title}&country=ID&locationName=All+Cities%2FProvinces&lowestLocationLevel=1&page={page_num}"
               
                try:
                    soup = self._get_page_soup(url)
                    cards = soup.find_all(
                        "div",
                        class_="CompactOpportunityCardsc__CompactJobCard-sc-dkg8my-4",
                    )
                    if not cards:
                        pbar.set_description(f"No more jobs found for '{job_title}'")
                        break

                    found_on_page = 0
                    for card in cards:
                        job_link_element = card.find(
                            "a",
                            class_="CompactOpportunityCardsc__JobCardTitleNoStyleAnchor-sc-dkg8my-12",
                        )
                        if job_link_element and job_link_element.has_attr("href"):
                            found_on_page += 1
                            if detail_level == 1:
                                yield self._extract_basic_info(card)
                            else:
                                yield job_link_element["href"]

                    if found_on_page == 0:
                        pbar.set_description(f"Reached end for '{job_title}'")
                        break

                    page_num += 1
                    pbar.update(1)
                except TimeoutException:
                    print(f"\nTimeout on page {page_num}. Stopping collection.")
                    break

    def extract_job_details(self, job_url, detail_level):
        full_url = self.BASE_URL + job_url
        for attempt in range(self.max_retries):
            try:
                time.sleep(randint(self.min_delay, self.max_delay))
                self.driver.get(full_url)
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
                soup = BeautifulSoup(self.driver.page_source, "lxml")
                return self._parse_job_details(soup, full_url, detail_level)
            except TimeoutException:
                print(
                    f"Timeout on {full_url} (Attempt {attempt + 1}/{self.max_retries})"
                )
            except Exception as e:
                print(
                    f"Error on {full_url}: {e} (Attempt {attempt + 1}/{self.max_retries})"
                )
        print(f"Failed to retrieve {full_url} after {self.max_retries} attempts.")
        return None

    def _extract_text(self, soup, selector, default="No Data"):
        element = soup.select_one(selector)
        return element.get_text(strip=True) if element else default

    def _extract_basic_info(self, card_soup):
        job_link = card_soup.find(
            "a",
            class_="CompactOpportunityCardsc__JobCardTitleNoStyleAnchor-sc-dkg8my-12",
        )
        return {
            "title": job_link.get_text(strip=True) if job_link else "No Title",
            "company": self._extract_text(
                card_soup, ".CompactOpportunityCardsc__CompanyLink-sc-dkg8my-14"
            ),
            "salary": self._extract_text(
                card_soup, ".CompactOpportunityCardsc__SalaryWrapper-sc-dkg8my-32"
            ),
            "location": self._extract_text(
                card_soup, ".CardJobLocation__LocationWrapper-sc-v7ofa9-0"
            ),
            "updated": self._extract_text(
                card_soup, ".CompactOpportunityCardsc__UpdatedAtMessage-sc-dkg8my-26"
            ),
            "url": self.BASE_URL + (job_link["href"] if job_link else ""),
            "timestamp": get_timestamp(),
        }

    def _parse_job_details(self, soup, url, detail_level):
        title = self._extract_text(soup, 'h1[aria-label="Job Title"]')
        company = self._extract_text(soup, ".TopFoldsc__CompanyName-sc-1fbktg5-4 a")
        job_data = {
            "title": title,
            "company": company,
            "url": url,
            "timestamp": get_timestamp(),
        }
        if detail_level >= 2:
            job_data["location"] = self._extract_text(
                soup, ".TopFoldsc__JobOverViewInfo-sc-1fbktg5-9"
            )
        if detail_level == 3:
            job_data["description"] = self._extract_text(
                soup, ".DraftjsReadersc__ContentContainer-sc-zm0o3p-0"
            )
        return job_data


class DataSaver:
    @staticmethod
    def _create_output_path(job_name, format_name):
        job_dir = os.path.join(os.getcwd(), "results", job_name.replace(" ", "_"))
        os.makedirs(job_dir, exist_ok=True)
        return os.path.join(job_dir, f"{get_timestamp()}.{format_name}")

    @staticmethod
    def to_json(data, job_name):
        if not data:
            return
        output_path = DataSaver._create_output_path(job_name, "json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Data successfully saved to: {output_path}")

    @staticmethod
    def to_csv(data, job_name):
        if not data:
            return
        output_path = DataSaver._create_output_path(job_name, "csv")
        df = pl.DataFrame(data)
        df.write_csv(output_path)
        print(f"Data successfully saved to: {output_path}")

    @staticmethod
    def to_parquet(data, job_name):
        if not data:
            return
        output_path = DataSaver._create_output_path(job_name, "parquet")
        pl.DataFrame(data).write_parquet(output_path, compression="snappy")
        print(f"Data successfully saved to: {output_path}")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Glints Job Market Intelligence Tool",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "search",
        nargs="?",
        default=None,
        type=str,
        help='Job titles to search, comma-separated (e.g., "devops,data analyst")',
    )
    parser.add_argument(
        "-b",
        "--browser",
        choices=["chrome", "firefox"],
        default="firefox",
        help="Browser to use (default: firefox)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "csv", "parquet"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "-d",
        "--details",
        type=int,
        choices=[1, 2, 3],
        default=None,
        help="Scraping detail level (overrides config)",
    )
    return parser.parse_args()


def get_credentials(config):
    username = input("\nEmail address: ")
    password = getpass.getpass("Password (hidden): ")
    save_choice = input("\nSave credentials for auto-login? (y/n): ").lower()
    if save_choice == "y":
        config.set("User", "email", username)
        config.set("User", "password", password)
        config.set("User", "auto_login", True)
        print("Credentials saved.")
    return username, password


def run_scraper_session(job_titles, browser_type, detail_level, output_format):
    config = ConfigManager()

    scrape_level = (
        detail_level
        if detail_level is not None
        else config.get("Scraping", "detail_level", 2)
    )

    with BrowserManager(browser_type) as driver:
        scraper = GlintsScraper(driver, config)

        login_choice = config.get("User", "auto_login")
        if login_choice:
            if config.get("User", "auto_login"):
                print("Attempting auto-login...")
                email = config.get("User", "email")
                password = config.get("User", "password")
                if not scraper.login(email, password):
                    print("Auto-login failed. Please log in manually.")
                    email, password = get_credentials(config)
                    scraper.login(email, password)
            else:
                email, password = get_credentials(config)
                scraper.login(email, password)

        for job_title in tqdm(job_titles, desc="Overall Progress", leave=True):
            print(
                f"\nStarting search for '{job_title}' with detail level {scrape_level}..."
            )

            if scrape_level == 1:
                results = list(scraper.collect_job_links(job_title, scrape_level))
            else:
                links = list(scraper.collect_job_links(job_title, scrape_level))
                if not links:
                    print(f"No links found for '{job_title}'.")
                    continue
                results = []
                for link in tqdm(
                    links, desc=f"Extracting '{job_title}' details", leave=False
                ):
                    details = scraper.extract_job_details(link, scrape_level)
                    if details:
                        results.append(details)

            if results:
                print(f"\nFound {len(results)} results for '{job_title}'. Saving...")
                if output_format == "json":
                    DataSaver.to_json(results, job_title)
                elif output_format == "csv":
                    DataSaver.to_csv(results, job_title)
                elif output_format == "parquet":
                    DataSaver.to_parquet(results, job_title)
            else:
                print(f"No data collected for '{job_title}'.")


def settings_menu(config):
    while True:
        print("\n" + "=" * 60)
        print(" SETTINGS")
        print("=" * 60)
        print("1. Change Auto-login Setting")
        print("2. Change Scraping Detail Level")
        print("3. Clear Saved Credentials")
        print("4. Return to Main Menu")

        choice = input("\nEnter your choice (1-4): ")

        if choice == "1":
            current = config.get("User", "auto_login", False)
            print(
                f"\nCurrent auto-login setting: {'Enabled' if current else 'Disabled'}"
            )
            new_setting = input("Enable auto-login? (y/n): ").lower() == "y"
            config.set("User", "auto_login", new_setting)
            print(f"Auto-login has been {'enabled' if new_setting else 'disabled'}")
        elif choice == "2":
            current = config.get("Scraping", "detail_level", 2)
            print(f"\nCurrent scraping detail level: {current}")
            try:
                new_level = int(input("Enter new detail level (1-3): "))
                if 1 <= new_level <= 3:
                    config.set("Scraping", "detail_level", new_level)
                    print(f"Scraping detail level set to {new_level}")
                else:
                    print("Invalid level. Please enter 1, 2, or 3.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        elif choice == "3":
            confirm = input(
                "\nAre you sure? This will clear your saved email and password. (y/n): "
            ).lower()
            if confirm == "y":
                config.set("User", "email", "")
                config.set("User", "password", "")
                config.set("User", "auto_login", False)
                print("Saved credentials have been cleared.")
        elif choice == "4":
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 4.")


def interactive_ui():
    config = ConfigManager()
    while True:
        print("\n" + "=" * 60)
        print(" GLINTS JOB MARKET INTELLIGENCE TOOL")
        print("=" * 60)
        print("1. Start Searching Jobs")
        print("2. Settings")
        print("3. Exit")

        choice = input("\nEnter your choice (1-3): ")

        if choice == "1":
            job_searches = input(
                "\nEnter job titles to search (separate with commas): "
            )
            job_titles = [
                item.strip().replace(" ", "+")
                for item in job_searches.split(",")
                if item.strip()
            ]
            if not job_titles:
                print("Please enter at least one job title.")
                continue

            print("\nSelect output format:")
            print("1. JSON | 2. CSV | 3. Parquet")
            format_choice = input("Your choice (1-3): ")
            format_map = {"1": "json", "2": "csv", "3": "parquet"}
            output_format = format_map.get(format_choice, "json")

            print("\nSelect browser:")
            print("1. Firefox | 2. Chrome")
            browser_choice = input("Your choice (1-2): ")
            browser_map = {"1": "firefox", "2": "chrome"}
            browser_type = browser_map.get(browser_choice, "firefox")

            run_scraper_session(job_titles, browser_type, None, output_format)

        elif choice == "2":
            settings_menu(config)
        elif choice == "3":
            print("\nExiting program. Thank you!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 3.")


def main():
    args = parse_arguments()

    if args.search:
        job_titles = [item.strip().replace(" ", "+") for item in args.search.split(",")]
        try:
            run_scraper_session(job_titles, args.browser, args.details, args.format)
            print("\nAll operations completed successfully!")
        except KeyboardInterrupt:
            print("\nOperation interrupted by user. Shutting down...")
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
    else:
        interactive_ui()


if __name__ == "__main__":
    main()
