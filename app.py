import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import math
import pandas as pd
import time

# --- 1. SETUP ---
st.set_page_config(page_title="Wien Öffis V24", layout="wide", page_icon="🚋")

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

# Zoom & Center State initialisieren
if 'map_zoom' not in st.session_state:
    st.session_state.map_zoom = 14
if 'map_center' not in st.session_state:
    st.session_state.map_center = [48.2082, 16.3738]

try:
    from streamlit_js_eval import get_geolocation
    HAS_GPS_MODULE = True
except ImportError:
    HAS_GPS_MODULE = False

st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GRAFIKEN (BASE64) ---

ICON_STATION_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAMCAIAAADtbgqsAAAAB3RJTUUH6gELByIjkfAdIgAAAoxJREFUeJxNzstrlGcYhvH7eQ8z3xwSJ4MxaWszJhiQduER3Fh0EWxr0ZIuohQhbVHU1iOIq2BQQjyQorVd1O5SaEUqQWuxbTAgSAOCqAhRkC4SjSaS4/jNTOY7vM/TRUH8cf0BF/i1IHAiXK74J3qnG1um8kun6gvTLe9PL26aqmmYXfdBdegWi7wZMTNE4BysdaNj5T0Hw8GbKp+HAGnPbt0S9P9i1q7O9PWqpnfF94mIjOViEdkscRjBGgDh9Rulw8fkxSTlc8QilSq981a6p6u06wAtqkUcY2EB1kApnpnRrcszF783sEaKxfKZvurZC5RIIJNmv0TWcmne1K0wq1YhlXTPx5WXEgBBIKVyoqM9+12famww8YOHlW8vRH/e0M3LnHCSAFJQytWlbcdnurlgt7fLwO8qnQGzOOcd2Jc8+DUAABSPP5cgkHRGEbTVEy/nQCTC2iYalheEWURe/jsGZgBQWhWWUjUQ4YVqRCwSAxYIgZMX/7h0fRgJA4JdCL/Z2bb/87au879dHrwrXhIswkwuZlBpzt/RvsFw7KzRzyamd3f3/33rPjLe/0colvqv/vPRppU/DtyenZpHyoNzsAbVAILj+7Yd/fJjo7W+MnRvT8/Psy9mka8FC5xLpj2kkpOvyvcePy1GjnI1pEhpFc/5rU0NP3R3bl7/HgATxHGhse7auf2ZjOdixyKLsqlHo5NHTl+amPf/Gh5xUYyEltCxX/mkbc1P3V+8XZ8Lo9gYTc6xUoQ3DN15dOjUryOjkyqdrMumZoplEGqVOrxzc9ferVapMHLWKADEzLFjEXHMWqkHT55t/OpsGLnaJTmO4sixlzAVv3K088OevZ+GUUwEozUAIvoPOtpWT2fW07IAAAAASUVORK5CYII="

