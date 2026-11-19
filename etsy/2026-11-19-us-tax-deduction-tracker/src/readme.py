import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
import pdfbook
from pdfbook import Book, EMAIL, BOOK, MUTED
from reportlab.lib.pagesizes import letter
pdfbook.NAME = 'US Self-Employed Tax Deduction and Quarterly Tax Tracker'
b = Book(os.path.join(HERE, '..', 'out', 'README.pdf'), letter)
b.new_page(title='README: start here')
b.text('Thank you for buying the US Self-Employed Tax Deduction and Quarterly Tax Tracker from Way of Wealth Studio. It is built for US 1099 '
       'freelancers, sole proprietors, single-member LLCs and side hustlers who file a Schedule C, for tax years 2026 and 2027.', 10.5)
b.h2("What's in your download")
for t in ['US Self-Employed Tax Tracker 2026-2027 - BLANK (start here).xlsx: the one you fill in with your own numbers.',
          'US Self-Employed Tax Tracker 2026-2027 - EXAMPLE (filled in).xlsx: a finished year for a made-up freelance designer, Jordan, '
          'so you can see every tab and chart working. Look, do not type.',
          'This README.']:
    b.text('•  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Set up in 5 steps (also written on the Start Here tab)')
for i, t in enumerate(['Settings: pick your TAX YEAR (2026 or 2027) in the one dropdown. Every log, due date, bracket and mileage rate follows it. '
                       'Then your filing status, last year\'s total tax (for safe harbor) and your home office square feet.',
                       'Income Log: type each payment, or paste a CSV of your invoices into the yellow columns B to F (paste as values). '
                       'Any order and any date style: the list on the right sorts itself and shows which clients should send a 1099-NEC.',
                       'Deductions and Mileage: pick the Schedule C category for each cost (the line number fills in) and log business trips '
                       '(the IRS standard mileage rate is picked by date).',
                       'Schedule C, Tax Estimate and Quarterly Tax: your totals by Schedule C line, self-employment tax, a federal income tax estimate, '
                       'the safe-harbor amount and what to pay on each Form 1040-ES due date.',
                       'Once a month, open the Monthly Money Check-in. Before tax time, work through the Accountant Checklist and hand over the file.'], 1):
    b.text(f'{i}.  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Open it in Google Sheets (free)')
for t in ['Go to drive.google.com, click New > File upload, and upload the BLANK .xlsx file.',
          'Open it, then choose File > Save as Google Sheets. Work in the Google Sheets copy.',
          'Move between tabs with the tab bar along the bottom of the screen.']:
    b.text('•  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Open it in Excel')
b.text('Double-click the BLANK file. Built with Excel 2016-compatible formulas; works in Microsoft Excel and Google Sheets. '
       'No macros. Pale yellow boxes are for typing; white boxes work themselves out and are locked so nothing breaks '
       '(Review > Unprotect Sheet, no password).', 9.8)
b.footer()
b.new_page(title='Good to know')
for t in ['Rates checked on 19 Nov 2026: Schedule C line numbers from the current (2025) form; mileage 72.5 cents (Jan-Jun 2026) and 76 cents (from Jul 1, 2026); '
          'Social Security wage base $184,500 (2026) and $192,300 (2027); brackets and standard deductions from IRS Rev. Proc. 2025-32 and 2026-35. '
          'The 2027 mileage rate is not out yet: update it on the Tax Rates tab when the IRS announces it.',
          'Covered: Schedule C income and expenses, standard mileage, simplified home office, self-employment tax, federal income tax with the '
          'standard deduction and QBI deduction, safe harbor, the four 1040-ES payments, and a rough state figure.',
          'Not covered: credits, itemized deductions, depreciation schedules, inventory detail, the extra 0.9% Medicare tax, state rules. Ask a tax pro.',
          'Estimate, not tax advice. The tracker organises your numbers and estimates your tax. It does not file anything: your tax pro or the IRS '
          'calculation is final.']:
    b.text('•  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Questions and help')
b.text('Email ' + EMAIL + ' and Joel will help.', 9.8)
b.text('Want help planning your cash flow as a self-employed person? Book a free Cash Flow Session: ' + BOOK, 9.8)
b.c.linkURL(BOOK, (b.M, b.y - 4, b.W - b.M, b.y + 30), relative=0)
b.text('General information, not financial or tax advice. For personal use only. Please do not share or resell the files.', 8.8, color=MUTED)
b.footer(); b.c.save()
print('saved README.pdf')
