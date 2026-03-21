import sys
sys.stdout.reconfigure(encoding='utf-8')
from src.pdf_extractor import PDFExtractor

# 创建extractor并直接调用内部方法
extractor = PDFExtractor()

pdf_path = 'data/今世缘：江苏今世缘酒业股份有限公司2024年年度报告.pdf'

# 手动模拟提取过程来调试
import pdfplumber
with pdfplumber.open(pdf_path) as pdf:
    # Check pages 64-68
    for i in range(63, 68):
        page = pdf.pages[i]
        page_text = page.extract_text()
        tables = page.extract_tables()
        
        # Get page type
        page_report_type, page_company_type = extractor.analyze_page_type(page_text, None)
        
        print(f'=== Page {i+1} ===')
        print(f'Page type: {page_report_type}, {page_company_type}')
        
        for tidx, table in enumerate(tables):
            if table and len(table) > 0:
                table_report, table_company = extractor.analyze_table_type(table)
                print(f'  Table {tidx}: {table_report}, {table_company}')
        print()
