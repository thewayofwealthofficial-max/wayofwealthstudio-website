"""Couples Money Year in Review and 2027 Goals - Way of Wealth Studio. Builds the Excel / Google Sheets workbook.
python3 build_xlsx.py out/file.xlsx [blank]
"""
import sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, Protection
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.hyperlink import Hyperlink
from openpyxl.utils import get_column_letter as L

OUT = sys.argv[1] if len(sys.argv) > 1 else 'out/workbook.xlsx'
BLANK = len(sys.argv) > 2 and sys.argv[2] == 'blank'

CREAM, SAGE, DSAGE, GOLD, CHAR, INPUT, WHITE = 'F5F0E8', 'B8C5B0', '8FA585', 'B8956E', '3D3D3D', 'FFF8E1', 'FFFFFF'
LINE = 'D9D1C3'; MUTED = '6E6A64'; SOFT = 'EDE6DA'
fill = lambda c: PatternFill('solid', start_color=c, end_color=c)
TF = 'Cambria'; BF = 'Arial'
thin = Side(style='thin', color=LINE)
box = Border(left=thin, right=thin, top=thin, bottom=thin)
MONEY = '#,##0'; PCT = '0%'
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

wb = Workbook()
TABS = ['Dashboard', 'Start Here', 'Settings', 'Year in Numbers', 'Spending Review', 'Net Worth', 'Year in Review',
        '2027 Goals', 'Monthly Check-ins', 'Money Date']
NAV = [('Dashboard', 'Dashboard'), ('Start', 'Start Here'), ('Settings', 'Settings'), ('1 Numbers', 'Year in Numbers'),
       ('2 Spending', 'Spending Review'), ('3 Net worth', 'Net Worth'), ('4 Review', 'Year in Review'),
       ('5 Goals', '2027 Goals'), ('6 Check-ins', 'Monthly Check-ins'), ('Money date', 'Money Date')]
sheets = {}
for i, t in enumerate(TABS):
    ws = wb.active if i == 0 else wb.create_sheet()
    ws.title = t
    ws.sheet_view.showGridLines = False
    ws.sheet_view.showRowColHeaders = False
    ws.sheet_properties.tabColor = DSAGE if i else GOLD
    sheets[t] = ws

S = lambda n: f"'{n}'"


def base(ws, title, sub, ncols=14, nrows=70, widths=None):
    ws.column_dimensions['A'].width = 3
    ncols = max(ncols, 11)
    for c in range(2, ncols + 2):
        ws.column_dimensions[L(c)].width = (widths or {}).get(c, 14)
    for r in range(1, nrows + 1):
        for c in range(1, ncols + 2):
            ws.cell(r, c).fill = fill(CREAM)
    ws.row_dimensions[1].height = 10
    ws['B2'] = title
    ws['B2'].font = Font(name=TF, size=22, bold=True, color=CHAR)
    ws.row_dimensions[2].height = 34
    ws['B3'] = sub
    ws['B3'].font = Font(name=BF, size=10, color=MUTED)
    # nav buttons
    ws.row_dimensions[4].height = 6
    ws.row_dimensions[5].height = 24
    col = 2
    for label, tgt in NAV:
        cell = ws.cell(5, col, f'=HYPERLINK("#{S(tgt)}!A1","{label}")')
        here = tgt == ws.title
        cell.fill = fill(GOLD if here else DSAGE)
        cell.font = Font(name=BF, size=9, bold=True, color=WHITE)
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = Border(left=Side(style='thick', color=CREAM), right=Side(style='thick', color=CREAM))
        col += 1
    ws.row_dimensions[6].height = 12
    ws.freeze_panes = 'A6'


def hdr(ws, r, c, text, w=1, color=DSAGE):
    cell = ws.cell(r, c, text)
    cell.fill = fill(color); cell.font = Font(name=BF, size=9.5, bold=True, color=WHITE)
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    if w > 1:
        ws.merge_cells(start_row=r, start_column=c, end_row=r, end_column=c + w - 1)
    return cell


def inp(ws, r, c, v=None, fmt=None, wrap=False, align='center'):
    cell = ws.cell(r, c)
    if v is not None and not BLANK:
        cell.value = v
    cell.fill = fill(INPUT); cell.border = box
    cell.font = Font(name=BF, size=10, color='1F3B73')
    cell.alignment = Alignment(horizontal=align, vertical='center', wrap_text=wrap)
    cell.protection = Protection(locked=False)
    if fmt:
        cell.number_format = fmt
    return cell


def fx(ws, r, c, f, fmt=None, bold=False, bg=WHITE, align='center', size=10):
    cell = ws.cell(r, c, f)
    cell.fill = fill(bg); cell.border = box
    cell.font = Font(name=BF, size=size, bold=bold, color=CHAR)
    cell.alignment = Alignment(horizontal=align, vertical='center', wrap_text=True)
    if fmt:
        cell.number_format = fmt
    return cell


def label(ws, r, c, text, bold=False, size=10, color=CHAR, wrap=True, align='left', italic=False):
    cell = ws.cell(r, c, text)
    cell.font = Font(name=BF, size=size, bold=bold, color=color, italic=italic)
    cell.alignment = Alignment(horizontal=align, vertical='center', wrap_text=wrap)
    return cell


def tip(ws, r, c, text, w=8):
    cell = ws.cell(r, c, text)
    cell.fill = fill(SOFT); cell.font = Font(name=BF, size=9, italic=True, color=MUTED)
    cell.alignment = Alignment(vertical='center', wrap_text=True)
    ws.merge_cells(start_row=r, start_column=c, end_row=r, end_column=c + w - 1)
    ws.row_dimensions[r].height = 30


def dv_list(ws, items, rng):
    dv = DataValidation(type='list', formula1='"' + ','.join(items) + '"', allow_blank=True)
    ws.add_data_validation(dv); dv.add(rng)


def protect(ws):
    ws.protection.sheet = True
    ws.protection.formatCells = False
    ws.protection.formatColumns = False
    ws.protection.formatRows = False


