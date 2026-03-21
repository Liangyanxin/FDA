import sys
sys.stdout.reconfigure(encoding='utf-8')
from src.pdf_extractor import PDFExtractor
import pdfplumber

extractor = PDFExtractor()
pdf = pdfplumber.open('data/今世缘：江苏今世缘酒业股份有限公司2024年年度报告.pdf')

page65 = pdf.pages[64]
text65 = page65.extract_text()
report_type, company_type = extractor.analyze_page_type(text65)
print('Page 65:', report_type, company_type)

page67 = pdf.pages[66]
text67 = page67.extract_text()
report_type, company_type = extractor.analyze_page_type(text67)
print('Page 67:', report_type, company_type)
