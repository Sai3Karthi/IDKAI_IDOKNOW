import json
import os
from typing import List, Dict, Any
from pathlib import Path

class TrustedSourcesManager:
    """Manages trusted sources configuration and validation."""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent / "trusted_sources.json"
        
        self.config_path = config_path
        self.sources_data = self._load_sources()
    
    def _load_sources(self) -> Dict[str, Any]:
        """Load trusted sources from configuration file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Trusted sources file not found at {self.config_path}")
            return {"trusted_sources": {}}
        except json.JSONDecodeError as e:
            print(f"Error parsing trusted sources JSON: {e}")
            return {"trusted_sources": {}}
    
    def get_all_domains(self) -> List[str]:
        """Get all trusted domains from all categories."""
        domains = []
        trusted_sources = self.sources_data.get("trusted_sources", {})
        
        for category in trusted_sources.values():
            if isinstance(category, list):
                for source in category:
                    if "domains" in source:
                        domains.extend(source["domains"])
        
        return list(set(domains))  # Remove duplicates
    
    def get_domains_by_category(self, category: str) -> List[str]:
        """Get domains for a specific category."""
        domains = []
        trusted_sources = self.sources_data.get("trusted_sources", {})
        
        if category in trusted_sources:
            for source in trusted_sources[category]:
                if "domains" in source:
                    domains.extend(source["domains"])
        
        return domains
    
    def get_high_credibility_sources(self, min_score: float = 0.9) -> List[Dict[str, Any]]:
        """Get sources with credibility score above threshold."""
        high_credibility = []
        trusted_sources = self.sources_data.get("trusted_sources", {})
        
        for category in trusted_sources.values():
            if isinstance(category, list):
                for source in category:
                    if source.get("credibility_score", 0) >= min_score:
                        high_credibility.append(source)
        
        return high_credibility
    
    def get_search_patterns(self, pattern_type: str = "general") -> List[str]:
        """Get search patterns for specific type."""
        search_patterns = self.sources_data.get("search_patterns", {})
        return search_patterns.get(pattern_type, [])
    
    def get_exclusion_patterns(self) -> List[str]:
        """Get patterns to exclude from search results."""
        return self.sources_data.get("exclusion_patterns", [])
    
    def is_trusted_domain(self, url: str) -> bool:
        """Check if a URL belongs to a trusted domain."""
        from urllib.parse import urlparse
        
        domain = urlparse(url).netloc.lower()
        # Remove www. prefix
        domain = domain.replace("www.", "")
        
        trusted_domains = self.get_all_domains()
        for trusted_domain in trusted_domains:
            if domain == trusted_domain or domain.endswith(f".{trusted_domain}"):
                return True
        
        return False
    
    def get_source_info(self, url: str) -> Dict[str, Any]:
        """Get detailed information about a source from its URL."""
        from urllib.parse import urlparse
        
        domain = urlparse(url).netloc.lower().replace("www.", "")
        trusted_sources = self.sources_data.get("trusted_sources", {})
        
        for category_name, category in trusted_sources.items():
            if isinstance(category, list):
                for source in category:
                    if "domains" in source:
                        for source_domain in source["domains"]:
                            if domain == source_domain or domain.endswith(f".{source_domain}"):
                                return {
                                    "category": category_name,
                                    "source_info": source,
                                    "is_trusted": True
                                }
        
        return {
            "category": "unknown",
            "source_info": {},
            "is_trusted": False
        }
    
    def generate_search_queries(self, topic: str, max_queries: int = 5) -> List[str]:
        """Generate search queries for a given topic using patterns."""
        queries = []
        
        # Get different types of search patterns
        pattern_types = ["general", "fact_checking", "academic"]
        
        for pattern_type in pattern_types:
            patterns = self.get_search_patterns(pattern_type)
            for pattern in patterns[:max_queries//len(pattern_types) + 1]:
                query = pattern.format(topic=topic)
                queries.append(query)
                
                if len(queries) >= max_queries:
                    break
            
            if len(queries) >= max_queries:
                break
        
        return queries[:max_queries]
    
    def filter_trusted_results(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter search results to only include trusted sources."""
        filtered_results = []
        
        for result in search_results:
            url = result.get("url", "")
            if self.is_trusted_domain(url):
                source_info = self.get_source_info(url)
                result["source_category"] = source_info["category"]
                result["credibility_score"] = source_info["source_info"].get("credibility_score", 0.5)
                result["bias_rating"] = source_info["source_info"].get("bias_rating", "unknown")
                filtered_results.append(result)
        
        return filtered_results

# Example usage and testing
if __name__ == "__main__":
    manager = TrustedSourcesManager()
    
    # Test basic functionality
    print("All trusted domains:", len(manager.get_all_domains()))
    print("News domains:", manager.get_domains_by_category("news_outlets"))
    print("High credibility sources:", len(manager.get_high_credibility_sources()))
    
    # Test search query generation
    topic = "climate change impacts"
    queries = manager.generate_search_queries(topic)
    print(f"Generated queries for '{topic}':")
    for i, query in enumerate(queries, 1):
        print(f"  {i}. {query}")
    
    # Test domain checking
    test_urls = [
        "https://www.bbc.com/news/article",
        "https://reuters.com/business/story",
        "https://example.com/fake-news",
        "https://nature.com/articles/scientific-paper"
    ]
    
    print("\nDomain trust checking:")
    for url in test_urls:
        is_trusted = manager.is_trusted_domain(url)
        source_info = manager.get_source_info(url)
        print(f"  {url}: {'✓' if is_trusted else '✗'} ({source_info['category']})")