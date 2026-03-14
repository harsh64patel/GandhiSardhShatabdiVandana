#!/usr/bin/env python
"""Build a printable PDF book from the Gujarati WordPress category posts.

Usage examples:
  python build_book.py --max-chapters 1
  python build_book.py --max-chapters 5
  python build_book.py --max-chapters all --output output/book.pdf

This script will:
  1) Scrape all posts in the configured category.
  2) Convert each post into a chapter with a title and subtitle.
  3) Generate a clickable table of contents and a keyword index.
  4) Render a PDF via WeasyPrint using an embedded Gujarati font.

The script defaults to pulling the first 65 category pages (10 posts per page).
"""

from __future__ import annotations

import argparse
import os
import pickle
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup

try:
    from weasyprint import CSS, HTML
except ImportError as exc:
    raise SystemExit(
        "WeasyPrint is required to generate PDFs. Install it with `pip install weasyprint`."  # noqa: E501
    ) from exc


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

CATEGORY_URL = (
    "https://rameshozajournalistblog.wordpress.com/category/"
    "%E0%AA%97%E0%AA%BE%E0%AA%82%E0%AA%A7%E0%AB%80-%E0%AA%B8%E0%AA%BE%E0%AA%B0%E0%AB%8D"
    "%E0%AA%A7-%E0%AA%B6%E0%AA%A4%E0%AA%BE%E0%AA%AC%E0%AB%8D%E0%AA%A6%E0%AB%80-%E0%AA%B5%E0%AA%82"
    "%E0%AA%A6%E0%AA%A8/page/{page}/"
)
PAGES = 65
MISSING_CHAPTERS = {330, 369, 370}
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
"(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

# Gujarati digits (to convert to ASCII digits)
GUJARATI_DIGITS = "૦૧૨૩૪૫૬૭૮૯"
ASCII_DIGITS = "0123456789"
DIGIT_TRANSLATION = str.maketrans(GUJARATI_DIGITS, ASCII_DIGITS)

# Common words to omit from the index (and from any generated concordance)
STOPWORDS = {
    "અને",
    "આ",
    "ના",
    "માં",
    "હવે",
    "છે",
    "કે",
    "આવવા",
    "જે",
    "હતી",
    "હૈ",
    "નો",
    "હોય",
    "પર",
    "છે",
    "માટે",
    "સે",
    "બરાબર",
    "જ",
    "છે",
    "ગાંધીજી",
    "સાર્ધ શતાબ્દી",
    "વંદના",
    "રમેશ",
    "ઓઝા",
    "શતાબ્દી",
    'અને', 'કે', 'તે', 'તેમ', 'તેમને', 'તેમનો', 'તેમના',
    'આ', 'આપણે', 'આપણો', 'આપણા', 'આપણું',
    'હું', 'મારો', 'મારા', 'મારું', 'મને', 'મારામાં',
    'તમે', 'તમારો', 'તમારા', 'તમારું',
    'એ', 'એમ', 'એમાં', 'એટલે', 'એટલું',
    'જે', 'જેમ', 'જેમાં', 'જેમને', 'જેમનો', 'જેમના',
    'થે', 'થયું', 'થયો', 'થયા', 'થશે', 'થાય',
    'છે', 'છો', 'છું', 'છીએ', 'છીશ',
    'હતો', 'હતું', 'હતા', 'હતી',
    'નથી', 'નથો', 'નથું', 'નથીએ',
    'પણ', 'પર', 'પણે',
    'સાથે', 'વિના', 'માટે', 'માટી', 'માટો',
    'ધર્મ', 'ધર્મમાં', 'ધર્મે',
    'જીવન', 'જીવનમાં', 'જીવનનો',
    'કાર્ય', 'કાર્યમાં', 'કાર્યનો',
    'સમાજ', 'સમાજમાં', 'સમાજનો',
    'રાજ', 'રાજમાં', 'રાજનો',
    'વિશે', 'વિષે',
    'ત', 'તો', 'તર',
    'ના', 'નો', 'નું', 'ની',
    'એક', 'બે', 'ત્રણ', 'ચાર',
}

