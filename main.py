import os
import time
import json
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import KEYWORDS, BROWSER_HEADERS, DELAY_BETWEEN_REQUESTS

class RemoteJobScraper:
    def __init__(self):
        self.jobs = []
        self.setup_selenium()
        
    def setup_selenium(self):
        """Setup Selenium WebDriver with Chrome"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            
            # Install ChromeDriver using webdriver_manager
            service = Service(ChromeDriverManager().install())
            
            print("Initializing Chrome WebDriver...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("Chrome WebDriver initialized successfully!")
            
        except Exception as e:
            print(f"Error setting up Chrome WebDriver: {str(e)}")
            print("Continuing without Selenium-dependent features...")
            self.driver = None

    def search_remote_jobs(self, keyword):
        """Search for remote jobs across different platforms"""
        self.search_we_work_remotely(keyword)
        self.search_remote_ok(keyword)
        self.search_remote_co(keyword)
        
    def search_we_work_remotely(self, keyword):
        """Scrape jobs from WeWorkRemotely"""
        try:
            url = f"https://weworkremotely.com/remote-jobs/search?term={keyword}"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            job_listings = soup.find_all('li', class_='feature')
            for job in job_listings:
                title = job.find('span', class_='title')
                company = job.find('span', class_='company')
                if title and company:
                    self.jobs.append({
                        'title': title.text.strip(),
                        'company': company.text.strip(),
                        'source': 'WeWorkRemotely',
                        'url': f"https://weworkremotely.com{job.find('a')['href']}",
                        'date_posted': datetime.now().strftime('%Y-%m-%d'),
                        'keyword': keyword
                    })
        except Exception as e:
            print(f"Error scraping WeWorkRemotely: {str(e)}")

    def search_remote_ok(self, keyword):
        """Scrape jobs from RemoteOK"""
        try:
            url = f"https://remoteok.com/remote-{keyword}-jobs"
            headers = BROWSER_HEADERS
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            job_listings = soup.find_all('tr', class_='job')
            for job in job_listings:
                title = job.find('h2', itemprop='title')
                company = job.find('h3', itemprop='name')
                if title and company:
                    self.jobs.append({
                        'title': title.text.strip(),
                        'company': company.text.strip(),
                        'source': 'RemoteOK',
                        'url': f"https://remoteok.com{job.find('a', class_='preventLink')['href']}",
                        'date_posted': datetime.now().strftime('%Y-%m-%d'),
                        'keyword': keyword
                    })
        except Exception as e:
            print(f"Error scraping RemoteOK: {str(e)}")

    def search_remote_co(self, keyword):
        """Scrape jobs from Remote.co"""
        if self.driver is None:
            print("Skipping Remote.co scraping as Selenium WebDriver is not available")
            return
            
        try:
            url = f"https://remote.co/remote-jobs/search/?search_keywords={keyword}"
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "job_listing"))
            )
            
            job_listings = self.driver.find_elements(By.CLASS_NAME, "job_listing")
            for job in job_listings:
                try:
                    title = job.find_element(By.CLASS_NAME, "position").text
                    company = job.find_element(By.CLASS_NAME, "company").text
                    job_url = job.find_element(By.TAG_NAME, "a").get_attribute("href")
                    
                    self.jobs.append({
                        'title': title,
                        'company': company,
                        'source': 'Remote.co',
                        'url': job_url,
                        'date_posted': datetime.now().strftime('%Y-%m-%d'),
                        'keyword': keyword
                    })
                except Exception as e:
                    continue
        except Exception as e:
            print(f"Error scraping Remote.co: {str(e)}")

    def save_results(self, keyword):
        """Save scraped jobs to CSV and JSON files, organized by keyword and append to existing files"""
        if not os.path.exists('output'):
            os.makedirs('output')
            
        # Create a directory for this keyword if it doesn't exist
        keyword_dir = os.path.join('output', keyword)
        if not os.path.exists(keyword_dir):
            os.makedirs(keyword_dir)
        
        # Filter jobs for this keyword
        keyword_jobs = [job for job in self.jobs if job['keyword'] == keyword]
        
        if keyword_jobs:
            # Add update timestamp to each job
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for job in keyword_jobs:
                job['last_updated'] = timestamp

            # Base filenames without timestamp
            csv_filename = os.path.join(keyword_dir, f"{keyword}_jobs.csv")
            json_filename = os.path.join(keyword_dir, f"{keyword}_jobs.json")
            
            # Handle CSV file
            if os.path.exists(csv_filename):
                # Read existing CSV
                existing_df = pd.read_csv(csv_filename)
                # Create DataFrame for new jobs
                new_df = pd.DataFrame(keyword_jobs)
                
                # Combine existing and new jobs, drop duplicates based on URL
                combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['url'], keep='last')
                combined_df.to_csv(csv_filename, index=False)
            else:
                # Create new CSV if it doesn't exist
                pd.DataFrame(keyword_jobs).to_csv(csv_filename, index=False)
            
            print(f"Results saved/updated in {csv_filename}")
            
            # Handle JSON file
            if os.path.exists(json_filename):
                # Read existing JSON
                with open(json_filename, 'r') as f:
                    try:
                        existing_jobs = json.load(f)
                    except json.JSONDecodeError:
                        existing_jobs = []
                
                # Create URL-based dictionary of existing jobs
                existing_jobs_dict = {job['url']: job for job in existing_jobs}
                
                # Update with new jobs
                for job in keyword_jobs:
                    existing_jobs_dict[job['url']] = job
                
                # Convert back to list
                updated_jobs = list(existing_jobs_dict.values())
            else:
                updated_jobs = keyword_jobs
            
            # Save updated JSON
            with open(json_filename, 'w') as f:
                json.dump(updated_jobs, f, indent=2)
            
            # Save an update log
            log_filename = os.path.join(keyword_dir, f"{keyword}_update_log.txt")
            with open(log_filename, 'a') as f:
                f.write(f"Update performed at {timestamp}: Found {len(keyword_jobs)} new jobs\n")
            
    def close(self):
        """Close the Selenium WebDriver"""
        if self.driver is not None:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Error closing Chrome WebDriver: {str(e)}")

def main():
    # Create output directory if it doesn't exist
    if not os.path.exists('output'):
        os.makedirs('output')
    
    # Initialize scraper
    scraper = RemoteJobScraper()
    
    try:
        # Search for each keyword from config
        for keyword in KEYWORDS:
            print(f"Searching for {keyword} jobs...")
            scraper.search_remote_jobs(keyword)
            # Save results for this keyword
            scraper.save_results(keyword)
            # Use delay from config
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
    finally:
        # Clean up
        scraper.close()
    
    print("Job search completed!")

if __name__ == "__main__":
    main()
