import sys
sys.argv=['x','out']
exec(open('build.py').read().split("if __name__")[0])
from reportlab.lib.pagesizes import A4
b=Book('out/README.pdf',A4,'print')
b.new_page(title='README: start here')
b.text('Thank you for buying the Premarital Money Talks Workbook from Way of Wealth Studio.',10.5)
b.h2("What's in your download")
for t in ['Premarital Money Talks Workbook - A4 - fillable.pdf (type into the boxes)',
          'Premarital Money Talks Workbook - US Letter - fillable.pdf',
          'Premarital Money Talks Workbook - A4 - print.pdf (white pages and light boxes, for writing by hand)',
          'Premarital Money Talks Workbook - US Letter - print.pdf',
          'This README']:
    b.text('•  '+t,9.8,gap=3)
b.y-=6; b.h2('How to type into it')
for t in ['On a computer: open the fillable file in the free Adobe Acrobat Reader, or Preview on a Mac. Click a box and type. Save often.',
          'On an iPhone or iPad: open it in the Files app or the free Adobe Acrobat Reader and tap a box. On Android, use Adobe Acrobat Reader.',
          'In a web browser: Chrome and Edge let you type in the boxes, then use Download or Print > Save as PDF to keep your answers.',
          'Two of you, one file: take turns, or each keep a copy and compare at the "Together" parts.']:
    b.text('•  '+t,9.8,gap=4)
b.y-=4; b.h2('How to print it')
b.text('Use the print files. Choose "Fit to page" or "Actual size". Print only the talks you need, one talk per session.',9.8)
b.h2('Currency and country')
b.text('No currency signs are built in, so use pounds, dollars, euros or any currency. Nothing here is tax or legal advice; '
       'for a prenup or a will, speak to a solicitor or lawyer where you live.',9.8)
b.h2('Questions?')
b.text('Email joel@wayofwealthcoaching.com and I will help.',9.8)
b.text('Want help with your own numbers as a couple? Book a free Cash Flow Session: https://calendly.com/thewayofwealth-official/your-cash-flow-session',9.8)
b.c.linkURL(BOOK,(b.M,b.y-4,b.W-b.M,b.y+30),relative=0)
b.text('For personal use only. Please do not share or resell the files.',8.8,color=MUTED)
b.footer(); b.c.save()
