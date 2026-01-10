import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import math

# --- 1. KONFIGURATION & CSS (PIXEL ART STYLE) ---
st.set_page_config(page_title="Wien Öffis V8", layout="wide", page_icon="🚋")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    
    /* BASIS ZUG KÖRPER */
    .train-body {
        width: 44px; height: 24px;
        border: 2px solid #333;
        border-radius: 4px;
        display: flex; flex-direction: column;
        justify-content: space-between;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.4);
        font-family: sans-serif; font-weight: bold; font-size: 9px;
        overflow: hidden;
    }
    
    /* FENSTERBAND (Damit es wie ein Zug aussieht) */
    .windows {
        height: 8px; width: 100%;
        background: #333;
        margin-top: 4px;
        opacity: 0.8;
    }
    
    /* FAHRZEUG TYPEN (Farben gemäß deinem Bild) */
    
    /* Silberpfeil (Type U): Grau */
    .type-u { 
        background: linear-gradient(180deg, #d0d0d0 0%, #a0a0a0 100%); 
        color: black; 
    }
    
    /* V-Wagen: Silber mit roten Türen/Akzenten */
    .type-v { 
        background: linear-gradient(90deg, #e0e0e0 0%, #e0e0e0 20%, #d32f2f 20%, #d32f2f 30%, #e0e0e0 30%, #e0e0e0 70%, #d32f2f 70%, #d32f2f 80%, #e0e0e0 80%);
        color: black; 
    }
    
    /* Straßenbahn (E2): Rot-Weiß */
    .type-bim-old {
        background: linear-gradient(180deg, #d32f2f 50%, #ffffff 50%);
        color: white; 
    }
    
    /* ULF/Flexity: Modernes Rot/Grau */
    .type-ulf {
        background: linear-gradient(90deg, #b71c1c 0%, #b71c1c 10%, #dddddd 10%, #dddddd 90%, #b71c1c 90%);
        color: black; border-radius: 6px;
    }
    
    /* S-Bahn: Blau/Weiß */
    .type-sbahn {
        background: linear-gradient(180deg, #00549F 50%, #ffffff 50%);
        color: white;
    }

    /* Label im Fahrzeug (Liniennummer) */
    .veh-label {
        text-align: center; width: 100%; margin-top: -2px; z-index: 2;
        text-shadow: 0 0 2px white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🇦🇹 Wiener Linien Live-Map (Detail-Ansicht)")

# --- 2. FARBEN & ROUTEN DEFINITION ---

# Offizielle Linienfarben (Für die Strecke am Boden)
LINE_COLORS = {
    "U1": "#E2021A", "U2": "#A365A4", "U3": "#F67F21", 
    "U4": "#009641", "U5": "#F67F21", "U6": "#9D6643",
    "1": "#FF5C5C", "2": "#FF5C5C", "D": "#FF5C5C", "71": "#FF5C5C", # Bim Hellrot
    "S": "#00549F"
}

# Koordinaten (Simulation der Strecken)
# HINWEIS: Um ALLE Linien in ganz Wien zu haben, bräuchten wir externe Dateien.
# Ich habe hier die U2 ergänzt, damit sie sichtbar wird.
RAW_ROUTES = {
    "1": [ # Ring
        [48.2114, 16.3783], [48.2130, 16.3760], [48.2166, 16.3730], 
        [48.2160, 16.3690], [48.2150, 16.3650], [48.2110, 16.3600], 
        [48.2050, 16.3600], [48.2020, 16.3680], [48.2030, 16.3750]
    ],
    "U4": [ # Donaukanal
        [48.2250, 16.3600], [48.2180, 16.3650], [48.2166, 16.3730], 
        [48.2114, 16.3783], [48.2082, 16.3738], [48.2000, 16.3600], 
        [48.1900, 16.3500] 
    ],
    "U2": [ # Schottentor -> Karlsplatz (Simulation)
        [48.2150, 16.3610], # Schottentor
        [48.2100, 16.3570], # Rathaus
        [48.2070, 16.3580], # Volkstheater
        [48.2020, 16.3610], # Museumsquartier
        [48.2000, 16.3690]  # Karlsplatz
    ]
}

STATIONS = {
    "Zentrum (Schwedenpl/Stephanspl)": [4205, 4212, 4208, 4210, 4200, 4206],
    "Karlsplatz (U1, U2, U4)": [4202, 4216, 4617],
    "Schottentor (U2, Tram)": [4209, 4211] # Ergänzt für U2
}

# --- 3. HELFER: KURVEN & OPTIK ---

def smooth_path(points):
    """Macht eckige Pfade rund"""
    if len(points) < 2: return points
    smoothed = []
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i+1]
        steps = 6 # Mehr Schritte = runder
        for j in range(steps):
            f = j / steps
            smoothed.append([
                p1[0] * (1-f) + p2[0] * f,
                p1[1] * (1-f) + p2[1] * f
            ])
    smoothed.append(points[-1])
    return smoothed

SMOOTH_ROUTES = {k: smooth_path(v) for k,v in RAW_ROUTES.items()}

def get_css_class(line, v_type, features):
    """Wählt das Design passend zum Fahrzeug"""
    # U-BAHN
    if "ptMetro" in v_type or "U" in line:
        if line == "U6": return "type-u" # U6 (Typ T) sieht ähnlich aus wie Silberpfeil hier
        # Wenn Barrierefrei/Rampe -> Vermutlich V-Wagen (Neuer)
        if features.get("foldingRamp") or features.get("barrierFree"): return "type-v"
        return "type-u" # Silberpfeil
    
    # STRASSENBAHN
    if "ptTram" in v_type:
        if features.get("foldingRamp"): return "type-ulf"
        return "type-bim-old"
    
    # S-BAHN
    if "S" in line: return "type-sbahn"
    
    return "type-ulf" # Fallback

def get_line_color(line):
    # Farbe aus Dictionary holen oder Fallback
    if line in LINE_COLORS: return LINE_COLORS[line]
    if "S" in line: return LINE_COLORS["S"]
    return "#888888"

def calculate_bearing(p1, p2):
    lat1, lat2 = math.radians(p1[0]), math.radians(p2[0])
    dLon = math.radians(p2[1] - p1[1])
    x = math.sin(dLon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dLon))
    return (math.degrees(math.atan2(x, y)) + 360) % 360

# --- 4. API & LOGIK ---

@st.cache_data(ttl=10)
def fetch_data(rbls):
    url = f"https://www.wienerlinien.at/ogd_realtime/monitor?rbl={'&rbl='.join(map(str, rbls))}"
    try:
        data = requests.get(url, timeout=5).json()
        vehicles = []
        for mon in data.get("data", {}).get("monitors", []):
            slat = mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [0,0])[1]
            slon = mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [0,0])[0]
            for line in mon.get("lines", []):
                for dep in line.get("departures", {}).get("departure", []):
                    countdown = dep.get("departureTime", {}).get("countdown", 99)
                    if countdown > 25: continue
                    vehicles.append({
                        "line": line.get("name"), "type": line.get("type"),
                        "dest": line.get("towards"), "time": countdown,
                        "features": dep.get("vehicle", {}),
                        "lat": slat, "lon": slon
                    })
        return vehicles
    except: return []

# Daten laden
all_rbl = [id for ids in STATIONS.values() for id in ids]
vehicles = fetch_data(all_rbl)
vehicles.sort(key=lambda x: x["time"], reverse=True) # Sortieren für Z-Index

# --- 5. KARTE ZEICHNEN ---

m = folium.Map(location=[48.2080, 16.3700], zoom_start=14, tiles="CartoDB positron")

# A) LINIEN NETZ (Boden)
for line, path in SMOOTH_ROUTES.items():
    color = get_line_color(line)
    folium.PolyLine(path, color=color, weight=6, opacity=0.4, line_cap='round').add_to(m)

# B) FAHRZEUGE
for v in vehicles:
    # Position berechnen
    pos = [v["lat"], v["lon"]]
    rot = 0
    
    # Haben wir eine Route für diese Linie? (z.B. U2, U4, 1)
    if v["line"] in SMOOTH_ROUTES and v["time"] < 20:
        path = SMOOTH_ROUTES[v["line"]]
        # Index auf Route basierend auf Zeit
        idx = min(v["time"] * 4, len(path)-2) # *4 wegen geglätteter Punkte
        idx = max(0, int(idx))
        pos = path[idx]
        rot = calculate_bearing(path[idx], path[idx+1])
    
    # Design ermitteln
    css_class = get_css_class(v["line"], v["type"], v["features"])
    line_col = get_line_color(v["line"])
    
    # HTML ZUG ICON
    # Wir fügen einen farbigen Rahmen in der Linienfarbe hinzu (border-color)
    icon_html = f"""
    <div style="transform: rotate({rot-90}deg);">
        <div class="train-body {css_class}" style="border-color: {line_col};">
            <div class="windows"></div>
            <div class="veh-label">{v['line']}</div>
        </div>
    </div>
    """
    
    popup = f"<b>{v['line']}</b> ➤ {v['dest']}<br>in {v['time']} min"
    folium.Marker(pos, popup=popup, 
                  icon=folium.DivIcon(html=icon_html, icon_size=(44,24), icon_anchor=(22,12))).add_to(m)

st_folium(m, width="100%", height=500, returned_objects=[])

# --- 6. INFO LISTE ---
vehicles.sort(key=lambda x: x["time"])
st.subheader("Fahrzeuge in Echtzeit")

for v in vehicles:
    col = get_line_color(v["line"])
    type_name = "U-Bahn" if "ptMetro" in v["type"] else "Bim/Bus"
    ac = "❄️" if v["features"].get("foldingRamp") else "🌡️"
    
    st.markdown(f"""
    <div style="border-left: 6px solid {col}; background: white; padding: 12px; margin-bottom: 6px; box-shadow: 0 1px 3px #eee; display:flex; justify-content:space-between; align-items:center;">
        <div>
            <strong style="font-size:1.2em; color:{col}">{v['line']}</strong> 
            <span style="color:#555;">➜ {v['dest']}</span><br>
            <small>{type_name} | {ac}</small>
        </div>
        <div style="font-size:1.4em; font-weight:bold;">{v['time']} <small style="font-size:0.5em">min</small></div>
    </div>
    """, unsafe_allow_html=True)
