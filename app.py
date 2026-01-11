import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import math

# --- 1. SETUP ---
st.set_page_config(page_title="Wien Öffis V18", layout="wide", page_icon="🚋")

# GPS Modul Check
try:
    from streamlit_js_eval import get_geolocation
    HAS_GPS_MODULE = True
except ImportError:
    HAS_GPS_MODULE = False

st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BILDER & LOGOS ---

# Dein Stations-Logo
ICON_STATION_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAMCAIAAADtbgqsAAAAB3RJTUUH6gELByIjkfAdIgAAAoxJREFUeJxNzstrlGcYhvH7eQ8z3xwSJ4MxaWszJhiQduER3Fh0EWxr0ZIuohQhbVHU1iOIq2BQQjyQorVd1O5SaEUqQWuxbTAgSAOCqAhRkC4SjSaS4/jNTOY7vM/TRUH8cf0BF/i1IHAiXK74J3qnG1um8kun6gvTLe9PL26aqmmYXfdBdegWi7wZMTNE4BysdaNj5T0Hw8GbKp+HAGnPbt0S9P9i1q7O9PWqpnfF94mIjOViEdkscRjBGgDh9Rulw8fkxSTlc8QilSq981a6p6u06wAtqkUcY2EB1kApnpnRrcszF783sEaKxfKZvurZC5RIIJNmv0TWcmne1K0wq1YhlXTPx5WXEgBBIKVyoqM9+12famww8YOHlW8vRH/e0M3LnHCSAFJQytWlbcdnurlgt7fLwO8qnQGzOOcd2Jc8+DUAABSPP5cgkHRGEbTVEy/nQCTC2iYalheEWURe/jsGZgBQWhWWUjUQ4YVqRCwSAxYIgZMX/7h0fRgJA4JdCL/Z2bb/87au879dHrwrXhIswkwuZlBpzt/RvsFw7KzRzyamd3f3/33rPjLe/0colvqv/vPRppU/DtyenZpHyoNzsAbVAILj+7Yd/fJjo7W+MnRvT8/Psy9mka8FC5xLpj2kkpOvyvcePy1GjnI1pEhpFc/5rU0NP3R3bl7/HgATxHGhse7auf2ZjOdixyKLsqlHo5NHTl+amPf/Gh5xUYyEltCxX/mkbc1P3V+8XZ8Lo9gYTc6xUoQ3DN15dOjUryOjkyqdrMumZoplEGqVOrxzc9ferVapMHLWKADEzLFjEXHMWqkHT55t/OpsGLnaJTmO4sixlzAVv3K088OevZ+GUUwEozUAIvoPOtpWT2fW07IAAAAASUVORK5CYII="

# Dein V-Wagen Logo (Fahrzeug)
ICON_VEHICLE_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAICAIAAABh3dhzAAAAB3RJTUUH6gELByIbufKlvAAAAoZJREFUeJwFwUtvE1cUAOBz7p3ruWMPmdjjsT3EDxLCQ0iNBCFiB1WldtsdVTf9U0hdsWHbSuzYs4jEAgRIeZBA7VIbG8ePODN+zePOPf0+HF3ORqPR57PTvFXQBFprQEBERAQCQAACAMqINBESccYZY4igiYhIKXV+dp6lKQEgMm6w+lbDcTb2Dw4Mr7j557Nn8Xr9YP9gPB4N+gORE5yx1o1tpTUSASLjbDgYzMNAqcz1PM/z0jhmiDJfWC7n0XLBGOec1+v++dnnXpa9fPu22WoZQBRF6+cvXux8OA6G3677FadYGvzXnadUrNZ67Xblen29CLmKm82GzrLBxYCkE0dxvFrWGq2rYbfmbjpFNwzDMJiNx5c3b+1WSm670zYIQBjiUaV6z5JBxedC2ClVC7bghgFw13OlAZmdT0G6QsQAvu1YwiQptG0WDBZ5XsZApiph3HTLoZkvFWxCfXj42kDEOIl/efzkyf37neFwvVxJkUtUWnFLZi5nmqbKFDD2tdcFpTJNQua3fR8RkWGaJJMwmF3NpDC5ISxLrhYLpam2YY1AG+s42X+4//749A1jX5bzk6MjlaliqfTQK6dJNP3eRwacGcP+YL4IieBGq3U+z48mY8ZYza8mHI673cUqtCz71u5tIr3VaCylfPX3X2wyC3786ec/nj59tPfD6bv3mKhtf6t9fJIGQe3aRu/00/Tf3sU/HYsxf9Mt29e4ypplV0SREa33dnbD76N+p7Pt11eXl2cfP+zdvWNzfjWZ/Prb7/htONZaW5aU0pxOp47jbNqFr71+zsyVvLJEBAAAIAAFwAAIgAAEAABEmiYXF1mqWs16MF8sViuvWkmTVOYEAvwPrDxG5Tsp8voAAAAASUVORK5CYII="

