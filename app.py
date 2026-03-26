"""Suzuki Leads Report - BI Dashboard. Full-width, no sidebar."""

import json, os, base64
import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
from data_processor import process_all_data
from pdf_generator import generate_report_pdf
from config import (
    CIUDAD_PROVINCIA, CIUDADES_ORDER, MODELOS_ORDER,
    FUENTES_ORDER, MESES,
    DEFAULT_OBJETIVOS_CIUDAD, DEFAULT_OBJETIVOS_MODELO,
    DEFAULT_OBJETIVO_TOTAL, DEFAULT_OBJETIVO_PROPIO, DEFAULT_OBJETIVO_TERCERO,
    DEFAULT_OBJ_CIUDAD_MODELO, DEFAULT_PREV_DATA,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), '.app_data')
os.makedirs(DATA_DIR, exist_ok=True)
LOGO_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'logo.png')

st.set_page_config(page_title="Suzuki Leads Report", page_icon="🏍️", layout="wide", initial_sidebar_state="collapsed")

def get_logo_b64():
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

def save_json(key, obj):
    with open(os.path.join(DATA_DIR, f'{key}.json'), 'w') as f:
        json.dump(obj, f)

def load_json(key, default=None):
    p = os.path.join(DATA_DIR, f'{key}.json')
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return default

def p(val, obj):
    return round(val / obj * 100) if obj > 0 else 0

def vp(cur, prev):
    if prev == 0: return '-'
    v = round((cur - prev) / prev * 100)
    return f"+{v}%" if v > 0 else f"{v}%"

def pc(pct_val):
    if pct_val >= 80: return '#0e7a3a'
    if pct_val >= 50: return '#c27803'
    return '#c81e1e'

def pc_bg(pct_val):
    if pct_val >= 80: return '#f0fdf4'
    if pct_val >= 50: return '#fffbeb'
    return '#fef2f2'

def rc(pct_val):
    """Return CSS class for report tables: green >=80, yellow 50-79, red <50."""
    if pct_val >= 80: return 'rpt-good'
    if pct_val >= 50: return 'rpt-warn'
    return 'rpt-bad'

logo_b64 = get_logo_b64()

# ── Global CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
* { font-family: 'Inter', sans-serif; }

/* Hide sidebar completely */
section[data-testid="stSidebar"] { display: none; }
button[data-testid="stSidebarCollapsedControl"] { display: none; }
header[data-testid="stHeader"] { display: none; }

.main .block-container { padding: 16px 32px; max-width: 1400px; }

