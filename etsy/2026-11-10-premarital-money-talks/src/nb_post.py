"""Round-3 touch-ups on finished photos: serif footer wordmark, subtitle quotes (01), callout text (04)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
F='/home/claude/fonts/'
def paint_out(img,box,band=5):
    """remove ink inside box: mask = pixels clearly off the local background, inpainted (keeps gradients/light rays)"""
    import cv2
    from scipy import ndimage
    a=np.array(img); x0,y0,x1,y1=box
    sub=a[y0:y1,x0:x1].astype(int).sum(-1)
    border=np.concatenate([sub[0],sub[-1],sub[:,0],sub[:,-1]])
    off=sub<np.median(border)-45
    m=np.zeros(a.shape[:2],np.uint8); m[y0:y1,x0:x1]=ndimage.binary_dilation(off,iterations=4)*255
    out=cv2.inpaint(np.ascontiguousarray(a[...,::-1]),m,7,cv2.INPAINT_TELEA)[...,::-1]
    return Image.fromarray(np.ascontiguousarray(out))
def _old_paint_out(img,box,band=5):
    a=np.array(img).astype(float); x0,y0,x1,y1=box
    L=a[y0:y1,x0-band:x0].mean(1); R=a[y0:y1,x1:x1+band].mean(1)
    t=np.linspace(0,1,x1-x0)[None,:,None]
    a[y0:y1,x0:x1]=L[:,None,:]*(1-t)+R[:,None,:]*t
    return Image.fromarray(a.clip(0,255).astype('uint8'))
def ink(img,box):
    a=np.array(img).astype(int)[box[1]:box[3],box[0]:box[2]].reshape(-1,3)
    lum=a.sum(1); return tuple(int(v) for v in np.median(a[lum<np.percentile(lum,8)],0))
def tracked(img,text,font,cx,cap_top,width,fill):
    """draw text centred at cx, cap top at cap_top, letters spread so the run is `width` px wide"""
    d=ImageDraw.Draw(img); ws=[d.textlength(ch,font=font) for ch in text]
    gaps=len(text)-1; sp=(width-sum(ws))/gaps
    bb=font.getbbox('W'); x=cx-width/2
    for ch,w in zip(text,ws):
        d.text((x,cap_top-bb[1]),ch,font=font,fill=fill); x+=w+sp
def cap_font(path,cap):
    s=cap
    for _ in range(40):
        f=ImageFont.truetype(path,s); bb=f.getbbox('H'); h=bb[3]-bb[1]
        if abs(h-cap)<=0.5: break
        s=max(4,round(s*cap/h))
    return f
P02=Image.open('photos/02.jpg').convert('RGB'); GOLDTXT=ink(P02,(612,1920,1387,1956))
def footer(k,ytop,ybot):
    im=Image.open(f'photos/{k}.jpg').convert('RGB')
    im=paint_out(im,(650,ytop-8,1352,ybot+8))
    f=cap_font(F+'PF-600-normal.ttf',ybot-ytop)
    tracked(im,'WAY OF WEALTH STUDIO',f,1000.5,ytop,668,GOLDTXT)
    return im
if __name__=='__main__':
    print('gold',GOLDTXT)
    im=footer('01',1932,1964)
    # subtitle with quote marks
    im.save('photos/01.jpg',quality=90)
    for k in ('04','05'): footer(k,1877,1909).save(f'photos/{k}.jpg',quality=90)

def subtitle01():
    im=Image.open('photos/01.jpg').convert('RGB')
    col=ink(im,(269,481,1730,566))
    im=paint_out(im,(250,468,1750,578))
    t='6 money conversations to have before “I do”'
    d=ImageDraw.Draw(im); s=80
    while True:
        f=ImageFont.truetype(F+'PF-400-italic.ttf',s); bb=d.textbbox((0,0),t,font=f)
        if bb[2]-bb[0]<=1480: break
        s-=1
    x=1000-(bb[2]-bb[0])/2-bb[0]; y=481-bb[1]
    d.text((x,y),t,font=f,fill=col); im.save('photos/01.jpg',quality=90); print('subtitle size',s,col)

def callout04():
    im=Image.open('photos/04.jpg').convert('RGB')
    col=ink(im,(1578,907,1885,998))
    im=paint_out(im,(1560,895,1905,1015))
    f=ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Regular.otf',10)
    f=cap_font('/usr/share/fonts/opentype/inter/Inter-Regular.otf',36)
    d=ImageDraw.Draw(im); cx=1731
    for line,base in (('Set after bills',944),('and savings',998)):
        bb=d.textbbox((0,0),line,font=f,anchor='ls'); w=bb[2]-bb[0]
        d.text((cx-w/2,base),line,font=f,fill=col,anchor='ls')
    im.save('photos/04.jpg',quality=90); print('callout04',col)
