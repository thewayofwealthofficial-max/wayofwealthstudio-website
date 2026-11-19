"""Nail Tech Income & Expense Tracker (full rework, 19 Nov 2026) - Way of Wealth Studio.
11 tabs, cells-only app skin (Google Sheets safe), any currency, Dashboard first.
python3 build_xlsx.py out/file.xlsx [blank]
"""
import sys, os, datetime as dt, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
import skin
from skin import *
from openpyxl.chart import Reference, BarChart
from openpyxl.chart.series import SeriesLabel
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Font, Alignment, PatternFill

CHAR = '3D3D3D'
skin.NAVY = CHAR
OUT = sys.argv[1]; BLANK = len(sys.argv) > 2 and sys.argv[2] == 'blank'
NUM = '#,##0;-#,##0;"–"'
NUM2 = '#,##0.00;-#,##0.00;"–"'
DATE = 'd mmm yyyy'
MON = 'mmm yyyy'

TABS = [('Dashboard', GOLD), ('Start Here', GOLD), ('Settings', DSAGE), ('Client Log', DSAGE), ('Expenses', DSAGE),
        ('Supplies & Stock', DSAGE), ('Rent & Bills', DSAGE), ('Monthly Summary', CHAR), ('Pricing Check', CHAR),
        ('Tax Set-Aside', CHAR), ('Monthly Money Check-in', GOLD)]
B = Book(TABS, BLANK)
S = B.s
CL, EX, SS, RB, MS, PC, TX, CI = ("'Client Log'", "Expenses", "'Supplies & Stock'", "'Rent & Bills'", "'Monthly Summary'",
                                  "'Pricing Check'", "'Tax Set-Aside'", "'Monthly Money Check-in'")
NAME, BIZ, CUR, START, SETUP, TAXP, GOAL, HOURS, TARGET = [f'Settings!$C${r}' for r in range(7, 16)]
FMT = 'Settings!$H$7'
M = lambda x: f'TEXT({x},{FMT})'
CR1, CR2 = 9, 808      # client log rows
ER1, ER2 = 9, 308      # expense rows
SR1, SR2 = 9, 48       # stock rows
BR1, BR2 = 9, 26       # bills rows
PR1, PR2 = 10, 24      # services rows on Pricing Check
CATS = ['Gel & polish', 'Acrylic & powders', 'Tips & forms', 'Nail art & decoration', 'Files & disposables', 'Hygiene & PPE',
        'Tools & equipment', 'Chair / booth rent', 'Bills & utilities', 'Insurance & licences', 'Booking app & card fees',
        'Marketing & photos', 'Training & courses', 'Travel & mileage', 'Retail stock to sell', 'Other']
NC = len(CATS)
CAT0 = 21              # Settings rows for category list + monthly plan
CATRNG = f'Settings!$B${CAT0}:$B${CAT0 + NC - 1}'
PLANRNG = f'Settings!$C${CAT0}:$C${CAT0 + NC - 1}'
PAY = ['Card', 'Cash', 'Bank transfer', 'Voucher', 'Other']
STOCKTYPES = ['Gel & polish', 'Acrylic & powders', 'Tips & forms', 'Nail art', 'Disposables', 'Hygiene', 'Retail']
SERVICES = [('Gel manicure', 30, 2.10, 45), ('BIAB overlay', 38, 3.20, 60), ('BIAB infill', 35, 2.80, 60),
            ('Acrylic full set', 45, 4.50, 90), ('Acrylic infill', 32, 3.00, 75), ('Gel pedicure', 35, 2.60, 60),
            ('Gel removal and tidy', 12, 0.80, 20), ('Nail art (per set)', 10, 0.90, 20), ('Builder gel extensions', 50, 5.00, 105),
            ('Classic manicure', 22, 1.20, 40), ('Soft gel tips', 48, 4.20, 90)]
SVCRNG = f"{PC}!$B${PR1}:$B${PR2}"


def bar_f(pct, color, n=12):
    return (f'IFERROR(SPARKLINE(MAX(0,MIN(1,{pct})),{{"charttype","bar";"max",1;"color1","#{color}"}}),'
            f'REPT("█",ROUND(MAX(0,MIN(1,{pct}))*{n},0))&REPT("░",{n}-ROUND(MAX(0,MIN(1,{pct}))*{n},0)))')


def mrange(col, sheet, r1, r2, lo, hi, datecol='B'):
    return f'{sheet}!${col}${r1}:${col}${r2},{sheet}!${datecol}${r1}:${datecol}${r2},">="&{lo},{sheet}!${datecol}${r1}:${datecol}${r2},"<="&{hi}'


def coral_rule(ws, rng, first, start='●'):
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'LEFT({first},1)="{start}"'], font=Font(name=FONT, color=CORAL, bold=True)))
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'LEFT({first},1)="✓"'], font=Font(name=FONT, color=DSAGE, bold=True)))


def ex(v, b=None):
    """example value, or blank-file default"""
    return b if BLANK else v


# ================================================================== Settings
ws = S['Settings']
B.page(ws, 'Settings', 'Step 1: fill in the yellow boxes once. Every other tab updates on its own.',
       {2: 40, 3: 24, 4: 3, 5: 64}, ncols=5, nrows=50)
B.th(ws, 6, 2, 'ABOUT YOU'); B.th(ws, 6, 3, 'TYPE OR PICK HERE'); B.th(ws, 6, 5, 'WHAT IT MEANS')
rows = [('Your name', ex('Mia'), None, 'Shown on the Dashboard and in your monthly check-in. Nothing is sent anywhere.'),
        ('Business name', ex('Mia Rose Nails'), None, 'Shown at the top of the Dashboard.'),
        ('Currency symbol (£, $, €, A$, R ...)', '£', None, 'Any currency works. Type your symbol: every total and sentence uses it.'),
        ('Your year starts on', ex(dt.datetime(2025, 11, 1), dt.datetime(2027, 1, 1)), DATE,
         'The first day of your 12 months (any month: January, April, July ...). The Monthly Summary runs 12 months from here.'),
        ('How you work', ex('Chair renter', 'Chair renter'), None, 'Chair or booth renter, home studio, mobile, salon owner or employed + own clients. For your notes.'),
        ('Tax to set aside (% of profit)', 0.25, '0%', 'Rule of thumb for your country (often 20% to 30%). The Tax Set-Aside tab uses it. Not tax advice.'),
        ('Monthly profit goal', ex(1500, 1500), NUM, 'What you want to keep each month after costs. Used on the Dashboard and check-in.'),
        ('Hours you do nails per month', 120, NUM, 'Booked hours with clients. Spreads your rent and bills over each service (Pricing Check).'),
        ('What you want to earn per hour', ex(25, 25), NUM, 'Your target pay per hour after product and overheads. Pricing Check flags services below it.')]
for i, (lab, v, fmt, hlp) in enumerate(rows):
    r = 7 + i
    B.text(ws, r, 2, lab, 10, True); B.inp(ws, r, 3, v, fmt, keep=True); B.text(ws, r, 5, hlp, 9, color=MUTED)
    ws.row_dimensions[r].height = 30 if len(hlp) > 80 else 24
B.dv(ws, 'C11', ['Chair renter', 'Booth renter', 'Home studio', 'Mobile nail tech', 'Salon owner', 'Employed + own clients'])
ws['H7'] = '="""' + '"&IF($C$9="","£",$C$9)&"' + '""#,##0"'
ws['H7'].font = F(8, color='B9B2A6')
ws.column_dimensions['H'].hidden = True
B.section(ws, 18, 2, 'Expense categories and your monthly plan', 4)
B.text(ws, 19, 2, 'Rename a category if you like. The plan is what you expect to spend in a normal month: the check-in compares it with what you spent.', 9, color=MUTED, w=4)
ws.row_dimensions[19].height = 28
B.th(ws, 20, 2, 'CATEGORY'); B.th(ws, 20, 3, 'MONTHLY PLAN', align='right'); B.th(ws, 20, 5, 'EXAMPLES')
PLAN = [110, 45, 15, 15, 20, 15, 20, 347, 25, 8, 30, 10, 15, 10, 15, 10]
EXAMPLES = ['Gels, builder gel, base and top coats, polish', 'Acrylic powder, monomer, dip powder', 'Tips, forms, glue',
            'Foils, chrome, gems, stickers', 'Files, buffers, wipes, cotton, foil wraps', 'Gloves, masks, sanitiser, disinfectant',
            'Lamp, drill, bits, brushes, furniture', 'Weekly or monthly chair or booth rent, or room hire', 'Electricity, phone, internet',
            'Insurance, licence, council or salon fees', 'Booking app, card reader and payment fees', 'Ads, cards, photos, website',
            'Courses, certificates, trade shows', 'Fuel, parking, public transport', 'Cuticle oil, hand cream and anything you sell on',
            'Anything else for the business']
