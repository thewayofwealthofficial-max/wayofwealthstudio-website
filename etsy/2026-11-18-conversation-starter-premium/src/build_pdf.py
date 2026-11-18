"""Our 4-Week Money Date Plan + Monthly Money Check-in (fillable PDF, A4 + US Letter) - Way of Wealth Studio.
Matches the Couples Money Conversation Starter look: Lora headings, Source Sans 3 body, blush cream and mauve.
python3 build_pdf.py OUTDIR            -> plan A4 + Letter, check-in page A4 + Letter
python3 build_pdf.py OUTDIR --demo J   -> A4 plan with the field values in JSON file J (for the in-use video)
"""
import sys, os, json
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit

FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
for n, f in [('Serif', 'Lora-400'), ('SerifSB', 'Lora-600'), ('SerifI', 'Lora-400i'), ('Sans', 'SS-400'), ('SansSB', 'SS-600'),
             ('SansB', 'SS-700'), ('SansI', 'SS-400i')]:
    pdfmetrics.registerFont(TTFont(n, os.path.join(FD, f + '.ttf')))
BG = HexColor('#FFFCFA'); TINT = HexColor('#F3ECE8'); LINE = HexColor('#E1D4D0'); MAUVE = HexColor('#835E54')
INK = HexColor('#3E3431'); MUTED = HexColor('#7D706B'); GOLD = HexColor('#B8956E'); SOFT = HexColor('#FAF5F2')
EMAIL = 'joel@wayofwealthcoaching.com'
BOOK = 'https://calendly.com/thewayofwealth-official/your-cash-flow-session'
NAME = 'Our 4-Week Money Date Plan'

CARDS = {'1.1': 'The feeling I get when I think about our money situation is ___.',
         '1.2': 'The money moment from my childhood that I think about most is ___.',
         '1.3': 'The thing I wish you understood about how I feel about money is ___.',
         '1.4': 'When we disagree about money, the emotion underneath my reaction is usually ___.',
         '1.5': 'The financial topic I have been avoiding bringing up is ___.',
         '2.1': 'On a scale of 1-10, how comfortable do I feel talking about money with you right now?',
         '2.2': 'The reason I avoid money conversations is not because I do not care. It is because ___.',
         '2.3': 'If you could handle ONE financial thing so I did not have to think about it, what would help most?',
         '2.4': 'The smallest money topic I would feel okay discussing regularly is ___.',
         '2.5': 'Something I have never told you about my money habits is ___.',
         '3.1': 'The financial task I handle alone that I wish was shared is ___.',
         '3.2': 'The money worry I carry that I have never said out loud is ___.',
         '3.3': 'I feel most financially stressed at this specific moment each month: ___.',
         '3.4': 'The way I cope with money stress that my partner probably does not notice is ___.',
         '3.5': 'If I could change one thing about how we handle money together, it would be ___.',
         '4.1': 'The thing I most want our money to give us in the next 5 years is ___.',
         '4.2': 'Something I would love to spend money on guilt-free is ___.',
         '4.3': 'The financial value that matters most to me is: security / freedom / generosity / comfort / growth.',
         '4.4': 'A money goal I have never told you about is ___.',
         '4.5': 'If money was not a source of stress, the first thing I would want us to do together is ___.'}
TRACK = {'1': ('Feelings First', 7), '2': ('Breaking the Silence', 8), '3': ('Hidden Stress', 9), '4': ('Values and Dreams', 10)}

