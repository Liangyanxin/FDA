import sys
sys.stdout.reconfigure(encoding='utf-8')

# 清除缓存
for mod in list(sys.modules.keys()):
    if 'pdf' in mod.lower():
        del sys.modules[mod]

from src.pdf_extractor import PDFExtractor
ext = PDFExtractor()
data = {}
order = {}
ext.extract('data/今世缘：江苏今世缘酒业股份有限公司2024年年度报告.pdf', data, order)

print('资产负债表:')
for ct in ['consolidated', 'parent']:
    if '资产负债表' in data and ct in data['资产负债表']:
        print(f'  {ct}: {len(data["资产负债表"][ct])} items')
        
print('现金流量表:')
for ct in ['consolidated', 'parent']:
    if '现金流量表' in data and ct in data['现金流量表']:
        print(f'  {ct}: {len(data["现金流量表"][ct])} items')

print('利润表:')
for ct in ['consolidated', 'parent']:
    if '利润表' in data and ct in data['利润表']:
        print(f'  {ct}: {len(data["利润表"][ct])} items')
