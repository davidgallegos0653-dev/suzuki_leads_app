"""PDF Report Generator for Suzuki Leads Report."""

import io, os, calendar, base64
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader
from config import CIUDAD_PROVINCIA, CIUDADES_ORDER, MODELOS_ORDER, FUENTES_ORDER, MESES

BLUE = HexColor('#003399')
RED = HexColor('#CC0000')
HDR = HexColor('#003399')
GREEN = HexColor('#0e7a3a')
AMBER = HexColor('#c27803')
BAD = HexColor('#c81e1e')
GRAY = HexColor('#64748b')
LGRAY = HexColor('#f8fafc')
WHITE = white
BLACK = black
RH = 13

LOGO_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'logo.png')

def ps(v, o):
    return f"{round(v/o*100)}%" if o > 0 else '-'

def vs(c, p):
    if p == 0: return '-'
    v = round((c-p)/p*100)
    return f"+{v}%" if v > 0 else f"{v}%"

def cc(v, o):
    if o <= 0: return BAD
    r = v / o
    if r >= 0.8: return GREEN
    if r >= 0.5: return AMBER
    return BAD

def _style():
    return [
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'), ('FONTSIZE', (0,0), (-1,-1), 7),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'), ('GRID', (0,0), (-1,-1), 0.3, HexColor('#dde3ed')),
        ('BACKGROUND', (0,0), (-1,0), HDR), ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]

def _tbl(c, x, y, rows, cw, extra=None):
    t = Table(rows, colWidths=cw, rowHeights=[RH]*len(rows))
    s = _style()
    if extra: s.extend(extra)
    t.setStyle(TableStyle(s))
    h = RH * len(rows)
    t.wrapOn(c, 0, 0)
    t.drawOn(c, x, y - h)
    return y - h

def _title(c, x, y, text):
    c.setFont('Helvetica-Bold', 8)
    c.setFillColor(BLUE)
    c.drawString(x, y + 2, text)
    c.setFillColor(BLACK)

