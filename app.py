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
    /* Container für das Fahrzeug */
    .train-wrapper {
        transition: transform 0.5s linear;
    }
    
    .train-body {
        height: 20px; width: 44px;
        border: 2px solid #222; border-radius: 3px;
        display: flex; flex-direction: column; justify-content: space-between;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.5);
        font-family: monospace; font-weight: bold; font-size: 9px;
        overflow: hidden; position: relative; background: #ccc;
    }
    
    /* Fensterband */
    .windows { 
        height: 6px; width: 100%; 
        background: #333; margin-top: 3px; opacity: 0.85; 
        border-bottom: 1px solid #555;
    }
    
    /* U-BAHN: Silberpfeil (Grau) */
    .type-u { background: linear-gradient(180deg, #dddddd 0%, #999999 100%); color: black; }
    
    /* U-BAHN: V-Wagen (Silber mit roten Streifen an Türen) */
    .type-v { 
        background: repeating-linear-gradient(90deg, 
            #e0e0e0 0px, #e0e0e0 10px, 
            #d32f2f 10px, #d32f2f 14px);
        color: black; 
    }
    
    /* U6: Type T (Kastig, Oben Weiß, Unten Rot) */
    .type-u6 {
        background: linear-gradient(180deg, #ffffff 45%, #d32f2f 45%);
        color: black; border-radius: 1px;
    }

    /* TRAM: Old (E2 - Rot/Weiß) */
    .type-e2 { background: linear-gradient(180deg, #d32f2f 50%, #ffffff 50%); color: black; }

    /* TRAM: ULF (Modern - Grau/Rot mit schräger Front) */
    .type-ulf {
        background: linear-gradient(90deg, #b71c1c 0%, #b71c1c 20%, #777 20%);
        color: white; border-top-right-radius: 8px; 
    }
    
    /* BUS */
    .type-bus { background: #d32f2f; border-radius: 5px; color: white; }

    /* --- HALTESTELLEN SCHILD (OVAL) --- */
    .station-sign {
        width: 36px; height: 26px;
        background-color: #fdf5e6; /* Beige */
        border: 3px solid #b22222; /* Dunkelrot */
        border-radius: 50%; /* Oval */
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        box-shadow: 0 3px 6px rgba(0,0,0,0.4);
    }
    .sign-stripe { width: 20px; height: 2px; background: black; margin: 2px 0; }
    .sign-logo {
        width: 8px; height: 10px; background: #d32f2f;
        border-radius: 0 0 4px 4px; border-top: 2px solid white;
    }

    </style>
    """, unsafe_allow_html=True)

st.title("🇦🇹 Wiener Linien Live-Map")

# --- 2. DATEN: ROUTEN (Endstelle bis Endstelle) ---
RAW_ROUTES = {
    # U-BAHNEN
    "U1": [[48.1530, 16.3850], [48.1700, 16.3800], [48.1870, 16.3750], [48.2000, 16.3700], [48.2082, 16.3738], [48.2130, 16.3780], [48.2180, 16.3900], [48.2250, 16.4000], [48.2350, 16.4200], [48.2450, 16.4400], [48.2600, 16.4500]], 
    "U2": [[48.2200, 16.5100], [48.2150, 16.4500], [48.2180, 16.4200], [48.2180, 16.3900], [48.2150, 16.3610], [48.2100, 16.3570], [48.2070, 16.3580], [48.2000, 16.3690]], 
    "U3": [[48.2110, 16.3100], [48.1960, 16.3350], [48.1950, 16.3500], [48.2082, 16.3738], [48.2050, 16.3850], [48.1900, 16.4000], [48.1750, 16.4150]], 
    "U4": [[48.2050, 16.2500], [48.1900, 16.2900], [48.1850, 16.3200], [48.1900, 16.3500], [48.2000, 16.3690], [48.2082, 16.3738], [48.2114, 16.3783], [48.2166, 16.3730], [48.2250, 16.3600], [48.2400, 16.3600]], 
    "U6": [[48.1350, 16.3200], [48.1500, 16.3300], [48.1750, 16.3350], [48.1960, 16.3350], [48.2150, 16.3400], [48.2300, 16.3500], [48.2400, 16.3800], [48.2600, 16.4000]], 
    
    # STRASSENBAHNEN
    "1": [[48.2114, 16.3783], [48.2166, 16.3730], [48.2150, 16.3650], [48.2110, 16.3600], [48.2050, 16.3600], [48.2020, 16.3680], [48.2030, 16.3750], [48.2050, 16.3850], [48.2100, 16.3950]],
    "D": [[48.2600, 16.3650], [48.2350, 16.3600], [48.2166, 16.3730], [48.2150, 16.3650], [48.2050, 16.3600], [48.1900, 16.3800]],
    "2": [[48.2114, 16.3783], [48.2110, 16.3600], [48.2080, 16.3500], [48.2100, 16.3400]],
    "71": [[48.2160, 16.3690], [48.2050, 16.3600], [48.2020, 16.3680], [48.1950, 16.3900], [48.1800, 16.4100], [48.1600, 16.4400]]
}

# Stations-Marker Positionen & RBLs (Zum Abfragen der Live-Daten)
STATION_MARKERS = [
    {"name": "Schwedenplatz", "lat": 48.2114, "lon": 16.3783, "lines": "U1, U4, 1, 2", "rbl": [4205, 4212, 4208, 4210]},
    {"name": "Karlsplatz", "lat": 48.2000, "lon": 16.3690, "lines": "U1, U2, U4, WLB", "rbl": [4202, 4216, 4617, 4214]},
    {"name": "Stephansplatz", "lat": 48.2082, "lon": 16.3738, "lines": "U1, U3", "rbl": [4200, 4206]},
    {"name": "Westbahnhof", "lat": 48.1960, "lon": 16.3350, "lines": "U3, U6, 5, 6, 9, 18", "rbl": [4920, 4921, 4600]},
    {"name": "Schottentor", "lat": 48.2150, "lon": 16.3610, "lines": "U2, D, 1, 71", "rbl": [4209, 4211]},
    {"name": "Landstraße", "lat": 48.2060, "lon": 16.3850, "lines": "U3, U4, O", "rbl": [4204, 4213]},
    {"name": "Praterstern", "lat": 48.2180, "lon": 16.3900, "lines": "U1, U2, 5, O", "rbl": [4207, 4105]}
]

LINE_COLORS = {
    "U1": "#E2021A", "U2": "#A365A4", "U3": "#F67F21", 
    "U4": "#009641", "U5": "#F67F21", "U6": "#9D6643", 
    "1": "#FF5C5C", "2": "#FF5C5C", "D": "#FF5C5C", "71": "#FF5C5C"
}

# --- 3. HELFER FUNKTIONEN ---

def smooth_path(points):
    """Macht eckige Pfade rund"""
    if len(points) < 2: return points
    smoothed = []
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i+1]
        steps = 8
        for j in range(steps):
            f = j / steps
            smoothed.append([p1[0]*(1-f)+p2[0]*f, p1[1]*(1-f)+p2[1]*f])
    smoothed.append(points[-1])
    return smoothed

SMOOTH_ROUTES = {k: smooth_path(v) for k,v in RAW_ROUTES.items()}

def get_css_class(line, v_type, features):
    # CSS Klasse wählen basierend auf Typ
    if line == "U6": return "type-u6"
    if "ptMetro" in v_type or "U" in line:
        if features.get("foldingRamp") or features.get("barrierFree"): return "type-v"
        return "type-u"
    if "ptTram" in v_type:
        if features.get("foldingRamp"): return "type-ulf"
        return "type-e2"
    if "S" in line: return "type-u" 
    return "type-bus"

def calculate_bearing(p1, p2):
    lat1, lat2 = math.radians(p1[0]), math.radians(p2[0])
    dLon = math.radians(p2[1] - p1[1])
    x = math.sin(dLon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dLon))
    return (math.degrees(math.atan2(x, y)) + 360) % 360

# --- 4. API ABRUF ---
@st.cache_data(ttl=12)
def fetch_all_data():
    all_rbls = []
    for s in STATION_MARKERS: all_rbls.extend(s["rbl"])
    
    # API URL bauen
    url = f"https://www.wienerlinien.at/ogd_realtime/monitor?rbl={'&rbl='.join(map(str, all_rbls))}"
    
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        vehicles = []
        
        for mon in data.get("data", {}).get("monitors", []):
            slat = mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [0,0])[1]
            slon = mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [0,0])[0]
            
            for line in mon.get("lines", []):
                for dep in line.get("departures", {}).get("departure", []):
                    countdown = dep.get("departureTime", {}).get("countdown", 99)
                    
                    # HIER WAR DER FEHLER: Wir prüfen, ob countdown eine Zahl ist und filtern
                    if isinstance(countdown, int) and countdown > 30: 
                        continue
                    
                    vehicles.append({
                        "line": line.get("name"), "type": line.get("type"),
                        "dest": line.get("towards"), "time": countdown,
                        "features": dep.get("vehicle", {}),
                        "lat": slat, "lon": slon
                    })
        return vehicles
    except Exception as e:
        print(f"Fehler: {e}")
        return []

# Daten laden
vehicles = fetch_all_data()
# Sortieren, damit kleine Zahlen (baldige Ankunft) oben liegen
vehicles.sort(key=lambda x: x["time"] if isinstance(x["time"], int) else 99, reverse=True)

# --- 5. MAP RENDERING ---
m = folium.Map(location=[48.2080, 16.3700], zoom_start=13, tiles="CartoDB positron")

# A) LINIEN NETZ
for line, path in SMOOTH_ROUTES.items():
    color = LINE_COLORS.get(line, "#888")
    folium.PolyLine(path, color=color, weight=5, opacity=0.5, line_cap='round').add_to(m)

# B) STATIONEN (Haltestellen-Schild)
for s in STATION_MARKERS:
    html_sign = f"""
    <div class="station-sign">
        <div class="sign-stripe"></div>
        <div class="sign-logo"></div>
        <div class="sign-stripe"></div>
    </div>
    """
    folium.Marker(
        [s["lat"], s["lon"]],
        popup=f"<b>{s['name']}</b><br>Linien: {s['lines']}",
        icon=folium.DivIcon(html=html_sign, icon_size=(36,26), icon_anchor=(18,13))
    ).add_to(m)

# C) FAHRZEUGE (Pixel-Art CSS)
for v in vehicles:
    pos = [v["lat"], v["lon"]]
    rot = 0
    
    # Interpolation entlang der Route
    if v["line"] in SMOOTH_ROUTES and isinstance(v["time"], int) and v["time"] < 25:
        path = SMOOTH_ROUTES[v["line"]]
        idx = min(v["time"] * 3, len(path)-2) 
        idx = max(0, int(idx))
        pos = path[idx]
        rot = calculate_bearing(path[idx], path[idx+1])
    
    css_class = get_css_class(v["line"], v["type"], v["features"])
    line_col = LINE_COLORS.get(v["line"], "#333")
    
    # HTML für das Fahrzeug-Icon
    icon_html = f"""
    <div class="train-wrapper" style="transform: rotate({rot-90}deg);">
        <div class="train-body {css_class}" style="border-color: {line_col};">
            <div class="windows"></div>
            <div style="text-align:center; z-index:2; margin-top:-2px; color:inherit;">
                {v['line']}
            </div>
        </div>
    </div>
    """
    
    folium.Marker(
        pos, 
        popup=f"<b>{v['line']}</b> ➤ {v['dest']}<br>{v['time']} min",
        icon=folium.DivIcon(html=icon_html, icon_size=(44,20), icon_anchor=(22,10))
    ).add_to(m)

st_folium(m, width="100%", height=600, returned_objects=[])

# --- LISTE UNTEN ---
# Sortieren für Liste (Schnellste zuerst)
vehicles.sort(key=lambda x: x["time"] if isinstance(x["time"], int) else 99)

st.subheader("Aktuelle Verkehrslage")
cols = st.columns(3)

for i, v in enumerate(vehicles):
    col_idx = i % 3
    l_color = LINE_COLORS.get(v["line"], "#555")
    
    with cols[col_idx]:
        st.markdown(f"""
        <div style="border-top: 5px solid {l_color}; background:white; padding:10px; border-radius:4px; box-shadow:0 2px 4px #eee; margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between;">
                <b style="color:{l_color}; font-size:1.2em;">{v['line']}</b>
                <b>{v['time']} min</b>
            </div>
            <div style="font-size:0.9em; color:#666;">➜ {v['dest']}</div>
        </div>
        """, unsafe_allow_html=True)
