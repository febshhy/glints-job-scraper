# Glints Job Scraper

A simple Python-based CLI tool to scrape job listings from [Glints Indonesia](https://glints.com/id).  
It searches for jobs based on user-defined keywords and exports the results in your preferred file format (`json`, `csv`, or `parquet`).

> ⚠️ **Disclaimer:**  
> For educational use only. No liability assumed.


## 📋 Features

- Keyword-based job search
- Exports to JSON, CSV, or Parquet
- CLI-based interaction
- Collects key job and company information


## 🧾 Scraped Data Fields

| Field | Description |
|-------|-------------|
| `title` | Job Title |
| `salary` | Salary Range |
| `job_type` | Work Setting & Employment Type |
| `skills_requirements` | List of Skills Required |
| `education_requirements` | Minimum Education Level Required |
| `another_requirements` | Additional Requirements (e.g., age, gender) |
| `location_province` | Province |
| `location_city` | City |
| `location_district` | District |
| `company_name` | Company Name |
| `company_industry` | Industry |
| `company_size` | Number of Employees |
| `timestamp` | Time When the Job Was Scraped |
| `url` | Job Listing URL |

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

4. Run the scraper:
   ```bash
   python scraper.py
   ```


## 🚀 How to Use

1. Enter your Glints credentials (email and password).
2. Provide job search keywords (comma-separated) (trailing whitespace is accepted).  
   Example:  
   ```
   data analyst, data scientist,data engineer
   ```
3. Choose the desired export format: `json`, `csv`, or `parquet`.
4. Wait for the scraping to finish.
5. Find the results in the `./results/{your_search_term}` directory.

---

## 📌 Notes

- Some results may require additional cleaning or preprocessing depending on your use case.
- Make sure you have a stable internet connection while scraping.
- Hitting the Web Rate Limiter is expected. More robust error handling is needed
