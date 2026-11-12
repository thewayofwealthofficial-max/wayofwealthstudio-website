"""Self-Employed Couples Budget (one partner self-employed) - Way of Wealth Studio.
Tax pot first, steady 'pay yourself' amount with a buffer for low months, then a fair split of shared bills.
python3 build_xlsx.py out/file.xlsx [blank]
"""
import sys, os, datetime as dt
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
from skin import *
from openpyxl.chart import Reference, BarChart
from openpyxl.chart.series import SeriesLabel

OUT = sys.argv[1]; BLANK = len(sys.argv) > 2 and sys.argv[2] == 'blank'
TABS = [('Dashboard', GOLD), ('Start Here', DSAGE), ('Settings', DSAGE), ('Income Log', DSAGE), ('Tax Pot', DSAGE),
        ('Buffer', DSAGE), ('Shared Bills', DSAGE), ('Monthly Split', DSAGE), ('Money Talk', DSAGE)]
B = Book(TABS, BLANK)
S = B.s
NA, NB, CUR = 'Settings!$G$8', 'Settings!$G$9', 'Settings!$C$9'
TAX, PAY, PA, PB = 'Settings!$C$10', 'Settings!$C$21', 'Settings!$C$22', 'Settings!$C$23'
money = lambda x: f'{CUR}&TEXT({x},"#,##0")'
IL, TP, BF, SB, MS = "'Income Log'", "'Tax Pot'", "'Buffer'", "'Shared Bills'", "'Monthly Split'"
R1, R2 = 9, 20  # 12 month rows on the monthly tabs

# ------------------------------------------------------------------ Settings
ws = S['Settings']
B.page(ws, 'Settings', 'Fill in the yellow boxes once. Every other tab updates on its own.', {2: 40, 3: 20, 4: 3, 5: 44, 6: 3, 7: 18}, ncols=6)
B.th(ws, 6, 2, 'YOUR DETAILS'); B.th(ws, 6, 3, 'TYPE HERE'); B.th(ws, 6, 5, 'WHAT IT DOES')
rows = [('Self-employed partner (A)', 'Jordan', None, False, 'The partner whose income goes up and down.'),
        ('Employed partner (B)', 'Riley', None, False, 'The partner with a regular paycheck.'),
        ('Currency symbol ($, £, €, A$...)', '$', None, True, 'Any currency works: amounts are plain numbers.'),
        ('Tax pot: % of profit set aside', 0.25, PCT, True, 'Set your own %. Many set aside 25-30%: check yours with an accountant or your tax office.'),
        ('First month of your tracking year', dt.date(2026, 1, 1) if not BLANK else dt.date(2027, 1, 1), 'mmm yyyy', True, 'Any month: January, April (UK tax year) or your own.'),
        ('How we split shared costs', 'By income', None, True, 'By income (after the tax pot), 50-50, or Custom.'),
        ('If "Custom": partner A pays (%)', 0.5, PCT, False, 'Only used when the split is Custom. Type it with the % sign, e.g. 60%.'),
        ('Buffer goal (months of shared costs)', 3, '0', True, 'A cushion so low months do not hurt. 3 months is a good start.'),
        ('Pay yourself (A), per month', 3000, MONEY, False, 'Leave blank and it uses A\'s average after-tax profit so far.'),
        ('Buffer: money already in it', 1500, MONEY, False, 'What sits in the buffer today.'),
        ('Tax pot: money already in it', 0, MONEY, False, 'What is already put aside for tax.'),
        ('Joint savings per month', 400, MONEY, False, 'Saved together each month, split like the bills.')]
for i, (lab, v, fmt, keep, hlp) in enumerate(rows):
    r = 7 + i
    B.text(ws, r, 2, lab, 10, True); B.inp(ws, r, 3, v, fmt, keep=keep); B.text(ws, r, 5, hlp, 9, color=MUTED)
    ws.row_dimensions[r].height = 24
B.dv(ws, 'C12', ['By income', '50-50', 'Custom'])
B.text(ws, 20, 2, 'WORKED OUT FOR YOU', 8, True, MUTED)
B.text(ws, 21, 2, '="Pay yourself: "&G8&" takes home each month"', 10, True)
B.fx(ws, 21, 3, f"=IF(N(C15)>0,C15,IF(COUNT({IL}!G{R1}:G{R2})=0,0,MAX(0,SUM({IL}!G{R1}:G{R2})/COUNT({IL}!G{R1}:G{R2}))))", MONEY, True, TINT)
B.text(ws, 22, 2, '="Share of shared costs "&G8&" pays"', 10, True)
B.fx(ws, 22, 3, f"=IF(C12=\"50-50\",0.5,IF(C12=\"Custom\",MIN(1,MAX(0,N(C13))),IF(C21+N({IL}!H23)<=0,0.5,MIN(1,MAX(0,C21/(C21+N({IL}!H23)))))))", PCT, True, TINT)
B.text(ws, 23, 2, '="Share of shared costs "&G9&" pays"', 10, True)
B.fx(ws, 23, 3, '=1-C22', PCT, True, TINT)
B.tip(ws, 25, 2, 'The idea: business money comes in, the tax share goes straight to the tax pot, and the self-employed partner pays '
      'themself the same steady amount every month. Good months fill the buffer, low months draw on it. Shared bills are then split from steady pay, not from a lucky month.', 4, 1, 58)
