"""Printable PDF companion: Couples Money Year in Review and 2027 Goals. python3 build_pdf.py out"""
import sys, os
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit

FD = '/usr/share/fonts/truetype/'
for n, f in [('Serif', 'crosextra/Caladea-Regular.ttf'), ('SerifB', 'crosextra/Caladea-Bold.ttf'),
             ('Sans', 'google-fonts/Poppins-Regular.ttf'), ('SansM', 'google-fonts/Poppins-Medium.ttf'),
             ('SansB', 'google-fonts/Poppins-Bold.ttf'), ('SansL', 'google-fonts/Poppins-Light.ttf')]:
    pdfmetrics.registerFont(TTFont(n, FD + f))
CREAM = HexColor('#F5F0E8'); SAGE = HexColor('#B8C5B0'); DSAGE = HexColor('#8FA585')
GOLD = HexColor('#B8956E'); CHAR = HexColor('#3D3D3D'); LINE = HexColor('#BDB4A4'); MUTED = HexColor('#6E6A64')
SOFT = HexColor('#F3EEE5')
EMAIL = 'joel@wayofwealthcoaching.com'
BOOK = 'https://calendly.com/thewayofwealth-official/your-cash-flow-session'
NAME = 'Couples Money Year in Review and Goals'
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']


class Book:
    def __init__(self, path, size):
        self.W, self.H = size
        self.c = canvas.Canvas(path, pagesize=size)
        self.c.setTitle(NAME + ' - Way of Wealth Studio'); self.c.setAuthor('Way of Wealth Studio')
        self.page = 0; self.M = 40

    def new_page(self, tag=None, title=None, sub=None):
        if self.page:
            self.footer(); self.c.showPage()
        self.page += 1
        c = self.c
        self.y = self.H - self.M
        if tag:
            c.setFillColor(DSAGE); c.roundRect(self.M, self.y - 20, 74, 20, 10, fill=1, stroke=0)
            c.setFillColor(white); c.setFont('SansM', 9); c.drawCentredString(self.M + 37, self.y - 14, tag.upper())
            self.y -= 30
        if title:
            c.setFillColor(CHAR); c.setFont('SerifB', 24); c.drawString(self.M, self.y - 22, title); self.y -= 34
            c.setStrokeColor(GOLD); c.setLineWidth(1.4); c.line(self.M, self.y, self.M + 60, self.y); self.y -= 14
        if sub:
            self.text(sub, 10, color=MUTED, gap=8)

    def footer(self):
        c = self.c
        c.setFont('Sans', 7.5); c.setFillColor(MUTED)
        c.drawString(self.M, 22, NAME + '  |  Way of Wealth Studio')
        c.drawRightString(self.W - self.M, 22, str(self.page))

    def text(self, s, size=10, font='Sans', color=CHAR, width=None, x=None, gap=6):
        c = self.c; lead = size * 1.45
        width = width or (self.W - 2 * self.M); x = self.M if x is None else x
        c.setFont(font, size); c.setFillColor(color)
        for ln in simpleSplit(s, font, size, width):
            c.drawString(x, self.y - size, ln); self.y -= lead
        self.y -= gap

    def h2(self, s):
        self.text(s, 13, 'SerifB', gap=4)

    def box(self, x, y, w, h):
        c = self.c
        c.setFillColor(white); c.setStrokeColor(LINE); c.setLineWidth(0.6)
        c.roundRect(x, y, w, h, 3, fill=1, stroke=1)

    def table(self, cols, widths, rows, first=None, rh=22, shade_first=True, total=None):
        c = self.c; x0 = self.M; tw = self.W - 2 * self.M
        ws = [tw * f for f in widths]
        c.setFillColor(DSAGE); c.rect(x0, self.y - 20, tw, 20, fill=1, stroke=0)
        c.setFillColor(white); c.setFont('SansM', 8.3)
        x = x0
        for col, w in zip(cols, ws):
            c.drawString(x + 5, self.y - 13.5, col); x += w
        self.y -= 22
        allrows = list(range(rows)) + (['T'] if total else [])
        for r in allrows:
            x = x0
            for i, w in enumerate(ws):
                if i == 0 and (first or r == 'T'):
                    c.setFillColor(SAGE if r == 'T' else SOFT); c.rect(x + 1, self.y - rh + 2, w - 2, rh - 3, fill=1, stroke=0)
                    c.setFillColor(CHAR); c.setFont('SansM', 8.5)
                    c.drawString(x + 5, self.y - rh / 2 - 3, total if r == 'T' else first[r])
                else:
                    self.box(x + 1, self.y - rh + 2, w - 2, rh - 3)
                x += w
            self.y -= rh
        self.y -= 10

    def two_col(self, q, h=56):
        c = self.c; w = (self.W - 2 * self.M - 14) / 3
        c.setFont('SansM', 9.5); c.setFillColor(CHAR)
        for ln in simpleSplit(q, 'SansM', 9.5, self.W - 2 * self.M):
            c.drawString(self.M, self.y - 9.5, ln); self.y -= 13.5
        self.y -= 2
        c.setFont('Sans', 7.5); c.setFillColor(MUTED)
        for k, lab in enumerate(['PARTNER A', 'PARTNER B', 'TOGETHER']):
            c.drawString(self.M + k * (w + 7), self.y - 8, lab)
        self.y -= 11
        for k in range(3):
            self.box(self.M + k * (w + 7), self.y - h, w, h)
        self.y -= h + 12

    def note(self, title, body):
        c = self.c; w = self.W - 2 * self.M
        lines = simpleSplit(body, 'Sans', 8.8, w - 28); h = 26 + len(lines) * 12.5
        c.setFillColor(SAGE); c.roundRect(self.M, self.y - h, w, h, 8, fill=1, stroke=0)
        c.setFillColor(CHAR); c.setFont('SansB', 8.5); c.drawString(self.M + 14, self.y - 16, title.upper())
        c.setFont('Sans', 8.8); yy = self.y - 30
        for ln in lines:
            c.drawString(self.M + 14, yy, ln); yy -= 12.5
        self.y -= h + 12

    def labeled(self, label, h=24, w=None, x=None):
        x = self.M if x is None else x; w = w or (self.W - 2 * self.M)
        self.c.setFont('SansM', 8.5); self.c.setFillColor(CHAR); self.c.drawString(x, self.y - 9, label)
        self.box(x, self.y - 12 - h, w, h)

    # ----------------------------------------------------------- pages
    def cover(self):
        c = self.c; self.page += 1
        c.setStrokeColor(SAGE); c.setLineWidth(2); c.line(self.M, self.H * 0.42, self.W - self.M, self.H * 0.42)
        cx, cy = self.W / 2, self.H * 0.80
        # two overlapping calendar pages: our own simple motif
        for dx, col in ((-26, SAGE), (26, GOLD)):
            c.setFillColor(col); c.roundRect(cx + dx - 34, cy - 40, 68, 80, 8, fill=1, stroke=0)
            c.setFillColor(white); c.roundRect(cx + dx - 26, cy - 32, 52, 50, 4, fill=1, stroke=0)
        c.setFillColor(CHAR); c.setFont('SansM', 11); c.drawCentredString(cx, self.H * 0.68, 'OUR MONEY')
        c.setFont('SerifB', 42); c.drawCentredString(cx, self.H * 0.62, 'Year in Review')
        c.setFont('SerifB', 28); c.drawCentredString(cx, self.H * 0.565, '+ Next Year\'s Goals')
        c.setFont('Sans', 11.5); c.drawCentredString(cx, self.H * 0.50, 'Look back at the year\'s money together, then plan the next one')
        c.setFont('SansL', 10)
        c.drawCentredString(cx, self.H * 0.465, 'Numbers  ·  Spending  ·  Net worth  ·  Looking back  ·  Goals  ·  Monthly check-ins')
        w = 220
        for i, lab in enumerate(['OUR NAMES', 'THE YEAR WE ARE LOOKING BACK ON']):
            yy = self.H * 0.34 - i * 64
            c.setFont('SansM', 9); c.setFillColor(MUTED); c.drawCentredString(cx, yy, lab)
            self.box(cx - w / 2, yy - 34, w, 26)
        c.setFillColor(CHAR); c.setFont('Sans', 9)
        c.drawCentredString(cx, 64, 'Printable companion to the spreadsheet  ·  write by hand  ·  any currency')
        c.setFont('SansM', 9); c.drawCentredString(cx, 48, 'Way of Wealth Studio  ·  founded by Joel, MSc Behavioural Economics')

    def start(self):
        self.new_page(title='Start here', sub='About 90 minutes for the whole review: one long evening or two short ones. '
                      'Then 30 minutes once a month.')
        steps = [('1', 'Our year in numbers', 'Rough monthly numbers from your bank apps. No need to be exact.'),
                 ('2', 'Where the money went', 'The year total per category, then: was it worth it? What changes?'),
                 ('3', 'Net worth', 'What you owned and owed at the start and end of the year.'),
                 ('4', 'Looking back together', 'Eight questions. Answer on your own first, then together.'),
                 ('5', 'Next year\'s goals', '3 to 5 shared goals, each with a number, a month and a monthly amount.'),
                 ('6', 'Monthly check-ins', 'A one-page money date each month, plus a tracker for the whole year.')]
        for n, t, b in steps:
            c = self.c
            c.setFillColor(GOLD); c.circle(self.M + 11, self.y - 11, 11, fill=1, stroke=0)
            c.setFillColor(white); c.setFont('SansB', 11); c.drawCentredString(self.M + 11, self.y - 15, n)
            self.text(t, 10.5, 'SansB', x=self.M + 32, width=self.W - 2 * self.M - 32, gap=1)
            self.text(b, 9.5, x=self.M + 32, width=self.W - 2 * self.M - 32, gap=10)
        self.h2('Three ground rules')
        for t in ['No blame for the past. You are looking at the year, not judging each other.',
                  'Talk about the plan, not the person. "Our grocery number" beats "your shopping".',
                  'Stop when you said you would. Unfinished is fine: pick it up next time.']:
            self.text('•  ' + t, 9.8, gap=4)
        self.y -= 6
        self.note('Prefer to type?', 'Your download also has the spreadsheet (Excel and Google Sheets). It adds up every number for you, '
                  'draws the charts and tracks your goals through the year. This printable is the same journey on paper.')
        self.text('Any currency: there are no currency signs, so use pounds, dollars, euros or anything else.', 9, color=MUTED)

    def numbers(self):
        self.new_page('Step 1', 'Our year in numbers', 'One row per month. Round numbers are fine.')
        self.table(['Month', 'Income (both)', 'Spending', 'Saved or invested', 'Extra debt paid', 'Left over'],
                   [0.18, 0.164, 0.164, 0.164, 0.164, 0.164], 12, MONTHS, rh=26, total='Year total')
        self.note('How to work out "left over"', 'Income minus spending, minus saved, minus extra debt paid. '
                  'A negative month ran on savings or credit. Look for the pattern, not the perfect number.')
        w = (self.W - 2 * self.M - 20) / 3
        for i, lab in enumerate(['Our best month', 'Our toughest month', 'Saved as % of income']):
            self.labeled(lab, 26, w, self.M + i * (w + 10))
        self.y -= 46

    def spending(self):
        self.new_page('Step 2', 'Where the money went', 'Year total per category, then circle your answers together.')
        cats = ['Home (rent or mortgage)', 'Bills and utilities', 'Groceries', 'Transport', 'Eating out and takeaway', 'Shopping',
                'Travel and holidays', 'Kids and pets', 'Gifts and celebrations', 'Health and fitness', '', '']
        x0 = self.M; tw = self.W - 2 * self.M
        ws = [0.27, 0.15, 0.24, 0.34]
        c = self.c
        c.setFillColor(DSAGE); c.rect(x0, self.y - 20, tw, 20, fill=1, stroke=0)
        c.setFillColor(white); c.setFont('SansM', 8.3)
        x = x0
        for col, w in zip(['Category', 'Year total', 'Worth it?', 'Next year'], ws):
            c.drawString(x + 5, self.y - 13.5, col); x += w * tw
        self.y -= 22
        for cat in cats:
            rh = 30; x = x0
            if cat:
                c.setFillColor(SOFT); c.rect(x + 1, self.y - rh + 2, ws[0] * tw - 2, rh - 3, fill=1, stroke=0)
                c.setFillColor(CHAR); c.setFont('SansM', 8.5); c.drawString(x + 5, self.y - rh / 2 - 3, cat)
            else:
                self.box(x + 1, self.y - rh + 2, ws[0] * tw - 2, rh - 3)
            x += ws[0] * tw
            self.box(x + 1, self.y - rh + 2, ws[1] * tw - 2, rh - 3); x += ws[1] * tw
            for opts, w in ((['Yes', 'Partly', 'No'], ws[2]), (['Keep', 'Cut back', 'Spend more'], ws[3])):
                c.setFont('Sans', 8.3); c.setFillColor(CHAR)
                xx = x + 8
                for o in opts:
                    c.setStrokeColor(LINE); c.circle(xx + 4, self.y - rh / 2 + 1, 4, stroke=1, fill=0)
                    c.drawString(xx + 11, self.y - rh / 2 - 2, o); xx += c.stringWidth(o, 'Sans', 8.3) + 24
                x += w * tw
            self.y -= rh
        self.y -= 8
        w = (self.W - 2 * self.M - 10) / 2
        self.labeled('Total of the "worth it: Yes" rows', 26, w, self.M)
        self.labeled('Total we plan to cut back each month', 26, w, self.M + w + 10)
        self.y -= 48
        self.note('Why "worth it?" comes first', 'People judge spending more kindly when they look at what it bought, not only the total. '
                  'Agree on what to protect before you decide what to cut, and the cutting talk gets much calmer.')

    def networth(self):
        self.new_page('Step 3', 'Net worth: start vs end', 'What you own minus what you owe, on the first and last day of the year.')
        self.h2('What we own')
        self.table(['', 'Start of year', 'End of year', 'Change'], [0.34, 0.22, 0.22, 0.22], 6,
                   ['Joint savings', 'Partner A savings', 'Partner B savings', 'Pensions and retirement', 'Home value (if you own)', 'Other'],
                   total='Total we own')
        self.h2('What we owe')
        self.table(['', 'Start of year', 'End of year', 'Change'], [0.34, 0.22, 0.22, 0.22], 5,
                   ['Credit cards', 'Car finance', 'Student loans', 'Mortgage', 'Other loans'], total='Total we owe')
        self.h2('Our net worth (own minus owe)')
        self.table(['', 'Start of year', 'End of year', 'Change'], [0.34, 0.22, 0.22, 0.22], 1, ['Net worth'], rh=26)
        self.note('A scoreboard, not a judgement', 'A rising line matters more than the size of the number. Update this once every 3 months and watch it move.')

    def review(self):
        Q = ['Our biggest money win this year', 'Money we spent that was worth every penny', 'Money we spent that we would skip next time',
             'A money moment that stressed us out', 'What I learned about how you handle money', 'One habit to keep',
             'One habit to drop', 'If next year goes well, what is different by December?']
        self.new_page('Step 4', 'Looking back together', 'Answer on your own first. Then read each other\'s answers and fill in "Together".')
        for q in Q[:4]:
            self.two_col(q, 92)
        self.new_page('Step 4', 'Looking back together')
        for q in Q[4:]:
            self.two_col(q, 92)
        w = (self.W - 2 * self.M - 10) / 2
        self.labeled('Our word for this money year', 24, w, self.M)
        self.labeled('Our word for next year', 24, w, self.M + w + 10)
        self.y -= 44

    def goals(self):
        self.new_page('Step 5', 'Next year\'s goals', 'Pick 3 to 5. Each needs a number and a finish month.')
        tw = self.W - 2 * self.M
        for g in range(5):
            c = self.c
            c.setFillColor(GOLD); c.circle(self.M + 9, self.y - 9, 9, fill=1, stroke=0)
            c.setFillColor(white); c.setFont('SansB', 9); c.drawCentredString(self.M + 9, self.y - 12.5, str(g + 1))
            cols = [('Goal', 0.34), ('Target', 0.12), ('Have now', 0.12), ('Months left', 0.13), ('Per month', 0.13), ('Who', 0.16)]
            x = self.M + 26; avail = tw - 26
            for lab, f in cols:
                w = avail * f - 6
                c.setFont('SansM', 7.5); c.setFillColor(MUTED); c.drawString(x, self.y - 6, lab.upper())
                self.box(x, self.y - 34, w, 24); x += avail * f
            self.y -= 40
            c.setFont('SansM', 7.5); c.setFillColor(MUTED); c.drawString(self.M + 26, self.y - 6, 'WHY IT MATTERS TO US')
            self.box(self.M + 26, self.y - 32, avail - 6, 22)
            self.y -= 44
        self.note('Per month = (target minus have now) divided by months left',
                  'Then the reality check: add up the "per month" column and compare it with what you saved, paid off and had left over in an '
                  'average month this year. If the goals need more, push a finish month back or lower a target. A goal that fits gets done.')

    def tracker(self):
        self.new_page('Step 6', 'Goal tracker for the year', 'At each money date, write what went to each goal that month.')
        self.table(['Month', 'Goal 1', 'Goal 2', 'Goal 3', 'Goal 4', 'Goal 5', 'Date done'],
                   [0.16, 0.14, 0.14, 0.14, 0.14, 0.14, 0.14], 12, MONTHS, rh=27, total='Total added')
        self.text('Tip: write each goal\'s name above its column the first time you fill this in.', 9, color=MUTED)

    def money_date(self):
        self.new_page('Monthly', 'Our 30-minute money date', 'Print one for each month. Same day each month, phones down.')
        w = (self.W - 2 * self.M - 10) / 2
        self.labeled('Month', 22, w, self.M); self.labeled('Date of our money date', 22, w, self.M + w + 10)
        self.y -= 44
        steps = [('5 min', 'One win each', 'Something that went well with money this month. Small counts.', 40),
                 ('10 min', 'Log the month', 'Write what went to each goal on the tracker page. Then note anything surprising here.', 52),
                 ('5 min', 'Check the goals', 'On track or behind? If behind: a small top-up, or move the finish month. No blame.', 52),
                 ('5 min', 'Look ahead', 'Big costs next month: birthdays, renewals, trips, school things?', 52),
                 ('5 min', 'One nice thing', 'One small treat or plan for next month that you both look forward to.', 34)]
        for t, s, b, h in steps:
            c = self.c
            c.setFillColor(DSAGE); c.roundRect(self.M, self.y - 18, 52, 18, 9, fill=1, stroke=0)
            c.setFillColor(white); c.setFont('SansM', 8); c.drawCentredString(self.M + 26, self.y - 12.5, t)
            c.setFillColor(CHAR); c.setFont('SansB', 10.5); c.drawString(self.M + 62, self.y - 13, s)
            self.y -= 22
            self.text(b, 9, color=MUTED, gap=2)
            self.box(self.M, self.y - h, self.W - 2 * self.M, h); self.y -= h + 12

    def help(self):
        self.new_page(title='Questions and help')
        self.text('Thank you for buying from Way of Wealth Studio. If anything is unclear, email ' + EMAIL + ' and Joel will help.', 10.5)
        self.text('Want help with your own numbers as a couple? Book a free Cash Flow Session:', 10)
        self.text(BOOK, 9.5, 'SansM', color=DSAGE)
        self.c.linkURL(BOOK, (self.M, self.y - 4, self.W - self.M, self.y + 20), relative=0)
        self.text('General information, not financial or tax advice. For personal use only: please do not share or resell the files.', 8.8, color=MUTED)


