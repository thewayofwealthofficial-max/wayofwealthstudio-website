# render(xlsx, outprefix, areas={sheet: 'A1:H20'}, dpi) -> one PNG per listed sheet, fit to width, via LibreOffice (formulas recalc)
import openpyxl, subprocess, os, glob, sys
def render(wb, out, areas, dpi=400):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    names=list(areas)
    for s in list(wb.sheetnames):
        if s not in areas: wb[s].sheet_state='hidden'
    for s,a in areas.items():
        ws=wb[s]; ws.page_setup.orientation='landscape'; ws.page_setup.fitToWidth=1; ws.page_setup.fitToHeight=1
        ws.sheet_properties.pageSetUpPr.fitToPage=True; ws.print_area=a
        ws.print_options.horizontalCentered=False
        for m in ('left','right','top','bottom'): setattr(ws.page_margins,m,0.2)
    wb.active=wb.sheetnames.index(names[0])
    f=out+'.xlsx'; wb.save(f)
    subprocess.run(['soffice','--headless','--convert-to','pdf','--outdir',os.path.dirname(out),f],capture_output=True,check=True)
    for q in glob.glob(out+'-*.png'): os.remove(q)
    subprocess.run(['pdftoppm','-r',str(dpi),'-png',out+'.pdf',out],check=True)
    return sorted(glob.glob(out+'-*.png'))
if __name__=='__main__':
    wb=openpyxl.load_workbook(sys.argv[1]); print(render(wb,sys.argv[2],dict(a.split('=') for a in sys.argv[3:]),dpi=60))
