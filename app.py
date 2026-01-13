import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import math

# --- 1. SETUP ---
st.set_page_config(page_title="Wien Öffis V20", layout="wide", page_icon="🚋")

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

# --- 2. GRAFIKEN (BASE64) ---

# Station Logo
ICON_STATION_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAMCAIAAADtbgqsAAAAB3RJTUUH6gELByIjkfAdIgAAAoxJREFUeJxNzstrlGcYhvH7eQ8z3xwSJ4MxaWszJhiQduER3Fh0EWxr0ZIuohQhbVHU1iOIq2BQQjyQorVd1O5SaEUqQWuxbTAgSAOCqAhRkC4SjSaS4/jNTOY7vM/TRUH8cf0BF/i1IHAiXK74J3qnG1um8kun6gvTLe9PL26aqmmYXfdBdegWi7wZMTNE4BysdaNj5T0Hw8GbKp+HAGnPbt0S9P9i1q7O9PWqpnfF94mIjOViEdkscRjBGgDh9Rulw8fkxSTlc8QilSq981a6p6u06wAtqkUcY2EB1kApnpnRrcszF783sEaKxfKZvurZC5RIIJNmv0TWcmne1K0wq1YhlXTPx5WXEgBBIKVyoqM9+12famww8YOHlW8vRH/e0M3LnHCSAFJQytWlbcdnurlgt7fLwO8qnQGzOOcd2Jc8+DUAABSPP5cgkHRGEbTVEy/nQCTC2iYalheEWURe/jsGZgBQWhWWUjUQ4YVqRCwSAxYIgZMX/7h0fRgJA4JdCL/Z2bb/87au879dHrwrXhIswkwuZlBpzt/RvsFw7KzRzyamd3f3/33rPjLe/0colvqv/vPRppU/DtyenZpHyoNzsAbVAILj+7Yd/fJjo7W+MnRvT8/Psy9mka8FC5xLpj2kkpOvyvcePy1GjnI1pEhpFc/5rU0NP3R3bl7/HgATxHGhse7auf2ZjOdixyKLsqlHo5NHTl+amPf/Gh5xUYyEltCxX/mkbc1P3V+8XZ8Lo9gYTc6xUoQ3DN15dOjUryOjkyqdrMumZoplEGqVOrxzc9ferVapMHLWKADEzLFjEXHMWqkHT55t/OpsGLnaJTmO4sixlzAVv3K088OevZ+GUUwEozUAIvoPOtpWT2fW07IAAAAASUVORK5CYII="

# 1. U-BAHN (Silber/Rot)
ICON_UBAHN_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAICAIAAABh3dhzAAAAB3RJTUUH6gELByIbufKlvAAAAoZJREFUeJwFwUtvE1cUAOBz7p3ruWMPmdjjsT3EDxLCQ0iNBCFiB1WldtsdVTf9U0hdsWHbSuzYs4jEAgRIeZBA7VIbG8ePODN+zePOPf0+HF3ORqPR57PTvFXQBFprQEBERAQCQAACAMqINBESccYZY4igiYhIKXV+dp6lKQEgMm6w+lbDcTb2Dw4Mr7j557Nn8Xr9YP9gPB4N+gORE5yx1o1tpTUSASLjbDgYzMNAqcz1PM/z0jhmiDJfWC7n0XLBGOec1+v++dnnXpa9fPu22WoZQBRF6+cvXux8OA6G3677FadYGvzXnadUrNZ67Xblen29CLmKm82GzrLBxYCkE0dxvFrWGq2rYbfmbjpFNwzDMJiNx5c3b+1WSm670zYIQBjiUaV6z5JBxedC2ClVC7bghgFw13OlAZmdT0G6QsQAvu1YwiQptG0WDBZ5XsZApiph3HTLoZkvFWxCfXj42kDEOIl/efzkyf37neFwvVxJkUtUWnFLZi5nmqbKFDD2tdcFpTJNQua3fR8RkWGaJJMwmF3NpDC5ISxLrhYLpam2YY1AG+s42X+4//749A1jX5bzk6MjlaliqfTQK6dJNP3eRwacGcP+YL4IieBGq3U+z48mY8ZYza8mHI673cUqtCz71u5tIr3VaCylfPX3X2wyC3786ec/nj59tPfD6bv3mKhtf6t9fJIGQe3aRu/00/Tf3sU/HYsxf9Mt29e4ypplV0SREa33dnbD76N+p7Pt11eXl2cfP+zdvWNzfjWZ/Prb7/htONZaW5aU0pxOp47jbNqFr71+zsyVvLJEBAAAIAAFwAAIgAAEAABEmiYXF1mqWs16MF8sViuvWkmTVOYEAvwPrDxG5Tsp8voAAAAASUVORK5CYII="

