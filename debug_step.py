import sys
sys.stdout.reconfigure(encoding='utf-8')

# Read the source file directly
with open('src/pdf_extractor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find _extract_internal function and find the part that checks has_total_row
import re
# Find the part with "检查是否完成"
match = re.search(r'# 检查是否完成.*?prev_company_type = company_type', content, re.DOTALL)
if match:
    print("=== Key logic ===")
    print(match.group(0))
