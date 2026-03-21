#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复cleanup函数中的终止行查找逻辑
将"从前往后"改为"从后往前"
"""

# 读取原始文件
with open('src/pdf_extractor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复 cleanup_balance_sheet - 找到总计行的逻辑
old_bs_code = '''                # 找到总计行，删除之后的所有项目
                total_row_idx = -1
                for i, item_name in enumerate(order_list):
                    if '负债和' in item_name and ('股东权益' in item_name or '所有者权益' in item_name) and '总计' in item_name:
                        total_row_idx = i
                        break'''

new_bs_code = '''                # 找到总计行，删除之后的所有项目
                # 修复：从后往前找，找到最后一个总计行
                total_row_idx = -1
                for i in range(len(order_list) - 1, -1, -1):
                    item_name = order_list[i]
                    if '负债和' in item_name and ('股东权益' in item_name or '所有者权益' in item_name) and '总计' in item_name:
                        total_row_idx = i
                        break'''

content = content.replace(old_bs_code, new_bs_code)

# 修复 cleanup_cash_flow - 找到期末现金行的逻辑
old_cf_code = '''                # 找到期末现金行，删除之后的所有项目
                end_row_idx = -1
                for i, item_name in enumerate(order_list):
                    if '期末' in item_name and '现金' in item_name and '余额' in item_name:
                        end_row_idx = i
                        break'''

new_cf_code = '''                # 找到期末现金行，删除之后的所有项目
                # 修复：从后往前找，找到最后一个期末现金行
                end_row_idx = -1
                for i in range(len(order_list) - 1, -1, -1):
                    item_name = order_list[i]
                    if '期末' in item_name and '现金' in item_name and '余额' in item_name:
                        end_row_idx = i
                        break'''

content = content.replace(old_cf_code, new_cf_code)

# 修复 cleanup_income_statement - 找到利润表终止行的逻辑
old_is_code = '''                # 找到利润表终止行 - 优先找"八、每股收益"，然后是"七、综合收益总额"
                # 利润表可能以"八、每股收益"结束（如果有每股收益数据）
                end_row_idx = -1
                for i, item_name in enumerate(order_list):
                    if '每股收益' in item_name:
                        end_row_idx = i
                        break
                
                # 如果没找到"八、每股收益"，尝试找"七、综合收益总额"
                if end_row_idx < 0:
                    for i, item_name in enumerate(order_list):
                        if '综合收益总额' in item_name and '七、' in item_name:
                            end_row_idx = i
                            break
                
                # 如果没找到"七、综合收益总额"，尝试找"五、净利润"
                if end_row_idx < 0:
                    for i, item_name in enumerate(order_list):
                        if '净利润' in item_name and '五、' in item_name:
                            end_row_idx = i
                            break
                
                # 如果还没找到，继续查找任何净利润或综合收益
                if end_row_idx < 0:
                    for i, item_name in enumerate(order_list):
                        if '净利润' in item_name or '综合收益' in item_name:
                            end_row_idx = i
                            break'''

new_is_code = '''                # 找到利润表终止行 - 修复：从后往前找，找到最后一个有效终止行
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
                            break'''

content = content.replace(old_is_code, new_is_code)

# 写回文件
with open('src/pdf_extractor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("修复完成！")