/* Top bar */
.topbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 0; margin-bottom: 6px; border-bottom: 1px solid #eef0f4;
}
.topbar-logo img { height: 52px; }
.topbar-right { display: flex; align-items: center; gap: 16px; }
.topbar-date { font-size: 12px; color: #8492a6; font-weight: 500; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #f8f9fb; border-radius: 10px; padding: 4px; gap: 2px;
    border: 1px solid #eef0f4;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px; font-size: 13px; font-weight: 600; padding: 8px 20px;
    color: #5a6a7e;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: white; color: #003399; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 16px; }

/* KPI row */
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; }
.kpi-card {
    background: white; border: 1px solid #eef0f4; border-radius: 12px;
    padding: 20px; position: relative;
}
.kpi-label { font-size: 11px; color: #8492a6; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.kpi-value { font-size: 36px; font-weight: 900; color: #0f172a; margin: 6px 0 4px; line-height: 1; }
.kpi-sub { font-size: 12px; color: #64748b; }
.kpi-badge {
    position: absolute; top: 16px; right: 16px;
    font-size: 13px; font-weight: 700; padding: 4px 12px; border-radius: 20px;
}
.kpi-prog { height: 4px; background: #f1f5f9; border-radius: 4px; margin-top: 10px; overflow: hidden; }
.kpi-prog-fill { height: 100%; border-radius: 4px; }

/* Section */
.sec { margin: 24px 0 12px; font-size: 13px; font-weight: 700; color: #003399; letter-spacing: 0.3px; }

/* Mini cards */
.mcards { display: grid; gap: 10px; }
.mcards-6 { grid-template-columns: repeat(6, 1fr); }
.mc {
    background: white; border: 1px solid #eef0f4; border-radius: 10px;
    padding: 16px 12px; text-align: center; transition: all 0.15s;
}
.mc:hover { border-color: #c7d2e0; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.mc-name { font-size: 10px; color: #8492a6; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; }
.mc-val { font-size: 26px; font-weight: 900; color: #0f172a; margin: 4px 0 2px; }
.mc-obj { font-size: 10px; color: #94a3b8; }
.mc-pct { font-size: 14px; font-weight: 800; margin-top: 4px; }
.mc-bar { height: 3px; background: #f1f5f9; border-radius: 3px; margin-top: 6px; overflow: hidden; }
.mc-bar-fill { height: 100%; border-radius: 3px; }
.mc-prev { font-size: 9px; color: #94a3b8; margin-top: 6px; }

/* Config panels */
.cfg-box {
    background: white; border: 1px solid #eef0f4; border-radius: 12px;
    padding: 20px; margin-bottom: 14px;
}
.cfg-title { font-size: 13px; font-weight: 700; color: #1e293b; margin-bottom: 14px; }

/* Upload zone */
.upload-zone {
    background: white; border: 2px dashed #d1d9e6; border-radius: 14px;
    padding: 30px; text-align: center; margin-bottom: 14px;
}
.upload-zone:hover { border-color: #003399; }
.upload-title { font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 4px; }
.upload-sub { font-size: 12px; color: #8492a6; }

/* Report tab */
.rpt-header {
    background: #003399; color: white; padding: 14px 28px; border-radius: 10px;
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 20px;
}
.rpt-header h2 { margin: 0; font-size: 17px; font-weight: 800; }
.rpt-header img { height: 28px; }

.rpt-section { margin: 18px 0 8px; font-size: 12px; font-weight: 700; color: #003399;
    text-transform: uppercase; letter-spacing: 0.8px; }

.rpt-table { width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 16px; }
.rpt-table th {
    background: #003399; color: white; padding: 6px 10px; text-align: center;
    font-weight: 600; font-size: 10px; text-transform: uppercase; letter-spacing: 0.3px;
}
.rpt-table td { padding: 5px 10px; border-bottom: 1px solid #eef0f4; text-align: center; }
.rpt-table tr:hover td { background: #f8fafc; }
.rpt-table .row-label { text-align: left; font-weight: 600; color: #003399; }
.rpt-table .total-row td { background: #f8fafc; font-weight: 700; border-top: 2px solid #003399; }
.rpt-good { color: #0e7a3a; font-weight: 700; }
.rpt-warn { color: #c27803; font-weight: 700; }
.rpt-bad { color: #c81e1e; font-weight: 700; }
.rpt-neutral { color: #64748b; }

/* Published pill */
.pill {
    font-size: 11px; font-weight: 600; padding: 4px 14px; border-radius: 20px;
    display: inline-flex; align-items: center; gap: 5px;
}
.pill-green { background: #f0fdf4; color: #0e7a3a; border: 1px solid #bbf7d0; }

/* Footer */
.foot { text-align: center; color: #94a3b8; font-size: 10px; padding: 16px 0; border-top: 1px solid #f1f5f9; margin-top: 30px; }

/* Streamlit overrides */
div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; border: 1px solid #eef0f4; }
.stDownloadButton button { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ── Top bar ──
logo_img = f'<img src="data:image/png;base64,{logo_b64}">' if logo_b64 else '<span style="font-weight:900;color:#003399;font-size:18px;">SUZUKI</span>'
st.markdown(f"""<div class="topbar">
    <div class="topbar-logo">{logo_img}</div>
    <div class="topbar-right">
        <span class="topbar-date">{datetime.now().strftime('%d %b %Y')}</span>
    </div>
</div>""", unsafe_allow_html=True)

# ── Load persisted state ──
data = load_json('current_report')
prev_data = load_json('prev_month')
objetivos = load_json('objetivos', {
    'total': DEFAULT_OBJETIVO_TOTAL, 'propio': DEFAULT_OBJETIVO_PROPIO,
    'tercero': DEFAULT_OBJETIVO_TERCERO, 'total_prev': 3239,
    'por_ciudad': DEFAULT_OBJETIVOS_CIUDAD, 'por_modelo': DEFAULT_OBJETIVOS_MODELO,
    'ciudad_modelo': DEFAULT_OBJ_CIUDAD_MODELO,
})

now = datetime.now()

# ── Tabs ──
tabs = st.tabs(["📂  Cargar Datos", "🎯  Objetivos", "📊  Dashboard", "📄  Reporte"])


# ══════════════════════════════════════════
# TAB: CARGAR DATOS
# ══════════════════════════════════════════
with tabs[0]:
    st.markdown('<p style="color:#64748b;font-size:13px;margin-bottom:20px;">Sube los archivos para el mes actual y opcionalmente del mes anterior para comparación automática.</p>', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1], gap="large")

    with c1:
        st.markdown("""<div class="upload-zone">
            <div class="upload-title">📊 Mes Actual</div>
            <div class="upload-sub">Sube los dos archivos del mes en curso</div>
        </div>""", unsafe_allow_html=True)

        mes = st.selectbox("Mes", range(1, 13), index=now.month - 1, format_func=lambda x: MESES[x], key="mes_act")
        anio = st.number_input("Año", min_value=2024, max_value=2030, value=now.year, key="anio_act")
        dia_corte = st.number_input("Día de corte", min_value=1,
                                    max_value=calendar.monthrange(anio, mes)[1],
                                    value=min(now.day, calendar.monthrange(anio, mes)[1]), key="dia_act")
        file_reporte = st.file_uploader("Reporte Leads (Red Propia)", type=['xlsx', 'xls'], key="f_rpt")
        file_data = st.file_uploader("Data (Terceros: Meta + Landing)", type=['xlsx', 'xls'], key="f_data")

    with c2:
        st.markdown("""<div class="upload-zone">
            <div class="upload-title">📅 Mes Anterior</div>
            <div class="upload-sub">Opcional — mismos archivos del mes pasado para comparar</div>
        </div>""", unsafe_allow_html=True)

        prev_mes = st.selectbox("Mes anterior", range(1, 13),
                                index=(now.month - 2) % 12, format_func=lambda x: MESES[x], key="mes_prev")
        prev_anio = st.number_input("Año", min_value=2024, max_value=2030, value=now.year, key="anio_prev")
        file_prev_reporte = st.file_uploader("Reporte Leads (mes anterior)", type=['xlsx', 'xls'], key="fp_rpt")
        file_prev_data = st.file_uploader("Data Terceros (mes anterior)", type=['xlsx', 'xls'], key="fp_data")

    st.markdown("---")

    can_process = file_reporte and file_data

    if can_process:
        if st.button("🚀  Procesar y Publicar Reporte", type="primary", use_container_width=True):
            with st.spinner("Procesando datos del mes actual..."):
                try:
                    result = process_all_data(file_reporte, file_data)
                    result['dia_corte'] = dia_corte
                    result['mes'] = mes
                    result['anio'] = anio
                    result['timestamp'] = datetime.now().strftime('%d/%m/%Y %H:%M')
                    save_json('current_report', result)
                    data = result

                    # Process previous month if available
                    if file_prev_reporte and file_prev_data:
                        with st.spinner("Procesando mes anterior..."):
                            prev_result = process_all_data(file_prev_reporte, file_prev_data)
                            prev_result['mes'] = prev_mes
                            save_json('prev_month', prev_result)
                            prev_data = prev_result

                    st.success("Reporte publicado exitosamente. Ve a la pestaña **Dashboard** o **Reporte**.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())
    else:
        st.info("Sube al menos los dos archivos del **mes actual** para continuar.")

    # Show current status
    if data:
        st.markdown(f"""<div style="margin-top:12px;">
            <span class="pill pill-green">● Reporte activo: {MESES.get(data.get('mes', mes), '')} {data.get('anio', anio)} — Publicado {data.get('timestamp', '')}</span>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════
# TAB: OBJETIVOS
# ══════════════════════════════════════════
with tabs[1]:
    st.markdown('<p style="color:#64748b;font-size:13px;margin-bottom:16px;">Configura los objetivos mensuales. Se guardan y persisten para el reporte.</p>', unsafe_allow_html=True)

    st.markdown('<div class="cfg-box"><div class="cfg-title">Objetivos Generales</div>', unsafe_allow_html=True)
    g1, g2, g3, g4 = st.columns(4)
    with g1: ot = st.number_input("Total", value=objetivos.get('total', DEFAULT_OBJETIVO_TOTAL), step=10, key="ot")
    with g2: op = st.number_input("Propio", value=objetivos.get('propio', DEFAULT_OBJETIVO_PROPIO), step=10, key="op")
    with g3: otr = st.number_input("Tercero", value=objetivos.get('tercero', DEFAULT_OBJETIVO_TERCERO), step=10, key="otr")
    with g4: otp = st.number_input("Obj. Mes Anterior", value=objetivos.get('total_prev', 3239), step=10, key="otp")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="cfg-box"><div class="cfg-title">Por Ciudad</div>', unsafe_allow_html=True)
    cc = st.columns(len(CIUDADES_ORDER))
    oc = {}
    for i, c in enumerate(CIUDADES_ORDER):
        with cc[i]:
            oc[c] = st.number_input(CIUDAD_PROVINCIA[c], value=objetivos.get('por_ciudad', DEFAULT_OBJETIVOS_CIUDAD).get(c, 0), step=5, key=f"oc_{c}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="cfg-box"><div class="cfg-title">Por Modelo</div>', unsafe_allow_html=True)
    mc = st.columns(len(MODELOS_ORDER))
    om = {}
    for i, m in enumerate(MODELOS_ORDER):
        with mc[i]:
            om[m] = st.number_input(m, value=objetivos.get('por_modelo', DEFAULT_OBJETIVOS_MODELO).get(m, 0), step=5, key=f"om_{m}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="cfg-box"><div class="cfg-title">Ciudad × Modelo</div>', unsafe_allow_html=True)
    ocm = {}
    for ciudad in CIUDADES_ORDER:
        st.caption(f"**{CIUDAD_PROVINCIA[ciudad]} ({ciudad})**")
        cols = st.columns(len(MODELOS_ORDER))
        ocm[ciudad] = {}
        for j, m in enumerate(MODELOS_ORDER):
            with cols[j]:
                d = objetivos.get('ciudad_modelo', DEFAULT_OBJ_CIUDAD_MODELO).get(ciudad, {}).get(m, 0)
                ocm[ciudad][m] = st.number_input(m, value=d, step=1, key=f"ocm_{ciudad}_{m}")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("💾  Guardar Objetivos", type="primary", use_container_width=True):
        save_json('objetivos', {'total': ot, 'propio': op, 'tercero': otr, 'total_prev': otp,
                                'por_ciudad': oc, 'por_modelo': om, 'ciudad_modelo': ocm})
        st.success("Objetivos guardados")
        st.rerun()


# ══════════════════════════════════════════
# TAB: DASHBOARD
# ══════════════════════════════════════════
with tabs[2]:
    if not data:
        st.markdown('<div style="text-align:center;padding:60px;color:#94a3b8;"><h3>No hay datos publicados</h3><p>Ve a la pestaña "Cargar Datos" para comenzar.</p></div>', unsafe_allow_html=True)
    else:
        mes_nombre = MESES.get(data.get('mes', mes), '')
        prev_mes_nombre = MESES.get(data.get('mes', mes) - 1, '') if data.get('mes', mes) > 1 else MESES.get(12, '')
        dc = data.get('dia_corte', 24)
        anio_d = data.get('anio', now.year)
        avance = data['total']
        obj_t = objetivos.get('total', DEFAULT_OBJETIVO_TOTAL)
        obj_p = objetivos.get('propio', DEFAULT_OBJETIVO_PROPIO)
        obj_te = objetivos.get('tercero', DEFAULT_OBJETIVO_TERCERO)
        dias_mes = calendar.monthrange(anio_d, data.get('mes', mes))[1]
        pct_mes = round(dc / dias_mes * 100)
        obj_parcial = int(round(obj_t * pct_mes / 100))
        prev = prev_data if prev_data else DEFAULT_PREV_DATA

        st.markdown(f'<span class="pill pill-green">● Publicado {data.get("timestamp","")}</span> &nbsp; <span style="font-size:11px;color:#94a3b8;">Corte: día {dc} de {mes_nombre} ({pct_mes}% del mes)</span>', unsafe_allow_html=True)

        # KPI
        pt = p(avance, obj_t); pp = p(avance, obj_parcial)
        ppr = p(data['por_dealer']['Propio'], obj_p); ptr = p(data['por_dealer']['Tercero'], obj_te)

        st.markdown(f"""
        <div class="kpi-row">
            <div class="kpi-card">
                <div class="kpi-label">Total Leads</div>
                <div class="kpi-value">{avance:,}</div>
                <div class="kpi-sub">de {obj_t:,}</div>
                <div class="kpi-badge" style="background:{pc_bg(pt)};color:{pc(pt)};">{pt}%</div>
                <div class="kpi-prog"><div class="kpi-prog-fill" style="width:{min(pt,100)}%;background:{pc(pt)};"></div></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Avance al día {dc}</div>
                <div class="kpi-value">{avance:,}</div>
                <div class="kpi-sub">de {obj_parcial:,} ({pct_mes}%)</div>
                <div class="kpi-badge" style="background:{pc_bg(pp)};color:{pc(pp)};">{pp}%</div>
                <div class="kpi-prog"><div class="kpi-prog-fill" style="width:{min(pp,100)}%;background:{pc(pp)};"></div></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Red Propia</div>
                <div class="kpi-value">{data['por_dealer']['Propio']:,}</div>
                <div class="kpi-sub">de {obj_p:,}</div>
                <div class="kpi-badge" style="background:{pc_bg(ppr)};color:{pc(ppr)};">{ppr}%</div>
                <div class="kpi-prog"><div class="kpi-prog-fill" style="width:{min(ppr,100)}%;background:{pc(ppr)};"></div></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Terceros</div>
                <div class="kpi-value">{data['por_dealer']['Tercero']:,}</div>
                <div class="kpi-sub">de {obj_te:,}</div>
                <div class="kpi-badge" style="background:{pc_bg(ptr)};color:{pc(ptr)};">{ptr}%</div>
                <div class="kpi-prog"><div class="kpi-prog-fill" style="width:{min(ptr,100)}%;background:{pc(ptr)};"></div></div>
            </div>
        </div>""", unsafe_allow_html=True)

        # Fuente + Dealer
        cf, cd = st.columns([3, 2])
        with cf:
            st.markdown('<div class="sec">Leads por Fuente</div>', unsafe_allow_html=True)
            frows = []
            for f in FUENTES_ORDER:
                v = data['por_fuente'].get(f, 0)
                pv = prev.get('por_fuente', {}).get(f, 0)
                frows.append({'Fuente': f, 'Actual': v, 'Anterior': pv, 'Var.': vp(v, pv),
                              '% Total': f"{round(v/avance*100)}%" if avance else '-'})
            st.dataframe(pd.DataFrame(frows), use_container_width=True, hide_index=True,
                         column_config={'Actual': st.column_config.ProgressColumn(format="%d", min_value=0,
                                        max_value=max(r['Actual'] for r in frows) or 1)})

        with cd:
            st.markdown('<div class="sec">Comparación Mensual</div>', unsafe_allow_html=True)
            ptot = prev.get('total', 0)
            st.markdown(f"""<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                <div style="background:white;border:1px solid #eef0f4;border-radius:10px;padding:18px;text-align:center;">
                    <div style="font-size:10px;color:#94a3b8;font-weight:600;">VS MES ANTERIOR</div>
                    <div style="font-size:28px;font-weight:900;color:{'#0e7a3a' if avance >= ptot else '#c81e1e'};">{vp(avance, ptot)}</div>
                    <div style="font-size:11px;color:#94a3b8;">{ptot:,} → {avance:,}</div>
                </div>
                <div style="background:white;border:1px solid #eef0f4;border-radius:10px;padding:18px;text-align:center;">
                    <div style="font-size:10px;color:#94a3b8;font-weight:600;">PROPIO vs ANT.</div>
                    <div style="font-size:28px;font-weight:900;color:{'#0e7a3a' if data['por_dealer']['Propio'] >= prev.get('por_dealer',{}).get('Propio',0) else '#c81e1e'};">{vp(data['por_dealer']['Propio'], prev.get('por_dealer',{}).get('Propio',0))}</div>
                    <div style="font-size:11px;color:#94a3b8;">{prev.get('por_dealer',{}).get('Propio',0):,} → {data['por_dealer']['Propio']:,}</div>
                </div>
            </div>""", unsafe_allow_html=True)

        # Provincia cards
        st.markdown('<div class="sec">Por Provincia</div>', unsafe_allow_html=True)
        html = '<div class="mcards mcards-6">'
        for c in CIUDADES_ORDER:
            n = CIUDAD_PROVINCIA[c]; obj = objetivos.get('por_ciudad', DEFAULT_OBJETIVOS_CIUDAD).get(c, 0)
            v = data['por_ciudad'].get(c, 0); pv = prev.get('por_ciudad', {}).get(c, 0); cp = p(v, obj)
            html += f'''<div class="mc"><div class="mc-name">{n}</div><div class="mc-val">{v:,}</div>
                <div class="mc-obj">Obj: {obj:,}</div><div class="mc-pct" style="color:{pc(cp)};">{cp}%</div>
                <div class="mc-bar"><div class="mc-bar-fill" style="width:{min(cp,100)}%;background:{pc(cp)};"></div></div>
                <div class="mc-prev">Ant: {pv:,} ({vp(v, pv)})</div></div>'''
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

        # Model cards
        st.markdown('<div class="sec">Por Modelo</div>', unsafe_allow_html=True)
        html2 = '<div class="mcards mcards-6">'
        for m in MODELOS_ORDER:
            obj = objetivos.get('por_modelo', DEFAULT_OBJETIVOS_MODELO).get(m, 0)
            v = data['por_modelo'].get(m, 0); pv = prev.get('por_modelo', {}).get(m, 0); cp = p(v, obj)
            html2 += f'''<div class="mc"><div class="mc-name">{m}</div><div class="mc-val">{v:,}</div>
                <div class="mc-obj">Obj: {obj:,}</div><div class="mc-pct" style="color:{pc(cp)};">{cp}%</div>
                <div class="mc-bar"><div class="mc-bar-fill" style="width:{min(cp,100)}%;background:{pc(cp)};"></div></div>
                <div class="mc-prev">Ant: {pv:,} ({vp(v, pv)})</div></div>'''
        html2 += '</div>'
        st.markdown(html2, unsafe_allow_html=True)

        # Matrix
        st.markdown('<div class="sec">Ciudad × Modelo</div>', unsafe_allow_html=True)
        ta, tb = st.tabs(["Valores", "% Cumplimiento"])
        with ta:
            rows = []
            for c in CIUDADES_ORDER:
                r = {'Ciudad': f"{CIUDAD_PROVINCIA[c]}", 'Obj': objetivos.get('por_ciudad', DEFAULT_OBJETIVOS_CIUDAD).get(c, 0)}
                for m in MODELOS_ORDER:
                    r[m] = data['ciudad_modelo'].get(c, {}).get(m, 0)
                r['Total'] = sum(r[m] for m in MODELOS_ORDER)
                rows.append(r)
            tot = {'Ciudad': 'TOTAL', 'Obj': obj_t}
            for m in MODELOS_ORDER: tot[m] = sum(r[m] for r in rows)
            tot['Total'] = sum(tot[m] for m in MODELOS_ORDER)
            rows.append(tot)
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        with tb:
            prows = []
            for c in CIUDADES_ORDER:
                r = {'Ciudad': CIUDAD_PROVINCIA[c]}
                for m in MODELOS_ORDER:
                    v = data['ciudad_modelo'].get(c, {}).get(m, 0)
                    o = objetivos.get('ciudad_modelo', DEFAULT_OBJ_CIUDAD_MODELO).get(c, {}).get(m, 0)
                    r[m] = f"{p(v, o)}%"
                tv = sum(data['ciudad_modelo'].get(c, {}).get(m, 0) for m in MODELOS_ORDER)
                to = objetivos.get('por_ciudad', DEFAULT_OBJETIVOS_CIUDAD).get(c, 0)
                r['Total'] = f"{p(tv, to)}%"
                prows.append(r)
            st.dataframe(pd.DataFrame(prows), use_container_width=True, hide_index=True)

        st.markdown(f'<div class="foot">Suzuki Ecuador — Leads Report — {data.get("timestamp","")}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════
# TAB: REPORTE (visual, exportable)
# ══════════════════════════════════════════
with tabs[3]:
    if not data:
        st.markdown('<div style="text-align:center;padding:60px;color:#94a3b8;"><h3>No hay datos publicados</h3></div>', unsafe_allow_html=True)
    else:
        mes_nombre = MESES.get(data.get('mes', mes), '')
        prev_mes_nombre = MESES.get(data.get('mes', mes) - 1, '') if data.get('mes', mes) > 1 else MESES.get(12, '')
        dc = data.get('dia_corte', 24)
        anio_d = data.get('anio', now.year)
        avance = data['total']
        obj_t = objetivos.get('total', DEFAULT_OBJETIVO_TOTAL)
        obj_p = objetivos.get('propio', DEFAULT_OBJETIVO_PROPIO)
        obj_te = objetivos.get('tercero', DEFAULT_OBJETIVO_TERCERO)
        dias_mes = calendar.monthrange(anio_d, data.get('mes', mes))[1]
        pct_mes = round(dc / dias_mes * 100)
        obj_parcial = int(round(obj_t * pct_mes / 100))
        prev = prev_data if prev_data else DEFAULT_PREV_DATA

        dl = f"{dc}-{mes_nombre[:3].lower()}"
        pl = f"{dc}-{prev_mes_nombre[:3].lower()}"

        # Report header
        logo_rpt = f'<img src="data:image/png;base64,{logo_b64}" style="height:36px;">' if logo_b64 else '<span style="font-weight:900;color:white;">SUZUKI</span>'
        st.markdown(f'''<div class="rpt-header">
            <h2>REPORTE DE GENERACIÓN LEADS {mes_nombre} {anio_d}</h2>
            {logo_rpt}
        </div>''', unsafe_allow_html=True)

        # Row 1: Totals + Fuente + Dealer
        r1a, r1b, r1c = st.columns([1, 1, 1.2])

        with r1a:
            st.markdown('<div class="rpt-section">Leads Total Generados</div>', unsafe_allow_html=True)
            prev_obj = objetivos.get('total_prev', 3239)
            prev_total = prev.get('total', 0)
            pct_t = f"{p(avance, obj_t)}%"
            pct_prev = f"{p(prev_total, prev_obj)}%" if prev_obj else '-'
            html_t = f"""<table class="rpt-table">
                <tr><th></th><th>Objetivo</th><th>Avance</th><th>%</th></tr>
                <tr><td class="row-label">{prev_mes_nombre}</td><td>{prev_obj:,}</td><td>{prev_total:,}</td><td>{pct_prev}</td></tr>
                <tr><td class="row-label">{mes_nombre}</td><td>{obj_t:,}</td><td>{avance:,}</td>
                    <td class="{rc(p(avance,obj_t))}">{pct_t}</td></tr>
            </table>"""
            st.markdown(html_t, unsafe_allow_html=True)

            # Partial
            pct_parc = p(avance, obj_parcial)
            st.markdown(f"""<table class="rpt-table">
                <tr><th>Obj. {pct_mes}% (día {dc})</th><th>Avance</th><th>%</th></tr>
                <tr><td>{obj_parcial:,}</td><td>{avance:,}</td>
                    <td class="{rc(pct_parc)}">{pct_parc}%</td></tr>
            </table>""", unsafe_allow_html=True)

        with r1b:
            st.markdown('<div class="rpt-section">Leads por Fuente</div>', unsafe_allow_html=True)
            fhtml = f'<table class="rpt-table"><tr><th></th><th>{dl}</th><th>{pl}</th><th>% Var</th></tr>'
            for f in FUENTES_ORDER:
                v = data['por_fuente'].get(f, 0); pv = prev.get('por_fuente', {}).get(f, 0)
                fhtml += f'<tr><td class="row-label">{f}</td><td>{v:,}</td><td>{pv:,}</td><td class="rpt-neutral">{vp(v,pv)}</td></tr>'
            fhtml += f'<tr class="total-row"><td></td><td>{avance:,}</td><td>{prev.get("total",0):,}</td><td></td></tr></table>'
            st.markdown(fhtml, unsafe_allow_html=True)

        with r1c:
            st.markdown('<div class="rpt-section">Leads por Dealer</div>', unsafe_allow_html=True)
            pp_v = data['por_dealer']['Propio']; tp_v = data['por_dealer']['Tercero']
            ppv = prev.get('por_dealer',{}).get('Propio',0); tpv = prev.get('por_dealer',{}).get('Tercero',0)
            cpp = p(pp_v, obj_p); cpt = p(tp_v, obj_te)
            dhtml = f"""<table class="rpt-table">
                <tr><th></th><th>Objetivo</th><th>{dl}</th><th>{pl}</th><th>Variación</th><th>Cumpl.</th></tr>
                <tr><td class="row-label">Propio</td><td>{obj_p:,}</td><td>{pp_v:,}</td><td>{ppv:,}</td>
                    <td class="rpt-neutral">{vp(pp_v,ppv)}</td><td class="{rc(cpp)}">{cpp}%</td></tr>
                <tr><td class="row-label">Tercero</td><td>{obj_te:,}</td><td>{tp_v:,}</td><td>{tpv:,}</td>
                    <td class="rpt-neutral">{vp(tp_v,tpv)}</td><td class="{rc(cpt)}">{cpt}%</td></tr>
            </table>"""
            st.markdown(dhtml, unsafe_allow_html=True)

        st.markdown("---")

        # Row 2: Provincia + Modelo
        r2a, r2b = st.columns([1, 1])

        with r2a:
            st.markdown('<div class="rpt-section">Leads por Provincia</div>', unsafe_allow_html=True)
            phtml = f'<table class="rpt-table"><tr><th></th><th>Objetivo</th><th>{dl}</th><th>{pl}</th><th>% Var</th><th>Cumpl.</th></tr>'
            for c in CIUDADES_ORDER:
                n = CIUDAD_PROVINCIA[c]; obj = objetivos.get('por_ciudad', DEFAULT_OBJETIVOS_CIUDAD).get(c, 0)
                v = data['por_ciudad'].get(c, 0); pv = prev.get('por_ciudad', {}).get(c, 0); cp = p(v, obj)
                phtml += f'<tr><td class="row-label">{n}</td><td>{obj:,}</td><td>{v:,}</td><td>{pv:,}</td><td class="rpt-neutral">{vp(v,pv)}</td><td class="{rc(cp)}">{cp}%</td></tr>'
            phtml += '</table>'
            st.markdown(phtml, unsafe_allow_html=True)

        with r2b:
            st.markdown('<div class="rpt-section">Leads por Modelo</div>', unsafe_allow_html=True)
            mhtml = f'<table class="rpt-table"><tr><th></th><th>Obj</th><th>{dl}</th><th>{pl}</th><th>% Var</th><th>Cumpl.</th></tr>'
            for m in MODELOS_ORDER:
                obj = objetivos.get('por_modelo', DEFAULT_OBJETIVOS_MODELO).get(m, 0)
                v = data['por_modelo'].get(m, 0); pv = prev.get('por_modelo', {}).get(m, 0); cp = p(v, obj)
                mhtml += f'<tr><td class="row-label">{m}</td><td>{obj:,}</td><td>{v:,}</td><td>{pv:,}</td><td class="rpt-neutral">{vp(v,pv)}</td><td class="{rc(cp)}">{cp}%</td></tr>'
            mhtml += '</table>'
            st.markdown(mhtml, unsafe_allow_html=True)

        st.markdown("---")

        # Row 3: City x Model matrix
        st.markdown('<div class="rpt-section">Leads por Ciudad × Modelo</div>', unsafe_allow_html=True)

        r3a, r3b = st.columns([1.2, 1])

        with r3a:
            cmh = '<table class="rpt-table"><tr><th></th><th>Obj</th>'
            for m in MODELOS_ORDER: cmh += f'<th>{m}</th>'
            cmh += '<th>Total</th></tr>'
            mt = {m: 0 for m in MODELOS_ORDER}
            for c in CIUDADES_ORDER:
                obj = objetivos.get('por_ciudad', DEFAULT_OBJETIVOS_CIUDAD).get(c, 0)
                cmh += f'<tr><td class="row-label">{c}</td><td>{obj:,}</td>'
                row_total = 0
                for m in MODELOS_ORDER:
                    v = data['ciudad_modelo'].get(c, {}).get(m, 0)
                    mt[m] += v; row_total += v
                    cmh += f'<td>{v:,}</td>'
                cmh += f'<td><b>{row_total:,}</b></td></tr>'
            cmh += f'<tr class="total-row"><td></td><td>{obj_t:,}</td>'
            gt = 0
            for m in MODELOS_ORDER:
                cmh += f'<td>{mt[m]:,}</td>'; gt += mt[m]
            cmh += f'<td><b>{gt:,}</b></td></tr></table>'
            st.markdown(cmh, unsafe_allow_html=True)

        with r3b:
            pch = '<table class="rpt-table"><tr><th></th>'
            for m in MODELOS_ORDER: pch += f'<th>{m}</th>'
            pch += '</tr>'
            for c in CIUDADES_ORDER:
                pch += f'<tr><td class="row-label">{c}</td>'
                for m in MODELOS_ORDER:
                    v = data['ciudad_modelo'].get(c, {}).get(m, 0)
                    o = objetivos.get('ciudad_modelo', DEFAULT_OBJ_CIUDAD_MODELO).get(c, {}).get(m, 0)
                    cp = p(v, o)
                    pch += f'<td class="{rc(cp)}">{cp}%</td>'
                pch += '</tr>'
            pch += '</table>'
            st.markdown(pch, unsafe_allow_html=True)

        # Export PDF
        st.markdown("---")
        if st.button("📥  Exportar a PDF", type="primary", use_container_width=True):
            with st.spinner("Generando PDF..."):
                obj_for_pdf = {
                    'total': obj_t, 'total_prev': objetivos.get('total_prev', 3239),
                    'propio': obj_p, 'tercero': obj_te,
                    'por_ciudad': objetivos.get('por_ciudad', DEFAULT_OBJETIVOS_CIUDAD),
                    'por_modelo': objetivos.get('por_modelo', DEFAULT_OBJETIVOS_MODELO),
                    'ciudad_modelo': objetivos.get('ciudad_modelo', DEFAULT_OBJ_CIUDAD_MODELO),
                    'dia_actual': dc,
                }
                pdf = generate_report_pdf(data, obj_for_pdf, data.get('mes', mes), anio_d, prev)
                st.download_button("⬇️  Descargar PDF", data=pdf,
                                   file_name=f"SZK_Reporte_{dc}_{mes_nombre}_{anio_d}.pdf",
                                   mime="application/pdf", use_container_width=True)

        st.markdown(f'<div class="foot">Suzuki Ecuador — Reporte de Generación de Leads — {data.get("timestamp","")}</div>', unsafe_allow_html=True)