# Silberpfeil (Type U - Neu!)
ICON_SILBERPFEIL_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAMCAIAAACfoWgaAAAAAXNSR0IB2cksfwAAAARnQU1BAACxjwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+oBDQkSBMRJ7GwAAAQiSURBVDjLdVTJblxFFD33Vr1u92C/HuI4njseAsRxUAZhUCQ+APMNrMCfYj4hbCNWhF1WIHYJysDCgUQQ29gxiePY3Wm323H3e/2GupdFxwIhcVRSlXRL99Q9qnNor94AoKogAgGqUPw/pL8RMUAAVAVQIgL66x/8qwSA/9PIAgpQvwkpnEuJiIhUFEwAEVTVAAJSBqkCBFUACoBAClXtn1WBU3oF1KUpMzOzE0fvAIAUsP17nZPOy52dOImePPmNiKrV6tFhq5DPT9TOMxuPATAUjkSVoK7PoDilPR0ZgJy+I46izY31gYGBkZGRvdevh/zS+Pj42Oi5sfEpYkN79TdpEn1769aZ6pkkTTJZj5lbzaZziSiyNt9tv+gcNc5WC0ypCGIRb6jm5fwgCJgZ4MHikCgR9/UhhaiKiHQ73b5ig4NDZDgMAsOmF4U3bnw6d+F9C0BFfl17vHBpcffVy/n5uUq5vL7xjKBQnBsdCwPZP0qa3c7UxMTe3q44jNbiTNLe2txyzhHzwqUPX7x4xcb6vh8EQZIkBJmZmdzd3SbiMAynp88P+aXn29sD2awTCcKAoBbQw1azG7wV1a2tnfkLc0613X6byWaOj9sj50aPu9Fe40RVUs5tbh0YtjHn5memWketQr4IliR1a0+eGjaT46OHraNUBKq16clWs1UoDh3sN2Zm3zNephf3enEURdHDhw8WLi9aQLe3d4aHz3qeyeUGmA0RQyFpAhHDVCwWSv4QqQ4WBitln8kUCjknqbUmkzUiYi1Xyr41XskfMsZESSJpkqZpnMRFkmzGWsvMbIwVceWS/9fznThK6NVB486d256JG42wVKr2orBYzP3+9LGLo3zBz2YyY5M1MDExFH3Pqbr6wW4UBUdHrWx2YH5+gWwWRIZEVFWIgF7Y3d/fjXq94mAxX/TzRV/SJInjTEaAdPnzLywzGbKHzWMRjeJemqRQpHHiEonj2HpZAonAQd75gAiAS9NOpxuGkSiDiEQUcP3f3Xccaxj2Tk5O4jj1MnlSjePEsBHH3W5iWG0Yhre/+/7atathEARBEMfJ25POcfuICaqSzeb29+vWeu12W1WZGYC1NuqFvV5PVZP0TbN5zGSstQCcc8aamdnZjWd/1Bt1FQJ088+dYqFYrVas51Uq5YOD+vr6Bu0dNN7UD9bW1uqNOoBKpfz16iqUFY6AUqW8/NnyR0tLjx79wkSqcvGDi6urq865paWllZWVw8PDmze/uXx50fM8VVXVQrFw7fr1lS+/EpV8Pq+iA7mB5eXlM8PDcRwz88dLn0xP16gfmf3UJCKo3v/5nl/yp2o1Q3T//oPp2vTs3AVVJQJUiVhVARVVz3p9AUTFOSeqUBVomsQ//fDj4qXF8fEJw3z33t0rV6/45Uo/WYgYwN+Hl2oR8/jiRgAAAABJRU5ErkJggg=="

# V-Wagen (Moderner) - Fallback
ICON_VWAGEN_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAICAIAAACOpC0PAAAAB3RJTUUH6gELByIbufKlvAAAAoZJREFUeJwFwUtvE1cUAOBz7p3ruWMPmdjjsT3EDxLCQ0iNBCFiB1WldtsdVTf9U0hdsWHbSuzYs4jEAgRIeZBA7VIbG8ePODN+zePOPf0+HF3ORqPR57PTvFXQBFprQEBERAQCQAACAMqINBESccYZY4igiYhIKXV+dp6lKQEgMm6w+lbDcTb2Dw4Mr7j557Nn8Xr9YP9gPB4N+gORE5yx1o1tpTUSASLjbDgYzMNAqcz1PM/z0jhmiDJfWC7n0XLBGOec1+v++dnnXpa9fPu22WoZQBRF6+cvXux8OA6G3677FadYGvzXnadUrNZ67Xblen29CLmKm82GzrLBxYCkE0dxvFrWGq2rYbfmbjpFNwzDMJiNx5c3b+1WSm670zYIQBjiUaV6z5JBxedC2ClVC7bghgFw13OlAZmdT0G6QsQAvu1YwiQptG0WDBZ5XsZApiph3HTLoZkvFWxCfXj42kDEOIl/efzkyf37neFwvVxJkUtUWnFLZi5nmqbKFDD2tdcFpTJNQua3fR8RkWGaJJMwmF3NpDC5ISxLrhYLpam2YY1AG+s42X+4//749A1jX5bzk6MjlaliqfTQK6dJNP3eRwacGcP+YL4IieBGq3U+z48mY8ZYza8mHI673cUqtCz71u5tIr3VaCylfPX3X2wyC3786ec/nj59tPfD6bv3mKhtf6t9fJIGQe3aRu/00/Tf3sU/HYsxf9Mt29e4ypplV0SREa33dnbD76N+p7Pt11eXl2cfP+zdvWNzfjWZ/Prb7/htONZaW5aU0pxOp47jbNqFr71+zsyVvLJEBAAAIAAFwAAIgAAEAABEmiYXF1mqWs16MF8sViuvWkmTVOYEAvwPrDxG5Tsp8voAAAAASUVORK5CYII="

