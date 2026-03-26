"""Data processing logic for Suzuki Leads Report."""

import pandas as pd
import unicodedata
from config import (
    DISTRIBUIDOR_CIUDAD, TERCERO_CIUDAD_KEYWORDS,
    FUENTE_MAP_PROPIO, MODEL_MAP_PROPIO, MODEL_MAP_META, MODEL_MAP_LANDING,
    FUENTES_ORDER, MODELOS_ORDER, CIUDADES_ORDER,
)


def _normalize(text: str) -> str:
    """Normalize text: remove non-breaking spaces, newlines, extra whitespace."""
    if not text:
        return ''
    text = unicodedata.normalize('NFKD', text)
    text = text.replace('\xa0', ' ').replace('\n', ' ').replace('\r', '')
    text = ' '.join(text.split())
    return text.strip()


def _match_model(model_raw: str, model_map: dict):
    """Match a raw model string against a model map, longest key first."""
    model_norm = _normalize(model_raw).upper().replace('-', ' ')
    # Sort keys by length descending so longer/more specific keys match first
    sorted_keys = sorted(model_map.keys(), key=len, reverse=True)
    for key in sorted_keys:
        key_norm = _normalize(key).upper().replace('-', ' ')
        if key_norm in model_norm:
            return model_map[key]
    return None


def _match_ciudad(text: str):
    """Match a text string against city keywords."""
    text_norm = _normalize(text).lower()
    for keyword, code in TERCERO_CIUDAD_KEYWORDS.items():
        if keyword.lower() in text_norm:
            return code
    return None


def _find_col_index(header_row: list, *possible_names: str):
    """Find column index by trying multiple header names (case-insensitive)."""
    for i, val in enumerate(header_row):
        val_clean = _normalize(str(val)).lower() if pd.notna(val) else ''
        for name in possible_names:
            if name.lower() == val_clean:
                return i
    return None


def parse_reporte_leads(file) -> pd.DataFrame:
    df_raw = pd.read_excel(file, sheet_name='Report', header=None)
    header_idx = None
    for i in range(len(df_raw)):
        row = df_raw.iloc[i].tolist()
        row_clean = [_normalize(str(v)) for v in row]
        if 'Distribuidor' in row_clean and 'Auto' in row_clean:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("No se encontró la fila de encabezado en el Reporte Leads")

    data = df_raw.iloc[header_idx + 1:].copy()
    data.columns = [_normalize(str(v)) for v in df_raw.iloc[header_idx].tolist()]
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
        dealer_info = _normalize(str(row.iloc[10])) if pd.notna(row.iloc[10]) else ''
        model_raw = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ''
        source = _normalize(str(row.iloc[11])).lower() if pd.notna(row.iloc[11]) else ''

        if not dealer_info or not model_raw:
            continue

        ciudad = _match_ciudad(dealer_info)
        if ciudad is None:
            continue

        modelo = _match_model(model_raw, MODEL_MAP_META)
        if modelo and source in ('fb', 'ig'):
            records.append({
                'Ciudad': ciudad, 'Fuente_Norm': 'FB/IG',
                'Modelo': modelo, 'Dealer_Tipo': 'Tercero', 'Leads': 1,
            })

    return pd.DataFrame(records) if records else pd.DataFrame(
        columns=['Ciudad', 'Fuente_Norm', 'Modelo', 'Dealer_Tipo', 'Leads'])


def parse_landing(file) -> pd.DataFrame:
    df_raw = pd.read_excel(file, sheet_name='landing', header=None)

    # Dynamically find header row
    header_idx = None
    for i in range(min(10, len(df_raw))):
        row_vals = [_normalize(str(v)).lower() if pd.notna(v) else '' for v in df_raw.iloc[i]]
        if 'fecha' in row_vals and ('modelo' in row_vals or 'ciudad' in row_vals):
            header_idx = i
            break
    if header_idx is None:
        return pd.DataFrame(columns=['Ciudad', 'Fuente_Norm', 'Modelo', 'Dealer_Tipo', 'Leads'])

    # Get header values for dynamic column detection
    header_vals = [_normalize(str(v)) if pd.notna(v) else '' for v in df_raw.iloc[header_idx]]

    col_ciudad = _find_col_index(header_vals, 'Ciudad')
    col_modelo = _find_col_index(header_vals, 'Modelo')
    col_origen = _find_col_index(header_vals, 'Origen')
    col_tipo = _find_col_index(header_vals, 'Tipo Negocio', 'Tipo negocio')

    if col_ciudad is None or col_modelo is None:
        return pd.DataFrame(columns=['Ciudad', 'Fuente_Norm', 'Modelo', 'Dealer_Tipo', 'Leads'])

    data = df_raw.iloc[header_idx + 1:].copy()
    data = data.dropna(how='all')

    excluded_models = ['Grand Vitara', 'Alto', 'Celerio', 'Ciaz', 'Baleno', 'Ertiga', 'Vitara']
    records = []
    for _, row in data.iterrows():
        ciudad_raw = _normalize(str(row.iloc[col_ciudad])) if pd.notna(row.iloc[col_ciudad]) else ''
        model_raw = _normalize(str(row.iloc[col_modelo])) if pd.notna(row.iloc[col_modelo]) else ''
        origen = _normalize(str(row.iloc[col_origen])) if col_origen is not None and pd.notna(row.iloc[col_origen]) else ''
        tipo_negocio = _normalize(str(row.iloc[col_tipo])).lower() if col_tipo is not None and pd.notna(row.iloc[col_tipo]) else ''

        # Skip aftersales
        if tipo_negocio == 'aftersales':
            continue
        # Also skip if origen contains POSVENTA
        if 'POSVENTA' in origen.upper():
            continue

        # Skip excluded models
        if any(ex.lower() in model_raw.lower() for ex in excluded_models):
            continue

        # Match city
        ciudad = _match_ciudad(ciudad_raw)
        if ciudad is None:
            continue

        # Match model
        modelo = _match_model(model_raw, MODEL_MAP_LANDING)
        if modelo is None:
            continue

        fuente = 'Landing' if 'LANDINGPAGE' in origen.upper() else 'Web'
        records.append({
            'Ciudad': ciudad, 'Fuente_Norm': fuente,
            'Modelo': modelo, 'Dealer_Tipo': 'Tercero', 'Leads': 1,
        })

    return pd.DataFrame(records) if records else pd.DataFrame(
        columns=['Ciudad', 'Fuente_Norm', 'Modelo', 'Dealer_Tipo', 'Leads'])


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
    results['por_dealer'] = {
        'Propio': int(by_dealer.get('Propio', 0)),
        'Tercero': int(by_dealer.get('Tercero', 0)),
    }

    by_ciudad = df_all.groupby('Ciudad')['Leads'].sum()
    results['por_ciudad'] = {c: int(by_ciudad.get(c, 0)) for c in CIUDADES_ORDER}

    by_modelo = df_all.groupby('Modelo')['Leads'].sum()
    results['por_modelo'] = {m: int(by_modelo.get(m, 0)) for m in MODELOS_ORDER}

    pivot = df_all.groupby(['Ciudad', 'Modelo'])['Leads'].sum().unstack(fill_value=0)
    results['ciudad_modelo'] = {}
    for c_code in CIUDADES_ORDER:
        results['ciudad_modelo'][c_code] = {}
        for m in MODELOS_ORDER:
            results['ciudad_modelo'][c_code][m] = int(
                pivot.loc[c_code, m]) if c_code in pivot.index and m in pivot.columns else 0

    return results
