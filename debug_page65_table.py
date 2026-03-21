import sys
sys.stdout.reconfigure(encoding='utf-8')
import pdfplumber
from src.pdf_extractor import PDFExtractor

extractor = PDFExtractor()
pdf = pdfplumber.open('data/今世缘：江苏今世缘酒业股份有限公司2024年年度报告.pdf')

# Page 65 Table 1 (利润表)
page = pdf.pages[64]
tables = page.extract_tables()
table = tables[1]

print('=== Page 65 Table 1 (利润表) ===')
print('Last 5 rows:')
for row in table[-5:]:
    print(row)

print()
print('has_total_row:', extractor.has_total_row(table, '利润表'))
