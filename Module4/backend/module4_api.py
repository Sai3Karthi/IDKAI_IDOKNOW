#!/usr/bin/env python3
"""
Module 4 API Server
Simple FastAPI server for leftist and rightist agents
Provides REST endpoints for frontend integration
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import os
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

# FastAPI app
app = FastAPI(
    title="Module 4: Political Perspective Analysis Agents API",
    version="1.0.0",
    description="REST API for leftist and rightist political perspective analysis agents"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global job tracking
jobs = {}

class JobStatus(BaseModel):
    job_id: str
    status: str  # 'running', 'completed', 'error'
    progress: float
    message: str
    started_at: float
    completed_at: Optional[float] = None
    error: Optional[str] = None

class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str

class DebateRequest(BaseModel):
    leftist_job_id: str
    rightist_job_id: str

async def run_leftist_agent(job_id: str):
    """Run leftist agent in background."""
    try:
        jobs[job_id]['status'] = 'running'
        jobs[job_id]['message'] = 'Starting leftist agent analysis...'
        jobs[job_id]['progress'] = 10
        
        logger.info(f"Starting leftist agent for job {job_id}")
        
        # Import and run leftist agent
        from leftistagent import test_with_content
        
        # Update progress
        jobs[job_id]['progress'] = 25
        jobs[job_id]['message'] = 'Loading claims and initializing agent...'
        
        # Capture results by modifying the agent function temporarily
        results = await run_agent_with_capture('leftist')
        
        # Mark completion
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['progress'] = 100
        jobs[job_id]['message'] = 'Leftist agent analysis completed successfully'
        jobs[job_id]['completed_at'] = time.time()
        jobs[job_id]['results'] = results
        
        logger.info(f"Leftist agent completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"Leftist agent failed for job {job_id}: {e}")
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['error'] = str(e)
        jobs[job_id]['message'] = f'Leftist agent failed: {str(e)}'

async def run_rightist_agent(job_id: str):
    """Run rightist agent in background."""
    try:
        jobs[job_id]['status'] = 'running'
        jobs[job_id]['message'] = 'Starting rightist agent analysis...'
        jobs[job_id]['progress'] = 10
        
        logger.info(f"Starting rightist agent for job {job_id}")
        
        # Import and run rightist agent
        from rightistagent import test_with_content
        
        # Update progress
        jobs[job_id]['progress'] = 25
        jobs[job_id]['message'] = 'Loading claims and initializing agent...'
        
        # Capture results
        results = await run_agent_with_capture('rightist')
        
        # Mark completion
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['progress'] = 100
        jobs[job_id]['message'] = 'Rightist agent analysis completed successfully'
        jobs[job_id]['completed_at'] = time.time()
        jobs[job_id]['results'] = results
        
        logger.info(f"Rightist agent completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"Rightist agent failed for job {job_id}: {e}")
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['error'] = str(e)
        jobs[job_id]['message'] = f'Rightist agent failed: {str(e)}'

async def run_agent_with_capture(agent_type: str) -> Dict[str, Any]:
    """Run agent and capture output files for results."""
    try:
        if agent_type == 'leftist':
            from leftistagent import test_with_content
            await test_with_content()
        elif agent_type == 'rightist':
            from rightistagent import test_with_content
            await test_with_content()
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Find the most recent output file
        backend_dir = Path(__file__).parent
        pattern = f"{agent_type}*content_test_*.json" if agent_type == 'rightist' else "enhanced_content_test_*.json"
        
        output_files = list(backend_dir.glob(pattern))
        if not output_files:
            logger.warning(f"No output files found for {agent_type} agent")
            return {"error": "No output files generated"}
        
        # Get the most recent file
        latest_file = max(output_files, key=lambda f: f.stat().st_mtime)
        
        # Read and parse the results
        with open(latest_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Add metadata
        results['agent_type'] = agent_type
        results['output_file'] = str(latest_file)
        results['analysis_timestamp'] = datetime.now().isoformat()
        
        # Calculate summary stats
        extracted_content = results.get('extracted_content', [])
        total_urls = len(extracted_content)
        successful_urls = len([item for item in extracted_content if item.get('success', False)])
        
        results['totalUrls'] = total_urls
        results['successfulUrls'] = successful_urls
        results['successRate'] = f"{(successful_urls/total_urls*100):.1f}%" if total_urls > 0 else "0%"
        
        logger.info(f"Captured results for {agent_type} agent: {total_urls} URLs, {successful_urls} successful")
        
        return results
        
    except Exception as e:
        logger.error(f"Error capturing {agent_type} agent results: {e}")
        return {"error": str(e), "agent_type": agent_type}

async def run_debate(job_id: str, leftist_results: Dict, rightist_results: Dict):
    """Run debate between agents in background."""
    try:
        jobs[job_id]['status'] = 'running'
        jobs[job_id]['message'] = 'Starting debate between leftist and rightist agents...'
        jobs[job_id]['progress'] = 10
        
        logger.info(f"Starting debate for job {job_id}")
        
        # Import debate agent
        from Modules.DebateAgent import DebateAgent
        
        # Initialize debate agent
        debate_agent = DebateAgent()
        
        # Update progress
        jobs[job_id]['progress'] = 25
        jobs[job_id]['message'] = 'Analyzing arguments and evidence...'
        
        # Conduct debate
        debate_results = await debate_agent.conduct_debate(leftist_results, rightist_results)
        
        # Update progress
        jobs[job_id]['progress'] = 90
        jobs[job_id]['message'] = 'Generating debate summary...'
        
        # Mark completion
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['progress'] = 100
        jobs[job_id]['message'] = f'Debate completed - Winner: {debate_results.get("winner", "Tie").upper()}'
        jobs[job_id]['completed_at'] = time.time()
        jobs[job_id]['results'] = debate_results
        
        logger.info(f"Debate completed for job {job_id} - Winner: {debate_results.get('winner', 'Tie')}")
        
    except Exception as e:
        logger.error(f"Debate failed for job {job_id}: {e}")
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['error'] = str(e)
        jobs[job_id]['message'] = f'Debate failed: {str(e)}'

@app.post("/leftist/start", response_model=JobResponse)
async def start_leftist_agent(background_tasks: BackgroundTasks):
    """Start leftist agent analysis."""
    job_id = f"leftist_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    
    # Initialize job tracking
    jobs[job_id] = {
        'job_id': job_id,
        'status': 'starting',
        'progress': 0,
        'message': 'Leftist agent job created',
        'started_at': time.time(),
        'agent_type': 'leftist'
    }
    
    # Start background task
    background_tasks.add_task(run_leftist_agent, job_id)
    
    logger.info(f"Started leftist agent job: {job_id}")
    
    return JobResponse(
        job_id=job_id,
        status="starting",
        message="Leftist agent analysis started"
    )

@app.post("/rightist/start", response_model=JobResponse)
async def start_rightist_agent(background_tasks: BackgroundTasks):
    """Start rightist agent analysis."""
    job_id = f"rightist_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    
    # Initialize job tracking
    jobs[job_id] = {
        'job_id': job_id,
        'status': 'starting',
        'progress': 0,
        'message': 'Rightist agent job created',
        'started_at': time.time(),
        'agent_type': 'rightist'
    }
    
    # Start background task
    background_tasks.add_task(run_rightist_agent, job_id)
    
    logger.info(f"Started rightist agent job: {job_id}")
    
    return JobResponse(
        job_id=job_id,
        status="starting",
        message="Rightist agent analysis started"
    )

@app.get("/leftist/status/{job_id}")
async def get_leftist_status(job_id: str):
    """Get leftist agent job status."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]

