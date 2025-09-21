import os
import time
import json
import asyncio
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.generativeai as genai
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleCSEResearcher:
    """Google Custom Search Engine integration for finding relevant content."""
    
    def __init__(self, api_key: str = None, cse_id: str = None, gemini_api_key: str = None):
        self.api_key = api_key or os.getenv('GOOGLE_CSE_API_KEY')
        self.cse_id = cse_id or os.getenv('GOOGLE_CSE_ID')
        self.gemini_api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key or not self.cse_id:
            raise ValueError("Google CSE API key and CSE ID are required")
        
        # Initialize Google Custom Search
        self.search_service = build("customsearch", "v1", developerKey=self.api_key)
        
        # Initialize Gemini for summarization
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        else:
            logger.warning("Gemini API key not provided. Summarization will be limited.")
            self.gemini_model = None
        
        # Search configuration - can be customized per search type
        self.text_search_config = {
            "safe": "active",
            "dateRestrict": "y2",  # Last 2 years
            "lr": "lang_en"  # English language
        }
        
        self.image_search_config = {
            "safe": "active",
            "searchType": "image",
            "dateRestrict": "y2",
            "lr": "lang_en",
            "imgType": "news",  # Focus on news images
            "imgSize": "MEDIUM"  # Valid value from API
        }
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum seconds between requests
    
    def _apply_rate_limiting(self):
        """Apply rate limiting for API requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.info(f"Rate limiting: waiting {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def search_content(self, query: str, num_results: int = 10, search_type: str = "text") -> List[Dict[str, Any]]:
        """
        Search for content using Google Custom Search Engine.
        
        Args:
            query: Search query
            num_results: Number of results to return
            search_type: "text" for regular search, "image" for image search
            
        Returns:
            List of search results with metadata
        """
        try:
            self._apply_rate_limiting()
            
            logger.info(f"Searching for ({search_type}): {query}")
            
            # Choose search config based on type
            search_config = self.text_search_config if search_type == "text" else self.image_search_config
            
            # Execute search
            result = self.search_service.cse().list(
                q=query,
                cx=self.cse_id,
                **search_config,
                num=min(num_results, 10)  # API limit is 10 per request
            ).execute()
            
            # Process results
            search_results = []
            items = result.get('items', [])
            
            for item in items:
                search_result = {
                    "title": item.get('title', ''),
                    "url": item.get('link', ''),
                    "snippet": item.get('snippet', ''),
                    "display_url": item.get('displayLink', ''),
                    "formatted_url": item.get('formattedUrl', ''),
                    "html_snippet": item.get('htmlSnippet', ''),
                    "search_query": query,
                    "search_rank": len(search_results) + 1
                }
                
                # Extract additional metadata if available
                if 'pagemap' in item:
                    pagemap = item['pagemap']
                    
                    # Extract meta tags
                    if 'metatags' in pagemap and pagemap['metatags']:
                        meta = pagemap['metatags'][0]
                        search_result['meta_description'] = meta.get('description', '')
                        search_result['meta_author'] = meta.get('author', '')
                        search_result['meta_date'] = meta.get('article:published_time', '')
                    
                    # Extract images
                    if 'cse_image' in pagemap and pagemap['cse_image']:
                        search_result['image_url'] = pagemap['cse_image'][0].get('src', '')
                
                search_results.append(search_result)
            
            logger.info(f"Found {len(search_results)} results for query: {query}")
            return search_results
            
        except HttpError as e:
            logger.error(f"Google CSE API error for query '{query}': {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during search for '{query}': {e}")
            return []
    
    def search_multiple_queries(self, queries: List[str], max_results_per_query: int = 10, 
                              include_images: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for multiple queries and return organized results.
        
        Args:
            queries: List of search queries
            max_results_per_query: Maximum results per query
            include_images: Whether to also search for images
            
        Returns:
            Dictionary mapping queries to their results
        """
        all_results = {}
        
        for i, query in enumerate(queries, 1):
            logger.info(f"Processing query {i}/{len(queries)}: {query}")
            
            # Text search
            text_results = self.search_content(query, max_results_per_query, "text")
            all_results[f"{query}_text"] = text_results
            
            # Image search (optional)
            if include_images:
                image_results = self.search_content(query, min(max_results_per_query, 5), "image")
                all_results[f"{query}_images"] = image_results
            
            # Add delay between queries to be respectful
            if i < len(queries):
                time.sleep(1)
        
        return all_results
    
    def summarize_search_results(self, search_results: List[Dict[str, Any]], 
                               perspective: str, max_length: int = 500) -> Dict[str, Any]:
        """
        Summarize search results using Gemini.
        
        Args:
            search_results: List of search results to summarize
            perspective: The perspective being researched
            max_length: Maximum length of summary
            
        Returns:
            Summary with metadata
        """
        if not self.gemini_model:
            logger.warning("Gemini model not available for summarization")
            return self._create_basic_summary(search_results, perspective)
        
        try:
            # Prepare content for summarization
            content_pieces = []
            for result in search_results[:10]:  # Limit to top 10 results
                content_piece = f"Title: {result.get('title', '')}\n"
                content_piece += f"Source: {result.get('display_url', '')}\n"
                content_piece += f"Snippet: {result.get('snippet', '')}\n"
                content_pieces.append(content_piece)
            
            combined_content = "\n\n".join(content_pieces)
            
            # Create summarization prompt
            prompt = f"""
            Please analyze and summarize the following search results related to this perspective: "{perspective}"
            
            Search Results:
            {combined_content}
            
            Please provide:
            1. A comprehensive summary of the key findings (max {max_length} words)
            2. Main themes and patterns identified
            3. Any conflicting information or debates
            4. Assessment of information quality and reliability
            5. Key sources that provide the most credible information
            
            Format your response as structured text that can be easily parsed.
            """
            
            # Generate summary
            response = self.gemini_model.generate_content(prompt)
            summary_text = response.text
            
            # Calculate confidence based on source diversity and quality
            confidence_score = self._calculate_confidence_score(search_results)
            
            return {
                "summary": summary_text,
                "perspective": perspective,
                "sources_analyzed": len(search_results),
                "confidence_score": confidence_score,
                "key_sources": [r.get('display_url', '') for r in search_results[:5]],
                "generated_at": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error generating summary with Gemini: {e}")
            return self._create_basic_summary(search_results, perspective)
    
    def _create_basic_summary(self, search_results: List[Dict[str, Any]], 
                            perspective: str) -> Dict[str, Any]:
        """Create a basic summary without AI when Gemini is unavailable."""
        # Extract key information
        titles = [r.get('title', '') for r in search_results]
        snippets = [r.get('snippet', '') for r in search_results]
        sources = list(set([r.get('display_url', '') for r in search_results]))
        
        # Create basic summary
        summary = f"Research on perspective '{perspective}' found {len(search_results)} relevant sources. "
        summary += f"Key sources include: {', '.join(sources[:5])}. "
        summary += f"Main topics covered: {', '.join(titles[:3])}."
        
        confidence_score = min(0.8, len(search_results) / 10.0)
        
        return {
            "summary": summary,
            "perspective": perspective,
            "sources_analyzed": len(search_results),
            "confidence_score": confidence_score,
            "key_sources": sources[:5],
            "generated_at": time.time(),
            "note": "Basic summary generated (Gemini unavailable)"
        }
    
    def _calculate_confidence_score(self, search_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on search result quality."""
        if not search_results:
            return 0.0
        
        # Factors for confidence calculation
        num_results = len(search_results)
        unique_sources = len(set([r.get('display_url', '') for r in search_results]))
        avg_snippet_length = sum([len(r.get('snippet', '')) for r in search_results]) / len(search_results)
        
        # Calculate base confidence
        result_factor = min(1.0, num_results / 10.0)  # More results = higher confidence
        diversity_factor = min(1.0, unique_sources / 5.0)  # More diverse sources = higher confidence
        content_factor = min(1.0, avg_snippet_length / 200.0)  # Longer snippets = higher confidence
        
        # Weighted average
        confidence = (result_factor * 0.4 + diversity_factor * 0.4 + content_factor * 0.2)
        
        return round(confidence, 2)
    
    def research_perspective(self, perspective_data: Dict[str, Any], 
                           search_queries: List[str] = None,
                           include_images: bool = False) -> Dict[str, Any]:
        """
        Conduct comprehensive research on a single perspective.
        
        Args:
            perspective_data: Perspective information from Module 3
            search_queries: Custom search queries (optional)
            include_images: Whether to include image search results
            
        Returns:
            Comprehensive research results
        """
        perspective_title = perspective_data.get('title', '')
        perspective_content = perspective_data.get('perspective', '')
        
        # Generate search queries if not provided
        if not search_queries:
            search_queries = self._generate_search_queries(perspective_title, perspective_content)
        
        logger.info(f"Researching perspective: {perspective_title}")
        logger.info(f"Using {len(search_queries)} search queries")
        if include_images:
            logger.info("Including image search results")
        
        # Search for content
        all_search_results = self.search_multiple_queries(search_queries, include_images=include_images)
        
        # Combine and deduplicate results
        combined_results = []
        seen_urls = set()
        
        for query, results in all_search_results.items():
            search_type = "image" if "_images" in query else "text"
            clean_query = query.replace("_text", "").replace("_images", "")
            
            for result in results:
                url = result.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    result['source_query'] = clean_query
                    result['search_type'] = search_type
                    combined_results.append(result)
        
        # Generate summary (focusing on text results)
        text_results = [r for r in combined_results if r.get('search_type') == 'text']
        summary_data = self.summarize_search_results(
            text_results, 
            perspective_title
        )
        
        # Prepare final research results
        research_results = {
            "perspective_index": perspective_data.get('index', 0),
            "perspective_title": perspective_title,
            "perspective_content": perspective_content,
            "research_summary": summary_data,
            "search_queries_used": search_queries,
            "total_sources_found": len(combined_results),
            "text_sources": len([r for r in combined_results if r.get('search_type') == 'text']),
            "image_sources": len([r for r in combined_results if r.get('search_type') == 'image']),
            "all_sources": combined_results,
            "researched_at": time.time()
        }
        
        return research_results
    
    def _generate_search_queries(self, title: str, content: str) -> List[str]:
        """Generate search queries based on perspective title and content."""
        # Extract key terms from title and content
        import re
        
        # Basic keyword extraction
        text = f"{title} {content}".lower()
        
        # Remove common words and extract meaningful terms
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must'}
        
        words = re.findall(r'\b\w+\b', text)
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        
        # Generate different types of queries
        queries = []
        
        # Direct title query
        queries.append(f'"{title}"')
        
        # Factual queries
        if keywords:
            queries.append(f"{' '.join(keywords[:3])} research study")
            queries.append(f"{' '.join(keywords[:2])} expert analysis")
            queries.append(f"{' '.join(keywords[:2])} evidence")
        
        # Academic queries
        queries.append(f"{title} peer reviewed")
        queries.append(f"{title} academic research")
        
        # News and analysis queries
        queries.append(f"{title} news analysis")
        queries.append(f"{title} expert opinion")
        
        return queries[:6]  # Limit to 6 queries

# Testing and example usage
if __name__ == "__main__":
    # Example usage
    researcher = GoogleCSEResearcher()
    
    # Test with sample perspective
    sample_perspective = {
        "index": 0,
        "title": "Economic Impact of Climate Change",
        "perspective": "Analysis of how climate change affects global economic systems, including costs of adaptation and mitigation strategies.",
        "bias_x": 0.3,
        "significance_y": 0.8
    }
    
    try:
        results = researcher.research_perspective(sample_perspective)
        
        print(f"Research Results for: {results['perspective_title']}")
        print(f"Total sources found: {results['total_sources_found']}")
        print(f"Research summary: {results['research_summary']['summary'][:200]}...")
        print(f"Confidence score: {results['research_summary']['confidence_score']}")
        print(f"Key sources: {', '.join(results['research_summary']['key_sources'][:3])}")
        
    except Exception as e:
        print(f"Error during research: {e}")
        logger.exception("Detailed error information:")