import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import math
import pandas as pd

# --- 1. SETUP ---
st.set_page_config(page_title="Wien Öffis V38", layout="wide", page_icon="🚋")

# State Initialisierung
if 'map_zoom' not in st.session_state:
    st.session_state.map_zoom = 16
if 'map_center' not in st.session_state:
    st.session_state.map_center = [48.2082, 16.3738]
if 'gps_lat' not in st.session_state:
    st.session_state.gps_lat = None
if 'gps_lon' not in st.session_state:
    st.session_state.gps_lon = None

try:
    from streamlit_js_eval import get_geolocation
    HAS_GPS_MODULE = True
except ImportError:
    HAS_GPS_MODULE = False

# CSS: Bilder 15px, Grid Layout
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    
    /* Tabelle: Bilder auf 15px zwingen */
    div[data-testid="stDataFrame"] div[data-testid="stImage"] > img {
        height: 15px !important;
        width: auto !important;
        object-fit: contain !important;
        background-color: transparent !important;
    }
    
    /* Grid Styling */
    .ac-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
        gap: 12px;
        margin-bottom: 20px;
    }
    .ac-tile {
        min-height: 100px;
        border-radius: 8px;
        padding: 6px;
        color: white;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        font-family: sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GRAFIKEN (BASE64 - Kompakt) ---
ICON_STATION = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAMCAIAAADtbgqsAAAAB3RJTUUH6gELByIjkfAdIgAAAoxJREFUeJxNzstrlGcYhvH7eQ8z3xwSJ4MxaWszJhiQduER3Fh0EWxr0ZIuohQhbVHU1iOIq2BQQjyQorVd1O5SaEUqQWuxbTAgSAOCqAhRkC4SjSaS4/jNTOY7vM/TRUH8cf0BF/i1IHAiXK74J3qnG1um8kun6gvTLe9PL26aqmmYXfdBdegWi7wZMTNE4BysdaNj5T0Hw8GbKp+HAGnPbt0S9P9i1q7O9PWqpnfF94mIjOViEdkscRjBGgDh9Rulw8fkxSTlc8QilSq981a6p6u06wAtqkUcY2EB1kApnpnRrcszF783sEaKxfKZvurZC5RIIJNmv0TWcmne1K0wq1YhlXTPx5WXEgBBIKVyoqM9+12famww8YOHlW8vRH/e0M3LnHCSAFJQytWlbcdnurlgt7fLwO8qnQGzOOcd2Jc8+DUAABSPP5cgkHRGEbTVEy/nQCTC2iYalheEWURe/jsGZgBQWhWWUjUQ4YVqRCwSAxYIgZMX/7h0fRgJA4JdCL/Z2bb/87au879dHrwrXhIswkwuZlBpzt/RvsFw7KzRzyamd3f3/33rPjLe/0colvqv/vPRppU/DtyenZpHyoNzsAbVAILj+7Yd/fJjo7W+MnRvT8/Psy9mka8FC5xLpj2kkpOvyvcePy1GjnI1pEhpFc/5rU0NP3R3bl7/HgATxHGhse7auf2ZjOdixyKLsqlHo5NHTl+amPf/Gh5xUYyEltCxX/mkbc1P3V+8XZ8Lo9gYTc6xUoQ3DN15dOjUryOjkyqdrMumZoplEGqVOrxzc9ferVapMHLWKADEzLFjEXHMWqkHT55t/OpsGLnaJTmO4sixlzAVv3K088OevZ+GUUwEozUAIvoPOtpWT2fW07IAAAAASUVORK5CYII="
ICON_BUS = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAARCAIAAAAg6XlfAAAAAXNSR0IB2cksfwAAAARnQU1BAACxjwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+oBDQoiFXP5RDQAAASmSURBVEjHxVVNi51ZEX6eOnXevh9Nf998GTuJSXo0UTCOoiAIuhCHQZwwG52VMKv5JZKFS7fCgDO4nBGEGceOMAZBjZmIi2QSEs2N3E5id9J9++P2fd9TVS6uaYcJDoILa3E4p+o5VaeKOk/x8uXL+H+I/u8uSD6rjIiI+E/WfweegA5wB8dPkK2tLVWNCJJPVxIBAMLt4fahwz0hAU4AHwuhEbG3tzcYDFqtFkl3/y/zc/eqqiZ4EQGCFMAREKq7PXzwEGCET0KKiLuPRqOVlZWIUACDweD8+fMXL148SPejD5wEe7ZiEwxJEel09eSpI8PhcHGxLUCg8dA7dza2NhuETzxExKVLl65cubK0tLSwsKATrYe3Ol0mCWtEW6RYvQ+SkgCIJDLq0cjcgQgPJ1NYbnUkZSCY/PHmno318RMAHibFi5sKG6YsRDCRcPfG7MaNG3Nzc0+bK3j05JmgbK4/mFnsJa22Nx5OadapNhEBwprB3++f/Oz58DLer7szM08e3O/OL0luRSDCm/F+3Qyl3SMigBRol43ZXtWZW9x5sjEzv+DNOGs+sbycc+73+3LQSjHZBOlCpzDrVAepMqSxobEoZm7m7mZmEUEJpKAAICCkwx3uZBGGimRBkiA9zNxKQFJ69513VLXX6/2r1IhYu3OLIlRJ6XCENaVpi1BVVSVAS5IknnYpgu7BIALBhKAjpZQ0ZS+mWZOkBHpBMQ8PBIVQVQfPnTtXVZVOGtQ210l3IBVbH9wDWI9Hze6QmigUJkKSVknViwmCYYywUquSIEFNNEm0en3wt1an/YWV5ev9YXt2JqNBkDDlmBBJmnMmqQCkaepfvvujH75qSnN2p6dJuJsjWAzhrCpJcvXDO+/f7atWpuaULz139uVvfD0CSFlSQoR5w+JhjQfd4qWvfevHb/70qxc+/cc/PDp9Ig3WiqSgu5mLiCJgEuNfvbe+MQxJRzOXkiS3QqmZb6aoCz5Taa+Ytds4cyZICIUhN2/PXPl9RgQBIBAA17S6XeokqTfVltnpqdz9y4e7J5ePlaLbex3euv2dlbNmJWdVkGZ4ROlI8kBFdB3Z0p5yVfCL6VZ3dnZ+sPYaKm3qMItiTV1ru91NXHKGN05xhDHu5+ono+HmkR7Dz27uvLjtzex8s4t/PNyYWzrUarWb138201sU4YQyo5J0KOsjlIZaIAZAyt7R2bfXy7dfeHGq0/7T1avvX/tzldooBeYKKBEWsZBtfRwwBjR4s4xHy8uvvPw9Cf35m2+s7wxV5s291GU82hdvmlPHn7/4EpMCUASOnzpx67svrL/3m85oHzujnHKFMkQquTa38c5eV3WYckdzR8FKONXysvfYm7+KsNVKpIAEd93brVY11RGysbJbdbPElFh7thM+1vCtu2t3f/u7b37u8wC4+uvVYIR7mO/s7G5vDwkg4OF379176623jxw7bMVf+f4PREiRCVv6hC8jSDAYCABM6dq1D65f/6Cu6y9euPCVLz9PSgDk5KuDEcc+dTxXGQBXV1efHQAHPNzv90spvV5venp6Yp2w7jNTEECALKX0+30Ap0+fFpGPIj92658EqrXXmmhvFQAAAABJRU5ErkJggg=="
ICON_TRAM = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAALCAIAAACCpFiiAAAAAXNSR0IB2cksfwAAAARnQU1BAACxjwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+oBDQkNH4N2Kx4AAAN8SURBVDjLTY7PbxRlHIe/P953ZmdmZ3a3u9AKhdLShKK0VaNRL7YXIAYJmpjGGP8QD3rWkHjQP8Gbib8ORgkQDURUEj2QygaktJYWul12u7vdndmZ2Zn36wFifJLP5flcHtxuNgUEBcCYkckJEAEAQJ4OAAAQlFZiJDM5/if/B4IgGMNaI46MwRyG8fBOvZ4k8cuvvEpMgIACihUwGhEUVAiYRuHVr7/pP9xuXbrioGEiBhAAA2BIRGAflH3uXNjvVq/9Qk+fJ1UoiCCCIhnTYGk5OFAdfPmVhyK5gIgQ1AlNLggwIiq/vlybPb584YJd9PFhs3X9p6s+yFgpyEeZyZJwP/QrFWQCIhQweZ6koy++/86z7PffelvEoBExImBAAJFQKyRGlG8v/dDsdt87c75QsEkzMps8lyxNokhrix0XNQ36YWOQnH7jLG4+anx68ZOxSuXK5cvlTjdgdUfSYQ5a63gYV8efQYKkv7/40mK33WnV746BWLpwfzhQ5TFhxF5v1nEHWdpKRodfeK5arf35+00qBMi012p5jpumcQBm2nH7UdLwvLNnTnc6ex98+JEahqHrOjd+/S03xra1XR3Xza1gfJK1bu00Ck5RMWRhlwUQ0VZYKvpKF6wkKlYPMnPUj4JySQ+TUHpxnAwGEaSpN1FRAlmS1cYPxlGUbK3riUnK9ixt3fpr9cWFxXDQ53dWVqJBr9Pe85xCFkVoa2PZpaDkuYWS75WKrsWkACzXGQ4TX8xk7YBtqdS2i0HJ1mSJmSz7rutEAlapSIostoOi53tO0XOcgrYUk6U9YgFTmpwoet7JuRMF11FpEs9Z1rNTRxLEa1H8OB69e2q+5PugGAiNARrlaT76cWf7UNE9VZq5988GMb95bHq6VsuM/O159QebLLB07MiapULBlYWFRGSEwMwMaCMkUXTj9t3D5WBpZsYAaJA0jBTE8fWPL85qBmFgGNPc+Xm7naaMKAIERJpyrWh+vt/Z31xb70NGwJtbj2xERAiFtK1yk23s7u5OHUI/2Lj5BxhgMUaMAshAMmYGSk22c28dTLaW5a99/hk+2NnduL/GYhQjAgkIAK7ertdqtXKlst/rNRuNxefnPT+IkiTq9wWfAGiEiAnIgDFGMsk8P/Acd9DZu7W6OnX0qBcU283O43b75NwJECFCMpIjiODU8Zl/AQJfwL2xhZLWAAAAAElFTkSuQmCC"
ICON_SUBWAY = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAMCAIAAACfoWgaAAAAAXNSR0IB2cksfwAAAARnQU1BAACxjwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+oBDQkSBMRJ7GwAAAQiSURBVDjLdVTJblxFFD33Vr1u92C/HuI4njseAsRxUAZhUCQ+APMNrMCfYj4hbCNWhF1WIHYJysDCgUQQ29gxiePY3Wm323H3e/2GupdFxwIhcVRSlXRL99Q9qnNor94AoKogAgGqUPw/pL8RMUAAVAVQIgL66x/8qwSA/9PIAgpQvwkpnEuJiIhUFEwAEVTVAAJSBqkCBFUACoBAClXtn1WBU3oF1KUpMzOzE0fvAIAUsP17nZPOy52dOImePPmNiKrV6tFhq5DPT9TOMxuPATAUjkSVoK7PoDilPR0ZgJy+I46izY31gYGBkZGRvdevh/zS+Pj42Oi5sfEpYkN79TdpEn1769aZ6pkkTTJZj5lbzaZziSiyNt9tv+gcNc5WC0ypCGIRb6jm5fwgCJgZ4MHikCgR9/UhhaiKiHQ73b5ig4NDZDgMAsOmF4U3bnw6d+F9C0BFfl17vHBpcffVy/n5uUq5vL7xjKBQnBsdCwPZP0qa3c7UxMTe3q44jNbiTNLe2txyzhHzwqUPX7x4xcb6vh8EQZIkBJmZmdzd3SbiMAynp88P+aXn29sD2awTCcKAoBbQw1azG7wV1a2tnfkLc0613X6byWaOj9sj50aPu9Fe40RVUs5tbh0YtjHn5memWketQr4IliR1a0+eGjaT46OHraNUBKq16clWs1UoDh3sN2Zm3zNephf3enEURdHDhw8WLi9aQLe3d4aHz3qeyeUGmA0RQyFpAhHDVCwWSv4QqQ4WBitln8kUCjknqbUmkzUiYi1Xyr41XskfMsZESSJpkqZpnMRFkmzGWsvMbIwVceWS/9fznThK6NVB486d256JG42wVKr2orBYzP3+9LGLo3zBz2YyY5M1MDExFH3Pqbr6wW4UBUdHrWx2YH5+gWwWRIZEVFWIgF7Y3d/fjXq94mAxX/TzRV/SJInjTEaAdPnzLywzGbKHzWMRjeJemqRQpHHiEonj2HpZAonAQd75gAiAS9NOpxuGkSiDiEQUcP3f3Xccaxj2Tk5O4jj1MnlSjePEsBHH3W5iWG0Yhre/+/7atathEARBEMfJ25POcfuICaqSzeb29+vWeu12W1WZGYC1NuqFvV5PVZP0TbN5zGSstQCcc8aamdnZjWd/1Bt1FQJ088+dYqFYrVas51Uq5YOD+vr6Bu0dNN7UD9bW1uqNOoBKpfz16iqUFY6AUqW8/NnyR0tLjx79wkSqcvGDi6urq865paWllZWVw8PDmze/uXx50fM8VVXVQrFw7fr1lS+/EpV8Pq+iA7mB5eXlM8PDcRwz88dLn0xP16gfmf3UJCKo3v/5nl/yp2o1Q3T//oPp2vTs3AVVJQJUiVhVARVVz3p9AUTFOSeqUBVomsQ//fDj4qXF8fEJw3z33t0rV6/45Uo/WYgYwN+Hl2oR8/jiRgAAAABJRU5ErkJggg=="
ICON_TRAIN = "data:image/png;base64,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"

# --- 3. DATEN (Erweitert um Nachbarstationen & Busse) ---
STATION_MARKERS = [
    {"name": "Schwedenplatz", "lat": 48.2114, "lon": 16.3783, "lines": ["U1", "U4", "1", "2"], "rbl": [4205, 4212, 4208, 4210]},
    {"name": "Karlsplatz", "lat": 48.2000, "lon": 16.3690, "lines": ["U1", "U2", "U4", "1", "D", "62", "WLB"], "rbl": [4202, 4216, 4617, 4214, 32, 40]}, 
    # Stephansplatz mit U1 und Bussen
    {"name": "Stephansplatz", "lat": 48.2082, "lon": 16.3738, "lines": ["U1", "U3", "1A", "2A", "3A"], "rbl": [4200, 4206, 4203, 4209, 360, 361, 362]},
    {"name": "Westbahnhof", "lat": 48.1960, "lon": 16.3350, "lines": ["U3", "U6", "5", "6", "18", "52", "60", "S50"], "rbl": [4920, 4921, 4600, 350, 354]}, 
    {"name": "Schottentor", "lat": 48.2150, "lon": 16.3610, "lines": ["U2", "1", "D", "37", "38", "40", "41", "42", "43", "44", "71"], "rbl": [4209, 4211, 4001, 4002]}, 
    {"name": "Landstraße", "lat": 48.2060, "lon": 16.3850, "lines": ["U3", "U4", "O", "74A", "S"], "rbl": [4204, 4213, 107, 108]},
    {"name": "Praterstern", "lat": 48.2180, "lon": 16.3900, "lines": ["U1", "U2", "5", "O", "80A", "82A", "S"], "rbl": [4207, 4105, 127, 128]},
    {"name": "Neubaugasse (13A)", "lat": 48.1990, "lon": 16.3450, "lines": ["U3", "13A", "14A"], "rbl": [267, 266]},
    {"name": "Pilgramgasse (13A)", "lat": 48.1930, "lon": 16.3550, "lines": ["U4", "13A", "14A"], "rbl": [272, 273]},
    {"name": "Alser Straße (43)", "lat": 48.2170, "lon": 16.3420, "lines": ["U6", "43", "44"], "rbl": [4219, 4220, 100, 101]},
    # Hbf + Quartier Belvedere (für S-Bahn Strecken)
    {"name": "Hauptbahnhof", "lat": 48.1850, "lon": 16.3750, "lines": ["U1", "D", "13A", "69A", "O", "18", "S"], "rbl": [4111, 4112, 150, 151, 160, 161, 301, 302, 110, 111, 1000]},
    {"name": "Quartier Belvedere", "lat": 48.1880, "lon": 16.3820, "lines": ["S", "D", "18", "O"], "rbl": [1001, 1002]},
    # Für den "Off-Station" Test (Karlsplatz/Herrengasse/Stubentor)
    {"name": "Herrengasse", "lat": 48.2095, "lon": 16.3660, "lines": ["U3", "1A", "2A"], "rbl": [4204, 4210]},
    {"name": "Stubentor", "lat": 48.2070, "lon": 16.3790, "lines": ["U3", "2", "3A", "74A"], "rbl": [4205, 4211]}
]

# Strecken erweitert (inkl. S-Bahn Stammstrecke)
RAW_ROUTES = {
    "U1": [[48.1530, 16.3850], [48.1700, 16.3800], [48.1870, 16.3750], [48.2000, 16.3700], [48.2082, 16.3738], [48.2130, 16.3780], [48.2180, 16.3900], [48.2250, 16.4000], [48.2450, 16.4400], [48.2600, 16.4500]], 
    "13A": [[48.2020, 16.3380], [48.2005, 16.3420], [48.1990, 16.3450], [48.1970, 16.3490], [48.1960, 16.3550], [48.1945, 16.3580], [48.1930, 16.3600], [48.1850, 16.3650]], 
    "43": [[48.2150, 16.3610], [48.2160, 16.3550], [48.2165, 16.3500], [48.2170, 16.3420], [48.2180, 16.3350], [48.2200, 16.3300]],
    "D": [[48.2150, 16.3610], [48.2050, 16.3600], [48.2020, 16.3680], [48.2000, 16.3720], [48.1950, 16.3750], [48.1850, 16.3750], [48.1800, 16.3800], [48.1700, 16.3900]],
    "U2": [[48.2200, 16.5100], [48.2150, 16.4500], [48.2180, 16.4200], [48.2100, 16.3570], [48.2070, 16.3580], [48.2000, 16.3690]], 
    "U3": [[48.2110, 16.3100], [48.1960, 16.3350], [48.2082, 16.3738], [48.2060, 16.3850], [48.1900, 16.4000]], 
    "U4": [[48.1900, 16.2900], [48.1900, 16.3500], [48.2000, 16.3690], [48.2082, 16.3738], [48.2114, 16.3783], [48.2166, 16.3730], [48.2250, 16.3600]], 
    "U6": [[48.1750, 16.3350], [48.1960, 16.3350], [48.2150, 16.3400], [48.2300, 16.3500]],
    # City Busse
    "1A": [[48.2082, 16.3738], [48.2095, 16.3660], [48.2110, 16.3640]],
    "2A": [[48.2082, 16.3738], [48.2100, 16.3750], [48.2114, 16.3783]],
    "3A": [[48.2082, 16.3738], [48.2070, 16.3790], [48.2060, 16.3850]],
    # S-Bahn Stammstrecke (Schematisch)
    "S": [[48.1850, 16.3750], [48.1880, 16.3820], [48.2060, 16.3850], [48.2180, 16.3900], [48.2300, 16.3950]]
}

# FARB-LEGENDE OFFIZIELL
LINE_COLORS = {
    "U1": "#E2021A", "U2": "#A365A4", "U3": "#F67F21", "U4": "#009641", "U6": "#9D6643",
    "S": "#002D72", # S-Bahn dunkelblau
    "13A": "#E31C1C", "1A": "#E31C1C", "2A": "#E31C1C", "3A": "#E31C1C", "48A": "#E31C1C", # Busse Rot (Standard WL)
    "D": "#E31C1C", "43": "#E31C1C", "1": "#E31C1C", "2": "#E31C1C", "71": "#E31C1C", # Tram Rot
    "WLB": "#002D72"
}

# --- 4. MATHEMATIK ---

def smooth_path(points):
    if len(points) < 2: return points
    smoothed = []
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i+1]
        steps = 8
        for j in range(steps):
            f = j / steps
            smoothed.append([p1[0]*(1-f)+p2[0]*f, p1[1]*(1-f)+p2[1]*f])
    smoothed.append(points[-1])
    return smoothed

