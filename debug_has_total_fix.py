import sys
sys.stdout.reconfigure(encoding='utf-8')

# Force reload
import importlib
import src.pdf_extractor
importlib.reload(src.pdf_extractor)

from src.pdf_extractor import PDFExtractor
import pdfplumber

extractor = PDFExtractor()

# Test Page 66 Table 0
pdf = pdfplumber.open('data/今世缘：江苏今世缘酒业股份有限公司2024年年度报告.pdf')
page = pdf.pages[65]  # Page 66
tables = page.extract_tables()
table = tables[0]

print('=== Testing Page 66 Table 0 ===')
print('First row:', table[0])
print('has_total_row:', extractor.has_total_row(table, '利润表'))
