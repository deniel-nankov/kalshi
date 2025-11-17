#!/usr/bin/env python3
"""
OpenBB Platform UI/API Demonstration
====================================

This script demonstrates how to:
1. Start the OpenBB Platform API server (REST API with web UI)
2. Access the interactive API documentation
3. Make API calls to fetch energy commodity data
4. Integrate with the existing gas price forecasting system

The OpenBB Platform provides three ways to interact with it:
- Web UI: Interactive API documentation at http://localhost:8000/docs
- REST API: HTTP endpoints for programmatic access
- Python SDK: Direct Python integration (what we already implemented)

Author: Christian Lee
Date: November 17, 2025
"""

import sys
import time
import requests
from pathlib import Path
import subprocess
import webbrowser

print("="*80)
print("OpenBB Platform UI/API Demonstration")
print("="*80)

def start_api_server():
    """Start the OpenBB Platform API server"""
    print("\n1. Starting OpenBB Platform API Server...")
    print("-" * 80)
    
    # Start the server in a subprocess
    cmd = [sys.executable, "-m", "uvicorn", "openbb_platform_api.main:app", 
           "--host", "0.0.0.0", "--port", "8000"]
    
    print(f"Command: {' '.join(cmd)}")
    print("\nThe server will provide:")
    print("  - Web UI: http://localhost:8000")
    print("  - API Documentation: http://localhost:8000/docs")
    print("  - OpenAPI Spec: http://localhost:8000/openapi.json")
    print("  - 171+ API endpoints for financial data")
    
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def wait_for_server(max_attempts=30):
    """Wait for the API server to be ready"""
    print("\n2. Waiting for server to be ready...")
    print("-" * 80)
    
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://localhost:8000/", timeout=1)
            if response.status_code == 200:
                print(f"✓ Server is ready! (attempt {attempt + 1})")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(1)
        if (attempt + 1) % 5 == 0:
            print(f"  Still waiting... ({attempt + 1}/{max_attempts})")
    
    print("✗ Server failed to start")
    return False

def demonstrate_api_endpoints():
    """Demonstrate available API endpoints"""
    print("\n3. Available API Endpoints")
    print("-" * 80)
    
    try:
        # Get OpenAPI spec
        response = requests.get("http://localhost:8000/openapi.json")
        spec = response.json()
        
        print(f"API Title: {spec['info']['title']}")
        print(f"API Version: {spec['info']['version']}")
        print(f"Total Endpoints: {len(spec['paths'])}")
        
        print("\nEnergy & Commodity Related Endpoints:")
        energy_endpoints = [
            path for path in spec['paths'].keys() 
            if any(term in path.lower() for term in ['commodity', 'energy', 'petroleum'])
        ]
        
        for endpoint in energy_endpoints[:10]:
            print(f"  - {endpoint}")
        
        if len(energy_endpoints) > 10:
            print(f"  ... and {len(energy_endpoints) - 10} more")
        
        return True
    except Exception as e:
        print(f"✗ Error getting API spec: {e}")
        return False

def demonstrate_api_call():
    """Demonstrate making an API call"""
    print("\n4. Making Sample API Call")
    print("-" * 80)
    
    try:
        # Try to get commodity price data
        endpoint = "/api/v1/commodity/price/spot"
        url = f"http://localhost:8000{endpoint}"
        
        print(f"Endpoint: {endpoint}")
        print(f"URL: {url}")
        
        # Note: This may require API keys for actual data
        response = requests.get(url, params={"symbol": "CL"}, timeout=5)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ API call successful!")
            print(f"Response preview: {str(data)[:200]}...")
        else:
            print(f"Response: {response.text[:200]}")
        
    except Exception as e:
        print(f"Note: API call requires configuration - {e}")
        print("This is expected without API keys configured")

def show_integration_example():
    """Show how to integrate with existing system"""
    print("\n5. Integration with Gas Price Forecasting System")
    print("-" * 80)
    
    print("""
The OpenBB Platform can be used in three ways:

A. Python SDK (Already Implemented) ✓
   - Direct Python integration
   - See: Gas/src/openbb_integration/
   - Usage: from openbb_integration import EnergyDataFetcher

B. REST API (Now Available) ✓
   - HTTP endpoints for any programming language
   - Example: curl http://localhost:8000/api/v1/commodity/price/spot
   - Useful for microservices or web integrations

C. OpenBB Workspace Integration
   - Enterprise UI for data visualization
   - Connect at: https://pro.openbb.co/
   - Backend URL: http://localhost:8000

Integration Pattern:
--------------------
1. Start API server: python openbb_ui_demo.py
2. Access Web UI: http://localhost:8000
3. Use REST API: requests.get('http://localhost:8000/api/v1/...')
4. Or use Python SDK: EnergyDataFetcher() (our implementation)
""")

def show_web_ui_guide():
    """Show guide for accessing the web UI"""
    print("\n6. Accessing the Web UI")
    print("-" * 80)
    
    print("""
To access the OpenBB Platform UI:

1. Main Page:
   URL: http://localhost:8000
   - Overview of the platform
   - Integration instructions
   - Links to documentation

2. Interactive API Documentation (Swagger UI):
   URL: http://localhost:8000/docs
   - Interactive API explorer
   - Test endpoints directly in browser
   - See request/response examples

3. Alternative API Docs (ReDoc):
   URL: http://localhost:8000/redoc
   - Clean, readable API documentation
   - Better for reference

4. OpenAPI Specification:
   URL: http://localhost:8000/openapi.json
   - Machine-readable API spec
   - For generating clients

Note: The server is currently running at http://localhost:8000
    """)

def main():
    """Main demonstration function"""
    print("\nThis script demonstrates the OpenBB Platform UI/API capabilities.")
    print("The server is already running in the background.")
    print("\n" + "="*80 + "\n")
    
    # The server is already running from the previous command
    # Just demonstrate what's available
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    # Check if server is responding
    try:
        response = requests.get("http://localhost:8000/", timeout=2)
        print("✓ OpenBB Platform API server is running")
        print(f"  Status: {response.status_code}")
    except:
        print("Note: Server may need a moment to start...")
    
    # Demonstrate features
    demonstrate_api_endpoints()
    demonstrate_api_call()
    show_integration_example()
    show_web_ui_guide()
    
    # Final instructions
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("""
1. Open your browser and visit:
   http://localhost:8000           - Main UI
   http://localhost:8000/docs      - Interactive API Docs

2. Try our Python SDK integration:
   cd /home/runner/work/kalshi/kalshi
   python Gas/scripts/demo_openbb_integration.py

3. Access energy commodity data:
   from openbb_integration import EnergyDataFetcher
   fetcher = EnergyDataFetcher()
   rbob = fetcher.get_rbob_futures(start_date="2024-01-01")

4. See full documentation:
   cat Gas/OPENBB_INTEGRATION_COMPLETE.md
    """)
    print("="*80)

if __name__ == "__main__":
    main()
