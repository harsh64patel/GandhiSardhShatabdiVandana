# Gandhi Book Generator

This tool automatically scrapes articles from the blog, extracts content, and generates a complete book titled "ગાંધી સાર્ધ-શતાબ્દી વંદના" by "રમેશ ઓઝા" in both HTML and PDF formats.

## Features

- Scrapes all Gandhi articles from the blog
- Extracts article content and creates summaries
- Generates a well-formatted book with:
  - Title page
  - Clickable table of contents
  - Chapters with proper formatting
  - Clickable index
- Outputs in both HTML and PDF formats
- Processes chapters in batches to save progress
- Supports Gujarati text with proper fonts

## Requirements

### Python Version
- Python 3.6 or higher

### Required Packages
Install the following packages using pip:

```bash
pip install requests beautifulsoup4 weasyprint tqdm
```

Note: WeasyPrint has additional system dependencies. See the [WeasyPrint installation guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation) for details.

### Font Requirements for Gujarati Text
For proper rendering of Gujarati text in PDF, the script uses:
- Noto Sans Gujarati (loaded via CSS from Google Fonts)

If you encounter font issues, you can install these fonts locally:
- For Ubuntu/Debian: `sudo apt-get install fonts-noto-cjk fonts-wqy-zenhei`
- For Windows: Download and install Noto Sans Gujarati from Google Fonts
- For macOS: Download and install Noto Sans Gujarati from Google Fonts

## Usage

### Basic Usage
Run the script with default settings (processes chapters 1-30):

```bash
python gandhi_book_generator.py
```

### Advanced Usage
Specify chapter range and batch size:

```bash
python gandhi_book_generator.py --start_chapter 1 --end_chapter 100 --batch_size 20
```

Parameters:
- `--start_chapter`: First chapter to process (default: 1)
- `--end_chapter`: Last chapter to process (default: 30)
- `--batch_size`: Number of chapters to process in each batch (default: 10)

### Output
The script creates a directory called `gandhi_book_output` with:
- `chapters/`: Individual chapter files in Markdown format
- `summaries/`: Chapter summaries
- HTML files for each batch and the complete book
- PDF files for each batch and the complete book

## Processing the Complete Book
To process all 646 chapters (excluding the 3 missing articles: 330, 369, 370):

```bash
python gandhi_book_generator.py --start_chapter 1 --end_chapter 649 --batch_size 50
```

This will take some time to complete, but it saves progress after each batch.

## Troubleshooting

### PDF Generation Issues
If you encounter issues with PDF generation:
1. Ensure WeasyPrint is properly installed with all dependencies
2. Check that the required fonts are installed
3. Try increasing the batch size to reduce the number of PDF generations

### Web Scraping Issues
If you encounter issues with web scraping:
1. Check your internet connection
2. The script includes delays to be respectful to the server; you may need to adjust these
3. If the website structure changes, the script may need to be updated

### Memory Issues
If you encounter memory issues when processing many chapters:
1. Reduce the batch size
2. Close other applications to free up memory
3. Consider running the script on a machine with more RAM

## License
This tool is provided for personal use only. Please respect copyright and use responsibly.
