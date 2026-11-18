"""Typing stages for the in-use video: copies of the EXAMPLE file with April 2027 typed into the 2027 Check-ins tab
step by step (column G), recalculated and rendered by LibreOffice. Pages: 1 Dashboard, 9 2027 Check-ins, 10 Monthly Money Check-in.
Run: python3 video_stages.py"""
import os, sys, glob, subprocess
from openpyxl import load_workbook
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import EXAMPLE, WORK
R = glob.glob('/root/.claude/skills/synced/*/xlsx/scripts/recalc.py')[0]
OUT = os.path.join(WORK, 'stages'); os.makedirs(OUT, exist_ok=True)
INC = [('G10', 3550), ('G11', 2900)]
SP = [('G14', 1650), ('G15', 340), ('G16', 720), ('G17', 330), ('G18', 180), ('G19', 260), ('G20', 150), ('G21', 170), ('G22', 60), ('G23', 100)]
TOP = [('G28', 500), ('G29', 460), ('G30', 300), ('G31', 300), ('G35', 'Yes')]
STEPS = [[], INC[:1], INC, INC + SP[:5], INC + SP, INC + SP + TOP]
for i, edits in enumerate(STEPS):
    name = f's{i}'
    if glob.glob(f'{OUT}/{name}-p9.png'): continue
    wb = load_workbook(EXAMPLE); ws = wb['2027 Check-ins']
    for c, v in edits: ws[c].value = v
    f = os.path.join(OUT, name + '.xlsx'); wb.save(f)
    subprocess.run(['python3', R, f, '90'], check=True, capture_output=True)
    subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', OUT, f], check=True, capture_output=True)
    pages = [1, 9, 10] if i in (0, len(STEPS) - 1) else [9]
    for p in pages:
        subprocess.run(['pdftoppm', '-r', '300', '-png', '-singlefile', '-f', str(p), '-l', str(p), f[:-5] + '.pdf', f'{OUT}/{name}-p{p}'], check=True)
    print(name, 'done')
