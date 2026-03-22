#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务数据提取程序 v2.0
模块化版本 - 将代码分离到多个文件中便于维护
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd

# 导入各模块
from src.constants import DATA_TEMPLATE, ITEM_ORDER_TEMPLATE
from src.data_manager import DataManager
from src.pdf_extractor import PDFExtractor
from src.ui_components import UIComponents
from src.view_updater import ViewUpdater


class FinancialDataExtractor:
    """财务数据提取器主类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("财务数据提取工具 v2.0")
        self.root.geometry("1400x900")
        
        # 数据存储
        self.pdf_path = ""
        self.data = None
        self.item_order = None
        self.all_raw_tables = []
        
        # 初始化数据结构
        self._init_data()
        
        # 数据目录
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        
        # 初始化各模块
        self.data_manager = DataManager(self.data_dir)
        self.pdf_extractor = PDFExtractor()
        self.view_updater = ViewUpdater(self)
        
        # UI组件
        self.ui = UIComponents(self.root, self)
        
        # 创建界面
        self._create_ui()
        
    def _init_data(self):
        """初始化数据结构"""
        import copy
        self.data = copy.deepcopy(DATA_TEMPLATE)
        self.item_order = copy.deepcopy(ITEM_ORDER_TEMPLATE)
        
    def _create_ui(self):
        """创建界面"""
        self.ui.create_toolbar()
        self.ui.create_path_display()
        self.ui.create_notebook()
        self.report_tabs = self.ui.create_tabs(self.ui.app.notebook)
        self.ui.create_status_bar()
        
        # 刷新文件列表
        self.refresh_file_list()
    
    def select_pdf_file(self):
        """选择PDF文件"""
        file_path = filedialog.askopenfilename(
            title="选择财务报告PDF文件",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        if file_path:
            self.pdf_path = file_path
            self.path_label.config(text=os.path.basename(file_path))
            self.status_label.config(text="文件已加载，点击'提取数据'开始处理")
            
    def extract_data(self, force_rebuild=False):
        """提取PDF数据"""
        if not self.pdf_path:
            messagebox.showwarning("警告", "请先选择PDF文件！")
            return
        
        self.status_label.config(text="正在提取数据...")
        self.root.update()
        
        # 尝试加载缓存
        if not force_rebuild:
            cached = self.data_manager.load_from_cache(self.pdf_path)
            if cached and "data" in cached:
                self._load_cached_data(cached)
                self.status_label.config(text="已从缓存加载数据")
                self.view_updater.update_all_views()
                messagebox.showinfo("成功", "数据已从缓存加载！")
                return
        
        try:
            # 重新初始化数据
            self._init_data()
            self.all_raw_tables = []
            
            # 提取数据
            def status_callback(msg):
                self.status_label.config(text=msg)
                self.root.update()
            
            total_pages, table_count = self.pdf_extractor.extract(
                self.pdf_path, self.data, self.item_order, status_callback
            )
            
            # 获取原始表格
            self.all_raw_tables = self.pdf_extractor.all_raw_tables
            
            # 保存到JSON
            self.data_manager.save_to_json(self.pdf_path, self.data, self.item_order)
            
            # 更新界面
            self.view_updater.update_all_views()
            
            self.status_label.config(text=f"提取完成！共{total_pages}页，发现{table_count}个表格")
            messagebox.showinfo("成功", "数据提取完成！")
            
        except Exception as e:
            self.status_label.config(text=f"提取失败: {str(e)}")
            messagebox.showerror("错误", f"提取数据时出错：{str(e)}")
    
    def _load_cached_data(self, cached_data):
        """加载缓存数据"""
        if "data" in cached_data:
            for report_type in cached_data["data"]:
                if report_type in self.data:
                    for company_type in cached_data["data"][report_type]:
                        if company_type in self.data[report_type]:
                            self.data[report_type][company_type] = cached_data["data"][report_type][company_type]
        
        if "item_order" in cached_data:
            self.item_order = cached_data["item_order"]
        
        if "all_raw_tables" in cached_data:
            self.all_raw_tables = cached_data["all_raw_tables"]
    
    def rebuild_data(self):
        """强制重新从PDF提取数据"""
        if not self.pdf_path:
            messagebox.showwarning("警告", "请先选择PDF文件！")
            return
        
        if messagebox.askyesno("确认", "确定要重新从PDF提取数据吗？\n这将重新处理PDF文件，可能需要较长时间。"):
            self.extract_data(force_rebuild=True)
            
    def refresh_file_list(self):
        """刷新文件列表"""
        if hasattr(self, 'file_listbox'):
            self.file_listbox.delete(0, tk.END)
            pdf_files = self.data_manager.list_pdf_files()
            for f in pdf_files:
                self.file_listbox.insert(tk.END, f)
    
    def on_file_select(self, event):
        """文件选择事件"""
        selection = self.file_listbox.curselection()
        if selection:
            filename = self.file_listbox.get(selection[0])
            self.pdf_path = os.path.join(self.data_dir, filename)
            self.path_label.config(text=filename)
            self.extract_data()
    
    def refresh(self):
        """刷新界面"""
        self.pdf_path = ""
        self.path_label.config(text="未选择文件")
        
        # 清空数据
        self._init_data()
        self.all_raw_tables = []
        
        # 清空所有树视图
        for tab_id, config in self.report_tabs.items():
            if config['tree']:
                config['tree'].delete(*config['tree'].get_children())
            if config['combo']:
                config['combo']['values'] = []
                
        self.refresh_file_list()
        self.status_label.config(text="就绪")
    
    def export_to_excel(self):
        """导出到Excel"""
        has_data = any(
            self.data[rt][ct] 
            for rt in self.data 
            for ct in self.data[rt]
        )
        
        if not has_data:
            messagebox.showwarning("警告", "没有可导出的数据！")
            return
            
        from datetime import datetime
        file_path = filedialog.asksaveasfilename(
            title="保存Excel文件",
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
            initialfile=f"财务数据_{datetime.now().strftime('%Y%m%d')}"
        )
        
        if not file_path:
            return
            
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 导出6张报表
                for report_type in ["资产负债表", "现金流量表", "利润表"]:
                    for company_type, company_name in [("parent", "母公司"), ("consolidated", "合并报表")]:
                        data = self.data.get(report_type, {}).get(company_type, {})
                        if data:
                            rows = []
                            max_cols = 0
                            for item, values in data.items():
                                max_cols = max(max_cols, len(values) if values else 0)
                            
                            for item, values in data.items():
                                row = [item]
                                for i in range(max_cols):
                                    val = values[i] if i < len(values) else None
                                    if val is not None and isinstance(val, (int, float)):
                                        row.append(f"{val:,.2f}")
                                    elif val is not None:
                                        row.append(str(val))
                                    else:
                                        row.append("")
                                rows.append(row)
                            
                            col_names = ["科目"] + [f"列{i+1}" for i in range(max_cols)]
                            df = pd.DataFrame(rows, columns=col_names)
                            sheet_name = f"{company_name}_{report_type[:6]}"
                            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
                            
                # 导出汇总对照表
                summary_rows = []
                for report_type in ["资产负债表", "现金流量表", "利润表"]:
                    parent_data = self.data.get(report_type, {}).get("parent", {})
                    consolidated_data = self.data.get(report_type, {}).get("consolidated", {})
                    
                    all_items = set(parent_data.keys()) | set(consolidated_data.keys())
                    
                    max_cols = 0
                    for values in list(parent_data.values()) + list(consolidated_data.values()):
                        if values:
                            max_cols = max(max_cols, len(values))
                    
                    col_index = self.view_updater._get_latest_col_index(report_type, max_cols)
                    
                    for item in sorted(all_items):
                        parent_vals = parent_data.get(item, [])
                        consolidated_vals = consolidated_data.get(item, [])
                        
                        parent_val = parent_vals[col_index] if col_index < len(parent_vals) else None
                        consolidated_val = consolidated_vals[col_index] if col_index < len(consolidated_vals) else None
                        
                        diff = None
                        if (parent_val is not None and consolidated_val is not None and
                            isinstance(parent_val, (int, float)) and isinstance(consolidated_val, (int, float))):
                            diff = consolidated_val - parent_val
                        
                        summary_rows.append({
                            '报表类型': report_type,
                            '科目': item,
                            '母公司': parent_val,
                            '合并报表': consolidated_val,
                            '差值': diff
                        })
                    
                if summary_rows:
                    df = pd.DataFrame(summary_rows)
                    df.to_excel(writer, sheet_name="汇总对照表", index=False)
                    
            messagebox.showinfo("成功", f"数据已导出到：\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{str(e)}")


def main():
    """主函数"""
    root = tk.Tk()
    app = FinancialDataExtractor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
