# Shared frame kit (same look as the 17/18 Nov videos): cream gradient, Playfair headline, gold italic line, rounded screen, gold box.
import os, subprocess, shutil
from PIL import Image, ImageDraw, ImageFilter, ImageFont
F='/home/claude/fonts/'
pf=lambda s: ImageFont.truetype(F+'PF-700-normal.ttf',s); pfi=lambda s: ImageFont.truetype(F+'PF-400-italic.ttf',s); pfr=lambda s: ImageFont.truetype(F+'PF-400-normal.ttf',s)
inter=lambda s,w=500: ImageFont.truetype(F+f'Inter-{w}.ttf',s)
INK=(42,38,32); GOLD_D=(160,122,74); BOX=(176,128,60); OUT=1080; FPS=30
def _bg():
    im=Image.new('RGB',(OUT,OUT)); d=ImageDraw.Draw(im)
    for y in range(OUT):
        t=y/OUT; d.line([(0,y),(OUT,y)],fill=tuple(int(a+(b-a)*t) for a,b in zip((252,244,236),(244,232,216))))
    d.text((OUT/2,1042),'WAY OF WEALTH STUDIO',font=pfr(42),fill=GOLD_D,anchor='mm')   # cap height ~30 px
    return im
BG=_bg()
LOG=[]   # (label, display scale) per screen, for the text-size check
def frame(src, title, sub, hl=None, maxw=980, maxh=760, label=None):
    """src: PIL image (crop of a real render). hl: box in src pixels, or list of boxes."""
    im=BG.copy(); d=ImageDraw.Draw(im)
    d.text((OUT/2,92),title,font=pf(64),fill=INK,anchor='mm')
    d.text((OUT/2,168),sub,font=pfi(42),fill=GOLD_D,anchor='mm')
    sc=min(maxw/src.width, maxh/src.height); W=round(src.width*sc); h=round(src.height*sc)
    x0=(OUT-W)//2; top=240+(760-h)//3
    sh=Image.new('L',(OUT,OUT),0); ImageDraw.Draw(sh).rounded_rectangle((x0,top+12,x0+W,top+h+12),20,fill=80)
    im.paste((150,115,70),(0,0),sh.filter(ImageFilter.GaussianBlur(16)))
    view=src.resize((W,h),Image.LANCZOS)
    m=Image.new('L',(W,h),0); ImageDraw.Draw(m).rounded_rectangle((0,0,W-1,h-1),20,fill=255)
    im.paste(view,(x0,top),m)
    if hl:
        for a,b,c,e in (hl if isinstance(hl,list) else [hl]):
            d.rounded_rectangle((x0+a*sc-6,top+b*sc-6,x0+c*sc+6,top+e*sc+6),12,outline=BOX,width=6)
    if label: LOG.append((label,sc))
    return im
class Reel:
    def __init__(s): s.frames=[]
    def hold(s,img,sec): s.frames.extend([img]*round(sec*FPS))
    def fade(s,a,b,sec=0.3):
        n=round(sec*FPS)
        for i in range(n): s.frames.append(Image.blend(a,b,(i+1)/n))
    def save(s,out,tmp):
        shutil.rmtree(tmp,ignore_errors=True); os.makedirs(tmp)
        for i,f in enumerate(s.frames): f.save(f'{tmp}/f{i:04d}.png')
        subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i',f'{tmp}/f%04d.png','-c:v','libx264','-pix_fmt','yuv420p','-crf','24','-an','-movflags','+faststart',out],check=True)
        shutil.rmtree(tmp); return len(s.frames)/FPS, os.path.getsize(out)
def hero(path): return Image.open(path).convert('RGB').resize((OUT,OUT),Image.LANCZOS)
ease=lambda t: t*t*(3-2*t)
def lerp(a,b,t): return tuple(p+(q-p)*t for p,q in zip(a,b))
def _geom(src,maxw=980,maxh=760):
    sc=min(maxw/src.width, maxh/src.height); W=round(src.width*sc); h=round(src.height*sc)
    return sc,W,h,(OUT-W)//2,240+(760-h)//3
def flip(r, a, b, title, sub, sec=0.55):
    """page turn: page A folds away to the left spine, page B unfolds from it (no dark fade)"""
    n=round(sec*FPS); ga=_geom(a); gb=_geom(b)
    for i in range(n):
        t=ease((i+1)/n); im=BG.copy(); d=ImageDraw.Draw(im)
        d.text((OUT/2,92),title,font=pf(64),fill=INK,anchor='mm'); d.text((OUT/2,168),sub,font=pfi(42),fill=GOLD_D,anchor='mm')
        src,(sc,W,h,x0,top)=(a,ga) if t<0.5 else (b,gb)
        k=abs(1-2*t); w=max(2,round(W*k))
        view=src.resize((W,h),Image.LANCZOS).resize((w,h),Image.LANCZOS)
        view=Image.blend(view,Image.new('RGB',view.size,(255,252,247)),0.35*(1-k))   # page catches the light as it turns
        xl=x0 if t<0.5 else x0   # spine on the left edge
        im.paste(view,(xl,top)); d.line([(xl,top),(xl,top+h)],fill=(200,185,165),width=3)
        r.frames.append(im)

def title_card(name_lines, sub, src, hl=None, label=None):
    """house-style opening/closing card: Playfair product name, gold italic line, a real dashboard render below"""
    im=BG.copy(); d=ImageDraw.Draw(im); y=86
    for ln in name_lines: d.text((OUT/2,y),ln,font=pf(66),fill=INK,anchor='mm'); y+=78
    d.text((OUT/2,y+6),sub,font=pfi(44),fill=GOLD_D,anchor='mm')
    top=y+70; maxh=1000-top
    sc=min(980/src.width, maxh/src.height); W=round(src.width*sc); h=round(src.height*sc); x0=(OUT-W)//2; top=top+(maxh-h)//2
    sh=Image.new('L',(OUT,OUT),0); ImageDraw.Draw(sh).rounded_rectangle((x0,top+12,x0+W,top+h+12),20,fill=80)
    im.paste((150,115,70),(0,0),sh.filter(ImageFilter.GaussianBlur(16)))
    m=Image.new('L',(W,h),0); ImageDraw.Draw(m).rounded_rectangle((0,0,W-1,h-1),20,fill=255)
    im.paste(src.resize((W,h),Image.LANCZOS),(x0,top),m)
    if label: LOG.append((label,sc))
    return im
