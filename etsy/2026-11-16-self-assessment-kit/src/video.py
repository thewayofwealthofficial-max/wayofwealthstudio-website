"""In-use listing video (1080x1080, silent, H.264 crf 24): a new payment typed into the Income Log of the real
EXAMPLE file, then the Dashboard total updating. Frames come from video_stages.py renders (LibreOffice recalculated).
Run after photos.py and video_stages.py:  SA_WORK=/some/tmp python3 video.py"""
import os, sys, shutil, subprocess
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import WORK, KIT, pf, pfi, pfr, INK, GOLD_D, SHEETBG, sparkle, spaced

OUT = 1080; FPS = 30
ST = os.path.join(WORK, 'stages')
MP4 = os.path.join(KIT, 'UK Self Assessment 2025-26 Deadline Kit - video.mp4')
CREAM = (250, 242, 233)
SX0, SY0, SW = 40, 236, 1000          # screen card: left, top, width (height follows the window)
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


# ---- income log geometry (300 dpi, measured from the grid lines)
rt = lambda k: 439.6 + (k - 9) * 41.72          # top of sheet row k
COLS = {'B': 105, 'C': 322, 'D': 694, 'E': 1314, 'F': 1531, 'G': 1933, 'end': 2336}


def log_view(stage, c0, c1, first=33, last=41, row=40):
    """header row + rows first..last, columns c0..c1 (cut on grid lines only, so no text is cut)"""
    im = L(f's{stage}-p4.png'); x0, x1 = COLS[c0], COLS[c1]
    head = im.crop((x0, round(rt(8)) + 2, x1, round(rt(9))))
    body = im.crop((x0, round(rt(first)), x1, round(rt(last + 1))))
    c = Image.new('RGB', (x1 - x0, head.height + body.height), SHEETBG); c.paste(head, (0, 0)); c.paste(body, (0, head.height))
    new = (0, head.height + rt(row) - rt(first), x1 - x0, head.height + rt(row + 1) - rt(first))
    return c, new


def dash_view(stage, box):
    """box in 300-dpi page coords; the Dashboard page is rendered at 600 dpi for sharp zooms"""
    return L(f's{stage}-p1.png').crop(tuple(2 * v for v in box))


def frame(src, title, sub, hl=None):
    """src image scaled to the screen width; hl = box in src pixels outlined in gold (drawn on row/card edges)"""
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
    """fade through plain cream, never a dark wash"""
    c = Image.new('RGB', (OUT, OUT), CREAM); xfade(c, sec / 2); xfade(img, sec / 2)
def zoom(img, sec, z0, z1):
    n = int(sec * FPS)
    for k in range(n):
        z = z0 + (z1 - z0) * k / max(1, n - 1); c = OUT / z; o = (OUT - c) / 2
        fr.append(img.crop((o, o, o + c, o + c)).resize((OUT, OUT), Image.LANCZOS))


cover = Image.open(os.path.join(KIT, 'photos', '01.jpg')).convert('RGB').resize((OUT, OUT), Image.LANCZOS)

# 1) cover
zoom(cover, 1.0, 1.0, 1.03)
# 2) typing the new row: date + client
T1 = 'Add a payment'
v, r41 = log_view(0, 'B', 'D')
cream_fade(frame(v, T1, 'A new client paid you on 28 Mar 2026', r41), 0.5); hold(fr[-1], 0.5)
for s, sub, sec in [(1, 'Type the date it arrived', 0.7), (2, 'Then the client’s name', 0.45), (3, 'Then the client’s name', 0.45),
                    (4, 'Then the client’s name', 0.8)]:
    v, r41 = log_view(s, 'B', 'D'); hold(frame(v, T1, sub, r41), sec)
# 3) what for, then amount + type (hard cuts: never two layers of text)
v, r41 = log_view(5, 'D', 'E'); hold(frame(v, T1, 'What the work was for', r41), 1.2)
v, r41 = log_view(5, 'E', 'G'); hold(frame(v, T1, 'Then the amount', r41), 0.5)
v, r41 = log_view(6, 'E', 'G'); hold(frame(v, T1, '£2,000, counted for 2025/26', r41), 1.3)
# 4) dashboard before / after, zoomed so labels are ~30 px (hero label + figure only, cut above the next text line)
T2 = 'Your tax bill updates'
HW = (94, 276, 500, 420)
HB = tuple(2 * v for v in (100 - 94, 334 - 276, 496 - 94, 416 - 276))   # gold box round the total (600-dpi px), clear of the label
cream_fade(frame(dash_view(0, HW), T2, 'Before: £8,549 due by 31 Jan 2027', HB), 0.4); hold(fr[-1], 1.0)
hold(frame(dash_view(6, HW), T2, 'After: £9,329, worked out for you', HB), 1.7)
IT = (846, 434, 1126, 578)
hold(frame(dash_view(6, IT), T2, 'Income Tax goes up to £4,784'), 1.0)
# 5) what to pay
T3 = 'Know what to pay by 31 Jan'
hold(frame(dash_view(6, HW), T3, 'Then £3,110 more by 31 Jul 2027', HB), 1.5)
# 6) cover again
cream_fade(cover, 0.5); zoom(cover, 1.0, 1.03, 1.0)

print('seconds', len(fr) / FPS)
FD = os.path.join(WORK, 'vframes'); shutil.rmtree(FD, ignore_errors=True); os.makedirs(FD)
for i, im in enumerate(fr): im.save(f'{FD}/{i:04d}.png')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{FD}/%04d.png', '-c:v', 'libx264', '-preset', 'slow',
                '-crf', '24', '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart', MP4], check=True)
# contact sheet for review
idx = list(range(0, len(fr), max(1, len(fr) // 24)))[:24]
cs = Image.new('RGB', (6 * 360, 4 * 360), 'white')
for j, i in enumerate(idx): cs.paste(fr[i].resize((360, 360)), ((j % 6) * 360, (j // 6) * 360))
cs.save(os.path.join(WORK, 'video_contact.jpg'), quality=85)
print(MP4, os.path.getsize(MP4))
