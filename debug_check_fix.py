import sys
sys.stdout.reconfigure(encoding='utf-8')

# Read the source file directly
with open('src/pdf_extractor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find has_total_row function and print it
import re
match = re.search(r'def has_total_row\(self.*?\n        return False', content, re.DOTALL)
if match:
    print("=== has_total_row function ===")
    print(match.group(0))
