import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np

# --- 1. KONFIGURATION & DESIGN ---
st.set_page_config(page_title="Wien Öffis Live", layout="wide", page_icon="🚋")

# Titel und CSS Anpassungen für Handy-Optimierung
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("🇦🇹 Wiener Linien Monitor")

# --- 2. LOGIK: FARBEN & TYPEN ---
# Offizielle Farben der Wiener Linien
LINE_COLORS = {
    "U1": "#E2021A", "U2": "#A365A4", "U3": "#F67F21", 
    "U4": "#009641", "U5": "#F67F21", "U6": "#9D6643",
    "1": "#BE1522", "D": "#BE1522", # Straßenbahnen oft Rot im Plan, wir machen Route grün für Erkennbarkeit?
    # Oder wir nutzen Systemfarben:
}

def get_route_color(line_name, v_type):
    """Bestimmt die Farbe der Linie auf der Karte"""
    if line_name in LINE_COLORS:
        return LINE_COLORS[line_name]
    if "ptMetro" in v_type: return "#BE1522" # Fallback U-Bahn Rot
    if "ptTram" in v_type: return "#009641"  # Bim Grün (User Wunsch)
    if "ptBus" in v_type: return "#000000"   # Bus Schwarz
    if "ptTrain" in v_type: return "#00549F" # S-Bahn Blau
    return "gray"

def get_icon_emoji(v_type):
    if "Tram" in v_type: return "🚋"
    if "Metro" in v_type: return "🚇"
    if "Bus" in v_type: return "🚌"
    return "📍"

# --- 3. DATEN (SIMULATION) ---
# HIER würden wir später die echte "shapes.txt" der Wiener Linien laden.
# Für den Start simulieren wir die Route der Linie 1 und U4 exakt.

ROUTES = {
    "1": [
        [48.2114, 16.3783], [48.2130, 16.3760], [48.2166, 16.3730], # Kai
        [48.2160, 16.3690], [48.2150, 16.3650], [48.2110, 16.3600], # Ring
        [48.2050, 16.3600], [48.2020, 16.3680], [48.2030, 16.3750]  # Oper
    ],
    "U4": [
        [48.2114, 16.3783], [48.2082, 16.3738], [48.2000, 16.3600],
        [48.1900, 16.3500], [48.1850, 16.3400]
    ]
}

# Simulierte Live-Fahrzeuge (Später API Abruf)
VEHICLES = [
    {"line": "1", "type": "ptTram", "to": "Prater Hauptallee", "min": 2, "ac": True, "model": "Flexity"},
    {"line": "1", "type": "ptTram", "to": "Stefan-F.-Platz", "min": 7, "ac": False, "model": "E2"},
    {"line": "U4", "type": "ptMetro", "to": "Hütteldorf", "min": 3, "ac": True, "model": "V-Wagen"}
]

# --- 4. POSITION BERECHNEN ---
def get_position_on_route(route, minutes_left):
    """
    Zauberei: Berechnet wo das Fahrzeug auf der Linie ist.
    Annahme für Demo: Ganze Route dauert ca 15 min.
    """
    total_points = len(route)
    if total_points < 2: return route[0]
    
    # Wir tun so, als ob Index 0 die Station ist. 
    # Je mehr Minuten, desto weiter weg (höherer Index).
    # Skalierung: 1 Min = 1 Segment (nur als Beispiel)
    idx = min(minutes_left, total_points - 2)
    
    # Interpolation zwischen zwei Punkten für flüssige Optik
    p1 = route[idx]
    p2 = route[idx+1]
    
    lat = (p1[0] + p2[0]) / 2
    lon = (p1[1] + p2[1]) / 2
    return [lat, lon]


# --- 5. DIE APP GUI ---

# Karte erstellen (Zentrum Wien)
m = folium.Map(location=[48.2100, 16.3700], zoom_start=14, tiles="CartoDB dark_matter")

# User Position
folium.Marker(
    [48.2114, 16.3783], tooltip="Du bist hier",
    icon=folium.Icon(color="white", icon="user", prefix="fa")
).add_to(m)

# Routen einzeichnen
for line, points in ROUTES.items():
    v_type = "ptMetro" if "U" in line else "ptTram"
    c = get_route_color(line, v_type)
    folium.PolyLine(points, color=c, weight=5, opacity=0.7).add_to(m)

# Fahrzeuge einzeichnen
for v in VEHICLES:
    if v["line"] in ROUTES:
        pos = get_position_on_route(ROUTES[v["line"]], v["min"])
        c = get_route_color(v["line"], v["type"])
        emoji = get_icon_emoji(v["type"])
        
        # HTML Icon (Der farbige Punkt mit Emoji)
        ac_mark = "❄️" if v["ac"] else ""
        icon_html = f"""
        <div style="
            background-color: {c}; width: 35px; height: 35px;
            border: 2px solid white; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 18px; color: white; box-shadow: 0 0 5px black;">
            {emoji}
        </div>
        """
        
        popup_txt = f"""
        <b>Linie {v['line']}</b> nach {v['to']}<br>
        in {v['min']} Min.<br>
        {v['model']} {ac_mark}
        """
        
        folium.Marker(
            pos, popup=popup_txt,
            icon=folium.DivIcon(html=icon_html, icon_size=(35,35), icon_anchor=(17,17))
        ).add_to(m)

# Karte rendern
st_folium(m, width="100%", height=500)

# Info Liste unter der Karte
st.subheader("Aktuelle Fahrzeuge im Umkreis")

for v in VEHICLES:
    c = get_route_color(v["line"], v["type"])
    ac_text = "❄️ Klimatisiert" if v["ac"] else "🌡️ Keine Klima"
    
    st.markdown(f"""
    <div style="
        border-left: 5px solid {c}; 
        background-color: #f8f9fa; 
        padding: 10px; margin-bottom: 10px; border-radius: 5px;">
        <h4 style="margin:0; color: {c};">Linie {v['line']} <span style="color:black; font-size:0.8em">➜ {v['to']}</span></h4>
        <div style="display:flex; justify-content:space-between;">
            <span><b>{v['model']}</b> ({ac_text})</span>
            <span style="font-weight:bold; font-size:1.2em;">{v['min']} min</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