# 2. TRAM (Rot/Weiß - E2 Style)
ICON_TRAM_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAICAYAAAABDm1nAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAACYSURBVDhPY/wPBAw4wX98YLCB4T8DGlBmYPzPgA+gq2VAB9A1/EcH6GqR1T5H5/9H5/9H5/9H5w/C+f/R+f/R+f/R+f/R+VjV4nM07z86H6tafI7m/UfnY1WLz9G8/+h8rGrxOZr3H52PVS0+R/P+o/OxqsXnaN5/dD5WtficzfuPzseqFp+jef/R+VjV4nM07z86H6ta5LUPAgMAs0910tWq1ZAAAAAASUVORK5CYII="

# 3. BUS (Rot - Gelenkbus)
ICON_BUS_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAICAYAAADe1u3TAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAABtSURBVDhPY/wPBAw4wX98YLCB4T8DGlBmYPzPgA+gq2VAB9A1/EcH6GqR1T5H5/9H5/9H5/9H5w/C+f/R+f/R+f/R+f/R+VjV4nM07z86H6tafI7m/UfnY1WLz9G8/+h8rGrxOZr3H52PVS2y2geBAQD8+2215x45wAAAAABJRU5ErkJggg=="


# --- 3. STATIONEN & ROUTEN ---
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

RAW_ROUTES = {
    "U1": [[48.1530, 16.3850], [48.1700, 16.3800], [48.1870, 16.3750], [48.2000, 16.3700], [48.2082, 16.3738], [48.2130, 16.3780], [48.2180, 16.3900], [48.2250, 16.4000], [48.2450, 16.4400], [48.2600, 16.4500]], 
    "13A": [[48.2020, 16.3380], [48.2005, 16.3420], [48.1990, 16.3450], [48.1970, 16.3490], [48.1960, 16.3550], [48.1945, 16.3580], [48.1930, 16.3600], [48.1850, 16.3650]], 
    "43": [[48.2150, 16.3610], [48.2160, 16.3550], [48.2165, 16.3500], [48.2170, 16.3420], [48.2180, 16.3350], [48.2200, 16.3300]],
    "D": [[48.2150, 16.3610], [48.2050, 16.3600], [48.2020, 16.3680], [48.2000, 16.3720], [48.1950, 16.3750], [48.1850, 16.3750]],
    "U2": [[48.2200, 16.5100], [48.2150, 16.4500], [48.2180, 16.4200], [48.2100, 16.3570], [48.2070, 16.3580], [48.2000, 16.3690]], 
    "U3": [[48.2110, 16.3100], [48.1960, 16.3350], [48.2082, 16.3738], [48.2060, 16.3850], [48.1900, 16.4000]], 
    "U4": [[48.1900, 16.2900], [48.1900, 16.3500], [48.2000, 16.3690], [48.2082, 16.3738], [48.2114, 16.3783], [48.2166, 16.3730], [48.2250, 16.3600]], 
    "U6": [[48.1750, 16.3350], [48.1960, 16.3350], [48.2150, 16.3400], [48.2300, 16.3500]]
}

LINE_COLORS = {
    "U1": "#E2021A", "U2": "#A365A4", "U3": "#F67F21", "U4": "#009641", "U6": "#9D6643",
    "S": "#00549F", "13A": "#E3001B", "D": "#E3001B", "43": "#E3001B", "1": "#E3001B"
}

# --- 4. MATHEMATIK ---

def smooth_path(points):
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

def calculate_bearing(p1, p2):
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