# ------------------------------------------------------------------ Settings
ws = sheets['Settings']
base(ws, 'Settings', 'Fill in the yellow boxes once. Everything else updates on its own.', 10, 40, {2: 34, 3: 22})
label(ws, 7, 2, 'Partner A name', True); inp(ws, 7, 3, 'Sam')
label(ws, 8, 2, 'Partner B name', True); inp(ws, 8, 3, 'Alex')
label(ws, 9, 2, 'Currency symbol (any: $, £, €, A$...)', True); inp(ws, 9, 3, '$').value = '$'
label(ws, 10, 2, 'Year you are looking back on', True); inp(ws, 10, 3, 2026, '0').value = 2026
label(ws, 11, 2, 'Goal year', True); fx(ws, 11, 3, '=IF(C10="","",C10+1)', '0')
tip(ws, 13, 2, 'Rename the spending categories below to fit your life. The Spending Review and the dashboard use these names.', 6)
hdr(ws, 15, 2, 'Spending categories')
CATS = ['Home (rent or mortgage)', 'Bills and utilities', 'Groceries', 'Transport', 'Eating out and takeaway', 'Shopping',
        'Travel and holidays', 'Kids and pets', 'Gifts and celebrations', 'Health and fitness']
for i, c in enumerate(CATS):
    cell = inp(ws, 16 + i, 2, c, align='left')
    if BLANK:
        cell.value = c  # keep category names in the blank copy
tip(ws, 27, 2, 'Amounts are plain numbers, so the workbook works in any currency. Pale yellow = type here. White = worked out for you.', 6)
protect(ws)
label(ws, 7, 5, 'Who list (used by Goals)', True, 8, MUTED)
fx(ws, 8, 5, 'Both'); fx(ws, 9, 5, '=IF(C7="","Partner A",C7)'); fx(ws, 10, 5, '=IF(C8="","Partner B",C8)')
ws.column_dimensions['E'].width = 16
NA, NB, CUR, YR, GY = 'IF(Settings!$C$7="","Partner A",Settings!$C$7)', 'IF(Settings!$C$8="","Partner B",Settings!$C$8)', "Settings!$C$9", "Settings!$C$10", "Settings!$C$11"

# ------------------------------------------------------------------ Year in Numbers
ws = sheets['Year in Numbers']
base(ws, 'Step 1: Our year in numbers', 'One row per month. Rough numbers from your bank app are fine.', 11, 40,
     {2: 14, 3: 14, 4: 14, 5: 14, 6: 14, 7: 15, 8: 14, 9: 14, 10: 13})
heads = ['Month', '=' + NA + '&" income"', '=' + NB + '&" income"', 'Total income', 'Spending', 'Saved or invested',
         'Extra debt paid', 'Left over', 'Savings rate']
for j, h in enumerate(heads):
    hdr(ws, 7, 2 + j, h)
ws.row_dimensions[7].height = 32
inc_a = [3200, 3200, 3250, 3250, 3250, 3400, 3400, 3400, 3400, 3400, 3400, 3900]
inc_b = [2650, 2700, 2600, 2900, 2750, 2700, 2600, 2800, 3100, 2750, 2700, 2900]
spend = [4300, 4050, 4400, 4250, 4600, 4700, 5600, 5200, 4300, 4350, 4550, 5900]
saved = [800, 900, 700, 900, 650, 700, 300, 400, 900, 850, 800, 500]
debt = [300, 300, 300, 400, 300, 300, 100, 250, 400, 300, 300, 150]
for i, m in enumerate(MONTHS):
    r = 8 + i
    fx(ws, r, 2, m[:3], bg=SOFT, bold=True)
    inp(ws, r, 3, inc_a[i], MONEY); inp(ws, r, 4, inc_b[i], MONEY)
    fx(ws, r, 5, f'=IF(COUNT(C{r}:D{r})=0,"",SUM(C{r}:D{r}))', MONEY)
    inp(ws, r, 6, spend[i], MONEY); inp(ws, r, 7, saved[i], MONEY); inp(ws, r, 8, debt[i], MONEY)
    fx(ws, r, 9, f'=IF(E{r}="","",E{r}-SUM(F{r}:H{r}))', MONEY)
    fx(ws, r, 10, f'=IF(N(E{r})=0,"",G{r}/E{r})', PCT)
r = 20
fx(ws, r, 2, 'Year total', bold=True, bg=SAGE)
for c in range(3, 10):
    fx(ws, r, c, f'=SUM({L(c)}8:{L(c)}19)', MONEY, True, SAGE)
fx(ws, r, 10, '=IF(E20=0,"",G20/E20)', PCT, True, SAGE)
fx(ws, 21, 2, 'Monthly average', bold=True, bg=SOFT)
for c in range(3, 10):
    fx(ws, 21, c, f'=IF(COUNT({L(c)}8:{L(c)}19)=0,"",AVERAGE({L(c)}8:{L(c)}19))', MONEY, False, SOFT)
fx(ws, 21, 10, '', bg=SOFT)
tip(ws, 23, 2, 'Left over = income minus spending, saving and extra debt payments. If it is negative, that month ran on savings or credit. '
    'Nobody gets every month right: look for the pattern, not the perfect number.', 9)
ws.row_dimensions[23].height = 40
protect(ws)
YN = S('Year in Numbers')

# ------------------------------------------------------------------ Spending Review
ws = sheets['Spending Review']
base(ws, 'Step 2: Where the money went', 'Total for the year per category. Then decide together: was it worth it?', 10, 40,
     {2: 26, 3: 14, 4: 13, 5: 10, 6: 13, 7: 14, 8: 15, 9: 14})
heads = ['Category', 'Year total', 'Per month', 'Share', 'Worth it?', 'Next year', 'Plan per month', 'Change per month']
for j, h in enumerate(heads):
    hdr(ws, 7, 2 + j, h)
