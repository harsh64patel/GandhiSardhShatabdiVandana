import re

# Read the file
with open('book_without_subtitle.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove chapter-subtitle divs (including newlines/spaces)
# Pattern: <div class='chapter-subtitle'>...</div> with any content inside
content = re.sub(r"<div class='chapter-subtitle'>.*?</div>\s*\n?", "", content, flags=re.DOTALL)

# Remove index-entry divs
# Pattern: <div class='index-entry'>...</div> with any content inside
content = re.sub(r"<div class='index-entry'>.*?</div>\s*\n?", "", content, flags=re.DOTALL)

# Write back to file
with open('book_without_subtitle.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Successfully removed all chapter-subtitle divs")
print("✓ Successfully removed all index-entry divs")
print("✓ File formatting preserved")
