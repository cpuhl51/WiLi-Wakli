import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import math

# --- 1. SETUP & CSS (PIXEL ART & SCHILDER) ---
st.set_page_config(page_title="Wien Öffis Master", layout="wide", page_icon="🚋")

st.markdown("""
    <style>
    .block-container { padding-top: 0rem; }
    
    /* --- FAHRZEUG STYLES (Pixel Art Nachbau) --- */
    .train-body {
        height: 22px; width: 46px;
        border: 2px solid #222; border-radius: 4px;
        display: flex; flex-direction: column; justify-content: space-between;
        box-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        font-family: monospace; font-weight: bold; font-size: 9px;
        overflow: hidden; position: relative;
    }
    .windows { height: 8px; width: 100%; background: #333; margin-top: 3px; opacity: 0.9; }
    
    /* U-BAHN: Silberpfeil (Type U) */
    .type-u { background: linear-gradient(180deg, #ccc 0%, #999 100%); color: black; }
    
    /* U-BAHN: V-Wagen (Rot/Silber Streifen) */
    .type-v { 
        background: linear-gradient(90deg, #ccc 0%, #ccc 15%, #d32f2f 15%, #d32f2f 25%, #ccc 25%, #ccc 75%, #d32f2f 75%, #d32f2f 85%, #ccc 85%);
        color: black; 
    }
    
    /* U6: Type T/T1 (Kastiger, Weiß/Rot) */
    .type-u6 {
        background: linear-gradient(180deg, #fff 40%, #d32f2f 40%, #d32f2f 60%, #fff 60%);
        color: black; border-radius: 2px;
    }

    /* TRAM: Old (E2 - Rot/Weiß) */
    .type-e2 { background: linear-gradient(180deg, #d32f2f 50%, #fff 50%); color: black; }

    /* TRAM: ULF (Ultra Low Floor - Grau/Rot, schräge Front simulieren wir mit border) */
    .type-ulf {
        background: linear-gradient(90deg, #b71c1c 0%, #b71c1c 10%, #555 10%);
        color: white; border-top-right-radius: 10px; border-bottom-right-radius: 0;
    }
    
    /* BUS */
    .type-bus { background: #d32f2f; border-radius: 6px; color: white; }

    /* --- HALTESTELLEN SCHILD (OVAL) --- */
    .station-sign {
        width: 34px; height: 24px;
        background-color: #fdf5e6; /* Beige */
        border: 3px solid #b22222; /* Dunkelrot */
        border-radius: 50%; /* Oval */
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        box-shadow: 0 3px 6px rgba(0,0,0,0.4);
        position: relative;
    }
    /* Schwarze Streifen (statt Text) */
    .sign-stripe { width: 60%; height: 2px; background: black; margin: 2px 0; }
    /* Wappen in der Mitte (Simuliert durch roten Kreis mit Kreuz) */
    .sign-logo {
        width: 8px; height: 9px;
        background: #d32f2f;
        border-radius: 2px; border-bottom-left-radius: 4px; border-bottom-right-radius: 4px;
        position: relative;
    }
    .sign-logo::after {
        content: ""; position: absolute; top: 0; left: 3px; width: 2px; height: 9px; background: white;
    }
    .sign-logo::before {
        content: ""; position: absolute; top: 3px; left: 0; width: 8px; height: 2px; background: white;
    }

    </style>
    """, unsafe_allow_html=True)

st.title("🇦🇹 Wiener Linien Live-Map (Vollständig)")

# --- 2. DATEN: ROUTEN (Vollständig von Endstelle zu Endstelle) ---
# Koordinaten sind vereinfacht, bilden aber die ganze Stadt ab.

RAW_ROUTES = {
    # U-BAHNEN
    "U1": [[48.1530, 16.3850], [48.1700, 16.3800], [48.1870, 16.3750], [48.2000, 16.3700], [48.2082, 16.3738], [48.2130, 16.3780], [48.2180, 16.3900], [48.2250, 16.4000], [48.2350, 16.4200], [48.2450, 16.4400], [48.2600, 16.4500]], # Oberlaa <-> Leopoldau
    "U2": [[48.2200, 16.5100], [48.2150, 16.4500], [48.2180, 16.4200], [48.2180, 16.3900], [48.2150, 16.3610], [48.2100, 16.3570], [48.2070, 16.3580], [48.2000, 16.3690]], # Seestadt <-> Karlsplatz
    "U3": [[48.2110, 16.3100], [48.1960, 16.3350], [48.1950, 16.3500], [48.2082, 16.3738], [48.2050, 16.3850], [48.1900, 16.4000], [48.1750, 16.4150]], # Ottakring <-> Simmering
    "U4": [[48.2050, 16.2500], [48.1900, 16.2900], [48.1850, 16.3200], [48.1900, 16.3500], [48.2000, 16.3690], [48.2082, 16.3738], [48.2114, 16.3783], [48.2166, 16.3730], [48.2250, 16.3600], [48.2400, 16.3600]], # Hütteldorf <-> Heiligenstadt
    "U6": [[48.1350, 16.3200], [48.1500, 16.3300], [48.1750, 16.3350], [48.1960, 16.3350], [48.2150, 16.3400], [48.2300, 16.3500], [48.2400, 16.3800], [48.2600, 16.4000]], # Siebenhirten <-> Floridsdorf
    
    # STRASSENBAHNEN (Ring & Co)
    "1": [[48.2114, 16.3783], [48.2166, 16.3730], [48.2150, 16.3650], [48.2110, 16.3600], [48.2050, 16.3600], [48.2020, 16.3680], [48.2030, 16.3750], [48.2050, 16.3850], [48.2100, 16.3950]],
    "D": [[48.2600, 16.3650], [48.2350, 16.3600], [48.2166, 16.3730], [48.2150, 16.3650], [48.2050, 16.3600], [48.1900, 16.3800]],
    "2": [[48.2114, 16.3783], [48.2110, 16.3600], [48.2080, 16.3500], [48.2100, 16.3400]],
    "71": [[48.2160, 16.3690], [48.2050, 16.3600], [48.2020, 16.3680], [48.1950, 16.3900], [48.1800, 16.4100], [48.1600, 16.4400]]
}