@app.get("/rightist/status/{job_id}")
async def get_rightist_status(job_id: str):
    """Get rightist agent job status."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]

@app.get("/leftist/results/{job_id}")
async def get_leftist_results(job_id: str):
    """Get leftist agent results."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f"Job not completed. Status: {job['status']}")
    
    if 'results' not in job:
        raise HTTPException(status_code=500, detail="Results not available")
    
    return job['results']

@app.get("/rightist/results/{job_id}")
async def get_rightist_results(job_id: str):
    """Get rightist agent results."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f"Job not completed. Status: {job['status']}")
    
    if 'results' not in job:
        raise HTTPException(status_code=500, detail="Results not available")
    
    return job['results']

@app.post("/debate/start", response_model=JobResponse)
async def start_debate(debate_request: DebateRequest, background_tasks: BackgroundTasks):
    """Start debate between leftist and rightist agents."""
    
    # Validate that both jobs exist and are completed
    if debate_request.leftist_job_id not in jobs:
        raise HTTPException(status_code=404, detail="Leftist job not found")
    
    if debate_request.rightist_job_id not in jobs:
        raise HTTPException(status_code=404, detail="Rightist job not found")
    
    leftist_job = jobs[debate_request.leftist_job_id]
    rightist_job = jobs[debate_request.rightist_job_id]
    
    if leftist_job['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f"Leftist job not completed. Status: {leftist_job['status']}")
    
    if rightist_job['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f"Rightist job not completed. Status: {rightist_job['status']}")
    
    if 'results' not in leftist_job or 'results' not in rightist_job:
        raise HTTPException(status_code=500, detail="Agent results not available for debate")
    
    # Create debate job
    job_id = f"debate_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    
    # Initialize job tracking
    jobs[job_id] = {
        'job_id': job_id,
        'status': 'starting',
        'progress': 0,
        'message': 'Debate job created',
        'started_at': time.time(),
        'agent_type': 'debate',
        'leftist_job_id': debate_request.leftist_job_id,
        'rightist_job_id': debate_request.rightist_job_id
    }
    
    # Start background task
    background_tasks.add_task(
        run_debate, 
        job_id, 
        leftist_job['results'], 
        rightist_job['results']
    )
    
    logger.info(f"Started debate job: {job_id}")
    
    return JobResponse(
        job_id=job_id,
        status="starting",
        message="Debate between agents started"
    )

@app.get("/debate/status/{job_id}")
async def get_debate_status(job_id: str):
    """Get debate job status."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]

