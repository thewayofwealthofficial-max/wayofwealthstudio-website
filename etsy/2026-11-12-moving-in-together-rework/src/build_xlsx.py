"""Moving In Together Money Planner (11 Nov standard rework) - Way of Wealth Studio.
python3 build_xlsx.py out/file.xlsx [blank]
"""
import sys, os, datetime as dt
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
from skin import *
from openpyxl.chart import Reference
from openpyxl.worksheet.datavalidation import DataValidation

OUT = sys.argv[1]; BLANK = len(sys.argv) > 2 and sys.argv[2] == 'blank'
TABS = [('Dashboard', GOLD), ('Start Here', DSAGE), ('Settings', DSAGE), ('Move-In Costs', DSAGE), ('Shared Bills', DSAGE),
        ('Year View', DSAGE), ('Settle Up', DSAGE), ('Move-In Savings', DSAGE), ('Money Talk', DSAGE)]
B = Book(TABS, BLANK)
S = B.s
NA, NB, CUR = 'Settings!$G$8', 'Settings!$G$9', 'Settings!$C$9'
PA, PB = 'Settings!$C$18', 'Settings!$C$19'
MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
MONARR = '{"' + '","'.join(MON) + '"}'
money = lambda x: f'{CUR}&TEXT({x},"#,##0")'

# ------------------------------------------------------------------ Settings
ws = S['Settings']
B.page(ws, 'Settings', 'Fill in the yellow boxes once. Every other tab updates on its own.', {2: 36, 3: 20, 4: 3, 5: 40, 6: 3, 7: 18},
       ncols=6)
rows = [('Partner A name', 'Sam', None, True), ('Partner B name', 'Alex', None, True), ('Currency symbol ($, £, €, A$...)', '$', None, True),
        ("Partner A monthly take-home pay", 3400, MONEY, False), ("Partner B monthly take-home pay", 2600, MONEY, False),
        ('How we split shared costs', 'By income', None, True), ('If "Custom": Partner A pays (%)', 0.6, PCT, False),
        ('Move-in date', dt.date(2027, 3, 1), 'd mmm yyyy', False), ('Already saved for the move', 1200, MONEY, False),
        ('Start saving for the move from', dt.date(2026, 7, 1), 'mmm yyyy', False)]
B.th(ws, 6, 2, 'YOUR DETAILS'); B.th(ws, 6, 3, 'TYPE HERE'); B.th(ws, 6, 5, 'WHAT IT DOES')
help_ = ['Shown on every tab and in the dashboard sentences.', '', 'Any currency works: amounts are plain numbers.',
         'After tax. Only used for the "By income" split.', '', 'By income (fair share of what you earn), 50-50, or Custom.',
         'Only used when the split is Custom. Type it with the % sign, e.g. 60%.', 'Sets the countdown and the 12-month Year View.',
         'Counts towards your move-in fund.', 'First month on the Move-In Savings tab.']
for i, (lab, v, fmt, keep) in enumerate(rows):
    r = 7 + i
    B.text(ws, r, 2, lab, 10, True)
    B.inp(ws, r, 3, v, fmt, keep=keep if lab != 'Partner A name' and lab != 'Partner B name' else False)
    B.text(ws, r, 5, help_[i], 9, color=MUTED)
    ws.row_dimensions[r].height = 22
B.dv(ws, 'C12', ['By income', '50-50', 'Custom'])
_d = DataValidation(type='decimal', operator='between', formula1='0', formula2='1', showErrorMessage=True,
                    errorTitle='Percent', error='Type a percentage between 0% and 100%, e.g. 60%')
ws.add_data_validation(_d); _d.add('C13')
B.text(ws, 18 - 1, 2, 'OUR SPLIT (WORKED OUT FOR YOU)', 8, True, MUTED)
B.text(ws, 18, 2, '="Share "&G8&" pays"', 10, True)
B.fx(ws, 18, 3, '=IF(C12="50-50",0.5,IF(C12="Custom",MIN(1,MAX(0,N(C13))),IF(N(C10)+N(C11)=0,0.5,N(C10)/(N(C10)+N(C11)))))', PCT, True, TINT)
B.text(ws, 19, 2, '="Share "&G9&" pays"', 10, True)
B.fx(ws, 19, 3, '=1-C18', PCT, True, TINT)
B.tip(ws, 21, 2, 'Why split by income? Paying the same amount can leave the lower earner with almost nothing to spend. '
      'Splitting by income means you each put in the same share of what you earn.', 4, 1, 44)
