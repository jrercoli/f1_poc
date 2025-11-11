import pytz

# Define UTC for scraper comparisons
UTC = pytz.timezone('UTC')
# ISO 8601 con Z
ISO_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

# -------------------------------------------------------------------
# SOURCE CONFIGURATION MAP (F1_SOURCE_CONFIG)
# Date extraction logic for each website.
# -------------------------------------------------------------------
F1_SOURCE_CONFIG = {    
    "https://www.f1technical.net/news/": {
        "source": "GP Blog",
        "driver": "F1 News",
        "date_selector": '',
        "date_attribute": "",
        "date_format": '%H:%M, %d %b',
    }
}

# -------------------------------------------------------------------
F1_SOURCES = [{"url": url, **config} for url, config in F1_SOURCE_CONFIG.items()]

# -------------------------------------------------------------------
# KEYWORDS (F1_KEYWORDS)
# Used to determine the relevance of the articles.
# -------------------------------------------------------------------
F1_KEYWORDS = ['f1', 'fórmula 1', 'formula 1', 'verstappen', 'hamilton', 'alonso', 'sainz', 'wolff',
               'leclerc', 'red bull', 'mercedes', 'ferrari', 'gp', 'gran premio', 'aston martin'
               'mclaren', 'alpine', 'pit stop', 'parrilla', 'carrera', 'colapinto']

# -------------------------------------------------------------------
# User agents for web scarper
# -------------------------------------------------------------------
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'
]
