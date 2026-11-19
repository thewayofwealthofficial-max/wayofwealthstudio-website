# openpyxl copies of the FIXED ADHD Money Companion Tracker with one impulse purchase typed in step by step; LibreOffice renders each.
import openpyxl, datetime as dt, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import render
V=os.path.dirname(os.path.abspath(__file__))
SRC=V+'/work/fixed/ADHD_Money_Companion_Tracker.xlsx'; OUT=V+'/work/wbst'
new=dict(A=dt.datetime(2026,11,18),B='Trainers — 1am scroll',C=59,D='Tired',E='Yes - Waited 24hrs',F='Yes',G=2)
order=[('A',None),('B','Trainers'),('B',None),('C',None),('D',None),('E',None),('F',None),('G',None)]
steps=[{}]; cur={}
for k,partial in order:
    cur=dict(cur); cur[k]=partial or new[k]; steps.append(cur)
only=[int(a) for a in sys.argv[1:]] or range(len(steps))
for i in only:
    wb=openpyxl.load_workbook(SRC); ws=wb['Impulse Spend Log']
    for k,v in steps[i].items(): ws[f'{k}8']=v
    print(i, steps[i], render(wb, f'{OUT}/s{i}', {'Impulse Spend Log':'A1:H12','Dashboard':'A1:L26'}))
