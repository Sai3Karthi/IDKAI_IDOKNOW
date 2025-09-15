#!/usr/bin/env python3
"""
FastAPI URL Validator - Clean and powerful
URL safety checker with content scraping API.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from Modules.LinkValidator.linkValidator import LinkValidator
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="URL Validator API",
    description="Validate URLs for safety and scrape content from safe URLs",
    version="1.0.0"
)

# API Keys from environment variables
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
VIRUSTOTAL_API_KEY = os.getenv('VIRUSTOTAL_API_KEY')

# Validate API keys are present
if not GOOGLE_API_KEY or not VIRUSTOTAL_API_KEY:
    raise ValueError("API keys not found! Please check your .env file.")

# Initialize validator
validator = LinkValidator(GOOGLE_API_KEY, VIRUSTOTAL_API_KEY)

class URLRequest(BaseModel):
    url: str

class URLResponse(BaseModel):
    safe: bool
    content: str

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "URL Validator API",
        "endpoints": {
            "POST /validate": "Validate URL and scrape content if safe",
            "GET /health": "Health check"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "URL Validator API"}

@app.post("/validate", response_model=URLResponse)
async def validate_url(request: URLRequest):
    """
    Validate URL safety and scrape content if safe.
    
    - **url**: The URL to validate and scrape
    
    Returns:
    - **safe**: Boolean indicating if URL is safe
    - **content**: Scraped text content (only if safe)
    """
    try:
        if not request.url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        # Validate URL safety
        validation_result = validator.validate_url(request.url)
        
        # Prepare response
        response = {
            "safe": validation_result.get('safe', False),
            "content": ""
        }
        
        # If safe, scrape content
        if validation_result.get('safe') is True:
            scraped_data = validator.scrape_website_content(validation_result.get('url', request.url))
            response["content"] = scraped_data.get('main_text', '') if scraped_data else ''
        
        return JSONResponse(content=response)
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "safe": False,
                "content": ""
            }
        )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.2", port=8000)