def generate_report_pdf(data, objetivos, mes_actual, anio, prev_data=None) -> bytes:
    buf = io.BytesIO()
    mn = MESES.get(mes_actual, '')
    pmn = MESES.get(mes_actual-1, '') if mes_actual > 1 else MESES.get(12, '')
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    w, h = landscape(A4)

    # Header bar
    c.setFillColor(BLUE)
    c.rect(25, h-48, w-50, 28, fill=1)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 13)
    c.drawCentredString(w/2, h-40, f'REPORTE DE GENERACIÓN LEADS {mn} {anio}')

    # Logo
    if os.path.exists(LOGO_PATH):
        try:
            c.drawImage(LOGO_PATH, w-160, h-46, width=120, height=22, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    prev = prev_data or {'total':0,'por_fuente':{},'por_dealer':{'Propio':0,'Tercero':0},'por_ciudad':{},'por_modelo':{},'ciudad_modelo':{}}

    ot = objetivos['total']; av = data['total']
    da = objetivos.get('dia_actual', 24)
    dm = calendar.monthrange(anio, mes_actual)[1]
    pm = round(da/dm*100); op = int(round(ot*pm/100))
    dl = f"{da}-{mn[:3].lower()}"; pl = f"{da}-{pmn[:3].lower()}"

    y1 = h - 62

    # S1: Totals
    x1 = 28
    _title(c, x1, y1, 'Leads Total Generados')
    po = objetivos.get('total_prev', 0); pav = prev.get('total', 0)
    rows1 = [['','Objetivo','Avance','%'],
             [pmn, str(po), str(pav), ps(pav,po) if po else '-'],
             [mn, str(ot), str(av), ps(av,ot)]]
    es1 = [('FONTNAME',(0,1),(0,-1),'Helvetica-Bold'), ('TEXTCOLOR',(3,2),(3,2),cc(av,ot))]
    b1 = _tbl(c, x1, y1, rows1, [55,48,42,32], es1)

    # Partial
    rows1b = [[f'Obj {pm}% (día {da})','Avance','%'],[str(op),str(av),ps(av,op)]]
    es1b = [('TEXTCOLOR',(2,1),(2,1),cc(av,op))]
    _tbl(c, x1, b1-8, rows1b, [72,42,32], es1b)

    # S2: Fuente
    x2 = 220
    _title(c, x2, y1, 'Leads por Fuente')
    rf = [['',dl,pl,'% Var']]
    for f in FUENTES_ORDER:
        v = data['por_fuente'].get(f,0); pv = prev.get('por_fuente',{}).get(f,0)
        rf.append([f,str(v),str(pv),vs(v,pv)])
    rf.append(['',str(av),str(pav),''])
    esf = [('BACKGROUND',(0,-1),(-1,-1),LGRAY),('FONTNAME',(0,-1),(-1,-1),'Helvetica-Bold')]
    _tbl(c, x2, y1, rf, [38,36,36,36], esf)

    # S3: Dealer
    x3 = 400
    _title(c, x3, y1, 'Leads por Dealer')
    opr = objetivos.get('propio',0); ote = objetivos.get('tercero',0)
    vp_ = data['por_dealer']['Propio']; vt = data['por_dealer']['Tercero']
    ppv = prev.get('por_dealer',{}).get('Propio',0); tpv = prev.get('por_dealer',{}).get('Tercero',0)
    rd = [['','Objetivo',dl,pl,'Var','Cumpl.'],
          ['Propio',str(opr),str(vp_),str(ppv),vs(vp_,ppv),ps(vp_,opr)],
          ['Tercero',str(ote),str(vt),str(tpv),vs(vt,tpv),ps(vt,ote)]]
    esd = [('TEXTCOLOR',(5,1),(5,1),cc(vp_,opr)),('TEXTCOLOR',(5,2),(5,2),cc(vt,ote)),
           ('FONTNAME',(0,1),(0,-1),'Helvetica-Bold')]
    _tbl(c, x3, y1, rd, [40,48,36,36,36,36], esd)

    # Row 2
    y2 = y1 - RH*9 - 8

    # S4: Provincia
    x4 = 28
    _title(c, x4, y2, 'Leads por Provincia')
    rp = [['','Objetivo',dl,pl,'% Var','Cumpl.']]
    esp = []
    for i, ci in enumerate(CIUDADES_ORDER):
        n = CIUDAD_PROVINCIA[ci]; obj = objetivos.get('por_ciudad',{}).get(ci,0)
        v = data['por_ciudad'].get(ci,0); pv = prev.get('por_ciudad',{}).get(ci,0); cp = round(v/obj*100) if obj else 0
        rp.append([n,str(obj),str(v),str(pv),vs(v,pv),ps(v,obj)])
        esp.append(('TEXTCOLOR',(5,i+1),(5,i+1),cc(v,obj)))
        esp.append(('FONTNAME',(0,i+1),(0,i+1),'Helvetica-Bold'))
        esp.append(('TEXTCOLOR',(0,i+1),(0,i+1),BLUE))
    _tbl(c, x4, y2, rp, [60,48,36,36,42,36], esp)

    # S5: Modelo
    x5 = 320
    _title(c, x5, y2, 'Leads por Modelo')
    rm = [['','Obj',dl,pl,'% Var','Cumpl.']]
    esm = []
    for i, m in enumerate(MODELOS_ORDER):
        obj = objetivos.get('por_modelo',{}).get(m,0)
        v = data['por_modelo'].get(m,0); pv = prev.get('por_modelo',{}).get(m,0)
        rm.append([m,str(obj),str(v),str(pv),vs(v,pv),ps(v,obj)])
        esm.append(('TEXTCOLOR',(5,i+1),(5,i+1),cc(v,obj)))
        esm.append(('FONTNAME',(0,i+1),(0,i+1),'Helvetica-Bold'))
    _tbl(c, x5, y2, rm, [52,32,36,36,42,36], esm)

    # Row 3: City x Model
    y3 = y2 - RH*8 - 12
    x6 = 28
    _title(c, x6, y3, 'Leads por Ciudad × Modelo')

    cm = [['','Obj'] + MODELOS_ORDER + ['Total']]
    esc = [('ALIGN',(0,0),(0,-1),'CENTER')]
    mts = {m:0 for m in MODELOS_ORDER}
    for ri, ci in enumerate(CIUDADES_ORDER):
        obj = objetivos.get('por_ciudad',{}).get(ci,0)
        row = [ci, str(obj)]
        rt = 0
        for m in MODELOS_ORDER:
            v = data['ciudad_modelo'].get(ci,{}).get(m,0); mts[m]+=v; rt+=v
            row.append(str(v))
        row.append(str(rt))
        cm.append(row)
        esc.append(('FONTNAME',(0,ri+1),(0,ri+1),'Helvetica-Bold'))
        esc.append(('TEXTCOLOR',(0,ri+1),(0,ri+1),BLUE))
    gt = sum(mts.values())
    cm.append(['',str(ot)]+[str(mts[m]) for m in MODELOS_ORDER]+[str(gt)])
    esc.append(('BACKGROUND',(0,-1),(-1,-1),LGRAY))
    esc.append(('FONTNAME',(0,-1),(-1,-1),'Helvetica-Bold'))

    cw6 = [26,38]+[44]*len(MODELOS_ORDER)+[38]
    _tbl(c, x6, y3, cm, cw6, esc)

    # Pct table
    x7 = x6 + sum(cw6) + 12
    pc = [[''] + MODELOS_ORDER]
    epc = [('ALIGN',(0,0),(0,-1),'CENTER')]
    for ri, ci in enumerate(CIUDADES_ORDER):
        row = [ci]
        for ji, m in enumerate(MODELOS_ORDER):
            v = data['ciudad_modelo'].get(ci,{}).get(m,0)
            o = objetivos.get('ciudad_modelo',{}).get(ci,{}).get(m,0)
            row.append(ps(v,o))
            epc.append(('TEXTCOLOR',(ji+1,ri+1),(ji+1,ri+1),cc(v,o)))
        pc.append(row)
        epc.append(('FONTNAME',(0,ri+1),(0,ri+1),'Helvetica-Bold'))
        epc.append(('TEXTCOLOR',(0,ri+1),(0,ri+1),BLUE))
    cw7 = [26]+[44]*len(MODELOS_ORDER)
    _tbl(c, x7, y3, pc, cw7, epc)

    c.save()
    buf.seek(0)
    return buf.read()