ws.row_dimensions[7].height = 30
tot = [21000, 4300, 9600, 3900, 4100, 3450, 4800, 2100, 1800, 1150]
worth = ['Yes', 'Yes', 'Yes', 'Partly', 'Partly', 'No', 'Yes', 'Yes', 'Partly', 'Yes']
nxt = ['Keep', 'Cut back', 'Keep', 'Keep', 'Cut back', 'Cut back', 'Spend more', 'Keep', 'Cut back', 'Keep']
plan = [1650, 330, 740, 325, 220, 180, 420, 175, 120, 100]
for i in range(10):
    r = 8 + i
    fx(ws, r, 2, f'=IF(Settings!B{16 + i}="","",Settings!B{16 + i})', bg=SOFT, bold=True, align='left')
    inp(ws, r, 3, tot[i], MONEY)
    fx(ws, r, 4, f'=IF(C{r}="","",C{r}/12)', MONEY)
    fx(ws, r, 5, f'=IF(OR(C{r}="",N($C$18)=0),"",C{r}/$C$18)', PCT)
    inp(ws, r, 6, worth[i]); inp(ws, r, 7, nxt[i]); inp(ws, r, 8, plan[i], MONEY)
    fx(ws, r, 9, f'=IF(OR(H{r}="",D{r}=""),"",H{r}-D{r})', '+#,##0;-#,##0;0')
for i in range(10):
    ws.cell(8 + i, 13, f'=IF(C{8 + i}="","",C{8 + i}+ROW()/1000000)')
ws.column_dimensions['M'].hidden = True
dv_list(ws, ['Yes', 'Partly', 'No'], 'F8:F17'); dv_list(ws, ['Keep', 'Cut back', 'Spend more'], 'G8:G17')
fx(ws, 18, 2, 'Total', bold=True, bg=SAGE)
fx(ws, 18, 3, '=SUM(C8:C17)', MONEY, True, SAGE); fx(ws, 18, 4, '=SUM(D8:D17)', MONEY, True, SAGE)
fx(ws, 18, 5, '=IF(N(C18)=0,"",SUM(E8:E17))', PCT, True, SAGE)
fx(ws, 18, 6, '', bg=SAGE); fx(ws, 18, 7, '', bg=SAGE)
fx(ws, 18, 8, '=SUM(H8:H17)', MONEY, True, SAGE); fx(ws, 18, 9, '=IF(COUNT(I8:I17)=0,"",SUM(I8:I17))', '+#,##0;-#,##0;0', True, SAGE)
label(ws, 20, 2, 'Check against Step 1', True)
label(ws, 21, 2, 'Spending total in Step 1'); fx(ws, 21, 3, f'={YN}!F20', MONEY)
label(ws, 22, 2, 'Difference'); fx(ws, 22, 3, '=C18-C21', '+#,##0;-#,##0;0')
fx(ws, 22, 4, '=IF(N(C21)=0,"",IF(ABS(C22)<=C21*0.05,"Close enough","Worth a look"))', bg=SOFT)
ws.merge_cells('D22:E22')
label(ws, 24, 2, 'Spending we called "worth it"', True); fx(ws, 24, 3, '=SUMIF(F8:F17,"Yes",C8:C17)', MONEY)
fx(ws, 24, 4, '=IF(N(C18)=0,"",C24/C18)', PCT)
label(ws, 25, 2, 'Spending we would cut', True); fx(ws, 25, 3, '=SUMIF(G8:G17,"Cut back",C8:C17)', MONEY)
fx(ws, 25, 4, '=IF(N(C18)=0,"",C25/C18)', PCT)
tip(ws, 27, 2, 'Why "worth it?" first: people judge spending more kindly when they look at what it bought, not just the total. '
    'Agree on what to protect before you decide what to cut, and the cutting talk gets much calmer.', 8)
ws.row_dimensions[27].height = 42
protect(ws)
SR = S('Spending Review')

# ------------------------------------------------------------------ Net Worth
ws = sheets['Net Worth']
base(ws, 'Step 3: Net worth, start vs end of year', 'What you own minus what you owe, on 1 January and 31 December.', 8, 40,
     {2: 30, 3: 16, 4: 16, 5: 16, 6: 12})
for j, h in enumerate(['What we own', 'Start of year', 'End of year', 'Change']):
    hdr(ws, 7, 2 + j, h)
ASSETS = ['Joint savings', '=' + NA + '&" savings"', '=' + NB + '&" savings"', 'Pensions and retirement', 'Home value (if you own)', 'Other (car, investments)']
a_s = [4200, 6100, 2300, 38000, 0, 6500]; a_e = [9800, 7400, 3900, 44500, 0, 5200]
for i, a in enumerate(ASSETS):
    r = 8 + i
    fx(ws, r, 2, a, bg=SOFT, bold=True, align='left') if a.startswith('=') else label(ws, r, 2, a, True)
    if not a.startswith('='):
        ws.cell(r, 2).fill = fill(SOFT); ws.cell(r, 2).border = box
    inp(ws, r, 3, a_s[i], MONEY); inp(ws, r, 4, a_e[i], MONEY)
    fx(ws, r, 5, f'=IF(COUNT(C{r}:D{r})=0,"",N(D{r})-N(C{r}))', '+#,##0;-#,##0;0')
fx(ws, 14, 2, 'Total we own', bold=True, bg=SAGE, align='left')
for c in (3, 4, 5):
    fx(ws, 14, c, f'=SUM({L(c)}8:{L(c)}13)', MONEY if c < 5 else '+#,##0;-#,##0;0', True, SAGE)
for j, h in enumerate(['What we owe', 'Start of year', 'End of year', 'Change']):
    hdr(ws, 16, 2 + j, h, color=GOLD)
DEBTS = ['Credit cards', 'Car finance', 'Student loans', 'Mortgage', 'Other loans']
d_s = [2900, 7400, 21000, 0, 0]; d_e = [600, 4600, 19800, 0, 0]
for i, a in enumerate(DEBTS):
    r = 17 + i
    c = label(ws, r, 2, a, True); c.fill = fill(SOFT); c.border = box
    inp(ws, r, 3, d_s[i], MONEY); inp(ws, r, 4, d_e[i], MONEY)
    fx(ws, r, 5, f'=IF(COUNT(C{r}:D{r})=0,"",N(D{r})-N(C{r}))', '+#,##0;-#,##0;0')
fx(ws, 22, 2, 'Total we owe', bold=True, bg=SAGE, align='left')
for c in (3, 4, 5):
    fx(ws, 22, c, f'=SUM({L(c)}17:{L(c)}21)', MONEY if c < 5 else '+#,##0;-#,##0;0', True, SAGE)
