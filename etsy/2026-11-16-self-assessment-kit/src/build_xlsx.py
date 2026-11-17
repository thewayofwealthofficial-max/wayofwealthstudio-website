"""UK Self Assessment 2025/26 Deadline Kit - Way of Wealth Studio.
For UK sole traders filing the 2025/26 return (6 Apr 2025 - 5 Apr 2026) by 31 January 2027.
python3 build_xlsx.py out/file.xlsx [blank]

Every rate below was checked on gov.uk in Nov 2026 (see the Tax Estimate tab, 'Rates used'):
- SA103S 2026 / SA103F 2026 forms and notes (HMRC 12/25) for every box number and wording
- income-tax-rates-and-allowances-current-and-past, rates-and-allowances-national-insurance-contributions
- simpler-income-tax-simplified-expenses (vehicles, working-from-home)
"""
import sys, os, datetime as dt, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
import skin
from skin import *
from openpyxl.chart import Reference, BarChart
from openpyxl.chart.series import SeriesLabel
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Font, Alignment

CHAR = '3D3D3D'
skin.NAVY = CHAR  # hero card in charcoal (spec palette)
OUT = sys.argv[1]; BLANK = len(sys.argv) > 2 and sys.argv[2] == 'blank'
GBP = '£#,##0;-£#,##0;"–"'
GBP2 = '£#,##0.00;-£#,##0.00;"–"'
DATE = 'd mmm yyyy'
YS, YE = 'DATE(2025,4,6)', 'DATE(2026,4,5)'

TABS = [('Dashboard', GOLD), ('Start Here', GOLD), ('Settings', DSAGE), ('Income Log', DSAGE), ('Expenses Log', DSAGE),
        ('Mileage', DSAGE), ('Use of Home', DSAGE), ('SA103 Boxes', CHAR), ('Tax Estimate', CHAR),
        ('Tax Pot 26-27', GOLD), ('Deadlines', CORAL)]
B = Book(TABS, BLANK)
S = B.s
IL, EL, ML, UH, BX, TE, TP, DL = ("'Income Log'", "'Expenses Log'", "'Mileage'", "'Use of Home'", "'SA103 Boxes'",
                                  "'Tax Estimate'", "'Tax Pot 26-27'", "'Deadlines'")
NAME, DESC, UTR, BASIS, TA, SCOT, EMP, PAYE, POAPAID, C2VOL = [f'Settings!$C${r}' for r in range(7, 17)]
IR1, IR2 = 9, 158   # income rows
ER1, ER2 = 9, 208   # expense rows
MR1, MR2 = 9, 88    # mileage rows
INCCATS = ['Turnover (fees and sales)', 'Other business income']
# expense categories: (dropdown name = SA103F wording, short label, SA103F box, SA103S box)
CATS = [('Cost of goods bought for resale or goods used', 'Goods for resale', 17, '11'),
        ('Wages, salaries and other staff costs', 'Staff costs', 19, '13'),
        ('Car, van and travel expenses', 'Car, van, travel', 20, '12'),
        ('Rent, rates, power and insurance costs', 'Rent, power, insurance', 21, '14'),
        ('Repairs and maintenance of property and equipment', 'Repairs', 22, '15'),
        ('Phone, fax, stationery and other office costs', 'Phone, office, software', 23, '18'),
        ('Advertising (not client entertaining)', 'Advertising, website', 24, '19'),
        ('Interest on bank and other loans', 'Loan interest', 25, '17'),
        ('Bank, credit card and other financial charges', 'Bank charges', 26, '17'),
        ('Accountancy, legal and other professional fees', 'Accountant, legal, PI', 28, '16'),
        ('Other business expenses', 'Other', 30, '19')]
CATROW0 = 20  # Settings!G20:G30 holds the dropdown list


def inyear(col, r):
    return f'AND({col}{r}>={YS},{col}{r}<={YE})'


def check_fmt(ws, rng, first):
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'LEFT({first},1)="✕"'], font=Font(name=FONT, color=CORAL, bold=True)))
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'LEFT({first},1)="✓"'], font=Font(name=FONT, color=DSAGE, bold=True)))


# ================================================================== Settings
ws = S['Settings']
B.page(ws, 'Settings', 'Fill in the yellow boxes once. Every other tab updates on its own.',
       {2: 46, 3: 26, 4: 3, 5: 62, 6: 3, 7: 30}, ncols=6, nrows=40)
B.th(ws, 6, 2, 'ABOUT YOU'); B.th(ws, 6, 3, 'TYPE OR PICK HERE'); B.th(ws, 6, 5, 'WHAT IT MEANS')
rows = [('Your name', 'Sam Taylor', None, False, 'Shown on the Dashboard. Nothing is sent anywhere.'),
        ('What your business does', 'Freelance graphic design', None, False, 'Goes in box 1 (short form) or box 2 (full form).'),
        ('Your UTR (optional)', '12345 67890', '@', False, 'Unique Taxpayer Reference: 10 digits on HMRC letters. Optional here.'),
        ('Accounting basis', 'Cash basis', None, True, 'Cash basis (the default since April 2024) = money in and out when it actually moved. '
         'Pick "Traditional accounting" only if you or your accountant chose it (then put X in box 8 / box 10).'),
        ('Use the £1,000 trading allowance instead of expenses?', 'No', None, True,
         'Yes = take £1,000 off your income and claim NO expenses. Only worth it if your costs were under £1,000.'),
        ('Scottish taxpayer?', 'No', None, True, 'Yes if your main home was in Scotland. Scotland has its own Income Tax bands.'),
        ('Employment pay in 2025/26 (from your P60)', 0, GBP2, False, 'Pay from a job, if you also had one. Leave 0 if not.'),
        ('Tax already taken off that pay (P60)', 0, GBP2, False, 'The tax on your P60. It comes off your bill.'),
        ('Payments on account already paid for 2025/26', 0, GBP2, False,
         'Only if HMRC asked you for payments on account in Jan 2026 and Jul 2026. First return? Leave 0.'),
        ('Pay voluntary Class 2 NI?', 'No', None, True, 'Only matters if your profit is under £6,845: £3.50 a week keeps your State Pension record. '
         'At £6,845 or more it is treated as paid for free.')]
for i, (lab, v, fmt, keep, hlp) in enumerate(rows):
    r = 7 + i
    B.text(ws, r, 2, lab, 10, True); B.inp(ws, r, 3, v, fmt, keep=keep); B.text(ws, r, 5, hlp, 9, color=MUTED)
    ws.row_dimensions[r].height = 34 if len(hlp) > 70 else 26
B.dv(ws, 'C10', ['Cash basis', 'Traditional accounting']); B.dv(ws, 'C11', ['No', 'Yes']); B.dv(ws, 'C12', ['No', 'Yes'])
B.dv(ws, 'C16', ['No', 'Yes'])
B.tip(ws, 18, 2, 'Not tax advice. This kit helps you add up your numbers and see where they go on the form. It does not file your return: '
      'you type the figures into HMRC online yourself (or give them to your accountant). Questions: joel@wayofwealthcoaching.com', 4, 1, 46)
B.text(ws, 6, 7, 'LISTS (USED BY DROPDOWNS)', 7, True, 'B9B2A6')
for i, c in enumerate(CATS):
    B.text(ws, CATROW0 + i, 7, c[0], 8, False, 'A79F92', wrap=False)
ws.column_dimensions['G'].hidden = True
B.protect(ws)
CATREF = f'=Settings!$G${CATROW0}:$G${CATROW0 + len(CATS) - 1}'

# ================================================================== Example data
random.seed(7)
inc = []
clients = [('Harbour Coffee Co', 'Brand refresh and menu design'), ('Northlight Studio', 'Sub-contract design days'),
           ('Bright Lane Bakery', 'Packaging labels'), ('Kestrel Fitness', 'Social media templates'),
           ('Mill Street Books', 'Book cover design'), ('Fernway Charity', 'Annual report layout'),
           ('Oakfield Dental', 'Leaflet and signage'), ('Tidewater Events', 'Event posters')]
amounts = [1450, 1800, 650, 900, 1200, 2400, 780, 1100, 1650, 950, 600, 2100, 1300, 875, 1500, 720, 1950, 1150, 980, 1400,
           640, 1250, 2200, 860, 1050, 1700, 690, 1325, 900, 1080, 760]
d = dt.date(2025, 4, 14)
for i, a in enumerate(amounts):
    c = clients[(i * 3) % len(clients)]
    inc.append((d, c[0], c[1], a, INCCATS[0]))
    d += dt.timedelta(days=11)