# lists (helper, pale)
B.text(ws, 6, 7, 'LISTS (USED BY DROPDOWNS)', 7, True, 'B9B2A6')
for r, f in [(7, 'Shared'), (8, '=IF(TRIM(C7)="","Partner A",TRIM(C7))'), (9, '=IF(TRIM(C8)="","Partner B",TRIM(C8))'),
             (11, 'Our split'), (12, '50-50'), (13, '=G8&" only"'), (14, '=G9&" only"')]:
    B.text(ws, r, 7, f, 8, False, 'A79F92')
B.protect(ws)

# ------------------------------------------------------------------ Move-In Costs
ws = S['Move-In Costs']
B.page(ws, 'Move-in costs', 'Everything the move will cost, who pays it and what is paid already.',
       {2: 30, 3: 24, 4: 12, 5: 14, 6: 12, 7: 13, 8: 13, 9: 12}, ncols=8, nrows=60)
heads = [('ITEM', 'left'), ('CATEGORY', 'left'), ('COST', 'right'), ('WHO PAYS', 'left'), ('STATUS', 'left'),
         ('="A: "&' + NA, 'right'), ('="B: "&' + NB, 'right'), ('PAID', 'right')]
for j, (h, a) in enumerate(heads):
    B.th(ws, 7, 2 + j, h, align=a)
CATS = ['Deposit and first rent', 'Moving', 'Furniture', 'Kitchen and appliances', 'Setup and connection fees', 'Cleaning and repairs', 'Other']
items = [('Security deposit', 0, 2400, 'Shared', 'Paid'), ("First month's rent", 0, 2200, 'Shared', 'Booked'),
         ('Moving van and helpers', 1, 650, 'Shared', 'Booked'), ('Sofa', 2, 900, 'Shared', 'Planned'),
         ('Bed and mattress', 2, 1100, 'Sam', 'Planned'), ('Kitchen basics', 3, 350, 'Shared', 'Planned'),
         ('Washing machine', 3, 480, 'Shared', 'Planned'), ('Internet setup', 4, 60, 'Shared', 'Planned'),
         ('End-of-lease clean (old place)', 5, 180, 'Shared', 'Planned'), ('Curtains and blinds', 2, 220, 'Alex', 'Planned'),
         ('Storage boxes', 1, 70, 'Shared', 'Paid'), ('New locks and keys', 4, 90, 'Shared', 'Planned')]
R1, R2 = 8, 37
for r in range(R1, R2 + 1):
    it = items[r - R1] if r - R1 < len(items) else None
    B.inp(ws, r, 2, it[0] if it else None)
    B.inp(ws, r, 3, CATS[it[1]] if it else None)
    B.inp(ws, r, 4, it[2] if it else None, MONEY, 'right')
    B.inp(ws, r, 5, it[3] if it else None)
    B.inp(ws, r, 6, it[4] if it else None)
    B.fx(ws, r, 7, f'=IF(N(D{r})=0,"",IF(E{r}={NA},D{r},IF(E{r}={NB},0,D{r}*{PA})))', MONEY)
    B.fx(ws, r, 8, f'=IF(G{r}="","",D{r}-G{r})', MONEY)
    B.fx(ws, r, 9, f'=IF(AND(F{r}="Paid",N(D{r})>0),D{r},"")', MONEY)
B.dv(ws, f'C{R1}:C{R2}', CATS)
B.dv(ws, f'E{R1}:E{R2}', ref='=Settings!$G$7:$G$9')
B.dv(ws, f'F{R1}:F{R2}', ['Planned', 'Booked', 'Paid'])
T = R2 + 1
B.fx(ws, T, 2, 'Total', bold=True, bg=TINT, align='left')
for c in range(3, 10):
    B.fx(ws, T, c, '' if c in (3, 5, 6) else f'=SUM({L(c)}{R1}:{L(c)}{R2})', MONEY, True, TINT)
B.tip(ws, T + 2, 2, 'Who pays: "Shared" splits the cost by your Settings split. Pick a name when one of you pays it all '
      '(for example, furniture you bring). Leave a row blank and it is ignored.', 8, 1, 34)
B.protect(ws)
MC = "'Move-In Costs'"

# ------------------------------------------------------------------ Shared Bills
ws = S['Shared Bills']
B.page(ws, 'Shared bills', 'Every bill you will share once you live together, turned into a monthly amount and split.',
       {2: 26, 3: 22, 4: 11, 5: 12, 6: 11, 7: 15, 8: 12, 9: 12, 10: 12, 11: 9, 12: 3, 13: 6, 14: 6}, ncols=10, nrows=50)
heads = [('BILL', 'left'), ('CATEGORY', 'left'), ('AMOUNT', 'right'), ('HOW OFTEN', 'left'), ('FIRST DUE', 'left'),
         ('SPLIT', 'left'), ('PER MONTH', 'right'), ('="A: "&' + NA, 'right'), ('="B: "&' + NB, 'right'), ('DUE DAY', 'right')]
