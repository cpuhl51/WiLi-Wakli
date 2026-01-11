import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import math
import pandas as pd
import io

# --- 1. SETUP & CSS ---
st.set_page_config(page_title="Wien Öffis V19 (Stable URLs)", layout="wide", page_icon="🚋")

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

TYPE_COLORS = {
    "ptBusCity": "#E3001B", "ptBusNight": "#182C52", 
    "ptTram": "#FF5C5C", "ptTramWLB": "#00549F",
    "ptMetro": "#A365A4", "ptTrainS": "#00549F"
}

# --- 3. DATA LOADER (REPARIERT: Stabile URLs) ---
@st.cache_data(ttl=3600, show_spinner="Lade Netzdaten der Stadt Wien...") 
def load_network_data():
    """Lädt Stationen, Steige und Linien von data.wien.gv.at"""
    
    # NEUE, STABILE URLS
    url_haltestellen = "https://data.wien.gv.at/csv/wienerlinien-ogd-haltestellen.csv"
    url_steige = "https://data.wien.gv.at/csv/wienerlinien-ogd-steige.csv"
    url_linien = "https://data.wien.gv.at/csv/wienerlinien-ogd-linien.csv"

    try:
        # Load Haltestellen
        s_h = requests.get(url_haltestellen, timeout=10).content
        df_h = pd.read_csv(io.StringIO(s_h.decode('utf-8')), sep=';')
        
        # Load Steige
        s_s = requests.get(url_steige, timeout=10).content
        df_s = pd.read_csv(io.StringIO(s_s.decode('utf-8')), sep=';')
        
        # Load Linien
        s_l = requests.get(url_linien, timeout=10).content
        df_l = pd.read_csv(io.StringIO(s_l.decode('utf-8')), sep=';')
        
        # Merge Steige + Linien Info
        df_full = df_s.merge(df_l, left_on='FK_LINIEN_ID', right_on='LINIEN_ID', how='left')
        
        return df_h, df_full
    except Exception as e:
        st.error(f"⚠️ Netzwerkfehler beim Laden der Wiener Linien Datenbank: {e}")
        # Leere Dataframes zurückgeben, damit App nicht abstürzt
        return pd.DataFrame(), pd.DataFrame()

# Load Data once
df_stations, df_steige = load_network_data()

# --- 4. GEOMETRIE HELFER ---

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def get_nearby_rbls_and_lines(lat, lon, radius=500):
    if df_stations.empty or df_steige.empty: return [], [], []
    
    # 1. Filtere Haltestellen im Radius (Box-Suche)
    lat_min, lat_max = lat - 0.01, lat + 0.01
    lon_min, lon_max = lon - 0.015, lon + 0.015
    
    nearby_h = df_stations[
        (df_stations['STEIG_WGS84_LAT'] > lat_min) & (df_stations['STEIG_WGS84_LAT'] < lat_max) &
        (df_stations['STEIG_WGS84_LON'] > lon_min) & (df_stations['STEIG_WGS84_LON'] < lon_max)
    ].copy()
    
    if nearby_h.empty: return [], [], []

    # Exakte Distanz
    nearby_h['dist'] = nearby_h.apply(lambda row: haversine(lat, lon, row['STEIG_WGS84_LAT'], row['STEIG_WGS84_LON']), axis=1)
    nearby_h = nearby_h[nearby_h['dist'] <= radius].sort_values('dist')
    
    if nearby_h.empty: return [], [], []

    halt_ids = nearby_h['HALTESTELLEN_ID'].unique()
    
    # 2. Steige und Linien finden
    relevant_steige = df_steige[df_steige['FK_HALTESTELLEN_ID'].isin(halt_ids)]
    
    rbl_list = relevant_steige['RBL_NUMMER'].dropna().unique().astype(int).tolist()
    line_ids = relevant_steige['LINIEN_ID'].unique()
    
    return rbl_list, nearby_h.to_dict('records'), line_ids

def get_route_points_for_lines(line_ids):
    """Holt ALLE Punkte (Stationen) für die gefundenen Linien, um sie zu zeichnen"""
    if df_steige.empty: return {}
    
    routes = {}
    lines_data = df_steige[df_steige['LINIEN_ID'].isin(line_ids)]
    
    for lid in line_ids:
        points = lines_data[lines_data['LINIEN_ID'] == lid][['STEIG_WGS84_LAT', 'STEIG_WGS84_LON']].dropna()
        if not points.empty:
            line_name = lines_data[lines_data['LINIEN_ID'] == lid]['BEZEICHNUNG'].iloc[0]
            routes[lid] = {
                "name": line_name,
                "points": points.values.tolist()
            }
    return routes

# --- 5. HAUPTPROGRAMM ---

with st.sidebar:
    st.header("Einstellungen")
    gps_mode = st.toggle("Echtstandort verwenden", value=True)
    
    user_lat, user_lon = 48.2082, 16.3738
    
    if gps_mode and HAS_GPS_MODULE:
        loc = get_geolocation()
        if loc:
            user_lat = loc['coords']['latitude']
            user_lon = loc['coords']['longitude']
            st.success(f"GPS: {user_lat:.4f}, {user_lon:.4f}")
        else:
            st.warning("Suche GPS...")
    elif not gps_mode:
        st.write("🧪 Testversion (Simuliert)")
        # Simuliere Kagraner Platz als Test für Busse
        user_lat = st.slider("Lat", 48.10, 48.30, 48.2435) 
        user_lon = st.slider("Lon", 16.20, 16.60, 16.4432)