SMOOTH_ROUTES = {k: smooth_path(v) for k,v in RAW_ROUTES.items()}

def calculate_bearing(p1, p2):
    if not p1 or not p2: return 0
    lat1, lat2 = math.radians(p1[0]), math.radians(p2[0])
    dLon = math.radians(p2[1] - p1[1])
    x = math.sin(dLon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dLon))
    return (math.degrees(math.atan2(x, y)) + 360) % 360

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def get_vehicle_position_and_rotation(line_name, minutes_away):
    route_key = line_name
    # Fallback für S-Bahnen auf Stammstrecke
    if line_name.startswith("S") or "CJX" in line_name or "REX" in line_name:
        route_key = "S"
        
    if route_key not in SMOOTH_ROUTES:
        if "U" in route_key: route_key = "U1"
        elif "A" in route_key: route_key = "1A"
        elif len(route_key) <= 2: route_key = "D"
        else: return None, None, 0

    path = SMOOTH_ROUTES.get(route_key, [])
    if len(path) < 2: return None, None, 0

    speed_factor = 2.5
    start_index = len(path) - 2 
    current_index = start_index - int(minutes_away * speed_factor)
    current_index = max(0, min(current_index, len(path)-2))
    
    p1 = path[current_index]
    p2 = path[current_index + 1]
    rotation = calculate_bearing(p1, p2)
    return p1[0], p1[1], rotation

