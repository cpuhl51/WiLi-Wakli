import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import pandas as pd
from datetime import datetime

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Wien Öffis Live", layout="wide", page_icon="🚋")

# Custom CSS für bessere Lesbarkeit am Handy
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    .css-1y4p8pa { padding: 0 1rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("🇦🇹 Wiener Linien Live-Monitor")

# RBL Nummern für wichtige Stationen (API IDs)
STATIONS = {
    "Schwedenplatz": [4205, 4212, 4208, 4210], # U1, U4, 1, 2
    "Karlsplatz": [4202, 4216, 4617],         # U1, U4, U2, Badner Bahn
    "Stephansplatz": [4200, 4206]             # U1, U3
}

# Routen-Simulation (Damit wir Linien zeichnen können)
# Hinweis: Für ein perfektes Netz bräuchte man die GTFS shapes.txt (zu groß für hier).
# Wir nutzen Demo-Pfade für U4 und Linie 1.
ROUTES = {
    "1": [[48.2114, 16.3783], [48.2130, 16.3760], [48.2166, 16.3730], [48.2150, 16.3650]],
    "U4": [[48.2114, 16.3783], [48.2082, 16.3738], [48.2000, 16.3600], [48.1900, 16.3500]]
}

# --- 2. HILFSFUNKTIONEN (Farben & Icons) ---
def get_line_color(line, v_type):
    colors = {
        "U1": "#E2021A", "U2": "#A365A4", "U3": "#F67F21", 
        "U4": "#009641", "U5": "#F67F21", "U6": "#9D6643",
        "1": "#BE1522", "2": "#BE1522", "D": "#BE1522", "71": "#BE1522"
    }
    if line in colors: return colors[line]
    if "ptMetro" in v_type: return "#BE1522"
    if "ptTram" in v_type: return "#009641" # Grün für Bim
    if "ptBus" in v_type: return "#000000"
    return "blue"

def get_icon(v_type):
    if "Tram" in v_type: return "🚋"
    if "Metro" in v_type: return "🚇"
    if "Bus" in v_type: return "🚌"
    return "📍"

# --- 3. LIVE DATEN ABRUFEN ---
@st.cache_data(ttl=15) # Daten nur alle 15 sek neu laden (Caching)
def fetch_live_data(rbl_list):
    # RBLs zu String verbinden: "4205,4212,..."
    rbl_str = "&rbl=".join(map(str, rbl_list))
    url = f"https://www.wienerlinien.at/ogd_realtime/monitor?rbl={rbl_str}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        vehicles = []
        monitors = data.get("data", {}).get("monitors", [])
        
        for mon in monitors:
            lines = mon.get("lines", [])
            for line in lines:
                line_name = line.get("name")
                v_type = line.get("type")
                towards = line.get("towards")
                
                # Nächste Abfahrten
                departures = line.get("departures", {}).get("departure", [])
                for dep in departures:
                    time_widget = dep.get("departureTime", {})
                    countdown = time_widget.get("countdown", 99)
                    
                    # Fahrzeug Infos
                    vehicle = dep.get("vehicle", {})
                    barrier_free = vehicle.get("barrierFree", False)
                    folding_ramp = vehicle.get("foldingRamp", False)
                    # Annahme: Wenn barrierefrei oder Rampe -> oft klimatisiert (vereinfacht)
                    # Echte API hat manchmal "airConditioned", aber nicht immer.
                    ac = folding_ramp or barrier_free 
                    
                    vehicles.append({
                        "line": line_name,
                        "type": v_type,
                        "dest": towards,
                        "time": countdown,
                        "ac": ac,
                        "lat": mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [16,48])[1],
                        "lon": mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [16,48])[0]
                    })
        return vehicles
    except Exception as e:
        st.error(f"Fehler beim API Abruf: {e}")
        return []

# --- 4. APP LOGIK ---

# 1. Daten holen (Alle RBLs zusammen)
all_rbls = []
for rbls in STATIONS.values():
    all_rbls.extend(rbls)

live_vehicles = fetch_live_data(all_rbls)

# 2. Karte vorbereiten
m = folium.Map(location=[48.2100, 16.3750], zoom_start=14, tiles="CartoDB dark_matter")

# Stationen Marker
for name, rbls in STATIONS.items():
    # Wir nehmen an, der erste Monitor hat die Koordinaten der Station
    # (In einer echten App hätten wir die Koordinaten fest gespeichert)
    pass 

# Fahrzeuge auf Karte (Position interpolieren oder an Station zeigen)
for v in live_vehicles:
    # Wenn wir eine simulierte Route haben (z.B. U4), berechnen wir die Position
    pos = [v["lat"], v["lon"]] # Default: An der Station stehen
    
    if v["line"] in ROUTES and v["time"] < 15:
        # Simple Interpolation: Wir schieben das Icon entlang der Route
        route = ROUTES[v["line"]]
        idx = min(v["time"], len(route)-1)
        # Sehr vereinfacht - nur Demo:
        if idx < len(route):
            pos = route[idx]

    # Marker erstellen
    color = get_line_color(v["line"], v["type"])
    icon_sym = get_icon(v["type"])
    ac_txt = "❄️" if v["ac"] else ""
    
    html = f"""
    <div style="background:{color}; width:30px; height:30px; border-radius:50%; 
                border:2px solid white; display:flex; justify-content:center; 
                align-items:center; color:white; font-size:14px; box-shadow:0 0 5px black;">
        {icon_sym}
    </div>
    """
    
    folium.Marker(
        pos,
        popup=f"<b>{v['line']}</b> nach {v['dest']}<br>in {v['time']} min",
        icon=folium.DivIcon(html=html, icon_size=(30,30))
    ).add_to(m)

st_folium(m, width="100%", height=500)

# 3. Liste unter der Karte
st.subheader("⏱️ Live Abfahrtszeiten")

# Wir sortieren nach Zeit
live_vehicles.sort(key=lambda x: x["time"])

for v in live_vehicles:
    c = get_line_color(v["line"], v["type"])
    ac_badge = "❄️ Klima" if v["ac"] else "🌡️ Keine Klima"
    
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; 
                border-bottom:1px solid #eee; padding:8px; margin-bottom:5px;">
        <div>
            <span style="background:{c}; color:white; padding:2px 8px; border-radius:4px; font-weight:bold;">
                {v['line']}
            </span>
            <span style="margin-left:8px; font-weight:500;">{v['dest']}</span><br>
            <span style="font-size:0.8em; color:gray;">{ac_badge}</span>
        </div>
        <div style="text-align:right;">
            <span style="font-size:1.2em; font-weight:bold; color:{'red' if v['time']<2 else 'green'}">
                {v['time']} min
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
