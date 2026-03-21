#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务数据工具 - 启动脚本
支持财务数据提取工具 (v2.0)
"""

import sys
import os

# 确保可以导入src目录下的模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def main():
    """主函数"""
    print("=" * 50)
    print("财务数据工具 v2.0")
    print("=" * 50)
    
    from src.financial_extractor import main as extractor_main
    extractor_main()


if __name__ == "__main__":
    main()