for i, c in enumerate(CATS):
    r = CAT0 + i
    B.inp(ws, r, 2, c, keep=True); B.inp(ws, r, 3, ex(PLAN[i]), NUM, 'right')
    B.text(ws, r, 5, EXAMPLES[i], 9, color=MUTED)
B.fx(ws, CAT0 + NC, 2, 'Total monthly plan', None, True, WHITE, 'left'); B.fx(ws, CAT0 + NC, 3, f'=SUM(C{CAT0}:C{CAT0 + NC - 1})', NUM, True, WHITE)
B.text(ws, 6, 7, 'LISTS', 7, True, 'B9B2A6')
for i, p in enumerate(PAY):
    B.text(ws, 8 + i, 7, p, 8, False, 'A79F92', wrap=False)
for i, p in enumerate(STOCKTYPES):
    B.text(ws, 14 + i, 7, p, 8, False, 'A79F92', wrap=False)
ws.column_dimensions['G'].hidden = True
PAYREF = '=Settings!$G$8:$G$12'
STREF = f'=Settings!$G$14:$G${14 + len(STOCKTYPES) - 1}'
B.protect(ws)

# ================================================================== Pricing Check (services menu lives here)
ws = S['Pricing Check']
B.page(ws, 'Pricing Check', 'What each service really earns you per hour, after product and your share of rent and bills.',
       {2: 24, 3: 10, 4: 11, 5: 9, 6: 11, 7: 11, 8: 11, 9: 11, 10: 9, 11: 8, 12: 15, 13: 12}, ncols=12, nrows=60)
OVH = f"{RB}!$F${BR2 + 1}"
B.box(ws, 7, 2, 7, 13, GOLDT, GOLDT)
B.text(ws, 7, 2, f'="Your rent and bills come to "&{M(OVH)}&" a month. Over "&{HOURS}&" hours that is "&TEXT(IFERROR({OVH}/{HOURS},0),SUBSTITUTE({FMT},"#,##0","#,##0.00"))&" an hour, added to every service below. Target: "&{M(TARGET)}&" an hour."',
       10, True, '6B5B45', w=12, indent=1)
ws.row_dimensions[7].height = 30
hd = ['SERVICE (YOUR MENU)', 'YOUR PRICE', 'PRODUCT COST', 'MINUTES', 'RENT + BILLS SHARE', 'TRUE COST', 'PROFIT EACH',
      'PROFIT PER HOUR', 'MARGIN', 'DONE', 'VERDICT', 'PRICE FOR TARGET']
for j, h in enumerate(hd):
    B.th(ws, 9, 2 + j, h, align='left' if j in (0, 10) else 'right')
ws.row_dimensions[9].height = 30
for c in range(2, 14):
    ws.cell(9, c).alignment = Alignment(horizontal='left' if c in (2, 12) else 'right', vertical='center', wrap_text=True, indent=1 if c in (2, 12) else 0)
for i in range(PR2 - PR1 + 1):
    r = PR1 + i
    s = SERVICES[i] if i < len(SERVICES) else None
    B.inp(ws, r, 2, s[0] if s else None, keep=True)
    B.inp(ws, r, 3, s[1] if s else None, NUM2, 'right')
    B.inp(ws, r, 4, s[2] if s else None, NUM2, 'right')
    B.inp(ws, r, 5, s[3] if s else None, '0', 'right')
    B.fx(ws, r, 6, f'=IF(OR(B{r}="",E{r}=""),"",IFERROR({OVH}/{HOURS}*E{r}/60,0))', NUM2)
    B.fx(ws, r, 7, f'=IF(B{r}="","",N(D{r})+N(F{r}))', NUM2)
    B.fx(ws, r, 8, f'=IF(OR(B{r}="",C{r}=""),"",C{r}-G{r})', NUM2, True)
    B.fx(ws, r, 9, f'=IF(OR(B{r}="",C{r}="",N(E{r})=0),"",H{r}/E{r}*60)', NUM2, True)
    B.fx(ws, r, 10, f'=IF(OR(B{r}="",N(C{r})=0),"",H{r}/C{r})', '0%')
    B.fx(ws, r, 11, f'=IF(B{r}="","",COUNTIFS({CL}!$D${CR1}:$D${CR2},B{r}))', '0')
    B.fx(ws, r, 12, f'=IF(I{r}="","",IF(I{r}<{TARGET}*0.9,"● Raise price",IF(I{r}<{TARGET},"◐ Close","✓ On target")))', None, True, align='left')
    B.fx(ws, r, 13, f'=IF(OR(B{r}="",N(E{r})=0),"",ROUNDUP(G{r}+{TARGET}*E{r}/60,0))', NUM)
    # hidden helpers: takings per service this year, rank key
    ws.cell(r, 15, f'=IF(B{r}="",0,SUMIFS({CL}!$E${CR1}:$E${CR2},{CL}!$D${CR1}:$D${CR2},B{r}))')
    ws.cell(r, 16, f'=O{r}+ROW()/1000000')
    ws.cell(r, 17, f'=IF(I{r}="",99999,I{r})+ROW()/1000000')
    ws.cell(r, 18, f'=IF(I{r}="",-99999,I{r})+ROW()/1000000')
coral_rule(ws, f'L{PR1}:L{PR2}', f'L{PR1}')
ws.conditional_formatting.add(f'L{PR1}:L{PR2}', FormulaRule(formula=[f'LEFT(L{PR1},1)="◐"'], font=Font(name=FONT, color=GOLD, bold=True)))
for c in 'OPQR':
    ws.column_dimensions[c].hidden = True
r0 = PR2 + 2
B.section(ws, r0, 2, 'Worth check: what charging 10% more would look like', 10)
B.box(ws, r0 + 1, 2, r0 + 3, 13, WHITE)
B.text(ws, r0 + 1, 2, f'=IF(SUM(O{PR1}:O{PR2})=0,"Log a few clients and this works out what a 10% price rise would add.","A 10% rise on the services you did this year = "&{M(f"SUM(O{PR1}:O{PR2})*0.1")}&" more, for exactly the same hours. That is about "&{M(f"SUM(O{PR1}:O{PR2})*0.1/MAX(1,COUNT({MS}!$C$9:$C$20)-COUNTIF({MS}!$C$9:$C$20,0))")}&" a month.")',
       11, True, INK, w=12, indent=1)
B.text(ws, r0 + 2, 2, f'=IF(COUNT(I{PR1}:I{PR2})=0,"Type your price, product cost and minutes for each service above (the names are a starter menu: rename them to yours).",IF(COUNTIF(I{PR1}:I{PR2},"<"&{TARGET})=0,"Every service earns your target per hour. Nice work. Review again when your rent or product costs change.",COUNTIF(I{PR1}:I{PR2},"<"&{TARGET})&" service(s) earn less than your target per hour ("&COUNTIF(L{PR1}:L{PR2},"●*")&" by more than 10%). The PRICE FOR TARGET column shows the price that would pay you properly."))',
       10, False, MUTED, w=12, indent=1)
B.text(ws, r0 + 3, 2, 'Most regulars accept a small, explained price rise. Give a month\'s notice, change it on your booking page, and say thank you.', 9, False, MUTED, w=12, indent=1, italic=True)
for rr in range(r0 + 1, r0 + 4): ws.row_dimensions[rr].height = 26
B.protect(ws)

# ================================================================== Example data
random.seed(19)
clients = ['Chloe B.', 'Amira K.', 'Jess T.', 'Priya S.', 'Hannah W.', 'Sophie L.', 'Zara M.', 'Ellie R.', 'Grace H.', 'Niamh O.',
           'Leah P.', 'Olivia D.', 'Ruby C.', 'Maya F.', 'Isla G.', 'Freya N.', 'Lucy A.', 'Aisha J.', 'Megan V.', 'Holly E.',
           'Tara Q.', 'Erin Y.', 'Nadia Z.', 'Kate U.', 'Bea I.', 'Lola X.', 'Rosa J.', 'Faye K.']
weights = [16, 14, 12, 6, 9, 9, 6, 6, 3, 8, 4]
log = []
d = dt.date(2025, 11, 1)
while d <= dt.date(2026, 10, 31):
    if d.weekday() in (1, 2, 3, 4, 5):
        for _ in range(random.choice([2, 2, 3, 3, 3, 4])):
            s = random.choices(SERVICES, weights)[0]
            tip = random.choice([0, 0, 0, 2, 3, 4, 5, 5]) if random.random() < 0.6 else 0
            pay = random.choices(PAY[:3], [70, 25, 5])[0]
            retail = random.choice([8, 12]) if random.random() < 0.07 else 0
            log.append([d, random.choice(clients), s[0], s[1], tip or None, pay, retail or None, ''])
    d += dt.timedelta(days=1)