B.text(ws, 6, 7, 'LISTS', 7, True, 'B9B2A6')
for r, f in [(8, '=IF(TRIM(C7)="","Partner A",TRIM(C7))'), (9, '=IF(TRIM(C8)="","Partner B",TRIM(C8))'),
             (11, 'Our split'), (12, '50-50'), (13, '=G8&" only"'), (14, '=G9&" only"'),
             (16, "=SUMPRODUCT(MAX(('Monthly Split'!J8:J19<>\"\")*ROW('Monthly Split'!J8:J19)))"),
             (17, "=SUMPRODUCT(MAX(('Buffer'!F11:F22<>\"\")*ROW('Buffer'!F11:F22)))")]:
    B.text(ws, r, 7, f, 8, False, 'A79F92')
B.protect(ws)

month = lambda i: f'=EDATE(IF(Settings!$C$11="",DATE(YEAR(TODAY()),1,1),DATE(YEAR(Settings!$C$11),MONTH(Settings!$C$11),1)),{i})'

# ------------------------------------------------------------------ Income Log
ws = S['Income Log']
B.page(ws, 'Income log', 'Once a month: what came in, business costs, and the employed partner\'s pay. The tax pot share is worked out.',
       {2: 16, 3: 15, 4: 15, 5: 14, 6: 15, 7: 15, 8: 16}, ncols=7, nrows=40)
B.text(ws, 7, 3, '="A: "&' + NA + '&" (self-employed)"', 8, True, GOLD, w=5)
B.text(ws, 7, 8, '="B: "&' + NB, 8, True, GOLD)
heads = [('MONTH', 'left'), ('MONEY IN', 'right'), ('BUSINESS COSTS', 'right'), ('PROFIT', 'right'), ('="TAX POT ("&TEXT(' + TAX + ',"0%")&")"', 'right'),
         ('AFTER TAX', 'right'), ('TAKE-HOME PAY', 'right')]
for j, (h, a) in enumerate(heads):
    B.th(ws, 8, 2 + j, h, align=a)
inc = [5200, 3100, 6800, 4200, 2600, 7400, 3900, 5600, 2900, 6100]
cost = [400, 350, 520, 380, 300, 610, 420, 450, 330, 500]
for i in range(12):
    r = R1 + i
    B.fx(ws, r, 2, month(i), 'mmm yyyy', True, align='left')
    B.inp(ws, r, 3, inc[i] if i < 10 else None, MONEY, 'right'); B.inp(ws, r, 4, cost[i] if i < 10 else None, MONEY, 'right')
    B.fx(ws, r, 5, f'=IF(COUNT(C{r}:D{r})=0,"",N(C{r})-N(D{r}))', MONEY)
    B.fx(ws, r, 6, f'=IF(E{r}="","",MAX(0,E{r})*{TAX})', MONEY)
    B.fx(ws, r, 7, f'=IF(E{r}="","",E{r}-F{r})', MONEY)
    B.inp(ws, r, 8, 3350 if i < 10 else None, MONEY, 'right')
B.fx(ws, 21, 2, 'Year so far', bold=True, bg=TINT, align='left')
for c in range(3, 9):
    B.fx(ws, 21, c, f'=SUM({L(c)}{R1}:{L(c)}{R2})', MONEY, True, TINT)
B.fx(ws, 22, 2, 'Highest month', bold=True, bg=WHITE, align='left')
B.fx(ws, 23, 2, 'Average month', bold=True, bg=WHITE, align='left')
B.fx(ws, 24, 2, 'Lowest month', bold=True, bg=WHITE, align='left')
for c in range(3, 9):
    col = L(c)
    B.fx(ws, 22, c, f'=IF(COUNT({col}{R1}:{col}{R2})=0,"",MAX({col}{R1}:{col}{R2}))', MONEY, False, WHITE)
    B.fx(ws, 23, c, f'=IF(COUNT({col}{R1}:{col}{R2})=0,"",AVERAGE({col}{R1}:{col}{R2}))', MONEY, False, WHITE)
    B.fx(ws, 24, c, f'=IF(COUNT({col}{R1}:{col}{R2})=0,"",MIN({col}{R1}:{col}{R2}))', MONEY, False, WHITE)
B.tip(ws, 26, 2, 'Money in = what actually landed in the business account that month (not invoices sent). '
      'Business costs = what the business paid out. If a month is empty, leave it blank: it will not count. A month with no take-home pay: type 0, not blank.', 7, 1, 40)
B.protect(ws)