hdr(ws, 24, 2, 'Our net worth'); hdr(ws, 24, 3, 'Start of year'); hdr(ws, 24, 4, 'End of year'); hdr(ws, 24, 5, 'Change')
fx(ws, 25, 2, 'Own minus owe', bold=True, bg=SOFT, align='left')
fx(ws, 25, 3, '=C14-C22', MONEY, True); fx(ws, 25, 4, '=D14-D22', MONEY, True)
fx(ws, 25, 5, '=D25-C25', '+#,##0;-#,##0;0', True)
fx(ws, 26, 2, 'Debt paid down this year', bold=True, bg=SOFT, align='left')
fx(ws, 26, 3, '', bg=WHITE); fx(ws, 26, 4, '=MAX(0,C22-D22)', MONEY, True); fx(ws, 26, 5, '', bg=WHITE)
hdr(ws, 30, 2, 'For the dashboard chart'); hdr(ws, 30, 3, 'Start'); hdr(ws, 30, 4, 'End')
for i, (lab, rr) in enumerate((('Own', 14), ('Owe', 22), ('Net worth', 25))):
    fx(ws, 31 + i, 2, lab, bg=SOFT, align='left'); fx(ws, 31 + i, 3, f'=C{rr}', MONEY); fx(ws, 31 + i, 4, f'=D{rr}', MONEY)
tip(ws, 28, 2, 'Net worth is just a scoreboard for the two of you, not a judgement. A rising line matters more than the size of the number.', 5)
ws.row_dimensions[28].height = 36
protect(ws)
NW = S('Net Worth')

# ------------------------------------------------------------------ Year in Review
ws = sheets['Year in Review']
base(ws, 'Step 4: Looking back together', 'Answer on your own first, then read each other\'s answers and fill in "Together".', 6, 40,
     {2: 34, 3: 30, 4: 30, 5: 30})
hdr(ws, 7, 2, 'Question'); hdr(ws, 7, 3, '=' + NA); hdr(ws, 7, 4, '=' + NB); hdr(ws, 7, 5, 'Together')
Q = [
    ('Our biggest money win this year', 'Paid off the credit card in May', 'Finally started a joint savings pot', 'We cleared a debt AND built a buffer'),
    ('Money we spent that was worth every penny', 'The Lisbon trip', 'Lisbon. And the new mattress', 'Travel is a "protect" category'),
    ('Money we spent that we would skip next time', 'Takeaways on weeknights', 'Subscriptions we forgot about', 'Cancel 3 subs, plan 2 cook nights'),
    ('A money moment that stressed us out', 'The July car repair', 'December, again', 'We need a buffer for big months'),
    ('What I learned about how you handle money', 'You worry more than you say', 'You like a plan, not a lecture', 'Check in monthly, not in a crisis'),
    ('One habit to keep', 'Sunday money check', 'Auto-saving on payday', 'Payday auto-save + Sunday check'),
    ('One habit to drop', 'Buying when bored', 'Avoiding the bank app', 'One "wait 48 hours" rule each'),
    ('If next year goes well, what is different by December?', 'A 3-month buffer', 'Car loan gone', 'Buffer built, car loan cleared, a trip paid in cash'),
]
for i, (q, a, b, t) in enumerate(Q):
    r = 8 + i
    c = label(ws, r, 2, q, True); c.fill = fill(SOFT); c.border = box
    inp(ws, r, 3, a, wrap=True, align='left'); inp(ws, r, 4, b, wrap=True, align='left'); inp(ws, r, 5, t, wrap=True, align='left')
    ws.row_dimensions[r].height = 46
label(ws, 17, 2, 'Our word for this money year', True)
inp(ws, 17, 3, 'Steadier', align='left')
label(ws, 18, 2, 'Our word for next year', True)
inp(ws, 18, 3, 'Ahead', align='left')
tip(ws, 20, 2, 'Why answer apart first: when one person speaks first, the other tends to anchor on their answer. '
    'Writing first means you hear what each of you really thinks.', 4)
ws.row_dimensions[20].height = 40
protect(ws)

# ------------------------------------------------------------------ 2027 Goals
ws = sheets['2027 Goals']
base(ws, '=Settings!C11&" goals: 3 to 5 shared goals"', 'Pick a few, give each one a number and a month. The sheet works out the monthly amount.', 11, 40,
     {2: 5, 3: 28, 4: 12, 5: 13, 6: 13, 7: 13, 8: 14, 9: 13, 10: 30})
ws['B2'].value = '=Settings!C11&" goals: 3 to 5 shared goals"'
heads = ['#', 'Goal', 'Type', 'Target', 'Already have', 'Finish by month (1-12)', 'Needed per month', 'Who', 'Why it matters to us']
for j, h in enumerate(heads):
    hdr(ws, 7, 2 + j, h)
ws.row_dimensions[7].height = 32
G = [('3-month emergency buffer', 'Save', 9000, 3000, 12, 'Both', 'No more panic when the car breaks'),
     ('Clear the car loan', 'Pay off', 4600, 0, 10, 'Sam', 'One less bill before the baby talk'),
     ('Summer trip, paid in cash', 'Spend on', 2400, 0, 8, 'Both', 'Holidays without the credit card'),
     ('Wedding fund', 'Save', 4000, 500, 12, 'Both', 'Start married life debt-free'),
     ('', '', None, None, None, '', '')]
for i, g in enumerate(G):
    r = 8 + i
    fx(ws, r, 2, i + 1, bg=SOFT, bold=True)
    inp(ws, r, 3, g[0] or None, align='left'); inp(ws, r, 4, g[1] or None)
    inp(ws, r, 5, g[2], MONEY); inp(ws, r, 6, g[3], MONEY); inp(ws, r, 7, g[4], '0')
    fx(ws, r, 8, f'=IF(OR(N(E{r})=0,N(G{r})=0),"",MAX(0,(E{r}-N(F{r}))/G{r}))', MONEY, True)
    inp(ws, r, 9, g[5] or None); inp(ws, r, 10, g[6] or None, wrap=True, align='left')
    ws.row_dimensions[r].height = 30
