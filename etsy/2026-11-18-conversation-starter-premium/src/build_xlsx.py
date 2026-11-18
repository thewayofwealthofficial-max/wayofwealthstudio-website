"""Couples Money Date Planner (premium kit for the Couples Money Conversation Starter) - Way of Wealth Studio.
python3 build_xlsx.py out/file.xlsx [blank] [stage-json]
stage-json (optional, for the in-use video): {"nov_date": false, ...} overrides on the example data.
"""
import sys, os, json, datetime as dt
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
import skin
from skin import *
from openpyxl.chart import Reference, BarChart
from openpyxl.chart.series import SeriesLabel
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Font, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation

CHAR = '3D3D3D'
skin.NAVY = CHAR
OUT = sys.argv[1]; BLANK = len(sys.argv) > 2 and sys.argv[2] == 'blank'
ST = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}

TABS = [('Dashboard', GOLD), ('Start Here', GOLD), ('Settings', DSAGE), ('Shared Income', DSAGE), ('Joint Bills', DSAGE),
        ('Spending Plan', DSAGE), ('Shared Goals', DSAGE), ('Money Dates', CHAR), ('Monthly Check-in', CORAL),
        ('Conversation Cards', CHAR)]
B = Book(TABS, BLANK)
S = B.s
SI, JB, SP, SG, MD, CI, CC = ("'Shared Income'", "'Joint Bills'", "'Spending Plan'", "'Shared Goals'", "'Money Dates'",
                              "'Monthly Check-in'", "'Conversation Cards'")
NA, NB, CUR = 'Settings!$G$8', 'Settings!$G$9', 'Settings!$C$9'
CMI = 'Settings!$G$18'                  # index (1-12) of the month shown
CML = 'Settings!$G$17'                  # its label
PA, PB = 'Settings!$C$17', 'Settings!$C$18'
LBL = lambda k: f'Settings!$G${20 + k}'  # k = 0..11
LBLS = 'Settings!$G$20:$G$31'
money = lambda x: f'{CUR}&TEXT({x},"#,##0")'
DATE = 'd mmm yyyy'

# ================================================================== example data
INC_A = [3300, 3300, 3350, 3350, 3350]
INC_B = [2600, 2600, 2600, 2650, 2650]
INC_O = [0, 120, 0, 0, 80]
BILLS = [('Rent or mortgage', 'Home', 1650, 1), ('Property tax / council tax', 'Home', 160, 1), ('Energy', 'Utilities', 120, 5),
         ('Water', 'Utilities', 40, 5), ('Internet', 'Utilities', 35, 12), ('Home insurance', 'Insurance', 22, 15),
         ('Car insurance', 'Insurance', 55, 15), ('Streaming', 'Subscriptions', 25, 20), ('Phone plans', 'Utilities', 48, 22)]
CATS = ['Groceries', 'Eating out', 'Transport', 'Household', 'Date nights', 'Shopping',
        'Gifts', 'Other']
PLAN = [520, 180, 160, 90, 120, 150, 60, 80]
ACT = [[505, 168, 150, 70, 140, 130, 0, 60], [540, 210, 172, 95, 110, 190, 45, 75], [498, 175, 155, 120, 95, 140, 90, 40],
       [531, 240, 165, 85, 130, 160, 30, 95], [512, 265, 148, 80, 150, 120, 110, 70]]
GOALS = [('Emergency fund', 9000, 2400, dt.date(2027, 12, 1)), ('Holiday in Lisbon', 2400, 300, dt.date(2027, 6, 1)),
         ('Wedding fund', 8000, 1000, dt.date(2028, 6, 1)), ('Car deposit', 4000, 0, dt.date(2028, 3, 1))]
CONTRIB = [[400, 250, 250, 150], [400, 250, 250, 150], [400, 250, 200, 100], [400, 300, 250, 150], [400, 300, 250, 150]]
WEEKS = ['Week 1 · Money stories', 'Week 2 · Where it all goes', 'Week 3 · Shared goals', 'Week 4 · Our money system']
FOCUS = WEEKS + ['Monthly check-in', 'Big decision', 'Catch-up']
W4 = [(dt.date(2026, 6, 7), '1.2, 1.3, 2.1', 4, 3, 'We talk, we don\'t fix. 20 minutes, phones down, every Sunday this month.'),
      (dt.date(2026, 6, 14), '3.1, 3.3, 2.4', 5, 4, 'All joint bills go in the planner. We split them by income, not 50/50.'),
      (dt.date(2026, 6, 21), '4.1, 4.2, 4.4', 6, 5, 'Four shared goals: emergency fund first, then Lisbon, wedding, car.'),
      (dt.date(2026, 6, 28), '3.5, 2.3, 4.3', 6, 6, 'Joint account for bills and food. £100 each, no-ask spending money a week.')]
MONTHLY = [(dt.date(2026, 7, 5), 'Monthly check-in', '1.4, 2.1', 6, 6, 'Under £150 needs no check. Over £150, we ask first.'),
           (dt.date(2026, 8, 2), 'Monthly check-in', '3.2, 4.5', 7, 6, 'Jordan takes over the energy and internet bills.'),
           (dt.date(2026, 9, 6), 'Big decision', '3.4, 1.5', 7, 7, 'We keep the old car one more year and add £50 to the car fund.'),
           (dt.date(2026, 10, 4), 'Monthly check-in', '1.3, 4.2', 7, 7, 'Eating out cap of £200. Takeaway counts too.'),
           (dt.date(2026, 11, 1), 'Monthly check-in', '4.1, 4.5', 8, 7, 'Lisbon goes up to £300 a month until it is booked.')]
if ST.get('nov_date') is False:
    MONTHLY = MONTHLY[:4]
if 'nov' in ST:
    v = list(ST['nov']); v[0] = dt.date(*v[0]) if v[0] else None
    MONTHLY = MONTHLY[:4] + [tuple(v)]

CARDS = [('1.1', 'Feelings First', 'The feeling I get when I think about our money situation is ___.'),
         ('1.2', 'Feelings First', 'The money moment from my childhood that I think about most is ___.'),
         ('1.3', 'Feelings First', 'The thing I wish you understood about how I feel about money is ___.'),
         ('1.4', 'Feelings First', 'When we disagree about money, the emotion underneath my reaction is usually ___.'),
         ('1.5', 'Feelings First', 'The financial topic I have been avoiding bringing up is ___.'),
         ('2.1', 'Breaking the Silence', 'On a scale of 1-10, how comfortable do I feel talking about money with you right now?'),
         ('2.2', 'Breaking the Silence', 'The reason I avoid money conversations is not because I do not care. It is because ___.'),
         ('2.3', 'Breaking the Silence', 'If you could handle ONE financial thing so I did not have to think about it, what would help most?'),
         ('2.4', 'Breaking the Silence', 'The smallest money topic I would feel okay discussing regularly is ___.'),
         ('2.5', 'Breaking the Silence', 'Something I have never told you about my money habits is ___.'),
         ('3.1', 'Hidden Stress', 'The financial task I handle alone that I wish was shared is ___.'),
         ('3.2', 'Hidden Stress', 'The money worry I carry that I have never said out loud is ___.'),
         ('3.3', 'Hidden Stress', 'I feel most financially stressed at this specific moment each month: ___.'),
         ('3.4', 'Hidden Stress', 'The way I cope with money stress that my partner probably does not notice is ___.'),
         ('3.5', 'Hidden Stress', 'If I could change one thing about how we handle money together, it would be ___.'),
         ('4.1', 'Values and Dreams', 'The thing I most want our money to give us in the next 5 years is ___.'),
         ('4.2', 'Values and Dreams', 'Something I would love to spend money on guilt-free is ___.'),
         ('4.3', 'Values and Dreams', 'The financial value that matters most to me is: security / freedom / generosity / comfort / growth.'),
         ('4.4', 'Values and Dreams', 'A money goal I have never told you about is ___.'),
         ('4.5', 'Values and Dreams', 'If money was not a source of stress, the first thing I would want us to do together is ___.')]