# Important terms to prioritize in index
IMPORTANT_TERMS = {
    'સત્ય', 'અહિંસા', 'સ્વતંત્રતા', 'ધર્મ', 'સમાજ',
    'રાજકારણ', 'આત્મા', 'સેવા', 'શાંતિ', 'ભારત',
    'આંદોલન', 'સંસ્કૃતિ', 'શિક્ષણ', 'અર્થતંત્ર',
    'ન્યાય', 'લોકશાહી', 'રાષ્ટ્રવાદ', 'આધુનિકતા',
}

# Terms to exclude from index (repetitive)
REPETITIVE_TERMS = {
    'ગાંધીજી', 'ગાંધી', 'રમેશ ઓઝા', 'રમેશ', 'ઓઝા',
    'શતાબ્દી વંદના', 'શતાબ્દી', 'વંદના',
    'ગાંધી સાર્ધ-શતાબ્દી વંદના',
    'ગાંધી સાર્ધ શતાબ્દી વંદના',
    'ગાંધીજીને', 'ગાંધીજીના', 'ગાંધીજીનો', 'ગાંધીજીનું', 'ગાંધીજીની',
    'મહાત્મા', 'મહાત્માના', 'મહાત્માનો', 'મહાત્માનું', 'મહાત્માની',
}

# If you want to include a second or alternate font, set FONT_FILES accordingly.
FONT_FILES = [
    # We will download this file if it does not already exist in the fonts directory.
    "NotoSansGujarati-Regular.ttf"
]

DEFAULT_FONT_DOWNLOAD_URL = (
    "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/"
    "NotoSansGujarati/NotoSansGujarati-Regular.ttf"
)