WEEKS = [
    dict(n=1, title='Money stories', why='Before any numbers: where each of your money habits came from.',
         prep='Open the Conversation Starter at the Ground Rules (page 3). Phones face down. Set a 20-minute timer.',
         timer=[(2, 'Ground rules aloud'), (6, 'Card 1.2'), (6, 'Card 1.3'), (4, 'What I heard'), (2, 'Agree + score')],
         cards=['1.2', '1.3', '2.1'],
         steps=['Read the six Ground Rules aloud, one each, taking turns.',
                'Card 1.2: one of you answers for 3 minutes, the other only listens, then says "Thank you for telling me that." Swap.',
                'Card 1.3, the same way. No fixing, no advice.',
                'Each of you writes one thing you heard (below). Read it back: "Did I get that right?"',
                'Agree on one small thing for the week. Then each give card 2.1 a score from 1 to 10.']),
    dict(n=2, title='Where it all goes', why='Look at the real numbers together, with no blame for the past.',
         prep='Bring your banking apps and last month\'s statements. Open the planner at Shared Income and Joint Bills.',
         timer=[(3, 'Card 3.1'), (3, 'Card 3.3'), (9, 'Bills + income in'), (3, 'Our split'), (2, 'Agree + score')],
         cards=['3.1', '3.3', '2.4'],
         steps=['Card 3.1 and card 3.3: a quick answer each. They show who has been carrying the money load.',
                'Type both take-home pays into Shared Income and every shared bill into Joint Bills (or write them below).',
                'Look at your fair split: the planner shows what each of you pays by income, and what 50/50 would cost.',
                'Card 2.4: pick the smallest money topic you will check every month.',
                'Agree how you split joint bills for now. Score card 2.1.']),
    dict(n=3, title='Shared goals', why='Decide what your money is for, then put a number and a date on it.',
         prep='Open the planner at Shared Goals. Something nice to drink. This is the fun one.',
         timer=[(4, 'Card 4.1'), (4, 'Card 4.2'), (3, 'Card 4.4'), (7, 'Pick your goals'), (2, 'Agree + score')],
         cards=['4.1', '4.2', '4.4', '4.5'],
         steps=['Card 4.1: where do you want your money to take you in 5 years?',
                'Card 4.2: each name one guilt-free spend. Keep room for it in the plan.',
                'Card 4.4: say the goal you have never said out loud. Card 4.5 if you have time.',
                'Pick your top 3 shared goals here: how much, by when, how much a month. The planner holds up to 6 (Alex and Jordan use 4).',
                'Agree which goal comes first. Score card 2.1.']),
    dict(n=4, title='Our money system', why='Turn three weeks of talking into a simple system you both agreed to.',
         prep='Open your notes from Weeks 1-3 and the planner Dashboard. Your agreement page is next.',
         timer=[(3, 'Card 3.5'), (3, 'Card 2.3'), (2, 'Card 4.3'), (10, 'Decide the system'), (2, 'Sign + score')],
         cards=['3.5', '2.3', '4.3'],
         steps=['Card 3.5: one change each. Card 2.3: what could one of you take off the other\'s plate?',
                'Card 4.3: your top money value each. Let it guide the choices below.',
                'Decide your accounts, your split, your no-ask spending limit and who pays what (below).',
                'Put your monthly money date in both calendars. Same day each month.',
                'Fill in the Money Agreement page together and sign it. Score card 2.1.']),
]

CHECK_QS = ['Which money moment this month brought us closer, and which one pulled us apart a little?',
            'Was there a spend one of us felt uneasy about but did not mention? What stopped us saying it?',
            'Where did our money go somewhere that really mattered to us both?',
            'Talking about money felt a ___ out of 10 this month. What would make it one point easier next time?',
            'What is one small thing each of us will do before our next money date?']