# --- 5. DATEN & LOGIK ---

@st.cache_data(ttl=10)
def fetch_data(rbl_list):
    if not rbl_list: return []
    
    chunk_size = 15
    chunks = [rbl_list[i:i + chunk_size] for i in range(0, len(rbl_list), chunk_size)]
    
    all_vehicles = []
    unique_ids = set()

    for chunk in chunks:
        url = f"https://www.wienerlinien.at/ogd_realtime/monitor?rbl={'&rbl='.join(map(str, chunk))}"
        try:
            response = requests.get(url, timeout=4)
            data = response.json()
            
            for mon in data.get("data", {}).get("monitors", []):
                for line in mon.get("lines", []):
                    line_name = line.get("name")
                    direction = line.get("towards", "").strip()
                    
                    for i, dep in enumerate(line.get("departures", {}).get("departure", [])):
                        if i >= 5: break 
                        countdown = dep.get("departureTime", {}).get("countdown", 99)
                        
                        if isinstance(countdown, int) and countdown < 40:
                            vh = dep.get("vehicle", {})
                            v_id = vh.get("id")
                            if not v_id: v_id = f"{line_name}_{direction}"
                            
                            ac = vh.get("barrierFree", False) or vh.get("foldingRamp", False)
                            
                            v_type = "tram"
                            if line_name == "U6":
                                v_type = "subway"
                            elif "U" in line_name:
                                v_type = "subway"
                            elif "A" in line_name or "Bus" in line_name:
                                v_type = "bus"
                            elif line_name == "WLB":
                                v_type = "tram"
                            elif line_name.startswith("S") or line_name.startswith("R") or "CJX" in line_name or "REX" in line_name:
                                v_type = "train"
                            
                            if v_id not in unique_ids:
                                all_vehicles.append({
                                    "id": v_id,
                                    "line": line_name,
                                    "dest": direction,
                                    "time": countdown,
                                    "ac": ac,
                                    "type": v_type
                                })
                                unique_ids.add(v_id)

        except: continue
        
    return all_vehicles

