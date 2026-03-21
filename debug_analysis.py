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

# 打印每个报表类型的项目列表
print('=== 资产负债表 parent ===')
if '资产负债表' in data and 'parent' in data.get('资产负债表', {}):
    for item in list(data['资产负债表']['parent'].keys())[:20]:
        print(f'  {item}')
else:
    print('  No data')
    
print()
print('=== 现金流量表 consolidated ===')
if '现金流量表' in data and 'consolidated' in data.get('现金流量表', {}):
    for item in list(data['现金流量表']['consolidated'].keys())[:20]:
        print(f'  {item}')
else:
    print('  No data')
