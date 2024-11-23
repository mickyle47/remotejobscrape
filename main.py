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
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            import platform
            
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            
            # Set up ChromeDriver based on OS
            if platform.system() == 'Windows':
                # Use a specific ChromeDriver version for Windows
                driver_path = ChromeDriverManager(version="114.0.5735.90").install()
            else:
                driver_path = ChromeDriverManager().install()
            
            service = Service(driver_path)
            
            print("Initializing Chrome WebDriver...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("Chrome WebDriver initialized successfully!")
            
        except Exception as e:
            print(f"Error setting up Chrome WebDriver: {str(e)}")
            print("Continuing without Selenium-dependent features...")
            self.driver = None

    def search_remote_jobs(self, keyword):
        """Search for remote jobs across different platforms"""
        try:
            # Search job boards that don't require Selenium
            self.search_we_work_remotely(keyword)
            self.search_remote_ok(keyword)
            self.search_stackoverflow_jobs(keyword)
            self.search_github_jobs(keyword)
            self.search_nodesk_jobs(keyword)
            self.search_justremote_jobs(keyword)
            self.search_remotive_jobs(keyword)
            
            # Only try Selenium-dependent sources if driver is available
            if self.driver:
                self.search_company_jobs(keyword)
                self.search_remote_co(keyword)
        except Exception as e:
            print(f"Error during job search: {str(e)}")
            
    def search_we_work_remotely(self, keyword):
        """Search We Work Remotely for jobs"""
        try:
            url = f"https://weworkremotely.com/remote-jobs/search?term={keyword}"
            response = requests.get(url, headers=BROWSER_HEADERS)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for job in soup.select('li.feature'):
                title = job.select_one('.title')
                company = job.select_one('.company')
                date = job.select_one('.date')
                
                if title and company:
                    self.jobs.append({
                        'title': title.text.strip(),
                        'company': company.text.strip(),
                        'date_posted': date.text.strip() if date else '',
                        'source': 'We Work Remotely',
                        'url': f"https://weworkremotely.com{job.select_one('a')['href']}" if job.select_one('a') else '',
                    })
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        except Exception as e:
            print(f"Error scraping We Work Remotely: {str(e)}")
            
    def search_remote_ok(self, keyword):
        """Search RemoteOK for jobs"""
        try:
            url = f"https://remoteok.com/remote-{keyword}-jobs"
            response = requests.get(url, headers=BROWSER_HEADERS)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for job in soup.select('tr.job'):
                title = job.select_one('.company h2')
                company = job.select_one('.company h3')
                date = job.select_one('.time')
                
                if title and company:
                    self.jobs.append({
                        'title': title.text.strip(),
                        'company': company.text.strip(),
                        'date_posted': date.text.strip() if date else '',
                        'source': 'RemoteOK',
                        'url': f"https://remoteok.com{job['data-url']}" if 'data-url' in job.attrs else '',
                    })
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        except Exception as e:
            print(f"Error scraping RemoteOK: {str(e)}")
            
    def search_remotive_jobs(self, keyword):
        """Search Remotive for jobs"""
        try:
            url = f"https://remotive.com/remote-jobs/search?term={keyword}"
            response = requests.get(url, headers=BROWSER_HEADERS)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for job in soup.select('.job-list-item'):
                title = job.select_one('.position')
                company = job.select_one('.company')
                date = job.select_one('.job-date')
                
                if title and company:
                    self.jobs.append({
                        'title': title.text.strip(),
                        'company': company.text.strip(),
                        'date_posted': date.text.strip() if date else '',
                        'source': 'Remotive',
                        'url': f"https://remotive.com{job.select_one('a')['href']}" if job.select_one('a') else '',
                    })
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        except Exception as e:
            print(f"Error scraping Remotive: {str(e)}")
            
    def search_company_jobs(self, keyword):
        """Search for jobs directly from company career pages"""
        company_job_boards = {
            'Microsoft': 'https://careers.microsoft.com/us/en/search-results',
            'Google': 'https://careers.google.com/jobs/results/',
            'Amazon': 'https://www.amazon.jobs/en/search',
            'Meta': 'https://www.metacareers.com/jobs/',
            'Apple': 'https://jobs.apple.com/en-us/search',
            'Netflix': 'https://jobs.netflix.com/search',
            'Twitter': 'https://careers.twitter.com/en/roles',
            'LinkedIn': 'https://careers.linkedin.com/jobs',
            'Salesforce': 'https://careers.salesforce.com/jobs',
            'Adobe': 'https://careers.adobe.com/us/en/search-results'
        }
        
        for company, url in company_job_boards.items():
            try:
                if self.driver is None:
                    print(f"Skipping {company} jobs as Selenium WebDriver is not available")
                    continue
                
                print(f"Searching {company} jobs...")
                self.driver.get(url)
                time.sleep(DELAY_BETWEEN_REQUESTS)
                
                # Search for keyword if search box is available
                try:
                    search_box = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[type='search']"))
                    )
                    search_box.send_keys(keyword)
                    search_box.submit()
                    time.sleep(DELAY_BETWEEN_REQUESTS)
                except:
                    print(f"Could not find search box on {company} careers page")
                
                # Extract job listings
                job_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-job-id], .job-card, .job-listing")
                for job in job_elements[:10]:  # Limit to first 10 results per company
                    try:
                        title = job.find_element(By.CSS_SELECTOR, "h2, h3, .job-title").text.strip()
                        location = job.find_element(By.CSS_SELECTOR, ".location, .job-location").text.strip()
                        url = job.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                        
                        if "remote" in location.lower() or "hybrid" in location.lower():
                            self.jobs.append({
                                'title': title,
                                'company': company,
                                'location': location,
                                'source': f"{company} Careers",
                                'url': url,
                                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                                'keyword': keyword,
                                'is_company_direct': True
                            })
                    except Exception as e:
                        print(f"Error extracting job from {company}: {str(e)}")
                
            except Exception as e:
                print(f"Error searching {company} jobs: {str(e)}")

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

    def search_stackoverflow_jobs(self, keyword):
        """Scrape jobs from Stack Overflow Jobs"""
        try:
            url = f"https://stackoverflow.com/jobs/feed?r=true&q={keyword}"
            headers = BROWSER_HEADERS
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'xml')
                items = soup.find_all('item')
                
                for item in items:
                    title = item.title.text if item.title else ''
                    company = item.find('a10:author').find('a10:name').text if item.find('a10:author') else ''
                    location = item.location.text if item.location else 'Remote'
                    
                    self.jobs.append({
                        'title': title,
                        'company': company,
                        'location': location,
                        'source': 'Stack Overflow',
                        'url': item.link.text if item.link else '',
                        'date_posted': item.pubDate.text if item.pubDate else datetime.now().strftime('%Y-%m-%d'),
                        'keyword': keyword
                    })
        except Exception as e:
            print(f"Error scraping Stack Overflow Jobs: {str(e)}")
            
    def search_github_jobs(self, keyword):
        """Scrape jobs from GitHub Jobs"""
        try:
            url = f"https://jobs.github.com/positions.json?description={keyword}&location=remote"
            headers = BROWSER_HEADERS
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                jobs_data = response.json()
                for job in jobs_data:
                    self.jobs.append({
                        'title': job.get('title', ''),
                        'company': job.get('company', ''),
                        'location': job.get('location', 'Remote'),
                        'source': 'GitHub Jobs',
                        'url': job.get('url', ''),
                        'date_posted': job.get('created_at', datetime.now().strftime('%Y-%m-%d')),
                        'keyword': keyword
                    })
        except Exception as e:
            print(f"Error scraping GitHub Jobs: {str(e)}")
            
    def search_nodesk_jobs(self, keyword):
        """Scrape jobs from NoDesk"""
        try:
            url = f"https://nodesk.co/remote-jobs/?search={keyword}"
            headers = BROWSER_HEADERS
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_listings = soup.find_all('article', class_='job')
                
                for job in job_listings:
                    title_elem = job.find('h2', class_='job-title')
                    company_elem = job.find('span', class_='company')
                    
                    if title_elem and company_elem:
                        title = title_elem.text.strip()
                        company = company_elem.text.strip()
                        url = title_elem.find('a')['href'] if title_elem.find('a') else ''
                        
                        self.jobs.append({
                            'title': title,
                            'company': company,
                            'location': 'Remote',
                            'source': 'NoDesk',
                            'url': url,
                            'date_posted': datetime.now().strftime('%Y-%m-%d'),
                            'keyword': keyword
                        })
        except Exception as e:
            print(f"Error scraping NoDesk: {str(e)}")
            
    def search_justremote_jobs(self, keyword):
        """Scrape jobs from JustRemote"""
        try:
            url = f"https://justremote.co/remote-{keyword}-jobs"
            headers = BROWSER_HEADERS
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_listings = soup.find_all('div', class_='job-list-item')
                
                for job in job_listings:
                    title_elem = job.find('h3', class_='job-title')
                    company_elem = job.find('div', class_='company-name')
                    
                    if title_elem and company_elem:
                        title = title_elem.text.strip()
                        company = company_elem.text.strip()
                        url = 'https://justremote.co' + title_elem.find('a')['href'] if title_elem.find('a') else ''
                        
                        self.jobs.append({
                            'title': title,
                            'company': company,
                            'location': 'Remote',
                            'source': 'JustRemote',
                            'url': url,
                            'date_posted': datetime.now().strftime('%Y-%m-%d'),
                            'keyword': keyword
                        })
        except Exception as e:
            print(f"Error scraping JustRemote: {str(e)}")

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
