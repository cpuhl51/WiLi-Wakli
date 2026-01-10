import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import random
import math

# --- 1. KONFIGURATION & CSS ---
st.set_page_config(page_title="Wien Öffis Live V4", layout="wide", page_icon="🚋")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    /* Wir definieren eine CSS Klasse für rotierte Marker */
    .arrow-icon {
        display: flex; justify-content: center; align-items: center;
        width: 40px; height: 40px;
        font-size: 24px; text-shadow: 0 0 3px white;
        transition: all 0.3s ease;
    }
    .station-cluster-icon {
        display: flex; justify-content: center; align-items: center;
        width: 30px; height: 30px; border-radius: 50%;
        border: 2px solid white; color: white; font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3); font-size: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🇦🇹 Wiener Linien Monitor (Richtung & Routen)")

# Stationen (RBL IDs)
STATIONS = {
    "Schwedenplatz (U1, U4, Tram)": [4205, 4212, 4208, 4210],
    "Karlsplatz (U1, U2, U4, WLB)": [4202, 4216, 4617, 4214],
    "Stephansplatz (U1, U3)": [4200, 4206]
}

# --- ROUTEN DATEN (Simulation) ---
# Diese Pfade werden nun fix auf die Karte gezeichnet.
# Für echte App bräuchte man ALLE Linien (GTFS shapes).
ROUTES = {
    "1": [ # Ring/Kai Rundfahrt
        [48.2114, 16.3783], [48.2130, 16.3760], [48.2166, 16.3730], # Schwedenpl -> Schottenring
        [48.2160, 16.3690], [48.2150, 16.3650], [48.2110, 16.3600], # Börse -> Burgtheater
        [48.2050, 16.3600], [48.2020, 16.3680], [48.2030, 16.3750]  # Oper -> Schwarzenbergpl
    ],
    "U4": [ # Donaukanal Strecke (Ausschnitt)
        [48.2250, 16.3600], [48.2180, 16.3650], # Friedensbrücke -> Roßauer Lände
        [48.2166, 16.3730], [48.2114, 16.3783], # Schottenring -> Schwedenplatz
        [48.2082, 16.3738], [48.2000, 16.3600], # Stadtpark -> Karlsplatz
        [48.1900, 16.3500] # Kettenbrückengasse
    ]
}

# --- 2. MATHEMATIK & HILFSFUNKTIONEN ---

def get_line_color(line, v_type):
    """Farben nach User-Vorgabe"""
    colors = {"U1": "#E2021A", "U2": "#A365A4", "U3": "#F67F21", 
              "U4": "#009641", "U5": "#F67F21", "U6": "#9D6643"}
    if line in colors: return colors[line]
    
    if "ptTram" in v_type or line in ["1", "2", "D", "71"]: return "#009641" # BIM GRÜN
    if "ptBus" in v_type: return "#000000"   # BUS SCHWARZ
    if "ptMetro" in v_type: return "#E2021A" # Fallback U-Bahn Rot
    if "ptTrain" in v_type: return "#00549F" # S-Bahn BLAU
    return "gray"

def calculate_bearing(pointA, pointB):
    """Berechnet den Winkel (Himmelsrichtung 0-360 Grad) zwischen zwei Koordinaten"""
    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])
    diffLong = math.radians(pointB[1] - pointA[1])

    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diffLong))

    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360
    return compass_bearing

@st.cache_data(ttl=12)
def fetch_live_data(rbl_list):
    rbl_str = "&rbl=".join(map(str, rbl_list))
    url = f"https://www.wienerlinien.at/ogd_realtime/monitor?rbl={rbl_str}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        vehicles = []
        for mon in data.get("data", {}).get("monitors", []):
            # Station coordinates fallback
            s_lat = mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [16,48])[1]
            s_lon = mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [16,48])[0]
            for line in mon.get("lines", []):
                for dep in line.get("departures", {}).get("departure", []):
                    countdown = dep.get("departureTime", {}).get("countdown", 99)
                    if countdown > 25: continue # Nur die nächsten 25 min
                    
                    vehicles.append({
                        "line": line.get("name"), "type": line.get("type"),
                        "dest": line.get("towards"), "time": countdown,
                        "ac": dep.get("vehicle", {}).get("foldingRamp", False),
                        "lat": s_lat, "lon": s_lon
                    })
        return vehicles
    except: return []

# --- 3. APP STARTEN ---

all_rbls = []
for rbls in STATIONS.values(): all_rbls.extend(rbls)
live_vehicles = fetch_live_data(all_rbls)
# WICHTIG: Sortieren damit "nahe" Fahrzeuge OBEN liegen (zuletzt gezeichnet werden)
live_vehicles.sort(key=lambda x: x["time"], reverse=True)

# HELLE KARTE (CartoDB Positron)
m = folium.Map(location=[48.2100, 16.3700], zoom_start=14, tiles="CartoDB positron")

# A) ROUTEN EINZEICHNEN (Die farbigen Linien)
for line_name, coords in ROUTES.items():
    l_type = "ptMetro" if "U" in line_name else "ptTram"
    color = get_line_color(line_name, l_type)
    folium.PolyLine(
        coords, color=color, weight=4, opacity=0.6, 
        tooltip=f"Streckenverlauf Linie {line_name}"
    ).add_to(m)


# B) FAHRZEUGE ZEICHNEN
for v in live_vehicles:
    color = get_line_color(v["line"], v["type"])
    popup_txt = f"<b>{v['line']}</b> ➤ {v['dest']}<br>in {v['time']} min"

    # Fall 1: Wir kennen die Route -> Wir zeichnen einen PFEIL
    if v["line"] in ROUTES and v["time"] < 20:
        route = ROUTES[v["line"]]
        # Interpolation index based on time
        idx = min(v["time"], len(route) - 2)
        idx = max(0, idx) # Safety handle
        
        pos_curr = route[idx]
        pos_next = route[idx+1]
        
        # Winkel berechnen
        bearing = calculate_bearing(pos_curr, pos_next)
        
        # Das rotierte Pfeil-Icon (nutzt die CSS Klasse von oben)
        # Wir müssen 90deg abziehen, da das Unicode Zeichen ➤ standardmäßig nach rechts zeigt.
        html_arrow = f"""
        <div class="arrow-icon" style="transform: rotate({bearing - 90}deg); color: {color};">
            ➤
        </div>
        """
        folium.Marker(
            pos_curr, popup=popup_txt,
            icon=folium.DivIcon(html=html_arrow, icon_size=(40,40), icon_anchor=(20,20))
        ).add_to(m)
        
    # Fall 2: Keine Route bekannt -> Runder Marker mit Jitter an Station
    else:
        jitter_lat = v["lat"] + random.uniform(-0.0004, 0.0004)
        jitter_lon = v["lon"] + random.uniform(-0.0004, 0.0004)
        
        html_cluster = f"""
        <div class="station-cluster-icon" style="background:{color};">
            {v['line']}
        </div>
        """
        folium.Marker(
            [jitter_lat, jitter_lon], popup=popup_txt,
            icon=folium.DivIcon(html=html_cluster, icon_size=(30,30))
        ).add_to(m)

st_folium(m, width="100%", height=600)
