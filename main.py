import os
import time
import json
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from config import KEYWORDS, BROWSER_HEADERS, DELAY_BETWEEN_REQUESTS, REMOTE_COMPANIES, TECH_COMPANIES, JOB_BOARDS, COMPANY_CAREER_PAGES
from urllib.parse import urljoin
from logging_config import logger
from dateutil import parser

def log_and_print(message, level="info", error=None):
    """Helper function to log and print messages with improved error handling"""
    try:
        if level == "info":
            logger.info(message)
            print(f"INFO: {message}")
        elif level == "error":
            error_msg = f"{message}"
            if error:
                error_msg += f"\nError details: {str(error)}"
                logger.error(error_msg, exc_info=True)  # Include stack trace for errors
            else:
                logger.error(error_msg)
            print(f"ERROR: {message}")
        elif level == "warning":
            warning_msg = f"{message}"
            if error:
                warning_msg += f"\nWarning details: {str(error)}"
            logger.warning(warning_msg)
            print(f"WARNING: {message}")
        elif level == "debug":
            logger.debug(message)
            # Don't print debug messages to console to keep it clean
    except Exception as e:
        # Fallback if logging fails
        print(f"Logging error: {str(e)}")
        print(f"{level.upper()}: {message}")

class RemoteJobScraper:
    def __init__(self):
        """Initialize the scraper"""
        try:
            log_and_print("Initializing RemoteJobScraper")
            self.jobs = []
            self.seen_jobs = set()  # Track seen jobs to prevent duplicates
            self.driver = None
            self.setup_selenium()
        except Exception as e:
            log_and_print("Error initializing RemoteJobScraper", "error", e)
            raise
        
    def add_job(self, job_data):
        """Add a job to the list if it's not a duplicate"""
        # Create a unique identifier for the job
        job_id = f"{job_data['title'].lower()}|{job_data['company'].lower()}"
        
        if job_id not in self.seen_jobs:
            self.seen_jobs.add(job_id)
            self.jobs.append(job_data)
            # Only log at debug level to avoid cluttering the output
            logger.debug(f"Added: {job_data['title']} at {job_data['company']}")
            
    def setup_selenium(self):
        """Setup Selenium WebDriver with Chrome"""
        try:
            log_and_print("Setting up Chrome WebDriver")
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-software-rasterizer")
            
            # Get Chrome version
            import winreg
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                version = winreg.QueryValueEx(key, "version")[0]
                log_and_print(f"Detected Chrome version: {version}")
                winreg.CloseKey(key)
            except Exception as e:
                log_and_print(f"Could not detect Chrome version from registry: {str(e)}", "warning", e)
                version = None
            
            try:
                if version:
                    # Try installing specific version first
                    log_and_print(f"Attempting to install ChromeDriver for Chrome {version}")
                    driver_path = ChromeDriverManager(version=version).install()
                else:
                    # If version detection failed, try latest
                    log_and_print("Installing latest ChromeDriver version")
                    driver_path = ChromeDriverManager().install()
                
                service = Service(driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                log_and_print("Chrome WebDriver initialized successfully!")
                
            except Exception as e:
                log_and_print(f"Error installing ChromeDriver: {str(e)}", "error", e)
                # Try one more time with latest version
                try:
                    log_and_print("Attempting to install latest ChromeDriver version")
                    driver_path = ChromeDriverManager().install()
                    service = Service(driver_path)
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    log_and_print("Chrome WebDriver initialized successfully with latest version!")
                except Exception as e:
                    log_and_print(f"Failed to initialize Chrome WebDriver: {str(e)}", "error", e)
                    self.driver = None
                    raise
            
        except Exception as e:
            log_and_print(f"Error setting up Chrome WebDriver: {str(e)}", "error", e)
            log_and_print("Continuing without Selenium-dependent features...")
            self.driver = None

    def search_remote_jobs(self, keyword):
        """Search for remote jobs across different platforms"""
        try:
            log_and_print(f"Searching for remote jobs with keyword: {keyword}")
            # Clear previous results for this keyword
            self.jobs = []
            self.seen_jobs = set()
            
            # First try company career pages if Selenium is available
            if self.driver:
                log_and_print(f"Searching company career pages for '{keyword}'...")
                self.search_company_jobs(keyword)
            
            # Then search job boards
            log_and_print(f"Searching job boards for '{keyword}'...")
            self.search_we_work_remotely(keyword)
            self.search_remote_ok(keyword)
            self.search_remotive_jobs(keyword)
            
        except Exception as e:
            log_and_print(f"Error during job search: {str(e)}", "error", e)
            
    def search_company_jobs(self, keyword):
        """Search for jobs directly from company career pages"""
        company_job_boards = {
            'Microsoft': {
                'url': 'https://careers.microsoft.com/professionals/us/en/search-results',
                'search_selector': '#search-box-input',
                'job_selector': '.job-tile',
                'title_selector': '.job-title',
                'company': 'Microsoft',
                'location_selector': '.location'
            },
            'Google': {
                'url': 'https://careers.google.com/jobs/results/',
                'search_selector': 'input[aria-label="Search jobs"]',
                'job_selector': '.gc-card',
                'title_selector': '.gc-card__title',
                'company': 'Google',
                'location_selector': '.gc-card__location'
            },
            'Meta': {
                'url': 'https://www.metacareers.com/jobs',
                'search_selector': 'input[type="text"]',
                'job_selector': '.job-results-card',
                'title_selector': '.job-title',
                'company': 'Meta',
                'location_selector': '.job-location'
            },
            'Apple': {
                'url': 'https://jobs.apple.com/en-us/search',
                'search_selector': '#search-input',
                'job_selector': '.table-row',
                'title_selector': '.table-col-1',
                'company': 'Apple',
                'location_selector': '.table-col-2'
            }
        }
        
        if self.driver is None:
            log_and_print("Skipping company jobs as Selenium WebDriver is not available", "warning")
            return
            
        for company, config in company_job_boards.items():
            try:
                log_and_print(f"Searching {company} jobs...")
                self.driver.get(config['url'])
                time.sleep(DELAY_BETWEEN_REQUESTS * 2)  # Extra delay for company sites
                
                # Search for keyword
                try:
                    search_box = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, config['search_selector']))
                    )
                    search_box.clear()
                    search_box.send_keys('remote ' + keyword)  # Add 'remote' to search
                    search_box.send_keys(Keys.RETURN)
                    time.sleep(DELAY_BETWEEN_REQUESTS * 2)
                except Exception as e:
                    log_and_print(f"Could not search on {company}: {str(e)}", "error", e)
                    continue
                
                # Wait for job listings
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, config['job_selector']))
                    )
                except Exception as e:
                    log_and_print(f"No jobs found for {company}: {str(e)}", "error", e)
                    continue
                
                # Extract jobs
                jobs = self.driver.find_elements(By.CSS_SELECTOR, config['job_selector'])
                log_and_print(f"Found {len(jobs)} potential jobs at {company}")
                
                for job in jobs[:10]:  # Limit to first 10 jobs per company
                    try:
                        title = job.find_element(By.CSS_SELECTOR, config['title_selector']).text.strip()
                        location = job.find_element(By.CSS_SELECTOR, config['location_selector']).text.strip()
                        
                        # Check if job is remote
                        if any(term in location.lower() for term in ['remote', 'anywhere', 'global', 'worldwide']):
                            job_url = job.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                            
                            job_data = {
                                'title': title,
                                'company': config['company'],
                                'location': location,
                                'source': f"{company} Careers",
                                'url': job_url,
                                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                                'is_company_direct': True  # Mark as direct company posting
                            }
                            
                            self.add_job(job_data)
                            log_and_print(f"Added job: {title} at {company}")
                            
                    except Exception as e:
                        log_and_print(f"Error extracting job from {company}: {str(e)}", "error", e)
                        continue
                        
            except Exception as e:
                log_and_print(f"Error searching {company} jobs: {str(e)}", "error", e)
                continue
                
    def scrape_jobs(self, keywords):
        """Main method to scrape jobs from all sources"""
        log_and_print(f"Starting job scraping for keywords: {keywords}")
        all_jobs = []
        
        # Scrape job boards first
        for board_name, board_config in JOB_BOARDS.items():
            if board_config['enabled']:
                try:
                    log_and_print(f"Scraping {board_name}...")
                    for keyword in keywords:
                        jobs = self.scrape_job_board(board_name, board_config, keyword)
                        all_jobs.extend(jobs)
                        time.sleep(DELAY_BETWEEN_REQUESTS)
                except Exception as e:
                    log_and_print(f"Error scraping {board_name}: {str(e)}", "error", e)
        
        # Then scrape company career pages if Selenium is available
        if self.driver:
            # Scrape remote-first companies
            for company, config in REMOTE_COMPANIES.items():
                try:
                    log_and_print(f"Scraping {company}...")
                    jobs = self.scrape_company_jobs(company, config, keywords)
                    all_jobs.extend(jobs)
                except Exception as e:
                    log_and_print(f"Error scraping {company}: {str(e)}", "error", e)
            
            # Scrape tech companies
            for company, config in TECH_COMPANIES.items():
                try:
                    log_and_print(f"Scraping {company}...")
                    jobs = self.scrape_company_jobs(company, config, keywords)
                    all_jobs.extend(jobs)
                except Exception as e:
                    log_and_print(f"Error scraping {company}: {str(e)}", "error", e)
            
            # Scrape company career pages
            try:
                log_and_print("Scraping company career pages...")
                jobs = self.scrape_company_career_pages(keywords)
                all_jobs.extend(jobs)
            except Exception as e:
                log_and_print(f"Error scraping company career pages: {str(e)}", "error", e)
        else:
            log_and_print("Skipping company career pages - Selenium not available", "warning")
        
        log_and_print(f"Completed scraping. Found {len(all_jobs)} total jobs")
        return all_jobs
    
    def scrape_job_board(self, board_name, board_config, keyword):
        """Scrape a specific job board for a keyword"""
        try:
            # Construct URL
            url = board_config['base_url'] + keyword
            log_and_print(f"Accessing URL: {url}")
            
            # Get page content
            response = requests.get(url, headers=BROWSER_HEADERS)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all job listings
            jobs = soup.select(board_config['job_selector'])
            log_and_print(f"Found {len(jobs)} job listings on {board_name}")
            
            # Process each job
            for job in jobs:
                try:
                    # Extract job details
                    title = job.select_one(board_config['title_selector']).text.strip()
                    company = job.select_one(board_config['company_selector']).text.strip()
                    
                    # Get the direct job posting URL
                    job_url = self.get_job_url(job, board_name)
                    if not job_url:  # Skip if no valid URL found
                        continue
                    
                    try:
                        location = job.select_one(board_config['location_selector']).text.strip()
                    except (AttributeError, KeyError):
                        location = "Remote"
                    
                    try:
                        date_element = job.select_one(board_config['date_selector'])
                        if date_element:
                            if date_element.has_attr('datetime'):
                                date_posted = date_element['datetime']
                            else:
                                date_posted = date_element.text.strip()
                        else:
                            date_posted = datetime.now().strftime('%Y-%m-%d')
                    except (AttributeError, KeyError):
                        date_posted = datetime.now().strftime('%Y-%m-%d')
                    
                    # Create job dictionary
                    job_data = {
                        'title': title,
                        'company': company,
                        'location': location,
                        'date_posted': date_posted,
                        'url': job_url,
                        'source': board_name,
                        'keyword': keyword
                    }
                    
                    self.add_job(job_data)
                    log_and_print(f"Added job: {title} at {company} - URL: {job_url}")
                    
                except Exception as e:
                    log_and_print(f"Error parsing job from {board_name}: {str(e)}", "error", e)
                    continue
            
            log_and_print(f"Successfully scraped {len(jobs)} jobs from {board_name} for keyword '{keyword}'")
            
        except Exception as e:
            log_and_print(f"Error scraping {board_name}: {str(e)}", "error", e)
        
        return self.jobs
    
    def get_job_url(self, job_element, board_name):
        """Get the actual job posting URL"""
        try:
            if board_name == 'WeWorkRemotely':
                # Find the link that specifically points to a job listing
                # Job URLs contain '/remote-jobs/' in their path
                link = job_element.find('a', href=lambda x: x and '/remote-jobs/' in x)
                if link and link['href']:
                    return f"https://weworkremotely.com{link['href']}"
            
            elif board_name == 'RemoteOK':
                # RemoteOK job URLs are in the data-url attribute and start with /remote-jobs/
                url = job_element.get('data-url', '')
                if url and url.startswith('/remote-jobs/'):
                    return f"https://remoteok.com{url}"
            
            elif board_name == 'Remotive':
                # Remotive job URLs contain /remote-jobs/ in their path
                link = job_element.find('a', href=lambda x: x and '/remote-jobs/' in x)
                if link and link['href']:
                    return f"https://remotive.com{link['href']}"
            
            # If all else fails, look for any link containing job-specific patterns
            any_link = job_element.find('a', href=lambda x: x and (
                '/remote-jobs/' in x or 
                '/job/' in x or 
                '/position/' in x
            ))
            if any_link and any_link['href']:
                href = any_link['href']
                if href.startswith('http'):
                    return href
                elif board_name == 'WeWorkRemotely':
                    return f"https://weworkremotely.com{href}"
                elif board_name == 'RemoteOK':
                    return f"https://remoteok.com{href}"
                elif board_name == 'Remotive':
                    return f"https://remotive.com{href}"
            
            log_and_print("Could not find job posting URL in element", "warning")
            return None
            
        except Exception as e:
            log_and_print(f"Error getting job URL: {str(e)}", "error")
            return None
    
    def scrape_company_jobs(self, company_name, company_config, keywords):
        """Scrape jobs from a company's career page"""
        jobs = []
        if not self.driver:
            return jobs
        
        try:
            self.driver.get(company_config['url'])
            time.sleep(2)  # Wait for page to load
            
            # Try to find and use search if available
            try:
                search = self.driver.find_element(By.CSS_SELECTOR, company_config['search_selector'])
                for keyword in keywords:
                    search.clear()
                    search.send_keys(keyword)
                    search.send_keys(Keys.RETURN)
                    time.sleep(2)  # Wait for results
                    
                    # Find all job listings
                    job_elements = self.driver.find_elements(By.CSS_SELECTOR, company_config['job_selector'])
                    
                    for job_element in job_elements:
                        try:
                            title = job_element.find_element(By.CSS_SELECTOR, company_config['title_selector']).text
                            location = job_element.find_element(By.CSS_SELECTOR, company_config['location_selector']).text
                            
                            # Create unique job identifier
                            job_id = f"{company_name}:{title}:{location}"
                            
                            if job_id not in self.seen_jobs and 'remote' in location.lower():
                                self.seen_jobs.add(job_id)
                                job = {
                                    'title': title,
                                    'company': company_name,
                                    'location': location,
                                    'date': datetime.now().strftime('%Y-%m-%d'),
                                    'url': job_element.get_attribute('href') or company_config['url'],
                                    'is_company_direct': True
                                }
                                jobs.append(job)
                        except Exception as e:
                            log_and_print(f"Error extracting job details from {company_name}: {str(e)}", "error", e)
                            continue
                        
            except Exception as e:
                log_and_print(f"Error searching jobs at {company_name}: {str(e)}", "error", e)
        
        except Exception as e:
            log_and_print(f"Error accessing {company_name} career page: {str(e)}", "error", e)
        
        log_and_print(f"Found {len(jobs)} jobs from {company_name}")
        return jobs
    
    def scrape_company_career_pages(self, keywords):
        """Scrape jobs from company career pages"""
        if not self.driver:
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    log_and_print(f"Attempt {retry_count + 1} to initialize Selenium for company career pages")
                    self.setup_selenium()
                    if self.driver:
                        break
                except Exception as e:
                    log_and_print(f"Retry {retry_count + 1} failed: {str(e)}", "error", e)
                    retry_count += 1
                    time.sleep(2)  # Wait before retrying
            
            if not self.driver:
                log_and_print("All attempts to initialize Selenium failed. Skipping company career pages.", "warning")
                return []

        log_and_print("Scraping company career pages...")
        all_jobs = []
        
        for company in COMPANY_CAREER_PAGES:
            try:
                log_and_print(f"Scraping {company['name']} career page")
                url = company['url']
                self.driver.get(url)
                time.sleep(3)  # Wait for JavaScript to load
                
                # Use company-specific selectors
                job_elements = self.driver.find_elements(By.CSS_SELECTOR, company.get('job_selector', '.job-listing'))
                
                for job in job_elements:
                    try:
                        title = job.find_element(By.CSS_SELECTOR, company.get('title_selector', '.job-title')).text
                        
                        # Check if job matches any keyword
                        if any(keyword.lower() in title.lower() for keyword in keywords):
                            job_data = {
                                'title': title,
                                'company': company['name'],
                                'url': job.find_element(By.CSS_SELECTOR, company.get('link_selector', 'a')).get_attribute('href'),
                                'location': job.find_element(By.CSS_SELECTOR, company.get('location_selector', '.location')).text,
                                'source': f"{company['name']} Careers",
                                'is_company_direct': True
                            }
                            all_jobs.append(job_data)
                            log_and_print(f"Added job: {title} at {company['name']}")
                    
                    except Exception as e:
                        log_and_print(f"Error parsing job from {company['name']}: {str(e)}", "error", e)
                        continue
                
                time.sleep(DELAY_BETWEEN_REQUESTS)
            
            except Exception as e:
                log_and_print(f"Error scraping {company['name']} career page: {str(e)}", "error", e)
                continue
        
        return all_jobs
    
    def scrape_job_boards(self, keywords):
        """Scrape job boards"""
        job_boards = {
            'We Work Remotely': self.search_we_work_remotely,
            'RemoteOK': self.search_remote_ok,
            'Remotive': self.search_remotive_jobs
        }
        
        all_jobs = {}
        
        for board, method in job_boards.items():
            try:
                log_and_print(f"Scraping {board}...")
                jobs = method(keywords)
                all_jobs[board] = jobs
            except Exception as e:
                log_and_print(f"Error scraping {board}: {str(e)}", "error", e)
        
        return all_jobs
    
    def parse_weworkremotely_job(self, job_element):
        """Parse a job listing from We Work Remotely"""
        try:
            if not job_element:
                logger.warning("Empty job element received")
                return None

            # Extract job details with None checks
            title_element = job_element.find('span', class_='title')
            title = title_element.text.strip() if title_element and hasattr(title_element, 'text') else "Unknown Title"
            
            company_element = job_element.find('span', class_='company')
            company = company_element.text.strip() if company_element and hasattr(company_element, 'text') else "Unknown Company"
            
            link_element = job_element.find('a', href=True)
            link = f"https://weworkremotely.com{link_element['href']}" if link_element and 'href' in link_element.attrs else None
            
            region_element = job_element.find('span', class_='region')
            region = region_element.text.strip() if region_element and hasattr(region_element, 'text') else "Remote"
            
            # Create job object only if we have minimum required info
            if title != "Unknown Title" or company != "Unknown Company":
                job = {
                    'title': title,
                    'company': company,
                    'location': region,
                    'url': link,
                    'source': 'We Work Remotely'
                }
                return job
            else:
                logger.warning("Skipping job due to missing required information")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing job from weworkremotely: {str(e)}")
            return None
    
    def search_we_work_remotely(self, keyword):
        """Search We Work Remotely for jobs"""
        try:
            log_and_print(f"Searching We Work Remotely for keyword: {keyword}")
            url = f"https://weworkremotely.com/remote-jobs/search?term={keyword}"
            response = requests.get(url, headers=BROWSER_HEADERS)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for job in soup.select('li.feature'):
                job_data = self.parse_weworkremotely_job(job)
                if job_data:
                    self.add_job(job_data)
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        except Exception as e:
            log_and_print(f"Error scraping We Work Remotely: {str(e)}", "error", e)
            
    def search_remote_ok(self, keyword):
        """Search RemoteOK for jobs"""
        try:
            log_and_print(f"Searching RemoteOK for keyword: {keyword}")
            url = f"https://remoteok.com/remote-{keyword}-jobs"
            response = requests.get(url, headers=BROWSER_HEADERS)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for job in soup.select('tr.job'):
                title = job.select_one('.company h2')
                company = job.select_one('.company h3')
                date = job.select_one('.time')
                
                if title and company:
                    job_data = {
                        'title': title.text.strip(),
                        'company': company.text.strip(),
                        'date_posted': date.text.strip() if date else '',
                        'source': 'RemoteOK',
                        'url': self.extract_job_url(job, 'https://remoteok.com'),
                        'is_company_direct': False
                    }
                    self.add_job(job_data)
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        except Exception as e:
            log_and_print(f"Error scraping RemoteOK: {str(e)}", "error", e)
            
    def search_remotive_jobs(self, keyword):
        """Search Remotive for jobs"""
        try:
            log_and_print(f"Searching Remotive for keyword: {keyword}")
            url = f"https://remotive.com/remote-jobs/search?term={keyword}"
            response = requests.get(url, headers=BROWSER_HEADERS)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for job in soup.select('.job-list-item'):
                title = job.select_one('.position')
                company = job.select_one('.company')
                date = job.select_one('.job-date')
                
                if title and company:
                    job_data = {
                        'title': title.text.strip(),
                        'company': company.text.strip(),
                        'date_posted': date.text.strip() if date else '',
                        'source': 'Remotive',
                        'url': f"https://remotive.com{job.select_one('a')['href']}" if job.select_one('a') else '',
                        'is_company_direct': False
                    }
                    self.add_job(job_data)
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        except Exception as e:
            log_and_print(f"Error scraping Remotive: {str(e)}", "error", e)
            
    def save_results(self, keyword):
        """Save scraped jobs to CSV and JSON files, organized by keyword and append to existing files"""
        log_and_print(f"Saving results for keyword: {keyword}")
        if not os.path.exists('output'):
            os.makedirs('output')
        
        # Create a directory for this keyword if it doesn't exist
        keyword_dir = os.path.join('output', keyword)
        if not os.path.exists(keyword_dir):
            os.makedirs(keyword_dir)
        
        # Filter jobs for this keyword
        keyword_jobs = [job for job in self.jobs if 'keyword' in job and job['keyword'] == keyword]
        
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
            
            log_and_print(f"Results saved/updated in {csv_filename}")
            
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
                log_and_print("Closing Chrome WebDriver...")
                self.driver.quit()
                log_and_print("Chrome WebDriver closed successfully!")
            except Exception as e:
                log_and_print(f"Error closing Chrome WebDriver: {str(e)}", "error", e)

    def get_application_link(self, job_url, source):
        """Extract the actual application link from a job posting page"""
        try:
            if not self.driver:
                return job_url
                
            # Visit the job page
            self.driver.get(job_url)
            time.sleep(2)  # Wait for page to load
            
            # Common application button/link patterns
            apply_selectors = [
                'a[href*="apply"]',
                'a[href*="application"]',
                'a[href*="job-details"]',
                'button[contains(text(), "Apply")]',
                '.apply-button',
                '#apply-button',
                '.application-btn',
                '.job-apply',
                'a.btn-apply',
                'a[data-automation="job-detail-apply"]'
            ]
            
            # Try each selector
            for selector in apply_selectors:
                try:
                    apply_element = WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    apply_url = apply_element.get_attribute('href')
                    if apply_url and apply_url.startswith('http'):
                        log_and_print(f"Found application link: {apply_url}", "debug")
                        return apply_url
                except:
                    continue
            
            # If no apply button found, try to find any link containing "apply" or "application"
            try:
                links = self.driver.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    href = link.get_attribute('href')
                    if href and any(term in href.lower() for term in ['apply', 'application']):
                        return href
            except:
                pass
                
            return job_url
            
        except Exception as e:
            log_and_print(f"Error getting application link: {str(e)}", "error", e)
            return job_url

def main():
    # Create output directory if it doesn't exist
    if not os.path.exists('output'):
        os.makedirs('output')
    
    # Initialize scraper
    scraper = RemoteJobScraper()
    
    try:
        # Search for each keyword from config
        for keyword in KEYWORDS:
            log_and_print(f"Searching for {keyword} jobs...")
            scraper.search_remote_jobs(keyword)
            # Save results for this keyword
            scraper.save_results(keyword)
            # Use delay from config
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
    finally:
        # Clean up
        scraper.close()
    
    log_and_print("Job search completed!")

if __name__ == "__main__":
    main()
