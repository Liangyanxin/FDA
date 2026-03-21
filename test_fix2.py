import sys
sys.stdout.reconfigure(encoding='utf-8')

# 清除所有缓存
for mod_name in list(sys.modules.keys()):
    if 'pdf_extractor' in mod_name or mod_name.startswith('src.'):
        del sys.modules[mod_name]

# 直接读取并修改源代码
import re as re_module
import pdfplumber
from src.constants import RE_NUMERIC_START, RE_CLEAN_NUMBER

# 手动实现 PDFExtractor 的核心功能
class FixedExtractor:
    def __init__(self):
        pass
    
    def analyze_page_type(self, page_text, prev_company_type=None):
        title_text = page_text[:1500] if len(page_text) > 1500 else page_text
        company_type = None
        report_type = None
        footnote_indicators = [
            "资产负债表日", "利润表日", "现金流量表日",
            "附注七", "附注五", "附注六", "附注八", "附注九", "附注十",
            "附注", "（一）", "（二）", "（三）", "（四）", "（五）", "（六）",
            "1、", "2、", "3、", "4、", "5、", "6、", "7、", "8、", "9、"
        ]
        has_footnote_indicator = any(indicator in title_text for indicator in footnote_indicators)
        
        if "合并利润表" in title_text and "合并利润表内" not in title_text and "合并利润表相关" not in title_text:
            if "母公司利润表" in title_text:
                pos1 = title_text.find("合并利润表")
                pos2 = title_text.find("母公司利润表")
                if pos2 > 0 and (pos1 < 0 or pos2 < pos1):
                    company_type = "parent"
                    report_type = "利润表"
                else:
                    company_type = "consolidated"
                    report_type = "利润表"
            else:
                company_type = "consolidated"
                report_type = "利润表"
        elif "母公司利润表" in title_text and "母公司利润表内" not in title_text and "母公司利润表相关" not in title_text:
            company_type = "parent"
            report_type = "利润表"
        elif "利润表" in title_text and "利润表相关" not in title_text and "利润表内" not in title_text:
            if not has_footnote_indicator:
                report_type = "利润表"
                if prev_company_type:
                    company_type = prev_company_type
        return report_type, company_type

    def extract_table_data(self, table, report_type, company_type, page_num, data, item_order):
        if not table or len(table) < 2:
            return
        if report_type not in data:
            data[report_type] = {}
        if company_type not in data[report_type]:
            data[report_type][company_type] = {}
        if report_type not in item_order:
            item_order[report_type] = {}
        if company_type not in item_order[report_type]:
            item_order[report_type][company_type] = []
        
        headers = table[0] if table else []
        data_col_start = 1
        has_footnote_col = False
        for i, header in enumerate(headers):
            if header and '附注' in str(header):
                has_footnote_col = True
                data_col_start = i + 1
                break
        
        first_col = str(headers[0]).strip() if headers and headers[0] else ""
        has_header = first_col in ["项目", "科目", "行次", ""]
        if first_col == "科目":
            has_header = True
        
        if not has_header and has_footnote_col:
            data_col_start = 2
        
        if not has_header and not has_footnote_col:
            if len(table) > 1:
                first_data_row = table[1]
                if first_data_row and len(first_data_row) >= 3:
                    col1 = str(first_data_row[0]).strip() if first_data_row[0] else ""
                    col2 = str(first_data_row[1]).strip() if len(first_data_row) > 1 and first_data_row[1] else ""
                    col3 = str(first_data_row[2]).strip() if len(first_data_row) > 2 and first_data_row[2] else ""
                    if col1 and not col2 and col3:
                        data_col_start = 2
        
        data_rows = table[1:] if has_header else table
        
        for row in data_rows:
            if not row or len(row) < 2:
                continue
            item_name = str(row[0]).strip() if row[0] else ''
            if not item_name or item_name == "None" or item_name in ["项目", "科目", "行次", ""]:
                continue
            item_name = item_name.replace('\n', '').replace('\r', '').strip()
            if not item_name:
                continue
            
            values = []
            for cell in row[data_col_start:]:
                if cell:
                    cell_str = str(cell).strip()
                    cell_str = re_module.sub(r'[\s,\-–—]', '', cell_str)
                    if cell_str and cell_str != '-':
                        try:
                            values.append(float(cell_str))
                        except:
                            values.append(None)
                    else:
                        values.append(None)
                else:
                    values.append(None)
            
            if any(v is not None for v in values):
                data_dict = data[report_type][company_type]
                order_list = item_order[report_type][company_type]
                if item_name in data_dict:
                    existing = data_dict[item_name]
                    max_len = max(len(existing), len(values))
                    merged = []
                    for i in range(max_len):
                        v1 = existing[i] if i < len(existing) else None
                        v2 = values[i] if i < len(values) else None
                        if v1 is not None:
                            merged.append(v1)
                        elif v2 is not None:
                            merged.append(v2)
                        else:
                            merged.append(None)
                    data_dict[item_name] = merged
                else:
                    data_dict[item_name] = values
                    if item_name not in order_list:
                        order_list.append(item_name)

    def cleanup_income_statement_fixed(self, data, item_order):
        """修复版：从后往前找终止行"""
        for company_type in ['consolidated', 'parent']:
            if '利润表' in data and company_type in data['利润表']:
                data_dict = data['利润表'][company_type]
                order_list = item_order['利润表'][company_type]
                
                # 从后往前找终止行
                end_row_idx = -1
                for i in range(len(order_list) - 1, -1, -1):
                    item_name = order_list[i]
                    # 找"八、每股收益"
                    if item_name.startswith("八、") and '每股收益' in item_name:
                        values = data_dict.get(item_name, [])
                        if any(v is not None for v in values):
                            end_row_idx = i
                            break
                    # 找"七、综合收益总额"
                    if item_name.startswith("七、") and '综合收益总额' in item_name:
                        values = data_dict.get(item_name, [])
                        if any(v is not None for v in values):
                            end_row_idx = i
                            break
                    # 找"五、净利润"
                    if item_name.startswith("五、") and '净利润' in item_name:
                        values = data_dict.get(item_name, [])
                        if any(v is not None for v in values):
                            end_row_idx = i
                            break
                
                # 如果找到终止行，删除其后面的项目
                if end_row_idx >= 0 and end_row_idx < len(order_list) - 1:
                    items_to_remove = order_list[end_row_idx + 1:]
                    for item_name in items_to_remove:
                        if item_name in data_dict:
                            del data_dict[item_name]
                    order_list = order_list[:end_row_idx + 1]
                    item_order['利润表'][company_type] = order_list
                
                # 清理无效项目
                valid_patterns = [
                    "营业总收入", "营业收入", "营业成本", "税金及附加",
                    "销售费用", "管理费用", "研发费用", "财务费用",
                    "营业利润", "利润总额", "净利润",
                    "其他综合收益", "综合收益", "每股收益",
                    "一、", "二、", "三、", "四、", "五、", "六、", "七、", "八、",
                    "（一）", "（二）", "（三）", "（四）", "（五）", "（六）",
                    "其中：", "加：", "减："
                ]
                
                items_to_remove = []
                for item_name in list(data_dict.keys()):
                    is_valid = any(item_name.startswith(p) or item_name == p for p in valid_patterns)
                    if not is_valid:
                        items_to_remove.append(item_name)
                
                for item_name in items_to_remove:
                    if item_name in data_dict:
                        del data_dict[item_name]
                    if item_name in order_list:
                        order_list.remove(item_name)

