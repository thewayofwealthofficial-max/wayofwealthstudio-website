"""Make real recalculated stage files for the video: months typed in one by one, goals added one by one."""
import os, subprocess, glob
from openpyxl import load_workbook
from PIL import Image
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out'))
R = glob.glob('/root/.claude/skills/synced/*/xlsx/scripts/recalc.py')[0]
os.makedirs('stg', exist_ok=True)
jobs = [('m', k) for k in (0, 3, 6, 9, 12)] + [('g', k) for k in (0, 1, 2, 3, 4)]
for kind, k in jobs:
    wb = load_workbook('sample.xlsx')
    if kind == 'm':
        ws = wb['Year in Numbers']
        for r in range(8 + k, 20):
            for c in (3, 4, 6, 7, 8):
                ws.cell(r, c).value = None
    else:
        ws = wb['2027 Goals']
        for r in range(8 + k, 13):
            for c in (3, 4, 5, 6, 7, 9, 10):
                ws.cell(r, c).value = None
    f = f'stg/{kind}{k}.xlsx'
    wb.save(f)
    subprocess.run(['python3', R, f, '60'], check=True, capture_output=True)
    subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', 'stg', f], check=True, capture_output=True)
    page = 4 if kind == 'm' else 8
    subprocess.run(['pdftoppm', '-r', '200', '-png', '-f', str(page), '-l', str(page), f'stg/{kind}{k}.pdf', f'stg/{kind}{k}_p'], check=True)
    subprocess.run(['pdftoppm', '-r', '200', '-png', '-f', '1', '-l', '1', f'stg/{kind}{k}.pdf', f'stg/{kind}{k}_d'], check=True)
    for tag in ('p', 'd'):
        fn = glob.glob(f'stg/{kind}{k}_{tag}-*.png')[0]
        im = Image.open(fn).convert('RGB')
        im.crop((150, 200, 2051, 1500) if im.width > im.height else (150, 200, 1549, 1929)).save(f'stg/{kind}{k}_{tag}.png')
    print(kind, k)