# Stations-Marker Positionen & RBLs
STATION_MARKERS = [
    {"name": "Schwedenplatz", "lat": 48.2114, "lon": 16.3783, "lines": "U1, U4, 1, 2", "rbl": [4205, 4212, 4208, 4210]},
    {"name": "Karlsplatz", "lat": 48.2000, "lon": 16.3690, "lines": "U1, U2, U4, WLB", "rbl": [4202, 4216, 4617, 4214]},
    {"name": "Stephansplatz", "lat": 48.2082, "lon": 16.3738, "lines": "U1, U3", "rbl": [4200, 4206]},
    {"name": "Westbahnhof", "lat": 48.1960, "lon": 16.3350, "lines": "U3, U6, 5, 6, 9, 18", "rbl": [4920, 4921, 4600]},
    {"name": "Schottentor", "lat": 48.2150, "lon": 16.3610, "lines": "U2, D, 1, 71", "rbl": [4209, 4211]},
    {"name": "Landstraße", "lat": 48.2060, "lon": 16.3850, "lines": "U3, U4, O", "rbl": [4204, 4213]},
    {"name": "Praterstern", "lat": 48.2180, "lon": 16.3900, "lines": "U1, U2, 5, O", "rbl": [4207, 4105]}
]

# Farben
LINE_COLORS = {
    "U1": "#E2021A", "U2": "#A365A4", "U3": "#F67F21", 
    "U4": "#009641", "U5": "#F67F21", "U6": "#9D6643", # U6 Ocker
    "1": "#FF5C5C", "2": "#FF5C5C", "D": "#FF5C5C", "71": "#FF5C5C"
}

# --- 3. HELPER ---
def smooth_path(points):
    """Fügt weiche Kurven zwischen Punkten ein"""
    if len(points) < 2: return points
    smoothed = []
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i+1]
        steps = 8 # Runder
        for j in range(steps):
            f = j / steps
            smoothed.append([p1[0]*(1-f)+p2[0]*f, p1[1]*(1-f)+p2[1]*f])
    smoothed.append(points[-1])
    return smoothed

SMOOTH_ROUTES = {k: smooth_path(v) for k,v in RAW_ROUTES.items()}

def get_css_class(line, v_type, features):
    if line == "U6": return "type-u6"
    if "ptMetro" in v_type or "U" in line:
        if features.get("foldingRamp") or features.get("barrierFree"): return "type-v"
        return "type-u"
    if "ptTram" in v_type:
        if features.get("foldingRamp"): return "type-ulf"
        return "type-e2"
    if "S" in line: return "type-u" # S-Bahn Fallback
    return "type-bus"

def calculate_bearing(p1, p2):
    lat1, lat2 = math.radians(p1[0]), math.radians(p2[0])
    dLon = math.radians(p2[1] - p1[1])
    x = math.sin(dLon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dLon))
    return (math.degrees(math.atan2(x, y)) + 360) % 360

# --- 4. API CALL ---
@st.cache_data(ttl=12)
def fetch_all_data():
    # Alle RBLs sammeln
    all_rbls = []
    for s in STATION_MARKERS: all_rbls.extend(s["rbl"])
    
    url = f"https://www.wienerlinien.at/ogd_realtime/monitor?rbl={'&rbl='.join(map(str, all_rbls))}"
    try:
        data = requests.get(url, timeout=5).json()
        vehicles = []
        for mon in data.get("data", {}).get("monitors", []):
            slat = mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [0,0])[1]
            slon = mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [0,0])[0]
            for line in mon.get("lines", []):
                for dep in line.get("departures", {}).get("departure", []):
                    countdown = dep.get("departureTime", {}).get("countdown", 99)
                    if countdown >
