"""US Self-Employed Tax Deduction and Quarterly Tax Tracker - Way of Wealth Studio (19 Nov 2026).
For US 1099 freelancers, sole proprietors and side hustlers. Tax years 2026 and 2027, picked with ONE dropdown.
python3 build_xlsx.py out/file.xlsx [blank]

Figures checked by web search on 19 Nov 2026 (see the Tax Rates tab for each source):
- Schedule C (Form 1040) line numbers and titles: 2025 form and instructions (irs.gov/instructions/i1040sc), the current form.
- Standard mileage rate 2026: 72.5 cents (Notice 2026-10, Jan-Jun) and 76 cents from 1 Jul 2026 (Announcement 2026-11).
- Social Security wage base: $184,500 (2026), $192,300 (2027) - SSA.
- Brackets + standard deduction: 2026 Rev. Proc. 2025-32 (IRS IR-2025-103, Tax Foundation); 2027 Rev. Proc. 2026-35 (Tax Foundation).
- 1040-ES due dates: 15 Apr, 15 Jun, 15 Sep, 15 Jan (moved to the next business day when it falls on a weekend or holiday).
- 1099-NEC threshold $2,000 for payments from 2026 (One Big Beautiful Bill Act).
Excel 2016+ and Google Sheets only: no XLOOKUP / FILTER / SORT / UNIQUE / LET, no shapes, no data bars.
"""
import sys, os, datetime as dt
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
USD = '$#,##0;-$#,##0;"–"'
USD2 = '$#,##0.00;-$#,##0.00;"–"'
DATE = 'mmm d, yyyy'
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
MON = [m[:3] for m in MONTHS]
STATUSES = ['Single', 'Married filing jointly', 'Head of household', 'Married filing separately']

TABS = [('Dashboard', GOLD), ('Start Here', GOLD), ('Settings', DSAGE), ('Income Log', DSAGE), ('Deductions', DSAGE),
        ('Mileage', DSAGE), ('Schedule C', CHAR), ('Tax Estimate', CHAR), ('Quarterly Tax', CORAL),
        ('Accountant Checklist', GOLD), ('Monthly Money Check-in', CORAL), ('Tax Rates', CHAR)]
B = Book(TABS, BLANK)
S = B.s
IL, DL_, ML, SC, TE, QT, AC, MC, TR = ("'Income Log'", "Deductions", "Mileage", "'Schedule C'", "'Tax Estimate'", "'Quarterly Tax'",
                                       "'Accountant Checklist'", "'Monthly Money Check-in'", "'Tax Rates'")
M = lambda x: f'TEXT({x},"$#,##0")'        # money in words (US-only product: $ is fixed)


def bar_f(pct, color, n=12):
    return (f'IFERROR(SPARKLINE(MAX(0,MIN(1,{pct})),{{"charttype","bar";"max",1;"color1","#{color}"}}),'
            f'REPT("█",ROUND(MAX(0,MIN(1,{pct}))*{n},0))&REPT("░",{n}-ROUND(MAX(0,MIN(1,{pct}))*{n},0)))')


def check_fmt(ws, rng, first):
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'LEFT({first},1)="✕"'], font=Font(name=FONT, color=CORAL, bold=True)))
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'LEFT({first},1)="✓"'], font=Font(name=FONT, color=DSAGE, bold=True)))
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'LEFT({first},1)="–"'], font=Font(name=FONT, color=MUTED, bold=False)))


# ================================================================== categories (dropdown label, Schedule C line, check-in group)
CATS = [('Line 4 · Cost of goods sold (products you sell)', 'Line 4'),
        ('Line 8 · Advertising and marketing', 'Line 8'),
        ('Line 9 · Parking and tolls (business trips)', 'Line 9'),
        ('Line 10 · Commissions and platform fees', 'Line 10'),
        ('Line 11 · Contract labor (freelancers you paid)', 'Line 11'),
        ('Line 13 · Equipment: depreciation and section 179', 'Line 13'),
        ('Line 14 · Employee benefit programs', 'Line 14'),
        ('Line 15 · Business insurance (not health)', 'Line 15'),
        ('Line 16a · Mortgage interest (business property)', 'Line 16a'),
        ('Line 16b · Other business interest', 'Line 16b'),
        ('Line 17 · Legal and professional services', 'Line 17'),
        ('Line 18 · Office expense', 'Line 18'),
        ('Line 19 · Pension and profit-sharing (employees)', 'Line 19'),
        ('Line 20a · Rent: vehicles, machinery, equipment', 'Line 20a'),
        ('Line 20b · Rent: other business property', 'Line 20b'),
        ('Line 21 · Repairs and maintenance', 'Line 21'),
        ('Line 22 · Supplies', 'Line 22'),
        ('Line 23 · Taxes and licenses', 'Line 23'),
        ('Line 24a · Travel (flights, hotels)', 'Line 24a'),
        ('Line 24b · Business meals (50% counted)', 'Line 24b'),
        ('Line 25 · Utilities (business phone, internet)', 'Line 25'),
        ('Line 26 · Wages (employees)', 'Line 26'),
        ('Line 27b · Other: software and subscriptions', 'Line 27b'),
        ('Line 27b · Other: education and training', 'Line 27b'),
        ('Line 27b · Other: bank fees', 'Line 27b'),
        ('Line 27b · Other: dues and memberships', 'Line 27b'),
        ('Line 27b · Other: anything else', 'Line 27b')]
CAT = {c[0].split(' · ')[1].split(' (')[0].split(':')[0]: c[0] for c in CATS}
C_ = lambda key: next(c[0] for c in CATS if key in c[0])
CATROW0 = 30
NCAT = len(CATS)
CATREF = f'=Settings!$G${CATROW0}:$G${CATROW0 + NCAT - 1}'
CATS_RNG, LINES_RNG = f'Settings!$G${CATROW0}:$G${CATROW0 + NCAT - 1}', f'Settings!$H${CATROW0}:$H${CATROW0 + NCAT - 1}'

# ================================================================== Settings
ws = S['Settings']
B.page(ws, 'Settings', 'Step 1: fill in the yellow boxes once. Pick the tax year here and every tab, date and rate follows it.',
       {2: 50, 3: 26, 4: 3, 5: 64}, ncols=5, nrows=60)
B.th(ws, 6, 2, 'ABOUT YOU'); B.th(ws, 6, 3, 'TYPE OR PICK HERE'); B.th(ws, 6, 5, 'WHAT IT MEANS')
SET = [('name', 'Your name', 'Jordan Lee', None, False, 'Shown on the Dashboard. Nothing is sent anywhere.'),
       ('biz', 'What your business does', 'Freelance UX design', None, False, 'Schedule C line A: your principal business or profession.'),
       ('ty', 'TAX YEAR (the one dropdown that drives everything)', 2026, '0', True,
        'Pick 2026 or 2027. Logs count only dates in that year; due dates, brackets, mileage rate and wage base all switch with it.'),
       ('fs', 'Filing status', 'Single', None, True, 'Picks your standard deduction and tax brackets.'),
       ('w2', 'W-2 wages from a job (optional)', 0, USD, False, 'If you also had a job. Leave 0 if not.'),
       ('wh', 'Federal tax withheld from that job (optional)', 0, USD, False, 'Box 2 of your W-2. It counts towards what you owe.'),
       ('oth', 'Other income: interest, dividends (optional)', 350, USD, False, 'Rough is fine. Used only in the income tax estimate.'),
       ('extra', 'Profit you still expect this year (optional)', 5600, USD, False,
        'Income you expect minus costs, for months not logged yet. Makes the quarterly estimate fairer early in the year.'),
       ('prior', 'Last year\'s total tax (Form 1040 line 24)', 12000, USD, False, 'For the safe-harbor amount. Leave blank on your first year.'),
       ('agi150', 'Was last year\'s AGI over $150,000? ($75,000 if married filing separately)', 'No', None, True,
        'Yes = safe harbor is 110% of last year\'s tax instead of 100%.'),
       ('state', 'Your state income tax rate (optional, rough)', 0.05, '0.0%', False,
        'A rough flat %, applied to your AGI, for a ballpark state figure. 0% if your state has no income tax. States have their own rules.'),
       ('sqft', 'Home office: square feet used only for work (simplified method)', 150, '#,##0', False,
        'Regular and exclusive use only. $5 per sq ft, up to 300 sq ft. Leave 0 if you have no home office.'),
       ('ho_act', 'OR home office actual expenses from Form 8829 (optional)', None, USD, False, 'Only if your tax pro uses Form 8829. Replaces the simplified figure.'),
       ('health', 'Self-employed health insurance premiums paid this year', 3600, USD, False,
        'Only if you were not eligible for an employer plan. Reduces income tax, not SE tax.'),
       ('retire', 'Retirement contributions: SEP-IRA, solo 401(k) (optional)', 4000, USD, False, 'Reduces income tax in this estimate.'),
       ('qbi', 'Include the 20% QBI deduction?', 'Yes', None, True,
        'Most freelancers qualify. At high incomes (about $200,000 single) limits can apply: ask your tax pro.'),
       ('setaside', 'Set aside this % of every payment for tax', 0.25, '0%', True,
        'Used in the Income Log, tax pot and check-in. The Tax Estimate tab suggests a % for you.')]
SR = {}
for i, (k, lab, v, fmt, keep, hlp) in enumerate(SET):
    r = 7 + i; SR[k] = f'Settings!$C${r}'
    B.text(ws, r, 2, lab, 10, True); B.inp(ws, r, 3, v, fmt, keep=keep); B.text(ws, r, 5, hlp, 9, color=MUTED)
    ws.row_dimensions[r].height = 34 if len(hlp) > 72 or len(lab) > 52 else 26
    if k == 'ty':
        for cc in (2, 3): ws.cell(r, cc).font = F(10.5, True, '1F3B73' if cc == 3 else INK)
B.dv(ws, SR['ty'].split('!')[1].replace('$', ''), ['2026', '2027'])
B.dv(ws, SR['fs'].split('!')[1].replace('$', ''), STATUSES)
for k in ('agi150', 'qbi'):
    B.dv(ws, SR[k].split('!')[1].replace('$', ''), ['No', 'Yes'])
TY = SR['ty']
B.tip(ws, 25, 2, 'Estimate, not tax advice. This tracker organises your numbers and estimates your tax so there are no surprises. It does not file anything. '
      'Your tax pro or the IRS calculation is final. Questions about the file: joel@wayofwealthcoaching.com', 4, 1, 44)
# hidden lists + helpers (columns G onward)
B.text(ws, 6, 7, 'LISTS (USED BY DROPDOWNS)', 7, True, 'B9B2A6')
for i, (lab, line) in enumerate(CATS):
    ws.cell(CATROW0 + i, 7, lab).font = F(8, color='A79F92'); ws.cell(CATROW0 + i, 8, line).font = F(8, color='A79F92')
for i, m in enumerate(MONTHS):
    ws.cell(7 + i, 9, m).font = F(8, color='A79F92')
for i, s in enumerate(STATUSES):
    ws.cell(7 + i, 10, s).font = F(8, color='A79F92')
ws['M7'] = f'=IF(OR({TY}=2027,{TY}="2027"),2,1)'; ws['M8'] = f'=IFERROR(MATCH({SR["fs"]},$J$7:$J$10,0),1)'
ws['M9'] = f'=IF(OR({TY}=2027,{TY}="2027"),2027,2026)'
for c in ('M7', 'M8', 'M9'): ws[c].font = F(8, color='A79F92')
for col in 'GHIJKLM':
    ws.column_dimensions[col].hidden = True
YI, SI, YR = 'Settings!$M$7', 'Settings!$M$8', 'Settings!$M$9'
YS, YE = f'DATE({YR},1,1)', f'DATE({YR},12,31)'
MONTHREF = 'Settings!$I$7:$I$18'
B.protect(ws)

# ================================================================== Tax Rates (both years side by side, the selected one in column E)
ws = S['Tax Rates']
B.page(ws, 'Tax rates and due dates', 'Every number the tracker uses, for 2026 and 2027. Column E follows the tax year on Settings. Yellow = update if the IRS changes it.',
       {2: 50, 3: 15, 4: 15, 5: 15, 6: 13, 7: 13, 8: 13, 9: 13, 10: 13, 11: 13, 12: 13}, ncols=12, nrows=70)
