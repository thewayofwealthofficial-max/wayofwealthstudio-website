from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os, subprocess, shutil
OUT=1080; FPS=30; F='/home/claude/fonts/'
H=lambda s: ImageFont.truetype(F+'PF-700-normal.ttf',s); IT=lambda s: ImageFont.truetype(F+'PF-400-italic.ttf',s)
INK=(43,38,32); GOLD=(169,132,74)
VX,VY,VW,VH=50,260,980,620
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
CACHE={}
def L(p):
    if p not in CACHE: CACHE[p]=Image.open(p).convert('RGB')
    return CACHE[p]
def frame(src,win,title,sub,hl=None):
    x,y,w=win; h=w*VH/VW
    s=L(src); pad=Image.new('RGB',(max(s.width,int(x+w)+1),max(s.height,int(y+h)+1)),(246,241,234)); pad.paste(s,(0,0))
    view=pad.crop((int(x),int(y),int(x+w),int(y+h))).resize((VW,VH),Image.LANCZOS)
    im=BG.copy(); im.paste(view,(VX,VY),MASK); d=ImageDraw.Draw(im)
    d.rounded_rectangle((VX,VY,VX+VW,VY+VH),22,outline=(205,185,155),width=2)
    if hl:
        r=VW/w; a,b,c,e=hl; d.rounded_rectangle((VX+(a-x)*r-6,VY+(b-y)*r-6,VX+(c-x)*r+6,VY+(e-y)*r+6),10,outline=GOLD,width=6)
    for txt,f,yy,c in [(title,H(66),70,INK),(sub,IT(40),165,GOLD)]:
        tw=d.textlength(txt,font=f); d.text(((OUT-tw)/2,yy),txt,font=f,fill=c)
    return im
def lerp(a,b,t): t=t*t*(3-2*t); return tuple(p+(q-p)*t for p,q in zip(a,b))
fr=[]
def add(img,sec): fr.extend([img]*int(sec*FPS))
def fade(img,sec=0.3):
    a=fr[-1]; n=int(sec*FPS); fr.extend(Image.blend(a,img,k/n) for k in range(1,n+1))
cover=Image.open('/home/claude/work/secouples/photos/01.jpg').convert('RGB').resize((OUT,OUT),Image.LANCZOS)
def zoom(img,sec,z0,z1):
    n=int(sec*FPS)
    for k in range(n):
        z=z0+(z1-z0)*k/max(1,n-1); c=OUT/z; o=(OUT-c)/2; fr.append(img.crop((o,o,o+c,o+c)).resize((OUT,OUT),Image.LANCZOS))
S='/home/claude/work/secouples/vid/stg/'
s=[S+f's{i}_p4.png' for i in range(3)]; d0,d3=S+'d0_p1.png',S+'d3_p1.png'
W0=(0,0,2711); W1=(40,880,1100); W2=(1440,880,1100)
T1,S1='Log a new month',"Riley's pay is in: 3,350"
zoom(cover,1.3,1.0,1.04)
fade(frame(s[0],W0,T1,S1,hl=(2140,1180,2530,1252)),0.3); add(fr[-1],0.9)
n=int(0.8*FPS)
for k in range(n): fr.append(frame(s[0],lerp(W0,W1,k/(n-1)),T1,S1))
add(fr[-1],0.3)
add(frame(s[0],W1,T1,'Now Jordan\'s month'),0.5)
add(frame(s[1],W1,T1,'Money in: 6,400'),0.8)
add(frame(s[2],W1,T1,'Business costs: 450'),0.8)
T2,S2='Tax set aside for you','25% of profit, worked out'
n=int(0.7*FPS)
for k in range(n): fr.append(frame(s[2],lerp(W1,W2,k/(n-1)),T2,S2))
f=frame(s[2],W2,T2,S2,hl=(1440,1180,2130,1252)); fade(f,0.25); add(f,1.3)
T3,S3='Your dashboard updates','Tax pot and buffer, before'
DW0=(0,0,2796); DW1=(0,250,2000)
fade(frame(d0,DW0,T3,S3),0.35); add(fr[-1],0.4)
n=int(0.7*FPS)
for k in range(n): fr.append(frame(d0,lerp(DW0,DW1,k/(n-1)),T3,S3))
add(fr[-1],0.4)
f=frame(d3,DW1,T3,'Tax pot $2,685 now $4,173',hl=(1340,352,1842,893)); fade(f,0.25); add(f,2.2)
fade(cover,0.4); zoom(cover,1.3,1.04,1.0)
print(len(fr)/FPS)
shutil.rmtree('fr',ignore_errors=True); os.makedirs('fr')
for i,im in enumerate(fr): im.save(f'fr/{i:04d}.jpg',quality=92)
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i','fr/%04d.jpg','-c:v','libx264','-preset','veryfast','-crf','24','-pix_fmt','yuv420p','-an','-movflags','+faststart','/home/claude/work/secouples/video.mp4'],check=True)
