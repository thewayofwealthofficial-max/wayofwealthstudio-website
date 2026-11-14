"""Premarital Money Talks Workbook - Way of Wealth Studio. Builds fillable + sample PDFs in A4 and US Letter."""
import sys
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit

FD = '/usr/share/fonts/truetype/'
pdfmetrics.registerFont(TTFont('Serif', FD + 'crosextra/Caladea-Regular.ttf'))
pdfmetrics.registerFont(TTFont('SerifB', FD + 'crosextra/Caladea-Bold.ttf'))
pdfmetrics.registerFont(TTFont('SerifI', FD + 'crosextra/Caladea-Italic.ttf'))
pdfmetrics.registerFont(TTFont('Sans', FD + 'google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('SansM', FD + 'google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('SansB', FD + 'google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('SansL', FD + 'google-fonts/Poppins-Light.ttf'))

CREAM = HexColor('#F5F0E8'); SAGE = HexColor('#B8C5B0'); DSAGE = HexColor('#8FA585')
GOLD = HexColor('#B8956E'); CHAR = HexColor('#3D3D3D'); INPUT = HexColor('#FFF8E1')
LINE = HexColor('#D9D1C3'); SOFT = HexColor('#EAE3D6'); MUTED = HexColor('#6E6A64')
EMAIL = 'joel@wayofwealthcoaching.com'
BOOK = 'https://calendly.com/thewayofwealth-official/your-cash-flow-session'

# ---------- sample answers (used only for preview images and the video) ----------
SAMPLE = {
 't1_grew_A': 'Money was tight but never talked about. My parents hid bills in a drawer.',
 't1_grew_B': 'Dad ran a small business. Good months, scary months, lots of arguing.',
 't1_rule_A': '"Never borrow, never owe anyone."',
 't1_rule_B': '"Spend it while you have it."',
 't1_fear_A': 'Not having a safety net if one of us loses work.',
 't1_fear_B': 'Being judged for spending my own money.',
 't2_inc_A': '2,450 / month', 't2_inc_B': '2,100 / month',
 't2_sav_A': '6,200', 't2_sav_B': '850',
 'd_type_0': 'Student loan', 'd_who_0': 'B', 'd_owed_0': '18,400', 'd_rate_0': '6.3%', 'd_pay_0': '130',
 'd_type_1': 'Credit card', 'd_who_1': 'B', 'd_owed_1': '1,250', 'd_rate_1': '24.9%', 'd_pay_1': '60',
 'd_type_2': 'Car finance', 'd_who_2': 'A', 'd_owed_2': '4,800', 'd_rate_2': '7.9%', 'd_pay_2': '180',
 't3_incA': '2,450', 't3_incB': '2,100', 't3_tot': '4,550', 't3_pctA': '54%', 't3_pctB': '46%',
 't3_bills': '1,900', 't3_payA': '1,026', 't3_payB': '874', 't3_fun': '150 each',
 'w_total': '12,000', 'w_us': '8,000', 'w_fam': '4,000', 'w_guests': '60', 'w_date': 'June 2027',
 'w_pA1': 'Photographer', 'w_pA2': 'Food', 'w_pA3': 'Music',
 'w_pB1': 'Venue', 'w_pB2': 'Food', 'w_pB3': 'Honeymoon',
 'ag_acc': 'Hybrid: one joint account for bills, our own accounts for the rest',
 'ag_split': 'By income (54 / 46), checked every April',
 'ag_limit': '200', 'ag_save': '500 a month, wedding first then house deposit',
 'ag_debt': 'Clear the credit card by March, then extra on the car',
 'ag_date': 'First Sunday of the month, 45 minutes, coffee out',
 't3_why_A': 'I like seeing everything in one place, but I want some money of my own too.',
 't3_why_B': 'Bills from one pot stops the who-paid-what chats. Own accounts for the fun stuff.',
 't3_admin': 'A sets up the joint account and direct debits. We check it together on money-date Sunday.',
 't3_free': '200 each a month, no questions asked',
 'w_less': 'Flowers, favours and the cake. A smaller guest list.',
 'w_borrow': 'No loans or credit cards for the wedding. If it does not fit, we cut it.',
 'w_family': 'They can suggest. We decide, and we tell them together.',
 'plan_date_1': 'Sun 3 Jan', 'plan_date_2': 'Sun 10 Jan', 'plan_date_3': 'Sun 17 Jan',
 'plan_date_4': 'Sun 24 Jan', 'plan_date_5': 'Sun 31 Jan', 'plan_date_6': 'Sun 7 Feb',
 't1_mem_A': 'Best: my first pay cheque. Worst: a bounced rent payment at 22.',
 't1_mem_B': 'Best: saving for a car at 17. Worst: losing a deposit on a flat.',
 't5_kids_A': 'Yes, two, in about three years.', 't5_kids_B': 'Yes, one or two. Not before we own a home.',
 't5_break_A': 'I would take 9 months. We save a buffer first.', 't5_break_B': 'Happy to go part-time for a year.',
 't5_family_A': 'My mum may need help in 10 years. Up to 100 a month is fine.', 't5_family_B': 'None expected. Gifts at birthdays only.',
 't5_home_A': 'Renting, saving for a deposit near work.', 't5_home_B': 'Buying a small house, outside the city.',
 'md_0_0': 'Jan', 'md_2_0': '250', 'md_3_0': 'Card paid down', 'md_4_0': 'Cook in more',
 'md_0_1': 'Feb', 'md_2_1': '300', 'md_3_1': 'Wedding fund 2k', 'md_4_1': 'Cancel 2 apps',
 'md_0_2': 'Mar', 'md_2_2': '320', 'md_3_2': 'Card cleared', 'md_4_2': 'Raise savings',
}
SAMPLE_CHECKS = {'plan_done_1', 'plan_done_2', 'plan_done_3', 't3_choice_2', 't3_income', 'md_done_0', 'md_done_1', 'md_done_2'}


class Book:
    def __init__(self, path, size, mode):
        self.W, self.H = size
        self.mode = mode
        self.c = canvas.Canvas(path, pagesize=size)
        self.c.setTitle('Premarital Money Talks Workbook - Way of Wealth Studio')
        self.c.setAuthor('Way of Wealth Studio')
        self.page = 0
        self.M = 40  # margin
        self.fields = 0

    # ---------- primitives ----------
    def new_page(self, talk=None, title=None):
        if self.page:
            self.footer()
            self.c.showPage()
        self.page += 1
        c = self.c
        c.setFillColor(white if self.mode == 'print' else CREAM); c.rect(0, 0, self.W, self.H, fill=1, stroke=0)
        self.y = self.H - self.M
        if title:
            if talk:
                c.setFillColor(DSAGE); c.roundRect(self.M, self.y - 20, 74, 20, 10, fill=1, stroke=0)
                c.setFillColor(white); c.setFont('SansM', 9)
                c.drawCentredString(self.M + 37, self.y - 14, talk.upper())
                self.y -= 30
            c.setFillColor(CHAR); c.setFont('SerifB', 24)
            c.drawString(self.M, self.y - 22, title)
            self.y -= 34
            c.setStrokeColor(GOLD); c.setLineWidth(1.4)
            c.line(self.M, self.y, self.M + 60, self.y)
            self.y -= 16

    def footer(self):
        c = self.c
        c.setFont('Sans', 7.5); c.setFillColor(MUTED)
        c.drawString(self.M, 22, 'Premarital Money Talks Workbook  |  Way of Wealth Studio')
        c.drawRightString(self.W - self.M, 22, str(self.page))

    def text(self, s, size=10, font='Sans', color=CHAR, lead=None, width=None, x=None, gap=6):
        c = self.c
        lead = lead or size * 1.45
        width = width or (self.W - 2 * self.M)
        x = self.M if x is None else x
        lines = simpleSplit(s, font, size, width)
        c.setFont(font, size); c.setFillColor(color)
        for ln in lines:
            c.drawString(x, self.y - size, ln)
            self.y -= lead
        self.y -= gap
        return len(lines)

    def h2(self, s, color=CHAR):
        self.text(s, 13, 'SerifB', color, gap=4)

    def field(self, name, x, y, w, h, multiline=False, size=9.5):
        """y = bottom. Fillable box in form mode, sample text in sample mode, empty box in print mode."""
        c = self.c
        c.setFillColor(white if self.mode == 'print' else INPUT); c.setStrokeColor(HexColor('#BDB4A4') if self.mode == 'print' else LINE); c.setLineWidth(0.6)
        c.roundRect(x, y, w, h, 3, fill=1, stroke=1)
        if self.mode == 'form':
            self.fields += 1
            c.acroForm.textfield(name=f'{name}_p{self.page}', x=x + 1, y=y + 1, width=w - 2, height=h - 2,
                                 borderWidth=0, fillColor=INPUT, textColor=HexColor('#2F4A8A'), fontName='Helvetica',
                                 fontSize=0 if multiline else size,
                                 fieldFlags='multiline' if multiline else '', forceBorder=False,
                                 tooltip=name.replace('_', ' '))
        elif self.mode == 'sample' and name in SAMPLE:
            c.setFillColor(HexColor('#2F4A8A')); c.setFont('Sans', size)
            lines = simpleSplit(SAMPLE[name], 'Sans', size, w - 10)
            ty = y + h - size - 4 if multiline else y + (h - size) / 2 + 2
            for ln in lines[: max(1, int((h - 4) // (size * 1.3)))]:
                c.drawString(x + 5, ty, ln); ty -= size * 1.3

    def check(self, name, x, y, label, size=9, tip=None, group=None):
        """group: tick boxes sharing a group are a radio set in the fillable PDF (only one can be ticked)."""
        c = self.c
        c.setFillColor(INPUT); c.setStrokeColor(DSAGE); c.setLineWidth(0.8)
        c.rect(x, y, 10, 10, fill=1, stroke=1)
        if self.mode == 'form':
            self.fields += 1
            if group:
                c.acroForm.radio(name=f'{group}_p{self.page}', value=name, x=x, y=y, size=10, buttonStyle='check',
                                 borderWidth=0, fillColor=INPUT, textColor=HexColor('#2F4A8A'), forceBorder=False,
                                 tooltip=tip or label, selected=False, shape='square')
            else:
                c.acroForm.checkbox(name=f'{name}_p{self.page}', x=x, y=y, size=10, buttonStyle='check',
                                    borderWidth=0, fillColor=INPUT, textColor=HexColor('#2F4A8A'), forceBorder=False,
                                    tooltip=tip or label)
        elif self.mode == 'sample' and name in SAMPLE_CHECKS:
            c.setStrokeColor(HexColor('#2F4A8A')); c.setLineWidth(1.6)
            c.line(x + 2, y + 5, x + 4.3, y + 2.3); c.line(x + 4.3, y + 2.3, x + 8.5, y + 8.2)
        c.setFillColor(CHAR); c.setFont('Sans', size)
        c.drawString(x + 15, y + 1.5, label)

    def labeled(self, label, name, h=34, multiline=True, w=None, x=None, size=9):
        x = self.M if x is None else x
        w = w or (self.W - 2 * self.M)
        self.c.setFont('SansM', size); self.c.setFillColor(CHAR)
        for ln in simpleSplit(label, 'SansM', size, w):
            self.c.drawString(x, self.y - size, ln); self.y -= size * 1.4
        self.y -= 3
        self.field(name, x, self.y - h, w, h, multiline)
        self.y -= h + 10

    def two_col(self, q, key, h=40):
        """Same question, Partner A and Partner B side by side."""
        c = self.c
        w = (self.W - 2 * self.M - 14) / 2
        c.setFont('SansM', 9.5); c.setFillColor(CHAR)
        for ln in simpleSplit(q, 'SansM', 9.5, self.W - 2 * self.M):
            c.drawString(self.M, self.y - 9.5, ln); self.y -= 13.5
        self.y -= 2
        c.setFont('Sans', 7.5); c.setFillColor(MUTED)
        c.drawString(self.M, self.y - 8, 'PARTNER A'); c.drawString(self.M + w + 14, self.y - 8, 'PARTNER B')
        self.y -= 11
        self.field(key + '_A', self.M, self.y - h, w, h, True)
        self.field(key + '_B', self.M + w + 14, self.y - h, w, h, True)
        self.y -= h + 12

    def note(self, title, body, color=SAGE):
        """A 'Why this works' box (behavioural economics angle)."""
        c = self.c
        w = self.W - 2 * self.M
        lines = simpleSplit(body, 'Sans', 8.8, w - 28)
        h = 26 + len(lines) * 12.5
        c.setFillColor(color); c.roundRect(self.M, self.y - h, w, h, 8, fill=1, stroke=0)
        c.setFillColor(CHAR); c.setFont('SansB', 8.5)
        c.drawString(self.M + 14, self.y - 16, title.upper())
        c.setFont('Sans', 8.8)
        yy = self.y - 30
        for ln in lines:
            c.drawString(self.M + 14, yy, ln); yy -= 12.5
        self.y -= h + 12

    def table(self, cols, widths, rows, prefix, rh=22):
        c = self.c
        x0 = self.M
        tw = self.W - 2 * self.M
        ws = [tw * f for f in widths]
        c.setFillColor(DSAGE); c.rect(x0, self.y - 20, tw, 20, fill=1, stroke=0)
        c.setFillColor(white); c.setFont('SansM', 8.5)
        x = x0
        for col, w in zip(cols, ws):
            c.drawString(x + 5, self.y - 13.5, col); x += w
        self.y -= 22
        for r in range(rows):
            x = x0
            for i, w in enumerate(ws):
                if prefix == 'md' and i == 1:
                    self.check(f'md_done_{r}', x + w / 2 - 5, self.y - rh / 2 - 4, '', tip=f'Money date {r + 1} done')
                else:
                    self.field(f'{prefix}_{i}_{r}' if prefix != 'd' else f'd_{["type","who","owed","rate","pay"][i]}_{r}',
                               x + 1, self.y - rh + 2, w - 2, rh - 3)
                x += w
            self.y -= rh
        self.y -= 10

    # ---------- pages ----------
    def cover(self):
        c = self.c
        self.page += 1
        pr = self.mode == 'print'
        c.setFillColor(white if pr else CREAM); c.rect(0, 0, self.W, self.H, fill=1, stroke=0)
        if not pr:
            c.setFillColor(SAGE); c.rect(0, self.H * 0.42, self.W, self.H * 0.58, fill=1, stroke=0)
        else:
            c.setStrokeColor(SAGE); c.setLineWidth(2); c.line(self.M, self.H * 0.42, self.W - self.M, self.H * 0.42)
        # interlocking rings motif (simple geometry, our own)
        cx, cy = self.W / 2, self.H * 0.80
        c.setStrokeColor(GOLD); c.setLineWidth(5)
        c.circle(cx - 24, cy, 42, stroke=1, fill=0); c.circle(cx + 24, cy, 42, stroke=1, fill=0)
        c.setFillColor(CHAR); c.setFont('SansM', 11)
        c.drawCentredString(self.W / 2, self.H * 0.68, 'THE PREMARITAL')
        c.setFont('SerifB', 44)
        c.drawCentredString(self.W / 2, self.H * 0.62, 'Money Talks')
        c.setFont('SerifB', 30)
        c.drawCentredString(self.W / 2, self.H * 0.565, 'Workbook')
        c.setFont('Sans', 11.5)
        c.drawCentredString(self.W / 2, self.H * 0.50, '6 short money conversations to have before you marry')
        c.setFont('SansL', 10)
        c.drawCentredString(self.W / 2, self.H * 0.465, 'Money histories  ·  Debts  ·  Accounts  ·  Wedding  ·  Children  ·  Family')
        # names
        w = 200
        c.setFont('SansM', 9); c.setFillColor(MUTED)
        c.drawCentredString(self.W / 2, self.H * 0.34, 'OUR NAMES')
        self.field('names', self.W / 2 - w / 2, self.H * 0.34 - 34, w, 26)
        c.setFont('SansM', 9); c.setFillColor(MUTED)
        c.drawCentredString(self.W / 2, self.H * 0.34 - 54, 'OUR WEDDING DATE')
        self.field('wedding_date', self.W / 2 - w / 2, self.H * 0.34 - 88, w, 26)
        c.setFillColor(CHAR); c.setFont('Sans', 9)
        c.drawCentredString(self.W / 2, 64, 'Print version  ·  write by hand  ·  any currency' if pr else 'Fillable PDF  ·  type on screen  ·  any currency')
        c.setFont('SansM', 9)
        c.drawCentredString(self.W / 2, 48, 'Way of Wealth Studio  ·  founded by Joel, MSc Behavioural Economics')

    def start_here(self):
        self.new_page(title='Start here')
        self.text('This workbook is all about money. Not love languages, not chores: just the money questions '
                  'couples wish they had asked before the wedding. Six talks, one page per step, '
                  'about 30 to 45 minutes each.', 10.5)
        self.h2('How to use it')
        steps = [
            ('1', 'Pick a time', 'Book your six talks on the plan page. One a week works well. Phones away.'),
            ('2', 'Write or type' if self.mode != 'print' else 'Write it in', ('Write in the boxes by hand. This is the print version; use the fillable file in your download if you want to type. ' if self.mode == 'print' else
             'Type straight into the boxes on a laptop or tablet (Adobe Acrobat Reader, Preview on a Mac, the iPhone or iPad Files app, or Chrome). '
             'Or print the pages you need: there is a print version in your download.')),
            ('3', 'Answer apart, then together', 'Each talk starts with questions you answer on your own (Partner A, Partner B). '
             'Then you read each other\'s answers and fill in the "together" part.'),
            ('4', 'Write your agreement', 'Talk 6 turns everything into a one-page Money Agreement you can both sign, '
             'plus a monthly money date to keep it alive.'),
        ]
        for n, t, b in steps:
            c = self.c
            c.setFillColor(GOLD); c.circle(self.M + 11, self.y - 11, 11, fill=1, stroke=0)
            c.setFillColor(white); c.setFont('SansB', 11); c.drawCentredString(self.M + 11, self.y - 15, n)
            y0 = self.y
            self.text(t, 10.5, 'SansB', x=self.M + 32, width=self.W - 2 * self.M - 32, gap=1)
            self.text(b, 9.5, x=self.M + 32, width=self.W - 2 * self.M - 32, gap=10)
        self.h2('Three ground rules')
        for r in ['Curious, not cross. Ask "what makes you feel that way?" before you answer back.',
                  'Swap who goes first each talk.',
                  'Agree a pause word. Either of you can say it, and you pick the talk up the next day.']:
            self.text('•  ' + r, 9.8, gap=3)
        self.y -= 6
        self.note('Any currency, any country',
                  'There are no currency signs in the boxes, so write amounts in pounds, dollars, euros or anything else. '
                  'Nothing in here is tax or legal advice. For a prenup or a will, talk to a solicitor or lawyer where you live.')

    def plan(self):
        self.new_page(title='Our money talk plan')
        self.text('Put a date next to each talk and check it off when it\'s done. Short and regular beats one long, tiring night.', 10)
        talks = [('1', 'Our money stories', 'How we each grew up with money'),
                 ('2', 'Where we each stand', 'Income, savings, debts and credit'),
                 ('3', 'How we\'ll bank together', 'Joint, separate or hybrid, and a fair split'),
                 ('4', 'The wedding', 'Total, who pays, what matters most'),
                 ('5', 'Children, family and the future', 'Kids, career breaks, family support, home'),
                 ('6', 'Our money agreement', 'Write it down, sign it, book money dates')]
        c = self.c
        for n, t, s in talks:
            h = 50
            c.setFillColor(white); c.setStrokeColor(LINE); c.roundRect(self.M, self.y - h, self.W - 2 * self.M, h, 8, fill=1, stroke=1)
            c.setFillColor(DSAGE); c.setFont('SerifB', 22); c.drawString(self.M + 14, self.y - 33, n)
            c.setFillColor(CHAR); c.setFont('SansB', 10.5); c.drawString(self.M + 44, self.y - 21, 'Talk ' + n + ': ' + t)
            c.setFont('Sans', 8.8); c.setFillColor(MUTED); c.drawString(self.M + 44, self.y - 35, s)
            c.setFont('Sans', 7.5); c.drawString(self.W - self.M - 190, self.y - 14, 'DATE')
            self.field(f'plan_date_{n}', self.W - self.M - 190, self.y - 42, 110, 24)
            self.check(f'plan_done_{n}', self.W - self.M - 66, self.y - 34, 'Done')
            self.y -= h + 9
        self.y -= 4
        self.note('Short on time?', 'Use the 20 quick questions near the back for a road trip or a dinner out, '
                  'then come back to the full talks.')

    def talk1(self):
        self.new_page('Talk 1', 'Our money stories')
        self.text('We all bring a money "rulebook" from childhood. Most money fights are two rulebooks clashing, not two bad people. '
                  'Answer on your own first.', 10)
        self.two_col('How was money handled in the home you grew up in?', 't1_grew', 58)
        self.two_col('A money rule you learned growing up (said out loud or not):', 't1_rule', 42)
        self.two_col('Your best and worst money memory:', 't1_mem', 56)
        self.two_col('Your biggest money fear for the two of you:', 't1_fear', 46)
        self.note('Why this works', 'Psychologists call these money scripts: beliefs we learn early and follow without noticing. '
                  'Naming them makes the other person\'s habits make sense, so "you\'re so tight" becomes "you grew up without a safety net".')

        self.new_page('Talk 1', 'What money means to us')
        self.text('Check the three that matter most to you. Then compare.', 10)
        opts = ['Security', 'Freedom', 'Time with family', 'Giving to others', 'Status and nice things', 'Experiences and travel',
                'Never owing anyone', 'Retiring early', 'Helping our parents', 'Our own home']
        c = self.c
        colw = (self.W - 2 * self.M - 14) / 2
        c.setFont('Sans', 7.5); c.setFillColor(MUTED)
        c.drawString(self.M, self.y - 8, 'PARTNER A'); c.drawString(self.M + colw + 14, self.y - 8, 'PARTNER B')
        self.y -= 20
        for i, o in enumerate(opts):
            row, col = divmod(i, 2)
            for p, xo in (('A', 0), ('B', colw + 14)):
                self.check(f'mean_{p}_{i}', self.M + xo + col * (colw / 2), self.y - row * 19 - 10, o, 8.6)
        self.y -= 5 * 19 + 16
        self.h2('Together')
        self.labeled('Where do we match? Where are we different?', 't1_match', 70)
        self.labeled('One thing I understand better about you after this talk:', 't1_learn', 64)
        self.labeled('One money habit of yours I will try not to judge:', 't1_judge', 60)

    def talk2(self):
        self.new_page('Talk 2', 'Where we each stand')
        self.text('Full honesty, no judging. Finding hidden debt after the wedding is a surprise nobody wants. '
                  'Use monthly figures after tax, in your own currency.', 10)
        c = self.c
        w = (self.W - 2 * self.M - 14) / 2
        for label, key in (('Take-home income each month', 't2_inc'), ('Savings and investments', 't2_sav'),
                           ('Pension or retirement savings', 't2_pen'), ('Regular costs I pay alone (car, phone, gym...)', 't2_cost')):
            c.setFont('SansM', 9.5); c.setFillColor(CHAR); c.drawString(self.M, self.y - 9.5, label); self.y -= 14
            c.setFont('Sans', 7.5); c.setFillColor(MUTED)
            c.drawString(self.M, self.y - 8, 'PARTNER A'); c.drawString(self.M + w + 14, self.y - 8, 'PARTNER B'); self.y -= 11
            self.field(key + '_A', self.M, self.y - 24, w, 24); self.field(key + '_B', self.M + w + 14, self.y - 24, w, 24)
            self.y -= 34
        self.h2('Everything we owe')
        self.text('Loans, credit cards, overdrawn accounts, car finance, buy now pay later, money owed to family.', 9, color=MUTED, gap=4)
        self.table(['Type of debt', 'Whose (A / B)', 'Amount owed', 'Interest rate', 'Monthly payment'],
                   [0.30, 0.15, 0.19, 0.17, 0.19], 9, 'd', 24)

        self.new_page('Talk 2', 'Credit, spending and surprises')
        self.two_col('Do you know your credit score or credit history? Anything the other should know (missed payments, defaults)?', 't2_credit', 54)
        self.two_col('Where does your money go without you noticing?', 't2_leak', 54)
        self.two_col('Any money promises already made (helping a sibling, a loan to a friend, a family business)?', 't2_promise', 54)
        self.h2('Together')
        self.labeled('Our total debt, and the one we will clear first (and why):', 't2_first', 50)
        self.labeled('Do we keep debts from before the wedding separate, or pay them down together?', 't2_debtrule', 50)
        self.check('t2_disclose', self.M, self.y - 10, 'We have both shared everything we owe and own. Nothing left out.', 9.5)
        self.y -= 26
        self.note('Why this works', 'People avoid looking at bad news about money (researchers call it the ostrich effect). '
                  'Writing the numbers down together, once, takes the fear out of them and stops a nasty surprise later.')

    def talk3(self):
        self.new_page('Talk 3', 'How we\'ll bank together')
        self.text('There is no right answer here, only the one that fits you both. Read the three options, then check yours.', 10)
        opts = [('Joint', 'Everything goes into one pot.', 'Simple, feels like a team.', 'Less privacy. Hard if spending styles differ.'),
                ('Separate', 'Each keeps their own money and pays agreed bills.', 'Independence. No fights over spending.', 'Can feel like roommates. Unfair if incomes differ.'),
                ('Hybrid', 'A joint account for shared bills, own accounts for the rest.', 'Teamwork plus freedom.', 'Needs a fair-split rule (next page).')]
        c = self.c
        cw = (self.W - 2 * self.M - 20) / 3
        top = self.y
        for i, (n, d, pro, con) in enumerate(opts):
            x = self.M + i * (cw + 10)
            h = 190
            c.setFillColor(white); c.setStrokeColor(LINE); c.roundRect(x, top - h, cw, h, 8, fill=1, stroke=1)
            c.setFillColor(DSAGE if i != 2 else GOLD); c.roundRect(x, top - 30, cw, 30, 8, fill=1, stroke=0)
            c.rect(x, top - 30, cw, 10, fill=1, stroke=0)
            c.setFillColor(white); c.setFont('SansB', 12); c.drawCentredString(x + cw / 2, top - 20, n)
            self.y = top - 40
            self.text(d, 9, 'SansM', x=x + 8, width=cw - 16, gap=6)
            self.text('Good: ' + pro, 8.6, x=x + 8, width=cw - 16, gap=6)
            self.text('Watch: ' + con, 8.6, x=x + 8, width=cw - 16, gap=4)
            self.check(f't3_choice_{i}', x + 8, top - h + 12, 'This is us', 8.6, group='t3_choice')
        self.y = top - 190 - 18
        self.two_col('Which option feels right to you, and why?', 't3_why', 60)
        self.labeled('Who will manage the bills and paperwork? How do we keep the other one in the loop?', 't3_admin', 56)
        self.labeled('How much can each of us spend without asking? (our "no questions" money each month)', 't3_free', 40)

        self.new_page('Talk 3', 'Our fair split')
        self.text('50/50 sounds fair but can leave the lower earner with nothing left. Splitting by income means you each pay the same share of '
                  'what you earn. Fill in the boxes; the steps show the sums.', 10)
        rows = [('1', 'Partner A take-home income', 't3_incA', ''), ('2', 'Partner B take-home income', 't3_incB', ''),
                ('3', 'Total (1 + 2)', 't3_tot', ''), ('4', 'Partner A share (1 ÷ 3 × 100)', 't3_pctA', '%'),
                ('5', 'Partner B share (2 ÷ 3 × 100)', 't3_pctB', '%'), ('6', 'Shared bills each month', 't3_bills', ''),
                ('7', 'Partner A pays (6 × 4 ÷ 100)', 't3_payA', ''), ('8', 'Partner B pays (6 × 5 ÷ 100)', 't3_payB', '')]
        c = self.c
        for n, lab, key, unit in rows:
            c.setFillColor(SOFT); c.circle(self.M + 10, self.y - 12, 10, fill=1, stroke=0)
            c.setFillColor(CHAR); c.setFont('SansB', 9); c.drawCentredString(self.M + 10, self.y - 15, n)
            c.setFont('Sans', 10); c.drawString(self.M + 28, self.y - 15, lab)
            self.field(key, self.W - self.M - 150, self.y - 23, 150, 22)
            self.y -= 30
        self.y -= 4
        self.check('t3_5050', self.M, self.y - 10, 'We prefer 50/50 instead', 9.5, group='t3_method')
        self.check('t3_income', self.M + 190, self.y - 10, 'We\'ll split by income', 9.5, group='t3_method')
        self.y -= 28
        self.labeled('Fun money each, after bills and savings:', 't3_fun', 26, False)
        self.note('Worked example', 'A earns 2,450 and B earns 2,100, so 4,550 in total. A\'s share is 54%, B\'s is 46%. '
                  'Shared bills of 1,900 mean A pays 1,026 and B pays 874. Each pays about 42% of what they earn.')

    def talk4(self):
        self.new_page('Talk 4', 'The wedding')
        self.text('Weddings often cost more than couples expect. Agree the number before you fall in love with a venue.', 10)
        c = self.c
        w3 = (self.W - 2 * self.M - 20) / 3
        for i, (lab, key) in enumerate((('Our total budget', 'w_total'), ('From our savings', 'w_us'), ('From family', 'w_fam'))):
            x = self.M + i * (w3 + 10)
            c.setFont('SansM', 9); c.setFillColor(CHAR); c.drawString(x, self.y - 9, lab)
            self.field(key, x, self.y - 40, w3, 26)
        self.y -= 52
        for i, (lab, key) in enumerate((('Guest count', 'w_guests'), ('Date or season', 'w_date'))):
            x = self.M + i * (w3 + 10)
            c.setFont('SansM', 9); c.setFillColor(CHAR); c.drawString(x, self.y - 9, lab)
            self.field(key, x, self.y - 40, w3, 26)
        self.y -= 56
        self.h2('Our top 3 (each of us, on our own)')
        w = (self.W - 2 * self.M - 14) / 2
        c.setFont('Sans', 7.5); c.setFillColor(MUTED)
        c.drawString(self.M, self.y - 8, 'PARTNER A'); c.drawString(self.M + w + 14, self.y - 8, 'PARTNER B'); self.y -= 12
        for k in (1, 2, 3):
            c.setFont('SansB', 10); c.setFillColor(GOLD)
            c.drawString(self.M, self.y - 16, str(k)); c.drawString(self.M + w + 14, self.y - 16, str(k))
            self.field(f'w_pA{k}', self.M + 14, self.y - 22, w - 14, 22); self.field(f'w_pB{k}', self.M + w + 28, self.y - 22, w - 14, 22)
            self.y -= 28
        self.y -= 6
        self.labeled('Where are we happy to spend less?', 'w_less', 44)
        self.labeled('Will we borrow for the wedding? Our rule:', 'w_borrow', 40)
        self.labeled('If family pays, what do they get a say in? Who talks to them?', 'w_family', 44)
        self.note('Why this works', 'The first big price you see becomes your "anchor" and makes everything after it look cheap. '
                  'Setting your total and your top 3 before any visits protects you from anchoring.')

    def talk5(self):
        self.new_page('Talk 5', 'Children, family and the future')
        self.text('These talks shape your money for decades. You don\'t need final answers, just to know where each of you stands.', 10)
        self.two_col('Children: do you want them? How many, and roughly when?', 't5_kids', 62)
        self.two_col('If we have children, who (if anyone) takes time off work or works less? How do we cover the drop in pay?', 't5_break', 70)
        self.two_col('Do you expect to support parents or family with money, now or later? How much feels okay?', 't5_family', 70)
        self.two_col('Where do you see us living in 5 years? Renting, buying, which area?', 't5_home', 62)

        self.new_page('Talk 5', 'Our big future')
        self.two_col('What does a good retirement look like to you, and at what age?', 't5_retire', 52)
        self.two_col('If one of us got a big windfall or inheritance, what would we do with it?', 't5_windfall', 52)
        self.two_col('What would you do if one of us lost their job for six months?', 't5_job', 52)
        self.h2('Together')
        self.labeled('Our 3 biggest goals for the next 5 years (with a rough cost):', 't5_goals', 80)
        self.labeled('Our emergency fund target (3 to 6 months of costs is a common rule):', 't5_emerg', 26, False)
        self.labeled('Wills, life insurance, a prenup: anything we want advice on before the wedding?', 't5_legal', 50)

    def talk6(self):
        self.new_page('Talk 6', 'Our money agreement')
        self.text('Bring your answers from Talks 1 to 5 into one page. Short and clear. You can change it any time, together.', 10)
        items = [('How we bank', 'ag_acc', 30), ('How we split shared costs', 'ag_split', 30),
                 ('Spend over this amount and we talk first', 'ag_limit', 24), ('What we save, and for what', 'ag_save', 30),
                 ('Our plan for debt', 'ag_debt', 30), ('Our monthly money date (when, where, how long)', 'ag_date', 30),
                 ('If we disagree about money, we will...', 'ag_disagree', 34)]
        for lab, key, h in items:
            self.labeled(lab, key, h, h > 24)
        c = self.c
        w = (self.W - 2 * self.M - 14) / 2
        self.y -= 2
        for i, lab in enumerate(('Signed (Partner A)', 'Signed (Partner B)')):
            x = self.M + i * (w + 14)
            c.setFont('SansM', 9); c.setFillColor(CHAR); c.drawString(x, self.y - 9, lab)
            self.field(f'ag_sign_{i}', x, self.y - 40, w, 26)
        self.y -= 50
        c.setFont('SansM', 9); c.setFillColor(CHAR); c.drawString(self.M, self.y - 9, 'Date')
        self.field('ag_signdate', self.M, self.y - 40, w, 26)
        self.y -= 50
        self.note('Why this works', 'A plan you wrote down and agreed to is easier to stick to (behavioural economists call this a commitment device). '
                  'The agreement turns good intentions into shared rules.')

        self.new_page('Talk 6', 'Our money dates')
        self.text('Once a month, 30 to 45 minutes. Check the agreement, the bills, the savings and how you both feel. Check each one off.', 10)
        cols = ['Month', 'Done', 'Saved this month', 'One win', 'One thing to change']
        self.table(cols, [0.14, 0.09, 0.2, 0.27, 0.30], 12, 'md', 34)
        self.text('Money date agenda: 1. Wins first.  2. Bills and spending.  3. Savings and debt.  4. Anything coming up.  5. One thing to change.',
                  9, 'SansM', MUTED)

    def extras(self):
        self.new_page(title='When we disagree')
        self.text('Disagreeing is normal. These steps keep it a talk, not a fight.', 10)
        steps = ['Say what you feel and need, not what they did wrong: "I feel anxious when the savings drop" beats "you always overspend".',
                 'Repeat back what you heard before you reply.',
                 'Find the value under the position. Often one of you wants security and the other wants freedom. Both are good.',
                 'Try a test: agree a rule for 3 months, then review it at a money date.',
                 'Use the pause word if it heats up, and come back within 24 hours.',
                 'Still stuck on something big? A couples counselor or a financial planner can help you both feel heard.']
        for i, s in enumerate(steps, 1):
            c = self.c
            c.setFillColor(SAGE); c.circle(self.M + 10, self.y - 10, 10, fill=1, stroke=0)
            c.setFillColor(CHAR); c.setFont('SansB', 9.5); c.drawCentredString(self.M + 10, self.y - 13.5, str(i))
            self.text(s, 9.8, x=self.M + 30, width=self.W - 2 * self.M - 30, gap=10)
        self.labeled('Our own rules for money arguments:', 'dis_rules', 150)

        self.new_page(title='20 quick questions')
        self.text('For a road trip, a walk or a dinner out. Take turns. No writing needed.', 10)
        qs = ['What did your parents argue about when it came to money?', 'What\'s the most you\'ve ever spent on one thing? Any regrets?',
              'Saver or spender? Be honest.', 'How much debt do you have right now?', 'What would you do with 10,000 tomorrow?',
              'Do you check your bank balance? How often?', 'What purchase would you want to talk about first?',
              'How do you feel about lending money to family?', 'Joint account: yes, no or some?', 'Who should pay for the wedding?',
              'What\'s one money goal for this year?', 'Rent or buy? Where?', 'How many children, if any?',
              'Would you work less to look after a child?', 'What does "being comfortable" mean to you?',
              'What is a waste of money to you?', 'What\'s a treat you never want to give up?', 'Retire at what age?',
              'What money habit of mine worries you?', 'What makes you feel safe about our money?']
        c = self.c
        cw = (self.W - 2 * self.M - 16) / 2
        for i, q in enumerate(qs):
            col, row = divmod(i, 10)
            x = self.M + col * (cw + 16)
            yy = self.y - row * 52
            c.setFillColor(white); c.setStrokeColor(LINE); c.roundRect(x, yy - 44, cw, 44, 6, fill=1, stroke=1)
            c.setFillColor(GOLD); c.setFont('SansB', 10); c.drawString(x + 8, yy - 17, str(i + 1))
            ty = yy - 15
            c.setFillColor(CHAR); c.setFont('Sans', 8.8)
            for ln in simpleSplit(q, 'Sans', 8.8, cw - 36)[:3]:
                c.drawString(x + 28, ty, ln); ty -= 11.5

        self.new_page(title='Notes')
        self.field('notes', self.M, 70, self.W - 2 * self.M, self.y - 70, True)

        self.new_page(title='Thank you')
        self.text('Thank you for choosing Way of Wealth Studio. I hope these talks bring you closer and save you a few arguments.', 10.5)
        self.text('Way of Wealth Studio is run by Joel, who holds an MSc in Behavioural Economics and qualified as a '
                  'financial planner. The talks in this workbook follow the money questions couples often skip before marriage.', 10)
        self.h2('Need a hand?')
        self.text('Questions about your download: ' + EMAIL, 10)
        self.text('Want help with your own numbers? Book a free Cash Flow Session: ' + BOOK, 10)
        self.c.linkURL(BOOK, (self.M, self.y - 4, self.W - self.M, self.y + 40), relative=0)
        self.h2('Using this workbook')
        self.text('For your personal use. Please don\'t share or resell the file. This workbook is general information, '
                  'not financial, tax or legal advice.', 9.5, color=MUTED)

    def build(self):
        self.cover(); self.start_here(); self.plan()
        self.talk1(); self.talk2(); self.talk3(); self.talk4(); self.talk5(); self.talk6(); self.extras()
        self.footer(); self.c.save()
        return self.page, self.fields


if __name__ == '__main__':
    out = sys.argv[1]
    for nm, sz in (('A4', A4), ('US-Letter', LETTER)):
        for mode in ('form', 'print', 'sample'):
            b = Book(f'{out}/{nm}-{mode}.pdf', sz, mode)
            print(nm, mode, b.build())
