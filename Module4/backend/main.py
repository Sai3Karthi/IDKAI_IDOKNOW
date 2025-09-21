import json
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import os
import sys

# Add modules to path
sys.path.append(str(Path(__file__).parent / "Modules"))

from TrustedSources.sources_manager import TrustedSourcesManager
from WebScraper.web_scraper import WebScraper
from ResearchSummarizer.research_summarizer import GoogleCSEResearcher

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Module 4: Deep Research & Analysis", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class PerspectiveInput(BaseModel):
    index: int
    title: str
    perspective: str
    color: Optional[str] = None
    bias_x: Optional[float] = None
    significance_y: Optional[float] = None

class ResearchRequest(BaseModel):
    perspectives: List[PerspectiveInput]
    max_sources_per_perspective: Optional[int] = 10
    use_web_scraping: Optional[bool] = True
    use_cse_search: Optional[bool] = True
    include_images: Optional[bool] = False

class ResearchResponse(BaseModel):
    job_id: str
    status: str
    message: str

# Global state management
research_jobs = {}
job_counter = 0

class DeepResearchOrchestrator:
    """Main orchestrator for deep research on perspectives."""
    
    def __init__(self):
        self.sources_manager = TrustedSourcesManager()
        self.web_scraper = None
        self.cse_researcher = None
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize research components."""
        try:
            # Initialize CSE researcher
            self.cse_researcher = GoogleCSEResearcher()
            logger.info("Google CSE researcher initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CSE researcher: {e}")
            self.cse_researcher = None
        
        # Web scraper will be initialized per session
        logger.info("Deep research orchestrator initialized")
    
    def conduct_research(self, perspectives: List[Dict[str, Any]], 
                        max_sources: int = 10, 
                        use_scraping: bool = True, 
                        use_cse: bool = True,
                        include_images: bool = False) -> Dict[str, Any]:
        """
        Conduct comprehensive research on multiple perspectives.
        
        Args:
            perspectives: List of perspective data from Module 3
            max_sources: Maximum sources to research per perspective
            use_scraping: Whether to use web scraping
            use_cse: Whether to use CSE search
            include_images: Whether to include image search results
            
        Returns:
            Comprehensive research results
        """
        logger.info(f"Starting deep research on {len(perspectives)} perspectives")
        
        research_results = {
            "research_metadata": {
                "total_perspectives": len(perspectives),
                "max_sources_per_perspective": max_sources,
                "use_web_scraping": use_scraping,
                "use_cse_search": use_cse,
                "include_images": include_images,
                "started_at": time.time(),
                "completed_at": None
            },
            "perspective_research": []
        }
        
        # Process each perspective
        for i, perspective in enumerate(perspectives, 1):
            logger.info(f"Processing perspective {i}/{len(perspectives)}: {perspective.get('title', 'Unknown')}")
            
            try:
                perspective_result = self._research_single_perspective(
                    perspective, max_sources, use_scraping, use_cse, include_images
                )
                research_results["perspective_research"].append(perspective_result)
                
            except Exception as e:
                logger.error(f"Error researching perspective {i}: {e}")
                # Add error entry
                error_result = {
                    "perspective_index": perspective.get('index', i-1),
                    "perspective_title": perspective.get('title', 'Unknown'),
                    "error": str(e),
                    "research_status": "failed"
                }
                research_results["perspective_research"].append(error_result)
            
            # Add delay between perspectives
            if i < len(perspectives):
                time.sleep(2)
        
        research_results["research_metadata"]["completed_at"] = time.time()
        
        # Calculate summary statistics
        successful_research = [r for r in research_results["perspective_research"] if "error" not in r]
        research_results["research_metadata"]["successful_perspectives"] = len(successful_research)
        research_results["research_metadata"]["failed_perspectives"] = len(perspectives) - len(successful_research)
        
        logger.info(f"Deep research completed. {len(successful_research)}/{len(perspectives)} perspectives researched successfully")
        
        return research_results
    
    def _research_single_perspective(self, perspective: Dict[str, Any], 
                                   max_sources: int, 
                                   use_scraping: bool, 
                                   use_cse: bool,
                                   include_images: bool) -> Dict[str, Any]:
        """Research a single perspective using available methods."""
        perspective_title = perspective.get('title', '')
        
        result = {
            "perspective_index": perspective.get('index', 0),
            "perspective_title": perspective_title,
            "perspective_content": perspective.get('perspective', ''),
            "research_methods_used": [],
            "research_sources": [],
            "research_summary": None,
            "confidence_score": 0.0,
            "research_status": "completed",
            "include_images": include_images
        }
        
        all_sources = []
        
        # Method 1: Google CSE Research
        if use_cse and self.cse_researcher:
            try:
                logger.info(f"Conducting CSE research for: {perspective_title}")
                cse_results = self.cse_researcher.research_perspective(perspective, include_images=include_images)
                
                result["research_methods_used"].append("google_cse")
                result["cse_research"] = cse_results
                
                # Add CSE sources to all sources
                cse_sources = cse_results.get("all_sources", [])
                for source in cse_sources:
                    source["research_method"] = "google_cse"
                    all_sources.append(source)
                
                logger.info(f"CSE research found {len(cse_sources)} sources ({cse_results.get('text_sources', 0)} text, {cse_results.get('image_sources', 0)} images)")
                
            except Exception as e:
                logger.error(f"CSE research failed for {perspective_title}: {e}")
        
        # Method 2: Web Scraping (on trusted sources)
        if use_scraping and len(all_sources) > 0:
            try:
                logger.info(f"Conducting web scraping for: {perspective_title}")
                
                # Filter to trusted sources only
                trusted_sources = self.sources_manager.filter_trusted_results(all_sources)
                
                if trusted_sources:
                    # Limit to top sources
                    top_sources = trusted_sources[:min(max_sources, 10)]
                    urls_to_scrape = [source.get('url', '') for source in top_sources if source.get('url')]
                    
                    if urls_to_scrape:
                        # Initialize web scraper for this session
                        scraper = WebScraper(headless=True, timeout=30, delay_range=(2, 4))
                        
                        try:
                            scraped_results = scraper.scrape_multiple_urls(urls_to_scrape)
                            
                            result["research_methods_used"].append("web_scraping")
                            result["scraped_content"] = scraped_results
                            
                            # Merge scraped content with CSE results
                            for scraped in scraped_results:
                                scraped["research_method"] = "web_scraping"
                                # Find matching CSE result and merge
                                for source in all_sources:
                                    if source.get('url') == scraped.get('url'):
                                        source.update(scraped)
                                        break
                            
                            logger.info(f"Web scraping completed for {len(scraped_results)} URLs")
                            
                        except Exception as scraping_error:
                            logger.error(f"Web scraping failed: {scraping_error}")
                
            except Exception as e:
                logger.error(f"Web scraping setup failed for {perspective_title}: {e}")
        
        # Finalize results
        result["research_sources"] = all_sources[:max_sources]
        result["total_sources_found"] = len(all_sources)
        
        # Generate final summary if we have CSE research
        if "cse_research" in result and result["cse_research"]:
            cse_summary = result["cse_research"].get("research_summary", {})
            result["research_summary"] = cse_summary.get("summary", "No summary available")
            result["confidence_score"] = cse_summary.get("confidence_score", 0.0)
        else:
            # Create basic summary
            result["research_summary"] = f"Found {len(all_sources)} sources for perspective: {perspective_title}"
            result["confidence_score"] = min(0.7, len(all_sources) / 10.0)
        
        return result

# Global orchestrator instance
orchestrator = DeepResearchOrchestrator()

@app.post("/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Start deep research on perspectives."""
    global job_counter
    job_counter += 1
    job_id = f"research_job_{job_counter}_{int(time.time())}"
    
    # Convert Pydantic models to dictionaries
    perspectives_data = [p.dict() for p in request.perspectives]
    
    # Initialize job tracking
    research_jobs[job_id] = {
        "status": "started",
        "progress": 0,
        "message": "Research job initiated",
        "started_at": time.time(),
        "results": None,
        "error": None
    }
    
    # Start background research
    background_tasks.add_task(
        run_research_job,
        job_id,
        perspectives_data,
        request.max_sources_per_perspective,
        request.use_web_scraping,
        request.use_cse_search,
        request.include_images
    )
    
    return ResearchResponse(
        job_id=job_id,
        status="started",
        message=f"Deep research started for {len(request.perspectives)} perspectives"
    )

