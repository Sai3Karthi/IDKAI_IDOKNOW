# Module 4 Setup Guide

## Overview
Module 4 provides intelligent content analysis agents for political perspective analysis. It includes both leftist and rightist analysis agents with comprehensive web scraping and content extraction capabilities.

## Features
- **Dual Agent System**: Leftist and Rightist analysis agents
- **Smart Claim Selection**: Bias-diverse sampling for representative results
- **Comprehensive Extraction**: Full web content scraping with structured output
- **Speed Optimization**: Fast and slow analysis modes
- **JSON Output**: Complete results with extracted content and metrics

## Components

### Backend (`/backend/`)
- `leftistagent.py` - Leftist perspective analysis agent
- `rightistagent.py` - Rightist perspective analysis agent  
- `speed_test.py` - Core speed testing functionality
- `main.py` - Main entry point
- `enhanced_main.py` - Enhanced main functionality
- `Modules/` - Core analysis modules
  - `SupportAgent/` - Support agent implementations
  - `WebScraper/` - Web scraping functionality
  - `VectorDB/` - Vector database for content storage

### Data Sources
- Integrates with Module 3 JSON files:
  - `leftist.json` - Leftist perspective claims
  - `rightist.json` - Rightist perspective claims
  - `common.json` - Common/neutral claims

## Installation

### Prerequisites
- Python 3.8+
- Chrome browser (for web scraping)
- Google API credentials (for AI content processing)

### Dependencies
Install required packages:
```bash
pip install -r requirements.txt
```

### Environment Setup
1. Copy `.env.example` to `.env`
2. Configure environment variables:
   ```
   GOOGLE_API_KEY=your_google_api_key
   CHROME_DRIVER_PATH=auto
   ```

## Usage

### Leftist Agent Analysis
```bash
cd backend
python leftistagent.py
```

### Rightist Agent Analysis
```bash
cd backend
python rightistagent.py
```

### Interactive Options
Both agents provide:
1. **Slow Mode**: Process ALL claims for maximum accuracy
2. **Fast Mode**: Process diverse subset (~8 claims) for speed
3. **Both Modes**: Run comparison analysis

### Output
- JSON files with extracted content: `*_content_test_YYYYMMDD_HHMMSS.json`
- Comprehensive metrics: timing, success rates, source counts
- Full extracted web content with metadata

## Integration

### With Other Modules
- **Module 1**: Can analyze links validated by Module 1
- **Module 2**: Can process claims classified/summarized by Module 2  
- **Module 3**: Directly uses Module 3's JSON output files
- **Orchestrator**: Can be integrated into the main orchestration workflow

### API Integration
The agents can be imported and used programmatically:
```python
from backend.leftistagent import test_with_content
from backend.rightistagent import test_with_content
```

## Configuration

### Speed Modes
- **Fast Mode**: 8 claims (5 perspective + 3 common), 2 sources per claim
- **Slow Mode**: All claims, 3 sources per claim, conservative delays

### Bias Selection
Claims are selected based on color/bias diversity:
- **Leftist**: Red (strong) → Orange (moderate) → Yellow (mild)
- **Rightist**: Blue (strong) → Indigo (moderate) → Violet (mild)
- **Common**: Green (neutral)

## Performance
- **Fast Mode**: ~2-3 minutes for representative analysis
- **Slow Mode**: ~4-6 minutes for comprehensive analysis
- **Output Size**: 500KB-2MB JSON files with full content

## Troubleshooting

### Common Issues
1. **Chrome Driver**: Automatically managed by webdriver-manager
2. **Rate Limiting**: Built-in delays and fallback search mechanisms
3. **API Limits**: Google API usage tracked and optimized

### Debug Mode
Enable verbose logging by setting environment variable:
```bash
LOG_LEVEL=DEBUG
```

## Development

### Adding New Agents
1. Create new agent file in `/backend/`
2. Implement the same interface as existing agents
3. Add data loading function for new perspective
4. Update documentation

### Extending Functionality
- Add new claim selection algorithms
- Integrate additional web sources
- Enhance content extraction methods
- Add new output formats

## Version History
- v1.0: Initial leftist agent implementation
- v1.1: Added rightist agent
- v2.0: Smart bias-diverse claim selection
- v2.1: Enhanced JSON output with full content extraction