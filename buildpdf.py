    
from pathlib import Path
from weasyprint import CSS, HTML

# Assuming this is part of a script with argparse or similar
# For simplicity, hardcoding the paths here
out_html = Path('book_without_subtitle.html')
out_pdf = Path('output.pdf')  # Or whatever your output path is

# Read the HTML content from the file
with open(out_html, 'r', encoding='utf-8') as f:
    html = f.read()

# Generate the PDF
HTML(string=html, base_url=str(out_html.parent)).write_pdf(
    str(out_pdf), stylesheets=[CSS(string="")]
)