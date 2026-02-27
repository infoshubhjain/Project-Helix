#-----------------------SHARED SCRAPER UTILITIES-----------------------#
"""
Common utilities and functions for all scrapers to reduce code duplication
"""

import time
import logging
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional, Any
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup

# Shared logger
logger = logging.getLogger(__name__)

# Shared configuration
SCRAPER_CONFIG = {
    'max_retries': 3,
    'retry_delay': 2,
    'request_timeout': 30,
    'rate_limit_delay': 1,
    'user_agent': 'Mozilla/5.0 (compatible; ProjectHelix/1.0; +https://github.com/infoshubhjain/Project-Helix)'
}

class BaseScraper:
    """Base class for all scrapers with common functionality"""
    
    def __init__(self):
        self.session = self._create_robust_session()
        self.events_scraped = 0
        self.errors = []
    
    def _create_robust_session(self) -> requests.Session:
        """Create a requests session with retry logic and proper headers"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=SCRAPER_CONFIG['max_retries'],
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=SCRAPER_CONFIG['retry_delay'],
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        session.headers.update({
            "User-Agent": SCRAPER_CONFIG['user_agent'],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })
        
        return session
    
    def safe_request(self, url: str, method: str = "GET", **kwargs) -> Optional[requests.Response]:
        """Make a safe HTTP request with error handling and logging"""
        try:
            # Add rate limiting
            time.sleep(SCRAPER_CONFIG['rate_limit_delay'])
            
            response = self.session.request(
                method, 
                url, 
                timeout=SCRAPER_CONFIG['request_timeout'],
                **kwargs
            )
            
            if response.status_code == 200:
                logger.debug(f"Successfully fetched: {url}")
                return response
            else:
                logger.warning(f"HTTP {response.status_code} for {url}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout for {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            return None
    
    def validate_event(self, event: Dict[str, Any]) -> bool:
        """Validate that an event has required fields"""
        required_fields = ['summary']
        
        for field in required_fields:
            if field not in event or not event[field]:
                logger.warning(f"Event missing required field '{field}': {event}")
                return False
        
        return True
    
    def parse_time_range(self, time_str: str, event_date: datetime) -> tuple[datetime, datetime]:
        """Parse time range string and return start/end datetime objects"""
        if "All Day" in time_str:
            start_dt = event_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = event_date.replace(hour=23, minute=59, second=59, microsecond=0)
            return start_dt, end_dt
        
        # Normalize string
        time_str = time_str.replace(".", "").lower()
        
        # Regex for range
        range_match = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)?\s*-\s*(\d{1,2}):(\d{2})\s*(am|pm)", time_str)
        if range_match:
            sh, sm, s_mer, eh, em, e_mer = range_match.groups()
            sh, sm, eh, em = int(sh), int(sm), int(eh), int(em)
            
            if not s_mer: s_mer = e_mer  # Inherit suffix if missing
            
            if s_mer == "pm" and sh != 12: sh += 12
            elif s_mer == "am" and sh == 12: sh = 0
            
            if e_mer == "pm" and eh != 12: eh += 12
            elif e_mer == "am" and eh == 12: eh = 0
            
            start_dt = event_date.replace(hour=sh, minute=sm)
            end_dt = event_date.replace(hour=eh, minute=em)
            return start_dt, end_dt
        
        # Single time
        single_match = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)", time_str)
        if single_match:
            sh, sm, s_mer = single_match.groups()
            sh, sm = int(sh), int(sm)
            if s_mer == "pm" and sh != 12: sh += 12
            elif s_mer == "am" and sh == 12: sh = 0
            
            start_dt = event_date.replace(hour=sh, minute=sm)
            end_dt = start_dt + timedelta(hours=1)  # Default 1 hour duration
            return start_dt, end_dt
        
        # Fallback
        start_dt = event_date.replace(hour=12, minute=0)
        end_dt = start_dt + timedelta(hours=1)
        return start_dt, end_dt
    
    def format_datetime(self, dt: datetime) -> str:
        """Format datetime to ISO string with timezone"""
        return dt.replace(tzinfo=ZoneInfo("America/Chicago")).isoformat()
    
    def detect_free_food(self, event_info: Dict[str, Any]) -> Dict[str, Any]:
        """Check if event mentions free food or is at a food-likely location"""
        FREE_FOOD_KEYWORDS = [
            # Single high-confidence words
            "pizza", "lunch", "dinner", "breakfast", "brunch", "snacks", "refreshments",
            "cookies", "donuts", "bagels", "coffee", "meal", "food",
            # Explicit free food mentions
            "free food", "free pizza", "free lunch", "free dinner", "free breakfast",
            "lunch provided", "dinner provided", "food will be served", 
            "snacks provided", "free snacks", "complimentary food", "free meal",
            # Common college food event patterns
            "pizza party", "food included", "lunch included", "dinner included",
            "continental breakfast", "catered", "potluck", "bbq", "cookout",
            "reception with food", "cookies and", "donuts", "bagels", "coffee and",
            # Social/mixer events often have food
            "social hour", "networking lunch", "luncheon", "banquet", "mixer",
            "tailgate", "picnic", "fest", "supper", "banquet", "buffet",
            # Workshop/info session food
            "lunch will be provided", "refreshments will be", "light refreshments",
            "food and drinks"
        ]
        
        # Location tags that often mean food (UIUC/Champaign specific)
        FOOD_LOCATIONS = [
            "Dining Hall", "Restaurant", "Cafe", "Kitchen", "Union Basement", 
            "Coffee Shop", "Bakery", "Grill", "Pub", "Tavern", "Snack Bar"
        ]

        text_to_check = (
            (event_info.get("summary", "") + " " + event_info.get("description", "") + " " + event_info.get("location", ""))
            .lower()
        )
        
        # Check keywords
        for keyword in FREE_FOOD_KEYWORDS:
            if keyword in text_to_check:
                event_info["tag"] = "Free Food 🍕"
                return event_info
                
        # Check locations if summary implies a social event
        summary_lower = event_info.get("summary", "").lower()
        if any(k in summary_lower for k in ["social", "meeting", "workshop", "information", "gathering"]):
            for loc in FOOD_LOCATIONS:
                if loc.lower() in text_to_check:
                    event_info["tag"] = "Free Food 🍕"
                    return event_info
                    
        return event_info
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics"""
        return {
            'events_scraped': self.events_scraped,
            'errors': len(self.errors),
            'error_details': self.errors[-5:] if self.errors else []  # Last 5 errors
        }