# ------------------------------------------------------------------ Tax Pot
ws = S['Tax Pot']
B.page(ws, 'Tax pot', 'Tax money set aside every month, tax payments made, and whether the pot covers the next bill.',
       {2: 14, 3: 30, 4: 14, 5: 12, 6: 3, 7: 13, 8: 15, 9: 15, 10: 15}, ncols=9, nrows=40)
B.section(ws, 7, 2, 'Tax payments (type your own dates)', 4)
for j, (h, a) in enumerate([('DUE DATE', 'left'), ('WHAT', 'left'), ('AMOUNT', 'right'), ('PAID?', 'left')]):
    B.th(ws, 8, 2 + j, h, align=a)
pays = [(dt.date(2026, 4, 15), 'Estimated tax, 1st payment', 2900, 'Yes'), (dt.date(2026, 6, 15), 'Estimated tax, 2nd payment', 2600, 'Yes'),
        (dt.date(2026, 9, 15), 'Estimated tax, 3rd payment', 2700, 'Yes'), (dt.date(2027, 1, 15), 'Estimated tax, 4th payment', 3000, 'No')]
for i in range(8):
    r = 9 + i
    p = pays[i] if i < len(pays) else None
    B.inp(ws, r, 2, p[0] if p else None, 'd mmm yyyy'); B.inp(ws, r, 3, p[1] if p else None)
    B.inp(ws, r, 4, p[2] if p else None, MONEY, 'right'); B.inp(ws, r, 5, p[3] if p else None)
B.dv(ws, 'E9:E16', ['Yes', 'No'])
B.tip(ws, 27, 2, 'US: estimated tax is due four times a year. UK: Self Assessment is due 31 January (and 31 July for payments on account). '
      'Elsewhere: type your own dates. Payments marked Paid come off the pot; one dated before or after your 12 months counts in the first or last month. Planning tool, not tax advice.', 9, 1, 40)
for j, (h, a) in enumerate([('MONTH', 'left'), ('SET ASIDE', 'right'), ('PAID OUT', 'right'), ('POT BALANCE', 'right')]):
    B.th(ws, 8, 7 + j, h, align=a)
for i in range(12):
    r = R1 + i
    B.fx(ws, r, 7, f'={IL}!B{r}', 'mmm yyyy', True, align='left')
    B.fx(ws, r, 8, f'=IF({IL}!F{r}="","",{IL}!F{r})', MONEY)
    extra = ''
    if i == 0: extra = '+SUMPRODUCT(($B$9:$B$16>0)*($B$9:$B$16<G9)*($E$9:$E$16="Yes"),$D$9:$D$16)'
    if i == 11: extra = '+SUMPRODUCT(($B$9:$B$16>=EDATE(G20,1))*($E$9:$E$16="Yes"),$D$9:$D$16)'
    B.fx(ws, r, 9, f'=SUMPRODUCT((YEAR($B$9:$B$16)=YEAR(G{r}))*(MONTH($B$9:$B$16)=MONTH(G{r}))*($E$9:$E$16="Yes"),$D$9:$D$16){extra}', MONEY)
    B.fx(ws, r, 10, f'=IF(AND(H{r}="",I{r}=0),"",N(Settings!$C$17)+SUM($H$9:H{r})-SUM($I$9:I{r}))', MONEY)
B.fx(ws, 21, 7, 'Year so far', bold=True, bg=TINT, align='left')
B.fx(ws, 21, 8, '=SUM(H9:H20)', MONEY, True, TINT); B.fx(ws, 21, 9, '=SUM(I9:I20)', MONEY, True, TINT)
B.fx(ws, 21, 10, '=N(Settings!C17)+H21-I21', MONEY, True, TINT)
# next payment
B.text(ws, 23, 7, 'NEXT TAX PAYMENT', 8, True, MUTED, w=4)
B.fx(ws, 24, 7, '=IF(_xlfn.MINIFS(B9:B16,B9:B16,">0",E9:E16,"<>Yes")=0,"",_xlfn.MINIFS(B9:B16,B9:B16,">0",E9:E16,"<>Yes"))', 'd mmm yyyy', True, WHITE, 'left', 2)
B.fx(ws, 24, 9, '=IF(G24="","",SUMIFS(D9:D16,B9:B16,G24,E9:E16,"<>Yes"))', MONEY, True, WHITE)
B.fx(ws, 25, 7, f'=IF(G24="","No unpaid tax payment typed in",IF(G24<TODAY(),"OVERDUE: mark it Paid once it is paid. ","")&IF(J21>=I24,"The pot covers it","Short by "&{CUR}&TEXT(I24-J21,"#,##0")))', None, True,
     TINT, 'left', 4)
B.protect(ws)

# ------------------------------------------------------------------ Shared Bills
ws = S['Shared Bills']
B.page(ws, 'Shared bills', 'Everything you share, turned into a monthly amount and split from steady pay.',
       {2: 26, 3: 22, 4: 11, 5: 12, 6: 15, 7: 12, 8: 12, 9: 12, 10: 3, 11: 6}, ncols=8, nrows=45)
