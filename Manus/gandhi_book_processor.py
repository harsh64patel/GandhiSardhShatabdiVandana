#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gandhi Book Processor - Subtitle Summarization and Index Processing
This script processes article content to generate subtitles and create
a filtered index for the Gandhi 150th Birth Anniversary Tribute book.
"""

import re
from typing import List, Set, Tuple, Dict
from collections import Counter
import json


class SubtitleSummarizer:
    """
    Generates concise subtitles from article content using keyword extraction
    and semantic analysis.
    """
    
    def __init__(self):
        """Initialize the summarizer with Gujarati stop words and patterns."""
        # Common Gujarati stop words to exclude from analysis
        self.gujarati_stopwords = {
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
        
        # Patterns to identify key concepts
        self.key_patterns = [
            r'ગાંધી\s+[^।]*',  # Gandhi-related concepts
            r'સત્ય[^।]*',  # Truth-related
            r'અહિંસા[^।]*',  # Non-violence
            r'સ્વતંત્રતા[^।]*',  # Freedom
            r'આત્મા[^।]*',  # Soul/Self
            r'ધર્મ[^।]*',  # Religion/Duty
            r'સેવા[^।]*',  # Service
            r'શાંતિ[^।]*',  # Peace
            r'યુગ[^।]*',  # Era/Age
            r'ભારત[^।]*',  # India
        ]
    
    def extract_key_phrases(self, text: str, num_phrases: int = 5) -> List[str]:
        """
        Extract key phrases from text using frequency analysis and pattern matching.
        
        Args:
            text: The article content
            num_phrases: Number of key phrases to extract
            
        Returns:
            List of key phrases
        """
        # Split text into sentences
        sentences = re.split(r'[।।।]', text)
        
        # Extract words and phrases
        words = []
        for sentence in sentences:
            # Remove extra whitespace and split
            tokens = sentence.strip().split()
            words.extend(tokens)
        
        # Filter out stop words and short words
        filtered_words = [
            w for w in words 
            if len(w) > 2 and w not in self.gujarati_stopwords
        ]
        
        # Count word frequency
        word_freq = Counter(filtered_words)
        
        # Get top phrases
        top_phrases = [word for word, _ in word_freq.most_common(num_phrases)]
        
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
        
        # Create subtitle based on key phrases
        if key_phrases:
            # Join key phrases with appropriate Gujarati connector
            subtitle = ' અને '.join(key_phrases[:2])
            return f"({subtitle})"
        else:
            # Fallback subtitle based on article number
            return f"(લેખ {article_number})"
    
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


class IndexProcessor:
    """
    Processes article content to generate index entries with filtering
    of repetitive terms.
    """
    
    def __init__(self):
        """Initialize the index processor with repetitive terms to exclude."""
        # Terms to exclude from index (as specified in requirements)
        self.repetitive_terms = {
            'ગાંધીજી', 'ગાંધી', 'રમેશ ઓઝા', 'રમેશ', 'ઓઝા',
            'શતાબ્દી વંદના', 'શતાબ્દી', 'વંદના',
            'ગાંધી સાર્ધ-શતાબ્દી વંદના',
            'ગાંધી સાર્ધ શતાબ્દી વંદના',
        }
        
        # Important terms to prioritize in index
        self.important_terms = {
            'સત્ય', 'અહિંસા', 'સ્વતંત્રતા', 'ધર્મ', 'સમાજ',
            'રાજકારણ', 'આત્મા', 'સેવા', 'શાંતિ', 'ભારત',
            'આંદોલન', 'સંસ્કૃતિ', 'શિક્ષણ', 'અર્થતંત્ર',
            'ન્યાય', 'લોકશાહી', 'રાષ્ટ્રવાદ', 'આધુનિકતા',
        }
    
    def extract_index_terms(self, text: str) -> Set[str]:
        """
        Extract meaningful terms from text for index.
        
        Args:
            text: Article content
            
        Returns:
            Set of index terms
        """
        # Split into words and clean
        words = re.findall(r'\b\w+\b', text)
        
        # Filter for meaningful terms
        index_terms = set()
        
        for word in words:
            # Skip if it's a repetitive term
            if word in self.repetitive_terms:
                continue
            
            # Skip very short words
            if len(word) < 3:
                continue
            
            # Add important terms
            if word in self.important_terms:
                index_terms.add(word)
            
            # Add other meaningful terms (capitalized or long words)
            elif len(word) > 4 or word[0].isupper():
                index_terms.add(word)
        
        return index_terms
    
    def create_index_entry(self, term: str, chapter_numbers: List[int]) -> Dict:
        """
        Create an index entry for a term.
        
        Args:
            term: The index term
            chapter_numbers: List of chapter numbers where term appears
            
        Returns:
            Dictionary with index entry data
        """
        return {
            'term': term,
            'chapters': sorted(list(set(chapter_numbers))),
            'frequency': len(chapter_numbers)
        }
    
    def filter_repetitive_terms(self, terms: Set[str]) -> Set[str]:
        """
        Filter out repetitive terms from index.
        
        Args:
            terms: Set of terms to filter
            
        Returns:
            Filtered set of terms
        """
        return {
            term for term in terms 
            if term not in self.repetitive_terms
        }
    
    def sort_index_entries(self, entries: List[Dict]) -> List[Dict]:
        """
        Sort index entries alphabetically in Gujarati order.
        
        Args:
            entries: List of index entries
            
        Returns:
            Sorted list of entries
        """
        # Sort by term (Gujarati alphabetical order)
        return sorted(entries, key=lambda x: x['term'])


class ChapterMetadata:
    """
    Manages metadata for chapters including titles, subtitles, and content.
    """
    
    def __init__(self):
        """Initialize chapter metadata storage."""
        self.chapters = {}
        self.summarizer = SubtitleSummarizer()
        self.index_processor = IndexProcessor()
    
    def add_chapter(self, chapter_num: int, title: str, content: str):
        """
        Add a chapter with its metadata.
        
        Args:
            chapter_num: Chapter number
            title: Chapter title
            content: Full chapter content
        """
        # Generate subtitle from content
        subtitle = self.summarizer.generate_subtitle(content, chapter_num)
        
        # Extract index terms
        index_terms = self.index_processor.extract_index_terms(content)
        
        self.chapters[chapter_num] = {
            'number': chapter_num,
            'title': title,
            'subtitle': subtitle,
            'content': content,
            'index_terms': index_terms,
            'word_count': len(content.split())
        }
    
    def get_chapter(self, chapter_num: int) -> Dict:
        """Get chapter metadata."""
        return self.chapters.get(chapter_num)
    
    def get_all_index_terms(self) -> Set[str]:
        """Get all unique index terms across all chapters."""
        all_terms = set()
        for chapter in self.chapters.values():
            all_terms.update(chapter['index_terms'])
        return all_terms
    
    def build_index(self) -> List[Dict]:
        """
        Build complete index with chapter references.
        
        Returns:
            List of sorted index entries
        """
        term_chapters = {}
        
        # Collect all terms and their chapter references
        for chapter_num, chapter_data in self.chapters.items():
            for term in chapter_data['index_terms']:
                if term not in term_chapters:
                    term_chapters[term] = []
                term_chapters[term].append(chapter_num)
        
        # Create index entries
        entries = [
            self.index_processor.create_index_entry(term, chapters)
            for term, chapters in term_chapters.items()
        ]
        
        # Sort and return
        return self.index_processor.sort_index_entries(entries)
    
    def export_metadata(self, filepath: str):
        """
        Export chapter metadata to JSON file.
        
        Args:
            filepath: Path to save JSON file
        """
        export_data = {
            'total_chapters': len(self.chapters),
            'chapters': {}
        }
        
        for num, chapter in self.chapters.items():
            export_data['chapters'][str(num)] = {
                'title': chapter['title'],
                'subtitle': chapter['subtitle'],
                'word_count': chapter['word_count'],
                'index_terms': list(chapter['index_terms'])
            }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)


def example_usage():
    """
    Demonstrate usage of the subtitle summarizer and index processor.
    """
    # Sample Gujarati article content
    sample_content = """
    ગાંધીજી સત્ય અને અહિંસાના માર્ગે ચાલતા હતા। તેમનો જીવન સેવા અને ત્યાગનું ઉદાહરણ છે।
    ભારતની સ્વતંત્રતા માટે તેમણે જે પ્રયાસ કર્યા તે અતુલનીય છે। તેમનો ધર્મ સર્વોદય અને 
    લોકશાહીમાં વિશ્વાસ રાખતો હતો। આધુનિક ભારતના નિર્માણમાં ગાંધીજીની ભૂમિકા અગ્રણી છે।
    """
    
    # Create instances
    summarizer = SubtitleSummarizer()
    index_processor = IndexProcessor()
    metadata = ChapterMetadata()
    
    # Generate subtitle
    subtitle = summarizer.generate_subtitle(sample_content, 1)
    print(f"Generated Subtitle: {subtitle}")
    
    # Extract index terms
    index_terms = index_processor.extract_index_terms(sample_content)
    print(f"Index Terms: {index_terms}")
    
    # Filter repetitive terms
    filtered_terms = index_processor.filter_repetitive_terms(index_terms)
    print(f"Filtered Index Terms: {filtered_terms}")
    
    # Add chapter to metadata
    metadata.add_chapter(
        1,
        "ગાંધી સાર્ધ શતાબ્દી વંદના – 1",
        sample_content
    )
    
    # Build index
    index = metadata.build_index()
    print(f"\nGenerated Index:")
    for entry in index:
        print(f"  {entry['term']}: Chapters {entry['chapters']}")


if __name__ == "__main__":
    example_usage()
