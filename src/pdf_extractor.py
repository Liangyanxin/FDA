#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF提取模块 - 表格链方式处理资产负债表
"""

import re
import pdfplumber
from src.constants import RE_NUMERIC_START, RE_CLEAN_NUMBER


class PDFExtractor:
    """PDF数据提取器 - 表格链版"""
    
    def __init__(self):
        self.all_raw_tables = []
        
    def open_pdf(self, pdf_path):
        return pdfplumber.open(pdf_path)
    
    # ===== 表格链核心方法 =====
    
    def _find_report_titles(self, pdf):
        """扫描PDF找到所有报表标题位置
        
        返回: dict {page_num: {title, company_type, report_type}}
        """
        titles = {}
        
        # 标题模式定义：(匹配关键词, 标准标题, 公司类型, 报表类型)
        title_patterns = [
            # 资产负债表
            ("合并资产负债表", "合并资产负债表", "consolidated", "资产负债表"),
            ("母公司资产负债表", "母公司资产负债表", "parent", "资产负债表"),
            # ("1、合并年初到报告期末的资产负债表", "合并资产负债表", "consolidated", "资产负债表"),
            # 利润表
            ("合并利润表", "合并利润表", "consolidated", "利润表"),
            ("母公司利润表", "母公司利润表", "parent", "利润表"),
            # ("2、合并年初到报告期末的利润表", "合并利润表", "consolidated", "利润表"),
            # 现金流量表
            ("合并现金流量表", "合并现金流量表", "consolidated", "现金流量表"),
            ("母公司现金流量表", "母公司现金流量表", "parent", "现金流量表"),
            # ("3、合并年初到报告期末的现金流量表", "合并现金流量表", "consolidated", "现金流量表")
        ]
        
        # 排除关键词
        exclude_words = ["附注", "相关", "内", "续", "详见", "参见", "：", ":"]
        
        for page in pdf.pages:
            # 使用 PDF 实际标注的页码
            page_num = page.page_number
            text = page.extract_text()
            if not text:
                continue
            
            # 分割成行，检查前100行（标题通常在页面顶部）
            lines = text.split('\n')[:100]
            
            title_line_idx = -1
            
            for idx, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # 检查是否包含排除词
                if any(w in line for w in exclude_words):
                    continue
                
                # 匹配标题
                for keyword, title, company_type, report_type in title_patterns:
                    if keyword in line:
                        title_line_idx = idx
                        # 检查标题后5行是否有表格
                        check_lines = lines[idx:idx+6]  # 标题行 + 后5行
                        has_table = self._check_has_table_in_lines(page, check_lines)
                        
                        if has_table:
                            titles[page_num] = {
                                "title": title,
                                "company_type": company_type,
                                "report_type": report_type
                            }
                        break
                
                if title_line_idx >= 0:
                    break
       
        return titles
    
    def _check_has_table_in_lines(self, page, lines):
        """检查给定的行区域中是否有表格"""
        # 提取页面所有表格
        tables = page.extract_tables()
        if not tables:
            return False
        
        # 获取页面文本，用于定位
        page_text = page.extract_text()
        if not page_text:
            return False
        
        # 检查每个表格的文本是否与给定行有重叠
        for table in tables:
            if not table or len(table) < 2:
                continue
            
            # 获取表格第一行的内容
            first_row = table[0]
            if not first_row or not first_row[0]:
                continue
            
            table_first_text = str(first_row[0]).strip()
            
            # 检查表格首行是否在给定的行区域中
            for line in lines:
                if table_first_text in line:
                    return True
        
        return False
    
    def _has_total_row(self, table, report_type, company_type=None):
        """检查表格是否包含总计行"""
        if not table:
            return False
        
        # 直接检查每一行，移除换行符后匹配
        for row in table:
            if not row or len(row) < 2:
                continue
            item_name = str(row[0]).strip() if row[0] else ''
            # 移除所有换行符和空格
            clean_name = item_name.replace('\n', '').replace('\r', '').replace(' ', '')
            
            if report_type == "资产负债表":
                # 结束标志："负债和所有者权益或股东权益总计" 或 "负债和股东权益总计"
                if ('负债和所有者权益（或股东权益）总计' in clean_name or 
                    '负债和股东权益总计' in clean_name or '负债和所有者权益总计' in clean_name):
                    # 检查是否有数值
                    for cell in row[1:]:
                        if cell:
                            try:
                                float(str(cell).strip().replace(',', ''))
                                return True
                            except:
                                pass
            elif report_type == "利润表":
                if company_type =="consolidated" and ("（二）稀释每股收益（元/股）" in clean_name or "（二）稀释每股收益(元/股)" in clean_name):
                    for cell in row[1:]:
                        if cell:
                            try:
                                float(str(cell).strip().replace(',', ''))
                                return True
                            except: pass
                if ("六、期末现金及现金等价物余额" in clean_name or"（二）稀释每股收益（元/股）" in clean_name or "（二）稀释每股收益(元/股)" in clean_name) and company_type == "parent":
                        for cell in row[1:]:
                            if cell:
                                try:
                                    float(str(cell).strip().replace(',', ''))
                                    return True
                                except: pass           
            elif report_type == "现金流量表":
                if '六、期末现金及现金等价物余额' in clean_name :
                    for cell in row[1:]:
                        if cell:
                            try:
                                float(str(cell).strip().replace(',', ''))
                                return True
                            except: pass
        
        return False
    
    def _extract_table_data(self, table, data, item_order, report_type, company_type):
        """提取表格数据"""
        if not table or len(table) < 2:
            return
        
        # 初始化
        if report_type not in data:
            data[report_type] = {}
        if company_type not in data[report_type]:
            data[report_type][company_type] = {}
        if report_type not in item_order:
            item_order[report_type] = {}
        if company_type not in item_order[report_type]:
            item_order[report_type][company_type] = []
        
        # 识别表头
        headers = table[0]
        
        # 判断第一行是否为表头
        first_col = str(headers[0]).strip() if headers and headers[0] else ""
        
        # 表头关键词
        header_keywords = ["项目", "科目", "行次"]
        is_header_row = first_col in header_keywords or first_col == ""
        
        # 如果第一行是表头，跳过它；否则从第0行开始
        data_rows = table[1:] if is_header_row else table
        
        # 提取数据 - 读取所有列（包括附注列）
        for row in data_rows:
            if not row or len(row) < 1:
                continue
            
            # 项目名称从第0列获取
            item_name = str(row[0]).strip() if row[0] else ''
            clean_name = item_name.replace('\n', '').replace('\r', '').replace(' ', '')
            
            # 跳过表头行（项目、科目、行次），但保留所有其他行（包括空行）
            if clean_name in ["项目", "科目", "行次", "None"]:
                continue
            
            # 清理项目名称
            item_name = RE_NUMERIC_START.sub('', str(item_name))
            item_name = item_name.replace('\n', '').replace('\r', '').strip()
            
            # 提取所有列的内容（包括附注列）
            # row[0] 是项目名称，row[1] 是附注列（如果有），row[2:] 是数据列
            values = []
            for cell in row[1:]:  # 从第1列开始（包含附注列），读取所有列
                if cell:
                    cell_str = str(cell).strip()
                    cell_str = re.sub(r'[\s,\-–—]', '', cell_str)
                    if cell_str and cell_str != '-':
                        try:
                            values.append(float(cell_str))
                        except:
                            values.append(None)  # 无法转换为数值的设为 None
                    else:
                        values.append(None)
                else:
                    values.append(None)
            
            # 保留所有行（包括空行），无论是否有数值
            data_dict = data[report_type][company_type]
            order_list = item_order[report_type][company_type]
            
            # 使用空字符串作为空行的项目名
            if not item_name:
                item_name = ""
            
            if item_name in data_dict:
                # 合并
                existing = data_dict[item_name]
                max_len = max(len(existing), len(values))
                merged = []
                for i in range(max_len):
                    v1 = existing[i] if i < len(existing) else None
                    v2 = values[i] if i < len(values) else None
                    merged.append(v1 if v1 is not None else v2)
                data_dict[item_name] = merged
            else:
                data_dict[item_name] = values
                if item_name not in order_list:
                    order_list.append(item_name)
    

    # ===== 主提取方法 =====    
    def extract(self, pdf_path, data, item_order, status_callback=None):
        """从PDF提取数据 - 使用表格链方式"""
        
        # 扫描所有标题
        with pdfplumber.open(pdf_path) as pdf:
            titles = self._find_report_titles(pdf)
            
            if status_callback:
                status_callback(f"正在处理... 共{len(pdf.pages)}页")
            
            prev_company_type = None
            prev_report_type = None
            current_company_type = None
            current_report_type = None
            
            for page in pdf.pages:
                tables = page.extract_tables()
                page_num = page.page_number  # 使用实际页码
                text = page.extract_text() or ""
                
                # 检查当前页面标题
                # 先检查titles中是否有当前页的标题
                if page_num in titles:
                    current_company_type = titles[page_num]["company_type"]
                    current_report_type = titles[page_num]["report_type"]
                else:
                    current_company_type = None
                    current_report_type = None
                
                # 如果没有表格，跳过
                if not tables:
                    continue
                
                # 处理表格
                if len(tables) == 1:
                    table = tables[0]
                    
                    # 优先使用当前页标题
                    if current_company_type and current_report_type:
                        company_type = current_company_type 
                        report_type = current_report_type 

                        if company_type and report_type:
                            self._extract_table_data(table, data, item_order, report_type, company_type)
                            prev_company_type = current_company_type
                            prev_report_type = current_report_type
                            
                            # 检查是否完成
                            if self._has_total_row(table, report_type,company_type):
                                prev_company_type = None
                                prev_report_type = None
                                current_company_type = None
                                current_report_type = None                                                                      
                                continue
                    # 如果没有尝试继承上一页的类型
                    elif prev_company_type and prev_report_type:
                        company_type = prev_company_type
                        report_type = prev_report_type
                        self._extract_table_data(table, data, item_order, report_type, company_type)                            

                        if self._has_total_row(table, report_type,company_type):
                            prev_company_type = None
                            prev_report_type = None
                            current_company_type = None
                            current_report_type = None                        
                        
                        continue
                    else:
                        continue  # 没有标题信息，无法确定类型，跳过

                elif len(tables) == 2 :
                    # 双表格：第一个继承，第二个用当前标题或判断内容
                    t0, t1 = tables[0], tables[1]
                    # print(tables[0],tables[1])
                    if current_company_type and current_report_type:
                        
                    # Table 0: 继承prev
                        company_type0 = prev_company_type
                        report_type0 = prev_report_type                
                        self._extract_table_data(t0, data, item_order, report_type0, company_type0)
                        if self._has_total_row(t0, report_type0, company_type0):
                                # 如果第一个表格已经complete了，重置prev
                                prev_company_type = None
                                prev_report_type = None

                    # Table 1: 使用当前标题
                        company_type1 = current_company_type 
                        report_type1 = current_report_type 
                        prev_company_type = current_company_type
                        prev_report_type = current_report_type                               
                       
                        self._extract_table_data(t1, data, item_order, report_type1, company_type1)
                            
                            
                            
                    else:
                        continue        
        
        return len(data.get('资产负债表', {}).get('consolidated', {})), len(item_order.get('资产负债表', {}).get('consolidated', []))
    
   
    
    
