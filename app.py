import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import math

# --- 1. SETUP & CSS (Gestreifte Indikatoren) ---
st.set_page_config(page_title="Wien Öffis V12", layout="wide", page_icon="🚋")

st.markdown("""
    <style>
    .block-container { padding-top: 0rem; }
    
    /* FAHRZEUG BASIS-BOX */
    .veh-box {
        width: 38px;
        height: 24px;
        border-radius: 2px;
        border: 1px solid #fff;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.5);
        display: flex;
        justify-content: space-between; /* Platz für Text und Strich */
        align-items: center;
        font-family: sans-serif;
        font-weight: bold;
        font-size: 11px;
        color: white;
        overflow: hidden;
        padding-left: 4px;
    }

    /* DER STRICH (Indikator für Klima & Richtung) */
    .indicator-stripe {
        width: 8px;
        height: 100%;
        border-left: 1px solid rgba(0,0,0,0.2);
    }

    /* KLIMATISIERT: BLAU-WEISS GESTREIFT */
    .ac-yes {
        background: repeating-linear-gradient(
            45deg,
            #0066b3,
            #0066b3 3px,
            #ffffff 3px,
            #ffffff 6px
        );
    }

    /* NICHT KLIMATISIERT: ROT-WEISS GESTREIFT */
    .ac-no {
        background: repeating-linear-gradient(
            45deg,
            #d32f2f,
            #d32f2f 3px,
            #ffffff 3px,
            #ffffff 6px
        );
    }

    /* STATIONSPUNKT */
    .station-dot {
        width: 12px; height: 12px;
        background-color: white;
        border: 3px solid #333;
        border-radius: 50%;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🇦🇹 Wiener Linien (Full Map & AC-Check)")

# --- 2. DATEN: ROUTEN (Vollständig) & FARBEN ---

LINE_COLORS = {
    "U1": "#E2021A", "U2": "#A365A4", "U3": "#F67F21", 
    "U4": "#009641", "U5": "#F67F21", "U6": "#9D6643", 
    "1": "#FF5C5C", "2": "#FF5C5C", "D": "#FF5C5C", "71": "#FF5C5C", # Bim Rot
    "S": "#00549F", "S45": "#00549F", "S50": "#00549F", # S-Bahn Blau
    "13A": "#E3001B", "40A": "#E3001B", "59A": "#E3001B" # Bus
}

# Routenverläufe (Endstelle zu Endstelle simuliert für schöne Optik)
RAW_ROUTES = {
    # U-BAHNEN (Komplett)
    "U1": [[48.1530, 16.3850], [48.1700, 16.3800], [48.1870, 16.3750], [48.2000, 16.3700], [48.2082, 16.3738], [48.2130, 16.3780], [48.2180, 16.3900], [48.2250, 16.4000], [48.2450, 16.4400], [48.2600, 16.4500]], 
    "U2": [[48.2200, 16.5100], [48.2150, 16.4500], [48.2180, 16.4200], [48.2180, 16.3900], [48.2150, 16.3610], [48.2100, 16.3570], [48.2070, 16.3580], [48.2000, 16.3690]], 
    "U3": [[48.2110, 16.3100], [48.1960, 16.3350], [48.1950, 16.3500], [48.2082, 16.3738], [48.2060, 16.3850], [48.1900, 16.4000], [48.1750, 16.4150]], 
    "U4": [[48.2050, 16.2500], [48.1900, 16.2900], [48.1850, 16.3200], [48.1900, 16.3500], [48.2000, 16.3690], [48.2082, 16.3738], [48.2114, 16.3783], [48.2166, 16.3730], [48.2250, 16.3600], [48.2400, 16.3600]], 
    "U6": [[48.1350, 16.3200], [48.1500, 16.3300], [48.1750, 16.3350], [48.1960, 16.3350], [48.2150, 16.3400], [48.2300, 16.3500], [48.2400, 16.3800], [48.2600, 16.4000]], 
    
    # STRASSENBAHNEN (Ring & Gürtel & Kai)
    "1": [[48.2114, 16.3783], [48.2166, 16.3730], [48.2150, 16.3650], [48.2110, 16.3600], [48.2050, 16.3600], [48.2020, 16.3680], [48.2030, 16.3750], [48.2050, 16.3850], [48.2100, 16.3950]],
    "2": [[48.2250, 16.3800], [48.2114, 16.3783], [48.2080, 16.3700], [48.2050, 16.3600], [48.2080, 16.3500], [48.2100, 16.3400], [48.2200, 16.3300]],
    "D": [[48.2600, 16.3650], [48.2350, 16.3600], [48.2166, 16.3730], [48.2150, 16.3650], [48.2050, 16.3600], [48.1900, 16.3800], [48.1830, 16.3800]],
    "71": [[48.2160, 16.3690], [48.2050, 16.3600], [48.2020, 16.3680], [48.1950, 16.3900], [48.1800, 16.4100], [48.1600, 16.4400]],
    
    # S-BAHN (Stammstrecke)
    "S": [[48.2600, 16.4000], [48.2400, 16.3800], [48.2180, 16.3900], [48.2060, 16.3850], [48.1850, 16.3800], [48.1700, 16.3700], [48.1500, 16.3200]] 
}

# Wir fragen Stationen ab, die auch Bim/Bus/S-Bahn haben
STATION_MARKERS = [
    {"name": "Schwedenplatz", "lat": 48.2114, "lon": 16.3783, "lines": "U1, U4, 1, 2", "rbl": [4205, 4212, 4208, 4210]},
    {"name": "Karlsplatz", "lat": 48.2000, "lon": 16.3690, "lines": "U1, U2, U4, WLB", "rbl": [4202, 4216, 4617, 4214]},
    {"name": "Stephansplatz", "lat": 48.2082, "lon": 16.3738, "lines": "U1, U3", "rbl": [4200, 4206]},
    {"name": "Westbahnhof", "lat": 48.1960, "lon": 16.3350, "lines": "U3, U6, 5, 6, 18, S50", "rbl": [4920, 4921, 4600]},
    {"name": "Schottentor", "lat": 48.2150, "lon": 16.3610, "lines": "U2, D, 1, 71", "rbl": [4209, 4211]},
    {"name": "Landstraße", "lat": 48.2060, "lon": 16.3850, "lines": "U3, U4, O, S-Bahn", "rbl": [4204, 4213]}, # Hier verkehrt auch S-Bahn
    {"name": "Praterstern", "lat": 48.2180, "lon": 16.3900, "lines": "U1, U2, 5, O, S-Bahn", "rbl": [4207, 4105]}
]

# --- 3. HELFER ---

def smooth_path(points):
    """Macht die Linien rund"""
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
                # JETZT ALLE TYPEN ERLAUBEN (nicht nur ptMetro)
                line_name = line.get("name")
                line_type = line.get("type")
                
                departures = line.get("departures", {}).get("departure", [])
                
                for i, dep in enumerate(departures):
                    # Nur die nächsten 4 Fahrzeuge pro Linie
                    if i >= 4: break 
                    
                    countdown = dep.get("departureTime", {}).get("countdown", 99)
                    
                    # RADIUS FILTER: Alles über 12 Minuten ist weiter als ~3km weg
                    if isinstance(countdown, int) and countdown > 12: continue
                    
                    # Klimaanlage checken (foldingRamp oder barrierFree oft als Indikator für moderne Züge)
                    vehicle_info = dep.get("vehicle", {})
                    has_ac = vehicle_info.get("foldingRamp", False) or vehicle_info.get("barrierFree", False)
                    
                    vehicles.append({
                        "line": line_name,
                        "type": line_type,
                        "dest": line.get("towards"), 
                        "time": countdown,
                        "lat": slat, "lon": slon,
                        "ac": has_ac
                    })
        return vehicles
    except: return []

vehicles = fetch_all_data()
vehicles.sort(key=lambda x: x["time"] if isinstance(x["time"], int) else 99)

# --- 4. KARTE RENDERING ---

m = folium.Map(location=[48.2080, 16.3700], zoom_start=13, tiles="CartoDB positron")

# A) LINIEN (Immer Gesamte Strecke anzeigen)
for line, path in SMOOTH_ROUTES.items():
    color = LINE_COLORS.get(line, "#888") # Fallback Grau
    if "S" in line: color = LINE_COLORS["S"] # Alle S-Bahnen Blau
    
    folium.PolyLine(path, color=color, weight=4, opacity=0.4).add_to(m)

# B) STATIONEN
for s in STATION_MARKERS:
    html_dot = f"""<div class="station-dot"></div>"""
    folium.Marker([s["lat"], s["lon"]], popup=s['name'], icon=folium.DivIcon(html=html_dot, icon_size=(12,12), icon_anchor=(6,6))).add_to(m)

# C) FAHRZEUGE (Im Umkreis von ~3km / 12min)
for v in vehicles:
    pos = [v["lat"], v["lon"]]
    rot = 0
    
    # Position berechnen (Interpolation)
    route_key = v["line"]
    if "S" in route_key: route_key = "S" # Fallback für S-Bahnen auf Stammstrecke
    
    if route_key in SMOOTH_ROUTES and isinstance(v["time"], int):
        path = SMOOTH_ROUTES[route_key]
        idx = min(v["time"] * 3, len(path)-2) 
        idx = max(0, int(idx))
        pos = path[idx]
        rot = calculate_bearing(path[idx], path[idx+1])
    
    # Farbe & Style
    l_color = LINE_COLORS.get(v["line"], "#333")
    if "S" in v["line"]: l_color = LINE_COLORS["S"]
    if "A" in v["line"]: l_color = LINE_COLORS["13A"] # Busse Rot

    # Klima-Strich Logik (Blau/Weiß oder Rot/Weiß)
    stripe_class = "ac-yes" if v["ac"] else "ac-no"
    ac_text = "Klimatisiert" if v["ac"] else "Nicht Klimatisiert"

    # HTML BOX mit Rotation und seitlichem Strich
    # Wir rotieren das Ganze, der Strich ist rechts (in Fahrtrichtung)
    icon_html = f"""
    <div style="transform: rotate({rot-90}deg);">
        <div class="veh-box" style="background-color: {l_color};">
            <span style="margin-right:2px;">{v['line']}</span>
            <div class="indicator-stripe {stripe_class}"></div>
        </div>
    </div>
    """
    
    folium.Marker(
        pos, 
        popup=f"<b>{v['line']}</b> nach {v['dest']}<br>{ac_text} (Indikator)<br>in {v['time']} min",
        icon=folium.DivIcon(html=icon_html, icon_size=(38,24), icon_anchor=(19,12))
    ).add_to(m)

st_folium(m, width="100%", height=600, returned_objects=[])

# --- 5. LEGENDE ---
st.subheader("Fahrzeuge in der Nähe (< 3km)")
st.info("ℹ️ Der gestreifte Balken am Fahrzeug zeigt die Ausstattung: **Blau/Weiß** = Klimatisiert/Niederflur, **Rot/Weiß** = Altbau/Keine Klima.")

cols = st.columns(3)
for i, v in enumerate(vehicles[:15]): # Max 15 anzeigen in Liste
    with cols[i % 3]:
        clr = LINE_COLORS.get(v["line"], "#333")
        if "S" in v["line"]: clr = LINE_COLORS["S"]
        icon = "❄️" if v["ac"] else "🔥"
        st.markdown(f"**<span style='color:{clr}'>{v['line']}</span>** {icon} ➜ {v['dest']} ({v['time']} min)", unsafe_allow_html=True)