log[3][7] = 'New client, came from Instagram'
log[9][7] = 'Rebooked for 3 weeks'
exps = []
for k in range(12):
    m = (10 + k) % 12 + 1
    md = dt.date(2025 if m >= 11 else 2026, m, 1)
    exps.append((md.replace(day=1), 'Salon owner', 'Chair rent for the month', 346.67, 'Chair / booth rent', 'Bank transfer'))
    exps.append((md.replace(day=3), 'Booking app', 'Monthly booking subscription', 19.00, 'Booking app & card fees', 'Card'))
    exps.append((md.replace(day=28), 'Card reader', 'Card payment fees', round(random.uniform(9, 14), 2), 'Booking app & card fees', 'Card'))
    exps.append((md.replace(day=12), 'Mobile network', 'Phone contract (business share)', 15.00, 'Bills & utilities', 'Card'))
    exps.append((md.replace(day=random.randint(5, 9)), 'Nail wholesaler', 'Gel colours, base and top coat', round(random.uniform(70, 120), 2), 'Gel & polish', 'Card'))
    exps.append((md.replace(day=random.randint(14, 18)), 'Nail wholesaler', 'Builder gel and BIAB', round(random.uniform(25, 55), 2), 'Gel & polish', 'Card'))
    exps.append((md.replace(day=random.randint(10, 20)), 'Beauty supplier', 'Files, buffers, wipes, foil wraps', round(random.uniform(14, 26), 2), 'Files & disposables', 'Card'))
    if m % 2 == 0:
        exps.append((md.replace(day=21), 'Beauty supplier', 'Acrylic powder and monomer', round(random.uniform(60, 95), 2), 'Acrylic & powders', 'Card'))
        exps.append((md.replace(day=22), 'Beauty supplier', 'Gloves, masks, disinfectant', round(random.uniform(18, 30), 2), 'Hygiene & PPE', 'Card'))
    if m % 3 == 1:
        exps.append((md.replace(day=24), 'Nail wholesaler', 'Tips and forms', round(random.uniform(20, 35), 2), 'Tips & forms', 'Card'))
        exps.append((md.replace(day=25), 'Craft supplier', 'Chrome powders, foils, gems', round(random.uniform(15, 30), 2), 'Nail art & decoration', 'Card'))
exps += [(dt.date(2026, 1, 15), 'Insurer', 'Beauty treatment insurance, 1 year', 89.00, 'Insurance & licences', 'Card'),
         (dt.date(2026, 2, 10), 'Tool shop', 'New e-file and bits', 129.00, 'Tools & equipment', 'Card'),
         (dt.date(2026, 3, 18), 'Printer', 'Business cards and aftercare cards', 32.00, 'Marketing & photos', 'Card'),
         (dt.date(2026, 4, 26), 'Training academy', 'Gel-X course', 145.00, 'Training & courses', 'Card'),
         (dt.date(2026, 5, 9), 'Beauty supplier', 'Cuticle oil to sell (24 pens)', 72.00, 'Retail stock to sell', 'Card'),
         (dt.date(2026, 6, 14), 'Tool shop', 'Replacement LED lamp', 89.99, 'Tools & equipment', 'Card'),
         (dt.date(2026, 7, 11), 'Social media', 'Boosted post for summer offers', 25.00, 'Marketing & photos', 'Card'),
         (dt.date(2026, 8, 30), 'Trade show', 'Nail trade show ticket and train', 68.50, 'Training & courses', 'Card'),
         (dt.date(2026, 9, 20), 'Beauty supplier', 'Cuticle oil to sell (24 pens)', 72.00, 'Retail stock to sell', 'Card'),
         (dt.date(2026, 10, 6), 'Nail wholesaler', 'Autumn gel colour collection', 64.00, 'Gel & polish', 'Card'),
         (dt.date(2026, 10, 19), 'Nail wholesaler', 'Extra builder gel (ran out)', 38.00, 'Gel & polish', 'Card'),
         (dt.date(2026, 10, 28), 'Craft supplier', 'Christmas nail art gems and foils', 27.50, 'Nail art & decoration', 'Card')]
exps = [e for e in exps if e[0] <= dt.date(2026, 10, 31)]
exps.sort(key=lambda x: x[0])
stock = [('Builder gel, clear', 'Gel & polish', 'Nail wholesaler', 18.50, 2, 2, dt.date(2026, 10, 19)),
         ('BIAB, natural pink', 'Gel & polish', 'Nail wholesaler', 16.00, 3, 2, dt.date(2026, 10, 2)),
         ('Gel base coat', 'Gel & polish', 'Nail wholesaler', 9.50, 1, 2, dt.date(2026, 9, 8)),
         ('Gel top coat, no wipe', 'Gel & polish', 'Nail wholesaler', 9.50, 3, 2, dt.date(2026, 10, 2)),
         ('Gel colours (autumn set)', 'Gel & polish', 'Nail wholesaler', 6.40, 10, 4, dt.date(2026, 10, 6)),
         ('Acrylic powder, clear', 'Acrylic & powders', 'Beauty supplier', 21.00, 1, 1, dt.date(2026, 10, 21)),
         ('Monomer liquid', 'Acrylic & powders', 'Beauty supplier', 24.00, 2, 1, dt.date(2026, 10, 21)),
         ('Soft gel tips, box', 'Tips & forms', 'Nail wholesaler', 14.00, 1, 1, dt.date(2026, 10, 24)),
         ('Nail forms, roll', 'Tips & forms', 'Nail wholesaler', 6.50, 2, 1, dt.date(2026, 10, 24)),
         ('Chrome powder', 'Nail art', 'Craft supplier', 4.00, 5, 2, dt.date(2026, 10, 28)),
         ('Files 100/180 (pack of 50)', 'Disposables', 'Beauty supplier', 12.00, 1, 1, dt.date(2026, 10, 12)),
         ('Lint-free wipes', 'Disposables', 'Beauty supplier', 3.50, 6, 3, dt.date(2026, 10, 12)),
         ('Nitrile gloves (box of 100)', 'Hygiene', 'Beauty supplier', 6.00, 1, 2, dt.date(2026, 10, 22)),
         ('Surface disinfectant', 'Hygiene', 'Beauty supplier', 7.50, 2, 1, dt.date(2026, 10, 22)),
         ('Cuticle oil pens (to sell)', 'Retail', 'Beauty supplier', 3.00, 9, 6, dt.date(2026, 9, 20))]
bills = [('Chair rent', 'Chair / booth rent', 80, 'Weekly', 'Every Monday', 'Paid to the salon by bank transfer'),
         ('Booking app', 'Booking app & card fees', 19, 'Monthly', '3rd', ''),
         ('Card reader fees (about)', 'Booking app & card fees', 12, 'Monthly', 'End of month', 'Roughly 1.7% of card takings'),
         ('Phone (business share)', 'Bills & utilities', 15, 'Monthly', '12th', ''),
         ('Insurance', 'Insurance & licences', 89, 'Yearly', '15 Jan', 'Treatment and public liability'),
         ('Training (planned)', 'Training & courses', 240, 'Yearly', 'Spring', 'One course a year')]
moved = []
for k in range(12):
    m = (10 + k) % 12 + 1
    inc_ = sum((x[3] or 0) + (x[4] or 0) + (x[6] or 0) for x in log if x[0].month == m)
    exp_ = sum(e[3] for e in exps if e[0].month == m)
    sug = max(0, inc_ - exp_) * 0.25
    moved.append(200 if m == 10 else int(round(sug / 10.0)) * 10)

# ================================================================== Client Log
ws = S['Client Log']
B.page(ws, 'Client Log', 'One row per appointment. Pick the service, type the price and any tip. Totals add up on their own.',
       {2: 13, 3: 18, 4: 22, 5: 10, 6: 9, 7: 14, 8: 10, 9: 11, 10: 30}, ncols=9, nrows=CR2 + 4)
B.box(ws, 7, 2, 7, 10, GOLDT, GOLDT)
B.text(ws, 7, 2, f'=COUNT(B{CR1}:B{CR2})&" appointments logged  ·  takings "&{M(f"SUM(I{CR1}:I{CR2})")}&"  ·  tips "&{M(f"SUM(F{CR1}:F{CR2})")}&" ("&{M(f"SUMIFS(F{CR1}:F{CR2},G{CR1}:G{CR2},\"Cash\")")}&" in cash)"',
       10, True, '6B5B45', w=9, indent=1)
ws.row_dimensions[7].height = 26
for j, h in enumerate(['DATE', 'CLIENT', 'SERVICE', 'PRICE', 'TIP', 'PAID BY', 'RETAIL SALE', 'TOTAL', 'NOTES']):
    B.th(ws, 8, 2 + j, h, align='right' if j in (3, 4, 6, 7) else 'left')
