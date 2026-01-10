import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import random
import math

# --- 1. KONFIGURATION & CSS ---
st.set_page_config(page_title="Wien Öffis Live V5", layout="wide", page_icon="🚋")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    /* Pfeil-Icon Stil */
    .arrow-icon {
        display: flex; justify-content: center; align-items: center;
        width: 40px; height: 40px;
        font-size: 24px; text-shadow: 0 0 3px white;
        transition: all 0.3s ease;
    }
    /* Runder Stations-Marker Stil */
    .station-cluster-icon {
        display: flex; justify-content: center; align-items: center;
        width: 30px; height: 30px; border-radius: 50%;
        border: 2px solid white; color: white; font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3); font-size: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🇦🇹 Wiener Linien Monitor (Stabil)")

# --- STATIONEN ---
STATIONS = {
    "Schwedenplatz (U1, U4, Tram)": [4205, 4212, 4208, 4210],
    "Karlsplatz (U1, U2, U4, WLB)": [4202, 4216, 4617, 4214],
    "Stephansplatz (U1, U3)": [4200, 4206]
}

# --- ROUTEN (SIMULATION) ---
ROUTES = {
    "1": [ 
        [48.2114, 16.3783], [48.2130, 16.3760], [48.2166, 16.3730], 
        [48.2160, 16.3690], [48.2150, 16.3650], [48.2110, 16.3600], 
        [48.2050, 16.3600], [48.2020, 16.3680], [48.2030, 16.3750]
    ],
    "U4": [ 
        [48.2250, 16.3600], [48.2180, 16.3650], 
        [48.2166, 16.3730], [48.2114, 16.3783], 
        [48.2082, 16.3738], [48.2000, 16.3600], 
        [48.1900, 16.3500] 
    ]
}

# --- 2. HILFSFUNKTIONEN ---

def get_line_color(line, v_type):
    colors = {"U1": "#E2021A", "U2": "#A365A4", "U3": "#F67F21", 
              "U4": "#009641", "U5": "#F67F21", "U6": "#9D6643"}
    if line in colors: return colors[line]
    if "ptTram" in v_type or line in ["1", "2", "D", "71"]: return "#009641"
    if "ptBus" in v_type: return "#000000"
    if "ptMetro" in v_type: return "#E2021A"
    if "ptTrain" in v_type: return "#00549F"
    return "gray"

def calculate_bearing(pointA, pointB):
    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])
    diffLong = math.radians(pointB[1] - pointA[1])
    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diffLong))
    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    return (initial_bearing + 360) % 360

@st.cache_data(ttl=12)
def fetch_live_data(rbl_list):
    rbl_str = "&rbl=".join(map(str, rbl_list))
    url = f"https://www.wienerlinien.at/ogd_realtime/monitor?rbl={rbl_str}"
    try:
        response = requests.get(url, timeout=4)
        data = response.json()
        vehicles = []
        for mon in data.get("data", {}).get("monitors", []):
            s_lat = mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [16,48])[1]
            s_lon = mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [16,48])[0]
            for line in mon.get("lines", []):
                for dep in line.get("departures", {}).get("departure", []):
                    countdown = dep.get("departureTime", {}).get("countdown", 99)
                    if countdown > 40: continue 
                    vehicles.append({
                        "line": line.get("name"), "type": line.get("type"),
                        "dest": line.get("towards"), "time": countdown,
                        "ac": dep.get("vehicle", {}).get("foldingRamp", False),
                        "lat": s_lat, "lon": s_lon
                    })
        return vehicles
    except: return []

# --- 3. LOGIK & KARTE ---

all_rbls = []
for rbls in STATIONS.values(): all_rbls.extend(rbls)
live_vehicles = fetch_live_data(all_rbls)

# Sortierung für Zeichnen (Weit entfernte zuerst malen -> unten liegen)
live_vehicles.sort(key=lambda x: x["time"], reverse=True)

m = folium.Map(location=[48.2100, 16.3700], zoom_start=14, tiles="CartoDB positron")

# Routen
for line_name, coords in ROUTES.items():
    l_type = "ptMetro" if "U" in line_name else "ptTram"
    folium.PolyLine(coords, color=get_line_color(line_name, l_type), weight=4, opacity=0.4).add_to(m)

# Fahrzeuge
for v in live_vehicles:
    color = get_line_color(v["line"], v["type"])
    popup_txt = f"<b>{v['line']}</b> ➤ {v['dest']}<br>in {v['time']} min"

    if v["line"] in ROUTES and v["time"] < 20:
        route = ROUTES[v["line"]]
        idx = min(v["time"], len(route) - 2)
        idx = max(0, idx)
        bearing = calculate_bearing(route[idx], route[idx+1])
        
        # PFEIL (Gedreht)
        html_arrow = f"""
        <div class="arrow-icon" style="transform: rotate({bearing - 90}deg); color: {color};">➤</div>
        """
        folium.Marker(route[idx], popup=popup_txt,
            icon=folium.DivIcon(html=html_arrow, icon_size=(40,40), icon_anchor=(20,20))
        ).add_to(m)
        
    else:
        # RUNDER PUNKT (Jitter)
        j_lat = v["lat"] + random.uniform(-0.0004, 0.0004)
        j_lon = v["lon"] + random.uniform(-0.0004, 0.0004)
        html_cluster = f"""
        <div class="station-cluster-icon" style="background:{color};">{v['line']}</div>
        """
        folium.Marker([j_lat, j_lon], popup=popup_txt,
            icon=folium.DivIcon(html=html_cluster, icon_size=(30,30))
        ).add_to(m)

# WICHTIG: returned_objects=[] verhindert, dass Streamlit beim Klicken neu lädt -> KEIN FLACKERN!
st_folium(m, width="100%", height=500, returned_objects=[])

# --- 4. LISTE (Wieder da!) ---

# Sortierung für Liste (Schnellste zuerst)
live_vehicles.sort(key=lambda x: x["time"])

st.subheader("⏱️ Nächste Abfahrten")
for v in live_vehicles:
    c = get_line_color(v["line"], v["type"])
    ac_icon = "❄️" if v["ac"] else "🌡️"
    
    st.markdown(f"""
    <div style="border-left:5px solid {c}; background:#f9f9f9; padding:10px; margin-bottom:8px; border-radius:4px; display:flex; justify-content:space-between; align-items:center;">
        <div>
            <b style="font-size:1.1em; color:{c}">{v['line']}</b> <small>nach</small> <b>{v['dest']}</b><br>
            <span style="font-size:0.8em; color:#666;">{ac_icon} {v['type']}</span>
        </div>
        <div style="text-align:right;">
            <span style="font-size:1.2em; font-weight:bold; color:{'#d32f2
