#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gandhi Book PDF Generator
Generates a professional PDF book in Gujarati with clickable TOC and Index.
"""

import os
import json
from weasyprint import HTML, CSS
from gandhi_book_processor import ChapterMetadata

class GandhiBookGenerator:
    def __init__(self, title, author):
        self.title = title
        self.author = author
        self.metadata = ChapterMetadata()
        self.chapters = []

    def add_chapter(self, number, title, content):
        self.metadata.add_chapter(number, title, content)
        chapter_data = self.metadata.get_chapter(number)
        self.chapters.append(chapter_data)

    def generate_html(self):
        # Build Index
        index_entries = self.metadata.build_index()
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="gu">
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                    @bottom-center {{
                        content: counter(page);
                        font-family: 'Noto Sans Gujarati', sans-serif;
                    }}
                }}
                body {{
                    font-family: 'Noto Sans Gujarati', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    text-align: justify;
                }}
                h1, h2, h3 {{
                    color: #2c3e50;
                    text-align: center;
                }}
                .title-page {{
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    page-break-after: always;
                }}
                .toc-page, .index-page {{
                    page-break-after: always;
                }}
                .chapter {{
                    page-break-before: always;
                }}
                .chapter-title {{
                    font-size: 24pt;
                    margin-bottom: 10pt;
                }}
                .chapter-subtitle {{
                    font-size: 18pt;
                    color: #7f8c8d;
                    margin-bottom: 30pt;
                }}
                .toc-list, .index-list {{
                    list-style-type: none;
                    padding: 0;
                }}
                .toc-item, .index-item {{
                    margin-bottom: 10pt;
                    border-bottom: 1px dotted #ccc;
                    display: flex;
                    justify-content: space-between;
                }}
                a {{
                    text-decoration: none;
                    color: inherit;
                }}
                .index-columns {{
                    column-count: 2;
                    column-gap: 20pt;
                }}
            </style>
        </head>
        <body>
            <!-- Title Page -->
            <div class="title-page">
                <h1 style="font-size: 36pt;">{self.title}</h1>
                <h2 style="font-size: 24pt;">લેખક: {self.author}</h2>
            </div>

            <!-- Table of Contents -->
            <div class="toc-page">
                <h1>અનુક્રમણિકા</h1>
                <ul class="toc-list">
        """
        
        for ch in self.chapters:
            html_content += f"""
                    <li class="toc-item">
                        <a href="#chapter-{ch['number']}">{ch['title']} {ch['subtitle']}</a>
                    </li>
            """
            
        html_content += """
                </ul>
            </div>

            <!-- Chapters -->
        """
        
        for ch in self.chapters:
            # Replace newlines with <br> tags outside of the f-string to avoid backslash error
            formatted_content = ch['content'].replace('\n', '<br>')
            html_content += f"""
            <div class="chapter" id="chapter-{ch['number']}">
                <h2 class="chapter-title">{ch['title']}</h2>
                <h3 class="chapter-subtitle">{ch['subtitle']}</h3>
                <div class="chapter-content">
                    {formatted_content}
                </div>
            </div>
            """
            
        html_content += """
            <!-- Index -->
            <div class="index-page">
                <h1>અનુક્રમ (Index)</h1>
                <div class="index-columns">
                    <ul class="index-list">
        """
        
        for entry in index_entries:
            chapters_links = ", ".join([f'<a href="#chapter-{n}">{n}</a>' for n in entry['chapters']])
            html_content += f"""
                        <li class="index-item">
                            <span>{entry['term']}</span>
                            <span>{chapters_links}</span>
                        </li>
            """
            
        html_content += """
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        return html_content

    def save_pdf(self, output_path):
        html_content = self.generate_html()
        HTML(string=html_content).write_pdf(output_path)
        print(f"PDF saved to {output_path}")

if __name__ == "__main__":
    # Example usage with sample data
    generator = GandhiBookGenerator("ગાંધી સાર્ધ-શતાબ્દી વંદના", "રમેશ ઓઝા")
    
    sample_content = "ગાંધીજી સત્ય અને અહિંસાના માર્ગે ચાલતા હતા. તેમનો જીવન સેવા અને ત્યાગનું ઉદાહરણ છે."
    generator.add_chapter(1, "ગાંધી સાર્ધ શતાબ્દી વંદના – 1", sample_content)
    
    generator.save_pdf("/home/ubuntu/gandhi_book_sample.pdf")
