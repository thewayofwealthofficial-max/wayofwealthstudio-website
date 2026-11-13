"""Round-2 compositing: filled + dilated screen masks (no green fringe), page fitted inside the screen, redrawn callout dots."""
import sys; sys.path.insert(0,'/home/claude/nbkit'); import nb
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
HI='/home/claude/work/premarital/hi2/'
PX=200/72
def page(n): return Image.open(f'{HI}p-{n:02d}.png').convert('RGB')
def contain(src,w,h,top_pad=0,fill=False):
    if fill:
        r=max(w/src.width,h/src.height); s=src.resize((round(src.width*r),round(src.height*r)),Image.LANCZOS)
        ox=(w-s.width)//2; oy=0; c=s.crop((-ox,0,-ox+w,h)); return c,(r,ox,oy)
    bgc=src.getpixel((5,5)); c=Image.new('RGB',(w,h),bgc)
    hh=h-top_pad; r=min(w/src.width,hh/src.height); s=src.resize((round(src.width*r),round(src.height*r)),Image.LANCZOS)
    ox=(w-s.width)//2; oy=top_pad+((hh-s.height)//2 if not top_pad else int(hh*.03)); c.paste(s,(ox,oy)); return c,(r,ox,oy)
def screens(img):
    a=np.array(img).astype(int)
    g=(a[...,1]>150)&(a[...,1]-a[...,0]>70)&(a[...,1]-a[...,2]>70)
    lab,n=ndimage.label(g); out=[]
    for i,sl in enumerate(ndimage.find_objects(lab)):
        m=lab==i+1
        if m.sum()<20000: continue
        r=np.zeros_like(m); c=np.zeros_like(m)
        for y in np.where(m.any(1))[0]:
            xs=np.where(m[y])[0]; r[y,xs.min():xs.max()+1]=True
        for x in np.where(m.any(0))[0]:
            ys=np.where(m[:,x])[0]; c[ys.min():ys.max()+1,x]=True
        m=r&c
        out.append((sl[1].start,sl[0].start,sl[1].stop,sl[0].stop,m))
    return sorted(out,key=lambda c:c[0])
GOLD=(176,138,78)
def callouts(img,m,x0,x1):
    """gold pixels inside the screen mask = old dots/lines; return per side (entry_y, dot_center)"""
    a=np.array(img).astype(int)
    gold=(a[...,0]>140)&(a[...,1]>100)&(a[...,2]<130)&(a[...,0]-a[...,2]>50)&m
    lab,n=ndimage.label(gold); res=[]
    for sl in ndimage.find_objects(lab):
        ys,xs=sl
        if (ys.stop-ys.start)*(xs.stop-xs.start)<150: continue
        res.append(((ys.start+ys.stop)//2,(xs.start+xs.stop)//2))
    return res
def bezel_fix(img,m):
    """even bezel: dark pixels in a ring around the screen set to one colour"""
    ring=ndimage.binary_dilation(m,iterations=45)&~ndimage.binary_dilation(m,iterations=2)
    a=np.array(img); lum=a.astype(int).sum(-1)/3
    sel=ring&(lum<125)
    a[sel]=(18,18,20); return Image.fromarray(a)
def build(raw,out,assign,targets=None,fix_bezel=False,line_w=5,dot_r=13):
    img=Image.open(raw).convert('RGB'); cs=screens(img)
    assert len(cs)==len(assign),(raw,len(cs))
    for (x0,y0,x1,y1,m),(src,kind) in zip(cs,assign):
        old=callouts(img,m,x0,x1) if targets else []
        if fix_bezel: img=bezel_fix(img,m)
        md=ndimage.binary_dilation(m,iterations=3)
        X0,Y0,X1,Y1=x0-3,y0-3,x1+3,y1+3
        w,h=X1-X0,Y1-Y0
        shot,(r,ox,oy)=contain(src,w,h,top_pad=int(h*.07) if kind=='phone' else 0,fill=(kind=='fill'))
        mk=Image.fromarray((md[Y0:Y1,X0:X1]*255).astype('uint8')).filter(ImageFilter.GaussianBlur(0.8))
        img.paste(shot,(X0,Y0),mk)
        if targets:
            d=ImageDraw.Draw(img); R=np.array(Image.open(raw).convert('RGB')).astype(int)
            for side,tx,ty in targets:
                isg=lambda col:(R[:,col,0]>140)&(R[:,col,1]>100)&(R[:,col,2]<130)&(R[:,col,0]-R[:,col,2]>50)
                sgn=-1 if side=='L' else 1; base=x0 if side=='L' else x1
                gm=isg(base+sgn*25)&isg(base+sgn*40)&isg(base+sgn*55)
                gy=np.where(gm)[0]; gy=gy[(gy>y0)&(gy<y1)]; ey=int(np.median(gy))
                row=np.where(m[ey])[0]; sx=int(row.min()) if side=='L' else int(row.max())
                P=lambda X,Y:(X0+ox+X*PX*r, Y0+oy+Y*PX*r)
                mx,_=P(20 if side=='L' else 575,0); px,py=P(tx,ty)
                pts=[(sx,ey),(mx,ey),(mx,py),(px,py)]
                d.line(pts,fill=GOLD,width=line_w,joint='curve')
                d.ellipse([px-dot_r,py-dot_r,px+dot_r,py+dot_r],fill=GOLD,outline=(255,250,240),width=3)
    a=np.array(img).astype(int); fringe=int(((a[...,1]-a[...,0]>=35)&(a[...,1]-a[...,2]>=35)).sum())
    img.resize((2000,2000),Image.LANCZOS).save(out,quality=90); print(out,'screens',len(cs),'G35 pixels',fringe)
def topcrop(n,f): p=page(n); return p.crop((0,0,p.width,int(p.height*f)))
JOBS={
 '01':dict(assign=[(page(1),'fill'),(topcrop(9,0.62),'phone')]),
 '03':dict(assign=[(page(8),'tab')],targets=[('L',30,245),('R',558,405)]),
 '04':dict(assign=[(page(9),'tab')],targets=[('L',30,272),('R',558,456)]),
 '05':dict(assign=[(page(10),'tab')],targets=[('L',30,168),('R',558,322)]),
 '06':dict(assign=[(page(13),'tab'),(page(14),'tab')]),
 '07':dict(assign=[(page(16).crop((int(30*PX),int(30*PX),int(565*PX),int(760*PX))),'tab')]),
 '08':dict(assign=[(page(3),'tab')],fix_bezel=True),
}
for k in sys.argv[1:] or JOBS:
    build(f'raw/s{k}.png',f'photos/{k}.jpg',**JOBS[k])
