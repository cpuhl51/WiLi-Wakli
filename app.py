import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import math
import pandas as pd
import io

# --- 1. SETUP & CSS ---
st.set_page_config(page_title="Wien Öffis V17 (Smart GPS)", layout="wide", page_icon="🚋")

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
        width: 44px; height: 24px;
        border: 1px solid white;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.6);
        display: flex; align-items: center; justify-content: center;
        font-family: sans-serif; font-weight: bold; font-size: 11px;
        color: white; border-radius: 3px; padding-right: 10px;
        background-repeat: no-repeat; background-position: right top; background-size: 10px 100%; 
    }
    .ac-yes-bg { background-image: repeating-linear-gradient(-45deg, #0066b3, #0066b3 3px, #ffffff 3px, #ffffff 6px); }
    .ac-no-bg { background-image: repeating-linear-gradient(-45deg, #d32f2f, #d32f2f 3px, #ffffff 3px, #ffffff 6px); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATEN & LOGOS ---

ICON_STATION_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAMCAIAAADtbgqsAAAAB3RJTUUH6gELByIjkfAdIgAAAoxJREFUeJxNzstrlGcYhvH7eQ8z3xwSJ4MxaWszJhiQduER3Fh0EWxr0ZIuohQhbVHU1iOIq2BQQjyQorVd1O5SaEUqQWuxbTAgSAOCqAhRkC4SjSaS4/jNTOY7vM/TRUH8cf0BF/i1IHAiXK74J3qnG1um8kun6gvTLe9PL26aqmmYXfdBdegWi7wZMTNE4BysdaNj5T0Hw8GbKp+HAGnPbt0S9P9i1q7O9PWqpnfF94mIjOViEdkscRjBGgDh9Rulw8fkxSTlc8QilSq981a6p6u06wAtqkUcY2EB1kApnpnRrcszF783sEaKxfKZvurZC5RIIJNmv0TWcmne1K0wq1YhlXTPx5WXEgBBIKVyoqM9+12famww8YOHlW8vRH/e0M3LnHCSAFJQytWlbcdnurlgt7fLwO8qnQGzOOcd2Jc8+DUAABSPP5cgkHRGEbTVEy/nQCTC2iYalheEWURe/jsGZgBQWhWWUjUQ4YVqRCwSAxYIgZMX/7h0fRgJA4JdCL/Z2bb/87au879dHrwrXhIswkwuZlBpzt/RvsFw7KzRzyamd3f3/33rPjLe/0colvqv/vPRppU/DtyenZpHyoNzsAbVAILj+7Yd/fJjo7W+MnRvT8/Psy9mka8FC5xLpj2kkpOvyvcePy1GjnI1pEhpFc/5rU0NP3R3bl7/HgATxHGhse7auf2ZjOdixyKLsqlHo5NHTl+amPf/Gh5xUYyEltCxX/mkbc1P3V+8XZ8Lo9gYTc6xUoQ3DN15dOjUryOjkyqdrMumZoplEGqVOrxzc9ferVapMHLWKADEzLFjEXHMWqkHT55t/OpsGLnaJTmO4sixlzAVv3K088OevZ+GUUwEozUAIvoPOtpWT2fW07IAAAAASUVORK5CYII="

LINE_COLORS = {
    "U1": "#E2021A", "U2": "#A365A4", "U3": "#F67F21", "U4": "#009641", "U5": "#F67F21", "U6": "#9D6643", 
    "1": "#FF5C5C", "2": "#FF5C5C", "D": "#FF5C5C", "71": "#FF5C5C", "O": "#FF5C5C", "5": "#FF5C5C", "6": "#FF5C5C", "18": "#FF5C5C",
    "S": "#00549F", "S1": "#00549F", "S2": "#00549F", "S3": "#00549F", "S4": "#00549F", "S7": "#00549F", "S45": "#00549F", "S50": "#00549F", "S80": "#00549F",
    "13A": "#E3001B", "40A": "#E3001B", "59A": "#E3001B", "57A": "#E3001B"
}

# Fixe Routen für die Optik (werden nur angezeigt, wenn Linie erkannt wird)
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

# Fallback Liste (Wien Mitte), falls GPS Suche nichts findet
DEFAULT_MARKERS = [
    {"name": "Stephansplatz", "lat": 48.2082, "lon": 16.3738, "rbl": [4200, 4206]},
    {"name": "Schwedenplatz", "lat": 48.2114, "lon": 16.3783, "rbl": [4205, 4212, 4208, 4210]},
]

# --- 3. HELFER FUNKTIONEN ---

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

# --- 4. DATA LOADER FÜR HALTESTELLEN (NEU!) ---
@st.cache_data(ttl=3600) # 1 Stunde Cache
def load_all_stations():
    # Wir laden die offizielle Haltestellenliste (CSV)
    url = "https://go.wien.gv.at/ressourcen/wienerlinien-ogd-haltestellen.csv"
    try:
        s = requests.get(url).content
        df = pd.read_csv(io.StringIO(s.decode('utf-8')), sep=';')
        # Wir brauchen nur RBL, Name, Lat, Lon
        # Spalten in CSV: RBL_NUMMER, HALTESTELLEN_NAME, STEIG_WGS84_LAT, STEIG_WGS84_LON
        return df[['RBL_NUMMER', 'HALTESTELLEN_NAME', 'STEIG_WGS84_LAT', 'STEIG_WGS84_LON']].dropna()
    except Exception as e:
        print(e)
        return pd.DataFrame()

def find_nearest_stations(lat, lon, limit=5):
    df = load_all_stations()
    if df.empty: return DEFAULT_MARKERS # Fallback
    
    # Simple Abstandsberechnung (Euklidisch reicht für Sortierung auf kurze Distanz)
    # Für exakte Meter nutzen wir später haversine
    df['dist'] = ((df['STEIG_WGS84_LAT'] - lat)**2 + (df['STEIG_WGS84_LON'] - lon)**2)
    
    # Die nächsten X finden
    nearest = df.sort_values('dist').head(limit * 4) # Mal mehr nehmen, da RBLs pro Steig sind
    
    # Gruppieren nach Stationsnamen, da eine Station mehrere RBLs (Steige) hat
    stations_map = {}
    for _, row in nearest.iterrows():
        name = row['HALTESTELLEN_NAME']
        rbl = int(row['RBL_NUMMER'])
        if name not in stations_map:
            stations_map[name] = {
                "name": name,
                "lat": row['STEIG_WGS84_LAT'],
                "lon": row['STEIG_WGS84_LON'],
                "rbl": []
            }
        stations_map[name]["rbl"].append(rbl)
    
    # Rückgabe als Liste
    result = list(stations_map.values())[:limit]
    return result

# --- 5. LOGIK: GPS & DATENABRUF ---

with st.sidebar:
    st.header("Einstellungen")
    gps_mode = st.toggle("Echtstandort verwenden", value=True)
    
    user_lat, user_lon = 48.2082, 16.3738 # Default
    
    if gps_mode:
        if HAS_GPS_MODULE:
            loc = get_geolocation()
            if loc:
                user_lat = loc['coords']['latitude']
                user_lon = loc['coords']['longitude']
                st.success(f"GPS: {user_lat:.4f}, {user_lon:.4f}")
            else:
                st.warning("Suche GPS...")
        else:
            st.error("Kein GPS Modul.")
            user_lat = st.slider("Lat", 48.10, 48.30, 48.2082)
            user_lon = st.slider("Lon", 16.20, 16.50, 16.3738)
    else:
        st.write("🧪 Testversion (Simuliert)")
        user_lat = 48.2090
        user_lon = 16.3720

# **KERN-ÄNDERUNG:** Dynamische Stationssuche
if gps_mode:
    # Suche die echten Stationen in deiner Nähe!
    active_stations = find_nearest_stations(user_lat, user_lon, limit=5)
else:
    active_stations = DEFAULT_MARKERS

# Nähe Check für Header
closest_station = active_stations[0]
min_dist = haversine(user_lat, user_lon, closest_station["lat"], closest_station["lon"])

if min_dist < 100:
    st.success(f"📍 **Du befindest Dich in der Station {closest_station['name']}**")
else:
    st.info(f"🚶 Unterwegs. Nächste Station: **{closest_station['name']}** ({int(min_dist)}m)")
    
# --- 6. API DATEN ---
# Wir entfernen Cache hier, da sich die Stationsliste dynamisch ändert!
def fetch_realtime_data(stations_list):
    all_rbls = []
    for s in stations_list: all_rbls.extend(s["rbl"])
    
    # URL darf nicht zu lang werden, Max ca 20-30 RBLs auf einmal ist sicher
    url = f"https://www.wienerlinien.at/ogd_realtime/monitor?rbl={'&rbl='.join(map(str, all_rbls))}"
    
    try:
        response = requests.get(url, timeout=5)
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

vehicles = fetch_realtime_data(active_stations)
vehicles.sort(key=lambda x: x["time"] if isinstance(x["time"], int) else 99)

# --- 7. KARTE ---
m = folium.Map(location=[user_lat, user_lon], zoom_start=15, tiles="CartoDB positron")

# User
folium.Marker(
    [user_lat, user_lon],
    tooltip="Deine Position",
    icon=folium.Icon(color="blue", icon="user", prefix="fa"),
    z_index_offset=1100
).add_to(m)

# Fixe Routen (Nur anzeigen wenn Linie da ist, sonst sieht es komisch aus in den Außenbezirken)
# Wir zeichnen sie trotzdem transparent, falls man zufällig in der Nähe ist
for line, path in SMOOTH_ROUTES.items():
    color = LINE_COLORS.get(line, "#888")
    if "S" in line: color = LINE_COLORS["S"]
    folium.PolyLine(path, color=color, weight=4, opacity=0.3).add_to(m)

# Fahrzeuge
for v in vehicles:
    pos = [v["lat"], v["lon"]]
    rot = 0
    
    # Versuche Position auf Linie zu mappen (nur wenn wir Pfad haben)
    route_key = v["line"]
    if "S" in route_key and "45" not in route_key: route_key = "S"
    
    if route_key in SMOOTH_ROUTES and isinstance(v["time"], int):
        path = SMOOTH_ROUTES[route_key]
        idx = min(v["time"] * 3, len(path)-2) 
        idx = max(0, int(idx))
        pos = path[idx]
        rot = calculate_bearing(path[idx], path[idx+1])
    
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

# Stationen (Dynamisch!)
for s in active_stations:
    icon = folium.CustomIcon(ICON_STATION_B64, icon_size=(20, 12), icon_anchor=(10, 6))
    folium.Marker(
        [s["lat"], s["lon"]], 
        popup=s['name'], 
        icon=icon,
        z_index_offset=1000
    ).add_to(m)

st_folium(m, width="100%", height=600, returned_objects=[])