# --- 6. SIDEBAR & GPS ---

with st.sidebar:
    st.header("Einstellungen")
    gps_mode = st.toggle("Echtstandort (GPS)", value=False, key="gps_toggle_btn")
    
    if gps_mode:
        st.write("📡 Suche GPS...")
        if HAS_GPS_MODULE:
            loc = get_geolocation()
            if loc:
                st.session_state.gps_lat = loc['coords']['latitude']
                st.session_state.gps_lon = loc['coords']['longitude']
                st.success(f"GPS: {st.session_state.gps_lat:.4f}, {st.session_state.gps_lon:.4f}")
            else:
                st.warning("Warte auf Browser-Freigabe...")
        else:
            st.error("Kein GPS Plugin.")
    else:
        st.session_state.gps_lat = None
        st.session_state.gps_lon = None

    if not gps_mode:
        sim_scenario = st.radio("Simulation:", ["Stephansplatz", "Ring/Oper", "Hauptbahnhof"], index=1)
        if sim_scenario == "Stephansplatz":
            user_lat, user_lon = 48.2082, 16.3738
        elif sim_scenario == "Hauptbahnhof":
            user_lat, user_lon = 48.1850, 16.3750
        else:
            user_lat, user_lon = 48.2050, 16.3650
    else:
        if st.session_state.gps_lat:
            user_lat, user_lon = st.session_state.gps_lat, st.session_state.gps_lon
        else:
            user_lat, user_lon = 48.2082, 16.3738

    if st.button("Aktualisieren"):
        st.rerun()

