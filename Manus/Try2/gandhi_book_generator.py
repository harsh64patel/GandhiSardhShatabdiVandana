#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gandhi Book Generator

This script scrapes articles from the blog, extracts content, and generates a book in both HTML and PDF formats.
The book is titled "ગાંધી સાર્ધ-શતાબ્દી વંદના" with author "રમેશ ઓઝા".

Usage:
    python gandhi_book_generator.py [--start_chapter INT] [--end_chapter INT] [--batch_size INT]

Requirements:
    - Python 3.6+
    - Required packages: requests, beautifulsoup4, weasyprint, tqdm

Author: Manus AI
"""

import os
import re
import time
import argparse
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import logging
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gandhi_book_generator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://rameshozajournalistblog.wordpress.com/category/%E0%AA%97%E0%AA%BE%E0%AA%82%E0%AA%A7%E0%AB%80-%E0%AA%B8%E0%AA%BE%E0%AA%B0%E0%AB%8D%E0%AA%A7-%E0%AA%B6%E0%AA%A4%E0%AA%BE%E0%AA%AC%E0%AB%8D%E0%AA%A6%E0%AB%80-%E0%AA%B5%E0%AA%82%E0%AA%A6%E0%AA%A8/page/"
MISSING_ARTICLES = [330, 369, 370]  # Articles to skip
BOOK_TITLE = "ગાંધી સાર્ધ-શતાબ્દી વંદના"
AUTHOR = "રમેશ ઓઝા"
OUTPUT_DIR = "gandhi_book_output"
CHAPTERS_DIR = os.path.join(OUTPUT_DIR, "chapters")
SUMMARIES_DIR = os.path.join(OUTPUT_DIR, "summaries")

# CSS for the book
CSS_CONTENT = """
@font-face {
    font-family: 'Gujarati';
    src: url('https://fonts.googleapis.com/css2?family=Noto+Sans+Gujarati&display=swap');
}

