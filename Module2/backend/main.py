#!/usr/bin/env python3
import json
import re
import sys
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from Modules.Classifier.classifier import FakeNewsDetector
from Modules.SignificanceScore.scoreProvider import get_triage_score
from Modules.Summarizer.summarizer import ComprehensiveSummarizer

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables
API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))
APP_TITLE = os.getenv("APP_TITLE", "Misinformation Analysis API")
APP_DESCRIPTION = os.getenv("APP_DESCRIPTION", "API for analyzing text for misinformation using classification, significance scoring, and summarization")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

# Validate required environment variables
if not API_KEY:
    raise ValueError("API_KEY environment variable is required")

# FastAPI app instance
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION
)

# Initialize components globally with environment variables
classifier = FakeNewsDetector(API_KEY, MODEL_NAME)
summarizer = ComprehensiveSummarizer(API_KEY, MODEL_NAME)


# Pydantic models for request/response
class AnalysisRequest(BaseModel):
    text: str

class ClassificationResult(BaseModel):
    person: float
    organization: float
    social: float
    critical: float
    stem: float

class AnalysisResponse(BaseModel):
    classification: ClassificationResult
    significance_score: int
    summary: str
    source: bool

class ErrorResponse(BaseModel):
    error: str
    classification: Optional[ClassificationResult] = None
    significance_score: int = -1
    summary: Optional[str] = None
    source: bool


def has_link(text: str) -> bool:
    # Pattern to match URLs with protocol (http/https) or domain names
    url_pattern = r'(https?://[^\s]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    return bool(re.search(url_pattern, text))


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": APP_TITLE,
        "version": APP_VERSION,
        "endpoints": {
            "POST /analyze": "Analyze text for misinformation",
            "GET /health": "Health check endpoint",
            "GET /docs": "API documentation"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest):
    """
    Analyze text for misinformation using classification, significance scoring, and summarization
    
    Args:
        request: AnalysisRequest containing the text to analyze
        
    Returns:
        AnalysisResponse with classification, significance score, summary, and source detection
        
    Raises:
        HTTPException: If analysis fails
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty")
    
    try:
        # Get classification
        classification = classifier.classify(request.text)
        
        # Get significance score
        score = get_triage_score(request.text)
        
        # Get summary
        summary = summarizer.summarize(request.text)
        
        # Create response
        response = AnalysisResponse(
            classification=ClassificationResult(
                person=classification.person,
                organization=classification.organization,
                social=classification.social,
                critical=classification.critical,
                stem=classification.stem
            ),
            significance_score=score,
            summary=summary.comprehensive_summary,
            source=has_link(request.text)
        )
        
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
