"""In-use listing video (1080x1080, silent, H.264 crf 24): a $3,000 contract-labor cost typed into the Deductions log of
the real EXAMPLE file, then the next quarterly estimated tax payment and the total tax updating on the Dashboard.
Frames come from video_stages.py renders (LibreOffice recalculated). Run after photos.py and video_stages.py."""
import os, sys, shutil, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import WORK, KIT, pf, pfi, pfr, INK, GOLD_D, SHEETBG, sparkle, spaced

OUT = 1080; FPS = 30
ST = os.path.join(WORK, 'stages')
MP4 = os.path.join(KIT, 'US Self-Employed Tax Tracker - video.mp4')
CREAM = (250, 242, 233)
SX0, SY0, SW = 40, 236, 1000
AREA_BOTTOM = 985
CAP = 2.3          # max zoom of a 300-dpi render
FRAME_SCALE = []


def bg():
    im = Image.new('RGB', (OUT, OUT)); d = ImageDraw.Draw(im)
    for y in range(OUT):
        t = y / OUT; d.line([(0, y), (OUT, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip((252, 244, 236), (244, 232, 216))))
    f = pfr(44); w = spaced(d, OUT / 2, 1012, 'WAY OF WEALTH STUDIO', f, GOLD_D, 6)
    for sx in (OUT / 2 - w / 2 - 34, OUT / 2 + w / 2 + 34): sparkle(im, sx, 1040, 13)
    return im


BG = bg()
_c = {}
def L(name):
    if name not in _c: _c[name] = Image.open(os.path.join(ST, name)).convert('RGB')
    return _c[name]


# ---- deductions geometry, measured from the input-cell grid lines of the 300-dpi render
def grid(img, x=300, y=300):
    a = np.array(img).astype(int)
    hit = lambda p: abs(p[0] - 230) < 12 and abs(p[1] - 217) < 12 and abs(p[2] - 181) < 14
    def groups(vals):
        g = []
        for v in vals:
            if not g or v - g[-1][-1] > 2: g.append([v])
            else: g[-1].append(v)
        return [round(sum(x) / len(x)) for x in g]
    return groups([yy for yy in range(a.shape[0]) if hit(a[yy, x])]), groups([xx for xx in range(a.shape[1]) if hit(a[y, xx])])


RY, CX = grid(L('s6-ded.png'))
HEAD = (RY[0] - 64, RY[0])            # header row band
NEW = 13                              # the new row is the 14th printed row (rows ROW-13 .. ROW+2)
COLS = {'B': CX[0], 'C': CX[1], 'D': CX[2], 'E': CX[3], 'F': CX[4], 'G': CX[5], 'H': CX[6], 'I': 2418, 'J': 2595, 'K': 2754, 'end': 3090}


def text_right(x0, x1):
    """right edge of the text inside columns x0..x1 (measured on the final stage, header + rows), so blank cell space
    can be trimmed without cutting any word"""
    a = np.array(L('s6-ded.png').crop((x0, HEAD[0], x1, RY[16]))).astype(int)
    dark = (a.max(2) < 170).any(0)
    xs = np.where(dark)[0]
    return x0 + (int(xs.max()) + 12 if len(xs) else x1 - x0)


def ded_view(stage, groups, first=9, last=15, trim=False, header=True):
    """groups: [(c0, c1), ...] whole-column ranges placed side by side; trim = drop blank space right of the text"""
    im = L(f's{stage}-ded.png'); parts = []
    for c0, c1 in groups:
        x0, x1 = COLS[c0], COLS[c1]
        if trim: x1 = min(x1, text_right(x0, x1))
        head = im.crop((x0, HEAD[0], x1, HEAD[1])) if header else Image.new('RGB', (x1 - x0, 24), SHEETBG)
        body = im.crop((x0, RY[first], x1, RY[last + 1]))
        p = Image.new('RGB', (x1 - x0, head.height + body.height), SHEETBG); p.paste(head, (0, 0)); p.paste(body, (0, head.height))
        parts.append(p)
    Mg = 24     # cream margin each side (40+ px in the frame at these zooms): nothing touches the frame edge
    W = sum(p.width for p in parts) + 2 * Mg
    c = Image.new('RGB', (W, parts[0].height), SHEETBG); x = Mg
    for p in parts: c.paste(p, (x, 0)); x += p.width
    hh = parts[0].height - (RY[last + 1] - RY[first])
    new = (Mg - 22, hh + RY[NEW] - RY[first], W - Mg + 22, hh + RY[NEW + 1] - RY[first])   # box sits in the margin
    return c, new


def dash_view(stage, box):
    return L(f's{stage}-dash.png').crop(tuple(4 * v for v in box))    # 600-dpi page, box in 150-dpi units


def frame(src, title, sub, hl=None):
    im = BG.copy(); d = ImageDraw.Draw(im)
    sc = min(SW / src.width, CAP, (AREA_BOTTOM - SY0) / src.height); vw = round(src.width * sc); h = round(src.height * sc)
    X0 = (OUT - vw) // 2
    top = SY0 + max(0, (AREA_BOTTOM - SY0 - h) // 2)
    view = src.resize((vw, h), Image.LANCZOS)
    sh = Image.new('L', (OUT, OUT), 0); ImageDraw.Draw(sh).rounded_rectangle((X0, top + 14, X0 + vw, top + h + 14), 22, fill=90)
    im.paste((150, 115, 70), (0, 0), sh.filter(ImageFilter.GaussianBlur(18)))
    m = Image.new('L', view.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, vw - 1, h - 1), 20, fill=255)
    im.paste(view, (X0, top), m)
    d.rounded_rectangle((X0 - 1, top - 1, X0 + vw + 1, top + h + 1), 21, outline=(214, 192, 160), width=2)
    FRAME_SCALE.append(sc)
    if hl:
        a, b, c, e = hl
        d.rounded_rectangle((X0 + a * sc + 4, top + b * sc - 2, X0 + c * sc - 4, top + e * sc + 2), 8, outline=(184, 140, 78), width=6)
    for txt, f, yy, col in [(title, pf(62), 50, INK), (sub, pfi(50), 136, GOLD_D)]:
        w = d.textlength(txt, font=f); assert w < OUT - 60, txt
        d.text(((OUT - w) / 2, yy), txt, font=f, fill=col)
    return im


fr = []
def hold(img, sec): fr.extend([img] * int(round(sec * FPS)))
def xfade(img, sec=0.25):
    a = fr[-1]; n = int(sec * FPS); fr.extend(Image.blend(a, img, k / n) for k in range(1, n + 1))
def cream_fade(img, sec=0.5):
    c = Image.new('RGB', (OUT, OUT), CREAM); xfade(c, sec / 2); xfade(img, sec / 2)
def zoom(img, sec, z0, z1):
    n = int(sec * FPS)
    for k in range(n):
        z = z0 + (z1 - z0) * k / max(1, n - 1); c = OUT / z; o = (OUT - c) / 2
        fr.append(img.crop((o, o, o + c, o + c)).resize((OUT, OUT), Image.LANCZOS))


cover = Image.open(os.path.join(KIT, 'photos', '01.jpg')).convert('RGB').resize((OUT, OUT), Image.LANCZOS)
FRAMES = []          # (label, image) of every steady frame, for the cap-height check
def show(img, sec, label):
    FRAMES.append((label, img)); hold(img, sec)


zoom(cover, 1.3, 1.0, 1.03)
T1 = 'Log a business cost'
# one or two whole columns at a time, header kept only where its small capitals still reach 30 px
v, r = ded_view(0, [('B', 'C')]); show(frame(v, T1, 'A new bill from a freelancer', r), 0.7, 'date blank')
v, r = ded_view(1, [('B', 'C')]); show(frame(v, T1, 'Type the date you paid', r), 0.7, 'date typed')
v, r = ded_view(2, [('C', 'D')]); show(frame(v, T1, 'Who you paid', r), 0.35, 'paid to 1')
v, r = ded_view(3, [('C', 'D')]); show(frame(v, T1, 'Who you paid', r), 0.55, 'paid to 2')
v, r = ded_view(4, [('D', 'E')]); show(frame(v, T1, 'And what it was for', r), 1.1, 'what for')
v, r = ded_view(4, [('B', 'C'), ('E', 'F')]); show(frame(v, T1, 'Then the amount', r), 0.45, 'amount blank')
v, r = ded_view(5, [('B', 'C'), ('E', 'F')]); show(frame(v, T1, 'Then the amount: $3,000', r), 0.8, 'amount typed')
# Schedule C step: the single row being typed, category column only
v, r = ded_view(5, [('F', 'G')], first=NEW, last=NEW, trim=True, header=False); show(frame(v, T1, 'Now pick the Schedule C category', r), 0.6, 'category blank')
v, r = ded_view(6, [('F', 'G')], first=NEW, last=NEW, trim=True, header=False); show(frame(v, T1, 'Line 11: contract labor', r), 1.0, 'category typed')
v, r = ded_view(6, [('I', 'K')]); show(frame(v, 'Counted for you', 'Deductible amount and line number', r), 0.8, 'deductible + line')
v, r = ded_view(6, [('K', 'end')], trim=True); show(frame(v, 'Counted for you', 'Every counted row gets a check', r), 0.7, 'check')
# dashboard: the payment card alone (label + amount), hard cuts
T2 = 'Your quarterly tax updates'
HERO = (47, 136, 240, 206)
HB = (8, 100, 600, 262)
show(frame(dash_view(0, HERO), T2, 'Before: $2,800 due Jan 15, 2027', HB), 1.2, 'payment before')
show(frame(dash_view(6, HERO), T2, 'After: $2,644, worked out for you', HB), 1.8, 'payment after')
K4 = (610, 217, 752, 289)
show(frame(dash_view(6, K4), 'Less tax for the year', 'Total tax estimate: $16,783 down to $15,952', (0, 92, 568, 200)), 1.3, 'total tax')
zoom(cover, 1.2, 1.03, 1.0)

print('seconds', len(fr) / FPS)
import capmeasure
worst = []
for lab, img in FRAMES:
    caps = capmeasure.lines_cap(img, (0, 30, OUT, OUT))
    m = min(c for _, c in caps); worst.append((m, lab))
    print(f'  {lab:18s} smallest cap height {m:5.1f} px   (lines: {[c for _, c in caps]})')
print('MINIMUM cap height over all steady frames (titles, captions, tables, cards, footer):', min(worst))
print('table zoom per frame (src 300 dpi -> frame):', sorted(set(round(x, 2) for x in FRAME_SCALE)))
_a = np.array(L('s6-ded.png').crop((COLS['E'], RY[NEW], COLS['F'], RY[NEW + 1]))).astype(int); _r = np.where((_a.max(2) < 140).any(1))[0]
print('digit height of 3,000.00 at 300 dpi:', _r.max() - _r.min() + 1, 'px')
FD = os.path.join(WORK, 'vframes'); shutil.rmtree(FD, ignore_errors=True); os.makedirs(FD)
for i, im in enumerate(fr): im.save(f'{FD}/{i:04d}.png')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{FD}/%04d.png', '-c:v', 'libx264', '-preset', 'slow',
                '-crf', '24', '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart', MP4], check=True)
idx = list(range(0, len(fr), max(1, len(fr) // 24)))[:24]
cs = Image.new('RGB', (6 * 360, 4 * 360), 'white')
for j, i in enumerate(idx): cs.paste(fr[i].resize((360, 360)), ((j % 6) * 360, (j // 6) * 360))
cs.save(os.path.join(KIT, 'review', 'video_contact.jpg'), quality=85)
print(MP4, os.path.getsize(MP4))
