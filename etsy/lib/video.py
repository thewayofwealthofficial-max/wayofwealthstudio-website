"""15-second silent square listing video from real product renders (slow zoom / pan per scene)."""
import os, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont

W = H = 1080; FPS = 30
BG = (247, 241, 236); PLUM = (74, 44, 61); GOLD = (184, 149, 110)
LORA = '/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf'
INTER = '/usr/share/fonts/opentype/inter/Inter-SemiBold.otf'


def _font(p, s):
    f = ImageFont.truetype(p, s)
    try:
        f.set_variation_by_name('SemiBold')
    except Exception:
        pass
    return f


_cache = {}


def _load(p):
    if p not in _cache:
        _cache[p] = Image.open(p).convert('RGB')
    return _cache[p]


def frame_scene(src, caption, t, mode, box=None):
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    cap = caption
    if isinstance(src, list):   # [(t_from, path, caption_or_None), ...] switch images mid-scene
        cur = src[0]
        for st in src:
            if t >= st[0]: cur = st
        src = cur[1]
        if len(cur) > 2 and cur[2]: cap = cur[2]
    d.text((W / 2, 60), cap, font=_font(LORA, 52), fill=PLUM, anchor='ma')
    s = _load(src)
    if box: s = s.crop(box)
    area_w, area_h, top = 1000, 900, 150
    # start view = whole width; zoom in 0-12% over the scene; 'pan' scrolls down
    z = 1 + 0.12 * t if mode == 'zoom' else 1.0
    if mode == 'hold': z = 1.0
    scale = area_w * z / s.width
    sw, sh = int(s.width * scale), int(s.height * scale)
    r = s.resize((sw, sh), Image.LANCZOS)
    ox = (sw - area_w) // 2
    oy = 0 if mode != 'pan' else int(max(0, sh - area_h) * t)
    if mode == 'zoom': oy = int((sh - min(sh, area_h)) * 0.0)
    view = r.crop((ox, oy, ox + area_w, oy + min(area_h, sh - oy)))
    x = (W - area_w) // 2
    top = top + max(0, (area_h - view.height) // 2)
    d.rounded_rectangle([x - 6, top - 6, x + area_w + 6, top + view.height + 6], radius=14, fill=(226, 214, 204))
    im.paste(view, (x, top))
    return im


def end_card(lines, sub):
    im = Image.new('RGB', (W, H), PLUM); d = ImageDraw.Draw(im)
    y = 330
    for ln in lines:
        d.text((W / 2, y), ln, font=_font(LORA, 92), fill=(255, 255, 255), anchor='ma'); y += 112
    y += 40
    for s in sub:
        d.text((W / 2, y), s, font=_font(INTER, 40), fill=(244, 227, 207), anchor='ma'); y += 60
    d.text((W / 2, 960), 'WAY OF WEALTH STUDIO', font=_font(INTER, 30), fill=GOLD, anchor='ma')
    return im


def make(scenes, end, out_mp4, work):
    """scenes: list of (seconds, src_png, caption, mode, crop_box). end: (seconds, lines, sub)."""
    shutil.rmtree(work, ignore_errors=True); os.makedirs(work)
    n = 0
    for dur, src, cap, mode, box in scenes:
        fr = int(dur * FPS)
        for i in range(fr):
            frame_scene(src, cap, i / max(1, fr - 1), mode, box).save(f'{work}/{n:04d}.jpg', quality=88); n += 1
    ec = end_card(end[1], end[2])
    for i in range(int(end[0] * FPS)):
        ec.save(f'{work}/{n:04d}.jpg', quality=88); n += 1
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{work}/%04d.jpg', '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p', '-crf', '21', '-an', '-movflags', '+faststart', out_mp4], check=True)
    shutil.rmtree(work)
    return n / FPS