class Book:
    def __init__(self, path, size, values=None):
        self.W, self.H = size
        self.c = canvas.Canvas(path, pagesize=size)
        self.c.setTitle(NAME + ' - Way of Wealth Studio'); self.c.setAuthor('Way of Wealth Studio')
        self.page = 0; self.M = 44
        self.v = values or {}
        self.letter = size == LETTER

    # ---------------------------------------------------------------- basics
    def start(self, tag=None, title=None, sub=None, footer=True):
        if self.page:
            self.c.showPage()
        self.page += 1
        c = self.c
        c.setFillColor(BG); c.rect(0, 0, self.W, self.H, fill=1, stroke=0)
        self.y = self.H - self.M + 4
        if tag:
            w = c.stringWidth(tag.upper(), 'SansSB', 8) + 20
            c.setFillColor(TINT); c.roundRect(self.M, self.y - 17, w, 17, 8.5, fill=1, stroke=0)
            c.setFillColor(MAUVE); c.setFont('SansSB', 8); c.drawString(self.M + 10, self.y - 11.8, tag.upper())
            self.y -= 26
        if title:
            c.setFillColor(INK); c.setFont('Serif', 26); c.drawString(self.M, self.y - 24, title); self.y -= 34
        if sub:
            self.text(sub, 11, 'SerifI', MUTED, gap=6)
        if footer:
            c.setFont('Sans', 7.5); c.setFillColor(MUTED)
            c.drawString(self.M, 22, NAME + '  ·  Way of Wealth Studio')
            c.drawRightString(self.W - self.M, 22, str(self.page))

    @property
    def CW(self):
        return self.W - 2 * self.M

    def text(self, s, size=10, font='Sans', color=INK, width=None, x=None, gap=4, lead=1.38):
        c = self.c; width = width or self.CW; x = self.M if x is None else x
        c.setFont(font, size); c.setFillColor(color)
        for ln in simpleSplit(s, font, size, width):
            c.drawString(x, self.y - size, ln); self.y -= size * lead
        self.y -= gap

    def field(self, name, x, y, w, h, multiline=False, size=10):
        """fillable box: x,y = bottom-left"""
        c = self.c
        c.setFillColor(white); c.setStrokeColor(LINE); c.setLineWidth(0.8)
        c.roundRect(x, y, w, h, 4, fill=1, stroke=1)
        flags = 'multiline' if multiline else ''
        val = self.v.get(name, '')
        if val:   # demo/preview: draw the typed answer the way a PDF reader shows it (wrapped), keep the field empty
            fs = size; c.setFont('Helvetica', fs); c.setFillColor(HexColor('#24305E'))
            lines = simpleSplit(val, 'Helvetica', fs, w - 8) if multiline else [val]
            ty = y + h - fs - 4 if multiline else y + (h - fs) / 2 + 2
            for ln in lines:
                if ty < y + 2: break
                c.drawString(x + 4, ty, ln); ty -= fs * 1.2
            return
        c.acroForm.textfield(name=name, x=x + 1.5, y=y + 1.5, width=w - 3, height=h - 3, borderWidth=0, fillColor=white,
                             textColor=HexColor('#24305E'), fontName='Helvetica', fontSize=size, fieldFlags=flags, value=val,
                             borderColor=white, forceBorder=False)

    def label(self, s, x, y, size=7.5, color=MUTED, font='SansSB'):
        self.c.setFont(font, size); self.c.setFillColor(color); self.c.drawString(x, y, s.upper())

    def boxed(self, label, name, h, x=None, w=None, multiline=True, size=10):
        x = self.M if x is None else x; w = w or self.CW
        self.label(label, x, self.y - 8)
        self.field(name, x, self.y - 12 - h, w, h, multiline, size)

    def pair(self, label, name, h, size=10):
        w = (self.CW - 12) / 2
        for k, who in enumerate(['A', 'B']):
            x = self.M + k * (w + 12)
            self.label(f'{label} · partner {who}', x, self.y - 8)
            self.field(f'{name}_{who}', x, self.y - 12 - h, w, h, True, size)
        self.y -= h + 22

    def note(self, title, body, fill=TINT, tc=INK):
        c = self.c; w = self.CW
        lines = simpleSplit(body, 'Sans', 9.2, w - 28); h = 24 + len(lines) * 12.6
        c.setFillColor(fill); c.roundRect(self.M, self.y - h, w, h, 10, fill=1, stroke=0)
        c.setFillColor(tc); c.setFont('SansB', 9); c.drawString(self.M + 14, self.y - 15, title)
        c.setFont('Sans', 9.2); yy = self.y - 28
        for ln in lines:
            c.drawString(self.M + 14, yy, ln); yy -= 12.6
        self.y -= h + 10

    def disc(self, x, y, n, r=10, fill=MAUVE):
        c = self.c; c.setFillColor(fill); c.circle(x, y, r, fill=1, stroke=0)
        c.setFillColor(white); c.setFont('SansB', r * 1.05); c.drawCentredString(x, y - r * 0.36, str(n))

    # ---------------------------------------------------------------- pages
    def cover(self):
        self.start(footer=False)
        c = self.c; cx = self.W / 2
        c.setFillColor(TINT); c.rect(0, self.H * 0.40, self.W, self.H * 0.60, fill=1, stroke=0)
        # two overlapping cards motif (our own)
        for dx, ang, col in ((-30, -8, white), (30, 8, white)):
            c.saveState(); c.translate(cx + dx, self.H * 0.80); c.rotate(ang)
            c.setFillColor(col); c.setStrokeColor(LINE); c.roundRect(-44, -58, 88, 116, 8, fill=1, stroke=1)
            c.setFillColor(MAUVE); c.setFont('Serif', 44); c.drawCentredString(0, -10, '\u201d' if dx > 0 else '\u201c')
            c.restoreState()
        c.setFillColor(MAUVE); c.setFont('SansSB', 9.5); c.drawCentredString(cx, self.H * 0.665, 'THE PREMIUM KIT  ·  PART 2')
        c.setFillColor(INK); c.setFont('Serif', 36); c.drawCentredString(cx, self.H * 0.605, 'Our 4-Week')
        c.drawCentredString(cx, self.H * 0.555, 'Money Date Plan')
        c.setFont('SerifI', 13); c.setFillColor(MUTED)
        c.drawCentredString(cx, self.H * 0.505, 'Four 20-minute dates that turn talking about money into a plan')
        c.drawCentredString(cx, self.H * 0.480, 'you both agreed to.')
        c.setFont('Sans', 10); c.setFillColor(INK)
        c.drawCentredString(cx, self.H * 0.34, 'Week 1 Money stories  ·  Week 2 Where it all goes  ·  Week 3 Shared goals  ·  Week 4 Our money system')
        c.drawCentredString(cx, self.H * 0.315, 'plus Our Money Agreement and the Monthly Money Check-in')
        w = 250
        self.label('our names', cx - w / 2, self.H * 0.25)
        self.field('cover_names', cx - w / 2, self.H * 0.25 - 32, w, 26)
        self.label('we start on', cx - w / 2, self.H * 0.25 - 52)
        self.field('cover_start', cx - w / 2, self.H * 0.25 - 84, w, 26)
        c.setFont('SansSB', 8.5); c.setFillColor(MAUVE); c.drawCentredString(cx, 40, 'WAY OF WEALTH STUDIO')
        c.setFont('Sans', 8); c.setFillColor(MUTED)
        c.drawCentredString(cx, 28, 'Created by Joel, MSc Behavioural Economics, qualified financial planner  ·  type in the boxes or print')

    def how(self):
        self.start('Start here', 'How the kit fits together', 'Three parts, one rhythm: talk, then numbers, then one agreement.')
        parts = [('1', 'Conversation Starter (the cards)', 'Your quiz, couple type, Ground Rules and 20 cards in 4 tracks. Each date below tells you which cards to pull. '
                  'Card 2.1 ends every date: a 1-10 score for how comfortable money talk felt.'),
                 ('2', 'This plan (4 dates, one a week)', 'An agenda, the cards, a 20-minute timer plan and an agreement box for each date. Type in the boxes or print it.'),
                 ('3', 'Couples Money Date Planner (Excel + Google Sheets)', 'Where the numbers live: income, joint bills split fairly, spending, goals, a log of every money date, '
                  'and a Monthly Check-in tab that writes your month in plain words.')]
        for n, t, b in parts:
            self.disc(self.M + 11, self.y - 11, n, 11)
            self.text(t, 12, 'SerifSB', INK, x=self.M + 32, width=self.CW - 32, gap=1)
            self.text(b, 9.6, 'Sans', MUTED, x=self.M + 32, width=self.CW - 32, gap=10)
        self.y -= 4
        self.text('The 20-minute rhythm', 14, 'Serif', gap=4)
        self.timer([(2, 'Settle in'), (12, 'Two or three cards'), (4, 'Write it down'), (2, 'Agree + score')], full=True)
        self.text('Every date has the same shape, so it starts to feel normal. When the timer goes, stop, even mid-sentence. '
                  'Finishing on time is what makes you both willing to come back next week.', 9.6, color=MUTED, gap=10)
        self.text('Before Week 1', 14, 'Serif', gap=4)
        for t in ['Each take the Money Personality Quiz on your own (Conversation Starter, page 4), then find your pairing (page 6).',
                  'Open the planner EXAMPLE to see how Alex and Jordan filled theirs in, then use the BLANK file for yours.',
                  'Pick a time: same day each week for 4 weeks, ideally not late at night and not straight after payday.']:
            self.c.setFillColor(GOLD); self.c.circle(self.M + 4, self.y - 6.5, 2.4, fill=1, stroke=0)
            self.text(t, 9.8, x=self.M + 14, width=self.CW - 14, gap=5)
        self.y -= 4
        self.note('If one of you is not ready', 'Do not push. Do Week 1 only, keep it to 10 minutes, and use the Breaking the Silence cards (Track 2). '
                  'An invited conversation builds trust. A forced one builds resistance.')

    def timer(self, segs, full=False):
        c = self.c; x0 = self.M; w = self.CW; h = 26; y = self.y - h
        tot = sum(s for s, _ in segs); x = x0
        cols = [MAUVE, HexColor('#9C7A70'), HexColor('#B59A90'), GOLD, HexColor('#CDB29A')]
        for i, (m, lab) in enumerate(segs):
            sw = w * m / tot
            c.setFillColor(cols[i % len(cols)]); c.rect(x, y, sw - 2, h, fill=1, stroke=0)
            c.setFillColor(white); c.setFont('SansB', 8.4)
            t = f'{m} min'
            c.drawCentredString(x + sw / 2 - 1, y + 15.5, t)
            c.setFont('Sans', 7.6)
            lab_ = lab if c.stringWidth(lab, 'Sans', 7.6) < sw - 6 else lab.split(' ')[0]
            c.drawCentredString(x + sw / 2 - 1, y + 5.5, lab_)
            x += sw
        c.setFillColor(MUTED); c.setFont('Sans', 7.2)
        acc = 0; x = x0
        for m, _ in segs:
            c.drawString(x, y - 9, f'{acc}′'); x += w * m / tot; acc += m
        c.drawRightString(x0 + w, y - 9, '20′')
        self.y -= h + 16

    def week(self, wk):
        n = wk['n']
        self.start(f'Week {n} of 4  ·  money date {n}', wk['title'], wk['why'])
        c = self.c
        self.text('Before you start: ' + wk['prep'], 9.2, 'SansI', MUTED, gap=6)
        self.text('20-minute timer plan', 10.5, 'SansB', gap=3)
        self.timer(wk['timer'])
        # agenda (left) + cards (right)
        top = self.y; colw = self.CW * 0.54; rx = self.M + colw + 14; rw = self.CW - colw - 14
        self.text('Agenda', 10.5, 'SansB', gap=3)
        for i, s in enumerate(wk['steps']):
            self.disc(self.M + 7, self.y - 6.5, i + 1, 7, GOLD)
            self.text(s, 8.9, x=self.M + 19, width=colw - 19, gap=3, lead=1.3)
        ly = self.y
        self.y = top
        c.setFillColor(SOFT); c.setStrokeColor(LINE)
        lines = sum(len(simpleSplit('"' + CARDS[k] + '"', 'SerifI', 8.6, rw - 22)) for k in wk['cards'])
        bh = 26 + len(wk['cards']) * 22 + lines * 11
        c.roundRect(rx, self.y - bh, rw, bh, 8, fill=1, stroke=1)
        c.setFillColor(MAUVE); c.setFont('SansB', 9); c.drawString(rx + 11, self.y - 15, 'CARDS TO PULL')
        yy = self.y - 30
        for k in wk['cards']:
            tr, pg = TRACK[k[0]]
            c.setFillColor(MAUVE); c.roundRect(rx + 11, yy - 4, 24, 14, 7, fill=1, stroke=0)
            c.setFillColor(white); c.setFont('SansB', 8); c.drawCentredString(rx + 23, yy, k)
            c.setFillColor(MUTED); c.setFont('Sans', 7.6); c.drawString(rx + 41, yy, f'{tr} · Conversation Starter p.{pg}')
            yy -= 13
            c.setFillColor(INK); c.setFont('SerifI', 8.6)
            for ln in simpleSplit('"' + CARDS[k] + '"', 'SerifI', 8.6, rw - 22):
                c.drawString(rx + 11, yy, ln); yy -= 11
            yy -= 9
        self.y = min(ly, self.y - bh - 10) - 4
        # fill-in section
        c.setStrokeColor(LINE); c.setLineWidth(0.8); c.line(self.M, self.y, self.W - self.M, self.y); self.y -= 8
        hb = 40 if self.letter else 48
        if n == 1:
            self.pair('What I heard you say', f'w{n}_heard', hb)
            self.pair('My money story in one sentence', f'w{n}_story', 28 if self.letter else 32)
        elif n == 2:
            self.pair('What I heard you say', f'w{n}_heard', hb - 8)
            self.numbers_row(n)
        elif n == 3:
            self.pair('What I heard you say', f'w{n}_heard', hb - 10)
            self.goals_table(n)
        else:
            self.system(n)
        # agreement + scores
        self.boxed('One thing we agree to this week', f'w{n}_agree', 40 if self.letter else 46)
        self.y -= (40 if self.letter else 46) + 20
        sw = 60; x = self.M
        for lab, nm, w in [('Card 2.1 · A (1-10)', f'w{n}_scoreA', sw), ('Card 2.1 · B (1-10)', f'w{n}_scoreB', sw),
                           ('Date of this money date', f'w{n}_date', 130), ('Next date', f'w{n}_next', 130)]:
            self.label(lab, x, self.y - 8)
            self.field(nm, x, self.y - 34, w if w > sw else 80, 22, size=10)
            x += (w if w > sw else 80) + 18
        self.y -= 44
        avail = self.y - 50
        h = max(26, min(64, avail - 26 - 20))
        self.pair('Something I appreciated about you today', f'w{n}_thanks', h)
        self.text('Log it in the planner: Money Dates tab, row "Week %d" (date, cards %s, both 2.1 scores, the agreement).'
                  % (n, ', '.join(wk['cards'])), 8.4, 'SansI', MUTED, gap=0)

    def numbers_row(self, n):
        w = (self.CW - 3 * 10) / 4
        labs = [('A take-home / month', 'incA'), ('B take-home / month', 'incB'), ('Joint bills / month', 'bills'), ('Shared spending / month', 'spend')]
        for i, (lab, k) in enumerate(labs):
            x = self.M + i * (w + 10)
            self.label(lab, x, self.y - 8); self.field(f'w{n}_{k}', x, self.y - 34, w, 22)
        self.y -= 44
        self.text('Fair split = A take-home ÷ (A + B). The planner works it out on the Joint Bills tab, with the monthly transfer for each of you.',
                  8.4, 'SansI', MUTED, gap=2)
        w2 = (self.CW - 10) / 2
        for i, (lab, k) in enumerate([('A pays (%)', 'splitA'), ('B pays (%)', 'splitB')]):
            x = self.M + i * (w2 + 10)
            self.label(lab, x, self.y - 8); self.field(f'w{n}_{k}', x, self.y - 34, w2, 22)
        self.y -= 46

    def goals_table(self, n):
        cols = [('Shared goal', 0.40), ('How much', 0.18), ('By when', 0.2), ('Per month', 0.22)]
        x = self.M
        for lab, f in cols:
            self.label(lab, x, self.y - 8); x += self.CW * f
        self.y -= 12
        for g in range(3):
            x = self.M
            for (lab, f), key in zip(cols, ['name', 'amt', 'when', 'pm']):
                self.field(f'w{n}_g{g + 1}_{key}', x, self.y - 22, self.CW * f - 6, 21)
                x += self.CW * f
            self.y -= 26
        self.y -= 8

    def system(self, n):
        c = self.c
        rows = [('Our accounts', ['Joint', 'Separate', 'Joint + our own']),
                ('Joint bills split', ['By income', '50/50', 'Our own %'])]
        for lab, opts in rows:
            c.setFont('SansB', 9); c.setFillColor(INK); c.drawString(self.M, self.y - 12, lab)
            x = self.M + 120
            for o in opts:
                nm = f'w{n}_{lab[:4].lower()}_{o[:4].lower().replace(" ", "").replace("/", "")}'
                c.acroForm.checkbox(name=nm, x=x, y=self.y - 15, size=12, borderColor=MAUVE, fillColor=white, buttonStyle='check',
                                    checked=bool(self.v.get(nm)), forceBorder=True, textColor=MAUVE, borderWidth=1)
                c.setFont('Sans', 9.4); c.setFillColor(INK); c.drawString(x + 17, self.y - 12.5, o); x += 120
            self.y -= 22
        self.y -= 4
        w = (self.CW - 12) / 2
        for pair in [(('No-ask spending money each, per week', 'noask'), ('Our monthly money date (day + time)', 'mdate')),
                     (('Bills A looks after', 'billsA'), ('Bills B looks after', 'billsB'))]:
            for k, (lab, key) in enumerate(pair):
                x = self.M + k * (w + 12)
                self.label(lab, x, self.y - 8); self.field(f'w{n}_{key}', x, self.y - 36, w, 24)
            self.y -= 46
        self.boxed('If we disagree about a spend, we will...', f'w{n}_disagree', 26)
        self.y -= 46

    def agreement(self):
        self.start('After Week 4', 'Our Money Agreement', 'One page, in your own words. Pin it up. Read it again at each monthly money date.')
        items = [('Why we are doing this (our money values, card 4.3)', 'ag_why', 40), ('How our accounts and bills work', 'ag_accounts', 46),
                 ('Our goals, in order', 'ag_goals', 46), ('Spending we never need to ask about', 'ag_noask', 32),
                 ('How we talk about money when it gets hard', 'ag_hard', 46), ('Our monthly money date', 'ag_date', 26)]
        if self.letter:
            items = [(a, b, h - 4) for a, b, h in items]
        for lab, key, h in items:
            self.boxed(lab, key, h); self.y -= h + 20
        w = (self.CW - 12) / 2
        for k, who in enumerate(['A', 'B']):
            x = self.M + k * (w + 12)
            self.label(f'Signed · partner {who}', x, self.y - 8); self.field(f'ag_sign{who}', x, self.y - 36, w, 24)
        self.y -= 46
        self.label('Date', self.M, self.y - 8); self.field('ag_signdate', self.M, self.y - 36, 160, 24)
        self.y -= 46
        self.text('Change it whenever it stops working. An agreement you update together beats a perfect one you ignore.', 9, 'SansI', MUTED)

    def checkin(self):
        self.start('Every month', 'Monthly Money Check-in', 'Ten minutes at each monthly money date. Print one per month, or type and save a copy.')
        c = self.c
        w = (self.CW - 4 * 8) / 5
        x = self.M
        self.label('Month', x, self.y - 8); self.field('ci_month', x, self.y - 34, w * 2 + 8, 22)
        x += 2 * (w + 8)
        for lab, k in [('Card 2.1 · A', 'ci_scoreA'), ('Card 2.1 · B', 'ci_scoreB'), ('Money date done on', 'ci_date')]:
            self.label(lab, x, self.y - 8); self.field(k, x, self.y - 34, w, 22); x += w + 8
        self.y -= 44
        x = self.M
        for lab, k in [('Income together', 'ci_inc'), ('Joint bills', 'ci_bills'), ('Spent vs plan', 'ci_spend'), ('Into goals', 'ci_goals'),
                       ('Left over', 'ci_left')]:
            self.label(lab, x, self.y - 8); self.field(k, x, self.y - 34, w, 22); x += w + 8
        self.y -= 44
        hs = 58 if self.letter else 74
        self.boxed('Our month in plain words (copy it from the planner\'s Check-in tab, or write 2-3 sentences)', 'ci_summary', hs, size=9.5)
        self.y -= hs + 20
        self.text('Five questions for the two of you', 12, 'Serif', gap=3)
        qh = 42 if self.letter else 56
        qw = self.CW * 0.40; aw = (self.CW - qw - 16) / 2
        self.label('Partner A', self.M + qw + 8, self.y - 8); self.label('Partner B', self.M + qw + 16 + aw, self.y - 8)
        self.y -= 12
        for i, q in enumerate(CHECK_QS):
            c.setFont('Sans', 8.8); c.setFillColor(INK)
            lines = simpleSplit(f'{i + 1}.  {q}', 'Sans', 8.8, qw - 6)
            yy = self.y - (qh - len(lines) * 11) / 2 - 8
            for ln in lines:
                c.drawString(self.M, yy, ln); yy -= 11
            self.field(f'ci_q{i + 1}_A', self.M + qw + 8, self.y - qh, aw, qh, True, 9)
            self.field(f'ci_q{i + 1}_B', self.M + qw + 16 + aw, self.y - qh, aw, qh, True, 9)
            self.y -= qh + 6
        self.y -= 4
        self.text('Want a second opinion? Copy your summary and these questions into any AI assistant you use (ChatGPT, Gemini, Copilot) '
                  'and ask it to reply like a kind, honest money coach. Optional: this page works fully on its own.', 8, 'SansI', MUTED)

    def card_index(self):
        self.start('Card index', 'Which card, which date', 'All 20 cards from your Conversation Starter, and where this plan uses them.')
        c = self.c
        use = {}
        for wk in WEEKS:
            for k in wk['cards']:
                use.setdefault(k, []).append(f'Wk {wk["n"]}')
        use['2.1'] = ['every date']
        for t in '1234':
            tr, pg = TRACK[t]
            c.setFillColor(MAUVE); c.setFont('SansB', 9); c.drawString(self.M, self.y - 10, f'TRACK {t}  ·  {tr.upper()}  ·  PAGE {pg}')
            self.y -= 16
            for k in [f'{t}.{i}' for i in range(1, 6)]:
                c.setFillColor(TINT if int(k[-1]) % 2 else BG); c.rect(self.M, self.y - 16, self.CW, 16, fill=1, stroke=0)
                c.setFillColor(INK); c.setFont('SansB', 8.6); c.drawString(self.M + 6, self.y - 11, k)
                t_ = CARDS[k]
                while c.stringWidth(t_, 'Sans', 8.3) > self.CW - 120: t_ = t_[:-4] + '...'
                c.setFont('Sans', 8.3); c.drawString(self.M + 32, self.y - 11, t_)
                c.setFillColor(MAUVE); c.setFont('SansSB', 8); c.drawRightString(self.W - self.M - 6, self.y - 11, ', '.join(use.get(k, ['free choice'])))
                self.y -= 16
            self.y -= 8
        self.y -= 2
        self.note('After the 4 weeks', 'At each monthly money date pull one card you have not used yet. The planner\'s Conversation Cards tab '
                  'ticks off every card you log on the Money Dates tab, so you can see which conversations are still waiting.')

    def hard(self):
        self.start('Help', 'When it gets hard', None)
        for t, b in [('If a date gets heated', 'Pause. Say "I need 10 minutes, I am coming back." When you return, start with: "The feeling underneath my reaction was ___."'),
                     ('If you find a big gap between you', 'That is useful information, not a crisis. Slow down, go back to Track 1, and consider a couples '
                      'therapist or financial counsellor who can hold space for you both.'),
                     ('If you miss a week', 'Just do the next date. The plan works because you keep coming back, not because you never miss.')]:
            self.text(t, 12, 'SerifSB', gap=2); self.text(b, 9.8, color=MUTED, gap=10)
        self.y -= 6
        self.text('Questions and help', 14, 'Serif', gap=4)
        self.text(f'Thank you for buying from Way of Wealth Studio. If anything is unclear, email {EMAIL} and Joel will help.', 10)
        self.text('Want help with your own numbers as a couple? Book a free Cash Flow Session:', 10)
        self.text(BOOK, 9.5, 'SansSB', MAUVE)
        self.c.linkURL(BOOK, (self.M, self.y + 2, self.W - self.M, self.y + 18), relative=0)
        self.y -= 8
        self.text('General information and conversation tools, not financial, legal or relationship therapy advice. For your personal use: '
                  'please do not share or resell the files.', 8.6, color=MUTED)

    def save(self):
        self.c.showPage(); self.c.save()


