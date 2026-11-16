import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
import pdfbook
from pdfbook import Book, A4, EMAIL, BOOK, MUTED
pdfbook.NAME = 'UK Self Assessment 2025/26 Deadline Kit'
b = Book(os.path.join(HERE, '..', 'out', 'README.pdf'), A4)
b.new_page(title='README: start here')
b.text('Thank you for buying the UK Self Assessment 2025/26 Deadline Kit from Way of Wealth Studio. It is built for UK sole traders '
       'filing the 2025/26 return (tax year 6 April 2025 to 5 April 2026) by 31 January 2027.', 10.5)
b.h2("What's in your download")
for t in ['UK Self Assessment 2025-26 Deadline Kit - BLANK (start here).xlsx: this is the one you fill in with your own numbers.',
          'UK Self Assessment 2025-26 Deadline Kit - EXAMPLE (filled in).xlsx: a finished year for a made-up freelance designer, Sam, '
          'so you can see every tab and chart working. Look, do not type.',
          'This README.']:
    b.text('•  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Set up in 5 steps')
for i, t in enumerate(['Open the BLANK file and go to Start Here (the second tab).',
                       'Settings: pick cash basis or traditional, the £1,000 trading allowance (Yes only if your costs were tiny), Scottish taxpayer, and any job pay from your P60.',
                       'Income Log and Expenses Log: one row per payment in or out between 6 April 2025 and 5 April 2026. Pick the HMRC category from the dropdown. '
                       'Add business car journeys on Mileage and hours worked at home on Use of Home.',
                       'SA103 Boxes: each total sits next to its official box number on the short form (SA103S) and the full form (SA103F). '
                       'Tax Estimate shows Income Tax, Class 4 National Insurance and what to pay on 31 January 2027 and 31 July 2027.',
                       'File online at gov.uk by 31 January 2027, pay HMRC, tick off the Deadlines tab, then use Tax Pot 26-27 to set money aside each month.'], 1):
    b.text(f'{i}.  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Open it in Google Sheets (free)')
for t in ['Go to drive.google.com, click New > File upload, and upload the BLANK .xlsx file.',
          'Open it, then choose File > Save as Google Sheets. Work in the Google Sheets copy.',
          'Move between tabs with the tab bar along the bottom of the screen.']:
    b.text('•  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Open it in Excel')
b.text('Double-click the BLANK file. Works in Excel 2016 and later (Windows and Mac), Excel online and the Excel phone app. '
       'Pale yellow boxes are for typing; white boxes work themselves out and are locked so nothing breaks '
       '(Review > Unprotect Sheet, no password).', 9.8)
b.h2('Good to know')
for t in ['Box numbers and wording come from HMRC\'s 2025/26 SA103S and SA103F pages (HMRC 12/25). Rates were checked on gov.uk in November 2026.',
          'Covered: trading profit, simplified mileage and use-of-home flat rates, Income Tax (England, Wales and NI bands, or Scottish bands), '
          'Class 4 and voluntary Class 2 National Insurance, payments on account.',
          'Not covered: capital allowances, losses, partnerships, CIS, property income, student loans, savings and dividends, pension and Gift Aid relief, '
          'Child Benefit charge. If any apply to you, speak to an accountant.',
          'Not tax advice. The kit helps you organise your numbers and estimate your bill. It does not file your return or contact HMRC: '
          'HMRC\'s own calculation when you file is the one that counts.']:
    b.text('•  ' + t, 9.8, gap=3)
b.new_page(title='Questions and help')
b.text('Email ' + EMAIL + ' and Joel will help.', 9.8)
b.text('Want help planning your cash flow as a self-employed person? Book a free Cash Flow Session: ' + BOOK, 9.8)
b.c.linkURL(BOOK, (b.M, b.y - 4, b.W - b.M, b.y + 30), relative=0)
b.text('General information, not financial or tax advice. For personal use only. Please do not share or resell the files.', 8.8, color=MUTED)
b.footer(); b.c.save()
print('saved README.pdf')
