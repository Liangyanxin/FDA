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

# 只运行提取，不运行cleanup
ext._extract_internal('data/今世缘：江苏今世缘酒业股份有限公司2024年年度报告.pdf', data, order, None)

# 打印资产负债表 parent 的顺序列表
print('=== 资产负债表 parent order_list ===')
if '资产负债表' in order and 'parent' in order.get('资产负债表', {}):
    for i, item in enumerate(order['资产负债表']['parent'][:30]):
        print(f'  {i}: {item}')
    print(f'  Total: {len(order["资产负债表"]["parent"])}')
else:
    print('  No order')
