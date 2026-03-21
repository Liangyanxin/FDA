import sys
sys.stdout.reconfigure(encoding='utf-8')

# Read file and find has_total_row
with open('src/pdf_extractor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the function
import re
match = re.search(r'(def has_total_row.*?return False)', content, re.DOTALL)
if match:
    print('Found has_total_row function:')
    print(match.group(1)[:2000])
