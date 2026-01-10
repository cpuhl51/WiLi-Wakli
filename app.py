import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import random
import math
import numpy as np # Für die Kurvenberechnung

# --- 1. KONFIGURATION & CSS ---
st.set_page_config(page_title="Wien Öffis Live V7", layout="wide", page_icon="🚋")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    
    /* PFEIL / FAHRZEUG BASIS-STIL */
    .vehicle-icon {
        display: flex; justify-content: center; align-items: center;
        width: 40px; height: 22px; /* Längliche Form wie im Bild */
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.4);
        font-weight: bold; font-size: 10px; color: black;
        transition: all 0.5s linear;
        border: 1px solid #333;
    }
    
    /* STILE NACH DEINEN PICTOGRAMMEN */
    /* U-Bahn: Silberpfeil (Grau) */
    .style-silberpfeil {
        background: linear-gradient(90deg, #a0a0a0 0%, #d0d0d0 50%, #a0a0a0 100%);
        color: white; text-shadow: 0 0 2px black;
    }
    /* U-Bahn: V-Wagen (Rot-Weiß-Rot) */
    .style-v-wagen {
        background: linear-gradient(90deg, #d32f2f 0%, #d32f2f 15%, #ffffff 15%, #ffffff 25%, #d32f2f 25%, #d32f2f 100%);
        color: white;
    }
    /* Tram: Rot-Weiß (Klassisch E2/c5) */
    .style-tram-old {
        background: linear-gradient(to bottom, #d32f2f 0%, #d32f2f 50%, #ffffff 50%, #ffffff 100%);
        color: black;
    }
    /* Tram: ULF (Dunkleres Grau/Rot) */
    .style-ulf {
        background: linear-gradient(90deg, #b71c1c 0%, #424242 100%);
        color: white; border-radius: 8px; /* Runder, da Low Floor */
    }
    /* Bus */
    .style-bus {
        background: #d32f2f; border-radius: 6px;
    }
    
    /* Runde Stationen Marker (Wenn keine Route da ist) */
    .station-cluster-icon {
        display: flex; justify-content: center; align-items: center;
        width: 25px; height: 25px; border-radius: 50%;
        background: #333; color: white; border: 2px solid white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.5); font-size: 11px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🇦🇹 Wiener Linien Master-Map")

# --- ÜBERSETZUNGSTABELLE (FIX FÜR "ptMetro") ---
TYPE_TRANSLATION = {
    "ptMetro": "U-Bahn",
    "ptTram": "Straßenbahn",
    "ptBus": "Autobus",
    "ptTrain": "S-Bahn"
}

# --- STATIONEN ---
STATIONS = {
    "Schwedenplatz": [4205, 4212, 4208, 4210],
    "Karlsplatz": [4202, 4216, 4617],
    "Stephansplatz": [4200, 4206]
}

# --- ROUTEN MIT KURVEN ---
# Wir nutzen wenige Eckpunkte, die Funktion smooth_path macht daraus Kurven
RAW_ROUTES = {
    "1": [ 
        [48.2114, 16.3783], [48.2130, 16.3760], [48.2166, 16.3730], # Kai
        [48.2160, 16.3690], [48.2150, 16.3650], [48.2110, 16.3600], # Ring
        [48.2050, 16.3600], [48.2020, 16.3680], [48.2030, 16.3750]  # Oper
    ],
    "U4": [ 
        [48.2250, 16.3600], [48.2180, 16.3650], [48.2166, 16.3730], 
        [48.2114, 16.3783], [48.2082, 16.3738], [48.2000, 16.3600], 
        [48.1900, 16.3500] 
    ]
}

# --- FUNKTIONEN ---

def smooth_path(points, formatting=False):
    """Macht aus eckigen Linien weiche Kurven (Interpolation)"""
    if len(points) < 3: return points
    
    smoothed = []
    # Einfache Interpolation für weichere Ecken
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i+1]
        
        # Wir fügen 5 Zwischenpunkte ein
        steps = 5
        for j in range(steps):
            alpha = j / steps
            lat = p1[0] * (1 - alpha) + p2[0] * alpha
            lon = p1[1] * (1 - alpha) + p2[1] * alpha
            smoothed.append([lat, lon])
            
    smoothed.append(points[-1])
    return smoothed

# Kurven vor-berechnen
SMOOTH_ROUTES = {k: smooth_path(v) for k,v in RAW_ROUTES.items()}


def get_vehicle_style_class(line, v_type, features):
    """
    Bestimmt den CSS-Style basierend auf dem Fahrzeugtyp (Silberpfeil, ULF, etc.)
    Da die API nicht immer das Modell nennt, raten wir hier schlau.
    """
    # 1. U-Bahnen
    if "ptMetro" in v_type or "U" in line:
        # U6 ist speziell (Typ T)
        if line == "U6": return "style-tram-old" # Sieht eher aus wie Bim
        # V-Wagen hat Klima (und ist neuer)
        if features.get("foldingRamp") or features.get("barrierFree"): 
            return "style-v-wagen"
        return "style-silberpfeil" # Alte U-Bahn
        
    # 2. Straßenbahnen
    if "ptTram" in v_type:
        # ULF/Flexity (Niederflur = Rampe)
        if features.get("foldingRamp"): return "style-ulf"
        return "style-tram-old" # E2 Hochflur
        
    return "style-bus"

def calculate_bearing(pointA, pointB):
    """Berechnet Drehung für das Fahrzeug"""
    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])
    diffLong = math.radians(pointB[1] - pointA[1])
    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diffLong))
    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    return (initial_bearing + 360) % 360

