import sys
sys.stdout.reconfigure(encoding='utf-8')

# 清除所有缓存的模块
import sys
for mod_name in list(sys.modules.keys()):
    if 'pdf_extractor' in mod_name or mod_name.startswith('src.'):
        del sys.modules[mod_name]

# 现在重新导入
from src.pdf_extractor import PDFExtractor

extractor = PDFExtractor()

pdf_path = 'data/今世缘：江苏今世缘酒业股份有限公司2024年年度报告.pdf'
data = {}
item_order = {}

print("开始提取...")
extractor.extract(pdf_path, data, item_order)

print('=== 利润表 ===')
for ct in ['consolidated', 'parent']:
    if '利润表' in data and ct in data['利润表']:
        items = list(data['利润表'][ct].keys())
        print(f'{ct}: {len(items)} items')
        if ct == 'parent':
            for item in items[:10]:
                print(f'  - {item}')
            if len(items) > 10:
                print(f'  ... and {len(items) - 10} more')
