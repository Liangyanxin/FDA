import sys
sys.stdout.reconfigure(encoding='utf-8')
from src.pdf_extractor import PDFExtractor
import pdfplumber

extractor = PDFExtractor()
pdf = pdfplumber.open('data/今世缘：江苏今世缘酒业股份有限公司2024年年度报告.pdf')

# Check pages 64, 65, 66, 67, 68 (indices)
for i in [63, 64, 65, 66, 67]:
    page = pdf.pages[i]
    text = page.extract_text() or ''
    tables = page.extract_tables()
    
    # Analyze page type
    page_report_type, page_company_type = extractor.analyze_page_type(text)
    
    print(f'=== Page {i+1} ===')
    print(f'Page type: {page_report_type}, {page_company_type}')
    print(f'Tables: {len(tables)}')
    
    # Check each table
    for tidx, table in enumerate(tables):
        if table and len(table) > 0:
            table_report_type, table_company_type = extractor.analyze_table_type(table)
            print(f'  Table {tidx}: report={table_report_type}, company={table_company_type}')
    print()
