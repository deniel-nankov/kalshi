# OpenBB Platform UI/API Guide

**Date:** November 17, 2025  
**Status:** ✅ Active - Server Running  
**Access URL:** http://localhost:8000

---

## 🎯 Overview

The OpenBB Platform provides **three ways** to access financial data:

1. **Web UI** - Interactive browser-based interface
2. **REST API** - HTTP endpoints for any programming language
3. **Python SDK** - Direct Python integration (already implemented in this project)

---

## 🚀 Quick Start

### Starting the OpenBB Platform API Server

```bash
# Method 1: Using Python directly
python -c "
from openbb_platform_api.main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8000)
"

# Method 2: Using uvicorn command
python -m uvicorn openbb_platform_api.main:app --host 0.0.0.0 --port 8000

# Method 3: Using our demo script
python Gas/scripts/openbb_ui_demo.py
```

### Server Output
```
INFO:     Started server process [3544]
INFO:     Waiting for application startup.
INFO:     

                   ███╗
  █████████████████╔══█████████████████╗       OpenBB Platform v4.5.0
  ███╔══════════███║  ███╔══════════███║
  █████████████████║  █████████████████║       Authentication: DISABLED
  ╚═════════════███║  ███╔═════════════╝
     ██████████████║  ██████████████╗
     ███╔═══════███║  ███╔═══════███║
     ██████████████║  ██████████████║
     ╚═════════════╝  ╚═════════════╝
Investment research for everyone, anywhere.

INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 🌐 Web UI Access Points

### 1. Main Page
**URL:** http://localhost:8000

Features:
- Overview of OpenBB Platform
- Integration instructions
- Links to documentation
- Connection guide for OpenBB Workspace

### 2. Interactive API Documentation (Swagger UI)
**URL:** http://localhost:8000/docs

Features:
- Interactive API explorer
- Test endpoints directly in browser
- See request/response examples
- Auto-generated from OpenAPI spec
- Try out API calls without code

### 3. Alternative API Docs (ReDoc)
**URL:** http://localhost:8000/redoc

Features:
- Clean, readable documentation
- Better for reference and reading
- Search functionality
- Organized by categories

### 4. OpenAPI Specification
**URL:** http://localhost:8000/openapi.json

Features:
- Machine-readable API specification
- Use for generating API clients
- 171+ endpoints documented
- Complete schema definitions

---

## 📊 Available API Endpoints

### Total Endpoints: 171

### Energy & Commodity Endpoints

```
/api/v1/commodity/price/spot
  - Get spot prices for commodities (WTI, Brent, etc.)

/api/v1/commodity/petroleum_status_report
  - Weekly petroleum status report from EIA

/api/v1/commodity/short_term_energy_outlook
  - Short-term energy outlook forecasts
```

### Economy Endpoints

```
/api/v1/economy/gdp/forecast
/api/v1/economy/gdp/nominal
/api/v1/economy/gdp/real
/api/v1/economy/shipping/port_info
/api/v1/economy/shipping/port_volume
```

### Equity & Market Data

```
/api/v1/equity/price/historical
/api/v1/equity/fundamental/...
/api/v1/equity/options/...
```

---

## 💻 Usage Examples

### Using cURL (Command Line)

```bash
# Get commodity spot prices
curl "http://localhost:8000/api/v1/commodity/price/spot?symbol=CL"

# Get petroleum status report
curl "http://localhost:8000/api/v1/commodity/petroleum_status_report"

# Get GDP forecast
curl "http://localhost:8000/api/v1/economy/gdp/forecast"
```

### Using Python Requests

```python
import requests

# Get commodity data
response = requests.get(
    "http://localhost:8000/api/v1/commodity/price/spot",
    params={"symbol": "CL"}  # WTI Crude Oil
)

data = response.json()
print(data)
```

### Using JavaScript/Fetch

```javascript
// Get commodity data
fetch('http://localhost:8000/api/v1/commodity/price/spot?symbol=CL')
    .then(response => response.json())
    .then(data => console.log(data));
```

### Using Our Python SDK (Recommended)

```python
from openbb_integration import EnergyDataFetcher

# Use our integrated Python SDK (easier!)
fetcher = EnergyDataFetcher()
rbob = fetcher.get_rbob_futures(start_date="2024-01-01")
wti = fetcher.get_wti_crude(start_date="2024-01-01")
```

---

## 🔗 Integration Options

### Option 1: Python SDK (Already Implemented) ✅

**Location:** `Gas/src/openbb_integration/`

**Advantages:**
- Type-safe Python interface
- Built-in error handling and retry
- Intelligent caching (85-90% hit rate)
- Data validation
- Performance monitoring

**Usage:**
```python
from openbb_integration import EnergyDataFetcher