def ok_bad(ws, rng, first):
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'LEFT({first},1)="▲"'], font=Font(name=FONT, color=CORAL, bold=True)))
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'LEFT({first},1)="✓"'], font=Font(name=FONT, color=DSAGE, bold=True)))


def bar(pct):
    k = f'ROUND(MIN(1,MAX(0,N({pct})))*12,0)'
    return (f'=IF({pct}="","",IFERROR(SPARKLINE(MIN(1,{pct}),{{"charttype","bar";"max",1;"color1","#B8956E"}}),'
            f'REPT("█",{k})&REPT("░",12-{k})))')


# ================================================================== Settings
ws = S['Settings']
B.page(ws, 'Settings', 'Fill in the yellow boxes once. Every other tab updates on its own.', {2: 40, 3: 22, 4: 3, 5: 56, 6: 3, 7: 16},
       ncols=6, nrows=40)
B.th(ws, 6, 2, 'ABOUT YOU TWO'); B.th(ws, 6, 3, 'TYPE OR PICK HERE'); B.th(ws, 6, 5, 'WHAT IT DOES')
rows = [('Partner A name', 'Alex', None, False, 'Shown on every tab and in your monthly summary.'),
        ('Partner B name', 'Jordan', None, False, ''),
        ('Currency symbol ($, £, €, A$...)', '£', None, False, 'TYPE YOURS FIRST. Any currency works: amounts are plain numbers, the symbol goes in every sentence.'),
        ('First month of your planner', dt.date(2026, 7, 1) if not BLANK else dt.date(2027, 1, 1), 'mmm yyyy', True,
         'Type the 1st of the month you start, e.g. 1 Jan 2027. Sets the 12 months on every tab.'),
        ('Month to show on the Dashboard and Check-in', 'Nov 2026' if not BLANK else 'Jan 2027', None, True,
         'Pick from the list. Change it at each monthly money date.'),
        ('How we split joint bills', 'By income (fair)', None, True, 'By income = you each pay the same share of what you earn. Or 50/50, or your own %.'),
        ('If "Our own %": Partner A pays', 0.6, PCT, False, 'Only used when you pick "Our own %". Type it with the % sign, e.g. 60%.'),
        ('Our monthly money date', 'First Sunday, 7pm', None, False, 'Same day each month makes it a habit. Shown on the Dashboard.')]
for i, (lab, v, fmt, keep, hlp) in enumerate(rows):
    r = 7 + i
    B.text(ws, r, 2, lab, 10, True); B.inp(ws, r, 3, v, fmt, keep=keep); B.text(ws, r, 5, hlp, 9, color=MUTED)
    if r == 9:
        ws.cell(r, 2).font = F(11, True, CORAL); ws.cell(r, 5).font = F(9, True, CORAL)
        ws.cell(r, 3).border = Border(left=Side(style='medium', color=CORAL), right=Side(style='medium', color=CORAL),
                                      top=Side(style='medium', color=CORAL), bottom=Side(style='medium', color=CORAL))
    ws.row_dimensions[r].height = 30 if len(hlp) > 60 else 24
B.dv(ws, 'C11', ref='$G$20:$G$31')
B.dv(ws, 'C12', ['By income (fair)', '50/50', 'Our own %'])
_d = DataValidation(type='decimal', operator='between', formula1='0', formula2='1', showErrorMessage=True,
                    errorTitle='Percent', error='Type a percentage between 0% and 100%, e.g. 60%')
ws.add_data_validation(_d); _d.add('C13')
ws['B3'] = '=IF(TRIM(C9)="","◆ START HERE: type your currency symbol in the red box ($, £, €, A$, R...), then your two names.","Fill in the yellow boxes once. Every other tab updates on its own.")'
ws['B3'].font = F(10.5, True, CORAL) if BLANK else F(10, color=MUTED)
B.text(ws, 16, 2, 'OUR SPLIT (WORKED OUT FOR YOU FROM SHARED INCOME)', 8, True, MUTED)
B.text(ws, 17, 2, '="Share "&G8&" pays"', 10, True)
B.fx(ws, 17, 3, f"=IF(C12=\"50/50\",0.5,IF(C12=\"Our own %\",MIN(1,MAX(0,N(C13))),IF(SUM({SI}!$D$9:$E$20)=0,0.5,"
                f"SUM({SI}!$D$9:$D$20)/SUM({SI}!$D$9:$E$20))))", PCT, True, TINT)
B.text(ws, 18, 2, '="Share "&G9&" pays"', 10, True)
B.fx(ws, 18, 3, '=1-C17', PCT, True, TINT)
B.tip(ws, 20, 2, 'Why split by income? Paying the same amount can leave the lower earner with almost nothing to spend. '
      'Splitting by income means you each put in the same share of what you earn. Talk it through with card 3.5.', 4, 1, 44)
B.text(ws, 6, 7, 'HELPERS', 7, True, 'B9B2A6')
B.text(ws, 8, 7, '=IF(TRIM(C7)="","Partner A",TRIM(C7))', 8, False, 'A79F92')
B.text(ws, 9, 7, '=IF(TRIM(C8)="","Partner B",TRIM(C8))', 8, False, 'A79F92')
B.text(ws, 18, 7, f"=IFERROR(MATCH(C11,$G$20:$G$31,0),MAX(1,COUNT({SI}!$C$9:$C$20)))", 8, False, 'A79F92')
B.text(ws, 17, 7, '=INDEX($G$20:$G$31,G18)', 8, False, 'A79F92')
for k in range(12):
    B.text(ws, 20 + k, 7, f'=TEXT(EDATE($C$10,{k}),"mmm yyyy")', 8, False, 'A79F92', wrap=False)
B.protect(ws)

# ================================================================== Shared Income
ws = S['Shared Income']
B.page(ws, 'Shared Income', 'Take-home pay for each of you, month by month. This sets your fair split.', ncols=13, nrows=50)
B.th(ws, 8, 2, 'MONTH', 1)
B.th(ws, 8, 3, f'=UPPER({NA})&" TAKE-HOME"', 2, 'right'); B.th(ws, 8, 5, f'=UPPER({NB})&" TAKE-HOME"', 2, 'right')
B.th(ws, 8, 7, 'OTHER SHARED INCOME', 2, 'right'); B.th(ws, 8, 9, 'TOGETHER', 2, 'right')
B.th(ws, 8, 11, f'=UPPER({NA})&" SHARE"', 1, 'right'); B.th(ws, 8, 12, f'=UPPER({NB})&" SHARE"', 2, 'right')
for k in range(12):
    r = 9 + k
    B.fx(ws, r, 2, f'={LBL(k)}', None, True, align='left')
    has = k < len(INC_A) and not BLANK
    B.inp(ws, r, 3, INC_A[k] if has else None, MONEY, 'right', w=2)
    B.inp(ws, r, 5, INC_B[k] if has else None, MONEY, 'right', w=2)
    B.inp(ws, r, 7, INC_O[k] if has else None, MONEY, 'right', w=2)
    B.fx(ws, r, 9, f'=IF(COUNT(C{r},E{r},G{r})=0,"",N(C{r})+N(E{r})+N(G{r}))', MONEY, True, w=2)
    B.fx(ws, r, 11, f'=IF(N(C{r})+N(E{r})=0,"",N(C{r})/(N(C{r})+N(E{r})))', PCT)
    B.fx(ws, r, 12, f'=IF(K{r}="","",1-K{r})', PCT, w=2)
r = 21
B.fx(ws, r, 2, 'Year so far', None, True, GOLDT, 'left')
for c in (3, 5, 7):
    B.fx(ws, r, c, f'=SUM({L(c)}9:{L(c)}20)', MONEY, True, GOLDT, w=2)
B.fx(ws, r, 9, '=SUM(I9:I20)', MONEY, True, GOLDT, w=2)
B.fx(ws, r, 11, '=IF(C21+E21=0,"",C21/(C21+E21))', PCT, True, GOLDT)
B.fx(ws, r, 12, '=IF(K21="","",1-K21)', PCT, True, GOLDT, w=2)
B.tip(ws, 23, 2, 'Take-home = what lands in your account after tax. Other shared income = gifts, refunds, side money you agree to pool. '
      'Fill in each month at your money date: it takes two minutes.', 12, 1, 34)