# --- 7. FILTERUNG & LOGIK (50m vs 500m) ---

relevant_rbls = []
visible_lines = set()
closest_station_dist = float('inf')
closest_station = None

# Finde erst die absolut nächste Station
for s in STATION_MARKERS:
    dist = haversine(user_lat, user_lon, s["lat"], s["lon"])
    if dist < closest_station_dist:
        closest_station_dist = dist
        closest_station = s

# Logik Anwenden
if closest_station and closest_station_dist <= 50:
    # Fall A: In der Station (<=50m) -> NUR diese Station
    relevant_rbls.extend(closest_station["rbl"])
    for l in closest_station.get("lines", []):
        visible_lines.add(l)
else:
    # Fall B: Außerhalb -> Alle im Umkreis von 500m
    for s in STATION_MARKERS:
        dist = haversine(user_lat, user_lon, s["lat"], s["lon"])
        if dist < 500:
            relevant_rbls.extend(s["rbl"])
            for l in s.get("lines", []):
                visible_lines.add(l)

vehicles = fetch_data(relevant_rbls)
vehicles.sort(key=lambda x: x["time"])

# --- 8. KARTE ---

if gps_mode and st.session_state.gps_lat:
    map_center = [st.session_state.gps_lat, st.session_state.gps_lon]