B.th(ws, 8, 2, 'RATE OR AMOUNT'); B.th(ws, 8, 3, '2026', align='right'); B.th(ws, 8, 4, '2027', align='right')
B.th(ws, 8, 5, 'YOUR TAX YEAR', align='right'); B.th(ws, 8, 6, 'SOURCE (CHECKED 19 NOV 2026)', 7)
d = lambda y, m, dd: dt.date(y, m, dd)
RATES = [('nef', 'Net earnings factor for SE tax', 0.9235, 0.9235, '0.00%', 'Schedule SE line 4a (92.35%)'),
         ('ssr', 'Social Security part of SE tax', 0.124, 0.124, '0.0%', 'Schedule SE instructions'),
         ('mcr', 'Medicare part of SE tax', 0.029, 0.029, '0.0%', 'Schedule SE instructions'),
         ('wb', 'Social Security wage base (12.4% stops here)', 184500, 192300, USD, 'SSA: $184,500 for 2026, $192,300 for 2027 (announced Oct 2026)'),
         ('semin', 'No SE tax if net earnings are under', 400, 400, USD, 'Schedule SE instructions'),
         ('sd1', 'Standard deduction: single', 16100, 16600, USD, 'IRS Rev. Proc. 2025-32 (2026), Rev. Proc. 2026-35 (2027)'),
         ('sd2', 'Standard deduction: married filing jointly', 32200, 33200, USD, 'same'),
         ('sd3', 'Standard deduction: head of household', 24150, 24925, USD, 'same'),
         ('sd4', 'Standard deduction: married filing separately', 16100, 16600, USD, 'same'),
         ('mile1', 'Standard mileage rate, Jan 1 to Jun 30 (per mile)', 0.725, 0.76, '$0.000', 'IRS Notice 2026-10 / IR-2025-128 (irs.gov newsroom): 72.5 cents. 2027: not out yet (IRS sets it in Dec): placeholder, update it'),
         ('mile2', 'Standard mileage rate, Jul 1 to Dec 31 (per mile)', 0.76, 0.76, '$0.000', 'IRS Announcement 2026-11: 76 cents from Jul 1, 2026 (journalofaccountancy.com/news/2026/jul/irs-raises-standard-mileage-rates-for-remainder-of-2026). 2027: placeholder'),
         ('hosq', 'Home office simplified method, per sq ft', 5, 5, '$0.00', 'Schedule C instructions, line 30'),
         ('homax', 'Home office simplified method, max sq ft', 300, 300, '#,##0', 'same'),
         ('meals', 'Business meals: share you can deduct', 0.5, 0.5, '0%', 'Schedule C instructions, line 24b'),
         ('qbi', 'QBI deduction rate', 0.2, 0.2, '0%', 'Section 199A, made permanent in 2025'),
         ('nec', 'Clients send a 1099-NEC if they paid you at least', 2000, 2000, USD, 'One Big Beautiful Bill Act: $2,000 for payments from 2026 ($600 before)'),
         ('sh90', 'Safe harbor: share of this year\'s tax', 0.9, 0.9, '0%', 'IRS Form 1040-ES instructions'),
         ('sh100', 'Safe harbor: share of last year\'s tax', 1.0, 1.0, '0%', 'same'),
         ('sh110', '...if last year\'s AGI was over $150,000', 1.1, 1.1, '0%', 'same'),
         ('min1k', 'No estimated payments needed if you owe less than', 1000, 1000, USD, 'same'),
         ('q1', 'Q1 payment due (income Jan 1 to Mar 31)', d(2026, 4, 15), d(2027, 4, 15), DATE, 'Form 1040-ES'),
         ('q2', 'Q2 payment due (income Apr 1 to May 31)', d(2026, 6, 15), d(2027, 6, 15), DATE, 'Form 1040-ES'),
         ('q3', 'Q3 payment due (income Jun 1 to Aug 31)', d(2026, 9, 15), d(2027, 9, 15), DATE, 'Form 1040-ES'),
         ('q4', 'Q4 payment due (income Sep 1 to Dec 31)', d(2027, 1, 15), d(2028, 1, 18), DATE,
          'Form 1040-ES. Jan 15, 2028 is a Saturday and Jan 17 is MLK Day, so it moves to Jan 18')]
RT = {}
for i, (k, lab, a, b, fmt, src) in enumerate(RATES):
    r = 9 + i; RT[k] = f"{TR}!$E${r}"
    B.fx(ws, r, 2, lab, None, False, None, 'left')
    B.inp(ws, r, 3, a, fmt, 'right', keep=True); B.inp(ws, r, 4, b, fmt, 'right', keep=True)
    B.fx(ws, r, 5, f'=INDEX(C{r}:D{r},{YI})', fmt, True, TINT)
    B.fx(ws, r, 6, src, None, False, None, 'left', 7, MUTED, 8.5)
QROWS = [9 + [x[0] for x in RATES].index(q) for q in ('q1', 'q2', 'q3', 'q4')]
QDUE = f"{TR}!$E${QROWS[0]}:$E${QROWS[3]}"
SD = f'INDEX({TR}!$E${9 + 5}:$E${9 + 8},{SI})'
# brackets
BR0 = 9 + len(RATES) + 2
B.section(ws, BR0, 2, 'Federal income tax brackets (taxable income where each rate starts)', 8)
B.th(ws, BR0 + 1, 2, 'RATE'); B.th(ws, BR0 + 1, 3, 'STEP UP', align='right')
heads = ['2026 single', '2026 joint', '2026 head of hh', '2026 separate', '2027 single', '2027 joint', '2027 head of hh', '2027 separate']
for j, h in enumerate(heads):
    B.th(ws, BR0 + 1, 4 + j, h.upper(), align='right')
B.th(ws, BR0 + 1, 12, 'YOURS', align='right')
BRK = {2026: {'S': [0, 12400, 50400, 105700, 201775, 256225, 640600], 'MFJ': [0, 24800, 100800, 211400, 403550, 512450, 768700],
              'HOH': [0, 17700, 67450, 105700, 201750, 256200, 640600], 'MFS': [0, 12400, 50400, 105700, 201775, 256225, 384350]},
       2027: {'S': [0, 12800, 52025, 109125, 208325, 264550, 661375], 'MFJ': [0, 25600, 104050, 218250, 416650, 529100, 793650],
              'HOH': [0, 18250, 69650, 109100, 208300, 264550, 661350], 'MFS': [0, 12800, 52025, 109125, 208325, 264550, 396825]}}
RATESB = [0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37]
for i, rt in enumerate(RATESB):
    r = BR0 + 2 + i
    B.fx(ws, r, 2, rt, '0%', True, None, 'left')
    B.fx(ws, r, 3, rt if i == 0 else f'=B{r}-B{r - 1}', '0%')
    for j, (y, st) in enumerate([(y, s) for y in (2026, 2027) for s in ('S', 'MFJ', 'HOH', 'MFS')]):
        B.inp(ws, r, 4 + j, BRK[y][st][i], '#,##0', 'right', keep=True)
    B.fx(ws, r, 12, f'=INDEX(D{r}:K{r},({YI}-1)*4+{SI})', '#,##0', True, TINT)
BRR = (BR0 + 2, BR0 + 8)
B.tip(ws, BR0 + 10, 2, 'Sources: IRS Rev. Proc. 2025-32 / IR-2025-103 (2026) and Rev. Proc. 2026-35 (2027), via irs.gov and Tax Foundation. Married filing separately '
      'uses the single brackets except the 37% rate, which starts at half the joint figure. The 2027 mileage rate is not out yet: update cell D18 and D19 when the IRS '
      'announces it (usually mid-December). Estimate, not tax advice.', 11, 1, 52)
B.protect(ws)

# ================================================================== example data
inc = []
clients = [('Northwind Health', 'UX audit and redesign', '1099-NEC'), ('Bluebird Apps', 'Mobile app wireframes', '1099-NEC'),
           ('Cedar and Pine Studio', 'Sub-contract design days', '1099-NEC'), ('Lumen AI (via Upwork)', 'Onboarding flow', '1099-K (card or app)'),
           ('Harbor Credit Union', 'Website usability test', '1099-NEC'), ('Maple Goods (via Stripe)', 'Checkout redesign', '1099-K (card or app)')]
amts = [4200, 2850, 1600, 3900, 2400, 1250, 5200, 1800, 3100, 2650, 4400, 950, 3600, 2200, 1500, 4800, 2750, 1350, 3300, 2900,
        1700, 4100, 2300, 1900, 3500, 2600]
dd = dt.date(2026, 1, 9)
for i, a in enumerate(amts):
    c = clients[(i * 5) % len(clients)]
    inc.append([dd, c[0], f'INV-{1040 + i} {c[1]}', a, c[2]])
    dd += dt.timedelta(days=12 if i % 3 else 13)
# rows pasted from an invoicing app export: text dates and "$" amounts, out of order (shows the paste area sorting itself)
pasted = [['2026-11-06', 'Bluebird Apps', 'INV-1066 Design system update', '$2,450.00', '1099-NEC'],
          ['2026-10-30', 'Northwind Health', 'INV-1067 Patient portal tests', '$3,150.00', '1099-NEC'],
          ['2025-12-29', 'Harbor Credit Union', 'INV-1039 (paid in 2025: other tax year)', '$1,800.00', '1099-NEC']]
inc_rows = inc[:20] + pasted + inc[20:]
inc_rows = [r for r in inc_rows if not (isinstance(r[0], dt.date) and r[0] > dt.date(2026, 11, 15))]
exp = []
for m in range(1, 12):
    exp.append([dt.date(2026, m, 3), 'Adobe', 'Creative Cloud', 59.99, C_('software'), None])
    exp.append([dt.date(2026, m, 5), 'Figma', 'Figma Professional', 16.00, C_('software'), None])
    exp.append([dt.date(2026, m, 1), 'Desk Hub Coworking', 'Coworking membership', 250.00, C_('other business property'), None])
    exp.append([dt.date(2026, m, 18), 'Verizon', 'Phone plan (70% business)', 85.00, C_('Utilities'), 0.7])
    exp.append([dt.date(2026, m, 21), 'Comcast', 'Home internet (50% business)', 70.00, C_('Utilities'), 0.5])
    exp.append([dt.date(2026, m, 26), 'Upwork', 'Platform service fee', 38.00 + (m % 4) * 6, C_('Commissions'), None])
exp += [[dt.date(2026, 1, 12), 'State of Illinois', 'Business license renewal', 50.00, C_('Taxes and licenses'), None],
        [dt.date(2026, 1, 20), 'Hiscox', 'Professional liability insurance', 480.00, C_('Business insurance'), None],
        [dt.date(2026, 2, 14), 'Apple', 'MacBook Pro for client work', 2199.00, C_('depreciation'), None],
        [dt.date(2026, 3, 2), 'Riverside CPA', '2025 tax prep fee', 450.00, C_('Legal and professional'), None],
        [dt.date(2026, 3, 19), 'LinkedIn', 'Sponsored post', 120.00, C_('Advertising'), None],
        [dt.date(2026, 4, 8), 'Office Depot', 'Printer ink and paper', 64.50, C_('Office expense'), None],
        [dt.date(2026, 4, 23), 'Sam Ortiz (developer)', 'Prototype build, contract', 1200.00, C_('Contract labor'), None],
        [dt.date(2026, 5, 11), 'Interaction Design Fdn', 'Annual membership', 199.00, C_('dues'), None],
        [dt.date(2026, 6, 4), 'United Airlines', 'Flight to client workshop, Denver', 412.00, C_('Travel'), None],
        [dt.date(2026, 6, 5), 'Hyatt Denver', 'Hotel, 2 nights', 389.00, C_('Travel'), None],
        [dt.date(2026, 6, 5), 'Denver Chophouse', 'Client dinner', 148.00, C_('Business meals'), None],
        [dt.date(2026, 7, 15), 'Udemy', 'Accessibility course', 89.00, C_('education'), None],
        [dt.date(2026, 8, 3), 'Amazon', 'Desk lamp and cables', 76.40, C_('Supplies'), None],
        [dt.date(2026, 8, 27), 'Blue Bottle Coffee', 'Client coffee meeting', 22.50, C_('Business meals'), None],
        [dt.date(2026, 9, 9), 'LinkedIn', 'Sponsored post', 120.00, C_('Advertising'), None],
        [dt.date(2026, 9, 24), 'SpotHero', 'Parking at client office', 28.00, C_('Parking'), None],
        [dt.date(2026, 10, 7), 'Config Conference', 'Conference ticket', 349.00, C_('education'), None],
        [dt.date(2026, 10, 15), 'Chase', 'Wire fee', 25.00, C_('bank fees'), None],
        [dt.date(2026, 10, 29), 'Apple', 'Laptop battery repair', 129.00, C_('Repairs'), None],
        [dt.date(2026, 11, 4), 'Office Depot', 'Notebooks and pens', 31.80, C_('Office expense'), None]]
exp = [e for e in exp if e[0] <= dt.date(2026, 11, 15)]   # nothing after the example's 'today' (mid-Nov)
exp.sort(key=lambda x: x[0])
trips = [('Home to Northwind Health, Evanston', 'Kick-off workshop', 32), ('Home to Bluebird Apps, Loop', 'Design review', 18),
         ('Home to Harbor Credit Union, Oak Park', 'Usability test day', 24), ('Home to Cedar and Pine Studio', 'Sprint planning', 14),
         ('Home to print shop, Wicker Park', 'Collect research boards', 9), ('Home to Northwind Health, Evanston', 'User interviews', 32),
         ('Home to O\'Hare airport', 'Drive to airport, Denver', 36), ('Home to Bluebird Apps, Loop', 'Handover meeting', 18)]
miles = []
dd = dt.date(2026, 1, 14)
for i in range(26):
    t = trips[i % len(trips)]
    miles.append([dd, t[0] + ' and back', t[1], t[2] * 2])
    dd += dt.timedelta(days=12 if i % 2 else 13)
miles = [m for m in miles if m[0] <= dt.date(2026, 11, 13)]

# ================================================================== Income Log
ws = S['Income Log']
IR1, IR2 = 9, 208
B.page(ws, 'Income log (1099 income)', 'Every payment from clients, platforms and apps. Type it, or PASTE a CSV of your invoices into the yellow columns: '
       'any order, any date style. The right side sorts itself.',
       {2: 15, 3: 24, 4: 31, 5: 13, 6: 19, 7: 25, 8: 11, 9: 2, 10: 15, 11: 24, 12: 12, 13: 2, 14: 24, 15: 12, 16: 29},
       ncols=16, nrows=IR2 + 10)
