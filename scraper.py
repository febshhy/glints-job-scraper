from selenium import webdriver
from selenium.webdriver.firefox.options import Options as Firefox_Options
from selenium.webdriver.chrome.options import Options as Chrome_Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
from tqdm import tqdm
import getpass
from random import randint
import polars as pl
from datetime import datetime, timezone
import os
import json
import time
import argparse

def get_config_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    config_path = get_config_path()
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {
            "User": {
                "auto_login": False,  
                "email": "",
                "password": ""
            },
            "Scraping": {
                "detail_level": 2,  
            }
        }
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    return config

def save_config(config):
    """Save configuration to file"""
    config_path = get_config_path()
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

def get_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace(":", "-")

def initialize_browser(browser_choice = None):
    valid_formats = ["1", "2"]
    
    while browser_choice not in valid_formats:
        print("Select your browser:")
        print("  1. Mozilla Firefox")
        print("  2. Google Chrome")
        browser_choice = input("\nYour choice (1-2): ")
            
    print("\nInitializing browser session...")        
    
    match browser_choice:
        case "1":
            options = Firefox_Options()
            options.add_argument("--headless")
            options.set_preference("general.useragent.override", 
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0,gzip(gfe) ")
            browser = webdriver.Firefox(options=options)
        case "2":
            options = Chrome_Options()
            options.add_argument("--headless")
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36")
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            browser = webdriver.Chrome(options=options)
    
    return browser

def login(browser, username, password):
    print("\n┌─────────────────────────────────┐")
    print("│ Attempting to log in to Glints  │")
    print("└─────────────────────────────────┘")
    
    try:
        browser.get("https://glints.com/id/login")
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.LinkStyle__StyledLink-sc-usx229-0:nth-child(3)"))
        ).click()

        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#login-form-email"))
        ).send_keys(username)

        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#login-form-password"))
        ).send_keys(password)

        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ButtonStyle__SolidShadowBtn-sc-jyb3o2-3"))
        ).click()

        WebDriverWait(browser, 10).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".ParagraphStyles__Paragraph-sc-1w5f8q5-0")),
                EC.presence_of_element_located((By.CSS_SELECTOR, ".UserMenuComponentssc__NameHolder-sc-ovl5x6-4"))
            )
        )
        
        if browser.find_elements(By.CSS_SELECTOR, ".UserMenuComponentssc__NameHolder-sc-ovl5x6-4"):
            return True
            
        print("\nAuthentication Error: Invalid credentials detected")
        return False

    except TimeoutException:
        print("\nNetwork Error: Timeout during login process")
        return False
    except Exception as e:
        print(f"\nSystem Error: Login failed - {str(e)}")
        return False

def login_sequence(browser, config):
    login_attempts = 0
    max_login_attempts = 3
    
    print("\nAuthentication Required")
    print("Please provide your Glints account credentials")
        
    username = config["User"].get("email", "")
    password = config["User"].get("password", "")
    auto_login = config["User"].get("auto_login", False)
    
    if auto_login and username and password:
        print("\nAttempting auto-login...")

        if login(browser, username, password):
            print("\nAuto-login successful!")
            return True
        else:
            print("Auto-login failed. Switching to manual login.")
            login_attempts = 1
    
    while login_attempts < max_login_attempts:            
        username = input("\nEmail address: ")
        password = getpass.getpass("Password (hidden): ")
        
        print("\nVerifying credentials...")
        if login(browser, username, password):
            print("\nAuthentication successful!")
            print("\nDo You Want to Save Your Credentials and Using Autologin?")
            print("0. No | 1. Yes")
            option = input("\nInput Your Choice (numbers only):")
            if option:
                config["User"]["email"] = username
                config["User"]["password"] = password
                config["User"]["auto_login"] = True
                save_config(config)
                print("\nCredentials Saved")
             
            break
            
        login_attempts += 1
        remaining = max_login_attempts - login_attempts
        
        if remaining > 0:
            print(f"Login failed. {remaining} attempts remaining.")
        else:
            print("Maximum login attempts reached. Exiting.")
            return