elif 'map_center' in st.session_state:
    map_center = st.session_state.map_center
else:
    map_center = [user_lat, user_lon]

m = folium.Map(
    location=map_center, 
    zoom_start=st.session_state.map_zoom, 
    tiles="CartoDB positron"
)

folium.Marker(
    [user_lat, user_lon],
    tooltip="Du",
    icon=folium.Icon(color="blue" if gps_mode else "gray", icon="user", prefix="fa"),
    z_index_offset=1100
).add_to(m)

# 4.A: NUR Linien einzeichnen, die in "visible_lines" sind (also abgefragt wurden)
for line_name in visible_lines:
    route_key = line_name
    if line_name.startswith("S") or "CJX" in line_name: route_key = "S"
    
    if route_key not in SMOOTH_ROUTES:
        if "U" in route_key: route_key = "U1"
        elif "A" in route_key: route_key = "1A"
        else: route_key = "D"
    
    if route_key in SMOOTH_ROUTES:
        # Farbe bestimmen
        l_color = LINE_COLORS.get(line_name, "#888888")
        if "A" in line_name or "Bus" in line_name: l_color = "#E31C1C" # Busse Rot auf Karte
        elif line_name.startswith("S"): l_color = "#002D72"
        
        folium.PolyLine(SMOOTH_ROUTES[route_key], color=l_color, weight=3, opacity=0.6).add_to(m)

