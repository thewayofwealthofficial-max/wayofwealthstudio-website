# Filled EXAMPLE copy of the fixed ADHD Spending Tracker (the listing promises "Example Spreadsheet with sample data").
# Same demo data as the video: a filled Profile, 10 purchases and one weekly Mindset Check.
import openpyxl, os, sys
V=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,V)
src=open(V+'/stages_spend.py').read().split('# typed in order')[0]   # profile + log definitions only
ns={'__file__':V+'/stages_spend.py'}; exec(src.replace('from render import render',''),ns)
wb=openpyxl.load_workbook(V+'/work/fixed/ADHD_Spending_Tracker.xlsx')
p=wb['Profile']; p['C5']='Maya'; p['C7']=2800; p['C9']='Regular (Salary)'; p['C11']='Online Shopping'; p['C13']='Dopamine Shopping (buy for the thrill)'
ws=wb['Spending Log']
for k,row in enumerate(ns['log']+[ns['new']]):
    for c,v in zip('BCDEFGH',row):
        if v!='': ws[f'{c}{5+k}']=v
m=wb['Mindset Check']; import datetime as dt
m["B5"]=dt.datetime(2026,11,16)
m['C5']='Earbuds at 11pm after a long, boring evening'; m['D5']='Bored and a bit flat, wanted something new'
m['E5']='Phone on charge in the kitchen after 10pm'
os.makedirs(V+'/work/example',exist_ok=True); out=V+'/work/example/ADHD_Spending_Tracker_EXAMPLE.xlsx'; wb.save(out); print(out)