def settings_menu(config):
    """Display and handle settings menu"""
    print("\n" + "="*60)
    print(" SETTINGS")
    print("="*60)
    print("1. Change Auto-login Setting")
    print("2. Change Scraping Detail Level")
    print("3. Clear Saved Credentials")
    print("4. Return to Main Menu")
    
    choice = input("\nEnter your choice (1-4): ")
    
    if choice == "1":
        current = config["User"]["auto_login"]
        print(f"\nCurrent auto-login setting: {'Enabled' if current else 'Disabled'}")
        new_setting = input("Enable auto-login? (y/n): ").lower() == 'y'
        config["User"]["auto_login"] = new_setting
        print(f"Auto-login has been {'enabled' if new_setting else 'disabled'}")
        save_config(config)
        
    elif choice == "2":
        current = config["Scraping"]["detail_level"]
        print(f"\nCurrent scraping detail level: {current}")
        print("1 - Basic information")
        print("2 - Standard detail")
        print("3 - Maximum detail")
        
        while True:
            try:
                new_level = int(input("Enter new detail level (1-3): "))
                if new_level in [1, 2, 3]:
                    config["Scraping"]["detail_level"] = new_level
                    print(f"Scraping detail level set to {new_level}")
                    save_config(config)
                    break
                else:
                    print("Please enter a number between 1 and 3")
            except ValueError:
                print("Please enter a valid number")
                
    elif choice == "3":
        confirm = input("\nAre you sure you want to clear saved credentials? (y/n): ").lower() == 'y'
        if confirm:
            config["User"]["email"] = ""
            config["User"]["password"] = ""
            config["User"]["auto_login"] = False
            save_config(config)
            print("Credentials have been cleared")
            
    elif choice == "4":
        return
    else:
        print("Invalid choice. Please enter a number between 1 and 4.")
    
    settings_menu(config)

def request_page(job_title, page_num, browser):
    try:
        time.sleep(randint(2, 5))
        
        url = f"https://glints.com/id/opportunities/jobs/explore?keyword={job_title}&country=ID&locationName=All+Cities%2FProvinces&lowestLocationLevel=1&page={page_num}"
        browser.get(url)
        
        WebDriverWait(browser, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.JobCardsc__JobcardContainer-sc-hmqj50-0"))
        )
        
        html = browser.page_source
        soup = BeautifulSoup(html, "html.parser")
        return soup.find(id="__next")
        
    except TimeoutException:
        print(f"\nTimeout loading page {page_num} for '{job_title}'. Skipping...")
        return None
    except WebDriverException as e:
        print(f"\nBrowser error on page {page_num} for '{job_title}': {str(e)}. Skipping...")
        return None
    except Exception as e:
        print(f"\nUnexpected error loading page {page_num} for '{job_title}': {str(e)}. Skipping...")
        return None

def extract_text(soup, selector, default="No Data", flag=0):
    element = soup.select_one(selector)
    if element and flag:
        return element.get_text(separator='\n', strip=True)
    elif element:
        return element.get_text()
    else:
        return default
    

def extract_job_links(html, job_title, details_level):
    if not html:
        return []
    
    cards = html.find_all("div", class_="CompactOpportunityCardsc__CompactJobCard-sc-dkg8my-4")    
    links = []
    
    for card in cards:
        job = card.find("a", class_="CompactOpportunityCardsc__JobCardTitleNoStyleAnchor-sc-dkg8my-12")
        
        if not job.has_attr('href') or not job.text:
            continue
        
        job_validation = job.text.strip().lower()
        if job_title.lower() in job_validation:
            if details_level == 1:
                links.append({
                    "title": job.get_text(),
                   "company": extract_text(card,".CompactOpportunityCardsc__CompanyLink-sc-dkg8my-14"),
                    "salary":extract_text(card,".CompactOpportunityCardsc__SalaryWrapper-sc-dkg8my-32"),
                    "location":extract_text(card,".CardJobLocation__LocationWrapper-sc-v7ofa9-0"),
                    "updated":extract_text(card,".CompactOpportunityCardsc__UpdatedAtMessage-sc-dkg8my-26"),
                    "url": "https://glints.com" + job['href'],  
                    "timestamp": get_timestamp(),
                    
                })
            else:
                links.append(job['href'])
            
    return links