dv_list(ws, ['Save', 'Pay off', 'Spend on'], 'D8:D12')
dvw = DataValidation(type='list', formula1='Settings!$E$8:$E$10', allow_blank=True); ws.add_data_validation(dvw); dvw.add('I8:I12')
dv = DataValidation(type='whole', operator='between', formula1='1', formula2='12', allow_blank=True,
                    error='Type a month number from 1 to 12', showErrorMessage=True)
ws.add_data_validation(dv); dv.add('G8:G12')
fx(ws, 13, 3, 'All goals together', bold=True, bg=SAGE, align='left')
for c in (4, 7, 9, 10):
    fx(ws, 13, c, '', bg=SAGE)
fx(ws, 13, 5, '=SUM(E8:E12)', MONEY, True, SAGE); fx(ws, 13, 6, '=SUM(F8:F12)', MONEY, True, SAGE)
fx(ws, 13, 8, '=SUM(H8:H12)', MONEY, True, SAGE)
hdr(ws, 15, 3, 'Reality check: do the goals fit?', 3)
label(ws, 16, 3, 'Average saved + debt + left over per month last year')
fx(ws, 16, 5, f'=IF(COUNT({YN}!G8:G19)=0,"",{YN}!G21+{YN}!H21+{YN}!I21)', MONEY, True)
label(ws, 17, 3, 'Goals need per month')
fx(ws, 17, 5, '=H13', MONEY, True)
label(ws, 18, 3, 'Planned cuts from the Spending Review')
fx(ws, 18, 5, f'=IF({SR}!I18="","",MAX(0,-{SR}!I18))', MONEY, True)
label(ws, 19, 3, 'Room left each month', True)
fx(ws, 19, 5, '=IF(E16="","",E16+N(E18)-E17)', '+#,##0;-#,##0;0', True, SAGE)
fx(ws, 20, 3, '=IF(E19="","",IF(E19>=0,"These goals fit. Set up the monthly transfers on payday.","Too much at once: push a finish month back or lower a target until this is 0 or more."))',
   bg=SOFT, align='left')
ws.merge_cells('C20:H20'); ws.row_dimensions[20].height = 30
for r in (16, 17, 18):
    ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=4)
ws.merge_cells('C19:D19')
tip(ws, 22, 3, 'Why a monthly number: a big goal feels far away, so it slides. A monthly amount set up as a payday transfer turns a wish into a habit '
    'you do not have to remember.', 7)
ws.row_dimensions[22].height = 40
protect(ws)
GL = S('2027 Goals')

# ------------------------------------------------------------------ Monthly Check-ins
ws = sheets['Monthly Check-ins']
base(ws, 'Step 6: Monthly check-ins', 'At each money date, type what you put towards each goal that month. Progress updates on its own.', 10, 45,
     {2: 13, 3: 15, 4: 15, 5: 15, 6: 15, 7: 15, 8: 13, 9: 40})
hdr(ws, 7, 2, 'Month')
for k in range(5):
    hdr(ws, 7, 3 + k, f'=IF({GL}!C{8 + k}="","Goal {k + 1}",{GL}!C{8 + k})')
hdr(ws, 7, 8, 'Money date done?'); hdr(ws, 7, 9, 'One-line note')
ws.row_dimensions[7].height = 44
SAMPLE_CI = [[500, 460, 300, 300, None, 'Yes', 'Good start. Car loan overpayment set up'],
             [500, 460, 300, 300, None, 'Yes', 'Birthday month, still hit every goal'],
             [450, 460, 250, 300, None, 'Yes', 'Boiler service hit us, buffer got less'],
             [500, 460, 400, 450, None, '', '']]
for i, m in enumerate(MONTHS):
    r = 8 + i
    fx(ws, r, 2, m, bg=SOFT, bold=True)
    row = SAMPLE_CI[i] if i < 3 else [None] * 7
    for k in range(5):
        inp(ws, r, 3 + k, row[k], MONEY)
    inp(ws, r, 8, row[5] or None); inp(ws, r, 9, row[6] or None, wrap=True, align='left')
dv_list(ws, ['Yes', 'No'], 'H8:H19')
for i in range(12):
    r = 8 + i
    ws.cell(r, 13, f'=IF(OR(H{r}="Yes",COUNT(C{r}:G{r})>0),1,0)')
ws.column_dimensions['M'].hidden = True; ws.column_dimensions['N'].hidden = True
hdr(ws, 21, 2, 'Goal progress', 8, GOLD)
for j, h in enumerate(['Goal', 'Target', 'Start', 'Added so far', 'Progress', 'Done', 'Expected by now', 'Status']):
    hdr(ws, 22, 2 + j, h)
ws.row_dimensions[22].height = 30
for k in range(5):
    r = 23 + k
    g = 8 + k
    col = L(3 + k)
    fx(ws, r, 2, f'=IF({GL}!C{g}="","Goal {k + 1}",{GL}!C{g})', bg=SOFT, bold=True, align='left')
    fx(ws, r, 3, f'=IF(N({GL}!E{g})=0,"",{GL}!E{g})', MONEY)
    fx(ws, r, 4, f'=IF(C{r}="","",N({GL}!F{g}))', MONEY)
    fx(ws, r, 5, f'=IF(C{r}="","",SUM({col}8:{col}19))', MONEY)
    fx(ws, r, 6, f'=IF(C{r}="","",D{r}+E{r})', MONEY, True)
    fx(ws, r, 7, f'=IF(C{r}="","",MIN(1,F{r}/C{r}))', PCT, True)
    fx(ws, r, 8, f'=IF(C{r}="","",MIN(C{r},D{r}+N({GL}!H{g})*SUM($M$8:$M$19)))', MONEY)
    ws.cell(r, 14, f'=IF(C{r}="",0,MIN(F{r},C{r}))')
    fx(ws, r, 9, f'=IF(C{r}="","",IF(F{r}>=C{r},"Done",IF(N({GL}!G{g})=0,"Add a finish month in Step 5",IF(F{r}>=H{r},"On track","Behind: add a little next month"))))', bg=SOFT)
label(ws, 29, 2, 'Money dates done', True); fx(ws, 29, 4, '=COUNTIF(H8:H19,"Yes")', '0', True)
ws.merge_cells('B29:C29')
label(ws, 30, 2, 'Total added to goals', True); fx(ws, 30, 4, '=SUM(C8:G19)', MONEY, True)
ws.merge_cells('B30:C30')
tip(ws, 32, 2, '"Expected by now" uses the monthly amount from Step 5 times the money dates you have marked Yes. '
    'Behind is fine: it just tells you which goal needs a little more next month.', 8)