B.protect(ws)
S['Settings']['C17'].value = (f"=IF(C12=\"50/50\",0.5,IF(C12=\"Our own %\",MIN(1,MAX(0,N(C13))),IF(SUM({SI}!$C$9:$C$20)+SUM({SI}!$E$9:$E$20)=0,0.5,"
                              f"SUM({SI}!$C$9:$C$20)/(SUM({SI}!$C$9:$C$20)+SUM({SI}!$E$9:$E$20)))))")
INC_T = lambda k: f"{SI}!$I${9 + k}"

# ================================================================== Joint Bills
ws = S['Joint Bills']
B.page(ws, 'Joint Bills', 'Every bill you share, split fairly. Your shares update when your pay changes.', ncols=15, nrows=60)
B.th(ws, 8, 2, 'BILL', 4); B.th(ws, 8, 6, 'TYPE', 2); B.th(ws, 8, 8, '="PER MONTH ("&' + CUR + '&")"', 2, 'right')
B.th(ws, 8, 10, 'DUE DAY', 1, 'right'); B.th(ws, 8, 11, f'=UPPER({NA})&" PAYS"', 2, 'right'); B.th(ws, 8, 13, f'=UPPER({NB})&" PAYS"', 2, 'right')
JR1, JR2 = 9, 26
for i, r in enumerate(range(JR1, JR2 + 1)):
    b = BILLS[i] if i < len(BILLS) else None
    B.inp(ws, r, 2, b[0] if b else None, w=4)
    B.inp(ws, r, 6, b[1] if b else None, w=2)
    B.inp(ws, r, 8, b[2] if b else None, MONEY, 'right', w=2)
    B.inp(ws, r, 10, b[3] if b else None, '0', 'right')
    B.fx(ws, r, 11, f'=IF(N(H{r})=0,"",ROUND(H{r}*{PA},0))', MONEY, w=2)
    B.fx(ws, r, 13, f'=IF(N(H{r})=0,"",H{r}-K{r})', MONEY, w=2)
B.dv(ws, f'F{JR1}:F{JR2}', ['Home', 'Utilities', 'Insurance', 'Subscriptions', 'Debt', 'Childcare', 'Pets', 'Other'])
r = JR2 + 1
B.fx(ws, r, 2, 'Total joint bills each month', None, True, GOLDT, 'left', 6)
B.fx(ws, r, 8, f'=SUM(H{JR1}:H{JR2})', MONEY, True, GOLDT, w=2); B.fx(ws, r, 10, '', None, False, GOLDT)
B.fx(ws, r, 11, f'=SUM(K{JR1}:K{JR2})', MONEY, True, GOLDT, w=2); B.fx(ws, r, 13, f'=SUM(M{JR1}:M{JR2})', MONEY, True, GOLDT, w=2)
BILLS_T, BA_T, BB_T = f"{JB}!$H${r}", f"{JB}!$K${r}", f"{JB}!$M${r}"
# transfer box
T0 = JR2 + 3
B.section(ws, T0, 2, 'Each month, move this into the joint account', 10)
B.th(ws, T0 + 1, 2, 'WHAT IT COVERS', 6); B.th(ws, T0 + 1, 8, 'TOGETHER', 2, 'right')
B.th(ws, T0 + 1, 10, f'=UPPER({NA})', 2, 'right'); B.th(ws, T0 + 1, 12, f'=UPPER({NB})', 2, 'right')
items = [('Joint bills (above)', BILLS_T), ('Shared spending plan (Spending Plan tab)', f"{SP}!$C$19"),
         ('Monthly amount for shared goals (Shared Goals tab)', f"{SG}!$M$15")]
for i, (lab, ref) in enumerate(items):
    rr = T0 + 2 + i
    B.fx(ws, rr, 2, lab, None, False, None, 'left', 6)
    B.fx(ws, rr, 8, f'=N({ref})', MONEY, w=2)
    B.fx(ws, rr, 10, f'=ROUND(H{rr}*{PA},0)', MONEY, w=2); B.fx(ws, rr, 12, f'=H{rr}-J{rr}', MONEY, w=2)
rr = T0 + 5
B.fx(ws, rr, 2, 'Monthly transfer', None, True, CHAR, 'left', 6, 'FFFFFF')
for c in (8, 10, 12):
    B.fx(ws, rr, c, f'=SUM({L(c)}{T0 + 2}:{L(c)}{T0 + 4})', MONEY, True, CHAR, w=2, color='FFFFFF')
TRANSFER_A, TRANSFER_B = f"{JB}!$J${rr}", f"{JB}!$L${rr}"
B.fx(ws, rr + 1, 2, f'=IF(OR(N(H{rr})=0,ABS({PA}-0.5)<0.005),"","Each of you puts in "&TEXT({PA},"0%")&" and "&TEXT({PB},"0%")&" of the shared costs. '
                    f'At 50/50, "&IF({PA}>=0.5,{NB},{NA})&" would pay "&{money(f"ABS(H{rr}/2-J{rr})")}&" more each month.")',
     None, False, TINT, 'left', 13, CHAR, 9.5)
ws.row_dimensions[rr + 1].height = 30
B.protect(ws)

# ================================================================== Spending Plan
ws = S['Spending Plan']
B.page(ws, 'Spending Plan', 'Your shared spending: a plan for each category, then what you really spent each month.',
       {2: 25, 3: 9, **{c: 7.2 for c in range(4, 16)}, 16: 9, 17: 9}, ncols=17, nrows=50)
B.th(ws, 8, 2, 'CATEGORY', 1); B.th(ws, 8, 3, 'PLAN / MONTH', 1, 'right')
for k in range(12):
    B.th(ws, 8, 4 + k, f'=LEFT({LBL(k)},3)', 1, 'right')
B.th(ws, 8, 16, 'TOTAL', 1, 'right'); B.th(ws, 8, 17, 'AVERAGE', 1, 'right')
CR1, CR2 = 9, 18
for i, r in enumerate(range(CR1, CR2 + 1)):
    B.inp(ws, r, 2, CATS[i] if i < len(CATS) else None, keep=True)
    B.inp(ws, r, 3, PLAN[i] if i < len(PLAN) else None, MONEY, 'right')
    for k in range(12):
        v = ACT[k][i] if (k < len(ACT) and i < len(CATS)) else None
        B.inp(ws, r, 4 + k, v, MONEY, 'right')
    B.fx(ws, r, 16, f'=IF(COUNT(D{r}:O{r})=0,"",SUM(D{r}:O{r}))', MONEY, True)
    B.fx(ws, r, 17, f'=IF(COUNT(D{r}:O{r})=0,"",AVERAGE(D{r}:O{r}))', MONEY)
r = 19
B.fx(ws, r, 2, 'Total', None, True, GOLDT, 'left')
B.fx(ws, r, 3, f'=SUM(C{CR1}:C{CR2})', MONEY, True, GOLDT)
for k in range(12):
    c = L(4 + k)
    B.fx(ws, r, 4 + k, f'=IF(COUNT({c}{CR1}:{c}{CR2})=0,"",SUM({c}{CR1}:{c}{CR2}))', MONEY, True, GOLDT)
B.fx(ws, r, 16, f'=SUM(P{CR1}:P{CR2})', MONEY, True, GOLDT); B.fx(ws, r, 17, '', None, False, GOLDT)
r = 20
B.fx(ws, r, 2, 'Over (▲) or under plan', None, False, None, 'left'); B.fx(ws, r, 3, '', None)
for k in range(12):
    c = L(4 + k)
    B.fx(ws, r, 4 + k, f'=IF({c}19="","",IF({c}19>$C$19,"▲ "&TEXT({c}19-$C$19,"#,##0"),"✓ "&TEXT($C$19-{c}19,"#,##0")))', None, False, None, 'right', size=8.5)
ok_bad(ws, 'D20:O20', 'D20')
B.tip(ws, 22, 2, 'Groceries, eating out, fun: the money you spend together that is not a fixed bill. Change the category names if you like. '
      'At each money date, type last month\'s totals from your banking app. Round numbers are fine.', 16, 1, 34)
