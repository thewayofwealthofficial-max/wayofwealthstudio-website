"""README.pdf for the Couples Money Conversation Kit (premium). python3 readme.py OUT.pdf"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_pdf as bp
from build_pdf import Book, A4, MAUVE, MUTED, INK, GOLD, EMAIL, BOOK

bp.NAME = 'README  ·  Couples Money Conversation Kit'
b = Book(sys.argv[1], A4)
b.start('Read me first', 'Your Couples Money Conversation Kit', 'The complete kit: the conversation cards, four money dates, and a planner for the numbers.')
b.text('What is in your download', 14, 'Serif', gap=4)
files = [('1 Conversation Cards (original)', 'Couples_Money_Conversation_Starter.pdf + its README',
          'The Money Personality Quiz, Couple Type Pairing Guide, Ground Rules, 20 cards in 4 tracks, 30-day calendar. Unchanged from our bestseller (A4).'),
         ('2 Conversation Cards, cut-out sheet', 'Conversation Cards - cut-out sheet (A4).pdf  and  (US Letter).pdf',
          'The same 20 cards on two printable pages with dashed cut lines. Card numbers (1.1 to 4.5) match the planner\'s Money Dates log.'),
         ('3 Four-Week Money Date Plan', 'Our 4-Week Money Date Plan (A4).pdf  and  (US Letter).pdf',
          'Four 20-minute dates. Each has an agenda, the cards to pull, a timer plan and fillable boxes. Plus Our Money Agreement and a card index.'),
         ('4 Couples Money Date Planner', 'Couples Money Date Planner - EXAMPLE (filled in).xlsx  and  - BLANK (start here).xlsx',
          '10 tabs for Excel and Google Sheets: Dashboard, Start Here, Settings, Shared Income, Joint Bills (fair split), Spending Plan, '
          'Shared Goals, Money Dates log, Monthly Check-in, Conversation Cards.'),
         ('5 Monthly Money Check-in', 'Monthly Money Check-in (A4).pdf  and  (US Letter).pdf',
          'The one-page check-in on its own, to print every month. The same five questions as the planner\'s Check-in tab.')]
for i, (t, f, d) in enumerate(files):
    b.disc(b.M + 11, b.y - 11, t[0], 11)
    b.text(t[2:], 12, 'SerifSB', x=b.M + 32, width=b.CW - 32, gap=1)
    b.text(f, 8.8, 'SansSB', MAUVE, x=b.M + 32, width=b.CW - 32, gap=1)
    b.text(d, 9.0, 'Sans', MUTED, x=b.M + 32, width=b.CW - 32, gap=4)
b.text('How the parts fit together', 14, 'Serif', gap=4)
for t in ['Day 1: each of you takes the quiz in the Conversation Starter, alone. Find your pairing and read the Ground Rules together.',
          'Weeks 1-4: one money date a week from the 4-Week Plan. It tells you which cards to pull and what to fill in.',
          'Week 2 and Week 3 are where the numbers go into the planner: income, joint bills (split fairly by income), spending and goals.',
          'Every date: log it on the planner\'s Money Dates tab (cards, a 1-10 comfort score, one agreement). The Dashboard updates.',
          'Every month after that: a 30-minute money date with the Monthly Check-in. The planner writes your month in plain words '
          '(income, bills, spending vs plan, biggest overspend, goal progress) and you answer five questions together.']:
    b.c.setFillColor(GOLD); b.c.circle(b.M + 4, b.y - 6.5, 2.4, fill=1, stroke=0)
    b.text(t, 9.3, x=b.M + 14, width=b.CW - 14, gap=3)
b.y -= 4
b.text('Opening the planner', 14, 'Serif', gap=4)
for t in ['Excel (2016 or later, Windows or Mac): open the BLANK file and start on Start Here. Yellow boxes are for typing; formulas are locked so nothing breaks.',
          'Google Sheets (free): go to sheets.google.com > File > Import > Upload, pick the BLANK file, "Replace spreadsheet". Move between tabs with the tab bar at the bottom.',
          'Progress bars appear as solid bars in Google Sheets and as text bars in Excel. Both work. Any currency: type your symbol on Settings.',
          'The PDFs are fillable: type in the boxes in a PDF app (Adobe Reader, Preview, or your browser), or print and write by hand.']:
    b.c.setFillColor(GOLD); b.c.circle(b.M + 4, b.y - 6.5, 2.4, fill=1, stroke=0)
    b.text(t, 9.2, x=b.M + 14, width=b.CW - 14, gap=3)
b.y -= 6
b.note('Questions and help', f'Email {EMAIL} and Joel will help. Want help with your own numbers as a couple? '
       f'Book a free Cash Flow Session: {BOOK}')
b.c.linkURL(BOOK, (b.M, b.y, b.W - b.M, b.y + 40), relative=0)
b.text('Note: the Conversation Starter is included exactly as sold on its own, so its last page and its own README show our older contact '
       f'details. Please use {EMAIL} instead.', 8.4, 'SansI', MUTED)
b.text('General information and conversation tools, not financial, legal or relationship therapy advice. For your personal use: '
       'please do not share or resell the files.', 8.4, color=MUTED)
b.save()
print('saved', sys.argv[1])