async def run_research_job(job_id: str, perspectives: List[Dict], 
                          max_sources: int, use_scraping: bool, use_cse: bool, include_images: bool):
    """Run research job in background."""
    try:
        research_jobs[job_id]["status"] = "running"
        research_jobs[job_id]["message"] = "Conducting deep research..."
        research_jobs[job_id]["progress"] = 10
        
        # Conduct research
        results = orchestrator.conduct_research(
            perspectives=perspectives,
            max_sources=max_sources,
            use_scraping=use_scraping,
            use_cse=use_cse,
            include_images=include_images
        )
        
        # Update job status
        research_jobs[job_id]["status"] = "completed"
        research_jobs[job_id]["progress"] = 100
        research_jobs[job_id]["message"] = "Research completed successfully"
        research_jobs[job_id]["results"] = results
        research_jobs[job_id]["completed_at"] = time.time()
        
        # Save results to file
        output_file = Path(__file__).parent / f"research_results_{job_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Research job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Research job {job_id} failed: {e}")
        research_jobs[job_id]["status"] = "failed"
        research_jobs[job_id]["error"] = str(e)
        research_jobs[job_id]["message"] = f"Research failed: {str(e)}"

@app.get("/status/{job_id}")
async def get_research_status(job_id: str):
    """Get research job status."""
    if job_id not in research_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return research_jobs[job_id]

