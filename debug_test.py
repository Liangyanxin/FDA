import sys
sys.stdout.reconfigure(encoding='utf-8')

# 直接从文件读取源代码并执行
import importlib.util
spec = importlib.util.spec_from_file_location("pdf_extractor", "src/pdf_extractor.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

PDFExtractor = module.PDFExtractor
extractor = PDFExtractor()

# 手动运行提取过程，添加调试输出
pdf_path = 'data/今世缘：江苏今世缘酒业股份有限公司2024年年度报告.pdf'

import pdfplumber
with pdfplumber.open(pdf_path) as pdf:
    prev_report_type = None
    prev_company_type = None
    completed_reports = set()
    data = {}
    item_order = {}
    
    for page_num, page in enumerate(pdf.pages, 1):
        if page_num < 60 or page_num > 70:
            continue
            
        page_text = page.extract_text() or ""
        if "利润表" not in page_text:
            continue
        
        print(f"\n=== Page {page_num} ===")
        tables = page.extract_tables()
        
        if not tables:
            continue
        
        # 分析页面类型
        page_report_type, page_company_type = extractor.analyze_page_type(page_text, prev_company_type)
        print(f"page_report_type={page_report_type}, page_company_type={page_company_type}")
        
        for table_idx, table in enumerate(tables):
            if not table or len(table) < 2:
                continue
            
            # 检查表格类型
            first_col = []
            for row in table[:10]:
                if row and row[0]:
                    first_col.append(str(row[0]).strip())
            
            print(f"\n--- Table {table_idx} ---")
            print(f"First col: {first_col[:5]}")
            
            # 确定报表类型
            report_type = page_report_type
            company_type = page_company_type
            
            if not report_type and prev_report_type:
                if tables and len(tables[0]) > 2:
                    report_type = prev_report_type
                    company_type = prev_company_type
            
            if not report_type:
                continue
            
            print(f"Using: report_type={report_type}, company_type={company_type}")
            
            # 检查 completed_reports
            key = (report_type, company_type)
            print(f"completed_reports before: {completed_reports}")
            if key in completed_reports:
                print(f"SKIP: Already completed!")
                continue
            
            # 检查 has_valid_data
            if not extractor.has_valid_data(table):
                print(f"SKIP: No valid data")
                continue
            
            # 提取数据
            print(f"EXTRACTING data...")
            extractor.extract_table_data(table, report_type, company_type, page_num, data, item_order)
            
            # 检查当前数据量
            if report_type in data and company_type in data[report_type]:
                count = len(data[report_type][company_type])
                print(f"Data count after extraction: {count}")
            
            # 检查是否完成
            has_total = extractor.has_total_row(table, report_type)
            print(f"has_total_row: {has_total}")
            
            if has_total:
                if report_type == "利润表" and company_type in data.get("利润表", {}):
                    items_count = len(data[report_type][company_type])
                    print(f"Items count: {items_count}")
                    if items_count >= 10:
                        completed_reports.add(key)
                        print(f"MARKED AS COMPLETED!")
                    else:
                        print(f"NOT completed (only {items_count} items)")
                else:
                    completed_reports.add(key)
                    print(f"MARKED AS COMPLETED!")

print(f"\n=== Final Result ===")
print(f"parent items: {len(data.get('利润表', {}).get('parent', {}))}")
if '利润表' in data and 'parent' in data['利润表']:
    for item in list(data['利润表']['parent'].keys())[:5]:
        print(f"  - {item}")