for i in range(CR2 - CR1 + 1):
    r = CR1 + i
    row = log[i] if (not BLANK and i < len(log)) else [None] * 8
    B.inp(ws, r, 2, row[0], DATE); B.inp(ws, r, 3, row[1]); B.inp(ws, r, 4, row[2])
    B.inp(ws, r, 5, row[3], NUM2, 'right'); B.inp(ws, r, 6, row[4], NUM2, 'right'); B.inp(ws, r, 7, row[5])
    B.inp(ws, r, 8, row[6], NUM2, 'right')
    B.fx(ws, r, 9, f'=IF(AND(E{r}="",F{r}="",H{r}=""),"",N(E{r})+N(F{r})+N(H{r}))', NUM2, True)
    B.inp(ws, r, 10, row[7] or None)
B.dv(ws, f'D{CR1}:D{CR2}', ref='=' + SVCRNG)
B.dv(ws, f'G{CR1}:G{CR2}', ref=PAYREF)
B.protect(ws)
LOGN = len(log)

# ================================================================== Expenses
ws = S['Expenses']
B.page(ws, 'Expenses', 'Every business cost: supplies, rent, fees. Pick a category so the Dashboard can show where the money goes.',
       {2: 13, 3: 18, 4: 32, 5: 25, 6: 11, 7: 14, 8: 24}, ncols=7, nrows=ER2 + 4)
B.box(ws, 7, 2, 7, 8, GOLDT, GOLDT)
B.text(ws, 7, 2, f'=COUNT(B{ER1}:B{ER2})&" costs logged  ·  total "&{M(f"SUM(F{ER1}:F{ER2})")}&"  ·  supplies (first 7 categories) "&{M(f"SUMPRODUCT(SUMIFS(F{ER1}:F{ER2},E{ER1}:E{ER2},Settings!$B${CAT0}:$B${CAT0 + 6}))")}',
       10, True, '6B5B45', w=7, indent=1)
ws.row_dimensions[7].height = 26
for j, h in enumerate(['DATE', 'PAID TO', 'WHAT FOR', 'CATEGORY', 'AMOUNT', 'PAID BY', 'NOTES']):
    B.th(ws, 8, 2 + j, h, align='right' if j == 4 else 'left')
for i in range(ER2 - ER1 + 1):
    r = ER1 + i
    e = exps[i] if (not BLANK and i < len(exps)) else [None] * 6
    B.inp(ws, r, 2, e[0], DATE); B.inp(ws, r, 3, e[1]); B.inp(ws, r, 4, e[2]); B.inp(ws, r, 5, e[4])
    B.inp(ws, r, 6, e[3], NUM2, 'right'); B.inp(ws, r, 7, e[5]); B.inp(ws, r, 8, None)
B.dv(ws, f'E{ER1}:E{ER2}', ref='=' + CATRNG)
B.dv(ws, f'G{ER1}:G{ER2}', ref=PAYREF)
B.protect(ws)

# ================================================================== Supplies & Stock
ws = S['Supplies & Stock']
B.page(ws, 'Supplies & Stock', 'Gel, acrylic, tips, disposables and retail. Set a reorder level and never run out mid-appointment.',
       {2: 28, 3: 18, 4: 18, 5: 11, 6: 10, 7: 11, 8: 14, 9: 12, 10: 13}, ncols=9, nrows=SR2 + 6)
B.box(ws, 7, 2, 7, 10, GOLDT, GOLDT)
B.text(ws, 7, 2, f'=IF(COUNTA(B{SR1}:B{SR2})=0,"Add the products you use. When IN STOCK falls to the REORDER AT level, the row turns coral.",COUNTIF(H{SR1}:H{SR2},"●*")&" item(s) to reorder  ·  stock on the shelf worth "&{M(f"SUM(I{SR1}:I{SR2})")})',
       10, True, '6B5B45', w=9, indent=1)
ws.row_dimensions[7].height = 26
for j, h in enumerate(['PRODUCT', 'TYPE', 'BUY FROM', 'COST EACH', 'IN STOCK', 'REORDER AT', 'STATUS', 'STOCK VALUE', 'LAST BOUGHT']):
    B.th(ws, 8, 2 + j, h, align='right' if j in (3, 4, 5, 7) else 'left')
for i in range(SR2 - SR1 + 1):
    r = SR1 + i
    s = stock[i] if (not BLANK and i < len(stock)) else [None] * 7
    B.inp(ws, r, 2, s[0]); B.inp(ws, r, 3, s[1]); B.inp(ws, r, 4, s[2]); B.inp(ws, r, 5, s[3], NUM2, 'right')
    B.inp(ws, r, 6, s[4], '0', 'right'); B.inp(ws, r, 7, s[5], '0', 'right')
    B.fx(ws, r, 8, f'=IF(OR(B{r}="",F{r}=""),"",IF(F{r}<=N(G{r}),"● Reorder","✓ OK"))', None, True, align='left')
    B.fx(ws, r, 9, f'=IF(B{r}="","",N(E{r})*N(F{r}))', NUM2)
    B.inp(ws, r, 10, s[6], DATE)
    ws.cell(r, 12, f'=IF(LEFT(H{r},1)="●",ROW(),99999)')
ws.column_dimensions['L'].hidden = True
coral_rule(ws, f'H{SR1}:H{SR2}', f'H{SR1}')
B.dv(ws, f'C{SR1}:C{SR2}', ref=STREF)
B.protect(ws)

# ================================================================== Rent & Bills
ws = S['Rent & Bills']
B.page(ws, 'Rent & Bills', 'Your fixed costs: chair or booth rent, booking app, insurance. Turned into one monthly figure.',
       {2: 28, 3: 25, 4: 11, 5: 12, 6: 13, 7: 14, 8: 32}, ncols=7, nrows=60)
for j, h in enumerate(['BILL', 'CATEGORY', 'AMOUNT', 'HOW OFTEN', 'PER MONTH', 'DUE', 'NOTES']):
    B.th(ws, 8, 2 + j, h, align='right' if j in (2, 4) else 'left')
for i in range(BR2 - BR1 + 1):
    r = BR1 + i
    b = bills[i] if i < len(bills) else None
    B.inp(ws, r, 2, b[0] if b else None, keep=True); B.inp(ws, r, 3, b[1] if b else None, keep=True)
    B.inp(ws, r, 4, ex(b[2]) if b else None, NUM2, 'right'); B.inp(ws, r, 5, b[3] if b else None, keep=True)
    B.fx(ws, r, 6, f'=IF(N(D{r})=0,"",D{r}*IF(E{r}="Weekly",52/12,IF(E{r}="Every 2 weeks",26/12,IF(E{r}="Quarterly",1/3,IF(E{r}="Yearly",1/12,1)))))', NUM2, True)
    B.inp(ws, r, 7, ex(b[4]) if b else None); B.inp(ws, r, 8, ex(b[5]) if b else None)
B.dv(ws, f'C{BR1}:C{BR2}', ref='=' + CATRNG)
B.dv(ws, f'E{BR1}:E{BR2}', ['Weekly', 'Every 2 weeks', 'Monthly', 'Quarterly', 'Yearly'])
r = BR2 + 1
B.fx(ws, r, 2, 'Fixed costs per month', None, True, WHITE, 'left', w=4); B.fx(ws, r, 6, f'=SUM(F{BR1}:F{BR2})', NUM2, True, WHITE)
B.fx(ws, r, 7, f'=IFERROR(TEXT(F{r}/{HOURS},SUBSTITUTE({FMT},"#,##0","#,##0.00"))&" per hour worked","")', None, False, WHITE, 'left', w=2)
B.box(ws, 7, 2, 7, 8, GOLDT, GOLDT)
B.text(ws, 7, 2, f'="Fixed costs: "&{M(f"F{r}")}&" a month, "&{M(f"F{r}*12")}&" a year. Pricing Check spreads them over your "&{HOURS}&" hours."', 10, True, '6B5B45', w=7, indent=1)
ws.row_dimensions[7].height = 26
# chair rent vs commission
c0 = r + 3
B.section(ws, c0, 2, 'Renting vs commission: which costs you less?', 6)
B.text(ws, c0 + 1, 2, 'Thinking of moving salon, or going on commission? Type the salon\'s commission and compare it with what you pay now.', 9, color=MUTED, w=7)
B.text(ws, c0 + 2, 2, 'Commission the salon would keep', 10, True, w=2); B.inp(ws, c0 + 2, 4, 0.4, '0%', 'right', keep=True)
B.text(ws, c0 + 3, 2, 'Your average monthly service takings', 10, True, w=2)
B.fx(ws, c0 + 3, 4, f'=IFERROR(AVERAGEIF({MS}!$C$9:$C$20,">0"),0)', NUM, True, WHITE)
B.text(ws, c0 + 4, 2, 'Commission would cost you', 10, True, w=2); B.fx(ws, c0 + 4, 4, f'=D{c0 + 3}*D{c0 + 2}', NUM, True, WHITE)
B.text(ws, c0 + 5, 2, 'Your fixed costs now', 10, True, w=2); B.fx(ws, c0 + 5, 4, f'=F{r}', NUM, True, WHITE)
B.box(ws, c0 + 2, 6, c0 + 5, 8, TINT, TINT)
B.text(ws, c0 + 2, 6, f'=IF(D{c0 + 3}=0,"Log a month of clients to compare.",IF(D{c0 + 4}>D{c0 + 5},"Renting saves you about "&{M(f"D{c0 + 4}-D{c0 + 5}")}&" a month compared with "&TEXT(D{c0 + 2},"0%")&" commission.","Commission would cost about "&{M(f"D{c0 + 5}-D{c0 + 4}")}&" a month less than your fixed costs now. Worth a conversation."))',
       11, True, INK, w=3, h=4, indent=1, valign='center')
