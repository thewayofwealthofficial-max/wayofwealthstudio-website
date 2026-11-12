import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
import pdfbook
from pdfbook import Book, A4, EMAIL, BOOK, MUTED
pdfbook.NAME = 'Self-Employed Couples Budget'
b = Book(os.path.join(HERE, 'out', 'README.pdf'), A4)
b.new_page(title='README: start here')
b.text('Thank you for buying the Self-Employed Couples Budget from Way of Wealth Studio.', 10.5)
b.h2("What's in your download")
for t in ['Self-Employed Couples Budget - blank.xlsx (start here, for your own numbers)',
          'Self-Employed Couples Budget - example.xlsx (filled in for an example couple, Jordan and Riley, so you can see it working)',
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
for t in ['Settings: your names, currency, tax pot %, first month of your year, how you split shared costs, your buffer goal and the steady amount the self-employed partner pays themself (leave it blank to use the average).',
          'Income Log, once a month: money in and business costs for the self-employed partner, take-home pay for the employed partner. The tax pot share is worked out.',
          'Tax Pot: type in your own tax due dates (US quarterly estimated tax, UK 31 January and 31 July, or your country). It shows the pot balance and whether it covers the next bill.',
          'Buffer: good months add to it, low months draw on it, so pay stays steady.',
          'Shared Bills: everything you share, turned into a monthly amount and split.',
          'Monthly Split: what each of you pays and keeps, and your safe-to-spend number.',
          'Money Talk: 12 questions for couples where one of you is self-employed.',
          'Dashboard: 9 headline numbers, 5 charts and your next step.',
          'Pale yellow boxes are for typing. White boxes work themselves out (locked in Excel; Review > Unprotect Sheet, no password). Any currency: amounts are plain numbers.',
          'The tax pot is worked out on profit only (a loss month sets nothing aside). Settings apply to every month, so if you change pay-yourself or the split mid-year, earlier months are worked out again with the new values.',
          'This is a planning tool, not tax advice. Check your tax % and dates with an accountant or your tax office.']:
    b.text('•  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Questions?')
b.text('Email ' + EMAIL + ' and Joel will help.', 9.8)
b.text('Want help with your money as a couple? Book a free Cash Flow Session: ' + BOOK, 9.8)
b.c.linkURL(BOOK, (b.M, b.y - 4, b.W - b.M, b.y + 30), relative=0)
b.text('General information, not financial or tax advice. For personal use only. Please do not share or resell the files.', 8.8, color=MUTED)
b.footer(); b.c.save()