for j, (h, a) in enumerate(heads):
    B.th(ws, 7, 2 + j, h, align=a)
B.text(ws, 7, 13, 'helper', 7, color='C9C2B6'); B.text(ws, 7, 14, 'helper', 7, color='C9C2B6')
BCATS = ['Rent or mortgage', 'Energy', 'Water', 'Internet and phone', 'Home or property tax', 'Insurance', 'Groceries',
         'Subscriptions', 'Transport', 'Household', 'Other']
bills = [('Rent', 0, 2200, 'Monthly', '', 'Our split', 1), ('Electricity and gas', 1, 140, 'Monthly', '', 'Our split', 12),
         ('Water', 2, 45, 'Monthly', '', 'Our split', 15), ('Internet', 3, 55, 'Monthly', '', '50-50', 20),
         ('Home or property tax', 4, 160, 'Monthly', '', 'Our split', 1), ("Renters' insurance", 5, 240, 'Yearly', 'Mar', 'Our split', 5),
         ('Groceries', 6, 650, 'Monthly', '', 'Our split', ''), ('Streaming', 7, 28, 'Monthly', '', '50-50', 8),
         ('Cleaning and household', 9, 40, 'Monthly', '', '50-50', ''), ('Window cleaning', 9, 90, 'Quarterly', 'Apr', '50-50', 3)]
R1, R2 = 8, 32
for r in range(R1, R2 + 1):
    b = bills[r - R1] if r - R1 < len(bills) else None
    B.inp(ws, r, 2, b[0] if b else None); B.inp(ws, r, 3, BCATS[b[1]] if b else None)
    B.inp(ws, r, 4, b[2] if b else None, MONEY, 'right'); B.inp(ws, r, 5, b[3] if b else None)
    B.inp(ws, r, 6, (b[4] or None) if b else None); B.inp(ws, r, 7, b[5] if b else None)
    B.inp(ws, r, 11, (b[6] or None) if b else None, '0', 'right')
    B.fx(ws, r, 8, f'=IF(N(D{r})=0,"",D{r}*IF(E{r}="Weekly",52/12,IF(E{r}="Quarterly",1/3,IF(E{r}="Yearly",1/12,1))))', MONEY)
    B.fx(ws, r, 9, f'=IF(H{r}="","",H{r}*M{r})', MONEY)
    B.fx(ws, r, 10, f'=IF(H{r}="","",H{r}-I{r})', MONEY)
    c = ws.cell(r, 13, f'=IF(G{r}=Settings!$G$13,1,IF(G{r}=Settings!$G$14,0,IF(G{r}="50-50",0.5,{PA})))'); c.font = F(7, color='C9C2B6'); c.number_format = '0.00'
    c = ws.cell(r, 14, f'=IFERROR(MATCH(F{r},{MONARR},0),1)'); c.font = F(7, color='C9C2B6')
B.dv(ws, f'C{R1}:C{R2}', BCATS); B.dv(ws, f'E{R1}:E{R2}', ['Monthly', 'Weekly', 'Quarterly', 'Yearly'])
B.dv(ws, f'F{R1}:F{R2}', MON); B.dv(ws, f'G{R1}:G{R2}', ref='=Settings!$G$11:$G$14')
T = R2 + 1
B.fx(ws, T, 2, 'Total per month', bold=True, bg=TINT, align='left')
for c in range(3, 12):
    B.fx(ws, T, c, f'=SUM({L(c)}{R1}:{L(c)}{R2})' if c in (8, 9, 10) else '', MONEY, True, TINT)
B.tip(ws, T + 2, 2, 'First due: only for quarterly and yearly bills (the month the first one lands), so the Year View puts them in the right month. '
      'Split: "Our split" uses Settings; pick "50-50" or one name for anything else.', 9, 1, 34)
ws.column_dimensions['M'].hidden = True; ws.column_dimensions['N'].hidden = True
B.protect(ws)
SB = "'Shared Bills'"

# ------------------------------------------------------------------ Year View
ws = S['Year View']
B.page(ws, 'Year view', 'Your first 12 months living together: what lands each month and what each of you pays.',
       {2: 16, 3: 16, 4: 16, 5: 16, 6: 18, 7: 3}, ncols=8, nrows=40)
for j, (h, a) in enumerate([('MONTH', 'left'), ('BILLS DUE', 'right'), ('="A: "&' + NA, 'right'), ('="B: "&' + NB, 'right'),
                            ('RUNNING TOTAL', 'right')]):
    B.th(ws, 7, 2 + j, h, align=a)