B.protect(ws)

# ================================================================== Shared Goals
ws = S['Shared Goals']
B.page(ws, 'Shared Goals', 'Up to 6 goals you are saving for together. Add what you put in each month below.',
       {2: 9, 3: 9, 4: 10, 5: 10, 6: 10, 7: 10, 8: 10, 9: 10, 10: 9, 11: 9, 12: 9, 13: 10, 14: 9, 15: 9}, ncols=15, nrows=60)
B.th(ws, 8, 2, 'GOAL', 3); B.th(ws, 8, 5, 'TARGET', 1, 'right'); B.th(ws, 8, 6, 'HAD AT START', 1, 'right')
B.th(ws, 8, 7, 'BY WHEN', 1, 'right'); B.th(ws, 8, 8, 'SAVED NOW', 1, 'right'); B.th(ws, 8, 9, 'DONE', 1, 'right')
B.th(ws, 8, 10, 'PROGRESS', 3); B.th(ws, 8, 13, 'NEEDED / MONTH', 1, 'right'); B.th(ws, 8, 14, 'STATUS', 2)
GR1, GR2 = 9, 14
CG1, CG2 = 20, 31
for i, r in enumerate(range(GR1, GR2 + 1)):
    g = GOALS[i] if i < len(GOALS) else None
    B.inp(ws, r, 2, g[0] if g else None, w=3)
    B.inp(ws, r, 5, g[1] if g else None, MONEY, 'right')
    B.inp(ws, r, 6, g[2] if g else None, MONEY, 'right')
    B.inp(ws, r, 7, g[3] if g else None, 'mmm yyyy', 'right')
    col = L(4 + i)  # contributions column D..I
    B.fx(ws, r, 8, f'=IF(N(E{r})=0,"",N(F{r})+SUM({col}{CG1}:{col}{CG2}))', MONEY, True)
    B.fx(ws, r, 9, f'=IF(H{r}="","",MIN(1,H{r}/E{r}))', PCT, True)
    B.fx(ws, r, 10, bar(f'I{r}'), None, False, None, 'left', 3, GOLD)
    B.fx(ws, r, 13, f'=IF(H{r}="","",IF(H{r}>=E{r},0,IF(N(G{r})=0,"",(E{r}-H{r})/MAX(1,DATEDIF(EDATE({LBL(0)}*0+DATE(YEAR(TODAY()),MONTH(TODAY()),1),0),G{r},"m")))))', MONEY)
    B.fx(ws, r, 14, f'=IF(H{r}="","",IF(H{r}>=E{r},"✓ Reached",IF(N(G{r})=0,"Add a date",IF(J{CG2 + 2}="","",IF(INDEX({{{",".join(["0"] * 6)}}},1)=0,"","")))))', None, False, None, 'left', 2)
# simpler, robust status: on track if average monthly add >= needed
for i, r in enumerate(range(GR1, GR2 + 1)):
    col = L(4 + i)
    ws.cell(r, 13).value = (f'=IF(H{r}="","",IF(H{r}>=E{r},0,IF(N(G{r})=0,"",'
                            f'ROUND((E{r}-H{r})/MAX(1,(YEAR(G{r})-YEAR(TODAY()))*12+MONTH(G{r})-MONTH(TODAY())),0))))')
    ws.cell(r, 14).value = (f'=IF(H{r}="","",IF(H{r}>=E{r},"✓ Reached",IF(N(G{r})=0,"Add a date",'
                            f'IF(IFERROR(AVERAGE({col}{CG1}:{col}{CG2}),0)>=M{r}*0.95,"✓ On track","▲ Add "&TEXT(M{r}-IFERROR(AVERAGE({col}{CG1}:{col}{CG2}),0),"#,##0")&"/mo"))))')
ok_bad(ws, f'N{GR1}:N{GR2}', f'N{GR1}')
r = 15
B.fx(ws, r, 2, 'All goals', None, True, GOLDT, 'left', 3)
B.fx(ws, r, 5, f'=SUM(E{GR1}:E{GR2})', MONEY, True, GOLDT); B.fx(ws, r, 6, f'=SUM(F{GR1}:F{GR2})', MONEY, True, GOLDT)
B.fx(ws, r, 7, '', None, False, GOLDT); B.fx(ws, r, 8, f'=SUM(H{GR1}:H{GR2})', MONEY, True, GOLDT)
B.fx(ws, r, 9, f'=IF(E15=0,"",H15/E15)', PCT, True, GOLDT)
B.fx(ws, r, 10, bar('I15'), None, False, GOLDT, 'left', 3, GOLD)
B.fx(ws, r, 13, f'=SUM(M{GR1}:M{GR2})', MONEY, True, GOLDT); B.fx(ws, r, 14, '', None, False, GOLDT, w=2)
B.section(ws, CG1 - 2, 2, 'What we put into each goal, month by month', 12)
B.th(ws, CG1 - 1, 2, 'MONTH', 2)
for i in range(6):
    B.th(ws, CG1 - 1, 4 + i, f'=IF(B{GR1 + i}="","Goal {i + 1}",LEFT(B{GR1 + i},14))', 1, 'right')
    ws.cell(CG1 - 1, 4 + i).alignment = ws.cell(CG1 - 1, 4 + i).alignment.copy(wrap_text=True)
B.th(ws, CG1 - 1, 10, 'TOGETHER', 1, 'right')
for k in range(12):
    rr = CG1 + k
    B.fx(ws, rr, 2, f'={LBL(k)}', None, True, align='left', w=2)
    for i in range(6):
        v = CONTRIB[k][i] if (k < len(CONTRIB) and i < len(GOALS)) else None
        B.inp(ws, rr, 4 + i, v, MONEY, 'right')
    B.fx(ws, rr, 10, f'=IF(COUNT(D{rr}:I{rr})=0,"",SUM(D{rr}:I{rr}))', MONEY, True)
rr = CG2 + 1
B.fx(ws, rr, 2, 'Total', None, True, GOLDT, 'left', 2)
for c in range(4, 11):
    B.fx(ws, rr, c, f'=SUM({L(c)}{CG1}:{L(c)}{CG2})', MONEY, True, GOLDT)
B.tip(ws, rr + 2, 2, 'Needed / month = what is left to save, spread over the months until "By when". The Joint Bills tab adds this to your '
      'monthly transfer. Pick goals together at Week 3 of the money date plan (cards 4.1, 4.2 and 4.4).', 14, 1, 34)
B.protect(ws)

# ================================================================== Money Dates
ws = S['Money Dates']
B.page(ws, 'Money Dates', 'Log each money date: when, which cards you pulled, how it felt (1-10) and the one thing you agreed.',
       {2: 11, 3: 6, 4: 6, 5: 8, 6: 8, 7: 8, 8: 7, 9: 7, 10: 7, 11: 7, 12: 9, 13: 9, 14: 9, 15: 9, 16: 9, 17: 10}, ncols=17, nrows=60)


def date_head(r):
    B.th(ws, r, 2, 'DATE', 1); B.th(ws, r, 3, 'DATE HELD', 2); B.th(ws, r, 5, 'FOCUS', 3); B.th(ws, r, 8, 'CARDS PULLED', 2)
    B.th(ws, r, 10, f'=UPPER({NA})&" 1-10"', 1, 'right'); B.th(ws, r, 11, f'=UPPER({NB})&" 1-10"', 1, 'right')
    B.th(ws, r, 12, 'ONE THING WE AGREED', 5); B.th(ws, r, 17, 'STATUS', 1)


B.section(ws, 7, 2, 'Our 4-week start (the 4-Week Money Date Plan PDF)', 12)
date_head(8)
for i in range(4):
    r = 9 + i
    w = W4[i] if not BLANK else None
    B.fx(ws, r, 2, f'Week {i + 1}', None, True, align='left')
    B.inp(ws, r, 3, w[0] if w else None, DATE, 'right', w=2)
    B.fx(ws, r, 5, WEEKS[i].split('· ')[1], None, False, align='left', w=3)
    B.inp(ws, r, 8, w[1] if w else None, '@', 'left', w=2)
    B.inp(ws, r, 10, w[2] if w else None, '0', 'center'); B.inp(ws, r, 11, w[3] if w else None, '0', 'center')
    B.inp(ws, r, 12, w[4] if w else None, None, 'left', w=5)
    B.fx(ws, r, 17, f'=IF(C{r}="","Planned","✓ Done")', None, True, align='left')
    ws.row_dimensions[r].height = 32
    ws.cell(r, 12).alignment = ws.cell(r, 12).alignment.copy(wrap_text=True)
