import asyncio
import aiohttp
import time
import random
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScraper:
    """Advanced web scraper using Selenium with proper rate limiting and error handling."""
    
    def __init__(self, headless: bool = True, timeout: int = 30, delay_range: tuple = (0.8, 1.2)):
        self.headless = headless
        self.timeout = timeout
        self.delay_range = delay_range
        self.user_agent = UserAgent()
        self.driver = None
        self.session_stats = {
            "requests_made": 0,
            "successful_scrapes": 0,
            "failed_scrapes": 0,
            "blocked_attempts": 0
        }
    
    def _create_driver(self) -> webdriver.Chrome:
        """Create and configure Chrome driver."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Standard options for better compatibility
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Rotate user agent
        chrome_options.add_argument(f"--user-agent={self.user_agent.random}")
        
        # Install and setup ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Hide webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def _apply_rate_limiting(self):
        """Apply random delay to avoid being detected as bot."""
        delay = random.uniform(*self.delay_range)
        logger.info(f"Applying rate limiting delay: {delay:.2f} seconds")
        time.sleep(delay)
    
    def start_session(self):
        """Start scraping session."""
        try:
            self.driver = self._create_driver()
            logger.info("Web scraping session started successfully")
        except Exception as e:
            logger.error(f"Failed to start scraping session: {e}")
            raise
    
    def end_session(self):
        """End scraping session and cleanup."""
        if self.driver:
            self.driver.quit()
            self.driver = None
        
        logger.info(f"Session ended. Stats: {self.session_stats}")
    
    def scrape_url(self, url: str, wait_for_element: str = None) -> Optional[Dict[str, Any]]:
        """
        Scrape content from a single URL.
        
        Args:
            url: URL to scrape
            wait_for_element: CSS selector to wait for before scraping
            
        Returns:
            Dictionary with scraped content or None if failed
        """
        if not self.driver:
            raise RuntimeError("Scraping session not started. Call start_session() first.")
        
        self.session_stats["requests_made"] += 1
        
        try:
            logger.info(f"Scraping URL: {url}")
            
            # Navigate to URL
            self.driver.get(url)
            
            # Wait for specific element if specified
            if wait_for_element:
                wait = WebDriverWait(self.driver, self.timeout)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element)))
            else:
                # Default wait for body
                wait = WebDriverWait(self.driver, self.timeout)
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract content
            result = self._extract_content(soup, url)
            
            if result:
                self.session_stats["successful_scrapes"] += 1
                logger.info(f"Successfully scraped: {url}")
            else:
                self.session_stats["failed_scrapes"] += 1
                logger.warning(f"No content extracted from: {url}")
            
            # Apply rate limiting
            self._apply_rate_limiting()
            
            return result
            
        except TimeoutException:
            logger.error(f"Timeout while loading: {url}")
            self.session_stats["failed_scrapes"] += 1
            return None
            
        except WebDriverException as e:
            if "ERR_BLOCKED_BY_CLIENT" in str(e) or "ERR_ACCESS_DENIED" in str(e):
                logger.error(f"Blocked by website: {url}")
                self.session_stats["blocked_attempts"] += 1
            else:
                logger.error(f"WebDriver error for {url}: {e}")
                self.session_stats["failed_scrapes"] += 1
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            self.session_stats["failed_scrapes"] += 1
            return None
    
    def _extract_content(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """Extract relevant content from parsed HTML."""
        try:
            # Get title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else "No title"
            
            # Enhanced content selectors with more comprehensive options
            content_selectors = [
                'article',
                '[role="main"]',
                '.content',
                '.article-content',
                '.post-content',
                '.entry-content',
                '.story-content',
                '.article-body',
                '.post-body',
                '.story-body',
                '.text-content',
                '.main-content',
                '.page-content',
                '.content-body',
                '.article-text',
                'main',
                '#content',
                '#main-content',
                '#article-content',
                '.search-results',
                '.results',
                '.listing',
                '.items',
                'section',
                '.section-content'
            ]
            
            content_text = ""
            content_elements = []
            
            # Try multiple selectors and combine content
            for selector in content_selectors:
                elements = soup.select(selector)
                for element in elements:
                    if element and element not in content_elements:
                        element_text = element.get_text(separator=' ', strip=True)
                        if element_text and len(element_text) > 20:  # Reduced minimum
                            content_elements.append(element)
                            content_text += element_text + " "
                
                # Break if we found substantial content
                if len(content_text) > 200:
                    break
            
            # If still no content, try broader selectors
            if len(content_text) < 50:
                broader_selectors = ['div', 'p', 'span', 'body']
                for selector in broader_selectors:
                    elements = soup.select(selector)
                    for element in elements:
                        element_text = element.get_text(separator=' ', strip=True)
                        if element_text and len(element_text) > 10:
                            content_text += element_text + " "
                    
                    if len(content_text) > 100:
                        break
            
            # Clean and validate content
            content_text = self._clean_text(content_text)
            
            # Reduced minimum content length requirement
            if len(content_text) < 20:  # Much lower threshold
                logger.warning(f"Content too short for {url}: {len(content_text)} chars")
                return None
            
            # Extract metadata
            meta_description = ""
            meta_tag = soup.find('meta', attrs={'name': 'description'})
            if meta_tag and meta_tag.get('content'):
                meta_description = meta_tag['content'].strip()
            
            # Extract publication date if available
            pub_date = self._extract_publication_date(soup)
            
            return {
                "url": url,
                "title": title,
                "content": content_text,
                "meta_description": meta_description,
                "publication_date": pub_date,
                "content_length": len(content_text),
                "scraped_at": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove common navigation and footer text
        unwanted_phrases = [
            "Subscribe to our newsletter",
            "Follow us on",
            "Cookie policy",
            "Privacy policy",
            "Terms of service",
            "Advertisement",
            "Sponsored content"
        ]
        
        for phrase in unwanted_phrases:
            text = text.replace(phrase, "")
        
        return text.strip()
    
    def _extract_publication_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Try to extract publication date from various meta tags."""
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="publishdate"]',
            'meta[name="date"]',
            'time[datetime]',
            '.published',
            '.date'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content')
                elif element.name == 'time':
                    return element.get('datetime') or element.get_text().strip()
                else:
                    return element.get_text().strip()
        
        return None
    
    def scrape_multiple_urls(self, urls: List[str], max_concurrent: int = 3) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs with proper session management.
        
        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum number of concurrent requests (not used in Selenium)
            
        Returns:
            List of scraped content dictionaries
        """
        results = []
        
        try:
            self.start_session()
            
            for i, url in enumerate(urls, 1):
                logger.info(f"Processing URL {i}/{len(urls)}: {url}")
                
                result = self.scrape_url(url)
                if result:
                    results.append(result)
                
                # Add extra delay between URLs to be respectful
                if i < len(urls):
                    time.sleep(random.uniform(1, 3))
            
        finally:
            self.end_session()
        
        logger.info(f"Scraping completed. Successfully scraped {len(results)}/{len(urls)} URLs")
        return results
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        return self.session_stats.copy()

# Testing and example usage
if __name__ == "__main__":
    # Example usage
    scraper = WebScraper(headless=True, timeout=30, delay_range=(2, 4))
    
    test_urls = [
        "https://www.bbc.com/news",
        "https://www.reuters.com",
        "https://www.nature.com"
    ]
    
    try:
        results = scraper.scrape_multiple_urls(test_urls)
        
        print(f"\nScraping Results:")
        print(f"Successfully scraped: {len(results)} URLs")
        
        for result in results:
            print(f"\nURL: {result['url']}")
            print(f"Title: {result['title'][:100]}...")
            print(f"Content length: {result['content_length']} characters")
            print(f"Meta description: {result['meta_description'][:100]}...")
        
        print(f"\nSession Statistics:")
        stats = scraper.get_session_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"Error during scraping: {e}")
        logger.exception("Detailed error information:")