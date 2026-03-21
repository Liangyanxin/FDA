import sys
sys.stdout.reconfigure(encoding='utf-8')
import pdfplumber
from src.pdf_extractor import PDFExtractor

extractor = PDFExtractor()
pdf = pdfplumber.open('data/今世缘：江苏今世缘酒业股份有限公司2024年年度报告.pdf')

# Check pages 65-70
for i in range(64, 70):
    page = pdf.pages[i]
    tables = page.extract_tables()
    
    print(f'=== Page {i+1} ===')
    for tidx, table in enumerate(tables):
        if table and len(table) > 0:
            report_type, company_type = extractor.analyze_table_type(table)
            has_total = extractor.has_total_row(table, '利润表')
            print(f'  Table {tidx}: report={report_type}, has_total={has_total}')
            if has_total:
                # Find the total row
                for row in table:
                    if row and len(row) > 0:
                        item = str(row[0]).strip() if row[0] else ''
                        if '每股收益' in item or '综合收益' in item:
                            print(f'    Total row: {row}')
                            break