MR1, MR2 = 17, 28
B.section(ws, 15, 2, '12 monthly money dates', 12)
date_head(16)
for k in range(12):
    r = MR1 + k
    m = MONTHLY[k] if (k < len(MONTHLY) and not BLANK) else None
    B.fx(ws, r, 2, f'={LBL(k)}', None, True, align='left')
    B.inp(ws, r, 3, m[0] if m else None, DATE, 'right', w=2)
    B.inp(ws, r, 5, m[1] if m else None, None, 'left', w=3)
    B.inp(ws, r, 8, m[2] if m else None, '@', 'left', w=2)
    B.inp(ws, r, 10, m[3] if m else None, '0', 'center'); B.inp(ws, r, 11, m[4] if m else None, '0', 'center')
    B.inp(ws, r, 12, m[5] if m else None, None, 'left', w=5)
    B.fx(ws, r, 17, f'=IF(C{r}="",IF(B{r}={CML},"◆ This month","Planned"),"✓ Done")', None, True, align='left')
    ws.row_dimensions[r].height = 32
    ws.cell(r, 12).alignment = ws.cell(r, 12).alignment.copy(wrap_text=True)
ok_bad(ws, 'Q9:Q28', 'Q9')
ws.conditional_formatting.add('Q9:Q28', FormulaRule(formula=['LEFT(Q9,1)="◆"'], font=Font(name=FONT, color=GOLD, bold=True)))
B.dv(ws, f'E{MR1}:E{MR2}', FOCUS)
dvn = DataValidation(type='whole', operator='between', formula1='1', formula2='10', showErrorMessage=True, error='A number from 1 to 10')
ws.add_data_validation(dvn); dvn.add('J9:K12'); dvn.add(f'J{MR1}:K{MR2}')
B.tip(ws, MR2 + 2, 2, 'Cards are numbered track.card from the Conversation Starter, e.g. 2.1 = Track 2, card 1. Type them with commas: 1.2, 4.5. '
      'The 1-10 score is card 2.1: how comfortable talking about money felt today. Watch it climb on the Dashboard.', 16, 1, 34)
B.protect(ws)

# ================================================================== Conversation Cards
ws = S['Conversation Cards']
B.page(ws, 'Conversation Cards', 'The 20 cards from your Conversation Starter. See which ones you have pulled and which are still waiting.',
       {2: 7, 3: 10, 4: 10, **{c: 8.3 for c in range(5, 13)}, 13: 11, 14: 7, 15: 10, 16: 10}, ncols=16, nrows=50)
B.th(ws, 8, 2, 'CARD', 1); B.th(ws, 8, 3, 'TRACK', 2); B.th(ws, 8, 5, 'THE CARD', 8); B.th(ws, 8, 13, 'FIRST PULLED', 1, 'right')
B.th(ws, 8, 14, 'TIMES LOGGED', 1, 'right'); B.th(ws, 8, 15, 'STATUS', 2)
DCARDS = f"{MD}!$H$9:$H$28"; DDATES = f"{MD}!$C$9:$C$28"
for i, (cid, tr, txt) in enumerate(CARDS):
    r = 9 + i
    B.fx(ws, r, 2, cid, None, True, align='left')
    B.fx(ws, r, 3, tr, None, False, align='left', w=2, color=MUTED, size=9)
    B.fx(ws, r, 5, f'"{txt}"' if False else txt, None, False, align='left', w=8, size=9.5)
    ws.cell(r, 5).alignment = ws.cell(r, 5).alignment.copy(wrap_text=True)
    B.fx(ws, r, 13, f'=IFERROR(INDEX({DDATES},MATCH("*{cid}*",{DCARDS},0)),"")', 'd mmm', False)
    B.fx(ws, r, 14, f'=IF(COUNTIF({DCARDS},"*{cid}*")=0,"",COUNTIF({DCARDS},"*{cid}*"))', '0')
    B.fx(ws, r, 15, f'=IF(N(N{r})>0,"✓ Talked about","Still waiting")', None, True, align='left', w=2)
    ws.row_dimensions[r].height = 28
ok_bad(ws, 'O9:O28', 'O9')
r = 29
B.fx(ws, r, 2, f'=COUNTIF(O9:O28,"✓*")&" of 20 cards talked about"', None, True, GOLDT, 'left', 15)
B.tip(ws, 31, 2, 'Full wording, the tips under each card, and which track suits your couple type are in the Conversation Starter PDF '
      '(Tracks 1-4, pages 7-10). Pull the cards the 4-week plan suggests, then any that are still waiting.', 15, 1, 34)
B.protect(ws)

# ================================================================== Monthly Check-in
ws = S['Monthly Check-in']
B.page(ws, 'Monthly Check-in', 'Your month in plain words, then five questions to answer together. 10 minutes at your money date.',
       {**{c: 8 for c in range(2, 18)}}, ncols=17, nrows=60)
B.text(ws, 7, 2, '="MONTH: "&UPPER(' + CML + ')', 12, True, CHAR, w=8)
B.text(ws, 7, 10, 'Change the month on the Settings tab', 9, False, MUTED, w=7, align='right', italic=True)
ws.row_dimensions[7].height = 24
# numbers table (right) and spending table (left), rows 16+
N0 = 18
B.section(ws, N0 - 1, 11, 'This month in numbers', 7)
nums = [('Income together', f'INDEX({SI}!$I$9:$I$20,{CMI})'),
        ('Joint bills', f'IF(N(INDEX({SI}!$I$9:$I$20,{CMI}))=0,0,{BILLS_T})'),
        ('Shared spending', f'INDEX({SP}!$D$19:$O$19,{CMI})'),
        ('Spending plan', f'{SP}!$C$19'),
        ('Put into goals', f'INDEX({SG}!$J${CG1}:$J${CG2},{CMI})'),
        ('Left over', f'N(L{N0})-N(L{N0 + 1})-N(L{N0 + 2})-N(L{N0 + 4})'),
        ('="Comfort 1-10: "&' + NA, f'INDEX({MD}!$J${MR1}:$J${MR2},{CMI})'),
        ('="Comfort 1-10: "&' + NB, f'INDEX({MD}!$K${MR1}:$K${MR2},{CMI})')]
for i, (lab, f) in enumerate(nums):
    r = N0 + i
    B.fx(ws, r, 11, lab, None, i == 5, None, 'left', 3)
    fmt = '0' if i >= 6 else MONEY
    B.fx(ws, r, 14, f'=IF({f}="","",{f})' if i >= 6 else f'=N({f})', fmt, True, None, w=2)
# keep the values in col N; references below use N
NUM = lambda i: f'$N${N0 + i}'
ws.cell(N0 + 5, 14).value = f'=N({NUM(0)})-N({NUM(1)})-N({NUM(2)})-N({NUM(4)})'
B.section(ws, N0 - 1, 2, 'Spending vs plan this month', 8)
B.th(ws, N0, 2, 'CATEGORY', 3); B.th(ws, N0, 5, 'PLAN', 1, 'right'); B.th(ws, N0, 6, 'SPENT', 1, 'right'); B.th(ws, N0, 7, 'DIFFERENCE', 2)
for i in range(10):
    r = N0 + 1 + i
    src = CR1 + i
    B.fx(ws, r, 2, f'=IF({SP}!$B${src}="","",{SP}!$B${src})', None, False, align='left', w=3)
    B.fx(ws, r, 5, f'=IF(B{r}="","",N({SP}!$C${src}))', MONEY)
    B.fx(ws, r, 6, f'=IF(B{r}="","",N(INDEX({SP}!$D${src}:$O${src},{CMI})))', MONEY)
    B.fx(ws, r, 7, f'=IF(OR(B{r}="",N(E{r})+N(F{r})=0),"",IF(F{r}>E{r},"▲ "&TEXT(F{r}-E{r},"#,##0")&" over","✓ "&TEXT(E{r}-F{r},"#,##0")&" under"))', None, False, align='left', w=2)
    B.fx(ws, r, 19, f'=IF(B{r}="","",F{r}-E{r})', '0', False, WHITE)  # helper (hidden col S)
