import numpy as np
from PIL import Image, ImageFilter, ImageDraw
P='/home/claude/wayofwealthstudio-website/etsy/2026-11-10-premarital-money-talks/photos/'
G='/tmp/claude-0/w/pm/'
def fill_bg(a, box):
    import cv2
    x0,y0,x1,y1=box
    H,W,_=a.shape; k=8
    sm=cv2.resize(a,(W//k,H//k),interpolation=cv2.INTER_AREA)
    m=np.zeros(sm.shape[:2],np.uint8); m[y0//k:y1//k+1,x0//k:x1//k+1]=255
    inp=sm.copy()
    for _ in range(3):
        inp=cv2.inpaint(inp,m,15,cv2.INPAINT_TELEA)
    inp=cv2.GaussianBlur(inp,(0,0),6)
    up=cv2.resize(inp,(W,H),interpolation=cv2.INTER_CUBIC).astype(float)
    fm=np.zeros((H,W),float); fm[y0:y1,x0:x1]=1
    fm=cv2.GaussianBlur(fm,(0,0),10)
    fm[y0+8:y1-8,x0+8:x1-8]=1
    return (a*(1-fm[...,None])+up*fm[...,None]).clip(0,255).astype(np.uint8)
def page_card(path, w, rot=0):
    pg=Image.open(path).convert('RGB')
    h=int(pg.height*w/pg.width); pg=pg.resize((w,h),Image.LANCZOS)
    pad=40
    card=Image.new('RGBA',(w+2*pad,h+2*pad),(0,0,0,0))
    sh=Image.new('RGBA',card.size,(0,0,0,0))
    ImageDraw.Draw(sh).rectangle([pad+8,pad+14,pad+w+8,pad+h+14],fill=(80,60,40,70))
    sh=sh.filter(ImageFilter.GaussianBlur(14))
    card.alpha_composite(sh)
    d=ImageDraw.Draw(card); d.rectangle([pad-2,pad-2,pad+w+1,pad+h+1],fill=(225,216,200,255))
    card.paste(pg,(pad,pad))
    if rot: card=card.rotate(rot,resample=Image.BICUBIC,expand=True)
    return card
def rework(src, dst, box, scale, lx, pages, fillbox):
    im=Image.open(P+src).convert('RGB'); a=np.array(im)
    x0,y0,x1,y1=box
    lst=im.crop(box)
    a2=fill_bg(a,fillbox)
    base=Image.fromarray(a2).convert('RGBA')
    nl=lst.resize((int(lst.width*scale),int(lst.height*scale)),Image.LANCZOS)
    m=Image.new('L',nl.size,0); f=24
    ImageDraw.Draw(m).rectangle([f,f,nl.width-f,nl.height-f],fill=255)
    m=m.filter(ImageFilter.GaussianBlur(f/2))
    ly=y0+(y1-y0-nl.height)//2
    base.paste(nl,(lx,ly),m)
    for (pth,w,rot,px,py) in pages:
        c=page_card(G+pth,w,rot); base.alpha_composite(c,(px,py))
    base.convert('RGB').save(dst,quality=90)