B.text(ws, 7, 2, f'="Counted for "&{YR}&": "&TEXT(E{IR2 + 2},"$#,##0.00")&"   ·   payments: "&E{IR2 + 3}&"   ·   rows that need a look: "&E{IR2 + 5}', 9, True, DSAGE, w=7)
for j, (h, a) in enumerate([('DATE PAID', 'left'), ('CLIENT OR PLATFORM', 'left'), ('INVOICE # / WHAT FOR', 'left'), ('AMOUNT ($)', 'right'),
                            ('FORM YOU\'LL GET', 'left'), ('CHECK', 'left'), ('SET ASIDE', 'right')]):
    B.th(ws, 8, 2 + j, h, align=a)
B.th(ws, 8, 10, 'SORTED: NEWEST FIRST'); B.th(ws, 8, 11, 'CLIENT'); B.th(ws, 8, 12, 'AMOUNT', align='right')
B.th(ws, 8, 14, 'BY CLIENT (THIS TAX YEAR)'); B.th(ws, 8, 15, 'TOTAL', align='right'); B.th(ws, 8, 16, '1099-NEC EXPECTED?')
FORMS = ['1099-NEC', '1099-K (card or app)', '1099-MISC', 'No form (cash, direct)']
NSORT, NCLI = IR2 - IR1 + 1, 30
for i in range(IR2 - IR1 + 1):
    r = IR1 + i
    x = inc_rows[i] if i < len(inc_rows) else None
    B.inp(ws, r, 2, x[0] if x else None, DATE); B.inp(ws, r, 3, x[1] if x else None); B.inp(ws, r, 4, x[2] if x else None)
    B.inp(ws, r, 5, x[3] if x else None, '#,##0.00', 'right'); B.inp(ws, r, 6, x[4] if x else None)
    # helpers U: date value, V: amount value, W: counted amount, X: sort key, Y: first time this client appears this year
    ws.cell(r, 21, f'=IF(B{r}="","",IF(ISNUMBER(B{r}),B{r},IFERROR(DATEVALUE(TRIM(B{r})),"")))')
    ws.cell(r, 22, f'=IF(E{r}="","",IF(ISNUMBER(E{r}),E{r},IFERROR(VALUE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(TRIM(E{r}),"$",""),",","")," ","")),"")))')
    ws.cell(r, 23, f'=IF(LEFT(G{r},1)="✓",V{r},0)')
    ws.cell(r, 24, f'=IF(W{r}>0,U{r}+ROW()/100000,"")')
    ws.cell(r, 25, f'=IF(AND(W{r}>0,C{r}<>""),IF(COUNTIFS(C${IR1}:C{r},C{r},W${IR1}:W{r},">0")=1,ROW(),""),"")')
    B.fx(ws, r, 7, f'=IF(AND(B{r}="",E{r}=""),"",IF(U{r}="","✕ Date not recognised",IF(V{r}="","✕ Amount not recognised",'
                   f'IF(YEAR(U{r})<>{YR},"– Other year: not counted",IF(V{r}<=0,"✕ Amount must be over 0","✓ Counted")))))', None, False, None, 'left', size=9)
    B.fx(ws, r, 8, f'=IF(W{r}>0,W{r}*{SR["setaside"]},"")', '#,##0')
    # sorted view
    k = i + 1
    look = f'MATCH(LARGE($X${IR1}:$X${IR2},{k}),$X${IR1}:$X${IR2},0)'
    B.fx(ws, r, 10, f'=IF({k}>COUNT($X${IR1}:$X${IR2}),"",INDEX($U${IR1}:$U${IR2},{look}))', DATE, False, None, 'left')
    B.fx(ws, r, 11, f'=IF({k}>COUNT($X${IR1}:$X${IR2}),"",INDEX($C${IR1}:$C${IR2},{look}))', None, False, None, 'left')
    B.fx(ws, r, 12, f'=IF({k}>COUNT($X${IR1}:$X${IR2}),"",INDEX($V${IR1}:$V${IR2},{look}))', '#,##0.00')
    if k <= NCLI:
        B.fx(ws, r, 14, f'=IF({k}>COUNT($Y${IR1}:$Y${IR2}),"",INDEX($C:$C,SMALL($Y${IR1}:$Y${IR2},{k})))', None, False, None, 'left')
        B.fx(ws, r, 15, f'=IF(N{r}="","",SUMIFS($W${IR1}:$W${IR2},$C${IR1}:$C${IR2},N{r}))', '#,##0')
        B.fx(ws, r, 16, f'=IF(N{r}="","",IF(O{r}>={RT["nec"]},IF(COUNTIFS($C${IR1}:$C${IR2},N{r},$F${IR1}:$F${IR2},"1099-K*")>0,"Check: 1099-K if paid by card/app","Yes, by Jan 31"),"Not required (still taxable)"))',
             None, False, None, 'left', size=9)
for col in 'UVWXY':
    ws.column_dimensions[col].hidden = True
    for r in range(IR1, IR2 + 1): ws[f'{col}{r}'].font = F(8, color='C9C2B6')
B.dv(ws, f'F{IR1}:F{IR2}', FORMS)
check_fmt(ws, f'G{IR1}:G{IR2}', f'G{IR1}')
ws.conditional_formatting.add(f'P{IR1}:P{IR1 + NCLI - 1}', FormulaRule(formula=[f'LEFT(P{IR1},3)="Yes"'], font=Font(name=FONT, color=DSAGE, bold=True)))
T1 = IR2 + 2
B.fx(ws, T1, 2, '="Gross receipts counted for "&' + YR + '&" (Schedule C line 1)"', None, True, TINT, 'left', 3)
B.fx(ws, T1, 5, f'=SUM(W{IR1}:W{IR2})', USD2, True, TINT)
B.fx(ws, T1 + 1, 2, 'Payments counted', None, True, WHITE, 'left', 3); B.fx(ws, T1 + 1, 5, f'=COUNTIF(W{IR1}:W{IR2},">0")', '0', True, WHITE)
B.fx(ws, T1 + 2, 2, 'Other tax year (shown, not counted)', None, True, WHITE, 'left', 3); B.fx(ws, T1 + 2, 5, f'=COUNTIF(G{IR1}:G{IR2},"–*")', '0', True, WHITE)
B.fx(ws, T1 + 3, 2, 'Rows that need a look (✕)', None, True, WHITE, 'left', 3); B.fx(ws, T1 + 3, 5, f'=COUNTIF(G{IR1}:G{IR2},"✕*")', '0', True, WHITE)
B.tip(ws, T1 + 5, 2, 'PASTING A CSV: open your invoices export, copy the Date, Client, Description and Amount columns, click the first empty yellow cell in column B and '
      'paste as values (Excel: Ctrl+Shift+V or Paste Special > Values; Google Sheets: Ctrl+Shift+V). Dates like 2026-03-14 or 3/14/2026 and amounts like "$1,250.00" '
      'are read for you. Rows can be in any order: the sorted list and client totals on the right update by themselves.', 7, 1, 70)
B.tip(ws, T1 + 7, 2, 'All business income is taxable, with or without a 1099. Use the date the money reached you (cash method). A 1099-K from Stripe, PayPal or '
      'Upwork can include the same payments as a 1099-NEC: count each payment once. Estimate, not tax advice.', 7, 1, 44)
INC_T, INC_N, INC_X = f'{IL}!$E${T1}', f'{IL}!$E${T1 + 1}', f'{IL}!$E${T1 + 3}'
B.protect(ws)

# ================================================================== Deductions
ws = S['Deductions']
ER1, ER2 = 9, 308
B.page(ws, 'Deductions log', 'Every business cost. Pick the Schedule C category and the line number is filled in. Business % for things you also use '
       'personally. Meals count at 50% automatically.',
       {2: 14, 3: 22, 4: 30, 5: 12, 6: 46, 7: 10, 8: 12, 9: 12, 10: 10, 11: 22}, ncols=11, nrows=ER2 + 10)
B.text(ws, 7, 2, f'="Deductible for "&{YR}&": "&TEXT(I{ER2 + 2},"$#,##0.00")&"   ·   rows that need a look: "&I{ER2 + 3}', 9, True, DSAGE, w=8)
for j, (h, a) in enumerate([('DATE PAID', 'left'), ('PAID TO', 'left'), ('WHAT FOR', 'left'), ('AMOUNT ($)', 'right'),
                            ('SCHEDULE C CATEGORY', 'left'), ('BUSINESS %', 'right'), ('BUSINESS SHARE', 'right'), ('DEDUCTIBLE', 'right'),
                            ('LINE', 'left'), ('CHECK', 'left')]):
    B.th(ws, 8, 2 + j, h, align=a)
for i in range(ER2 - ER1 + 1):
    r = ER1 + i
    x = exp[i] if i < len(exp) else None
    B.inp(ws, r, 2, x[0] if x else None, DATE); B.inp(ws, r, 3, x[1] if x else None); B.inp(ws, r, 4, x[2] if x else None)
    B.inp(ws, r, 5, x[3] if x else None, '#,##0.00', 'right'); B.inp(ws, r, 6, x[4] if x else None)
    B.inp(ws, r, 7, x[5] if x else None, '0%', 'right')
    ws.cell(r, 14, f'=IF(B{r}="","",IF(ISNUMBER(B{r}),B{r},IFERROR(DATEVALUE(TRIM(B{r})),"")))')
    ws.cell(r, 15, f'=IF(E{r}="","",IF(ISNUMBER(E{r}),ABS(E{r}),IFERROR(ABS(VALUE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(TRIM(E{r}),"$",""),",","")," ",""))),"")))')
    B.fx(ws, r, 8, f'=IF(O{r}="","",O{r}*IF(G{r}="",1,MIN(1,MAX(0,G{r}))))', '#,##0.00')
    B.fx(ws, r, 9, f'=IF(LEFT(K{r},1)="✓",H{r}*IF(J{r}="Line 24b",{RT["meals"]},1),"")', '#,##0.00', True)
    B.fx(ws, r, 10, f'=IF(F{r}="","",IFERROR(INDEX({LINES_RNG},MATCH(F{r},{CATS_RNG},0)),"?"))', None, False, None, 'left', color=GOLD)
    B.fx(ws, r, 11, f'=IF(AND(B{r}="",E{r}=""),"",IF(N{r}="","✕ Date not recognised",IF(O{r}="","✕ Amount not recognised",'
                    f'IF(YEAR(N{r})<>{YR},"– Other year: not counted",IF(F{r}="","✕ Pick a category",IF(J{r}="?","✕ Pick from the list",IF(N(G{r})>1,"✕ % over 100","✓ Counted")))))))',
         None, False, None, 'left', size=9)
for col in 'NO':
    ws.column_dimensions[col].hidden = True
    for r in range(ER1, ER2 + 1): ws[f'{col}{r}'].font = F(8, color='C9C2B6')
B.dv(ws, f'F{ER1}:F{ER2}', ref=CATREF)
check_fmt(ws, f'K{ER1}:K{ER2}', f'K{ER1}')
T2 = ER2 + 2
B.fx(ws, T2, 2, '="Deductible business costs counted for "&' + YR + '&" (before mileage and home office)"', None, True, TINT, 'left', 7)
B.fx(ws, T2, 9, f'=SUM(I{ER1}:I{ER2})', USD2, True, TINT)
B.fx(ws, T2 + 1, 2, 'Rows that need a look (✕)', None, True, WHITE, 'left', 7); B.fx(ws, T2 + 1, 9, f'=COUNTIF(K{ER1}:K{ER2},"✕*")', '0', True, WHITE)
B.tip(ws, T2 + 3, 2, 'Business % = the work share of something you also use personally (for example 70% of a phone plan). Blank means 100%. Using the standard mileage rate? '
      'Then log only parking and tolls here, not gas, insurance or car repairs. Equipment over $2,500 may need to be spread over years: ask your tax pro. '
      'Bank CSVs paste in too (columns B to E, values only). Estimate, not tax advice.', 10, 1, 58)
EXP_T, EXP_X = f'{DL_}!$I${T2}', f'{DL_}!$I${T2 + 1}'
B.protect(ws)

# ================================================================== Mileage
ws = S['Mileage']
MR1, MR2 = 9, 158
B.page(ws, 'Mileage log', 'Business trips in your own car at the IRS standard mileage rate. The rate is picked by date (it changed on Jul 1, 2026).',
       {2: 14, 3: 36, 4: 28, 5: 11, 6: 11, 7: 13, 8: 22, 9: 3, 10: 44, 11: 16}, ncols=11, nrows=MR2 + 8)
B.text(ws, 7, 2, f'="Mileage deduction for "&{YR}&": "&TEXT(G{MR2 + 2},"$#,##0.00")&"   ·   business miles: "&TEXT(E{MR2 + 2},"#,##0")&"   ·   rows that need a look: "&G{MR2 + 3}',
       9, True, DSAGE, w=7)
for j, (h, a) in enumerate([('DATE', 'left'), ('FROM AND TO', 'left'), ('BUSINESS PURPOSE', 'left'), ('MILES', 'right'), ('RATE', 'right'),
                            ('DEDUCTION', 'right'), ('CHECK', 'left')]):
    B.th(ws, 8, 2 + j, h, align=a)
for i in range(MR2 - MR1 + 1):
    r = MR1 + i
    x = miles[i] if i < len(miles) else None
    B.inp(ws, r, 2, x[0] if x else None, DATE); B.inp(ws, r, 3, x[1] if x else None); B.inp(ws, r, 4, x[2] if x else None)
    B.inp(ws, r, 5, x[3] if x else None, '#,##0.0', 'right')
    B.fx(ws, r, 6, f'=IF(NOT(ISNUMBER(B{r})),"",IF(MONTH(B{r})<7,{RT["mile1"]},{RT["mile2"]}))', '$0.000')
    B.fx(ws, r, 7, f'=IF(LEFT(H{r},1)="✓",E{r}*F{r},"")', '#,##0.00', True)
    B.fx(ws, r, 8, f'=IF(AND(B{r}="",E{r}=""),"",IF(NOT(ISNUMBER(B{r})),"✕ Type a date",IF(YEAR(B{r})<>{YR},"– Other year: not counted",'
                   f'IF(N(E{r})<=0,"✕ Type the miles",IF(D{r}="","✕ Add the purpose","✓ Counted")))))', None, False, None, 'left', size=9)
