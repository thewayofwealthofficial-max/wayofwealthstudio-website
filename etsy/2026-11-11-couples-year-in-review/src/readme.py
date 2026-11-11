from build_pdf import *
b = Book('out/README.pdf', A4)
b.new_page(title='README: start here')
b.text('Thank you for buying the Couples Money Year in Review and Goals from Way of Wealth Studio.', 10.5)
b.h2("What's in your download")
for t in ['Couples Money Year in Review - spreadsheet - blank.xlsx (start here, for your own numbers)',
          'Couples Money Year in Review - spreadsheet - example.xlsx (filled in for an example couple, to see how it works)',
          'Couples Money Year in Review and Goals - printable A4.pdf and printable US Letter.pdf (the same steps on paper)',
          'This README']:
    b.text('•  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Open it in Google Sheets')
for t in ['Go to drive.google.com and upload the blank .xlsx file.',
          'Open it, then choose File > Save as Google Sheets. Work in the Google Sheets copy.',
          'Share it with your partner (Share button, top right) so you can both fill it in.']:
    b.text('•  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Open it in Excel')
b.text('Double-click the blank .xlsx file. Works in Excel for Windows, Mac and Excel online. The buttons along the top of every tab take you to the other tabs.', 9.8)
b.h2('How it works')
for t in ['Start on the Settings tab: your names, your currency symbol and the year you are looking back on.',
          'Then follow the numbered tabs 1 to 6. Pale yellow boxes are for typing; white boxes work themselves out and are locked so the sums stay safe.',
          'The Dashboard fills in as you go: 8 headline numbers, 5 charts and your goal progress.',
          'Through the year, use the Money Date tab as a 30-minute agenda and log each month on Monthly Check-ins.',
          'Any currency: amounts are plain numbers. Locked cells can be unlocked in Excel (Review > Unprotect Sheet), no password.']:
    b.text('•  ' + t, 9.8, gap=3)
b.y -= 6; b.h2('Questions?')
b.text('Email ' + EMAIL + ' and Joel will help.', 9.8)
b.text('Want help with your own numbers as a couple? Book a free Cash Flow Session: ' + BOOK, 9.8)
b.c.linkURL(BOOK, (b.M, b.y - 4, b.W - b.M, b.y + 30), relative=0)
b.text('General information, not financial or tax advice. For personal use only. Please do not share or resell the files.', 8.8, color=MUTED)
b.footer(); b.c.save()