def plan(path, size, values=None):
    b = Book(path, size, values)
    b.cover(); b.how()
    for wk in WEEKS:
        b.week(wk)
    b.agreement(); b.checkin(); b.card_index(); b.hard()
    b.save()
    return b.page


def checkin_only(path, size):
    global NAME
    old = NAME; NAME = 'Monthly Money Check-in'
    b = Book(path, size); b.checkin(); b.save(); NAME = old


def cards_sheet(path, size):
    """printable cut-out sheet: the 20 conversation cards, 10 per page, dashed cut lines, ids match the planner"""
    W, H = size; c = canvas.Canvas(path, pagesize=size)
    c.setTitle('Conversation Cards (cut-out) - Way of Wealth Studio'); c.setAuthor('Way of Wealth Studio')
    M = 34; top = 64; bot = 40; cw = (W - 2 * M) / 2; ch = (H - top - bot) / 5
    ids = list(CARDS)
    for pg in range(2):
        c.setFillColor(BG); c.rect(0, 0, W, H, fill=1, stroke=0)
        c.setFillColor(INK); c.setFont('Serif', 15); c.drawString(M, H - 34, 'Conversation Cards')
        c.setFillColor(MUTED); c.setFont('Sans', 8.5)
        c.drawString(M, H - 48, f'Cut along the dashed lines.  Cards {ids[pg * 10]} to {ids[pg * 10 + 9]}  ·  numbers match the planner\'s Money Dates log')
        for k in range(10):
            cid = ids[pg * 10 + k]; tr, pgref = TRACK[cid[0]]
            x = M + (k % 2) * cw; y = H - top - (k // 2 + 1) * ch
            c.setStrokeColor(HexColor('#BFAEA8')); c.setLineWidth(0.7); c.setDash(4, 3); c.rect(x, y, cw, ch, fill=0, stroke=1); c.setDash()
            p = 9; c.setFillColor(white); c.setStrokeColor(LINE); c.roundRect(x + p, y + p, cw - 2 * p, ch - 2 * p, 8, fill=1, stroke=1)
            c.setFillColor(MAUVE); c.roundRect(x + p + 12, y + ch - p - 30, 38, 20, 10, fill=1, stroke=0)
            c.setFillColor(white); c.setFont('SansB', 10.5); c.drawCentredString(x + p + 31, y + ch - p - 23.5, cid)
            c.setFillColor(MAUVE); c.setFont('SansSB', 7.8); c.drawString(x + p + 58, y + ch - p - 23, f'TRACK {cid[0]} · {tr.upper()}')
            c.setFillColor(INK); fs = 12.5
            lines = simpleSplit('"' + CARDS[cid] + '"', 'SerifI', fs, cw - 2 * p - 26)
            while len(lines) > 4: fs -= 0.5; lines = simpleSplit('"' + CARDS[cid] + '"', 'SerifI', fs, cw - 2 * p - 26)
            c.setFont('SerifI', fs); yy = y + ch - p - 52
            for ln in lines:
                c.drawString(x + p + 13, yy, ln); yy -= fs * 1.3
            c.setFillColor(MUTED); c.setFont('Sans', 6.8)
            c.drawString(x + p + 13, y + p + 9, f'From the Conversation Starter, p.{pgref}')
            c.drawRightString(x + cw - p - 12, y + p + 9, 'WAY OF WEALTH STUDIO')
        c.setFillColor(MUTED); c.setFont('Sans', 7.5)
        c.drawString(M, 18, 'Conversation Cards  ·  Couples Money Conversation Kit  ·  Way of Wealth Studio'); c.drawRightString(W - M, 18, f'{pg + 1} of 2')
        c.showPage()
    c.save()


if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    if '--demo' in sys.argv:
        vals = json.load(open(sys.argv[sys.argv.index('--demo') + 1]))
        plan(os.path.join(out, 'demo.pdf'), A4, vals)
        cards_sheet(os.path.join(out, 'cards.pdf'), A4)
    else:
        for tag, size in [('A4', A4), ('US Letter', LETTER)]:
            n = plan(os.path.join(out, f'Our 4-Week Money Date Plan ({tag}).pdf'), size)
            checkin_only(os.path.join(out, f'Monthly Money Check-in ({tag}).pdf'), size)
            cards_sheet(os.path.join(out, f'Conversation Cards - cut-out sheet ({tag}).pdf'), size)
            print(tag, n, 'pages')