# --- 3. DATEN: STATIONEN & RBLs ---
# Damit Busse/Bims erscheinen, müssen wir ihre Stationen abfragen.
# Ich habe die Liste erweitert.
STATION_MARKERS = [
    # U-BAHN KNOTEN
    {"name": "Schwedenplatz", "lat": 48.2114, "lon": 16.3783, "rbl": [4205, 4212, 4208, 4210]},
    {"name": "Karlsplatz", "lat": 48.2000, "lon": 16.3690, "rbl": [4202, 4216, 4617, 4214, 32, 40]}, # + Bim
    {"name": "Stephansplatz", "lat": 48.2082, "lon": 16.3738, "rbl": [4200, 4206]},
    {"name": "Westbahnhof", "lat": 48.1960, "lon": 16.3350, "rbl": [4920, 4921, 4600, 350, 354]}, # + Bim 5, 6, 18
    {"name": "Schottentor", "lat": 48.2150, "lon": 16.3610, "rbl": [4209, 4211, 4001, 4002]}, # + Bim D, 1, 71
    {"name": "Landstraße", "lat": 48.2060, "lon": 16.3850, "rbl": [4204, 4213]},
    {"name": "Praterstern", "lat": 48.2180, "lon": 16.3900, "rbl": [4207, 4105]},
    
    # BUS 13A STRECKE (Beispiele)
    {"name": "Neubaugasse (13A)", "lat": 48.1990, "lon": 16.3450, "rbl": [267, 266]},
    {"name": "Pilgramgasse (13A)", "lat": 48.1930, "lon": 16.3550, "rbl": [272, 273]},
    
    # BIM 43 STRECKE
    {"name": "Alser Straße (43)", "lat": 48.2170, "lon": 16.3420, "rbl": [4219, 4220, 100, 101]},
    
    # BIM D STRECKE
    {"name": "Hauptbahnhof (D)", "lat": 48.1850, "lon": 16.3750, "rbl": [150, 151]}
]

# Strecken für die grauen Linien (Nur zur Orientierung)
RAW_ROUTES = {
    "U1": [[48.1530, 16.3850], [48.1700, 16.3800], [48.1870, 16.3750], [48.2000, 16.3700], [48.2082, 16.3738], [48.2130, 16.3780], [48.2180, 16.3900], [48.2250, 16.4000], [48.2450, 16.4400], [48.2600, 16.4500]], 
    "U2": [[48.2200, 16.5100], [48.2150, 16.4500], [48.2180, 16.4200], [48.2180, 16.3900], [48.2150, 16.3610], [48.2100, 16.3570], [48.2070, 16.3580], [48.2000, 16.3690]], 
    "U3": [[48.2110, 16.3100], [48.1960, 16.3350], [48.1950, 16.3500], [48.2082, 16.3738], [48.2060, 16.3850], [48.1900, 16.4000], [48.1750, 16.4150]], 
    "U4": [[48.2050, 16.2500], [48.1900, 16.2900], [48.1850, 16.3200], [48.1900, 16.3500], [48.2000, 16.3690], [48.2082, 16.3738], [48.2114, 16.3783], [48.2166, 16.3730], [48.2250, 16.3600], [48.2400, 16.3600]], 
    "U6": [[48.1350, 16.3200], [48.1500, 16.3300], [48.1750, 16.3350], [48.1960, 16.3350], [48.2150, 16.3400], [48.2300, 16.3500], [48.2400, 16.3800], [48.2600, 16.4000]], 
    "13A": [[48.2020, 16.3380], [48.1990, 16.3450], [48.1960, 16.3550], [48.1930, 16.3600], [48.1850, 16.3650]]
}

LINE_COLORS = {
    "U1": "#E2021A", "U2": "#A365A4", "U3": "#F67F21", "U4": "#009641", "U6": "#9D6643",
    "S": "#00549F", "13A": "#E3001B", "D": "#E3001B", "43": "#E3001B", "1": "#E3001B"
}

# --- 4. FUNKTIONEN ---

def calculate_bearing(p1, p2):
    lat1, lat2 = math.radians(p1[0]), math.radians(p2[0])
    dLon = math.radians(p2[1] - p1[1])
    x = math.sin(dLon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dLon))
    return (math.degrees(math.atan2(x, y)) + 360) % 360

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# --- 5. APP LOGIK (GPS SCHALTER) ---