ws.row_dimensions[32].height = 36
protect(ws)
CI = S('Monthly Check-ins')

# ------------------------------------------------------------------ Money Date
ws = sheets['Money Date']
base(ws, 'Your 30-minute monthly money date', 'Same day each month. Snacks allowed. Phones down, this sheet open.', 8, 40,
     {2: 8, 3: 30, 4: 60})
hdr(ws, 7, 2, 'Min'); hdr(ws, 7, 3, 'Step'); hdr(ws, 7, 4, 'What to do')
AG = [('5', 'One win each', 'Start with something that went well with money this month. Small counts.'),
      ('10', 'Log the month', 'Fill in this month on the Monthly Check-ins tab: what went to each goal, then mark the money date Yes.'),
      ('5', 'Check the goals', 'Look at Status. Behind on one? Agree a small top-up, or move its finish month. No blame.'),
      ('5', 'Look ahead', 'Any big costs next month: birthdays, renewals, trips? Plan for them now.'),
      ('5', 'One nice thing', 'Pick one small treat or plan for next month that you both look forward to.')]
for i, (m, s, w) in enumerate(AG):
    r = 8 + i
    fx(ws, r, 2, m, bold=True, bg=SOFT); fx(ws, r, 3, s, bold=True, align='left'); fx(ws, r, 4, w, align='left')
    ws.row_dimensions[r].height = 38
hdr(ws, 14, 3, 'Every 3 months, also', 2, GOLD)
for i, t in enumerate(['Open the Spending Review: are the "cut back" categories actually smaller?',
                       'Update the Net Worth tab with today\'s balances, so you can see the line move.',
                       'Ask: is each goal still the right goal? It is fine to change one.']):
    fx(ws, 15 + i, 3, '•', bg=WHITE); fx(ws, 15 + i, 4, t, align='left'); ws.row_dimensions[15 + i].height = 30
tip(ws, 19, 3, 'Ground rules: no blame for the past, talk about the plan not the person, and stop at 30 minutes even if you are not done.', 2)
ws.row_dimensions[19].height = 36
protect(ws)

# ------------------------------------------------------------------ Start Here
ws = sheets['Start Here']
base(ws, 'Start here', 'About 90 minutes for the whole review, in one sitting or two evenings. Then 30 minutes a month.', 8, 45,
     {2: 8, 3: 34, 4: 70})
steps = [('', 'Settings', 'Type your names, your currency symbol and the year. Rename the spending categories if you like.'),
         ('1', 'Year in Numbers', 'Income, spending, saving and extra debt payments for each month. Rough numbers are fine.'),
         ('2', 'Spending Review', 'The year total for each category. Then: was it worth it, and what changes next year?'),
         ('3', 'Net Worth', 'What you owned and owed on 1 January and 31 December.'),
         ('4', 'Year in Review', 'Eight questions. Answer apart first, then fill in "Together".'),
         ('5', 'Goals', 'Pick 3 to 5 shared goals. The sheet works out what each needs per month and checks they fit.'),
         ('6', 'Monthly Check-ins', 'Each month, log what went to each goal. Use the Money Date tab as your agenda.')]
hdr(ws, 7, 2, 'Step'); hdr(ws, 7, 3, 'Tab'); hdr(ws, 7, 4, 'What you do')
for i, (n, t, w) in enumerate(steps):
    r = 8 + i
    fx(ws, r, 2, n, bold=True, bg=SOFT)
    tgt = 'Settings' if t == 'Settings' else ('2027 Goals' if t == 'Goals' else t)
    c = fx(ws, r, 3, t, bold=True, align='left')
    c.hyperlink = Hyperlink(ref=c.coordinate, location=f"{S(tgt)}!A1", display=t)
    c.font = Font(name=BF, size=10, bold=True, color='2F5E8A', underline='single')
    fx(ws, r, 4, w, align='left'); ws.row_dimensions[r].height = 32
hdr(ws, 16, 3, 'Good to know', 2, GOLD)
GTK = ['Pale yellow boxes are for typing. White boxes work themselves out, so they are locked to keep the sums safe.',
       'Two copies are in your download: one filled in for an example couple (Sam and Alex) so you can see how it works, '
       'and a blank one for you. Open the blank one to start.',
       'Google Sheets: File > Import > Upload, or open the file in Google Drive and choose File > Save as Google Sheets.',
       'Excel: open as normal. The tabs at the top of every page are buttons: click one to jump there.',
       'Any currency: amounts are plain numbers. Set your symbol on the Settings tab for the dashboard.',
       'Questions: joel@wayofwealthcoaching.com']
for i, t in enumerate(GTK):
    fx(ws, 17 + i, 3, '•'); fx(ws, 17 + i, 4, t, align='left'); ws.row_dimensions[17 + i].height = 34
tip(ws, 24, 3, 'General information, not financial or tax advice.', 2)
protect(ws)

# ------------------------------------------------------------------ Dashboard
ws = sheets['Dashboard']
base(ws, '="Our "&IF(Settings!C10="","",Settings!C10&" ")&"money year, together"', '', 13, 90, {**{c: 12.5 for c in range(2, 14)}, 11: 20})
ws['B2'].value = '="Our "&IF(Settings!C10="","",Settings!C10&" ")&"money year, together"'
ws['B3'].value = '='+NA+'&" and "&'+NB+'&IF(Settings!C10="","","  ·  looking back on "&Settings!C10&", planning "&Settings!C11)'


