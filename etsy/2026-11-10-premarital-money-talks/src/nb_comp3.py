"""Round-3 compositing: clean rounded-rect screen masks, screens filled like a PDF viewer (page content + top of next page), callouts on page targets."""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
HI='/home/claude/work/premarital/hi3/'
PX=200/72; PW=round(595.2756*PX)
GOLD=(176,138,78); GAP=(214,208,198)
def page(n): return Image.open(f'{HI}p-{n:02d}.png').convert('RGB')
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
        m=r&c; ys,xs=np.where(m)
        x0,y0,x1,y1=xs.min(),ys.min(),xs.max()+1,ys.max()+1
        miss=((x1-x0)*(y1-y0)-m.sum())/4; rad=int(np.sqrt(max(miss,1)/(1-np.pi/4)))
        out.append((x0,y0,x1,y1,m,rad))
    return sorted(out,key=lambda c:c[0])
def viewer(w,h,parts,mode='stack'):
    """canvas w x h (screen px). parts: [(page, ycut_pt)] stacked with a gap, scaled to the screen width.
    mode 'fit': first part scaled to width, centred vertically with even page-colour margins."""
    r=w/PW; c=Image.new('RGB',(w,h),GAP)
    if mode=='fit':
        p,yc=parts[0]; im=page(p).crop((0,0,PW,int(yc*PX))); im=im.resize((w,round(im.height*r)),Image.LANCZOS)
        c=Image.new('RGB',(w,h),im.getpixel((5,5))); oy=(h-im.height)//2; c.paste(im,(0,oy)); return c,(r,0,oy)
    y=0
    for p,yc in parts:
        im=page(p); im=im.crop((0,0,PW,int(yc*PX) if yc else im.height)); im=im.resize((w,round(im.height*r)),Image.LANCZOS)
        c.paste(im,(0,y)); y+=im.height+max(6,int(18*r*3))
        if y>=h: break
    return c,(r,0,0)
def build(raw,out,assign,targets=None,fix_bezel=False,line_w=5,dot_r=13):
    img=Image.open(raw).convert('RGB'); R=np.array(img).astype(int); cs=screens(img)
    assert len(cs)==len(assign),(raw,len(cs))
    for (x0,y0,x1,y1,m,rad),(parts,mode) in zip(cs,assign):
        if fix_bezel:
            ring=ndimage.binary_dilation(m,iterations=45)&~ndimage.binary_dilation(m,iterations=2)
            a=np.array(img); lum=a.astype(int).sum(-1)/3; a[ring&(lum<125)]=(18,18,20); img=Image.fromarray(a)
        e=2; X0,Y0,X1,Y1=x0-e,y0-e,x1+e,y1+e; w,h=X1-X0,Y1-Y0
        if mode=='phone':
            pad=int(h*.07); shot,(r,ox,oy)=viewer(w,h-pad,parts,'fit'); s2=Image.new('RGB',(w,h),shot.getpixel((2,2))); s2.paste(shot,(0,pad)); shot=s2; oy+=pad
        else:
            shot,(r,ox,oy)=viewer(w,h,parts,mode)
        mk=Image.new('L',(w,h),0); ImageDraw.Draw(mk).rounded_rectangle((0,0,w-1,h-1),max(rad,4),fill=255)
        md=ndimage.binary_dilation(m,iterations=3)[Y0:Y1,X0:X1]
        mk=Image.fromarray(np.maximum(np.array(mk),(md*255).astype('uint8'))).filter(ImageFilter.GaussianBlur(0.7))
        img.paste(shot,(X0,Y0),mk)
        if targets:
            d=ImageDraw.Draw(img)
            isg=lambda col:(R[:,col,0]>140)&(R[:,col,1]>100)&(R[:,col,2]<130)&(R[:,col,0]-R[:,col,2]>50)
            for side,tx,ty,mx_pt in targets:
                sgn=-1 if side=='L' else 1; base=x0 if side=='L' else x1
                gm=isg(base+sgn*25)&isg(base+sgn*40)&isg(base+sgn*55)
                gy=np.where(gm)[0]; gy=gy[(gy>y0)&(gy<y1)]
                run=[gy[0]]
                for v in gy[1:]:
                    if v-run[-1]>2: break
                    run.append(v)
                ey=int(np.median(run))
                sx=X0 if side=='L' else X1
                P=lambda X,Y:(X0+ox+X*PX*r, Y0+oy+Y*PX*r)
                mx,_=P(mx_pt,0); px,py=P(tx,ty)
                pts=[(sx-3*sgn,ey),(mx,ey),(mx,py),(px,py)]
                d.line(pts,fill=GOLD,width=line_w,joint='curve')
                d.ellipse([px-dot_r,py-dot_r,px+dot_r,py+dot_r],fill=GOLD,outline=(255,250,240),width=3)
    img=img.resize((2000,2000),Image.LANCZOS); img.save(out,quality=90); print(out,'screens',len(cs))
JOBS={
 '01':dict(assign=[([(1,None)],'stack'),([(9,540)],'phone')]),
 '03':dict(assign=[([(8,600),(9,None)],'stack')],targets=[('L',30,245,20),('R',558,405,575)]),
 '04':dict(assign=[([(9,540),(10,None)],'stack')],targets=[('L',30,272,20),('R',558,456,575)]),
 '05':dict(assign=[([(10,650),(11,None)],'stack')],targets=[('L',30,168,20),('R',558,322,575)]),
 '06':dict(assign=[([(13,None)],'stack'),([(14,None)],'stack')]),
 '07':dict(assign=[([(16,690)],'fit')]),
 '08':dict(assign=[([(3,500),(4,None)],'stack')],fix_bezel=True),
}
if __name__=='__main__':
    for k in sys.argv[1:] or JOBS: build(f'raw/s{k}.png',f'photos/{k}.jpg',**JOBS[k])