ok_bad(ws, f'G{N0 + 1}:G{N0 + 10}', f'G{N0 + 1}')
SR = f'$S${N0 + 1}:$S${N0 + 10}'; SC = f'$B${N0 + 1}:$B${N0 + 10}'
ws.column_dimensions['S'].hidden = True
# goal helpers (hidden col T)
for i in range(6):
    col = L(4 + i); g = GR1 + i
    B.fx(ws, 9 + i, 22, f'=IF(N({SG}!$E${g})=0,0,N({SG}!$F${g})+SUMPRODUCT(--(ROW({SG}!${col}${CG1}:${col}${CG2})-{CG1 - 1}<={CMI}),{SG}!${col}${CG1}:${col}${CG2}))', '0', False, WHITE)
    B.fx(ws, 9 + i, 21, f'=IF(N({SG}!$E${g})=0,"",MIN(1,V{9 + i}/{SG}!$E${g}))', PCT, False, WHITE)
ws.column_dimensions['U'].hidden = True; ws.column_dimensions['V'].hidden = True
B.fx(ws, 9, 20, f'=IFERROR(INDEX({SG}!$B${GR1}:$B${GR2},MATCH(MAX($U$9:$U$14),$U$9:$U$14,0)),"")', None, False, WHITE, 'left')
B.fx(ws, 10, 20, f'=IFERROR(MAX($U$9:$U$14),0)', PCT, False, WHITE)
B.fx(ws, 13, 20, f'=IF(N({SG}!$E$15)=0,0,SUM($V$9:$V$14)/{SG}!$E$15)', PCT, False, WHITE)
B.fx(ws, 11, 20, f'=IFERROR(AVERAGE({MD}!$J$9:$K$9),"")', '0.0', False, WHITE)
B.fx(ws, 12, 20, f'=IF(COUNT({NUM(6)},{NUM(7)})=0,"",AVERAGE({NUM(6)},{NUM(7)}))', '0.0', False, WHITE)
ws.column_dimensions['T'].hidden = True
mx = f'MAX({SR})'
summary = (
    f'=IF(N({NUM(0)})=0,"Fill in Shared Income, Joint Bills and the Spending Plan for "&{CML}&" and your summary writes itself here.",'
    f'"In "&{CML}&" we earned "&{money(NUM(0))}&" together ("&{NA}&" "&{money(f"INDEX({SI}!$C$9:$C$20,{CMI})")}&", "&{NB}&" "&{money(f"INDEX({SI}!$E$9:$E$20,{CMI})")}&IF(N(INDEX({SI}!$G$9:$G$20,{CMI}))>0,", + "&{money(f"INDEX({SI}!$G$9:$G$20,{CMI})")}&" other","")&"). '
    f'Joint bills came to "&{money(NUM(1))}&": "&{NA}&" paid "&{money(f"IF(N({NUM(1)})=0,0,{BA_T})")}&" and "&{NB}&" "&{money(f"IF(N({NUM(1)})=0,0,{BB_T})")}&" ("&TEXT({PA},"0%")&" / "&TEXT({PB},"0%")&"). '
    f'We spent "&{money(NUM(2))}&" against a plan of "&{money(NUM(3))}&IF({NUM(2)}>{NUM(3)}," ("&{money(f"{NUM(2)}-{NUM(3)}")}&" over)."," ("&{money(f"{NUM(3)}-{NUM(2)}")}&" under).")&" '
    f'"&IF({mx}>0,"Biggest overspend: "&INDEX({SC},MATCH({mx},{SR},0))&", "&{money(mx)}&" over plan. ","No category went over plan. ")&'
    f'"We put "&{money(NUM(4))}&" into our goals"&IF($T$9="",". ","; "&$T$9&" is "&TEXT($T$10,"0%")&" of the way there (all goals: "&TEXT(N($T$13),"0%")&"). ")&'
    f'"Left over: "&{money(NUM(5))}&"."&IF($T$12="",""," Talking about money felt "&TEXT($T$12,"0.0")&" out of 10"&IF($T$11="",".", " (it was "&TEXT($T$11,"0.0")&" at our first money date)."))'
    f')')
B.text(ws, 9, 2, 'OUR MONTH IN PLAIN WORDS  ·  one cell, ready to copy', 8, True, DSAGE, w=8, indent=1)
B.box(ws, 10, 2, 15, 9, WHITE, GOLD)
c = B.text(ws, 10, 2, summary, 14, False, CHAR, w=8, h=6, valign='top', indent=1)
for r in range(10, 16):
    ws.row_dimensions[r].height = 34
B.text(ws, 9, 11, 'HOW TO USE IT', 8, True, DSAGE, w=7, indent=1)
B.tip(ws, 10, 11, 'Read it out loud at the start of your money date: it is the whole month in one breath, with no blame in it.\n\n'
      'Copy the cell into your notes app, or send it to each other, so you both see the same picture.\n\n'
      'Want to look back? Change the month on the Settings tab and the summary rewrites itself.', 7, 6)
QR = N0 + 13
B.section(ws, QR, 2, 'Five questions for the two of you', 12)
B.th(ws, QR + 1, 2, 'QUESTION', 7); B.th(ws, QR + 1, 9, f'=UPPER({NA})', 4); B.th(ws, QR + 1, 13, f'=UPPER({NB})', 5)
QS = ['Which money moment this month brought us closer, and which one pulled us apart a little?',
      'Was there a spend one of us felt uneasy about but did not mention? What stopped us saying it?',
      'Where did our money go somewhere that really mattered to us both?',
      'Talking about money felt a ___ out of 10 this month. What would make it one point easier next time?',
      'What is one small thing each of us will do before our next money date?']
EX_A = ['Booking Lisbon together felt great. The car repair bill made me tense for a week.',
        'The new jacket. I didn\'t say anything because I didn\'t want to sound like your mum.',
        'Lisbon fund and your sister\'s birthday dinner.',
        '8. If we did it before dinner, not after.',
        'Move £300 to Lisbon on payday.']
EX_B = ['Same: Lisbon. Pulled apart: the takeaway nights I didn\'t mention.',
        'Takeaways. I knew we were over and felt embarrassed.',
        'Lisbon. And the emergency fund passing £4,000 felt really safe.',
        '7. Starting with a win each, like we did today.',
        'Cook twice a week so eating out drops back under £200.']
for i, q in enumerate(QS):
    r = QR + 2 + i
    B.text(ws, r, 2, f'{i + 1}.  {q}', 10, False, CHAR, w=7, indent=1)
    B.inp(ws, r, 9, EX_A[i], w=4); B.inp(ws, r, 13, EX_B[i], w=5)
    for cc in (9, 13):
        ws.cell(r, cc).alignment = ws.cell(r, cc).alignment.copy(wrap_text=True, vertical='center')
    ws.row_dimensions[r].height = 48
r = QR + 8
B.tip(ws, r, 2, 'Want a second opinion? Copy your summary and these questions into any AI assistant you use (ChatGPT, Gemini, Copilot) '
      'and ask it to reply like a kind, honest money coach.', 16, 1, 32)
B.text(ws, r + 1, 2, 'Optional. Everything on this tab works on its own, with no AI at all: the summary is written by formulas from your own numbers.',
       8.5, False, MUTED, w=16, italic=True)
B.protect(ws)

# ================================================================== Start Here
ws = S['Start Here']
B.page(ws, 'Start Here', 'How the kit fits together, and what to do first. About 15 minutes to set up.',
       {2: 6, 3: 30, 4: 3, 5: 70}, ncols=5, nrows=50)