rng = lambda col: f"{SB}!${col}$8:${col}$32"
due = (f"{rng('D')}*(({rng('E')}=\"Monthly\")+({rng('E')}=\"Weekly\")*52/12+({rng('E')}=\"Quarterly\")*(MOD(MONTH(B{{r}})-{rng('N')},3)=0)"
       f"+({rng('E')}=\"Yearly\")*(MONTH(B{{r}})={rng('N')}))")
for i in range(12):
    r = 8 + i
    B.fx(ws, r, 2, f'=EDATE(IF(Settings!$C$14="",DATE(YEAR(TODAY()),MONTH(TODAY()),1),DATE(YEAR(Settings!$C$14),MONTH(Settings!$C$14),1)),{i})',
         'mmm yyyy', True, align='left')
    B.fx(ws, r, 3, f'=SUMPRODUCT({due.format(r=r)})', MONEY)
    B.fx(ws, r, 4, f'=SUMPRODUCT({due.format(r=r)}*{rng("M")})', MONEY)
    B.fx(ws, r, 5, f'=C{r}-D{r}', MONEY)
    B.fx(ws, r, 6, f'=SUM($C$8:C{r})', MONEY)
B.fx(ws, 20, 2, 'Year total', bold=True, bg=TINT, align='left')
for c in (3, 4, 5):
    B.fx(ws, 20, c, f'=SUM({L(c)}8:{L(c)}19)', MONEY, True, TINT)
B.fx(ws, 20, 6, '', bg=TINT)
B.fx(ws, 21, 2, 'Biggest month', bold=True, bg=WHITE, align='left')
B.fx(ws, 21, 3, '=MAX(C8:C19)', MONEY, True, WHITE)
B.fx(ws, 21, 4, '=IF(C21=0,"",TEXT(INDEX(B8:B19,MATCH(C21,C8:C19,0)),"mmmm"))', None, False, WHITE, 'left', 2)
B.tip(ws, 23, 2, 'Quarterly and yearly bills make some months bigger. Spot them here and put a little aside in the quiet months.', 5, 1, 34)
B.protect(ws)

# ------------------------------------------------------------------ Settle Up
ws = S['Settle Up']
B.page(ws, 'Settle up', 'Log shared spending as it happens. It works out who owes whom, so nobody keeps score in their head.',
       {2: 13, 3: 30, 4: 12, 5: 14, 6: 15, 7: 13, 8: 13, 9: 16}, ncols=8, nrows=70)
B.box(ws, 7, 2, 7, 9, NAVY, NAVY)
B.text(ws, 7, 2, '=IF(ABS(SUM(I10:I59))<0.005,"All square: nobody owes anybody.",IF(SUM(I10:I59)>0,'
       f'{NB}&" owes "&{NA}&" "&{CUR}&TEXT(SUM(I10:I59),"#,##0.00"),{NA}&" owes "&{NB}&" "&{CUR}&TEXT(-SUM(I10:I59),"#,##0.00")))',
       14, True, WHITE, w=8, indent=1)
ws.row_dimensions[7].height = 34
heads = [('DATE', 'left'), ('WHAT', 'left'), ('AMOUNT', 'right'), ('PAID BY', 'left'), ('WHO IT WAS FOR', 'left'),
         ('="A share"', 'right'), ('="B share"', 'right'), ('OWED TO A (+) / B (-)', 'right')]
for j, (h, a) in enumerate(heads):
    B.th(ws, 9, 2 + j, h, align=a)
log = [(dt.date(2027, 3, 2), 'Big first food shop', 186.40, 'Sam', 'Our split'), (dt.date(2027, 3, 4), 'Paint and brushes', 64.00, 'Alex', 'Our split'),
       (dt.date(2027, 3, 6), 'Takeaway on moving day', 38.50, 'Alex', '50-50'), (dt.date(2027, 3, 9), 'Shower curtain and towels', 52.00, 'Sam', 'Our split'),
       (dt.date(2027, 3, 12), "Alex's new desk lamp", 29.99, 'Sam', 'Alex only'), (dt.date(2027, 3, 15), 'Hardware store', 47.20, 'Sam', 'Our split'),
       (dt.date(2027, 3, 18), 'Plants for the balcony', 41.00, 'Sam', '50-50'), (dt.date(2027, 3, 21), 'Groceries', 132.75, 'Sam', 'Our split')]
