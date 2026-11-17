import os, subprocess, shutil
from PIL import Image, ImageDraw, ImageFilter, ImageFont
V=os.path.dirname(os.path.abspath(__file__)); S=V+'/se'
F='/home/claude/fonts/'; IN='/usr/share/fonts/opentype/inter/'
pf=lambda s: ImageFont.truetype(F+'PF-700-normal.ttf',s); pfi=lambda s: ImageFont.truetype(F+'PF-400-italic.ttf',s); pfr=lambda s: ImageFont.truetype(F+'PF-400-normal.ttf',s)
INK=(42,38,32); GOLD=(184,149,110); GOLD_D=(160,122,74); OUT=1080; FPS=30
def bg():
    im=Image.new('RGB',(OUT,OUT)); d=ImageDraw.Draw(im)
    for y in range(OUT):
        t=y/OUT; d.line([(0,y),(OUT,y)],fill=tuple(int(a+(b-a)*t) for a,b in zip((252,244,236),(244,232,216))))
    f=pfr(22); txt='W A Y   O F   W E A L T H   S T U D I O'
    d.text((OUT/2,1040),txt,font=f,fill=GOLD_D,anchor='mm')
    return im
BG=bg()
L=lambda st,p: Image.open(f'{S}/h{st}-{p}.png').convert('RGB')
k=4  # 400 dpi = 4 x the 100-dpi measurements
def box(b): return tuple(int(v*k) for v in b)
def frame(src, title, sub, hl=None, zoom=1.0):
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
# income log measurements (100 dpi): header 162-182, row n top = 182+16.5*(n-1)
rowt=lambda n: 200.5+20.2*(n-1)
HEAD=(163,rowt(1)); 
def logcrop(st,x0,x1,r0=4,r1=8):
    im=L(st,4); head=im.crop(box((x0,HEAD[0],x1,HEAD[1]))); body=im.crop(box((x0,rowt(r0),x1,rowt(r1+1))))
    c=Image.new('RGB',(head.width,head.height+body.height),(255,255,255)); c.paste(head,(0,0)); c.paste(body,(0,head.height))
    hl=(0,head.height+(rowt(7)-rowt(r0))*k,head.width,head.height+(rowt(8)-rowt(r0))*k)
    return c,hl
frames=[]
def hold(img,sec): frames.extend([img]*round(sec*FPS))
def fade(a,b,sec=0.3):
    n=round(sec*FPS)
    for i in range(n): frames.append(Image.blend(a,b,(i+1)/n))
hero=Image.open(S+'/hero1.jpg').convert('RGB').resize((OUT,OUT),Image.LANCZOS)
full,_=logcrop(0,97,389,1,7)
f_full=frame(full,'Log every expense','Your Expense Log, one row each')
A=lambda st: logcrop(st,97,389)
B=lambda st: logcrop(st,388,756)
seq=[]
hold(hero,1.2); fade(hero,f_full); hold(f_full,1.2)
prev=f_full
for st in (1,2):
    c,hl=A(st); fr=frame(c,'Add an expense','Date, then pick a category',hl)
    if st==1: fade(prev,fr)
    hold(fr,1.1); prev=fr
for st in (3,4,5):
    c,hl=B(st); fr=frame(c,'Add an expense','What it was and how much',hl)
    if st==3: fade(prev,fr)
    hold(fr,1.0 if st<5 else 1.5); prev=fr
def dc(st):
    im=L(st,5); a=im.crop(box((96,143,318,196))); b=im.crop(box((573,235,906,256))); r=im.crop(box((573,460,906,482))); b2=Image.new('RGB',(b.width,b.height+r.height),(255,255,255)); b2.paste(b,(0,0)); b2.paste(r,(0,b.height)); b=b2
    sc=b.width/a.width; a=a.resize((b.width,round(a.height*sc)),Image.LANCZOS)
    c=Image.new('RGB',(a.width,a.height+b.height+40),(246,241,234)); c.paste(a,(0,0)); c.paste(b,(0,a.height+40)); return c
d0=frame(dc(0),'Your dashboard updates','Before the new expense')
d1=frame(dc(5),'Your dashboard updates','After: total and November updated',(0,0,dc(5).width,dc(5).height))
fade(prev,d0); hold(d0,1.5); hold(d1,1.8); fade(d1,hero); hold(hero,0.8)
tmp=V+'/frames'; shutil.rmtree(tmp,ignore_errors=True); os.makedirs(tmp)
for i,f in enumerate(frames): f.save(f'{tmp}/f{i:04d}.png')
out=V+'/Self Employed Expense Tracker - video NEW.mp4'
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i',f'{tmp}/f%04d.png','-c:v','libx264','-pix_fmt','yuv420p','-crf','24','-movflags','+faststart',out],check=True)
print(len(frames)/FPS,'s', os.path.getsize(out))
