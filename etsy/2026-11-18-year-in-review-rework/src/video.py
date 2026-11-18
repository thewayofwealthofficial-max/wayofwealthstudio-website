"""In-use listing video (1080x1080, silent, H.264 crf 24, ~14.5 s): a couple's April 2027 typed into the 2027 Check-ins tab of
the real EXAMPLE file, then the Monthly Money Check-in sentence and the Dashboard updating. Frames come from video_stages.py
renders (LibreOffice recalculated). Run after photos.py and video_stages.py:  python3 video.py"""
import os, sys, shutil, subprocess
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import WORK, KIT, pf, pfi, pfr, INK, GOLD_D, SHEETBG, sparkle, spaced

OUT = 1080; FPS = 30
ST = os.path.join(WORK, 'stages')
MP4 = os.path.join(KIT, 'Couples Money Year in Review and 2027 Goals - video.mp4')
CREAM = (250, 242, 233)
SX0, SY0, SW = 40, 236, 1000
AREA_BOTTOM = 990


def bg():
    im = Image.new('RGB', (OUT, OUT)); d = ImageDraw.Draw(im)
    for y in range(OUT):
        t = y / OUT; d.line([(0, y), (OUT, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip((252, 244, 236), (244, 232, 216))))
    f = pfr(20); spaced(d, OUT / 2, 1032, 'WAY OF WEALTH STUDIO', f, GOLD_D, 5)
    for sx in (OUT / 2 - 190, OUT / 2 + 190): sparkle(im, sx, 1045, 10)
    return im


BG = bg()
_c = {}
def Lp(name):
    if name not in _c: _c[name] = Image.open(os.path.join(ST, name)).convert('RGB')
    return _c[name]


# ---- 2027 Check-ins geometry (300 dpi, measured from the grid lines)
ROW = {8: 420, 9: 480, 10: 540, 11: 601, 12: 661, 13: 723, 14: 784}
for r in range(15, 25): ROW[r] = 784 + (r - 14) * 60.6
for r in range(25, 28): ROW[r] = ROW[24] + (r - 24) * 61
ROW[28] = 1636
for r in range(29, 37): ROW[r] = 1636 + (r - 28) * 60.6
COL = {'B': 113, 'C': 580, 'D': 753, 'E': 898, 'F': 1044, 'G': 1189, 'H': 1335, 'I': 1480}


def grid(stage, r0, r1, row_hl=None):
    """header row 8 + rows r0..r1, columns B, then Mar (F), Apr (G), May (H). Gold box on the April cell of row_hl."""
    im = Lp(f's{stage}-p9.png')
    parts = [(COL['B'], COL['C']), (COL['F'], COL['I'])]
    def strip(y0, y1):
        ps = [im.crop((a, round(y0), b, round(y1))) for a, b in parts]
        c = Image.new('RGB', (sum(p.width for p in ps), ps[0].height), SHEETBG); x = 0
        for p in ps: c.paste(p, (x, 0)); x += p.width
        return c
    head = strip(ROW[8] + 4, ROW[9]); body = strip(ROW[r0], ROW[r1 + 1])
    c = Image.new('RGB', (head.width, head.height + body.height), SHEETBG); c.paste(head, (0, 0)); c.paste(body, (0, head.height))
    hl = None
    if row_hl:
        ax = (COL['C'] - COL['B']) + (COL['G'] - COL['F'])
        if isinstance(row_hl, tuple):
            ra, rb = row_hl
        else:
            ra = rb = row_hl
        hl = (ax + 6, head.height + ROW[ra] - ROW[r0], ax + (COL['H'] - COL['G']) + 14, head.height + ROW[rb + 1] - ROW[r0])
    return c, hl


def frame(src, title, sub, hl=None, z=1.0, anchor=(0, 0)):
    """src image scaled to the screen width (optionally zoomed z about the top-left anchor fraction); hl = gold box in src px"""
    im = BG.copy(); d = ImageDraw.Draw(im)
    if z > 1:
        cw, ch = src.width / z, src.height / z
        x0 = (src.width - cw) * anchor[0]; y0 = (src.height - ch) * anchor[1]
        src = src.crop((round(x0), round(y0), round(x0 + cw), round(y0 + ch)))
        if hl: hl = tuple((v - (x0 if i % 2 == 0 else y0)) for i, v in enumerate(hl))
    sc = SW / src.width; h = round(src.height * sc)
    if h > AREA_BOTTOM - SY0:
        sc = (AREA_BOTTOM - SY0) / src.height; h = AREA_BOTTOM - SY0
    w = round(src.width * sc); x = (OUT - w) // 2
    top = SY0 + max(0, (AREA_BOTTOM - SY0 - h) // 2)
    view = src.resize((w, h), Image.LANCZOS)
    sh = Image.new('L', (OUT, OUT), 0); ImageDraw.Draw(sh).rounded_rectangle((x, top + 14, x + w, top + h + 14), 22, fill=90)
    im.paste((150, 115, 70), (0, 0), sh.filter(ImageFilter.GaussianBlur(18)))
    m = Image.new('L', view.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), 20, fill=255)
    im.paste(view, (x, top), m)
    d.rounded_rectangle((x - 1, top - 1, x + w + 1, top + h + 1), 21, outline=(214, 192, 160), width=2)
    if hl:
        a, b, c, e = hl
        d.rounded_rectangle((x + a * sc + 3, top + b * sc, x + c * sc - 3, top + e * sc), 8, outline=(184, 140, 78), width=6)
    for txt, f, yy, col in [(title, pf(62), 50, INK), (sub, pfi(40), 142, GOLD_D)]:
        tw_ = d.textlength(txt, font=f); assert tw_ < OUT - 60, txt
        d.text(((OUT - tw_) / 2, yy), txt, font=f, fill=col)
    return im


fr = []
def hold(img, sec): fr.extend([img] * int(round(sec * FPS)))
def xfade(img, sec=0.25):
    a = fr[-1]; n = int(sec * FPS); fr.extend(Image.blend(a, img, k / n) for k in range(1, n + 1))
def cream_fade(img, sec=0.5):
    xfade(img, sec)   # direct crossfade: never a blank or plain-cream frame
def zoom(img, sec, z0, z1):
    n = int(sec * FPS)
    for k in range(n):
        z = z0 + (z1 - z0) * k / max(1, n - 1); c = OUT / z; o = (OUT - c) / 2
        fr.append(img.crop((o, o, o + c, o + c)).resize((OUT, OUT), Image.LANCZOS))


cover = Image.open(os.path.join(KIT, 'photos', '01.jpg')).convert('RGB').resize((OUT, OUT), Image.LANCZOS)
# 1) cover
zoom(cover, 1.3, 1.0, 1.03)
# 2) the full tab, April column boxed
full = Lp('s0-p9.png').crop((60, 400, 2520, 2140))
apr = (COL['G'] - 60 - 10, 84, COL['H'] - 60 + 14, 2140 - 400)
cream_fade(frame(full, 'Your April check-in', '2027 Check-ins: one column per month', apr), 0.4); hold(fr[-1], 0.6)
# 3) money in
T = 'Type your month'
v, hl = grid(0, 9, 12, 10); cream_fade(frame(v, T, 'What came in for each of you', hl), 0.3); hold(fr[-1], 0.2)
v, hl = grid(1, 9, 12, 10); hold(frame(v, T, 'What came in for each of you', hl), 0.5)
v, hl = grid(2, 9, 12, 11); hold(frame(v, T, 'Total income adds itself up', (hl[0], hl[1], hl[2], hl[3] + (ROW[12] - ROW[11]))), 0.7)
# 4) spending by category
v, hl = grid(2, 13, 18, (14, 18)); hold(frame(v, T, 'Then what you spent, by category', hl), 0.4)
v, hl = grid(3, 13, 18, (14, 18)); hold(frame(v, T, 'Then what you spent, by category', hl), 0.7)
v, hl = grid(4, 18, 26, (19, 23)); hold(frame(v, T, 'Spending vs plan is worked out', hl), 0.4)
v, hl = grid(4, 18, 26, (24, 26)); hold(frame(v, T, 'April: $300 under plan', hl), 0.8)
# 5) goal top-ups
v, hl = grid(4, 27, 35, (28, 31)); hold(frame(v, T, 'And what went to each goal', hl), 0.4)
v, hl = grid(5, 27, 35, (28, 31)); hold(frame(v, T, 'And what went to each goal', hl), 0.5)
v, hl = grid(5, 27, 35, (33, 35)); hold(frame(v, T, '$1,560 to goals, $930 left over', hl), 0.7)
# 6) the plain-words summary updates (Monthly Money Check-in tab)
T2 = 'Your month in plain words'
SUM = (96, 458, 1090, 822)
s0 = Lp('s0-p10.png').crop(SUM); s5 = Lp('s5-p10.png').crop(SUM)
cream_fade(frame(s0, T2, 'Before: last month, March'), 0.4); hold(fr[-1], 0.5)
xfade(frame(s5, T2, 'After: April, written for you'), 0.3); hold(fr[-1], 1.4)
# biggest overspend row, boxed
_t = Lp('s5-p10.png'); _y0, _y1 = 1134, 1370
_a = _t.crop((96, _y0, 560, _y1)); _b = _t.crop((990, _y0, 1470, _y1)); _h = _t.crop((96, 950, 560, 994)); _hb = _t.crop((990, 950, 1470, 994))
TB = Image.new('RGB', (_a.width + _b.width, _h.height + _a.height), SHEETBG)
TB.paste(_h, (0, 0)); TB.paste(_hb, (_a.width, 0)); TB.paste(_a, (0, _h.height)); TB.paste(_b, (_a.width, _h.height))
shop = (0, _h.height + 1228 - _y0, TB.width, _h.height + 1274 - _y0)
hold(frame(TB, T2, 'Biggest overspend: shopping, $80', shop), 0.9)
# 7) dashboard before / after
T3 = 'The Dashboard updates'
DB = (80, 80, 1732, 950); GP = (1364 - 80 - 8, 752 - 80 - 6, 1680 - 80 + 8, 912 - 80 + 6)
cream_fade(frame(Lp('s0-p1.png').crop(DB), T3, 'Before: goals 41% of the way there', GP), 0.4); hold(fr[-1], 0.5)
hold(frame(Lp('s5-p1.png').crop(DB), T3, 'After: 48% of the way there', GP), 0.6)
hold(frame(Lp('s5-p1.png').crop(DB), T3, 'After: 48% of the way there', GP, z=1.8, anchor=(1, 1)), 0.8)
# 8) cover again
cream_fade(cover, 0.4); zoom(cover, 0.8, 1.03, 1.0)

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
