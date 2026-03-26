"""Data processing logic for Suzuki Leads Report."""

import pandas as pd
from config import (
    DISTRIBUIDOR_CIUDAD, TERCERO_CIUDAD_KEYWORDS,
    FUENTE_MAP_PROPIO, MODEL_MAP_PROPIO, MODEL_MAP_META, MODEL_MAP_LANDING,
    FUENTES_ORDER, MODELOS_ORDER, CIUDADES_ORDER,
)


def parse_reporte_leads(file) -> pd.DataFrame:
    df_raw = pd.read_excel(file, sheet_name='Report', header=None)
    header_idx = None
    for i in range(len(df_raw)):
        row = df_raw.iloc[i].tolist()
        if 'Distribuidor' in [str(v).strip() for v in row] and 'Auto' in [str(v).strip() for v in row]:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("No se encontró la fila de encabezado en el Reporte Leads")

    data = df_raw.iloc[header_idx + 1:].copy()
    data.columns = [str(v).strip() for v in df_raw.iloc[header_idx].tolist()]
    data = data.dropna(how='all')
    data = data[data['Distribuidor'].notna()].copy()
    data['Prospectos (Digital)'] = pd.to_numeric(data['Prospectos (Digital)'], errors='coerce').fillna(0).astype(int)
    data['Ciudad'] = data['Distribuidor'].map(DISTRIBUIDOR_CIUDAD)
    data['Fuente_Norm'] = data['Fuente'].map(FUENTE_MAP_PROPIO)
    data['Modelo'] = data['Auto'].map(MODEL_MAP_PROPIO)
    data['Dealer_Tipo'] = 'Propio'
    return data[data['Modelo'].notna()].copy()


def parse_meta_leads(file) -> pd.DataFrame:
    df_raw = pd.read_excel(file, sheet_name='meta leads', header=None)
    df_raw = df_raw.dropna(how='all')
    records = []
    for _, row in df_raw.iterrows():
        dealer_info = str(row.iloc[10]) if pd.notna(row.iloc[10]) else ''
        model_raw = str(row.iloc[2]).strip().replace('\n', '') if pd.notna(row.iloc[2]) else ''
        source = str(row.iloc[11]).strip().lower() if pd.notna(row.iloc[11]) else ''

        ciudad = None
        for keyword, code in TERCERO_CIUDAD_KEYWORDS.items():
            if keyword.lower() in dealer_info.lower():
                ciudad = code
                break
        if ciudad is None:
            continue

        modelo = None
        model_upper = model_raw.upper().replace('-', ' ').strip()
        for key, val in MODEL_MAP_META.items():
            if key.upper() in model_upper:
                modelo = val
                break
        if modelo and source in ('fb', 'ig'):
            records.append({'Ciudad': ciudad, 'Fuente_Norm': 'FB/IG', 'Modelo': modelo, 'Dealer_Tipo': 'Tercero', 'Leads': 1})

    return pd.DataFrame(records) if records else pd.DataFrame(columns=['Ciudad', 'Fuente_Norm', 'Modelo', 'Dealer_Tipo', 'Leads'])


def parse_landing(file) -> pd.DataFrame:
    df_raw = pd.read_excel(file, sheet_name='landing', header=None)
    header_idx = 0
    for i in range(len(df_raw)):
        row_vals = [str(v).strip() if pd.notna(v) else '' for v in df_raw.iloc[i]]
        if 'Fecha' in row_vals or 'Nombre' in row_vals:
            header_idx = i
            break

    data = df_raw.iloc[header_idx + 1:].copy()
    data = data.dropna(how='all')
    excluded_models = ['Grand Vitara', 'Alto', 'Celerio', 'Ciaz', 'Baleno', 'Ertiga', 'Vitara']
    records = []
    for _, row in data.iterrows():
        ciudad_raw = str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) else ''
        model_raw = str(row.iloc[7]).strip() if pd.notna(row.iloc[7]) else ''
        origen = str(row.iloc[9]).strip() if pd.notna(row.iloc[9]) else ''
        tipo_negocio = str(row.iloc[8]).strip().lower() if pd.notna(row.iloc[8]) else ''

        if tipo_negocio == 'aftersales':
            continue
        if any(ex.lower() in model_raw.lower() for ex in excluded_models):
            continue

        ciudad = None
        for keyword, code in TERCERO_CIUDAD_KEYWORDS.items():
            if keyword.lower() in ciudad_raw.lower():
                ciudad = code
                break
        if ciudad is None:
            continue

        modelo = None
        for key, val in MODEL_MAP_LANDING.items():
            if key.upper() in model_raw.upper().replace('-', ' ').replace('  ', ' '):
                modelo = val
                break
        if modelo is None:
            continue

        fuente = 'Landing' if 'LANDINGPAGE' in origen.upper() else 'Web'
        records.append({'Ciudad': ciudad, 'Fuente_Norm': fuente, 'Modelo': modelo, 'Dealer_Tipo': 'Tercero', 'Leads': 1})

    return pd.DataFrame(records) if records else pd.DataFrame(columns=['Ciudad', 'Fuente_Norm', 'Modelo', 'Dealer_Tipo', 'Leads'])


def process_all_data(reporte_leads_file, data_file) -> dict:
    df_propio = parse_reporte_leads(reporte_leads_file)
    propio_records = []
    for _, row in df_propio.iterrows():
        propio_records.append({
            'Ciudad': row['Ciudad'], 'Fuente_Norm': row['Fuente_Norm'],
            'Modelo': row['Modelo'], 'Dealer_Tipo': 'Propio',
            'Leads': int(row['Prospectos (Digital)']),
        })
    df_propio_clean = pd.DataFrame(propio_records)
    df_meta = parse_meta_leads(data_file)
    df_landing = parse_landing(data_file)
    df_all = pd.concat([df_propio_clean, df_meta, df_landing], ignore_index=True)

    results = {}
    results['total'] = int(df_all['Leads'].sum())

    by_fuente = df_all.groupby('Fuente_Norm')['Leads'].sum()
    results['por_fuente'] = {f: int(by_fuente.get(f, 0)) for f in FUENTES_ORDER}

    by_dealer = df_all.groupby('Dealer_Tipo')['Leads'].sum()
    results['por_dealer'] = {'Propio': int(by_dealer.get('Propio', 0)), 'Tercero': int(by_dealer.get('Tercero', 0))}

    by_ciudad = df_all.groupby('Ciudad')['Leads'].sum()
    results['por_ciudad'] = {c: int(by_ciudad.get(c, 0)) for c in CIUDADES_ORDER}

    by_modelo = df_all.groupby('Modelo')['Leads'].sum()
    results['por_modelo'] = {m: int(by_modelo.get(m, 0)) for m in MODELOS_ORDER}

    pivot = df_all.groupby(['Ciudad', 'Modelo'])['Leads'].sum().unstack(fill_value=0)
    results['ciudad_modelo'] = {}
    for c_code in CIUDADES_ORDER:
        results['ciudad_modelo'][c_code] = {}
        for m in MODELOS_ORDER:
            results['ciudad_modelo'][c_code][m] = int(pivot.loc[c_code, m]) if c_code in pivot.index and m in pivot.columns else 0

    return results