def card(r, c, title, f, fmt, sub):
    ws.merge_cells(start_row=r, start_column=c, end_row=r, end_column=c + 2)
    ws.merge_cells(start_row=r + 1, start_column=c, end_row=r + 1, end_column=c + 2)
    ws.merge_cells(start_row=r + 2, start_column=c, end_row=r + 2, end_column=c + 2)
    for rr in range(r, r + 3):
        for cc in range(c, c + 3):
            ws.cell(rr, cc).fill = fill(WHITE)
    t = ws.cell(r, c, title); t.font = Font(name=BF, size=9, bold=True, color=DSAGE); t.alignment = Alignment(horizontal='left', indent=1, vertical='bottom')
    v = ws.cell(r + 1, c, f); v.font = Font(name=TF, size=22, bold=True, color=CHAR); v.alignment = Alignment(horizontal='left', indent=1, vertical='center')
    if fmt:
        v.number_format = fmt
    s = ws.cell(r + 2, c, sub); s.font = Font(name=BF, size=8.5, color=MUTED); s.alignment = Alignment(horizontal='left', indent=1, vertical='top')
    # gold top bar
    for cc in range(c, c + 3):
        ws.cell(r, cc).border = Border(top=Side(style='thick', color=GOLD))


money = lambda ref: f'=IF(N({ref})=0,"–",{CUR}&TEXT({ref},"#,##0"))'
for rr in (7, 11):
    ws.row_dimensions[rr].height = 20; ws.row_dimensions[rr + 1].height = 34; ws.row_dimensions[rr + 2].height = 18
ws.row_dimensions[10].height = 10
card(7, 2, 'TOTAL INCOME', money(f'{YN}!E20'), None, '="Both of you, "&IF(Settings!C10="","this year",Settings!C10)')
card(7, 5, 'TOTAL SPENT', money(f'{YN}!F20'), None, f'=IF(N({YN}!F21)=0,"",{CUR}&TEXT({YN}!F21,"#,##0")&" a month on average")')
card(7, 8, 'SAVED OR INVESTED', money(f'{YN}!G20'), None, f'=IF({YN}!J20="","","That is "&TEXT({YN}!J20,"0%")&" of income")')
card(7, 11, 'EXTRA DEBT PAID', money(f'{YN}!H20'), None, f'=IF(COUNT({NW}!C17:D21)=0,"",IF(N({NW}!D22)=0,"Debt now cleared","Debt now "&{CUR}&TEXT({NW}!D22,"#,##0")))')
card(11, 2, 'NET WORTH CHANGE', f'=IF(COUNT({NW}!C8:D13,{NW}!C17:D21)=0,"–",IF({NW}!E25>=0,"+","-")&{CUR}&TEXT(ABS({NW}!E25),"#,##0"))', None,
     f'=IF(COUNT({NW}!C8:D13,{NW}!C17:D21)=0,"","From "&IF({NW}!C25<0,"-","")&{CUR}&TEXT(ABS({NW}!C25),"#,##0")&" to "&IF({NW}!D25<0,"-","")&{CUR}&TEXT(ABS({NW}!D25),"#,##0"))')
card(11, 5, 'SPENDING "WORTH IT"', f'=IF({SR}!D24="","–",{SR}!D24)', PCT, f'=IF(N({SR}!C25)=0,"","Cutting back on "&TEXT({SR}!D25,"0%")&" of spending")')
card(11, 8, '=IF(Settings!C11="","GOALS","GOALS FOR "&Settings!C11)', f'=COUNTA({GL}!C8:C12)', '0', f'=IF(N({GL}!H13)=0,"",{CUR}&TEXT({GL}!H13,"#,##0")&" a month for all goals")')
card(11, 11, 'GOAL PROGRESS', f'=IF(N({CI}!C28)=0,"–",{CI}!G28)', PCT, f'={CI}!D29&" of 12 money dates done"')

# helper rows for goal totals in Check-ins (row 28)
ci = sheets['Monthly Check-ins']
fx(ci, 28, 2, 'All goals', bold=True, bg=SAGE, align='left')
fx(ci, 28, 3, '=SUM(C23:C27)', MONEY, True, SAGE); fx(ci, 28, 4, '=SUM(D23:D27)', MONEY, True, SAGE)
fx(ci, 28, 5, '=SUM(E23:E27)', MONEY, True, SAGE); fx(ci, 28, 6, '=SUM(F23:F27)', MONEY, True, SAGE)
fx(ci, 28, 7, '=IF(N(C28)=0,"",SUM(N23:N27)/C28)', PCT, True, SAGE); fx(ci, 28, 8, '=SUM(H23:H27)', MONEY, True, SAGE)
fx(ci, 28, 9, '', bg=SAGE)
# move the counters down one row so they don't collide
for (r_old, r_new) in ((29, 30), (30, 31)):
    pass

# small tables
ws.row_dimensions[14].height = 12
hdr(ws, 15, 2, 'Top 3 spending categories', 4, GOLD)
hdr(ws, 16, 2, 'Category', 2); hdr(ws, 16, 4, 'Year'); hdr(ws, 16, 5, 'Share')
for k in range(3):
    r = 17 + k
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
    fx(ws, r, 2, f'=IF(COUNT({SR}!C8:C17)<{k + 1},"",INDEX({SR}!B8:B17,MATCH(LARGE({SR}!M8:M17,{k + 1}),{SR}!M8:M17,0)))', align='left')
    fx(ws, r, 4, f'=IF(B{r}="","",INDEX({SR}!C8:C17,MATCH(LARGE({SR}!M8:M17,{k + 1}),{SR}!M8:M17,0)))', MONEY)
    fx(ws, r, 5, f'=IF(OR(D{r}="",N({SR}!C18)=0),"",D{r}/{SR}!C18)', PCT)
