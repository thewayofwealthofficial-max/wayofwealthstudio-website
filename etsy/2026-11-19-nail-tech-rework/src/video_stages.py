"""Typing stages for the in-use video: copies of the EXAMPLE file with a new Client Log row typed in step by step
(31 Oct 2026, Ruby C., BIAB overlay, 38.00, tip 5.00, Cash), recalculated and rendered by LibreOffice.
Rows 9-719 of the Client Log are hidden in these copies so the page shows the latest rows; nothing else changes.
openpyxl drops charts on save, so only the Dashboard cards above the charts are used. Run: python3 video_stages.py"""
import os, sys, glob, subprocess, datetime as dt
from openpyxl import load_workbook
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import EXAMPLE, WORK

R = glob.glob('/root/.claude/skills/synced/*/xlsx/scripts/recalc.py')[0]
OUT = os.path.join(WORK, 'stages'); os.makedirs(OUT, exist_ok=True)
wb0 = load_workbook(EXAMPLE, read_only=True)
last = max(r for r in range(9, 809) if wb0['Client Log'].cell(r, 2).value)
ROW = last + 1
D = ('B', dt.datetime(2026, 10, 31))
STEPS = [[], [D], [D, ('C', 'Ruby C.')], [D, ('C', 'Ruby C.'), ('D', 'BIAB overlay')],
         [D, ('C', 'Ruby C.'), ('D', 'BIAB overlay'), ('E', 38)],
         [D, ('C', 'Ruby C.'), ('D', 'BIAB overlay'), ('E', 38), ('F', 5)],
         [D, ('C', 'Ruby C.'), ('D', 'BIAB overlay'), ('E', 38), ('F', 5), ('G', 'Cash')]]
print('new row', ROW)
for i, edits in enumerate(STEPS):
    name = f's{i}'
    if glob.glob(f'{OUT}/{name}-p4.png'): continue
    wb = load_workbook(EXAMPLE)
    ws = wb['Client Log']
    for col, v in edits: ws[f'{col}{ROW}'].value = v
    for r in range(9, ROW - 11): ws.row_dimensions[r].hidden = True
    ws.print_area = f'A1:K{ROW + 4}'
    f = os.path.join(OUT, name + '.xlsx'); wb.save(f)
    subprocess.run(['python3', R, f, '180'], check=True, capture_output=True)
    subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', OUT, f], check=True, capture_output=True)
    for p in ([1, 4] if i in (0, len(STEPS) - 1) else [4]):
        subprocess.run(['pdftoppm', '-r', '600' if p == 1 else '300', '-png', '-singlefile', '-f', str(p), '-l', str(p), f[:-5] + '.pdf', f'{OUT}/{name}-p{p}'], check=True)
    print(name, 'done')
wb = load_workbook(f'{OUT}/s6.xlsx', data_only=True); w0 = load_workbook(f'{OUT}/s0.xlsx', data_only=True)
print('hero before/after', w0['Dashboard']['B8'].value, wb['Dashboard']['B8'].value, '| tips', w0['Dashboard']['J12'].value, wb['Dashboard']['J12'].value)