inc.append((dt.date(2026, 4, 14), 'Harbour Coffee Co', 'Menu update (this is 2026/27: not counted)', 600, INCCATS[0]))
exp = []
for m in range(12):
    md = dt.date(2025 + (m + 3) // 12, (m + 3) % 12 + 1, 1)
    exp.append((md.replace(day=8), 'Adobe', 'Creative Cloud subscription', 56.98, CATS[5][0], 1))
    exp.append((md.replace(day=12), 'Mobile phone network', 'Phone contract', 25.00, CATS[5][0], 0.6))
    exp.append((md.replace(day=28), 'Business bank', 'Monthly account fee', 6.00, CATS[8][0], 1))
exp += [(dt.date(2025, 4, 20), 'Web host', 'Website hosting and domain, 1 year', 180.00, CATS[6][0], 1),
        (dt.date(2025, 5, 3), 'Insurer', 'Professional indemnity insurance', 210.00, CATS[9][0], 1),
        (dt.date(2025, 5, 22), 'Rail operator', 'Train to client workshop, Bath', 38.40, CATS[2][0], 1),
        (dt.date(2025, 6, 10), 'Co-working space', 'Day passes x 6', 90.00, CATS[3][0], 1),
        (dt.date(2025, 6, 18), 'Stationer', 'Printing proofs and paper', 64.50, CATS[5][0], 1),
        (dt.date(2025, 7, 2), 'Font foundry', 'Font licence for client work', 149.00, CATS[5][0], 1),
        (dt.date(2025, 7, 25), 'Social media ads', 'Promoted posts', 120.00, CATS[6][0], 1),
        (dt.date(2025, 8, 14), 'Computer shop', 'Laptop screen repair', 95.00, CATS[4][0], 1),
        (dt.date(2025, 9, 5), 'Electronics retailer', 'External monitor (cash basis)', 249.00, CATS[5][0], 1),
        (dt.date(2025, 9, 19), 'Rail operator', 'Train to London client', 72.60, CATS[2][0], 1),
        (dt.date(2025, 10, 8), 'Co-working space', 'Day passes x 6', 90.00, CATS[3][0], 1),
        (dt.date(2025, 10, 30), 'Design magazine', 'Annual trade subscription', 64.00, CATS[10][0], 1),
        (dt.date(2025, 11, 12), 'Online course', 'Motion graphics refresher course', 85.00, CATS[10][0], 1),
        (dt.date(2025, 12, 3), 'Social media ads', 'Promoted posts', 150.00, CATS[6][0], 1),
        (dt.date(2026, 1, 15), 'Stationer', 'Business cards', 42.00, CATS[6][0], 1),
        (dt.date(2026, 2, 9), 'Rail operator', 'Train to Cardiff client', 46.20, CATS[2][0], 1),
        (dt.date(2026, 2, 26), 'Co-working space', 'Day passes x 6', 90.00, CATS[3][0], 1),
        (dt.date(2026, 3, 20), 'Stock image site', 'Image credits', 79.00, CATS[10][0], 1)]
exp.sort(key=lambda x: x[0])
miles = [(dt.date(2025, 4, 23), 'Home to Harbour Coffee Co, Clifton and back', 'Car or van', 14),
         (dt.date(2025, 5, 14), 'Home to Bright Lane Bakery, Keynsham and back', 'Car or van', 22),
         (dt.date(2025, 6, 4), 'Home to Kestrel Fitness, Weston and back', 'Car or van', 46),
         (dt.date(2025, 6, 25), 'Home to print shop, Avonmouth and back', 'Car or van', 18),
         (dt.date(2025, 7, 16), 'Home to Fernway Charity, Gloucester and back', 'Car or van', 72),
         (dt.date(2025, 8, 6), 'Home to Oakfield Dental, Yate and back', 'Car or van', 28),
         (dt.date(2025, 9, 3), 'Home to Tidewater Events, Swindon and back', 'Car or van', 84),
         (dt.date(2025, 9, 24), 'Home to Mill Street Books, Bath and back', 'Car or van', 30),
         (dt.date(2025, 10, 15), 'Home to Fernway Charity, Gloucester and back', 'Car or van', 72),
         (dt.date(2025, 11, 5), 'Home to Harbour Coffee Co, Clifton and back', 'Car or van', 14),
         (dt.date(2025, 11, 26), 'Home to Northlight Studio, Cardiff and back', 'Car or van', 92),
         (dt.date(2025, 12, 10), 'Home to Kestrel Fitness, Weston and back', 'Car or van', 46),
         (dt.date(2026, 1, 21), 'Home to Tidewater Events, Swindon and back', 'Car or van', 84),
         (dt.date(2026, 2, 11), 'Home to Oakfield Dental, Yate and back', 'Car or van', 28),
         (dt.date(2026, 3, 4), 'Home to Northlight Studio, Cardiff and back', 'Car or van', 92),
         (dt.date(2026, 3, 25), 'Home to Bright Lane Bakery, Keynsham and back', 'Car or van', 22)]
hours = [62, 70, 58, 45, 66, 80, 104, 96, 52, 74, 88, 110]

# ================================================================== Income Log
ws = S['Income Log']
B.page(ws, 'Income log', 'Every payment your business received between 6 April 2025 and 5 April 2026. One row per payment.',
       {2: 14, 3: 24, 4: 40, 5: 14, 6: 26, 7: 26}, ncols=6, nrows=IR2 + 8)
B.text(ws, 7, 2, f'="Counted for 2025/26: "&TEXT(E{IR2 + 2}+E{IR2 + 3},"£#,##0.00")&"   ·   rows that need a look: "&E{IR2 + 4}', 9, True, DSAGE, w=6)
for j, (h, a) in enumerate([('DATE PAID', 'left'), ('CLIENT', 'left'), ('WHAT FOR', 'left'), ('AMOUNT (£)', 'right'),
                            ('TYPE', 'left'), ('CHECK', 'left')]):
    B.th(ws, 8, 2 + j, h, align=a)
for i in range(IR2 - IR1 + 1):
    r = IR1 + i
    x = inc[i] if i < len(inc) else None
    B.inp(ws, r, 2, x[0] if x else None, DATE); B.inp(ws, r, 3, x[1] if x else None); B.inp(ws, r, 4, x[2] if x else None)
    B.inp(ws, r, 5, x[3] if x else None, '#,##0.00', 'right'); B.inp(ws, r, 6, x[4] if x else None)
    B.fx(ws, r, 7, f'=IF(AND(B{r}="",E{r}=""),"",IF(NOT(ISNUMBER(B{r})),"✕ Type a date",IF(NOT({inyear("B", r)}),"✕ Not 2025/26: not counted",'
                   f'IF(N(E{r})=0,"✕ Type the amount",IF(F{r}="","✕ Pick a type","✓ Counted")))))', None, False, None, 'left', size=9)
B.dv(ws, f'F{IR1}:F{IR2}', INCCATS)
check_fmt(ws, f'G{IR1}:G{IR2}', f'G{IR1}')
T1 = IR2 + 2
B.fx(ws, T1, 2, 'Turnover counted for 2025/26 (box 9 short / box 15 full)', bold=True, bg=TINT, align='left', w=3)
B.fx(ws, T1, 5, f'=SUMIFS(E{IR1}:E{IR2},F{IR1}:F{IR2},"{INCCATS[0]}",B{IR1}:B{IR2},">="&{YS},B{IR1}:B{IR2},"<="&{YE})', GBP2, True, TINT)
B.fx(ws, T1 + 1, 2, 'Other business income (box 10 short / box 16 full)', bold=True, bg=WHITE, align='left', w=3)
B.fx(ws, T1 + 1, 5, f'=SUMIFS(E{IR1}:E{IR2},F{IR1}:F{IR2},"{INCCATS[1]}",B{IR1}:B{IR2},">="&{YS},B{IR1}:B{IR2},"<="&{YE})', GBP2, True, WHITE)
B.fx(ws, T1 + 2, 2, 'Rows that need a look (✕)', bold=True, bg=WHITE, align='left', w=3)
B.fx(ws, T1 + 2, 5, f'=COUNTIF(G{IR1}:G{IR2},"✕*")', '0', True, WHITE)
B.tip(ws, T1 + 4, 2, 'Cash basis: use the date the money reached you, not the invoice date. Payments dated outside 6 Apr 2025 to 5 Apr 2026 are shown '
      'but not counted. "Other business income" is rare (for example letting part of your business premises): most people only use Turnover.', 6, 1, 44)
INC_T, INC_O, INC_X = f'{IL}!$E${T1}', f'{IL}!$E${T1 + 1}', f'{IL}!$E${T1 + 2}'
B.protect(ws)

# ================================================================== Expenses Log
ws = S['Expenses Log']
B.page(ws, 'Expenses log', 'Every business cost paid between 6 April 2025 and 5 April 2026. Pick the HMRC category; the box is filled in for you.',
       {2: 15, 3: 24, 4: 38, 5: 12, 6: 52, 7: 10, 8: 13, 9: 24}, ncols=8, nrows=ER2 + 8)
B.text(ws, 7, 2, f'="Allowable for 2025/26: "&TEXT(H{ER2 + 2},"£#,##0.00")&"   ·   rows that need a look: "&H{ER2 + 3}', 9, True, DSAGE, w=8)
for j, (h, a) in enumerate([('DATE PAID', 'left'), ('SUPPLIER', 'left'), ('WHAT FOR', 'left'), ('AMOUNT (£)', 'right'),
                            ('HMRC CATEGORY (SA103 BOX)', 'left'), ('BUSINESS %', 'right'), ('ALLOWABLE', 'right'), ('CHECK', 'left')]):
    B.th(ws, 8, 2 + j, h, align=a)
for i in range(ER2 - ER1 + 1):
    r = ER1 + i
    x = exp[i] if i < len(exp) else None
    B.inp(ws, r, 2, x[0] if x else None, DATE); B.inp(ws, r, 3, x[1] if x else None); B.inp(ws, r, 4, x[2] if x else None)
    B.inp(ws, r, 5, x[3] if x else None, '#,##0.00', 'right'); B.inp(ws, r, 6, x[4] if x else None)
    B.inp(ws, r, 7, x[5] if x else None, '0%', 'right')
    B.fx(ws, r, 8, f'=IF(N(E{r})=0,"",E{r}*IF(G{r}="",1,MIN(1,MAX(0,G{r}))))', '#,##0.00')
    B.fx(ws, r, 9, f'=IF(AND(B{r}="",E{r}=""),"",IF(NOT(ISNUMBER(B{r})),"✕ Type a date",IF(NOT({inyear("B", r)}),"✕ Not 2025/26: not counted",'
                   f'IF(N(E{r})=0,"✕ Type the amount",IF(F{r}="","✕ Pick a category",IF(N(G{r})>1,"✕ % over 100","✓ Counted"))))))', None, False, None, 'left', size=9)
B.dv(ws, f'F{ER1}:F{ER2}', ref=CATREF)
check_fmt(ws, f'I{ER1}:I{ER2}', f'I{ER1}')
T2 = ER2 + 2
B.fx(ws, T2, 2, 'Allowable expenses counted for 2025/26 (before mileage and use of home)', bold=True, bg=TINT, align='left', w=6)
B.fx(ws, T2, 8, f'=SUMIFS(H{ER1}:H{ER2},B{ER1}:B{ER2},">="&{YS},B{ER1}:B{ER2},"<="&{YE},F{ER1}:F{ER2},"<>")', GBP2, True, TINT)
B.fx(ws, T2 + 1, 2, 'Rows that need a look (✕)', bold=True, bg=WHITE, align='left', w=6)
B.fx(ws, T2 + 1, 8, f'=COUNTIF(I{ER1}:I{ER2},"✕*")', '0', True, WHITE)
B.tip(ws, T2 + 3, 2, 'Business % = the business share of a cost you also use privately (for example 60% of a phone bill). Blank means 100%. '
      'Do not include client entertaining, your own wages or drawings, fines, or the cost of buying a car. If you claim mileage on the Mileage tab, '
      'do not also put that car\'s fuel, insurance or repairs here. Not tax advice: if unsure whether a cost is allowable, ask an accountant.', 8, 1, 56)
EXP_X = f'{EL}!$H${T2 + 1}'
B.protect(ws)

# ================================================================== Mileage
ws = S['Mileage']
B.page(ws, 'Mileage', 'Business journeys in your own car, van or motorbike, 2025/26. HMRC flat rates replace fuel, insurance and repairs.',
       {2: 15, 3: 46, 4: 15, 5: 12, 6: 13, 7: 24, 8: 3, 9: 36, 10: 11}, ncols=9, nrows=MR2 + 8)
B.text(ws, 7, 2, f'="Mileage claim for 2025/26: "&TEXT(F{MR2 + 2},"£#,##0.00")&"   ·   business miles: "&TEXT(F{MR2 + 3},"#,##0")&"   ·   rows that need a look: "&F{MR2 + 4}', 9, True, DSAGE, w=6)
for j, (h, a) in enumerate([('DATE', 'left'), ('JOURNEY (FROM, TO, WHY)', 'left'), ('VEHICLE', 'left'), ('BUSINESS MILES', 'right'),
                            ('CLAIM', 'right'), ('CHECK', 'left')]):
    B.th(ws, 8, 2 + j, h, align=a)
B.th(ws, 8, 9, 'HMRC FLAT RATES (BEFORE 6 APR 2026)'); B.th(ws, 8, 10, 'PER MILE', align='right')
rates = [('Car or van: first 10,000 business miles', 0.45), ('Car or van: after 10,000 miles', 0.25), ('Motorcycle: every mile', 0.24),
         ('Miles at the higher car rate', 10000)]
for i, (lab, v) in enumerate(rates):
    B.fx(ws, 9 + i, 9, lab, None, False, WHITE, 'left'); B.fx(ws, 9 + i, 10, v, '#,##0' if v > 1 else '£0.00', True, WHITE)
B.text(ws, 13, 9, 'Source: gov.uk/simpler-income-tax-simplified-expenses/vehicles. From 6 Apr 2026 (2026/27) the first-10,000 car rate is 55p.', 8, False, MUTED, w=2, h=3)
R1C, R2C, RMC, THR = '$J$9', '$J$10', '$J$11', '$J$12'
for i in range(MR2 - MR1 + 1):
    r = MR1 + i
    x = miles[i] if i < len(miles) else None
    B.inp(ws, r, 2, x[0] if x else None, DATE); B.inp(ws, r, 3, x[1] if x else None); B.inp(ws, r, 4, x[2] if x else None)
    B.inp(ws, r, 5, x[3] if x else None, '#,##0', 'right')
    prior = f'SUMIFS($E$8:E{r - 1},$D$8:D{r - 1},"Car or van",$B$8:B{r - 1},">="&{YS},$B$8:B{r - 1},"<="&{YE})'
    hi = f'MIN(E{r},MAX(0,{THR}-{prior}))'
    B.fx(ws, r, 6, f'=IF(OR(NOT(ISNUMBER(B{r})),N(E{r})=0),"",IF(NOT({inyear("B", r)}),0,IF(D{r}="Motorcycle",E{r}*{RMC},'
                   f'IF(D{r}="Car or van",{hi}*{R1C}+(E{r}-{hi})*{R2C},0))))', '#,##0.00')
    B.fx(ws, r, 7, f'=IF(AND(B{r}="",E{r}=""),"",IF(NOT(ISNUMBER(B{r})),"✕ Type a date",IF(NOT({inyear("B", r)}),"✕ Not 2025/26: not counted",'
                   f'IF(N(E{r})=0,"✕ Type the miles",IF(D{r}="","✕ Pick a vehicle","✓ Counted")))))', None, False, None, 'left', size=9)
B.dv(ws, f'D{MR1}:D{MR2}', ['Car or van', 'Motorcycle'])
check_fmt(ws, f'G{MR1}:G{MR2}', f'G{MR1}')
T3 = MR2 + 2
B.fx(ws, T3, 2, 'Mileage claim for 2025/26 (goes in Car, van and travel: box 12 short / box 20 full)', bold=True, bg=TINT, align='left', w=4)
B.fx(ws, T3, 6, f'=SUM(F{MR1}:F{MR2})', GBP2, True, TINT)
B.fx(ws, T3 + 1, 2, 'Business miles counted', bold=True, bg=WHITE, align='left', w=4)
B.fx(ws, T3 + 1, 6, f'=SUMIFS(E{MR1}:E{MR2},B{MR1}:B{MR2},">="&{YS},B{MR1}:B{MR2},"<="&{YE},D{MR1}:D{MR2},"<>")', '#,##0', True, WHITE)
B.fx(ws, T3 + 2, 2, 'Rows that need a look (✕)', bold=True, bg=WHITE, align='left', w=4)
B.fx(ws, T3 + 2, 6, f'=COUNTIF(G{MR1}:G{MR2},"✕*")', '0', True, WHITE)
B.tip(ws, 17, 9, 'Business journeys only, for example to clients or suppliers. Ordinary commuting to a regular place of work does not count. '
      'You cannot use these rates for a vehicle you already claimed capital allowances for. This tab assumes one car or van.', 2, 6, None)
MIL_T, MIL_X = f'{ML}!$F${T3}', f'{ML}!$F${T3 + 2}'
B.protect(ws)

# ================================================================== Use of Home
ws = S['Use of Home']
B.page(ws, 'Use of home', 'HMRC flat rate for working from home: type the hours you worked at home each month.',
       {2: 16, 3: 18, 4: 16, 5: 3, 6: 26, 7: 14, 8: 3}, ncols=7, nrows=40)
for j, (h, a) in enumerate([('MONTH', 'left'), ('HOURS WORKED AT HOME', 'right'), ('FLAT RATE', 'right')]):
    B.th(ws, 8, 2 + j, h, align=a)
B.th(ws, 8, 6, 'HOURS IN THE MONTH'); B.th(ws, 8, 7, 'FLAT RATE', align='right')
for i, (lab, v) in enumerate([('Under 25', 0), ('25 to 50', 10), ('51 to 100', 18), ('101 and more', 26)]):
    B.fx(ws, 9 + i, 6, lab, None, False, WHITE, 'left'); B.fx(ws, 9 + i, 7, v, '£#,##0', True, WHITE)
B.text(ws, 13, 6, 'Source: gov.uk/simpler-income-tax-simplified-expenses/working-from-home', 8, False, MUTED, w=2, h=2)
months = [dt.date(2025, 4, 1) + dt.timedelta(days=31 * k) for k in range(12)]
for i in range(12):
    r = 9 + i
    y, m = 2025 + (3 + i) // 12, (3 + i) % 12 + 1
    B.fx(ws, r, 2, dt.date(y, m, 1), 'mmm yyyy', True, align='left')
    B.inp(ws, r, 3, hours[i], '#,##0', 'right')
    B.fx(ws, r, 4, f'=IF(N(C{r})<25,0,IF(C{r}<=50,$G$10,IF(C{r}<=100,$G$11,$G$12)))', GBP2)
B.fx(ws, 21, 2, 'Total for 2025/26', bold=True, bg=TINT, align='left', w=2)
B.fx(ws, 21, 4, '=SUM(D9:D20)', GBP2, True, TINT)
B.tip(ws, 23, 2, 'Goes in Rent, rates, power and insurance costs (box 14 short / box 21 full). The flat rate covers heating, light and power only: '
      'you can still claim the business part of your phone and internet in Expenses. Use either the flat rate or a share of real home costs, not both. '
      'Hours = time spent working at home, 25 or more in the month.', 3, 1, 84)
B.tip(ws, 15, 6, 'April counts 6 to 30 April 2025; March counts 1 March to 5 April 2026.', 2, 2, None)
HOME_T = f'{UH}!$D$21'
B.protect(ws)

# ================================================================== SA103 Boxes
ws = S['SA103 Boxes']
B.page(ws, 'Your SA103 boxes', 'Your totals mapped to the official 2025/26 self-employment pages (SA103S short, SA103F full). Copy each figure into the matching box.',
       {2: 9, 3: 64, 4: 17, 5: 3, 6: 58}, ncols=5, nrows=72)
fx_ = lambda f: f
# category amounts (expenses log + mileage + home)
def cat_amt(i):
    name = f'Settings!$G${CATROW0 + i}'
    f = f'SUMIFS({EL}!$H${ER1}:$H${ER2},{EL}!$F${ER1}:$F${ER2},{name},{EL}!$B${ER1}:$B${ER2},">="&{YS},{EL}!$B${ER1}:$B${ER2},"<="&{YE})'
    if CATS[i][2] == 20: f += f'+{MIL_T}'
    if CATS[i][2] == 21: f += f'+{HOME_T}'
    return f'=IF({TA}="Yes",0,{f})'
# which form
B.box(ws, 7, 2, 9, 6, TINT, TINT)
B.text(ws, 7, 2, 'WHICH FORM DO I USE?', 8, True, DSAGE, w=2, indent=1)
B.fx(ws, 8, 2, f'=IF({INC_T}+{INC_O}>=90000,"SA103F (full): your turnover is £90,000 or more","SA103S (short): your turnover is under £90,000")',
     None, True, TINT, 'left', 2, CHAR, 12)
B.text(ws, 9, 2, 'Rule from the SA103S notes: use the short pages if turnover was under £90,000. Use the full pages instead if your accounting period '
       'did not end 31 Mar to 5 Apr, you changed accounting basis, or your business is more complex. Online, HMRC asks questions and picks the page for you.',
       8.5, False, MUTED, w=5, indent=1)
ws.row_dimensions[8].height = 24; ws.row_dimensions[9].height = 40
for c in range(2, 7):
    ws.cell(9, c).fill = fill(TINT)
B.text(ws, 7, 6, '=IF(' + TA + '="Yes","You chose the £1,000 trading allowance: no expense boxes are used.","")', 9, True, CORAL)

# ---- short form
r0 = 11
B.section(ws, r0, 2, 'SA103S Self-employment (short) 2025/26', 3)
for j, (h, a) in enumerate([('BOX', 'left'), ('OFFICIAL WORDING (SA103S 2026)', 'left'), ('YOUR FIGURE', 'right'), ('', 'left'), ('WHERE IT COMES FROM', 'left')]):
    if h or j == 4: B.th(ws, r0 + 1, 2 + j, h, align=a)
FULLROW = {}  # filled later; short form refers to full-form rows
short = [('8', 'If you\'ve used traditional accounting rather than cash basis to calculate your income and expenses, put \'X\' in the box',
          f'=IF({BASIS}="Traditional accounting","X","Leave blank")', None, 'Settings: accounting basis'),
         ('9', 'Your turnover – the takings, fees, sales or money earned by your business', f'={INC_T}', GBP2, 'Income Log'),
         ('10', 'Any other business income not included in box 9', f'={INC_O}', GBP2, 'Income Log ("Other business income")'),
         ('10.1', 'Trading income allowance – read the notes', f'=IF({TA}="Yes",MIN(1000,{INC_T}+{INC_O}),0)', GBP2, 'Settings: only if you chose it')]
for box_s in ['11', '12', '13', '14', '15', '16', '17', '18', '19']:
    short.append((box_s, None, None, GBP2, None))
short += [('20', 'Total allowable expenses – total of boxes 11 to 19', None, GBP2, 'Sum of boxes 11 to 19'),
          ('21', 'Net profit – if your business income is more than your expenses (if box 9 + box 10 minus box 20 is positive)', None, GBP2, ''),
          ('22', 'Or, net loss – if your expenses exceed your business income (if box 20 minus (box 9 + box 10) is positive)', None, GBP2, ''),
          ('28', 'Net business profit for tax purposes (if box 21 + box 26 + box 27 minus (boxes 22 to 25.2) is positive). Or if you\'ve completed box 10.1 (box 21 + box 26 + box 27 minus box 10.1)', None, GBP2,
           'No capital allowances, balancing charges or own-use goods in this kit'),
          ('31', 'Total taxable profits from this business (if box 28 + box 30 minus box 29 is positive)', None, GBP2, 'No losses brought forward in this kit'),
          ('36', 'If your total profits for 2025–26 are less than £6,845 and you choose to pay Class 2 NICs voluntarily, put \'X\' in the box', None, None, 'Settings: voluntary Class 2')]
SWORD = {'11': 'Costs of goods bought for resale or goods used', '12': 'Car, van and travel expenses – after private use proportion',
         '13': 'Wages, salaries and other staff costs', '14': 'Rent, rates, power and insurance costs',
         '15': 'Repairs and maintenance of property and equipment', '16': 'Accountancy, legal and other professional fees',
         '17': 'Interest and bank and credit card financial charges', '18': 'Phone, fax, stationery and other office costs',
         '19': 'Other allowable business expenses – client entertaining costs are not an allowable expense'}
SROW = {}
for i, s in enumerate(short):
    SROW[s[0]] = r0 + 2 + i
# ---- full form rows
f0 = r0 + 2 + len(short) + 2
FW = {15: 'Your turnover – the takings, fees, sales or money earned by your business', 16: 'Any other business income not included in box 15',
      '16.1': 'Trading income allowance – read the notes', 17: 'Cost of goods bought for resale or goods used', 19: 'Wages, salaries and other staff costs',
      20: 'Car, van and travel expenses', 21: 'Rent, rates, power and insurance costs', 22: 'Repairs and maintenance of property and equipment',
      23: 'Phone, fax, stationery and other office costs', 24: 'Advertising and business entertainment costs',
      25: 'Interest on bank and other loans', 26: 'Bank, credit card and other financial charges', 28: 'Accountancy, legal and other professional fees',
      30: 'Other business expenses'}
full = [('10', 'If you used traditional accounting rather than cash basis to calculate your income and expenses, put \'X\' in the box',
         f'=D{SROW["8"]}', None, 'Settings: accounting basis'),
        ('15', FW[15], f'=D{SROW["9"]}', GBP2, 'Income Log'), ('16', FW[16], f'=D{SROW["10"]}', GBP2, 'Income Log'),
        ('16.1', FW['16.1'], f'=D{SROW["10.1"]}', GBP2, 'Settings: only if you chose it')]
for i, c in enumerate(CATS):
    note = {20: 'Expenses Log + Mileage tab', 21: 'Expenses Log + Use of Home tab', 24: 'Advertising only. Client entertaining is not allowable: leave it out',
            28: 'Includes professional indemnity insurance'}.get(c[2], 'Expenses Log')
    full.append((str(c[2]), FW[c[2]], cat_amt(i), GBP2, note))
full += [('31', 'Total expenses (total of boxes 17 to 30)', None, GBP2, 'Sum of the expense boxes above'),
         ('47', 'Net profit – if your business income is more than your expenses (if box 15 + box 16 minus box 31 is positive)', None, GBP2, ''),
         ('48', 'Or, net loss – if your expenses are more than your business income (if box 31 minus (box 15 + box 16) is positive)', None, GBP2, ''),
         ('64', 'Net business profit for tax purposes (if box 47 + box 61 minus (box 48 + box 63) is positive)', None, GBP2, 'No disallowable or capital allowance adjustments'),
         ('73', 'Adjusted profit for 2025–26 – see the working sheet in the notes', None, GBP2, 'Working sheet: box 64 minus box 16.1'),
         ('76', 'Total taxable profits from this business – see the working sheet in the notes', None, GBP2, 'No losses brought forward in this kit'),
         ('100', 'If your total profits for 2025–26 are less than £6,845 and you choose to pay Class 2 NICs voluntarily, put \'X\' in the box', f'=D{SROW["36"]}', None, 'Settings: voluntary Class 2')]
FROW = {f[0]: f0 + 2 + i for i, f in enumerate(full)}
# short-form expense lines draw from full rows
smap = {'11': ['17'], '12': ['20'], '13': ['19'], '14': ['21'], '15': ['22'], '16': ['28'], '17': ['25', '26'], '18': ['23'], '19': ['24', '30']}
snote = {'12': 'Expenses Log + Mileage tab', '14': 'Expenses Log + Use of Home tab', '17': 'Full-form boxes 25 + 26', '19': 'Advertising + other (full-form boxes 24 + 30)',
         '16': 'Includes professional indemnity insurance'}
for k, rr in SROW.items():
    pass
for i, (bx, word, f, fmt, note) in enumerate(short):
    r = SROW[bx]
    if bx in smap:
        word = SWORD[bx]; f = '=' + '+'.join(f'D{FROW[x]}' for x in smap[bx]); note = snote.get(bx, 'Expenses Log')
    if bx == '20': f = f'=SUM(D{SROW["11"]}:D{SROW["19"]})'
    if bx == '21': f = f'=MAX(0,D{SROW["9"]}+D{SROW["10"]}-D{SROW["20"]})'
    if bx == '22': f = f'=MAX(0,D{SROW["20"]}-(D{SROW["9"]}+D{SROW["10"]}))'
    if bx == '28': f = f'=MAX(0,D{SROW["21"]}-D{SROW["22"]}-D{SROW["10.1"]})'
    if bx == '31': f = f'=D{SROW["28"]}'
    if bx == '36': f = f'=IF(AND({C2VOL}="Yes",D{SROW["31"]}<6845),"X","Leave blank")'
    B.fx(ws, r, 2, bx, None, True, None, 'left', color=GOLD)
    B.fx(ws, r, 3, word, None, False, None, 'left', size=9.5); ws.cell(r, 3).alignment = Alignment(wrap_text=True, vertical='center', indent=1)
    B.fx(ws, r, 4, f, fmt, bx in ('20', '21', '28', '31'), TINT if bx in ('31',) else None)
    B.fx(ws, r, 6, note, None, False, None, 'left', color=MUTED, size=8.5)
    ws.row_dimensions[r].height = 44 if len(word) > 140 else 30 if len(word) > 80 else 20
B.section(ws, f0, 2, 'SA103F Self-employment (full) 2025/26 – same numbers, full-form box numbers', 3)
for j, (h, a) in enumerate([('BOX', 'left'), ('OFFICIAL WORDING (SA103F 2026)', 'left'), ('YOUR FIGURE', 'right')]):
    B.th(ws, f0 + 1, 2 + j, h, align=a)
B.th(ws, f0 + 1, 6, 'WHERE IT COMES FROM')
for i, (bx, word, f, fmt, note) in enumerate(full):
    r = FROW[bx]
    exp_rows = [FROW[str(c[2])] for c in CATS]
    if bx == '31': f = f'=SUM(D{min(exp_rows)}:D{max(exp_rows)})'
    if bx == '47': f = f'=MAX(0,D{FROW["15"]}+D{FROW["16"]}-D{FROW["31"]})'
    if bx == '48': f = f'=MAX(0,D{FROW["31"]}-(D{FROW["15"]}+D{FROW["16"]}))'
    if bx == '64': f = f'=D{FROW["47"]}'
    if bx == '73': f = f'=MAX(0,D{FROW["64"]}-D{FROW["48"]}-D{FROW["16.1"]})'
    if bx == '76': f = f'=D{FROW["73"]}'
    B.fx(ws, r, 2, bx, None, True, None, 'left', color=GOLD)
    B.fx(ws, r, 3, word, None, False, None, 'left', size=9.5); ws.cell(r, 3).alignment = Alignment(wrap_text=True, vertical='center', indent=1)
    B.fx(ws, r, 4, f, fmt, bx in ('31', '47', '64', '76'), TINT if bx == '76' else None)
    B.fx(ws, r, 6, note, None, False, None, 'left', color=MUTED, size=8.5)
    ws.row_dimensions[r].height = 30 if len(word) > 80 else 20
endr = max(FROW.values()) + 2
B.tip(ws, endr, 2, 'Box numbers and wording are copied from HMRC\'s SA103S 2026 and SA103F 2026 pages (HMRC 12/25) for the tax year 6 April 2025 to 5 April 2026. '
      'Under £90,000 turnover you may put just the total in box 20 (short) or box 31 (full) instead of each line. Boxes not shown (capital allowances, '
      'losses, CIS, balance sheet, full-form disallowable column 32 to 46) are not covered by this kit: leave them blank unless they apply to you. '
      'The paper form prints the pence as 00, so type whole pounds.', 5, 1, 72)
B.tip(ws, endr + 2, 2, 'Not tax advice and it does not file anything: you copy these figures into your return at gov.uk (or give them to your accountant).', 5, 1, 24)
PROFIT = f'{BX}!$D${SROW["31"]}'
TURN, OTHER, EXPT, TAUSED = f'{BX}!$D${SROW["9"]}', f'{BX}!$D${SROW["10"]}', f'{BX}!$D${SROW["20"]}', f'{BX}!$D${SROW["10.1"]}'
FORMCELL = f'{BX}!$B$8'
B.protect(ws)

# ================================================================== Tax Estimate
ws = S['Tax Estimate']
B.page(ws, 'Tax estimate 2025/26', 'Income Tax and National Insurance on your 2025/26 profit, and what you pay on 31 Jan 2027 and 31 Jul 2027.',
       {2: 30, 3: 11, 4: 14, 5: 14, 6: 16, 7: 3, 8: 56}, ncols=7, nrows=80)
RT0 = 52  # rates table
RATES = [('Personal Allowance', 12570, GBP, 'gov.uk Income Tax rates and allowances, 2025 to 2026'),
         ('Personal Allowance taper starts at', 100000, GBP, 'same page'),
         ('Basic rate band (20%), taxable income up to', 37700, GBP, 'same page: England, NI and Wales'),
         ('Higher rate (40%) up to, then additional rate (45%)', 125140, GBP, 'same page'),
         ('Class 4 NI: Lower Profits Limit', 12570, GBP, 'gov.uk Rates and allowances: National Insurance, 2025 to 2026'),
         ('Class 4 NI: Upper Profits Limit', 50270, GBP, 'same page'),
         ('Class 4 NI: main rate', 0.06, '0%', 'same page'),
         ('Class 4 NI: rate above Upper Profits Limit', 0.02, '0%', 'same page'),
         ('Class 2 NI: Small Profits Threshold', 6845, GBP, 'same page; also SA103S box 36'),
         ('Class 2 NI: voluntary rate per week', 3.50, '£0.00', 'same page'),
         ('Payments on account: not needed if the bill is under', 1000, GBP, 'gov.uk Understand your Self Assessment bill: payments on account'),
         ('...or if more than this share was taken at source', 0.8, '0%', 'same page'),
         ('Trading income allowance', 1000, GBP, 'SA103S notes 2026, page SESN 1'),
         ('VAT threshold (short form if turnover under)', 90000, GBP, 'SA103S 2026 page SES 1; gov.uk VAT registration')]
RT = {}
B.section(ws, RT0, 2, 'Rates used (2025/26, checked on gov.uk, Nov 2026)', 5)
B.th(ws, RT0 + 1, 2, 'RATE', 3); B.th(ws, RT0 + 1, 5, 'VALUE', align='right'); B.th(ws, RT0 + 1, 6, ''); B.th(ws, RT0 + 1, 8, 'SOURCE')
for i, (lab, v, fmt, src) in enumerate(RATES):
    r = RT0 + 2 + i
    B.fx(ws, r, 2, lab, None, False, None, 'left', 3); B.fx(ws, r, 5, v, fmt, True); B.fx(ws, r, 6, '', None)
    B.fx(ws, r, 8, src, None, False, None, 'left', color=MUTED, size=8.5)
    RT[i] = f'$E${r}'
PA_, PAL, BB, HL, LPL, UPL, C4M, C4A, SPT, C2W, POA1K, POA80, TALW, VATT = [RT[i] for i in range(14)]
SCOT_ROWS = [('Starter rate', 0.19, 0, 2827), ('Basic rate', 0.20, 2827, 14921), ('Intermediate rate', 0.21, 14921, 31092),
             ('Higher rate', 0.42, 31092, 62430), ('Advanced rate', 0.45, 62430, 125140), ('Top rate', 0.48, 125140, None)]


def line(r, lab, f, fmt=GBP2, note='', bold=False, bg=None):
    B.fx(ws, r, 2, lab, None, bold, bg, 'left', 4)
    B.fx(ws, r, 6, f, fmt, bold, bg)
    B.fx(ws, r, 8, note, None, False, bg, 'left', color=MUTED, size=8.5)
    ws.cell(r, 8).alignment = Alignment(wrap_text=True, vertical='center', indent=1)
    if len(note) > 60: ws.row_dimensions[r].height = 32


B.section(ws, 7, 2, '1 · Your income', 5)
line(8, 'Self-employment taxable profit (box 31 short / box 76 full)', f'={PROFIT}', note='From the SA103 Boxes tab.')
line(9, 'Employment pay (Settings)', f'=N({EMP})', note='From a job, if any. Tax on it is taken off below.')
line(10, 'Total income', '=F8+F9', bold=True)
line(11, 'Personal Allowance', f'=MAX(0,{PA_}-INT(MAX(0,F10-{PAL})/2))', note='£12,570, reduced by £1 for every £2 of income over £100,000.')
line(12, 'Taxable income', '=MAX(0,F10-F11)', bold=True, bg=TINT)
B.section(ws, 14, 2, '2 · Income Tax', 3)
B.fx(ws, 14, 6, f'=IF({SCOT}="Yes","Using: Scotland","Using: England, Wales, NI")', None, True, WHITE, 'right', color=DSAGE)
for j, (h, a) in enumerate([('BAND (ENGLAND, WALES, NI)', 'left'), ('RATE', 'right'), ('FROM', 'right'), ('TO', 'right'), ('TAX', 'right')]):
    B.th(ws, 15, 2 + j, h, align=a)
ruk = [('Basic rate', 0.20, '0', BB), ('Higher rate', 0.40, BB, HL), ('Additional rate', 0.45, HL, None)]
for i, (lab, rate, lo, hi) in enumerate(ruk):
    r = 16 + i
    B.fx(ws, r, 2, lab, None, False, None, 'left'); B.fx(ws, r, 3, rate, '0%')
    B.fx(ws, r, 4, f'={lo}', GBP); B.fx(ws, r, 5, f'={hi}' if hi else 'and above', GBP)
    upper = f'MIN($F$12,{hi})' if hi else '$F$12'
    B.fx(ws, r, 6, f'=IF({SCOT}="Yes",0,MAX(0,{upper}-D{r})*C{r})', GBP2)
for j, (h, a) in enumerate([('BAND (SCOTLAND, 2025/26)', 'left'), ('RATE', 'right'), ('FROM', 'right'), ('TO', 'right'), ('TAX', 'right')]):
    B.th(ws, 20, 2 + j, h, align=a)
for i, (lab, rate, lo, hi) in enumerate(SCOT_ROWS):
    r = 21 + i
    B.fx(ws, r, 2, lab, None, False, None, 'left'); B.fx(ws, r, 3, rate, '0%')
    B.fx(ws, r, 4, lo, GBP); B.fx(ws, r, 5, hi if hi else 'and above', GBP)
    upper = f'MIN($F$12,E{r})' if hi else '$F$12'
    B.fx(ws, r, 6, f'=IF({SCOT}="Yes",MAX(0,{upper}-D{r})*C{r},0)', GBP2)
B.fx(ws, 15, 8, 'Bands are on taxable income (after the Personal Allowance). Scottish bands: gov.uk Income Tax rates, Scotland 2025 to 2026. '
     'Scottish rates apply to earnings and profit only; National Insurance is the same everywhere.', None, False, WHITE, 'left', color=MUTED, size=8.5)
ws.merge_cells('H15:H24'); ws['H15'].alignment = Alignment(wrap_text=True, vertical='top', indent=1)
line(28, 'Income Tax on all your income', f'=ROUND(IF({SCOT}="Yes",SUM(F21:F26),SUM(F16:F18)),2)', bold=True)
line(29, 'Less: tax already taken off your pay (Settings)', f'=-N({PAYE})')
line(30, 'Income Tax to pay through Self Assessment', '=MAX(0,F28+F29)', bold=True, bg=TINT, note='If your job overpaid, HMRC may refund: this estimate shows 0.')
B.section(ws, 32, 2, '3 · National Insurance', 5)
line(33, 'Class 4 at 6% on profit between £12,570 and £50,270', f'=ROUND(MAX(0,MIN(F8,{UPL})-{LPL})*{C4M},2)')
line(34, 'Class 4 at 2% on profit above £50,270', f'=ROUND(MAX(0,F8-{UPL})*{C4A},2)')
line(35, 'Class 4 National Insurance', '=F33+F34', bold=True, bg=TINT)
line(36, 'Class 2 National Insurance (voluntary only)', f'=IF(AND({C2VOL}="Yes",F8<{SPT}),{C2W}*52,0)',
     note='Since April 2024 nobody has to pay Class 2. Profit of £6,845+ counts as paid; under that you can choose to pay £3.50 a week.')
B.section(ws, 38, 2, '4 · What you pay, and when', 5)
line(39, 'Your 2025/26 Self Assessment bill', '=F30+F35+F36', bold=True, note='Income Tax + Class 4 + Class 2.')
line(40, 'Payments on account for 2026/27 needed?',
     f'=IF(F30+F35<{POA1K},"No: bill under £1,000",IF(N({PAYE})>{POA80}*(F28+F35),"No: over 80% paid at source","Yes"))', None,
     note='Due unless the bill is under £1,000 or more than 80% of your tax was taken at source (for example through PAYE).')
ws['F40'].alignment = Alignment(horizontal='right', vertical='center', indent=1)
line(41, 'Each payment on account (half of Income Tax + Class 4)', '=IF(F40="Yes",ROUNDDOWN((F30+F35)/2,2),0)')
line(42, 'Less: payments on account already paid for 2025/26', f'=-N({POAPAID})', note='Settings. These were due 31 Jan 2026 and 31 Jul 2026.')
line(43, 'Balancing payment for 2025/26', '=F39+F42', bold=True)
line(44, 'TOTAL TO PAY BY 31 JANUARY 2027', '=MAX(0,F43+F41)', bold=True, bg=GOLDT, note='Balancing payment + 1st payment on account for 2026/27.')
line(45, 'To pay by 31 July 2027', '=F41', bold=True, bg=GOLDT, note='2nd payment on account for 2026/27.')
B.tip(ws, 47, 2, 'An estimate for planning, not tax advice. It does not cover student loan repayments, savings or dividend income, pension or Gift Aid relief, '
      'Marriage Allowance, High Income Child Benefit Charge, losses or capital allowances. HMRC\'s own calculation when you file is the one that counts.', 7, 1, 46)
B.tip(ws, 49, 2, 'Payments on account: each one is half of last year\'s bill (Income Tax and Class 4, not Class 2). gov.uk/understand-self-assessment-bill/payments-on-account', 7, 1, 26)
TE_IT, TE_ITTOT, TE_C4, TE_C2, TE_BILL, TE_POA, TE_BAL, TE_JAN, TE_JUL, TE_POAQ = [f'{TE}!$F${r}' for r in (30, 28, 35, 36, 39, 41, 43, 44, 45, 40)]
B.protect(ws)

# ================================================================== Tax Pot 26-27
ws = S['Tax Pot 26-27']
B.page(ws, 'Tax pot 2026/27', 'Set money aside every month so 31 Jan 2027, 31 Jul 2027 and next year\'s bill are never a shock.',
       {2: 14, 3: 15, 4: 15, 5: 15, 6: 15, 7: 15, 8: 3, 9: 46, 10: 16}, ncols=9, nrows=50)
B.section(ws, 7, 2, 'Your monthly plan (6 Apr 2026 to 5 Apr 2027)', 6)
for j, (h, a) in enumerate([('MONTH', 'left'), ('PROFIT THIS MONTH', 'right'), ('SET ASIDE (PLAN)', 'right'), ('MOVED TO POT', 'right'),
                            ('PAID TO HMRC', 'right'), ('POT BALANCE', 'right')]):
    B.th(ws, 8, 2 + j, h, align=a)
pprof = [2850, 3100, 2600, 3300, 2750, 2900, 3050]
for i in range(12):
    r = 9 + i
    y, m = 2026 + (3 + i) // 12, (3 + i) % 12 + 1
    B.fx(ws, r, 2, dt.date(y, m, 1), 'mmm yyyy', True, align='left')
    B.inp(ws, r, 3, pprof[i] if i < len(pprof) else None, '#,##0', 'right')
    B.fx(ws, r, 4, f'=IF(C{r}="","",MAX(0,C{r})*$J$9)', '#,##0')
    B.inp(ws, r, 5, round(pprof[i] * 0.25) if i < len(pprof) else None, '#,##0', 'right')
    B.inp(ws, r, 6, None, '#,##0', 'right')
    B.fx(ws, r, 7, f'=IF(AND(E{r}="",F{r}=""),"",$J$10+SUM($E$9:E{r})-SUM($F$9:F{r}))', '#,##0')
B.fx(ws, 21, 2, 'Total', bold=True, bg=TINT, align='left')
for c in range(3, 7):
    B.fx(ws, 21, c, f'=SUM({L(c)}9:{L(c)}20)', GBP, True, TINT)
B.fx(ws, 21, 7, '=$J$10+E21-F21', GBP, True, TINT)
# right panel
B.th(ws, 8, 9, 'YOUR SETTINGS'); B.th(ws, 8, 10, '', align='right')
B.text(ws, 9, 9, 'Set-aside % of each month\'s profit', 10, True); B.inp(ws, 9, 10, 0.25, '0%', 'right', keep=True)
B.text(ws, 10, 9, 'Already in your tax pot on 6 Apr 2026', 10, True); B.inp(ws, 10, 10, 3000, GBP, 'right')
B.text(ws, 11, 9, 'Suggested % (your 2025/26 bill ÷ profit)', 10, False, MUTED)
B.fx(ws, 11, 10, f'=IF(N({PROFIT})=0,"–",{TE_BILL}/{PROFIT})', '0%', True, WHITE)
B.th(ws, 13, 9, 'BILLS TO SAVE FOR'); B.th(ws, 13, 10, 'AMOUNT', align='right')
B.fx(ws, 14, 9, '31 Jan 2027: balance + 1st payment on account', None, False, WHITE, 'left'); B.fx(ws, 14, 10, f'={TE_JAN}', GBP, True, WHITE)
B.fx(ws, 15, 9, '31 Jul 2027: 2nd payment on account', None, False, WHITE, 'left'); B.fx(ws, 15, 10, f'={TE_JUL}', GBP, True, WHITE)
B.fx(ws, 16, 9, '31 Jan 2028: 2026/27 balance (estimate, see below)', None, False, WHITE, 'left')
B.fx(ws, 16, 10, '=G42', GBP, True, WHITE)
B.fx(ws, 17, 9, 'Pot top-up at your set-aside % (full year, not a bill)', None, False, None, 'left', color=MUTED, size=9)
B.fx(ws, 17, 10, '=G29*J9', GBP, False, None, color=MUTED, size=9)
B.th(ws, 18, 9, 'WHERE YOU STAND'); B.th(ws, 18, 10, '', align='right')
B.fx(ws, 19, 9, 'Pot balance now', None, True, TINT, 'left'); B.fx(ws, 19, 10, '=G21', GBP, True, TINT)
B.fx(ws, 20, 9, '=IF(J14=0,"Fill in the Income Log first",IF(J19>=J14,"Covers 31 Jan 2027 with spare","Short for 31 Jan 2027 by"))', None, True, WHITE, 'left')
B.fx(ws, 20, 10, '=IF(J14=0,"",IF(J19>=J14,J19-J14,J14-J19))', GBP, True, WHITE)
ML_ = 'MAX(1,(2027-YEAR(TODAY()))*12+1-MONTH(TODAY())+1)'
B.fx(ws, 21, 9, '=IF(TODAY()>DATE(2027,1,31),"31 Jan 2027 has passed","Save each month until 31 Jan 2027")', None, True, WHITE, 'left')
B.fx(ws, 21, 10, f'=IF(TODAY()>DATE(2027,1,31),0,MAX(0,J14-J19)/{ML_})', GBP, True, WHITE)
B.fx(ws, 22, 9, 'Then save each month for 31 Jul 2027', None, True, WHITE, 'left')
B.fx(ws, 22, 10, f'=MAX(0,J15-MAX(0,J19-J14))/6', GBP, True, WHITE)
B.tip(ws, 24, 2, 'How it works: each month, move the set-aside amount into a separate savings account (your tax pot) and type what you moved. '
      'When you pay HMRC, type it under "Paid to HMRC" and the pot balance drops. Not sure what % to use? Start with the suggested % '
      '(your 2025/26 bill as a share of profit). 2026/27 rates checked on gov.uk: Personal Allowance £12,570 and Class 4 at 6% / 2% are unchanged; '
      'the car mileage rate rises to 55p for the first 10,000 miles.', 9, 1, 60)
B.tip(ws, 26, 2, 'Planning tool, not tax advice. Payments on account can be reduced if you expect a lower 2026/27 profit: ask HMRC or your accountant before you do.', 9, 1, 26)
# ---- 2026/27 bill estimate (same logic as Tax Estimate, 2026/27 rates)
B.section(ws, 28, 2, 'How the 31 Jan 2028 estimate is worked out (2026/27 rates)', 6)
SC27 = [(0.19, 0, 3967), (0.20, 3967, 16956), (0.21, 16956, 31092), (0.42, 31092, 62430), (0.45, 62430, 125140), (0.48, 125140, None)]
scot27 = '+'.join(f'MAX(0,{f"MIN(G33,{hi})" if hi else "G33"}-{lo})*{rt}' for rt, lo, hi in SC27)
ruk27 = 'MIN(G33,37700)*0.2+MAX(0,MIN(G33,125140)-37700)*0.4+MAX(0,G33-125140)*0.45'
rows27 = [(29, 'Projected 2026/27 profit (average month so far x 12)', '=IF(COUNT(C9:C20)=0,0,SUM(C9:C20)/COUNT(C9:C20)*12)', 'From the Profit column above.'),
          (30, 'Employment pay (assumed same as 2025/26, Settings)', f'=N({EMP})', ''),
          (31, 'Total income', '=G29+G30', ''),
          (32, 'Personal Allowance (£12,570, tapered over £100,000)', '=MAX(0,12570-INT(MAX(0,G31-100000)/2))', ''),
          (33, 'Taxable income', '=MAX(0,G31-G32)', ''),
          (34, 'Income Tax on all income', f'=ROUND(IF({SCOT}="Yes",{scot27},{ruk27}),2)', 'England, Wales, NI 20/40/45% or Scottish 2026/27 bands, per Settings.'),
          (35, 'Less: tax taken off your pay (assumed same as 2025/26)', f'=-N({PAYE})', ''),
          (36, 'Income Tax to pay through Self Assessment', '=MAX(0,G34+G35)', ''),
          (37, 'Class 4 NI (6% from £12,570 to £50,270, 2% above)', '=ROUND(MAX(0,MIN(G29,50270)-12570)*0.06,2)+ROUND(MAX(0,G29-50270)*0.02,2)', ''),
          (38, 'Class 2 NI (voluntary, only if profit under £7,105)', f'=IF(AND({C2VOL}="Yes",G29<7105),3.65*52,0)', ''),
          (39, 'Estimated 2026/27 bill', '=G36+G37+G38', ''),
          (40, 'Less: 1st payment on account (31 Jan 2027)', f'=-{TE_POA}', ''),
          (41, 'Less: 2nd payment on account (31 Jul 2027)', f'=-{TE_POA}', ''),
          (42, 'Balancing payment due 31 Jan 2028', '=MAX(0,G39+G40+G41)', 'If negative, HMRC would owe you: shown as 0.')]
for r, lab, f, note in rows27:
    bold = r in (31, 33, 39, 42)
    bg = TINT if r == 42 else None
    B.fx(ws, r, 2, lab, None, bold, bg, 'left', 5); B.fx(ws, r, 7, f, GBP2, bold, bg)
    B.fx(ws, r, 9, note, None, False, bg, 'left', color=MUTED, size=8.5)
B.tip(ws, 44, 2, '2026/27 rates checked on gov.uk (Nov 2026): Personal Allowance £12,570, basic rate band £37,700, higher rate to £125,140, '
      'Class 4 at 6% / 2% between £12,570 and £50,270 are all unchanged from 2025/26. Scottish bands changed (starter to £3,967, basic to £16,956). '
      'Class 2 voluntary: £3.65 a week, threshold £7,105.', 9, 1, 40)
B.protect(ws)

# ================================================================== Deadlines
ws = S['Deadlines']
B.page(ws, 'Deadlines and checklist', 'Tick each one off. The Dashboard shows your next 3 steps from this list.',
       {2: 14, 3: 52, 4: 16, 5: 14, 6: 13, 7: 46, 8: 6}, ncols=7, nrows=40)
for j, (h, a) in enumerate([('DATE', 'left'), ('WHAT TO DO', 'left'), ('TYPE', 'left'), ('DONE?', 'left'), ('DAYS LEFT', 'right'), ('GOOD TO KNOW', 'left')]):
    B.th(ws, 8, 2 + j, h, align=a)
DLS = [(None, 'Fill in Settings (2 minutes)', 'Your step', 'Done', 'Scottish taxpayer? Other job? Trading allowance?'),
       (None, 'Not registered yet? Register for Self Assessment now (the 5 Oct 2026 deadline has passed; you can still file)', 'HMRC rule', 'Done',
        'Register at gov.uk. HMRC then gives you 3 months from its letter to file, but the tax is still due 31 Jan 2027. Already registered? Pick "Not needed".'),
       (None, 'Type every 2025/26 payment into the Income Log', 'Your step', 'Done', '6 Apr 2025 to 5 Apr 2026, date the money arrived.'),
       (None, 'Type every 2025/26 cost into Expenses, Mileage and Use of Home', 'Your step', 'Done', 'Bank statements make this quick.'),
       (dt.date(2026, 10, 31), 'Paper return deadline (passed: file online instead)', 'HMRC deadline', 'Not needed', 'Filing online? Leave it as "Not needed".'),
       (None, 'Check your figures on the SA103 Boxes tab', 'Your step', 'Not yet', 'Look for ✕ rows in the logs first.'),
       (None, 'Find your UTR and sign in to your HMRC online account', 'Your step', 'Not yet', 'UTR is on HMRC letters. Allow time for activation codes by post.'),
       (dt.date(2027, 1, 31), 'File your 2025/26 return online', 'HMRC deadline', 'Not yet', 'By 11:59pm. Late filing means a penalty.'),
       (dt.date(2027, 1, 31), 'Pay the 2025/26 balance + 1st payment on account for 2026/27', 'HMRC deadline', 'Not yet', 'Amount: see the Dashboard or Tax Estimate.'),
       (None, 'Each month: move money into your tax pot', 'Your step', 'Not yet', 'Tax Pot 26-27 tab shows how much.'),
       (dt.date(2027, 7, 31), 'Pay the 2nd payment on account for 2026/27', 'HMRC deadline', 'Not yet', 'Half of your 2025/26 bill, if payments on account apply.'),
       (dt.date(2032, 1, 31), 'Keep your 2025/26 records until at least this date', 'HMRC rule', 'Not yet',
        'At least 5 years after the 31 Jan 2027 deadline: receipts, invoices, bank statements, this file.')]
for i, (d0, task, typ, done, note) in enumerate(DLS):
    r = 9 + i
    B.fx(ws, r, 2, d0 if d0 else 'Now', DATE if d0 else None, True, None, 'left')
    B.fx(ws, r, 3, task, None, False, None, 'left'); ws.cell(r, 3).alignment = Alignment(wrap_text=True, vertical='center', indent=1)
    B.fx(ws, r, 4, typ, None, False, None, 'left', color=CORAL if typ != 'Your step' else DSAGE, size=9)
    B.inp(ws, r, 5, done, keep=(done == 'Not needed'))
    B.fx(ws, r, 6, f'=IF(OR(E{r}="Done",E{r}="Not needed"),"✓",IF(ISNUMBER(B{r}),IF(B{r}<TODAY(),"passed",B{r}-TODAY()),""))', '0', True)
    B.fx(ws, r, 7, note, None, False, None, 'left', color=MUTED, size=8.5); ws.cell(r, 7).alignment = Alignment(wrap_text=True, vertical='center', indent=1)
    B.text(ws, r, 9, f'=IF(OR(E{r}="Done",E{r}="Not needed"),"",SUMPRODUCT(($E$9:E{r}<>"Done")*($E$9:E{r}<>"Not needed")))', 8, False, 'C9C2B6')
    ws.row_dimensions[r].height = 46 if len(task) > 60 else 32
DL1, DL2 = 9, 9 + len(DLS) - 1
ws.column_dimensions['I'].hidden = True
B.dv(ws, f'E{DL1}:E{DL2}', ['Done', 'Not yet', 'Not needed'])
B.fx(ws, DL2 + 2, 2, f'="Done: "&COUNTIF(E{DL1}:E{DL2},"Done")+COUNTIF(E{DL1}:E{DL2},"Not needed")&" of {len(DLS)}"', None, True, TINT, 'left', 2)
B.fx(ws, DL2 + 2, 4, f'=REPT("█",COUNTIF(E{DL1}:E{DL2},"Done")+COUNTIF(E{DL1}:E{DL2},"Not needed"))&REPT("░",{len(DLS)}-COUNTIF(E{DL1}:E{DL2},"Done")-COUNTIF(E{DL1}:E{DL2},"Not needed"))',
     None, False, TINT, 'left', 2, DSAGE)
ws.conditional_formatting.add(f'F{DL1}:F{DL2}', FormulaRule(formula=[f'F{DL1}="passed"'], font=Font(name=FONT, color=CORAL, bold=True)))
B.tip(ws, DL2 + 4, 2, 'Dates from gov.uk: register by 5 October, paper return by 31 October, online return and payment by 31 January, '
      'payments on account 31 January and 31 July, records kept at least 5 years after the 31 January deadline. "Now" items are your own steps.', 6, 1, 40)
B.protect(ws)

# ================================================================== Start Here
ws = S['Start Here']
B.page(ws, 'Start here', 'Your 2025/26 self-employed tax return, step by step. No jargon, no formulas to touch.', {2: 7, 3: 92, 4: 3}, ncols=3, nrows=50)
B.box(ws, 7, 2, 7, 3, GOLDT, GOLDT)
B.text(ws, 7, 2, '=IF(Settings!$C$7="","Two files: EXAMPLE (filled in) shows a finished year for a made-up designer, Sam. BLANK (start here) is yours. Type your own numbers in the BLANK file.",'
       '"You are looking at the EXAMPLE file: a made-up designer, Sam, so you can see every tab working. Open the BLANK (start here) file for your own numbers.")',
       10, True, '6B5B45', w=2, indent=1)
ws.row_dimensions[7].height = 40
steps = [('1', 'Settings. Pick your answers in the yellow boxes: cash basis or traditional, the £1,000 trading allowance (Yes only if your costs were tiny), '
               'Scottish taxpayer, and any job pay from your P60.'),
         ('2', 'Income Log. One row for every payment your business received from 6 April 2025 to 5 April 2026. Check column shows ✓ when a row counts.'),
         ('3', 'Expenses Log, Mileage, Use of Home. Every business cost, with its HMRC category from the dropdown. Business journeys by car on Mileage, '
               'hours worked at home on Use of Home. The flat rates are worked out for you.'),
         ('4', 'SA103 Boxes and Tax Estimate. See each figure next to its official box number (short or full form) and your estimated Income Tax, '
               'Class 4 National Insurance and what to pay on 31 Jan 2027 and 31 Jul 2027.'),
         ('5', 'File and pay by 31 January 2027. Copy the figures into your return at gov.uk, pay HMRC, tick off the Deadlines tab, '
               'then use Tax Pot 26-27 to set money aside each month for next time.')]
for i, (n, t) in enumerate(steps):
    r = 9 + i * 2
    B.box(ws, r, 2, r, 3); B.text(ws, r, 2, n, 18, True, GOLD, align='center'); B.text(ws, r, 3, t, 10.5, indent=1)
    ws.row_dimensions[r].height = 46; ws.row_dimensions[r + 1].height = 6
B.tip(ws, 20, 2, 'Colours: pale yellow = type here. White = worked out for you (locked so nothing breaks; Review > Unprotect Sheet, no password). '
      '✕ in a Check column = a row that is not counted yet. Dates in the logs must be inside 6 Apr 2025 to 5 Apr 2026.', 2, 1, 44)
B.tip(ws, 22, 2, 'Google Sheets: upload the .xlsx to Google Drive, open it, choose File > Save as Google Sheets, then move between tabs with the tab bar '
      'along the bottom of the screen. Works in Excel 2016 and later, Excel for Mac, Excel online and Google Sheets.', 2, 1, 44)
B.tip(ws, 24, 2, 'Not tax advice. This kit helps you organise your numbers and estimate your bill. It does not file your return or talk to HMRC. '
      'If your situation is not simple (losses, capital allowances, partnerships, CIS, property income), speak to an accountant. '
      'Questions about the kit: joel@wayofwealthcoaching.com', 2, 1, 52)
B.text(ws, 26, 2, 'Way of Wealth Studio', 9, True, GOLD, w=2)
B.protect(ws)

# ================================================================== Dashboard
ws = S['Dashboard']
B.page(ws, 'UK Self Assessment 2025/26', '', ncols=16, nrows=110)
ws['B3'] = f'=IF({NAME}="","Your Deadline Kit",{NAME})&"  ·  tax year 6 Apr 2025 to 5 Apr 2026  ·  file and pay by 31 Jan 2027  ·  "&IF({SCOT}="Yes","Scottish bands","England, Wales, NI bands")'
ws['B3'].font = F(10, color=MUTED)
for r, h in [(7, 22), (8, 30), (9, 18), (10, 8), (11, 22), (12, 30), (13, 18)]:
    ws.row_dimensions[r].height = h
B.hero(ws, 7, 2, 7, 7, 'TOTAL TO PAY BY 31 JANUARY 2027', f'={TE_JAN}',
       f'=IF({TURN}+{OTHER}=0,"Fill in Settings and the Income Log to see your bill.","2025/26 balance "&TEXT({TE_BAL},"£#,##0")&" + first payment on account "&TEXT({TE_POA},"£#,##0")&". Then "&TEXT({TE_JUL},"£#,##0")&" on 31 July 2027.")',
       'Estimate, not tax advice. HMRC\'s calculation is final.', value_fmt='£#,##0')
B.kpi(ws, 7, 10, 'DAYS TO 31 JAN 2027', '=MAX(0,DATE(2027,1,31)-TODAY())', '=IF(TODAY()>DATE(2027,1,31),"deadline passed","to file online and pay")', value_fmt='0', accent=CORAL)
B.kpi(ws, 7, 14, 'TAXABLE PROFIT', f'={PROFIT}', f'="box 31 short / box 76 full"', value_fmt='£#,##0', accent=DSAGE)
B.kpi(ws, 11, 10, 'INCOME TAX', f'={TE_IT}', f'=IF({SCOT}="Yes","Scottish bands","England, Wales, NI bands")', value_fmt='£#,##0', accent=GOLD)
B.kpi(ws, 11, 14, 'CLASS 4 NI', f'={TE_C4}', '="6% / 2% on profit"', value_fmt='£#,##0', accent=GOLD)
# next steps box
B.box(ws, 15, 2, 19, 16, TINT, TINT)
B.text(ws, 15, 2, 'YOUR NEXT 3 STEPS', 8, True, DSAGE, w=4, indent=1)
B.text(ws, 15, 6, f'=IF({INC_X}+{EXP_X}+{MIL_X}>0,"Check: "&({INC_X}+{EXP_X}+{MIL_X})&" row(s) in your logs show ✕ (not counted)","")', 9, True, CORAL, w=11, align='right')
for k in range(3):
    r = 16 + k
    f = (f'=IFERROR("{k + 1}.  "&INDEX({DL}!$C$9:$C$30,MATCH({k + 1},{DL}!$I$9:$I$30,0))&IF(ISNUMBER(INDEX({DL}!$B$9:$B$30,MATCH({k + 1},{DL}!$I$9:$I$30,0))),'
         f'"  ·  by "&TEXT(INDEX({DL}!$B$9:$B$30,MATCH({k + 1},{DL}!$I$9:$I$30,0)),"d mmm yyyy"),""),IF({k}=0,"All done. Set money aside in the Tax Pot each month.",""))')
    B.text(ws, r, 2, f, 10.5, k == 0, CHAR, w=15, indent=2)
    ws.row_dimensions[r].height = 22
ws.row_dimensions[19].height = 8
for r, h in [(21, 22), (22, 30), (23, 18)]:
    ws.row_dimensions[r].height = h
B.kpi(ws, 21, 2, 'TURNOVER', f'={TURN}+{OTHER}', '="money in, 2025/26"', value_fmt='£#,##0')
B.kpi(ws, 21, 6, 'ALLOWABLE EXPENSES', f'={EXPT}+{TAUSED}', f'=IF({TA}="Yes","£1,000 trading allowance","incl. mileage and use of home")', value_fmt='£#,##0')
B.kpi(ws, 21, 10, 'DUE 31 JULY 2027', f'={TE_JUL}', f'=IF({TE_POAQ}="Yes","2nd payment on account",{TE_POAQ})', value_fmt='£#,##0')
B.kpi(ws, 21, 14, 'FORM TO USE', f'=IF({TURN}+{OTHER}>=90000,"SA103F","SA103S")', f'=IF({TURN}+{OTHER}>=90000,"full: turnover £90k+","short: turnover under £90k")')
# chart data
D0 = 80
B.section(ws, D0, 2, 'The numbers behind the charts', 10)
B.th(ws, D0 + 1, 2, 'MONTH', 2); B.th(ws, D0 + 1, 4, 'Income', 2, 'right'); B.th(ws, D0 + 1, 6, 'Expenses', 2, 'right')
for i in range(12):
    r = D0 + 2 + i
    y, m = 2025 + (3 + i) // 12, (3 + i) % 12 + 1
    lo = YS if i == 0 else f'DATE({y},{m},1)'
    hi = YE if i == 11 else f'DATE({y},{m + 1},1)-1'
    B.fx(ws, r, 2, dt.date(y, m, 1).strftime('%b %y'), None, True, align='left', w=2)
    B.fx(ws, r, 4, f'=SUMIFS({IL}!$E${IR1}:$E${IR2},{IL}!$B${IR1}:$B${IR2},">="&{lo},{IL}!$B${IR1}:$B${IR2},"<="&{hi},{IL}!$F${IR1}:$F${IR2},"<>")', GBP, w=2)
    ex = (f'SUMIFS({EL}!$H${ER1}:$H${ER2},{EL}!$B${ER1}:$B${ER2},">="&{lo},{EL}!$B${ER1}:$B${ER2},"<="&{hi},{EL}!$F${ER1}:$F${ER2},"<>")'
          f'+SUMIFS({ML}!$F${MR1}:$F${MR2},{ML}!$B${MR1}:$B${MR2},">="&{lo},{ML}!$B${MR1}:$B${MR2},"<="&{hi})+N({UH}!$D${9 + i})')
    B.fx(ws, r, 6, f'=IF({TA}="Yes",0,{ex})', GBP, w=2)
B.th(ws, D0 + 1, 9, 'EXPENSE CATEGORY', 3); B.th(ws, D0 + 1, 12, 'Allowable', 2, 'right')
for i, c in enumerate(CATS):
    r = D0 + 2 + i
    B.fx(ws, r, 9, c[1], align='left', w=3); B.fx(ws, r, 12, f'={BX}!$D${FROW[str(c[2])]}', GBP, w=2)
TB = D0 + 16
B.th(ws, TB, 2, 'TAX BILL', 2); B.th(ws, TB, 4, '2025/26', 2, 'right')
for i, (lab, ref) in enumerate([('Income Tax', TE_IT), ('Class 4 NI', TE_C4), ('Class 2 NI', TE_C2)]):
    B.fx(ws, TB + 1 + i, 2, lab, align='left', w=2); B.fx(ws, TB + 1 + i, 4, f'={ref}', GBP2, w=2)
B.th(ws, TB, 9, 'PAYMENT DATE', 3); B.th(ws, TB, 12, '2025/26 balance', 2, 'right'); B.th(ws, TB, 14, 'Payment on account', 2, 'right')
B.fx(ws, TB + 1, 9, '31 Jan 2027', align='left', w=3); B.fx(ws, TB + 1, 12, f'=MAX(0,{TE_BAL})', GBP, w=2); B.fx(ws, TB + 1, 14, f'={TE_POA}', GBP, w=2)
B.fx(ws, TB + 2, 9, '31 Jul 2027', align='left', w=3); B.fx(ws, TB + 2, 12, 0, GBP, w=2); B.fx(ws, TB + 2, 14, f'={TE_JUL}', GBP, w=2)
PB = TB + 6
B.th(ws, PB, 2, 'MONTH', 2); B.th(ws, PB, 4, 'Tax pot', 2, 'right'); B.th(ws, PB, 6, 'Bill due 31 Jan 2027', 2, 'right')
for i in range(12):
    r = PB + 1 + i
    y, m = 2026 + (3 + i) // 12, (3 + i) % 12 + 1
    B.fx(ws, r, 2, dt.date(y, m, 1).strftime('%b %y'), None, True, align='left', w=2)
    B.fx(ws, r, 4, f'=IF({TP}!G{9 + i}="",' + (f'D{r - 1}' if i else f'N({TP}!$J$10)') + f',{TP}!G{9 + i})', GBP, w=2)
    B.fx(ws, r, 6, f'={TE_JAN}', GBP, w=2)
cats = Reference(ws, min_col=2, min_row=D0 + 2, max_row=D0 + 13)
bar_chart(ws, 'B25', 'Money in vs costs, 2025/26', cats, Reference(ws, min_col=4, max_col=4, min_row=D0 + 1, max_row=D0 + 13),
          w=11.8, h=7.4, colors=[DSAGE])
ch = ws._charts[-1]
ch2 = BarChart(); ch2.add_data(Reference(ws, min_col=6, min_row=D0 + 1, max_row=D0 + 13), titles_from_data=True)
s2 = ch2.series[0]; s2.graphicalProperties.solidFill = GOLD; s2.graphicalProperties.line.solidFill = GOLD
ch.series.append(s2); ch.gapWidth = 40
ch.series[0].tx = SeriesLabel(v='Income'); ch.series[1].tx = SeriesLabel(v='Expenses')
bar_chart(ws, 'J25', 'Expenses by HMRC category', Reference(ws, min_col=9, min_row=D0 + 2, max_row=D0 + 12),
          Reference(ws, min_col=12, min_row=D0 + 1, max_row=D0 + 12), w=11.8, h=7.4, horizontal=True, legend=False, colors=[DSAGE])
doughnut(ws, 'B41', 'Your 2025/26 tax bill', Reference(ws, min_col=2, min_row=TB + 1, max_row=TB + 3),
         Reference(ws, min_col=4, min_row=TB, max_row=TB + 3), w=11.8, h=7.4, colors=[CHAR, GOLD, SAGE])
bar_chart(ws, 'J41', 'What you pay, and when', Reference(ws, min_col=9, min_row=TB + 1, max_row=TB + 2),
          Reference(ws, min_col=12, max_col=15, min_row=TB, max_row=TB + 2), w=11.8, h=7.4, stacked=True, colors=[CHAR, GOLD])
pay = ws._charts[-1]
# columns 12-15 include merged spacer columns: keep only real series
pay.series = [s for s in pay.series if s.tx and s.tx.strRef and s.tx.strRef.f.split('!')[-1].replace('$', '')[0] in ('L', 'N')]
for s_, col in zip(pay.series, [CHAR, GOLD]):
    s_.graphicalProperties.solidFill = col; s_.graphicalProperties.line.solidFill = col
cats2 = Reference(ws, min_col=2, min_row=PB + 1, max_row=PB + 12)
line_chart(ws, 'B57', 'Tax pot vs 31 Jan 2027 bill', cats2,
           [Reference(ws, min_col=4, min_row=PB, max_row=PB + 12), Reference(ws, min_col=6, min_row=PB, max_row=PB + 12)], w=11.8, h=7.4, colors=[DSAGE, CORAL])
B.section(ws, 57, 10, 'Key dates', 7)
B.th(ws, 58, 10, 'DATE', 2); B.th(ws, 58, 12, 'WHAT', 5)
for i, (dd, t) in enumerate([('5 Oct 2026', 'Register deadline (passed: register now)'), ('31 Oct 2026', 'Paper return deadline (passed)'),
                             ('31 Jan 2027', 'File online, pay balance + 1st payment'),
                             ('31 Jul 2027', '2nd payment on account for 2026/27'), ('31 Jan 2032', 'Keep 2025/26 records until at least')]):
    r = 59 + i
    B.fx(ws, r, 10, dd, None, True, None, 'left', 2); B.fx(ws, r, 12, t, None, False, None, 'left', 5)
B.text(ws, 65, 10, 'Not tax advice. This kit does not file your return. Way of Wealth Studio · joel@wayofwealthcoaching.com', 8.5, False, MUTED, w=7, h=2)
for c in ws._charts:
    c.roundedCorners = False
    if c.legend is not None: c.legend.overlay = False
B.protect(ws)

for w_ in B.wb.worksheets:
    for c in w_._charts:
        c.roundedCorners = False

# ================================================================== save (skin save, then long tabs paginate)
AREAS = {'Dashboard': 'A1:R74', 'Income Log': f'A1:H{T1 + 5}', 'Expenses Log': f'A1:J{T2 + 4}', 'Mileage': f'A1:K{T3 + 3}',
         'SA103 Boxes': f'A1:G{endr + 3}', 'Tax Estimate': f'A1:I{RT0 + 2 + len(RATES)}', 'Start Here': 'A1:E27', 'Settings': 'A1:F19',
         'Use of Home': 'A1:I24', 'Tax Pot 26-27': 'A1:K45', 'Deadlines': f'A1:H{DL2 + 5}'}
orig_save = B.wb.save
B.wb.save = lambda p: None
B.save(OUT, AREAS)
for t in ('Income Log', 'Expenses Log', 'Mileage'):
    S[t].page_setup.fitToHeight = 0
    S[t].page_setup.orientation = 'portrait'
    S[t].print_title_rows = '8:8'
for w_ in B.wb.worksheets:
    w_.oddFooter.center.text = 'Way of Wealth Studio  ·  UK Self Assessment 2025/26 Deadline Kit  ·  not tax advice'
    w_.oddFooter.center.size = 8
B.wb.active = 1 if BLANK else 0
if BLANK:
    for _w in B.wb.worksheets: _w.sheet_view.tabSelected = False
    B.wb.worksheets[1].sheet_view.tabSelected = True
orig_save(OUT)
print('saved', OUT)