def collect_job_links(job_title, browser, details_level):
    print(f"\nAnalyzing job market for: {job_title}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    all_links = []
    page_num = 1
    
    
    with tqdm(desc=f"Collecting {job_title} listings", colour='green') as pbar:
        while True:

            page = request_page(job_title, page_num, browser)
            
            if not page:
                print(f"\nError or no content on page {page_num}. Stopping.")
                break
                

            page_links = extract_job_links(page, job_title, details_level)
            

            if not page_links:
                print(f"\nNo new jobs found on page {page_num}. Reached the end.")
                break
                
            all_links.extend(page_links)
            
      
            page_num += 1
            pbar.update(1) 
            
            time.sleep(0.5) 

    print(f"\nSuccessfully gathered {len(all_links)} {job_title} listings from {page_num - 1} pages.")
    return all_links



def extract_job_details(url, browser, details_level):
    full_url = "https://glints.com" + url
    
    try:
        browser.get(full_url)
        time.sleep(randint(1, 3))  
        
        WebDriverWait(browser, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "main.Opportunitysc__Main-sc-gb4ubh-3.kpUoLB"))
        )
        
        html = browser.page_source
        soup = BeautifulSoup(html, "html.parser")
        page = soup.select_one("html.notranslate body div#app div#__next div div.MainContainersc__MainLayout-sc-xmyke8-0.desvou div.MainContainersc__MainBody-sc-xmyke8-2.drnzBQ div.GlintsContainer-sc-usaans-0.fNeuNN div.Opportunitysc__Container-sc-gb4ubh-2.cXvpcO main.Opportunitysc__Main-sc-gb4ubh-3.kpUoLB")

        if not page:
            return None
        
        title = extract_text(page,"h1.TopFoldsc__JobOverViewTitle-sc-1fbktg5-3")
        salary = extract_text(page, "span.TopFoldsc__BasicSalary-sc-1fbktg5-13", "Undisclosed")
        job_type = extract_text(page, "div.TopFoldsc__JobOverViewInfo-sc-1fbktg5-9:nth-child(3)", "Undisclosed")
        education = extract_text(page, "div.TopFoldsc__JobOverViewInfo-sc-1fbktg5-9:nth-child(4)", "No Requirement")
        experience = extract_text(page, "div.TopFoldsc__JobOverViewInfo-sc-1fbktg5-9:nth-child(5)", "No Requirement")

        skills = []
        container_skill = page.find("div", class_="Opportunitysc__SkillsContainer-sc-gb4ubh-10 jccjri")
        if container_skill:
            skills_raw = container_skill.find_all("label", class_="TagStyle__TagContent-sc-66xi2f-0 iFeugN tag-content")
            skills = [skill.get_text() for skill in skills_raw if skill]
 
 
        requirements = []
        extra_requirements = page.find_all("div", class_="TagStyle-sc-r1wv7a-4 bJWZOt JobRequirementssc__Tag-sc-15g5po6-3 cIkSrV")
        if extra_requirements and len(extra_requirements) > 3:
            requirements = [req.get_text() for req in extra_requirements[3:] if req]
  
        province = extract_text(page, "label.BreadcrumbStyle__BreadcrumbItemWrapper-sc-eq3cq-0:nth-child(3) > a:nth-child(1)")
        city = extract_text(page, "label.BreadcrumbStyle__BreadcrumbItemWrapper-sc-eq3cq-0:nth-child(4) > a:nth-child(1)")
        district = extract_text(page, "label.BreadcrumbStyle__BreadcrumbItemWrapper-sc-eq3cq-0:nth-child(5) > a:nth-child(1)")
 
        company_name = extract_text(page, ".AboutCompanySectionsc__Title-sc-c7oevo-6 > a:nth-child(2)", "Undisclosed")
        company_industry = extract_text(page, ".AboutCompanySectionsc__CompanyIndustryAndSize-sc-c7oevo-7 > span:nth-child(1)", "Undisclosed")
        company_size = extract_text(page, ".AboutCompanySectionsc__CompanyIndustryAndSize-sc-c7oevo-7 > span:nth-child(3)", "Undisclosed")
        post_updated = extract_text(page,".CompactOpportunityCardsc__UpdatedAtMessage-sc-dkg8my-26")
 
        data = {
                "title": title,
                "salary": salary,
                "job type": job_type,
                "skills requirements": skills,
                "education requirements": education,
                "experience requirements": experience,
                "another requirements": requirements,
                "location (province)": province,
                "location (city)": city,
                "location (district)": district,
                "company name": company_name,
                "company industry": company_industry,
                "company size": company_size,
                "post updated": post_updated,
                "timestamp": get_timestamp(),
                "url": full_url,
            }
            
        if details_level == 3:
            description = extract_text(page, ".DraftjsReadersc__ContentContainer-sc-zm0o3p-0", flag=1)
            data["description"] = description
        
        return data
        
    except TimeoutException:
        print(f"Timeout while loading job details for {full_url}")
        return None
        
    except Exception as e:
        print(f"Error extracting job details for {full_url}: {str(e)}")
        return None