for r in range(10, 60):
    e = log[r - 10] if r - 10 < len(log) else None
    B.inp(ws, r, 2, e[0] if e else None, 'd mmm', 'left'); B.inp(ws, r, 3, e[1] if e else None)
    B.inp(ws, r, 4, e[2] if e else None, MONEY2, 'right'); B.inp(ws, r, 5, e[3] if e else None)
    B.inp(ws, r, 6, e[4] if e else None)
    B.fx(ws, r, 7, f'=IF(N(D{r})=0,"",D{r}*IF(F{r}=Settings!$G$13,1,IF(F{r}=Settings!$G$14,0,IF(F{r}="50-50",0.5,{PA}))))', MONEY2)
    B.fx(ws, r, 8, f'=IF(G{r}="","",D{r}-G{r})', MONEY2)
    B.fx(ws, r, 9, f'=IF(G{r}="","",IF(E{r}={NA},H{r},IF(E{r}={NB},-G{r},0)))', '+#,##0.00;-#,##0.00;"–"')
B.dv(ws, 'E10:E59', ref='=Settings!$G$8:$G$9'); B.dv(ws, 'F10:F59', ref='=Settings!$G$11:$G$14')
B.text(ws, 9, 7, '="A: "&' + NA, 8, True, MUTED, align='right'); B.text(ws, 9, 8, '="B: "&' + NB, 8, True, MUTED, align='right')
B.protect(ws)

# ------------------------------------------------------------------ Move-In Savings
ws = S['Move-In Savings']
B.page(ws, 'Move-in savings', 'What you each put aside each month until the move is covered.',
       {2: 14, 3: 14, 4: 14, 5: 14, 6: 16, 7: 22, 8: 3, 9: 10, 10: 10}, ncols=7, nrows=50)
B.th(ws, 7, 2, 'TARGET', align='right'); B.th(ws, 7, 3, 'SAVED', align='right'); B.th(ws, 7, 4, 'LEFT', align='right')
B.th(ws, 7, 5, 'MONTHS LEFT', align='right'); B.th(ws, 7, 6, 'NEEDED A MONTH', align='right')
B.fx(ws, 8, 2, f"={MC}!D38", MONEY, True, TINT); B.fx(ws, 8, 3, '=Settings!C15+SUM(E12:E35)', MONEY, True, TINT)
B.fx(ws, 8, 4, '=MAX(0,B8-C8)', MONEY, True, TINT)
B.fx(ws, 8, 5, '=IF(Settings!C14="","",MAX(1,IFERROR(DATEDIF(TODAY(),Settings!C14,"m"),1)))', '0', True, TINT)
B.fx(ws, 8, 6, '=IF(OR(D8=0,E8=""),0,D8/E8)', MONEY, True, TINT)
B.fx(ws, 8, 7, f'=IF(B8=0,"Add your move-in costs",IF(D8=0,"Move covered",{NA}&" "&{CUR}&TEXT(F8*IFERROR({MC}!G38/{MC}!D38,{PA}),"#,##0")&" / "&{NB}&" "&{CUR}&TEXT(F8*IFERROR({MC}!H38/{MC}!D38,{PB}),"#,##0")))', None, False, TINT, 'left')
for j, (h, a) in enumerate([('MONTH', 'left'), ('="A: "&' + NA, 'right'), ('="B: "&' + NB, 'right'), ('TOGETHER', 'right'),
                            ('MOVE FUND', 'right'), ('PROGRESS', 'left')]):
    B.th(ws, 11, 2 + j, h, align=a)
sa = [250, 300, 300, 350, 300]; sb = [200, 200, 250, 250, 250]
for i in range(24):
    r = 12 + i
    B.fx(ws, r, 2, f'=EDATE(IF(Settings!$C$16="",DATE(YEAR(TODAY()),MONTH(TODAY()),1),DATE(YEAR(Settings!$C$16),MONTH(Settings!$C$16),1)),{i})', 'mmm yyyy', True, align='left')
    B.inp(ws, r, 3, sa[i] if i < 5 else None, MONEY, 'right'); B.inp(ws, r, 4, sb[i] if i < 5 else None, MONEY, 'right')
    B.fx(ws, r, 5, f'=IF(COUNT(C{r}:D{r})=0,"",SUM(C{r}:D{r}))', MONEY)
    B.fx(ws, r, 6, f'=IF(E{r}="","",Settings!$C$15+SUM($E$12:E{r}))', MONEY)
    B.fx(ws, r, 7, f'=IF(OR(F{r}="",N($B$8)=0),"",REPT("█",ROUND(MIN(1,F{r}/$B$8)*12,0))&REPT("░",12-ROUND(MIN(1,F{r}/$B$8)*12,0))&"  "&TEXT(MIN(1,F{r}/$B$8),"0%"))',
         None, False, None, 'left', color=DSAGE)
B.protect(ws)

# ------------------------------------------------------------------ Money Talk
ws = S['Money Talk']
B.page(ws, 'The money talk', '12 questions to agree before you share a home. Tick them off together, one evening or over a few weeks.',
       {2: 5, 3: 58, 4: 14, 5: 50}, ncols=4, nrows=40)
