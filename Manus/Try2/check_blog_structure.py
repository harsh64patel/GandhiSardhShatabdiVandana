#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Check Blog Structure

This script checks the structure of the Gandhi blog to help debug the article scraping issue.
"""

import requests
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# URL to check
URL = "https://rameshozajournalistblog.wordpress.com/category/%E0%AA%97%E0%AA%BE%E0%AA%82%E0%AA%A7%E0%AB%80-%E0%AA%B8%E0%AA%BE%E0%AA%B0%E0%AB%8D%E0%AA%A7-%E0%AA%B6%E0%AA%A4%E0%AA%BE%E0%AA%AC%E0%AB%8D%E0%AA%A6%E0%AB%80-%E0%AA%B5%E0%AA%82%E0%AA%A6%E0%AA%A8/page/1/"

def check_blog_structure():
    """Check the structure of the blog."""
    try:
        logger.info(f"Requesting URL: {URL}")
        response = requests.get(URL)
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Failed to access the blog. Status code: {response.status_code}")
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Save HTML for inspection
        with open("blog_page.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        logger.info("Saved HTML to blog_page.html")
        
        # Check for articles
        articles = soup.find_all('article')
        logger.info(f"Number of articles found: {len(articles)}")
        
        # Check article structure
        for i, article in enumerate(articles[:3]):  # Check first 3 articles
            logger.info(f"\nArticle {i+1} details:")
            
            # Check for title
            title_element = article.find('h1', class_='entry-title')
            if title_element:
                title = title_element.text.strip()
                logger.info(f"  Title: {title}")
                
                # Check if it's a Gandhi article
                if "ગાંધી સાર્ધ શતાબ્દી વંદના" in title:
                    logger.info(f"  Is Gandhi article: Yes")
                    
                    # Extract article number
                    import re
                    match = re.search(r'ગાંધી સાર્ધ શતાબ્દી વંદના\s*[-–—]\s*(\d+)', title)
                    if match:
                        article_num = match.group(1)
                        logger.info(f"  Article number: {article_num}")
                    else:
                        logger.info(f"  Article number: Not found")
                else:
                    logger.info(f"  Is Gandhi article: No")
            else:
                logger.info(f"  Title: Not found")
            
            # Check for more-link
            more_link = article.find('a', class_='more-link')
            if more_link:
                logger.info(f"  More link: {more_link.get('href')}")
            else:
                logger.info(f"  More link: Not found")
            
            # Check for alternative link structures
            all_links = article.find_all('a')
            logger.info(f"  Total links in article: {len(all_links)}")
            for j, link in enumerate(all_links[:3]):  # Check first 3 links
                logger.info(f"    Link {j+1}: {link.get('href')} (Text: {link.text.strip()[:30]}...)")
        
        # Check for alternative article structures
        logger.info("\nChecking alternative article structures:")
        
        # Check for posts
        posts = soup.find_all('div', class_='post')
        logger.info(f"Number of 'post' divs: {len(posts)}")
        
        # Check for entries
        entries = soup.find_all('div', class_='entry')
        logger.info(f"Number of 'entry' divs: {len(entries)}")
        
        # Check for blog posts
        blog_posts = soup.find_all('div', class_='blog-post')
        logger.info(f"Number of 'blog-post' divs: {len(blog_posts)}")
        
        # Check main content area
        content_area = soup.find('div', id='content')
        if content_area:
            logger.info("Found main content area")
            main_children = list(content_area.children)
            logger.info(f"Number of children in main content area: {len(main_children)}")
            
            # Check first few children
            for i, child in enumerate(main_children[:5]):
                if hasattr(child, 'name'):
                    logger.info(f"  Child {i+1} tag: {child.name}, class: {child.get('class', 'None')}")
                    
                    # If it's a potential article container, check its structure
                    if child.name == 'article' or child.name == 'div':
                        title_elements = child.find_all(['h1', 'h2', 'h3'])
                        for title_el in title_elements:
                            logger.info(f"    Title element: {title_el.name}, text: {title_el.text.strip()[:50]}...")
        
    except Exception as e:
        logger.error(f"Error checking blog structure: {e}")

if __name__ == "__main__":
    check_blog_structure()
