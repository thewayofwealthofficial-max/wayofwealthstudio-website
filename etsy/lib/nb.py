"""Nano Banana Pro kit (rewritten from Drive nano_banana_photo_kit.py, 12 Nov 2026)."""
import base64, json, os, urllib.request
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from scipy import ndimage
K = os.environ.get('GEMINI_API_KEY', '')
STYLE = ("Square premium Etsy listing image in exactly the same visual style as the reference images: warm cream and soft beige background with gentle studio light, "
 "large elegant bold serif headline in dark brown-black, gold italic serif subtitle, soft gold accents and small gold four-point sparkles, glossy realistic devices with soft shadows, clean and uncluttered, premium feel. "
 "Very bottom centre: small gold letter-spaced serif text 'WAY OF WEALTH STUDIO' between two small gold sparkles. "
 "CRITICAL: every device screen must be filled edge to edge with plain solid bright green (#00FF00) and nothing else on it - no documents, no pages, no text, no UI on the screens. Devices face the viewer straight on, screens flat and rectangular, not tilted. "
 "Spell every word exactly as given. Do not add any other text. Do not copy any text or pages from the reference images. ")
CALLS = {'n': 0}
def gen(prompt, refs, out, model='gemini-3-pro-image', size='2K'):
    parts = [{"text": prompt}]
    for r in refs:
        parts.append({"inline_data": {"mime_type": "image/jpeg" if r.endswith('jpg') else "image/png", "data": base64.b64encode(open(r, 'rb').read()).decode()}})
    body = {"contents": [{"parts": parts}], "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "1:1", "imageSize": size}}}
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", data=json.dumps(body).encode(),
                                 headers={"x-goog-api-key": K, "Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=300)); CALLS['n'] += 1
    with open('/home/claude/nbkit/calls.log', 'a') as f: f.write(out + '\n')
    for c in d.get('candidates', []):
        for p in c['content']['parts']:
            x = p.get('inlineData') or p.get('inline_data')
            if x:
                open(out, 'wb').write(base64.b64decode(x['data'])); return out
    raise RuntimeError(json.dumps(d)[:800])
def fit(src, w, h):
    sw, sh = src.size; r = max(w / sw, h / sh); s = src.resize((round(sw * r), round(sh * r)), Image.LANCZOS); return s.crop((0, 0, w, h))
def phone_shot(src, w, h):
    pad = int(h * .075); c = Image.new('RGB', (w, h), (245, 240, 232)); c.paste(fit(src, w, h - pad), (0, pad)); return c
def comps(img, minarea=20000):
    a = np.array(img).astype(int); m = (a[..., 1] > 175) & (a[..., 0] < 140) & (a[..., 2] < 140) & (a[..., 1] - a[..., 0] > 90)
    lab, n = ndimage.label(m); out = []
    for i, sl in enumerate(ndimage.find_objects(lab)):
        ys, xs = sl; area = (lab[sl] == i + 1).sum()
        if area > minarea: out.append((xs.start, ys.start, xs.stop, ys.stop, lab == i + 1))
    return out
def green_left(img):
    a = np.array(img).astype(int); return int(((a[..., 1] > 170) & (a[..., 0] < 120) & (a[..., 2] < 120)).sum())
def composite(raw, out, assign, order='x'):
    """assign: list of (PIL image, kind) in left-to-right order (order='x') or top-to-bottom ('y'). kind: tab|phone|rect"""
    img = Image.open(raw).convert('RGB')
    cs = sorted(comps(img), key=lambda c: c[0] if order == 'x' else c[1])
    if len(cs) != len(assign): print('WARNING screens found', len(cs), 'expected', len(assign))
    for (x0, y0, x1, y1, mask), (src, kind) in zip(cs, assign):
        w, h = x1 - x0, y1 - y0
        shot = phone_shot(src, w, h) if kind == 'phone' else fit(src, w, h)
        m = Image.fromarray((mask[y0:y1, x0:x1] * 255).astype('uint8')).filter(ImageFilter.MaxFilter(7))
        img.paste(shot, (x0, y0), m)
        e = 4; X0, Y0, X1, Y1 = max(0, x0 - e), max(0, y0 - e), min(img.width, x1 + e), min(img.height, y1 + e)
        a = np.array(img).astype(int)[Y0:Y1, X0:X1]
        g2 = (a[..., 1] > 150) & (a[..., 1] - a[..., 0] > 70) & (a[..., 1] - a[..., 2] > 70)
        if g2.any():
            big = Image.new('RGB', (X1 - X0, Y1 - Y0)); big.paste(shot.resize((X1 - X0, Y1 - Y0), Image.LANCZOS))
            m2 = Image.fromarray((g2 * 255).astype('uint8')).filter(ImageFilter.MaxFilter(3))
            img.paste(big, (X0, Y0), m2)
    left = green_left(img)
    img.resize((2000, 2000), Image.LANCZOS).save(out, quality=90); print(out, len(cs), 'green left', left); return left

def screens(img, gap=40):
    """green components grouped: overlapping/near bboxes merged into one screen."""
    cs = comps(img, 3000); groups = []
    for c in cs:
        merged = False
        for g in groups:
            ox = max(0, min(c[2], g[2]) - max(c[0], g[0])); oy = max(0, min(c[3], g[3]) - max(c[1], g[1]))
            small = min((c[2]-c[0])*(c[3]-c[1]), (g[2]-g[0])*(g[3]-g[1]))
            stacked = abs(c[0]-g[0]) < 40 and abs(c[2]-g[2]) < 40 and (c[1] <= g[3] + gap and c[3] >= g[1] - gap)
            if ox * oy > 0.6 * small or stacked:
                g[0] = min(g[0], c[0]); g[1] = min(g[1], c[1]); g[2] = max(g[2], c[2]); g[3] = max(g[3], c[3]); g[4] = g[4] | c[4]; merged = True; break
        if not merged: groups.append(list(c))
    return [g for g in groups if (g[2]-g[0])*(g[3]-g[1]) > 20000]
def composite2(raw, out, assign, order='x'):
    img = Image.open(raw).convert('RGB')
    gs = sorted(screens(img), key=lambda c: c[0] if order == 'x' else c[1])
    if len(gs) != len(assign): print('WARNING screens', len(gs), 'expected', len(assign), [g[:4] for g in gs])
    for (x0, y0, x1, y1, mask), (src, kind) in zip(gs, assign):
        w, h = x1 - x0, y1 - y0
        shot = phone_shot(src, w, h) if kind == 'phone' else fit(src, w, h)
        m = Image.fromarray((mask[y0:y1, x0:x1] * 255).astype('uint8')).filter(ImageFilter.MaxFilter(9))
        # fill holes inside the screen (thin lines between green parts)
        a = np.pad(np.array(m) > 0, 10); a = ndimage.binary_closing(a, iterations=6); a = ndimage.binary_fill_holes(a)[10:-10, 10:-10]
        m = Image.fromarray((a * 255).astype('uint8'))
        img.paste(shot, (x0, y0), m)
    left = green_left(img)
    img.resize((2000, 2000), Image.LANCZOS).save(out, quality=90); print(out, len(gs), 'green left', left); return left
