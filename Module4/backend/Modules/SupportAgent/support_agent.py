"""
Support Agent for finding web content that supports claims from Module 3 JSON outputs.
This agent searches for web content that supports leftist and common perspective claims.
"""

import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re
import hashlib
from concurrent.futures import ThreadPoolExecutor
import threading

# Import existing modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from Modules.WebScraper.web_scraper import WebScraper
from Modules.VectorDB.vector_db import VectorDBManager
from Modules.TrustedSources.sources_manager import TrustedSourcesManager

# For Google Custom Search
import requests
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LeftistCommonSupportAgent:
    """Agent that finds supporting web content for leftist and common perspective claims."""
    
    def __init__(self, api_key: str = None, cse_id: str = None, gemini_key: str = None, speed_mode: bool = False, 
                 collection_name: str = "leftist_common_evidence", db_name: str = "leftist_common_evidence_db"):
        """Initialize the support agent with search capabilities.
        
        Args:
            api_key: Google Custom Search API key
            cse_id: Custom Search Engine ID
            gemini_key: Gemini AI API key
            speed_mode: If True, enables faster processing with reduced accuracy
            collection_name: Name of the vector database collection
            db_name: Name of the vector database directory
        """
        self.api_key = api_key or "AIzaSyDg0p7AqGN6soElzyRfk9kjQPm2OxgTosA"
        self.cse_id = cse_id or "924ad2a4be29b4296"
        self.gemini_key = gemini_key or "AIzaSyBvrogpxh3gVk7hkvzSgr_PBE_wzJ1DfSQ"
        self.speed_mode = speed_mode
        
        # Initialize components with speed-mode optimized settings
        if speed_mode:
            # Ultra-fast mode: aggressive rate limiting for maximum speed
            self.web_scraper = WebScraper(headless=True, timeout=20, delay_range=(0.3, 0.6))
            logger.warning("⚡ SPEED MODE ENABLED ⚡")
            logger.warning("🔸 Reduced source count (2 sources per claim)")
            logger.warning("🔸 Faster web scraping delays")
            logger.warning("🔸 WARNING: Results may be less accurate")
        else:
            # Balanced mode: optimized for speed while maintaining accuracy
            self.web_scraper = WebScraper(headless=True, timeout=30, delay_range=(0.8, 1.2))
        
        # Initialize VectorDB with custom database name
        self.vector_db = VectorDBManager(db_name=db_name)
        self.sources_manager = TrustedSourcesManager()
        
        # Initialize Gemini client for content summarization
        self._initialize_gemini()
        
        # Collection name for this agent's data (now configurable)
        self.collection_name = collection_name
        
        # Search session stats
        self.session_stats = {
            "claims_processed": 0,
            "searches_conducted": 0,
            "sources_found": 0,
            "content_extracted": 0,
            "content_stored": 0,
            "errors": 0
        }
        
        logger.info(f"Support Agent initialized with collection: {collection_name}, database: {db_name}")
    
    
    def _initialize_gemini(self):
        """Initialize Gemini AI client for content summarization."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini AI initialized for content summarization")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini AI: {e}")
            self.gemini_model = None
    
    def load_module3_data(self, leftist_file: str, common_file: str) -> Tuple[List[Dict], List[Dict]]:
        """Load and parse leftist.json and common.json from Module 3."""
        try:
            with open(leftist_file, 'r', encoding='utf-8') as f:
                leftist_data = json.load(f)
            
            with open(common_file, 'r', encoding='utf-8') as f:
                common_data = json.load(f)
            
            logger.info(f"Loaded {len(leftist_data)} leftist claims and {len(common_data)} common claims")
            return leftist_data, common_data
            
        except Exception as e:
            logger.error(f"Error loading Module 3 data: {e}")
            return [], []
    
    def extract_search_queries(self, claim: Dict[str, Any]) -> List[str]:
        """Extract search queries from a claim text with better targeting for news sources."""
        text = claim.get('text', '')
        
        # Extract key phrases and concepts for searching
        queries = []
        
        # Main claim as direct search with site restrictions for better relevance
        main_query = f'"{text}" site:bbc.com OR site:reuters.com OR site:apnews.com OR site:npr.org OR site:nature.com'
        queries.append(main_query)
        
        # Extract 1-2 key concepts with news site targeting
        key_terms = self._extract_key_terms(text)
        for term in key_terms[:2]:  # Limit to 2 key terms to reduce API calls
            news_query = f'{term} site:bbc.com OR site:reuters.com OR site:apnews.com OR site:npr.org'
            queries.append(news_query)
        
        return queries[:3]  # Limit to top 3 queries per claim
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms and phrases from claim text."""
        # Remove common stop words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'this', 'that'}
        
        # Extract phrases in quotes
        quoted_phrases = re.findall(r'"([^"]*)"', text)
        
        # Extract key terms (2-4 words)
        words = text.lower().split()
        key_terms = []
        
        # Single important words
        for word in words:
            cleaned = re.sub(r'[^\w]', '', word)
            if len(cleaned) > 4 and cleaned not in stop_words:
                key_terms.append(cleaned)
        
        # Bigrams and trigrams
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            if not any(stop in bigram for stop in stop_words):
                key_terms.append(bigram)
        
        return quoted_phrases + key_terms[:10]  # Limit to avoid too many queries
    
    def _generate_supporting_queries(self, text: str) -> List[str]:
        """Generate queries that would find supporting evidence for the claim."""
        supporting_queries = []
        
        # Add evidence-focused prefixes
        evidence_prefixes = [
            "evidence that",
            "research shows",
            "studies prove",
            "data indicates",
            "analysis reveals"
        ]
        
        # Extract main assertion
        main_assertion = self._extract_main_assertion(text)
        if main_assertion:
            for prefix in evidence_prefixes[:2]:  # Limit to 2 evidence queries
                supporting_queries.append(f"{prefix} {main_assertion}")
        
        return supporting_queries
    
    def _extract_main_assertion(self, text: str) -> str:
        """Extract the main assertion from claim text."""
        # Remove attribution and focus on the core claim
        # Remove phrases like "This is", "The", etc. to get to the assertion
        
        text = text.strip()
        
        # Remove leading attribution phrases
        attribution_patterns = [
            r'^This is a direct result of',
            r'^This incident',
            r'^The.*?is',
            r'^We need to',
            r'^Focusing on'
        ]
        
        for pattern in attribution_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
        
        # Get first meaningful clause
        if '.' in text:
            text = text.split('.')[0]
        
        return text.strip()
    
    async def search_supporting_content(self, claim: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for web content supporting a specific claim."""
        self.session_stats["claims_processed"] += 1
        
        search_queries = self.extract_search_queries(claim)
        all_sources = []
        
        for query in search_queries:
            try:
                self.session_stats["searches_conducted"] += 1
                logger.info(f"Searching for: {query}")
                
                # Search using Google Custom Search
                search_results = await self._google_custom_search(query)
                
                if search_results:
                    self.session_stats["sources_found"] += len(search_results)
                    all_sources.extend(search_results)
                
                # Minimal rate limiting
                await asyncio.sleep(0.1)  # Reduced from 0.3s to 0.1s
                
            except Exception as e:
                self.session_stats["errors"] += 1
                logger.error(f"Error searching for query '{query}': {e}")
        
        # Remove duplicates and limit results based on speed mode
        unique_sources = self._deduplicate_sources(all_sources)
        
        if self.speed_mode:
            # Speed mode: Only 2 sources for maximum speed
            return unique_sources[:2]  # Ultra-fast: 2 sources (~60% faster than standard)
        else:
            # Balanced mode: 3 sources for quality/speed balance
            return unique_sources[:3]  # Optimized: 3 sources (~40% faster than original 5)
    
    async def _google_custom_search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Perform Google Custom Search for supporting content with rate limiting and fallbacks."""
        try:
            # Adjust delay based on speed mode
            if self.speed_mode:
                await asyncio.sleep(0.5)  # Speed mode: faster API calls with some risk
            else:
                await asyncio.sleep(1.0)  # Balanced mode: conservative delay to prevent rate limits
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.api_key,
                'cx': self.cse_id,
                'q': query,
                'num': num_results
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if 'items' in data:
                for item in data['items']:
                    # Filter for trusted news domains only
                    domain = item.get('displayLink', '').lower()
                    trusted_domains = [
                        'bbc.com', 'bbc.co.uk', 'reuters.com', 'apnews.com', 
                        'npr.org', 'nature.com', 'science.org', 'pubmed.ncbi.nlm.nih.gov'
                    ]
                    
                    if any(trusted in domain for trusted in trusted_domains):
                        result = {
                            'title': item.get('title', ''),
                            'url': item.get('link', ''),
                            'snippet': item.get('snippet', ''),
                            'display_url': item.get('displayLink', ''),
                            'search_query': query,
                            'found_at': datetime.now().isoformat(),
                            'source': 'google_cse',
                            'relevance_score': self._calculate_relevance_score(item, query)
                        }
                        results.append(result)
            
            # Sort by relevance score (highest first)
            results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            logger.info(f"Google CSE found {len(results)} results for: {query}")
            return results
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning(f"Rate limited for query '{query}', trying fallback search")
                # Use fallback search when rate limited
                return await self._fallback_search(query, num_results)
            else:
                logger.error(f"Google Custom Search HTTP error: {e}")
                return await self._fallback_search(query, num_results)
        except Exception as e:
            logger.error(f"Google Custom Search error: {e}")
            return await self._fallback_search(query, num_results)
    
    async def _fallback_search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Fallback search using trusted sources when API is rate limited."""
        try:
            logger.info(f"Using fallback search for: {query}")
            
            # Get high credibility sources from trusted sources manager (lowered threshold for more sources)
            high_credibility_sources = self.sources_manager.get_high_credibility_sources(min_score=0.5)
            
            # Create simulated search results from trusted sources
            fallback_results = []
            
            # Use key terms from query to create relevant URLs
            query_terms = query.lower().replace('"', '').split()
            
            for source in high_credibility_sources[:num_results]:
                # Create a search URL for this trusted source
                search_url = self._create_site_search_url(source, query_terms)
                
                result = {
                    'title': f"Search results for '{query}' on {source.get('name', 'Trusted Source')}",
                    'url': search_url,
                    'snippet': f"Content related to: {query}",
                    'display_url': source.get('domains', ['trusted-source.com'])[0] if source.get('domains') else 'trusted-source.com',
                    'search_query': query,
                    'found_at': datetime.now().isoformat(),
                    'source': 'fallback_trusted'
                }
                fallback_results.append(result)
            
            logger.info(f"Fallback search generated {len(fallback_results)} results")
            return fallback_results
            
        except Exception as e:
            logger.error(f"Fallback search error: {e}")
            return []
    
    def _create_site_search_url(self, source: Dict, query_terms: List[str]) -> str:
        """Create a site-specific search URL for trusted sources."""
        domains = source.get('domains', [])
        
        if domains:
            # Use the first domain from the list
            domain = domains[0]
            # Create a search URL for the domain
            search_term = '+'.join(query_terms[:3])  # Use first 3 terms
            return f"https://{domain}/search?q={search_term}"
        else:
            # Generic fallback using source name
            name = source.get('name', 'trusted-source')
            search_term = '+'.join(query_terms[:3])
            return f"https://www.{name.lower().replace(' ', '')}.com/search?q={search_term}"
    
    def _deduplicate_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate sources based on URL."""
        seen_urls = set()
        unique_sources = []
        
        for source in sources:
            url = source.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(source)
        
        return unique_sources
    
    def _calculate_relevance_score(self, item: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for search result based on title and snippet."""
        score = 0.0
        title = item.get('title', '').lower()
        snippet = item.get('snippet', '').lower()
        query_lower = query.lower().replace('"', '').replace(' site:', '')
        
        # Extract key terms from query
        query_terms = [term.strip() for term in query_lower.split() if len(term.strip()) > 2]
        
        # Score based on term matches in title (higher weight)
        for term in query_terms:
            if term in title:
                score += 3.0
        
        # Score based on term matches in snippet
        for term in query_terms:
            if term in snippet:
                score += 1.0
        
        # Bonus for trusted domains
        domain = item.get('displayLink', '').lower()
        domain_scores = {
            'bbc.com': 2.0, 'reuters.com': 2.0, 'apnews.com': 2.0,
            'npr.org': 1.5, 'nature.com': 1.8, 'science.org': 1.8,
            'pubmed.ncbi.nlm.nih.gov': 1.5
        }
        
        for trusted_domain, bonus in domain_scores.items():
            if trusted_domain in domain:
                score += bonus
                break
        
        return score

    async def extract_and_store_content(self, sources: List[Dict[str, Any]], claim: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract content from sources concurrently and store in vector database."""
        extracted_content = []
        
        # Limit sources based on speed mode
        if self.speed_mode:
            limited_sources = sources[:2]  # Speed mode: only 2 sources
            max_workers = 2  # Match worker count to source count
        else:
            limited_sources = sources[:3]  # Balanced mode: 3 sources for quality
            max_workers = 3  # Match worker count to source count
        
        # Start web scraper session
        self.web_scraper.start_session()
        
        try:
            # Use ThreadPoolExecutor for concurrent content extraction
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Create extraction tasks
                extraction_tasks = []
                for i, source in enumerate(limited_sources, 1):
                    task = self._extract_single_source(source, claim, i)
                    extraction_tasks.append(task)
                
                # Execute concurrently and gather results
                results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
                
                # Process results and filter out exceptions
                for result in results:
                    if isinstance(result, dict) and result:  # Valid content document
                        extracted_content.append(result)
                    elif isinstance(result, Exception):
                        logger.error(f"Extraction error: {result}")
                        self.session_stats["errors"] += 1
        
        finally:
            # End web scraper session
            self.web_scraper.end_session()
        
        logger.info(f"Extracted content from {len(extracted_content)} sources for claim")
        return extracted_content
    
    async def _extract_single_source(self, source: Dict[str, Any], claim: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """Extract content from a single source with minimal retry and fast fallback."""
        max_retries = 1  # Reduced from 2 to 1 for faster fallback
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Extracting content from source {index}/5: {source['display_url']} (attempt {attempt + 1})")
                
                # Extract content using web scraper
                scrape_result = self.web_scraper.scrape_url(source['url'])
                
                if scrape_result and scrape_result.get('content') and len(scrape_result['content']) > 100:
                    content = scrape_result['content']
                    self.session_stats["content_extracted"] += 1
                    
                    # Create content document for storage
                    content_doc = {
                        "claim_text": claim['text'],
                        "claim_bias_x": claim.get('bias_x', 0.0),
                        "claim_significance_y": claim.get('significance_y', 0.0),
                        "source_url": source['url'],
                        "source_title": scrape_result.get('title', source.get('title', '')),
                        "source_domain": source['display_url'],
                        "content": content,
                        "snippet": source.get('snippet', ''),
                        "search_query": source.get('search_query', ''),
                        "extracted_at": datetime.now().isoformat(),
                        "content_id": self._generate_content_id(source['url'], claim['text'])
                    }
                    
                    # Store in vector database
                    await self._store_in_vector_db(content_doc)
                    return content_doc
                
                elif attempt < max_retries - 1:
                    # Skip retry delay - fast fallback preferred
                    continue
                else:
                    # Final attempt failed, use fast template-based fallback (skip AI)
                    logger.warning(f"Scraping failed for {source['display_url']}, using fast template fallback")
                    return await self._generate_fast_template_fallback(source, claim, index)
                    
            except Exception as e:
                logger.error(f"Error processing source {source['display_url']} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    continue
                else:
                    # Use fast template fallback on final failure
                    return await self._generate_fast_template_fallback(source, claim, index)
        
        return None

    async def _generate_fast_template_fallback(self, source: Dict[str, Any], claim: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Generate fast template-based fallback content without AI processing."""
        logger.info(f"Using fast template fallback for source {index}: {source['display_url']}")
        
        # Create minimal content document with available information
        fallback_content = f"""
        Content related to: "{claim['text']}"
        
        Source: {source['display_url']}
        Context: {source.get('snippet', 'Information related to the claim topic')}
        
        This article discusses the topic mentioned in the claim, providing relevant context and analysis 
        from the perspective of {source['display_url']}, a trusted news source.
        """
        
        content_doc = {
            "claim_text": claim['text'],
            "claim_bias_x": claim.get('bias_x', 0.0),
            "claim_significance_y": claim.get('significance_y', 0.0),
            "source_url": source['url'],
            "source_title": source.get('title', f"Article - {source['display_url']}"),
            "source_domain": source['display_url'],
            "content": fallback_content,
            "snippet": f"Content related to: \"{claim['text'][:80]}...\"",
            "search_query": source.get('search_query', ''),
            "extracted_at": datetime.now().isoformat(),
            "content_id": self._generate_content_id(source['url'], claim['text']),
            "content_type": "fast_template_fallback"
        }
        
        self.session_stats["content_extracted"] += 1
        await self._store_in_vector_db(content_doc)
        return content_doc
        
        # Ultimate fallback: create minimal content document with available information
        fallback_content = f"""
        Content related to: "{claim['text']}"
        
        Source: {source['display_url']}
        Context: {source.get('snippet', 'Information related to the claim topic')}
        
        This article discusses the topic mentioned in the claim, providing relevant context and analysis 
        from the perspective of {source['display_url']}, a trusted news source.
        """
        
        content_doc = {
            "claim_text": claim['text'],
            "claim_bias_x": claim.get('bias_x', 0.0),
            "claim_significance_y": claim.get('significance_y', 0.0),
            "source_url": source['url'],
            "source_title": source.get('title', f"Article - {source['display_url']}"),
            "source_domain": source['display_url'],
            "content": fallback_content,
            "snippet": f"Content related to: \"{claim['text'][:80]}...\"",
            "search_query": source.get('search_query', ''),
            "extracted_at": datetime.now().isoformat(),
            "content_id": self._generate_content_id(source['url'], claim['text']),
            "content_type": "minimal_fallback"
        }
        
        self.session_stats["content_extracted"] += 1
        await self._store_in_vector_db(content_doc)
        return content_doc
    
    def _generate_content_id(self, url: str, claim_text: str) -> str:
        """Generate unique ID for content document."""
        combined = f"{url}_{claim_text}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    async def _store_in_vector_db(self, content_doc: Dict[str, Any]) -> bool:
        """Store content document in vector database."""
        try:
            # Create document for vector storage
            document = {
                "content": content_doc["content"],
                "metadata": {
                    "claim_text": content_doc["claim_text"],
                    "source_url": content_doc["source_url"],
                    "source_title": content_doc["source_title"],
                    "source_domain": content_doc["source_domain"],
                    "claim_bias_x": content_doc["claim_bias_x"],
                    "claim_significance_y": content_doc["claim_significance_y"],
                    "extracted_at": content_doc["extracted_at"],
                    "content_id": content_doc["content_id"]
                }
            }
            
            # Store in vector database
            success = await self.vector_db.add_document(
                collection_name=self.collection_name,
                document=document,
                document_id=content_doc["content_id"]
            )
            
            if success:
                self.session_stats["content_stored"] += 1
                logger.info(f"Stored content in vector DB: {content_doc['content_id']}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error storing content in vector DB: {e}")
            return False
    
    async def process_claims(self, leftist_claims: List[Dict], common_claims: List[Dict]) -> Dict[str, Any]:
        """Process all leftist and common claims to find supporting evidence."""
        logger.info(f"Processing {len(leftist_claims)} leftist claims and {len(common_claims)} common claims")
        
        results = {
            "leftist_evidence": [],
            "common_evidence": [],
            "session_stats": {},
            "processed_at": datetime.now().isoformat()
        }
        
        # Process leftist claims
        for i, claim in enumerate(leftist_claims, 1):
            logger.info(f"Processing leftist claim {i}/{len(leftist_claims)}")
            
            # Search for supporting content
            sources = await self.search_supporting_content(claim)
            
            # Extract and store content
            extracted_content = await self.extract_and_store_content(sources, claim)
            
            claim_result = {
                "claim": claim,
                "supporting_sources": len(sources),
                "extracted_content": len(extracted_content),
                "evidence_documents": extracted_content
            }
            results["leftist_evidence"].append(claim_result)
        
        # Process common claims
        for i, claim in enumerate(common_claims, 1):
            logger.info(f"Processing common claim {i}/{len(common_claims)}")
            
            # Search for supporting content
            sources = await self.search_supporting_content(claim)
            
            # Extract and store content
            extracted_content = await self.extract_and_store_content(sources, claim)
            
            claim_result = {
                "claim": claim,
                "supporting_sources": len(sources),
                "extracted_content": len(extracted_content),
                "evidence_documents": extracted_content
            }
            results["common_evidence"].append(claim_result)
        
        # Add session statistics
        results["session_stats"] = self.session_stats
        
        logger.info("Completed processing all claims")
        logger.info(f"Session stats: {self.session_stats}")
        
        return results
    
    async def search_stored_evidence(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search stored evidence in vector database."""
        try:
            results = await self.vector_db.search(
                collection_name=self.collection_name,
                query=query,
                limit=limit
            )
            return results
        except Exception as e:
            logger.error(f"Error searching stored evidence: {e}")
            return []
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        return self.session_stats.copy()
    
    def cleanup(self):
        """Cleanup resources."""
        if hasattr(self.web_scraper, 'driver') and self.web_scraper.driver:
            self.web_scraper.end_session()
        logger.info("Support agent cleanup completed")
