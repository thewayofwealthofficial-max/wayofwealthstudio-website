"""README.pdf for the Couples Money Year in Review and 2027 Goals. python3 readme.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_pdf import Book, A4, EMAIL, BOOK, MUTED
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out', 'README.pdf')
b = Book(OUT, A4)
b.new_page(title='README: start here')
b.text('Thank you for buying the Couples Money Year in Review and 2027 Goals from Way of Wealth Studio. Look back at your whole money year '
       'together (January to December), then plan 2027 with 3 to 5 shared goals and a 30-minute check-in each month.', 10.5)
b.h2("What's in your download")
for t in ['Couples Money Year in Review 2027 - BLANK (start here).xlsx: the one you fill in with your own numbers.',
          'Couples Money Year in Review 2027 - EXAMPLE (filled in).xlsx: a made-up couple, Sam and Alex, so you can see every tab, chart '
          'and the monthly summary working. Look, do not type.',
          'Couples Money Year in Review and 2027 Goals - printable A4.pdf and printable US Letter.pdf: the same steps on paper, one page per step, '
          'plus a Monthly Money Check-in page. Every box can be typed into on screen, or print and write by hand.',
          'This README.']:
    b.text('•  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Set up in 5 steps')
for i, t in enumerate(['Open the BLANK file. Go to Settings: your two names, your currency symbol (one setting for every amount) and the year you are looking back on.',
                       'Look back on the whole year: Year in Numbers (all 12 months), Spending Review (was it worth it?) and Net Worth (start vs end).',
                       'Year in Review: 8 questions. Answer apart first, then fill in "Together".',
                       '2027 Goals: 3 to 5 shared goals with a target and a finish month. The sheet works out the monthly amount and checks the goals fit.',
                       'Once a month: type the month on 2027 Check-ins, then open the Monthly Money Check-in. It writes your month in plain words '
                       'and gives you 5 questions to talk through. Use the Money Date tab as your 30-minute agenda.'], 1):
    b.text(f'{i}.  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Open it in Google Sheets (free)')
for t in ['Go to drive.google.com, click New > File upload, and upload the BLANK .xlsx file.',
          'Open it, then choose File > Save as Google Sheets. Work in the Google Sheets copy and share it with your partner (Share, top right).',
          'Move between tabs with the tab bar along the bottom of the screen. Progress bars show as small bar charts in Google Sheets.']:
    b.text('•  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Open it in Excel')
b.text('Double-click the BLANK file. Works in Excel 2016 and later (Windows and Mac), Excel online and the Excel phone app, and it works offline: '
       'no web app, no account, no internet needed. Pale yellow boxes are for typing; white boxes work themselves out and are locked so '
       'the formulas cannot break (Review > Unprotect Sheet, no password).', 9.8)
b.h2('Good to know')
for t in ['Any currency: change the symbol on Settings and every amount and sentence follows.',
          'Every formula was tested: the example and blank files both recalculate with 0 errors.',
          'The Monthly Money Check-in works fully on its own. If you like, you can paste your summary into an AI assistant for a second opinion; it is optional.',
          'General information, not financial advice.']:
    b.text('•  ' + t, 9.8, gap=3)
b.new_page(title='Questions and help')
b.text('Email ' + EMAIL + ' and Joel will help.', 9.8)
b.text('Want help with your own numbers as a couple? Book a free Cash Flow Session: ' + BOOK, 9.8)
b.c.linkURL(BOOK, (b.M, b.y - 4, b.W - b.M, b.y + 30), relative=0)
b.text('For personal use only. Please do not share or resell the files.', 8.8, color=MUTED)
b.footer(); b.c.save()
print('saved README.pdf')
