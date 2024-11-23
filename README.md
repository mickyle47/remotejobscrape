# Remote Jobs Scraper

This Python-based tool scrapes remote job listings from various remote-first companies and search engines.

## Features
- Scrapes remote job listings from multiple sources
- Supports various job search engines
- Exports results to CSV format
- Configurable search parameters

## Setup
1. Install Python 3.8 or higher
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage
Run the main script:
```bash
python main.py
```

The results will be saved in a CSV file in the `output` directory.

## Configuration
You can modify the search parameters in the config.py file:
- Job titles/keywords
- Location preferences
- Experience level
- Job categories

## Note
Please be mindful of the websites' robots.txt files and implement appropriate delays between requests to avoid being blocked.
