"""Suzuki Leads Report - BI Dashboard with Admin/Viewer modes."""

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
ADMIN_KEY = 'suzuki'

st.set_page_config(page_title="Suzuki Leads Report", page_icon="🏍️", layout="wide", initial_sidebar_state="collapsed")

# ── Check admin mode ──
is_admin = st.query_params.get('admin', '') == ADMIN_KEY

def get_logo_b64():
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

def save_json(key, obj):
    with open(os.path.join(DATA_DIR, f'{key}.json'), 'w') as f:
        json.dump(obj, f)

def load_json(key, default=None):
    fp = os.path.join(DATA_DIR, f'{key}.json')
    if os.path.exists(fp):
        with open(fp) as f:
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
    if pct_val >= 80: return 'rpt-good'
    if pct_val >= 50: return 'rpt-warn'
    return 'rpt-bad'

logo_b64 = get_logo_b64()

# ── Global CSS — Force white background everywhere including mobile ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
* { font-family: 'Inter', sans-serif; }

/* Force white theme everywhere */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"],
.main, .stApp, [data-testid="stAppViewBlockContainer"] {
    background-color: #ffffff !important;
    color: #0f172a !important;
}
[data-testid="stAppViewContainer"] > section > div { background: #ffffff !important; }

/* Force white on dark mode / mobile */
@media (prefers-color-scheme: dark) {
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"],
    .main, .stApp { background-color: #ffffff !important; color: #0f172a !important; }
    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] div { color: #0f172a !important; }
}

/* Hide sidebar + header */
section[data-testid="stSidebar"] { display: none !important; }
button[data-testid="stSidebarCollapsedControl"] { display: none !important; }
header[data-testid="stHeader"] { display: none !important; }

.main .block-container { padding: 12px 24px; max-width: 1400px; }

/* Top bar */
.topbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 0; margin-bottom: 4px; border-bottom: 1px solid #eef0f4;
}
.topbar-logo img { height: 48px; }
.topbar-right { display: flex; align-items: center; gap: 12px; }
.topbar-date { font-size: 11px; color: #8492a6; font-weight: 500; }
.topbar-badge {
    font-size: 9px; font-weight: 700; padding: 3px 10px; border-radius: 12px;
    text-transform: uppercase; letter-spacing: 0.5px;
}
.badge-admin { background: #ede9fe; color: #6d28d9; }
.badge-viewer { background: #f0fdf4; color: #0e7a3a; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #f8f9fb; border-radius: 10px; padding: 4px; gap: 2px;
    border: 1px solid #eef0f4;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px; font-size: 13px; font-weight: 600; padding: 8px 18px;
    color: #5a6a7e;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: white; color: #003399; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 14px; }

/* KPI row */
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 18px; }
.kpi-card {
    background: white; border: 1px solid #eef0f4; border-radius: 12px;
    padding: 18px; position: relative;
}
.kpi-label { font-size: 10px; color: #8492a6; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.kpi-value { font-size: 32px; font-weight: 900; color: #0f172a; margin: 4px 0 2px; line-height: 1; }
.kpi-sub { font-size: 11px; color: #64748b; }
.kpi-badge {
    position: absolute; top: 14px; right: 14px;
    font-size: 12px; font-weight: 700; padding: 3px 10px; border-radius: 16px;
}
.kpi-prog { height: 4px; background: #f1f5f9; border-radius: 4px; margin-top: 8px; overflow: hidden; }
.kpi-prog-fill { height: 100%; border-radius: 4px; }

/* Section */
.sec { margin: 20px 0 10px; font-size: 12px; font-weight: 700; color: #003399; letter-spacing: 0.3px; }

/* Mini cards */
.mcards { display: grid; gap: 10px; }
.mcards-6 { grid-template-columns: repeat(6, 1fr); }
.mc {
    background: white; border: 1px solid #eef0f4; border-radius: 10px;
    padding: 14px 10px; text-align: center; transition: all 0.15s;
}
.mc:hover { border-color: #c7d2e0; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.mc-name { font-size: 9px; color: #8492a6; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; }
.mc-val { font-size: 24px; font-weight: 900; color: #0f172a; margin: 3px 0 2px; }
.mc-obj { font-size: 9px; color: #94a3b8; }
.mc-pct { font-size: 13px; font-weight: 800; margin-top: 3px; }
.mc-bar { height: 3px; background: #f1f5f9; border-radius: 3px; margin-top: 5px; overflow: hidden; }
.mc-bar-fill { height: 100%; border-radius: 3px; }
.mc-prev { font-size: 8px; color: #94a3b8; margin-top: 5px; }

/* Config panels */
.cfg-box {
    background: white; border: 1px solid #eef0f4; border-radius: 12px;
    padding: 18px; margin-bottom: 12px;
}
.cfg-title { font-size: 12px; font-weight: 700; color: #1e293b; margin-bottom: 12px; }

/* Upload zone */
.upload-zone {
    background: white; border: 2px dashed #d1d9e6; border-radius: 14px;
    padding: 24px; text-align: center; margin-bottom: 12px;
}
.upload-zone:hover { border-color: #003399; }
.upload-title { font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 3px; }
.upload-sub { font-size: 11px; color: #8492a6; }

/* Report styles */
.rpt-header {
    background: #003399; color: white; padding: 12px 24px; border-radius: 10px;
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 18px;
}
.rpt-header h2 { margin: 0; font-size: 15px; font-weight: 800; color: white !important; }
.rpt-header img { height: 28px; }

.rpt-section { margin: 16px 0 6px; font-size: 11px; font-weight: 700; color: #003399;
    text-transform: uppercase; letter-spacing: 0.8px; }

.rpt-table { width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 14px; }
.rpt-table th {
    background: #003399; color: white !important; padding: 5px 8px; text-align: center;
    font-weight: 600; font-size: 9px; text-transform: uppercase; letter-spacing: 0.3px;
}
.rpt-table td { padding: 4px 8px; border-bottom: 1px solid #eef0f4; text-align: center; color: #0f172a !important; }
.rpt-table tr:hover td { background: #f8fafc; }
.rpt-table .row-label { text-align: left; font-weight: 600; color: #003399 !important; }
.rpt-table .total-row td { background: #f8fafc; font-weight: 700; border-top: 2px solid #003399; }
.rpt-good { color: #0e7a3a !important; font-weight: 700; }
.rpt-warn { color: #c27803 !important; font-weight: 700; }
.rpt-bad { color: #c81e1e !important; font-weight: 700; }
.rpt-neutral { color: #64748b !important; }

/* Published pill */
.pill {
    font-size: 10px; font-weight: 600; padding: 3px 12px; border-radius: 16px;
    display: inline-flex; align-items: center; gap: 4px;
}
.pill-green { background: #f0fdf4; color: #0e7a3a; border: 1px solid #bbf7d0; }
.pill-amber { background: #fffbeb; color: #c27803; border: 1px solid #fde68a; }

/* Footer */
.foot { text-align: center; color: #94a3b8; font-size: 9px; padding: 14px 0; border-top: 1px solid #f1f5f9; margin-top: 24px; }

/* No-data */
.no-data {
    text-align: center; padding: 60px 20px; color: #94a3b8;
    border: 2px dashed #eef0f4; border-radius: 16px; margin: 30px 0;
}
.no-data h3 { color: #64748b; margin-bottom: 6px; }

/* Streamlit overrides */
div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; border: 1px solid #eef0f4; }
.stDownloadButton button { border-radius: 8px; }

/* Status box */
.status-box {
    background: white; border: 1px solid #eef0f4; border-radius: 12px;
    padding: 20px; margin: 14px 0; text-align: center;
}
.status-title { font-size: 11px; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
.status-info { font-size: 14px; color: #1e293b; font-weight: 700; }

/* ═══ MOBILE RESPONSIVE ═══ */
@media (max-width: 768px) {
    .main .block-container { padding: 8px 12px; }
    .topbar { padding: 8px 0; }
    .topbar-logo img { height: 36px; }
    .kpi-row { grid-template-columns: repeat(2, 1fr); gap: 8px; }
    .kpi-value { font-size: 24px; }
    .kpi-card { padding: 12px; }
    .mcards-6 { grid-template-columns: repeat(2, 1fr); }
    .mc-val { font-size: 20px; }
    .rpt-header { padding: 10px 14px; flex-direction: column; gap: 6px; }
    .rpt-header h2 { font-size: 12px; text-align: center; }
    .rpt-table { font-size: 9px; }
    .rpt-table th { font-size: 8px; padding: 3px 4px; }
    .rpt-table td { padding: 3px 4px; }
    .stTabs [data-baseweb="tab"] { font-size: 11px; padding: 6px 10px; }
}
@media (max-width: 480px) {
    .kpi-row { grid-template-columns: 1fr; }
    .mcards-6 { grid-template-columns: repeat(2, 1fr); }
}
</style>
""", unsafe_allow_html=True)

# ── Top bar ──
logo_img = f'<img src="data:image/png;base64,{logo_b64}">' if logo_b64 else '<span style="font-weight:900;color:#003399;font-size:18px;">SUZUKI</span>'
badge = '<span class="topbar-badge badge-admin">Admin</span>' if is_admin else ''
st.markdown(f"""<div class="topbar">
    <div class="topbar-logo">{logo_img}</div>
    <div class="topbar-right">
        {badge}
        <span class="topbar-date">{datetime.now().strftime('%d %b %Y')}</span>
    </div>
</div>""", unsafe_allow_html=True)

# ── Load persisted state ──
data = load_json('current_report')
prev_data = load_json('prev_month')
published = load_json('published_state', {})
objetivos = load_json('objetivos', {
    'total': DEFAULT_OBJETIVO_TOTAL, 'propio': DEFAULT_OBJETIVO_PROPIO,
    'tercero': DEFAULT_OBJETIVO_TERCERO, 'total_prev': 3239,
    'por_ciudad': DEFAULT_OBJETIVOS_CIUDAD, 'por_modelo': DEFAULT_OBJETIVOS_MODELO,
    'ciudad_modelo': DEFAULT_OBJ_CIUDAD_MODELO,
})

now = datetime.now()
is_published = published.get('is_published', False)

# ── Tabs based on role ──
if is_admin:
    tabs = st.tabs(["📂  Cargar Datos", "🎯  Objetivos", "📊  Dashboard", "📄  Reporte"])
    tab_upload, tab_obj, tab_dash, tab_report = tabs
else:
    tabs = st.tabs(["📊  Dashboard", "📄  Reporte"])
    tab_dash, tab_report = tabs
    tab_upload = tab_obj = None


# ══════════════════════════════════════════
# TAB: CARGAR DATOS (Admin only)
# ══════════════════════════════════════════
if tab_upload is not None:
  with tab_upload:
    # Show current publish status
    if is_published:
        st.markdown(f"""<div class="status-box">
            <div class="status-title">Estado del Reporte</div>
            <div class="status-info"><span class="pill pill-green">● Publicado — {published.get('timestamp','')}</span></div>
            <div style="font-size:11px;color:#94a3b8;margin-top:6px;">{MESES.get(published.get('mes',0),'')} {published.get('anio','')} — Corte día {published.get('dia_corte','')}</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class="status-box">
            <div class="status-title">Estado del Reporte</div>
            <div class="status-info"><span class="pill pill-amber">⏳ Sin publicar — Los viewers no ven datos aún</span></div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<p style="color:#64748b;font-size:12px;margin-bottom:16px;">Sube los archivos, revisa los datos y publica para que el equipo pueda verlos.</p>', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1], gap="large")

    with c1:
        st.markdown("""<div class="upload-zone">
            <div class="upload-title">📊 Mes Actual</div>
            <div class="upload-sub">Archivos del período en curso</div>
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
            <div class="upload-sub">Opcional — para comparación automática</div>
        </div>""", unsafe_allow_html=True)

        prev_mes = st.selectbox("Mes anterior", range(1, 13),
                                index=(now.month - 2) % 12, format_func=lambda x: MESES[x], key="mes_prev")
        prev_anio = st.number_input("Año", min_value=2024, max_value=2030, value=now.year, key="anio_prev")
        file_prev_reporte = st.file_uploader("Reporte Leads (mes anterior)", type=['xlsx', 'xls'], key="fp_rpt")
        file_prev_data = st.file_uploader("Data Terceros (mes anterior)", type=['xlsx', 'xls'], key="fp_data")

    st.markdown("---")

    can_process = file_reporte and file_data

    col_proc, col_pub = st.columns([1, 1])

    with col_proc:
        if can_process:
            if st.button("⚙️  Procesar Datos (vista previa)", type="secondary", use_container_width=True):
                with st.spinner("Procesando datos..."):
                    try:
                        result = process_all_data(file_reporte, file_data)
                        result['dia_corte'] = dia_corte
                        result['mes'] = mes
                        result['anio'] = anio
                        result['timestamp'] = datetime.now().strftime('%d/%m/%Y %H:%M')
                        save_json('current_report', result)
                        data = result

                        if file_prev_reporte and file_prev_data:
                            prev_result = process_all_data(file_prev_reporte, file_prev_data)
                            prev_result['mes'] = prev_mes
                            save_json('prev_month', prev_result)
                            prev_data = prev_result

                        st.success("Datos procesados. Revisa en **Dashboard** y luego **publica** cuando estés listo.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                        import traceback
                        st.code(traceback.format_exc())
        else:
            st.info("Sube al menos los dos archivos del **mes actual** para continuar.")

    with col_pub:
        if data:
            if st.button("🚀  Publicar Reporte", type="primary", use_container_width=True,
                         help="Publica los datos para que todos los viewers puedan verlos"):
                save_json('published_state', {
                    'is_published': True,
                    'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M'),
                    'mes': data.get('mes', now.month),
                    'anio': data.get('anio', now.year),
                    'dia_corte': data.get('dia_corte', now.day),
                })
                st.success("Reporte publicado. El equipo ya puede verlo.")
                st.rerun()

    # Quick preview of processed data
    if data and not is_published:
        st.markdown("---")
        st.markdown('<div class="sec">Vista previa de datos procesados</div>', unsafe_allow_html=True)
        qc1, qc2, qc3, qc4 = st.columns(4)
        qc1.metric("Total Leads", f"{data['total']:,}")
        qc2.metric("Red Propia", f"{data['por_dealer']['Propio']:,}")
        qc3.metric("Terceros", f"{data['por_dealer']['Tercero']:,}")
        qc4.metric("Modelos", len([m for m in MODELOS_ORDER if data['por_modelo'].get(m, 0) > 0]))


# ══════════════════════════════════════════
# TAB: OBJETIVOS (Admin only)
# ══════════════════════════════════════════
if tab_obj is not None:
  with tab_obj:
    st.markdown('<p style="color:#64748b;font-size:12px;margin-bottom:14px;">Configura los objetivos mensuales. Se guardan automáticamente.</p>', unsafe_allow_html=True)

    st.markdown('<div class="cfg-box"><div class="cfg-title">Objetivos Generales</div>', unsafe_allow_html=True)
    g1, g2, g3, g4 = st.columns(4)
    with g1: ot = st.number_input("Total", value=objetivos.get('total', DEFAULT_OBJETIVO_TOTAL), step=10, key="ot")
    with g2: op = st.number_input("Propio", value=objetivos.get('propio', DEFAULT_OBJETIVO_PROPIO), step=10, key="op")
    with g3: otr = st.number_input("Tercero", value=objetivos.get('tercero', DEFAULT_OBJETIVO_TERCERO), step=10, key="otr")
    with g4: otp = st.number_input("Obj. Mes Anterior", value=objetivos.get('total_prev', 3239), step=10, key="otp")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="cfg-box"><div class="cfg-title">Por Ciudad</div>', unsafe_allow_html=True)
    cc_cols = st.columns(len(CIUDADES_ORDER))
    oc = {}
    for i, c in enumerate(CIUDADES_ORDER):
        with cc_cols[i]:
            oc[c] = st.number_input(CIUDAD_PROVINCIA[c], value=objetivos.get('por_ciudad', DEFAULT_OBJETIVOS_CIUDAD).get(c, 0), step=5, key=f"oc_{c}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="cfg-box"><div class="cfg-title">Por Modelo</div>', unsafe_allow_html=True)
    mc_cols = st.columns(len(MODELOS_ORDER))
    om = {}
    for i, m in enumerate(MODELOS_ORDER):
        with mc_cols[i]:
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
with tab_dash:
    show_dash = (is_admin and data) or (not is_admin and is_published and data)

    if not show_dash:
        if not is_admin and not is_published:
            st.markdown("""<div class="no-data">
                <h3>Reporte aún no disponible</h3>
                <p style="font-size:13px;">El equipo de marketing está preparando los datos de hoy.<br>Vuelve a consultar en unos minutos.</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="no-data">
                <h3>No hay datos cargados</h3>
                <p style="font-size:13px;">Ve a "Cargar Datos" para subir los archivos.</p>
            </div>""", unsafe_allow_html=True)
    else:
        mes_nombre = MESES.get(data.get('mes', now.month), '')
        prev_mes_nombre = MESES.get(data.get('mes', now.month) - 1, '') if data.get('mes', now.month) > 1 else MESES.get(12, '')
        dc = data.get('dia_corte', 24)
        anio_d = data.get('anio', now.year)
        avance = data['total']
        obj_t = objetivos.get('total', DEFAULT_OBJETIVO_TOTAL)
        obj_p = objetivos.get('propio', DEFAULT_OBJETIVO_PROPIO)
        obj_te = objetivos.get('tercero', DEFAULT_OBJETIVO_TERCERO)
        dias_mes = calendar.monthrange(anio_d, data.get('mes', now.month))[1]
        pct_mes = round(dc / dias_mes * 100)
        obj_parcial = int(round(obj_t * pct_mes / 100))
        prev = prev_data if prev_data else DEFAULT_PREV_DATA

        pub_ts = published.get('timestamp', data.get('timestamp', ''))
        st.markdown(f'<span class="pill pill-green">● Publicado {pub_ts}</span> &nbsp; <span style="font-size:10px;color:#94a3b8;">Corte: día {dc} de {mes_nombre} ({pct_mes}% del mes)</span>', unsafe_allow_html=True)

        # KPI cards
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

        # Fuente + Comparación
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
                <div style="background:white;border:1px solid #eef0f4;border-radius:10px;padding:16px;text-align:center;">
                    <div style="font-size:9px;color:#94a3b8;font-weight:600;">VS MES ANTERIOR</div>
                    <div style="font-size:26px;font-weight:900;color:{'#0e7a3a' if avance >= ptot else '#c81e1e'};">{vp(avance, ptot)}</div>
                    <div style="font-size:10px;color:#94a3b8;">{ptot:,} → {avance:,}</div>
                </div>
                <div style="background:white;border:1px solid #eef0f4;border-radius:10px;padding:16px;text-align:center;">
                    <div style="font-size:9px;color:#94a3b8;font-weight:600;">PROPIO vs ANT.</div>
                    <div style="font-size:26px;font-weight:900;color:{'#0e7a3a' if data['por_dealer']['Propio'] >= prev.get('por_dealer',{}).get('Propio',0) else '#c81e1e'};">{vp(data['por_dealer']['Propio'], prev.get('por_dealer',{}).get('Propio',0))}</div>
                    <div style="font-size:10px;color:#94a3b8;">{prev.get('por_dealer',{}).get('Propio',0):,} → {data['por_dealer']['Propio']:,}</div>
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
                r = {'Ciudad': CIUDAD_PROVINCIA[c], 'Obj': objetivos.get('por_ciudad', DEFAULT_OBJETIVOS_CIUDAD).get(c, 0)}
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
            # HTML table with color-coded percentages
            pch = '<table class="rpt-table"><tr><th>Ciudad</th>'
            for m in MODELOS_ORDER: pch += f'<th>{m}</th>'
            pch += '<th>Total</th></tr>'
            for c in CIUDADES_ORDER:
                pch += f'<tr><td class="row-label">{CIUDAD_PROVINCIA[c]}</td>'
                for m in MODELOS_ORDER:
                    v = data['ciudad_modelo'].get(c, {}).get(m, 0)
                    o = objetivos.get('ciudad_modelo', DEFAULT_OBJ_CIUDAD_MODELO).get(c, {}).get(m, 0)
                    cp = p(v, o)
                    pch += f'<td class="{rc(cp)}">{cp}%</td>'
                tv = sum(data['ciudad_modelo'].get(c, {}).get(m, 0) for m in MODELOS_ORDER)
                to = objetivos.get('por_ciudad', DEFAULT_OBJETIVOS_CIUDAD).get(c, 0)
                tcp = p(tv, to)
                pch += f'<td class="{rc(tcp)}" style="font-weight:800;">{tcp}%</td>'
                pch += '</tr>'
            pch += '</table>'
            st.markdown(pch, unsafe_allow_html=True)

        st.markdown(f'<div class="foot">Suzuki Ecuador — Leads Report — {pub_ts}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════
# TAB: REPORTE
# ══════════════════════════════════════════
with tab_report:
    show_rpt = (is_admin and data) or (not is_admin and is_published and data)

    if not show_rpt:
        if not is_admin and not is_published:
            st.markdown("""<div class="no-data">
                <h3>Reporte aún no disponible</h3>
                <p style="font-size:13px;">El equipo de marketing está preparando los datos de hoy.</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="no-data">
                <h3>No hay datos cargados</h3>
                <p style="font-size:13px;">Ve a "Cargar Datos" para subir los archivos.</p>
            </div>""", unsafe_allow_html=True)
    else:
        mes_nombre = MESES.get(data.get('mes', now.month), '')
        prev_mes_nombre = MESES.get(data.get('mes', now.month) - 1, '') if data.get('mes', now.month) > 1 else MESES.get(12, '')
        dc = data.get('dia_corte', 24)
        anio_d = data.get('anio', now.year)
        avance = data['total']
        obj_t = objetivos.get('total', DEFAULT_OBJETIVO_TOTAL)
        obj_p = objetivos.get('propio', DEFAULT_OBJETIVO_PROPIO)
        obj_te = objetivos.get('tercero', DEFAULT_OBJETIVO_TERCERO)
        dias_mes = calendar.monthrange(anio_d, data.get('mes', now.month))[1]
        pct_mes = round(dc / dias_mes * 100)
        obj_parcial = int(round(obj_t * pct_mes / 100))
        prev = prev_data if prev_data else DEFAULT_PREV_DATA

        dl = f"{dc}-{mes_nombre[:3].lower()}"
        pl = f"{dc}-{prev_mes_nombre[:3].lower()}"

        # Report header
        logo_rpt = f'<img src="data:image/png;base64,{logo_b64}" style="height:28px;">' if logo_b64 else '<span style="font-weight:900;color:white;">SUZUKI</span>'
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
                pdf = generate_report_pdf(data, obj_for_pdf, data.get('mes', now.month), anio_d, prev)
                st.download_button("⬇️  Descargar PDF", data=pdf,
                                   file_name=f"SZK_Reporte_{dc}_{mes_nombre}_{anio_d}.pdf",
                                   mime="application/pdf", use_container_width=True)

        st.markdown(f'<div class="foot">Suzuki Ecuador — Reporte de Generación de Leads — {data.get("timestamp","")}</div>', unsafe_allow_html=True)
