import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import math

# --- 1. SETUP ---
st.set_page_config(page_title="Wien Öffis Master", layout="wide", page_icon="🚋")

st.markdown("""
    <style>
    .block-container { padding-top: 0rem; }
    
    /* HALTESTELLEN SCHILD (Oval) - Funktioniert zuverlässig via CSS */
    .station-sign {
        width: 36px; height: 26px;
        background-color: #fdf5e6; /* Beige */
        border: 3px solid #b22222; /* Dunkelrot */
        border-radius: 50%; /* Oval */
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        box-shadow: 0 3px 6px rgba(0,0,0,0.4);
    }
    .sign-stripe { width: 20px; height: 2px; background: black; margin: 2px 0; }
    .sign-logo {
        width: 8px; height: 10px; background: #d32f2f;
        border-radius: 0 0 4px 4px; border-top: 2px solid white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🇦🇹 Wiener Linien Live-Map (V9)")

# --- 2. BILDER DATENBANK (BASE64) ---
# Hier fügst du später deine ECHTEN Bild-Codes ein.
# Ich habe hier Platzhalter generiert (Pixel-Art Balken), damit du siehst, dass es klappt.

ICONS = {
    # ROT-WEISS (Straßenbahn Old / ULF)
    "tram_red": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAFAAQCAYAAAB44qeNAAAAZ0lEQVRIS+3SwQmAQBBE0d1A7Eyw/yZsxBIEsQYxM0hwF3wM/znM7sA250yuqro552V/uO2xfa6qI6W0d61133Zfa71TSlvn3O4xxtq11rv3fubc7lE84ogoHhHF4/fI/xHFI46I4hHFAw41FwIJj3e1AAAAAElFTkSuQmCC",
    
    # SILBER (Silberpfeil)
    "metro_silver": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAFAAQCAYAAAB44qeNAAAAXUlEQVRIS+3SwQmAMBAE0U0h9iZYfxO2YwmCWIN4M0hwwZfwM4fZHdjmnMlVVbfMvO0Pt+19n6tqSimtXWvdt93XWu+U0tY5t3uMsXat9e69n5lzu0fxiCOieEQUj98j/0cUjzgijke8APbYFAJ054B6AAAAAElFTkSuQmCC",
    
    # ROT-SILBER (V-Wagen)
    "metro_v": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAFAAQCAYAAAB44qeNAAAAaUlEQVRIS+3SwQmAMBBE0d1A7Eyw/yZsxBIEsQbxZpDggov4m8PsDmxlzvmqqltm3vaH2x7b56o6Ukpr11r3bfe11jultHXOmX2MMXat9e69n5l9j+IRR0TxiCgev0f+jygccUQUjygccQAu5xcCNy296wAAAABJRU5ErkJggg==",
    
    # OCKER (U6)
    "metro_u6": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAFAAQCAYAAAB44qeNAAAAY0lEQVRIS+3SwQmAMBBE0d1A7Eyw/yZsxBIEsQbxZpDggr/gZw6zO7DNOZOrqm6Zedofbtv7PufVfQ4ppdl737fd11rvlNLWObd7jLF2rfXuvZ+Zc7tH8YgjoniE8fA98n9E8Ygj4gU2tRcCU43zugAAAABJRU5ErkJggg==",
    
    # BLAU (S-Bahn)
    "sbahn": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAFAAQCAYAAAB44qeNAAAAZklEQVRIS+3SwQmAMBBE0d1A7Eyw/yZsxBIEsQbxZpDggr/gZw6zO7DNOZOrqm6Zedofbtv7PufVfQ4ppdl737fd11rvlNLWObd7jLF2rfXuvZ+Zc7tH8YgjoniE8fA98n9E8Ygj4gUIJxcC/Kqf4wAAAABJRU5ErkJggg==",
    
    # BUS
    "bus": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAQCAYAAAB3AH1ZAAAAVklEQVRIS+3SwQmAMBBE0d1A7Eyw/yZsxBIEsQbxZpDggov4m8PsDmxzzuSqqltm3vaH2x7b56o6Ukpr11r3bfe11jultHXOmX2M4hFHRPGIIx6/R/6PKA78FwI3q9x7AAAAAElFTkSuQmCC"
}

# --- 3. GEORDNETE ROUTEN (Gegen das Spinnennetz) ---
# WICHTIG: Die Punkte müssen der Reihe nach liegen, nicht durcheinander.

RAW_ROUTES = {
    # U1: Reumannplatz -> Leopoldau (Grob)
    "U1": [[48.1730, 16.3780], [48.1860, 16.3750], [48.2000, 16.3700], [48.2082, 16.3738], [48.2130, 16.3780], [48.2180, 16.3900], [48.2450, 16.4400]], 
    # U2: Schottentor -> Aspern (Grob)
    "U2": [[48.2150, 16.3610], [48.2180, 16.3900], [48.2180, 16.4200], [48.2250, 16.5000]], 
    # U3: Westbahnhof -> Simmering (Grob)
    "U3": [[48.1960, 16.3350], [48.2000, 16.3550], [48.2082, 16.3738], [48.2060, 16.3850], [48.1750, 16.4150]], 
    # U4: Heiligenstadt -> Hütteldorf (Grob)
    "U4": [[48.2400, 16.3600], [48.2250, 16.3600], [48.2166, 16.3730], [48.2114, 16.3783], [48.2000, 16.3690], [48.1900, 16.3500], [48.1900, 16.2900]], 
    # U6: Floridsdorf -> Siebenhirten
    "U6": [[48.2600, 16.4000], [48.2400, 16.3800], [48.2150, 16.3400], [48.1960, 16.3350], [48.1750, 16.3350], [48.1350, 16.3200]], 
    # Ring-Linie (Rundkurs)
    "1": [[48.2114, 16.3783], [48.2166, 16.3730], [48.2150, 16.3650], [48.2110, 16.3600], [48.2050, 16.3600], [48.2020, 16.3680], [48.2030, 16.3750]]
}

STATION_MARKERS = [
    {"name": "Schwedenplatz", "lat": 48.2114, "lon": 16.3783, "lines": "U1, U4, 1, 2", "rbl": [4205, 4212, 4208, 4210]},
    {"name": "Karlsplatz", "lat": 48.2000, "lon": 16.3690, "lines": "U1, U2, U4, WLB", "rbl": [4202, 4216, 4617, 4214]},
    {"name": "Stephansplatz", "lat": 48.2082, "lon": 16.3738, "lines": "U1, U3", "rbl": [4200, 4206]},
    {"name": "Westbahnhof", "lat": 48.1960, "lon": 16.3350, "lines": "U3, U6, 5, 6, 18", "rbl": [4920, 4921, 4600]},
    {"name": "Schottentor", "lat": 48.2150, "lon": 16.3610, "lines": "U2, D, 1, 71", "rbl": [4209, 4211]},
    {"name": "Landstraße", "lat": 48.2060, "lon": 16.3850, "lines": "U3, U4, O", "rbl": [4204, 4213]},
    {"name": "Praterstern", "lat": 48.2180, "lon": 16.3900, "lines": "U1, U2, 5, O", "rbl": [4207, 4105]}
]

LINE_COLORS = {
    "U1": "#E2021A", "U2": "#A365A4", "U3": "#F67F21", "U4": "#009641", "U5": "#F67F21", "U6": "#9D6643", 
    "1": "#FF5C5C", "2": "#FF5C5C", "D": "#FF5C5C", "71": "#FF5C5C"
}

# --- 4. FUNKTIONEN ---

def smooth_path(points):
    if len(points) < 2: return points
    smoothed = []
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i+1]
        steps = 10 # Viele Schritte für runde Kurven
        for j in range(steps):
            f = j / steps
            smoothed.append([p1[0]*(1-f)+p2[0]*f, p1[1]*(1-f)+p2[1]*f])
    smoothed.append(points[-1])
    return smoothed

SMOOTH_ROUTES = {k: smooth_path(v) for k,v in RAW_ROUTES.items()}

def get_icon_base64(line, v_type, features):
    # Logik: Welches Bild für welches Fahrzeug?
    
    # 1. U6 ist speziell
    if line == "U6": return ICONS["metro_u6"]
    
    # 2. Andere U-Bahnen
    if "ptMetro" in v_type or "U" in line:
        # Hat es Rampe? -> V-Wagen (Neuer)
        if features.get("foldingRamp") or features.get("barrierFree"): 
            return ICONS["metro_v"]
        return ICONS["metro_silver"] # Silberpfeil
        
    # 3. Straßenbahn
    if "ptTram" in v_type:
        return ICONS["tram_red"]
        
    # 4. Bus
    if "ptBus" in v_type:
        return ICONS["bus"]
        
    return ICONS["sbahn"] # Fallback

def calculate_bearing(p1, p2):
    lat1, lat2 = math.radians(p1[0]), math.radians(p2[0])
    dLon = math.radians(p2[1] - p1[1])
    x = math.sin(dLon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dLon))
    return (math.degrees(math.atan2(x, y)) + 360) % 360

@st.cache_data(ttl=12)
def fetch_all_data():
    all_rbls = []
    for s in STATION_MARKERS: all_rbls.extend(s["rbl"])
    url = f"https://www.wienerlinien.at/ogd_realtime/monitor?rbl={'&rbl='.join(map(str, all_rbls))}"
    
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        vehicles = []
        for mon in data.get("data", {}).get("monitors", []):
            slat = mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [0,0])[1]
            slon = mon.get("locationStop", {}).get("geometry", {}).get("coordinates", [0,0])[0]
            for line in mon.get("lines", []):
                for dep in line.get("departures", {}).get("departure", []):
                    countdown = dep.get("departureTime", {}).get("countdown", 99)
                    
                    # Fehlerbehebung: Prüfen ob countdown eine Zahl ist
                    if isinstance(countdown, int) and countdown > 30: 
                        continue
                    
                    vehicles.append({
                        "line": line.get("name"), "type": line.get("type"),
                        "dest": line.get("towards"), "time": countdown,
                        "features": dep.get("vehicle", {}),
                        "lat": slat, "lon": slon
                    })
        return vehicles
    except: return []

vehicles = fetch_all_data()
vehicles.sort(key=lambda x: x["time"] if isinstance(x["time"], int) else 99, reverse=True)

# --- 5. KARTE ---
m = folium.Map(location=[48.2080, 16.3700], zoom_start=13, tiles="CartoDB positron")

# Linien zeichnen
for line, path in SMOOTH_ROUTES.items():
    color = LINE_COLORS.get(line, "#888")
    folium.PolyLine(path, color=color, weight=4, opacity=0.6, line_cap='round').add_to(m)

# Stationen Schilder
for s in STATION_MARKERS:
    html_sign = f"""<div class="station-sign"><div class="sign-stripe"></div><div class="sign-logo"></div><div class="sign-stripe"></div></div>"""
    folium.Marker([s["lat"], s["lon"]], popup=s['name'], icon=folium.DivIcon(html=html_sign, icon_size=(36,26), icon_anchor=(18,13))).add_to(m)

# Fahrzeuge
for v in vehicles:
    pos = [v["lat"], v["lon"]]
    rot = 0
    # Interpolation
    if v["line"] in SMOOTH_ROUTES and isinstance(v["time"], int) and v["time"] < 25:
        path = SMOOTH_ROUTES[v["line"]]
        idx = min(v["time"] * 3, len(path)-2) 
        idx = max(0, int(idx))
        pos = path[idx]
        rot = calculate_bearing(path[idx], path[idx+1])
    
    # BILD HOLEN (Base64)
    icon_b64 = get_icon_base64(v["line"], v["type"], v["features"])
    
    # HTML IMG TAG mit Rotation
    # width/height anpassen je nach deinem Bildformat (hier ca 50x20)
    icon_html = f"""
    <div style="transform: rotate({rot-90}deg); transition: transform 1s;">
        <img src="{icon_b64}" style="width: 50px; height: 20px; filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.5));">
        <div style="position:absolute; top:-10px; left:15px; font-weight:bold; font-size:10px; color:black; background:white; padding:0 2px;">{v['line']}</div>
    </div>
    """
    
    folium.Marker(pos, popup=f"{v['line']} nach {v['dest']}", icon=folium.DivIcon(html=icon_html, icon_size=(50,20), icon_anchor=(25,10))).add_to(m)

st_folium(m, width="100%", height=600, returned_objects=[])

# --- LISTE ---
st.subheader("Aktuelle Verkehrslage")
vehicles.sort(key=lambda x: x["time"] if isinstance(x["time"], int) else 99)
cols = st.columns(3)
for i, v in enumerate(vehicles):
    with cols[i % 3]:
        st.info(f"**{v['line']}** ➜ {v['dest']} ({v['time']} min)")