B.th(ws, 7, 2, '#'); B.th(ws, 7, 3, 'QUESTION'); B.th(ws, 7, 4, 'AGREED?'); B.th(ws, 7, 5, 'WHAT WE DECIDED')
Q = ['How do we split rent and bills: 50-50, by income, or another way?', 'Joint account, separate accounts, or both?',
     'Who pays the move-in costs, and who keeps what if we ever split up?', 'How much can each of us spend without checking first?',
     'What happens in a month when one of us earns less?', 'What debts does each of us bring, and are they shared or personal?',
     'How much do we save each month, and what for?', 'Who looks after which bills and due dates?',
     'How do we handle groceries and eating out?', 'How do we pay for guests, holidays and family visits?',
     'How often do we sit down to check our money? (We suggest once a month.)', 'If one of us moves out, how much notice, and who keeps the lease?']
agreed = ['Yes', 'Yes', 'Yes', 'Not yet', 'Yes', 'Not yet', 'Yes', 'Yes', 'Not yet', 'Not yet', 'Yes', 'Not yet']
notes = ['By income, about 57 / 43. Review when pay changes.', 'Joint account for bills, own accounts for the rest.',
         'Shared items split by our split. Sam keeps the bed.', '', '50-50 that month, catch up later.', '', '$550 a month, move fund first.',
         'Sam: rent and energy. Alex: internet and insurance.', '', '', 'First Sunday of the month.', '']
for i, q in enumerate(Q):
    r = 8 + i
    B.fx(ws, r, 2, i + 1, '0', True, align='center', color=GOLD)
    B.fx(ws, r, 3, q, None, False, align='left')
    ws.cell(r, 3).alignment = Alignment(wrap_text=True, vertical='center', indent=1)
    B.inp(ws, r, 4, agreed[i]); B.inp(ws, r, 5, notes[i] or None)
    ws.row_dimensions[r].height = 30
B.dv(ws, 'D8:D19', ['Yes', 'Not yet', 'Skip'])
B.fx(ws, 21, 3, '="Agreed: "&COUNTIF(D8:D19,"Yes")&" of 12"', None, True, TINT, 'left')
B.fx(ws, 21, 4, '=REPT("█",COUNTIF(D8:D19,"Yes"))&REPT("░",12-COUNTIF(D8:D19,"Yes"))', None, False, TINT, 'left', 2, DSAGE)
B.tip(ws, 23, 3, 'Tip: start with the easy ones (2, 8, 11). Talk about what you want, not what went wrong before. '
      'There is no wrong answer, only one you both agree to.', 3, 1, 36)
B.protect(ws)

# ------------------------------------------------------------------ Start Here
ws = S['Start Here']
B.page(ws, 'Start here', 'Five minutes to set up. Then just keep the yellow boxes up to date.', {2: 6, 3: 70, 4: 3}, ncols=3, nrows=40)
steps = [('1', 'Settings: your names, take-home pay, currency and how you want to split (by income, 50-50 or custom).'),
         ('2', 'Move-In Costs: list everything the move will cost and who pays. Mark items Paid as you go.'),
         ('3', 'Shared Bills: every bill you will share. Quarterly and yearly bills become a monthly amount.'),
         ('4', 'Year View: see your first 12 months, and the bigger months coming.'),
         ('5', 'Settle Up: log shared spending as it happens. It shows who owes whom.'),
         ('6', 'Move-In Savings: what you each put aside until the move is covered.'),
         ('7', 'Money Talk: 12 questions to agree before you move in.'),
         ('8', 'Dashboard: everything on one screen. Check it once a month together.')]
for i, (n, t) in enumerate(steps):
    r = 7 + i * 2
    B.box(ws, r, 2, r, 3)
    B.text(ws, r, 2, n, 16, True, GOLD, align='center'); B.text(ws, r, 3, t, 10.5, indent=1)
    ws.row_dimensions[r].height = 34; ws.row_dimensions[r + 1].height = 6
B.tip(ws, 24, 2, 'Pale yellow = type here. White = worked out for you (locked in Excel so nothing breaks). '
      'Google Sheets: File > Import or open the .xlsx from Drive, then move between tabs with the tab bar at the bottom.', 2, 1, 44)
B.tip(ws, 26, 2, 'This file comes with example numbers so you can see it working. Use the BLANK copy to start your own. '
      'Questions: joel@wayofwealthcoaching.com', 2, 1, 36)
B.protect(ws)

