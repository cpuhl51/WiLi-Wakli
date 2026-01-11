import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import math

# --- 1. SETUP & CSS ---
st.set_page_config(page_title="Wien Öffis V17", layout="wide", page_icon="🚋")

# Versuch, GPS Modul zu laden (für Echtstandort)
try:
    from streamlit_js_eval import get_geolocation
    HAS_GPS_MODULE = True
except ImportError:
    HAS_GPS_MODULE = False

st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    
    /* FAHRZEUG BOX */
    .veh-box {
        width: 44px;
        height: 24px;
        border: 1px solid white;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: sans-serif;
        font-weight: bold;
        font-size: 11px;
        color: white;
        border-radius: 3px;
        padding-right: 10px; /* Platz für den Streifen rechts */
        
        /* HINTERGRUND-BILD FÜR DEN STRICH (Rechts fixiert) */
        background-repeat: no-repeat;
        background-position: right top;
        background-size: 10px 100%; 
    }

    /* KLIMATISIERT (Blau/Weiß) */
    .ac-yes-bg {
        background-image: repeating-linear-gradient(
            -45deg,
            #0066b3,
            #0066b3 3px,
            #ffffff 3px,
            #ffffff 6px
        );
    }

    /* NICHT KLIMATISIERT (Rot/Weiß) */
    .ac-no-bg {
        background-image: repeating-linear-gradient(
            -45deg,
            #d32f2f,
            #d32f2f 3px,
            #ffffff 3px,
            #ffffff 6px
        );
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO & FARBEN ---

ICON_STATION_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAMCAIAAADtbgqsAAAAB3RJTUUH6gELByIjkfAdIgAAAoxJREFUeJxNzstrlGcYhvH7eQ8z3xwSJ4MxaWszJhiQduER3Fh0EWxr0ZIuohQhbVHU1iOIq2BQQjyQorVd1O5SaEUqQWuxbTAgSAOCqAhRkC4SjSaS4/jNTOY7vM/TRUH8cf0BF/i1IHAiXK74J3qnG1um8kun6gvTLe9PL26aqmmYXfdBdegWi7wZMTNE4BysdaNj5T0Hw8GbKp+HAGnPbt0S9P9i1q7O9PWqpnfF94mIjOViEdkscRjBGgDh9Rulw8fkxSTlc8QilSq981a6p6u06wAtqkUcY2EB1kApnpnRrcszF783sEaKxfKZvurZC5RIIJNmv0TWcmne1K0wq1YhlXTPx5WXEgBBIKVyoqM9+12famww8YOHlW8vRH/e0M3LnHCSAFJQytWlbcdnurlgt7fLwO8qnQGzOOcd2Jc8+DUAABSPP5cgkHRGEbTVEy/nQCTC2iYalheEWURe/jsGZgBQWhWWUjUQ4YVqRCwSAxYIgZMX/7h0fRgJA4JdCL/Z2bb/87au879dHrwrXhIswkwuZlBpzt/RvsFw7KzRzyamd3f3/33rPjLe/0colvqv/vPRppU/DtyenZpHyoNzsAbVAILj+7Yd/fJjo7W+MnRvT8/Psy9mka8FC5xLpj2kkpOvyvcePy1GjnI1pEhpFc/5rU0NP3R3bl7/HgATxHGhse7auf2ZjOdixyKLsqlHo5NHTl+amPf/Gh5xUYyEltCxX/mkbc1P3V+8XZ8Lo9gYTc6xUoQ3DN15dOjUryOjkyqdrMumZoplEGqVOrxzc9ferVapMHLWKADEzLFjEXHMWqkHT55t/OpsGLnaJTmO4sixlzAVv3K088OevZ+GUUwEozUAIvoPOtpWT2fW07IAAAAASUVORK5CYII="

LINE_COLORS = {
    "U1": "#E2021A", "U2": "#A365A4", "U3": "#F67F21", "U4": "#009641", "U5": "#F67F21", "U6": "#9D6643", 
    "1": "#FF5C5C", "2": "#FF5C5C", "D": "#FF5C5C", "71": "#FF5C5C", "O": "#FF5C5C", "5": "#FF5C5C", "6": "#FF5C5C", "18": "#FF5C5C", "43": "#FF5C5C",
    "S": "#00549F", "S45": "#00549F", "S50": "#00549F", 
    "13A": "#E3001B", "40A": "#E3001B", "59A": "#E3001B", "57A": "#E3001B"
}

# Routen (Vereinfacht für Darstellung)
RAW_ROUTES = {
    "U1": [[48.1530, 16.3850], [48.1700, 16.3800], [48.1870, 16.3750], [48.2000, 16.3700], [48.2082, 16.3738], [48.2130, 16.3780], [48.2180, 16.3900], [48.2250, 16.4000], [48.2450, 16.4400], [48.2600, 16.4500]], 
    "U2": [[48.2200, 16.5100], [48.2150, 16.4500], [48.2180, 16.4200], [48.2180, 16.3900], [48.2150, 16.3610], [48.2100, 16.3570], [48.2070, 16.3580], [48.2000, 16.3690]], 
    "U3": [[48.2110, 16.3100], [48.1960, 16.3350], [48.1950, 16.3500], [48.2082, 16.3738], [48.2060, 16.3850], [48.1900, 16.4000], [48.1750, 16.4150]], 
    "U4": [[48.2050, 16.2500], [48.1900, 16.2900], [48.1850, 16.3200], [48.1900, 16.3500], [48.2000, 16.3690], [48.2082, 16.3738], [48.2114, 16.3783], [48.2166, 16.3730], [48.2250, 16.3600], [48.2400, 16.3600]], 
    "U6": [[48.1350, 16.3200], [48.1500, 16.3300], [48.1750, 16.3350], [48.1960, 16.3350], [48.2150, 16.3400], [48.2300, 16.3500], [48.2400, 16.3800], [48.2600, 16.4000]], 
    "1": [[48.2114, 16.3783], [48.2166, 16.3730], [48.2150, 16.3650], [48.2110, 16.3600], [48.2050, 16.3600], [48.2020, 16.3680], [48.2030, 16.3750], [48.2050, 16.3850], [48.2100, 16.3950]],
    "2": [[48.2250, 16.3800], [48.2114, 16.3783], [48.2080, 16.3700], [48.2050, 16.3600], [48.2080, 16.3500], [48.2100, 16.3400], [48.2200, 16.3300]],
    "D": [[48.2600, 16.3650], [48.2350, 16.3600], [48.2166, 16.3730], [48.2150, 16.3650], [48.2050, 16.3600], [48.1900, 16.3800], [48.1830, 16.3800]],
    "13A": [[48.2020, 16.3380], [48.1990, 16.3450], [48.1960, 16.3550], [48.1930, 16.3600], [48.1850, 16.3650]], 
    "S": [[48.2600, 16.4000], [48.2400, 16.3800], [48.2180, 16.3900], [48.2060, 16.3850], [48.1850, 16.3800], [48.1700, 16.3700], [48.1500, 16.3200]] 
}

# INTERNE STATIONSLISTE (Erweitert um Bim/Bus Beispiele)
# Dies verhindert den KeyError, da wir kein CSV laden.
STATION_MARKERS = [
    {"name": "Schwedenplatz", "lat": 48.2114, "lon": 16.3783, "rbl": [4205, 4212, 4208, 4210]},
    {"name": "Karlsplatz (U)", "lat": 48.2000, "lon": 16.3690, "rbl": [4202, 4216, 4617, 4214]},
    {"name": "Stephansplatz", "lat": 48.2082, "lon": 16.3738, "rbl": [4200, 4206]},
    {"name": "Westbahnhof", "lat": 48.1960, "lon": 16.3350, "rbl": [4920, 4921, 4600]},
    {"name": "Schottentor", "lat": 48.2150, "lon": 16.3610, "rbl": [4209, 4211]}, # Bim 1, D, 71
    {"name": "Landstraße", "lat": 48.2060, "lon": 16.3850, "rbl": [4204, 4213]},
    {"name": "Praterstern", "lat": 48.2180, "lon": 16.3900, "rbl": [4207, 4105]},
    # BUS & BIM BEISPIELE
    {"name": "Neubaugasse (13A)", "lat": 48.1990, "lon": 16.3450, "rbl": [267, 266]}, 
    {"name": "Oper/Karlsplatz (Bim)", "lat": 48.2020, "lon": 16.3690, "rbl": [32, 40]}, # D, 1, 2, 71
    {"name": "Alser Straße (43/U6)", "lat": 48.2170, "lon": 16.3420, "rbl": [4219, 4220]} 
]

# --- 3. HELFER ---

def smooth_path(points):
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

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# --- 4. SIDEBAR: GPS ---

with st.sidebar:
    st.header("Einstellungen")
    gps_mode = st.toggle("Echtstandort (GPS)", value=False)
    
    # Default: Simuliert
    user_lat, user_lon = 48.2090, 16.3720 
    
    if gps_mode:
        st.write("📡 Suche GPS...")
        if HAS_GPS_MODULE:
            loc = get_geolocation()
            if loc:
                user_lat = loc['coords']['latitude']
                user_lon = loc['coords']['longitude']
                st.success(f"Pos: {user_lat:.4f}, {user_lon:.4f}")
            else:
                st.warning("Bitte Browser-Zugriff erlauben.")
        else:
            st.error("Plugin 'streamlit-js-eval' fehlt.")
            user_lat = st.slider("Lat", 48.15, 48.25, 48.2082)
            user_lon = st.slider("Lon", 16.30, 16.45, 16.3738)
    else:
        st.write("🧪 Test-Modus (Fixe Pos.)")

# --- 5. LOGIK ---

closest_station = None
min_dist = 999999
stations_with_dist = []

# Berechne Distanz zu allen bekannten Stationen
for s in STATION_MARKERS:
    dist = haversine(user_lat, user_lon, s["lat"], s["lon"])
    stations_with_dist.append({**s, "dist": dist})
    if dist < min_dist:
        min_dist = dist
        closest_station = s

stations_with_dist.sort(key=lambda x: x["dist"])

# Info-Header
if min_dist < 100:
    st.success(f"📍 **Du befindest Dich in der Station {closest_station['name']}**")
else:
    st.info(f"🚶 Nächste Station: **{closest_station['name']}** ({int(min_dist)}m)")
    
    # Zeige die 3 nächsten Stationen an
    near_str = " | ".join([f"{s['name']} ({int(s['dist'])}m)" for s in stations_with_dist[:3]])
    st.caption(f"In der Nähe: {near_str}")

# --- 6. API ABFRAGE (Nur nahe RBLs oder Alle?) ---
# Um API-Limits zu sparen und Performance zu halten, fragen wir hier
# die 7 nächsten Stationen ab (oder alle, wenn die Liste kurz ist).
rbls_to_fetch = []
for s in stations_with_dist[:7]: # Top 7 nächste Stationen
    rbls_to_fetch.extend(s["rbl"])

@st.cache_data(ttl=10)
def fetch_live_data(rbl_list):
    if not rbl_list: return []
    # RBL Liste in String umwandeln für URL
    rbl_str = "&rbl=".join(map(str, rbl_list))
    url = f"https://www.wienerlinien.at/ogd_realtime/monitor?rbl={rbl_str}"
    
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
                    if isinstance(countdown, int) and countdown > 20: continue # Radius Filter
                    
                    vehicle_info = dep.get("vehicle", {})
                    # Klapprampe/Barrierefrei als Klima-Indikator
                    has_ac = vehicle_info.get("barrierFree", False) or vehicle_info.get("foldingRamp", False)
                    
                    vehicles.append({
                        "line": line_name,
                        "dest": line.get("towards"), 
                        "time": countdown,
                        "lat": slat, "lon": slon,
                        "ac": has_ac
                    })
        return vehicles
    except: return []

vehicles = fetch_live_data(rbls_to_fetch)
vehicles.sort(key=lambda x: x["time"] if isinstance(x["time"], int) else 99)

# --- 7. KARTE ---
m = folium.Map(location=[user_lat, user_lon], zoom_start=15, tiles="CartoDB positron")

# A) User
folium.Marker(
    [user_lat, user_lon],
    tooltip="Deine Position",
    icon=folium.Icon(color="blue", icon="user", prefix="fa"),
    z_index_offset=1100
).add_to(m)

# B) Linien (Hintergrund)
for line, path in SMOOTH_ROUTES.items():
    color = LINE_COLORS.get(line, "#888")
    if "S" in line: color = LINE_COLORS["S"]
    folium.PolyLine(path, color=color, weight=4, opacity=0.4).add_to(m)

# C) Fahrzeuge
for v in vehicles:
    pos = [v["lat"], v["lon"]]
    rot = 0
    
    # Routing-Logik (Optional, verbessert Optik)
    route_key = v["line"]
    if "S" in route_key and "45" not in route_key and "50" not in route_key: route_key = "S"
    
    if route_key in SMOOTH_ROUTES and isinstance(v["time"], int):
        path = SMOOTH_ROUTES[route_key]
        idx = min(v["time"] * 3, len(path)-2) 
        idx = max(0, int(idx))
        pos = path[idx]
        rot = calculate_bearing(path[idx], path[idx+1])
    
    # Farbe
    l_color = LINE_COLORS.get(v["line"], "#555")
    if "S" in v["line"]: l_color = LINE_COLORS["S"]
    if "A" in v["line"]: l_color = LINE_COLORS["13A"]

    bg_class = "ac-yes-bg" if v["ac"] else "ac-no-bg"
    
    icon_html = f"""
    <div style="transform: rotate({rot-90}deg);">
        <div class="veh-box {bg_class}" style="background-color: {l_color};">
            {v['line']}
        </div>
    </div>
    """
    
    folium.Marker(
        pos, 
        popup=f"{v['line']} -> {v['dest']} ({v['time']}m)",
        icon=folium.DivIcon(html=icon_html, icon_size=(44,24), icon_anchor=(22,12))
    ).add_to(m)

# D) Stationen (OBEN AUF)
# Wir zeichnen nur die relevanten Stationen in der Nähe ein, um die Karte nicht zu fluten
for s in stations_with_dist[:10]: 
    icon = folium.CustomIcon(ICON_STATION_B64, icon_size=(20, 12), icon_anchor=(10, 6))
    folium.Marker(
        [s["lat"], s["lon"]], 
        popup=s['name'], 
        icon=icon,
        z_index_offset=1000 # Immer im Vordergrund
    ).add_to(m)

st_folium(m, width="100%", height=600, returned_objects=[])