heads = [('BILL', 'left'), ('CATEGORY', 'left'), ('AMOUNT', 'right'), ('HOW OFTEN', 'left'), ('SPLIT', 'left'),
         ('PER MONTH', 'right'), ('="A: "&' + NA, 'right'), ('="B: "&' + NB, 'right')]
for j, (h, a) in enumerate(heads):
    B.th(ws, 7, 2 + j, h, align=a)
BCATS = ['Home', 'Utilities', 'Internet and phone', 'Insurance', 'Groceries', 'Transport', 'Subscriptions', 'Childcare and pets', 'Household', 'Other']
bills = [('Rent or mortgage', 0, 2100, 'Monthly', 'Our split'), ('Electricity, gas and water', 1, 180, 'Monthly', 'Our split'),
         ('Internet', 2, 60, 'Monthly', '50-50'), ('Home and car insurance', 3, 1440, 'Yearly', 'Our split'),
         ('Groceries', 4, 700, 'Monthly', 'Our split'), ('Fuel and transit', 5, 160, 'Monthly', 'Our split'),
         ('Streaming', 6, 30, 'Monthly', '50-50'), ('Dog food and vet plan', 7, 75, 'Monthly', 'Our split'),
         ('Cleaning and household', 8, 45, 'Monthly', '50-50')]
for r in range(8, 33):
    b = bills[r - 8] if r - 8 < len(bills) else None
    B.inp(ws, r, 2, b[0] if b else None); B.inp(ws, r, 3, BCATS[b[1]] if b else None)
    B.inp(ws, r, 4, b[2] if b else None, MONEY, 'right'); B.inp(ws, r, 5, b[3] if b else None); B.inp(ws, r, 6, b[4] if b else None)
    B.fx(ws, r, 7, f'=IF(N(D{r})=0,"",D{r}*IF(E{r}="Weekly",52/12,IF(E{r}="Quarterly",1/3,IF(E{r}="Yearly",1/12,1))))', MONEY)
    B.fx(ws, r, 8, f'=IF(G{r}="","",G{r}*IF(F{r}=Settings!$G$13,1,IF(F{r}=Settings!$G$14,0,IF(F{r}="50-50",0.5,{PA}))))', MONEY)
    B.fx(ws, r, 9, f'=IF(G{r}="","",G{r}-H{r})', MONEY)
B.dv(ws, 'C8:C32', BCATS); B.dv(ws, 'E8:E32', ['Monthly', 'Weekly', 'Quarterly', 'Yearly']); B.dv(ws, 'F8:F32', ref='=Settings!$G$11:$G$14')
B.fx(ws, 33, 2, 'Total per month', bold=True, bg=TINT, align='left')
for c in range(3, 10):
    B.fx(ws, 33, c, f'=SUM({L(c)}8:{L(c)}32)' if c >= 7 else '', MONEY, True, TINT)
B.tip(ws, 35, 2, '"Our split" uses the Settings split (by income after the tax pot, 50-50 or custom). Pick 50-50 or one name for anything else. '
      'Weekly, quarterly and yearly bills become a monthly amount.', 8, 1, 36)
B.protect(ws)

# ------------------------------------------------------------------ Buffer
ws = S['Buffer']
B.page(ws, 'Buffer', 'Good months fill it, low months draw on it, so the self-employed partner\'s pay stays steady.',
       {2: 13, 3: 15, 4: 15, 5: 16, 6: 15, 7: 33, 8: 3}, ncols=7, nrows=40)
for j, (h, a) in enumerate([('PAY YOURSELF', 'right'), ('BUFFER NOW', 'right'), ('GOAL', 'right'), ('MONTHS COVERED', 'right')]):
    B.th(ws, 7, 2 + j, h, align=a)
B.fx(ws, 8, 2, f'={PAY}', MONEY, True, TINT); B.fx(ws, 8, 3, '=IF(Settings!G17=0,N(Settings!C16),INDEX(F:F,Settings!G17))', MONEY, True, TINT)
B.fx(ws, 8, 4, f'=N(Settings!C14)*({SB}!G33+N(Settings!C18))', MONEY, True, TINT)
B.fx(ws, 8, 5, f'=IF(({SB}!G33+N(Settings!C18))=0,"",C8/({SB}!G33+N(Settings!C18)))', '0.0', True, TINT)
B.fx(ws, 8, 6, '=IF(D8=0,"",IF(C8>=D8,"Goal reached","Goal: "&TEXT(MIN(1,C8/D8),"0%")))', None, True, TINT, 'left', 2)
for j, (h, a) in enumerate([('MONTH', 'left'), ('AFTER-TAX PROFIT', 'right'), ('PAY YOURSELF', 'right'), ('IN (+) / OUT (-)', 'right'),
                            ('BUFFER BALANCE', 'right'), ('MONTH WAS', 'left')]):
    B.th(ws, 10, 2 + j, h, align=a)