B.protect(ws)

# ================================================================== Monthly Summary
ws = S['Monthly Summary']
B.page(ws, 'Monthly Summary', 'Your 12 months side by side. Everything here works itself out from the logs.',
       {2: 12, 3: 11, 4: 9, 5: 9, 6: 11, 7: 11, 8: 11, 9: 11, 10: 11, 11: 9, 12: 11, 13: 9, 14: 9}, ncols=13, nrows=40)
hd = ['MONTH', 'SERVICES', 'TIPS', 'RETAIL', 'TAKINGS', 'COSTS', 'PROFIT', 'SET ASIDE FOR TAX', 'YOURS TO KEEP', 'CLIENTS',
      'AVERAGE PER CLIENT', 'CARD TIPS', 'CASH TIPS']
for j, h in enumerate(hd):
    B.th(ws, 8, 2 + j, h, align='left' if j == 0 else 'right')
ws.row_dimensions[8].height = 30
for c in range(2, 15):
    ws.cell(8, c).alignment = Alignment(horizontal='left' if c == 2 else 'right', vertical='center', wrap_text=True, indent=1 if c == 2 else 0)
for i in range(12):
    r = 9 + i
    lo, hi = f'$B{r}', f'EOMONTH($B{r},0)'
    B.fx(ws, r, 2, f'=EDATE({START},{i})' if i else f'=DATE(YEAR({START}),MONTH({START}),1)', MON, True, align='left')
    B.fx(ws, r, 3, f'=SUMIFS({mrange("E", CL, CR1, CR2, lo, hi)})', NUM)
    B.fx(ws, r, 4, f'=SUMIFS({mrange("F", CL, CR1, CR2, lo, hi)})', NUM)
    B.fx(ws, r, 5, f'=SUMIFS({mrange("H", CL, CR1, CR2, lo, hi)})', NUM)
    B.fx(ws, r, 6, f'=C{r}+D{r}+E{r}', NUM, True)
    B.fx(ws, r, 7, f'=SUMIFS({mrange("F", EX, ER1, ER2, lo, hi)})', NUM)
    B.fx(ws, r, 8, f'=F{r}-G{r}', NUM, True)
    B.fx(ws, r, 9, f'=MAX(0,H{r})*{TAXP}', NUM)
    B.fx(ws, r, 10, f'=H{r}-I{r}', NUM, True)
    B.fx(ws, r, 11, f'=COUNTIFS({CL}!$B${CR1}:$B${CR2},">="&{lo},{CL}!$B${CR1}:$B${CR2},"<="&{hi})', '0;-0;"–"')
    B.fx(ws, r, 12, f'=IF(K{r}=0,0,F{r}/K{r})', NUM)
    B.fx(ws, r, 13, f'=SUMIFS({mrange("F", CL, CR1, CR2, lo, hi)},{CL}!$G${CR1}:$G${CR2},"<>Cash")', NUM)
    B.fx(ws, r, 14, f'=SUMIFS({mrange("F", CL, CR1, CR2, lo, hi)},{CL}!$G${CR1}:$G${CR2},"Cash")', NUM)
r = 21
B.fx(ws, r, 2, 'Year', None, True, WHITE, 'left')
for c in range(3, 15):
    L_ = L(c)
    f = f'=IF(SUM(K9:K20)=0,0,F{r}/K{r})' if c == 12 else f'=SUM({L_}9:{L_}20)'
    B.fx(ws, r, c, f, NUM if c != 11 else '0', True, WHITE)
    ws.cell(r, c).border = Border(top=thin('CFC6B6'))
ws.cell(r, 2).border = Border(top=thin('CFC6B6'))
B.text(ws, 23, 2, 'Costs = everything on the Expenses tab in that month (rent, supplies, fees). Set aside for tax = profit x your % in Settings. Card tips = tips paid any way except cash.',
       9, color=MUTED, w=13)
B.protect(ws)

# ================================================================== Tax Set-Aside
ws = S['Tax Set-Aside']
B.page(ws, 'Tax Set-Aside', 'Move a slice of every month\'s profit into a separate pot, so the tax bill never comes as a shock.',
       {2: 12, 3: 12, 4: 14, 5: 14, 6: 14, 7: 14, 8: 26}, ncols=7, nrows=40)
B.box(ws, 7, 2, 7, 8, GOLDT, GOLDT)
B.text(ws, 7, 2, f'="Your rate: "&TEXT({TAXP},"0%")&" of profit (change it in Settings to suit your country). Set aside so far "&{M("SUM(E9:E20)")}&" of "&{M("SUM(D9:D20)")}&" suggested."',
       10, True, '6B5B45', w=7, indent=1)
ws.row_dimensions[7].height = 26
for j, h in enumerate(['MONTH', 'PROFIT', 'SUGGESTED', 'YOU MOVED', 'POT SO FAR', 'BEHIND (–) / AHEAD', 'NOTE']):
    B.th(ws, 8, 2 + j, h, align='left' if j in (0, 6) else 'right')
for i in range(12):
    r = 9 + i
    B.fx(ws, r, 2, f'={MS}!B{9 + i}', MON, True, align='left')
    B.fx(ws, r, 3, f'={MS}!H{9 + i}', NUM)
    B.fx(ws, r, 4, f'={MS}!I{9 + i}', NUM)
    B.inp(ws, r, 5, ex(moved[i] if i < len(moved) else None), NUM, 'right')
    B.fx(ws, r, 6, f'=IF(AND(E{r}="",D{r}=0),"",SUM($E$9:E{r}))', NUM, True)
    B.fx(ws, r, 7, f'=IF(AND(E{r}="",D{r}=0),"",SUM($E$9:E{r})-SUM($D$9:D{r}))', '#,##0;-#,##0;"–"')
    B.fx(ws, r, 8, f'=IF(G{r}="","",IF(G{r}<-50,"● Top up the pot",IF(E{r}="","Move it when the month ends","✓ On track")))', None, True, align='left')
coral_rule(ws, 'H9:H20', 'H9')
B.fx(ws, 21, 2, 'Year', None, True, WHITE, 'left')
for c, f in [(3, '=SUM(C9:C20)'), (4, '=SUM(D9:D20)'), (5, '=SUM(E9:E20)')]:
    B.fx(ws, 21, c, f, NUM, True, WHITE)
B.tip(ws, 23, 2, 'Tip: open a separate savings pot just for tax and move the SUGGESTED amount on the 1st of each month. '
      'This is a simple estimate, not tax advice: tax rules differ by country, so check your local rules or ask an accountant.', 7, 1, 40)
B.protect(ws)

# ================================================================== Monthly Money Check-in
ws = S['Monthly Money Check-in']
B.page(ws, 'Monthly Money Check-in', 'Ten minutes at the end of each month: your month in plain words, then a few honest questions.',
       {2: 26, 3: 12, 4: 12, 5: 12, 6: 3, 7: 16, 8: 30, 9: 9}, ncols=8, nrows=60)
B.text(ws, 7, 2, 'Month to check in on', 10, True); B.inp(ws, 7, 3, ex(dt.datetime(2026, 10, 1)), MON, w=2)
B.text(ws, 7, 5, 'Leave blank for your latest month', 8.5, color=MUTED, w=3)
CHK = "$K$7"
ws['K7'] = (f'=IF(C7="",IF(COUNT({CL}!$B${CR1}:$B${CR2})=0,DATE(YEAR({START}),MONTH({START}),1),'
            f'DATE(YEAR(MAX({CL}!$B${CR1}:$B${CR2})),MONTH(MAX({CL}!$B${CR1}:$B${CR2})),1)),DATE(YEAR(C7),MONTH(C7),1))')
