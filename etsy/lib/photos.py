"""Listing photo slots for couples spreadsheets, laid out 1:1 on the AbundanceBudgets 'Couples Simple Budget'
benchmark (Bestseller, 8 photos, 2700x2025): cover, features, dashboard callouts, zoom callouts, log + summary,
re-use/plan with ticks, how to access, reviews/please note. Our product screenshots, our words, our branding.
"""
import os, html
from playwright.sync_api import sync_playwright

W, H = 2700, 2025
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:2700px;height:2025px;overflow:hidden;font-family:Inter,sans-serif;color:#3A2A33;
 background:linear-gradient(135deg,#F6E9E4 0%,#FBF7F0 55%,#F3EEE4 100%);position:relative}
.t{position:absolute;left:0;right:0;text-align:center;font-family:Lora,serif;font-weight:600;color:#4A2C3D;
 letter-spacing:.03em;text-transform:uppercase}
.t b{color:#B8956E;font-weight:600}
.s{position:absolute;left:0;right:0;text-align:center;font-weight:500;color:#6B5560;letter-spacing:.14em;text-transform:uppercase}
.card{position:absolute;background:#fff;box-shadow:0 18px 50px rgba(74,44,61,.16);border-radius:14px;overflow:hidden}
.card img{display:block;width:100%}
.lap{position:absolute}
.lap .lid{background:#26262a;border-radius:30px 30px 8px 8px;padding:34px 34px 40px}
.lap .scr{overflow:hidden;background:#F7F3EC}
.lap .scr img{display:block;width:100%}
.lap .base{height:40px;margin:0 -110px;background:linear-gradient(#d9d6d2,#b9b5b0);border-radius:0 0 40px 40px}
.badge{position:absolute;width:300px;height:300px;border-radius:50%;background:#fff;border:6px solid #B8956E;
 display:flex;align-items:center;justify-content:center;text-align:center;font-weight:700;font-size:40px;line-height:1.15;
 color:#4A2C3D;letter-spacing:.04em;text-transform:uppercase;box-shadow:0 10px 30px rgba(74,44,61,.12)}
.strip{position:absolute;left:0;right:0;bottom:0;height:200px;background:rgba(255,255,255,.78);display:flex;align-items:center;
 justify-content:center;gap:40px;font-weight:600;font-size:54px;letter-spacing:.08em;color:#4A2C3D;text-transform:uppercase}
.strip i{font-style:normal;color:#B8956E}
.seal{position:absolute;left:120px;bottom:40px;width:250px;height:250px;border-radius:50%;background:#4A2C3D;color:#F4E3CF;
 display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;font-size:27px;font-weight:600;
 letter-spacing:.08em;text-transform:uppercase;line-height:1.25;border:8px solid #B8956E}
.seal span{font-family:Lora,serif;font-size:62px;letter-spacing:0;text-transform:none;color:#fff}
.step h3{font-weight:700;font-size:60px;color:#4A2C3D;letter-spacing:.04em;text-transform:uppercase;margin-bottom:14px}
.step p{font-size:46px;line-height:1.35;color:#5A4A52}
.co{position:absolute;font-size:44px;line-height:1.3;color:#4A2C3D;font-weight:500}
svg{position:absolute;left:0;top:0}
.tick{display:flex;align-items:center;gap:34px;font-size:48px;color:#4A2C3D;margin-bottom:34px}
.tick .bx{width:64px;height:64px;border:5px solid #4A2C3D;border-radius:8px;display:flex;align-items:center;justify-content:center;
 font-size:52px;font-weight:700;color:#B8956E;flex:none}
.tick b{font-weight:700;text-transform:uppercase;letter-spacing:.04em}
.foot{position:absolute;left:0;right:0;bottom:46px;text-align:center;font-size:34px;letter-spacing:.14em;color:#8C7A82;text-transform:uppercase}
"""


def img(p):
    return 'file://' + os.path.abspath(p)


def page(body, foot=True):
    f = '<div class="foot">Way of Wealth Studio · created by a qualified financial planner</div>' if foot else ''
    return f'<html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{body}{f}</body></html>'


def title(t, sub, ty=95, size=128, sy=None, ssize=46):
    sy = sy or ty + int(size * 1.25)
    return f'<div class="t" style="top:{ty}px;font-size:{size}px">{t}</div><div class="s" style="top:{sy}px;font-size:{ssize}px">{sub}</div>'


def laptop(src, x, y, w, crop_top=0):
    sh = int((w - 68) * 0.625)
    return (f'<div class="lap" style="left:{x}px;top:{y}px;width:{w}px"><div class="lid"><div class="scr" style="height:{sh}px">'
            f'<img src="{img(src)}" style="margin-top:-{crop_top}px"></div></div><div class="base"></div></div>')


def callouts(items, color='#B8956E'):
    """items: (text, box_x, box_y, box_w, align, px, py) -> label + elbow line to (px,py)."""
    out, lines = [], []
    for it in items:
        t, x, y, w, al, px, py = it[:7]
        ey = it[7] if len(it) > 7 else y - 70
        if al == 'up':
            out.append(f'<div class="co" style="left:{x}px;top:{y}px;width:{w}px;text-align:center">{t}</div>')
            ax = x + w / 2
            lines.append(f'<polyline points="{ax},{y - 18} {ax},{ey} {px},{ey} {px},{py}" fill="none" stroke="{color}" stroke-width="5"/>'
                         f'<circle cx="{px}" cy="{py}" r="13" fill="#fff" stroke="{color}" stroke-width="6"/>')
            continue
        out.append(f'<div class="co" style="left:{x}px;top:{y}px;width:{w}px;text-align:{al}">{t}</div>')
        ax = x + w + 20 if al == 'left' and px > x + w else (x - 20 if px < x else x + w + 20)
        if al == 'right':
            ax = x + w + 24 if px > x + w else x - 24
        ay = y + 30
        lines.append(f'<polyline points="{ax},{ay} {(ax + px) / 2},{ay} {(ax + px) / 2},{py} {px},{py}" fill="none" stroke="{color}" stroke-width="5"/>'
                     f'<circle cx="{px}" cy="{py}" r="13" fill="#fff" stroke="{color}" stroke-width="6"/>')
    return f'<svg width="{W}" height="{H}">{"".join(lines)}</svg>' + ''.join(out)


def render(pages, outdir):
    os.makedirs(outdir, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=1)
        for i, h in enumerate(pages, 1):
            fn = os.path.join(outdir, f'_{i:02d}.html')
            open(fn, 'w').write(h)
            pg.goto('file://' + os.path.abspath(fn)); pg.wait_for_timeout(350)
            pg.screenshot(path=os.path.join(outdir, f'{i:02d}.png'))
            os.remove(fn)
        b.close()
    from PIL import Image
    for i in range(1, len(pages) + 1):
        Image.open(os.path.join(outdir, f'{i:02d}.png')).convert('RGB').save(os.path.join(outdir, f'{i:02d}.jpg'), quality=90)
        os.remove(os.path.join(outdir, f'{i:02d}.png'))
