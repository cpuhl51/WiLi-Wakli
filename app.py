import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import math

# --- 1. SETUP ---
st.set_page_config(page_title="Wien Öffis V19", layout="wide", page_icon="🚋")

# Versuch, GPS Modul zu laden
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

# --- 2. BILDER ---
ICON_STATION_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAMCAIAAADtbgqsAAAAB3RJTUUH6gELByIjkfAdIgAAAoxJREFUeJxNzstrlGcYhvH7eQ8z3xwSJ4MxaWszJhiQduER3Fh0EWxr0ZIuohQhbVHU1iOIq2BQQjyQorVd1O5SaEUqQWuxbTAgSAOCqAhRkC4SjSaS4/jNTOY7vM/TRUH8cf0BF/i1IHAiXK74J3qnG1um8kun6gvTLe9PL26aqmmYXfdBdegWi7wZMTNE4BysdaNj5T0Hw8GbKp+HAGnPbt0S9P9i1q7O9PWqpnfF94mIjOViEdkscRjBGgDh9Rulw8fkxSTlc8QilSq981a6p6u06wAtqkUcY2EB1kApnpnRrcszF783sEaKxfKZvurZC5RIIJNmv0TWcmne1K0wq1YhlXTPx5WXEgBBIKVyoqM9+12famww8YOHlW8vRH/e0M3LnHCSAFJQytWlbcdnurlgt7fLwO8qnQGzOOcd2Jc8+DUAABSPP5cgkHRGEbTVEy/nQCTC2iYalheEWURe/jsGZgBQWhWWUjUQ4YVqRCwSAxYIgZMX/7h0fRgJA4JdCL/Z2bb/87au879dHrwrXhIswkwuZlBpzt/RvsFw7KzRzyamd3f3/33rPjLe/0colvqv/vPRppU/DtyenZpHyoNzsAbVAILj+7Yd/fJjo7W+MnRvT8/Psy9mka8FC5xLpj2kkpOvyvcePy1GjnI1pEhpFc/5rU0NP3R3bl7/HgATxHGhse7auf2ZjOdixyKLsqlHo5NHTl+amPf/Gh5xUYyEltCxX/mkbc1P3V+8XZ8Lo9gYTc6xUoQ3DN15dOjUryOjkyqdrMumZoplEGqVOrxzc9ferVapMHLWKADEzLFjEXHMWqkHT55t/OpsGLnaJTmO4sixlzAVv3K088OevZ+GUUwEozUAIvoPOtpWT2fW07IAAAAASUVORK5CYII="
ICON_VEHICLE_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAICAIAAABh3dhzAAAAB3RJTUUH6gELByIbufKlvAAAAoZJREFUeJwFwUtvE1cUAOBz7p3ruWMPmdjjsT3EDxLCQ0iNBCFiB1WldtsdVTf9U0hdsWHbSuzYs4jEAgRIeZBA7VIbG8ePODN+zePOPf0+HF3ORqPR57PTvFXQBFprQEBERAQCQAACAMqINBESccYZY4igiYhIKXV+dp6lKQEgMm6w+lbDcTb2Dw4Mr7j557Nn8Xr9YP9gPB4N+gORE5yx1o1tpTUSASLjbDgYzMNAqcz1PM/z0jhmiDJfWC7n0XLBGOec1+v++dnnXpa9fPu22WoZQBRF6+cvXux8OA6G3677FadYGvzXnadUrNZ67Xblen29CLmKm82GzrLBxYCkE0dxvFrWGq2rYbfmbjpFNwzDMJiNx5c3b+1WSm670zYIQBjiUaV6z5JBxedC2ClVC7bghgFw13OlAZmdT0G6QsQAvu1YwiQptG0WDBZ5XsZApiph3HTLoZkvFWxCfXj42kDEOIl/efzkyf37neFwvVxJkUtUWnFLZi5nmqbKFDD2tdcFpTJNQua3fR8RkWGaJJMwmF3NpDC5ISxLrhYLpam2YY1AG+s42X+4//749A1jX5bzk6MjlaliqfTQK6dJNP3eRwacGcP+YL4IieBGq3U+z48mY8ZYza8mHI673cUqtCz71u5tIr3VaCylfPX3X2wyC3786ec/nj59tPfD6bv3mKhtf6t9fJIGQe3aRu/00/Tf3sU/HYsxf9Mt29e4ypplV0SREa33dnbD76N+p7Pt11eXl2cfP+zdvWNzfjWZ/Prb7/htONZaW5aU0pxOp47jbNqFr71+zsyVvLJEBAAAIAAFwAAIgAAEAABEmiYXF1mqWs16MF8sViuvWkmTVOYEAvwPrDxG5Tsp8voAAAAASUVORK5CYII="

