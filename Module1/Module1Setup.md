# URL Validator API

A powerful and clean FastAPI service that validates URL safety using Google Safe Browsing and VirusTotal APIs, and scrapes content from safe URLs.

## Features

- **🛡️ Dual Security Validation**: Google Safe Browsing + VirusTotal APIs
- **🔍 Smart Content Scraping**: Extracts main text content from safe URLs only
- **⚡ FastAPI REST API**: Clean JSON responses with automatic documentation
- **🚀 Production Ready**: Minimal, efficient, and scalable
- **🎯 Simple Integration**: Easy to use with any application

## Quick Start

### 1. Installation

```bash
cd Module1
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the `Module1/` directory:

```bash
GOOGLE_API_KEY=your_google_api_key_here
VIRUSTOTAL_API_KEY=your_virustotal_api_key_here
```

### 3. Start the API Server

```bash
cd backend
python main.py
```

The API will be available at `http://127.0.0.2:8000`

### 3. API Documentation

Visit `http://127.0.0.2:8000/docs` for interactive API documentation.

## API Endpoints

### POST `/validate`

Validates a URL and scrapes content if safe.

**Request:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "safe": true,
  "content": "Main text content from the website..."
}
```

### GET `/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "URL Validator API"
}
```

## Usage Examples

### cURL
```bash
curl -X POST "http://127.0.0.2:8000/validate" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.wikipedia.org"}'
```

### Python
```python
import requests

response = requests.post(
    "http://127.0.0.2:8000/validate",
    json={"url": "https://www.wikipedia.org"}
)

result = response.json()
print(f"Safe: {result['safe']}")
if result['safe']:
    print(f"Content: {result['content'][:100]}...")
```

### JavaScript
```javascript
fetch('http://127.0.0.2:8000/validate', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        url: 'https://www.wikipedia.org'
    })
})
.then(response => response.json())
.then(data => {
    console.log('Safe:', data.safe);
    if (data.safe) {
        console.log('Content:', data.content.substring(0, 100) + '...');
    }
});
```

## How It Works

### 1. **URL Safety Validation**
- **Google Safe Browsing API**: Checks against malware, phishing, and social engineering threats
- **VirusTotal API**: Scans with 70+ security engines for comprehensive threat detection
- **Pattern Analysis**: Validates URL structure for suspicious patterns (IP addresses, URL shorteners, etc.)

### 2. **Smart Content Scraping**
- Only scrapes content from URLs marked as **safe**
- Uses Selenium + Chrome headless browser for dynamic content
- Extracts clean main text content (removes scripts, navigation, etc.)
- Limited to 3000 characters for optimal performance

### 3. **Safety Logic**
- **Safe**: All security checks pass ✅
- **Unsafe**: Any security engine detects threats ⚠️
- **Conservative Approach**: If any doubt exists, URL is marked unsafe

## Response Format

The API returns clean JSON with only essential data:

```json
{
  "safe": boolean,    // true if URL is safe, false otherwise
  "content": string   // scraped text content (empty if unsafe)
}
```

## Security Features

- **Multi-layered Protection**: Combines multiple threat detection services
- **Real-time Analysis**: Fresh scanning for new/unknown URLs
- **Pattern Detection**: Identifies common malicious URL structures
- **Rate Limiting**: Respects API quotas and prevents abuse
- **No Data Persistence**: No logs or files created during operation

## Configuration

The API uses these services:
- **Google Safe Browsing API**: Requires valid API key
- **VirusTotal API**: Requires valid API key

### API Key Setup

1. Create a `.env` file in the `Module1/` directory
2. Add your API keys:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   VIRUSTOTAL_API_KEY=your_virustotal_api_key_here
   ```
3. The application will automatically load these keys on startup

### Getting API Keys

**Google Safe Browsing API:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Safe Browsing API
3. Create credentials (API key)
4. Enable billing for your project

**VirusTotal API:**
1. Create account at [VirusTotal](https://www.virustotal.com/)
2. Get your API key from your profile

## Dependencies

- `fastapi>=0.104.0` - Modern web framework
- `uvicorn>=0.24.0` - ASGI server
- `selenium>=4.15.0` - Web scraping
- `beautifulsoup4>=4.12.0` - HTML parsing
- `requests>=2.31.0` - HTTP client
- `webdriver-manager>=4.0.0` - Chrome driver management
- `python-dotenv>=1.0.0` - Environment variable management

## Project Structure

```
Module1/
├── .env                                 # Environment variables (API keys)
├── .gitignore                          # Git ignore file
├── backend/
│   ├── main.py                          # FastAPI application
│   └── Modules/
│       └── LinkValidator/
│           └── linkValidator.py         # Core validation logic
├── requirements.txt                     # Dependencies
└── README.md                           # This file
```

## Performance

- **Average Response Time**: 2-5 seconds (includes security checks + scraping)
- **Rate Limits**: 
  - Google Safe Browsing: 1 request/second
  - VirusTotal: 4 requests/minute (free tier)
- **Content Limit**: 3000 characters max
- **Memory Usage**: Minimal (headless browser auto-cleanup)

## Error Handling

The API handles errors gracefully:
- Invalid URLs return `{"safe": false, "content": ""}`
- API timeouts are handled automatically
- All errors return proper HTTP status codes
- No error details exposed in JSON response for security

## Production Deployment

For production use:

1. **Environment Variables**: ✅ Already implemented with .env file
2. **HTTPS**: Use reverse proxy (nginx) with SSL certificates
3. **Scaling**: Use multiple uvicorn workers
4. **Monitoring**: Add logging and metrics collection
5. **Rate Limiting**: Implement request rate limiting

Example production command:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is open source and available under the MIT License.

---

**Built with ❤️ for secure web browsing and content analysis.**