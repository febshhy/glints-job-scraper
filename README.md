# Glints Job Scraper

A simple Python-based CLI tool to scrape job listings from [Glints Indonesia](https://glints.com/id).  
It searches for jobs based on user-defined keywords and exports the results in your preferred file format (`json`, `csv`, or `parquet`).

> ⚠️ **DISCLAIMER:**  
> For educational purposes only. Using scraping tools, especially with login credentials, may violate the Computer Fraud and Abuse Act, Terms of Service, and other laws, potentially constituting a felony. Obtain permission before scraping any website. User assumes all legal responsibility. No liability assumed.


## 📋 Features

- Keyword-based job search
- Exports to JSON, CSV, or Parquet
- Configurable scraping detail levels
- Browser choice (Firefox or Chrome)
- Command-line arguments for automation
- Interactive CLI-based mode for easy use
- Collects key job and company information


## 🧾 Scraped Data Fields

The tool offers three levels of scraping detail:

### Level 1 (Significantly Faster up to 3X)
Basic job information:
- `title` - Job Title
- `company` - Company Name
- `salary` - Salary Range
- `location` - Location
- `updated` - Last Updated Date
- `url` - Job Listing URL
- `timestamp` - Time When the Job Was Scraped

### Level 2 (Default)
All fields from Level 1, plus:
- `job_type` - Work Setting & Employment Type
- `skills_requirements` - List of Skills Required
- `education_requirements` - Minimum Education Level Required
- `another_requirements` - Additional Requirements (e.g., age, gender)
- `location_province` - Province
- `location_city` - City
- `location_district` - District
- `company_industry` - Industry
- `company_size` - Number of Employees

### Level 3 (Comprehensive)
All fields from Level 2, plus:
- `description` - Full Job Description


## Performance Testing Results

### Large Dataset (18 pages, 78 listings - CSV)

| Complexity Level | Run Time | Memory Usage | Storage Size |
|------------------|----------|-------------|--------------|
| Level 1          | 169 sec  | 92.23 MB    | 25 KB        |
| Level 2          | 667 sec  | 90.93 MB    | 35 KB        |
| Level 3          | 543 sec  | 93.23 MB    | 137 KB       |

### Small Dataset (4 pages, 10 listings - CSV)

| Complexity Level | Run Time | Memory Usage | Storage Size |
|------------------|----------|-------------|--------------|
| Level 1          | 45 sec   | 70.79 MB    | 4 KB         |
| Level 2          | 105 sec  | 76.80 MB    | 5 KB         |
| Level 3          | 110 sec  | 77.48 MB    | 13 KB        |

---

## ⚙️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/febshhy/glints-job-scraper.git
   ```

2. Navigate to the project folder:
   ```bash
   cd path/to/glints-job-scraper
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 How to Use

The scraper can be used in two ways: with command-line arguments or through an interactive CLI interface.

### Method 1: Command-Line Arguments

```bash
python scraper.py "job title" [options]
```

#### Required Arguments:
- `search`: Job title(s) to search (use quotes for multi-word terms, e.g., "data analyst")

#### Optional Arguments:
- `-b, --browser`: Browser to use (`chrome` or `firefox`, default: `firefox`)
- `-f, --format`: Output format (`json`, `csv`, or `parquet`, default: `json`)
- `-u, --username`: Glints account email
- `-p, --password`: Glints account password
- `-d, --details`: Scraping detail level (`1`, `2`, or `3`, default: `2`)
  - Level 1: Basic job information (fastest)
  - Level 2: Detailed job information (default)
  - Level 3: Comprehensive information including job description

### Method 2: Interactive CLI

Simply run the script without arguments to enter interactive mode:

```bash
python scraper.py
```

In interactive mode, you'll be prompted to:
1. In main menu, you can choose settings or job searchs
2. Choose which browser to use (Firefox or Chrome)
3. Enter your Glints credentials (email and password)
4. Choose if you want to save the credentials and do an auto login or not
5. Provide job search keywords (comma-separated) (trailing whitespace is accepted)  
   Example:  
   ```
   data analyst, data scientist, data engineer
   ```
6. Choose the desired export format: `json`, `csv`, or `parquet`
7. Select a scraping detail level (1, 2, or 3)

In settings, there is:
1. Change Auto-login Setting - Turn on or turn off auto-login function
2. Change Scraping Detail Level - Changing the level of scrape
3. Clear Saved Credentials - Remove email and passwords
4. Return to Main Menu

### Examples

Command-line usage:
```bash
python scraper.py "devops engineer" -b chrome -f csv -d 1
```

With login credentials:
```bash
python scraper.py "UI/UX designer" -u your.email@example.com -p yourpassword -d 3
```

The results will be saved in the `./results/{your_search_term}` directory.

---

## 📌 Notes

- Level 1 scraping is significantly faster for quick searches
- Some results may require additional cleaning or preprocessing depending on your use case
- Make sure you have a stable internet connection while scraping
- Hitting the Web Rate Limiter is expected. More robust error handling is needed