for i in range(12):
    r = 11 + i; ri = R1 + i
    B.fx(ws, r, 2, f'={IL}!B{ri}', 'mmm yyyy', True, align='left')
    B.fx(ws, r, 3, f'=IF({IL}!G{ri}="","",{IL}!G{ri})', MONEY)
    B.fx(ws, r, 4, f'=IF(C{r}="","",{PAY})', MONEY)
    B.fx(ws, r, 5, f'=IF(C{r}="","",C{r}-D{r})', '+#,##0;-#,##0;0')
    B.fx(ws, r, 6, f'=IF(C{r}="","",N(Settings!$C$16)+SUM($E$11:E{r}))', MONEY)
    B.fx(ws, r, 7, f'=IF(C{r}="","",IF(F{r}<0,"● Buffer empty: pay not covered",IF(E{r}<0,"● Low: buffer topped up pay","● Good: added to buffer")))', None, False, None, 'left')
B.fx(ws, 23, 2, 'Year so far', bold=True, bg=TINT, align='left')
B.fx(ws, 23, 3, '=SUM(C11:C22)', MONEY, True, TINT); B.fx(ws, 23, 4, '=SUM(D11:D22)', MONEY, True, TINT)
B.fx(ws, 23, 5, '=SUM(E11:E22)', '+#,##0;-#,##0;0', True, TINT)
B.fx(ws, 23, 6, '', bg=TINT); B.fx(ws, 23, 7, '=COUNTIF(E11:E22,"<0")&" low months"', None, True, TINT, 'left')
B.tip(ws, 25, 2, 'If the buffer keeps falling, the pay-yourself amount is too high for now: lower it in Settings. '
      'If it keeps growing past the goal, you can give yourself a raise.', 6, 1, 36)
B.protect(ws)
from openpyxl.formatting.rule import FormulaRule
ws.conditional_formatting.add('G11:G22', FormulaRule(formula=['$E11<0'], font=Font(name=FONT, color=CORAL, bold=True)))
ws.conditional_formatting.add('G11:G22', FormulaRule(formula=['$E11>=0'], font=Font(name=FONT, color=DSAGE)))

# ------------------------------------------------------------------ Monthly Split
ws = S['Monthly Split']
B.page(ws, 'Monthly split', 'Each month: steady pay in, shared bills and savings split, and what each of you keeps.',
       {2: 13, 3: 14, 4: 14, 5: 14, 6: 13, 7: 13, 8: 14, 9: 14, 10: 15}, ncols=9, nrows=40)
heads = [('MONTH', 'left'), ('="A pay"', 'right'), ('="B pay"', 'right'), ('BILLS + SAVINGS', 'right'), ('A PAYS', 'right'),
         ('B PAYS', 'right'), ('A KEEPS', 'right'), ('B KEEPS', 'right'), ('SAFE TO SPEND', 'right')]
for j, (h, a) in enumerate(heads):
    B.th(ws, 7, 2 + j, h, align=a)
B.text(ws, 7, 3, '=' + NA + '&" pay"', 8, True, MUTED, align='right'); B.text(ws, 7, 4, '=' + NB + '&" pay"', 8, True, MUTED, align='right')
B.text(ws, 7, 6, '=' + NA + '&" pays"', 8, True, MUTED, align='right'); B.text(ws, 7, 7, '=' + NB + '&" pays"', 8, True, MUTED, align='right')
B.text(ws, 7, 8, '=' + NA + '&" keeps"', 8, True, MUTED, align='right'); B.text(ws, 7, 9, '=' + NB + '&" keeps"', 8, True, MUTED, align='right')
for i in range(12):
    r = 8 + i; ri = R1 + i
    B.fx(ws, r, 2, f'={IL}!B{ri}', 'mmm yyyy', True, align='left')
    B.fx(ws, r, 3, f'=IF(OR({IL}!C{ri}="",{IL}!H{ri}=""),"",{PAY})', MONEY)
    B.fx(ws, r, 4, f'=IF(OR({IL}!C{ri}="",{IL}!H{ri}=""),"",{IL}!H{ri})', MONEY)
    B.fx(ws, r, 5, f'=IF(C{r}="","",{SB}!$G$33+N(Settings!$C$18))', MONEY)
    B.fx(ws, r, 6, f'=IF(E{r}="","",{SB}!$H$33+N(Settings!$C$18)*{PA})', MONEY)
    B.fx(ws, r, 7, f'=IF(E{r}="","",E{r}-F{r})', MONEY)
    B.fx(ws, r, 8, f'=IF(E{r}="","",N(C{r})-F{r})', MONEY)
    B.fx(ws, r, 9, f'=IF(E{r}="","",N(D{r})-G{r})', MONEY)
    B.fx(ws, r, 10, f'=IF(E{r}="","",H{r}+I{r})', MONEY, True)