check_fmt(ws, f'H{MR1}:H{MR2}', f'H{MR1}')
T3 = MR2 + 2
B.fx(ws, T3, 2, 'Business miles and mileage deduction (Schedule C line 9)', None, True, TINT, 'left', 3)
B.fx(ws, T3, 5, f'=SUMIFS(E{MR1}:E{MR2},H{MR1}:H{MR2},"✓*")', '#,##0', True, TINT); B.fx(ws, T3, 6, '', None, False, TINT)
B.fx(ws, T3, 7, f'=SUM(G{MR1}:G{MR2})', USD2, True, TINT)
B.fx(ws, T3 + 1, 2, 'Rows that need a look (✕)', None, True, WHITE, 'left', 5); B.fx(ws, T3 + 1, 7, f'=COUNTIF(H{MR1}:H{MR2},"✕*")', '0', True, WHITE)
# rate box + Part IV
B.th(ws, 8, 10, 'IRS STANDARD MILEAGE RATE'); B.th(ws, 8, 11, 'PER MILE', align='right')
B.fx(ws, 9, 10, '="Jan 1 to Jun 30, "&' + YR, None, False, WHITE, 'left'); B.fx(ws, 9, 11, f'={RT["mile1"]}', '$0.000', True, WHITE)
B.fx(ws, 10, 10, '="Jul 1 to Dec 31, "&' + YR, None, False, WHITE, 'left'); B.fx(ws, 10, 11, f'={RT["mile2"]}', '$0.000', True, WHITE)
B.text(ws, 11, 10, 'Change the rates on the Tax Rates tab (yellow cells). 2026: 72.5 cents, then 76 cents from Jul 1 (IRS Notice 2026-10, Announcement 2026-11).',
       8, False, MUTED, w=2, h=2)
B.th(ws, 14, 10, 'SCHEDULE C PART IV: YOUR VEHICLE'); B.th(ws, 14, 11, 'ANSWER', align='right')
P4 = [('Line 43: date the car was first used for business', dt.date(2023, 5, 1), DATE), ('Line 44a: business miles (from the log)', f'=E{T3}', '#,##0'),
      ('Line 44b: commuting miles', 0, '#,##0'), ('Line 44c: other (personal) miles', 7400, '#,##0'),
      ('Line 45: car available for personal use off duty?', 'Yes', None), ('Line 46: another vehicle for personal use?', 'No', None),
      ('Line 47a: evidence for the deduction?', 'Yes', None), ('Line 47b: is the evidence written?', 'Yes', None)]
for i, (lab, v, fmt) in enumerate(P4):
    r = 15 + i
    B.fx(ws, r, 10, lab, None, False, WHITE, 'left', size=9)
    if isinstance(v, str) and v.startswith('='):
        B.fx(ws, r, 11, v, fmt, True, WHITE)
    else:
        B.inp(ws, r, 11, v, fmt, 'right')
B.dv(ws, 'K19:K22', ['Yes', 'No'])
B.tip(ws, 24, 10, 'Business trips only: clients, suppliers, the bank, a second work site. Home to a regular office is commuting and does not count. '
      'Write the purpose every time: it is what makes the log hold up.', 2, 6, None)
MIL_T, MIL_M, MIL_X = f'{ML}!$G${T3}', f'{ML}!$E${T3}', f'{ML}!$G${T3 + 1}'
B.protect(ws)

# ================================================================== Schedule C
ws = S['Schedule C']
B.page(ws, 'Schedule C summary', '="Your "&' + YR + '&" totals on the Schedule C (Form 1040) line numbers. Copy each figure across, or hand this page to your tax pro."',
       {2: 9, 3: 62, 4: 17, 5: 3, 6: 46}, ncols=5, nrows=70)
ws['B3'].font = F(10, color=MUTED)
B.th(ws, 7, 2, 'LINE'); B.th(ws, 7, 3, 'SCHEDULE C WORDING (2025 FORM, CURRENT)'); B.th(ws, 7, 4, 'YOUR FIGURE', align='right'); B.th(ws, 7, 6, 'WHERE IT COMES FROM')
sumline = lambda ln: f'=SUMIFS({DL_}!$I${ER1}:$I${ER2},{DL_}!$J${ER1}:$J${ER2},"Line {ln}")'
SCH = [('P', 'Part I · Income'),
       ('1', 'Gross receipts or sales', f'={INC_T}', 'Income Log'),
       ('2', 'Returns and allowances', 'INPUT', 'Refunds you gave clients (type it)'),
       ('3', 'Subtract line 2 from line 1', '=D9-D10', ''),
       ('4', 'Cost of goods sold (from line 42)', sumline('4'), 'Deductions: "Line 4" (simple version of Part III)'),
       ('5', 'Gross profit. Subtract line 4 from line 3', '=D11-D12', ''),
       ('6', 'Other income, including federal and state gasoline or fuel tax credit or refund', 'INPUT', 'Rare (type it)'),
       ('7', 'Gross income. Add lines 5 and 6', '=D13+D14', ''),
       ('P', 'Part II · Expenses'),
       ('8', 'Advertising', sumline('8'), 'Deductions'),
       ('9', 'Car and truck expenses', f'=SUMIFS({DL_}!$I${ER1}:$I${ER2},{DL_}!$J${ER1}:$J${ER2},"Line 9")+{MIL_T}', 'Mileage log + parking and tolls'),
       ('10', 'Commissions and fees', sumline('10'), 'Deductions (platform fees)'),
       ('11', 'Contract labor', sumline('11'), 'Deductions'),
       ('12', 'Depletion', 0, 'Not used by most freelancers'),
       ('13', 'Depreciation and section 179 expense deduction', sumline('13'), 'Deductions: equipment (check with your tax pro)'),
       ('14', 'Employee benefit programs (other than on line 19)', sumline('14'), 'Deductions'),
       ('15', 'Insurance (other than health)', sumline('15'), 'Deductions'),
       ('16a', 'Interest: Mortgage (paid to banks, etc.)', sumline('16a'), 'Deductions'),
       ('16b', 'Interest: Other', sumline('16b'), 'Deductions'),
       ('17', 'Legal and professional services', sumline('17'), 'Deductions'),
       ('18', 'Office expense', sumline('18'), 'Deductions'),
       ('19', 'Pension and profit-sharing plans', sumline('19'), 'Employees only. Your own SEP is on Settings'),
       ('20a', 'Rent or lease: Vehicles, machinery, and equipment', sumline('20a'), 'Deductions'),
       ('20b', 'Rent or lease: Other business property', sumline('20b'), 'Deductions (coworking, studio)'),
       ('21', 'Repairs and maintenance', sumline('21'), 'Deductions'),
       ('22', 'Supplies (not included in Part III)', sumline('22'), 'Deductions'),
       ('23', 'Taxes and licenses', sumline('23'), 'Deductions'),
       ('24a', 'Travel', sumline('24a'), 'Deductions'),
       ('24b', 'Deductible meals', sumline('24b'), 'Deductions (already at 50%)'),
       ('25', 'Utilities', sumline('25'), 'Deductions (business % of phone, internet)'),
       ('26', 'Wages (less employment credits)', sumline('26'), 'Deductions'),
       ('27a', 'Energy efficient commercial bldgs deduction (Form 7205)', 0, 'Not used by most freelancers'),
       ('27b', 'Other expenses (from line 48)', sumline('27b'), 'Deductions: software, training, bank fees, dues, other'),
       ('28', 'Total expenses before expenses for business use of home. Add lines 8 through 27b', None, 'Sum of lines 8 to 27b'),
       ('29', 'Tentative profit or (loss). Subtract line 28 from line 7', None, ''),
       ('30', 'Expenses for business use of your home (simplified method or Form 8829)', None, 'Settings: home office'),
       ('31', 'Net profit or (loss). Subtract line 30 from line 29', None, 'Goes to Schedule 1 line 3 and Schedule SE')]
SROW = {}
r = 8
for row in SCH:
    if row[0] == 'P':
        B.section(ws, r, 2, row[1], 3); r += 1; continue
    SROW[row[0]] = r; r += 1
ELINES = ['8', '9', '10', '11', '12', '13', '14', '15', '16a', '16b', '17', '18', '19', '20a', '20b', '21', '22', '23', '24a', '24b', '25', '26', '27a', '27b']
for row in SCH:
    if row[0] == 'P': continue
    ln, word, f, note = row; rr = SROW[ln]
    if ln == '3': f = f'=D{SROW["1"]}-D{SROW["2"]}'
    if ln == '5': f = f'=D{SROW["3"]}-D{SROW["4"]}'
    if ln == '7': f = f'=D{SROW["5"]}+D{SROW["6"]}'
    if ln == '28': f = f'=SUM(D{SROW["8"]}:D{SROW["27b"]})'
    if ln == '29': f = f'=D{SROW["7"]}-D{SROW["28"]}'
    if ln == '30': f = (f'=IF(N({SR["ho_act"]})>0,N({SR["ho_act"]}),MIN(MAX(0,D{SROW["29"]}),MIN(N({SR["sqft"]}),{RT["homax"]})*{RT["hosq"]}))')
    if ln == '31': f = f'=D{SROW["29"]}-D{SROW["30"]}'
    B.fx(ws, rr, 2, ln, None, True, None, 'left', color=GOLD)
    c = B.fx(ws, rr, 3, word, None, ln in ('7', '28', '29', '31'), None, 'left', size=9.5); c.alignment = Alignment(wrap_text=True, vertical='center', indent=1)
    if f == 'INPUT':
        B.inp(ws, rr, 4, 0, USD2, 'right')
    else:
        B.fx(ws, rr, 4, f, USD2, ln in ('7', '28', '29', '31'), TINT if ln == '31' else None)
    B.fx(ws, rr, 6, note, None, False, None, 'left', color=MUTED, size=8.5)
    ws.row_dimensions[rr].height = 30 if len(word) > 70 else 20
endr = max(SROW.values()) + 2
B.tip(ws, endr, 2, 'Line numbers and wording are from the 2025 Schedule C (Form 1040) and its instructions, the current form on 19 Nov 2026. The IRS can renumber lines: '
      'check the year\'s form when you file. Not covered: inventory detail (Part III), depreciation schedules (Form 4562), the home office income limit beyond line 29, '
      'at-risk rules. Estimate, not tax advice.', 5, 1, 58)
NET = f'{SC}!$D${SROW["31"]}'
GROSS, EXPTOT, HOME = f'{SC}!$D${SROW["7"]}', f'{SC}!$D${SROW["28"]}', f'{SC}!$D${SROW["30"]}'
B.protect(ws)

# ================================================================== Tax Estimate
ws = S['Tax Estimate']
B.page(ws, 'Tax estimate', '="Self-employment tax, federal income tax and a rough state figure for "&' + YR + '&". Estimate, not tax advice."',
       {2: 52, 3: 16, 4: 3, 5: 60}, ncols=5, nrows=70)
ws['B3'].font = F(10, color=MUTED)


def line(r, lab, f, fmt=USD2, note='', bold=False, bg=None):
    B.fx(ws, r, 2, lab, None, bold, bg, 'left')
    B.fx(ws, r, 3, f, fmt, bold, bg)
    B.fx(ws, r, 5, note, None, False, bg, 'left', color=MUTED, size=8.5)
    ws.cell(r, 5).alignment = Alignment(wrap_text=True, vertical='center', indent=1)
    ws.row_dimensions[r].height = 30 if len(note) > 70 else 20


B.section(ws, 7, 2, '1 · Your business profit', 2)
line(8, 'Net profit so far (Schedule C line 31)', f'={NET}', note='From the Schedule C tab.')
line(9, 'Plus: profit you still expect this year (Settings)', f'=N({SR["extra"]})', note='Optional. Leave 0 to estimate on what you logged so far.')
line(10, 'Profit used for this estimate', '=C8+C9', bold=True, bg=TINT)
B.section(ws, 12, 2, '2 · Self-employment tax (Schedule SE)', 2)
line(13, 'Net earnings from self-employment (profit x 92.35%)', f'=IF(C10*{RT["nef"]}<{RT["semin"]},0,ROUND(C10*{RT["nef"]},2))',
     note='Under $400 of net earnings: no SE tax.')
line(14, 'Social Security part (12.4% up to the wage base)', f'=ROUND({RT["ssr"]}*MIN(C13,MAX(0,{RT["wb"]}-N({SR["w2"]}))),2)',
     note='="Wage base "&TEXT(' + RT["wb"] + ',"$#,##0")&" for "&' + YR + '&", less any W-2 wages."')