def get_vehicle_position_and_rotation(line_name, minutes_away):
    route_key = line_name
    if route_key not in SMOOTH_ROUTES:
        if "U" in route_key: route_key = "U1"
        elif "A" in route_key: route_key = "13A"
        elif len(route_key) <= 2: route_key = "D"
        else: return None, None, 0

    path = SMOOTH_ROUTES.get(route_key, [])
    if len(path) < 2: return None, None, 0

    speed_factor = 2.5
    start_index = len(path) - 2 
    current_index = start_index - int(minutes_away * speed_factor)
    current_index = max(0, min(current_index, len(path)-2))
    
    p1 = path[current_index]
    p2 = path[current_index + 1]
    rotation = calculate_bearing(p1, p2)
    return p1[0], p1[1], rotation

# --- 5. LOGIK: DATEN LADEN & DEDUPLIZIEREN ---

@st.cache_data(ttl=10)
def fetch_data():
    all_rbls = []
    for s in STATION_MARKERS: all_rbls.extend(s["rbl"])
    
    url = f"https://www.wienerlinien.at/ogd_realtime/monitor?rbl={'&rbl='.join(map(str, all_rbls))}"
    
    # Dictionary zur Deduplizierung: Key = VehicleID (oder Line+Dest), Value = Datensatz
    unique_vehicles = {}

    try:
        response = requests.get(url, timeout=4)
        data = response.json()
        
        for mon in data.get("data", {}).get("monitors", []):
            for line in mon.get("lines", []):
                line_name = line.get("name")
                direction = line.get("towards")
                
                for i, dep in enumerate(line.get("departures", {}).get("departure", [])):
                    if i >= 4: break 
                    countdown = dep.get("departureTime", {}).get("countdown", 99)
                    
                    if isinstance(countdown, int) and countdown < 40:
                        vh = dep.get("vehicle", {})
                        
                        # 1. Eindeutige ID bestimmen
                        # Die API liefert oft eine 'id' im vehicle-Objekt. Wenn nicht, bauen wir eine eigene.
                        v_id = vh.get("id")
                        if not v_id:
                            # Fallback ID: Linie + Richtung + (ungefähre Abfahrtszeit, um verschiedene Busse zu unterscheiden)
                            # Wir runden den Countdown auf 5-Minuten Blöcke, um Busse weit auseinander zu halten
                            # ABER: Hier wollen wir ja, dass der gleiche Bus (2 min und 5 min) erkannt wird.
                            # Bessere Strategie ohne ID: Wir nehmen Linie + Richtung als Key und speichern nur den KLEINSTEN Countdown.
                            # Das bedeutet aber, wir sehen pro Linie/Richtung nur EINEN Bus. Das ist zu wenig.
                            # Kompromiss: Wir nehmen an, Busse fahren alle 5 min.
                            # Also Key = Linie + Richtung + "Block_" + int(countdown / 10)
                            # Das ist unsicher.
                            # Sicherer: Einfach Linie + Richtung als Basis.
                            # Wenn wir schon einen Eintrag für 13A nach Alser Straße haben mit Zeit 2,
                            # und jetzt kommt einer mit Zeit 5 -> Wahrscheinlich der gleiche Bus an der nächsten Station.
                            # Wir behalten den mit Zeit 2 (genauer/näher).
                            v_id = f"{line_name}_{direction}"
                        
                        # 2. Fahrzeug-Typ bestimmen (für Icon)
                        v_type = "tram" # Default
                        if "U" in line_name: v_type = "ubahn"
                        elif "A" in line_name or "Bus" in line_name: v_type = "bus"
                        
                        ac = vh.get("barrierFree", False) or vh.get("foldingRamp", False)
                        
                        new_entry = {
                            "id": v_id,
                            "line": line_name,
                            "dest": direction,
                            "time": countdown,
                            "ac": ac,
                            "type": v_type
                        }
                        
                        # 3. Deduplizierungs-Logik
                        # Wenn wir dieses Fahrzeug schon kennen:
                        if v_id in unique_vehicles:
                            existing = unique_vehicles[v_id]
                            # Ist der neue Countdown kleiner? (Fahrzeug ist näher an einer gemessenen Station)
                            # Dann ist diese Position "genauer" bzw. aktueller für die Visualisierung.
                            if countdown < existing["time"]:
                                unique_vehicles[v_id] = new_entry
                            # Sonst behalten wir den alten (kleineren) Wert.
                        else:
                            # Neu
                            unique_vehicles[v_id] = new_entry

        return list(unique_vehicles.values())
    except: return []