ws['K7'].number_format = MON; ws['K7'].font = F(8, color='B9B2A6')
lo, hi = CHK, f'EOMONTH({CHK},0)'
# category table (spending vs plan)
T0 = 26
B.section(ws, T0 - 1, 2, 'Spending vs your plan this month', 4)
for j, h in enumerate(['CATEGORY', 'PLAN', 'SPENT', 'OVER (+) / UNDER']):
    B.th(ws, T0, 2 + j, h, align='left' if j == 0 else 'right')
B.th(ws, T0, 7, ''); B.th(ws, T0, 8, 'SPENT AS A SHARE OF PLAN'); B.th(ws, T0, 9, '')
for i in range(NC):
    r = T0 + 1 + i
    B.fx(ws, r, 2, f'=Settings!B{CAT0 + i}', None, False, align='left')
    B.fx(ws, r, 3, f'=N(Settings!C{CAT0 + i})', NUM)
    B.fx(ws, r, 4, f'=SUMIFS({mrange("F", EX, ER1, ER2, lo, hi)},{EX}!$E${ER1}:$E${ER2},B{r})', NUM)
    B.fx(ws, r, 5, f'=ROUND(D{r}-C{r},0)', '+#,##0;-#,##0;"–"', True)
    B.fx(ws, r, 8, f'={bar_f(f"IF(C{r}=0,0,D{r}/C{r})", DSAGE, 16)}', None, False, align='left', color=DSAGE)
    B.fx(ws, r, 9, f'=IF(C{r}=0,IF(D{r}>0,"no plan",""),TEXT(D{r}/C{r},"0%"))', None, False, align='left', color=DSAGE)
    ws.cell(r, 10, f'=E{r}+ROW()/1000000')
ws.column_dimensions['J'].hidden = True
ws.conditional_formatting.add(f'E{T0 + 1}:E{T0 + NC}', FormulaRule(formula=[f'E{T0 + 1}>0.5'], font=Font(name=FONT, color=CORAL, bold=True)))
TE = T0 + NC + 1
B.fx(ws, TE, 2, 'Total', None, True, WHITE, 'left')
for c, f in [(3, f'=SUM(C{T0 + 1}:C{TE - 1})'), (4, f'=SUM(D{T0 + 1}:D{TE - 1})'), (5, f'=ROUND(D{TE}-C{TE},0)')]:
    B.fx(ws, TE, c, f, NUM if c < 5 else '+#,##0;-#,##0;"–"', True, WHITE)
# figures for the month (hidden helper column H rows 8-16)
inc = f'SUMIFS({mrange("I", CL, CR1, CR2, lo, hi)})'
tips = f'SUMIFS({mrange("F", CL, CR1, CR2, lo, hi)})'
cash = f'SUMIFS({mrange("F", CL, CR1, CR2, lo, hi)},{CL}!$G${CR1}:$G${CR2},"Cash")'
ncl = f'COUNTIFS({CL}!$B${CR1}:$B${CR2},">="&{lo},{CL}!$B${CR1}:$B${CR2},"<="&{hi})'
spent = f'D{TE}'
plan = f'C{TE}'
prof = '($K$8-$K$12)'
helpers = [(8, inc), (9, tips), (10, cash), (11, ncl), (12, spent), (13, f'MAX(J{T0 + 1}:J{T0 + NC})'),
           (14, f'IFERROR(INDEX(B{T0 + 1}:B{T0 + NC},MATCH(K13,J{T0 + 1}:J{T0 + NC},0)),"")'), (15, f'IFERROR({prof}/{GOAL},0)'),
           (16, f'IFERROR(INDEX({TX}!$E$9:$E$20,MATCH({CHK},{TX}!$B$9:$B$20,0)),"")')]
for rr, f in helpers:
    ws.cell(rr, 11, '=' + f).font = F(8, color='B9B2A6')
ws.column_dimensions['K'].hidden = True
ws.column_dimensions['L'].width = 2
summary = (f'=IF(K8=0,"No appointments logged for "&TEXT({CHK},"mmmm yyyy")&" yet. Add them on the Client Log and your summary writes itself here.",'
           f'"In "&TEXT({CHK},"mmmm yyyy")&" I did "&K11&" appointments and took "&{M("K8")}&", including "&{M("K9")}&" in tips ("&{M("K10")}&" in cash). '
           f'I spent "&{M("K12")}&" on the business against a plan of "&{M(plan)}&IF(K12>{plan}," ("&{M(f"K12-{plan}")}&" over)."," ("&{M(f"{plan}-K12")}&" under).")&'
           f'IF(K13>=0.5," My biggest overspend was "&K14&", "&{M("K13")}&" over plan."," Every category stayed within plan.")&'
           f'" My profit was "&{M(prof)}&", "&TEXT(K15,"0%")&" of my "&{M(GOAL)}&" monthly goal. '
           f'I should put "&{M(f"MAX(0,{prof})*{TAXP}")}&" aside for tax"&IF(K16="",", and I have not moved it yet.",IF(K16>=MAX(0,{prof})*{TAXP}-0.5," and I have done it."," and so far I have moved "&{M("K16")}&".")))')
B.section(ws, 9, 2, '1.  Your month in plain words', 6)
B.text(ws, 10, 2, 'Worked out from your logs. Copy this one box if you want to keep a note or share it.', 9, color=MUTED, w=7)
B.box(ws, 11, 2, 15, 8, WHITE, GOLD)
c = B.text(ws, 11, 2, summary, 13, False, INK, w=7, h=5, indent=1, valign='center')
for rr in range(11, 16): ws.row_dimensions[rr].height = 22
B.text(ws, 16, 2, 'Goal progress', 10, True, GOLD, indent=1)
B.text(ws, 16, 3, f'={bar_f("K15", GOLD, 20)}', 10, True, GOLD, w=3)
B.text(ws, 16, 6, f'=TEXT(K15,"0%")&" of "&{M(GOAL)}&" monthly profit goal"', 10, True, GOLD, w=3, indent=1)
ws.row_dimensions[16].height = 24
B.section(ws, 18, 2, '2.  Five honest questions', 6)
B.text(ws, 19, 2, 'No right answers. Write a line or two, just for you. Next month, read last month\'s answers first.', 9, color=MUTED, w=7)
QS = [('Which appointment this month made you proud, and which one left you drained?',
       'Proud of Zara\'s chrome set. Drained after the Saturday I squeezed in 4 infills.'),
      ('Did you buy any supplies on a whim? Would you buy them again?', 'The autumn gel collection. Half the colours are still unopened.'),
      ('Was there a moment you felt awkward saying your price, or gave a discount you did not need to?',
       'Knocked £5 off for a regular without being asked. I need to stop doing that.'),
      ('Looking at your profit, did the hours you worked feel worth it?', 'Mostly. Acrylic infills take too long for what I charge.'),
      ('What is one small thing you will try next month?', 'Raise infills to the Pricing Check price and only reorder gel from the reorder list.')]
for i, (q, a) in enumerate(QS):
    r = 20 + i
    B.text(ws, r, 2, f'{i + 1}.  {q}', 10, True, INK, w=3, indent=1)
    B.inp(ws, r, 5, a, w=4)
    ws.cell(r, 5).alignment = Alignment(wrap_text=True, vertical='center', indent=1)
    ws.row_dimensions[r].height = 40
B.tip(ws, TE + 2, 2, 'Want a second opinion? Copy your summary and these questions into any AI assistant you use (ChatGPT, Gemini, Copilot) '
      'and ask it to reply like a kind, honest money coach. Optional: this tab works fully on its own.', 7, 1, 36)
B.protect(ws)

# ================================================================== Start Here
ws = S['Start Here']
B.page(ws, 'Start here', 'Your nail business money in one place. Five steps, no formulas to touch.', {2: 7, 3: 96, 4: 3}, ncols=3, nrows=50)
B.box(ws, 7, 2, 7, 3, GOLDT, GOLDT)
B.text(ws, 7, 2, '=IF(COUNT(\'Client Log\'!B9:B808)=0,"This is your BLANK file: type your own numbers in it. The EXAMPLE file shows a full year for a made-up nail tech, Mia.",'
       '"You are looking at the EXAMPLE file: a made-up nail tech, Mia, so you can see every tab working. Open the BLANK (start here) file for your own numbers.")',
       10, True, '6B5B45', w=2, indent=1)