# ULF
ICON_ULF_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAGCAIAAABb17kDAAAAAXNSR0IB2cksfwAAAARnQU1BAACxjwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+oBDQkCBI6L/j0AAAHASURBVCjPLdHNU9NAGAfg97ddm2xC+k0NiOg4I87gf4D4l+MV5KAePEA/ZGRsSytJv0u72WTf9YDn5/hg+PgIosnDeDwZ53nearY83wNARETUajaTJAVAIBARwZEjIgCNej1J0tVyeXtzc/rxNFBhOp8KgYM4fhkfAELC0Y/v375cXNRqNRYEgAgABATb4q7fbbdfhZWoJP6Lc+wKR8S9Tic+PAyDkIiSNIEAOweC8rz3Jydn558liHqdzm23v1jMokrVOdJaM7MXhDbbfTh59/X62lOBY9a7HQHK9wVEYYu3x4dXV9ey7DFzEEWOma192mz2KlVmPvt0LlfLZWm9bC1mR5Xq2mTMrpDlXGuhM2tyZ60y+qDd3qSpKAGAM7oWx6PRSErsOxaWc1uUtzvpOC/yN1HoVvPNcDD+O5HdXufn5WUt8FebldS64al8vaTCWlnKXkhTFFVrzeBeAXElckSP6+32/nckS5nOYilUrovMlDItlZcYw2TrSo37v+56Pfx5GI+Gg+32iQgC0Jmezee+5xtj9pvNZnt/lk6JiPAcCHLPwdyoNdLpNEkTFShjTBTueb4vhAChXPaOjl//A2YO+xQMJTAwAAAAAElFTkSuQmCC"

# FLEXITY
ICON_FLEXITY_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAALCAIAAACCpFiiAAAAAXNSR0IB2cksfwAAAARnQU1BAACxjwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+oBDQkNH4N2Kx4AAAN8SURBVDjLTY7PbxRlHIe/P953ZmdmZ3a3u9AKhdLShKK0VaNRL7YXIAYJmpjGGP8QD3rWkHjQP8Gbib8ORgkQDURUEj2QygaktJYWul12u7vdndmZ2Zn36wFifJLP5flcHtxuNgUEBcCYkckJEAEAQJ4OAAAQlFZiJDM5/if/B4IgGMNaI46MwRyG8fBOvZ4k8cuvvEpMgIACihUwGhEUVAiYRuHVr7/pP9xuXbrioGEiBhAAA2BIRGAflH3uXNjvVq/9Qk+fJ1UoiCCCIhnTYGk5OFAdfPmVhyK5gIgQ1AlNLggwIiq/vlybPb584YJd9PFhs3X9p6s+yFgpyEeZyZJwP/QrFWQCIhQweZ6koy++/86z7PffelvEoBExImBAAJFQKyRGlG8v/dDsdt87c75QsEkzMps8lyxNokhrix0XNQ36YWOQnH7jLG4+anx68ZOxSuXK5cvlTjdgdUfSYQ5a63gYV8efQYKkv7/40mK33WnV746BWLpwfzhQ5TFhxF5v1nEHWdpKRodfeK5arf35+00qBMi012p5jpumcQBm2nH7UdLwvLNnTnc6ex98+JEahqHrOjd+/S03xra1XR3Xza1gfJK1bu00Ck5RMWRhlwUQ0VZYKvpKF6wkKlYPMnPUj4JySQ+TUHpxnAwGEaSpN1FRAlmS1cYPxlGUbK3riUnK9ixt3fpr9cWFxXDQ53dWVqJBr9Pe85xCFkVoa2PZpaDkuYWS75WKrsWkACzXGQ4TX8xk7YBtqdS2i0HJ1mSJmSz7rutEAlapSIostoOi53tO0XOcgrYUk6U9YgFTmpwoet7JuRMF11FpEs9Z1rNTRxLEa1H8OB69e2q+5PugGAiNARrlaT76cWf7UNE9VZq5988GMb95bHq6VsuM/O159QebLLB07MiapULBlYWFRGSEwMwMaCMkUXTj9t3D5WBpZsYAaJA0jBTE8fWPL85qBmFgGNPc+Xm7naaMKAIERJpyrWh+vt/Z31xb70NGwJtbj2xERAiFtK1yk23s7u5OHUI/2Lj5BxhgMUaMAshAMmYGSk22c28dTLaW5a99/hk+2NnduL/GYhQjAgkIAK7ertdqtXKlst/rNRuNxefnPT+IkiTq9wWfAGiEiAnIgDFGMsk8P/Acd9DZu7W6OnX0qBcU283O43b75NwJECFCMpIjiODU8Zl/AQJfwL2xhZLWAAAAAElFTkSuQmCC"

