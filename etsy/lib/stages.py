"""Render 'in use' stages: copy the example workbook, change some input cells, recalculate, render chosen tabs."""
import os, subprocess, glob, shutil
from openpyxl import load_workbook
from PIL import Image, ImageChops
R = glob.glob('/root/.claude/skills/synced/*/xlsx/scripts/recalc.py')[0]


def stage(src, edits, name, pages, work, dpi=220):
    os.makedirs(work, exist_ok=True)
    wb = load_workbook(src)
    for sh, cell, v in edits:
        wb[sh][cell].value = v
    f = os.path.join(work, name + '.xlsx'); wb.save(f)
    subprocess.run(['python3', R, f, '90'], check=True, capture_output=True)
    subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', work, f], check=True, capture_output=True)
    out = {}
    for p in pages:
        base = os.path.join(work, f'{name}_p{p}')
        subprocess.run(['pdftoppm', '-r', str(dpi), '-png', '-f', str(p), '-l', str(p), f[:-5] + '.pdf', base], check=True)
        fn = glob.glob(base + '-*.png')[0]
        im = Image.open(fn).convert('RGB'); bb = ImageChops.difference(im, Image.new('RGB', im.size, (255, 255, 255))).getbbox()
        im.crop(bb).save(base + '.png'); os.remove(fn); out[p] = base + '.png'
    return out
