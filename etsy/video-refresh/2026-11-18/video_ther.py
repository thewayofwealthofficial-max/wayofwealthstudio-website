# Therapist Self Employed Tax Tracker 4527554740 - in-use video from LibreOffice renders of openpyxl copies (stages_ther.py)
import os, subprocess, shutil
from PIL import Image, ImageDraw, ImageFilter, ImageFont
V=os.path.dirname(os.path.abspath(__file__)); W_=V+'/work'; S=W_+'/st'
F='/home/claude/fonts/'
pf=lambda s: ImageFont.truetype(F+'PF-700-normal.ttf',s); pfi=lambda s: ImageFont.truetype(F+'PF-400-italic.ttf',s); pfr=lambda s: ImageFont.truetype(F+'PF-400-normal.ttf',s)
INK=(42,38,32); GOLD_D=(160,122,74); OUT=1080; FPS=30; k=4
def bg():
    im=Image.new('RGB',(OUT,OUT)); d=ImageDraw.Draw(im)
    for y in range(OUT):
        t=y/OUT; d.line([(0,y),(OUT,y)],fill=tuple(int(a+(b-a)*t) for a,b in zip((252,244,236),(244,232,216))))
    d.text((OUT/2,1040),'W A Y   O F   W E A L T H   S T U D I O',font=pfr(22),fill=GOLD_D,anchor='mm')
    return im
BG=bg()
L=lambda st,p: Image.open(f'{S}/s{st}-{p}.png').convert('RGB')
def frame(src, title, sub, hl=None):
    im=BG.copy(); d=ImageDraw.Draw(im)
    d.text((OUT/2,92),title,font=pf(64),fill=INK,anchor='mm')
    d.text((OUT/2,168),sub,font=pfi(42),fill=GOLD_D,anchor='mm')
    W=1000; sc=W/src.width; h=round(src.height*sc)
    if h>760: sc=760/src.height; h=760; W=round(src.width*sc)
    x0=(OUT-W)//2; top=240+(760-h)//4
    sh=Image.new('L',(OUT,OUT),0); ImageDraw.Draw(sh).rounded_rectangle((x0,top+12,x0+W,top+h+12),20,fill=80)
    im.paste((150,115,70),(0,0),sh.filter(ImageFilter.GaussianBlur(16)))
    view=src.resize((W,h),Image.LANCZOS)
    m=Image.new('L',(W,h),0); ImageDraw.Draw(m).rounded_rectangle((0,0,W-1,h-1),20,fill=255)
    im.paste(view,(x0,top),m)
    if hl:
        a,b,c,e=hl; d.rounded_rectangle((x0+a*sc-6,top+b*sc-6,x0+c*sc+6,top+e*sc+6),12,outline=(176,128,60),width=6)
    return im
bx=lambda b: tuple(int(v*k) for v in b)
# Income Tracker (page 4) measurements at 100 dpi: header 170-205, row n top = 205+19.8*(n-1); new session = row 9
rowt=lambda n: 205+19.8*(n-1)
def logcrop(st,x0,x1,r0=6,r1=10,hlrow=9):
    im=L(st,4); head=im.crop(bx((x0,170,x1,205))); body=im.crop(bx((x0,rowt(r0),x1,rowt(r1+1))))
    c=Image.new('RGB',(head.width,head.height+body.height),(255,255,255)); c.paste(head,(0,0)); c.paste(body,(0,head.height))
    hl=(0,head.height+(rowt(hlrow)-rowt(r0))*k,head.width,head.height+(rowt(hlrow+1)-rowt(r0))*k)
    return c,hl
frames=[]
def hold(img,sec): frames.extend([img]*round(sec*FPS))
def fade(a,b,sec=0.3):
    n=round(sec*FPS)
    for i in range(n): frames.append(Image.blend(a,b,(i+1)/n))
hero=Image.open(W_+'/hero_t.jpg').convert('RGB').resize((OUT,OUT),Image.LANCZOS)
# 1 the real Income Tracker tab
f_full=frame(L(0,4).crop(bx((90,112,361.5,365))),'Log every session','Your Income Tracker, one row each')
hold(hero,1.2); fade(hero,f_full); hold(f_full,1.4); prev=f_full
# 2 zoom into the new row: date, then session type
for st,sec in ((0,0.3),(1,0.6),(2,1.0)):
    c,hl=logcrop(st,97,361); fr=frame(c,'Add a new session','Date, then session type',hl)
    if st==0: fade(prev,fr)
    hold(fr,sec); prev=fr
# 3 client code typed word by word, then the fee
for st,sec in ((2,0.3),(3,0.45),(4,0.6),(5,0.9)):
    c,hl=logcrop(st,361,654); fr=frame(c,'Add a new session','Client code, then the fee',hl)
    if st==2: fade(prev,fr)
    hold(fr,sec); prev=fr
# 4 pan up to the running total
T=(92,108,400,168.6)
def totcrop(st):  # sheet's cream title band, padded below with the same cream so the box sits inside the screen
    c=L(st,4).crop(bx(T)); p=Image.new('RGB',(c.width,c.height+14*k),c.getpixel((8,8))); p.paste(c,(0,0)); return p
t0=frame(totcrop(4),'Totals update instantly','Total income before the fee')
t1=frame(totcrop(5),'Totals update instantly','After: up by the £75 fee',((252-92)*k,(146-108)*k,(366-92)*k,(169-108)*k))
fade(prev,t0); hold(t0,0.6); hold(t1,0.9)
# 5 Tax Summary set-aside before / after (page 7)
# label and amount cells of the real render, stacked so the labels read at ~40 px on a phone
CREAM=(245,240,232)
def taxstack(st):
    im=L(st,7); parts=[('l',(95,341,385,382)),('v',(390,339,562,384)),('l',(95,383,385,451)),('v',(390,382,562,452))]
    W=300*k; crops=[im.crop(bx(b)) for _,b in parts]; gap=10*k
    H=sum(c.height for c in crops)+gap*3; c=Image.new('RGB',(W,H),CREAM); y=0; boxes=[]
    for (kind,_),cr in zip(parts,crops):
        x=5*k if kind=='l' else (W-cr.width)//2
        c.paste(cr,(x,y)); boxes.append((x,y,x+cr.width,y+cr.height)); y+=cr.height+gap
    return c,boxes
s4,_=taxstack(4); s5,bxs=taxstack(5); vb=bxs[1]
d0=frame(s4,'Tax to set aside each month','Before the new session')
d1=frame(s5,'Tax to set aside each month','After: monthly amount boxed',(vb[0]+2*k,vb[1]+2*k,vb[2]-2*k,vb[3]-2*k))
fade(t1,d0); hold(d0,1.2); hold(d1,1.8); fade(d1,hero); hold(hero,1.0)
tmp=W_+'/frames_t'; shutil.rmtree(tmp,ignore_errors=True); os.makedirs(tmp)
for i,f in enumerate(frames): f.save(f'{tmp}/f{i:04d}.png')
out=V+'/Therapist Self Employed Tax Tracker 4527554740 - video NEW.mp4'
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i',f'{tmp}/f%04d.png','-c:v','libx264','-pix_fmt','yuv420p','-crf','24','-movflags','+faststart',out],check=True)
print(len(frames)/FPS,'s', os.path.getsize(out))
