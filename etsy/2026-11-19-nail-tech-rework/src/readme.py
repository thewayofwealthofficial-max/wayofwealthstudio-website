import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
import pdfbook
from pdfbook import Book, A4, EMAIL, BOOK, MUTED
pdfbook.NAME = 'Nail Tech Income & Expense Tracker'
b = Book(os.path.join(HERE, '..', 'out', 'README.pdf'), A4)
b.new_page(title='README: start here')
b.text('Thank you for buying the Nail Tech Income & Expense Tracker from Way of Wealth Studio. It shows what you really earn from your '
       'nail business after supplies, chair or booth rent and fees, in any currency, in Excel or Google Sheets.', 10.5)
b.h2("What's in your download")
for t in ['Nail Tech Income Expense Tracker - BLANK (start here).xlsx: the one you fill in with your own numbers.',
          'Nail Tech Income Expense Tracker - EXAMPLE (filled in).xlsx: a full year for a made-up chair-renting nail tech, Mia, '
          'so you can see every tab and chart working. Look, do not type.',
          'This README. Both spreadsheets are plain .xlsx files: nothing opens in Canva and nothing needs a password.']:
    b.text('•  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('The 11 tabs')
for t in ['Dashboard: profit so far, takings, costs, tips (card and cash), average per client, tax set aside, supplies to reorder, '
          'best earner per hour, goal progress, 5 charts and your next steps.',
          'Start Here and Settings: currency, the month your year starts, tax %, profit goal, hours and the hourly pay you want.',
          'Client Log, Expenses, Supplies & Stock (reorder levels), Rent & Bills (chair or booth rent turned into one monthly figure, plus a renting vs commission check).',
          'Monthly Summary, Pricing Check (true cost and profit per hour for every service, and the price that would pay you properly), '
          'Tax Set-Aside, and the Monthly Money Check-in (your month in plain words plus five reflection questions).']:
    b.text('•  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Set up in 5 steps')
for i, t in enumerate(['Open the BLANK file and read Start Here (the second tab).',
                       'Settings: your currency symbol, year start, tax set-aside %, monthly profit goal, hours and target pay per hour. Then a monthly plan per expense category.',
                       'Pricing Check: edit the service menu to your own prices, product cost and minutes. Rent & Bills: your chair or booth rent and fixed bills.',
                       'Each day, add appointments on the Client Log (pick the service from the dropdown, type price, tip and how they paid). Add costs on Expenses.',
                       'Each month: look at the Dashboard, move your tax money (Tax Set-Aside) and do the Monthly Money Check-in.'], 1):
    b.text(f'{i}.  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Open it in Google Sheets (free)')
for t in ['Go to drive.google.com, click New > File upload, and upload the BLANK .xlsx file.',
          'Open it, then choose File > Save as Google Sheets. Work in the Google Sheets copy.',
          'Move between tabs with the tab bar along the bottom of the screen. Progress bars become real bars in Google Sheets.']:
    b.text('•  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Open it in Excel')
b.text('Double-click the BLANK file. Works in Excel 2016 and later (Windows and Mac), Excel online and the Excel phone app. '
       'Pale yellow boxes are for typing; white boxes work themselves out and are locked so nothing breaks '
       '(Review > Unprotect Sheet, no password, if you want to change them).', 9.8)
b.h2('Good to know')
for t in ['Any country and any currency: type your symbol in Settings. The tax set-aside is a simple % you choose. It is not tax advice: '
          'rules differ by country, so check your local rules or ask an accountant.']:
    b.text('•  ' + t, 9.8, gap=3)
b.new_page(title='Questions and help')
b.text('Room to grow: the Client Log holds 800 appointments and Expenses 300 costs. For a new year, save a fresh copy of the BLANK file and change the start month in Settings.', 9.8)
b.text('Email ' + EMAIL + ' and Joel will help, usually within a day.', 9.8)
b.text('Want help planning your cash flow as a self-employed nail tech? Book a free Cash Flow Session: ' + BOOK, 9.8)
b.c.linkURL(BOOK, (b.M, b.y - 4, b.W - b.M, b.y + 30), relative=0)
b.text('General information, not financial or tax advice. For personal use only. Please do not share or resell the files.', 8.8, color=MUTED)
b.footer(); b.c.save()
print('saved README.pdf')
