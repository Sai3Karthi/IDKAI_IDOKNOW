"""
Enhanced Module 4: Broad Search & Top 10 Summarization
Searches many websites, selects top 10 most credible, and prepares debate-ready summaries
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import sys

# Add modules to path
sys.path.append(str(Path(__file__).parent / "Modules"))

from TrustedSources.sources_manager import TrustedSourcesManager
from WebScraper.web_scraper import WebScraper
from ResearchSummarizer.research_summarizer import GoogleCSEResearcher

logger = logging.getLogger(__name__)

class EnhancedDeepResearchOrchestrator:
    """Enhanced orchestrator that searches broadly and selects top sources for debate preparation."""
    
    def __init__(self):
        self.sources_manager = TrustedSourcesManager()
        self.cse_researcher = None
        self.web_scraper = None
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize research components."""
        try:
            self.cse_researcher = GoogleCSEResearcher()
            logger.info("Enhanced CSE researcher initialized")
        except Exception as e:
            logger.error(f"Failed to initialize CSE researcher: {e}")
            self.cse_researcher = None
    
    def cleanup(self):
        """Cleanup resources including WebScraper session."""
        if self.web_scraper:
            try:
                self.web_scraper.end_session()
                logger.info("WebScraper session ended successfully")
            except Exception as e:
                logger.error(f"Error ending WebScraper session: {e}")
            finally:
                self.web_scraper = None
    
    def conduct_enhanced_research(self, perspectives: List[Dict[str, Any]], 
                                 broad_search_limit: int = 50,
                                 top_sources_limit: int = 10) -> Dict[str, Any]:
        """
        Enhanced research: Search broadly, select top sources, summarize for debate.
        
        Args:
            perspectives: List of perspective data from Module 3
            broad_search_limit: Maximum sources to find in broad search
            top_sources_limit: Top sources to select for detailed analysis
            
        Returns:
            Enhanced research results ready for debate module
        """
        logger.info(f"Starting enhanced research on {len(perspectives)} perspectives")
        logger.info(f"Broad search limit: {broad_search_limit}, Top sources limit: {top_sources_limit}")
        
        research_results = {
            "enhanced_research_metadata": {
                "total_perspectives": len(perspectives),
                "broad_search_limit": broad_search_limit,
                "top_sources_limit": top_sources_limit,
                "research_strategy": "broad_search_top_selection",
                "started_at": time.time(),
                "completed_at": None
            },
            "perspective_research": [],
            "debate_preparation": {
                "leftist_summaries": [],
                "rightist_summaries": [],
                "common_summaries": [],
                "cross_perspective_analysis": {}
            }
        }
        
        # Process each perspective with enhanced methodology
        for i, perspective in enumerate(perspectives, 1):
            logger.info(f"Enhanced processing perspective {i}/{len(perspectives)}: {perspective.get('title', 'Unknown')}")
            
            try:
                perspective_result = self._enhanced_research_single_perspective(
                    perspective, broad_search_limit, top_sources_limit
                )
                research_results["perspective_research"].append(perspective_result)
                
                # Categorize for debate preparation
                self._categorize_for_debate(perspective_result, research_results["debate_preparation"])
                
            except Exception as e:
                logger.error(f"Error in enhanced research for perspective {i}: {e}")
                error_result = {
                    "perspective_index": perspective.get('index', i-1),
                    "perspective_title": perspective.get('title', 'Unknown'),
                    "perspective_category": perspective.get('color', 'unknown'),
                    "error": str(e),
                    "research_status": "failed"
                }
                research_results["perspective_research"].append(error_result)
            
            # Delay between perspectives
            if i < len(perspectives):
                time.sleep(1)
        
        research_results["enhanced_research_metadata"]["completed_at"] = time.time()
        
        # Generate cross-perspective analysis
        self._generate_cross_perspective_analysis(research_results)
        
        # Calculate statistics
        successful = [r for r in research_results["perspective_research"] if "error" not in r]
        research_results["enhanced_research_metadata"]["successful_perspectives"] = len(successful)
        research_results["enhanced_research_metadata"]["failed_perspectives"] = len(perspectives) - len(successful)
        
        logger.info(f"Enhanced research completed. {len(successful)}/{len(perspectives)} perspectives processed")
        
        return research_results
    
    def _enhanced_research_single_perspective(self, perspective: Dict[str, Any], 
                                            broad_limit: int, 
                                            top_limit: int) -> Dict[str, Any]:
        """Enhanced research methodology for a single perspective."""
        perspective_title = perspective.get('title', '')
        perspective_content = perspective.get('perspective', '')
        perspective_category = perspective.get('color', 'unknown')
        
        logger.info(f"Broad search phase for: {perspective_title}")
        
        # Phase 1: Broad Search - Cast a wide net
        broad_search_results = []
        
        if self.cse_researcher:
            # Multiple search strategies for comprehensive coverage
            search_queries = self._generate_search_queries(perspective_title, perspective_content)
            
            for query in search_queries:
                try:
                    query_results = self.cse_researcher.search_content(
                        query, num_results=min(20, broad_limit // len(search_queries))
                    )
                    if query_results:
                        broad_search_results.extend(query_results)
                        logger.info(f"Found {len(query_results)} results for query: {query[:50]}...")
                except Exception as e:
                    logger.warning(f"Search failed for query '{query[:50]}...': {e}")
                
                time.sleep(0.5)  # Rate limiting
        
        # Remove duplicates based on URL
        unique_results = {}
        for result in broad_search_results:
            url = result.get('url', '')
            if url and url not in unique_results:
                unique_results[url] = result
        
        broad_search_results = list(unique_results.values())
        logger.info(f"Broad search found {len(broad_search_results)} unique sources")
        
        # Phase 2: Source Selection - Select top sources based on credibility
        top_sources = self._select_top_sources(broad_search_results, top_limit)
        logger.info(f"Selected {len(top_sources)} top sources for detailed analysis")
        
        # Phase 3: Content Extraction & Summarization
        detailed_summaries = self._extract_and_summarize_sources(top_sources, perspective)
        
        # Phase 4: Prepare debate-ready output
        debate_summary = self._prepare_debate_summary(detailed_summaries, perspective)
        
        return {
            "perspective_index": perspective.get('index', 0),
            "perspective_title": perspective_title,
            "perspective_content": perspective_content,
            "perspective_category": perspective_category,
            "bias_score": perspective.get('bias_x', 0.5),
            "significance_score": perspective.get('significance_y', 0.5),
            "research_methodology": {
                "broad_search_results": len(broad_search_results),
                "top_sources_selected": len(top_sources),
                "detailed_summaries_generated": len(detailed_summaries),
                "search_queries_used": search_queries
            },
            "broad_search_results": broad_search_results[:20],  # Store sample for transparency
            "top_selected_sources": top_sources,
            "detailed_content_summaries": detailed_summaries,
            "debate_ready_summary": debate_summary,
            "credibility_analysis": self._analyze_source_credibility(top_sources),
            "research_status": "completed"
        }
    
    def _generate_search_queries(self, title: str, content: str) -> List[str]:
        """Generate multiple search queries for comprehensive coverage."""
        # Extract key terms
        key_terms = title.replace(' ', ' ').split()[:3]
        content_terms = content.split()[:5]
        
        queries = [
            f"{title} research evidence",
            f"{title} scientific studies",
            f"{title} expert analysis",
            f"{' '.join(key_terms)} facts data",
            f"{' '.join(content_terms[:3])} research",
            f"{title} peer reviewed studies",
            f"{title} government reports",
            f"{title} academic research"
        ]
        
        return queries[:6]  # Limit to avoid too many API calls
    
    def _select_top_sources(self, sources: List[Dict], limit: int) -> List[Dict]:
        """Select top sources based on credibility scoring."""
        if not sources:
            return []
        
        # Score each source
        scored_sources = []
        for source in sources:
            credibility_score = self._calculate_credibility_score(source)
            source['credibility_score'] = credibility_score
            scored_sources.append(source)
        
        # Sort by credibility score (descending)
        scored_sources.sort(key=lambda x: x['credibility_score'], reverse=True)
        
        # Return top sources
        return scored_sources[:limit]
    
    def _calculate_credibility_score(self, source: Dict) -> float:
        """Calculate credibility score for a source."""
        score = 0.0
        
        domain = source.get('display_url', '').lower()
        
        # Check if it's a trusted domain
        trusted_domains = self.sources_manager.get_all_domains()
        if any(trusted_domain in domain for trusted_domain in trusted_domains):
            score += 0.8
        
        # Domain authority indicators
        if any(indicator in domain for indicator in ['.gov', '.edu', '.org']):
            score += 0.6
        elif any(indicator in domain for indicator in ['who.int', 'cdc.gov', 'nih.gov', 'nature.com']):
            score += 0.9
        elif any(indicator in domain for indicator in ['bbc.com', 'reuters.com', 'ap.org']):
            score += 0.7
        
        # Content quality indicators
        title = source.get('title', '').lower()
        snippet = source.get('snippet', '').lower()
        
        quality_terms = ['research', 'study', 'analysis', 'evidence', 'data', 'peer-reviewed', 'scientific']
        quality_score = sum(1 for term in quality_terms if term in title or term in snippet) * 0.1
        score += min(quality_score, 0.3)
        
        # Recency (if available)
        # Note: Could be enhanced with actual date parsing
        
        return min(score, 1.0)
    
    def _extract_and_summarize_sources(self, sources: List[Dict], perspective: Dict) -> List[Dict]:
        """Extract content and create summaries from top sources."""
        summaries = []
        
        # Initialize web scraper for this session
        if not self.web_scraper:
            self.web_scraper = WebScraper()
            self.web_scraper.start_session()
        
        for i, source in enumerate(sources, 1):
            try:
                logger.info(f"Extracting content from source {i}/{len(sources)}: {source['display_url']}")
                
                # Extract content using web scraper
                scrape_result = self.web_scraper.scrape_url(source['url'])
                
                if scrape_result and scrape_result.get('content'):
                    content = scrape_result['content']
                    
                    # Create summary
                    summary = {
                        "source_index": i,
                        "source_url": source['url'],
                        "source_domain": source['display_url'],
                        "source_title": scrape_result.get('title', source.get('title', 'Unknown')),
                        "credibility_score": source.get('credibility_score', 0.0),
                        "extracted_content": content[:2000],  # Limit for processing
                        "content_summary": self._summarize_content(content, perspective),
                        "relevance_to_perspective": self._assess_relevance(content, perspective),
                        "key_points": self._extract_key_points(content),
                        "stance_analysis": self._analyze_content_stance(content, perspective),
                        "scraped_at": scrape_result.get('scraped_at'),
                        "content_length": scrape_result.get('content_length', 0)
                    }
                    summaries.append(summary)
                else:
                    logger.warning(f"No content extracted from {source['display_url']}")
                    
            except Exception as e:
                logger.error(f"Error processing source {source['display_url']}: {e}")
                continue
        
        logger.info(f"Successfully processed {len(summaries)} sources for content extraction")
        return summaries
    
    def _summarize_content(self, content: str, perspective: Dict) -> str:
        """Create a focused summary of content relevant to the perspective."""
        # Simple extractive summarization (could be enhanced with Gemini API)
        sentences = content.split('.')[:10]
        perspective_terms = perspective.get('title', '').lower().split()
        
        relevant_sentences = []
        for sentence in sentences:
            if any(term in sentence.lower() for term in perspective_terms):
                relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            return '. '.join(relevant_sentences[:3]) + '.'
        else:
            return '. '.join(sentences[:2]) + '.'
    
    def _assess_relevance(self, content: str, perspective: Dict) -> float:
        """Assess how relevant the content is to the perspective."""
        perspective_terms = set(perspective.get('title', '').lower().split())
        content_words = set(content.lower().split())
        
        overlap = len(perspective_terms.intersection(content_words))
        relevance = overlap / len(perspective_terms) if perspective_terms else 0.0
        
        return min(relevance, 1.0)
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content."""
        # Simple key point extraction
        sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 50]
        
        # Look for sentences with important indicators
        key_indicators = ['research shows', 'study found', 'data indicates', 'evidence suggests', 'according to']
        key_points = []
        
        for sentence in sentences[:20]:
            if any(indicator in sentence.lower() for indicator in key_indicators):
                key_points.append(sentence)
        
        return key_points[:5]
    
    def _analyze_content_stance(self, content: str, perspective: Dict) -> Dict:
        """Analyze if content supports, opposes, or is neutral to the perspective."""
        # Simplified stance analysis
        positive_terms = ['supports', 'confirms', 'evidence for', 'proves', 'shows that']
        negative_terms = ['contradicts', 'disproves', 'evidence against', 'refutes', 'disputes']
        
        content_lower = content.lower()
        positive_count = sum(1 for term in positive_terms if term in content_lower)
        negative_count = sum(1 for term in negative_terms if term in content_lower)
        
        if positive_count > negative_count:
            stance = "supportive"
        elif negative_count > positive_count:
            stance = "opposing"
        else:
            stance = "neutral"
        
        return {
            "stance": stance,
            "confidence": abs(positive_count - negative_count) / max(positive_count + negative_count, 1),
            "positive_indicators": positive_count,
            "negative_indicators": negative_count
        }
    
    def _prepare_debate_summary(self, summaries: List[Dict], perspective: Dict) -> Dict:
        """Prepare a debate-ready summary for this perspective."""
        if not summaries:
            return {"error": "No summaries available for debate preparation"}
        
        # Aggregate information for debate
        supporting_sources = [s for s in summaries if s['stance_analysis']['stance'] == 'supportive']
        opposing_sources = [s for s in summaries if s['stance_analysis']['stance'] == 'opposing']
        neutral_sources = [s for s in summaries if s['stance_analysis']['stance'] == 'neutral']
        
        debate_summary = {
            "perspective_position": perspective.get('title', ''),
            "perspective_category": perspective.get('color', 'unknown'),
            "total_sources_analyzed": len(summaries),
            "source_distribution": {
                "supporting": len(supporting_sources),
                "opposing": len(opposing_sources),
                "neutral": len(neutral_sources)
            },
            "key_supporting_evidence": [s['content_summary'] for s in supporting_sources[:3]],
            "key_opposing_evidence": [s['content_summary'] for s in opposing_sources[:3]],
            "neutral_evidence": [s['content_summary'] for s in neutral_sources[:2]],
            "strongest_sources": sorted(summaries, key=lambda x: x['credibility_score'], reverse=True)[:3],
            "debate_talking_points": self._generate_talking_points(summaries, perspective),
            "credibility_assessment": {
                "average_credibility": sum(s['credibility_score'] for s in summaries) / len(summaries),
                "high_credibility_sources": len([s for s in summaries if s['credibility_score'] > 0.7]),
                "source_diversity": len(set(s['source_domain'] for s in summaries))
            }
        }
        
        return debate_summary
    
    def _generate_talking_points(self, summaries: List[Dict], perspective: Dict) -> List[str]:
        """Generate debate talking points from the research."""
        talking_points = []
        
        # Extract key points from all summaries
        all_key_points = []
        for summary in summaries:
            all_key_points.extend(summary.get('key_points', []))
        
        # Select most relevant talking points
        for point in all_key_points[:5]:
            if len(point) > 30:  # Ensure substantial content
                talking_points.append(point)
        
        return talking_points
    
    def _categorize_for_debate(self, perspective_result: Dict, debate_prep: Dict):
        """Categorize research results for debate preparation."""
        category = perspective_result.get('perspective_category', 'unknown')
        debate_summary = perspective_result.get('debate_ready_summary', {})
        
        if category == 'red':  # leftist
            debate_prep['leftist_summaries'].append(debate_summary)
        elif category == 'purple':  # rightist
            debate_prep['rightist_summaries'].append(debate_summary)
        elif category == 'green':  # common/centrist
            debate_prep['common_summaries'].append(debate_summary)
    
    def _generate_cross_perspective_analysis(self, research_results: Dict):
        """Generate analysis comparing perspectives for debate preparation."""
        leftist_summaries = research_results['debate_preparation']['leftist_summaries']
        rightist_summaries = research_results['debate_preparation']['rightist_summaries']
        common_summaries = research_results['debate_preparation']['common_summaries']
        
        cross_analysis = {
            "perspective_distribution": {
                "leftist_perspectives": len(leftist_summaries),
                "rightist_perspectives": len(rightist_summaries),
                "common_perspectives": len(common_summaries)
            },
            "credibility_comparison": {
                "leftist_avg_credibility": self._avg_credibility(leftist_summaries),
                "rightist_avg_credibility": self._avg_credibility(rightist_summaries),
                "common_avg_credibility": self._avg_credibility(common_summaries)
            },
            "source_overlap": self._analyze_source_overlap(research_results['perspective_research']),
            "debate_readiness_score": self._calculate_debate_readiness(research_results)
        }
        
        research_results['debate_preparation']['cross_perspective_analysis'] = cross_analysis
    
    def _avg_credibility(self, summaries: List[Dict]) -> float:
        """Calculate average credibility for a group of summaries."""
        if not summaries:
            return 0.0
        
        credibilities = []
        for summary in summaries:
            cred_assessment = summary.get('credibility_assessment', {})
            avg_cred = cred_assessment.get('average_credibility', 0.0)
            credibilities.append(avg_cred)
        
        return sum(credibilities) / len(credibilities) if credibilities else 0.0
    
    def _analyze_source_overlap(self, perspective_research: List[Dict]) -> Dict:
        """Analyze overlap in sources between perspectives."""
        all_sources = {}
        
        for research in perspective_research:
            category = research.get('perspective_category', 'unknown')
            sources = research.get('top_selected_sources', [])
            
            for source in sources:
                domain = source.get('display_url', '')
                if domain not in all_sources:
                    all_sources[domain] = []
                all_sources[domain].append(category)
        
        overlap_analysis = {
            "shared_sources": {domain: categories for domain, categories in all_sources.items() if len(set(categories)) > 1},
            "unique_sources_per_category": {},
            "total_unique_sources": len(all_sources)
        }
        
        return overlap_analysis
    
    def _calculate_debate_readiness(self, research_results: Dict) -> float:
        """Calculate overall debate readiness score."""
        perspective_research = research_results.get('perspective_research', [])
        
        if not perspective_research:
            return 0.0
        
        factors = []
        
        # Factor 1: Research completion rate
        successful = len([r for r in perspective_research if r.get('research_status') == 'completed'])
        completion_rate = successful / len(perspective_research)
        factors.append(completion_rate)
        
        # Factor 2: Average source credibility
        total_credibility = 0
        total_sources = 0
        
        for research in perspective_research:
            summaries = research.get('detailed_content_summaries', [])
            for summary in summaries:
                total_credibility += summary.get('credibility_score', 0)
                total_sources += 1
        
        avg_credibility = total_credibility / total_sources if total_sources > 0 else 0
        factors.append(avg_credibility)
        
        # Factor 3: Source diversity
        unique_domains = set()
        for research in perspective_research:
            sources = research.get('top_selected_sources', [])
            for source in sources:
                unique_domains.add(source.get('display_url', ''))
        
        source_diversity = min(len(unique_domains) / 20, 1.0)  # Normalize to 20 sources
        factors.append(source_diversity)
        
        # Overall score
        return sum(factors) / len(factors)
    
    def _analyze_source_credibility(self, sources: List[Dict]) -> Dict:
        """Analyze credibility distribution of sources."""
        if not sources:
            return {"error": "No sources to analyze"}
        
        credibility_scores = [s.get('credibility_score', 0) for s in sources]
        
        return {
            "average_credibility": sum(credibility_scores) / len(credibility_scores),
            "highest_credibility": max(credibility_scores),
            "lowest_credibility": min(credibility_scores),
            "high_credibility_count": len([s for s in credibility_scores if s > 0.7]),
            "medium_credibility_count": len([s for s in credibility_scores if 0.4 <= s <= 0.7]),
            "low_credibility_count": len([s for s in credibility_scores if s < 0.4]),
            "credibility_distribution": {
                "excellent": len([s for s in credibility_scores if s > 0.8]),
                "good": len([s for s in credibility_scores if 0.6 < s <= 0.8]),
                "fair": len([s for s in credibility_scores if 0.4 < s <= 0.6]),
                "poor": len([s for s in credibility_scores if s <= 0.4])
            }
        }


def main():
    """CLI interface for enhanced research."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Module 4: Broad Search & Top 10 Analysis")
    parser.add_argument("--input", required=True, help="Input JSON file with perspectives")
    parser.add_argument("--output", required=True, help="Output JSON file for results")
    parser.add_argument("--broad-search", type=int, default=50, help="Broad search limit")
    parser.add_argument("--top-sources", type=int, default=10, help="Top sources to analyze")
    
    args = parser.parse_args()
    
    # Load input
    with open(args.input, 'r', encoding='utf-8') as f:
        input_data = json.load(f)
    
    perspectives = input_data.get('perspectives', [])
    
    if not perspectives:
        print("No perspectives found in input file")
        return
    
    print(f"Starting enhanced research on {len(perspectives)} perspectives")
    print(f"Broad search limit: {args.broad_search}")
    print(f"Top sources limit: {args.top_sources}")
    
    # Initialize orchestrator
    orchestrator = EnhancedDeepResearchOrchestrator()
    
    # Conduct research
    results = orchestrator.conduct_enhanced_research(
        perspectives, args.broad_search, args.top_sources
    )
    
    # Save results
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"Enhanced research completed!")
    print(f"Results saved to: {args.output}")
    
    # Print summary
    metadata = results.get('enhanced_research_metadata', {})
    successful = metadata.get('successful_perspectives', 0)
    total = metadata.get('total_perspectives', 0)
    
    print(f"\nResearch Summary:")
    print(f"   Perspectives processed: {successful}/{total}")
    print(f"   Debate readiness score: {results['debate_preparation']['cross_perspective_analysis'].get('debate_readiness_score', 0):.2f}")
    print(f"   Leftist summaries: {len(results['debate_preparation']['leftist_summaries'])}")
    print(f"   Rightist summaries: {len(results['debate_preparation']['rightist_summaries'])}")
    print(f"   Common summaries: {len(results['debate_preparation']['common_summaries'])}")


if __name__ == "__main__":
    main()