"""Reviewer side-by-sides: benchmark photos 1-4 vs ours 1-4, and ours vs Moving In Together (house style) 1-4."""
import os
from PIL import Image, ImageDraw, ImageFont
K = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = ImageFont.truetype('/home/claude/fonts/Inter-700.ttf', 34)
def sheet(rows, out):
    T = 700; im = Image.new('RGB', (4 * T + 50, len(rows) * (T + 70) + 10), 'white'); d = ImageDraw.Draw(im)
    for i, (lab, fs) in enumerate(rows):
        y = i * (T + 70) + 10; d.text((12, y), lab, font=F, fill=(42, 38, 32))
        for j, f in enumerate(fs):
            s = Image.open(f).convert('RGB'); s.thumbnail((T, T)); im.paste(s, (10 + j * (T + 10), y + 55))
    im.save(out, quality=85); print(out)
ours = [f'{K}/photos/0{n}.jpg' for n in range(1, 5)]
sheet([('Benchmark: MyProductiveLifeCo "Ultimate Budget for Couples" (Bestseller, listing 1547450542), photos 1-4', [f'{K}/compare/bench/b{n}.jpg' for n in range(1, 5)]),
       ('Ours: Couples Money Year in Review and 2027 Goals, photos 1-4', ours)], f'{K}/compare/side_by_side_benchmark.jpg')
mit = os.path.join(K, '..', '2026-11-12-moving-in-together-rework', 'photos')
sheet([('House style: Moving In Together Money Planner (4613098009), photos 1-4', [f'{mit}/0{n}.jpg' for n in range(1, 5)]),
       ('Ours: Couples Money Year in Review and 2027 Goals, photos 1-4', ours)], f'{K}/compare/side_by_side_house_style.jpg')
