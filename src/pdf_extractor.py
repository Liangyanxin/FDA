#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF提取模块 - 处理PDF文件解析和数据提取
重写版：修复财务报表提取逻辑错误
"""

import re
import pdfplumber
from src.constants import RE_NUMERIC_START, RE_CLEAN_NUMBER


class PDFExtractor:
    """PDF数据提取器 - 重写版"""
    
    def __init__(self):
        self.all_raw_tables = []
        
    def open_pdf(self, pdf_path):
        """打开PDF文件"""
        return pdfplumber.open(pdf_path)
    
    def analyze_page_type(self, page_text, prev_company_type=None):
        """从页面文本中分析报表类型"""
        title_text = page_text[:1500] if len(page_text) > 1500 else page_text
        
        company_type = None
        report_type = None
        
        # 排除附注页面的关键词（这些关键词出现在附注中会导致误识别）
        footnote_indicators = [
            "资产负债表日", "利润表日", "现金流量表日",
            "附注七", "附注五", "附注六", "附注八", "附注九", "附注十",
            "附注", "（一）", "（二）", "（三）", "（四）", "（五）", "（六）",
            "1、", "2、", "3、", "4、", "5、", "6、", "7、", "8、", "9、"
        ]
        
        # 检查是否是附注页面（如果同时出现报表名称和附注关键词，更可能是附注）
        has_footnote_indicator = any(indicator in title_text for indicator in footnote_indicators)
        
        # 检查合并报表
        if "合并资产负债表" in title_text and "合并资产负债表内" not in title_text and "合并资产负债表相关" not in title_text:
            # 只有在没有强烈附注信号时才识别为主表
            if not has_footnote_indicator or "合并资产负债表" in title_text[:500]:
                company_type = "consolidated"
                report_type = "资产负债表"
        elif "合并利润表" in title_text and "合并利润表内" not in title_text and "合并利润表相关" not in title_text:
            # 检查是否有母公司利润表
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
        elif "合并现金流量表" in title_text and "合并现金流量表内" not in title_text and "合并现金流量表相关" not in title_text:
            company_type = "consolidated"
            report_type = "现金流量表"
        elif "合并股东权益变动表" in title_text:
            company_type = "consolidated"
            report_type = "股东权益变动表"
        elif "母公司资产负债表" in title_text and "母公司资产负债表内" not in title_text and "母公司资产负债表相关" not in title_text:
            company_type = "parent"
            report_type = "资产负债表"
        elif "母公司利润表" in title_text and "母公司利润表内" not in title_text and "母公司利润表相关" not in title_text:
            company_type = "parent"
            report_type = "利润表"
        elif "母公司现金流量表" in title_text and "母公司现金流量表内" not in title_text and "母公司现金流量表相关" not in title_text:
            company_type = "parent"
            report_type = "现金流量表"
        elif "母公司股东权益变动表" in title_text:
            company_type = "parent"
            report_type = "股东权益变动表"
        # 通用匹配（用于延续页）- 但需要更严格的检查
        elif "资产负债表" in title_text and "资产负债表相关" not in title_text and "资产负债表内" not in title_text:
            # 排除附注页
            if not has_footnote_indicator:
                report_type = "资产负债表"
                if prev_company_type:
                    company_type = prev_company_type
        elif "利润表" in title_text and "利润表相关" not in title_text and "利润表内" not in title_text:
            if not has_footnote_indicator:
                report_type = "利润表"
                if prev_company_type:
                    company_type = prev_company_type
        elif "现金流量表" in title_text and "现金流量表相关" not in title_text and "现金流量表内" not in title_text:
            if not has_footnote_indicator:
                report_type = "现金流量表"
                if prev_company_type:
                    company_type = prev_company_type
            
        return report_type, company_type

    def extract(self, pdf_path, data, item_order, status_callback=None):
        """从PDF提取数据 - 主入口"""
        self._extract_internal(pdf_path, data, item_order, status_callback)
        
        # 后处理：清理资产负债表中的非资产负债表项目
        self.cleanup_balance_sheet(data, item_order)
        
        # 清理现金流量表中的非现金流量表项目
        self.cleanup_cash_flow(data, item_order)
        
        # 清理利润表中的非利润表项目
        self.cleanup_income_statement(data, item_order)
        
        return len(data.get('资产负债表', {}).get('consolidated', {})), len(item_order.get('资产负债表', {}).get('consolidated', []))
    
    def _extract_internal(self, pdf_path, data, item_order, status_callback=None):
        """内部提取方法 - 重写版"""
        self.all_raw_tables = []
        completed_reports = set()
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            if status_callback:
                status_callback(f"正在处理... 共{total_pages}页")
            
            prev_report_type = None
            prev_company_type = None
            pending_table = None
            
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text() or ""
                tables = page.extract_tables()
                
                # 分析页面类型
                page_report_type, page_company_type = self.analyze_page_type(page_text, prev_company_type)
                
                # 如果没有检测到页面类型，但有前一个报表的类型，检查是否是延续页
                if not page_report_type and prev_report_type:
                    # 检查页面是否包含表格（延续页通常会有表格）
                    if tables and len(tables[0]) > 2:
                        page_report_type = prev_report_type
                        page_company_type = prev_company_type
                
                # 如果仍然没有页面类型，检查表格本身是否可以确定类型
                if not page_report_type and tables:
                    # 尝试通过表格内容识别
                    for table in tables:
                        if table and len(table) > 2:
                            table_report_type, table_company_type = self.analyze_table_type(table)
                            if table_report_type:
                                page_report_type = table_report_type
                                # 如果没有公司类型，使用前一个的
                                if not page_company_type and prev_company_type:
                                    page_company_type = prev_company_type
                                break
                
                # 关键修复：如果有报表类型但没有公司类型，使用前一个的公司类型
                if page_report_type and not page_company_type and prev_company_type:
                    page_company_type = prev_company_type
                
                # 关键修复：只要识别到报表类型，就更新 prev 变量（用于延续页）
                # 这样即使当前页没有总计行，下一个延续页也能正确识别
                if page_report_type and page_company_type:
                    prev_report_type = page_report_type
                    prev_company_type = page_company_type
                
                # 处理表格
                for table_idx, table in enumerate(tables):
                    if not table or len(table) < 2:
                        continue
                    
                    # 分析表格类型
                    table_report_type, table_company_type = self.analyze_table_type(table)
                    
                    # 确定最终的报表类型和公司类型
                    report_type = table_report_type if table_report_type else page_report_type
                    company_type = table_company_type if table_company_type else page_company_type
                    
                    # 如果页面有明确的类型，覆盖表格分析的类型
                    if page_report_type and page_company_type:
                        report_type = page_report_type
                        company_type = page_company_type
                    
                    # 如果仍然没有类型，但有前一个报表的类型，沿用前一个
                    if not report_type and prev_report_type:
                        report_type = prev_report_type
                        company_type = prev_company_type
                    
                    # 检查是否是附注内容 - 只有在没有明确的页面类型时才检查
                    if report_type and company_type and not page_report_type:
                        if self.is_footnote_content(table):
                            continue
                        
                        # 检查是否是股东权益变动表
                        if self.is_equity_change_statement(table):
                            continue
                    
                    # 检查表格是否有有效数据
                    if not self.has_valid_data(table):
                        continue
                    
                    # 提取表格数据
                    if report_type and company_type:
                        # 检查是否已完成
                        if (report_type, company_type) in completed_reports:
                            # 如果找到总计行，说明报表已完成
                            if self.has_total_row(table, report_type):
                                continue  # 跳过已完成的报表的后续页
                        
                        self.extract_table_data(table, report_type, company_type, page_num, data, item_order)
                        
                        # 检查是否完成
                        if self.has_total_row(table, report_type):
                            completed_reports.add((report_type, company_type))
                            # 更新 prev_ 变量（覆盖上面的更新，因为找到了完整的报表）
                            prev_report_type = report_type
                            prev_company_type = company_type
                        else:
                            # 保存待处理的表格
                            pending_table = table
                    else:
                        # 没有检测到类型，保存表格待处理
                        if table_report_type:
                            report_type = table_report_type
                            company_type = table_company_type
                            if report_type and company_type:
                                self.extract_table_data(table, report_type, company_type, page_num, data, item_order)
                
                if page_num % 20 == 0 and status_callback:
                    status_callback(f"正在处理... 第{page_num}/{total_pages}页")
        
        return total_pages, len(self.all_raw_tables)
    
    def has_valid_data(self, table):
        """检查表格是否包含有效数据"""
        if not table or len(table) < 2:
            return False
        
        # 检查是否有数值数据
        for row in table[1:]:  # 跳过表头
            if not row or len(row) < 2:
                continue
            for cell in row[1:]:
                if cell:
                    cell_str = str(cell).strip()
                    # 检查是否是数字
                    try:
                        float(cell_str.replace(',', '').replace(' ', '').replace('-', ''))
                        return True
                    except:
                        continue
        return False
    
    def has_total_row(self, table, report_type):
        """检查表格是否包含总计行"""
        if not table:
            return False
        
        for row in table:
            if not row or len(row) < 2:
                continue
            item_name = str(row[0]).strip() if row[0] else ''
            
            if report_type == "资产负债表":
                # 检查负债和股东权益总计行
                if ('负债和' in item_name or '负债与' in item_name) and \
                   ('股东权益' in item_name or '所有者权益' in item_name) and \
                   '总计' in item_name:
                    # 检查是否有有效数据
                    for cell in row[1:]:
                        if cell:
                            cell_str = str(cell).strip()
                            if cell_str and cell_str not in ['', '-', 'None', '—']:
                                try:
                                    float(cell_str.replace(',', '').replace(' ', ''))
                                    return True
                                except:
                                    pass
            elif report_type == "利润表":
                # 检查利润表总计行 - 优先检查"八、每股收益"，然后是"七、综合收益总额"
                # 如果有"八、每股收益"，则以它为结束标志；否则以"七、综合收益总额"为结束标志
                if "每股收益" in item_name:
                    for cell in row[1:]:
                        if cell:
                            cell_str = str(cell).strip()
                            if cell_str and cell_str not in ['', '-', 'None', '—']:
                                try:
                                    float(cell_str.replace(',', '').replace(' ', ''))
                                    return True
                                except:
                                    pass
                elif "综合收益" in item_name and "总额" in item_name:
                    # 如果没有"八、每股收益"，则以"七、综合收益总额"为结束标志
                    for cell in row[1:]:
                        if cell:
                            cell_str = str(cell).strip()
                            if cell_str and cell_str not in ['', '-', 'None', '—']:
                                try:
                                    float(cell_str.replace(',', '').replace(' ', ''))
                                    return True
                                except:
                                    pass
            elif report_type == "现金流量表":
                # 检查期末现金余额行
                if '期末现金' in item_name and '余额' in item_name:
                    for cell in row[1:]:
                        if cell:
                            cell_str = str(cell).strip()
                            if cell_str and cell_str not in ['', '-', 'None', '—']:
                                try:
                                    float(cell_str.replace(',', '').replace(' ', ''))
                                    return True
                                except:
                                    pass
        
        return False
    
    def analyze_table_type(self, table):
        """分析表格类型 - 改进版"""
        if not table or len(table) < 2:
            return None, None
        
        # 提取表格前几行的文本
        table_text = ""
        for row in table[:8]:
            if row:
                for cell in row:
                    if cell:
                        table_text += str(cell) + " "
        
        # 检查是否包含"相关"或"内"等无效关键词
        invalid_patterns = ["相关", "表内"]
        has_invalid = False
        for pattern in invalid_patterns:
            if pattern in table_text:
                # 检查是否是有效的报表标题
                valid_titles = ["合并资产负债表", "合并利润表", "合并现金流量表",
                              "母公司资产负债表", "母公司利润表", "母公司现金流量表"]
                is_valid_title = any(title + pattern in table_text for title in valid_titles)
                if not is_valid_title:
                    has_invalid = True
                    break
        
        if has_invalid:
            return None, None
        
        company_type = None
        report_type = None
        
        # 判断公司类型
        if "合并资产负债表" in table_text and "合并资产负债表相关" not in table_text:
            company_type = "consolidated"
        elif "合并利润表" in table_text and "合并利润表相关" not in table_text:
            company_type = "consolidated"
        elif "合并现金流量表" in table_text and "合并现金流量表相关" not in table_text:
            company_type = "consolidated"
        elif "母公司资产负债表" in table_text and "母公司资产负债表相关" not in table_text:
            company_type = "parent"
        elif "母公司利润表" in table_text and "母公司利润表相关" not in table_text:
            company_type = "parent"
        elif "母公司现金流量表" in table_text and "母公司现金流量表相关" not in table_text:
            company_type = "parent"
            
        # 判断报表类型
        if "资产负债表" in table_text and "资产负债表相关" not in table_text and "资产负债表内" not in table_text:
            report_type = "资产负债表"
        elif "利润表" in table_text and "利润表相关" not in table_text and "利润表内" not in table_text:
            report_type = "利润表"
        elif "现金流量表" in table_text and "现金流量表相关" not in table_text and "现金流量表内" not in table_text:
            report_type = "现金流量表"
        
        # 如果没有通过标题判断，通过内容特征判断
        if not report_type:
            report_type = self._detect_report_type_from_content(table)
        
        return report_type, company_type
    
    def _detect_report_type_from_content(self, table):
        """通过表格内容特征检测报表类型"""
        if not table or len(table) < 2:
            return None
        
        # 提取第一列的项目名称
        first_col_items = []
        for row in table[:20]:
            if row and row[0]:
                first_col_items.append(str(row[0]).strip())
        
        first_col_text = " ".join(first_col_items)
        
        # 审计关键词 - 包含这些关键词的表格不是财务报表
        audit_keywords = [
            "关键审计事项", "审计报告", "审计意见", "我们根据职业判断",
            "该事项在审计中是如何应对的", "审计过程中"
        ]
        if any(kw in first_col_text[:200] for kw in audit_keywords):
            return None
        
        # 资产负债表特征项目
        balance_sheet_items = [
            "货币资金", "交易性金融资产", "应收票据", "应收账款", "预付款项",
            "存货", "流动资产", "非流动资产", "固定资产", "无形资产",
            "短期借款", "应付票据", "应付账款", "预收款项", "应付职工薪酬",
            "应交税费", "流动负债", "非流动负债", "负债合计",
            "实收资本", "资本公积", "盈余公积", "未分配利润", "所有者权益",
            "资产总计", "负债合计", "股东权益"
        ]
        
        # 利润表特征项目
        income_items = [
            "营业收入", "营业成本", "税金及附加", "销售费用", "管理费用",
            "财务费用", "营业利润", "利润总额", "净利润", "综合收益",
            "基本每股收益", "稀释每股收益", "营业总收入"
        ]
        
        # 现金流量表特征项目
        cash_flow_items = [
            "销售商品、提供劳务收到的现金", "经营活动产生的现金流量净额",
            "投资活动产生的现金流量净额", "筹资活动产生的现金流量净额",
            "期末现金", "现金等价物", "现金流入小计", "现金流出小计"
        ]
        
        # 统计各类项目的出现次数
        balance_count = sum(1 for item in balance_sheet_items if item in first_col_text)
        income_count = sum(1 for item in income_items if item in first_col_text)
        cash_count = sum(1 for item in cash_flow_items if item in first_col_text)
        
        max_count = max(balance_count, income_count, cash_count)
        
        if max_count == 0:
            return None
        
        if balance_count == max_count:
            return "资产负债表"
        elif income_count == max_count:
            return "利润表"
        elif cash_count == max_count:
            return "现金流量表"
        
        return None
    
    def is_footnote_content(self, table):
        """检查表格内容是否是附注/明细数据"""
        if not table or len(table) < 2:
            return False
        
        # 提取第一列的项目名称
        first_col_items = []
        for row in table[:15]:
            if row and row[0]:
                first_col_items.append(str(row[0]).strip())
        
        first_col_text = " ".join(first_col_items)
        
        # 附注关键词
        footnote_keywords = [
            "账龄", "原值合计", "坏账准备", "按单项计提", "按组合计提",
            "第一名", "第二名", "第三名", "第四名", "第五名",
            "被投资单位", "一、合营企业", "二、联营企业",
            "长期应收款", "应收账款坏账准备", "存货明细", "固定资产原值", "累计折旧",
            "无形资产明细", "商誉明细", "递延所得税资产", "递延所得税负债",
            "政府补助", "负债项目", "预计负债",
            "应付债券明细", "长期借款明细", "股份变动", "权益工具",
            "收入分类", "合同分类", "主营业务", "其他业务",
            "现金流量补充", "不涉及现金收支", "现金等价物净变动",
            "会计政策变更", "关联方交易", "关联交易",
            "税种", "企业所得税", "增值税", "城市维护建设税",
            "聘请中介机构", "研发费", "研发费用",
            "类别", "房屋及建筑物", "机器设备", "运输设备", "办公设备",
            "工程物资", "专用设备", "项目名称", "本期增加", "本期减少",
            "期初余额", "期末余额", "年初余额", "编制单位", "币种"
        ]
        
        match_count = sum(1 for kw in footnote_keywords if kw in first_col_text)
        
        # 如果匹配超过2个关键词，认为是附注
        if match_count >= 2:
            return True
        
        # 检查特殊模式
        special_patterns = [
            r"^\d+、",  # 数字序号
            r"^\[\d+\]",  # 方括号数字
            r"\d{4}年\d{1,2}月",  # 日期
            r"附注",  # 附注
            r"单位名称",  # 单位名称
            r"被投资单位名称",  # 被投资单位
        ]
        
        for pattern in special_patterns:
            if re.search(pattern, first_col_text):
                if match_count >= 1:
                    return True
        
        return False
    
    def is_equity_change_statement(self, table):
        """检查表格内容是否是股东权益变动表"""
        if not table or len(table) < 2:
            return False
        
        # 提取第一列的项目名称
        first_col_items = []
        for row in table[:30]:
            if row and row[0]:
                first_col_items.append(str(row[0]).strip())
        
        first_col_text = " ".join(first_col_items)
        
        # 股东权益变动表特征
        equity_change_keywords = [
            "上年年末余额", "本年期初余额", "本期增减变动",
            "综合收益总额", "利润分配", "所有者投入",
            "一、上", "二、本", "三、本", "四、本",
            "（一）", "（二）", "（三）", "（四）", "（五）", "（六）",
            "本期提取", "本期使用", "前期差错更正", "会计政策变更",
            "资本公积转", "盈余公积转", "股东权益变动", "所有者权益变动"
        ]
        
        match_count = sum(1 for kw in equity_change_keywords if kw in first_col_text)
        
        return match_count >= 2
    
    def extract_table_data(self, table, report_type, company_type, page_num, data, item_order):
        """提取表格数据 - 改进版"""
        if not table or len(table) < 2:
            return
        
        # 初始化数据结构
        if report_type not in data:
            data[report_type] = {}
        if company_type not in data[report_type]:
            data[report_type][company_type] = {}
        if report_type not in item_order:
            item_order[report_type] = {}
        if company_type not in item_order[report_type]:
            item_order[report_type][company_type] = []
        
        # 识别表头行和数据行的起始位置
        headers = table[0] if table else []
        
        # 检查表头
        data_col_start = 1  # 默认从第2列开始是数据
        
        # 查找"附注"列的位置，并确定数据列的起始位置
        has_footnote_col = False
        for i, header in enumerate(headers):
            if header and '附注' in str(header):
                has_footnote_col = True
                data_col_start = i + 1
                break
        
        # 判断是否有表头行
        first_col = str(headers[0]).strip() if headers and headers[0] else ""
        has_header = first_col in ["项目", "科目", "行次", ""]
        
        # 如果第一列是"科目"，也视为有效表头
        if first_col == "科目":
            has_header = True
        
        # 如果表格有附注列但没有标准表头，可能需要从第0列开始读取数据
        # 检查第一行第一列是否是项目名称（不是表头）
        if not has_header and has_footnote_col:
            # 跳过附注列，从实际数值列开始
            data_col_start = 2  # 假设附注列之后是数值列
        
        # 如果没有表头也没有附注列，检查是否是延续页（没有表头的后续页）
        # 延续页通常第一列是项目名，第二列是空的，第三列开始是数据
        if not has_header and not has_footnote_col:
            # 检查第一行数据行的结构
            if len(table) > 1:
                first_data_row = table[1]
                if first_data_row and len(first_data_row) >= 3:
                    # 如果第1列是项目名，第2列是空的，第3列开始有数据，说明是延续页
                    col1 = str(first_data_row[0]).strip() if first_data_row[0] else ""
                    col2 = str(first_data_row[1]).strip() if len(first_data_row) > 1 and first_data_row[1] else ""
                    col3 = str(first_data_row[2]).strip() if len(first_data_row) > 2 and first_data_row[2] else ""
                    if col1 and not col2 and col3:
                        # 这是延续页，从第3列开始读取数据
                        data_col_start = 2
        
        # 数据行起始位置
        data_rows = table[1:] if has_header else table
        
        # 逐行处理
        for row in data_rows:
            if not row or len(row) < 2:
                continue
            
            item_name = str(row[0]).strip() if row[0] else ''
            
            # 跳过空行和无效行
            if not item_name or item_name == "None" or item_name in ["项目", "科目", "行次", ""]:
                continue
            
            # 清理项目名称
            item_name = self.clean_item_name(item_name)
            if not item_name:
                continue
            
            # 提取数值
            values = []
            for cell in row[data_col_start:]:
                if cell:
                    cell_str = str(cell).strip()
                    cell_str = re.sub(r'[\s,\-–—]', '', cell_str)
                    if cell_str and cell_str != '-':
                        try:
                            values.append(float(cell_str))
                        except:
                            values.append(None)
                    else:
                        values.append(None)
                else:
                    values.append(None)
            
            # 保留有有效数据的行，或者保留分类标题（如"流动资产："）
            # 分类标题以冒号结尾，且是资产负债表/利润表/现金流量表的分类
            is_category_header = False
            if item_name.endswith('：') or item_name.endswith(':'):
                # 检查是否是有效的分类标题
                valid_category_headers = [
                    # 资产负债表
                    "流动资产", "非流动资产", "流动负债", "非流动负债", 
                    "股东权益", "所有者权益", "负债和股东权益", "负债和所有者权益",
                    "资产总计", "负债合计", "负债总计",
                    # 利润表
                    "营业收入", "营业成本", "营业利润", "利润总额", "净利润",
                    # 现金流量表 - 带数字前缀
                    "一、经营活动产生的现金流量", "二、投资活动产生的现金流量", 
                    "三、筹资活动产生的现金流量",
                    # 现金流量表 - 不带数字前缀
                    "经营活动产生的现金流量", "投资活动产生的现金流量", "筹资活动产生的现金流量",
                    "汇率变动对现金", "现金及现金等价物净增加", "期末现金及现金等价物"
                ]
                for header in valid_category_headers:
                    if item_name.startswith(header):
                        is_category_header = True
                        break
                
                # 如果没有匹配到，检查是否是完全匹配的分类标题
                if not is_category_header:
                    exact_category_headers = [
                        "一、经营活动产生的现金流量：", "二、投资活动产生的现金流量：",
                        "三、筹资活动产生的现金流量：", "四、汇率变动对现金及现金等价物的影响",
                        "五、现金及现金等价物净增加额", "六、期末现金及现金等价物余额"
                    ]
                    if item_name in exact_category_headers:
                        is_category_header = True
            
            if any(v is not None for v in values) or is_category_header:
                # 如果是分类标题，保存空值列表
                if is_category_header and not any(v is not None for v in values):
                    values = [None] * len(values)
                self._save_data_item(item_name, values, report_type, company_type, data, item_order)
    
    def _save_data_item(self, item_name, values, report_type, company_type, data, item_order):
        """保存数据项"""
        data_dict = data[report_type][company_type]
        order_list = item_order[report_type][company_type]
        
        if item_name in data_dict:
            # 合并数据
            existing = data_dict[item_name]
            max_len = max(len(existing), len(values))
            merged = []
            for i in range(max_len):
                v1 = existing[i] if i < len(existing) else None
                v2 = values[i] if i < len(values) else None
                # 优先使用非空值
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
    
    def clean_item_name(self, name):
        """清理科目名称"""
        if not name:
            return ""
        name = RE_NUMERIC_START.sub('', str(name))
        # 清理换行符
        name = name.replace('\n', '').replace('\r', '').strip()
        return name
    
    def cleanup_balance_sheet(self, data, item_order):
        """后处理：清理资产负债表中的非资产负债表项目"""
        # 资产负债表标准项目
        valid_items = {
            # 资产
            "货币资金", "交易性金融资产", "应收票据", "应收账款", "预付款项",
            "其他应收款", "存货", "合同资产", "持有待售资产", "一年内到期非流动资产",
            "其他流动资产", "流动资产合计", "流动资产", 
            "债权投资", "其他债权投资", "长期应收款", "长期股权投资", "投资性房地产",
            "固定资产", "在建工程", "使用权资产", "无形资产", "开发支出",
            "商誉", "长期待摊费用", "递延所得税资产", "其他非流动资产",
            "非流动资产合计", "非流动资产",
            "资产总计", "资产合计",
            # 资产 - 补充项目
            "衍生金融资产", "应收款项融资", "其中：应收利息", "应收股利",
            # 负债
            "短期借款", "交易性金融负债", "应付票据", "应付账款", "预收款项",
            "合同负债", "应付职工薪酬", "应交税费", "其他应付款", "持有待售负债",
            "一年内到期非流动负债", "一年内到期的非流动负债", "其他流动负债", "流动负债合计", "流动负债",
            "长期借款", "应付债券", "租赁负债", "长期应付款", "预计负债",
            "递延收益", "递延所得税负债", "其他非流动负债", "非流动负债合计", "非流动负债",
            "负债合计", "负债总计",
            # 负债 - 补充项目
            "衍生金融负债", "长期应付职工薪酬",
            # 权益
            "实收资本", "其他权益工具", "资本公积", "减：库存股", "其他综合收益",
            "专项储备", "盈余公积", "一般风险准备", "未分配利润",
            "归属于母公司所有者权益合计", "归属于母公司所有者权益",
            "少数股东权益", "股东权益合计", "所有者权益合计",
            "负债和股东权益总计", "负债和所有者权益总计", "负债及股东权益合计", "负债及所有者权益合计",
            # 权益 - 补充项目
            "其中：永续债", "股本",
            # 分类标题
            "流动资产：", "非流动资产：", "流动负债：", "非流动负债：", "股东权益：", "所有者权益："
        }
        
        for company_type in ['consolidated', 'parent']:
            if '资产负债表' in data and company_type in data['资产负债表']:
                data_dict = data['资产负债表'][company_type]
                order_list = item_order['资产负债表'][company_type]
                
                # 找到总计行，删除之后的所有项目
                # 修复：从后往前找，找到最后一个总计行
                total_row_idx = -1
                for i in range(len(order_list) - 1, -1, -1):
                    item_name = order_list[i]
                    if '负债和' in item_name and ('股东权益' in item_name or '所有者权益' in item_name) and '总计' in item_name:
                        total_row_idx = i
                        break
                
                # 如果找到总计行，删除其后的所有项目
                if total_row_idx >= 0:
                    items_to_remove = order_list[total_row_idx + 1:]
                    for item_name in items_to_remove:
                        if item_name in data_dict:
                            del data_dict[item_name]
                    order_list = order_list[:total_row_idx + 1]
                    item_order['资产负债表'][company_type] = order_list
                
                # 清理非资产负债表项目
                items_to_remove = []
                for item_name in data_dict.keys():
                    # 检查是否是有效的资产负债表项目
                    is_valid = False
                    for valid_item in valid_items:
                        if item_name == valid_item or item_name.startswith(valid_item + "：") or item_name.startswith(valid_item):
                            is_valid = True
                            break
                    
                    if not is_valid:
                        items_to_remove.append(item_name)
                
                for item_name in items_to_remove:
                    del data_dict[item_name]
                    if item_name in order_list:
                        order_list.remove(item_name)
    
    def cleanup_cash_flow(self, data, item_order):
        """后处理：清理现金流量表中的非现金流量表项目"""
        # 现金流量表标准项目
        valid_items = {
            # 经营活动
            "销售商品、提供劳务收到的现金", "销售商品，提供劳务收到的现金", "收到的税费返还", "收到其他与经营活动有关的现金",
            "经营活动现金流入小计", "购买商品、接受劳务支付的现金", "支付给职工及为职工支付的现金",
            "支付的各项税费", "支付其他与经营活动有关的现金", "经营活动现金流出小计",
            "经营活动产生的现金流量净额", "经营活动产生的现金流量：",
            # 投资活动
            "收回投资收到的现金", "取得投资收益收到的现金", 
            "处置固定资产、无形资产和其他长期资产收回的现金",
            "处置固定资产、无形资产和其他长期资产收回的现金净额",
            "处置子公司及其他营业单位收到的现金净额", "收到其他与投资活动有关的现金",
            "投资活动现金流入小计", "购建固定资产、无形资产和其他长期资产支付的现金",
            "购建固定资产支付的现金", "投资支付的现金", 
            "取得子公司及其他营业单位支付的现金净额", "支付其他与投资活动有关的现金",
            "投资活动现金流出小计", "投资活动产生的现金流量净额", "投资活动产生的现金流量：",
            "投资活动产生/（使用）的现金流量净额",
            # 筹资活动
            "吸收投资收到的现金", "取得借款收到的现金", "发行债券收到的现金",
            "收到其他与筹资活动有关的现金", "赎回其他权益工具所支付的现金",
            "筹资活动现金流入小计", "偿还债务支付的现金", 
            "分配股利、利润或偿付利息支付的现金", "分配股利、利润或偿付利息",
            "支付其他与筹资活动有关的现金", "筹资活动现金流出小计", 
            "筹资活动产生的现金流量净额", "筹资活动产生的现金流量：",
            "筹资活动使用的现金流量净额",
            # 汇率变动
            "汇率变动对现金及现金等价物的影响",
            # 合计
            "现金及现金等价物净增加额", "期初现金及现金等价物余额", "期末现金及现金等价物余额",
            "加：期初现金及现金等价物余额", "六、期末现金及现金等价物余额",
            "五、现金及现金等价物净增加额", "四、汇率变动对现金及现金等价物的影响",
            "现金净增加额",
            # 分类标题 - 带数字前缀的
            "一、经营活动产生的现金流量：", "二、投资活动产生的现金流量：", 
            "三、筹资活动产生的现金流量：", "四、汇率变动对现金及现金等价物的影响",
            "五、现金及现金等价物净增加额", "六、期末现金及现金等价物余额",
            # 分类标题 - 不带数字前缀的
            "经营活动产生的现金流量：", "投资活动产生的现金流量：", 
            "筹资活动产生的现金流量：", "汇率变动对现金及现金等价物的影响",
            "现金及现金等价物净增加额", "期末现金及现金等价物余额",
            # 数字序号分类标题（用于匹配"一、"、"二、"等）
            "一、", "二、", "三、", "四、", "五、", "六、"
        }
        
        for company_type in ['consolidated', 'parent']:
            if '现金流量表' in data and company_type in data['现金流量表']:
                data_dict = data['现金流量表'][company_type]
                order_list = item_order['现金流量表'][company_type]
                
                # 找到期末现金行，删除之后的所有项目
                # 修复：从后往前找，找到最后一个期末现金行
                end_row_idx = -1
                for i in range(len(order_list) - 1, -1, -1):
                    item_name = order_list[i]
                    if '期末' in item_name and '现金' in item_name and '余额' in item_name:
                        end_row_idx = i
                        break
                
                if end_row_idx >= 0:
                    items_to_remove = order_list[end_row_idx + 1:]
                    for item_name in items_to_remove:
                        if item_name in data_dict:
                            del data_dict[item_name]
                    order_list = order_list[:end_row_idx + 1]
                    item_order['现金流量表'][company_type] = order_list
                
                # 清理非现金流量表项目
                items_to_remove = []
                for item_name in data_dict.keys():
                    # 检查是否是有效的现金流量表项目
                    is_valid = False
                    for valid_item in valid_items:
                        if item_name == valid_item or item_name.startswith(valid_item):
                            is_valid = True
                            break
                    
                    if not is_valid:
                        items_to_remove.append(item_name)
                
                for item_name in items_to_remove:
                    del data_dict[item_name]
                    if item_name in order_list:
                        order_list.remove(item_name)
    
    def cleanup_income_statement(self, data, item_order):
        """后处理：清理利润表中的非利润表项目"""
        # 利润表标准项目（包含带前缀和不带前缀的版本）
        valid_items = {
            # 收入 - 带前缀和不带前缀
            "一、营业总收入", "营业总收入", "一、营业收入", "营业收入", "其中：营业收入", "利息收入", "已赚保费", "手续费及佣金收入",
            # 成本费用 - 带前缀和不带前缀
            "二、营业总成本", "营业总成本", "二、营业成本", "营业成本", "其中：营业成本", "利息支出", "手续费及佣金支出",
            "退保金", "赔付支出净额", "提取保险责任准备金净额", "保单红利支出", "分保费用",
            "税金及附加", "销售费用", "管理费用", "研发费用", "财务费用",
            "其中：利息费用", "其中：利息收入",
            # 其他收益 - 带前缀和不带前缀
            "加：其他收益", "其他收益", "加：公允价值变动收益", "公允价值变动收益", 
            "加：投资收益", "投资收益", "加：汇兑收益", "汇兑收益", "加：净敞口套期收益", "净敞口套期收益",
            "信用减值损失", "资产减值损失", "资产处置收益",
            # 营业利润 - 带前缀和不带前缀
            "三、营业利润", "营业利润", "四、利润总额", "利润总额", "五、净利润", "净利润",
            # 利润分配 - 带前缀和不带前缀
            "（一）经营持续性分类", "经营持续性分类", "（二）终止经营分类", "终止经营分类", 
            "持续经营净利润", "终止经营净利润",
            # 其他综合收益 - 带前缀和不带前缀
            "六、其他综合收益的税后净额", "其他综合收益的税后净额", "七、综合收益总额", "综合收益总额",
            "（一）不能重分类进损益的其他综合收益", "不能重分类进损益的其他综合收益", 
            "（二）将重分类进损益的其他综合收益", "将重分类进损益的其他综合收益",
            "其他权益工具投资公允价值变动", "权益法下不能转损益的其他综合收益",
            "外币财务报表折算差额",
            # 综合收益的详细子项目
            "（一）归属母公司所有者的其他综合收益的税后净额", "归属母公司所有者的其他综合收益的税后净额",
            "．不能重分类进损益的其他综合收益", "不能重分类进损益的其他综合收益",
            "（1）权益法下不能转损益的其他综合收益", "权益法下不能转损益的其他综合收益",
            "（2）其他权益工具投资公允价值变动", "其他权益工具投资公允价值变动",
            "．将重分类进损益的其他综合收益", "将重分类进损益的其他综合收益",
            "（1）外币财务报表折算差额", "外币财务报表折算差额",
            "（二）归属于少数股东的其他综合收益的税后净额", "归属于少数股东的其他综合收益的税后净额",
            # 综合收益总额分配
            "（一）归属于母公司所有者的综合收益总额", "归属于母公司所有者的综合收益总额",
            "（二）归属于少数股东的综合收益总额", "归属于少数股东的综合收益总额",
            # 每股收益
            "八、每股收益", "八、每股收益：", "每股收益",
            "（一）基本每股收益", "（一）基本每股收益(元/股)", "基本每股收益", "基本每股收益(元/股)",
            "（二）稀释每股收益", "（二）稀释每股收益(元/股)", "稀释每股收益", "稀释每股收益(元/股)",
            # 分类标题 - 包含所有数字序号
            "一、", "二、", "三、", "四、", "五、", "六、", "七、", "八、",
            "（一）", "（二）", "（三）", "（四）", "（五）", "（六）",
            "（1）", "（2）", "（3）", "（4）", "（5）",
            "．", "其中：", "加：", "减："
        }
        
        for company_type in ['consolidated', 'parent']:
            if '利润表' in data and company_type in data['利润表']:
                data_dict = data['利润表'][company_type]
                order_list = item_order['利润表'][company_type]
                
                # 找到利润表终止行 - 修复：从后往前找，找到最后一个有效终止行
                end_row_idx = -1
                for i in range(len(order_list) - 1, -1, -1):
                    item_name = order_list[i]
                    
                    # 1. "八、每股收益"
                    if item_name.startswith("八、") and '每股收益' in item_name:
                        values = data_dict.get(item_name, [])
                        if any(v is not None for v in values):
                            end_row_idx = i
                            break
                    
                    # 2. "七、综合收益总额"
                    if item_name.startswith("七、") and '综合收益总额' in item_name:
                        values = data_dict.get(item_name, [])
                        if any(v is not None for v in values):
                            end_row_idx = i
                            break
                    
                    # 3. "五、净利润"
                    if item_name.startswith("五、") and '净利润' in item_name:
                        values = data_dict.get(item_name, [])
                        if any(v is not None for v in values):
                            end_row_idx = i
                            break
                
                if end_row_idx >= 0:
                    items_to_remove = order_list[end_row_idx + 1:]
                    for item_name in items_to_remove:
                        if item_name in data_dict:
                            del data_dict[item_name]
                    order_list = order_list[:end_row_idx + 1]
                    item_order['利润表'][company_type] = order_list
                
                # 清理非利润表项目（附注等）
                items_to_remove = []
                for item_name in data_dict.keys():
                    # 跳过带数字前缀的分类标题（如"一、"、"二、"等），但如果它们有有效数据则保留
                    # 只有当项目名称正好匹配分类标题模式且没有数据时才跳过
                    # 但由于我们已经在前面过滤了，这里简化处理：保留所有以数字开头的项目
                    # 因为它们可能是有效的利润表项目
                    
                    # 检查是否是有效的利润表项目
                    is_valid = False
                    for valid_item in valid_items:
                        if item_name == valid_item or item_name.startswith(valid_item):
                            is_valid = True
                            break
                    
                    if not is_valid:
                        items_to_remove.append(item_name)
                
                for item_name in items_to_remove:
                    del data_dict[item_name]
                    if item_name in order_list:
                        order_list.remove(item_name)