class SubtitleSummarizer:
    """
    Generates concise subtitles from article content using keyword extraction
    and semantic analysis.
    """
    
    def __init__(self):
        """Initialize the summarizer with Gujarati stop words and patterns."""
        self.gujarati_stopwords = STOPWORDS
        
    def extract_first_meaningful_sentence(self, text: str, max_length: int = 100) -> str:
        """
        Extract the first meaningful sentence from the article.
        
        Args:
            text: Article content
            max_length: Maximum length of extracted sentence
            
        Returns:
            First meaningful sentence
        """
        sentences = re.split(r'[।।।]', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < max_length:
                return sentence
        
        return sentences[0] if sentences else ""
    
    def extract_key_phrases(self, text: str, num_phrases: int = 5) -> List[str]:
        """
        Extract key phrases from text using frequency analysis, pattern matching, and semantic filtering.
        
        Args:
            text: The article content
            num_phrases: Number of key phrases to extract
            
        Returns:
            List of key phrases
        """
        # Split text into sentences
        sentences = re.split(r'[।।।]', text)
        
        # Skip first sentence if it's intro-like (contains words like વંદના, શરુ, ઈરાદો)
        relevant_sentences = []
        for sent in sentences:
            if not any(word in sent for word in ['વંદના', 'શરુ', 'ઈરાદો', 'જન્મજયંતિ']):
                relevant_sentences.append(sent)
            if len(relevant_sentences) >= 3:
                break
        
        relevant_text = ' '.join(relevant_sentences[:3])
        
        # Extract words
        words = re.findall(r"[\u0A80-\u0AFF]+", relevant_text)
        
        # Clean tokens: strip punctuation, filter
        cleaned_words = []
        for word in words:
            clean_word = re.sub(r'[^\u0A80-\u0AFF]', '', word).strip()
            if len(clean_word) > 2 and clean_word not in self.gujarati_stopwords and clean_word not in REPETITIVE_TERMS:
                cleaned_words.append(clean_word)
        
        # Count word frequency
        word_freq = Counter(cleaned_words)
        
        # Prioritize important terms, then long words, then high frequency
        candidates = []
        for word, freq in word_freq.items():
            if word in IMPORTANT_TERMS:
                candidates.append((word, freq + 10))  # Boost important terms
            elif len(word) > 6:
                candidates.append((word, freq + 5))  # Boost long words
            else:
                candidates.append((word, freq))
        
        # Sort by boosted frequency
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Get top phrases
        top_phrases = [word for word, _ in candidates[:num_phrases]]
        
        return top_phrases
    
    def generate_subtitle(self, article_content: str, article_number: int) -> str:
        """
        Generate a concise subtitle for an article.
        
        Args:
            article_content: Full content of the article
            article_number: Article number for context
            
        Returns:
            A concise subtitle in Gujarati
        """
        # Extract key phrases
        key_phrases = self.extract_key_phrases(article_content, num_phrases=3)
        
        # Filter out poor phrases (too short or common)
        good_phrases = [p for p in key_phrases if len(p) > 4 and p not in ['છે', 'હતા', 'હતો', 'હતું']]
        
        if good_phrases:
            # Join key phrases with appropriate Gujarati connector
            subtitle = ' અને '.join(good_phrases[:2])
            return f"({subtitle})"
        else:
            # Fallback to first meaningful sentence
            first_sentence = self.extract_first_meaningful_sentence(article_content)
            if first_sentence:
                # Take first few words
                words = first_sentence.split()[:5]
                subtitle = ' '.join(words)
                return f"({subtitle}...)"
            else:
                # Fallback subtitle based on article number
                return f"(લેખ {article_number})"


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class Chapter:
    number: int
    title: str
    url: str
    html: str
    subtitle: str


def ensure_fonts(fonts_dir: Path) -> Dict[str, Path]:
    """Ensure required font files exist locally and return mapping name->path."""

    fonts_dir.mkdir(parents=True, exist_ok=True)

    out: Dict[str, Path] = {}
    for font_name in FONT_FILES:
        target = fonts_dir / font_name
        if not target.exists():
            print(f"Downloading font {font_name}...")
            resp = requests.get(DEFAULT_FONT_DOWNLOAD_URL, stream=True)
            resp.raise_for_status()
            target.write_bytes(resp.content)
        out[font_name] = target

    return out


def numeric_part_from_title(title: str) -> Optional[int]:
    """Extract chapter number from a title like 'ગાંધી સાર્ધ શતાબ્દી વંદના – ૧'."""

    # Normalize Gujarati digits to ASCII digits for parsing.
    normalized = title.translate(DIGIT_TRANSLATION)

    # Find the last run of digits in the title (e.g., '…– 27' or '…–27')
    match = re.search(r"(\d{1,4})\s*$", normalized)
    if not match:
        return None

    try:
        return int(match.group(1))
    except ValueError:
        return None


def _make_session() -> requests.Session:
    """Create a requests session with retry support."""

    session = requests.Session()
    retry = requests.adapters.Retry(
        total=4,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def fetch_category_posts(max_pages: int = PAGES) -> List[Tuple[int, str, str]]:
    """Return list of (chapter_number, title, url) sorted by chapter_number."""

    session = _make_session()
    found: Dict[int, Tuple[str, str]] = {}

    for page in range(1, max_pages + 1):
        url = CATEGORY_URL.format(page=page)
        print(f"Fetching category page {page}/{max_pages}: {url}")

        try:
            r = session.get(url, timeout=30)
            r.raise_for_status()
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Warning: failed to fetch {url}: {exc}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.select("article h2.entry-title a")

        for a in items:
            title = a.text.strip().replace("\xa0", " ")
            href = a.get("href")
            if not href:
                continue
            chap = numeric_part_from_title(title)
            if chap is None:
                continue
            if chap in MISSING_CHAPTERS:
                continue
            if chap in found:
                # already seen via another page
                continue
            found[chap] = (title, href)

    return sorted(((k, v[0], v[1]) for k, v in found.items()), key=lambda t: t[0])


def sanitize_html_content(raw_html: str) -> str:
    """Keep a minimal clean subset of HTML tags for PDF rendering."""

    soup = BeautifulSoup(raw_html, "html.parser")

    # Remove scripts, styles, navigation, comments, and non-content nodes.
    for selector in ["script", "style", "iframe", "nav", ".post-navigation"]:
        for node in soup.select(selector):
            node.decompose()

    # Remove common WordPress "Share" / "Related" blocks that are not part of the article text.
    for heading in soup.find_all(["h2", "h3", "h4"]):
        text = heading.get_text(" ", strip=True).lower()
        if any(marker in text for marker in ("share", "related", "શેર", "સંબંધિત")):
            # Remove the heading and any immediately following list/paragraphs.
            next_node = heading.find_next_sibling()
            heading.decompose()
            while next_node is not None and next_node.name in ("ul", "ol", "p", "div"):
                nxt = next_node.find_next_sibling()
                next_node.decompose()
                next_node = nxt

    # Remove 'Like Loading...' text
    for element in soup.find_all(text=True):
        if "Like Loading..." in element:
            parent = element.parent
            if parent:
                parent.decompose()

    # In WordPress content, 'entry-content' is used; ensure we keep it.
    # Convert common tags to a stable subset.
    allowed_tags = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "br", "strong", "b", "em", "i"}

    def clean_tag(tag):
        if tag.name not in allowed_tags:
            tag.unwrap()
            return
        # Remove any attributes (e.g., class, style) to avoid unwanted styling.
        tag.attrs = {}

    for tag in soup.find_all(True):
        clean_tag(tag)

    text = str(soup)
    text = re.sub(r'Like Loading\.\.\.', '', text)
    return text


def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """Extract a ranked list of keywords from the text (improved semantic filtering)."""

    # Split into words using Gujarati Unicode
    words = re.findall(r"[\u0A80-\u0AFF]+", text)
    
    # Filter for meaningful terms
    index_terms = []
    
    for word in words:
        # Skip if it's a repetitive term
        if word in REPETITIVE_TERMS:
            continue
        
        # Skip very short words
        if len(word) < 3:
            continue
        
        # Prioritize important terms
        if word in IMPORTANT_TERMS:
            index_terms.append(word)
        # Add long words or capitalized (though Gujarati may not have caps)
        elif len(word) > 5:
            index_terms.append(word)
    
    # Use frequency to rank, but limit to max_keywords
    freq = Counter(index_terms)
    most_common = [w for w, _ in freq.most_common(max_keywords)]
    return most_common


def build_html(
    chapters: List[Chapter],
    font_paths: Dict[str, Path],
    font_face_rules: List[str],
    css: str,
    book_title: str,
    author: str,
    output_html_path: Path,
) -> str:
    """Build the full HTML content for the book."""

    html_parts: List[str] = []
    html_parts.append("<!DOCTYPE html>")
    html_parts.append('<html lang="gu">')
    html_parts.append("<head>")
    html_parts.append("<meta charset='UTF-8'>")
    html_parts.append(f"<title>{book_title}</title>")
    html_parts.append("<style>")
    html_parts.append("\n".join(font_face_rules))
    html_parts.append(css)
    html_parts.append("</style>")
    html_parts.append("</head>")
    html_parts.append("<body>")

    # Title page
    html_parts.append("<div class='title-page'>")
    html_parts.append(f"<h1>{book_title}</h1>")
    html_parts.append(f"<div class='author'>લેખક: {author}</div>")
    html_parts.append("</div>")

    # Table of contents
    html_parts.append("<h2 class='toc-title'>અનુક્રમણિકા</h2>")
    for chap in chapters:
        html_parts.append(
            "<div class='toc-entry'>"
            f"<a href='#chapter{chap.number}'>"  # noqa: W503
            f"{chap.number}. {chap.title}"  # noqa: W503
            f"</a>"
            "</div>"
        )

    # Chapters
    for chap in chapters:
        html_parts.append(f"<div class='chapter' id='chapter{chap.number}'>")
        html_parts.append(f"<h2 class='chapter-title'>{chap.title}</h2>")
        if chap.subtitle:
            html_parts.append(
                f"<div class='chapter-subtitle'>{chap.subtitle}</div>"
            )
        html_parts.append(chap.html)
        html_parts.append("</div>")

    # Index (concordance)
    # Aggregate keywords across chapters
    word_to_chapters: Dict[str, Set[int]] = defaultdict(set)
    for chap in chapters:
        kws = extract_keywords(BeautifulSoup(chap.html, "html.parser").get_text())
        for word in kws:
            word_to_chapters[word].add(chap.number)

    # Sort by frequency (most chapters) and then alphabetically
    entries = sorted(
        word_to_chapters.items(),
        key=lambda kv: (-len(kv[1]), kv[0]),
    )

    html_parts.append("<div class='chapter'>")
    html_parts.append("<h2 class='toc-title'>અનુક્રમ</h2>")
    html_parts.append("<div class='index'>")

    for word, chaps in entries:
        if word in STOPWORDS:
            continue
        links = ", ".join(
            f"<a href='#chapter{n}'>{n}</a>" for n in sorted(chaps)
        )
        html_parts.append(
            "<div class='index-entry'>"
            f"<a href='#chapter{sorted(chaps)[0]}'>{word}</a>, {links}"
            "</div>"
        )

    html_parts.append("</div>")
    html_parts.append("</div>")

    html_parts.append("</body>")
    html_parts.append("</html>")

    html = "\n".join(html_parts)
    output_html_path.write_text(html, encoding="utf-8")
    return html


def main(argv: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(description="Build Gujarati book PDF from WordPress posts.")
    parser.add_argument(
        "--max-chapters",
        type=str,
        default="1",
        help="Number of chapters to generate (use 'all' for everything).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="book.pdf",
        help="Output PDF file path.",
    )
    parser.add_argument(
        "--temp-html",
        type=str,
        default="book.html",
        help="Temporary HTML output path (for debugging).",
    )
    parser.add_argument(
        "--fonts-dir",
        type=str,
        default="fonts",
        help="Directory to download or store fonts.",
    )
    args = parser.parse_args(argv)

    out_pdf = Path(args.output).expanduser().resolve()
    out_html = Path(args.temp_html).expanduser().resolve()
    fonts_dir = Path(args.fonts_dir).expanduser().resolve()

    font_paths = ensure_fonts(fonts_dir)

    # Define font and CSS for reuse
    font_face_rules = []
    for font_file in font_paths.values():
        uri = font_file.resolve().as_uri()
        font_face_rules.append(
            f"@font-face {{ font-family: 'Noto Sans Gujarati'; src: url('{uri}'); }}"
        )

    css = """
        @page {
            size: A4;
            margin: 2cm;
        }

        body {
            font-family: 'Noto Sans Gujarati', sans-serif;
            margin: 0;
            padding: 0;
            color: #222;
            line-height: 1.6;
        }

        h1 {
            font-size: 28pt;
            color: #1a237e;
            text-align: center;
            margin-top: 4cm;
            margin-bottom: 1.5cm;
            page-break-after: avoid;
        }

        .author {
            text-align: center;
            font-size: 16pt;
            margin-bottom: 2.5cm;
            color: #333;
        }

        .toc-title {
            font-size: 20pt;
            text-align: center;
            margin-bottom: 1.2cm;
        }

        .toc-entry {
            margin-bottom: 0.25cm;
            font-size: 12pt;
        }

        .toc-entry a {
            text-decoration: none;
            color: #1565c0;
        }

        .chapter {
            page-break-before: always;
        }

        .chapter-title {
            font-size: 18pt;
            text-align: center;
            margin-bottom: 0.5cm;
        }

        .chapter-subtitle {
            font-size: 14pt;
            font-style: italic;
            text-align: center;
            color: #455a64;
            margin-bottom: 1.2cm;
        }

        p {
            text-align: justify;
            margin-bottom: 0.5cm;
            font-size: 11.5pt;
        }

        .index {
            column-count: 2;
            column-gap: 1cm;
            font-size: 11pt;
        }

        .index-entry {
            margin-bottom: 0.2cm;
        }

        .index-entry a {
            text-decoration: none;
            color: #1565c0;
        }

        .title-page {
            page-break-after: always;
        }
    """

    # Initialize subtitle summarizer
    summarizer = SubtitleSummarizer()

    posts = fetch_category_posts()
    if not posts:
        raise SystemExit("No posts found; aborting.")

    # Load checkpoint if exists
    checkpoint_file = Path("chapters_checkpoint.pkl")
    if checkpoint_file.exists():
        with open(checkpoint_file, "rb") as f:
            chapters = pickle.load(f)
        print(f"Loaded {len(chapters)} chapters from checkpoint.")
        # Skip already processed
        processed_nums = {c.number for c in chapters}
        posts = [p for p in posts if p[0] not in processed_nums]
    else:
        chapters = []

    if args.max_chapters.lower() != "all":
        try:
            max_ch = int(args.max_chapters)
        except ValueError:
            raise SystemExit("--max-chapters must be a number or 'all'.")
        posts = posts[:max_ch]

    for i, (number, title, url) in enumerate(posts):
        print(f"Fetching chapter {number}: {title}")
        r = requests.get(url, headers={"User-Agent": USER_AGENT})
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        content_div = soup.select_one("div.entry-content")
        if content_div is None:
            print(f"Warning: could not find entry content for {url}")
            continue

        clean_html = sanitize_html_content(str(content_div))

        # Generate subtitle
        subtitle = summarizer.generate_subtitle(content_div.get_text(), number)

        chapters.append(Chapter(number=number, title=title, url=url, html=clean_html, subtitle=subtitle))

        # Checkpoint every 10 chapters
        if len(chapters) % 10 == 0:
            with open(checkpoint_file, "wb") as f:
                pickle.dump(chapters, f)
            print(f"Checkpoint saved: {len(chapters)} chapters processed.")

    # Final save
    with open(checkpoint_file, "wb") as f:
        pickle.dump(chapters, f)
    print(f"Final checkpoint saved: {len(chapters)} chapters processed.")

    # Ensure chapters are sorted
    chapters.sort(key=lambda c: c.number)
    
    print(f"Total chapters to process: {len(chapters)}")
    chapter_nums = [c.number for c in chapters]
    print(f"Chapter numbers: {chapter_nums}")
    
    # Find missing chapters
    expected = set(range(1, max(chapter_nums) + 1))
    actual = set(chapter_nums)
    missing = sorted(expected - actual - MISSING_CHAPTERS)
    print(f"Missing chapters (excluding known {MISSING_CHAPTERS}): {missing}")

    html = build_html(
        chapters=chapters,
        font_paths=font_paths,
        font_face_rules=font_face_rules,
        css=css,
        book_title="ગાંધી સાર્ધ-શતાબ્દી વંદના",
        author="રમેશ ઓઝા",
        output_html_path=out_html,
    )

    # Generate per chapter HTML files
    for chap in chapters:
        chap_html_path = out_html.parent / f"chapter{chap.number}.html"
        chap_html_parts = []
        chap_html_parts.append("<!DOCTYPE html>")
        chap_html_parts.append('<html lang="gu">')
        chap_html_parts.append("<head>")
        chap_html_parts.append("<meta charset='UTF-8'>")
        chap_html_parts.append(f"<title>{chap.title}</title>")
        chap_html_parts.append("<style>")
        chap_html_parts.append("\n".join(font_face_rules))
        chap_html_parts.append(css)
        chap_html_parts.append("</style>")
        chap_html_parts.append("</head>")
        chap_html_parts.append("<body>")
        chap_html_parts.append("<div class='title-page'>")
        chap_html_parts.append(f"<h1>ગાંધી સાર્ધ-શતાબ્દી વંદના</h1>")
        chap_html_parts.append(f"<div class='author'>લેખક: રમેશ ઓઝા</div>")
        chap_html_parts.append("</div>")
        chap_html_parts.append("<h2 class='toc-title'>અનુક્રમણિકા</h2>")
        chap_html_parts.append(
            "<div class='toc-entry'>"
            f"<a href='#chapter{chap.number}'>"  # noqa: W503
            f"{chap.number}. {chap.title}"  # noqa: W503
            f"</a>"
            "</div>"
        )
        chap_html_parts.append(f"<div class='chapter' id='chapter{chap.number}'>")
        chap_html_parts.append(f"<h2 class='chapter-title'>{chap.title}</h2>")
        if chap.subtitle:
            chap_html_parts.append(
                f"<div class='chapter-subtitle'>{chap.subtitle}</div>"
            )
        chap_html_parts.append(chap.html)
        chap_html_parts.append("</div>")
        # Index for this chapter
        kws = extract_keywords(BeautifulSoup(chap.html, "html.parser").get_text())
        if kws:
            chap_html_parts.append("<div class='chapter'>")
            chap_html_parts.append("<h2 class='toc-title'>અનુક્રમ</h2>")
            chap_html_parts.append("<div class='index'>")
            for word in kws:
                chap_html_parts.append(
                    "<div class='index-entry'>"
                    f"{word}"
                    "</div>"
                )
            chap_html_parts.append("</div>")
            chap_html_parts.append("</div>")
        chap_html_parts.append("</body>")
        chap_html_parts.append("</html>")
        chap_html = "\n".join(chap_html_parts)
        chap_html_path.write_text(chap_html, encoding="utf-8")
        print(f"Generated {chap_html_path}")

    print(f"Writing PDF to {out_pdf}")
    HTML(string=html, base_url=str(out_html.parent)).write_pdf(
        str(out_pdf), stylesheets=[CSS(string="")]
    )

    print("Done.")

    # Remove checkpoint on success
    checkpoint_file.unlink(missing_ok=True)


def test_subtitle_and_index():
    """Test subtitle generation and index extraction."""
    from bs4 import BeautifulSoup
    
    # Sample content
    sample_html = """
    <p>ગાંધીજી સત્ય અને અહિંસાના માર્ગે ચાલતા હતા। તેમનો જીવન સેવા અને ત્યાગનું ઉદાહરણ છે।</p>
    <p>ભારતની સ્વતંત્રતા માટે તેમણે જે પ્રયાસ કર્યા તે અતુલનીય છે। તેમનો ધર્મ સર્વોદય અને લોકશાહીમાં વિશ્વાસ રાખતો હતો।</p>
    """
    
    summarizer = SubtitleSummarizer()
    subtitle = summarizer.generate_subtitle(BeautifulSoup(sample_html, "html.parser").get_text(), 1)
    print(f"Test Subtitle: {subtitle}")
    
    keywords = extract_keywords(BeautifulSoup(sample_html, "html.parser").get_text())
    print(f"Test Keywords: {keywords}")
    
    # Check that excluded words are not in keywords
    assert "ગાંધીજી" not in keywords
    assert "સાર્ધ શતાબ્દી" not in keywords
    assert len(keywords) <= 5
    print("Tests passed.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_subtitle_and_index()
    else:
        main()
