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

# Browser settings
BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Target job boards
JOB_BOARDS = {
    'weworkremotely': {
        'enabled': True,
        'base_url': 'https://weworkremotely.com'
    },
    'remoteok': {
        'enabled': True,
        'base_url': 'https://remoteok.com'
    },
    'remote_co': {
        'enabled': True,
        'base_url': 'https://remote.co'
    }
}