@st.cache_data(ttl=10)
def fetch_live_data(rbl_list):
    rbl_str = "&rbl=".join(map(str, rbl_list))
    url = f"https://www.wienerlinien.at/ogd_realtime/monitor?rbl={rbl_str}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        vehicles = []
        for mon in data.get("data", {}).get("monitors", []):
            s_lat = mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [16,48])[1]
            s_lon = mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [16,48])[0]
            
            for line in mon.get("lines", []):
                for dep in line.get("departures", {}).get("departure", []):
                    countdown = dep.get("departureTime", {}).get("countdown", 99)
                    if countdown > 30: continue 
                    
                    veh_info = dep.get("vehicle", {})
                    
                    vehicles.append({
                        "line": line.get("name"), 
                        "type": line.get("type"), # z.B. ptMetro
                        "dest": line.get("towards"), 
                        "time": countdown,
                        "features": veh_info, # Enthält Infos über Rampe etc.
                        "lat": s_lat, "lon": s_lon
                    })
        return vehicles
    except: return []

# --- APP START ---

all_rbls = []
for rbls in STATIONS.values(): all_rbls.extend(rbls)
live_vehicles = fetch_live_data(all_rbls)
live_vehicles.sort(key=lambda x: x["time"], reverse=True)

m = folium.Map(location=[48.2100, 16.3700], zoom_start=14, tiles="CartoDB positron")

# A) KURVIGE ROUTEN ZEICHNEN
for line_name, points in SMOOTH_ROUTES.items():
    color = "#009641" if line_name == "U4" else "#FF5C5C" # U4 Grün, Bim Rot
    folium.PolyLine(points, color=color, weight=4, opacity=0.5).add_to(m)

# B) FAHRZEUGE IM PICTROGRAMM-STIL ZEICHNEN
for v in live_vehicles:
    # 1. Übersetzung (ptMetro -> U-Bahn)
    display_type = TYPE_TRANSLATION.get(v["type"], v["type"])
    
    # 2. Welcher Style? (Silberpfeil, V-Wagen, etc.)
    css_class = get_vehicle_style_class(v["line"], v["type"], v["features"])
    
    # Popup Text
    popup_txt = f"<b>{v['line']}</b> ➤ {v['dest']}<br>Modell: {display_type}<br>in {v['time']} min"

    # Position & Rotation berechnen
    pos = [v["lat"], v["lon"]]
    rotation = 0
    
    if v["line"] in SMOOTH_ROUTES and v["time"] < 20:
        route = SMOOTH_ROUTES[v["line"]]
        # Wir fahren die Kurve ab (mehr Punkte = genauere Position)
        idx = min(v["time"] * 3, len(route) - 2) # *3 wegen mehr Punkten durch Glättung
        idx = max(0, int(idx))
        pos = route[idx]
        rotation = calculate_bearing(route[idx], route[idx+1])

    # DAS ICON (CSS Rechteck, sieht aus wie Fahrzeug)
    # Wir drehen das ganze Div um 'rotation' Grad
    html_icon = f"""
    <div style="transform: rotate({rotation - 90}deg);">
        <div class="vehicle-icon {css_class}">
            {v['line']}
        </div>
    </div>
    """
    
    folium.Marker(pos, popup=popup_txt,
        icon=folium.DivIcon(html=html_icon, icon_size=(40,22), icon_anchor=(20,11))
    ).add_to(m)

st_folium(m, width="100%", height=500, returned_objects=[])

# --- LISTE UNTEN ---
live_vehicles.sort(key=lambda x: x["time"])

st.subheader("Fahrzeuge im Umkreis")
for v in live_vehicles:
    display_type = TYPE_TRANSLATION.get(v["type"], v["type"])
    c_bar = "#009641" if "U" in v["line"] else "#FF5C5C"
    
    # Check für Klima
    ac = v["features"].get("foldingRamp") or v["features"].get("barrierFree")
    ac_icon = "❄️" if ac else "🌡️"
    
    st.markdown(f"""
    <div style="border-left:5px solid {c_bar}; background:white; padding:10px; margin-bottom:5px; border-radius:4px; box-shadow:0 1px 2px #ddd;">
        <div style="display:flex; justify-content:space-between;">
            <div>
                <b style="font-size:1.1em;">{v['line']}</b> <small>Richtung</small> <b>{v['dest']}</b>
                <br><span style="color:gray; font-size:0.85em;">{display_type} | {ac_icon}</span>
            </div>
            <div style="text-align:right;">
                 <span style="font-size:1.3em; font-weight:bold; color:#333;">{v['time']}</span> min
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