vehicles = fetch_data()
vehicles.sort(key=lambda x: x["time"])

# --- 6. SIDEBAR & STANDORT ---

with st.sidebar:
    st.header("Einstellungen")
    gps_mode = st.toggle("Echtstandort (GPS)", value=False)
    
    # Standardwerte
    user_lat, user_lon = 48.2082, 16.3738
    
    if gps_mode:
        st.write("📡 Suche GPS...")
        if HAS_GPS_MODULE:
            loc = get_geolocation()
            if loc:
                user_lat, user_lon = loc['coords']['latitude'], loc['coords']['longitude']
                st.success("GPS Aktiv")
            else:
                st.warning("Warte auf Signal...")
        else:
            st.error("Plugin fehlt.")
    else:
        # Simulations-Modus
        sim_scenario = st.radio(
            "Szenario (Simulation):",
            ["In einer Station", "Unterwegs"],
            index=0
        )
        
        if sim_scenario == "In einer Station":
            # Stephansplatz Koordinaten
            user_lat, user_lon = 48.2082, 16.3738
            st.info("Standort: Stephansplatz")
        else:
            # Irgendwo dazwischen (z.B. Ring)
            user_lat, user_lon = 48.2050, 16.3650
            st.info("Standort: Ring / Oper")

# --- 7. KARTE ---

m = folium.Map(location=[user_lat, user_lon], zoom_start=15, tiles="CartoDB positron")

# User Marker
folium.Marker(
    [user_lat, user_lon],
    tooltip="Du bist hier",
    icon=folium.Icon(color="blue", icon="user", prefix="fa"),
    z_index_offset=1100
).add_to(m)

# Routen
for line, path in SMOOTH_ROUTES.items():
    color = LINE_COLORS.get(line, "#888")
    folium.PolyLine(path, color=color, weight=3, opacity=0.4).add_to(m)

# Stationen
for s in STATION_MARKERS:
    icon = folium.CustomIcon(ICON_STATION_B64, icon_size=(24, 14), icon_anchor=(12, 7))
    folium.Marker([s["lat"], s["lon"]], popup=s['name'], icon=icon, z_index_offset=1000).add_to(m)

# Fahrzeuge
for v in vehicles:
    lat, lon, rot = get_vehicle_position_and_rotation(v["line"], v["time"])
    
    if lat and lon:
        border_color = "#0066b3" if v["ac"] else "#d32f2f"
        
        # Icon Wahl
        current_icon_b64 = ICON_UBAHN_B64
        width, height = 40, 12
        if v["type"] == "bus":
            current_icon_b64 = ICON_BUS_B64
            width, height = 30, 8
        elif v["type"] == "tram":
            current_icon_b64 = ICON_TRAM_B64
            width, height = 32, 8
        
        display_rot = rot - 90
        
        icon_html = f"""
        <div style="
            transform: rotate({display_rot}deg); 
            transform-origin: center center; 
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            width: 40px; height: 40px;
        ">
            <img src="{current_icon_b64}" style="width: {width}px; height: {height}px; display: block;">
            <div style="width: {width}px; height: 3px; background: {border_color}; margin-top: 1px; border-radius: 2px;"></div>
            <div style="
                transform: rotate({-display_rot}deg);
                background: rgba(255,255,255,0.8); color: black; font-weight: bold; 
                font-size: 9px; padding: 0px 3px; border-radius: 4px; margin-top: 2px;
                border: 1px solid #ccc;
            ">
                {v['line']}
            </div>
        </div>
        """
        
        folium.Marker(
            [lat, lon],
            popup=f"{v['line']} -> {v['dest']} ({v['time']}m)",
            icon=folium.DivIcon(html=icon_html, icon_size=(40,40), icon_anchor=(20,20))
        ).add_to(m)

st_folium(m, width="100%", height=600, returned_objects=[])
