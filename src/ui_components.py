#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI组件模块 - 创建和管理Tkinter界面组件
"""

import tkinter as tk
from tkinter import ttk
import os


class UIComponents:
    """UI组件管理器"""
    
    def __init__(self, root, app):
        self.root = root
        self.app = app  # 主应用实例引用
        self.report_tabs = {}
        
    def create_toolbar(self):
        """创建顶部工具栏"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="📂 选择PDF文件", command=self.app.select_pdf_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="📊 提取数据", command=lambda: self.app.extract_data()).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="🔄 重新提取", command=lambda: self.app.rebuild_data()).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="💾 导出Excel", command=self.app.export_to_excel).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="🔃 刷新", command=self.app.refresh).pack(side=tk.LEFT, padx=5)
        
        return toolbar
    
    def create_path_display(self):
        """创建文件路径显示"""
        path_frame = ttk.Frame(self.root)
        path_frame.pack(side=tk.TOP, fill=tk.X, padx=5)
        
        ttk.Label(path_frame, text="当前文件:").pack(side=tk.LEFT)
        self.app.path_label = ttk.Label(path_frame, text="未选择文件", foreground="gray")
        self.app.path_label.pack(side=tk.LEFT, padx=5)
        
        return path_frame
    
    def create_notebook(self):
        """创建Notebook"""
        self.app.notebook = ttk.Notebook(self.root)
        self.app.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        return self.app.notebook
    
    def create_status_bar(self):
        """创建状态栏"""
        self.app.status_label = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.app.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        return self.app.status_label
    
    def create_tabs(self, notebook):
        """创建所有Tab页面"""
        from src.constants import TABS_CONFIG
        
        for tab_id, tab_title, report_type, company_type in TABS_CONFIG:
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=tab_title)
            
            self.report_tabs[tab_id] = {
                'frame': frame,
                'report_type': report_type,
                'company_type': company_type,
                'tree': None,
                'combo': None
            }
            
            if tab_id == "summary":
                self.create_summary_view(frame)
            elif tab_id == "raw":
                self.create_raw_view(frame)
            else:
                self.create_single_report_view(frame, tab_id)
        
        return self.report_tabs
    
    def create_single_report_view(self, frame, tab_id):
        """创建单张报表视图"""
        config = self.report_tabs[tab_id]
        
        # 控制栏
        control_frame = ttk.Frame(frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Label(control_frame, text="报表列:").pack(side=tk.LEFT)
        combo = ttk.Combobox(control_frame, width=25, state='readonly')
        combo.pack(side=tk.LEFT, padx=5)
        combo.bind('<<ComboboxSelected>>', lambda e, t=tab_id: self.app.view_updater.update_report_view(t))
        config['combo'] = combo
        
        # 表格
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tree = ttk.Treeview(tree_frame, show='headings')
        scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        tree.pack(fill=tk.BOTH, expand=True)
        
        config['tree'] = tree
    
    def create_summary_view(self, frame):
        """创建汇总对照表视图"""
        control_frame = ttk.Frame(frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Label(control_frame, text="报表类型:").pack(side=tk.LEFT)
        self.app.summary_combo = ttk.Combobox(control_frame, width=20, state='readonly')
        self.app.summary_combo.pack(side=tk.LEFT, padx=5)
        self.app.summary_combo['values'] = ["资产负债表", "现金流量表", "利润表"]
        self.app.summary_combo.bind('<<ComboboxSelected>>', self.app.view_updater.update_summary_view)
        
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.app.summary_tree = ttk.Treeview(tree_frame, show='headings')
        scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.app.summary_tree.yview)
        scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.app.summary_tree.xview)
        self.app.summary_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.app.summary_tree.pack(fill=tk.BOTH, expand=True)
    
    def create_raw_view(self, frame):
        """创建原始数据视图"""
        # 左侧文件列表
        left_frame = ttk.Frame(frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        ttk.Label(left_frame, text="PDF文件:").pack(anchor=tk.W)
        self.app.file_listbox = tk.Listbox(left_frame, width=30, height=25)
        self.app.file_listbox.pack(fill=tk.Y, pady=5)
        self.app.file_listbox.bind('<<ListboxSelect>>', self.app.on_file_select)
        
        ttk.Button(left_frame, text="刷新列表", command=self.app.refresh_file_list).pack(pady=5)
        
        # 右侧表格列表
        right_frame = ttk.Frame(frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(right_frame, text="提取的表格列表:").pack(anchor=tk.W)
        
        table_select_frame = ttk.Frame(right_frame)
        table_select_frame.pack(fill=tk.X, pady=5)
        
        self.app.table_combo = ttk.Combobox(table_select_frame, width=40, state='readonly')
        self.app.table_combo.pack(side=tk.LEFT, padx=5)
        self.app.table_combo.bind('<<ComboboxSelected>>', self.app.view_updater.update_raw_view)
        
        tree_frame = ttk.Frame(right_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.app.raw_tree = ttk.Treeview(tree_frame, show='headings')
        scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.app.raw_tree.yview)
        scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.app.raw_tree.xview)
        self.app.raw_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.app.raw_tree.pack(fill=tk.BOTH, expand=True)