# Stationen Marker
for s in STATION_MARKERS:
    dist = haversine(user_lat, user_lon, s["lat"], s["lon"])
    should_show = False
    if closest_station_dist <= 50:
        if s == closest_station: should_show = True
    elif dist < 500:
        should_show = True
        
    if should_show:
        icon = folium.CustomIcon(ICON_STATION, icon_size=(24, 14), icon_anchor=(12, 7))
        folium.Marker([s["lat"], s["lon"]], popup=s['name'], icon=icon, z_index_offset=1000).add_to(m)

def get_icon_props(v):
    if v["type"] == "bus": return ICON_BUS, 32, 12
    if v["type"] == "tram": return ICON_STATION, 15, 12 # Fallback
    if v["type"] == "subway": return ICON_STATION, 15, 12 # Fallback
    if v["type"] == "train": return ICON_STATION, 15, 12 # Fallback
    return ICON_STATION, 32, 8

for v in vehicles:
    lat, lon, rot = get_vehicle_position_and_rotation(v["line"], v["time"])
    if lat and lon:
        border_color = "#0066b3" if v["ac"] else "#d32f2f"
        # Nutzung des generischen Stations-Icons als Platzhalter für Fahrzeug (einfacher)
        # oder Bus Icon für Busse
        icon_b64, w, h = get_icon_props(v)
        
        display_rot = rot - 90
        icon_html = f"""
        <div style="transform: rotate({display_rot}deg); display: flex; flex-direction: column; align-items: center; justify-content: center; width: 40px; height: 40px;">
            <img src="{icon_b64}" style="width: {w}px; height: {h}px;">
            <div style="width: {w}px; height: 3px; background: {border_color}; margin-top: 1px; border-radius: 2px;"></div>
            <div style="transform: rotate({-display_rot}deg); background: rgba(255,255,255,0.8); color: black; font-weight: bold; font-size: 9px; padding: 0 3px; border-radius: 4px; border: 1px solid #ccc;">
                {v['line']}
            </div>
        </div>
        """
        folium.Marker([lat, lon], icon=folium.DivIcon(html=icon_html, icon_size=(40,40), icon_anchor=(20,20))).add_to(m)

