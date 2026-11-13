import os, subprocess, shutil, warnings; warnings.filterwarnings('ignore')
import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFilter, ImageFont
OUT=1080; FPS=30; Z=3
F='/home/claude/fonts/'
H=lambda s: ImageFont.truetype(F+'PF-700-normal.ttf',s); IT=lambda s: ImageFont.truetype(F+'PF-400-italic.ttf',s)
INK=(43,38,32); GOLD=(169,132,74)
VX,VY,VW,VH=50,250,980,680
def bg():
    im=Image.new('RGB',(OUT,OUT)); d=ImageDraw.Draw(im)
    for y in range(OUT):
        t=y/OUT; d.line([(0,y),(OUT,y)],fill=tuple(int(a+(b-a)*t) for a,b in zip((249,243,234),(239,228,210))))
    sh=Image.new('L',(OUT,OUT),0); ImageDraw.Draw(sh).rounded_rectangle((VX,VY+20,VX+VW,VY+VH+20),26,fill=110)
    im.paste((120,95,60),(0,0),sh.filter(ImageFilter.GaussianBlur(30)))
    d=ImageDraw.Draw(im); f=ImageFont.truetype(F+'PF-400-normal.ttf',24); t='W A Y   O F   W E A L T H   S T U D I O'
    w=d.textlength(t,font=f); d.text(((OUT-w)/2,1000),t,font=f,fill=GOLD); return im
BG=bg()
MASK=Image.new('L',(VW,VH),0); ImageDraw.Draw(MASK).rounded_rectangle((0,0,VW-1,VH-1),22,fill=255)
def frame(src,win,title,sub,hl=None):
    x,y,w=[v*Z for v in win]; h=w*VH/VW
    view=src.crop((int(x),int(y),int(x+w),int(y+h))).resize((VW,VH),Image.LANCZOS)
    im=BG.copy(); im.paste(view,(VX,VY),MASK); d=ImageDraw.Draw(im)
    d.rounded_rectangle((VX,VY,VX+VW,VY+VH),22,outline=(205,185,155),width=2)
    if hl:
        r=VW/w; a,b,c,e=[v*Z for v in hl]
        d.rounded_rectangle((VX+(a-x)*r-6,VY+(b-y)*r-6,VX+(c-x)*r+6,VY+(e-y)*r+6),10,outline=GOLD,width=6)
    for txt,f,yy,col in [(title,H(64),62,INK),(sub,IT(40),158,GOLD)]:
        tw=d.textlength(txt,font=f); d.text(((OUT-tw)/2,yy),txt,font=f,fill=col)
    return im
def lerp(a,b,t): t=t*t*(3-2*t); return tuple(p+(q-p)*t for p,q in zip(a,b))
frames=[]
def add(img,sec): frames.extend([img]*max(1,int(sec*FPS)))
def fade(img,sec=0.3):
    a=frames[-1]; n=int(sec*FPS); frames.extend(Image.blend(a,img,k/n) for k in range(1,n+1))
def zoom(img,sec,z0,z1):
    n=int(sec*FPS)
    for k in range(n):
        z=z0+(z1-z0)*k/max(1,n-1); c=OUT/z; o=(OUT-c)/2; frames.append(img.crop((o,o,o+c,o+c)).resize((OUT,OUT),Image.LANCZOS))
def pan(src,w0,w1,sec,t,s,hl=None):
    n=int(sec*FPS)
    for k in range(n): frames.append(frame(src,lerp(w0,w1,k/(n-1)),t,s,hl))
PDF='/home/claude/work/premarital/out2/A4-form.pdf'
def render(pn,vals):
    d=fitz.open(PDF); p=d[pn-1]
    for wd in p.widgets():
        k=wd.field_name.rsplit('_p',1)[0]
        if k in vals and wd.field_type_string=='Text':
            wd.field_value=vals[k]; wd.text_fontsize=17; wd.text_color=(0.12,0.2,0.45); wd.update()
    pm=p.get_pixmap(matrix=fitz.Matrix(Z,Z),annots=True)
    return Image.frombytes('RGB',(pm.width,pm.height),pm.samples)
cover=Image.open('/home/claude/work/premarital/photos/01.jpg').convert('RGB').resize((OUT,OUT),Image.LANCZOS)
FULL=(0,0,595)
# ---- scene A: fair split ----
T1,S1='Talk 3: your fair split','Type your answers in the boxes'
W1=(30,108,530)
zoom(cover,1.3,1.0,1.04)
v={}; img=render(9,v); fade(frame(img,FULL,T1,S1),0.3); add(frames[-1],0.4)
pan(img,FULL,W1,0.8,T1,S1)
seq=[('t3_incA','2,450'),('t3_incB','2,100')]
for k,val in seq:
    for i in range(1,len(val)+1):
        v[k]=val[:i]; add(frame(render(9,v),W1,T1,S1,hl=(406,157 if k=='t3_incA' else 187,554,177 if k=='t3_incA' else 207)),0.11)
    add(frames[-1],0.25)
T2,S2='Follow the steps','Each pays the same share of pay'
for k,val in [('t3_tot','4,550'),('t3_pctA','54%'),('t3_pctB','46%'),('t3_bills','1,900')]:
    v[k]=val; add(frame(render(9,v),W1,T2,S2),0.35)
v['t3_payA']='1,026'; v['t3_payB']='874'
fr=frame(render(9,v),W1,T2,S2,hl=(60,337,556,387)); fade(fr,0.2); add(fr,1.4)
# ---- scene B: agreement ----
T3,S3='Agree it together','One page you both sign'
W2=(28,112,544)
v2={}; img=render(13,v2); fade(frame(img,FULL,T3,S3),0.35); add(frames[-1],0.3)
pan(img,FULL,W2,0.7,T3,S3)
for k,val in [('ag_acc','Hybrid: joint for bills, own for the rest'),('ag_split','By income, 54 / 46')]:
    words=val.split(' ')
    for i in range(1,len(words)+1):
        v2[k]=' '.join(words[:i]); add(frame(render(13,v2),W2,T3,S3),0.17)
    add(frames[-1],0.2)
fr=frame(render(13,v2),W2,T3,'Your rules, in writing',hl=(41,172,554,255)); fade(fr,0.2); add(fr,1.3)
fade(cover,0.4); zoom(cover,1.2,1.04,1.0)
print('seconds',len(frames)/FPS)
w='/home/claude/work/premarital/vid/fr'; shutil.rmtree(w,ignore_errors=True); os.makedirs(w)
for i,f in enumerate(frames): f.save(f'{w}/{i:04d}.jpg',quality=92)
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i',f'{w}/%04d.jpg','-c:v','libx264','-preset','veryfast','-crf','24','-pix_fmt','yuv420p','-an','-movflags','+faststart','/home/claude/work/premarital/video.mp4'],check=True)
shutil.rmtree(w)
