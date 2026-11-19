# openpyxl copies of the real ADHD Spending Tracker: profile + example log, then one impulse purchase typed in step by step.
# LibreOffice renders each copy, so every formula (pattern note, dashboard) recalculates.
import openpyxl, datetime as dt, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import render
V=os.path.dirname(os.path.abspath(__file__))
SRC=sys.argv[1] if len(sys.argv)>1 else V+'/work/fixed/ADHD_Spending_Tracker.xlsx'  # the FIXED copy (fix_products.py)
OUT=V+'/work/sp'
D=dt.datetime
log=[(D(2026,11,2),'Weekly food shop',64.20,'Groceries','Planned',4,''),
     (D(2026,11,3),'Bus pass',38.00,'Transport','Planned',4,''),
     (D(2026,11,5),'Takeaway after a long day',22.50,'Food & Takeaway','Semi-Impulse',3,'Too tired to cook'),
     (D(2026,11,7),'Phone bill',18.00,'Utilities','Planned',3,''),
     (D(2026,11,8),'Candle set from an Instagram ad',34.00,'Home & Decor','Impulse',2,'Scrolling in bed'),
     (D(2026,11,10),'Streaming add-on',9.99,'Subscriptions','Impulse',2,'Free trial rolled over'),
     (D(2026,11,12),'Weekly food shop',58.75,'Groceries','Planned',4,''),
     (D(2026,11,14),'Birthday gift for Sam',25.00,'Gifts','Planned',5,''),
     (D(2026,11,15),'Hobby paints (new hyperfocus)',46.80,'Education','Impulse',4,'Still using them')]
new=(D(2026,11,18),'Wireless earbuds',39.99,'Online Shopping','Impulse',2,'11pm, bored, saw an ad')
cols='BCDEFGH'
# typed in order: date, item (2 keystroke stages), amount, category, impulse?, satisfaction, notes (2 stages)
B,C,Dc,E,F,G,H=new
steps=[{},{'B':B},{'B':B,'C':'Wireless'},{'B':B,'C':C},{'B':B,'C':C,'D':Dc},{'B':B,'C':C,'D':Dc,'E':E},
       {'B':B,'C':C,'D':Dc,'E':E,'F':F},{'B':B,'C':C,'D':Dc,'E':E,'F':F,'G':G},
       {'B':B,'C':C,'D':Dc,'E':E,'F':F,'G':G,'H':'11pm, bored,'},{'B':B,'C':C,'D':Dc,'E':E,'F':F,'G':G,'H':H}]
only=[int(a) for a in sys.argv[2:]] or range(len(steps))
for i in only:
    wb=openpyxl.load_workbook(SRC)
    p=wb['Profile']; p['C5']='Maya'; p['C7']=2800; p['C9']='Regular (Salary)'; p['C11']='Online Shopping'
    p['C13']='Dopamine Shopping (buy for the thrill)'
    ws=wb['Spending Log']
    for k,row in enumerate(log):
        for c,v in zip(cols,row):
            if v!='': ws[f'{c}{5+k}']=v
    r=5+len(log)
    for c,v in steps[i].items(): ws[f'{c}{r}']=v
    print(i, render(wb, f'{OUT}/s{i}', {'Spending Log':'A1:J18','Dashboard':'A1:F12'}))