# Bim Alt
ICON_BIM_OLD_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAALCAIAAACCpFiiAAAAAXNSR0IB2cksfwAAAARnQU1BAACxjwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+oBDQkIBQNjJiEAAAQXSURBVDjLVZTLb5RlFMaf816++b7p2JkOl4ItbXGQBBHFakKkqDTYhQmuXaoLFy4kRqMx/gcujAvDRiEuTEw0LgyEGAgOCAkIBI1KQ0vpBRhocS7ftJ3Ld3nf97goGDzJyTk5z5Pn7H5ULpcBMDMAAEQEgMEAYa0BZiYiZiYCkcDDI/5fa7b/9na7VavVPU8PDAwy86MqALVmcs6taQCSJFlcui+lBIOZeW0AAAshrDGlUomZhRBEVKlUAPT39xPRo7mVSuXs2bPZbHZiYiJJkkajYa31fb9QKEgpmZnK5XIzDFUmQyS0p7XSxKw9T0qZpEmaGGvTOE6FELlcj1La2pSEPH3qZBiGBw8eDIIsCFLKdquVGAPHGT8jSGgtPS/T7nasMZ7nra6sZjzPAWmSWpPmC3kF8PzCgmMCu7GxseMnTpwq/zo8+Pi+vXu/+/4H7emPP3h/dnaOmUdHRz/7/Itao/nJh4eUUrdu3SoWi4c++hQk33vnzTBsSKlWWq2MsHN/HOvJ57a/8Mbhr7+xxnx1+Msrl6/29j7W6nTgmAijzz2jGKjVG6kxnW53//j+KEqkn6s2ms2VFVZB4iwYi/cWjTVP79x5txqS8uIoZsDTmogcAKDT6dyYmd06MtxptRPP++12EMetwkgDKvB8dLvVWqMulJyfn8/39gIgEkIwJicn8z0559g5l/G9bqfVV+jN5XqMM0oSCURJYo0RQF/gmbgd+FqQkEoqrdIkiuOu0sqyc+wADjI6TtOeILuurxjFnajVUTLnHCRICQr84PqNGRKSzpTPVI8f09b9ODc3/sTW3Z7vTCqUVrms63RtnPwt6Uq1Zp0bXV8cVZ5LIj+fPzI1XRX07sjWnsTAukV2P9WqQ8PDtdnZt57cJtLUkZBexqysEhuzYf2RyclNmwcri3df37NnJlzec2BcgdG9dk3+ObVPw01Nx1LJao2ZHMCAFIJ871lBKyaNhLTdWDLHUkTbSzQ4EB79NuOcBBIh9vqZxrnzJeuicxdUYpk4BRMAJVvjL+0+fzEk2sUcXZ/u3/ciwKreqB+dvvm8whhhvtv9yzrWWjAxEYgJvMS8w3KBcRs8qUVKkoiq1lISXdO0BKWBOvMucJuJHV/WKkskwAyygCNuXby0hQBBBeOu3L8/8/PJtw+8SuXyL0t3KuHs7O2Zm/ko4guXpDFw1kpyUmx45eW61m0iAFnnNgOr/1SXp26clqIRZF9rNjdu2lh8akckxB3AAIp5hNG8+jvqIaxxBBtkRGlbdXBAMxTRUGlbbnhoS6lE5XL5AZUAxzy/sFAoFDxPx3GyvLw8MjIsSDyEGQNIjZmbmx8c2sLsmmGY8YP1xeIDdDxgDTcaYbvV6ltXJKLFe/eGhob8bAAHEIm1T8C/kTBUcj/lvpIAAAAASUVORK5CYII="

