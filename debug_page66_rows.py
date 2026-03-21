import sys
sys.stdout.reconfigure(encoding='utf-8')
import pdfplumber

pdf = pdfplumber.open('data/今世缘：江苏今世缘酒业股份有限公司2024年年度报告.pdf')
page = pdf.pages[65]  # Page 66
tables = page.extract_tables()
table = tables[0]

print('All rows in Page 66 Table 0:')
for i, row in enumerate(table):
    if row and row[0]:
        item = str(row[0]).strip()
        if '每股收益' in item or '综合收益' in item or '七、' in item:
            print(f'Row {i}: {row}')