def extract_all_job_details(links, browser, details_level):
    jobs = []
    
    for link in tqdm(links, desc="Extracting detailed job information", colour='red'):
        job_details = extract_job_details(link, browser, details_level)
        if job_details:
            jobs.append(job_details)
  
    return jobs

def create_output_path(job_name, format_name):
    timestamp = get_timestamp()
    job_dir = os.path.join(os.getcwd(), "results", job_name)
    try:
        os.makedirs(job_dir, exist_ok=True)
        return os.path.join(job_dir, f"{timestamp}.{format_name}")
    except OSError as e:
        print(f"Error creating directory: {str(e)}")
        return os.path.join(os.getcwd(), f"{job_name}_{timestamp}.{format_name}")


def save_to_json(jobs, job_name):
    if not jobs:
        print(f"No data to save for '{job_name}'")
        return False
        
    output_path = create_output_path(job_name, "json")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(jobs, file, indent=4, ensure_ascii=False)
        print(f"Data successfully saved to: {output_path}")
        return True
    except Exception as e:
        print(f"Error saving to JSON: {e}")
        return False

def save_to_csv(jobs, job_name, details_level):
    if not jobs:
        print(f"No data to save for '{job_name}'")
        return False
    
    try:
        df = pl.DataFrame(jobs)
        
        if details_level >= 2:
            df = df.with_columns(
                pl.col("skills requirements").map_elements(lambda x: ",".join(x) if isinstance(x, list) else "", return_dtype=pl.String),
                pl.col("another requirements").map_elements(lambda x: ",".join(x) if isinstance(x, list) else "", return_dtype=pl.String)
            )

        output_path = create_output_path(job_name, "csv")
        df.write_csv(output_path, include_header=True)
        print(f"Data successfully saved to: {output_path}")
        return True
    except Exception as e:
        print(f"Error saving to CSV: {e}")
        return False

def save_to_parquet(jobs, job_name):
    if not jobs:
        print(f"No data to save for '{job_name}'")
        return False
    
    try:
        df = pl.DataFrame(jobs)
        output_path = create_output_path(job_name, "parquet")
        df.write_parquet(output_path, compression="snappy")
        print(f"Data successfully saved to: {output_path}")
        return True
    except Exception as e:
        print(f"Error saving to Parquet: {e}")
        return False
    

