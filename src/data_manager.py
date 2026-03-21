#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据管理模块 - 处理数据存储、缓存和JSON文件
"""

import os
import json
from datetime import datetime


class DataManager:
    """数据管理器 - 处理数据存储和加载"""
    
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.current_data = None
        self.current_item_order = None
        self.current_raw_tables = None
        
    def get_json_path(self, pdf_path):
        """获取JSON文件路径"""
        pdf_name = os.path.basename(pdf_path)
        json_name = pdf_name.replace('.pdf', '.json')
        return os.path.join(self.data_dir, json_name)
    
    def load_from_cache(self, pdf_path):
        """从JSON缓存加载数据"""
        json_path = self.get_json_path(pdf_path)
        
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                return cached_data
            except Exception as e:
                print(f"加载缓存失败: {e}")
        return None
    
    def save_to_json(self, pdf_path, data, item_order):
        """保存数据到JSON文件"""
        json_path = self.get_json_path(pdf_path)
        
        pdf_name = os.path.basename(pdf_path)
        
        output_data = {
            "source_file": pdf_name,
            "extract_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": data,
            "item_order": item_order
        }
        
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存JSON失败: {str(e)}")
            return False
    
    def init_data_structure(self):
        """初始化数据结构"""
        from src.constants import DATA_TEMPLATE, ITEM_ORDER_TEMPLATE
        import copy
        return copy.deepcopy(DATA_TEMPLATE), copy.deepcopy(ITEM_ORDER_TEMPLATE)
    
    def list_pdf_files(self):
        """列出data目录下的PDF文件"""
        pdf_files = []
        if os.path.exists(self.data_dir):
            for f in os.listdir(self.data_dir):
                if f.lower().endswith('.pdf'):
                    pdf_files.append(f)
        return sorted(pdf_files)
