# Module 4: Political Perspective Analysis Agents

## 🎯 Overview
Module 4 provides intelligent content analysis agents for processing political perspectives. It features dual agents (leftist and rightist) with sophisticated web scraping, content extraction, and bias-diverse claim selection.

## 🚀 Quick Start

### Option 1: Interactive Main Interface
```bash
python module4_main.py
```

### Option 2: Direct Agent Execution
```bash
# Leftist agent
cd backend
python leftistagent.py

# Rightist agent  
cd backend
python rightistagent.py
```

### Option 3: Windows Batch File
```bash
start_module4.bat
```

## 📋 Features

### 🤖 Dual Agent System
- **🔴 Leftist Agent**: Processes leftist + common claims from Module 3
- **🔵 Rightist Agent**: Processes rightist + common claims from Module 3
- **🔄 Comparative Mode**: Run both agents for side-by-side analysis

### ⚡ Smart Analysis Modes
- **Fast Mode**: ~8 bias-diverse claims, 2-3 minutes
- **Slow Mode**: All claims, 4-6 minutes  
- **Both Modes**: Comparison with performance metrics

### 🎨 Bias-Diverse Selection
Claims selected based on color/bias distribution:
- **Leftist**: Red (strong) → Orange (moderate) → Yellow (mild)
- **Rightist**: Blue (strong) → Indigo (moderate) → Violet (mild)
- **Common**: Green (neutral)

### 📊 Comprehensive Output
- **JSON Files**: Complete extracted content with metadata
- **Performance Metrics**: Timing, success rates, source counts
- **Content Analysis**: Full web scraping results
- **Structured Data**: Ready for further processing

## 📁 Project Structure
```
Module4/
├── module4_main.py          # Main entry point
├── start_module4.bat        # Windows quick start
├── Module4Setup.md          # Detailed setup guide
├── README.md               # This file
├── requirements.txt        # Python dependencies
├── .env.example           # Environment configuration template
├── .env                   # Your environment variables (create from .env.example)
└── backend/               # Core functionality
    ├── leftistagent.py    # Leftist analysis agent
    ├── rightistagent.py   # Rightist analysis agent
    ├── speed_test.py      # Core testing functionality
    ├── main.py           # Original main module
    ├── enhanced_main.py  # Enhanced functionality
    └── Modules/          # Supporting modules
        ├── SupportAgent/ # Agent implementations
        ├── WebScraper/   # Web scraping engine
        └── VectorDB/     # Content storage
```

## ⚙️ Configuration

### Environment Setup
1. Copy `.env.example` to `.env`
2. Configure your API keys:
   ```bash
   GOOGLE_CSE_API_KEY=your_api_key
   GEMINI_API_KEY=your_gemini_key
   GOOGLE_CSE_ID=your_search_engine_id
   ```

### Dependencies
```bash
pip install -r requirements.txt
```

## 🔗 Integration

### With Other Modules
- **Module 1**: Link validation integration
- **Module 2**: Claim classification integration
- **Module 3**: Direct JSON data consumption
- **Orchestrator**: Main workflow integration

### Data Flow
```
Module 3 JSON → Module 4 Agents → Enhanced Analysis → JSON Output
```

## 📈 Performance

### Typical Results
- **Fast Mode**: 8 claims in ~2-3 minutes
- **Slow Mode**: 16 claims in ~4-6 minutes
- **Success Rate**: 95%+ with fallback mechanisms
- **Output Size**: 500KB-2MB JSON files

### Optimization Features
- Intelligent rate limiting
- Fallback search mechanisms
- Parallel processing where possible
- Vector database for content deduplication

## 🛠️ Usage Examples

### Interactive Mode
```python
python module4_main.py
# Select option 1 (Leftist) or 2 (Rightist) or 3 (Both)
```

### Programmatic Usage
```python
from backend.leftistagent import test_with_content as leftist_test
from backend.rightistagent import test_with_content as rightist_test

# Run leftist analysis
await leftist_test()

# Run rightist analysis  
await rightist_test()
```

## 📊 Output Format

### JSON Structure
```json
{
  "test_session": {
    "timestamp": "2025-09-20T12:34:56",
    "test_type": "leftist_content_test",
    "agent_type": "leftist",
    "choice_selected": "2"
  },
  "results": [{
    "mode": "fast",
    "data": {
      "claims_with_content": [{
        "claim_text": "...",
        "extracted_content": [...],
        "sources_found": [...],
        "processing_time_seconds": 12.5
      }]
    }
  }]
}
```

## 🔧 Troubleshooting

### Common Issues
1. **Chrome Driver**: Auto-managed by webdriver-manager
2. **API Rate Limits**: Built-in delays and retry logic
3. **Import Errors**: Ensure you're in the correct directory

### Debug Mode
```bash
LOG_LEVEL=DEBUG python module4_main.py
```

## 🎯 Best Practices

### For Fast Analysis
- Use Fast Mode for quick insights
- Check color distribution in output
- Review bias diversity metrics

### For Comprehensive Analysis  
- Use Slow Mode for complete coverage
- Allow 5-10 minutes for full processing
- Check all claim types are represented

### For Comparative Analysis
- Use Both Modes option
- Compare timing vs accuracy trade-offs
- Analyze bias representation differences

## 📝 Version History
- **v1.0**: Initial leftist agent
- **v1.1**: Added rightist agent
- **v2.0**: Smart bias-diverse selection
- **v2.1**: Enhanced JSON output
- **v2.2**: Module 4 integration

## 🤝 Contributing
See main project guidelines for contribution standards.

## 📜 License
Part of the IDKAI_IDOKNOW project.