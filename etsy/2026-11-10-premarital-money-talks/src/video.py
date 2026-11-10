import os, subprocess
from PIL import Image, ImageDraw, ImageFont
os.chdir(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1350, 30
FD = '/usr/share/fonts/truetype/'
F = lambda f, s: ImageFont.truetype(FD + f, s)
SERB = 'crosextra/Caladea-Bold.ttf'; SM = 'google-fonts/Poppins-Medium.ttf'
CREAM = (245, 240, 232); CHAR = (61, 61, 61); DSAGE = (143, 165, 133); GOLD = (184, 149, 110)
S = lambda n: Image.open(f'hi/s-{n:02d}.png').convert('RGB')
E = lambda n: Image.open(f'hie/f-{n:02d}.png').convert('RGB')


def base(caption):
    im = Image.new('RGB', (W, H), CREAM); d = ImageDraw.Draw(im)
    f = F(SERB, 62)
    d.text((W / 2, 60), caption, font=f, fill=CHAR, anchor='ma')
    return im, d


def place(im, page, t, y0=180, zoom=(1.0, 1.0), focus=(0.5, 0.0)):
    """Show page in a window under the caption, with a slow zoom from zoom[0] to zoom[1]."""
    z = zoom[0] + (zoom[1] - zoom[0]) * t
    win_w, win_h = W - 100, H - y0 - 60
    pw = int(win_w * z); ph = int(page.height * pw / page.width)
    p = page.resize((pw, ph), Image.LANCZOS)
    ox = int((pw - win_w) * focus[0]); oy = int(max(0, min(ph - win_h, (ph - win_h) * focus[1] * t)))
    crop = p.crop((ox, oy, ox + win_w, oy + min(win_h, ph)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([46, y0 - 4, 54 + win_w, y0 + crop.height + 4], radius=14, fill=(225, 216, 200))
    im.paste(crop, (50, y0))


def wipe(empty, full, t):
    """Fill-in effect: top part shows the filled page, the rest still empty."""
    h = int(full.height * (0.12 + 0.88 * t))
    out = empty.copy(); out.paste(full.crop((0, 0, full.width, h)), (0, 0))
    return out


scenes = [
    (2.0, lambda t: (lambda im_d: (place(im_d[0], S(1).crop((0, 0, 1406, 1200)), t, zoom=(1.0, 1.06), focus=(0.5, 0.0)), im_d[0])[1])(base('6 money talks before you marry'))),
    (3.0, lambda t: (lambda im_d: (place(im_d[0], wipe(E(9), S(9), min(1, t * 1.3)), t, zoom=(1.0, 1.0)), im_d[0])[1])(base('Type in your numbers...'))),
    (2.0, lambda t: (lambda im_d: (place(im_d[0], S(9), t, zoom=(1.0, 1.12), focus=(0.5, 0.0)), im_d[0])[1])(base('Work out a fair split'))),
    (3.0, lambda t: (lambda im_d: (place(im_d[0], wipe(E(13).crop((0, 0, 1406, 1500)), S(13).crop((0, 0, 1406, 1500)), min(1, t * 1.3)), t), im_d[0])[1])(base('Write your Money Agreement'))),
    (2.0, lambda t: (lambda im_d: (place(im_d[0], S(16), t, zoom=(1.0, 1.08)), im_d[0])[1])(base('Plus 20 quick questions'))),
]


def endcard(t):
    im = Image.new('RGB', (W, H), (184, 197, 176)); d = ImageDraw.Draw(im)
    d.text((W / 2, 420), 'Premarital Money', font=F(SERB, 96), fill=CHAR, anchor='ma')
    d.text((W / 2, 530), 'Talks Workbook', font=F(SERB, 96), fill=CHAR, anchor='ma')
    d.text((W / 2, 700), 'Fillable PDF + printable', font=F(SM, 46), fill=CHAR, anchor='ma')
    d.text((W / 2, 770), 'A4 and US Letter  ·  any currency', font=F(SM, 46), fill=CHAR, anchor='ma')
    d.text((W / 2, 1150), 'Way of Wealth Studio', font=F(SM, 40), fill=(80, 80, 80), anchor='ma')
    return im


scenes.append((2.5, endcard))
os.makedirs('vf', exist_ok=True)
n = 0
for dur, fn in scenes:
    frames = int(dur * FPS)
    for i in range(frames):
        fn(i / max(1, frames - 1)).save(f'vf/{n:04d}.jpg', quality=88); n += 1
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', 'vf/%04d.jpg', '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p', '-crf', '21', '-movflags', '+faststart', 'video.mp4'], check=True)
print(n / FPS, 'seconds')
