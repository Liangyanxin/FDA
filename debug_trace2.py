import sys
sys.stdout.reconfigure(encoding='utf-8')
import pdfplumber
import re
from src.constants import RE_NUMERIC_START

pdf_path = 'data/今世缘：江苏今世缘酒业股份有限公司2024年年度报告.pdf'

# 打开PDF
with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages, 1):
        if page_num != 67:  # 只关注第67页
            continue
            
        page_text = page.extract_text() or ""
        print(f"=== Page {page_num} ===")
        print(f"Page text preview: {page_text[:800]}")
        print(f"\n=== Checking analyze_page_type result ===")
        
        # 模拟 analyze_page_type
        title_text = page_text[:1500] if len(page_text) > 1500 else page_text
        footnote_indicators = [
            "资产负债表日", "利润表日", "现金流量表日",
            "附注七", "附注五", "附注六", "附注八", "附注九", "附注十",
            "附注", "（一）", "（二）", "（三）", "（四）", "（五）", "（六）",
            "1、", "2、", "3、", "4、", "5、", "6、", "7、", "8、", "9、"
        ]
        has_footnote_indicator = any(indicator in title_text for indicator in footnote_indicators)
        
        company_type = None
        report_type = None
        
        # 检查合并利润表
        if "合并利润表" in title_text and "合并利润表内" not in title_text and "合并利润表相关" not in title_text:
            print("Found: 合并利润表")
            # 检查是否有母公司利润表
            if "母公司利润表" in title_text:
                pos1 = title_text.find("合并利润表")
                pos2 = title_text.find("母公司利润表")
                print(f"  pos1 (合并利润表): {pos1}, pos2 (母公司利润表): {pos2}")
                if pos2 > 0 and (pos1 < 0 or pos2 < pos1):
                    company_type = "parent"
                else:
                    company_type = "consolidated"
            else:
                company_type = "consolidated"
            report_type = "利润表"
        elif "母公司利润表" in title_text and "母公司利润表内" not in title_text and "母公司利润表相关" not in title_text:
            print("Found: 母公司利润表")
            company_type = "parent"
            report_type = "利润表"
        
        print(f"\nanalyze_page_type result: report_type={report_type}, company_type={company_type}")
        
        tables = page.extract_tables()
        
        for table_idx, table in enumerate(tables):
            print(f"\n--- Table {table_idx} ---")
            
            # 分析表格类型
            table_text = ""
            for row in table[:8]:
                if row:
                    for cell in row:
                        if cell:
                            table_text += str(cell) + " "
            
            print(f"Table text preview: {table_text[:200]}...")
            
            # 检查表格中的报表标题
            if "合并利润表" in table_text:
                print("  -> 表格包含: 合并利润表")
            if "母公司利润表" in table_text:
                print("  -> 表格包含: 母公司利润表")
            
            # 检查是否是只有每股收益的表格
            first_col = []
            for row in table[:15]:
                if row and row[0]:
                    first_col.append(str(row[0]).strip())
            
            print(f"First column: {first_col[:5]}")
            
            has_eps = any("每股收益" in str(item) for item in first_col)
            has_earnings = any("营业收入" in str(item) for item in first_col)
            
            print(f"Has 每股收益: {has_eps}, Has 营业收入: {has_earnings}")
            
            # 如果只有每股收益，没有营业收入，这是一个不完整的表格
            if has_eps and not has_earnings:
                print("  => 这是一个不完整的表格（只有每股收益），应该跳过或单独处理")
