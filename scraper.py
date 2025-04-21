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

def request_page(job_title, page_num, browser):
    try:
        # Random delay to avoid rate limiting
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

def extract_job_links(html, job_title):
    if not html:
        return []
        
    jobs = html.find_all("a", class_="CompactOpportunityCardsc__JobCardTitleNoStyleAnchor-sc-dkg8my-12")
    links = []
    
    for job in jobs:
        
        if not job.has_attr('href') or not job.text:
            continue
        
        job_validation = job.text.strip().lower()
        if job_title.lower() in job_validation:
            links.append(job['href'])
            
    return links

def collect_job_links(job_title, browser):
    print(f"\nAnalyzing job market for: {job_title}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    all_links = []
    first_page = request_page(job_title, 1, browser)
    
    if not first_page:
        print(f"No results found for '{job_title}' or error loading first page")
        return []
        
    first_page_links = extract_job_links(first_page, job_title)
    all_links.extend(first_page_links)
    
  
    pagination_buttons = first_page.find_all("button", class_="UnstyledButton-sc-zp0cw8-0 AnchorPaginationsc__Number-sc-8wke03-3 dYSdtB bkvUQn")
    
    if not pagination_buttons:
        print(f"Found {len(all_links)} job listings on a single page")
        return all_links
        
    try:
        last_page_num = int(pagination_buttons[-1].get_text())
        print(f"Found {last_page_num} pages of results to process")
        
        for page_num in tqdm(range(2, last_page_num + 1), desc=f"Collecting {job_title} listings", colour='green'):
            page = request_page(job_title, page_num, browser)
            if page:
                page_links = extract_job_links(page, job_title)
                all_links.extend(page_links)
            # Continue to next page even if current page failed
            
        print(f"Successfully gathered {len(all_links)} job listings")
        return all_links
        
    except (ValueError, IndexError) as e:
        print(f"Error parsing pagination: {str(e)}")
        return all_links  # Return whatever links we've collected so far

def get_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace(":", "-")

def extract_text(soup, selector, default="No Data"):
    """Helper function to safely extract text from a CSS selector"""
    element = soup.select_one(selector)
    return element.get_text() if element else default

def extract_job_details(url, browser):
    full_url = "https://glints.com" + url
    
    try:
        browser.get(full_url)
        time.sleep(randint(1, 3))  # Random delay to avoid rate limiting
        
        WebDriverWait(browser, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".TopFoldsc__JobOverViewTitle-sc-1fbktg5-3"))
        )
        
        html = browser.page_source
        soup = BeautifulSoup(html, "html.parser")
        page = soup.find(id="__next")
        
        if not page:
            return None
        

        title = extract_text(page, "h1.TopFoldsc__JobOverViewTitle-sc-1fbktg5-3", "No Title")
        education = extract_text(page, "div.TopFoldsc__JobOverViewInfo-sc-1fbktg5-9:nth-child(4) > span:nth-child(2)", "No Requirement")
        experience = extract_text(page, "div.TopFoldsc__JobOverViewInfo-sc-1fbktg5-9:nth-child(5)", "No Requirement")
        job_type = extract_text(page, "div.TopFoldsc__JobOverViewInfo-sc-1fbktg5-9:nth-child(3)", "Undisclosed")
        salary = extract_text(page, ".TopFoldsc__BasicSalary-sc-1fbktg5-13", "Undisclosed")
        
   
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
        
        return {
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
            "timestamp": get_timestamp(),
            "url": full_url,
        }
        
    except TimeoutException:
        print(f"Timeout while loading job details for {full_url}")
        return None
    except Exception as e:
        print(f"Error extracting job details for {full_url}: {str(e)}")
        return None

def extract_all_job_details(links, browser):
    jobs = []
    
    for link in tqdm(links, desc="Extracting detailed job information", colour='red'):
        job_details = extract_job_details(link, browser)
        if job_details:
            jobs.append(job_details)
        # Continue to next link even if current link failed
            
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

def save_to_csv(jobs, job_name):
    if not jobs:
        print(f"No data to save for '{job_name}'")
        return False
    
    try:
        df = pl.DataFrame(jobs)
        
        # Convert list columns to strings for CSV compatibility
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

def main():
    print("\n" + "="*60)
    print("       GLINTS JOB MARKET INTELLIGENCE TOOL")
    print("="*60)
    
    browser = None
    
    try:
        # Set up the browser
        valid_formats = ["1", "2"]
        browser_choice = None
        
        while browser_choice not in valid_formats:
            print("Select you browser:")
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
            
                
        login_attempts = 0
        max_login_attempts = 3
        
        print("\nAuthentication Required")
        print("Please provide your Glints account credentials")
        
        while login_attempts < max_login_attempts:
            username = input("\nEmail address: ")
            password = getpass.getpass("Password (hidden): ")
            
            print("\nVerifying credentials...")
            if login(browser, username, password):
                print("\nAuthentication successful!")
                break
                
            login_attempts += 1
            remaining = max_login_attempts - login_attempts
            
            if remaining > 0:
                print(f"Login failed. {remaining} attempts remaining.")
            else:
                print("Maximum login attempts reached. Exiting.")
                return
        
        # Get job search terms
        while True:
            job_searches = input("\nEnter job titles to search (separate multiple jobs with commas): ")
            job_search_list = [item.strip() for item in job_searches.split(",") if item.strip()]
            
            if job_search_list:
                break
                
            print("Please enter at least one job title.")
        

        print("\nData Export Configuration")
        
        valid_formats = ["1", "2", "3"]
        file_format = None
        
        while file_format not in valid_formats:
            print("Select output format:")
            print("  1. JSON  - Human-readable, ideal for further processing")
            print("  2. CSV   - Compatible with spreadsheet applications")
            print("  3. Parquet - Efficient storage, best for data analysis")
            file_format = input("\nYour choice (1-3): ")
            
            if file_format not in valid_formats:
                print("Invalid choice. Please select 1, 2, or 3.")
        
        # Process each job search
        print("\nStarting job search operation")
        for job_title in tqdm(job_search_list, desc="Processing job categories", leave=True):

            links = collect_job_links(job_title, browser)
            
            if not links:
                print(f"No job listings found for '{job_title}'. Skipping to next job title.")
                continue
                

            jobs = extract_all_job_details(links, browser)
            
            if not jobs:
                print(f"Failed to extract any job details for '{job_title}'. Skipping to next job title.")
                continue
                

            print(f"\nPreparing to export {len(jobs)} {job_title} job listings")
            
            match file_format:
                case "1":
                    save_to_json(jobs, job_title)
                case "2":
                    save_to_csv(jobs, job_title)
                case "3":
                    save_to_parquet(jobs, job_title)
        
        print("\nAll operations completed successfully!")
        print("="*60)
        
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