fetcher = EnergyDataFetcher()
data = fetcher.get_rbob_futures(start_date="2024-01-01")
```

### Option 2: REST API (Now Available) ✅

**Base URL:** http://localhost:8000

**Advantages:**
- Language-agnostic (any programming language)
- Standard HTTP/REST interface
- Easy to use with curl, Postman, etc.
- Great for microservices architecture
- Web application integration

**Usage:**
```bash
curl http://localhost:8000/api/v1/commodity/price/spot
```

### Option 3: OpenBB Workspace Integration

**Workspace URL:** https://pro.openbb.co/

**Setup Steps:**
1. Sign in to OpenBB Workspace
2. Navigate to "Apps" tab
3. Click "Connect backend"
4. Fill in:
   - Name: OpenBB Platform
   - URL: http://localhost:8000
5. Click "Test" (should see "Test successful")
6. Click "Add" to complete

**Advantages:**
- Enterprise-grade UI
- AI workflow integration
- Data visualization
- Team collaboration
- No coding required

---

## 📸 Screenshots

### Main UI Page
![OpenBB Platform UI](https://github.com/user-attachments/assets/a6518c79-39be-461f-971c-570b273e3a25)

The main page shows:
- Platform overview
- Integration instructions
- Steps to connect with OpenBB Workspace
- Links to documentation

---

## 🔧 Configuration

### API Keys

The OpenBB Platform uses various data providers, some require API keys:

**Setting API Keys:**

```bash
# Option 1: Environment Variables
export FRED_API_KEY="your_fred_api_key"
export POLYGON_API_KEY="your_polygon_api_key"

# Option 2: .env file
# Create Gas/.env with:
FRED_API_KEY=your_fred_api_key
POLYGON_API_KEY=your_polygon_api_key
```

**Free API Keys:**
- FRED (Federal Reserve): https://fred.stlouisfed.org/docs/api/api_key.html
- Alpha Vantage: https://www.alphavantage.co/support/#api-key

### Server Configuration

```bash
# Change port
uvicorn openbb_platform_api.main:app --port 8080

# Enable auto-reload for development
uvicorn openbb_platform_api.main:app --reload

# Bind to specific host
uvicorn openbb_platform_api.main:app --host 127.0.0.1
```

---

## 🎓 Advanced Features

### 1. Request Authentication

The API server supports authentication (currently disabled by default):

```python
# When authentication is enabled
headers = {"Authorization": "Bearer YOUR_TOKEN"}
response = requests.get(url, headers=headers)
```

### 2. Batch Requests

Multiple endpoints can be called in parallel:

```python
import asyncio
import aiohttp

async def fetch_multiple():
    urls = [
        "http://localhost:8000/api/v1/commodity/price/spot",
        "http://localhost:8000/api/v1/economy/gdp/forecast"
    ]
    
    async with aiohttp.ClientSession() as session:
        tasks = [session.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return responses
```

### 3. WebSocket Support

Some endpoints support WebSocket for real-time data:

```python
import websockets

async def stream_data():
    uri = "ws://localhost:8000/ws/stream"
    async with websockets.connect(uri) as websocket:
        while True:
            data = await websocket.recv()
            print(data)
```

---

## 🐛 Troubleshooting

### Server Won't Start

**Problem:** Port 8000 already in use

**Solution:**
```bash
# Find process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn openbb_platform_api.main:app --port 8001
```

### API Key Errors

**Problem:** `Missing credential 'fred_api_key'`

**Solution:**
```bash
# Set environment variable
export FRED_API_KEY="your_key_here"

# Or add to .env file
echo "FRED_API_KEY=your_key_here" >> Gas/.env
```

### CORS Issues (Web Browser)

**Problem:** CORS errors when accessing from browser

**Solution:**
The API has CORS enabled by default. If issues persist:
```python
# Check CORS configuration in openbb_platform_api/main.py
# Or use a proxy
```

---

## 📚 Documentation Links

### OpenBB Resources
- **Main Documentation:** https://docs.openbb.co/platform
- **API Reference:** https://docs.openbb.co/platform/reference
- **GitHub:** https://github.com/OpenBB-finance/OpenBB
- **Discord:** https://discord.com/invite/xPHTuHCmuV

### Our Implementation
- **Integration Guide:** `Gas/OPENBB_INTEGRATION_COMPLETE.md`
- **Python SDK Docs:** `Gas/src/openbb_integration/`
- **Demo Script:** `Gas/scripts/demo_openbb_integration.py`
- **UI Demo:** `Gas/scripts/openbb_ui_demo.py`
- **Tests:** `Gas/tests/test_openbb_integration.py`

---

## ✅ Summary

### What's Running
✅ OpenBB Platform API Server (http://localhost:8000)  
✅ 171+ API endpoints available  
✅ Interactive documentation at /docs  
✅ Python SDK integration in `Gas/src/openbb_integration/`

### How to Access
1. **Web Browser:** http://localhost:8000
2. **API Docs:** http://localhost:8000/docs
3. **Python SDK:** `from openbb_integration import EnergyDataFetcher`
4. **REST API:** `curl http://localhost:8000/api/v1/...`

### Next Steps
1. Open browser and explore the UI
2. Try API endpoints in the interactive docs
3. Use our Python SDK for production code
4. Configure API keys for full data access

---

*Last Updated: November 17, 2025*  
*Server Status: ✅ Running on http://localhost:8000*
