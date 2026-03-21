import sys
sys.stdout.reconfigure(encoding='utf-8')
import pdfplumber
import re
from src.constants import RE_NUMERIC_START

pdf_path = 'data/今世缘：江苏今世缘酒业股份有限公司2024年年度报告.pdf'

# 打开PDF，模拟提取流程
with pdfplumber.open(pdf_path) as pdf:
    prev_report_type = None
    prev_company_type = None
    completed_reports = set()
    
    for page_num, page in enumerate(pdf.pages, 1):
        if page_num < 60 or page_num > 70:  # 只关注60-70页
            continue
            
        page_text = page.extract_text() or ""
        
        # 只关注包含"利润表"的页面
        if "利润表" not in page_text:
            continue
            
        print(f"\n=== Page {page_num} ===")
        tables = page.extract_tables()
        
        if not tables:
            continue
            
        for table_idx, table in enumerate(tables):
            if not table or len(table) < 2:
                continue
            
            # 检查表格内容
            first_col = []
            for row in table[:15]:
                if row and row[0]:
                    first_col.append(str(row[0]).strip())
            
            print(f"\n--- Table {table_idx} ---")
            print(f"First col items: {first_col[:5]}")
            
            # 检查是否有"每股收益"
            has_eps = any("每股收益" in str(item) for item in first_col)
            has_earnings = any("营业收入" in str(item) for item in first_col)
            
            print(f"Has 营业收入: {has_earnings}")
            print(f"Has 每股收益: {has_eps}")
            
            # 模拟处理
            # 1. 检查是否是母公司利润表
            is_parent = "母公司利润表" in page_text or "母公司" in page_text[:500]
            
            # 2. 检查 completed_reports
            print(f"completed_reports before: {completed_reports}")
            
            # 3. 模拟has_total_row
            has_total = False
            for row in table:
                if not row or len(row) < 2:
                    continue
                item_name = str(row[0]).strip() if row[0] else ''
                if "每股收益" in item_name:
                    has_total = True
                    break
            
            print(f"has_total_row result: {has_total}")
            
            # 4. 模拟提取
            if is_parent and "利润表" in page_text:
                report_type = "利润表"
                company_type = "parent"
                
                # 检查是否已完成
                if (report_type, company_type) in completed_reports:
                    print(f"SKIP: Already completed!")
                    continue
                
                # 提取数据
                print(f"EXTRACTING data for {report_type}/{company_type}")
                
                # 模拟extract_table_data
                data_count = len([row for row in table[1:] if row and row[0] and str(row[0]).strip()])
                print(f"  Extracted {data_count} rows from table")
                
                # 模拟完成检查
                if has_total:
                    if report_type == "利润表":
                        items_count = data_count  # 假设
                        if items_count >= 10:
                            completed_reports.add((report_type, company_type))
                            print(f"  MARKED AS COMPLETED!")
                        else:
                            print(f"  NOT completed yet (only {items_count} items)")
                    else:
                        completed_reports.add((report_type, company_type))
                        print(f"  MARKED AS COMPLETED!")
            
            print(f"completed_reports after: {completed_reports}")
