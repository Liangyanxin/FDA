#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视图更新模块 - 处理界面的数据展示和更新
"""

import re
import os
import tkinter as tk


class ViewUpdater:
    """视图更新器"""
    
    def __init__(self, app):
        self.app = app
    
    def update_all_views(self):
        """更新所有视图"""
        if self.app.all_raw_tables:
            table_headers = self.extract_year_headers()
        else:
            table_headers = self._infer_headers_from_data()
        
        # 更新6个报表Tab的列选择下拉框
        for tab_id in ["parent_balance", "consolidated_balance", 
                       "parent_cashflow", "consolidated_cashflow",
                       "parent_income", "consolidated_income"]:
            config = self.app.report_tabs[tab_id]
            if config['combo']:
                report_type = config['report_type']
                company_type = config['company_type']
                data = self.app.data.get(report_type, {}).get(company_type, {})
                
                if data:
                    max_cols = 0
                    for values in data.values():
                        if values:
                            max_cols = max(max_cols, len(values))
                    
                    if max_cols > 0:
                        col_options = [f"列{i+1}" for i in range(max_cols)]
                        config['combo']['values'] = col_options
                        config['combo'].current(0)
        
        self.app.table_headers = table_headers
        
        for tab_id in ["parent_balance", "consolidated_balance", 
                       "parent_cashflow", "consolidated_cashflow",
                       "parent_income", "consolidated_income"]:
            self.update_report_view(tab_id)
        
        self.app.summary_combo.current(0)
        self.update_summary_view(None)
        
        self.update_raw_table_list()
    
    def _infer_headers_from_data(self):
        """从已提取的数据中推断年份表头 - 动态生成"""
        headers = {}
        
        for report_type in self.app.data:
            for company_type in self.app.data[report_type]:
                data_dict = self.app.data[report_type][company_type]
                if data_dict:
                    max_cols = 0
                    for values in data_dict.values():
                        if values:
                            max_cols = max(max_cols, len(values))
                    
                    if max_cols > 0:
                        # 动态生成列名
                        year_list = [f"列{i+1}" for i in range(max_cols)]
                        headers[(report_type, company_type)] = year_list
        
        return headers
    
    def extract_year_headers(self):
        """从表格中提取年份表头 - 动态获取所有列（包括附注列）"""
        headers = {}
        
        for table_info in self.app.all_raw_tables:
            report_type = table_info.get('report_type')
            company_type = table_info.get('company_type')
            table = table_info.get('data', [])
            
            if table and len(table) > 0:
                header_row = table[0]
                year_list = []
                
                # 动态获取实际的列数（跳过第一列的项目名）
                actual_col_count = len(header_row) - 1
                
                # 从第1列开始获取所有表头（包括附注列）
                for i in range(1, len(header_row)):
                    cell = header_row[i]
                    if cell:
                        cell_str = str(cell).strip()
                        if not cell_str:
                            continue
                        
                        # 检查是否是附注列
                        if '附注' in cell_str:
                            year_list.append('附注')
                            continue
                        
                        years = re.findall(r'20\d{2}', cell_str)
                        if years:
                            year_list.append(cell_str[:20] if len(cell_str) > 20 else cell_str)
                        elif '上年' in cell_str or '上期' in cell_str or '同期' in cell_str:
                            year_list.append('上年')
                        elif '本期' in cell_str:
                            year_list.append('本期')
                        elif cell_str and len(cell_str) < 15:
                            year_list.append(cell_str)
                
                # 如果没有找到年份表头，使用动态生成的列名
                if not year_list and actual_col_count > 0:
                    year_list = [f"列{i}" for i in range(1, actual_col_count + 1)]
                
                if year_list:
                    key = (report_type, company_type)
                    headers[key] = year_list
        
        return headers
    
    def update_report_view(self, tab_id):
        """更新单个报表视图"""
        config = self.app.report_tabs[tab_id]
        tree = config['tree']
        combo = config['combo']
        
        report_type = config['report_type']
        company_type = config['company_type']
        
        data = self.app.data.get(report_type, {}).get(company_type, {})
        
        max_cols = 0
        for values in data.values():
            if values:
                max_cols = max(max_cols, len(values))
        
        header_key = (report_type, company_type)
        saved_headers = getattr(self.app, 'table_headers', {})
        
        # 动态获取列描述，确保与实际列数匹配
        if header_key in saved_headers and len(saved_headers[header_key]) == max_cols:
            col_description = saved_headers[header_key]
        else:
            # 动态生成列名
            col_description = [f"列{i+1}" for i in range(max_cols)] if max_cols > 0 else []
        
        tree.delete(*tree.get_children())
        
        columns = ["科目"] + col_description
        tree['columns'] = columns
        tree.heading("#0", text="")
        tree.heading("科目", text="科目/项目")
        for i, desc in enumerate(col_description):
            tree.heading(desc, text=desc)
        
        tree.column("科目", width=250)
        for desc in col_description:
            tree.column(desc, width=150)
        
        header_years = col_description
        order = self.app.item_order.get(report_type, {}).get(company_type, [])
        
        for item_name in order:
            if item_name in data:
                values = data[item_name]
                row = [item_name]
                for i in range(len(header_years)):
                    if i < len(values):
                        val = values[i]
                        if val is not None and isinstance(val, (int, float)):
                            val_str = f"{val:,.2f}"
                        elif val is not None:
                            val_str = str(val)
                        else:
                            val_str = ""
                    else:
                        val_str = ""
                    row.append(val_str)
                tree.insert("", tk.END, values=row)
    
    def update_summary_view(self, event):
        """更新汇总对照表视图"""
        report_type = self.app.summary_combo.get()
        if not report_type:
            return
        
        tree = self.app.summary_tree
        tree.delete(*tree.get_children())
        
        columns = ["科目", "母公司", "合并报表", "差值"]
        tree['columns'] = columns
        tree.heading("#0", text="")
        tree.heading("科目", text="科目/项目")
        tree.heading("母公司", text="母公司")
        tree.heading("合并报表", text="合并报表")
        tree.heading("差值", text="差值(合并-母公司)")
        
        tree.column("科目", width=250)
        tree.column("母公司", width=150)
        tree.column("合并报表", width=150)
        tree.column("差值", width=150)
        
        parent_data = self.app.data.get(report_type, {}).get("parent", {})
        consolidated_data = self.app.data.get(report_type, {}).get("consolidated", {})
        
        parent_order = self.app.item_order.get(report_type, {}).get("parent", [])
        consolidated_order = self.app.item_order.get(report_type, {}).get("consolidated", [])
        
        ordered_items = []
        seen = set()
        
        for item in parent_order:
            if item not in seen:
                ordered_items.append(item)
                seen.add(item)
        
        for item in consolidated_order:
            if item not in seen:
                ordered_items.append(item)
                seen.add(item)
        
        max_cols = 0
        for values in list(parent_data.values()) + list(consolidated_data.values()):
            if values:
                max_cols = max(max_cols, len(values))
        
        col_index = self._get_latest_col_index(report_type, max_cols)
        
        for item in ordered_items:
            parent_vals = parent_data.get(item, [])
            consolidated_vals = consolidated_data.get(item, [])
            
            parent_val = parent_vals[col_index] if col_index < len(parent_vals) else None
            consolidated_val = consolidated_vals[col_index] if col_index < len(consolidated_vals) else None
            
            if (parent_val is not None and consolidated_val is not None and 
                isinstance(parent_val, (int, float)) and isinstance(consolidated_val, (int, float))):
                diff = consolidated_val - parent_val
                diff_str = f"{diff:+,.2f}"
            else:
                diff_str = ""
                
            if parent_val is not None and isinstance(parent_val, (int, float)):
                parent_str = f"{parent_val:,.2f}"
            elif parent_val is not None:
                parent_str = str(parent_val)
            else:
                parent_str = ""
                
            if consolidated_val is not None and isinstance(consolidated_val, (int, float)):
                consolidated_str = f"{consolidated_val:,.2f}"
            elif consolidated_val is not None:
                consolidated_str = str(consolidated_val)
            else:
                consolidated_str = ""
            
            tree.insert("", tk.END, values=[item, parent_str, consolidated_str, diff_str])
    
    def _get_latest_col_index(self, report_type, max_cols):
        """获取最新数据的列索引"""
        if max_cols == 0:
            return 0
        
        header_key = (report_type, "parent")
        saved_headers = getattr(self.app, 'table_headers', {})
        
        if header_key in saved_headers:
            year_list = saved_headers[header_key]
            for i, year in enumerate(year_list):
                if '本期' in year:
                    return i
                if '12月31日' in year or ('20' in year and '年度' in year):
                    return i
            return len(year_list) - 1 if year_list else max_cols - 1
        
        pdf_name = os.path.basename(self.app.pdf_path) if self.app.pdf_path else ""
        
        is_half_year = '半年度' in pdf_name or '半年' in pdf_name
        is_quarter = '第一季' in pdf_name or '一季度' in pdf_name or '第一季度' in pdf_name
        
        if is_half_year or is_quarter:
            return 0
        else:
            return max_cols - 1
    
    def update_raw_table_list(self):
        """更新原始数据表格列表"""
        table_options = []
        for i, table_info in enumerate(self.app.all_raw_tables):
            report_type = table_info['report_type'] or "未知"
            company_type = table_info['company_type'] or "未知"
            table_options.append(f"P{table_info['page']}_{report_type}_{company_type}")
        
        self.app.table_combo['values'] = table_options
        if table_options:
            self.app.table_combo.current(0)
            self.update_raw_view(None)
    
    def update_raw_view(self, event):
        """更新原始数据视图"""
        table_index = self.app.table_combo.current()
        if table_index < 0 or table_index >= len(self.app.all_raw_tables):
            return
        
        table_info = self.app.all_raw_tables[table_index]
        table = table_info['data']
        
        tree = self.app.raw_tree
        tree.delete(*tree.get_children())
        
        max_cols = 0
        for row in table:
            max_cols = max(max_cols, len(row))
        
        columns = [f"列{i+1}" for i in range(max_cols)]
        tree['columns'] = columns
        tree.heading("#0", text="")
        for col in columns:
            tree.heading(col, text=col)
        
        for row in table:
            values = [str(cell) if cell else "" for cell in row]
            while len(values) < max_cols:
                values.append("")
            tree.insert("", tk.END, values=values[:max_cols])
