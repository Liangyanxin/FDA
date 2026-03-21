#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
常量定义模块
"""

import re

# 预编译正则表达式
RE_NUMERIC_START = re.compile(r'^[\d\.\)\-\s]+')
RE_YEAR = re.compile(r'20\d{2}')
RE_CLEAN_NUMBER = re.compile(r'[\s,\-–—]')

# 报表类型关键词
REPORT_KEYWORDS = [
    "合并资产负债表", "母公司资产负债表",
    "合并利润表", "母公司利润表", 
    "合并现金流量表", "母公司现金流量表"
]

# 数据存储结构模板
DATA_TEMPLATE = {
    "资产负债表": {"parent": {}, "consolidated": {}},
    "现金流量表": {"parent": {}, "consolidated": {}},
    "利润表": {"parent": {}, "consolidated": {}}
}

# 科目顺序存储模板
ITEM_ORDER_TEMPLATE = {
    "资产负债表": {"parent": [], "consolidated": []},
    "现金流量表": {"parent": [], "consolidated": []},
    "利润表": {"parent": [], "consolidated": []}
}

# Tab配置
TABS_CONFIG = [
    ("parent_balance", "🏢 母公司资产负债表", "资产负债表", "parent"),
    ("consolidated_balance", "🌐 合并资产负债表", "资产负债表", "consolidated"),
    ("parent_cashflow", "🏢 母公司现金流量表", "现金流量表", "parent"),
    ("consolidated_cashflow", "🌐 合并现金流量表", "现金流量表", "consolidated"),
    ("parent_income", "🏢 母公司利润表", "利润表", "parent"),
    ("consolidated_income", "🌐 合并利润表", "利润表", "consolidated"),
    ("summary", "📊 汇总对照表", None, None),
    ("raw", "📋 原始数据", None, None),
]