line(15, 'Medicare part (2.9%, no cap)', f'=ROUND({RT["mcr"]}*C13,2)', note='The extra 0.9% Medicare tax on high incomes is not included.')
line(16, 'Self-employment tax', '=C14+C15', bold=True, bg=TINT)
line(17, 'Half of SE tax (an above-the-line deduction)', '=ROUND(C16/2,2)', note='Schedule 1 line 15. Lowers your income tax, not your SE tax.')
B.section(ws, 19, 2, '3 · Federal income tax', 2)
line(20, 'Business profit', '=C10')
line(21, 'Plus: W-2 wages and other income (Settings)', f'=N({SR["w2"]})+N({SR["oth"]})')
line(22, 'Less: half of SE tax', '=-C17')
line(23, 'Less: self-employed health insurance', f'=-MIN(N({SR["health"]}),MAX(0,C10-C17))', note='Capped at your business profit after half SE tax.')
line(24, 'Less: SEP-IRA / solo 401(k) contributions', f'=-N({SR["retire"]})')
line(25, 'Adjusted gross income (estimate)', '=MAX(0,SUM(C20:C24))', bold=True)
line(26, 'Less: standard deduction', f'=-{SD}', note=f'="{" "}"&{SR["fs"]}&", "&' + YR + '&". From the Tax Rates tab."')
line(27, 'Less: qualified business income (QBI) deduction', f'=IF({SR["qbi"]}="Yes",-ROUND(MIN({RT["qbi"]}*MAX(0,C10-C17-N({SR["health"]})-N({SR["retire"]})),{RT["qbi"]}*MAX(0,C25+C26)),2),0)',
     note='20% of business income after the adjustments, capped at 20% of taxable income. Limits can apply above about $200,000 single / $400,000 joint.')
line(28, 'Taxable income', '=MAX(0,C25+C26+C27)', bold=True, bg=TINT)
line(29, 'Federal income tax (2026 or 2027 brackets)', f"=ROUND(SUMPRODUCT((C28>{TR}!$L${BRR[0]}:$L${BRR[1]})*(C28-{TR}!$L${BRR[0]}:$L${BRR[1]})*{TR}!$C${BRR[0]}:$C${BRR[1]}),2)",
     note='Brackets for your year and filing status, from the Tax Rates tab. Credits (child tax credit etc.) are not included.')
line(30, 'Your top bracket', f"=INDEX({TR}!$B${BRR[0]}:$B${BRR[1]},MAX(1,COUNTIF({TR}!$L${BRR[0]}:$L${BRR[1]},\"<\"&C28)))", '0%')
B.section(ws, 32, 2, '4 · What you owe for the year', 2)
line(33, 'Federal income tax', '=C29')
line(34, 'Self-employment tax', '=C16')
line(35, 'Total federal tax', '=C33+C34', bold=True)
line(36, 'Less: tax withheld from a job (Settings)', f'=-N({SR["wh"]})')
line(37, 'Federal tax left to pay through estimated payments', '=MAX(0,C35+C36)', bold=True, bg=GOLDT)
line(38, 'State income tax (rough: AGI x your state %)', f'=ROUND(MAX(0,C25)*N({SR["state"]}),2)', note='Ballpark only. Your state has its own rules and due dates.')
line(39, 'Total tax for the year, federal + state (estimate)', '=C35+C38', bold=True, bg=GOLDT)
line(40, 'Share of your business profit', '=IF(C10<=0,0,C39/C10)', '0.0%', note='Rule of thumb for the set-aside %. Compare it with your Settings set-aside %.', bold=True)
line(41, 'Suggested set-aside % of every payment', '=IF(C10<=0,0,CEILING(C39/C10,0.01))', '0%', note='Rounded up. Move this share of each payment into a separate tax savings account.')
B.tip(ws, 43, 2, 'Estimate, not tax advice. Not included: credits, itemized deductions, the extra 0.9% Medicare tax, net investment income tax, AMT, '
      'QBI limits at high incomes, depreciation rules, state-specific rules. A tax pro or the IRS calculation is final.', 4, 1, 46)
TE_FIT, TE_SE, TE_FED, TE_LEFT, TE_STATE, TE_ALL, TE_RATE, TE_SUG, TE_PROFIT, TE_HALF, TE_AGI, TE_TI = [f'{TE}!$C${r}' for r in (29, 16, 35, 37, 38, 39, 40, 41, 10, 17, 25, 28)]
B.protect(ws)

# ================================================================== Quarterly Tax
ws = S['Quarterly Tax']
B.page(ws, 'Quarterly estimated tax', '="Form 1040-ES payments for "&' + YR + '&": four due dates, a safe-harbor target and a tax savings pot."',
       {c: 9.2 for c in range(2, 18)}, ncols=17, nrows=80)
ws['B3'].font = F(10, color=MUTED)
# --- plan (rows 13-27), computed first so cards can refer to it
B.section(ws, 13, 2, 'Your target for the year', 8)
PL = [(14, 'This year\'s estimated federal tax (income tax + SE tax)', f'={TE_FED}', USD, ''),
      (15, '90% of this year\'s estimate', f'=ROUND({RT["sh90"]}*K14,0)', USD, ''),
      (16, 'Last year\'s total tax (Settings)', f'=IF({SR["prior"]}="","not entered",N({SR["prior"]}))', USD, ''),
      (17, 'Safe harbor: 100% of last year (110% if last year\'s AGI was over $150,000)',
       f'=IF(ISNUMBER(K16),ROUND(K16*IF({SR["agi150"]}="Yes",{RT["sh110"]},{RT["sh100"]}),0),"")', USD, ''),
      (18, 'Required for the year: the smaller of the two', '=IF(ISNUMBER(K17),MIN(K15,K17),K15)', USD, ''),
      (19, 'Less: tax withheld from a job', f'=-N({SR["wh"]})', USD, ''),
      (20, 'Estimated payments needed (federal)', f'=IF(K14+K19<{RT["min1k"]},0,MAX(0,K18+K19))', USD, ''),
      (21, 'Your plan (pick)', 'Safe harbor: smallest required', None, ''),
      (22, 'Target for the year', f'=IF(LEFT(K21,4)="Safe",K20,MAX(0,K14+K19))', USD, ''),
      (23, 'Each quarter (target ÷ 4)', '=ROUND(K22/4,0)', USD, ''),
      (24, 'Paid so far', '=SUM(L38:M41)', USD, ''),
      (25, 'Still to pay this year', '=MAX(0,K22-K24)', USD, '')]
for r, lab, f, fmt, _ in PL:
    B.fx(ws, r, 2, lab, None, r in (18, 20, 22), TINT if r == 22 else None, 'left', 9)
    if r == 21:
        B.inp(ws, r, 11, f, None, 'left', w=3, keep=True)
    else:
        B.fx(ws, r, 11, f, fmt, r in (18, 20, 22, 25), TINT if r == 22 else None, 'right', 3)
    ws.row_dimensions[r].height = 20
B.dv(ws, 'K21', ['Safe harbor: smallest required', 'Pay this year\'s full estimate'])
B.fx(ws, 26, 2, f'=IF(K14+K19<{RT["min1k"]},"You expect to owe under $1,000 after withholding: no estimated payments are required.",IF(LEFT(K21,4)="Safe","Safe harbor: pay this on time and there is no underpayment penalty, even if you owe more in April.","Paying the full estimate: less to pay in April, more now."))',
     None, False, GOLDT, 'left', 15, '6B5B45', 9)
ws.row_dimensions[26].height = 26
# side notes
B.box(ws, 14, 15, 25, 17, TINT, TINT)
B.text(ws, 14, 15, 'HOW SAFE HARBOR WORKS', 8, True, DSAGE, w=3, indent=1)
B.text(ws, 15, 15, 'Pay at least the smaller of 90% of this year\'s tax or 100% of last year\'s (110% if your AGI was over $150,000), spread evenly over the 4 dates. '
       'Then the IRS charges no underpayment penalty, even if you owe more when you file. Any balance is due by the April filing date.', 9, False, INK, w=3, h=11, valign='top', indent=1)
# --- payments table
B.section(ws, 28, 2, 'Your four payments', 8)
B.th(ws, 29, 2, 'QUARTER'); B.th(ws, 29, 3, 'INCOME PERIOD', 2); B.th(ws, 29, 5, 'DUE DATE', 2)
B.th(ws, 29, 7, 'PLANNED', 2, 'right'); B.th(ws, 29, 9, 'DATE PAID', 2); B.th(ws, 29, 11, 'AMOUNT PAID', 2, 'right')
B.th(ws, 29, 13, 'CONFIRMATION #', 2); B.th(ws, 29, 15, 'STATUS', 3)
# keep rows 30-33 empty spacing? use 30..33 for quarters -> but PL refers L38:M41. place quarters at 38..41 instead
for r in range(30, 38):
    ws.row_dimensions[r].hidden = True
PERIODS = [('Q1', 'Jan 1 – Mar 31'), ('Q2', 'Apr 1 – May 31'), ('Q3', 'Jun 1 – Aug 31'), ('Q4', 'Sep 1 – Dec 31')]
PAID = [(dt.date(2026, 4, 14), 3100, 'EFTPS 4417'), (dt.date(2026, 6, 12), 3000, 'Direct Pay 7720'), (dt.date(2026, 9, 14), 3100, 'Direct Pay 9031'), (None, None, None)]
for q in range(4):
    r = 38 + q
    B.fx(ws, r, 2, PERIODS[q][0], None, True, None, 'left')
    B.fx(ws, r, 3, PERIODS[q][1], None, False, None, 'left', 2)
    B.fx(ws, r, 5, f'={TR}!$E${QROWS[q]}', DATE, True, None, 'left', 2)
    prev = f'-SUM($K$38:K{r - 1})' if q else ''
    B.fx(ws, r, 7, f'=MAX(0,ROUND($K$22*{q + 1}/4{prev},0))', USD, True, None, 'right', 2)
    B.inp(ws, r, 9, PAID[q][0], DATE, w=2); B.inp(ws, r, 11, PAID[q][1], '#,##0', 'right', w=2); B.inp(ws, r, 13, PAID[q][2], w=2)
    B.fx(ws, r, 15, f'=IF(N(K{r})>0,"✓ Paid "&TEXT(K{r},"$#,##0"),IF(G{r}=0,"✓ Nothing due",IF(E{r}<TODAY(),"✕ Overdue: pay now",E{r}-TODAY()&" days left")))', None, True, None, 'left', 3)
    ws.row_dimensions[r].height = 24
check_fmt(ws, 'O38:O41', 'O38')
B.fx(ws, 42, 2, 'Year: target and paid', None, True, TINT, 'left', 5); B.fx(ws, 42, 7, '=$K$22', USD, True, TINT, 'right', 2)
B.fx(ws, 42, 9, '', None, False, TINT, 'left', 2); B.fx(ws, 42, 11, '=SUM(K38:L41)', USD, True, TINT, 'right', 2)
B.fx(ws, 42, 13, '', None, False, TINT, 'left', 5)
B.text(ws, 43, 2, '"Planned" catches you up: if you paid less earlier, the next quarter shows what keeps you on track. Pay at irs.gov/payments (Direct Pay or EFTPS). '
       'State estimated payments have their own dates.', 8.5, False, MUTED, w=16, h=2)
# fix: plan "paid so far" refers to amounts paid
ws['K24'] = '=SUM(K38:L41)'
# --- cards (rows 7-11)
for r, h in [(7, 22), (8, 30), (9, 18), (10, 18), (11, 8)]:
    ws.row_dimensions[r].height = h
for q in range(4):
    c0 = 2 + q * 4; r = 38 + q
    B.box(ws, 7, c0, 10, c0 + 2)
    for cc in range(c0, c0 + 3):
        ws.cell(7, cc).border = skin.Border(top=skin.Side(style='medium', color=[DSAGE, GOLD, CHAR, CORAL][q]),
                                            left=thin() if cc == c0 else None, right=thin() if cc == c0 + 2 else None)
    B.text(ws, 7, c0, f'=IF(N(K{r})>0,"{PERIODS[q][0]} · PAID "&UPPER(TEXT(I{r},"mmm d, yyyy")),"{PERIODS[q][0]} · DUE "&UPPER(TEXT(E{r},"mmm d, yyyy")))', 7.5, True, MUTED, w=3, indent=1, valign='bottom')
    B.text(ws, 8, c0, f'=IF(N(K{r})>0,K{r},G{r})', 17, True, INK, w=3, indent=1, fmt=USD)
    B.text(ws, 9, c0, f'=IF(N(K{r})>0,"✓ Paid · planned "&TEXT(G{r},"$#,##0"),O{r})', 8.5, True, DSAGE, w=3, indent=1)
    B.text(ws, 10, c0, f'="Due "&TEXT(E{r},"mmm d")&" · income "&C{r}', 8, False, MUTED, w=3, indent=1, valign='top')
check_fmt(ws, 'B9:P9', 'B9')
# --- tax pot (rows 46-60)
B.section(ws, 46, 2, 'Your tax savings pot, month by month', 10)
B.th(ws, 47, 2, 'MONTH', 2); B.th(ws, 47, 4, 'PROFIT', 2, 'right'); B.th(ws, 47, 6, 'SET ASIDE (PLAN)', 2, 'right')
B.th(ws, 47, 8, 'MOVED TO POT', 2, 'right'); B.th(ws, 47, 10, 'PAID TO IRS', 2, 'right'); B.th(ws, 47, 12, 'POT BALANCE', 2, 'right')
B.th(ws, 47, 14, 'ON TRACK?', 4)
import math
_mi = [0] * 12
for _r in inc_rows:
    if isinstance(_r[0], dt.date) and _r[0].year == 2026: _mi[_r[0].month - 1] += _r[3]
    elif isinstance(_r[0], str) and _r[0].startswith('2026'): _mi[int(_r[0][5:7]) - 1] += float(_r[3].strip('$').replace(',', ''))
