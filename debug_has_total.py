import sys
sys.stdout.reconfigure(encoding='utf-8')
import pdfplumber

# 打开PDF，找到利润表相关表格
pdf_path = 'data/今世缘：江苏今世缘酒业股份有限公司2024年年度报告.pdf'

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages, 1):
        page_text = page.extract_text() or ""
        
        # 只检查包含"利润表"的页面
        if "利润表" not in page_text:
            continue
            
        print(f"\n=== Page {page_num} ===")
        print(f"Text preview: {page_text[:200]}...")
        
        tables = page.extract_tables()
        if not tables:
            print("No tables found")
            continue
            
        for table_idx, table in enumerate(tables):
            if not table or len(table) < 2:
                continue
                
            print(f"\n--- Table {table_idx} ---")
            
            # 检查表格前几行的第一列
            first_col = []
            for row in table[:15]:
                if row and row[0]:
                    first_col.append(str(row[0]).strip())
            
            print("First column items:")
            for i, item in enumerate(first_col):
                print(f"  {i}: {item}")
            
            # 检查是否有"六、其他综合收益的税后净额"或"七、综合收益总额"
            has_liu_zhonghe = any("六、其他综合收益" in item for item in first_col)
            has_qi_zhonghe = any(item.startswith("七、") and "综合收益总额" in item for item in first_col)
            has_earnings_per_share = any("每股收益" in item for item in first_col)
            
            print(f"\nHas '六、其他综合收益': {has_liu_zhonghe}")
            print(f"Has '七、综合收益总额': {has_qi_zhonghe}")
            print(f"Has '每股收益': {has_earnings_per_share}")
            
            # 手动测试 has_total_row 逻辑
            print("\nTesting has_total_row logic:")
            for row in table:
                if not row or len(row) < 2:
                    continue
                item_name = str(row[0]).strip() if row[0] else ''
                
                if "每股收益" in item_name:
                    # 检查数据
                    for cell in row[1:]:
                        if cell:
                            cell_str = str(cell).strip()
                            if cell_str and cell_str not in ['', '-', 'None', '—']:
                                try:
                                    val = float(cell_str.replace(',', '').replace(' ', ''))
                                    print(f"  FOUND '每股收益' with data: {item_name} = {val}")
                                except:
                                    pass
                elif item_name.startswith("七、") and "综合收益总额" in item_name:
                    for cell in row[1:]:
                        if cell:
                            cell_str = str(cell).strip()
                            if cell_str and cell_str not in ['', '-', 'None', '—']:
                                try:
                                    val = float(cell_str.replace(',', '').replace(' ', ''))
                                    print(f"  FOUND '七、综合收益总额' with data: {item_name} = {val}")
                                except:
                                    pass