# Bus
ICON_BUS_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAHCAIAAACQi2qmAAAAAXNSR0IB2cksfwAAAARnQU1BAACxjwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAOwwAADsMBx2+oZAAAAAd0SU1FB+oBDQg4Nfs+SkkAAAIMSURBVCjPJc85T1RRGAbg9/vOOffcubM7IgqDCdg4A7GwMBYkdGLsbfwFJvrfwFho4UJBYVxiAHc0hmUGhsWZ4S5zmbt8FvRP81CndyQiAAACkKVJODzLCQKx2ilWqwAAgRBILgwEEPH9YZakBAihVK4oowkCQIQulBaRo2739coKQxRzv3vYWXubCTKI1Gu3H9xnVqZavTw9I4TdjU1AiIgEm6urCEc5icMys7RUnWqmIiAC8d17y7M35jSAUb//5sXLY8lyQZKMueASmBhW6y/Pnhvr1ireteaUa+362rpXqqTJWClF1smMo4y+UnD62z/lz++uH2XMNhr1wuDxk6f64tc0TqhMqoxJxqVyWSk9igOlrbB/qd7QNPa8omtdrzJRn5gYRYHWjtJmHIXGODHTP39oC0Xj6ZJXKli/Nd92rNUAtHXnDvaocfVHrXEzy1rbv2IlB7XG16pp57K8vbXfanWslSx91D89POnVHOfV9VnFeHjcrcWJIQyYB6rXaUx+Po+niequx8waABwji4vnG9/OozBI4nfNxlhx8SSIjRPH0YB4kKY5mBnfs/Tszq2dT1vhsA+l/DhxNBSwPlmLymV3/zQpcSc4IwIRUad3BBGAcslzESba2fk7iuJWe0FyIRKC5CAwCJQmyccP79ut+XKlBFJCooTSPOvs7gVRMN9eyAECiATE/wFeLf0Ld9L4ZwAAAABJRU5ErkJggg=="