steps = [('1', 'Read the Conversation Starter first', 'Take the Money Personality Quiz on your own, find your couple type, read the Ground Rules aloud together.'),
         ('2', 'Settings', 'Your names, your currency, the first month of your planner and how you split bills.'),
         ('3', 'Shared Income + Joint Bills', 'Take-home pay for each of you, then every bill you share. Your fair split is worked out for you.'),
         ('4', 'Spending Plan + Shared Goals', 'A plan for shared spending, and up to 6 goals. This is Week 2 and Week 3 of the plan.'),
         ('5', 'Money Dates', 'Do the 4-week plan (the PDF), one 20-minute date a week. Log each one here: cards, a 1-10 score, one agreement.'),
         ('6', 'Monthly Check-in', 'Once a month: type last month\'s numbers, read your month in plain words, answer the five questions.')]
B.th(ws, 7, 2, 'STEP', 1); B.th(ws, 7, 3, 'WHERE', 1); B.th(ws, 7, 5, 'WHAT TO DO', 1)
for i, (n, a, b) in enumerate(steps):
    r = 8 + i
    B.fx(ws, r, 2, n, None, True, GOLDT, 'center', size=12)
    B.fx(ws, r, 3, a, None, True, None, 'left')
    B.fx(ws, r, 4, '', None)
    B.fx(ws, r, 5, b, None, False, None, 'left', size=9.5)
    ws.cell(r, 5).alignment = ws.cell(r, 5).alignment.copy(wrap_text=True)
    ws.row_dimensions[r].height = 36
B.section(ws, 15, 2, 'Good to know', 4)
tips = ['Yellow boxes are for typing. Everything else is worked out for you and locked so nothing breaks (no password: Review > Unprotect).',
        'Google Sheets: File > Import (or upload and open with Google Sheets). Move between tabs with the tab bar along the bottom.',
        'Progress bars show as solid bars in Google Sheets and as text bars in Excel. Both work.',
        'Any currency: type your symbol on Settings. Amounts are plain numbers.',
        'This EXAMPLE file shows Alex and Jordan\'s first five months. Your own numbers go in the BLANK file.',
        'Questions? Email joel@wayofwealthcoaching.com. Free Cash Flow Session: calendly.com/thewayofwealth-official/your-cash-flow-session']
for i, t in enumerate(tips):
    r = 16 + i
    B.fx(ws, r, 2, '✓', None, True, None, 'center', color=DSAGE)
    B.fx(ws, r, 3, t, None, False, None, 'left', 3, size=9.5)
    ws.cell(r, 3).alignment = ws.cell(r, 3).alignment.copy(wrap_text=True)
    ws.row_dimensions[r].height = 30
if BLANK:
    ws.cell(20, 3).value = 'This is your BLANK file. Open the EXAMPLE file to see Alex and Jordan\'s first five months filled in.'
B.protect(ws)

# ================================================================== Dashboard
ws = S['Dashboard']
B.page(ws, 'Couples Money Date Planner', '', ncols=16, nrows=110)
ws['B3'] = f'={NA}&" and "&{NB}&"  ·  showing "&{CML}&"  ·  money date: "&IF(Settings!$C$14="","pick a day on Settings",Settings!$C$14)'
ws['B3'].font = F(10, color=MUTED)
D0 = 80
for r, h in [(7, 22), (8, 30), (9, 18), (10, 8), (11, 22), (12, 30), (13, 18)]:
    ws.row_dimensions[r].height = h
CIN = lambda i: f"{CI}!$N${N0 + i}"
B.hero(ws, 7, 2, 7, 7, '="LEFT OVER IN "&UPPER(' + CML + ')&", TOGETHER"', f'={money(CIN(5))}',
       f'=IF(N({CIN(0)})=0,"Fill in Shared Income, Joint Bills and the Spending Plan to see your month.",'
       f'"Earned "&{money(CIN(0))}&", joint bills "&{money(CIN(1))}&", spent "&{money(CIN(2))}&", "&{money(CIN(4))}&" into goals.")',
       'Income minus bills, shared spending and goal savings.')
B.kpi(ws, 7, 10, 'INCOME TOGETHER', f'={money(CIN(0))}',
      f'={NA}&" "&{money(f"INDEX({SI}!$C$9:$C$20,{CMI})")}&" · "&{NB}&" "&{money(f"INDEX({SI}!$E$9:$E$20,{CMI})")}', accent=DSAGE)
B.kpi(ws, 7, 14, 'JOINT BILLS', f'={money(CIN(1))}', f'={NA}&" "&{money(BA_T)}&" · "&{NB}&" "&{money(BB_T)}', accent=GOLD)
B.kpi(ws, 11, 10, 'SHARED SPENDING', f'={money(CIN(2))}',
      f'=IF({CIN(2)}>{CIN(3)},"▲ "&{money(f"{CIN(2)}-{CIN(3)}")}&" over plan","✓ "&{money(f"{CIN(3)}-{CIN(2)}")}&" under plan")', accent=CORAL)
B.kpi(ws, 11, 14, 'INTO GOALS THIS MONTH', f'={money(CIN(4))}', f'="all goals "&TEXT(N({SG}!$I$15),"0%")&" of the way"', accent=DSAGE)
# next step bar
nxt = (f'=IF(TRIM({CUR})="","First: open Settings and type your currency symbol ($, £, €, A$...) and your two names. Every sentence uses them.",'
       f'IF(COUNT({MD}!$C$9:$C$12)<4,"Next: Week "&(COUNT({MD}!$C$9:$C$12)+1)&" of the 4-week plan. 20 minutes, phones down, cards from the PDF.",'
       f'IF(INDEX({MD}!$C${MR1}:$C${MR2},{CMI})="","This month\'s money date is still to do: "&IF(Settings!$C$14="","pick a day on Settings",Settings!$C$14)&". Then answer the five Check-in questions.",'
       f'IF(MAX({CI}!$S${N0 + 1}:$S${N0 + 10})>0,"Done for "&{CML}&". Talk about "&INDEX({CI}!$B${N0 + 1}:$B${N0 + 10},MATCH(MAX({CI}!$S${N0 + 1}:$S${N0 + 10}),{CI}!$S${N0 + 1}:$S${N0 + 10},0))&" at the next one: it went over plan.",'
       f'"Done for "&{CML}&". Everything on plan: pick a card still waiting on the Conversation Cards tab."))))')
B.bar(ws, 15, 2, 15, 'NEXT', nxt)
for r, h in [(17, 22), (18, 30), (19, 18)]:
    ws.row_dimensions[r].height = h
DONE = f'COUNT({MD}!$C${MR1}:$C${MR2})'
B.kpi(ws, 17, 2, 'MONEY DATES DONE', f'={DONE}&" of 12"', f'="+ "&COUNT({MD}!$C$9:$C$12)&" of 4 in the 4-week start"', accent=CHAR)
B.kpi(ws, 17, 6, 'COMFORT TALKING (1-10)', f'=IF({CI}!$T$12="","–",TEXT({CI}!$T$12,"0.0"))',
      f'=IF({CI}!$T$12="","log this month\'s date",IF({CI}!$T$11="","card 2.1 at each date","up from "&TEXT({CI}!$T$11,"0.0")&" at week 1"))', accent=GOLD)
B.kpi(ws, 17, 10, 'OUR SPLIT', f'=TEXT({PA},"0%")&" / "&TEXT({PB},"0%")', f'=Settings!$C$12', accent=DSAGE)
B.kpi(ws, 17, 14, 'BIGGEST OVERSPEND', f'=IF(MAX({CI}!$S${N0 + 1}:$S${N0 + 10})>0,INDEX({CI}!$B${N0 + 1}:$B${N0 + 10},MATCH(MAX({CI}!$S${N0 + 1}:$S${N0 + 10}),{CI}!$S${N0 + 1}:$S${N0 + 10},0)),"None")',
      f'=IF(MAX({CI}!$S${N0 + 1}:$S${N0 + 10})>0,{money(f"MAX({CI}!$S${N0 + 1}:$S${N0 + 10})")}&" over plan","every category on plan")', accent=CORAL)