# 1. Datenanalyse
rbls, station_info, active_line_ids = get_nearby_rbls_and_lines(user_lat, user_lon, radius=500)
route_geometries = get_route_points_for_lines(active_line_ids)

# Header
if station_info:
    closest = station_info[0]
    st.info(f"📍 Standort erkannt. Nächste Haltestelle: **{closest['HALTESTELLEN_NAME']}** ({int(closest['dist'])}m). Frage **{len(rbls)}** Steige ab.")
else:
    if df_stations.empty:
        st.warning("Datenbank konnte nicht geladen werden. Bitte Internet prüfen.")
    else:
        st.warning("Keine Haltestellen im Umkreis von 500m gefunden.")

# 2. Echtzeitdaten
def fetch_realtime_data(rbl_list):
    if not rbl_list: return []
    vehicles = []
    chunk_size = 20
    
    for i in range(0, len(rbl_list), chunk_size):
        chunk = rbl_list[i:i+chunk_size]
        url = f"https://www.wienerlinien.at/ogd_realtime/monitor?rbl={'&rbl='.join(map(str, chunk))}"
        try:
            resp = requests.get(url, timeout=4).json()
            for mon in resp.get("data", {}).get("monitors", []):
                slat = mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [0,0])[1]
                slon = mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [0,0])[0]
                
                for line in mon.get("lines", []):
                    line_name = line.get("name")
                    line_type = line.get("type") 
                    
                    departures = line.get("departures", {}).get("departure", [])
                    for dep in departures[:3]:
                        countdown = dep.get("departureTime", {}).get("countdown", 99)
                        if isinstance(countdown, int) and countdown > 30: continue
                        
                        v_info = dep.get("vehicle", {})
                        has_ac = v_info.get("barrierFree", False) or v_info.get("foldingRamp", False)
                        
                        vehicles.append({
                            "line": line_name,
                            "type": line_type,
                            "dest": line.get("towards"), 
                            "time": countdown,
                            "lat": slat, "lon": slon,
                            "ac": has_ac
                        })
        except: pass
    return vehicles

vehicles = fetch_realtime_data(rbls)
vehicles.sort(key=lambda x: x["time"] if isinstance(x["time"], int) else 99)

# --- 6. KARTE ---
m = folium.Map(location=[user_lat, user_lon], zoom_start=15, tiles="CartoDB positron")

folium.Marker([user_lat, user_lon], tooltip="Du", icon=folium.Icon(color="blue", icon="user", prefix="fa"), z_index_offset=1100).add_to(m)

# A) LINIE VERLÄUFE (Punkte)
for lid, data in route_geometries.items():
    l_name = data["name"]
    color = "#888888"
    if "U" in l_name: color = "#A365A4"
    elif "S" in l_name: color = "#00549F"
    elif "A" in l_name or "Bus" in l_name: color = "#E3001B"
    else: color = "#FF5C5C"
    
    # Verlauf als Punkte-Wolke
    for p in data["points"]:
        folium.CircleMarker(location=p, radius=2, color=color, fill=True, fill_opacity=0.4, popup=f"Linie {l_name}", weight=0).add_to(m)

# B) STATIONEN
for s in station_info:
    icon = folium.CustomIcon(ICON_STATION_B64, icon_size=(20, 12), icon_anchor=(10, 6))
    folium.Marker(
        [s['STEIG_WGS84_LAT'], s['STEIG_WGS84_LON']],
        popup=s['HALTESTELLEN_NAME'],
        icon=icon,
        z_index_offset=1000
    ).add_to(m)

# C) FAHRZEUGE
for v in vehicles:
    v_color = "#333"
    if "ptBus" in v["type"]: v_color = TYPE_COLORS["ptBusCity"]
    elif "ptTram" in v["type"]: v_color = TYPE_COLORS["ptTram"]
    elif "ptMetro" in v["type"]: v_color = TYPE_COLORS["ptMetro"]
    elif "ptTrain" in v["type"]: v_color = TYPE_COLORS["ptTrainS"]
    
    # U-Bahn Override
    if "U1" in v["line"]: v_color = "#E2021A"
    if "U2" in v["line"]: v_color = "#A365A4"
    if "U3" in v["line"]: v_color = "#F67F21"
    if "U4" in v["line"]: v_color = "#009641"
    if "U6" in v["line"]: v_color = "#9D6643"
    
    bg_class = "ac-yes-bg" if v["ac"] else "ac-no-bg"
    
    icon_html = f"""
    <div class="veh-box {bg_class}" style="background-color: {v_color};">
        {v['line']}
    </div>
    """
    
    folium.Marker(
        [v["lat"], v["lon"]], 
        popup=f"{v['line']} -> {v['dest']} ({v['time']}m)",
        icon=folium.DivIcon(html=icon_html, icon_size=(44,24), icon_anchor=(22,12))
    ).add_to(m)

st_folium(m, width="100%", height=600, returned_objects=[])
