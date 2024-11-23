# Search configuration
KEYWORDS = [
    'python',
    'javascript',
    'react',
    'software-engineer',
    'full-stack',
    'backend',
    'frontend',
    'facebook-ads',
    'meta-ads',
    'social-media-marketing',
    'digital-marketing',
    'paid-social',
    'ppc-specialist'
]

# Job search settings
EXPERIENCE_LEVELS = [
    'entry',
    'mid',
    'senior'
]

# Scraping configuration
DELAY_BETWEEN_REQUESTS = 2  # seconds
MAX_RETRIES = 3
TIMEOUT = 30  # seconds

# Output settings
OUTPUT_DIRECTORY = 'output'
SAVE_AS_CSV = True
SAVE_AS_JSON = True

# Job board configurations
JOB_BOARDS = {
    'WeWorkRemotely': {
        'enabled': True,
        'base_url': 'https://weworkremotely.com/remote-jobs/search?term=',
        'job_selector': '.feature, .job',
        'title_selector': 'span.title',
        'company_selector': 'span.company',
        'location_selector': 'span.region',
        'date_selector': 'time'
    },
    'RemoteOK': {
        'enabled': True,
        'base_url': 'https://remoteok.com/remote-',
        'job_selector': 'tr[data-url]',
        'title_selector': 'h2[itemprop="title"]',
        'company_selector': 'h3[itemprop="name"]',
        'location_selector': '.location',
        'date_selector': 'time[datetime]'
    },
    'Remotive': {
        'enabled': True,
        'base_url': 'https://remotive.com/remote-jobs/search?query=',
        'job_selector': '.job-list-item',
        'title_selector': '.job-title',
        'company_selector': '.company-name',
        'location_selector': '.location',
        'date_selector': '.job-date'
    }
}

# Browser headers for requests
BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Company career pages configuration
COMPANY_CAREER_PAGES = [
    {
        'name': 'GitLab',
        'url': 'https://about.gitlab.com/jobs/',
        'job_selector': '.job',
        'title_selector': '.job-title',
        'location_selector': '.job-location',
        'link_selector': 'a'
    },
    {
        'name': 'Zapier',
        'url': 'https://zapier.com/jobs/',
        'job_selector': '.posting',
        'title_selector': '.posting-title',
        'location_selector': '.posting-location',
        'link_selector': 'a'
    },
    {
        'name': 'Buffer',
        'url': 'https://journey.buffer.com/jobs',
        'job_selector': '.job-posting',
        'title_selector': '.job-title',
        'location_selector': '.job-location',
        'link_selector': 'a'
    },
    {
        'name': 'Automattic',
        'url': 'https://automattic.com/work-with-us/',
        'job_selector': '.job-listing',
        'title_selector': '.job-title',
        'location_selector': '.job-meta',
        'link_selector': 'a'
    }
]

# Remote-first companies and their career pages
REMOTE_COMPANIES = {
    'GitLab': {
        'url': 'https://about.gitlab.com/jobs/',
        'search_selector': '#search',
        'job_selector': '.job',
        'title_selector': '.job-title',
        'location_selector': '.job-location'
    },
    'Zapier': {
        'url': 'https://zapier.com/jobs/',
        'search_selector': '#search-jobs',
        'job_selector': '.posting',
        'title_selector': '.posting-title',
        'location_selector': '.posting-location'
    },
    'Buffer': {
        'url': 'https://journey.buffer.com/jobs',
        'search_selector': '#job-search',
        'job_selector': '.job-posting',
        'title_selector': '.job-title',
        'location_selector': '.job-location'
    },
    'Automattic': {
        'url': 'https://automattic.com/work-with-us/',
        'search_selector': '#search',
        'job_selector': '.job-listing',
        'title_selector': '.job-title',
        'location_selector': '.job-meta'
    },
    'Toptal': {
        'url': 'https://www.toptal.com/careers',
        'search_selector': '#search-jobs',
        'job_selector': '.job-opportunity',
        'title_selector': '.opportunity-title',
        'location_selector': '.opportunity-location'
    },
    'InVision': {
        'url': 'https://www.invisionapp.com/company/careers',
        'search_selector': '#search',
        'job_selector': '.job-posting',
        'title_selector': '.job-title',
        'location_selector': '.job-location'
    },
    'Basecamp': {
        'url': 'https://basecamp.com/about/jobs',
        'search_selector': '#search',
        'job_selector': '.job-listing',
        'title_selector': '.job-title',
        'location_selector': '.job-location'
    },
    'Doist': {
        'url': 'https://doist.com/careers',
        'search_selector': '#search',
        'job_selector': '.job-post',
        'title_selector': '.job-title',
        'location_selector': '.job-location'
    }
}

# Large tech companies that offer remote positions
TECH_COMPANIES = {
    'Microsoft': {
        'url': 'https://careers.microsoft.com/professionals/us/en/search-results',
        'search_selector': '#search-box-input',
        'job_selector': '.job-tile',
        'title_selector': '.job-title',
        'location_selector': '.location'
    },
    'Google': {
        'url': 'https://careers.google.com/jobs/results/',
        'search_selector': 'input[aria-label="Search jobs"]',
        'job_selector': '.gc-card',
        'title_selector': '.gc-card__title',
        'location_selector': '.gc-card__location'
    },
    'Meta': {
        'url': 'https://www.metacareers.com/jobs',
        'search_selector': 'input[type="text"]',
        'job_selector': '.job-results-card',
        'title_selector': '.job-title',
        'location_selector': '.job-location'
    },
    'Apple': {
        'url': 'https://jobs.apple.com/en-us/search',
        'search_selector': '#search-input',
        'job_selector': '.table-row',
        'title_selector': '.table-col-1',
        'location_selector': '.table-col-2'
    }
}