@app.get("/debate/results/{job_id}")
async def get_debate_results(job_id: str):
    """Get debate results."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f"Job not completed. Status: {job['status']}")
    
    if 'results' not in job:
        raise HTTPException(status_code=500, detail="Results not available")
    
    return job['results']

@app.get("/jobs")
async def list_jobs():
    """List all jobs."""
    return {
        "jobs": [
            {
                "job_id": job_id,
                "status": job["status"],
                "agent_type": job.get("agent_type", "unknown"),
                "started_at": job["started_at"],
                "message": job["message"],
                "progress": job.get("progress", 0)
            }
            for job_id, job in jobs.items()
        ]
    }

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job from tracking."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    del jobs[job_id]
    return {"message": f"Job {job_id} deleted"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "module": "Module 4: Political Perspective Analysis Agents API",
        "version": "1.0.0",
        "active_jobs": len(jobs),
        "components": {
            "leftist_agent": True,
            "rightist_agent": True,
            "job_tracking": True
        }
    }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Module 4: Political Perspective Analysis Agents API",
        "version": "1.0.0",
        "description": "REST API for leftist and rightist political perspective analysis agents",
        "endpoints": {
            "leftist": {
                "start": "POST /leftist/start",
                "status": "GET /leftist/status/{job_id}",
                "results": "GET /leftist/results/{job_id}"
            },
            "rightist": {
                "start": "POST /rightist/start", 
                "status": "GET /rightist/status/{job_id}",
                "results": "GET /rightist/results/{job_id}"
            },
            "general": {
                "health": "GET /health",
                "jobs": "GET /jobs",
                "delete_job": "DELETE /jobs/{job_id}"
            },
            "debate": {
                "start": "POST /debate/start",
                "status": "GET /debate/status/{job_id}",
                "results": "GET /debate/results/{job_id}"
            }
        }
    }

if __name__ == "__main__":
    import argparse
    import uvicorn
    
    parser = argparse.ArgumentParser(description="Module 4 API Server")
    parser.add_argument("--port", type=int, default=8004, help="Server port")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    print("="*70)
    print("🚀 MODULE 4 API SERVER")
    print("="*70)
    print(f"🌐 Server: http://{args.host}:{args.port}")
    print(f"📋 API Docs: http://{args.host}:{args.port}/docs")
    print(f"🔴 Leftist Agent: POST /leftist/start")
    print(f"🔵 Rightist Agent: POST /rightist/start")
    print(f"📊 Health Check: GET /health")
    print("="*70)
    
    uvicorn.run(
        "module4_api:app" if not args.reload else app,
        host=args.host,
        port=args.port,
        reload=args.reload
    )