def scraper(browser, details_level, file_format=None, job_search_list=None):        

    if job_search_list:
        job_search_list = [item.strip() for item in job_search_list.split(",") if item.strip()]
    
    while not job_search_list:
        job_searches = input("\nEnter job titles to search (separate multiple jobs with commas): ")
        job_search_list = [item.strip() for item in job_searches.split(",") if item.strip()]
        print("Please enter at least one job title.")
    

    print("\nData Export Configuration")
    
    valid_formats = ["1", "2", "3"]
    
    while file_format not in valid_formats:
        print("Select output format:")
        print("  1. JSON  - Human-readable, ideal for further processing")
        print("  2. CSV   - Compatible with spreadsheet applications")
        print("  3. Parquet - Efficient storage, best for data analysis")
        file_format = input("\nYour choice (1-3): ")
        
        if file_format not in valid_formats:
            print("Invalid choice. Please select 1, 2, or 3.")
    

    print("\nStarting job search operation")
    for job_title in tqdm(job_search_list, desc="Processing job categories", leave=True):

        links = collect_job_links(job_title, browser, details_level)
            
        if not links:
            print(f"No job listings found for '{job_title}'. Skipping to next job title.")
            continue

        if details_level == 1:
            jobs = links
        else:
            jobs = extract_all_job_details(links, browser, details_level)
        
        if not jobs:
            print(f"Failed to extract any job details for '{job_title}'. Skipping to next job title.")
            continue
            

        print(f"\nPreparing to export {len(jobs)} {job_title} job listings")
        
        match file_format:
            case "1":
                save_to_json(jobs, job_title)
            case "2":
                save_to_csv(jobs, job_title, details_level)
            case "3":
                save_to_parquet(jobs, job_title)
    
    print("\nAll operations completed successfully!")
    print("="*60)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Glints Job Market Intelligence Tool",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument('search',nargs='?', default=None, type=str, help='Job titles to search (add quotation "devops")')
    parser.add_argument('-b', '--browser', type=str, choices=['chrome', 'firefox'], 
                        default='firefox', help='Browser to use (default: firefox)')
    parser.add_argument('-f', '--format', type=str, choices=['json', 'csv', 'parquet'], 
                        default='json', help='Output format (default: json)')
    parser.add_argument('-u', '--username', type=str, help='Glints account email')
    parser.add_argument('-p', '--password', type=str, help='Glints account password')
    parser.add_argument('-d', '--details', type=int, choices=[1, 2, 3], default = 2,
                        help="Scraping Detail (default: level 2)")
    parser.add_argument('--no-login', action='store_true', help='Skip the login process')
    
    args = parser.parse_args()
    
    if (args.browser != 'firefox' or args.format != 'json') and not args.search:
        parser.error("--browser and --format can only be used when --search is specified")
    
    if bool(args.username) != bool(args.password):
        parser.error("Both --username and --password must be provided together")
    
    browser_map = {'firefox': '1', 'chrome': '2'}
    format_map = {'json': '1', 'csv': '2', 'parquet': '3'}
    
    args.browser_code = browser_map[args.browser]
    args.format_code = format_map[args.format]
        
    return args

def main():
    print("\n" + "="*60)
    print("       GLINTS JOB MARKET INTELLIGENCE TOOL")
    print("="*60)
    config = load_config()
    args = parse_arguments()
    
    try:
        if args.search:
            browser = initialize_browser(args.browser_code)
            if not args.no_login:
                if args.username and args.password:
                    succeed = login(browser, args.username, args.password)
                    config["User"]["email"] = args.username
                    config["User"]["password"] = args.password
                    
                    if not succeed:
                        print("Your Credentials is Wrong!!!!")
                        exit()
                else:
                    login(browser, config["User"].get("email"), config["User"].get("password"))
            scraper(browser, args.details, args.format_code, args.search)
            
        else:        
            while True:
                print("\nMain Menu")
                print("1. Start Searching Job")
                print("2. Settings")
                print("3. Exit")
                
                choice = input("\nInput Your Choice:")
                browser = None
                if choice == "1":
                    details = config["Scraping"].get("detail_level", 2)
                    browser = initialize_browser()
                    print("\nDo you want to login to Glints?")
                    print("0. No | 1. Yes")
                    login_choice = input("\nInput Your Choice (numbers only):")
                    
                    if login_choice == "1":
                        login_sequence(browser, config)
                    scraper(browser, details)
                
                if choice == "2":
                    settings_menu(config)
                
                if choice == "3":
                    print("\nExiting program. Thank you for using This Tool.")
                    break

        
    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user. Shutting down...")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        print("The program will now exit gracefully.")
    finally:
        if browser:
            print("\nCleaning up resources...")
            try:
                browser.quit()
                print("Browser session terminated\n")
            except Exception:
                print("Failed to cleanly close the browser, but exiting anyway.\n")

if __name__ == "__main__":
    
    main()