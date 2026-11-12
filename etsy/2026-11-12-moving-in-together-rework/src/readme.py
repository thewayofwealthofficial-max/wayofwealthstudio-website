import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
import pdfbook
from pdfbook import Book, A4, EMAIL, BOOK, MUTED
pdfbook.NAME = 'Moving In Together Money Planner'
b = Book(os.path.join(HERE, 'out', 'README.pdf'), A4)
b.new_page(title='README: start here')
b.text('Thank you for buying the Moving In Together Money Planner from Way of Wealth Studio.', 10.5)
b.h2("What's in your download")
for t in ['Moving In Together Money Planner - blank.xlsx (start here, for your own numbers)',
          'Moving In Together Money Planner - example.xlsx (filled in for an example couple, Sam and Alex, so you can see it working)',
          'This README']:
    b.text('•  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Open it in Google Sheets (free)')
for t in ['Go to drive.google.com, click New > File upload, and upload the blank .xlsx file.',
          'Open it, then choose File > Save as Google Sheets. Work in the Google Sheets copy.',
          'Share it with your partner (Share button, top right) so you can both fill it in.',
          'Move between tabs with the tab bar along the bottom of the screen.']:
    b.text('•  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Open it in Excel')
b.text('Double-click the blank .xlsx file. Works in Excel for Windows, Mac, Excel online and the Excel phone app.', 9.8)
b.h2('How it works (9 tabs)')
for t in ['Start Here: the steps in order, and where to type.',
          'Settings: your names, take-home pay, currency symbol, move-in date and how you split shared costs (by income, 50-50 or a custom %).',
          'Move-In Costs: everything the move will cost, who pays it (shared or one of you) and what is paid already.',
          'Shared Bills: every bill you will share. Weekly, quarterly and yearly bills are turned into a monthly amount and split.',
          'Year View: your first 12 months, month by month, with the bigger months where quarterly or yearly bills land.',
          'Settle Up: log shared spending as it happens. One line tells you who owes whom.',
          'Move-In Savings: what you each put aside until the move is covered, and how much a month is still needed.',
          'Money Talk: 12 questions to agree before you share a home.',
          'Dashboard: 9 headline numbers, 5 charts and your next step, all worked out for you.',
          'Pale yellow boxes are for typing. White boxes work themselves out. In Excel they are locked so the sums stay safe '
          '(Review > Unprotect Sheet, no password, if you want to change them). Any currency: amounts are plain numbers.']:
    b.text('•  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Questions?')
b.text('Email ' + EMAIL + ' and Joel will help.', 9.8)
b.text('Want help with your money as a couple? Book a free Cash Flow Session: ' + BOOK, 9.8)
b.c.linkURL(BOOK, (b.M, b.y - 4, b.W - b.M, b.y + 30), relative=0)
b.text('General information, not financial or tax advice. For personal use only. Please do not share or resell the files.', 8.8, color=MUTED)
b.footer(); b.c.save()
