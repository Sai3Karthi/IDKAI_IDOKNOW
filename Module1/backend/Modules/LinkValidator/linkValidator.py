#!/usr/bin/env python3
"""
Core Link Validator - Clean and minimal
URL safety checker with content scraping functionality.
"""

import requests
import json
import base64
import time
import urllib.parse
from typing import Dict
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

class LinkValidator:
    """Core link validator with URL safety checking and content scraping."""
    
    def __init__(self, google_api_key: str, virustotal_api_key: str):
        """Initialize with API keys."""
        self.google_api_key = google_api_key
        self.virustotal_api_key = virustotal_api_key
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'LinkValidator/1.0'})
        
        # Rate limiting
        self.last_google_request = 0
        self.last_virustotal_request = 0
    
    def sanitize_url(self, url: str) -> str:
        """Sanitize and validate URL format."""
        if not url or not isinstance(url, str):
            raise ValueError("URL must be a non-empty string")
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        parsed = urllib.parse.urlparse(url)
        if not parsed.netloc:
            raise ValueError("Invalid URL")
        
        return urllib.parse.urlunparse(parsed)
    
    def validate_url_pattern(self, url: str) -> bool:
        """Check for suspicious URL patterns."""
        suspicious_patterns = [
            r'bit\.ly|tinyurl|t\.co',  # URL shorteners
            r'\d+\.\d+\.\d+\.\d+',    # Direct IP addresses
            r'[0-9a-f]{32,}',         # Long hex strings
        ]
        
        url_lower = url.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, url_lower):
                return False
        return True
    
    def check_google_safe_browsing(self, url: str) -> Dict:
        """Check URL against Google Safe Browsing API."""
        # Rate limiting
        current_time = time.time()
        if current_time - self.last_google_request < 1.0:
            time.sleep(1.0 - (current_time - self.last_google_request))
        self.last_google_request = time.time()
        
        endpoint = f'https://safebrowsing.googleapis.com/v4/threatMatches:find?key={self.google_api_key}'
        payload = {
            "client": {"clientId": "LinkValidator", "clientVersion": "1.0"},
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}]
            }
        }
        
        try:
            response = self.session.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()
            threats = response.json().get('matches', [])
            return {'safe': len(threats) == 0, 'error': None}
        except Exception as e:
            return {'safe': None, 'error': str(e)}
    
    def check_virustotal(self, url: str) -> Dict:
        """Check URL against VirusTotal API."""
        # Rate limiting
        current_time = time.time()
        if current_time - self.last_virustotal_request < 15.0:
            time.sleep(15.0 - (current_time - self.last_virustotal_request))
        self.last_virustotal_request = time.time()
        
        headers = {'x-apikey': self.virustotal_api_key}
        
        try:
            url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
            check_url = f'https://www.virustotal.com/api/v3/urls/{url_id}'
            response = self.session.get(check_url, headers=headers, timeout=30)
            
            if response.status_code == 404:
                # Submit for analysis
                submit_response = self.session.post(
                    'https://www.virustotal.com/api/v3/urls',
                    headers=headers,
                    data={'url': url},
                    timeout=30
                )
                submit_response.raise_for_status()
                time.sleep(5)
                response = self.session.get(check_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                stats = response.json()['data']['attributes']['last_analysis_stats']
                malicious = stats.get('malicious', 0)
                suspicious = stats.get('suspicious', 0)
                return {'safe': malicious == 0 and suspicious == 0, 'error': None}
            else:
                return {'safe': None, 'error': f'API error: {response.status_code}'}
                
        except Exception as e:
            return {'safe': None, 'error': str(e)}
    
    def validate_url(self, url: str) -> Dict:
        """Main validation function."""
        try:
            sanitized_url = self.sanitize_url(url)
            pattern_safe = self.validate_url_pattern(sanitized_url)
            
            google_result = self.check_google_safe_browsing(sanitized_url)
            virustotal_result = self.check_virustotal(sanitized_url)
            
            # Determine safety
            checks = [google_result.get('safe'), virustotal_result.get('safe')]
            
            if False in checks:
                overall_safe = False
            elif None in checks:
                overall_safe = pattern_safe
            else:
                overall_safe = True and pattern_safe
            
            return {
                'url': sanitized_url,
                'safe': overall_safe,
                'google': google_result,
                'virustotal': virustotal_result
            }
            
        except Exception as e:
            return {'url': url, 'safe': False, 'error': str(e)}
    
    def scrape_website_content(self, url: str) -> Dict:
        """Scrape main text content from website."""
        driver = None
        try:
            # Setup Chrome
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--log-level=3')
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(30)
            
            # Load page
            driver.get(url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "header", "footer"]):
                element.decompose()
            
            # Extract main content
            main_content = ""
            main_selectors = ['main', 'article', '.content', '#content', '.post', '.entry']
            
            for selector in main_selectors:
                elements = soup.select(selector)
                if elements:
                    main_content = ' '.join([elem.get_text() for elem in elements])
                    break
            
            if not main_content:
                body = soup.find('body')
                if body:
                    main_content = body.get_text()
            
            # Clean text
            main_content = ' '.join(main_content.split())
            
            return {
                'main_text': main_content[:3000] if main_content else '',
                'error': None
            }
            
        except Exception as e:
            return {'main_text': '', 'error': str(e)}
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass