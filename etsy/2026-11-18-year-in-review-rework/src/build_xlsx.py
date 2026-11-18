"""Couples Money Year in Review and 2027 Goals (rework, 18 Nov 2026) - Way of Wealth Studio.
Cells-only app skin (etsy/lib/skin.py), Google Sheets safe: no shapes, no data bars, no icon sets, no internal links.
Whole year look-back (Jan-Dec) + 2027 goals + 12 monthly check-ins + the Monthly Money Check-in (behaviour layer).
python3 build_xlsx.py out/file.xlsx [blank]
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
import skin
from skin import *
from openpyxl.chart import Reference, BarChart
from openpyxl.chart.series import SeriesLabel
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Font, Alignment

CHAR = '3D3D3D'
skin.NAVY = CHAR
OUT = sys.argv[1]; BLANK = len(sys.argv) > 2 and sys.argv[2] == 'blank'
MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
SGN = '+#,##0;-#,##0;"–"'

TABS = [('Dashboard', GOLD), ('Start Here', GOLD), ('Settings', DSAGE), ('Year in Numbers', DSAGE), ('Spending Review', DSAGE),
        ('Net Worth', DSAGE), ('Year in Review', CHAR), ('2027 Goals', GOLD), ('2027 Check-ins', GOLD),
        ('Monthly Money Check-in', CORAL), ('Money Date', CHAR)]
B = Book(TABS, BLANK)
S = B.s
YN, SR, NW, YR, GL, CI, MC = ("'Year in Numbers'", "'Spending Review'", "'Net Worth'", "'Year in Review'", "'2027 Goals'",
                             "'2027 Check-ins'", "'Monthly Money Check-in'")
NA = 'IF(Settings!$C$7="","Partner A",Settings!$C$7)'
NB = 'IF(Settings!$C$8="","Partner B",Settings!$C$8)'
FMT = 'Settings!$G$7'          # TEXT() format built from the one currency cell
YEAR, GY = 'Settings!$C$10', 'Settings!$C$11'
M = lambda x: f'TEXT({x},{FMT})'   # money in plain words, buyer's currency
CATS = ['Home (rent or mortgage)', 'Bills and utilities', 'Groceries', 'Transport', 'Eating out and takeaway', 'Shopping',
        'Travel and holidays', 'Kids and pets', 'Gifts and celebrations', 'Health and fitness']
NC = len(CATS)


def bar_f(pct, color, n=12):
    """progress bar: real sparkline in Google Sheets, text bar in Excel / LibreOffice"""
    return (f'IFERROR(SPARKLINE(MAX(0,MIN(1,{pct})),{{"charttype","bar";"max",1;"color1","#{color}"}}),'
            f'REPT("█",ROUND(MAX(0,MIN(1,{pct}))*{n},0))&REPT("░",{n}-ROUND(MAX(0,MIN(1,{pct}))*{n},0)))')


# ================================================================== Settings
ws = S['Settings']
B.page(ws, 'Settings', 'Step 1: fill in the yellow boxes once. Every other tab updates on its own.', {2: 40, 3: 26, 4: 3, 5: 62}, ncols=5, nrows=40)
B.th(ws, 6, 2, 'ABOUT YOU'); B.th(ws, 6, 3, 'TYPE HERE'); B.th(ws, 6, 5, 'WHAT IT MEANS')
rows = [('Partner A name', 'Sam', None, False, 'Shown on the Dashboard and the check-in. Nothing is sent anywhere.'),
        ('Partner B name', 'Alex', None, False, 'Your partner. Use nicknames if you like.'),
        ('Your currency symbol', '$', '@', True, 'The ONE currency setting: $, £, €, A$, C$, R, kr, ₹ ... Every amount and sentence uses it.'),
        ('The year you are looking back on', 2026, '0', True, 'Your look-back year, January to December.'),
        ('Your goal year', '=IF(C10="","",C10+1)', '0', None, 'Worked out for you: the year after.')]
for i, (lab, v, fmt, keep, hlp) in enumerate(rows):
    r = 7 + i
    B.text(ws, r, 2, lab, 10, True)
    if keep is None:
        B.fx(ws, r, 3, v, fmt, True, WHITE, 'left')
    else:
        B.inp(ws, r, 3, v, fmt, keep=keep)
    B.text(ws, r, 5, hlp, 9, color=MUTED); ws.row_dimensions[r].height = 28
B.th(ws, 13, 2, 'SPENDING CATEGORIES'); B.th(ws, 13, 3, ''); B.th(ws, 13, 5, 'RENAME THEM TO FIT YOUR LIFE')
for i, c in enumerate(CATS):
    B.inp(ws, 14 + i, 2, c, keep=True)
    ws.row_dimensions[14 + i].height = 22
B.text(ws, 14, 5, 'Every tab, chart and the monthly summary uses these names. Keep 10 or fewer.', 9, color=MUTED, h=2)
B.tip(ws, 25, 2, 'Pale yellow = type here. White = worked out for you (locked so nothing breaks; Excel: Review > Unprotect Sheet, no password). '
      'Questions: joel@wayofwealthcoaching.com', 4, 1, 40)
# hidden lists
B.text(ws, 6, 7, 'LISTS', 7, True, 'B9B2A6')
ws['G7'] = '=""""&IF(C9="","",C9)&"""#,##0;-"""&IF(C9="","",C9)&"""#,##0"'
ws['H7'] = 'Both'; ws['H8'] = f'={NA}'; ws['H9'] = f'={NB}'
for i, m in enumerate(MONTHS):
    ws.cell(9 + i, 9, m)
for col in 'GHI':
    ws.column_dimensions[col].hidden = True
B.protect(ws)

# ================================================================== Year in Numbers (Jan-Dec look-back)
ws = S['Year in Numbers']
B.page(ws, 'Our year in numbers', '="Step 2, look back (1 of 3): every month of "&Settings!$C$10&", January to December. Rough numbers from your bank apps are fine."',
       {**{c: 12.5 for c in range(2, 12)}, 11: 15}, ncols=11, nrows=45)
heads = ['MONTH', f'={NA}&" income"', f'={NB}&" income"', 'Total income', 'Spending', 'Saved or invested', 'Extra debt paid', 'Left over',
         'Savings rate', 'How it felt']
for j, h in enumerate(heads):
    B.th(ws, 8, 2 + j, h, align='left' if j in (0, 9) else 'right')
inc_a = [3200, 3200, 3250, 3250, 3250, 3400, 3400, 3400, 3400, 3400, 3400, 3900]
inc_b = [2650, 2700, 2600, 2900, 2750, 2700, 2600, 2800, 3100, 2750, 2700, 2900]
spend = [4300, 4050, 4400, 4250, 4600, 4700, 5600, 5200, 4300, 4350, 4550, 5900]
saved = [800, 900, 700, 900, 650, 700, 300, 400, 900, 850, 800, 500]
debt = [300, 300, 300, 400, 300, 300, 100, 250, 400, 300, 300, 150]
felt = ['OK', 'Good', 'OK', 'Good', 'OK', 'OK', 'Tough', 'Tough', 'Good', 'Good', 'OK', 'Tough']
for i, m in enumerate(MONTHS):
    r = 9 + i
    B.fx(ws, r, 2, MON[i], None, True, align='left')
    B.inp(ws, r, 3, inc_a[i], MONEY, 'right'); B.inp(ws, r, 4, inc_b[i], MONEY, 'right')
    B.fx(ws, r, 5, f'=IF(COUNT(C{r}:D{r})=0,"",SUM(C{r}:D{r}))', MONEY, True)
    B.inp(ws, r, 6, spend[i], MONEY, 'right'); B.inp(ws, r, 7, saved[i], MONEY, 'right'); B.inp(ws, r, 8, debt[i], MONEY, 'right')
    B.fx(ws, r, 9, f'=IF(E{r}="","",E{r}-SUM(F{r}:H{r}))', SGN)
    B.fx(ws, r, 10, f'=IF(N(E{r})=0,"",G{r}/E{r})', PCT)
    B.inp(ws, r, 11, felt[i])
    ws.row_dimensions[r].height = 21
B.dv(ws, 'K9:K20', ['Good', 'OK', 'Tough'])
ws.conditional_formatting.add('I9:I20', FormulaRule(formula=['AND(ISNUMBER(I9),I9<0)'], font=Font(name=FONT, color=CORAL, bold=True)))
B.fx(ws, 21, 2, 'Year total', None, True, TINT, 'left')
for c in range(3, 10):
    B.fx(ws, 21, c, f'=SUM({L(c)}9:{L(c)}20)', SGN if c == 9 else MONEY, True, TINT)
B.fx(ws, 21, 10, '=IF(N(E21)=0,"",G21/E21)', PCT, True, TINT)
B.fx(ws, 21, 11, '=IF(COUNTA(K9:K20)=0,"",COUNTIF(K9:K20,"Good")&" good")', None, True, TINT, 'left')
B.fx(ws, 22, 2, 'Monthly average', None, True, BAND, 'left')
for c in range(3, 10):
    B.fx(ws, 22, c, f'=IF(COUNT({L(c)}9:{L(c)}20)=0,"",AVERAGE({L(c)}9:{L(c)}20))', SGN if c == 9 else MONEY, False, BAND)
B.fx(ws, 22, 10, '', bg=BAND); B.fx(ws, 22, 11, '', bg=BAND)
B.tip(ws, 24, 2, 'Left over = income minus spending, saving and extra debt payments. A negative month ran on savings or credit (shown in coral). '
      'Nobody gets every month right: look for the pattern, not the perfect number.', 10, 1, 40)
B.protect(ws)

# ================================================================== Spending Review
ws = S['Spending Review']
B.page(ws, 'Where the money went', 'Step 2, look back (2 of 3): the year total for each category. Then decide together: was it worth it, and what changes next year?',
       {2: 26, **{c: 12 for c in range(3, 10)}, 10: 16}, ncols=9, nrows=40)
heads = ['CATEGORY', 'Year total', 'Per month', 'Share', 'Worth it?', 'Next year', '="Plan per month "&Settings!$C$11', 'Change per month', 'Share of spending']
for j, h in enumerate(heads):
    B.th(ws, 8, 2 + j, h, align='left' if j in (0, 4, 5, 8) else 'right')
ws.row_dimensions[8].height = 28
tot = [21000, 4300, 9600, 3900, 4100, 3450, 4800, 2100, 1800, 1150]
worth = ['Yes', 'Yes', 'Yes', 'Partly', 'Partly', 'No', 'Yes', 'Yes', 'Partly', 'Yes']
nxt = ['Keep', 'Cut back', 'Keep', 'Keep', 'Cut back', 'Cut back', 'Spend more', 'Keep', 'Cut back', 'Keep']
plan = [1650, 330, 740, 325, 220, 180, 420, 175, 120, 100]
for i in range(NC):
    r = 9 + i
    B.fx(ws, r, 2, f'=IF(Settings!B{14 + i}="","",Settings!B{14 + i})', None, True, align='left')
    B.inp(ws, r, 3, tot[i], MONEY, 'right')
    B.fx(ws, r, 4, f'=IF(C{r}="","",C{r}/12)', MONEY)
    B.fx(ws, r, 5, f'=IF(OR(C{r}="",N($C$19)=0),"",C{r}/$C$19)', PCT)
    B.inp(ws, r, 6, worth[i]); B.inp(ws, r, 7, nxt[i]); B.inp(ws, r, 8, plan[i], MONEY, 'right')
    B.fx(ws, r, 9, f'=IF(OR(H{r}="",D{r}=""),"",H{r}-D{r})', SGN)
    B.fx(ws, r, 10, f'=IF(E{r}="","",REPT("█",ROUND(E{r}/MAX($E$9:$E$18)*9,0)))', None, False, None, 'left', color=DSAGE, size=9)
    ws.cell(r, 13, f'=IF(C{r}="","",C{r}+ROW()/1000000)').font = F(8, color='C9C2B6')
    ws.row_dimensions[r].height = 21
ws.column_dimensions['M'].hidden = True
B.dv(ws, 'F9:F18', ['Yes', 'Partly', 'No']); B.dv(ws, 'G9:G18', ['Keep', 'Cut back', 'Spend more'])
B.fx(ws, 19, 2, 'Total', None, True, TINT, 'left')
B.fx(ws, 19, 3, '=SUM(C9:C18)', MONEY, True, TINT); B.fx(ws, 19, 4, '=SUM(D9:D18)', MONEY, True, TINT)
B.fx(ws, 19, 5, '=IF(N(C19)=0,"",SUM(E9:E18))', PCT, True, TINT)
B.fx(ws, 19, 6, '', bg=TINT); B.fx(ws, 19, 7, '', bg=TINT)
B.fx(ws, 19, 8, '=SUM(H9:H18)', MONEY, True, TINT); B.fx(ws, 19, 9, '=IF(COUNT(I9:I18)=0,"",SUM(I9:I18))', SGN, True, TINT)
B.fx(ws, 19, 10, '', bg=TINT)
B.section(ws, 21, 2, 'Checks', 4)
B.fx(ws, 22, 2, 'Total on Year in Numbers', None, False, None, 'left'); B.fx(ws, 22, 3, f'={YN}!F21', MONEY)
B.fx(ws, 23, 2, 'Difference', None, False, None, 'left'); B.fx(ws, 23, 3, '=C19-C22', SGN)
B.fx(ws, 23, 4, '=IF(N(C22)=0,"",IF(ABS(C23)<=C22*0.05,"✓ Close enough","Worth a look"))', None, True, None, 'left', 3)
B.fx(ws, 24, 2, '"Worth it" spending', None, False, None, 'left'); B.fx(ws, 24, 3, '=SUMIF(F9:F18,"Yes",C9:C18)', MONEY)
B.fx(ws, 24, 4, '=IF(N(C19)=0,"",C24/C19)', PCT)
B.fx(ws, 25, 2, 'Spending to cut back', None, False, None, 'left'); B.fx(ws, 25, 3, '=SUMIF(G9:G18,"Cut back",C9:C18)', MONEY)
B.fx(ws, 25, 4, '=IF(N(C19)=0,"",C25/C19)', PCT)
B.tip(ws, 27, 2, 'Why "worth it?" first: we judge spending more kindly when we look at what it bought, not just the total. '
      'Agree on what to protect before you decide what to cut, and the cutting talk gets much calmer. The plan column feeds your 2027 Check-ins.', 9, 1, 42)
B.protect(ws)

# ================================================================== Net Worth
ws = S['Net Worth']
B.page(ws, 'Net worth: start vs end of year', 'Step 2, look back (3 of 3): what you own minus what you owe, on 1 January and 31 December.',
       {2: 32, 3: 15, 4: 15, 5: 15, 6: 22}, ncols=5, nrows=40)
for j, h in enumerate(['WHAT WE OWN', 'Start of year', 'End of year', 'Change']):
    B.th(ws, 8, 2 + j, h, align='left' if j == 0 else 'right')
ASSETS = ['Joint savings', f'={NA}&" savings"', f'={NB}&" savings"', 'Pensions and retirement', 'Home value (if you own)', 'Other (car, investments)']
a_s = [4200, 6100, 2300, 38000, 0, 6500]; a_e = [9800, 7400, 3900, 44500, 0, 5200]
for i, a in enumerate(ASSETS):
    r = 9 + i
    B.fx(ws, r, 2, a, None, True, align='left')
    B.inp(ws, r, 3, a_s[i], MONEY, 'right'); B.inp(ws, r, 4, a_e[i], MONEY, 'right')
    B.fx(ws, r, 5, f'=IF(COUNT(C{r}:D{r})=0,"",N(D{r})-N(C{r}))', SGN)
B.fx(ws, 15, 2, 'Total we own', None, True, TINT, 'left')
for c in (3, 4, 5):
    B.fx(ws, 15, c, f'=SUM({L(c)}9:{L(c)}14)', MONEY if c < 5 else SGN, True, TINT)
for j, h in enumerate(['WHAT WE OWE', 'Start of year', 'End of year', 'Change']):
    B.th(ws, 17, 2 + j, h, align='left' if j == 0 else 'right')
DEBTS = ['Credit cards', 'Car finance', 'Student loans', 'Mortgage', 'Other loans']
d_s = [2900, 7400, 21000, 0, 0]; d_e = [600, 4600, 19800, 0, 0]
for i, a in enumerate(DEBTS):
    r = 18 + i
    B.fx(ws, r, 2, a, None, True, align='left')
    B.inp(ws, r, 3, d_s[i], MONEY, 'right'); B.inp(ws, r, 4, d_e[i], MONEY, 'right')
    B.fx(ws, r, 5, f'=IF(COUNT(C{r}:D{r})=0,"",N(D{r})-N(C{r}))', SGN)
B.fx(ws, 23, 2, 'Total we owe', None, True, TINT, 'left')
for c in (3, 4, 5):
    B.fx(ws, 23, c, f'=SUM({L(c)}18:{L(c)}22)', MONEY if c < 5 else SGN, True, TINT)
for j, h in enumerate(['OUR NET WORTH', 'Start of year', 'End of year', 'Change']):
    B.th(ws, 25, 2 + j, h, align='left' if j == 0 else 'right')
B.fx(ws, 26, 2, 'Own minus owe', None, True, WHITE, 'left')
B.fx(ws, 26, 3, '=C15-C23', SGN, True, WHITE); B.fx(ws, 26, 4, '=D15-D23', SGN, True, WHITE); B.fx(ws, 26, 5, '=D26-C26', SGN, True, WHITE)
B.fx(ws, 27, 2, 'Debt paid down this year', None, False, BAND, 'left')
B.fx(ws, 27, 3, '', bg=BAND); B.fx(ws, 27, 4, '=MAX(0,C23-D23)', MONEY, True, BAND); B.fx(ws, 27, 5, '', bg=BAND)
B.tip(ws, 29, 2, 'Net worth is a scoreboard for the two of you, not a judgement. A rising line matters more than the size of the number.', 4, 1, 34)
B.section(ws, 31, 2, 'For the dashboard chart', 4)
B.th(ws, 32, 2, ''); B.th(ws, 32, 3, 'Start', align='right'); B.th(ws, 32, 4, 'End', align='right')
for i, (lab, rr) in enumerate((('Own', 15), ('Owe', 23), ('Net worth', 26))):
    B.fx(ws, 33 + i, 2, lab, None, False, None, 'left'); B.fx(ws, 33 + i, 3, f'=C{rr}', MONEY); B.fx(ws, 33 + i, 4, f'=D{rr}', MONEY)
B.protect(ws)

# ================================================================== Year in Review (look-back questions)
ws = S['Year in Review']
B.page(ws, 'Looking back together', 'Step 3: answer on your own first, then read each other\'s answers and fill in "Together".',
       {2: 34, 3: 30, 4: 30, 5: 30}, ncols=4, nrows=40)
B.th(ws, 8, 2, 'QUESTION'); B.th(ws, 8, 3, f'={NA}'); B.th(ws, 8, 4, f'={NB}'); B.th(ws, 8, 5, 'Together')
Q = [('Our biggest money win this year', 'Paid off the credit card in May', 'Finally started a joint savings pot', 'We cleared a debt AND built a buffer'),
     ('Money we spent that was worth every penny', 'The Lisbon trip', 'Lisbon. And the new mattress', 'Travel is a "protect" category'),
     ('Money we spent that we would skip next time', 'Takeaways on weeknights', 'Subscriptions we forgot about', 'Cancel 3 subs, plan 2 cook nights'),
     ('A money moment that stressed us out', 'The July car repair', 'December, again', 'We need a buffer for big months'),
     ('What I learned about how you handle money', 'You worry more than you say', 'You like a plan, not a lecture', 'Check in monthly, not in a crisis'),
     ('One habit to keep', 'Sunday money check', 'Auto-saving on payday', 'Payday auto-save + Sunday check'),
     ('One habit to drop', 'Buying when bored', 'Avoiding the bank app', 'One "wait 48 hours" rule each'),
     ('If next year goes well, what is different by December?', 'A 3-month buffer', 'Car loan gone', 'Buffer built, car loan cleared, a trip paid in cash')]
for i, (q, a, b, t) in enumerate(Q):
    r = 9 + i
    B.fx(ws, r, 2, q, None, True, None, 'left'); ws.cell(r, 2).alignment = Alignment(wrap_text=True, vertical='center', indent=1)
    for k, v in enumerate((a, b, t)):
        c = B.inp(ws, r, 3 + k, v); c.alignment = Alignment(wrap_text=True, vertical='center', indent=1)
    ws.row_dimensions[r].height = 44
B.fx(ws, 18, 2, 'Our word for this money year', None, True, None, 'left'); B.inp(ws, 18, 3, 'Steadier')
B.fx(ws, 19, 2, 'Our word for next year', None, True, None, 'left'); B.inp(ws, 19, 3, 'Ahead')
B.tip(ws, 21, 2, 'Why answer apart first: when one of you speaks first, the other tends to anchor on that answer. '
      'Writing first means you hear what each of you really thinks.', 4, 1, 36)
B.protect(ws)

# ================================================================== 2027 Goals
ws = S['2027 Goals']
B.page(ws, '=Settings!$C$11&" goals: 3 to 5 shared goals"', 'Step 4: give each goal a number and a finish month. The sheet works out the monthly amount and checks they fit.',
       {2: 5, 3: 28, 4: 11, 5: 12, 6: 12, 7: 12, 8: 13, 9: 12, 10: 34}, ncols=9, nrows=45)
heads = ['#', 'GOAL', 'Type', 'Target', 'Already have', 'Finish month', 'Needed per month', 'Who', 'Why it matters to us']
for j, h in enumerate(heads):
    B.th(ws, 8, 2 + j, h, align='right' if j in (3, 4, 5, 6) else 'left')
ws.row_dimensions[8].height = 28
G = [('3-month emergency buffer', 'Save', 9000, 3000, 12, 'Both', 'No more panic when the car breaks'),
     ('Clear the car loan', 'Pay off', 4600, 0, 10, 'Sam', 'One less bill before the baby talk'),
     ('Summer trip, paid in cash', 'Spend on', 2400, 0, 8, 'Both', 'Holidays without the credit card'),
     ('Wedding fund', 'Save', 4000, 500, 12, 'Both', 'Start married life debt-free'),
     (None, None, None, None, None, None, None)]
for i, g in enumerate(G):
    r = 9 + i
    B.fx(ws, r, 2, i + 1, '0', True, None, 'center')
    B.inp(ws, r, 3, g[0]); B.inp(ws, r, 4, g[1])
    B.inp(ws, r, 5, g[2], MONEY, 'right'); B.inp(ws, r, 6, g[3], MONEY, 'right'); B.inp(ws, r, 7, g[4], '0', 'right')
    B.fx(ws, r, 8, f'=IF(OR(N(E{r})=0,N(G{r})=0),"",MAX(0,(E{r}-N(F{r}))/G{r}))', MONEY, True)
    B.inp(ws, r, 9, g[5]); c = B.inp(ws, r, 10, g[6]); c.alignment = Alignment(wrap_text=True, vertical='center', indent=1)
    ws.row_dimensions[r].height = 26
B.dv(ws, 'D9:D13', ['Save', 'Pay off', 'Spend on'])
B.dv(ws, 'I9:I13', ref='Settings!$H$7:$H$9')
from openpyxl.worksheet.datavalidation import DataValidation
dv = DataValidation(type='whole', operator='between', formula1='1', formula2='12', allow_blank=True,
                    error='Type a month number from 1 to 12', showErrorMessage=True)
ws.add_data_validation(dv); dv.add('G9:G13')
B.fx(ws, 14, 3, 'All goals together', None, True, TINT, 'left')
for c in (2, 4, 7, 9, 10):
    B.fx(ws, 14, c, '', bg=TINT)
B.fx(ws, 14, 5, '=SUM(E9:E13)', MONEY, True, TINT); B.fx(ws, 14, 6, '=SUM(F9:F13)', MONEY, True, TINT)
B.fx(ws, 14, 8, '=SUM(H9:H13)', MONEY, True, TINT)
# progress (fed by the 2027 Check-ins tab)
B.section(ws, 16, 2, 'Progress through the year (from your 2027 Check-ins)', 9)
for j, (h, c) in enumerate([('GOAL', 3), ('Added so far', 5), ('Total now', 6), ('Done', 7), ('Expected by now', 8), ('Status', 9), ('Progress', 10)]):
    B.th(ws, 17, c, h, align='right' if c in (5, 6, 7, 8) else 'left')
B.th(ws, 17, 2, ''); B.th(ws, 17, 4, '')
LM = f"{CI}!$P$38"   # latest month with check-in data (0-12)
for k in range(5):
    r = 18 + k; g = 9 + k
    B.fx(ws, r, 2, k + 1, '0', True, None, 'center')
    B.fx(ws, r, 3, f'=IF(C{g}="","",C{g})', None, True, None, 'left', 2)
    B.fx(ws, r, 5, f'=IF(N(E{g})=0,"",SUM({CI}!D{28 + k}:O{28 + k}))', MONEY)
    B.fx(ws, r, 6, f'=IF(N(E{g})=0,"",N(F{g})+E{r})', MONEY, True)
    B.fx(ws, r, 7, f'=IF(N(E{g})=0,"",MIN(1,F{r}/E{g}))', PCT, True)
    B.fx(ws, r, 8, f'=IF(N(E{g})=0,"",MIN(E{g},N(F{g})+N(H{g})*{LM}))', MONEY)
    B.fx(ws, r, 9, f'=IF(N(E{g})=0,"",IF(F{r}>=E{g},"✓ Done",IF(N(G{g})=0,"Add a month",IF(F{r}>=H{r}-0.5,"On track","Behind"))))', None, True, None, 'left')
    B.fx(ws, r, 10, f'=IF(N(E{g})=0,"",{bar_f(f"F{r}/E{g}", DSAGE, 14)}&"  "&TEXT(G{r},"0%"))', None, False, None, 'left', color=DSAGE, size=9)
    ws.row_dimensions[r].height = 22
ws.conditional_formatting.add('I18:I22', FormulaRule(formula=['I18="Behind"'], font=Font(name=FONT, color=CORAL, bold=True)))
ws.conditional_formatting.add('I18:I22', FormulaRule(formula=['OR(I18="On track",I18="✓ Done")'], font=Font(name=FONT, color=DSAGE, bold=True)))
B.fx(ws, 23, 3, 'All goals', None, True, TINT, 'left', 2)
B.fx(ws, 23, 2, '', bg=TINT)
B.fx(ws, 23, 5, '=SUM(E18:E22)', MONEY, True, TINT); B.fx(ws, 23, 6, '=SUM(F18:F22)', MONEY, True, TINT)
B.fx(ws, 23, 7, '=IF(N(E14)=0,"",MIN(1,F23/E14))', PCT, True, TINT); B.fx(ws, 23, 8, '=SUM(H18:H22)', MONEY, True, TINT)
B.fx(ws, 23, 9, '', bg=TINT); B.fx(ws, 23, 10, '', bg=TINT)
# reality check
B.section(ws, 25, 3, 'Reality check: do the goals fit?', 6)
rc = [('Last year: saved + extra debt + left over, per month', f'=IF(COUNT({YN}!G9:G20)=0,"",{YN}!G22+{YN}!H22+{YN}!I22)'),
      ('Planned cuts from the Spending Review, per month', f'=IF({SR}!I19="","",MAX(0,-{SR}!I19))'),
      ('Goals need per month', '=H14')]
for i, (lab, f) in enumerate(rc):
    r = 26 + i
    B.fx(ws, r, 3, lab, None, False, None, 'left', 4); B.fx(ws, r, 7, f, MONEY, True, None, 'right', 2)
B.fx(ws, 29, 3, 'Room left each month', None, True, TINT, 'left', 4)
B.fx(ws, 29, 7, '=IF(G26="","",G26+N(G27)-G28)', SGN, True, TINT, 'right', 2)
B.fx(ws, 30, 3, '=IF(G29="","",IF(G29>=0,"✓ These goals fit. Set up the monthly transfers on payday.","Too much at once: push a finish month back or lower a target until this is 0 or more."))',
     None, True, GOLDT, 'left', 6)
ws.row_dimensions[30].height = 28
B.tip(ws, 32, 3, 'Why a monthly number: a big goal feels far away, so it slides. A monthly amount set up as a payday transfer turns a wish into a habit '
      'you do not have to remember.', 8, 1, 36)
B.protect(ws)

# ================================================================== 2027 Check-ins (12 months on one tab)
ws = S['2027 Check-ins']
B.page(ws, '=Settings!$C$11&" check-ins: all 12 months"', 'Step 5, once a month: type what came in, what you spent in each category and what went to each goal. One column per month.',
       {2: 27, 3: 10, **{c: 8.4 for c in range(4, 16)}, 16: 10.5}, ncols=15, nrows=45)
B.th(ws, 8, 2, ''); B.th(ws, 8, 3, 'Plan / month', align='right')
for j, m in enumerate(MON):
    B.th(ws, 8, 4 + j, m, align='right')
B.th(ws, 8, 16, 'Year', align='right')


def sub(r, t):
    B.text(ws, r, 2, t, 8, True, GOLD, w=2, indent=1)
    ws.row_dimensions[r].height = 20


# example: Jan-Mar typed (April left for the buyer / the video)
EXM = 3
incA = [3500, 3500, 3550]; incB = [2800, 2850, 2800]
actual = [[1650, 1650, 1650], [348, 336, 352], [762, 715, 768], [318, 305, 310], [265, 210, 335],
          [210, 165, 150], [90, 140, 120], [182, 160, 190], [95, 70, 210], [100, 100, 100]]
tops = [[500, 500, 500], [460, 460, 460], [300, 300, 250], [300, 300, 300], [None] * 3]
sub(9, 'MONEY IN')
for k, (lab, vals) in enumerate(((f'={NA}&" income"', incA), (f'={NB}&" income"', incB))):
    r = 10 + k
    B.fx(ws, r, 2, lab, None, True, None, 'left'); B.fx(ws, r, 3, '', None)
    for j in range(12):
        B.inp(ws, r, 4 + j, vals[j] if j < EXM else None, MONEY, 'right')
    B.fx(ws, r, 16, f'=SUM(D{r}:O{r})', MONEY, True)
B.fx(ws, 12, 2, 'Total income', None, True, TINT, 'left'); B.fx(ws, 12, 3, '', bg=TINT)
for j in range(12):
    c = L(4 + j); B.fx(ws, 12, 4 + j, f'=IF(COUNT({c}10:{c}11)=0,"",SUM({c}10:{c}11))', MONEY, True, TINT)
B.fx(ws, 12, 16, '=SUM(D12:O12)', MONEY, True, TINT)
sub(13, 'SPENDING BY CATEGORY')
for i in range(NC):
    r = 14 + i
    B.fx(ws, r, 2, f'={SR}!B{9 + i}', None, False, None, 'left')
    B.fx(ws, r, 3, f'=IF({SR}!H{9 + i}="","",{SR}!H{9 + i})', MONEY, False, GOLDT)
    for j in range(12):
        B.inp(ws, r, 4 + j, actual[i][j] if j < EXM else None, MONEY, 'right')
    B.fx(ws, r, 16, f'=SUM(D{r}:O{r})', MONEY)
B.fx(ws, 24, 2, 'Total spent', None, True, TINT, 'left'); B.fx(ws, 24, 3, '=SUM(C14:C23)', MONEY, True, TINT)
for j in range(12):
    c = L(4 + j); B.fx(ws, 24, 4 + j, f'=IF(COUNT({c}14:{c}23)=0,"",SUM({c}14:{c}23))', MONEY, True, TINT)
B.fx(ws, 24, 16, '=SUM(D24:O24)', MONEY, True, TINT)
B.fx(ws, 25, 2, 'Spending plan', None, False, BAND, 'left'); B.fx(ws, 25, 3, '', bg=BAND)
for j in range(12):
    c = L(4 + j); B.fx(ws, 25, 4 + j, f'=IF({c}24="","",$C$24)', MONEY, False, BAND)
B.fx(ws, 25, 16, '=SUM(D25:O25)', MONEY, False, BAND)
B.fx(ws, 26, 2, 'Over (+) or under (-) plan', None, False, WHITE, 'left'); B.fx(ws, 26, 3, '', bg=WHITE)
for j in range(12):
    c = L(4 + j); B.fx(ws, 26, 4 + j, f'=IF({c}24="","",{c}24-{c}25)', SGN, True, WHITE)
B.fx(ws, 26, 16, '=IF(COUNT(D26:O26)=0,"",SUM(D26:O26))', SGN, True, WHITE)
ws.conditional_formatting.add('D26:P26', FormulaRule(formula=['AND(ISNUMBER(D26),D26>0)'], font=Font(name=FONT, color=CORAL, bold=True)))
ws.conditional_formatting.add('D26:P26', FormulaRule(formula=['AND(ISNUMBER(D26),D26<=0)'], font=Font(name=FONT, color=DSAGE, bold=True)))
sub(27, 'GOAL TOP-UPS')
for k in range(5):
    r = 28 + k
    B.fx(ws, r, 2, f'=IF({GL}!C{9 + k}="","Goal {k + 1}",{GL}!C{9 + k})', None, False, None, 'left')
    B.fx(ws, r, 3, f'=IF({GL}!H{9 + k}="","",{GL}!H{9 + k})', MONEY, False, GOLDT)
    for j in range(12):
        B.inp(ws, r, 4 + j, tops[k][j] if j < EXM else None, MONEY, 'right')
    B.fx(ws, r, 16, f'=SUM(D{r}:O{r})', MONEY)
B.fx(ws, 33, 2, 'Total to goals', None, True, TINT, 'left'); B.fx(ws, 33, 3, '=SUM(C28:C32)', MONEY, True, TINT)
for j in range(12):
    c = L(4 + j); B.fx(ws, 33, 4 + j, f'=IF({c}38=0,"",SUM({c}28:{c}32))', MONEY, True, TINT)
B.fx(ws, 33, 16, '=SUM(D33:O33)', MONEY, True, TINT)
B.fx(ws, 34, 2, 'Left over', None, True, WHITE, 'left'); B.fx(ws, 34, 3, '', bg=WHITE)
for j in range(12):
    c = L(4 + j); B.fx(ws, 34, 4 + j, f'=IF({c}38=0,"",N({c}12)-N({c}24)-N({c}33))', SGN, True, WHITE)
B.fx(ws, 34, 16, '=IF(COUNT(D34:O34)=0,"",SUM(D34:O34))', SGN, True, WHITE)
ws.conditional_formatting.add('D34:P34', FormulaRule(formula=['AND(ISNUMBER(D34),D34<0)'], font=Font(name=FONT, color=CORAL, bold=True)))
B.fx(ws, 35, 2, 'Money date done?', None, True, None, 'left'); B.fx(ws, 35, 3, '', None)
for j in range(12):
    B.inp(ws, 35, 4 + j, 'Yes' if j < EXM else None, None, 'center')
B.fx(ws, 35, 16, '=COUNTIF(D35:O35,"Yes")&" of 12"', None, True)
B.dv(ws, 'D35:O35', ['Yes', 'No'])
B.fx(ws, 36, 2, 'Goals: total now', None, False, BAND, 'left'); B.fx(ws, 36, 3, f'={GL}!F14', MONEY, False, BAND)
for j in range(12):
    c = L(4 + j); prev = 'C36' if j == 0 else f'{L(3 + j)}36'
    B.fx(ws, 36, 4 + j, f'=IF({c}38=0,"",N({GL}!$F$14)+SUM($D$33:{c}33))', MONEY, False, BAND)
B.fx(ws, 36, 16, '', bg=BAND)
B.fx(ws, 37, 2, 'Goals: % of the way there', None, False, BAND, 'left'); B.fx(ws, 37, 3, f'=IF(N({GL}!E14)=0,"",C36/{GL}!E14)', PCT, False, BAND)
for j in range(12):
    c = L(4 + j); B.fx(ws, 37, 4 + j, f'=IF(OR({c}36="",N({GL}!$E$14)=0),"",{c}36/{GL}!$E$14)', PCT, False, BAND)
B.fx(ws, 37, 16, '', bg=BAND)
# helper row: month number if the month has any numbers, else 0 (drives "latest month")
B.text(ws, 38, 2, 'helper: month has numbers', 7.5, False, 'C9C2B6')
for j in range(12):
    c = L(4 + j)
    B.text(ws, 38, 4 + j, f'=IF(COUNT({c}10:{c}11,{c}14:{c}23,{c}28:{c}32)>0,{j + 1},0)', 7.5, False, 'C9C2B6', align='right')
B.text(ws, 38, 16, '=MAX(D38:O38)', 7.5, False, 'C9C2B6', align='right')
for r in range(9, 38):
    ws.row_dimensions[r].height = ws.row_dimensions[r].height or 20
B.tip(ws, 40, 2, 'Plan / month comes from your Spending Review (spending) and 2027 Goals (top-ups). Type each month after payday or at your money date, '
      'then open the Monthly Money Check-in tab: it writes your month in plain words.', 15, 1, 36)
B.protect(ws)

# ================================================================== Monthly Money Check-in (behaviour layer)
ws = S['Monthly Money Check-in']
B.page(ws, 'Monthly Money Check-in', 'Step 5, once a month: see your month in plain words, then talk it through together. About 20 minutes.',
       {c: 9 for c in range(2, 17)}, ncols=16, nrows=70)
B.text(ws, 7, 2, 'WHICH MONTH?', 8, True, MUTED, w=2, indent=1)
B.inp(ws, 7, 4, None, None, 'left', w=3)
B.dv(ws, 'D7', ref='Settings!$I$9:$I$20')
B.text(ws, 7, 7, '=IF(D7="","Blank = your latest month ("&IF(N(R22)=0,"none typed yet",INDEX(Settings!$I$9:$I$20,MAX(1,N(R22))))&"). Pick a month to look back at an earlier one.","Showing "&D7&". Clear the box to go back to your latest month.")',
       9, False, MUTED, w=10, indent=1)
ws.row_dimensions[7].height = 26
# helpers (column R onward, hidden)
H = {}
helpers = [('m', f'=IF(D7="",N({CI}!$P$38),MATCH(D7,Settings!$I$9:$I$20,0))'),
           ('mname', '=IF(N(R8)=0,"",INDEX(Settings!$I$9:$I$20,R8)&" "&Settings!$C$11)'),
           ('inc', f'=IF(N(R8)=0,0,N(INDEX({CI}!$D$12:$O$12,R8)))'),
           ('spent', f'=IF(N(R8)=0,0,N(INDEX({CI}!$D$24:$O$24,R8)))'),
           ('plan', f'=N({CI}!$C$24)'),
           ('goals', f'=IF(N(R8)=0,0,N(INDEX({CI}!$D$33:$O$33,R8)))'),
           ('left', '=R10-R11-R13'),
           ('maxover', '=MAX(0,MAX(J23:J32))'),
           ('overcat', '=IF(R15<=0,"",INDEX(B23:B32,MATCH(R15,J23:J32,0)))'),
           ('nover', '=COUNTIF(J23:J32,">0")'),
           ('pct', f'=IF(OR(N(R8)=0,N({GL}!$E$14)=0),0,N(INDEX({CI}!$D$37:$O$37,R8)))'),
           ('target', f'=N({GL}!$E$14)'),
           ('hasdata', f'=IF(N(R8)=0,0,N(INDEX({CI}!$D$38:$O$38,R8)))'),
           ('under', '=IF(R11<=R12,R12-R11,0)')]
for i, (k, f) in enumerate(helpers):
    r = 8 + i; H[k] = f'$R${r}'
    ws.cell(r, 17, k).font = F(7.5, color='C9C2B6'); ws.cell(r, 18, f).font = F(7.5, color='C9C2B6')
ws['R22'] = f'={CI}!$P$38'; ws['R22'].font = F(7.5, color='C9C2B6')
for col in 'QRS':
    ws.column_dimensions[col].hidden = True
ws.row_dimensions[8].height = 10
# plain-words summary (ONE cell, ready to copy)
B.section(ws, 9, 2, 'Your month in plain words', 8)
B.text(ws, 9, 11, 'One cell, ready to copy: click it, copy, paste.', 8.5, False, MUTED, w=6, align='right', italic=True)
summ = (f'=IF(OR(N({H["m"]})=0,{H["hasdata"]}=0),"Type a month on the 2027 Check-ins tab (income, spending and goal top-ups) and your month appears here in plain words.",'
        f'"In "&{H["mname"]}&" we earned "&{M(H["inc"])}&" together and spent "&{M(H["spent"])}'
        f'&IF({H["plan"]}=0,". "," against a plan of "&{M(H["plan"])}&", "&IF({H["spent"]}<={H["plan"]},{M(H["under"])}&" under plan. ",{M(H["spent"] + "-" + H["plan"])}&" over plan. "))'
        f'&IF({H["maxover"]}>0,"Our biggest overspend was "&LOWER({H["overcat"]})&", "&{M(H["maxover"])}&" over plan"'
        f'&IF({H["nover"]}>1," ("&{H["nover"]}&" categories went over)","")&". ",IF({H["plan"]}=0,"","Every category stayed within plan. "))'
        f'&IF({H["target"]}=0,IF({H["goals"]}>0,"We put "&{M(H["goals"])}&" towards our goals. ",""),"We put "&{M(H["goals"])}&" towards our goals, so together they are "&TEXT({H["pct"]},"0%")&" of the way to "&{M(H["target"])}&". ")'
        f'&IF({H["left"]}>=0,"That left "&{M(H["left"])}&" for everything else.","That took "&{M("-" + H["left"])}&" from savings or credit."))')
B.box(ws, 10, 2, 16, 9, GOLDT, 'E6D9B5')
c = B.text(ws, 10, 2, summ, 12.5, False, '4A3F30', w=8, h=7, indent=1)
c.alignment = Alignment(wrap_text=True, vertical='center', indent=1)
# KPI cards, 2 x 2 to the right of the summary
for r, h in [(10, 22), (11, 30), (12, 18), (13, 8), (14, 22), (15, 30), (16, 18)]:
    ws.row_dimensions[r].height = h
B.kpi(ws, 10, 11, 'WE EARNED', f'=IF({H["hasdata"]}=0,"–",{M(H["inc"])})', f'=IF({H["mname"]}="","",{H["mname"]})', accent=DSAGE)
B.kpi(ws, 10, 14, 'WE SPENT', f'=IF({H["hasdata"]}=0,"–",{M(H["spent"])})', f'=IF({H["hasdata"]}=0,"","plan "&{M(H["plan"])})', accent=GOLD)
B.kpi(ws, 14, 11, 'TO OUR GOALS', f'=IF({H["hasdata"]}=0,"–",{M(H["goals"])})', f'=IF({H["hasdata"]}=0,"",TEXT({H["pct"]},"0%")&" of the way there")', accent=GOLD)
B.kpi(ws, 14, 14, 'LEFT OVER', f'=IF({H["hasdata"]}=0,"–",{M(H["left"])})', '="after spending and goals"', accent=CHAR)
for r in (17, 18, 19):
    ws.row_dimensions[r].height = 6