with st.sidebar:
    st.header("Modus")
    gps_mode = st.toggle("Echtstandort verwenden", value=False)
    
    # Standard: Stephansplatz
    user_lat, user_lon = 48.2082, 16.3738
    
    if gps_mode:
        st.write("📡 Suche GPS...")
        if HAS_GPS_MODULE:
            loc = get_geolocation()
            if loc:
                user_lat = loc['coords']['latitude']
                user_lon = loc['coords']['longitude']
                st.success(f"GPS: {user_lat:.4f}, {user_lon:.4f}")
            else:
                st.warning("Bitte Zugriff erlauben.")
        else:
            st.error("Plugin fehlt, nutze Regler.")
            user_lat = st.slider("Lat", 48.15, 48.25, 48.2082)
            user_lon = st.slider("Lon", 16.30, 16.45, 16.3738)
    else:
        st.write("🧪 Test-Modus (Stephansplatz)")

# --- 6. API DATEN LADEN ---

@st.cache_data(ttl=10)
def fetch_data():
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
                line_name = line.get("name")
                departures = line.get("departures", {}).get("departure", [])
                
                for i, dep in enumerate(departures):
                    if i >= 4: break 
                    countdown = dep.get("departureTime", {}).get("countdown", 99)
                    if isinstance(countdown, int) and countdown > 25: continue
                    
                    vehicle_info = dep.get("vehicle", {})
                    # Barrierefrei/Klapprampe = Klima
                    has_ac = vehicle_info.get("barrierFree", False) or vehicle_info.get("foldingRamp", False)
                    
                    # Versuche echte Koordinaten aus vehicle zu holen (Falls vorhanden, oft nicht öffentlich)
                    # Die API liefert oft keine echten Vehicle-Koordinaten im Monitor-Endpoint.
                    # Wir nutzen daher die Stop-Location als Basis.
                    
                    vehicles.append({
                        "line": line_name,
                        "dest": line.get("towards"), 
                        "time": countdown,
                        "lat": slat, "lon": slon, 
                        "ac": has_ac
                    })
        return vehicles
    except: return []

vehicles = fetch_data()
vehicles.sort(key=lambda x: x["time"] if isinstance(x["time"], int) else 99)

# --- 7. KARTE ZEICHNEN ---

m = folium.Map(location=[user_lat, user_lon], zoom_start=15, tiles="CartoDB positron")

# A) User Marker
folium.Marker(
    [user_lat, user_lon],
    tooltip="Du bist hier",
    icon=folium.Icon(color="blue", icon="user", prefix="fa"),
    z_index_offset=1100
).add_to(m)

# B) Routen
for line, path in RAW_ROUTES.items():
    color = LINE_COLORS.get(line, "#888")
    folium.PolyLine(path, color=color, weight=3, opacity=0.3).add_to(m)

# C) Fahrzeuge (Mit V-Wagen Logo!)
for v in vehicles:
    pos = [v["lat"], v["lon"]]
    rot = 0
    
    # 1. Position Logik: U-Bahnen auf Linie fixieren, Bims/Busse frei lassen (wegen Kurven)
    route_key = v["line"]
    
    # Nur U-Bahnen "snappen" wir auf die schöne Linie
    if "U" in route_key and route_key in RAW_ROUTES and isinstance(v["time"], int):
        # Einfache Interpolation entlang der Linie
        path = RAW_ROUTES[route_key]
        idx = min(v["time"] * 2, len(path)-2) # *2 Speed Faktor
        idx = max(0, int(idx))
        pos = path[idx]
        rot = calculate_bearing(path[idx], path[idx+1])
    else:
        # Bus/Bim/S-Bahn: Bleiben an der Haltestelle (oder leicht versetzt)
        # Da wir keine Live-GPS Koordinaten haben, simulieren wir Bewegung minimal
        rot = 0 # Keine Rotation wenn stehend
    
    # 2. Indikator Farbe (Klima)
    border_color = "#0066b3" if v["ac"] else "#d32f2f"
    
    # 3. HTML ICON
    # Bild + farbiger Balken darunter
    icon_html = f"""
    <div style="transform: rotate({rot}deg); display: flex; flex-direction: column; align-items: center;">
        <img src="{ICON_VEHICLE_B64}" style="width: 40px; height: 12px; display: block;">
        <div style="width: 40px; height: 4px; background: {border_color}; margin-top: 1px; border-radius: 2px;"></div>
        <div style="background: rgba(0,0,0,0.7); color: white; font-size: 9px; padding: 1px 3px; border-radius: 3px; margin-top: 2px;">
            {v['line']}
        </div>
    </div>
    """
    
    folium.Marker(
        pos, 
        popup=f"{v['line']} -> {v['dest']} ({v['time']} min)",
        icon=folium.DivIcon(html=icon_html, icon_size=(40,30), icon_anchor=(20,15))
    ).add_to(m)

# D) Stationen (Ganz oben)
for s in STATION_MARKERS:
    icon = folium.CustomIcon(ICON_STATION_B64, icon_size=(24, 14), icon_anchor=(12, 7))
    folium.Marker(
        [s["lat"], s["lon"]], 
        popup=s['name'], 
        icon=icon,
        z_index_offset=1000 # Top Layer
    ).add_to(m)

st_folium(m, width="100%", height=600, returned_objects=[])