def parse_month_to_number(month_str: str) -> int:
    """Convert month name to number"""
    try:
        return datetime.strptime(month_str, "%B").month
    except ValueError:
        return datetime.strptime(month_str, "%b").month

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    return text.strip().replace('\n', ' ').replace('\t', ' ')

def extract_location_info(location_text: str) -> Dict[str, str]:
    """Extract structured information from location text"""
    if not location_text:
        return {'building': '', 'room': '', 'address': ''}
    
    location_text = clean_text(location_text).lower()
    
    # Common UIUC building patterns
    building_patterns = {
        'union': 'Illinois Union',
        'library': 'Library',
        'arc': 'Activities and Recreation Center',
        'crce': 'Campus Recreation Center East',
        'siebel': 'Siebel Center',
        'eb': 'Engineering Hall',
        'nrc': 'Natural Resources Building',
        'lincoln': 'Lincoln Hall',
        'gregory': 'Gregory Hall',
        'english': 'English Building'
    }
    
    result = {'building': '', 'room': '', 'address': location_text}
    
    for pattern, building in building_patterns.items():
        if pattern in location_text:
            result['building'] = building
            break
    
    # Extract room number
    room_match = re.search(r'room\s*(\w+\d*\w*)', location_text)
    if room_match:
        result['room'] = room_match.group(1).upper()
    
    return result
