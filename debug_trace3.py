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
        
        # 分析页面类型
        page_report_type, page_company_type = extractor.analyze_page_type(page_text, prev_company_type)
        
        if page_report_type == "利润表":
            print(f"\n=== Page {page_num}: {page_company_type} ===")
            
            for table_idx, table in enumerate(tables):
                if not table or len(table) < 2:
                    continue
                
                # 确定报表类型
                report_type = page_report_type
                company_type = page_company_type
                
                if not report_type and prev_report_type:
                    report_type = prev_report_type
                    company_type = prev_company_type
                
                if not report_type or not company_type:
                    continue
                
                key = (report_type, company_type)
                
                # 检查 completed_reports
                if key in completed_reports:
                    print(f"  Table {table_idx}: SKIP - already completed")
                    continue
                
                # 提取数据
                extractor.extract_table_data(table, report_type, company_type, page_num, data, item_order)
                
                # 检查提取后的数量
                if report_type in data and company_type in data[report_type]:
                    count = len(data[report_type][company_type])
                    print(f"  Table {table_idx}: count={count}")
                
                # 检查 has_total_row
                has_total = extractor.has_total_row(table, report_type)
                print(f"  Table {table_idx}: has_total_row={has_total}")
                
                if has_total:
                    if report_type == "利润表" and company_type in data.get("利润表", {}):
                        items_count = len(data[report_type][company_type])
                        print(f"    -> Items: {items_count}, threshold=10")
                        if items_count >= 10:
                            completed_reports.add(key)
                            print(f"    -> MARKED COMPLETE!")
                        else:
                            print(f"    -> NOT complete yet")
                    else:
                        completed_reports.add(key)
                        print(f"    -> MARKED COMPLETE!")
                    
                    # 关键：更新 prev 变量
                    prev_report_type = report_type
                    prev_company_type = company_type
                    
                    print(f"    -> prev updated: {prev_report_type}, {prev_company_type}")

print(f"\n=== Final Result ===")
print(f"parent items: {len(data.get('利润表', {}).get('parent', {}))}")
if '利润表' in data and 'parent' in data['利润表']:
    for item in list(data['利润表']['parent'].keys())[:10]:
        print(f"  - {item}")