# --- 3. DATEN ---
STATION_MARKERS = [
    {"name": "Schwedenplatz", "lat": 48.2114, "lon": 16.3783, "lines": ["U1", "U4", "1", "2"], "rbl": [4205, 4212, 4208, 4210]},
    {"name": "Karlsplatz", "lat": 48.2000, "lon": 16.3690, "lines": ["U1", "U2", "U4", "1", "D", "62", "WLB"], "rbl": [4202, 4216, 4617, 4214, 32, 40]}, 
    {"name": "Stephansplatz", "lat": 48.2082, "lon": 16.3738, "lines": ["U1", "U3"], "rbl": [4200, 4206]},
    {"name": "Westbahnhof", "lat": 48.1960, "lon": 16.3350, "lines": ["U3", "U6", "5", "6", "18", "52", "60"], "rbl": [4920, 4921, 4600, 350, 354]}, 
    {"name": "Schottentor", "lat": 48.2150, "lon": 16.3610, "lines": ["U2", "1", "D", "37", "38", "40", "41", "42", "43", "44", "71"], "rbl": [4209, 4211, 4001, 4002]}, 
    {"name": "Landstraße", "lat": 48.2060, "lon": 16.3850, "lines": ["U3", "U4", "O", "74A"], "rbl": [4204, 4213]},
    {"name": "Praterstern", "lat": 48.2180, "lon": 16.3900, "lines": ["U1", "U2", "5", "O", "80A", "82A"], "rbl": [4207, 4105]},
    {"name": "Neubaugasse (13A)", "lat": 48.1990, "lon": 16.3450, "lines": ["U3", "13A", "14A"], "rbl": [267, 266]},
    {"name": "Pilgramgasse (13A)", "lat": 48.1930, "lon": 16.3550, "lines": ["U4", "13A", "14A"], "rbl": [272, 273]},
    {"name": "Alser Straße (43)", "lat": 48.2170, "lon": 16.3420, "lines": ["U6", "43", "44"], "rbl": [4219, 4220, 100, 101]},
    {"name": "Hauptbahnhof (D)", "lat": 48.1850, "lon": 16.3750, "lines": ["U1", "D", "13A", "69A", "O", "18"], "rbl": [150, 151]}
]

# Koordinaten-Pfade für Linien
RAW_ROUTES = {
    "U1": [[48.1530, 16.3850], [48.1700, 16.3800], [48.1870, 16.3750], [48.2000, 16.3700], [48.2082, 16.3738], [48.2130, 16.3780], [48.2180, 16.3900], [48.2250, 16.4000], [48.2450, 16.4400], [48.2600, 16.4500]], 
    "13A": [[48.2020, 16.3380], [48.2005, 16.3420], [48.1990, 16.3450], [48.1970, 16.3490], [48.1960, 16.3550], [48.1945, 16.3580], [48.1930, 16.3600], [48.1850, 16.3650]], 
    "43": [[48.2150, 16.3610], [48.2160, 16.3550], [48.2165, 16.3500], [48.2170, 16.3420], [48.2180, 16.3350], [48.2200, 16.3300]],
    "D": [[48.2150, 16.3610], [48.2050, 16.3600], [48.2020, 16.3680], [48.2000, 16.3720], [48.1950, 16.3750], [48.1850, 16.3750]],
    "U2": [[48.2200, 16.5100], [48.2150, 16.4500], [48.2180, 16.4200], [48.2100, 16.3570], [48.2070, 16.3580], [48.2000, 16.3690]], 
    "U3": [[48.2110, 16.3100], [48.1960, 16.3350], [48.2082, 16.3738], [48.2060, 16.3850], [48.1900, 16.4000]], 
    "U4": [[48.1900, 16.2900], [48.1900, 16.3500], [48.2000, 16.3690], [48.2082, 16.3738], [48.2114, 16.3783], [48.2166, 16.3730], [48.2250, 16.3600]], 
    "U6": [[48.1750, 16.3350], [48.1960, 16.3350], [48.2150, 16.3400], [48.2300, 16.3500]]
}