B.fx(ws, 20, 2, 'Year so far', bold=True, bg=TINT, align='left')
for c in range(3, 11):
    B.fx(ws, 20, c, f'=SUM({L(c)}8:{L(c)}19)', MONEY, True, TINT)
B.tip(ws, 22, 2, 'Safe to spend = what you both keep after the tax pot, shared bills and joint savings. '
      'Because the self-employed pay is steady, this number stays steady too, even in a slow month.', 9, 1, 36)
B.protect(ws)

# ------------------------------------------------------------------ Money Talk
ws = S['Money Talk']
B.page(ws, 'The money talk', '12 questions for couples where one of you is self-employed. Agree them once, review every few months.',
       {2: 5, 3: 60, 4: 14, 5: 48}, ncols=4, nrows=40)
B.th(ws, 7, 2, '#'); B.th(ws, 7, 3, 'QUESTION'); B.th(ws, 7, 4, 'AGREED?'); B.th(ws, 7, 5, 'WHAT WE DECIDED')
Q = ['What tax pot % do we use, and who moves the money each month?', 'What steady amount does the self-employed partner pay themself?',
     'How many months of shared costs do we want in the buffer?', 'In a low month, does the buffer pay, or do we cut back?',
     'In a great month, how much goes to the buffer, savings or a treat?', 'How do we split shared bills: by income, 50-50, or another way?',
     'Is business money kept in its own account, away from household money?', 'Who files the tax return, and when do we look at it together?',
     'What do we do if a client pays late?', 'How do we both save for retirement when only one of us has a workplace plan?',
     'Which business spending needs a chat first?', 'When do we review all this? (We suggest monthly, 30 minutes.)']
ag = ['Yes', 'Yes', 'Yes', 'Yes', 'Not yet', 'Yes', 'Yes', 'Not yet', 'Not yet', 'Not yet', 'Yes', 'Yes']
nt = ['25%, moved on the 1st by Jordan', 'Average after-tax profit, reviewed each quarter', '3 months', 'Buffer pays; no cuts unless it drops under 1 month',
      '', 'By income after the tax pot', 'Yes, separate business account', '', '', '', 'Anything over $500', 'First Sunday, after coffee']
for i, q in enumerate(Q):
    r = 8 + i
    B.fx(ws, r, 2, i + 1, '0', True, align='center', color=GOLD)
    B.fx(ws, r, 3, q, None, False, align='left'); ws.cell(r, 3).alignment = Alignment(wrap_text=True, vertical='center', indent=1)
    B.inp(ws, r, 4, ag[i]); B.inp(ws, r, 5, nt[i] or None)
    ws.row_dimensions[r].height = 30
B.dv(ws, 'D8:D19', ['Yes', 'Not yet', 'Skip'])
B.fx(ws, 21, 3, '="Agreed: "&COUNTIF(D8:D19,"Yes")&" of 12"', None, True, TINT, 'left')
B.fx(ws, 21, 4, '=REPT("█",COUNTIF(D8:D19,"Yes"))&REPT("░",12-COUNTIF(D8:D19,"Yes"))', None, False, TINT, 'left', 2, DSAGE)
B.protect(ws)

# ------------------------------------------------------------------ Start Here
ws = S['Start Here']
B.page(ws, 'Start here', 'Ten minutes to set up, ten minutes a month after that.', {2: 6, 3: 72, 4: 3}, ncols=3, nrows=40)
steps = [('1', 'Settings: your names, currency, tax pot %, the first month of your year and how you split shared costs.'),
         ('2', 'Shared Bills: everything you share. Weekly, quarterly and yearly bills become a monthly amount.'),
         ('3', 'Income Log, once a month: money in and business costs for the self-employed partner, take-home pay for the other.'),
         ('4', 'Tax Pot: type in your tax due dates. It shows the pot balance and whether it covers the next bill.'),
         ('5', 'Buffer: see good months fill it and low months draw on it. Pay yourself stays steady.'),
         ('6', 'Monthly Split: what each of you pays and keeps, and your safe-to-spend number.'),
         ('7', 'Money Talk: 12 questions to agree as a couple.'),
         ('8', 'Dashboard: everything on one screen, with your next step.')]
for i, (n, t) in enumerate(steps):
    r = 7 + i * 2
    B.box(ws, r, 2, r, 3); B.text(ws, r, 2, n, 16, True, GOLD, align='center'); B.text(ws, r, 3, t, 10.5, indent=1)
    ws.row_dimensions[r].height = 34; ws.row_dimensions[r + 1].height = 6
B.tip(ws, 24, 2, 'Pale yellow = type here. White = worked out for you (locked in Excel so nothing breaks). '
      'Google Sheets: upload the .xlsx to Drive, open it, File > Save as Google Sheets, then use the tab bar at the bottom.', 2, 1, 44)
B.tip(ws, 26, 2, 'Planning tool, not tax advice: check your tax % and dates with an accountant or your tax office. Questions: joel@wayofwealthcoaching.com', 2, 1, 36)
B.protect(ws)

