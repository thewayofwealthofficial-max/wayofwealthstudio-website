"""In-use listing video (1080x1080, silent, H.264 crf 26): a new appointment with a cash tip typed into the Client Log of the
real EXAMPLE file, then the Dashboard profit and tips updating. Frames come from video_stages.py renders (LibreOffice recalculated).
Run after photos.py and video_stages.py:  python3 video.py"""
import os, sys, shutil, subprocess
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import WORK, KIT, pf, pfi, pfr, INK, GOLD_D, SHEETBG, sparkle, spaced

OUT = 1080; FPS = 30
ST = os.path.join(WORK, 'stages')
MP4 = os.path.join(KIT, 'Nail Tech Income Expense Tracker - video.mp4')
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
def Ld(name):
    if name not in _c: _c[name] = Image.open(os.path.join(ST, name)).convert('RGB')
    return _c[name]


# client log geometry in 150-dpi units (page rendered at 300 dpi = x2), measured from the stage render
rt = lambda k: 322 + k * 28.75          # top of visible data row k (0 = first visible row, 11 = the new row)
HEAD = (285, 320)
COLS = {'date': 62, 'client': 200, 'service': 392, 'price': 625, 'tip': 732, 'paid': 828, 'retail': 977, 'total': 1083, 'end': 1200, 'paidend': 915}


def log_view(stage, spans, first=7, last=11, row=11):
    """header + rows first..last for the column spans [(c0,c1),...] glued side by side; returns image + new-row box"""
    im = Ld(f's{stage}-p4.png'); parts = []
    for c0, c1 in spans:
        x0, x1 = 2 * COLS[c0], 2 * COLS[c1]
        head = im.crop((x0, 2 * HEAD[0], x1, 2 * HEAD[1]))
        body = im.crop((x0, round(2 * rt(first)), x1, round(2 * rt(last + 1))))
        p = Image.new('RGB', (x1 - x0, head.height + body.height), SHEETBG); p.paste(head, (0, 0)); p.paste(body, (0, head.height))
        parts.append(p)
    W = sum(p.width for p in parts); c = Image.new('RGB', (W, parts[0].height), SHEETBG); x = 0
    for p in parts: c.paste(p, (x, 0)); x += p.width
    hh = 2 * (HEAD[1] - HEAD[0])
    new = (0, hh + 2 * (rt(row) - rt(first)), W, hh + 2 * (rt(row + 1) - rt(first)))
    return c, new


def full_view(stage):
    return Ld(f's{stage}-p4.png').crop((2 * 40, 2 * 40, 2 * 1210, 2 * 690))


def dash_view(stage, box):
    """box in 150-dpi units; the Dashboard is rendered at 600 dpi (x4)"""
    return Ld(f's{stage}-p1.png').crop(tuple(4 * v for v in box))


def frame(src, title, sub, hl=None):
    im = BG.copy(); d = ImageDraw.Draw(im)
    sc = SW / src.width; h = round(src.height * sc)
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
    cc = Image.new('RGB', (OUT, OUT), CREAM); xfade(cc, sec / 2); xfade(img, sec / 2)
def zoom(img, sec, z0, z1):
    n = int(sec * FPS)
    for k in range(n):
        z = z0 + (z1 - z0) * k / max(1, n - 1); cc = OUT / z; o = (OUT - cc) / 2
        fr.append(img.crop((o, o, o + cc, o + cc)).resize((OUT, OUT), Image.LANCZOS))


cover = Image.open(os.path.join(KIT, 'photos', '01.jpg')).convert('RGB').resize((OUT, OUT), Image.LANCZOS)
T1 = 'Log an appointment'
A = [('date', 'service')]
# 1) cover 1.3 s
zoom(cover, 1.3, 1.0, 1.03)
# 2) full tab
cream_fade(frame(full_view(0), 'The Client Log', 'One row per appointment'), 0.4); hold(fr[-1], 0.9)
# 3) zoom to the new row + typing
v, nr = log_view(0, [('date', 'service')]); cream_fade(frame(v, T1, 'Ruby just paid for a BIAB overlay', nr), 0.3); hold(fr[-1], 0.6)
for s, sub, sec in [(1, 'Type the date', 0.6), (2, 'Then the client', 0.6)]:
    v, nr = log_view(s, [('date', 'service')]); hold(frame(v, T1, sub, nr), sec)
v, nr = log_view(3, [('client', 'price')]); hold(frame(v, T1, 'Pick the service from your menu', nr), 0.9)
v, nr = log_view(3, [('price', 'paidend'), ('total', 'end')]); hold(frame(v, T1, 'Then the price', nr), 0.5)
for s, sub, sec in [(4, 'Then the price', 0.7), (5, 'Add the tip', 0.8), (6, 'Paid in cash: total adds itself', 1.3)]:
    v, nr = log_view(s, [('price', 'paidend'), ('total', 'end')]); hold(frame(v, T1, sub, nr), sec)
# 4) dashboard before / after
T2 = 'Your profit updates'
HW = (38, 115, 345, 265)
HB = tuple(4 * v for v in (48 - 38, 146 - 115, 178 - 38, 185 - 115))
cream_fade(frame(dash_view(0, HW), T2, 'Before: £16,308 profit this year', HB), 0.4); hold(fr[-1], 0.9)
hold(frame(dash_view(6, HW), T2, 'After: £16,351, worked out for you', HB), 1.4)
TW = (368, 190, 505, 262)
TB = tuple(4 * v for v in (377 - 368, 215 - 190, 430 - 368, 240 - 190))
hold(frame(dash_view(6, TW), 'Tips, card and cash', 'Cash tips now £222 of £953', TB), 1.2)
# 5) cover again
cream_fade(cover, 0.5); zoom(cover, 0.9, 1.03, 1.0)

print('seconds', len(fr) / FPS)
FD = os.path.join(WORK, 'vframes'); shutil.rmtree(FD, ignore_errors=True); os.makedirs(FD)
for i, im in enumerate(fr): im.save(f'{FD}/{i:04d}.png')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{FD}/%04d.png', '-c:v', 'libx264', '-preset', 'slow',
                '-crf', '26', '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart', MP4], check=True)
idx = list(range(0, len(fr), max(1, len(fr) // 24)))[:24]
cs = Image.new('RGB', (6 * 360, 4 * 360), 'white')
for j, i in enumerate(idx): cs.paste(fr[i].resize((360, 360)), ((j % 6) * 360, (j // 6) * 360))
cs.save(os.path.join(WORK, 'video_contact.jpg'), quality=85)
print(MP4, os.path.getsize(MP4))