ws.cell(18, 14).font = F(13, True, INK)
# ---- chart data
B.section(ws, D0, 2, 'The numbers behind the charts', 10)
B.th(ws, D0 + 1, 2, 'MONTH', 2); B.th(ws, D0 + 1, 4, 'Money in', 2, 'right'); B.th(ws, D0 + 1, 6, 'Money out', 2, 'right')
B.th(ws, D0 + 1, 8, 'Left over', 2, 'right')
for k in range(12):
    r = D0 + 2 + k
    B.fx(ws, r, 2, f'=LEFT({LBL(k)},3)', None, True, align='left', w=2)
    B.fx(ws, r, 4, f'=N({INC_T(k)})', MONEY, w=2)
    B.fx(ws, r, 6, f'=IF(D{r}=0,0,{BILLS_T}+N(INDEX({SP}!$D$19:$O$19,{k + 1}))+N({SG}!$J${CG1 + k}))', MONEY, w=2)
    B.fx(ws, r, 8, f'=D{r}-F{r}', MONEY, w=2)
B.th(ws, D0 + 1, 11, 'CATEGORY', 2); B.th(ws, D0 + 1, 13, 'Plan', 1, 'right'); B.th(ws, D0 + 1, 14, 'Spent', 1, 'right')
for i in range(8):
    r = D0 + 2 + i
    B.fx(ws, r, 11, f'=LEFT({CI}!$B${N0 + 1 + i},18)', None, False, align='left', w=2)
    B.fx(ws, r, 13, f'=N({CI}!$E${N0 + 1 + i})', MONEY); B.fx(ws, r, 14, f'=N({CI}!$F${N0 + 1 + i})', MONEY)
G0 = D0 + 16
B.th(ws, G0, 2, 'GOAL', 2); B.th(ws, G0, 4, 'Saved', 2, 'right'); B.th(ws, G0, 6, 'Still to save', 2, 'right')
for i in range(6):
    r = G0 + 1 + i
    B.fx(ws, r, 2, f'=IF({SG}!$B${GR1 + i}="","",LEFT({SG}!$B${GR1 + i},20))', None, False, align='left', w=2)
    B.fx(ws, r, 4, f'=N({SG}!$H${GR1 + i})', MONEY, w=2)
    B.fx(ws, r, 6, f'=MAX(0,N({SG}!$E${GR1 + i})-N({SG}!$H${GR1 + i}))', MONEY, w=2)
B.th(ws, G0, 11, 'WHO PAYS THE BILLS', 2); B.th(ws, G0, 13, 'Per month', 2, 'right')
B.fx(ws, G0 + 1, 11, f'={NA}', None, False, align='left', w=2); B.fx(ws, G0 + 1, 13, f'=N({BA_T})', MONEY, w=2)
B.fx(ws, G0 + 2, 11, f'={NB}', None, False, align='left', w=2); B.fx(ws, G0 + 2, 13, f'=N({BB_T})', MONEY, w=2)
C0 = G0 + 9
B.th(ws, C0, 2, 'DATE', 2); B.th(ws, C0, 4, f'={NA}', 2, 'right'); B.th(ws, C0, 6, f'={NB}', 2, 'right')
labs = ['Wk 1', 'Wk 2', 'Wk 3', 'Wk 4'] + [None] * 12
for k in range(16):
    r = C0 + 1 + k
    src = 9 + k if k < 4 else MR1 + k - 4
    B.fx(ws, r, 2, labs[k] if labs[k] else f'=LEFT({LBL(k - 4)},3)', None, False, align='left', w=2)
    B.fx(ws, r, 4, f'=N({MD}!$J${src})', '0', w=2); B.fx(ws, r, 6, f'=N({MD}!$K${src})', '0', w=2)
# ---- charts
bar_chart(ws, 'B21', 'Money in vs money out, by month', Reference(ws, min_col=2, min_row=D0 + 2, max_row=D0 + 13),
          Reference(ws, min_col=4, min_row=D0 + 1, max_row=D0 + 13), w=11.8, h=7.4, colors=[DSAGE])
ch = ws._charts[-1]
ch2 = BarChart(); ch2.add_data(Reference(ws, min_col=6, min_row=D0 + 1, max_row=D0 + 13), titles_from_data=True)
s2 = ch2.series[0]; s2.graphicalProperties.solidFill = GOLD; s2.graphicalProperties.line.solidFill = GOLD
ch.series.append(s2); ch.gapWidth = 40
ch.series[0].tx = SeriesLabel(v='Money in'); ch.series[1].tx = SeriesLabel(v='Bills + spending + goals')
bar_chart(ws, 'J21', 'Spending vs plan this month', Reference(ws, min_col=11, min_row=D0 + 2, max_row=D0 + 9),
          Reference(ws, min_col=13, max_col=14, min_row=D0 + 1, max_row=D0 + 9), w=11.8, h=7.4, horizontal=True, colors=[SAGE, CORAL])
sp_ch = ws._charts[-1]; sp_ch.y_axis.delete = True
for s_ in sp_ch.series: s_.dLbls = None
sp_ch.gapWidth = 50
bar_chart(ws, 'B37', 'Shared goals: saved and to go', Reference(ws, min_col=2, min_row=G0 + 1, max_row=G0 + 6),
          Reference(ws, min_col=4, max_col=7, min_row=G0, max_row=G0 + 6), w=11.8, h=7.4, horizontal=True, stacked=True, colors=[DSAGE, 'E3DCCF'])
gch = ws._charts[-1]
gch.series = [s for s in gch.series if s.tx and s.tx.strRef and s.tx.strRef.f.split('!')[-1].replace('$', '')[0] in ('D', 'F')]
for s_, col in zip(gch.series, [DSAGE, 'D9CBB5']):
    s_.graphicalProperties.solidFill = col; s_.graphicalProperties.line.solidFill = col
    s_.dLbls = None
doughnut(ws, 'J37', 'Who pays the joint bills', Reference(ws, min_col=11, min_row=G0 + 1, max_row=G0 + 2),
         Reference(ws, min_col=13, min_row=G0, max_row=G0 + 2), w=11.8, h=7.4, colors=[CHAR, GOLD])
bar_chart(ws, 'B53', 'Comfort talking about money (card 2.1, 1-10)', Reference(ws, min_col=2, min_row=C0 + 1, max_row=C0 + 16),
          Reference(ws, min_col=4, min_row=C0, max_row=C0 + 16), w=23.6, h=7.0, colors=[CHAR])
cch = ws._charts[-1]
ch3 = BarChart(); ch3.add_data(Reference(ws, min_col=6, min_row=C0, max_row=C0 + 16), titles_from_data=True)
s3 = ch3.series[0]; s3.graphicalProperties.solidFill = GOLD; s3.graphicalProperties.line.solidFill = GOLD
cch.series.append(s3); cch.gapWidth = 50
cch.y_axis.scaling.min = 0; cch.y_axis.scaling.max = 10; cch.y_axis.majorUnit = 2
for x in ws._charts:
    x.roundedCorners = False
    if x.legend is not None: x.legend.overlay = False
B.text(ws, 68, 2, 'Way of Wealth Studio  ·  general information, not financial advice  ·  joel@wayofwealthcoaching.com', 8.5, False, MUTED, w=15)
B.protect(ws)

# ================================================================== save
AREAS = {'Dashboard': 'A1:R69', 'Start Here': 'A1:F22', 'Settings': 'A1:F21', 'Shared Income': 'A1:N24', 'Joint Bills': f'A1:O{T0 + 7}',
         'Spending Plan': 'A1:R23', 'Shared Goals': f'A1:P{CG2 + 4}', 'Money Dates': f'A1:R{MR2 + 3}', 'Monthly Check-in': f'A1:R{QR + 10}',
         'Conversation Cards': 'A1:Q32'}
orig_save = B.wb.save
B.wb.save = lambda p: None
B.save(OUT, AREAS)
for w_ in B.wb.worksheets:
    w_.oddFooter.center.text = 'Way of Wealth Studio  ·  Couples Money Date Planner'
    w_.oddFooter.center.size = 8
B.wb.active = 1 if BLANK else 0
if BLANK:
    for _w in B.wb.worksheets: _w.sheet_view.tabSelected = False
    B.wb.worksheets[1].sheet_view.tabSelected = True
orig_save(OUT)
print('saved', OUT)