# plan vs actual
B.section(ws, 20, 2, 'Plan vs actual, by category', 8)
B.th(ws, 22, 2, 'CATEGORY', 3); B.th(ws, 22, 5, 'Plan', 2, 'right'); B.th(ws, 22, 7, 'Actual', 2, 'right')
B.th(ws, 22, 9, 'Difference', 2, 'right'); B.th(ws, 22, 11, 'How it went', 6)
for i in range(NC):
    r = 23 + i; src = 14 + i
    B.fx(ws, r, 2, f'={CI}!B{src}', None, False, None, 'left', 3)
    B.fx(ws, r, 5, f'=N({CI}!C{src})', MONEY, False, None, 'right', 2)
    B.fx(ws, r, 7, f'=IF({H["hasdata"]}=0,"",N(INDEX({CI}!$D${src}:$O${src},{H["m"]})))', MONEY, False, None, 'right', 2)
    B.fx(ws, r, 9, f'=IF(G{r}="","",G{r}-E{r})', SGN, True, None, 'right', 2)
    B.fx(ws, r, 11, f'=IF(I{r}="","",IF(I{r}>0,"▲ over by "&{M(f"I{r}")},IF(I{r}=0,"● on plan","▼ under by "&{M(f"-I{r}")})))', None, False, None, 'left', 6)
    ws.row_dimensions[r].height = 20
# J23:J32 = difference copy for MAX/MATCH helpers (column J is inside the merged Difference cell, so use a visible-safe helper column T)
for i in range(NC):
    r = 23 + i
    ws.cell(r, 20, f'=IF(OR(I{r}="",N(E{r})=0),-1E+99,I{r})').font = F(7.5, color='C9C2B6')
ws.column_dimensions['T'].hidden = True
for k in ('maxover', 'overcat', 'nover'):
    pass
ws[H['maxover'].replace('$', '')] = '=IF(MAX(T23:T32)>0,MAX(T23:T32),0)'
ws[H['overcat'].replace('$', '')] = '=IF(R15<=0,"",INDEX(B23:B32,MATCH(MAX(T23:T32),T23:T32,0)))'
ws[H['nover'].replace('$', '')] = '=COUNTIF(T23:T32,">0")'
for k in ('maxover', 'overcat', 'nover'):
    ws[H[k].replace('$', '')].font = F(7.5, color='C9C2B6')
ws.conditional_formatting.add('K23:K32', FormulaRule(formula=['LEFT(K23,1)="▲"'], font=Font(name=FONT, color=CORAL, bold=True)))
ws.conditional_formatting.add('K23:K32', FormulaRule(formula=['OR(LEFT(K23,1)="▼",LEFT(K23,1)="●")'], font=Font(name=FONT, color=DSAGE, bold=True)))
B.fx(ws, 33, 2, 'Total', None, True, TINT, 'left', 3); B.fx(ws, 33, 5, '=SUM(E23:F32)', MONEY, True, TINT, 'right', 2)
B.fx(ws, 33, 7, f'=IF({H["hasdata"]}=0,"",SUM(G23:H32))', MONEY, True, TINT, 'right', 2)
B.fx(ws, 33, 9, '=IF(G33="","",G33-E33)', SGN, True, TINT, 'right', 2); B.fx(ws, 33, 11, '', None, False, TINT, 'left', 6)
# reflection questions
ws.row_dimensions[34].height = 12
B.section(ws, 35, 2, 'Talk it through: 5 questions for the two of you', 12)
B.text(ws, 36, 2, 'Read the summary out loud first. Then take turns. There are no wrong answers, only honest ones.', 9.5, False, MUTED, w=15, italic=True)
B.th(ws, 37, 2, 'QUESTION', 4); B.th(ws, 37, 6, f'={NA}', 4); B.th(ws, 37, 10, f'={NB}', 4); B.th(ws, 37, 14, 'Together', 3)
QS = [('Which spend this month did you both feel good about, and what made it feel worth it?',
       'Friday pizza night in, it felt like us', 'The birthday dinner for Mum', 'Small, planned treats feel best'),
      ('Was there a moment money caused tension between us? What was really going on for each of us?',
       'Takeaways: I was tired, not hungry', 'I felt judged about the takeaways', 'Tired evenings, not greed. Plan for them'),
      ('Which number in the summary surprised you, and how do you each feel about it?',
       'Eating out over by $115', 'How far the goals have come', 'Proud of the goals, eyes on eating out'),
      ('What is one thing your partner did with money this month that you appreciated?',
       'You set up the car loan overpayment', 'You cooked 3 nights to save for Lisbon', 'Say thank you more often'),
      ('What is one small habit we will try together next month?',
       'Batch-cook on Sundays', 'Takeaway only on Fridays', 'Sunday batch-cook, Friday takeaway night')]
EXQ = True
for i, (q, a, b, t) in enumerate(QS):
    r = 38 + i
    c = B.fx(ws, r, 2, q, None, True, None, 'left', 4); c.alignment = Alignment(wrap_text=True, vertical='center', indent=1)
    for col, v, w in ((6, a, 4), (10, b, 4), (14, t, 3)):
        cc = B.inp(ws, r, col, v, None, 'left', w=w); cc.alignment = Alignment(wrap_text=True, vertical='center', indent=1)
    ws.row_dimensions[r].height = 50
B.tip(ws, 44, 2, 'Want a second opinion? Copy your summary and these questions into any AI assistant you use (ChatGPT, Gemini, Copilot) '
      'and ask it to reply like a kind, honest money coach.', 15, 1, 34)
B.text(ws, 45, 2, 'Optional. Everything on this tab works on its own, with no AI and no internet: the summary is built by formulas from your own numbers.',
       8.5, False, MUTED, w=15, italic=True)
# habits log
ws.row_dimensions[46].height = 12
B.section(ws, 47, 2, 'Our small habits, month by month', 10)
B.th(ws, 48, 2, 'MONTH', 2); B.th(ws, 48, 4, 'The one small habit we tried', 7); B.th(ws, 48, 11, 'Did we do it?', 2); B.th(ws, 48, 13, 'Note', 4)
HB = [('Payday auto-save to the buffer', 'Yes', 'Set up on the 1st, done'), ('No-spend weekend once a month', 'Partly', 'Did one, skipped one'),
      ('Sunday batch-cook', 'Yes', 'Eating out down by half')]
for j in range(12):
    r = 49 + j
    B.fx(ws, r, 2, f'=INDEX(Settings!$I$9:$I$20,{j + 1})', None, True, None, 'left', 2)
    h = HB[j] if j < EXM else (None, None, None)
    B.inp(ws, r, 4, h[0], w=7); B.inp(ws, r, 11, h[1], w=2); B.inp(ws, r, 13, h[2], w=4)
    ws.row_dimensions[r].height = 20
B.dv(ws, 'K49:K60', ['Yes', 'Partly', 'Not yet'])
B.fx(ws, 61, 2, '="Habits kept: "&COUNTIF(K49:K60,"Yes")&" of "&MAX(1,COUNTA(D49:D60))', None, True, TINT, 'left', 6)
B.fx(ws, 61, 8, f'=IF(COUNTA(D49:D60)=0,"",{bar_f("COUNTIF(K49:K60,\"Yes\")/MAX(1,COUNTA(D49:D60))", DSAGE, 16)})', None, False, TINT, 'left', 9, DSAGE)
B.protect(ws)

# ================================================================== Money Date
ws = S['Money Date']
B.page(ws, 'Your 30-minute monthly money date', 'Your Step 5 agenda. Same day each month. Snacks allowed. Phones down, this file open.', {2: 9, 3: 30, 4: 66}, ncols=3, nrows=40)
B.th(ws, 8, 2, 'MIN'); B.th(ws, 8, 3, 'STEP'); B.th(ws, 8, 4, 'WHAT TO DO')
AG = [('5', 'One win each', 'Start with something that went well with money this month. Small counts.'),
      ('5', 'Type the month', 'On 2027 Check-ins: income, spending per category and what went to each goal. Mark the money date Yes.'),
      ('5', 'Read it in plain words', 'Open the Monthly Money Check-in. One of you reads the summary out loud.'),
      ('10', 'Talk it through', 'Answer the 5 questions, apart first, then together. Pick ONE small habit for next month.'),
      ('5', 'Look ahead', 'Birthdays, renewals, trips next month? Then one nice thing you both look forward to.')]
