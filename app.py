import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import math

# --- 1. SETUP & CSS (Performance-Optimiert) ---
st.set_page_config(page_title="Wien Öffis Light", layout="wide", page_icon="🚋")

st.markdown("""
    <style>
    .block-container { padding-top: 0rem; }
    
    /* Simples Viereck für Fahrzeuge */
    .veh-box {
        width: 32px;
        height: 22px;
        border-radius: 4px;
        border: 2px solid white;
        box-shadow: 2px 2px 4px rgba(0,0,0,0.4);
        display: flex;
        justify-content: center;
        align-items: center;
        font-family: sans-serif;
        font-weight: bold;
        font-size: 11px;
        color: white;
        z-index: 1000;
    }

    /* Haltestellen Punkt (klein und performant) */
    .station-dot {
        width: 14px; height: 14px;
        background-color: white;
        border: 3px solid #333;
        border-radius: 50%;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🇦🇹 Wiener Linien (Performance Mode)")

# --- 2. DATEN: ROUTEN & FARBEN ---

LINE_COLORS = {
    "U1": "#E2021A", "U2": "#A365A4", "U3": "#F67F21", 
    "U4": "#009641", "U5": "#F67F21", "U6": "#9D6643", 
    "1": "#FF5C5C", "2": "#FF5C5C", "D": "#FF5C5C", "71": "#FF5C5C",
    "S": "#00549F", "WLB": "#00549F"
}

# Grobe Routenverläufe (Damit die Fahrzeuge nicht in der Luft schweben)
RAW_ROUTES = {
    "U1": [[48.1530, 16.3850], [48.1700, 16.3800], [48.1870, 16.3750], [48.2000, 16.3700], [48.2082, 16.3738], [48.2130, 16.3780], [48.2180, 16.3900], [48.2250, 16.4000], [48.2450, 16.4400], [48.2600, 16.4500]], 
    "U2": [[48.2200, 16.5100], [48.2150, 16.4500], [48.2180, 16.4200], [48.2180, 16.3900], [48.2150, 16.3610], [48.2100, 16.3570], [48.2070, 16.3580], [48.2000, 16.3690]], 
    "U3": [[48.2110, 16.3100], [48.1960, 16.3350], [48.1950, 16.3500], [48.2082, 16.3738], [48.2060, 16.3850], [48.1900, 16.4000], [48.1750, 16.4150]], 
    "U4": [[48.2050, 16.2500], [48.1900, 16.2900], [48.1850, 16.3200], [48.1900, 16.3500], [48.2000, 16.3690], [48.2082, 16.3738], [48.2114, 16.3783], [48.2166, 16.3730], [48.2250, 16.3600], [48.2400, 16.3600]], 
    "U6": [[48.1350, 16.3200], [48.1500, 16.3300], [48.1750, 16.3350], [48.1960, 16.3350], [48.2150, 16.3400], [48.2300, 16.3500], [48.2400, 16.3800], [48.2600, 16.4000]], 
    "1": [[48.2114, 16.3783], [48.2166, 16.3730], [48.2150, 16.3650], [48.2110, 16.3600], [48.2050, 16.3600], [48.2020, 16.3680], [48.2030, 16.3750], [48.2050, 16.3850], [48.2100, 16.3950]],
    "D": [[48.2600, 16.3650], [48.2350, 16.3600], [48.2166, 16.3730], [48.2150, 16.3650], [48.2050, 16.3600], [48.1900, 16.3800]],
    "2": [[48.2114, 16.3783], [48.2110, 16.3600], [48.2080, 16.3500], [48.2100, 16.3400]],
    "71": [[48.2160, 16.3690], [48.2050, 16.3600], [48.2020, 16.3680], [48.1950, 16.3900], [48.1800, 16.4100], [48.1600, 16.4400]]
}

STATION_MARKERS = [
    {"name": "Schwedenplatz", "lat": 48.2114, "lon": 16.3783, "lines": "U1, U4, 1, 2", "rbl": [4205, 4212, 4208, 4210]},
    {"name": "Karlsplatz", "lat": 48.2000, "lon": 16.3690, "lines": "U1, U2, U4, WLB", "rbl": [4202, 4216, 4617, 4214]},
    {"name": "Stephansplatz", "lat": 48.2082, "lon": 16.3738, "lines": "U1, U3", "rbl": [4200, 4206]},
    {"name": "Westbahnhof", "lat": 48.1960, "lon": 16.3350, "lines": "U3, U6, 5, 6, 18", "rbl": [4920, 4921, 4600]},
    {"name": "Schottentor", "lat": 48.2150, "lon": 16.3610, "lines": "U2, D, 1, 71", "rbl": [4209, 4211]},
    {"name": "Landstraße", "lat": 48.2060, "lon": 16.3850, "lines": "U3, U4, O", "rbl": [4204, 4213]},
    {"name": "Praterstern", "lat": 48.2180, "lon": 16.3900, "lines": "U1, U2, 5, O", "rbl": [4207, 4105]}
]

# --- 3. HELFER ---

def smooth_path(points):
    """Macht die Linien etwas runder"""
    if len(points) < 2: return points
    smoothed = []
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i+1]
        steps = 5 
        for j in range(steps):
            f = j / steps
            smoothed.append([p1[0]*(1-f)+p2[0]*f, p1[1]*(1-f)+p2[1]*f])
    smoothed.append(points[-1])
    return smoothed

SMOOTH_ROUTES = {k: smooth_path(v) for k,v in RAW_ROUTES.items()}

def calculate_bearing(p1, p2):
    lat1, lat2 = math.radians(p1[0]), math.radians(p2[0])
    dLon = math.radians(p2[1] - p1[1])
    x = math.sin(dLon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dLon))
    return (math.degrees(math.atan2(x, y)) + 360) % 360

@st.cache_data(ttl=15)
def fetch_all_data():
    all_rbls = []
    for s in STATION_MARKERS: all_rbls.extend(s["rbl"])
    
    url = f"https://www.wienerlinien.at/ogd_realtime/monitor?rbl={'&rbl='.join(map(str, all_rbls))}"
    
    try:
        response = requests.get(url, timeout=4)
        data = response.json()
        vehicles = []
        
        for mon in data.get("data", {}).get("monitors", []):
            slat = mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [0,0])[1]
            slon = mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [0,0])[0]
            
            for line in mon.get("lines", []):
                # HIER: LIMIT AUF 4 FAHRZEUGE pro Linie/Richtung
                departures = line.get("departures", {}).get("departure", [])
                
                for i, dep in enumerate(departures):
                    if i >= 4: break # Limit 4!
                    
                    countdown = dep.get("departureTime", {}).get("countdown", 99)
                    if isinstance(countdown, int) and countdown > 30: continue
                    
                    vehicles.append({
                        "line": line.get("name"), 
                        "dest": line.get("towards"), 
                        "time": countdown,
                        "lat": slat, "lon": slon
                    })
        return vehicles
    except: return []

vehicles = fetch_all_data()
# Sortieren
vehicles.sort(key=lambda x: x["time"] if isinstance(x["time"], int) else 99)

# --- 4. KARTE ZEICHNEN ---

m = folium.Map(location=[48.2080, 16.3700], zoom_start=13, tiles="CartoDB positron")

# A) LINIEN (Hintergrund)
for line, path in SMOOTH_ROUTES.items():
    color = LINE_COLORS.get(line, "#888")
    folium.PolyLine(path, color=color, weight=3, opacity=0.4).add_to(m)

# B) STATIONEN (Einfache Punkte)
for s in STATION_MARKERS:
    html_dot = f"""<div class="station-dot"></div>"""
    folium.Marker(
        [s["lat"], s["lon"]], 
        popup=s['name'],
        icon=folium.DivIcon(html=html_dot, icon_size=(14,14), icon_anchor=(7,7))
    ).add_to(m)

# C) FAHRZEUGE (Vierecke mit Text)
for v in vehicles:
    pos = [v["lat"], v["lon"]]
    
    # Position auf Route berechnen
    if v["line"] in SMOOTH_ROUTES and isinstance(v["time"], int) and v["time"] < 25:
        path = SMOOTH_ROUTES[v["line"]]
        idx = min(v["time"] * 3, len(path)-2) 
        idx = max(0, int(idx))
        pos = path[idx]
        # Rotation lassen wir weg für bessere Lesbarkeit des Textes
    
    line_color = LINE_COLORS.get(v["line"], "#555")
    
    # HTML: Einfaches Viereck, Farbe der Linie
    icon_html = f"""
    <div class="veh-box" style="background-color: {line_color};">
        {v['line']}
    </div>
    """
    
    folium.Marker(
        pos, 
        popup=f"<b>{v['line']}</b> ➤ {v['dest']}<br>{v['time']} min",
        icon=folium.DivIcon(html=icon_html, icon_size=(32,22), icon_anchor=(16,11))
    ).add_to(m)

st_folium(m, width="100%", height=550, returned_objects=[])

# --- 5. INFO LISTE (Kompakt) ---
st.subheader("Nächste Abfahrten (Max 4 pro Linie)")
cols = st.columns(3)

# Wir zeigen nur die ersten 12 Fahrzeuge insgesamt an, um die Liste kurz zu halten
# oder du nimmst 'vehicles' komplett, da wir oben schon gefiltert haben.
for i, v in enumerate(vehicles):
    with cols[i % 3]:
        clr = LINE_COLORS.get(v["line"], "#555")
        st.markdown(f"**<span style='color:{clr}'>{v['line']}</span>** ➜ {v['dest']} ({v['time']} min)", unsafe_allow_html=True)

