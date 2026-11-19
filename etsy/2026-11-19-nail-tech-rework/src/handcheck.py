"""Hand-check the EXAMPLE: recompute key totals in plain Python from the inputs and compare with the recalculated sheet."""
import sys, datetime as dt, openpyxl
P = sys.argv[1]
wb = openpyxl.load_workbook(P, data_only=True)
cl, ex, ms, ci, pc = wb['Client Log'], wb['Expenses'], wb['Monthly Summary'], wb['Monthly Money Check-in'], wb['Pricing Check']
rows = [[cl.cell(r, c).value for c in range(2, 9)] for r in range(9, 809) if cl.cell(r, 2).value]
exps = [[ex.cell(r, c).value for c in range(2, 7)] for r in range(9, 309) if ex.cell(r, 2).value]
n = lambda v: v or 0
tak = sum(n(r[3]) + n(r[4]) + n(r[6]) for r in rows); cost = sum(e[4] for e in exps); tips = sum(n(r[4]) for r in rows)
cash = sum(n(r[4]) for r in rows if r[5] == 'Cash')
octo = lambda d: d.year == 2026 and d.month == 10
otak = sum(n(r[3]) + n(r[4]) + n(r[6]) for r in rows if octo(r[0])); ocost = sum(e[4] for e in exps if octo(e[0]))
gel = sum(e[4] for e in exps if octo(e[0]) and e[3] == 'Gel & polish')
# acrylic infill profit per hour: price - product - overhead share
ovh = wb['Rent & Bills']['F27'].value; hours = wb['Settings']['C14'].value
ai = [pc.cell(r, c).value for r in range(10, 25) for c in [2] if pc.cell(r, 2).value == 'Acrylic infill'][0]
r_ai = [r for r in range(10, 25) if pc.cell(r, 2).value == 'Acrylic infill'][0]
pph = (32 - 3 - ovh / hours * 75 / 60) / 75 * 60
checks = [('takings year', tak, ms['F21'].value), ('costs year', cost, ms['G21'].value), ('profit year', tak - cost, ms['H21'].value),
          ('tips year', tips, ms['D21'].value), ('cash tips', cash, ms['N21'].value), ('Oct takings', otak, ci['K8'].value),
          ('Oct costs', ocost, ci['K12'].value), ('Oct gel spend', gel, ci['D27'].value), ('appointments', len(rows), ms['K21'].value),
          ('acrylic infill profit/hr', pph, pc.cell(r_ai, 9).value), ('rent per month', 80 * 52 / 12 + 19 + 12 + 15 + 89 / 12 + 240 / 12, ovh)]
ok = True
for k, h, s in checks:
    f = abs(h - s) < 0.01; ok &= f
    print(f'{k:26s} hand {h:12,.2f}   sheet {s:12,.2f}   {"OK" if f else "MISMATCH"}')
print('summary:', ci['B11'].value)
print('ALL MATCH' if ok else 'MISMATCH FOUND')
