import sys
sys.stdout.reconfigure(encoding='utf-8')
from src.pdf_extractor import PDFExtractor

extractor = PDFExtractor()

pdf_path = 'data/今世缘：江苏今世缘酒业股份有限公司2024年年度报告.pdf'
data = {}
item_order = {}

extractor.extract(pdf_path, data, item_order)

print('=== 利润表 ===')
for ct in ['consolidated', 'parent']:
    if '利润表' in data and ct in data['利润表']:
        items = list(data['利润表'][ct].keys())
        print(f'{ct}: {len(items)} items')
        if ct == 'parent':
            for item in items:
                print(f'  - {item}')