# 使用修复版提取
extractor = FixedExtractor()

pdf_path = 'data/今世缘：江苏今世缘酒业股份有限公司2024年年度报告.pdf'
data = {}
item_order = {}

print("开始提取...")
with pdfplumber.open(pdf_path) as pdf:
    prev_report_type = None
    prev_company_type = None
    
    for page_num, page in enumerate(pdf.pages, 1):
        if page_num < 60 or page_num > 75:
            continue
            
        page_text = page.extract_text() or ""
        tables = page.extract_tables()
        
        if not tables:
            continue
        
        page_report_type, page_company_type = extractor.analyze_page_type(page_text, prev_company_type)
        
        if page_report_type == "利润表":
            for table in tables:
                if not table or len(table) < 2:
                    continue
                
                report_type = page_report_type
                company_type = page_company_type
                
                if not report_type and prev_report_type:
                    report_type = prev_report_type
                    company_type = prev_company_type
                
                if not report_type or not company_type:
                    continue
                
                extractor.extract_table_data(table, report_type, company_type, page_num, data, item_order)
                
                if report_type and company_type:
                    prev_report_type = report_type
                    prev_company_type = company_type

print(f"提取后: parent items = {len(data.get('利润表', {}).get('parent', {}))}")

# 运行修复版的 cleanup
print("运行cleanup...")
extractor.cleanup_income_statement_fixed(data, item_order)

print('=== 利润表 ===')
for ct in ['consolidated', 'parent']:
    if '利润表' in data and ct in data['利润表']:
        items = list(data['利润表'][ct].keys())
        print(f'{ct}: {len(items)} items')
        if ct == 'parent':
            for item in items[:10]:
                print(f'  - {item}')