# --- 3. STATIONEN ---
STATION_MARKERS = [
    {"name": "Schwedenplatz", "lat": 48.2114, "lon": 16.3783, "rbl": [4205, 4212, 4208, 4210]},
    {"name": "Karlsplatz", "lat": 48.2000, "lon": 16.3690, "rbl": [4202, 4216, 4617, 4214, 32, 40]}, 
    {"name": "Stephansplatz", "lat": 48.2082, "lon": 16.3738, "rbl": [4200, 4206]},
    {"name": "Westbahnhof", "lat": 48.1960, "lon": 16.3350, "rbl": [4920, 4921, 4600, 350, 354]}, 
    {"name": "Schottentor", "lat": 48.2150, "lon": 16.3610, "rbl": [4209, 4211, 4001, 4002]}, 
    {"name": "Landstraße", "lat": 48.2060, "lon": 16.3850, "rbl": [4204, 4213]},
    {"name": "Praterstern", "lat": 48.2180, "lon": 16.3900, "rbl": [4207, 4105]},
    {"name": "Neubaugasse (13A)", "lat": 48.1990, "lon": 16.3450, "rbl": [267, 266]},
    {"name": "Pilgramgasse (13A)", "lat": 48.1930, "lon": 16.3550, "rbl": [272, 273]},
    {"name": "Alser Straße (43)", "lat": 48.2170, "lon": 16.3420, "rbl": [4219, 4220, 100, 101]},
    {"name": "Hauptbahnhof (D)", "lat": 48.1850, "lon": 16.3750, "rbl": [150, 151]}
]

# --- 4. ROUTEN (Detailliert für bessere Kurven-Animation) ---
RAW_ROUTES = {
    # U1 (Verläuft ca Nord-Süd)
    "U1": [[48.1530, 16.3850], [48.1700, 16.3800], [48.1870, 16.3750], [48.2000, 16.3700], [48.2082, 16.3738], [48.2130, 16.3780], [48.2180, 16.3900], [48.2250, 16.4000], [48.2450, 16.4400], [48.2600, 16.4500]], 
    # 13A (Kurvig durch Mariahilf)
    "13A": [[48.2020, 16.3380], [48.2005, 16.3420], [48.1990, 16.3450], [48.1970, 16.3490], [48.1960, 16.3550], [48.1945, 16.3580], [48.1930, 16.3600], [48.1850, 16.3650]], 
    # 43 (Vom Schottentor raus)
    "43": [[48.2150, 16.3610], [48.2160, 16.3550], [48.2165, 16.3500], [48.2170, 16.3420], [48.2180, 16.3350], [48.2200, 16.3300]],
    # D (Ring -> Hauptbahnhof)
    "D": [[48.2150, 16.3610], [48.2050, 16.3600], [48.2020, 16.3680], [48.2000, 16.3720], [48.1950, 16.3750], [48.1850, 16.3750]],
    # Standard U-Bahnen
    "U2": [[48.2200, 16.5100], [48.2150, 16.4500], [48.2180, 16.3900], [48.2100, 16.3570], [48.2070, 16.3580], [48.2000, 16.3690]], 
    "U3": [[48.2110, 16.3100], [48.1960, 16.3350], [48.2082, 16.3738], [48.2060, 16.3850], [48.1900, 16.4000]], 
    "U4": [[48.1900, 16.2900], [48.1900, 16.3500], [48.2000, 16.3690], [48.2082, 16.3738], [48.2114, 16.3783], [48.2166, 16.3730], [48.2250, 16.3600]], 
    "U6": [[48.1750, 16.3350], [48.1960, 16.3350], [48.2150, 16.3400], [48.2300, 16.3500]]
}

LINE_COLORS = {
    "U1": "#E2021A", "U2": "#A365A4", "U3": "#F67F21", "U4": "#009641", "U6": "#9D6643",
    "S": "#00549F", "13A": "#E3001B", "D": "#E3001B", "43": "#E3001B", "1": "#E3001B"
}

# --- 5. MATHEMATIK ---

def smooth_path(points):
    """Macht die Pfade geschmeidiger für bessere Rotation"""
    if len(points) < 2: return points
    smoothed = []
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i+1]
        steps = 8 # Mehr Steps für weichere Kurven
        for j in range(steps):
            f = j / steps
            smoothed.append([p1[0]*(1-f)+p2[0]*f, p1[1]*(1-f)+p2[1]*f])
    smoothed.append(points[-1])
    return smoothed

# Wir smoothen ALLE Routen, damit wir viele Punkte zum "Einrasten" haben
SMOOTH_ROUTES = {k: smooth_path(v) for k,v in RAW_ROUTES.items()}

def calculate_bearing(p1, p2):
    """Berechnet den Winkel zwischen zwei Koordinaten (0-360 Grad)"""
    if not p1 or not p2: return 0
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

# --- 6. POSITION & ROTATION BERECHNEN ---