for i, (m, s, w) in enumerate(AG):
    r = 9 + i
    B.fx(ws, r, 2, m, None, True, None, 'center'); B.fx(ws, r, 3, s, None, True, None, 'left')
    c = B.fx(ws, r, 4, w, None, False, None, 'left'); c.alignment = Alignment(wrap_text=True, vertical='center', indent=1)
    ws.row_dimensions[r].height = 36
B.section(ws, 15, 3, 'Every 3 months, also', 2)
for i, t in enumerate(['Look at the Spending Review: are the "cut back" categories actually smaller?',
                       'Update Net Worth with today\'s balances, so you can see the line move.',
                       'Ask: is each goal still the right goal? It is fine to change one.']):
    B.fx(ws, 16 + i, 3, '•', None, True, None, 'right'); c = B.fx(ws, 16 + i, 4, t, None, False, None, 'left')
    ws.row_dimensions[16 + i].height = 26
B.tip(ws, 20, 3, 'Ground rules: no blame for the past, talk about the plan not the person, and stop at 30 minutes even if you are not done.', 2, 1, 36)
B.protect(ws)

# ================================================================== Start Here
ws = S['Start Here']
B.page(ws, 'Start here', 'About 90 minutes for the whole look-back (one evening or two), then 30 minutes a month. No formulas to touch.',
       {2: 7, 3: 96, 4: 3}, ncols=3, nrows=45)
B.box(ws, 7, 2, 7, 3, GOLDT, GOLDT)
B.text(ws, 7, 2, '=IF(Settings!$C$7="","Two files: EXAMPLE (filled in) shows a made-up couple, Sam and Alex. BLANK (start here) is yours: type your own numbers in it.",'
       '"You are looking at the EXAMPLE file: a made-up couple, Sam and Alex, so you can see every tab working. Open the BLANK (start here) file for your own numbers.")',
       10, True, '6B5B45', w=2, indent=1)
ws.row_dimensions[7].height = 40
steps = [('1', 'Settings. Your two names, your currency symbol (the one setting for every amount) and the year you are looking back on.'),
         ('2', 'Look back on the whole year. Year in Numbers (all 12 months), Spending Review (was it worth it?) and Net Worth (start vs end). '
               'Rough numbers from your bank apps are fine.'),
         ('3', 'Talk it over. Year in Review has 8 questions: answer apart first, then fill in "Together".'),
         ('4', '2027 Goals. Pick 3 to 5 shared goals with a number and a finish month. The sheet works out the monthly amount and checks they fit.'),
         ('5', 'Once a month: type the month on 2027 Check-ins, then open the Monthly Money Check-in. It writes your month in plain words '
               'and gives you 5 questions to talk through. The Money Date tab is your 30-minute agenda.')]
for i, (n, t) in enumerate(steps):
    r = 9 + i * 2
    B.box(ws, r, 2, r, 3); B.text(ws, r, 2, n, 18, True, GOLD, align='center'); B.text(ws, r, 3, t, 10.5, indent=1)
    ws.row_dimensions[r].height = 46; ws.row_dimensions[r + 1].height = 6
B.tip(ws, 20, 2, 'Colours: pale yellow = type here. White = worked out for you (locked so the sums never break; Excel: Review > Unprotect Sheet, no password). '
      'The Dashboard fills in as you go.', 2, 1, 40)
B.tip(ws, 22, 2, 'Google Sheets: upload the .xlsx to Google Drive, open it, choose File > Save as Google Sheets, then share it with your partner. '
      'Move between tabs with the tab bar along the bottom of the screen. Works offline in Excel 2016+ (Windows and Mac), Excel online, and Google Sheets.', 2, 1, 44)
B.tip(ws, 24, 2, 'Prefer paper? Print the A4 or US Letter PDF in your download: the same steps, one page per step, plus a Monthly Money Check-in page.', 2, 1, 30)
B.tip(ws, 26, 2, 'General information, not financial advice. Questions about the file: joel@wayofwealthcoaching.com', 2, 1, 26)
B.text(ws, 28, 2, 'Way of Wealth Studio', 9, True, GOLD, w=2)
B.protect(ws)

# ================================================================== Dashboard
ws = S['Dashboard']
B.page(ws, '="Our "&Settings!$C$10&" money year, together"', '', ncols=16, nrows=110)
ws['B2'] = '="Our "&Settings!$C$10&" money year, together"'; ws['B2'].font = F(20, True)
ws['B3'] = f'={NA}&" and "&{NB}&"  ·  looking back on January to December "&Settings!$C$10&"  ·  planning "&Settings!$C$11'
ws['B3'].font = F(10, color=MUTED)
HAS = f'COUNT({YN}!C9:H20)>0'
for r, h in [(7, 22), (8, 30), (9, 18), (10, 8), (11, 22), (12, 30), (13, 18)]:
    ws.row_dimensions[r].height = h
NWC = f'{NW}!E26'
B.hero(ws, 7, 2, 7, 7, '="OUR NET WORTH IN "&Settings!$C$10',
       f'=IF(COUNT({NW}!C9:D14,{NW}!C18:D22)=0,"–",IF({NWC}>=0,"+","-")&TEXT(ABS({NWC}),{FMT}))',
       f'=IF(COUNT({NW}!C9:D14,{NW}!C18:D22)=0,"Fill in Year in Numbers and Net Worth to see your year.","From "&TEXT({NW}!C26,{FMT})&" on 1 January to "&TEXT({NW}!D26,{FMT})&" on 31 December. '
       f'We saved "&TEXT({YN}!G21,{FMT})&" and paid off "&TEXT({YN}!H21,{FMT})&" of extra debt.")',
       'Own minus owe, start vs end of year (Net Worth tab).')
B.kpi(ws, 7, 10, 'TOTAL INCOME', f'=IF({HAS},TEXT({YN}!E21,{FMT}),"–")', '="both of you, Jan to Dec"', accent=DSAGE)
B.kpi(ws, 7, 14, 'TOTAL SPENT', f'=IF({HAS},TEXT({YN}!F21,{FMT}),"–")', f'=IF({HAS},TEXT({YN}!F22,{FMT})&" a month on average","")', accent=GOLD)
B.kpi(ws, 11, 10, 'SAVED OR INVESTED', f'=IF({HAS},TEXT({YN}!G21,{FMT}),"–")', f'=IF({YN}!J21="","","that is "&TEXT({YN}!J21,"0%")&" of income")', accent=DSAGE)
B.kpi(ws, 11, 14, 'EXTRA DEBT PAID', f'=IF({HAS},TEXT({YN}!H21,{FMT}),"–")',
      f'=IF(COUNT({NW}!C18:D22)=0,"",IF(N({NW}!D23)=0,"debt now cleared","debt now "&TEXT({NW}!D23,{FMT})))', accent=CORAL)
# next step
NEXT = (f'=IF(NOT({HAS}),"Start with Settings, then type each month on Year in Numbers.",'
        f'IF(COUNTA({GL}!C9:C13)=0,"Look-back done. Next: pick 3 to 5 shared goals on the 2027 Goals tab.",'
        f'IF(N({GL}!G29)<0,"Your goals need more than you have each month: push a finish month back on 2027 Goals.",'
        f'IF(N({CI}!P38)=0,"Each month: type your numbers on 2027 Check-ins, then read the Monthly Money Check-in together.",'
        f'"Latest check-in: "&INDEX(Settings!$I$9:$I$20,{CI}!P38)&". Read your month in plain words on the Monthly Money Check-in tab and pick one small habit."))))')
B.bar(ws, 15, 2, 15, 'NEXT', NEXT)
ws.row_dimensions[14].height = 10; ws.row_dimensions[16].height = 10
for r, h in [(17, 22), (18, 30), (19, 18)]:
    ws.row_dimensions[r].height = h
B.kpi(ws, 17, 2, 'SPENDING "WORTH IT"', f'=IF({SR}!D24="","–",TEXT({SR}!D24,"0%"))', f'=IF(N({SR}!C25)=0,"","cutting back on "&TEXT({SR}!D25,"0%"))')
B.kpi(ws, 17, 6, 'BEST MONTH', f'=IF(COUNT({YN}!I9:I20)=0,"–",INDEX({YN}!B9:B20,MATCH(MAX({YN}!I9:I20),{YN}!I9:I20,0)))',
      f'=IF(COUNT({YN}!I9:I20)=0,"",TEXT(MAX({YN}!I9:I20),{FMT})&" left over")')
B.kpi(ws, 17, 10, '="GOALS FOR "&Settings!$C$11', f'=IF(COUNTA({GL}!C9:C13)=0,"–",COUNTA({GL}!C9:C13)&" goals")',
      f'=IF(N({GL}!H14)=0,"",TEXT({GL}!H14,{FMT})&" a month for all")', accent=GOLD)
