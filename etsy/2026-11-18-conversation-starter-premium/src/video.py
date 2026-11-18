"""In-use listing video (1080x1080, silent, H.264 crf 24): November's money date logged in the real EXAMPLE planner
(Money Dates tab), the Dashboard and the plain-words Check-in updating, then the Week 3 page of the 4-Week Plan PDF
being filled in. Frames come from video_stages.py renders (LibreOffice recalculated / real PDF).
Run after photos.py and video_stages.py."""
import os, sys, shutil, subprocess
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import WORK, KIT, pf, pfi, pfr, INK, GOLD_D, SHEETBG, sparkle, spaced

OUT = 1080; FPS = 30
ST = os.path.join(WORK, 'stages')
MP4 = os.path.join(KIT, 'Couples Money Conversation Kit - video.mp4')
CREAM = (250, 242, 233)
SX0, SY0, SW = 40, 236, 1000
AREA_BOTTOM = 985


def bg():
    im = Image.new('RGB', (OUT, OUT)); d = ImageDraw.Draw(im)
    for y in range(OUT):
        t = y / OUT; d.line([(0, y), (OUT, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip((252, 244, 236), (244, 232, 216))))
    f = pfr(20); spaced(d, OUT / 2, 1032, 'WAY OF WEALTH STUDIO', f, GOLD_D, 5)
    for sx in (OUT / 2 - 190, OUT / 2 + 190): sparkle(im, sx, 1045, 10)
    return im


BG = bg()
_c = {}
def L(name):
    if name not in _c: _c[name] = Image.open(os.path.join(ST, name)).convert('RGB')
    return _c[name]


# ---- Money Dates geometry (300 dpi, measured from the render)
HEAD = (1065, 1133)
rt = lambda k: 1135 + k * 96.7          # k = 0 Jul ... 4 Nov
COLS = {'B': 60, 'C': 299, 'E': 505, 'H': 915, 'J': 1155, 'K': 1274, 'L': 1394, 'Q': 2164, 'end': 2336}


def log_view(stage, cols, first=3, last=5, row=4, minw=700):
    """header + rows, built from whole columns only (cols = list of (c0, c1)) so text is never cut; narrow views are padded
    to minw so the table text is at least ~30 px high in the 1080 frame"""
    im = L(f'x{stage}-p8.png')
    head = hcat_([im.crop((COLS[a], HEAD[0], COLS[b], HEAD[1])) for a, b in cols])
    body = hcat_([im.crop((COLS[a], round(rt(first)) - 1, COLS[b], round(rt(last + 1)))) for a, b in cols])
    w = max(minw, head.width)
    c = Image.new('RGB', (w, head.height + body.height), SHEETBG)
    ox = (w - head.width) // 2
    c.paste(head, (ox, 0)); c.paste(body, (ox, head.height))
    new = (ox, head.height + rt(row) - rt(first), ox + head.width, head.height + rt(row + 1) - rt(first))
    return c, new


def hcat_(parts):
    W_ = sum(p.width for p in parts); H_ = max(p.height for p in parts); c = Image.new('RGB', (W_, H_), SHEETBG); x = 0
    for p in parts: c.paste(p, (x, 0)); x += p.width
    return c


def frame(src, title, sub, hl=None):
    # padding inside the panel so panel labels never touch its edge (highlight box coordinates shift with it)
    P = max(18, round(src.width * 0.025))
    padded = Image.new('RGB', (src.width + 2 * P, src.height + 2 * P), src.getpixel((min(4, src.width - 1), min(4, src.height - 1))))
    padded.paste(src, (P, P)); src = padded
    if hl: hl = (hl[0] + P, hl[1] + P, hl[2] + P, hl[3] + P)
    im = BG.copy(); d = ImageDraw.Draw(im)
    sc = SW / src.width; h = round(src.height * sc)
    if h > AREA_BOTTOM - SY0:
        h = AREA_BOTTOM - SY0; src = src.crop((0, 0, src.width, round(h / sc)))
    top = SY0 + max(0, (AREA_BOTTOM - SY0 - h) // 2)
    view = src.resize((SW, h), Image.LANCZOS)
    sh = Image.new('L', (OUT, OUT), 0); ImageDraw.Draw(sh).rounded_rectangle((SX0, top + 14, SX0 + SW, top + h + 14), 22, fill=90)
    im.paste((150, 115, 70), (0, 0), sh.filter(ImageFilter.GaussianBlur(18)))
    m = Image.new('L', view.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, SW - 1, h - 1), 20, fill=255)
    im.paste(view, (SX0, top), m)
    d.rounded_rectangle((SX0 - 1, top - 1, SX0 + SW + 1, top + h + 1), 21, outline=(214, 192, 160), width=2)
    if hl:
        a, b, c, e = hl
        d.rounded_rectangle((SX0 + a * sc + 4, top + b * sc, SX0 + c * sc - 4, top + e * sc), 8, outline=(184, 140, 78), width=6)
    for txt, f, yy, col in [(title, pf(62), 50, INK), (sub, pfi(40), 142, GOLD_D)]:
        w = d.textlength(txt, font=f); assert w < OUT - 60, txt
        d.text(((OUT - w) / 2, yy), txt, font=f, fill=col)
    return im


fr = []
def hold(img, sec): fr.extend([img] * int(round(sec * FPS)))
def xfade(img, sec=0.25):
    a = fr[-1]; n = int(sec * FPS); fr.extend(Image.blend(a, img, k / n) for k in range(1, n + 1))
def cream_fade(img, sec=0.5):
    fr.append(img)   # hard cut: never a blank frame, never two layers of text
def zoom(img, sec, z0, z1):
    n = int(sec * FPS)
    for k in range(n):
        z = z0 + (z1 - z0) * k / max(1, n - 1); c = OUT / z; o = (OUT - c) / 2
        fr.append(img.crop((o, o, o + c, o + c)).resize((OUT, OUT), Image.LANCZOS))


cover = Image.open(os.path.join(KIT, 'photos', '01.jpg')).convert('RGB').resize((OUT, OUT), Image.LANCZOS)
zoom(cover, 1.3, 1.0, 1.03)
# 1) the full Money Dates tab, then the November row being typed
T1 = 'Log your money date'
full = L('x0-p8.png').crop((40, 100, 2360, 1720))
cream_fade(frame(full, T1, 'Money Dates tab: one row per date'), 0.4); hold(fr[-1], 0.5)
DATECOLS = [('B', 'C'), ('C', 'E')]; CARDCOLS = [('B', 'C'), ('H', 'J')]; SCORECOLS = [('B', 'C'), ('H', 'J'), ('J', 'L')]
v, r = log_view(0, DATECOLS); hold(frame(v, T1, 'November: still to do', r), 0.6)
v, r = log_view(1, DATECOLS); hold(frame(v, T1, 'The date you sat down', r), 0.6)
v, r = log_view(2, CARDCOLS); hold(frame(v, T1, 'Which cards you pulled', r), 0.8)
v, r = log_view(3, SCORECOLS); hold(frame(v, T1, 'Card 2.1: how it felt, 1 to 10', r), 0.9)
v, r = log_view(4, [('L', 'Q')], minw=0); hold(frame(v, T1, 'One thing you agreed', r), 1.2)
# 2) dashboard before / after
T2 = 'The Dashboard updates'
def dv(s):
    """the two cards that change (money dates done, comfort score), stacked so the labels read at phone size"""
    im = L(f'x{s}-p1.png'); a, b = im.crop((90, 708, 400, 882)), im.crop((474, 708, 784, 882))
    w = 540; c = Image.new('RGB', (w, a.height + b.height + 30), SHEETBG)
    c.paste(a, ((w - a.width) // 2, 0)); c.paste(b, ((w - b.width) // 2, a.height + 30)); return c
HB = (60, 0, 480, 378)
cream_fade(frame(dv(0), T2, 'Before: 4 dates, no score yet', HB), 0.3); hold(fr[-1], 0.7)
hold(frame(dv(4), T2, 'After: 5 of 12, comfort 7.5 out of 10', HB), 1.6)
# 3) plain-words summary
T3 = 'Your month in plain words'
cream_fade(frame(L('x4-p9.png').crop((92, 432, 1014, 986)), T3, 'Written by formulas from your numbers'), 0.3); hold(fr[-1], 1.7)
# 4) the PDF: week 3 being filled in
T4 = 'Fill in the money date plan'
pv = lambda s, y0, y1: L(f'd{s}-p5.png').crop((170, y0, 1010, y1))
cream_fade(frame(pv(0, 1960, 2330), T4, 'Week 3: shared goals'), 0.3); hold(fr[-1], 0.4)
for s, sec in [(1, 0.35), (2, 0.35), (3, 0.6)]:
    hold(frame(pv(s, 1960, 2330), T4, 'Type in the boxes, or print it'), sec)
hold(frame(pv(4, 2380, 2640), T4, 'One thing you agree to this week'), 1.1)
# 5) cover again
cream_fade(cover, 0.4); zoom(cover, 0.7, 1.03, 1.0)

print('seconds', len(fr) / FPS)
FD = os.path.join(WORK, 'vframes'); shutil.rmtree(FD, ignore_errors=True); os.makedirs(FD)
for i, im in enumerate(fr): im.save(f'{FD}/{i:04d}.png')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{FD}/%04d.png', '-c:v', 'libx264', '-preset', 'slow',
                '-crf', '24', '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart', MP4], check=True)
idx = list(range(0, len(fr), max(1, len(fr) // 24)))[:24]
cs = Image.new('RGB', (6 * 360, 4 * 360), 'white')
for j, i in enumerate(idx): cs.paste(fr[i].resize((360, 360)), ((j % 6) * 360, (j // 6) * 360))
cs.save(os.path.join(WORK, 'video_contact.jpg'), quality=85)
print(MP4, os.path.getsize(MP4))
