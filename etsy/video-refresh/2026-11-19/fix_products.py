# Layout fixes found while filming (no formula or data changes). Writes fixed copies to work/fixed/.
import openpyxl, os, sys
from openpyxl.drawing.spreadsheet_drawing import OneCellAnchor, AnchorMarker
from openpyxl.chart.label import DataLabelList
V=os.path.dirname(os.path.abspath(__file__)); OUT=V+'/work/fixed'; os.makedirs(OUT,exist_ok=True)
def move(ch,col,row):  # 0-based col/row of the chart's top-left cell
    a=ch.anchor; dc=col-a._from.col; dr=row-a._from.row
    a._from.col+=dc; a._from.row+=dr
    if getattr(a,'to',None) is not None: a.to.col+=dc; a.to.row+=dr

# 1) ADHD Money Companion Tracker
wb=openpyxl.load_workbook('/home/claude/inputs/adhdwb/x/ADHD_Money_Companion_Tracker.xlsx')
d=wb['Dashboard']
d.column_dimensions['A'].width=22          # trigger labels were cut off ("Dopamine Chas", "Rejection Sensit")
pie,bar=d._charts
print('anchors', type(pie.anchor).__name__, type(bar.anchor).__name__)
move(pie,5,6); pie.anchor.to.row=21; move(bar,5,22); bar.anchor.to.row=44   # pie F7:K21, bar F23:K44 (inside the cream area): bar chart used to sit on top of the pie and cover the section headings
for s in pie.series:                         # pie labels read "No - Avoided; Count; 1; 20%": keep category + percent only
    dl=s.dLbls
    for lab in [dl]+list(dl.dLbl or []):
        lab.showSerName=False; lab.showLegendKey=False; lab.showVal=False; lab.showCatName=True; lab.showPercent=True
# Total Impulse Spend summed every logged row, including purchases marked "No - Resisted" or "Returned It".
d['G4']="=SUMIF('Impulse Spend Log'!F5:F100,\"Yes\",'Impulse Spend Log'!C5:C100)"
# KPI card labels were 9 pt (about 2 mm on a laptop screen): now 11 pt, row 3 a little taller
for col in 'ACEGIK':
    c=d[f'{col}3']; f=c.font.copy(sz=11); c.font=f
d.row_dimensions[3].height=18
m=wb['Money Task Log']
m.column_dimensions['B'].width=12           # "Wednesday" wrapped to "Wednesda / y"
m.column_dimensions['E'].width=13           # header "Completed?" wrapped to "Completed / ?"
# empty log rows were a fixed 15 pt, so any wrapped entry (e.g. "Yes - Waited 24hrs", a long task) was cut in half
for r in range(10,151): m.row_dimensions[r].height=27.75
im=wb['Impulse Spend Log']
im.column_dimensions['E'].width=20          # "Did Not Think To" / "Yes - Waited 24hrs" filled the cell edge to edge
for r in range(8,101): im.row_dimensions[r].height=27.75
wb.save(OUT+'/ADHD_Money_Companion_Tracker.xlsx')

# 2) ADHD Spending Tracker
wb=openpyxl.load_workbook('/home/claude/inputs/adhdspend/x/ADHD_Spending_Tracker.xlsx')
s=wb['Spending Log']; s.column_dimensions['I'].width=40   # Pattern Note was cut to its middle line ("impulse — check your"); 40 fits the longest note on one line
d=wb['Dashboard']
pie,bar=d._charts
move(bar,1,40)                               # Spending by Category chart (B34) covered the Satisfaction Insights table B35:C39; now B41
# ADHD Insight said "Your impulse rate is low — great pattern awareness." on a blank file: neutral prompt until something is logged
f5=d['F5'].value; assert f5.startswith('=IF(')
d['F5']='=IF(COUNTA(\'Spending Log\'!D5:D104)=0,"Log a few purchases and your pattern will show here.",'+f5[1:]+')'
p=wb['Profile']; p.column_dimensions['C'].width=42; p.column_dimensions['D'].width=50  # dropdown answers and notes were cut off
wb.save(OUT+'/ADHD_Spending_Tracker.xlsx')
print('ok')