MOVED = [math.ceil(v * 0.25 / 50) * 50 for v in _mi[:11]]
MOVED[6] -= 400
for i in range(12):
    r = 48 + i
    ms, me = f'DATE({YR},{i + 1},1)', f'DATE({YR},{i + 2},0)'
    B.fx(ws, r, 2, MON[i], None, True, None, 'left', 2)
    B.fx(ws, r, 4, f'=Dashboard!$J${82 + i}', USD, False, None, 'right', 2)
    B.fx(ws, r, 6, f'=MAX(0,Dashboard!$D${82 + i})*{SR["setaside"]}', USD, False, None, 'right', 2)
    B.inp(ws, r, 8, MOVED[i] if i < len(MOVED) else None, '#,##0', 'right', w=2)
    B.fx(ws, r, 10, f'=SUMIFS($K$38:$K$41,$I$38:$I$41,">="&{ms},$I$38:$I$41,"<="&{me})', USD, False, None, 'right', 2)
    B.fx(ws, r, 12, f'=IF(AND(H{r}="",SUM($J$48:K{r})=0),"",SUM($H$48:I{r})-SUM($J$48:K{r}))', USD, True, None, 'right', 2)
    B.fx(ws, r, 14, f'=IF(H{r}="","",IF(H{r}>=F{r},"✓ Moved the plan","✕ Short by "&{M(f"F{r}-H{r}")}))', None, False, None, 'left', 4, size=9)
check_fmt(ws, 'N48:N59', 'N48')
B.fx(ws, 60, 2, 'Total', None, True, TINT, 'left', 2)
for c in (4, 6, 8, 10):
    B.fx(ws, 60, c, f'=SUM({L(c)}48:{L(c + 1)}59)', USD, True, TINT, 'right', 2)
B.fx(ws, 60, 12, '=H60-J60', USD, True, TINT, 'right', 2); B.fx(ws, 60, 14, '', None, False, TINT, 'left', 4)
B.tip(ws, 62, 2, 'Keep the pot in a separate savings account. Each payday, move your set-aside % (Settings) and type it under "Moved to pot". '
      'Payments in the table above come off the pot by themselves. Estimate, not tax advice.', 16, 1, 34)
QT_TO = [f'{QT}!$G${38 + q}' for q in range(4)]
QT_PAID, QT_TARGET, QT_LEFT, QT_POT = f'{QT}!$K$24', f'{QT}!$K$22', f'{QT}!$K$25', f'{QT}!$L$60'
B.protect(ws)

# ================================================================== Accountant Checklist
ws = S['Accountant Checklist']
B.page(ws, 'Ready for your accountant', 'Tick each one off before tax time. Hand over this file, or print the Schedule C and Tax Estimate tabs as PDF.',
       {2: 6, 3: 58, 4: 16, 5: 3, 6: 52}, ncols=6, nrows=50)
B.th(ws, 8, 2, '#'); B.th(ws, 8, 3, 'WHAT TO HAVE READY'); B.th(ws, 8, 4, 'DONE?'); B.th(ws, 8, 6, 'WHY IT MATTERS')
CL = [('All income logged, and the total matches your business bank deposits', 'Done', 'Income Log. Every payment, with or without a 1099.'),
      ('1099-NEC and 1099-K forms collected and compared with the By client list', 'Not yet', 'Forms arrive by Jan 31. Count each payment once.'),
      ('Every deduction has a receipt or invoice saved (photo or PDF)', 'Done', 'Keep them with your return, at least 3 years.'),
      ('Deductions log has no ✕ rows', 'Done', 'Fix or delete rows the Check column flags.'),
      ('Mileage log complete: date, trip, purpose, miles', 'Done', 'A log written at the time is what the IRS asks for.'),
      ('Vehicle questions answered (Schedule C Part IV, Mileage tab)', 'Done', 'Lines 43 to 47.'),
      ('Home office measured: square feet used only for work', 'Done', 'Regular and exclusive use only.'),
      ('Quarterly payments: dates, amounts and confirmation numbers', 'Not yet', 'Quarterly Tax tab. Your tax pro needs all four.'),
      ('State estimated payments, if you made any', 'Not needed', ''),
      ('Health insurance statements (Form 1095-A if from the Marketplace)', 'Not yet', 'For the self-employed health insurance deduction.'),
      ('Retirement contributions: SEP-IRA or solo 401(k) statements', 'Not yet', 'Some can still be made up to the filing date.'),
      ('W-2 from a job, if you had one', 'Not needed', ''),
      ('Last year\'s tax return (PDF)', 'Done', 'For safe harbor and carry-overs.'),
      ('Big purchases listed (equipment over $2,500)', 'Done', 'Your tax pro decides: expense now or depreciate.'),
      ('Bank account and routing number for a refund or payment', 'Not yet', ''),
      ('Questions for your tax pro written down (below)', 'Done', 'Saves paid time on the call.')]
for i, (t, v, w) in enumerate(CL):
    r = 9 + i
    B.fx(ws, r, 2, i + 1, '0', True, None, 'center', color=GOLD)
    c = B.fx(ws, r, 3, t, None, False, None, 'left'); c.alignment = Alignment(wrap_text=True, vertical='center', indent=1)
    B.inp(ws, r, 4, v)
    B.fx(ws, r, 6, w, None, False, None, 'left', color=MUTED, size=8.5)
    ws.cell(r, 8, f'=IF(OR(D{r}="Done",D{r}="Not needed"),"",SUMPRODUCT(($D$9:D{r}<>"Done")*($D$9:D{r}<>"Not needed")))').font = F(8, color='C9C2B6')
    ws.row_dimensions[r].height = 26
ACT = ['Check your income total matches your business bank deposits', 'Collect your 1099-NEC / 1099-K forms and compare them with By client',
       'Save a receipt or invoice for every deduction', 'Fix any ✕ rows in the Deductions log', 'Finish the mileage log: date, trip, purpose, miles',
       'Answer the vehicle questions (Mileage tab, Part IV)', 'Measure your home office square feet',
       'Log each quarterly payment\'s date, amount and confirmation #', 'Gather any state estimated payment records',
       'Download your health insurance statements (Form 1095-A)', 'Download your SEP-IRA / solo 401(k) statements', 'Find your W-2, if you had a job',
       'Save last year\'s tax return as a PDF', 'List big purchases (equipment over $2,500)', 'Note your bank account and routing number',
       'Write down your questions for your tax pro']
for i, a_ in enumerate(ACT):
    ws.cell(9 + i, 9, a_).font = F(8, color='C9C2B6')
CL1, CL2 = 9, 8 + len(CL)
assert len(ACT) == len(CL)
ws.column_dimensions['H'].hidden = True
ws.column_dimensions['I'].hidden = True
B.dv(ws, f'D{CL1}:D{CL2}', ['Done', 'Not yet', 'Not needed'])
ws.conditional_formatting.add(f'D{CL1}:D{CL2}', FormulaRule(formula=[f'D{CL1}="Done"'], font=Font(name=FONT, color=DSAGE, bold=True)))
ws.conditional_formatting.add(f'D{CL1}:D{CL2}', FormulaRule(formula=[f'D{CL1}="Not yet"'], font=Font(name=FONT, color=CORAL, bold=True)))
DONE = f'(COUNTIF(D{CL1}:D{CL2},"Done")+COUNTIF(D{CL1}:D{CL2},"Not needed"))'
B.fx(ws, CL2 + 2, 2, f'="Ready: "&{DONE}&" of {len(CL)}"', None, True, TINT, 'left', 2)
B.fx(ws, CL2 + 2, 4, f'={bar_f(DONE + "/" + str(len(CL)), DSAGE, 16)}', None, False, TINT, 'left', 3, DSAGE)
B.section(ws, CL2 + 4, 2, 'Questions for your tax pro', 4)
QA = ['Should I expense the MacBook this year or depreciate it?', 'Am I on track with safe harbor for 2026?', 'Is a solo 401(k) better than a SEP-IRA for me next year?']
for i in range(4):
    r = CL2 + 5 + i
    B.fx(ws, r, 2, i + 1, '0', True, None, 'center', color=GOLD); B.inp(ws, r, 3, QA[i] if i < len(QA) else None, w=4)
    ws.row_dimensions[r].height = 24
B.tip(ws, CL2 + 10, 2, 'Bring: this file (or PDFs of the Schedule C, Tax Estimate and Quarterly Tax tabs), your 1099s, receipts folder and last year\'s return. '
      'Estimate, not tax advice: your tax pro will check every figure.', 5, 1, 40)
AC_DONE = f'{AC}!$B${CL2 + 2}'
B.protect(ws)

# ================================================================== Dashboard data (rows 80+) used by charts, tax pot and check-in
ws = S['Dashboard']
D0 = 80
B.page(ws, 'US Self-Employed Tax Tracker', '', ncols=16, nrows=120)
B.section(ws, D0, 2, 'The numbers behind the charts', 10)
B.th(ws, D0 + 1, 2, 'MONTH', 2); B.th(ws, D0 + 1, 4, 'Income', 2, 'right'); B.th(ws, D0 + 1, 6, 'Deductions', 2, 'right')
B.th(ws, D0 + 1, 8, 'Business spend', 2, 'right'); B.th(ws, D0 + 1, 10, 'Profit', 2, 'right'); B.th(ws, D0 + 1, 12, 'Payments', 2, 'right')
B.th(ws, D0 + 1, 14, 'Has data', 2, 'right')
for i in range(12):
    r = D0 + 2 + i
    ms, me = f'DATE({YR},{i + 1},1)', f'DATE({YR},{i + 2},0)'
    B.fx(ws, r, 2, MON[i], None, True, align='left', w=2)
    B.fx(ws, r, 4, f'=SUMIFS({IL}!$W${IR1}:$W${IR2},{IL}!$U${IR1}:$U${IR2},">="&{ms},{IL}!$U${IR1}:$U${IR2},"<="&{me})', USD, w=2)
    B.fx(ws, r, 6, f'=SUMIFS({DL_}!$I${ER1}:$I${ER2},{DL_}!$N${ER1}:$N${ER2},">="&{ms},{DL_}!$N${ER1}:$N${ER2},"<="&{me})'
                   f'+SUMIFS({ML}!$G${MR1}:$G${MR2},{ML}!$B${MR1}:$B${MR2},">="&{ms},{ML}!$B${MR1}:$B${MR2},"<="&{me})', USD, w=2)
    B.fx(ws, r, 8, f'=SUMIFS({DL_}!$H${ER1}:$H${ER2},{DL_}!$N${ER1}:$N${ER2},">="&{ms},{DL_}!$N${ER1}:$N${ER2},"<="&{me},{DL_}!$K${ER1}:$K${ER2},"✓*")', USD, w=2)
    B.fx(ws, r, 10, f'=D{r}-F{r}', USD, w=2)
    B.fx(ws, r, 12, f'=COUNTIFS({IL}!$U${IR1}:$U${IR2},">="&{ms},{IL}!$U${IR1}:$U${IR2},"<="&{me},{IL}!$W${IR1}:$W${IR2},">0")', '0', w=2)
    B.fx(ws, r, 14, f'=IF(D{r}+F{r}>0,{i + 1},0)', '0', w=2)
B.fx(ws, D0 + 14, 2, 'Latest month with data', None, True, TINT, 'left', 2); B.fx(ws, D0 + 14, 4, f'=MAX(N{D0 + 2}:N{D0 + 13})', '0', True, TINT, w=2)
LATEST = f'Dashboard!$D${D0 + 14}'
# expense lines table
LT = D0 + 16
B.th(ws, LT, 2, 'SCHEDULE C LINE', 4); B.th(ws, LT, 6, 'Amount', 2, 'right')
DLINES = [('Car and truck (line 9)', '9'), ('Office expense (18)', '18'), ('Rent: coworking (20b)', '20b'), ('Utilities (25)', '25'),
          ('Other: software etc. (27b)', '27b'), ('Equipment (13)', '13'), ('Travel (24a)', '24a'), ('Contract labor (11)', '11'),
          ('Legal and professional (17)', '17'), ('Commissions and fees (10)', '10'), ('Home office (30)', '30'), ('Everything else', 'rest')]
for i, (lab, ln) in enumerate(DLINES):
    r = LT + 1 + i
    B.fx(ws, r, 2, lab, align='left', w=4)
    if ln == 'rest':
        f = f'=MAX(0,{EXPTOT}+{HOME}-SUM(F{LT + 1}:G{r - 1}))'
    elif ln == '30':
        f = f'={HOME}'
    else:
        f = f'={SC}!$D${SROW[ln]}'
    B.fx(ws, r, 6, f, USD, w=2)
# tax split
TS = LT + 15
B.th(ws, TS, 2, 'TAX FOR THE YEAR', 4); B.th(ws, TS, 6, 'Estimate', 2, 'right')
for i, (lab, ref) in enumerate([('Federal income tax', TE_FIT), ('Self-employment tax', TE_SE), ('State (rough)', TE_STATE)]):
    B.fx(ws, TS + 1 + i, 2, lab, align='left', w=4); B.fx(ws, TS + 1 + i, 6, f'={ref}', USD, w=2)
# quarters
QD = TS + 5
B.th(ws, QD, 2, 'QUARTER', 2); B.th(ws, QD, 4, 'Planned', 2, 'right'); B.th(ws, QD, 6, 'Paid', 2, 'right')
for q in range(4):
    r = QD + 1 + q
    B.fx(ws, r, 2, f'="Q{q + 1} "&TEXT({TR}!$E${QROWS[q]},"mmm d")', None, True, align='left', w=2)
    B.fx(ws, r, 4, f'={QT}!$G${38 + q}', USD, w=2); B.fx(ws, r, 6, f'=N({QT}!$K${38 + q})', USD, w=2)