B.kpi(ws, 17, 14, 'GOAL PROGRESS', f'=IF({GL}!G23="","–",TEXT({GL}!G23,"0%"))', f'=IF({GL}!G23="",COUNTIF({CI}!D35:O35,"Yes")&" of 12 money dates done",TEXT({GL}!F23,{FMT})&" of "&TEXT({GL}!E14,{FMT}))', accent=GOLD)
ws.row_dimensions[20].height = 12
# tables
B.section(ws, 21, 2, '="Goals at a glance, "&Settings!$C$11', 8)
B.th(ws, 22, 2, 'GOAL', 3); B.th(ws, 22, 5, 'Done', align='right'); B.th(ws, 22, 6, 'Progress', 2); B.th(ws, 22, 8, 'Status', 2)
for k in range(5):
    r = 23 + k; g = 18 + k
    B.fx(ws, r, 2, f'=IF({GL}!C{9 + k}="","",{GL}!C{9 + k})', None, False, None, 'left', 3)
    B.fx(ws, r, 5, f'=IF(B{r}="","",{GL}!G{g})', PCT, True)
    B.fx(ws, r, 6, f'=IF(OR(B{r}="",{GL}!G{g}=""),"",{bar_f(f"{GL}!G{g}", DSAGE, 8)})', None, False, None, 'left', 2, DSAGE, 9)
    B.fx(ws, r, 8, f'=IF(B{r}="","",{GL}!I{g})', None, True, None, 'left', 2)
    ws.row_dimensions[r].height = 21
ws.conditional_formatting.add('H23:H27', FormulaRule(formula=['H23="Behind"'], font=Font(name=FONT, color=CORAL, bold=True)))
ws.conditional_formatting.add('H23:H27', FormulaRule(formula=['OR(H23="On track",H23="✓ Done")'], font=Font(name=FONT, color=DSAGE, bold=True)))
B.section(ws, 21, 11, 'Where most of it went', 6)
B.th(ws, 22, 11, 'CATEGORY', 3); B.th(ws, 22, 14, 'Year', 2, 'right'); B.th(ws, 22, 16, 'Share', align='right')
for k in range(3):
    r = 23 + k
    B.fx(ws, r, 11, f'=IF(COUNT({SR}!C9:C18)<{k + 1},"",INDEX({SR}!B9:B18,MATCH(LARGE({SR}!M9:M18,{k + 1}),{SR}!M9:M18,0)))', None, False, None, 'left', 3)
    B.fx(ws, r, 14, f'=IF(K{r}="","",INDEX({SR}!C9:C18,MATCH(LARGE({SR}!M9:M18,{k + 1}),{SR}!M9:M18,0)))', MONEY, False, None, 'right', 2)
    B.fx(ws, r, 16, f'=IF(OR(N(N{r})=0,N({SR}!C19)=0),"",N{r}/{SR}!C19)', PCT)
B.fx(ws, 26, 11, 'Toughest month', None, True, None, 'left', 3)
B.fx(ws, 26, 14, f'=IF(COUNT({YN}!I9:I20)=0,"",INDEX({YN}!B9:B20,MATCH(MIN({YN}!I9:I20),{YN}!I9:I20,0)))', None, False, None, 'right', 2)
B.fx(ws, 26, 16, f'=IF(COUNT({YN}!I9:I20)=0,"",TEXT(MIN({YN}!I9:I20),{FMT})&" left")', None)
B.fx(ws, 27, 11, 'Months that felt good', None, True, None, 'left', 3)
B.fx(ws, 27, 14, f'=IF(COUNTA({YN}!K9:K20)=0,"",COUNTIF({YN}!K9:K20,"Good")&" of 12")', None, False, None, 'right', 2)
B.fx(ws, 27, 16, '', None)
for r in (23, 24, 25, 26, 27):
    ws.row_dimensions[r].height = 21
# section headers above charts
B.section(ws, 29, 2, '="Looking back: January to December "&Settings!$C$10', 15)
yn, sr, nw, gl, ci = S['Year in Numbers'], S['Spending Review'], S['Net Worth'], S['2027 Goals'], S['2027 Check-ins']
bar_chart(ws, 'B31', 'Income vs spending by month', Reference(yn, min_col=2, min_row=9, max_row=20),
          Reference(yn, min_col=5, max_col=6, min_row=8, max_row=20), w=11.8, h=7.4, colors=[DSAGE, GOLD])
ch = ws._charts[-1]; ch.series[0].tx = SeriesLabel(v='Income'); ch.series[1].tx = SeriesLabel(v='Spending')
bar_chart(ws, 'J31', 'Where the money went', Reference(sr, min_col=2, min_row=9, max_row=18),
          Reference(sr, min_col=3, min_row=8, max_row=18), w=11.8, h=7.4, horizontal=True, legend=False, colors=[DSAGE])
ws._charts[-1].x_axis.scaling.orientation = 'maxMin'
line_chart(ws, 'B47', 'Saved or invested each month', Reference(yn, min_col=2, min_row=9, max_row=20),
           [Reference(yn, min_col=7, min_row=8, max_row=20), Reference(yn, min_col=8, min_row=8, max_row=20)], w=11.8, h=7.4, colors=[DSAGE, GOLD])
ch = ws._charts[-1]; ch.series[0].tx = SeriesLabel(v='Saved or invested'); ch.series[1].tx = SeriesLabel(v='Extra debt paid')
bar_chart(ws, 'J47', 'Net worth: start vs end of year', Reference(nw, min_col=2, min_row=33, max_row=35),
          Reference(nw, min_col=3, max_col=4, min_row=32, max_row=35), w=11.8, h=7.4, colors=[SAGE, GOLD])
B.section(ws, 63, 2, '="Looking ahead: "&Settings!$C$11&" goals and monthly check-ins"', 15)
bar_chart(ws, 'B65', '="Goal progress, "&Settings!$C$11', Reference(gl, min_col=3, min_row=18, max_row=22),
          Reference(gl, min_col=7, min_row=17, max_row=22), w=11.8, h=7.4, horizontal=True, legend=False, colors=[GOLD])
ch = ws._charts[-1]; ch.title = 'Goal progress so far'; ch.x_axis.scaling.orientation = 'maxMin'
ch.y_axis.scaling.min = 0; ch.y_axis.scaling.max = 1; ch.y_axis.numFmt = '0%'
for s_ in ch.series: s_.dLbls.numFmt = '0%'
bar_chart(ws, 'J65', 'Check-ins: spent vs plan', Reference(ci, min_col=4, max_col=15, min_row=8),
          Reference(ci, min_col=3, max_col=15, min_row=24, max_row=25), w=11.8, h=7.4, colors=[GOLD, SAGE], titles_from_data=True)
ch = ws._charts[-1]
# rows as series: rebuild from rows (Spent row 24, Plan row 25), categories Jan-Dec
ch.series = []
from openpyxl.chart import Series
for rr, nm, col in ((24, 'Spent', GOLD), (25, 'Plan', SAGE)):
    s_ = Series(Reference(ci, min_col=4, max_col=15, min_row=rr), title=nm)
    s_.graphicalProperties.solidFill = col; s_.graphicalProperties.line.solidFill = col
    ch.series.append(s_)
ch.set_categories(Reference(ci, min_col=4, max_col=15, min_row=8))
ch.y_axis.scaling.min = 0
B.text(ws, 82, 2, 'General information, not financial advice. Way of Wealth Studio · joel@wayofwealthcoaching.com', 8.5, False, MUTED, w=15)
for c in ws._charts:
    c.roundedCorners = False
    if c.legend is not None: c.legend.overlay = False
B.protect(ws)

# ================================================================== save
AREAS = {'Dashboard': 'A1:R83', 'Start Here': 'A1:E29', 'Settings': 'A1:F26', 'Year in Numbers': 'A1:L25', 'Spending Review': 'A1:K28',
         'Net Worth': 'A1:G36', 'Year in Review': 'A1:F22', '2027 Goals': 'A1:K33', '2027 Check-ins': 'A1:Q41',
         'Monthly Money Check-in': 'A1:Q62', 'Money Date': 'A1:E21'}
orig_save = B.wb.save
B.wb.save = lambda p: None
B.save(OUT, AREAS)
S['Monthly Money Check-in'].page_setup.orientation = 'portrait'
S['Dashboard'].page_setup.orientation = 'portrait'
for w_ in B.wb.worksheets:
    w_.oddFooter.center.text = 'Way of Wealth Studio  ·  Couples Money Year in Review and 2027 Goals'
    w_.oddFooter.center.size = 8
B.wb.active = 1 if BLANK else 0
if BLANK:
    for _w in B.wb.worksheets: _w.sheet_view.tabSelected = False
    B.wb.worksheets[1].sheet_view.tabSelected = True
orig_save(OUT)
print('saved', OUT)