map_data = st_folium(m, width="100%", height=500, returned_objects=[])

if not gps_mode and map_data:
    new_zoom = map_data.get('zoom')
    new_center = map_data.get('center')
    if new_zoom is not None: st.session_state.map_zoom = new_zoom
    if new_center is not None and 'lat' in new_center: st.session_state.map_center = [new_center['lat'], new_center['lng']]

# --- 9. KACHELN ---
st.subheader("❄️ Nächste klimatisierte Fahrzeuge")

if vehicles:
    line_data = {}
    for v in vehicles:
        if v["ac"]:
            if v["line"] not in line_data: line_data[v["line"]] = {}
            dest = v["dest"]
            time = v["time"]
            if dest not in line_data[v["line"]] or time < line_data[v["line"]][dest]:
                line_data[v["line"]][dest] = time

    if line_data:
        grid_items_str = ""
        for line, dests in line_data.items():
            bg = LINE_COLORS.get(line, "#555")
            if "A" in line or "Bus" in line: bg = "#E31C1C"
            elif line.startswith("S"): bg = "#002D72"
            
            dests_str = ""
            for dest_name, min_time in dests.items():
                dests_str += f'<div style="display:flex;justify-content:space-between;font-size:0.75em;margin-bottom:2px;"><span style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:70%;" title="{dest_name}">{dest_name}</span><span style="font-weight:bold;">{min_time}m</span></div>'
            grid_items_str += f'<div class="ac-tile" style="background-color:{bg};"><div style="text-align:center;font-weight:bold;font-size:1.1em;border-bottom:1px solid rgba(255,255,255,0.4);padding-bottom:2px;">{line}</div><div style="flex-grow:1;overflow:hidden;">{dests_str}</div><div style="text-align:center;font-size:0.6em;opacity:0.9;">❄️ AC</div></div>'
        
        full_html = f'<div class="ac-grid">{grid_items_str}</div>'
        st.markdown(full_html, unsafe_allow_html=True)
    else:
        st.info("Keine klimatisierten Fahrzeuge in Kürze.")
else:
    st.write("Keine Linien in der Nähe.")

# --- 10. TABELLE ---
st.subheader("📋 Alle Abfahrten (Live)")

if vehicles:
    t_data = []
    for v in vehicles:
        icon_url, _, _ = get_icon_props(v)
        
        line_color = LINE_COLORS.get(v["line"], "#888")
        if "A" in v["line"]: line_color = "#000000" # Schwarz in Tabelle wie gewünscht
        elif v["line"].startswith("S") or v["line"] == "WLB": line_color = "#002D72"
        elif v["line"] in ["D", "1", "43", "71", "6", "11", "18"]: line_color = "#E31C1C"
        
        clean_id = v['id']
        if "_" in clean_id: clean_id = "" 
        
        t_name = "Bim"
        if v["type"] == "bus": t_name = "Bus"
        elif v["type"] == "subway": t_name = "U-Bahn"
        elif v["type"] == "train": t_name = "Zug"
        
        descr = f"{t_name} ({clean_id})" if clean_id else t_name
        
        t_data.append({
            "Typ": icon_url, 
            "Fahrzeug": descr,
            "Linie": v["line"], 
            "LineColor": line_color, 
            "Ziel": v["dest"], 
            "Zeit": f"{v['time']} min", 
            "Klima": "❄️" if v["ac"] else "🔥"
        })
        
    df = pd.DataFrame(t_data)
    
    st.dataframe(
        df, 
        column_config={
            "Typ": st.column_config.ImageColumn("Typ", width="small"),
            "Fahrzeug": st.column_config.TextColumn("Fahrzeug"),
            "Linie": st.column_config.TextColumn("Linie", width="small"),
            "LineColor": None, 
            "Zeit": st.column_config.TextColumn("Abfahrt", width="small"),
            "Klima": st.column_config.TextColumn("AC", width="small")
        },
        hide_index=True, 
        use_container_width=True
    )
