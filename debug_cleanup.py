import sys
sys.stdout.reconfigure(encoding='utf-8')

# 清除所有缓存的模块
for mod_name in list(sys.modules.keys()):
    if 'pdf_extractor' in mod_name or mod_name.startswith('src.'):
        del sys.modules[mod_name]

from src.pdf_extractor import PDFExtractor

extractor = PDFExtractor()

pdf_path = 'data/今世缘：江苏今世缘酒业股份有限公司2024年年度报告.pdf'
data = {}
item_order = {}

# 手动运行提取过程
import pdfplumber
with pdfplumber.open(pdf_path) as pdf:
    prev_report_type = None
    prev_company_type = None
    completed_reports = set()
    
    for page_num, page in enumerate(pdf.pages, 1):
        if page_num < 60 or page_num > 75:
            continue
            
        page_text = page.extract_text() or ""
        tables = page.extract_tables()
        
        if not tables:
            continue
        
        page_report_type, page_company_type = extractor.analyze_page_type(page_text, prev_company_type)
        
        if page_report_type == "利润表":
            for table_idx, table in enumerate(tables):
                if not table or len(table) < 2:
                    continue
                
                report_type = page_report_type
                company_type = page_company_type
                
                if not report_type and prev_report_type:
                    report_type = prev_report_type
                    company_type = prev_company_type
                
                if not report_type or not company_type:
                    continue
                
                key = (report_type, company_type)
                
                if key in completed_reports:
                    continue
                
                extractor.extract_table_data(table, report_type, company_type, page_num, data, item_order)
                
                has_total = extractor.has_total_row(table, report_type)
                
                if has_total:
                    if report_type == "利润表" and company_type in data.get("利润表", {}):
                        items_count = len(data[report_type][company_type])
                        if items_count >= 10:
                            completed_reports.add(key)
                    else:
                        completed_reports.add(key)
                    
                    prev_report_type = report_type
                    prev_company_type = company_type

print("=== Before cleanup ===")
for ct in ['consolidated', 'parent']:
    if '利润表' in data and ct in data['利润表']:
        print(f"{ct}: {len(data['利润表'][ct])} items")
        if ct == 'parent':
            order = item_order['利润表'][ct]
            print(f"  Order list: {order[:5]}...")

# 现在手动运行 cleanup
print("\n=== Running cleanup ===")
extractor.cleanup_income_statement(data, item_order)

print("\n=== After cleanup ===")
for ct in ['consolidated', 'parent']:
    if '利润表' in data and ct in data['利润表']:
        print(f"{ct}: {len(data['利润表'][ct])} items")
        if ct == 'parent':
            order = item_order['利润表'][ct]
            print(f"  Order: {order[:10]}...")
