"""Hand-check the EXAMPLE file: recompute the tax in plain Python from the example inputs and compare to the recalculated sheet."""
import sys, datetime as dt, openpyxl
from decimal import Decimal as D, ROUND_DOWN
P = sys.argv[1]
wb = openpyxl.load_workbook(P, data_only=True)
YS, YE = dt.datetime(2025, 4, 6), dt.datetime(2026, 4, 5)
iny = lambda d: isinstance(d, dt.datetime) and YS <= d <= YE
il = wb['Income Log']; el = wb['Expenses Log']; ml = wb['Mileage']; uh = wb['Use of Home']
turn = sum(D(str(il.cell(r, 5).value)) for r in range(9, 159) if iny(il.cell(r, 2).value) and il.cell(r, 6).value == 'Turnover (fees and sales)')
exp = sum(D(str(el.cell(r, 5).value)) * D(str(el.cell(r, 7).value if el.cell(r, 7).value is not None else 1)) for r in range(9, 209) if iny(el.cell(r, 2).value) and el.cell(r, 6).value)
car = 0; mil = D(0)
for r in range(9, 89):
    d, v, m = ml.cell(r, 2).value, ml.cell(r, 4).value, ml.cell(r, 5).value
    if iny(d) and m:
        hi = min(m, max(0, 10000 - car)); mil += D(hi) * D('0.45') + D(m - hi) * D('0.25'); car += m
home = D(0)
for r in range(9, 21):
    h = uh.cell(r, 3).value or 0
    home += D(0 if h < 25 else 10 if h <= 50 else 18 if h <= 100 else 26)
expenses = exp + mil + home
profit = turn - expenses
ti = max(D(0), profit - 12570)
it = min(ti, D(37700)) * D('0.2') + max(D(0), min(ti, D(125140)) - 37700) * D('0.4')
c4 = max(D(0), min(profit, D(50270)) - 12570) * D('0.06') + max(D(0), profit - 50270) * D('0.02')
it = it.quantize(D('0.01')); c4 = c4.quantize(D('0.01'))
bill = it + c4
poa = (bill / 2).quantize(D('0.01'), ROUND_DOWN) if bill >= 1000 else D(0)
jan = bill + poa
hand = dict(turnover=turn, expenses_log=exp, mileage=mil, use_of_home=home, total_expenses=expenses, profit=profit, income_tax=it, class4=c4, bill=bill, poa_each=poa, due_31jan=jan, due_31jul=poa)
te = wb['Tax Estimate']
sheet = dict(turnover=wb['SA103 Boxes']['D14'].value, profit=te['F8'].value, income_tax=te['F30'].value, class4=te['F35'].value, bill=te['F39'].value,
             poa_each=te['F41'].value, due_31jan=te['F44'].value, due_31jul=te['F45'].value)
ok = True
for k, v in hand.items():
    s = sheet.get(k)
    flag = '' if s is None else ('OK' if abs(D(str(s)) - v) == 0 else 'MISMATCH')
    ok &= flag != 'MISMATCH'
    print(f'{k:15s} hand £{v:>12,.2f}   sheet {"" if s is None else f"£{s:,.2f}":>12s}  {flag}')
tp = wb['Tax Pot 26-27']
pr = [D(str(tp.cell(r, 3).value)) for r in range(9, 21) if tp.cell(r, 3).value is not None]
p27 = sum(pr) / len(pr) * 12
ti27 = max(D(0), p27 - 12570)
it27 = (min(ti27, D(37700)) * D('0.2') + max(D(0), min(ti27, D(125140)) - 37700) * D('0.4')).quantize(D('0.01'))
c427 = (max(D(0), min(p27, D(50270)) - 12570) * D('0.06')).quantize(D('0.01'))
bal28 = max(D(0), it27 + c427 - 2 * poa)
for k, v, sv in [('profit_2026_27', p27, tp['G29'].value), ('bill_2026_27', it27 + c427, tp['G39'].value), ('J16_31jan2028', bal28, tp['J16'].value)]:
    flag = 'OK' if abs(D(str(sv)) - v) < D('0.005') else 'MISMATCH'; ok &= flag == 'OK'
    print(f'{k:15s} hand £{v:>12,.2f}   sheet £{sv:>11,.2f}  {flag}')
print('ALL MATCH' if ok else 'MISMATCH FOUND')
