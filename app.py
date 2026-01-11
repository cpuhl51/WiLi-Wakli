import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import math

# --- 1. SETUP & CSS ---
st.set_page_config(page_title="Wien Öffis V13", layout="wide", page_icon="🚋")

st.markdown("""
    <style>
    .block-container { padding-top: 0rem; }
    
    /* FAHRZEUG BOX */
    .veh-box {
        width: 40px;
        height: 22px;
        border: 1px solid white;
        box-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center; /* Text zentriert, Strich ist absolut */
        font-family: sans-serif;
        font-weight: bold;
        font-size: 11px;
        color: white;
        position: relative; /* Wichtig für den Strich */
        overflow: hidden;
        border-radius: 2px;
    }

    /* DER STRICH (Indikator) - Absolut rechts positioniert */
    .indicator-stripe {
        position: absolute;
        top: 0;
        bottom: 0;
        right: 0; /* Immer rechts (Vorne) */
        width: 8px;
        border-left: 1px solid rgba(0,0,0,0.3);
        z-index: 2;
    }

    /* TEXT (Liniennummer) */
    .veh-text {
        z-index: 1;
        padding-right: 6px; /* Damit der Text nicht unterm Strich liegt */
    }

    /* KLIMATISIERT: BLAU-WEISS */
    .ac-yes {
        background: repeating-linear-gradient(
            -45deg,
            #0066b3,
            #0066b3 4px,
            #ffffff 4px,
            #ffffff 8px
        );
    }

    /* NICHT KLIMATISIERT: ROT-WEISS */
    .ac-no {
        background: repeating-linear-gradient(
            -45deg,
            #d32f2f,
            #d32f2f 4px,
            #ffffff 4px,
            #ffffff 8px
        );
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO & DATEN ---

# Dein Base64 Logo für Stationen
ICON_STATION_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAASCAIAAADDkPmOAAAAB3RJTUUH6gELBx0FGyOy4wAABC5JREFUeJx9VG1olWUYvu7nft6zs842j2eamlrLyPxi1I+prbQQRZEs+mMSlKmRSPaxSowUER1G0AcqSFqWLaOkREylKNO1GCgUpInkV5qVMtvmPDtne897nue++3GOZ5tgF+/P57me+74+XlJVlKAKIlWF92StO30227DSHTkKtlAlQI2BCAFg1jDUKCp/5cXyhuWUHAQiEKEfzI283kNB1ub27EvPmpc/eJg4IChEUBbj+2rhHJgl3U2pVOUXTYnGNVSdAjMZQwPRj5pInQMzxGffWNv95CJNp01qMFQAUu9RWRmbOUNVNZezU+uqDuyOPTpXMhn09iIMtfTlnXR1SXfG3iCC/+N8ZtnL+R+aTXUKAJwDEUDkvEkNttPqyVqIaOfVzKKlmu0ha0tbgwiGpb2Daycm3nnTFkUgImtze/dnX1ohbVfMrUPhXOFVADCkLm9GjbS1kyiZ1I4OufAnvMAY4LpVzHBOutNlC+Yn3nvLDB9m1XtiVpHsmvW9726meNxUp+A8TD+trIUqjxtrysvNmBrf1kZVVVApjQs2ms4gFqvYsql82bMKQMSCOX/st+zzDfnWZpNIIQy1pwcDoaoaRXZaPVSDB+6Pvt/PCojvMynMce2kivc3BlPqihoYY/MtrbmPm2Bt2ePz4R0UoiqipSApQNYGM6bHHp6uqvHlS10m438/AxUq8OYivuvOROMaU51yuQiWoTCiJL29FI+XBvQA46ZQVRoY3v8BqaqqkqoCzvsgCC5cal+3dd/VbEhsAFVFwvJDdfcseexBAD290abPDx4/dynnhajgIqkKGVPwnNl0dabvnVBjVZUADxAQBMHXLcefW9/U9tcVBBaloio+2/3T6BFDZk8Zv/HL5tXrPkUyAdEb5zQGIkhnp8+ZvHhevSUi74XZKLBqy94NH+wHm2Bosv8PgNnk29PfHT05Z+qEb4+c5FQlV97iB1ArW456cpbQuGLByoWzAVjnxbI5+/e/S9Z90tJ8DMkKEPJh1HdL1FkG04lzl6O8O33ximf27no8VEHEbKL29O01w7avfWZm3TjvhQiWCId+PrVsw87zlzuqx4xwXvqaoupFKxPxnjC6FuYutnUeO/NPe1c3LBfPqJIxquI704/Mrtu2+ukR1VV55y0bIrJszLia4c1bX43HY95L34aqXnRQRXnLr2eWNu68ZkxHOnvol1MSOQS2cIIt+54cEda/9sSqxXNRCIItRsyq4rYhg24WoA/3tja8vSuTDVEWpDPhgdYTKMaCQOSvZkbfMWz72oWzJo/3IgSyzKWAFsOnCpQ6ogrV9mvZ1zfv2bHrMCriZK2KAMRM3guICCDn59RP3Lb6qZFDkyUR+tHAAiDq60HhGWNM40ff7Pjqx9FjR+WdqAio5BmISMJo4t0jD2x8AUAY5eOxoFiTfhv/B/5aRhM1eYuUAAAAAElFTkSuQmCC"

# Simulierte User Position (z.B. Nähe Stephansplatz, aber nicht genau drin)
# Ändere diese Koordinaten, um "in der Station" zu testen (z.B. auf 48.2082, 16.3738 setzen)
USER_LAT = 48.2090
USER_LON = 16.3720

LINE_COLORS = {
    "U1": "#E2021A", "U2": "#A365A4", "U3": "#F67F21", "U4": "#009641", "U5": "#F67F21", "U6": "#9D6643", 
    "1": "#FF5C5C", "2": "#FF5C5C", "D": "#FF5C5C", "71": "#FF5C5C",
    "S": "#00549F", "13A": "#E3001B", "40A": "#E3001B", "59A": "#E3001B"
}

RAW_ROUTES = {
    "U1": [[48.1530, 16.3850], [48.1700, 16.3800], [48.1870, 16.3750], [48.2000, 16.3700], [48.2082, 16.3738], [48.2130, 16.3780], [48.2180, 16.3900], [48.2250, 16.4000], [48.2450, 16.4400], [48.2600, 16.4500]], 
    "U2": [[48.2200, 16.5100], [48.2150, 16.4500], [48.2180, 16.4200], [48.2180, 16.3900], [48.2150, 16.3610], [48.2100, 16.3570], [48.2070, 16.3580], [48.2000, 16.3690]], 
    "U3": [[48.2110, 16.3100], [48.1960, 16.3350], [48.1950, 16.3500], [48.2082, 16.3738], [48.2060, 16.3850], [48.1900, 16.4000], [48.1750, 16.4150]], 
    "U4": [[48.2050, 16.2500], [48.1900, 16.2900], [48.1850, 16.3200], [48.1900, 16.3500], [48.2000, 16.3690], [48.2082, 16.3738], [48.2114, 16.3783], [48.2166, 16.3730], [48.2250, 16.3600], [48.2400, 16.3600]], 
    "U6": [[48.1350, 16.3200], [48.1500, 16.3300], [48.1750, 16.3350], [48.1960, 16.3350], [48.2150, 16.3400], [48.2300, 16.3500], [48.2400, 16.3800], [48.2600, 16.4000]], 
    "1": [[48.2114, 16.3783], [48.2166, 16.3730], [48.2150, 16.3650], [48.2110, 16.3600], [48.2050, 16.3600], [48.2020, 16.3680], [48.2030, 16.3750], [48.2050, 16.3850], [48.2100, 16.3950]],
    "2": [[48.2250, 16.3800], [48.2114, 16.3783], [48.2080, 16.3700], [48.2050, 16.3600], [48.2080, 16.3500], [48.2100, 16.3400], [48.2200, 16.3300]],
    "D": [[48.2600, 16.3650], [48.2350, 16.3600], [48.2166, 16.3730], [48.2150, 16.3650], [48.2050, 16.3600], [48.1900, 16.3800], [48.1830, 16.3800]],
    "71": [[48.2160, 16.3690], [48.2050, 16.3600], [48.2020, 16.3680], [48.1950, 16.3900], [48.1800, 16.4100], [48.1600, 16.4400]],
    "S": [[48.2600, 16.4000], [48.2400, 16.3800], [48.2180, 16.3900], [48.2060, 16.3850], [48.1850, 16.3800], [48.1700, 16.3700], [48.1500, 16.3200]] 
}

STATION_MARKERS = [
    {"name": "Schwedenplatz", "lat": 48.2114, "lon": 16.3783, "rbl": [4205, 4212, 4208, 4210]},
    {"name": "Karlsplatz", "lat": 48.2000, "lon": 16.3690, "rbl": [4202, 4216, 4617, 4214]},
    {"name": "Stephansplatz", "lat": 48.2082, "lon": 16.3738, "rbl": [4200, 4206]},
    {"name": "Westbahnhof", "lat": 48.1960, "lon": 16.3350, "rbl": [4920, 4921, 4600]},
    {"name": "Schottentor", "lat": 48.2150, "lon": 16.3610, "rbl": [4209, 4211]},
    {"name": "Landstraße", "lat": 48.2060, "lon": 16.3850, "rbl": [4204, 4213]},
    {"name": "Praterstern", "lat": 48.2180, "lon": 16.3900, "rbl": [4207, 4105]}
]

# --- 3. HELPER & DISTANZ ---

def smooth_path(points):
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

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000 # Radius Erde in Metern
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c # Distanz in Metern

# --- 4. POSITION CHECK ---
# Wir prüfen, wo der User ist
closest_station = None
min_dist = 999999
stations_with_dist = []

for s in STATION_MARKERS:
    dist = haversine(USER_LAT, USER_LON, s["lat"], s["lon"])
    stations_with_dist.append({**s, "dist": dist})
    if dist < min_dist:
        min_dist = dist
        closest_station = s

# Sortieren nach Nähe
stations_with_dist.sort(key=lambda x: x["dist"])

# --- HEADER LOGIK (Im/Vor der Station) ---
if min_dist < 100:
    st.success(f"📍 **Du befindest Dich in der Station {closest_station['name']}**")
else:
    st.info(f"🚶 Du bist unterwegs. Nächste Station: **{closest_station['name']}** ({int(min_dist)}m)")
    # Kleine Liste der nächsten Stationen
    near_str = " | ".join([f"{s['name']} ({int(s['dist'])}m)" for s in stations_with_dist[:3]])
    st.caption(f"Nahegelegene Stationen: {near_str}")


# --- 5. API DATEN ---
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
                line_name = line.get("name")
                departures = line.get("departures", {}).get("departure", [])
                
                for i, dep in enumerate(departures):
                    if i >= 4: break 
                    countdown = dep.get("departureTime", {}).get("countdown", 99)
                    if isinstance(countdown, int) and countdown > 12: continue
                    
                    vehicle_info = dep.get("vehicle", {})
                    has_ac = vehicle_info.get("foldingRamp", False) or vehicle_info.get("barrierFree", False)
                    
                    vehicles.append({
                        "line": line_name,
                        "dest": line.get("towards"), 
                        "time": countdown,
                        "lat": slat, "lon": slon,
                        "ac": has_ac
                    })
        return vehicles
    except: return []

vehicles = fetch_all_data()
vehicles.sort(key=lambda x: x["time"] if isinstance(x["time"], int) else 99)

# --- 6. KARTE ---
m = folium.Map(location=[USER_LAT, USER_LON], zoom_start=14, tiles="CartoDB positron")

# User Position Marker
folium.Marker(
    [USER_LAT, USER_LON],
    tooltip="Deine Position",
    icon=folium.Icon(color="blue", icon="user", prefix="fa")
).add_to(m)

# Linien
for line, path in SMOOTH_ROUTES.items():
    color = LINE_COLORS.get(line, "#888")
    if "S" in line: color = LINE_COLORS["S"]
    folium.PolyLine(path, color=color, weight=4, opacity=0.4).add_to(m)

# Stationen (Dein Logo)
for s in STATION_MARKERS:
    # Custom Icon via Base64
    icon = folium.CustomIcon(
        ICON_STATION_B64,
        icon_size=(30, 18), # Größe angepasst an das Logo-Format (ca 30x18px)
        icon_anchor=(15, 9)
    )
    folium.Marker([s["lat"], s["lon"]], popup=s['name'], icon=icon).add_to(m)

# Fahrzeuge
for v in vehicles:
    pos = [v["lat"], v["lon"]]
    rot = 0
    
    route_key = v["line"]
    if "S" in route_key: route_key = "S"
    
    if route_key in SMOOTH_ROUTES and isinstance(v["time"], int):
        path = SMOOTH_ROUTES[route_key]
        idx = min(v["time"] * 3, len(path)-2) 
        idx = max(0, int(idx))
        pos = path[idx]
        rot = calculate_bearing(path[idx], path[idx+1])
    
    l_color = LINE_COLORS.get(v["line"], "#333")
    if "S" in v["line"]: l_color = LINE_COLORS["S"]
    if "A" in v["line"]: l_color = LINE_COLORS["13A"]

    stripe_class = "ac-yes" if v["ac"] else "ac-no"
    
    # Rotation -90 weil HTML Box horizontal ist, 0 Grad aber Norden
    icon_html = f"""
    <div style="transform: rotate({rot-90}deg);">
        <div class="veh-box" style="background-color: {l_color};">
            <span class="veh-text">{v['line']}</span>
            <div class="indicator-stripe {stripe_class}"></div>
        </div>
    </div>
    """
    
    folium.Marker(
        pos, 
        popup=f"{v['line']} -> {v['dest']} ({v['time']}m)",
        icon=folium.DivIcon(html=icon_html, icon_size=(40,24), icon_anchor=(20,12))
    ).add_to(m)

st_folium(m, width="100%", height=600, returned_objects=[])
