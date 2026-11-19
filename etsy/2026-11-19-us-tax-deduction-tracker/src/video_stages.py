"""Typing stages for the in-use video: copies of the EXAMPLE file with one more step of a new Deductions row typed
(a $3,000 contract-labor bill), recalculated and rendered by LibreOffice.
For each stage: the Deductions tab printed as header + the rows around the new row, and the Dashboard (page 1).
Run: python3 video_stages.py"""
import os, sys, glob, subprocess, datetime as dt, re
from openpyxl import load_workbook
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import EXAMPLE, WORK

R = glob.glob('/root/.claude/skills/synced/*/xlsx/scripts/recalc.py')[0]
OUT = os.path.join(WORK, 'stages'); os.makedirs(OUT, exist_ok=True)
wb0 = load_workbook(EXAMPLE)
ws0 = wb0['Deductions']
ROW = next(r for r in range(9, 309) if ws0[f'B{r}'].value is None)
D = ('B', dt.datetime(2026, 11, 16))
W = 'Sam Ortiz (developer)'
WHAT = 'Prototype phase 2, contract'
CAT = 'Line 11 · Contract labor (freelancers you paid)'
STEPS = [[], [D], [D, ('C', 'Sam Ortiz')], [D, ('C', W)], [D, ('C', W), ('D', WHAT)], [D, ('C', W), ('D', WHAT), ('E', 3000)],
         [D, ('C', W), ('D', WHAT), ('E', 3000), ('F', CAT)]]
for i, edits in enumerate(STEPS):
    name = f's{i}'
    if glob.glob(f'{OUT}/{name}-ded.png'): continue
    wb = load_workbook(EXAMPLE)
    ws = wb['Deductions']
    for col, v in edits: ws[f'{col}{ROW}'].value = v
    ws.print_area = f'A{ROW - 13}:L{ROW + 2}'
    ws.page_setup.fitToHeight = 0
    f = os.path.join(OUT, name + '.xlsx'); wb.save(f)
    subprocess.run(['python3', R, f, '90'], check=True, capture_output=True)
    subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', OUT, f], check=True, capture_output=True)
    pdf = f[:-5] + '.pdf'
    n = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout).group(1))
    ded = None
    for p in range(1, n + 1):
        t = subprocess.run(['pdftotext', '-f', str(p), '-l', str(p), '-layout', pdf, '-'], capture_output=True, text=True).stdout
        if 'SCHEDULE C CATEGORY' in t and 'BUSINESS SHARE' in t.replace('\n', ' ') or ('Line 20b' in t and 'DATE PAID' in t):
            ded = p; break
    subprocess.run(['pdftoppm', '-r', '300', '-png', '-singlefile', '-f', str(ded), '-l', str(ded), pdf, f'{OUT}/{name}-ded'], check=True)
    if i in (0, len(STEPS) - 1):
        subprocess.run(['pdftoppm', '-r', '600', '-png', '-singlefile', '-f', '1', '-l', '1', pdf, f'{OUT}/{name}-dash'], check=True)
    v = load_workbook(f, data_only=True)
    print(name, 'row', ROW, 'ded page', ded, 'Q4 to pay', v['Quarterly Tax']['G41'].value, 'total tax', v['Tax Estimate']['C39'].value,
          'fed', v['Tax Estimate']['C35'].value)