# ================================================================== Dashboard top
ws['B2'] = f'=IF({SR["name"]}="","Your",{SR["name"]}&"\'s")&" "&{YR}&" self-employed tax tracker"'; ws['B2'].font = F(20, True)
ws['B3'] = (f'=IF({SR["biz"]}="","",{SR["biz"]}&"  ·  ")&"tax year "&{YR}&"  ·  "&{SR["fs"]}&"  ·  estimate, not tax advice"')
ws['B3'].font = F(10, color=MUTED)
for r, h in [(7, 22), (8, 30), (9, 18), (10, 8), (11, 22), (12, 30), (13, 18)]:
    ws.row_dimensions[r].height = h
# next payment: first quarter not paid with due date >= today
for q in range(4):
    S['Quarterly Tax'].cell(38 + q, 19, f'=IF(AND(N(K{38 + q})=0,E{38 + q}>=TODAY(),G{38 + q}>0),1,0)').font = F(8, color='C9C2B6')
S['Quarterly Tax'].column_dimensions['S'].hidden = True
QIDX = f'IFERROR(MATCH(1,{QT}!$S$38:$S$41,0),0)'
ws['T7'] = f'={QIDX}'; ws['T7'].font = F(8, color='C9C2B6')
NQ = 'Dashboard!$T$7'
ws.column_dimensions['T'].hidden = True
B.hero(ws, 7, 2, 7, 7, '=IF(' + NQ + '=0,"NEXT ESTIMATED TAX PAYMENT","NEXT PAYMENT · Q"&' + NQ + '&" · DUE "&UPPER(TEXT(INDEX(' + QT + '!$E$38:$E$41,' + NQ + '),"mmm d, yyyy")))',
       f'=IF({NQ}=0,0,INDEX({QT}!$G$38:$G$41,{NQ}))',
       f'=IF({INC_T}=0,"Fill in Settings and the Income Log to see your payments.",IF({NQ}=0,"No payment left to make for "&{YR}&". Any balance is due when you file in April.",'
       f'INDEX({QT}!$E$38:$E$41,{NQ})-TODAY()&" days left. Pay at irs.gov/payments. Your tax pot holds "&{M(QT_POT)}&"."))',
       'Estimate, not tax advice. Safe harbor plan from the Quarterly Tax tab.', value_fmt='$#,##0')
B.kpi(ws, 7, 10, 'INCOME LOGGED', f'={INC_T}', f'={INC_N}&" payments"', value_fmt='$#,##0', accent=DSAGE)
B.kpi(ws, 7, 14, 'DEDUCTIONS', f'={EXPTOT}+{HOME}', f'="incl. "&TEXT({MIL_M},"#,##0")&" business miles"', value_fmt='$#,##0', accent=DSAGE)
B.kpi(ws, 11, 10, 'NET PROFIT', f'={NET}', '="Schedule C line 31"', value_fmt='$#,##0', accent=GOLD)
B.kpi(ws, 11, 14, 'TOTAL TAX (EST.)', f'={TE_ALL}', f'=TEXT({TE_RATE},"0%")&" of "&{M(TE_PROFIT)}&" projected profit"', value_fmt='$#,##0', accent=CORAL)
# next steps
B.box(ws, 15, 2, 19, 16, TINT, TINT)
B.text(ws, 15, 2, 'YOUR NEXT 3 STEPS', 8, True, DSAGE, w=4, indent=1)
B.text(ws, 15, 6, f'=IF({INC_X}+{EXP_X}+{MIL_X}>0,"Check: "&({INC_X}+{EXP_X}+{MIL_X})&" row(s) in your logs show ✕ (not counted)","")', 9, True, CORAL, w=11, align='right')
B.text(ws, 16, 2, f'=IF({NQ}=0,"1.  Keep logging income and costs as they happen","1.  Pay Q"&{NQ}&" estimated tax: "&{M("INDEX(" + QT + "!$G$38:$G$41," + NQ + ")")}&" by "&TEXT(INDEX({QT}!$E$38:$E$41,{NQ}),"mmm d, yyyy"))',
       10.5, True, CHAR, w=15, indent=2)
for k in range(2):
    r = 17 + k
    f = (f'=IFERROR("{k + 2}.  "&INDEX({AC}!$I${CL1}:$I${CL2},MATCH({k + 1},{AC}!$H${CL1}:$H${CL2},0)),IF({k}=0,"2.  Your accountant checklist is complete.",""))')
    B.text(ws, r, 2, f, 10.5, False, CHAR, w=15, indent=2)
for r in (16, 17, 18): ws.row_dimensions[r].height = 22
ws.row_dimensions[19].height = 8
for r, h in [(21, 22), (22, 30), (23, 18)]:
    ws.row_dimensions[r].height = h
B.kpi(ws, 21, 2, 'SE TAX', f'={TE_SE}', '="15.3% on 92.35% of profit"', value_fmt='$#,##0')
B.kpi(ws, 21, 6, 'FEDERAL INCOME TAX', f'={TE_FIT}', f'="taxable income "&{M(TE_TI)}', value_fmt='$#,##0')
B.kpi(ws, 21, 10, 'PAID SO FAR', f'={QT_PAID}', f'="of "&{M(QT_TARGET)}&" target"', value_fmt='$#,##0')
B.kpi(ws, 21, 14, 'SET ASIDE PER PAYMENT', f'={TE_SUG}', f'="suggested · yours: "&TEXT({SR["setaside"]},"0%")', value_fmt='0%')
# charts
cats = Reference(ws, min_col=2, min_row=D0 + 2, max_row=D0 + 13)
bar_chart(ws, 'B25', 'Income vs deductions by month', cats, Reference(ws, min_col=4, max_col=4, min_row=D0 + 1, max_row=D0 + 13), w=11.8, h=7.4, colors=[DSAGE])
ch = ws._charts[-1]
ch2 = BarChart(); ch2.add_data(Reference(ws, min_col=6, min_row=D0 + 1, max_row=D0 + 13), titles_from_data=True)
s2 = ch2.series[0]; s2.graphicalProperties.solidFill = GOLD; s2.graphicalProperties.line.solidFill = GOLD
ch.series.append(s2); ch.gapWidth = 40
ch.series[0].tx = SeriesLabel(v='Income'); ch.series[1].tx = SeriesLabel(v='Deductions')
bar_chart(ws, 'J25', 'Deductions by Schedule C line', Reference(ws, min_col=2, min_row=LT + 1, max_row=LT + 12),
          Reference(ws, min_col=6, min_row=LT, max_row=LT + 12), w=11.8, h=7.4, horizontal=True, legend=False, colors=[DSAGE])
doughnut(ws, 'B41', 'Your tax for the year (estimate)', Reference(ws, min_col=2, min_row=TS + 1, max_row=TS + 3),
         Reference(ws, min_col=6, min_row=TS, max_row=TS + 3), w=11.8, h=7.4, colors=[CHAR, GOLD, SAGE])
bar_chart(ws, 'J41', 'Quarterly payments: planned vs paid', Reference(ws, min_col=2, min_row=QD + 1, max_row=QD + 4),
          Reference(ws, min_col=4, max_col=4, min_row=QD, max_row=QD + 4), w=11.8, h=7.4, colors=[SAGE])
qc = ws._charts[-1]
ch3 = BarChart(); ch3.add_data(Reference(ws, min_col=6, min_row=QD, max_row=QD + 4), titles_from_data=True)
s3 = ch3.series[0]; s3.graphicalProperties.solidFill = CHAR; s3.graphicalProperties.line.solidFill = CHAR
qc.series.append(s3); qc.series[0].tx = SeriesLabel(v='Planned'); qc.series[1].tx = SeriesLabel(v='Paid')
PD = QD + 6
B.th(ws, PD, 2, 'IRS PERIOD', 2); B.th(ws, PD, 4, 'Income', 2, 'right'); B.th(ws, PD, 6, 'Deductions', 2, 'right'); B.th(ws, PD, 8, 'Profit', 2, 'right')
for q, (lab, a, b) in enumerate([('Q1 Jan-Mar', 0, 2), ('Q2 Apr-May', 3, 4), ('Q3 Jun-Aug', 5, 7), ('Q4 Sep-Dec', 8, 11)]):
    r = PD + 1 + q
    B.fx(ws, r, 2, lab, None, True, align='left', w=2)
    B.fx(ws, r, 4, f'=SUM(D{D0 + 2 + a}:E{D0 + 2 + b})', USD, w=2); B.fx(ws, r, 6, f'=SUM(F{D0 + 2 + a}:G{D0 + 2 + b})', USD, w=2)
    B.fx(ws, r, 8, f'=D{r}-F{r}', USD, w=2)
bar_chart(ws, 'B57', 'Profit by estimated-tax period', Reference(ws, min_col=2, min_row=PD + 1, max_row=PD + 4),
          Reference(ws, min_col=8, max_col=8, min_row=PD, max_row=PD + 4), w=11.8, h=7.4, colors=[GOLD], legend=False)
B.section(ws, 57, 10, 'Key dates', 7)
B.th(ws, 58, 10, 'DATE', 2); B.th(ws, 58, 12, 'WHAT', 5)
KD = [(f'={TR}!$E${QROWS[0]}', 'Q1 estimated tax (Jan to Mar income)'), (f'={TR}!$E${QROWS[1]}', 'Q2 estimated tax (Apr to May income)'),
      (f'={TR}!$E${QROWS[2]}', 'Q3 estimated tax (Jun to Aug income)'), (f'={TR}!$E${QROWS[3]}', 'Q4 estimated tax (Sep to Dec income)'),
      (f'=DATE({YR}+1,1,31)', '1099-NEC and 1099-K forms arrive by'), (f'=DATE({YR}+1,4,15)', 'File your return, pay any balance')]
for i, (dd_, t) in enumerate(KD):
    r = 59 + i
    B.fx(ws, r, 10, dd_, DATE, True, None, 'left', 2); B.fx(ws, r, 12, t, None, False, None, 'left', 5)
B.text(ws, 66, 10, 'April 15 moves to the next business day if it falls on a weekend or holiday. Estimate, not tax advice. Way of Wealth Studio · joel@wayofwealthcoaching.com',
       8.5, False, MUTED, w=7, h=2)
for c in ws._charts:
    c.roundedCorners = False
    if c.legend is not None: c.legend.overlay = False
B.protect(ws)

# ================================================================== Monthly Money Check-in
ws = S['Monthly Money Check-in']
B.page(ws, 'Monthly Money Check-in', 'Once a month, 15 minutes: see your month in plain words, then answer 5 questions. No AI needed.',
       {c: 9 for c in range(2, 17)}, ncols=16, nrows=70)
B.text(ws, 7, 2, 'WHICH MONTH?', 8, True, MUTED, w=2, indent=1)
B.inp(ws, 7, 4, 'October', None, 'left', w=3)
B.dv(ws, 'D7', ref=MONTHREF)
B.text(ws, 7, 7, f'=IF(D7="","Blank = your latest month ("&IF({LATEST}=0,"none logged yet",INDEX({MONTHREF},{LATEST}))&"). Pick a month to look back at another.","Showing "&D7&" "&{YR}&". Clear the box to see your latest month.")',
       9, False, MUTED, w=10, indent=1)
ws.row_dimensions[7].height = 26
GROUPS = [('Advertising and marketing', [C_('Advertising')]), ('Platform and payment fees', [C_('Commissions'), C_('bank fees')]),
          ('Contract labor', [C_('Contract labor')]), ('Office and supplies', [C_('Office expense'), C_('Supplies')]),
          ('Coworking and rent', [C_('other business property'), C_('vehicles, machinery')]), ('Software and subscriptions', [C_('software')]),
          ('Phone and internet', [C_('Utilities')]), ('Travel and meals', [C_('Travel'), C_('Business meals')]),
          ('Learning and memberships', [C_('education'), C_('dues')])]
PLAN = [100, 60, 0, 60, 250, 80, 110, 60, 60, 100]
NG = len(GROUPS) + 1
H = {}
helpers = [('m', f'=IF(D7="",N({LATEST}),MATCH(D7,{MONTHREF},0))'),
           ('mname', f'=IF(N(R8)=0,"",INDEX({MONTHREF},R8)&" "&{YR})'),
           ('inc', f'=IF(N(R8)=0,0,INDEX(Dashboard!$D${D0 + 2}:$D${D0 + 13},R8))'),
           ('spent', f'=IF(N(R8)=0,0,INDEX(Dashboard!$H${D0 + 2}:$H${D0 + 13},R8))'),
           ('plan', f'=SUM(E23:F{22 + NG})'),
           ('npay', f'=IF(N(R8)=0,0,INDEX(Dashboard!$L${D0 + 2}:$L${D0 + 13},R8))'),
           ('profit', f'=IF(N(R8)=0,0,INDEX(Dashboard!$J${D0 + 2}:$J${D0 + 13},R8))'),
           ('maxover', '=IF(MAX(T23:T32)>0,MAX(T23:T32),0)'),
           ('overcat', '=IF(R15<=0,"",INDEX(B23:B32,MATCH(MAX(T23:T32),T23:T32,0)))'),
           ('nover', '=COUNTIF(T23:T32,">0")'),
           ('moved', f'=IF(N(R8)=0,0,N(INDEX({QT}!$H$48:$H$59,R8)))'),
           ('pot', f'=IF(N(R8)=0,0,N(INDEX({QT}!$L$48:$L$59,R8)))'),
           ('nextq', f'=IF(N(R8)=0,0,COUNTIF({QDUE},"<="&DATE({YR},R8+1,0))+1)'),
           ('nextamt', f'=IF(OR(R20=0,R20>4),0,INDEX({QT}!$G$38:$G$41,R20))'),
           ('nextdate', f'=IF(OR(R20=0,R20>4),"",TEXT(INDEX({QDUE},R20),"mmm d, yyyy"))'),
           ('cover', '=IF(R21<=0,0,R19/R21)')]
