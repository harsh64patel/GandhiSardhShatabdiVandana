#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gandhi Book Generator - Test Script

This script tests the basic functionality of the gandhi_book_generator.py script
by processing a single article. Use this to verify your setup before running the full script.

Usage:
    python test_gandhi_book_generator.py

Requirements:
    Same as gandhi_book_generator.py
"""

import os
import requests
from bs4 import BeautifulSoup
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_gandhi_book_generator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Test URL - first article
TEST_URL = "https://rameshozajournalistblog.wordpress.com/category/%E0%AA%97%E0%AA%BE%E0%AA%82%E0%AA%A7%E0%AB%80-%E0%AA%B8%E0%AA%BE%E0%AA%B0%E0%AB%8D%E0%AA%A7-%E0%AA%B6%E0%AA%A4%E0%AA%BE%E0%AA%AC%E0%AB%8D%E0%AA%A6%E0%AB%80-%E0%AA%B5%E0%AA%82%E0%AA%A6%E0%AA%A8/page/1/"
TEST_OUTPUT_DIR = "test_output"

def test_requests():
    """Test if requests package is working properly."""
    try:
        response = requests.get("https://www.google.com")
        if response.status_code == 200:
            logger.info("✓ Requests package is working properly")
            return True
        else:
            logger.error("✗ Requests package test failed: Status code not 200")
            return False
    except Exception as e:
        logger.error(f"✗ Requests package test failed: {e}")
        return False

def test_beautifulsoup():
    """Test if BeautifulSoup package is working properly."""
    try:
        html = "<html><body><h1>Test</h1></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        if soup.h1.text == "Test":
            logger.info("✓ BeautifulSoup package is working properly")
            return True
        else:
            logger.error("✗ BeautifulSoup package test failed: Could not parse HTML")
            return False
    except Exception as e:
        logger.error(f"✗ BeautifulSoup package test failed: {e}")
        return False

def test_weasyprint():
    """Test if WeasyPrint package is working properly."""
    try:
        from weasyprint import HTML, CSS
        
        # Create a simple HTML file
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        html_file = os.path.join(TEST_OUTPUT_DIR, "test.html")
        with open(html_file, "w", encoding="utf-8") as f:
            f.write("<html><body><h1>Test</h1></body></html>")
        
        # Try to convert to PDF
        pdf_file = os.path.join(TEST_OUTPUT_DIR, "test.pdf")
        HTML(html_file).write_pdf(pdf_file)
        
        if os.path.exists(pdf_file) and os.path.getsize(pdf_file) > 0:
            logger.info("✓ WeasyPrint package is working properly")
            return True
        else:
            logger.error("✗ WeasyPrint package test failed: Could not generate PDF")
            return False
    except ImportError:
        logger.error("✗ WeasyPrint package is not installed")
        return False
    except Exception as e:
        logger.error(f"✗ WeasyPrint package test failed: {e}")
        return False

def test_blog_access():
    """Test if the blog can be accessed."""
    try:
        response = requests.get(TEST_URL)
        if response.status_code == 200:
            logger.info("✓ Blog can be accessed")
            
            # Check if we can find Gandhi articles
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('article')
            
            found_gandhi_article = False
            for article in articles:
                title_element = article.find('h1', class_='entry-title')
                if title_element and "ગાંધી સાર્ધ શતાબ્દી વંદના" in title_element.text:
                    found_gandhi_article = True
                    break
            
            if found_gandhi_article:
                logger.info("✓ Found Gandhi articles on the blog")
                return True
            else:
                logger.error("✗ Could not find Gandhi articles on the blog")
                return False
        else:
            logger.error(f"✗ Blog access test failed: Status code {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Blog access test failed: {e}")
        return False

def test_gujarati_font():
    """Test if Gujarati fonts are working properly."""
    try:
        from weasyprint import HTML, CSS
        
        # Create a simple HTML file with Gujarati text
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        html_file = os.path.join(TEST_OUTPUT_DIR, "test_gujarati.html")
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Gujarati Test</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Gujarati&display=swap');
                body {
                    font-family: 'Noto Sans Gujarati', Arial, sans-serif;
                }
            </style>
        </head>
        <body>
            <h1>ગાંધી સાર્ધ-શતાબ્દી વંદના</h1>
            <p>આ એક ટેસ્ટ છે.</p>
        </body>
        </html>
        """
        
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Try to convert to PDF
        pdf_file = os.path.join(TEST_OUTPUT_DIR, "test_gujarati.pdf")
        HTML(html_file).write_pdf(pdf_file)
        
        if os.path.exists(pdf_file) and os.path.getsize(pdf_file) > 0:
            logger.info("✓ Gujarati font test passed (PDF generated)")
            logger.info(f"  Check {pdf_file} to verify Gujarati text is displayed correctly")
            return True
        else:
            logger.error("✗ Gujarati font test failed: Could not generate PDF")
            return False
    except Exception as e:
        logger.error(f"✗ Gujarati font test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("Starting tests for Gandhi Book Generator")
    
    # Create test output directory
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    
    # Run tests
    tests = [
        ("Requests package", test_requests),
        ("BeautifulSoup package", test_beautifulsoup),
        ("WeasyPrint package", test_weasyprint),
        ("Blog access", test_blog_access),
        ("Gujarati font", test_gujarati_font)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        logger.info(f"Testing {test_name}...")
        try:
            result = test_func()
            if not result:
                all_passed = False
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            all_passed = False
        
        # Add a small delay between tests
        time.sleep(1)
    
    # Summary
    if all_passed:
        logger.info("✓ All tests passed! You can now run the full gandhi_book_generator.py script.")
    else:
        logger.error("✗ Some tests failed. Please fix the issues before running the full script.")
    
    logger.info(f"Test output files are in the {TEST_OUTPUT_DIR} directory")

if __name__ == "__main__":
    main()
