"""Way of Wealth Studio app-style spreadsheet skin (cells only, Google Sheets safe).
Built to the spreadsheet-app-design skill: Inter font, cream canvas, white cards, no shapes, no data bars,
no internal links (they break in Google Sheets), IFERROR/blank guards everywhere.
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, Protection
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.chart import BarChart, PieChart, DoughnutChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.drawing.line import LineProperties
from openpyxl.utils import get_column_letter as L

# palette
CREAM = 'F5F0E8'; PAGE = 'F7F3EC'; WHITE = 'FFFFFF'; INK = '2B3445'; MUTED = '7A8296'
SAGE = 'B8C5B0'; DSAGE = '8FA585'; GOLD = 'B8956E'; CORAL = 'D9786A'; INPUT = 'FFF8E1'
LINE = 'E3DCCF'; BAND = 'FBF8F3'; TINT = 'EEF2EA'; GOLDT = 'F4ECE1'; NAVY = '2B3445'
FONT = 'Inter'
SERIES = ['8FA585', 'B8956E', '2B3445', 'D9786A', 'B8C5B0', 'C9B79C', '7A8296', 'E3C7A6']

fill = lambda c: PatternFill('solid', start_color=c, end_color=c)
thin = lambda c=LINE: Side(style='thin', color=c)
MONEY = '#,##0;-#,##0;"–"'
MONEY2 = '#,##0.00;-#,##0.00;"–"'
PCT = '0%'


def F(size=10, bold=False, color=INK, italic=False):
    return Font(name=FONT, size=size, bold=bold, color=color, italic=italic)


class Book:
    def __init__(self, tabs, blank=False, width=8.3, ncols=17, nrows=90):
        self.wb = Workbook(); self.blank = blank; self.tabs = tabs
        self.s = {}
        for i, (t, color) in enumerate(tabs):
            ws = self.wb.active if i == 0 else self.wb.create_sheet()
            ws.title = t
            ws.sheet_view.showGridLines = False
            ws.sheet_view.showRowColHeaders = False
            ws.sheet_view.zoomScale = 100
            ws.sheet_properties.tabColor = color
            self.s[t] = ws
        self.width = width; self.ncols = ncols; self.nrows = nrows

    # ---------------------------------------------------------------- page
    def page(self, ws, title, sub, widths=None, ncols=None, nrows=None):
        ncols = ncols or self.ncols; nrows = nrows or self.nrows
        ws.column_dimensions['A'].width = 3
        for c in range(2, max(ncols, 30) + 2):
            ws.column_dimensions[L(c)].width = (widths or {}).get(c, self.width)
        for r in range(1, nrows + 1):
            for c in range(1, max(ncols, 30) + 2):
                ws.cell(r, c).fill = fill(PAGE)
        ws.row_dimensions[1].height = 14
        c = ws.cell(2, 2, title); c.font = F(20, True); c.alignment = Alignment(vertical='center')
        ws.row_dimensions[2].height = 32
        c = ws.cell(3, 2, sub); c.font = F(10, color=MUTED)
        ws.row_dimensions[3].height = 18
        # step strip (plain text, works in Sheets and Excel; tab bar does the navigating)
        names = [t for t, _ in self.tabs]
        i = names.index(ws.title)
        nxt = names[i + 1] if i + 1 < len(names) else names[0]
        ws.row_dimensions[4].height = 8
        span = ncols - 1
        c = ws.cell(5, 2, f'TAB {i + 1} OF {len(names)}   ·   {ws.title.upper()}   ·   NEXT: {nxt.upper()}  →   use the tabs along the bottom')
        c.font = F(8, True, MUTED); c.alignment = Alignment(vertical='center', indent=1)
        for cc in range(2, 2 + span):
            ws.cell(5, cc).fill = fill(WHITE)
            ws.cell(5, cc).border = Border(top=thin(), bottom=thin(), left=thin() if cc == 2 else None,
                                           right=thin() if cc == 1 + span else None)
        ws.merge_cells(start_row=5, start_column=2, end_row=5, end_column=1 + span)
        ws.row_dimensions[5].height = 22
        ws.row_dimensions[6].height = 12

    # ---------------------------------------------------------------- components
    def box(self, ws, r1, c1, r2, c2, bg=WHITE, edge=LINE):
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                cell = ws.cell(r, c); cell.fill = fill(bg)
                cell.border = Border(left=thin(edge) if c == c1 else None, right=thin(edge) if c == c2 else None,
                                     top=thin(edge) if r == r1 else None, bottom=thin(edge) if r == r2 else None)

    def text(self, ws, r, c, v, size=10, bold=False, color=INK, w=1, h=1, align='left', valign='center', fmt=None,
             wrap=True, italic=False, indent=0):
        cell = ws.cell(r, c, v)
        cell.font = F(size, bold, color, italic)
        cell.alignment = Alignment(horizontal=align, vertical=valign, wrap_text=wrap, indent=indent)
        if fmt: cell.number_format = fmt
        if w > 1 or h > 1:
            ws.merge_cells(start_row=r, start_column=c, end_row=r + h - 1, end_column=c + w - 1)
        return cell

    def hero(self, ws, r, c, w, h, label, value, sentence, how, value_fmt=None):
        self.box(ws, r, c, r + h - 1, c + w - 1, NAVY, NAVY)
        self.text(ws, r, c, label, 8, True, 'E3C7A6', w=w, indent=1, valign='bottom')
        ws.row_dimensions[r].height = 24
        self.text(ws, r + 1, c, value, 34, True, WHITE, w=w, h=2, indent=1, fmt=value_fmt)
        self.text(ws, r + 3, c, sentence, 10, False, 'E8EAEE', w=w, h=h - 5, indent=1, valign='top')
        self.text(ws, r + h - 2, c, how, 8, False, 'A9B0BE', w=w, h=1, indent=1, italic=True)

    def kpi(self, ws, r, c, label, value, sub, w=3, value_fmt=None, accent=None):
        self.box(ws, r, c, r + 2, c + w - 1)
        if accent:
            for cc in range(c, c + w):
                ws.cell(r, cc).border = Border(top=Side(style='medium', color=accent),
                                               left=thin() if cc == c else None, right=thin() if cc == c + w - 1 else None)
        self.text(ws, r, c, label, 7.5, True, MUTED, w=w, indent=1, valign='bottom')
        self.text(ws, r + 1, c, value, 17, True, INK, w=w, indent=1, fmt=value_fmt)
        self.text(ws, r + 2, c, sub, 8, False, MUTED, w=w, indent=1, valign='top')

    def bar(self, ws, r, c, w, label, sentence, bg=TINT, color=INK):
        self.box(ws, r, c, r, c + w - 1, bg, bg)
        self.text(ws, r, c, label, 8, True, DSAGE, indent=1)
        self.text(ws, r, c + 1, sentence, 10, False, color, w=w - 1, indent=1)
        ws.row_dimensions[r].height = 30

    def section(self, ws, r, c, title, w=8):
        self.text(ws, r, c, title, 11, True, INK, w=w)
        ws.row_dimensions[r].height = 22

    def tip(self, ws, r, c, v, w=10, h=1, height=None):
        self.box(ws, r, c, r + h - 1, c + w - 1, GOLDT, GOLDT)
        self.text(ws, r, c, v, 9, False, '6B5B45', w=w, h=h, indent=1)
        if height: ws.row_dimensions[r].height = height

    # table bits
    def th(self, ws, r, c, v, w=1, align='left'):
        cell = self.text(ws, r, c, v, 8, True, MUTED, w=w, align=align, indent=1 if align == 'left' else 0)
        for cc in range(c, c + w):
            ws.cell(r, cc).fill = fill(WHITE)
            ws.cell(r, cc).border = Border(bottom=thin('CFC6B6'))
        return cell

    def inp(self, ws, r, c, v=None, fmt=None, align='left', w=1, keep=False):
        cell = ws.cell(r, c)
        if v is not None and (keep or not self.blank):
            cell.value = v
        for cc in range(c, c + w):
            x = ws.cell(r, cc); x.fill = fill(INPUT)
            x.border = Border(bottom=thin('E6D9B5'), top=thin('E6D9B5'), left=thin('E6D9B5') if cc == c else None,
                              right=thin('E6D9B5') if cc == c + w - 1 else None)
            x.protection = Protection(locked=False)
        cell.font = F(10, color='1F3B73')
        cell.alignment = Alignment(horizontal=align, vertical='center', indent=1 if align == 'left' else 0)
        if fmt: cell.number_format = fmt
        if w > 1: ws.merge_cells(start_row=r, start_column=c, end_row=r, end_column=c + w - 1)
        return cell

    def fx(self, ws, r, c, f, fmt=None, bold=False, bg=None, align='right', w=1, color=INK, size=10):
        cell = ws.cell(r, c, f)
        cell.font = F(size, bold, color)
        cell.alignment = Alignment(horizontal=align, vertical='center', indent=1)
        for cc in range(c, c + w):
            ws.cell(r, cc).fill = fill(bg or (BAND if r % 2 else WHITE))
        if fmt: cell.number_format = fmt
        if w > 1: ws.merge_cells(start_row=r, start_column=c, end_row=r, end_column=c + w - 1)
        return cell

    def dv(self, ws, rng, items=None, ref=None):
        f1 = ref if ref else '"' + ','.join(items) + '"'
        d = DataValidation(type='list', formula1=f1, allow_blank=True)
        ws.add_data_validation(d); d.add(rng)

    def protect(self, ws):
        ws.protection.sheet = True
        ws.protection.formatCells = False; ws.protection.formatColumns = False; ws.protection.formatRows = False

    def save(self, path, areas=None):
        for ws in self.wb.worksheets:
            mr = mc = 1
            for row in ws.iter_rows():
                for c in row:
                    if c.value not in (None, ''):
                        mr = max(mr, c.row); mc = max(mc, c.column)
            for ch in ws._charts:
                from openpyxl.utils.cell import coordinate_from_string, column_index_from_string
                col_s, row_i = coordinate_from_string(ch.anchor)
                mr = max(mr, row_i + int(ch.height / 0.6)); mc = max(mc, column_index_from_string(col_s) + int(ch.width / 1.65))
            if areas and ws.title in areas:
                ws.print_area = areas[ws.title]
            else:
                ws.print_area = f'A1:{L(mc + 1)}{mr + 1}'
            ws.page_setup.orientation = 'landscape'
            ws.sheet_properties.pageSetUpPr.fitToPage = True
            ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 1
            ws.print_options.horizontalCentered = False
            ws.page_margins.left = ws.page_margins.right = ws.page_margins.top = ws.page_margins.bottom = 0.2
        self.wb.save(path)


# ---------------------------------------------------------------- charts
def _style(ch, title, w, h):
    ch.title = title
    ch.width = w; ch.height = h
    if ch.legend is not None: ch.legend.position = 'b'
    return ch


def bar_chart(ws, anchor, title, cats, data, w=12.5, h=7.2, colors=None, horizontal=False, stacked=False, legend=True,
              titles_from_data=True):
    ch = BarChart(); ch.type = 'bar' if horizontal else 'col'
    ch.style = 10
    if stacked: ch.grouping = 'stacked'; ch.overlap = 100
    ch.add_data(data, titles_from_data=titles_from_data); ch.set_categories(cats)
    for i, s in enumerate(ch.series):
        col = (colors or SERIES)[i % len(colors or SERIES)]
        s.graphicalProperties.solidFill = col; s.graphicalProperties.line.solidFill = col
    ch.gapWidth = 60
    ch.y_axis.majorGridlines = None
    ch.y_axis.numFmt = '#,##0'
    ch.y_axis.delete = False; ch.x_axis.delete = False
    if not legend: ch.legend = None
    if horizontal:
        for sr in ch.series:
            sr.dLbls = DataLabelList(); sr.dLbls.showVal = True; sr.dLbls.showSerName = False; sr.dLbls.showCatName = False
            sr.dLbls.showLegendKey = False; sr.dLbls.numFmt = '#,##0'
        ch.y_axis.delete = True
    _style(ch, title, w, h)
    ws.add_chart(ch, anchor)
    return ch


def doughnut(ws, anchor, title, cats, data, w=8, h=7.2, colors=None):
    from openpyxl.chart.series import DataPoint
    ch = DoughnutChart(); ch.holeSize = 58
    ch.add_data(data, titles_from_data=True); ch.set_categories(cats)
    s = ch.series[0]
    for i, col in enumerate(colors or SERIES):
        p = DataPoint(idx=i); p.graphicalProperties.solidFill = col; p.graphicalProperties.line.solidFill = 'FFFFFF'
        s.dPt.append(p)
    s.dLbls = DataLabelList(); s.dLbls.showPercent = True; s.dLbls.showVal = False; s.dLbls.showCatName = False
    s.dLbls.showSerName = False; s.dLbls.showLegendKey = False; s.dLbls.showLeaderLines = False; s.dLbls.numFmt = '0%'
    _style(ch, title, w, h)
    ws.add_chart(ch, anchor)
    return ch


def line_chart(ws, anchor, title, cats, datas, w=12.5, h=7.2, colors=None):
    ch = LineChart(); ch.style = 12
    for i, d in enumerate(datas):
        ch.add_data(d, titles_from_data=True)
    ch.set_categories(cats)
    for i, s in enumerate(ch.series):
        col = (colors or SERIES)[i % 8]
        s.graphicalProperties.line.solidFill = col; s.graphicalProperties.line.width = 28000; s.smooth = False
    ch.y_axis.majorGridlines = None; ch.y_axis.numFmt = '#,##0'
    ch.y_axis.delete = False; ch.x_axis.delete = False
    _style(ch, title, w, h)
    ws.add_chart(ch, anchor)
    return ch
