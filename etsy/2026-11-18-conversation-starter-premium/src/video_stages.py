"""Stages for the in-use video.
Planner: the EXAMPLE rebuilt by build_xlsx.py with November's money date typed in step by step (charts kept),
recalculated and rendered by LibreOffice (Dashboard p1, Money Dates p8, Monthly Check-in p9).
PDF: the Week 3 page of the 4-Week Plan with the goals and agreement typed in step by step (build_pdf.py --demo)."""
import os, sys, json, glob, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import WORK, HERE

R = glob.glob('/root/.claude/skills/synced/*/xlsx/scripts/recalc.py')[0]
OUT = os.path.join(WORK, 'stages'); os.makedirs(OUT, exist_ok=True)
D = [2026, 11, 1]
AG = 'Lisbon goes up to £300 a month until it is booked.'
XL = [{'nov_date': False},
      {'nov': [D, None, None, None, None, None]},
      {'nov': [D, 'Monthly check-in', '4.1, 4.5', None, None, None]},
      {'nov': [D, 'Monthly check-in', '4.1, 4.5', 8, 7, None]},
      {'nov': [D, 'Monthly check-in', '4.1, 4.5', 8, 7, AG]}]
for i, st in enumerate(XL):
    name = f'x{i}'
    if glob.glob(f'{OUT}/{name}-p8.png'): continue
    f = os.path.join(OUT, name + '.xlsx')
    subprocess.run(['python3', '-W', 'ignore', os.path.join(HERE, 'build_xlsx.py'), f, '', json.dumps(st)], check=True, capture_output=True)
    print(subprocess.run(['python3', R, f, '90'], check=True, capture_output=True, text=True).stdout.replace('\n', ' ')[:90])
    subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', OUT, f], check=True, capture_output=True)
    for p in ([1, 8, 9] if i in (0, len(XL) - 1) else [8]):
        subprocess.run(['pdftoppm', '-r', '300', '-png', '-singlefile', '-f', str(p), '-l', str(p), f[:-5] + '.pdf', f'{OUT}/{name}-p{p}'], check=True)
    print(name, 'done')

full = json.load(open(os.path.join(HERE, 'demo_values.json')))
w3 = {k: v for k, v in full.items() if k.startswith('w3_')}
order = ['w3_g1_name', 'w3_g1_amt', 'w3_g1_when', 'w3_g1_pm', 'w3_g2_name', 'w3_g2_amt', 'w3_g2_when', 'w3_g2_pm',
         'w3_g3_name', 'w3_g3_amt', 'w3_g3_when', 'w3_g3_pm', 'w3_agree']
PD = [{}, {k: w3[k] for k in order[:4]}, {k: w3[k] for k in order[:8]}, {k: w3[k] for k in order[:12]}, dict({k: w3[k] for k in order}, w3_agree='Emergency fund first, then Lisbon.')]
for i, vals in enumerate(PD):
    name = f'd{i}'
    if os.path.exists(f'{OUT}/{name}-p5.png'): continue
    d = os.path.join(OUT, name); os.makedirs(d, exist_ok=True)
    j = os.path.join(d, 'v.json'); json.dump(vals, open(j, 'w'))
    subprocess.run(['python3', os.path.join(HERE, 'build_pdf.py'), d, '--demo', j], check=True, capture_output=True)
    subprocess.run(['pdftoppm', '-r', '300', '-png', '-singlefile', '-f', '5', '-l', '5', os.path.join(d, 'demo.pdf'), f'{OUT}/{name}-p5'], check=True)
    print(name, 'done')