@app.get("/results/{job_id}")
async def get_research_results(job_id: str):
    """Get research results."""
    if job_id not in research_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = research_jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job not completed. Status: {job['status']}")
    
    if job["results"] is None:
        raise HTTPException(status_code=500, detail="Results not available")
    
    return job["results"]

@app.get("/jobs")
async def list_research_jobs():
    """List all research jobs."""
    return {
        "jobs": [
            {
                "job_id": job_id,
                "status": job["status"],
                "started_at": job["started_at"],
                "message": job["message"]
            }
            for job_id, job in research_jobs.items()
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "module": "Module 4: Deep Research & Analysis",
        "components": {
            "trusted_sources_manager": True,
            "cse_researcher": orchestrator.cse_researcher is not None,
            "web_scraper": True
        }
    }

# Command-line interface for direct usage
def run_cli(input_file: str, output_file: str, max_sources: int = 10, include_images: bool = False):
    """Command-line interface for running research."""
    try:
        # Load perspectives from input file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        perspectives = data.get('perspectives', [])
        if not perspectives:
            print("No perspectives found in input file")
            return
        
        print(f"Starting deep research on {len(perspectives)} perspectives...")
        if include_images:
            print("Including image search results...")
        
        # Conduct research
        results = orchestrator.conduct_research(
            perspectives=perspectives,
            max_sources=max_sources,
            use_scraping=True,
            use_cse=True,
            include_images=include_images
        )
        
        # Save results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"Research completed. Results saved to {output_file}")
        
        # Print summary
        metadata = results["research_metadata"]
        print(f"\nSummary:")
        print(f"  Total perspectives: {metadata['total_perspectives']}")
        print(f"  Successful research: {metadata['successful_perspectives']}")
        print(f"  Failed research: {metadata['failed_perspectives']}")
        
    except Exception as e:
        print(f"Error: {e}")
        logger.exception("Detailed error information:")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Module 4: Deep Research & Analysis")
    parser.add_argument("--input", help="Input JSON file with perspectives")
    parser.add_argument("--output", help="Output JSON file for results")
    parser.add_argument("--max-sources", type=int, default=10, help="Maximum sources per perspective")
    parser.add_argument("--include-images", action="store_true", help="Include image search results")
    parser.add_argument("--speed-mode", action="store_true", help="Enable speed mode (faster but less accurate)")
    parser.add_argument("--server", action="store_true", help="Run as FastAPI server")
    parser.add_argument("--port", type=int, default=8004, help="Server port")
    
    args = parser.parse_args()
    
    if args.speed_mode:
        print("⚡ SPEED MODE ENABLED ⚡")
        print("🔸 Processing will be faster but less accurate")
        print("🔸 Using 2 sources per claim instead of 3")
        print("🔸 Aggressive rate limiting for maximum speed")
        print()
    
    if args.server:
        import uvicorn
        print("Starting Module 4 server...")
        uvicorn.run(app, host="0.0.0.0", port=args.port)
    elif args.input and args.output:
        run_cli(args.input, args.output, args.max_sources, args.include_images, args.speed_mode)
    else:
        print("Use --server to run as API server, or provide --input and --output for CLI mode")
        print("Add --include-images to search for both text and images")
        print("Add --speed-mode for faster processing with reduced accuracy")
        parser.print_help()