body {
    font-family: 'Noto Sans Gujarati', Arial, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 0;
    color: #333;
    background-color: #f9f9f9;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    background-color: white;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

.title-page {
    text-align: center;
    margin-bottom: 50px;
    padding: 50px 0;
}

.title-page h1 {
    font-size: 32px;
    color: #333;
    margin-bottom: 20px;
}

.title-page h2 {
    font-size: 24px;
    color: #666;
}

.chapter {
    margin-bottom: 30px;
    page-break-before: always;
}

.chapter h2 {
    font-size: 24px;
    color: #333;
    border-bottom: 1px solid #ddd;
    padding-bottom: 10px;
    margin-bottom: 20px;
}

.chapter p {
    margin-bottom: 15px;
    text-align: justify;
}

.toc {
    margin-bottom: 30px;
}

.toc h2 {
    font-size: 24px;
    color: #333;
    border-bottom: 1px solid #ddd;
    padding-bottom: 10px;
    margin-bottom: 20px;
}

.toc ul {
    list-style-type: none;
    padding-left: 0;
}

.toc li {
    margin-bottom: 8px;
}

.toc a {
    text-decoration: none;
    color: #0066cc;
}

.toc a:hover {
    text-decoration: underline;
}

.index {
    margin-top: 50px;
}

.index h2 {
    font-size: 24px;
    color: #333;
    border-bottom: 1px solid #ddd;
    padding-bottom: 10px;
    margin-bottom: 20px;
}

.index ul {
    list-style-type: none;
    padding-left: 0;
    column-count: 2;
    column-gap: 20px;
}

.index li {
    margin-bottom: 8px;
    break-inside: avoid;
}

.index a {
    text-decoration: none;
    color: #0066cc;
}

.index a:hover {
    text-decoration: underline;
}

@media print {
    body {
        background-color: white;
    }
    
    .container {
        max-width: none;
        margin: 0;
        padding: 0;
        box-shadow: none;
    }
    
    .chapter {
        page-break-before: always;
    }
    
    .toc, .index {
        page-break-before: always;
    }
}
"""

def setup_directories():
    """Create necessary directories for output files."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(CHAPTERS_DIR, exist_ok=True)
    os.makedirs(SUMMARIES_DIR, exist_ok=True)
    
    # Create CSS file
    with open(os.path.join(OUTPUT_DIR, "book_style.css"), "w", encoding="utf-8") as f:
        f.write(CSS_CONTENT)
    
    logger.info(f"Created output directories in {OUTPUT_DIR}")

def get_article_urls(start_page=1, end_page=65):
    """
    Scrape the blog to get URLs of all articles.
    
    Args:
        start_page: First page to scrape
        end_page: Last page to scrape
        
    Returns:
        List of article URLs
    """
    article_urls = []
    
    for page_num in tqdm(range(start_page, end_page + 1), desc="Scraping blog pages"):
        url = f"{BASE_URL}{page_num}/"
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('article')
            
            for article in articles:
                # Find the article title to check if it's a Gandhi article
                title_element = article.find('h1', class_='entry-title')
                if not title_element:
                    continue
                    
                title = title_element.text.strip()
                if "ગાંધી સાર્ધ શતાબ્દી વંદના" in title:
                    # Extract article number
                    match = re.search(r'ગાંધી સાર્ધ શતાબ્દી વંદના\s*[-–—]\s*(\d+)', title)
                    if match:
                        article_num = int(match.group(1))
                        if article_num in MISSING_ARTICLES:
                            logger.info(f"Skipping missing article {article_num}")
                            continue
                            
                    # Get the article URL
                    link = article.find('a', class_='more-link')
                    if link:
                        article_url = link.get('href')
                        article_urls.append((article_num, article_url))
            
            # Be nice to the server
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error scraping page {page_num}: {e}")
    
    # Sort by article number
    article_urls.sort(key=lambda x: x[0])
    logger.info(f"Found {len(article_urls)} articles")
    
    return article_urls

def extract_article_content(article_num, url):
    """
    Extract content from an article.
    
    Args:
        article_num: Article number
        url: URL of the article
        
    Returns:
        Tuple of (article_title, article_content)
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get the article title
        title_element = soup.find('h1', class_='entry-title')
        if not title_element:
            logger.warning(f"Could not find title for article {article_num}")
            title = f"ગાંધી સાર્ધ શતાબ્દી વંદના – {article_num}"
        else:
            title = title_element.text.strip()
        
        # Get the article content
        content_element = soup.find('div', class_='entry-content')
        if not content_element:
            logger.warning(f"Could not find content for article {article_num}")
            return title, ""
        
        # Extract paragraphs
        paragraphs = content_element.find_all('p')
        content = "\n\n".join([p.text.strip() for p in paragraphs])
        
        # Be nice to the server
        time.sleep(1)
        
        return title, content
        
    except Exception as e:
        logger.error(f"Error extracting content for article {article_num}: {e}")
        return f"ગાંધી સાર્ધ શતાબ્દી વંદના – {article_num}", ""

def summarize_article(article_num, content):
    """
    Create a summary for the article.
    
    Args:
        article_num: Article number
        content: Article content
        
    Returns:
        Summary of the article (max 8 words)
    """
    # This is a simple summarization - in a real scenario, you might want to use NLP
    # For now, we'll just take the first sentence and limit to 8 words
    if not content:
        return "No content available"
    
    first_sentence = content.split('.')[0]
    words = first_sentence.split()
    if len(words) > 8:
        summary = ' '.join(words[:8])
    else:
        summary = first_sentence
        
    return summary

def save_chapter_and_summary(article_num, title, content, summary):
    """
    Save chapter content and summary to files.
    
    Args:
        article_num: Article number
        title: Article title
        content: Article content
        summary: Article summary
    """
    # Save chapter content
    chapter_filename = os.path.join(CHAPTERS_DIR, f"chapter{article_num}.md")
    with open(chapter_filename, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n{content}")
    
    # Save chapter summary
    summary_filename = os.path.join(SUMMARIES_DIR, f"chapter{article_num}_summary.txt")
    with open(summary_filename, "w", encoding="utf-8") as f:
        f.write(f"Based on the content of article {article_num} \"{title}\", a suitable short title would be:\n\n\"{summary}\"\n")
    
    return chapter_filename, summary_filename

def generate_index(chapters):
    """
    Generate an index for the book.
    
    Args:
        chapters: List of (chapter_num, title, content, summary) tuples
        
    Returns:
        HTML for the index
    """
    # Extract keywords from content
    keywords = {}
    exclude_words = ["ગાંધીજી", "રમેશ ઓઝા", "શતાબ્દી વંદના"]
    
    for chapter_num, title, content, summary in chapters:
        # Simple keyword extraction - in a real scenario, use NLP
        words = re.findall(r'\b\w+\b', content)
        for word in words:
            if len(word) > 3 and word not in exclude_words:
                if word not in keywords:
                    keywords[word] = []
                if chapter_num not in keywords[word]:
                    keywords[word].append(chapter_num)
    
    # Sort keywords
    sorted_keywords = sorted(keywords.items())
    
    # Generate HTML
    html = '<div class="index">\n'
    html += '<h2 id="index">અનુક્રમ</h2>\n'
    html += '<ul>\n'
    
    for keyword, chapter_nums in sorted_keywords:
        links = []
        for chapter_num in chapter_nums:
            links.append(f'<a href="#chapter{chapter_num}">{chapter_num}</a>')
        
        html += f'<li>{keyword}: {", ".join(links)}</li>\n'
    
    html += '</ul>\n'
    html += '</div>\n'
    
    return html

def generate_toc(chapters):
    """
    Generate a table of contents for the book.
    
    Args:
        chapters: List of (chapter_num, title, content, summary) tuples
        
    Returns:
        HTML for the table of contents
    """
    html = '<div class="toc">\n'
    html += '<h2 id="toc">અનુક્રમણિકા</h2>\n'
    html += '<ul>\n'
    
    for chapter_num, title, _, summary in chapters:
        html += f'<li><a href="#chapter{chapter_num}">{title} ({summary})</a></li>\n'
    
    html += '</ul>\n'
    html += '</div>\n'
    
    return html

def generate_html(chapters, output_file):
    """
    Generate HTML for the book.
    
    Args:
        chapters: List of (chapter_num, title, content, summary) tuples
        output_file: Path to output HTML file
    """
    # Generate table of contents and index
    toc_html = generate_toc(chapters)
    index_html = generate_index(chapters)
    
    # Generate HTML
    html = '<!DOCTYPE html>\n'
    html += '<html lang="gu">\n'
    html += '<head>\n'
    html += '<meta charset="UTF-8">\n'
    html += f'<title>{BOOK_TITLE}</title>\n'
    html += '<link rel="stylesheet" href="book_style.css">\n'
    html += '</head>\n'
    html += '<body>\n'
    html += '<div class="container">\n'
    
    # Title page
    html += '<div class="title-page">\n'
    html += f'<h1>{BOOK_TITLE}</h1>\n'
    html += f'<h2>{AUTHOR}</h2>\n'
    html += '</div>\n'
    
    # Table of contents
    html += toc_html
    
    # Chapters
    for chapter_num, title, content, summary in chapters:
        html += f'<div class="chapter" id="chapter{chapter_num}">\n'
        html += f'<h2>{title} ({summary})</h2>\n'
        
        # Convert content to HTML paragraphs
        paragraphs = content.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                html += f'<p>{paragraph}</p>\n'
        
        html += '</div>\n'
    
    # Index
    html += index_html
    
    html += '</div>\n'
    html += '</body>\n'
    html += '</html>\n'
    
    # Save HTML
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    logger.info(f"Generated HTML file: {output_file}")
    
    return output_file

def generate_pdf(html_file, output_file):
    """
    Generate PDF from HTML.
    
    Args:
        html_file: Path to HTML file
        output_file: Path to output PDF file
    """
    try:
        # Import weasyprint here to avoid import error if not installed
        from weasyprint import HTML, CSS
        
        # Get the directory of the HTML file for relative paths
        base_dir = os.path.dirname(os.path.abspath(html_file))
        
        # Generate PDF
        HTML(html_file).write_pdf(
            output_file,
            stylesheets=[CSS(os.path.join(base_dir, "book_style.css"))]
        )
        
        logger.info(f"Generated PDF file: {output_file}")
        return output_file
        
    except ImportError:
        logger.error("WeasyPrint not installed. Please install it to generate PDFs.")
        return None
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        return None

def process_chapters(start_chapter, end_chapter, batch_size=10):
    """
    Process chapters in batches.
    
    Args:
        start_chapter: First chapter to process
        end_chapter: Last chapter to process
        batch_size: Number of chapters to process in each batch
    """
    # Get article URLs
    article_urls = get_article_urls()
    
    # Filter articles by chapter number
    filtered_urls = [(num, url) for num, url in article_urls if start_chapter <= num <= end_chapter]
    
    if not filtered_urls:
        logger.error(f"No articles found between chapters {start_chapter} and {end_chapter}")
        return
    
    # Process articles in batches
    all_chapters = []
    
    for i in range(0, len(filtered_urls), batch_size):
        batch = filtered_urls[i:i+batch_size]
        batch_chapters = []
        
        for article_num, url in tqdm(batch, desc=f"Processing batch {i//batch_size + 1}"):
            # Extract content
            title, content = extract_article_content(article_num, url)
            
            # Create summary
            summary = summarize_article(article_num, content)
            
            # Save chapter and summary
            save_chapter_and_summary(article_num, title, content, summary)
            
            # Add to batch
            batch_chapters.append((article_num, title, content, summary))
        
        # Add batch to all chapters
        all_chapters.extend(batch_chapters)
        
        # Generate HTML and PDF for this batch
        batch_name = f"{start_chapter}-{min(end_chapter, batch[-1][0])}"
        html_file = os.path.join(OUTPUT_DIR, f"gandhi_book_chapters_{batch_name}.html")
        pdf_file = os.path.join(OUTPUT_DIR, f"gandhi_book_chapters_{batch_name}.pdf")
        
        generate_html(all_chapters, html_file)
        generate_pdf(html_file, pdf_file)
        
        logger.info(f"Completed batch {i//batch_size + 1}")
    
    # Generate final HTML and PDF
    html_file = os.path.join(OUTPUT_DIR, f"gandhi_book_chapters_{start_chapter}-{end_chapter}.html")
    pdf_file = os.path.join(OUTPUT_DIR, f"gandhi_book_chapters_{start_chapter}-{end_chapter}.pdf")
    
    generate_html(all_chapters, html_file)
    generate_pdf(html_file, pdf_file)
    
    logger.info(f"Completed processing chapters {start_chapter} to {end_chapter}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate Gandhi book from blog articles")
    parser.add_argument("--start_chapter", type=int, default=1, help="First chapter to process")
    parser.add_argument("--end_chapter", type=int, default=30, help="Last chapter to process")
    parser.add_argument("--batch_size", type=int, default=10, help="Number of chapters to process in each batch")
    
    args = parser.parse_args()
    
    logger.info(f"Starting Gandhi Book Generator")
    logger.info(f"Processing chapters {args.start_chapter} to {args.end_chapter}")
    
    # Setup directories
    setup_directories()
    
    # Process chapters
    process_chapters(args.start_chapter, args.end_chapter, args.batch_size)
    
    logger.info("Finished Gandhi Book Generator")

if __name__ == "__main__":
    main()
