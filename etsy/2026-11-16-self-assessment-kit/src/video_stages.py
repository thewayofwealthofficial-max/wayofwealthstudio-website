"""Typing stages for the in-use video: copies of the EXAMPLE file, each with one more step of a new
Income Log row typed. The example's deliberately out-of-year 14 Apr 2026 row (row 40) is cleared first,
and the new 28 Mar 2026 payment is typed into row 40, so the log stays in date order, recalculated and rendered by LibreOffice (Dashboard = page 1, Income Log = page 4).
Run: SA_WORK=/some/tmp python3 video_stages.py"""
import os, sys, glob, subprocess, datetime as dt
from openpyxl import load_workbook
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import EXAMPLE, WORK

R = glob.glob('/root/.claude/skills/synced/*/xlsx/scripts/recalc.py')[0]
OUT = os.path.join(WORK, 'stages'); os.makedirs(OUT, exist_ok=True)
ROW = 40
D = ('B', dt.datetime(2026, 3, 28)); W = 'Willow Lane Florist'.split()
STEPS = [[],
         [D],
         [D, ('C', W[0])],
         [D, ('C', ' '.join(W[:2]))],
         [D, ('C', ' '.join(W))],
         [D, ('C', ' '.join(W)), ('D', 'Spring window display')],
         [D, ('C', ' '.join(W)), ('D', 'Spring window display'), ('E', 2000), ('F', 'Turnover (fees and sales)')]]

for i, edits in enumerate(STEPS):
    name = f's{i}'
    if glob.glob(f'{OUT}/{name}-p4.png'): continue
    wb = load_workbook(EXAMPLE)
    ws = wb['Income Log']
    for col in 'BCDEF': ws[f'{col}{ROW}'].value = None
    for col, v in edits: ws[f'{col}{ROW}'].value = v
    f = os.path.join(OUT, name + '.xlsx'); wb.save(f)
    subprocess.run(['python3', R, f, '90'], check=True, capture_output=True)
    subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', OUT, f], check=True, capture_output=True)
    for p in ([1, 4] if i in (0, len(STEPS) - 1) else [4]):
        subprocess.run(['pdftoppm', '-r', '600' if p == 1 else '300', '-png', '-singlefile', '-f', str(p), '-l', str(p), f[:-5] + '.pdf', f'{OUT}/{name}-p{p}'], check=True)
    print(name, 'done')