# ------------------------------------------------------------------ Dashboard
ws = S['Dashboard']
B.page(ws, 'Self-Employed Couples Budget', '', ncols=16, nrows=110)
ws['B3'] = '=' + NA + '&" (self-employed) and "&' + NB + '&"  ·  tax pot "&TEXT(' + TAX + ',"0%")&"  ·  split "&IF(Settings!C12="","By income",Settings!C12)'
ws['B3'].font = F(10, color=MUTED)
for r, h in [(7, 22), (8, 30), (9, 18), (10, 8), (11, 22), (12, 30), (13, 18)]:
    ws.row_dimensions[r].height = h
last = f'INDEX({MS}!J:J,Settings!$G$16)'
lastA = f'INDEX({MS}!H:H,Settings!$G$16)'
lastB = f'INDEX({MS}!I:I,Settings!$G$16)'
lastM = f'INDEX({MS}!B:B,Settings!$G$16)'
B.hero(ws, 7, 2, 7, 7, 'SAFE TO SPEND TOGETHER (LATEST MONTH)', f'=IF(Settings!$G$16=0,{CUR}&"0",{money(last)})',
       f'=IF(Settings!$G$16=0,"Fill in Settings, Shared Bills and the Income Log to see this.","After the tax pot, shared bills and savings ("&TEXT({lastM},"mmmm")&"). "&{NA}&" keeps "&{money(lastA)}&", "&{NB}&" keeps "&{money(lastB)}&".")',
       'Steady pay in, minus shared bills and joint savings.')
B.kpi(ws, 7, 10, 'TAX POT', f"={money(TP + '!J21')}", f"=IF({TP}!G24=\"\",\"set aside so far\",\"Next bill \"&TEXT({TP}!G24,\"d mmm\")&\": \"&{money(TP + '!I24')})", accent=GOLD)
B.kpi(ws, 7, 14, 'PAY YOURSELF', f'={money(PAY)}', f'={NA}&", every month"', accent=DSAGE)
B.kpi(ws, 11, 10, 'BUFFER', f"={money(BF + '!C8')}", f"=IF({BF}!E8=\"\",\"\",TEXT({BF}!E8,\"0.0\")&\" months of costs\")", accent=DSAGE)
B.kpi(ws, 11, 14, 'LOW MONTHS', f'=COUNTIF({BF}!E11:E22,"<0")&" of "&COUNT({BF}!E11:E22)', f'=IF(COUNTIF({BF}!F11:F22,"<0")>0,"buffer ran out in "&COUNTIF({BF}!F11:F22,"<0")&" months",IF(COUNTIF({BF}!E11:E22,"<0")=0,"none so far","the buffer covered them"))', accent=CORAL)
nxt = (f'=IF(COUNT({IL}!C{R1}:C{R2})=0,"Start with Settings and Shared Bills, then log your first month on the Income Log.",'
       f'IF({BF}!C8<0,"Buffer is empty: lower Pay yourself in Settings until good months refill it.",'
       f'IF(AND({TP}!G24<>"",{TP}!J21<{TP}!I24),"Top up the tax pot: it is "&{CUR}&TEXT({TP}!I24-{TP}!J21,"#,##0")&" short of the "&TEXT({TP}!G24,"d mmm")&" payment.",'
       f'IF({BF}!C8<{BF}!D8,"Grow the buffer: "&{CUR}&TEXT({BF}!D8-{BF}!C8,"#,##0")&" to go to reach "&Settings!C14&" months of costs.",'
       f'IF(COUNTIF(\'Money Talk\'!D8:D19,"Yes")<12,"Finish the Money Talk: "&(12-COUNTIF(\'Money Talk\'!D8:D19,"Yes"))&" questions still open.","On track: tax covered, buffer full, bills split.")))))')
B.bar(ws, 15, 2, 15, 'NEXT STEP', nxt)
for r, h in [(17, 22), (18, 30), (19, 18)]:
    ws.row_dimensions[r].height = h