for i, (k, f) in enumerate(helpers):
    r = 8 + i; H[k] = f'$R${r}'
    ws.cell(r, 17, k).font = F(7.5, color='C9C2B6'); ws.cell(r, 18, f).font = F(7.5, color='C9C2B6')
for col in 'QRST':
    ws.column_dimensions[col].hidden = True
ws.row_dimensions[8].height = 10
B.section(ws, 9, 2, 'Your month in plain words', 8)
B.text(ws, 9, 11, 'One cell, ready to copy: click it, copy, paste.', 8.5, False, MUTED, w=6, align='right', italic=True)
summ = (f'=IF(OR(N({H["m"]})=0,{H["inc"]}+{H["spent"]}=0),"Log some income or costs for this month and it appears here in plain words.",'
        f'"In "&{H["mname"]}&" you earned "&{M(H["inc"])}&" from "&{H["npay"]}&IF({H["npay"]}=1," payment"," payments")&" and spent "&{M(H["spent"])}&" on the business"'
        f'&IF({H["plan"]}=0,". "," against a plan of "&{M(H["plan"])}&", "&IF({H["spent"]}<={H["plan"]},{M(H["plan"] + "-" + H["spent"])}&" under plan. ",{M(H["spent"] + "-" + H["plan"])}&" over plan. "))'
        f'&IF({H["maxover"]}>0,"Your biggest overspend was "&LOWER({H["overcat"]})&", "&{M(H["maxover"])}&" over plan"&IF({H["nover"]}>1," ("&{H["nover"]}&" categories went over)","")&". ",IF({H["plan"]}=0,"","Every category stayed within plan. "))'
        f'&"Profit after deductions was "&{M(H["profit"])}&" and you moved "&{M(H["moved"])}&" to tax savings. "'
        f'&IF({H["nextamt"]}>0,"Your tax pot holds "&{M(H["pot"])}&IF({H["cover"]}>=1,", enough for the "&{M(H["nextamt"])}&" estimated tax due on "&{H["nextdate"]}&", with "&{M(H["pot"] + "-" + H["nextamt"])}&" left towards April.",", which covers "&TEXT({H["cover"]},"0%")&" of the "&{M(H["nextamt"])}&" estimated tax due on "&{H["nextdate"]}&"."),'
        f'"Your tax pot holds "&{M(H["pot"])}&" towards April\'s balance."))')
B.box(ws, 10, 2, 16, 9, GOLDT, 'E6D9B5')
c = B.text(ws, 10, 2, summ, 12, False, '4A3F30', w=8, h=7, indent=1)
c.alignment = Alignment(wrap_text=True, vertical='center', indent=1)
for r, h in [(10, 22), (11, 30), (12, 18), (13, 8), (14, 22), (15, 30), (16, 18)]:
    ws.row_dimensions[r].height = h
B.kpi(ws, 10, 11, 'YOU EARNED', f'=IF(N({H["m"]})=0,"–",{M(H["inc"])})', f'={H["npay"]}&" payments"', accent=DSAGE)
B.kpi(ws, 10, 14, 'BUSINESS SPEND', f'=IF(N({H["m"]})=0,"–",{M(H["spent"])})', f'="plan "&{M(H["plan"])}', accent=GOLD)
B.kpi(ws, 14, 11, 'TO TAX SAVINGS', f'=IF(N({H["m"]})=0,"–",{M(H["moved"])})', f'="pot "&{M(H["pot"])}', accent=CORAL)
B.kpi(ws, 14, 14, 'NEXT PAYMENT', f'=IF({H["nextamt"]}=0,"–",{M(H["nextamt"])})', f'=IF({H["nextdate"]}="","",{H["nextdate"]})', accent=CHAR)
for r in (17, 18, 19):
    ws.row_dimensions[r].height = 6
B.section(ws, 20, 2, 'Plan vs actual, business spending', 8)
B.th(ws, 22, 2, 'CATEGORY', 3); B.th(ws, 22, 5, 'Monthly plan', 2, 'right'); B.th(ws, 22, 7, 'Actual', 2, 'right')
B.th(ws, 22, 9, 'Difference', 2, 'right'); B.th(ws, 22, 11, 'How it went', 6)
DLR = lambda c: f'{DL_}!${c}${ER1}:${c}${ER2}'
for i in range(NG):
    r = 23 + i
    ms, me = f'DATE({YR},{H["m"]},1)', f'DATE({YR},{H["m"]}+1,0)'
    if i < len(GROUPS):
        name, cl = GROUPS[i]
        act = '+'.join(f'SUMIFS({DLR("H")},{DLR("F")},"{cc}",{DLR("N")},">="&{ms},{DLR("N")},"<="&{me},{DLR("K")},"✓*")' for cc in cl)
    else:
        name = 'Everything else'
        act = f'MAX(0,{H["spent"]}-SUM(G23:H{r - 1}))'
    B.fx(ws, r, 2, name, None, False, None, 'left', 3)
    B.inp(ws, r, 5, PLAN[i], '#,##0', 'right', w=2, keep=False)
    B.fx(ws, r, 7, f'=IF(N({H["m"]})=0,"",{act})', USD, False, None, 'right', 2)
    B.fx(ws, r, 9, f'=IF(G{r}="","",G{r}-N(E{r}))', '+$#,##0;-$#,##0;"–"', True, None, 'right', 2)
    B.fx(ws, r, 11, f'=IF(I{r}="","",IF(I{r}>0,"▲ over by "&{M(f"I{r}")},IF(I{r}=0,"● on plan","▼ under by "&{M(f"-I{r}")})))', None, False, None, 'left', 6)
    ws.cell(r, 20, f'=IF(OR(I{r}="",N(E{r})=0),-1E+99,I{r})').font = F(7.5, color='C9C2B6')
    ws.row_dimensions[r].height = 20
ws.conditional_formatting.add('K23:K32', FormulaRule(formula=['LEFT(K23,1)="▲"'], font=Font(name=FONT, color=CORAL, bold=True)))
ws.conditional_formatting.add('K23:K32', FormulaRule(formula=['OR(LEFT(K23,1)="▼",LEFT(K23,1)="●")'], font=Font(name=FONT, color=DSAGE, bold=True)))
B.fx(ws, 33, 2, 'Total', None, True, TINT, 'left', 3); B.fx(ws, 33, 5, '=SUM(E23:F32)', USD, True, TINT, 'right', 2)
B.fx(ws, 33, 7, f'=IF(N({H["m"]})=0,"",SUM(G23:H32))', USD, True, TINT, 'right', 2)
B.fx(ws, 33, 9, '=IF(G33="","",G33-E33)', '+$#,##0;-$#,##0;"–"', True, TINT, 'right', 2); B.fx(ws, 33, 11, '', None, False, TINT, 'left', 6)
ws.row_dimensions[34].height = 12
B.section(ws, 35, 2, 'Five questions for your month', 12)
B.text(ws, 36, 2, 'Read the summary first. Answer in a line or two. Honest beats perfect.', 9.5, False, MUTED, w=15, italic=True)
B.th(ws, 37, 2, 'QUESTION', 6); B.th(ws, 37, 8, 'YOUR ANSWER', 9)
QS = [('Which client or project this month felt worth the effort, and which took more out of you than it paid?',
       'Northwind: steady and kind. The rush job for Lumen paid well but ate two weekends.'),
      ('Which business cost are you glad you paid for, and which would you skip next time?',
       'Glad: the conference. Skip: the second design tool I barely opened.'),
      ('When a payment came in late or smaller than you hoped, what did you do, and how did it feel?',
       'I panicked and spent from the tax pot. Next time I wait a week before touching it.'),
      ('Did you move money to tax savings on the day you were paid? If not, what got in the way?',
       'Twice yes, once I forgot. An automatic transfer on payday would fix it.'),
      ('What is one small habit you will try next month?',
       'Send the invoice the same day I finish the work.')]
for i, (q, a) in enumerate(QS):
    r = 38 + i
    c = B.fx(ws, r, 2, q, None, True, None, 'left', 6); c.alignment = Alignment(wrap_text=True, vertical='center', indent=1)
    cc = B.inp(ws, r, 8, a, None, 'left', w=9); cc.alignment = Alignment(wrap_text=True, vertical='center', indent=1)
    ws.row_dimensions[r].height = 46
B.tip(ws, 44, 2, 'Want a second opinion? Copy your summary and these questions into any AI assistant you use (ChatGPT, Gemini, Copilot) '
      'and ask it to reply like a kind, honest money coach.', 15, 1, 34)
B.text(ws, 45, 2, 'Optional. Everything on this tab works on its own, with no AI and no internet: the summary is built by formulas from your own logs.',
       8.5, False, MUTED, w=15, italic=True)
B.protect(ws)

# ================================================================== Start Here
ws = S['Start Here']
B.page(ws, 'Start here', 'Set up in 10 minutes. Five steps, written out. No formulas to touch.', {2: 7, 3: 96, 4: 3}, ncols=3, nrows=45)
B.box(ws, 7, 2, 7, 3, GOLDT, GOLDT)
B.text(ws, 7, 2, '=IF(Settings!$C$7="","Two files: EXAMPLE (filled in) shows a made-up freelancer, Jordan, so you can see every tab working. BLANK (start here) is yours.",'
       '"You are looking at the EXAMPLE file: a made-up freelance designer, Jordan. Look around, then open the BLANK (start here) file for your own numbers.")',
       10, True, '6B5B45', w=2, indent=1)
ws.row_dimensions[7].height = 40
steps = [('1', 'Settings. Pick your TAX YEAR (2026 or 2027) in the one dropdown at the top: every date, rate and due date follows it. '
               'Then your filing status, last year\'s total tax (for safe harbor) and your home office square feet.'),
         ('2', 'Income Log. Type each payment, or paste a CSV of your invoices into the yellow columns (paste as values). Any order, any date style. '
               'The list on the right sorts itself and shows which clients should send a 1099-NEC.'),
         ('3', 'Deductions and Mileage. Log each business cost and pick its Schedule C category: the line number fills in. '
               'Log business trips: the IRS rate is picked by date. A ✓ in the Check column means the row counts.'),
         ('4', 'Schedule C, Tax Estimate, Quarterly Tax. See every total on its Schedule C line, your SE tax and income tax estimate, '
               'and what to pay on each 1040-ES due date. Type each payment you make, and the next one catches you up.'),
         ('5', 'Every month: the Monthly Money Check-in writes your month in plain words. Before tax time: work through the Accountant Checklist '
               'and hand over this file.')]
for i, (n, t) in enumerate(steps):
    r = 9 + i * 2
    B.box(ws, r, 2, r, 3); B.text(ws, r, 2, n, 18, True, GOLD, align='center'); B.text(ws, r, 3, t, 10.5, indent=1)
    ws.row_dimensions[r].height = 50; ws.row_dimensions[r + 1].height = 6
B.tip(ws, 20, 2, 'Colours: pale yellow = type or paste here. White = worked out for you (locked so nothing breaks; Excel: Review > Unprotect Sheet, no password). '
      '✓ = counted, ✕ = needs a look, – = other tax year (kept, not counted).', 2, 1, 40)
B.tip(ws, 22, 2, 'Built with Excel 2016-compatible formulas; works in Microsoft Excel and Google Sheets. No macros, no add-ins. Google Sheets: upload the .xlsx to '
      'Google Drive, open it, choose File > Save as Google Sheets, and move between tabs with the tab bar along the bottom.', 2, 1, 44)
B.tip(ws, 24, 2, 'Estimate, not tax advice. Made for US federal taxes on a Schedule C (sole proprietors, single-member LLCs, 1099 freelancers). '
      'It does not file anything. Your tax pro or the IRS calculation is final. Questions about the file: joel@wayofwealthcoaching.com', 2, 1, 44)
B.text(ws, 26, 2, 'Way of Wealth Studio', 9, True, GOLD, w=2)
B.protect(ws)

for w_ in B.wb.worksheets:
    for c in w_._charts:
        c.roundedCorners = False

# ================================================================== save
AREAS = {'Dashboard': 'A1:R74', 'Income Log': f'A1:Q{T1 + 8}', 'Deductions': f'A1:L{T2 + 4}', 'Mileage': f'A1:L{T3 + 2}',
         'Schedule C': f'A1:G{endr + 1}', 'Tax Estimate': 'A1:F44', 'Quarterly Tax': 'A1:R63', 'Accountant Checklist': f'A1:G{CL2 + 11}',
         'Monthly Money Check-in': 'A1:Q46', 'Start Here': 'A1:D27', 'Settings': 'A1:F26', 'Tax Rates': f'A1:M{BR0 + 11}'}
orig_save = B.wb.save
B.wb.save = lambda p: None
B.save(OUT, AREAS)
for t in ('Income Log', 'Deductions', 'Mileage'):
    S[t].page_setup.fitToHeight = 0
    S[t].print_title_rows = '8:8'
for w_ in B.wb.worksheets:
    w_.oddFooter.center.text = 'Way of Wealth Studio  ·  US Self-Employed Tax Tracker  ·  estimate, not tax advice'
    w_.oddFooter.center.size = 8
B.wb.active = 1 if BLANK else 0
if BLANK:
    for _w in B.wb.worksheets: _w.sheet_view.tabSelected = False
    B.wb.worksheets[1].sheet_view.tabSelected = True
orig_save(OUT)
print('saved', OUT)
