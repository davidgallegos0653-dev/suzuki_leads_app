"""Configuration and mappings for Suzuki Leads Report."""

DISTRIBUIDOR_CIUDAD = {
    'CUMBAYA SZK STORE': 'UIO',
    'GRANADOS SZK STORE': 'UIO',
    'LABRADOR SZK STORE': 'UIO',
    'LOS CHILLOS SZK STORE': 'UIO',
    'SUR SZK STORE': 'UIO',
    'GUAYAQUIL SZK STORE': 'GYE',
    'C.J. AROSEMENA SZK STORE': 'GYE',
    'ESPAÑA SZK STORE': 'CUE',
    'MANTA SZK STORE': 'MTA',
}

TERCERO_CIUDAD_KEYWORDS = {
    'Ambato': 'AMB',
    'Riobamba': 'RIO',
    'Cuenca': 'CUE',
    'Quito': 'UIO',
    'Guayaquil': 'GYE',
    'Manta': 'MTA',
}

CIUDAD_PROVINCIA = {
    'UIO': 'Pichincha',
    'GYE': 'Guayas',
    'CUE': 'Azuay',
    'MTA': 'Manabí',
    'RIO': 'Chimborazo',
    'AMB': 'Tungurahua',
}

CIUDADES_PROPIO = ['UIO', 'GYE', 'CUE', 'MTA']
CIUDADES_TERCERO = ['RIO', 'AMB']
CIUDADES_ORDER = ['UIO', 'GYE', 'CUE', 'MTA', 'RIO', 'AMB']

FUENTE_MAP_PROPIO = {
    'FACEBOOK': 'FB/IG',
    'LANDING PAGE': 'Landing',
    'FORMULARIO WEB': 'Web',
    'PAGINA WEB': 'Web',
    'LLAMADA 1800SUZUKI': '1800',
}

FUENTES_ORDER = ['FB/IG', 'Landing', 'WAPP', '1800', 'Web', 'TikTok']

MODEL_MAP_PROPIO = {
    'FRONX': 'Fronx',
    'SWIFT': 'Swift',
    'XL7': 'XL7',
    'JIMNY': 'Jimny 3D',
    'JIMNY 5D': 'Jimny 5D',
    'S-CROSS': 'S-Cross',
    'SIN AUTO DE INTERES': None,
}

MODEL_MAP_META = {
    'JIMNY 3 DOOR': 'Jimny 3D',
    'JIMNY 5 DOOR': 'Jimny 5D',
    'JIMNY 5D': 'Jimny 5D',
    'S-CROSS': 'S-Cross',
    'SWIFT': 'Swift',
    'FRONX': 'Fronx',
    'XL7': 'XL7',
}

MODEL_MAP_LANDING = {
    'JIMNY 5DOOR': 'Jimny 5D',
    'JIMNY-5DOOR': 'Jimny 5D',
    'JIMNY 5DOOR-COTIZACION': 'Jimny 5D',
    'JIMNY-5DOOR-COTIZACION': 'Jimny 5D',
    'JIMNY 5D': 'Jimny 5D',
    'JIMNY5D-COTIZACION': 'Jimny 5D',
    'Jimny': 'Jimny 3D',
    'JIMNY': 'Jimny 3D',
    'JIMNY-COTIZACION': 'Jimny 3D',
    'SWIFT': 'Swift',
    'SWIFT-COTIZACION': 'Swift',
    'FRONX': 'Fronx',
    'FRONX-COTIZACION': 'Fronx',
    'S-CROSS': 'S-Cross',
    'S-CROSS-COTIZACION': 'S-Cross',
    'XL7': 'XL7',
    'XL7-COTIZACION': 'XL7',
}

MODELOS_ORDER = ['Swift', 'Fronx', 'S-Cross', 'Jimny 3D', 'Jimny 5D', 'XL7']

DEFAULT_OBJETIVOS_CIUDAD = {
    'UIO': 1940, 'GYE': 800, 'CUE': 365, 'MTA': 250, 'RIO': 262, 'AMB': 302,
}

DEFAULT_OBJETIVOS_MODELO = {
    'Swift': 544, 'Fronx': 1637, 'S-Cross': 667,
    'Jimny 3D': 346, 'Jimny 5D': 364, 'XL7': 362,
}

DEFAULT_OBJETIVO_TOTAL = 3921
DEFAULT_OBJETIVO_PROPIO = 2876
DEFAULT_OBJETIVO_TERCERO = 546

DEFAULT_OBJ_CIUDAD_MODELO = {
    'UIO': {'Swift': 269, 'Fronx': 810, 'S-Cross': 330, 'Jimny 3D': 171, 'Jimny 5D': 180, 'XL7': 179},
    'GYE': {'Swift': 111, 'Fronx': 334, 'S-Cross': 136, 'Jimny 3D': 71, 'Jimny 5D': 74, 'XL7': 74},
    'CUE': {'Swift': 51, 'Fronx': 152, 'S-Cross': 62, 'Jimny 3D': 32, 'Jimny 5D': 34, 'XL7': 34},
    'MTA': {'Swift': 35, 'Fronx': 104, 'S-Cross': 43, 'Jimny 3D': 22, 'Jimny 5D': 23, 'XL7': 23},
    'RIO': {'Swift': 36, 'Fronx': 109, 'S-Cross': 45, 'Jimny 3D': 23, 'Jimny 5D': 24, 'XL7': 24},
    'AMB': {'Swift': 42, 'Fronx': 126, 'S-Cross': 51, 'Jimny 3D': 27, 'Jimny 5D': 28, 'XL7': 28},
}

DEFAULT_PREV_DATA = {
    'total': 3936,
    'por_fuente': {'FB/IG': 2118, 'Landing': 777, 'WAPP': 0, '1800': 19, 'Web': 1022, 'TikTok': 0},
    'por_dealer': {'Propio': 3736, 'Tercero': 200},
    'por_ciudad': {'UIO': 1602, 'GYE': 1408, 'CUE': 499, 'MTA': 227, 'RIO': 55, 'AMB': 145},
    'por_modelo': {'Swift': 893, 'Fronx': 839, 'S-Cross': 411, 'Jimny 3D': 984, 'Jimny 5D': 303, 'XL7': 506},
    'ciudad_modelo': {
        'UIO': {'Swift': 338, 'Fronx': 260, 'S-Cross': 100, 'Jimny 3D': 290, 'Jimny 5D': 168, 'XL7': 158},
        'GYE': {'Swift': 117, 'Fronx': 200, 'S-Cross': 65, 'Jimny 3D': 63, 'Jimny 5D': 68, 'XL7': 68},
        'CUE': {'Swift': 34, 'Fronx': 53, 'S-Cross': 24, 'Jimny 3D': 29, 'Jimny 5D': 34, 'XL7': 34},
        'MTA': {'Swift': 44, 'Fronx': 35, 'S-Cross': 15, 'Jimny 3D': 34, 'Jimny 5D': 34, 'XL7': 25},
        'RIO': {'Swift': 0, 'Fronx': 0, 'S-Cross': 0, 'Jimny 3D': 0, 'Jimny 5D': 0, 'XL7': 0},
        'AMB': {'Swift': 0, 'Fronx': 0, 'S-Cross': 0, 'Jimny 3D': 0, 'Jimny 5D': 0, 'XL7': 0},
    },
}

MESES = {
    1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL',
    5: 'MAYO', 6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO',
    9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE',
}