B.kpi(ws, 17, 2, 'PROFIT THIS YEAR', f"={money(IL + '!E21')}", f"=\"after costs · \"&{money(IL + '!F21')}&\" to tax\"")
B.kpi(ws, 17, 6, 'OUR SPLIT', f'=TEXT({PA},"0%")&" / "&TEXT({PB},"0%")', f'={NA}&" / "&{NB}')
B.kpi(ws, 17, 10, 'SHARED COSTS A MONTH', f"={money(SB + '!G33+N(Settings!C18)')}", '="bills plus joint savings"')
B.kpi(ws, 17, 14, 'MONEY TALK', '=COUNTIF(\'Money Talk\'!D8:D19,"Yes")&" of 12"', '="agreed so far"')
# chart data
D0 = 70
B.section(ws, D0, 2, 'The numbers behind the charts', 10)
B.th(ws, D0 + 1, 2, 'MONTH', 2); B.th(ws, D0 + 1, 4, 'AFTER-TAX PROFIT', 2, 'right'); B.th(ws, D0 + 1, 6, 'PAY YOURSELF', 2, 'right')
B.th(ws, D0 + 1, 8, 'TAX POT', 1, 'right'); B.th(ws, D0 + 1, 9, 'BUFFER', 1, 'right')
for i in range(12):
    r = D0 + 2 + i
    B.fx(ws, r, 2, f'={BF}!B{11 + i}', 'mmm', True, align='left', w=2)
    B.fx(ws, r, 4, f'=N({BF}!C{11 + i})', MONEY, w=2)
    B.fx(ws, r, 6, f'=N({BF}!D{11 + i})', MONEY, w=2)
    B.fx(ws, r, 8, f'=N({TP}!J{9 + i})', MONEY)
    B.fx(ws, r, 9, f'=N({BF}!F{11 + i})', MONEY)
B.th(ws, D0 + 1, 11, 'WHO PAYS SHARED COSTS', 3); B.th(ws, D0 + 1, 14, 'PER MONTH', 2, 'right')
B.fx(ws, D0 + 2, 11, f'={NA}', align='left', w=3); B.fx(ws, D0 + 2, 14, f"={SB}!H33+N(Settings!C18)*{PA}", MONEY, w=2)
B.fx(ws, D0 + 3, 11, f'={NB}', align='left', w=3); B.fx(ws, D0 + 3, 14, f"={SB}!I33+N(Settings!C18)*{PB}", MONEY, w=2)
B.th(ws, D0 + 5, 11, 'SHARED BILLS BY CATEGORY', 3); B.th(ws, D0 + 5, 14, 'PER MONTH', 2, 'right')
for i, c in enumerate(BCATS):
    r = D0 + 6 + i
    B.fx(ws, r, 11, c, align='left', w=3); B.fx(ws, r, 14, f'=SUMIF({SB}!$C$8:$C$32,K{r},{SB}!$G$8:$G$32)', MONEY, w=2)
cats = Reference(ws, min_col=2, min_row=D0 + 2, max_row=D0 + 13)
ch = bar_chart(ws, 'B22', 'Profit goes up and down, pay stays steady', cats, Reference(ws, min_col=4, max_col=4, min_row=D0 + 1, max_row=D0 + 13),
               w=11.8, h=7.4, colors=[DSAGE])
ch2 = BarChart(); ch2.add_data(Reference(ws, min_col=6, min_row=D0 + 1, max_row=D0 + 13), titles_from_data=True)
s2 = ch2.series[0]; s2.graphicalProperties.solidFill = CORAL; s2.graphicalProperties.line.solidFill = CORAL
ch.series.append(s2); ch.gapWidth = 40
ch.series[0].tx = SeriesLabel(v='After-tax profit'); ch.series[1].tx = SeriesLabel(v='Pay yourself')
doughnut(ws, 'J22', 'Who pays shared costs', Reference(ws, min_col=11, min_row=D0 + 2, max_row=D0 + 3),
         Reference(ws, min_col=14, min_row=D0 + 1, max_row=D0 + 3), w=11.8, h=7.4, colors=[NAVY, GOLD])
bar_chart(ws, 'B38', 'Tax pot balance', cats, Reference(ws, min_col=8, min_row=D0 + 1, max_row=D0 + 13), w=11.8, h=7.4, legend=False, colors=[GOLD])
bar_chart(ws, 'J38', 'Buffer balance', cats, Reference(ws, min_col=9, min_row=D0 + 1, max_row=D0 + 13), w=11.8, h=7.4, legend=False, colors=[NAVY])
bar_chart(ws, 'B54', 'Shared bills per month by category', Reference(ws, min_col=11, min_row=D0 + 6, max_row=D0 + 15),
          Reference(ws, min_col=14, min_row=D0 + 5, max_row=D0 + 15), w=11.8, h=7.4, horizontal=True, legend=False, colors=[DSAGE])
B.section(ws, 54, 10, 'Tax payments', 7)
B.th(ws, 55, 10, 'DUE', 2); B.th(ws, 55, 12, 'AMOUNT', 2, 'right'); B.th(ws, 55, 14, 'PAID?', 2)
for i in range(6):
    r = 56 + i
    B.fx(ws, r, 10, f'=IF({TP}!B{9 + i}="","",{TP}!B{9 + i})', 'd mmm yyyy', True, align='left', w=2)
    B.fx(ws, r, 12, f'=IF({TP}!D{9 + i}="","",{TP}!D{9 + i})', MONEY, w=2)
    B.fx(ws, r, 14, f'=IF({TP}!E{9 + i}="","",{TP}!E{9 + i})', None, align='left', w=2)
B.text(ws, 63, 10, '=' + TP + '!G25', 9, True, DSAGE, w=7)
B.protect(ws)
B.save(OUT)
print('saved', OUT)
