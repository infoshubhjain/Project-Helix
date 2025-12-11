#!/usr/bin/env python3
"""
Project Helix - Comprehensive Test Script
Tests all components of the application
"""

import sys
import os
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def test_python_version():
    """Check Python version"""
    print_header("Python Version Check")
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    print(f"Python version: {version_str}")

    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version_str} is compatible")
        return True
    else:
        print_error(f"Python {version_str} is too old. Need 3.8+")
        return False

def test_dependencies():
    """Check if required packages are installed"""
    print_header("Dependency Check")

    required = [
        'flask',
        'flask_cors',
        'bs4',  # beautifulsoup4
        'playwright',
        'requests',
        'dotenv',  # python-dotenv
        'google.auth',
        'googleapiclient',
        'msal',
        'openai'
    ]

    all_installed = True
    for package in required:
        try:
            __import__(package)
            print_success(f"{package}")
        except ImportError:
            print_error(f"{package} - NOT INSTALLED")
            all_installed = False

    return all_installed

def test_file_structure():
    """Check if all required files exist"""
    print_header("File Structure Check")

    base = Path("/Users/shubh/Desktop/Project-Helix/Project")

    required_files = {
        "app.py": base / "app.py",
        "scrape.py": base / "scrape.py",
        "requirements.txt": base / "requirements.txt",
        "templates/index.html": base / "templates" / "index.html",
        "static/style.css": base / "static" / "style.css",
        "static/script.js": base / "static" / "script.js",
        "static/browse-events.js": base / "static" / "browse-events.js",
        "static/calendar-connect.js": base / "static" / "calendar-connect.js",
        "calander/readEmail.py": base / "calander" / "readEmail.py",
        "calander/prompt.txt": base / "calander" / "prompt.txt",
    }

    all_exist = True
    for name, path in required_files.items():
        if path.exists():
            print_success(f"{name}")
        else:
            print_error(f"{name} - NOT FOUND at {path}")
            all_exist = False

    return all_exist

def test_app_imports():
    """Test if Flask app can be imported"""
    print_header("Flask App Import Test")

    sys.path.insert(0, '/Users/shubh/Desktop/Project-Helix/Project')
    sys.path.insert(0, '/Users/shubh/Desktop/Project-Helix/Project/calander')

    try:
        from app import app, EMAIL_PARSING_ENABLED
        print_success("Flask app imports successfully")
        print_info(f"Email parsing enabled: {EMAIL_PARSING_ENABLED}")
        return True, app
    except Exception as e:
        print_error(f"Failed to import app: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_flask_routes(app):
    """Test Flask routes"""
    print_header("Flask Routes Test")

    if not app:
        print_error("App not available for testing")
        return False

    try:
        with app.test_client() as client:
            # Test home page
            response = client.get('/')
            if response.status_code == 200:
                print_success("GET / - Returns 200")
            else:
                print_error(f"GET / - Returns {response.status_code}")
                return False

            # Test email endpoint (should return 503 if not configured)
            response = client.post('/api/process_emails', json={'amount': 5})
            if response.status_code == 503:
                print_success("POST /api/process_emails - Correctly returns 503 (disabled)")
            elif response.status_code == 200:
                print_success("POST /api/process_emails - Returns 200 (enabled)")
            else:
                print_warning(f"POST /api/process_emails - Unexpected status {response.status_code}")

        return True
    except Exception as e:
        print_error(f"Route testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_env_file():
    """Check .env file"""
    print_header("Environment Configuration Check")

    env_path = Path("/Users/shubh/Desktop/Project-Helix/Project/.env")

    if not env_path.exists():
        print_warning(".env file does not exist")
        print_info("This is OK for basic browsing, but needed for email parsing")
        return True

    print_success(".env file exists")

    # Try to load env variables
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)

        tenant_id = os.getenv("TENANT_ID")
        client_id = os.getenv("CLIENT_ID")

        if tenant_id and client_id:
            print_success("Email parsing credentials configured")
        else:
            print_info("Email parsing credentials not configured (optional)")

        return True
    except Exception as e:
        print_error(f"Error loading .env: {e}")
        return False

def test_google_credentials():
    """Check Google Calendar credentials"""
    print_header("Google Calendar Credentials Check")

    cred_path = Path("/Users/shubh/Desktop/Project-Helix/Project/calander/credentials.json")

    if cred_path.exists():
        print_success("credentials.json exists")
        print_info("Google Calendar integration is available")
        return True
    else:
        print_warning("credentials.json not found")
        print_info("Google Calendar features will not work")
        print_info("See SIMPLE_SETUP.md to get credentials.json")
        return False

def test_playwright():
    """Test Playwright installation"""
    print_header("Playwright Browser Check")

    try:
        from playwright.sync_api import sync_playwright
        print_success("Playwright package installed")

        # Check if chromium is installed
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                browser.close()
                print_success("Chromium browser installed and working")
                return True
        except Exception as e:
            print_error(f"Chromium not installed: {e}")
            print_info("Run: playwright install chromium")
            return False

    except ImportError:
        print_error("Playwright not installed")
        return False

def run_all_tests():
    """Run all tests"""
    print(f"\n{Colors.BOLD}Project Helix - System Test{Colors.END}")
    print(f"{Colors.BOLD}Testing your installation...{Colors.END}\n")

    results = {}

    # Run tests
    results['python'] = test_python_version()
    results['dependencies'] = test_dependencies()
    results['files'] = test_file_structure()
    results['env'] = test_env_file()
    results['google_creds'] = test_google_credentials()
    results['playwright'] = test_playwright()

    success, app = test_app_imports()
    results['app_import'] = success

    if success:
        results['routes'] = test_flask_routes(app)
    else:
        results['routes'] = False

    # Summary
    print_header("Test Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"{test_name.ljust(20)}: {status}")

    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}\n")

    # Recommendations
    print_header("Recommendations")

    if results['python'] and results['dependencies'] and results['files'] and results['app_import'] and results['routes']:
        print_success("Core functionality is working!")
        print_info("You can run the app with: ./run.sh")
        print_info("Browse events will work immediately")
    else:
        print_error("Some core components are not working")
        print_info("Fix the failed tests above")

    if not results['google_creds']:
        print_info("To enable Google Calendar:")
        print_info("  1. Read SIMPLE_SETUP.md")
        print_info("  2. Get credentials.json from Google Cloud")
        print_info("  3. Place in Project/calander/credentials.json")

    if not results['playwright']:
        print_info("To enable web scraping:")
        print_info("  Run: playwright install chromium")

    print()

if __name__ == "__main__":
    run_all_tests()