def get_vehicle_position_and_rotation(line_name, minutes_away):
    """
    Simuliert, wo das Fahrzeug auf der Linie ist, basierend auf der Zeit.
    Gibt (lat, lon, rotation) zurück.
    """
    # 1. Route finden (Fallback auf U1 wenn Linie unbekannt)
    route_key = line_name
    if route_key not in SMOOTH_ROUTES:
        if "U" in route_key: route_key = "U1" # Fallback
        elif "A" in route_key: route_key = "13A"
        elif len(route_key) <= 2: route_key = "D" # Bim Fallback
        else: return None, None, 0

    path = SMOOTH_ROUTES.get(route_key, [])
    if len(path) < 2: return None, None, 0

    # 2. Index auf der Linie berechnen
    # Wir nehmen an: 0 min = Ende der Linie (Ziel), 20 min = Anfang der Linie
    # Das ist vereinfacht, aber visuell effektiv.
    
    # Mapping: Je mehr Minuten, desto weiter "hinten" im Array (oder vorne, je nach Definition)
    # Wir nutzen hier einfach einen Index-Faktor.
    # Speed Faktor: Wie schnell bewegt es sich durch unser Array?
    speed_factor = 2.5 
    
    # Wir starten in der Mitte und bewegen uns
    start_index = len(path) - 2 # Am Ende (nahe Station)
    current_index = start_index - int(minutes_away * speed_factor)
    
    # Bounds check
    current_index = max(0, min(current_index, len(path)-2))
    
    p1 = path[current_index]
    p2 = path[current_index + 1] # Nächster Punkt für Rotation
    
    # Rotation berechnen
    rotation = calculate_bearing(p1, p2)
    
    return p1[0], p1[1], rotation


# --- 7. APP UI & DATEN ---

with st.sidebar:
    st.header("Einstellungen")
    gps_mode = st.toggle("Echtstandort (GPS)", value=False)
    user_lat, user_lon = 48.2082, 16.3738
    
    if gps_mode and HAS_GPS_MODULE:
        loc = get_geolocation()
        if loc:
            user_lat, user_lon = loc['coords']['latitude'], loc['coords']['longitude']
            st.success("GPS Aktiv")
    elif gps_mode:
        st.error("GPS Modul fehlt.")
    else:
        st.write("Modus: Stephansplatz (Demo)")

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
            for line in mon.get("lines", []):
                line_name = line.get("name")
                for i, dep in enumerate(line.get("departures", {}).get("departure", [])):
                    if i >= 3: break 
                    countdown = dep.get("departureTime", {}).get("countdown", 99)
                    if isinstance(countdown, int) and countdown < 30:
                        vh = dep.get("vehicle", {})
                        ac = vh.get("barrierFree", False) or vh.get("foldingRamp", False)
                        vehicles.append({"line": line_name, "dest": line.get("towards"), "time": countdown, "ac": ac})
        return vehicles
    except: return []

vehicles = fetch_data()
vehicles.sort(key=lambda x: x["time"])

# --- 8. KARTE GENERIEREN ---

m = folium.Map(location=[user_lat, user_lon], zoom_start=15, tiles="CartoDB positron")

folium.Marker([user_lat, user_lon], icon=folium.Icon(color="blue", icon="user", prefix="fa"), z_index_offset=1100).add_to(m)

# Routen zeichnen
for line, path in SMOOTH_ROUTES.items():
    color = LINE_COLORS.get(line, "#888")
    folium.PolyLine(path, color=color, weight=3, opacity=0.4).add_to(m)

# Stationen zeichnen (Oben)
for s in STATION_MARKERS:
    icon = folium.CustomIcon(ICON_STATION_B64, icon_size=(24, 14), icon_anchor=(12, 7))
    folium.Marker([s["lat"], s["lon"]], popup=s['name'], icon=icon, z_index_offset=1000).add_to(m)

# Fahrzeuge zeichnen (Mit Rotation!)
for v in vehicles:
    # HIER PASSIERT DIE MAGIE:
    lat, lon, rot = get_vehicle_position_and_rotation(v["line"], v["time"])
    
    if lat and lon:
        border_color = "#0066b3" if v["ac"] else "#d32f2f"
        
        # Korrektur der Rotation: Das Icon zeigt standardmäßig nach RECHTS (90 Grad).
        # Wenn Bearing 0 (Nord) ist, muss das Bild -90 Grad gedreht werden.
        # Wenn Bearing 90 (Ost) ist, muss das Bild 0 Grad gedreht werden.
        display_rot = rot - 90
        
        icon_html = f"""
        <div style="
            transform: rotate({display_rot}deg); 
            transform-origin: center center; 
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            width: 40px; height: 40px;
        ">
            <img src="{ICON_VEHICLE_B64}" style="width: 40px; height: 12px; display: block;">
            <div style="width: 36px; height: 3px; background: {border_color}; margin-top: 1px; border-radius: 2px;"></div>
            <div style="
                transform: rotate({-display_rot}deg); /* Text wieder gerade drehen */
                background: rgba(255,255,255,0.8); color: black; font-weight: bold; 
                font-size: 10px; padding: 0px 4px; border-radius: 4px; margin-top: 4px;
                border: 1px solid #ccc;
            ">
                {v['line']}
            </div>
        </div>
        """
        
        folium.Marker(
            [lat, lon],
            popup=f"{v['line']} ({v['time']}m)",
            icon=folium.DivIcon(html=icon_html, icon_size=(40,40), icon_anchor=(20,20))
        ).add_to(m)

st_folium(m, width="100%", height=600, returned_objects=[])