# ------------------------------------------------------------------ Dashboard
ws = S['Dashboard']
B.page(ws, 'Moving In Together', 'Money plan', ncols=16, nrows=110)
ws['B3'] = '="Money plan for "&' + NA + '&" and "&' + NB + '&"  ·  move-in "&IF(Settings!C14="","date not set",TEXT(Settings!C14,"d mmm yyyy"))'
ws['B3'].font = F(10, color=MUTED)
for r, h in [(7, 22), (8, 30), (9, 18), (10, 8), (11, 22), (12, 30), (13, 18)]:
    ws.row_dimensions[r].height = h
billsA, billsB, billsT = f'{SB}!I33', f'{SB}!J33', f'{SB}!H33'
B.hero(ws, 7, 2, 7, 7, 'OUR SHARED BILLS EACH MONTH', f'={money(billsT)}',
       f'={NA}&" pays "&{money(billsA)}&"  ·  "&{NB}&" pays "&{money(billsB)}&".  Split: "&IF(Settings!C12="","By income",Settings!C12)&" ("&TEXT({PA},"0%")&" / "&TEXT({PB},"0%")&")"',
       'Monthly amount of every bill on Shared Bills, split your way.')
ws.row_dimensions[11].height = 22
B.kpi(ws, 7, 10, 'MOVE-IN COSTS', f'={money(MC + "!D38")}', f'=COUNT({MC}!D8:D37)&" items · "&{money(MC + "!I38")}&" paid"')
B.kpi(ws, 7, 14, 'SAVED FOR THE MOVE', f"={money(chr(39) + 'Move-In Savings' + chr(39) + '!C8')}",
      f"=IF(N('Move-In Savings'!B8)=0,\"\",TEXT(MIN(1,'Move-In Savings'!C8/'Move-In Savings'!B8),\"0%\")&\" of the target\")", accent=DSAGE)
B.kpi(ws, 11, 10, 'LEFT TO SAVE', f"={money(chr(39) + 'Move-In Savings' + chr(39) + '!D8')}",
      f"=IF('Move-In Savings'!B8=0,\"Add move-in costs first\",IF('Move-In Savings'!D8=0,\"Covered\",\"About \"&{money(chr(39) + 'Move-In Savings' + chr(39) + '!F8')}&\" a month\"))", accent=GOLD)
net = "SUM('Settle Up'!I10:I59)"
B.kpi(ws, 11, 14, 'SETTLE UP', f'=IF(ABS({net})<0.005,"All square",{CUR}&TEXT(ABS({net}),"#,##0"))',
      f'=IF(ABS({net})<0.005,"Nobody owes anybody",IF({net}>0,{NB}&" owes "&{NA},{NA}&" owes "&{NB}))', accent=CORAL)
# next step
nxt = (f'=IF(COUNT({MC}!D8:D37)=0,"Start with Settings, then list what the move will cost on Move-In Costs.",'
       f'IF(COUNTIF(\'Money Talk\'!D8:D19,"Yes")<12,"Have the Money Talk: "&(12-COUNTIF(\'Money Talk\'!D8:D19,"Yes"))&" questions still open. Agreeing now saves arguments later.",'
       f"IF('Move-In Savings'!D8>0,\"Save \"&{money(chr(39) + 'Move-In Savings' + chr(39) + '!F8')}&\" a month between you to cover the move in time.\","
       f'IF(ABS({net})>=0.005,"Settle up: "&IF({net}>0,{NB}&" owes "&{NA},{NA}&" owes "&{NB})&" "&{CUR}&TEXT(ABS({net}),"#,##0.00")&".","You are set: bills split, move covered, nobody owes anybody."))))')
B.bar(ws, 15, 2, 15, 'NEXT STEP', nxt)
for r, h in [(17, 22), (18, 30), (19, 18)]:
    ws.row_dimensions[r].height = h
B.kpi(ws, 17, 2, 'DAYS TO MOVE-IN', '=IF(Settings!C14="","Add a date",MAX(0,Settings!C14-TODAY()))', '=IF(Settings!C14="","in Settings",TEXT(Settings!C14,"d mmm yyyy"))', w=3, value_fmt='0')
B.kpi(ws, 17, 6, 'OUR SPLIT', f'=TEXT({PA},"0%")&" / "&TEXT({PB},"0%")', f'={NA}&" / "&{NB}')
B.kpi(ws, 17, 10, 'MONEY TALK', '=COUNTIF(\'Money Talk\'!D8:D19,"Yes")&" of 12"', '="agreed so far"')
B.kpi(ws, 17, 14, 'FIRST YEAR OF BILLS', f"={money(chr(39) + 'Year View' + chr(39) + '!C20')}",
      f"=\"Biggest: \"&IF('Year View'!D21=\"\",\"-\",'Year View'!D21)")