ws.row_dimensions[7].height = 40
steps = [('1', 'Settings. Your name, currency symbol (any country), the month your year starts, your tax set-aside %, monthly profit goal and the '
               'hourly pay you want. Then the monthly plan for each expense category.'),
         ('2', 'Pricing Check and Rent & Bills. Edit the service menu to your own prices, product cost and minutes. List your chair or booth rent '
               'and bills. You will see what each service really earns per hour.'),
         ('3', 'Every day: Client Log. One row per appointment: date, client, service (dropdown), price, tip and how they paid. Costs go on Expenses.'),
         ('4', 'Every week: Supplies & Stock. Update what is on the shelf. Anything at its reorder level turns coral and shows on the Dashboard.'),
         ('5', 'Every month: Dashboard, Monthly Summary, Tax Set-Aside and the Monthly Money Check-in. Move your tax money, read your month in '
               'plain words and answer the five questions.')]
for i, (n, t) in enumerate(steps):
    r = 9 + i * 2
    B.box(ws, r, 2, r, 3); B.text(ws, r, 2, n, 18, True, GOLD, align='center'); B.text(ws, r, 3, t, 10.5, indent=1)
    ws.row_dimensions[r].height = 46; ws.row_dimensions[r + 1].height = 6
B.tip(ws, 20, 2, 'Colours: pale yellow = type here. White = worked out for you (locked so nothing breaks; Review > Unprotect Sheet, no password). '
      'Coral ● = needs you (reorder, raise a price, top up the tax pot). Green ✓ = all good.', 2, 1, 44)
B.tip(ws, 22, 2, 'Google Sheets: upload the .xlsx to Google Drive, open it, choose File > Save as Google Sheets, then move between tabs with the tab bar '
      'along the bottom. Excel: works in Excel 2016 and later, Excel for Mac, Excel online and the Excel phone app.', 2, 1, 44)
B.tip(ws, 24, 2, 'Any country, any currency. The tax set-aside is a simple % you choose, not tax advice: check your local rules or ask an accountant. '
      'Questions about the tracker: joel@wayofwealthcoaching.com', 2, 1, 40)
B.text(ws, 26, 2, 'Way of Wealth Studio  ·  created by a qualified financial planner', 9, True, GOLD, w=2)
B.protect(ws)

# ================================================================== Dashboard
ws = S['Dashboard']
B.page(ws, 'Nail Business Dashboard', '', ncols=16, nrows=120)
ws['B2'] = f'=IF({BIZ}="","Nail Business Dashboard",{BIZ})'
ws['B3'] = f'=IF({NAME}="","Your year",{NAME}&"\'s year")&"  ·  "&TEXT({MS}!B9,"mmm yyyy")&" to "&TEXT({MS}!B20,"mmm yyyy")&"  ·  all amounts in "&IF({CUR}="","£",{CUR})&"  ·  "&{SETUP}'
ws['B3'].font = F(10, color=MUTED)
for r, h in [(7, 22), (8, 30), (9, 18), (10, 8), (11, 22), (12, 30), (13, 18)]:
    ws.row_dimensions[r].height = h
TAK, COST, PROF, TIPS, CLN = f'{MS}!$F$21', f'{MS}!$G$21', f'{MS}!$H$21', f'{MS}!$D$21', f'{MS}!$K$21'
B.hero(ws, 7, 2, 7, 7, 'PROFIT THIS YEAR SO FAR', f'={M(PROF)}',
       f'=IF({TAK}=0,"Log your first appointment on the Client Log to see your real profit.","From "&{CLN}&" appointments. After "&{M(COST)}&" of costs and "&{M(f"{MS}!$I$21")}&" put aside for tax, about "&{M(f"{MS}!$J$21")}&" is yours to keep.")',
       'Takings minus every cost on the Expenses tab.')
B.kpi(ws, 7, 10, 'TAKINGS', f'={M(TAK)}', f'="incl. tips "&{M(f"{MS}!$D$21")}&" · retail "&{M(f"{MS}!$E$21")}', accent=DSAGE)
B.kpi(ws, 7, 14, 'COSTS', f'={M(COST)}', f'=IF({COST}=0,"log costs on Expenses","biggest: "&INDEX(B{82}:B{97},MATCH(MAX(E82:E97),E82:E97,0)))', accent=CORAL)
B.kpi(ws, 11, 10, 'TIPS', f'={M(TIPS)}', f'="card "&{M(f"{MS}!$M$21")}&" · cash "&{M(f"{MS}!$N$21")}', accent=GOLD)
B.kpi(ws, 11, 14, 'AVERAGE PER CLIENT', f'={M(f"{MS}!$L$21")}', f'={CLN}&" appointments this year"', accent=GOLD)
# next steps
B.box(ws, 15, 2, 19, 16, TINT, TINT)
B.text(ws, 15, 2, 'YOUR NEXT STEPS', 8, True, DSAGE, w=4, indent=1)
nre = f'COUNTIF({SS}!$H${SR1}:$H${SR2},"●*")'
first_re = f'INDEX({SS}!$B${SR1}:$B${SR2},MATCH(SMALL({SS}!$L${SR1}:$L${SR2},1),{SS}!$L${SR1}:$L${SR2},0)-0)'
first_re = f'INDEX({SS}!$B:$B,SMALL({SS}!$L${SR1}:$L${SR2},1))'
nlow = f'COUNTIF({PC}!$L${PR1}:$L${PR2},"●*")'
low1 = f'INDEX({PC}!$B${PR1}:$B${PR2},MATCH(MIN({PC}!$Q${PR1}:$Q${PR2}),{PC}!$Q${PR1}:$Q${PR2},0))'
low1p = f'INDEX({PC}!$M${PR1}:$M${PR2},MATCH(MIN({PC}!$Q${PR1}:$Q${PR2}),{PC}!$Q${PR1}:$Q${PR2},0))'
gap = f'MIN({TX}!$G$9:$G$20)'
lines = [f'=IF({nre}>0,"●  Reorder "&{nre}&" supplies before they run out, starting with "&{first_re}&" (Supplies & Stock).",IF(COUNTA({SS}!$B${SR1}:$B${SR2})=0,"Add your supplies on Supplies & Stock to get reorder reminders.","✓  Stock is fine: nothing at its reorder level."))',
         f'=IF(COUNT({PC}!$I${PR1}:$I${PR2})=0,"Next: add your prices, product cost and minutes on Pricing Check.",IF({nlow}>0,"●  "&{low1}&" earns less than your "&{M(TARGET)}&" an hour target. The price that pays you properly: "&{M(low1p)}&" (Pricing Check).","✓  Every service earns your target per hour."))',
         f'=IF({TAK}=0,"Next: fill in Settings, then log your clients.",IF(N({gap})<-50,"●  Your tax pot is "&{M(f"-{gap}")}&" behind. Top it up on the Tax Set-Aside tab.","✓  Tax pot on track. Do your Monthly Money Check-in at the end of the month."))']
for k, f in enumerate(lines):
    r = 16 + k
    B.text(ws, r, 2, f, 10.5, k == 0, CHAR, w=15, indent=2)
    ws.row_dimensions[r].height = 22
    ws.conditional_formatting.add(f'B{r}', FormulaRule(formula=[f'LEFT(B{r},1)="●"'], font=Font(name=FONT, color='B5574A', bold=True)))
ws.row_dimensions[19].height = 8
for r, h in [(21, 22), (22, 30), (23, 18)]:
    ws.row_dimensions[r].height = h
GP = f'IFERROR(INDEX({MS}!$H$9:$H$20,MATCH({CI}!$K$7,{MS}!$B$9:$B$20,0))/{GOAL},0)'
B.kpi(ws, 21, 2, 'SET ASIDE FOR TAX', f'={M(f"{MS}!$I$21")}', f'=TEXT({TAXP},"0%")&" of profit · moved "&{M(f"{TX}!$E$21")}', accent=CHAR)
B.kpi(ws, 21, 6, 'SUPPLIES TO REORDER', f'={nre}', f'="stock worth "&{M(f"SUM({SS}!$I${SR1}:$I${SR2})")}', accent=CORAL)
B.kpi(ws, 21, 10, 'BEST EARNER PER HOUR', f'=IF(COUNT({PC}!$I${PR1}:$I${PR2})=0,"–",IFERROR(INDEX({PC}!$B${PR1}:$B${PR2},MATCH(MAX({PC}!$R${PR1}:$R${PR2}),{PC}!$R${PR1}:$R${PR2},0)),"–"))',
      f'=IF(COUNT({PC}!$I${PR1}:$I${PR2})=0,"add prices on Pricing Check",{M(f"MAX({PC}!$I${PR1}:$I${PR2})")}&" an hour after costs")', accent=DSAGE)
