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

# 打印利润表 parent 的所有项目
print('=== 利润表 parent ===')
if '利润表' in data and 'parent' in data.get('利润表', {}):
    for item in list(data['利润表']['parent'].keys()):
        print(f'  {item}')
else:
    print('  No data')
    
print()
print('=== 利润表 parent order_list ===')
if '利润表' in order and 'parent' in order.get('利润表', {}):
    for i, item in enumerate(order['利润表']['parent']):
        print(f'  {i}: {item}')
else:
    print('  No order')