# chart data tables (visible: "the numbers behind the charts")
D0 = 70
B.section(ws, D0, 2, 'The numbers behind the charts', 10)
B.th(ws, D0 + 1, 2, 'MOVE-IN COSTS BY CATEGORY', 4); B.th(ws, D0 + 1, 6, 'COST', align='right'); B.th(ws, D0 + 1, 7, 'PAID', align='right')
for i, c in enumerate(CATS):
    r = D0 + 2 + i
    B.fx(ws, r, 2, c, align='left', w=4)
    B.fx(ws, r, 6, f'=SUMIF({MC}!$C$8:$C$37,B{r},{MC}!$D$8:$D$37)', MONEY)
    B.fx(ws, r, 7, f'=SUMIF({MC}!$C$8:$C$37,B{r},{MC}!$I$8:$I$37)', MONEY)
B.th(ws, D0 + 1, 10, 'WHO PAYS THE MOVE', 4); B.th(ws, D0 + 1, 14, 'AMOUNT', align='right')
B.fx(ws, D0 + 2, 10, f'={NA}', align='left', w=4); B.fx(ws, D0 + 2, 14, f'={MC}!G38', MONEY)
B.fx(ws, D0 + 3, 10, f'={NB}', align='left', w=4); B.fx(ws, D0 + 3, 14, f'={MC}!H38', MONEY)
B.th(ws, D0 + 5, 10, 'BILLS PER MONTH BY CATEGORY', 4); B.th(ws, D0 + 5, 14, 'PER MONTH', align='right')
for i, c in enumerate(BCATS):
    r = D0 + 6 + i
    B.fx(ws, r, 10, c, align='left', w=4)
    B.fx(ws, r, 14, f'=SUMIF({SB}!$C$8:$C$32,J{r},{SB}!$H$8:$H$32)', MONEY)
# charts
bar_chart(ws, 'B22', 'Move-in costs by category', Reference(ws, min_col=2, min_row=D0 + 2, max_row=D0 + 8),
          Reference(ws, min_col=6, min_row=D0 + 1, max_row=D0 + 8), w=11.8, h=7.4, horizontal=True, legend=False, colors=[DSAGE])
doughnut(ws, 'J22', 'Who pays the move', Reference(ws, min_col=10, min_row=D0 + 2, max_row=D0 + 3),
         Reference(ws, min_col=14, min_row=D0 + 1, max_row=D0 + 3), w=11.8, h=7.4, colors=[NAVY, GOLD])
YV = S['Year View']
ch = bar_chart(ws, 'B38', 'First 12 months: who pays what', Reference(YV, min_col=2, min_row=8, max_row=19),
               Reference(YV, min_col=4, max_col=5, min_row=7, max_row=19), w=11.8, h=7.4, stacked=True, colors=[NAVY, GOLD])
ch.x_axis.number_format = 'mmm'
bar_chart(ws, 'J38', 'Shared bills per month by category', Reference(ws, min_col=10, min_row=D0 + 6, max_row=D0 + 16),
          Reference(ws, min_col=14, min_row=D0 + 5, max_row=D0 + 16), w=11.8, h=7.4, horizontal=True, legend=False, colors=[GOLD])
SV = S['Move-In Savings']
lc = bar_chart(ws, 'B54', 'Move fund, month by month', Reference(SV, min_col=2, min_row=12, max_row=23),
               Reference(SV, min_col=6, min_row=11, max_row=23), w=11.8, h=7.4, legend=False, colors=[DSAGE])
lc.x_axis.number_format = 'mmm yy'
# side panel next to the line chart: upcoming big months
B.section(ws, 54, 10, 'Coming up', 7)
for j, (h, a) in enumerate([('MONTH', 'left'), ('BILLS', 'right'), ('="A"', 'right'), ('="B"', 'right')]):
    pass
B.th(ws, 55, 10, 'MONTH', 2); B.th(ws, 55, 12, 'BILLS', 2, 'right'); B.th(ws, 55, 14, '=' + NA, 1, 'right'); B.th(ws, 55, 15, '=' + NB, 2, 'right')
for i in range(6):
    r = 56 + i
    B.fx(ws, r, 10, f"='Year View'!B{8 + i}", 'mmm yyyy', True, align='left', w=2)
    B.fx(ws, r, 12, f"='Year View'!C{8 + i}", MONEY, w=2)
    B.fx(ws, r, 14, f"='Year View'!D{8 + i}", MONEY)
    B.fx(ws, r, 15, f"='Year View'!E{8 + i}", MONEY, w=2)
B.text(ws, 63, 10, 'Bigger months are where quarterly or yearly bills land.', 8.5, False, MUTED, w=7, italic=True)
B.protect(ws)

B.save(OUT)
print('saved', OUT)
