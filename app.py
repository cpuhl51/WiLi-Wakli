import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import math

# --- 1. SETUP & NEUES CSS (Hintergrund-Streifen) ---
st.set_page_config(page_title="Wien Öffis V14", layout="wide", page_icon="🚋")

st.markdown("""
    <style>
    .block-container { padding-top: 0rem; }
    
    /* FAHRZEUG BOX - Basis Design */
    .veh-box {
        width: 42px;  /* Etwas breiter für Text + Streifen */
        height: 22px;
        border: 1px solid white;
        box-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: sans-serif;
        font-weight: bold;
        font-size: 11px;
        color: white;
        border-radius: 2px;
        /* WICHTIG: Platz rechts für den Streifen lassen, damit Text nicht überlappt */
        padding-right: 10px; 
        /* Grundeinstellung für Hintergrundbild (der Streifen) */
        background-repeat: no-repeat;
        background-position: right top; /* Immer rechts fixiert */
        background-size: 10px 100%; /* 10px breit, volle Höhe */
    }

    /* KLIMATISIERT: BLAU-WEISS GESTREIFTER HINTERGRUND */
    .ac-yes-bg {
        background-image: repeating-linear-gradient(
            -45deg,
            #0066b3,
            #0066b3 3px,
            #ffffff 3px,
            #ffffff 6px
        );
    }

    /* NICHT KLIMATISIERT: ROT-WEISS GESTREIFTER HINTERGRUND */
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

# --- 2. NEUE LOGOS & DATEN ---

# NEUES Station Logo (Kleineres Format)
ICON_STATION_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAMCAIAAADtbgqsAAAAB3RJTUUH6gELByIjkfAdIgAAAoxJREFUeJxNzstrlGcYhvH7eQ8z3xwSJ4MxaWszJhiQduER3Fh0EWxr0ZIuohQhbVHU1iOIq2BQQjyQorVd1O5SaEUqQWuxbTAgSAOCqAhRkC4SjSaS4/jNTOY7vM/TRUH8cf0BF/i1IHAiXK74J3qnG1um8kun6gvTLe9PL26aqmmYXfdBdegWi7wZMTNE4BysdaNj5T0Hw8GbKp+HAGnPbt0S9P9i1q7O9PWqpnfF94mIjOViEdkscRjBGgDh9Rulw8fkxSTlc8QilSq981a6p6u06wAtqkUcY2EB1kApnpnRrcszF783sEaKxfKZvurZC5RIIJNmv0TWcmne1K0wq1YhlXTPx5WXEgBBIKVyoqM9+12famww8YOHlW8vRH/e0M3LnHCSAFJQytWlbcdnurlgt7fLwO8qnQGzOOcd2Jc8+DUAABSPP5cgkHRGEbTVEy/nQCTC2iYalheEWURe/jsGZgBQWhWWUjUQ4YVqRCwSAxYIgZMX/7h0fRgJA4JdCL/Z2bb/87au879dHrwrXhIswkwuZlBpzt/RvsFw7KzRzyamd3f3/33rPjLe/0colvqv/vPRppU/DtyenZpHyoNzsAbVAILj+7Yd/fJjo7W+MnRvT8/Psy9mka8FC5xLpj2kkpOvyvcePy1GjnI1pEhpFc/5rU0NP3R3bl7/HgATxHGhse7auf2ZjOdixyKLsqlHo5NHTl+amPf/Gh5xUYyEltCxX/mkbc1P3V+8XZ8Lo9gYTc6xUoQ3DN15dOjUryOjkyqdrMumZoplEGqVOrxzc9ferVapMHLWKADEzLFjEXHMWqkHT55t/OpsGLnaJTmO4sixlzAVv3K088OevZ+GUUwEozUAIvoPOtpWT2fW07IAAAAASUVORK5CYII="

# NEUES Type V Logo (Wird aktuell nicht als Marker verwendet, da wir die CSS-Boxen für alle Züge nutzen, um den Richtungsstrich konsistent anzuzeigen)
ICON_TYPE_V_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAICAIAAABh3dhzAAAAB3RJTUUH6gELByIbufKlvAAAAoZJREFUeJwFwUtvE1cUAOBz7p3ruWMPmdjjsT3EDxLCQ0iNBCFiB1WldtsdVTf9U0hdsWHbSuzYs4jEAgRIeZBA7VIbG8ePODN+zePOPf0+HF3ORqPR57PTvFXQBFprQEBERAQCQAACAMqINBESccYZY4igiYhIKXV+dp6lKQEgMm6w+lbDcTb2Dw4Mr7j557Nn8Xr9YP9gPB4N+gORE5yx1o1tpTUSASLjbDgYzMNAqcz1PM/z0jhmiDJfWC7n0XLBGOec1+v++dnnXpa9fPu22WoZQBRF6+cvXux8OA6G3677FadYGvzXnadUrNZ67Xblen29CLmKm82GzrLBxYCkE0dxvFrWGq2rYbfmbjpFNwzDMJiNx5c3b+1WSm670zYIQBjiUaV6z5JBxedC2ClVC7bghgFw13OlAZmdT0G6QsQAvu1YwiQptG0WDBZ5XsZApiph3HTLoZkvFWxCfXj42kDEOIl/efzkyf37neFwvVxJkUtUWnFLZi5nmqbKFDD2tdcFpTJNQua3fR8RkWGaJJMwmF3NpDC5ISxLrhYLpam2YY1AG+s42X+4//749A1jX5bzk6MjlaliqfTQK6dJNP3eRwacGcP+YL4IieBGq3U+z48mY8ZYza8mHI673cUqtCz71u5tIr3VaCylfPX3X2wyC3786ec/nj59tPfD6bv3mKhtf6t9fJIGQe3aRu/00/Tf3sU/HYsxf9Mt29e4ypplV0SREa33dnbD76N+p7Pt11eXl2cfP+zdvWNzfjWZ/Prb7/htONZaW5aU0pxOp47jbNqFr71+zsyVvLJEBAAAIAAFwAAIgAAEAABEmiYXF1mqWs16MF8sViuvWkmTVOYEAvwPrDxG5Tsp8voAAAAASUVORK5CYII="

# Simulierte User Position (z.B. Nähe Stephansplatz)
USER_LAT = 48.2090
USER_LON = 16.3720

LINE_COLORS = {
    "U1": "#E2021A", "U2": "#A365A4", "U3": "#F67F21", "U4": "#009641", "U5": "#F67F21", "U6": "#9D6643", 
    "1": "#FF5C5C", "2": "#FF5C5C", "D": "#FF5C5C", "71": "#FF5C5C",
    "S": "#00549F", "13A": "#E3001B", "40A": "#E3001B", "59A": "#E3001B"
}

RAW_ROUTES = {
    "U1": [[48.1530, 16.3850], [48.1700, 16.3800], [48.1870, 16.3750], [48.2000, 16.3700], [48.2082, 16.3738], [48.2130, 16.3780], [48.2180, 16.3900], [48.2250, 16.4000], [48.2450, 16.4400], [48.2600, 16.4500]], 
    "U2": [[48.2200, 16.5100], [48.2150, 16.4500], [48.2180, 16.4200], [48.2180, 16.3900], [48.2150, 16.3610], [48.2100, 16.3570], [48.2070, 16.3580], [48.2000, 16.3690]], 
    "U3": [[48.2110, 16.3100], [48.1960, 16.3350], [48.1950, 16.3500], [48.2082, 16.3738], [48.2060, 16.3850], [48.1900, 16.4000], [48.1750, 16.4150]], 
    "U4": [[48.2050, 16.2500], [48.1900, 16.2900], [48.1850, 16.3200], [48.1900, 16.3500], [48.2000, 16.3690], [48.2082, 16.3738], [48.2114, 16.3783], [48.2166, 16.3730], [48.2250, 16.3600], [48.2400, 16.3600]], 
    "U6": [[48.1350, 16.3200], [48.1500, 16.3300], [48.1750, 16.3350], [48.1960, 16.3350], [48.2150, 16.3400], [48.2300, 16.3500], [48.2400, 16.3800], [48.2600, 16.4000]], 
    "1": [[48.2114, 16.3783], [48.2166, 16.3730], [48.2150, 16.3650], [48.2110, 16.3600], [48.2050, 16.3600], [48.2020, 16.3680], [48.2030, 16.3750], [48.2050, 16.3850], [48.2100, 16.3950]],
    "2": [[48.2250, 16.3800], [48.2114, 16.3783], [48.2080, 16.3700], [48.2050, 16.3600], [48.2080, 16.3500], [48.2100, 16.3400], [48.2200, 16.3300]],
    "D": [[48.2600, 16.3650], [48.2350, 16.3600], [48.2166, 16.3730], [48.2150, 16.3650], [48.2050, 16.3600], [48.1900, 16.3800], [48.1830, 16.3800]],
    "71": [[48.2160, 16.3690], [48.2050, 16.3600], [48.2020, 16.3680], [48.1950, 16.3900], [48.1800, 16.4100], [48.1600, 16.4400]],
    "S": [[48.2600, 16.4000], [48.2400, 16.3800], [48.2180, 16.3900], [48.2060, 16.3850], [48.1850, 16.3800], [48.1700, 16.3700], [48.1500, 16.3200]] 
}

STATION_MARKERS = [
    {"name": "Schwedenplatz", "lat": 48.2114, "lon": 16.3783, "rbl": [4205, 4212, 4208, 4210]},
    {"name": "Karlsplatz", "lat": 48.2000, "lon": 16.3690, "rbl": [4202, 4216, 4617, 4214]},
    {"name": "Stephansplatz", "lat": 48.2082, "lon": 16.3738, "rbl": [4200, 4206]},
    {"name": "Westbahnhof", "lat": 48.1960, "lon": 16.3350, "rbl": [4920, 4921, 4600]},
    {"name": "Schottentor", "lat": 48.2150, "lon": 16.3610, "rbl": [4209, 4211]},
    {"name": "Landstraße", "lat": 48.2060, "lon": 16.3850, "rbl": [4204, 4213]},
    {"name": "Praterstern", "lat": 48.2180, "lon": 16.3900, "rbl": [4207, 4105]}
]

# --- 3. HELFER & DISTANZ ---

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

# --- 4. POSITION CHECK ---
closest_station = None
min_dist = 999999
stations_with_dist = []

for s in STATION_MARKERS:
    dist = haversine(USER_LAT, USER_LON, s["lat"], s["lon"])
    stations_with_dist.append({**s, "dist": dist})
    if dist < min_dist:
        min_dist = dist
        closest_station = s

stations_with_dist.sort(key=lambda x: x["dist"])

if min_dist < 100:
    st.success(f"📍 **Du befindest Dich in der Station {closest_station['name']}**")
else:
    st.info(f"🚶 Du bist unterwegs. Nächste Station: **{closest_station['name']}** ({int(min_dist)}m)")
    near_str = " | ".join([f"{s['name']} ({int(s['dist'])}m)" for s in stations_with_dist[:3]])
    st.caption(f"Nahegelegene Stationen: {near_str}")

# --- 5. API DATEN ---
@st.cache_data(ttl=10)
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
                line_name = line.get("name")
                departures = line.get("departures", {}).get("departure", [])
                
                for i, dep in enumerate(departures):
                    if i >= 4: break 
                    countdown = dep.get("departureTime", {}).get("countdown", 99)
                    if isinstance(countdown, int) and countdown > 12: continue
                    
                    vehicle_info = dep.get("vehicle", {})
                    # Prüfe auf Barrierefreiheit ODER Klapprampe als Indikator für Klima
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

vehicles = fetch_all_data()
vehicles.sort(key=lambda x: x["time"] if isinstance(x["time"], int) else 99)

# --- 6. KARTE ---
m = folium.Map(location=[USER_LAT, USER_LON], zoom_start=14, tiles="CartoDB positron")

folium.Marker(
    [USER_LAT, USER_LON],
    tooltip="Deine Position",
    icon=folium.Icon(color="blue", icon="user", prefix="fa")
).add_to(m)

for line, path in SMOOTH_ROUTES.items():
    color = LINE_COLORS.get(line, "#888")
    if "S" in line: color = LINE_COLORS["S"]
    folium.PolyLine(path, color=color, weight=4, opacity=0.4).add_to(m)

for s in STATION_MARKERS:
    # Neues Logo, Größe angepasst (20x12)
    icon = folium.CustomIcon(
        ICON_STATION_B64,
        icon_size=(20, 12),
        icon_anchor=(10, 6)
    )
    folium.Marker([s["lat"], s["lon"]], popup=s['name'], icon=icon).add_to(m)

for v in vehicles:
    pos = [v["lat"], v["lon"]]
    rot = 0
    
    route_key = v["line"]
    if "S" in route_key: route_key = "S"
    
    if route_key in SMOOTH_ROUTES and isinstance(v["time"], int):
        path = SMOOTH_ROUTES[route_key]
        idx = min(v["time"] * 3, len(path)-2) 
        idx = max(0, int(idx))
        pos = path[idx]
        rot = calculate_bearing(path[idx], path[idx+1])
    
    l_color = LINE_COLORS.get(v["line"], "#333")
    if "S" in v["line"]: l_color = LINE_COLORS["S"]
    if "A" in v["line"]: l_color = LINE_COLORS["13A"]

    # Bestimme die CSS-Klasse für den Hintergrund-Streifen
    bg_class = "ac-yes-bg" if v["ac"] else "ac-no-bg"
    
    # HTML Box: Hintergrundfarbe + Hintergrundbild-Klasse
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
        icon=folium.DivIcon(html=icon_html, icon_size=(42,24), icon_anchor=(21,12))
    ).add_to(m)

st_folium(m, width="100%", height=600, returned_objects=[])
