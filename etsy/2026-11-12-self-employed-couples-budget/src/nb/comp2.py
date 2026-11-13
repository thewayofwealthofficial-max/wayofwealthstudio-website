import sys; sys.path.insert(0,'/home/claude/nbkit'); import nb
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
BANDS={}; _c=nb.composite2
def _comp(raw,out,assign,**k):
    img=_c(raw,out,assign,**k); BANDS[out or 'photos/03.jpg']=nb.LAST_BAND; return img
nb.composite2=_comp
SH='/home/claude/work/secouples/shots/'; R='raw/s'; P='photos/'; BG=(246,241,234)
F='/home/claude/fonts/'
L=lambda n: Image.open(SH+n+'.png').convert('RGB')
def pad(im,aspect,bg=BG,align='top'):
    w,h=im.size
    if w/h>aspect:
        c=Image.new('RGB',(w,int(w/aspect)),bg); c.paste(im,(0,0 if align=='top' else (int(w/aspect)-h)//2)); return c
    W=int(h*aspect); c=Image.new('RGB',(W,h),bg); c.paste(im,((W-w)//2,0)); return c
def stack(parts,gap=30,bg=BG):
    W=max(p.width for p in parts); H=sum(p.height for p in parts)+gap*(len(parts)-1)
    c=Image.new('RGB',(W,H),bg); y=0
    for p in parts: c.paste(p,((W-p.width)//2,y)); y+=p.height+gap
    return c
def hcat(parts,bg=BG):
    W=sum(p.width for p in parts); H=max(p.height for p in parts); c=Image.new('RGB',(W,H),bg); x=0
    for p in parts: c.paste(p,(x,0)); x+=p.width
    return c
def scr(k,i=0):
    g=nb.screens(Image.open(R+k+'.png').convert('RGB'))[i]; return g[2]-g[0],g[3]-g[1]
def raw(k): return Image.open(R+k+'.png').convert('RGB')
def erase_rows(im,box,xs1,xs2=None):
    """fill box row by row with colour interpolated between samples at x=xs1 and x=xs2"""
    a=np.array(im).astype(float); x0,y0,x1,y1=box
    for y in range(y0,y1):
        c1=a[y,xs1-3:xs1+3].mean(0); c2=a[y,xs2-3:xs2+3].mean(0) if xs2 else c1
        t=np.linspace(0,1,x1-x0)[:,None]; a[y,x0:x1]=c1*(1-t)+c2*t
    return Image.fromarray(a.clip(0,255).astype('uint8'))
def text_c(im,cx,y,txt,font,fill):
    d=ImageDraw.Draw(im); w=d.textlength(txt,font=font); d.text((cx-w/2,y),txt,font=font,fill=fill)
def text_l(im,x,y,txt,font,fill): ImageDraw.Draw(im).text((x,y),txt,font=font,fill=fill)
d=L('dash')
# ---- 01 hero: remove keys
r=raw('01'); a=np.array(r).astype(int)
m=np.zeros(a.shape[:2],bool)
for y in range(1490,1730):
    ref=a[y,355:365].mean(0); diff=np.abs(a[y,30:345]-ref).sum(1); m[y,30:345]=diff>20
m[:1590,250:]=False  # keep laptop corner
m=ndimage.binary_dilation(m,iterations=8)
r=Image.fromarray(cv2.inpaint(np.array(r),m.astype('uint8')*255,9,cv2.INPAINT_TELEA)); r.save('raw/s01_nokeys.png')
lap=d.crop((0,0,2950,1840)); ph=d.crop((40,420,1450,3520))
nb.composite2('raw/s01_nokeys.png',P+'01.jpg',[(lap,'tab'),(ph,'phone')])
# ---- 02 included: subtitle fix
r=raw('02'); a=np.array(r).astype(int); tm=np.zeros(a.shape[:2],bool)
tm[285:395,320:1730]=((a[...,0]-a[...,2])>45)[285:395,320:1730]
tm=ndimage.binary_dilation(tm,iterations=5); r=Image.fromarray(cv2.inpaint(np.array(r),tm.astype('uint8')*255,7,cv2.INPAINT_TELEA))
text_c(r,1024,288,'Start Here plus 8 working tabs.',ImageFont.truetype(F+'PF-500-italic.ttf',86),(163,120,62))
r.resize((2000,2000),Image.LANCZOS).save(P+'02.jpg',quality=90)
# ---- 03 dashboard KPIs: redraw leader lines
r=raw('03'); a=np.array(r).astype(int)
gold=(a[...,0]>140)&(a[...,0]-a[...,2]>40)&(a[...,1]>90)
M=np.zeros(gold.shape,bool)
for (x0,y0,x1,y1) in [(584,548,710,590),(680,548,710,790),(1340,548,1468,590),(1340,548,1372,790),(680,1500,710,1730),(554,1690,710,1730),(1340,1500,1372,1730),(1340,1690,1496,1730)]:
    M[y0:y1,x0:x1]=gold[y0:y1,x0:x1]
M=ndimage.binary_dilation(M,iterations=4)
r=Image.fromarray(cv2.inpaint(np.array(r),M.astype('uint8')*255,6,cv2.INPAINT_TELEA)); r.save('raw/s03_nolines.png')
tab=d.crop((0,0,2950,2080))
img=nb.composite2('raw/s03_nolines.png',None,[(tab,'tab')])
rr=1199/2950; k=2000/2048
X=lambda q: 425+q*4*rr; Y=lambda q: 758+q*4*rr
D=ImageDraw.Draw(img); G=(176,136,80)
def line(pts):
    P2=[(x*k,y*k) for x,y in pts]; D.line(P2,fill=G,width=5,joint='curve')
    ex,ey=P2[-1]; D.ellipse((ex-12,ey-12,ex+12,ey+12),fill=G,outline=(255,255,255),width=4)
line([(578,566),(X(370),566),(X(370),Y(150)),(X(330),Y(150))])   # safe to spend -> navy card
line([(1474,566),(X(462),566),(X(462),Y(116))])                    # tax pot -> TAX POT card
line([(300,1664),(300,Y(291)),(X(16),Y(291))])                     # next step -> NEXT STEP bar
line([(1502,1710),(X(335),1710),(X(335),Y(377))])                  # your split -> OUR SPLIT card
img.save(P+'03.jpg',quality=90); print('03 fringe',nb.fringe_count(img))
# ---- 04 charts (new scene s11)
B=lambda x0,y0: d.crop((x0,y0,x0+1372,y0+864))
row1=hcat([B(62,1684),Image.new('RGB',(40,864),BG),B(62,2664),Image.new('RGB',(40,864),BG),B(1566,2664)])
row2=hcat([B(1566,1684),Image.new('RGB',(40,864),BG),B(62,3644)])
r2=Image.new('RGB',(row1.width,864),BG); r2.paste(row2,((row1.width-row2.width)//2,0))
ch=stack([row1,r2],gap=40); w,h=scr('11'); nb.composite2(R+'11.png',P+'04.jpg',[(pad(ch,w/h,align='mid'),'tab')])
# ---- 05 tax pot (scene s04): filled rows only, stacked
tp=L('taxpot'); w,h=scr('04')
src=stack([tp.crop((0,0,1660,190)),tp.crop((40,440,1640,812)),hcat([tp.crop((1650,450,2990,1590))])],gap=20)
nb.composite2(R+'04.png',P+'05.jpg',[(pad(src,w/h),'tab')])
# ---- 06 buffer (scene s05): blob out, full Dec row + year so far
r=raw('05'); r=erase_rows(r,(0,980,300,1318),300); r.save('raw/s05_noblob.png')
w,h=scr('05'); nb.composite2('raw/s05_noblob.png',P+'06.jpg',[(pad(L('buffer').crop((0,0,2560,1530)),w/h),'tab')])
# ---- 07 shared bills (scene s06): filled rows + total, category column removed
bl=L('bills'); w,h=scr('06')
cols=hcat([bl.crop((0,0,665,1060)),bl.crop((1170,0,2960,1060))])
tot=hcat([bl.crop((0,2050,665,2120)),bl.crop((1170,2050,2960,2120))])
title=bl.crop((0,0,2455,395))
body=hcat([bl.crop((0,420,665,1438)),bl.crop((1170,420,2960,1438))])
src=stack([title,body,tot],gap=0)
nb.composite2(R+'06.png',P+'07.jpg',[(pad(src,w/h),'tab')])
# ---- 08 money talk (scene s07)
nb.composite2(R+'07.png',P+'08.jpg',[(L('talk'),'tab')])
# ---- 09 steps (scene s08): factual line
r=raw('08'); r=erase_rows(r,(300,1735,1745,1835),290,1760)
text_c(r,1024,1738,'Settings: 12 yellow boxes, filled in once.',ImageFont.truetype(F+'PF-700-italic.ttf',78),(182,138,80)); r.save('raw/s08_line.png')
nb.composite2('raw/s08_line.png',P+'09.jpg',[(L('settings'),'tab')])
# ---- 10 compatibility (scene s09): Income Log kept left of the phone
lw=1478-434-24; il=L('income').crop((0,0,2711,1849)); lh=1489-728
sc=min(lw/il.width,lh/il.height); c=Image.new('RGB',(int(1181/sc),int(lh/sc)),BG); c.paste(il,(0,0))
nb.composite2(R+'09.png',P+'10.jpg',[(c,'tab'),(ph,'phone')])
# ---- 11 reasons: own sub-lines
r=raw('10'); f=ImageFont.truetype(F+'PF-400-italic.ttf',60)
for (y0,y1,base,txt) in [(1198,1278,1258,"Jordan and Riley's year, then yours"),(1476,1562,1538,'Works in free Google Sheets. Locked in Excel.'),(1755,1840,1816,'One payment. Yours to keep.')]:
    r=erase_rows(r,(452,y0,1578,y1),1584)
    ImageDraw.Draw(r).text((463,base),txt,font=f,fill=(132,94,46),anchor='ls')
r.resize((2000,2000),Image.LANCZOS).save(P+'11.jpg',quality=90)

import glob
for p in sorted(glob.glob(P+'*.jpg')):
    for _ in range(3):
        im=Image.open(p).convert('RGB'); n=nb.fringe_count(im)
        if n==0: break
        im=nb.defringe(im); im.save(p,quality=90)
    if p in BANDS:
        for _ in range(3):
            im=Image.open(p).convert('RGB')
            if not nb.spill_mask(im,BANDS[p]).sum(): break
            nb.despill(im,BANDS[p]).save(p,quality=90)
    im=Image.open(p).convert('RGB')
    print(p,'green(G>100,+40)',nb.fringe_count(im),'edge spill(G>max(R,B)+15)',int(nb.spill_mask(im,BANDS[p]).sum()) if p in BANDS else '-')