ws.cell(22, 10).font = F(13, True, INK)
B.kpi(ws, 21, 14, f'="GOAL · "&UPPER(TEXT({CI}!$K$7,"mmm yyyy"))', f'={GP}', f'={bar_f(GP, GOLD, 12)}', value_fmt='0%', accent=GOLD)
# chart data
D0 = 80
B.section(ws, D0, 2, 'The numbers behind the charts', 10)
B.th(ws, D0 + 1, 2, 'MONTH'); B.th(ws, D0 + 1, 3, 'Takings', align='right'); B.th(ws, D0 + 1, 4, 'Costs', align='right')
B.th(ws, D0 + 1, 5, 'Profit', align='right'); B.th(ws, D0 + 1, 6, 'Goal', align='right')
for i in range(12):
    r = D0 + 2 + i
    B.fx(ws, r, 2, f'=TEXT({MS}!B{9 + i},"mmm")', None, True, align='left')
    B.fx(ws, r, 3, f'={MS}!F{9 + i}', NUM); B.fx(ws, r, 4, f'={MS}!G{9 + i}', NUM)
    B.fx(ws, r, 5, f'={MS}!H{9 + i}', NUM); B.fx(ws, r, 6, f'=N({GOAL})', NUM)
# category totals at col B..E rows 82-97 used by COSTS sub: put in cols 8-9 instead
B.th(ws, D0 + 1, 8, 'COST CATEGORY', 2); B.th(ws, D0 + 1, 10, 'This year', align='right')
for i in range(NC):
    r = D0 + 2 + i
    B.fx(ws, r, 8, f'=Settings!B{CAT0 + i}', None, False, align='left', w=2)
    B.fx(ws, r, 10, f'=SUMIFS({EX}!$F${ER1}:$F${ER2},{EX}!$E${ER1}:$E${ER2},H{r})', NUM)
# fix COSTS kpi sub to use the category block
ws.cell(9, 14).value = f'=IF({COST}=0,"log costs on Expenses","biggest: "&INDEX(H{D0 + 2}:H{D0 + 1 + NC},MATCH(MAX(J{D0 + 2}:J{D0 + 1 + NC}),J{D0 + 2}:J{D0 + 1 + NC},0)))'
B.th(ws, D0 + 1, 12, 'TAKINGS MIX', 2); B.th(ws, D0 + 1, 14, 'This year', align='right')
for i, (lab, ref) in enumerate([('Services', f'{MS}!$C$21'), ('Tips', f'{MS}!$D$21'), ('Retail', f'{MS}!$E$21')]):
    B.fx(ws, D0 + 2 + i, 12, lab, None, False, align='left', w=2); B.fx(ws, D0 + 2 + i, 14, f'={ref}', NUM)
SV0 = D0 + 6
B.th(ws, SV0, 12, 'SERVICE', 2); B.th(ws, SV0, 14, 'Profit / hour', align='right')
for i in range(len(SERVICES)):
    r = SV0 + 1 + i
    B.fx(ws, r, 12, f'=IF({PC}!B{PR1 + i}="","",{PC}!B{PR1 + i})', None, False, align='left', w=2)
    B.fx(ws, r, 14, f'=IF({PC}!I{PR1 + i}="",0,{PC}!I{PR1 + i})', NUM2)
TG = D0 + 2
cats = Reference(ws, min_col=2, min_row=D0 + 2, max_row=D0 + 13)
bar_chart(ws, 'B25', 'Takings vs costs by month', cats, Reference(ws, min_col=3, max_col=4, min_row=D0 + 1, max_row=D0 + 13),
          w=11.8, h=7.4, colors=[DSAGE, GOLD])
line_chart(ws, 'J25', 'Monthly profit vs your goal', cats,
           [Reference(ws, min_col=5, min_row=D0 + 1, max_row=D0 + 13), Reference(ws, min_col=6, min_row=D0 + 1, max_row=D0 + 13)],
           w=11.8, h=7.4, colors=[CHAR, GOLD])
bar_chart(ws, 'B41', 'Where the money goes', Reference(ws, min_col=8, min_row=D0 + 2, max_row=D0 + 1 + NC),
          Reference(ws, min_col=10, min_row=D0 + 1, max_row=D0 + 1 + NC), w=11.8, h=8.6, horizontal=True, legend=False, colors=[GOLD])
doughnut(ws, 'J41', 'Takings mix', Reference(ws, min_col=12, min_row=D0 + 2, max_row=D0 + 4),
         Reference(ws, min_col=14, min_row=D0 + 1, max_row=D0 + 4), w=11.8, h=8.6, colors=[DSAGE, GOLD, CHAR])
from openpyxl.chart.label import DataLabel
_dl = ws._charts[-1].series[0].dLbls
_dl.dLbl = [DataLabel(idx=i, showPercent=False, showVal=False, showCatName=False, showSerName=False, showLegendKey=False) for i in (1, 2)]   # tips and retail slices are small: no overlapping % labels
bar_chart(ws, 'B59', 'Profit per hour by service', Reference(ws, min_col=12, min_row=SV0 + 1, max_row=SV0 + len(SERVICES)),
          Reference(ws, min_col=14, min_row=SV0, max_row=SV0 + len(SERVICES)), w=11.8, h=8.6, horizontal=True, legend=False, colors=[DSAGE])
# top services table
B.section(ws, 59, 10, 'Top 5 services by takings', 7)
B.th(ws, 60, 10, 'SERVICE', 3); B.th(ws, 60, 13, 'DONE', align='right'); B.th(ws, 60, 14, 'TAKINGS', 2, 'right'); B.th(ws, 60, 16, '')
for k in range(5):
    r = 61 + k
    key = f'LARGE({PC}!$P${PR1}:$P${PR2},{k + 1})'
    pos = f'MATCH({key},{PC}!$P${PR1}:$P${PR2},0)'
    B.fx(ws, r, 10, f'=IF({key}<1,"",INDEX({PC}!$B${PR1}:$B${PR2},{pos}))', None, k == 0, align='left', w=3)
    B.fx(ws, r, 13, f'=IF(J{r}="","",INDEX({PC}!$K${PR1}:$K${PR2},{pos}))', '0')
    B.fx(ws, r, 14, f'=IF(J{r}="","",{M(f"INDEX({PC}!$O${PR1}:$O${PR2},{pos})")})', None, False, align='right', w=2)
    ws.row_dimensions[r].height = 22
B.section(ws, 67, 10, 'Reorder soon', 4)
B.text(ws, 67, 14, f'=IF({nre}=0,"",{nre}&" item(s)")', 9, True, CORAL, w=3, align='right')
for k in range(6):
    r = 68 + k
    B.fx(ws, r, 10, f'=IFERROR(IF(SMALL({SS}!$L${SR1}:$L${SR2},{k + 1})=99999,IF({k}=0,IF(COUNTA({SS}!$B${SR1}:$B${SR2})=0,"Add your supplies on Supplies & Stock","✓ Nothing to reorder"),""),"● "&INDEX({SS}!$B:$B,SMALL({SS}!$L${SR1}:$L${SR2},{k + 1}))&"  ("&INDEX({SS}!$F:$F,SMALL({SS}!$L${SR1}:$L${SR2},{k + 1}))&" left)"),"")',
         None, False, align='left', w=7)
    ws.row_dimensions[r].height = 17
    ws.conditional_formatting.add(f'J{r}', FormulaRule(formula=[f'LEFT(J{r},1)="●"'], font=Font(name=FONT, color='B5574A')))
B.fx(ws, 74, 10, f'=IF({nre}>6,"…and "&({nre}-6)&" more on Supplies & Stock","")', None, False, align='left', w=7, color=MUTED)
B.text(ws, 77, 2, 'Way of Wealth Studio  ·  created by a qualified financial planner  ·  joel@wayofwealthcoaching.com', 8.5, False, MUTED, w=15)
for c in ws._charts:
    c.roundedCorners = False
    if c.legend is not None: c.legend.overlay = False
B.protect(ws)

# ================================================================== save
AREAS = {'Dashboard': 'A1:R78', 'Start Here': 'A1:E27', 'Settings': f'A1:F{CAT0 + NC + 1}', 'Client Log': f'A1:K{CR1 + 45}',
         'Expenses': f'A1:I{ER1 + 45}', 'Supplies & Stock': f'A1:K{SR1 + 22}', 'Rent & Bills': f'A1:I{BR2 + 10}',
         'Monthly Summary': 'A1:O24', 'Pricing Check': f'A1:N{PR2 + 6}', 'Tax Set-Aside': 'A1:I24',
         'Monthly Money Check-in': f'A1:L{TE + 3}'}
orig_save = B.wb.save
B.wb.save = lambda p: None
B.save(OUT, AREAS)
for w_ in B.wb.worksheets:
    w_.oddFooter.center.text = 'Way of Wealth Studio  ·  Nail Tech Income & Expense Tracker'
    w_.oddFooter.center.size = 8
B.wb.active = 1 if BLANK else 0
if BLANK:
    for _w in B.wb.worksheets: _w.sheet_view.tabSelected = False
    B.wb.worksheets[1].sheet_view.tabSelected = True
orig_save(OUT)
print('saved', OUT, 'log rows', LOGN, 'expenses', len(exps))
