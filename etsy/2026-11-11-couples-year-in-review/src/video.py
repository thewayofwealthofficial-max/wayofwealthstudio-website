"""Listing video from real recalculated stage renders (stages.py): numbers and goals typed in, totals and dashboard update."""
import os, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out'))
W, H, FPS = 1080, 1350, 30
FD = '/usr/share/fonts/truetype/'
F = lambda f, s: ImageFont.truetype(FD + f, s)
SERB = 'crosextra/Caladea-Bold.ttf'; SM = 'google-fonts/Poppins-Medium.ttf'
CREAM = (245, 240, 232); CHAR = (61, 61, 61); DSAGE = (143, 165, 133); SAGE = (184, 197, 176); GOLD = (184, 149, 110)
img = lambda p: Image.open(p).convert('RGB')
X = lambda n: img(f'hi/xc-{n:02d}.png')
STG = lambda k, t: img(f'stg/{k}_{t}.png')


def base(caption):
    im = Image.new('RGB', (W, H), CREAM); d = ImageDraw.Draw(im)
    d.text((W / 2, 50), caption, font=F(SERB, 62), fill=CHAR, anchor='ma')
    return im


def put(im, src, box, y, w=1000, zoom=1.0):
    c = src.crop(box)
    pw = int(w * zoom); ph = int(c.height * pw / c.width)
    c = c.resize((pw, ph), Image.LANCZOS).crop((0, 0, w, ph))
    x = (W - w) // 2
    ImageDraw.Draw(im).rounded_rectangle([x - 5, y - 5, x + w + 5, y + ph + 5], radius=12, fill=(225, 216, 200))
    im.paste(c, (x, y))
    return y + ph


def cursor(im, x, y):
    d = ImageDraw.Draw(im)
    pts = [(x, y), (x, y + 44), (x + 12, y + 33), (x + 21, y + 52), (x + 29, y + 48), (x + 20, y + 30), (x + 36, y + 30)]
    d.polygon(pts, fill=(30, 30, 30), outline=(255, 255, 255))


def label(im, text, y):
    ImageDraw.Draw(im).text((W / 2, y), text, font=F(SM, 34), fill=DSAGE, anchor='ma')


NBOX = (40, 215, 1060, 760)        # Year in Numbers: Month .. Saved, incl. Year total row
GBOX = (40, 215, 1200, 860)        # Goals table + reality check
DBOX1 = (20, 140, 1290, 560)       # Dashboard: headline cards + tables (left part)
DBOX2 = (20, 255, 1290, 630)


def scene_dash(t):
    im = base('Your money year, together')
    put(im, X(1), (0, 0, 1399, 1729), 140, 1000, 1.0 + 0.05 * t)
    return im


def scene_numbers(t):
    stages = ['m0', 'm3', 'm6', 'm9', 'm12']
    i = min(4, int(t * 5))
    k = stages[i]
    im = base('Type in each month...')
    s = 1000 / (NBOX[2] - NBOX[0])
    yb = put(im, STG(k, 'p'), NBOX, 140)
    rows = int(k[1:])
    if rows < 12:
        cursor(im, int(40 + (310 - NBOX[0]) * s), int(140 + (285 + 32.5 * rows + 8 - NBOX[1]) * s))
    label(im, '...the totals and dashboard update', yb + 22)
    put(im, STG(k, 'd'), DBOX1, yb + 80)
    return im


def scene_spend(t):
    im = base('Decide what was worth it')
    put(im, X(5), (40, 215, 1060, 1010), 140, 1000, 1.0 + 0.04 * t)
    label(im, 'Protect what matters, cut what didn\'t', 1240)
    return im


def scene_goals(t):
    stages = ['g0', 'g1', 'g2', 'g3', 'g4']
    i = min(4, int(t * 5)); k = stages[i]
    im = base('Set goals that fit')
    s = 1000 / (GBOX[2] - GBOX[0])
    yb = put(im, STG(k, 'g' if False else 'p'), GBOX, 140)
    n = int(k[1:])
    if n < 4:
        cursor(im, int(40 + (330 - GBOX[0]) * s), int(140 + (300 + 41 * n + 10 - GBOX[1]) * s))
    label(im, 'Monthly amount and reality check, worked out', yb + 22)
    put(im, STG(k, 'd'), DBOX2, yb + 80)
    return im


def scene_ci(t):
    im = base('Check in every month')
    ci = X(9)
    y = put(im, ci, (40, 215, 1060, 640), 140)
    put(im, ci, (40, 650, 1530, 1060), y + 30, 1000, 1.0)
    return im


def endcard(t):
    im = Image.new('RGB', (W, H), SAGE); d = ImageDraw.Draw(im)
    d.text((W / 2, 400), 'Couples Money', font=F(SERB, 96), fill=CHAR, anchor='ma')
    d.text((W / 2, 510), 'Year in Review', font=F(SERB, 96), fill=CHAR, anchor='ma')
    d.text((W / 2, 680), '+ goals and monthly check-ins', font=F(SM, 46), fill=CHAR, anchor='ma')
    d.text((W / 2, 750), 'Google Sheets, Excel + printable', font=F(SM, 46), fill=CHAR, anchor='ma')
    d.text((W / 2, 1150), 'Way of Wealth Studio', font=F(SM, 40), fill=(80, 80, 80), anchor='ma')
    return im


scenes = [(2.0, scene_dash), (4.0, scene_numbers), (2.0, scene_spend), (3.0, scene_goals), (2.0, scene_ci), (1.8, endcard)]
shutil.rmtree('vf', ignore_errors=True); os.makedirs('vf')
n = 0
for dur, fn in scenes:
    fr = int(dur * FPS)
    for i in range(fr):
        fn(i / max(1, fr - 1)).save(f'vf/{n:04d}.jpg', quality=88); n += 1
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', 'vf/%04d.jpg', '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p', '-crf', '21', '-movflags', '+faststart', 'video.mp4'], check=True)
print(n / FPS, 'seconds')