LINE_COLORS = {
    "U1": "#E2021A", "U2": "#A365A4", "U3": "#F67F21", "U4": "#009641", "U6": "#9D6643",
    "S": "#00549F", "13A": "#E3001B", "D": "#E3001B", "43": "#E3001B", "1": "#E3001B"
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
    if route_key not in SMOOTH_ROUTES:
        if "U" in route_key: route_key = "U1"
        elif "A" in route_key: route_key = "13A"
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

# --- 5. DATEN & LOGIK (ÜBERARBEITET) ---

@st.cache_data(ttl=10)
def fetch_data(lines_to_check):
    """
    NEU: Sucht ALLE RBLs für die gewünschten Linien.
    Damit finden wir Fahrzeuge auch wenn sie weit weg sind.
    """
    if not lines_to_check: return []
    
    # Wir sammeln ALLE RBLs von ALLEN Stationen, die diese Linien führen.
    relevant_rbls = []
    for s in STATION_MARKERS:
        # Hat diese Station eine der Linien?
        if not set(s.get("lines", [])).isdisjoint(lines_to_check):
            relevant_rbls.extend(s["rbl"])
            
    # API Abfrage
    url = f"https://www.wienerlinien.at/ogd_realtime/monitor?rbl={'&rbl='.join(map(str, relevant_rbls))}"
    unique_vehicles = {}

    try:
        response = requests.get(url, timeout=4)
        data = response.json()
        
        for mon in data.get("data", {}).get("monitors", []):
            for line in mon.get("lines", []):
                line_name = line.get("name")
                # Nur speichern wenn die Linie relevant ist
                if line_name not in lines_to_check: continue
                
                direction = line.get("towards")
                for i, dep in enumerate(line.get("departures", {}).get("departure", [])):
                    # Wir nehmen jetzt mehr Fahrzeuge pro Monitor
                    if i >= 4: break 
                    countdown = dep.get("departureTime", {}).get("countdown", 99)
                    
                    if isinstance(countdown, int) and countdown < 40:
                        vh = dep.get("vehicle", {})
                        
                        v_id = vh.get("id")
                        if not v_id: v_id = f"{line_name}_{direction}"
                        
                        v_type = "tram_old" 
                        ac = vh.get("barrierFree", False) or vh.get("foldingRamp", False)
                        
                        if "U" in line_name:
                            v_type = "ubahn"
                        elif "A" in line_name or "Bus" in line_name:
                            v_type = "bus"
                        elif ac:
                            if line_name in ["D", "1", "6", "11", "18", "71"]:
                                v_type = "flexity"
                            else:
                                v_type = "ulf"
                        
                        new_entry = {
                            "id": v_id,
                            "line": line_name,
                            "dest": direction,
                            "time": countdown,
                            "ac": ac,
                            "type": v_type
                        }
                        
                        # Deduplizierung
                        if v_id in unique_vehicles:
                            if countdown < unique_vehicles[v_id]["time"]:
                                unique_vehicles[v_id] = new_entry
                        else:
                            unique_vehicles[v_id] = new_entry

        return list(unique_vehicles.values())
    except: return []

# --- 6. GUI & RADIUS ---

with st.sidebar:
    st.header("Einstellungen")
    gps_mode = st.toggle("Echtstandort (GPS)", value=False)
    
    if st.button("Manuell Refresh"):
        st.session_state.last_refresh = time.time()
        st.rerun()

    user_lat, user_lon = 48.2082, 16.3738
    
    if gps_mode:
        st.write("📡 Suche GPS...")
        if HAS_GPS_MODULE:
            loc = get_geolocation()
            if loc:
                user_lat, user_lon = loc['coords']['latitude'], loc['coords']['longitude']
                st.success(f"GPS: {user_lat:.4f}, {user_lon:.4f}")
            else:
                st.warning("Warte...")
        else:
            st.error("Kein GPS Plugin.")
    else:
        sim_scenario = st.radio("Simulation:", ["Stephansplatz", "Ring/Oper"], index=1)
        if sim_scenario == "Stephansplatz":
            user_lat, user_lon = 48.2082, 16.3738
        else:
            user_lat, user_lon = 48.2050, 16.3650 # Ring

# --- 7. FILTERUNG & ZOOM ERHALT ---

# Welche Linien sind in meiner Nähe?
nearby_lines = set()
for s in STATION_MARKERS:
    dist = haversine(user_lat, user_lon, s["lat"], s["lon"])
    if dist < 1200: # 1.2km Radius um mich herum
        for l in s.get("lines", []):
            nearby_lines.add(l)

# Jetzt laden wir ALLE Fahrzeuge dieser Linien (auch weit weg)
vehicles = fetch_data(nearby_lines)
vehicles.sort(key=lambda x: x["time"])

# Karte erstellen mit gespeichertem Zoom
m = folium.Map(
    location=st.session_state.map_center, 
    zoom_start=st.session_state.map_zoom, 
    tiles="CartoDB positron"
)

folium.Marker(
    [user_lat, user_lon],
    tooltip="Du",
    icon=folium.Icon(color="blue", icon="user", prefix="fa"),
    z_index_offset=1100
).add_to(m)

# Linien zeichnen
for line_name in nearby_lines:
    route_key = line_name
    if route_key not in SMOOTH_ROUTES:
        if "U" in route_key: route_key = "U1"
        elif "A" in route_key: route_key = "13A"
        else: route_key = "D"
    
    if route_key in SMOOTH_ROUTES:
        folium.PolyLine(SMOOTH_ROUTES[route_key], color=LINE_COLORS.get(line_name, "#888"), weight=3, opacity=0.5).add_to(m)

# Stationen zeichnen (Alle die zu den Linien gehören)
for s in STATION_MARKERS:
    s_lines = set(s.get("lines", []))
    if not s_lines.isdisjoint(nearby_lines):
        icon = folium.CustomIcon(ICON_STATION_B64, icon_size=(24, 14), icon_anchor=(12, 7))
        folium.Marker([s["lat"], s["lon"]], popup=s['name'], icon=icon, z_index_offset=1000).add_to(m)

# Fahrzeuge zeichnen
for v in vehicles:
    lat, lon, rot = get_vehicle_position_and_rotation(v["line"], v["time"])
    
    if lat and lon:
        border_color = "#0066b3" if v["ac"] else "#d32f2f"
        
        current_icon = ICON_BIM_OLD_B64
        w, h = 32, 8
        
        if v["type"] == "bus":
            current_icon = ICON_BUS_B64
            w, h = 30, 8
        elif v["type"] == "ulf":
            current_icon = ICON_ULF_B64
            w, h = 30, 6
        elif v["type"] == "flexity":
            current_icon = ICON_FLEXITY_B64
            w, h = 40, 9
        elif v["type"] == "ubahn":
            # Hier: Silberpfeil ist Standard für U-Bahn
            current_icon = ICON_SILBERPFEIL_B64
            w, h = 40, 12
        
        display_rot = rot - 90
        
        icon_html = f"""
        <div style="transform: rotate({display_rot}deg); display: flex; flex-direction: column; align-items: center; justify-content: center; width: 40px; height: 40px;">
            <img src="{current_icon}" style="width: {w}px; height: {h}px;">
            <div style="width: {w}px; height: 3px; background: {border_color}; margin-top: 1px; border-radius: 2px;"></div>
            <div style="transform: rotate({-display_rot}deg); background: rgba(255,255,255,0.8); color: black; font-weight: bold; font-size: 9px; padding: 0 3px; border-radius: 4px; border: 1px solid #ccc;">
                {v['line']}
            </div>
        </div>
        """
        folium.Marker([lat, lon], icon=folium.DivIcon(html=icon_html, icon_size=(40,40), icon_anchor=(20,20))).add_to(m)

# Karte rendern und State updaten
map_data = st_folium(m, width="100%", height=500)

# Wenn der User zoomt/bewegt, speichern wir das für den nächsten Refresh
if map_data['zoom'] is not None:
    st.session_state.map_zoom = map_data['zoom']
if map_data['center'] is not None:
    st.session_state.map_center = [map_data['center']['lat'], map_data['center']['lng']]

# --- 9. TABELLE ---
st.subheader("📋 Abfahrten (Live)")
if vehicles:
    t_data = []
    for v in vehicles:
        t = "🚋 (Alt)"
        if v["type"] == "ulf": t = "🚋 (ULF)"
        if v["type"] == "flexity": t = "🚋 (Flexity)"
        if v["type"] == "bus": t = "🚌"
        if v["type"] == "ubahn": t = "🚇 (Silberpfeil)"
        
        t_data.append({
            "Typ": t, 
            "Linie": v["line"], 
            "Ziel": v["dest"], 
            "Zeit": f"{v['time']} min", 
            "Klima": "❄️" if v["ac"] else "🔥"
        })
    st.dataframe(pd.DataFrame(t_data), hide_index=True, use_container_width=True)
else:
    st.info("Keine Fahrzeuge gefunden.")

time.sleep(15)
st.rerun()