hdr(ws, 15, 7, 'Best and toughest month', 3, GOLD)
hdr(ws, 16, 7, ''); hdr(ws, 16, 8, 'Month'); hdr(ws, 16, 9, 'Left over')
fx(ws, 17, 7, 'Best', bold=True, bg=SOFT)
fx(ws, 17, 8, f'=IF(COUNT({YN}!I8:I19)=0,"",INDEX({YN}!B8:B19,MATCH(MAX({YN}!I8:I19),{YN}!I8:I19,0)))')
fx(ws, 17, 9, f'=IF(H17="","",MAX({YN}!I8:I19))', '+#,##0;-#,##0;0')
fx(ws, 18, 7, 'Toughest', bold=True, bg=SOFT)
fx(ws, 18, 8, f'=IF(COUNT({YN}!I8:I19)=0,"",INDEX({YN}!B8:B19,MATCH(MIN({YN}!I8:I19),{YN}!I8:I19,0)))')
fx(ws, 18, 9, f'=IF(H18="","",MIN({YN}!I8:I19))', '+#,##0;-#,##0;0')
fx(ws, 19, 7, 'Average', bold=True, bg=SOFT); fx(ws, 19, 8, '–')
fx(ws, 19, 9, f'=IF(COUNT({YN}!I8:I19)=0,"",{YN}!I21)', '+#,##0;-#,##0;0')
hdr(ws, 15, 11, 'Goals at a glance', 3, GOLD)
hdr(ws, 16, 11, 'Goal'); hdr(ws, 16, 12, 'Done'); hdr(ws, 16, 13, 'Status')
for k in range(5):
    r = 17 + k
    fx(ws, r, 11, f'=IF({GL}!C{8 + k}="","",{GL}!C{8 + k})', align='left', size=9)
    fx(ws, r, 12, f'=IF(K{r}="","",{CI}!G{23 + k})', PCT)
    fx(ws, r, 13, f'=IF(K{r}="","",IF({CI}!I{23 + k}="","Add a target",IF({CI}!I{23 + k}="Done","Done",IF({CI}!I{23 + k}="On track","On track",IF(LEFT({CI}!I{23 + k},3)="Add","Add a month","Behind")))))', size=9)
for r in range(16, 22):
    ws.row_dimensions[r].height = 26

# chart data block (hidden helper area, columns P-T)
ws['P7'] = 'Chart data'
ws['P8'] = 'Own'; ws['P9'] = 'Owe'; ws['P10'] = 'Net worth'
ws['Q7'] = 'Start'; ws['R7'] = 'End'
ws['Q8'] = f'={NW}!C14'; ws['R8'] = f'={NW}!D14'
ws['Q9'] = f'={NW}!C22'; ws['R9'] = f'={NW}!D22'
ws['Q10'] = f'={NW}!C25'; ws['R10'] = f'={NW}!D25'
for k in range(5):
    ws.cell(12 + k, 16, f'=IF({GL}!C{8 + k}="","Goal {k + 1}",{GL}!C{8 + k})')
    ws.cell(12 + k, 17, f'=IF({CI}!G{23 + k}="",0,{CI}!G{23 + k})')
ws['P11'] = 'Goal'; ws['Q11'] = 'Done'
for col in 'PQRST':
    ws.column_dimensions[col].hidden = True

yn = sheets['Year in Numbers']; sr = sheets['Spending Review']


def style(ch, title):
    ch.title = title
    ch.style = 2
    ch.height = 7.6; ch.width = 14.8
    ch.legend.position = 'b'
    ch.plotVisOnly = False
    ch.x_axis.delete = False; ch.y_axis.delete = False
    return ch


c1 = style(BarChart(), 'Income vs spending, month by month')
c1.type = 'col'; c1.grouping = 'clustered'; c1.overlap = -10
c1.add_data(Reference(yn, min_col=5, min_row=7, max_row=19), titles_from_data=True)
c1.add_data(Reference(yn, min_col=6, min_row=7, max_row=19), titles_from_data=True)
c1.set_categories(Reference(yn, min_col=2, min_row=8, max_row=19))
c1.series[0].graphicalProperties.solidFill = DSAGE; c1.series[1].graphicalProperties.solidFill = GOLD
c1.y_axis.numFmt = '#,##0'; c1.y_axis.majorGridlines = None
ws.add_chart(c1, 'B24')

c2 = style(LineChart(), 'Saved or invested each month')
c2.add_data(Reference(yn, min_col=7, min_row=7, max_row=19), titles_from_data=True)
c2.set_categories(Reference(yn, min_col=2, min_row=8, max_row=19))
c2.series[0].graphicalProperties.line.solidFill = DSAGE; c2.series[0].graphicalProperties.line.width = 38000
c2.series[0].smooth = False; c2.y_axis.scaling.min = 0
c2.y_axis.numFmt = '#,##0'; c2.legend = None; c2.y_axis.majorGridlines = None
ws.add_chart(c2, 'H24')

c3 = style(BarChart(), 'Where the money went')
c3.type = 'bar'
c3.add_data(Reference(sr, min_col=3, min_row=7, max_row=17), titles_from_data=True)
c3.set_categories(Reference(sr, min_col=2, min_row=8, max_row=17))
c3.series[0].graphicalProperties.solidFill = DSAGE
c3.legend = None; c3.x_axis.scaling.orientation = 'maxMin'; c3.y_axis.numFmt = '#,##0'; c3.y_axis.majorGridlines = None
ws.add_chart(c3, 'B40')

c4 = style(BarChart(), 'Net worth: start vs end of year')
c4.type = 'col'
nwws = sheets['Net Worth']
c4.add_data(Reference(nwws, min_col=3, max_col=4, min_row=30, max_row=33), titles_from_data=True)
c4.set_categories(Reference(nwws, min_col=2, min_row=31, max_row=33))
c4.series[0].graphicalProperties.solidFill = SAGE; c4.series[1].graphicalProperties.solidFill = GOLD
c4.y_axis.numFmt = '#,##0'; c4.y_axis.majorGridlines = None
ws.add_chart(c4, 'H40')

c5 = style(BarChart(), '="Goal progress"')
c5.title = 'Goal progress so far'
c5.type = 'bar'
c5.add_data(Reference(ci, min_col=7, min_row=22, max_row=27), titles_from_data=True)
c5.set_categories(Reference(ci, min_col=2, min_row=23, max_row=27))
c5.series[0].graphicalProperties.solidFill = GOLD
c5.legend = None; c5.x_axis.scaling.orientation = 'maxMin'
c5.y_axis.scaling.min = 0; c5.y_axis.scaling.max = 1; c5.y_axis.numFmt = '0%'; c5.y_axis.majorGridlines = None
c5.width = 30.2
ws.add_chart(c5, 'B56')
protect(ws)

# print setup: each sheet one page wide
for ws in wb.worksheets:
    ws.page_setup.orientation = 'landscape'
    ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_options.horizontalCentered = True
sheets['Dashboard'].print_area = 'A1:N72'
sheets['Dashboard'].page_setup.fitToHeight = 1
sheets['Dashboard'].page_setup.orientation = 'portrait'

wb.active = 0
wb.save(OUT)
print('saved', OUT)
