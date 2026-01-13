import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import math
import pandas as pd

# --- 1. SETUP ---
st.set_page_config(page_title="Wien Öffis V31", layout="wide", page_icon="🚋")

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

st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GRAFIKEN (BASE64) ---

ICON_STATION_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAMCAIAAADtbgqsAAAAB3RJTUUH6gELByIjkfAdIgAAAoxJREFUeJxNzstrlGcYhvH7eQ8z3xwSJ4MxaWszJhiQduER3Fh0EWxr0ZIuohQhbVHU1iOIq2BQQjyQorVd1O5SaEUqQWuxbTAgSAOCqAhRkC4SjSaS4/jNTOY7vM/TRUH8cf0BF/i1IHAiXK74J3qnG1um8kun6gvTLe9PL26aqmmYXfdBdegWi7wZMTNE4BysdaNj5T0Hw8GbKp+HAGnPbt0S9P9i1q7O9PWqpnfF94mIjOViEdkscRjBGgDh9Rulw8fkxSTlc8QilSq981a6p6u06wAtqkUcY2EB1kApnpnRrcszF783sEaKxfKZvurZC5RIIJNmv0TWcmne1K0wq1YhlXTPx5WXEgBBIKVyoqM9+12famww8YOHlW8vRH/e0M3LnHCSAFJQytWlbcdnurlgt7fLwO8qnQGzOOcd2Jc8+DUAABSPP5cgkHRGEbTVEy/nQCTC2iYalheEWURe/jsGZgBQWhWWUjUQ4YVqRCwSAxYIgZMX/7h0fRgJA4JdCL/Z2bb/87au879dHrwrXhIswkwuZlBpzt/RvsFw7KzRzyamd3f3/33rPjLe/0colvqv/vPRppU/DtyenZpHyoNzsAbVAILj+7Yd/fJjo7W+MnRvT8/Psy9mka8FC5xLpj2kkpOvyvcePy1GjnI1pEhpFc/5rU0NP3R3bl7/HgATxHGhse7auf2ZjOdixyKLsqlHo5NHTl+amPf/Gh5xUYyEltCxX/mkbc1P3V+8XZ8Lo9gYTc6xUoQ3DN15dOjUryOjkyqdrMumZoplEGqVOrxzc9ferVapMHLWKADEzLFjEXHMWqkHT55t/OpsGLnaJTmO4sixlzAVv3K088OevZ+GUUwEozUAIvoPOtpWT2fW07IAAAAASUVORK5CYII="

# Silberpfeil
ICON_SILBERPFEIL_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAMCAIAAACfoWgaAAAAAXNSR0IB2cksfwAAAARnQU1BAACxjwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+oBDQkSBMRJ7GwAAAQiSURBVDjLdVTJblxFFD33Vr1u92C/HuI4njseAsRxUAZhUCQ+APMNrMCfYj4hbCNWhF1WIHYJysDCgUQQ29gxiePY3Wm323H3e/2GupdFxwIhcVRSlXRL99Q9qnNor94AoKogAgGqUPw/pL8RMUAAVAVQIgL66x/8qwSA/9PIAgpQvwkpnEuJiIhUFEwAEVTVAAJSBqkCBFUACoBAClXtn1WBU3oF1KUpMzOzE0fvAIAUsP17nZPOy52dOImePPmNiKrV6tFhq5DPT9TOMxuPATAUjkSVoK7PoDilPR0ZgJy+I46izY31gYGBkZGRvdevh/zS+Pj42Oi5sfEpYkN79TdpEn1769aZ6pkkTTJZj5lbzaZziSiyNt9tv+gcNc5WC0ypCGIRb6jm5fwgCJgZ4MHikCgR9/UhhaiKiHQ73b5ig4NDZDgMAsOmF4U3bnw6d+F9C0BFfl17vHBpcffVy/n5uUq5vL7xjKBQnBsdCwPZP0qa3c7UxMTe3q44jNbiTNLe2txyzhHzwqUPX7x4xcb6vh8EQZIkBJmZmdzd3SbiMAynp88P+aXn29sD2awTCcKAoBbQw1azG7wV1a2tnfkLc0613X6byWaOj9sj50aPu9Fe40RVUs5tbh0YtjHn5memWketQr4IliR1a0+eGjaT46OHraNUBKq16clWs1UoDh3sN2Zm3zNephf3enEURdHDhw8WLi9aQLe3d4aHz3qeyeUGmA0RQyFpAhHDVCwWSv4QqQ4WBitln8kUCjknqbUmkzUiYi1Xyr41XskfMsZESSJpkqZpnMRFkmzGWsvMbIwVceWS/9fznThK6NVB486d256JG42wVKr2orBYzP3+9LGLo3zBz2YyY5M1MDExFH3Pqbr6wW4UBUdHrWx2YH5+gWwWRIZEVFWIgF7Y3d/fjXq94mAxX/TzRV/SJInjTEaAdPnzLywzGbKHzWMRjeJemqRQpHHiEonj2HpZAonAQd75gAiAS9NOpxuGkSiDiEQUcP3f3Xccaxj2Tk5O4jj1MnlSjePEsBHH3W5iWG0Yhre/+/7atathEARBEMfJ25POcfuICaqSzeb29+vWeu12W1WZGYC1NuqFvV5PVZP0TbN5zGSstQCcc8aamdnZjWd/1Bt1FQJ088+dYqFYrVas51Uq5YOD+vr6Bu0dNN7UD9bW1uqNOoBKpfz16iqUFY6AUqW8/NnyR0tLjx79wkSqcvGDi6urq865paWllZWVw8PDmze/uXx50fM8VVXVQrFw7fr1lS+/EpV8Pq+iA7mB5eXlM8PDcRwz88dLn0xP16gfmf3UJCKo3v/5nl/yp2o1Q3T//oPp2vTs3AVVJQJUiVhVARVVz3p9AUTFOSeqUBVomsQ//fDj4qXF8fEJw3z33t0rV6/45Uo/WYgYwN+Hl2oR8/jiRgAAAABJRU5ErkJggg=="

# V-Wagen
ICON_VWAGEN_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAALCAIAAACCpFiiAAAAAXNSR0IB2cksfwAAAARnQU1BAACxjwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+oBDQkiICcMPk4AAAPNSURBVDjLbVRLb1tVEP6+c65v7Dzs2Emchx1QeKqpCn0SR7BpNt2g0v4ONgh2XSAkFqyAJfADoGxAtLQShR8AqCA1rUglRNMmrfNwkia+cXLte+6ZYWFTisQsznxnHjpnRvMN65sNBUAAUFUABuwCoHv+4wbIJ67etZv1tJ3/KuL/pBsfdGEU7RPKJ+HaU/rfh59GBBXa+x0BkKIkSTajvdXVFQCgUQUBBcpjYyOjo/n8EI0FwPpm49dffu60D7Nh1lpL0quoqIgQCmi3lF5xIEgRCawFNU1TKFTUGIoIDAEYY62xBHttUACaJM4Y7u+3Oqk7f+GiqgYkf/rxxuvzcx0FyCiKWvv7JDudTj6fL5fLziUgrbXWBqqq3i8tLZFMEmesmT1yJMhkSMaHcbavT1UFUm/U48M4m8167/v7+4eGBm8tLkJ1rjb33ZeX3zz/ljEmAASKTz7+dGSyehjHB7s782/UxsuTv9+8WZ2u/Hbrj3yhBKOb9bXxiYoXeby9XjtxIrXsU2por350pTRZNdbuNDaKpTGn6LSi8kihWCq9cuzVO7cXtx/vbG9upJ5D+fxYebTZ3I2au8PFEQPQi287l/pUCKUByFSsMSqqquK9T1yaOpcmnSSGS4WgaiKp8eJd0onjpNNOnRMRwpOgwABxfCjeUzUITCbMANo6aL384kt//blMWq5tNj784P3jwoEAmSDYVTXOJ2Fo9qIkl5nIZAVKBQ2NNTDGMlhu7gwo48Q5kalSKSOS6bPZIOuhXtMkTVeb0aBH0h8WhFHiioO5dttFLimXig2VDdr3Ll0KVFWAoWNHBvuyAU3S2h/J59cbjenjx+/V64PjE72hpAIQKIH8dmFytNyM9pPU5wuF0BglCEKEIgbav7H+wszM+lbjmUrl3spKXy5nvde4PTxcLEKz9bUMNABZrVST/oEol4Oi5dzyo0cHBwcPk04Y9o2UClAVQHrEUvF+5f6Dhlt3ztGYwvMzbfGp+C7BSBgair+9tdVqHTTqa2H/QFAorNXrNKY0Xk5Tt7m6uhe1WN/c9kn79p1F7/3dpbvXrn5PQ2OM957kXK12+szpLz77HF06iYhIEFhjLEkVLU+Mn6m99vVXlwkGmeDChYuZMHPlm2+99y5xLnXGmunp6bm5WtxuDwwNbm1tPbz/4O133wkADcLw5KnTIJ6dee5Rvb6wcLZULIro9evXzp07d/To0ampKRElewuEht6LqAIIw7BSqSycXbDWqmoum4vjePne8qmTpyrVKogbN36Yn5+fnZ1NvVdRAMPDw7Dmb2pFJgVZhojuAAAAAElFTkSuQmCC"

# X-Wagen
ICON_XWAGEN_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAALCAIAAACCpFiiAAAAAXNSR0IB2cksfwAAAARnQU1BAACxjwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+oBDQkvFcQRhCAAAAPfSURBVDjLZVRNb1tVEJ259/q9549nx37NF2nTxG6IaCI+mrAgVdogITYsWEOFEql0TXdE+QvAL2ADCxZs2IBEVbpAoqoERSVxahJo0tLWjnHqOE7wi5/fu3eGhZ0UibO6c2fumTnS3IOV2i4AIHSBAAx4HHXBAMh8csndYu5luq+OT/yc6n9g5v9EioB3yk92yjvIXRLu0XNvHgZgYAbAXm+BvebcK0QU3AsYe3MgAgKeNBMo9ht1Zdvzly4rpQBAsdHffndjx3aJFAgUAKInnDWx6Q6DiPxclUS0pFIIxKzJaGImQgBggWAJZCG0EIgojDGhoSgKwYCvzeOff7SVM3fpIgCoMOisrv52+Z13A8OgEKNoZ+O+MUYp6cRTp0bHAUAgCiG6GpBor/y4tVcHFVNKDp/N2246NIa1aTQPt55Us2l74ky2vFkiokw6oxynb3Dw19s/CaW86Vdv3Px+bv4iICgCs725sVetWK7nxJ16tTwzc0EiNht7Mbt559YPaa/fiqlntb/7h0Yi4la9+sr5l+r7jfGxsX8O97/54vOMNxSLp4J2q+0fWLazG4b3DvdnZmekkM1O24knbt+6abSOjHZf8+6slRqNupfzFCBKJSwbdeD7JjBRhzpBzHKIyELhSAmhCbXRQbt92CQGxQalEADAxGRYh63WQSwKyUSOZcfjKbY16o4SkplBCAGQsCyfNGroqJiVn6xUyqcGhnD7r+3lq9fen31dhxEZaoZRO+oc6ehMtv+g4w+nXQqNYcPEiMAMUoinR36/sitBO23ZiNyHEpXA7tpKBUChoVakI62HMtnKYWPASe7rkEDEZ+c2OHbBlW+/Na+YUORy0cvTAlECWC0/oaTj+7mR041HD83wMCLGEBEkAzMzkcan5eTI6WS1mhvo18Yk0q4h6uaYARBkO3C18Y/8zOjZ2oMHlMlYYZs1DnYau9vlYHqKNCvLtguTk79vbaFAIWUYhn9u/sFEUoh0tu8g7BAREQEdfw3kWrV6r3SfiVFg/lxBqpghAgYppVSSiMIgKK2va62llIlEauLFiTDoZDJu9oUhSu99/dWXC/NvKKliVz+81m77UohisbiysiIAUynXGIOIH5ybfHNh4ePl5UajAcy2Y0uplpaW8oX8Z598+qxeL5U2bNtOp93zU1N3f7m7uLjoplIfXb/uplLJZJKZW62Wm0rZcbtWq1Zqu48fPnrvyhURs7G823MuBGai9WIxXyg48XgURWura/lCwfM8AJAIiMjMRNR1ksgYPAGAkDKKNAAYbdbXi+PjY9lsVgixXiyOjo7lPI+IumbS3ZV/AegtHdiMMk7cAAAAAElFTkSuQmCC"

# Type T (U6)
ICON_TYPET_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAANCAIAAABU/bu/AAAAAXNSR0IB2cksfwAAAARnQU1BAACxjwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+oBDQkhBUclucoAAATDSURBVDjLPZXLb11XFca/b+19zr3H16/GqblxnLSyceS8mjZIQVBoEaAMisQIhMqAoKodoLYhPP6ASgwRCKmTlhkMoCABUanCI1HTKqJymjSmVLUS+sjDMfiFHd/XOfecvddi4KTfeEm/b7DWb3FpZdXMAIAkTGkCRqOoGY0wAGYQcSJSVRUIgjQARsAI73zQaGrYDimkmlah+vDfH1jQbCCbntlnBADeHYInCSBUVa8oKPTKivEXP/3Z5uaG846kmZmh0Rj8zokTv3z55X6eQwChE0fvPPmtb3zz7Llz/11eiSGo2fDwyKkfnFpYeP/ypcufnpraPTExMzPdzbsWFUBjaGibzaWVVefc73/3SuaT+5rjoao0aKQ6iHcOqiEEM1PYdkWIp9CL0SSaQlGaSYxqkSRJM0SLiXM1XzMKoAYNoapCnJu7+NRTT0/s3k3SAwgxtFqtkV27EoS5M39JqqpvMWUy85XHB4eGhd7MEu9VVUSc9xu3F29eeUeDBo0F3Re+/oRpIpI6J2YwRWkhMcy9/rrkBaGpsHno4NiDe3bvnbyzsTE5OWmAB62Xd/+3tn7u72e//MXPzb/1VjPxLMow0PAPTrx54R9mjCE8/thjFy9dpohAv/TZY++/PX9f3upmg6VzV5r3z118JwKzMzNFv7i1eEshxx5+6D/XP86XV2vdTmg06uP3/+HM36amp6b2TNNoNHFwy7eXs3pmYFnFSN9NapuwLZf0iwqWiKtLLYtqKr6v6BRlt98PLi0q0/qAc+Kcd0mmYK+X572ijGYiWZLU0zQdyFQrHRwuy6rd6X/80fWbizcilQavlFZrK0Ws9XqfyrIRWNYvk2h52dvhE8u7cB4ah8pKN1s0TWMYpUfRTYy+KEIiw+Kk100sNmu1TgzL/YpVyCi1aKGXq4p0uwMRad7O2xva7UEDWOPy6tqvX3xx5V//PLj3AanXbr/62qhqT0PiKMePD/hUownhRYIZRZzj0up6c/7KYrc9kdQXRWa/9kSMUUmBGRBBH4HUfXT+zWYnv9nPJxPf2b9/fHQE9fSVs+d//uofd4xP+L5Wo5PNrXCgduRALFTP/DUxdabeEndgf2Nsp5qamagkZiRByNWr1bvzIs77tMhSf+yoqTmQIIhUoVHBUFy6XHaKEhbFJwdn241s567xfd0eaQT85vr6r1566cAjnxm41ZCA9/ZOLFRaWRkqzty4ObS+QdJ7b5TtwzfY2p2tS6Oj1ejQe3B56kc/uKFQGESEFJgqAOqNwcaHTYE0lwQTW60d9Xqxfuftd+eHf/Pbk6d+zOuLi0W7vdVuFWVVlv2Tzz67trbar8pG1uh02o2h4aOPHH36mWe+/9zzTsRgEUYAahY1QoyVU2cCBUB++8kn981Mv/DCT0JeDI40JPF5u1uv10/+8EeHDh8Sys6dYxrjrsk9Pk3rtR21obExZy6E8nvPPX/hwoUTJ76b1tJU3OnTp488fOTRRz//p9f+DIAgSbvnUZJmik9UCQwONrKstrBwdXZ29vBDh524a9euvXH+ja8ePz42NnZXqCDMuLSyinsSNVPVCNB7D0BIM5hpNAVJAwH7hGNQmlBgRpF7cJpFVTVVyva2QURAd/cj3Mv/Ac+bomVUXkxVAAAAAElFTkSuQmCC"

# ULF
ICON_ULF_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAGCAIAAABb17kDAAAAAXNSR0IB2cksfwAAAARnQU1BAACxjwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+oBDQkCBI6L/j0AAAHASURBVCjPLdHNU9NAGAfg97ddm2xC+k0NiOg4I87gf4D4l+MV5KAePEA/ZGRsSytJv0u72WTf9YDn5/hg+PgIosnDeDwZ53nearY83wNARETUajaTJAVAIBARwZEjIgCNej1J0tVyeXtzc/rxNFBhOp8KgYM4fhkfAELC0Y/v375cXNRqNRYEgAgABATb4q7fbbdfhZWoJP6Lc+wKR8S9Tic+PAyDkIiSNIEAOweC8rz3Jydn558liHqdzm23v1jMokrVOdJaM7MXhDbbfTh59/X62lOBY9a7HQHK9wVEYYu3x4dXV9ey7DFzEEWOma192mz2KlVmPvt0LlfLZWm9bC1mR5Xq2mTMrpDlXGuhM2tyZ60y+qDd3qSpKAGAM7oWx6PRSErsOxaWc1uUtzvpOC/yN1HoVvPNcDD+O5HdXufn5WUt8FebldS64al8vaTCWlnKXkhTFFVrzeBeAXElckSP6+32/nckS5nOYilUrovMlDItlZcYw2TrSo37v+56Pfx5GI+Gg+32iQgC0Jmezee+5xtj9pvNZnt/lk6JiPAcCHLPwdyoNdLpNEkTFShjTBTueb4vhAChXPaOjl//A2YO+xQMJTAwAAAAAElFTkSuQmCC"

# FLEXITY
ICON_FLEXITY_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAALCAIAAACCpFiiAAAAAXNSR0IB2cksfwAAAARnQU1BAACxjwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+oBDQkNH4N2Kx4AAAN8SURBVDjLTY7PbxRlHIe/P953ZmdmZ3a3u9AKhdLShKK0VaNRL7YXIAYJmpjGGP8QD3rWkHjQP8Gbib8ORgkQDURUEj2QygaktJYWul12u7vdndmZ2Zn36wFifJLP5flcHtxuNgUEBcCYkckJEAEAQJ4OAAAQlFZiJDM5/if/B4IgGMNaI46MwRyG8fBOvZ4k8cuvvEpMgIACihUwGhEUVAiYRuHVr7/pP9xuXbrioGEiBhAAA2BIRGAflH3uXNjvVq/9Qk+fJ1UoiCCCIhnTYGk5OFAdfPmVhyK5gIgQ1AlNLggwIiq/vlybPb584YJd9PFhs3X9p6s+yFgpyEeZyZJwP/QrFWQCIhQweZ6koy++/86z7PffelvEoBExImBAAJFQKyRGlG8v/dDsdt87c75QsEkzMps8lyxNokhrix0XNQ36YWOQnH7jLG4+anx68ZOxSuXK5cvlTjdgdUfSYQ5a63gYV8efQYKkv7/40mK33WnV746BWLpwfzhQ5TFhxF5v1nEHWdpKRodfeK5arf35+00qBMi012p5jpumcQBm2nH7UdLwvLNnTnc6ex98+JEahqHrOjd+/S03xra1XR3Xza1gfJK1bu00Ck5RMWRhlwUQ0VZYKvpKF6wkKlYPMnPUj4JySQ+TUHpxnAwGEaSpN1FRAlmS1cYPxlGUbK3riUnK9ixt3fpr9cWFxXDQ53dWVqJBr9Pe85xCFkVoa2PZpaDkuYWS75WKrsWkACzXGQ4TX8xk7YBtqdS2i0HJ1mSJmSz7rutEAlapSIostoOi53tO0XOcgrYUk6U9YgFTmpwoet7JuRMF11FpEs9Z1rNTRxLEa1H8OB69e2q+5PugGAiNARrlaT76cWf7UNE9VZq5988GMb95bHq6VsuM/O159QebLLB07MiapULBlYWFRGSEwMwMaCMkUXTj9t3D5WBpZsYAaJA0jBTE8fWPL85qBmFgGNPc+Xm7naaMKAIERJpyrWh+vt/Z31xb70NGwJtbj2xERAiFtK1yk23s7u5OHUI/2Lj5BxhgMUaMAshAMmYGSk22c28dTLaW5a99/hk+2NnduL/GYhQjAgkIAK7ertdqtXKlst/rNRuNxefnPT+IkiTq9wWfAGiEiAnIgDFGMsk8P/Acd9DZu7W6OnX0qBcU283O43b75NwJECFCMpIjiODU8Zl/AQJfwL2xhZLWAAAAAElFTkSuQmCC"

# Bim Alt
ICON_BIM_OLD_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAALCAIAAACCpFiiAAAAAXNSR0IB2cksfwAAAARnQU1BAACxjwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+oBDQkIBQNjJiEAAAQXSURBVDjLVZTLb5RlFMaf816++b7p2JkOl4ItbXGQBBHFakKkqDTYhQmuXaoLFy4kRqMx/gcujAvDRiEuTEw0LgyEGAgOCAkIBI1KQ0vpBRhocS7ftJ3Ld3nf97goGDzJyTk5z5Pn7H5ULpcBMDMAAEQEgMEAYa0BZiYiZiYCkcDDI/5fa7b/9na7VavVPU8PDAwy86MqALVmcs6taQCSJFlcui+lBIOZeW0AAAshrDGlUomZhRBEVKlUAPT39xPRo7mVSuXs2bPZbHZiYiJJkkajYa31fb9QKEgpmZnK5XIzDFUmQyS0p7XSxKw9T0qZpEmaGGvTOE6FELlcj1La2pSEPH3qZBiGBw8eDIIsCFLKdquVGAPHGT8jSGgtPS/T7nasMZ7nra6sZjzPAWmSWpPmC3kF8PzCgmMCu7GxseMnTpwq/zo8+Pi+vXu/+/4H7emPP3h/dnaOmUdHRz/7/Itao/nJh4eUUrdu3SoWi4c++hQk33vnzTBsSKlWWq2MsHN/HOvJ57a/8Mbhr7+xxnx1+Msrl6/29j7W6nTgmAijzz2jGKjVG6kxnW53//j+KEqkn6s2ms2VFVZB4iwYi/cWjTVP79x5txqS8uIoZsDTmogcAKDT6dyYmd06MtxptRPP++12EMetwkgDKvB8dLvVWqMulJyfn8/39gIgEkIwJicn8z0559g5l/G9bqfVV+jN5XqMM0oSCURJYo0RQF/gmbgd+FqQkEoqrdIkiuOu0sqyc+wADjI6TtOeILuurxjFnajVUTLnHCRICQr84PqNGRKSzpTPVI8f09b9ODc3/sTW3Z7vTCqUVrms63RtnPwt6Uq1Zp0bXV8cVZ5LIj+fPzI1XRX07sjWnsTAukV2P9WqQ8PDtdnZt57cJtLUkZBexqysEhuzYf2RyclNmwcri3df37NnJlzec2BcgdG9dk3+ObVPw01Nx1LJao2ZHMCAFIJ871lBKyaNhLTdWDLHUkTbSzQ4EB79NuOcBBIh9vqZxrnzJeuicxdUYpk4BRMAJVvjL+0+fzEk2sUcXZ/u3/ciwKreqB+dvvm8whhhvtv9yzrWWjAxEYgJvMS8w3KBcRs8qUVKkoiq1lISXdO0BKWBOvMucJuJHV/WKkskwAyygCNuXby0hQBBBeOu3L8/8/PJtw+8SuXyL0t3KuHs7O2Zm/ko4guXpDFw1kpyUmx45eW61m0iAFnnNgOr/1SXp26clqIRZF9rNjdu2lh8akckxB3AAIp5hNG8+jvqIaxxBBtkRGlbdXBAMxTRUGlbbnhoS6lE5XL5AZUAxzy/sFAoFDxPx3GyvLw8MjIsSDyEGQNIjZmbmx8c2sLsmmGY8YP1xeIDdDxgDTcaYbvV6ltXJKLFe/eGhob8bAAHEIm1T8C/kTBUcj/lvpIAAAAASUVORK5CYII="

# Bus Normal
ICON_BUS_NORMAL_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAARCAIAAAAg6XlfAAAAAXNSR0IB2cksfwAAAARnQU1BAACxjwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+oBDQoiFXP5RDQAAASmSURBVEjHxVVNi51ZEX6eOnXevh9Nf998GTuJSXo0UTCOoiAIuhCHQZwwG52VMKv5JZKFS7fCgDO4nBGEGceOMAZBjZmIi2QSEs2N3E5id9J9++P2fd9TVS6uaYcJDoILa3E4p+o5VaeKOk/x8uXL+H+I/u8uSD6rjIiI+E/WfweegA5wB8dPkK2tLVWNCJJPVxIBAMLt4fahwz0hAU4AHwuhEbG3tzcYDFqtFkl3/y/zc/eqqiZ4EQGCFMAREKq7PXzwEGCET0KKiLuPRqOVlZWIUACDweD8+fMXL148SPejD5wEe7ZiEwxJEel09eSpI8PhcHGxLUCg8dA7dza2NhuETzxExKVLl65cubK0tLSwsKATrYe3Ol0mCWtEW6RYvQ+SkgCIJDLq0cjcgQgPJ1NYbnUkZSCY/PHmno318RMAHibFi5sKG6YsRDCRcPfG7MaNG3Nzc0+bK3j05JmgbK4/mFnsJa22Nx5OadapNhEBwprB3++f/Oz58DLer7szM08e3O/OL0luRSDCm/F+3Qyl3SMigBRol43ZXtWZW9x5sjEzv+DNOGs+sbycc+73+3LQSjHZBOlCpzDrVAepMqSxobEoZm7m7mZmEUEJpKAAICCkwx3uZBGGimRBkiA9zNxKQFJ69513VLXX6/2r1IhYu3OLIlRJ6XCENaVpi1BVVSVAS5IknnYpgu7BIALBhKAjpZQ0ZS+mWZOkBHpBMQ8PBIVQVQfPnTtXVZVOGtQ210l3IBVbH9wDWI9Hze6QmigUJkKSVknViwmCYYywUquSIEFNNEm0en3wt1an/YWV5ev9YXt2JqNBkDDlmBBJmnMmqQCkaepfvvujH75qSnN2p6dJuJsjWAzhrCpJcvXDO+/f7atWpuaULz139uVvfD0CSFlSQoR5w+JhjQfd4qWvfevHb/70qxc+/cc/PDp9Ig3WiqSgu5mLiCJgEuNfvbe+MQxJRzOXkiS3QqmZb6aoCz5Taa+Ytds4cyZICIUhN2/PXPl9RgQBIBAA17S6XeokqTfVltnpqdz9y4e7J5ePlaLbex3euv2dlbNmJWdVkGZ4ROlI8kBFdB3Z0p5yVfCL6VZ3dnZ+sPYaKm3qMItiTV1ru91NXHKGN05xhDHu5+ono+HmkR7Dz27uvLjtzex8s4t/PNyYWzrUarWb138201sU4YQyo5J0KOsjlIZaIAZAyt7R2bfXy7dfeHGq0/7T1avvX/tzldooBeYKKBEWsZBtfRwwBjR4s4xHy8uvvPw9Cf35m2+s7wxV5s291GU82hdvmlPHn7/4EpMCUASOnzpx67svrL/3m85oHzujnHKFMkQquTa38c5eV3WYckdzR8FKONXysvfYm7+KsNVKpIAEd93brVY11RGysbJbdbPElFh7thM+1vCtu2t3f/u7b37u8wC4+uvVYIR7mO/s7G5vDwkg4OF379176623jxw7bMVf+f4PREiRCVv6hC8jSDAYCABM6dq1D65f/6Cu6y9euPCVLz9PSgDk5KuDEcc+dTxXGQBXV1efHQAHPNzv90spvV5venp6Yp2w7jNTEECALKX0+30Ap0+fFpGPIj92658EqrXXmmhvFQAAAABJRU5ErkJggg=="

# Bus Eco (E/H2)
ICON_BUS_ECO_B64 = "data:image/png;base64,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"

# Badner Bahn
ICON_WLB_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAANCAIAAABU/bu/AAAAAXNSR0IB2cksfwAAAARnQU1BAACxjwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+oBDQkdJHi/0GsAAAS2SURBVDjLPVRbi1tVFP7W2vvknjlJJ8k0zejg1LH1Mq3WC6ioSK1vRRB8VEH8AQr67INabKsoKrQqLaj4IAji9UVbS6+g2FbrpdNpazvTSWZiJplMJic5Jzlr+ZDUDfthf+y1vm997P3RwtKSgggqRABAIAUUg6XAEFYanAAws6qoQgnQIQgooEIgFQIBPGxCIEBVFMzEUAVUiazCACCV4UUFQEM+BUEHyHUtSgSRkIiIQNDrFQBARCRy+Icfu91AVVWFmQFSEcexDz78SDIZE0SIRKGWSGrVamO5LjRg0cHATEQAESuIVAQKDKyBQgl0XRENeInIGHP+7z+PHjsWcWx1sWqN9f1uLJ4Mgm6hULh05cr2x3ZMbpxyiNSAFqq1Tz7+tFJrDvUDBB00I2OXaisinHA4l02Jyv+jX9/QoU4FcdjHcisg6Do3ZkhF+qqqICYYa7oh/XRmbt8rz98yNSVQS9yfKCWnJuN+J4zGTDoRbbR8YqeYdc7N1DIJE3Ta8VS65Mby+WjLUyIt5uILjbYRJz3Cvb52Oj1mU1iXPHTi8mgmZZj7ve6j92+s1TtBGCSjNjfiNLzQ68f+vtY+c/bcLVObSIQ5tG4yev63v/Z98OWRQ6cgrT27P3rt1bcp7LhxnTl3etNNpeXy1fyorrUqb+z58L33D45lowf2f/bmOwdby7WrF2b2H/jm+NGTN46lvNWlvtfoefVuq150nSM/Hd134OtauTxRTHRajdM/n3l824Zjp872Ax8KFhJlwBjrWGaybJJpd8RdB4gibK6t9hH6/Z4KWYqOZHKJpEs2Ek+mM9l1zBYgJmM4Ymyk0/G9TrfXC3y/ryQMMIwQK9mV1V4ul75ry9S5y9XlRhMg8/LLL/3y65lVP5opjY+MjgWIRdzSholJclJz5RV3/cag6yfdsXqr2zGZRL60YWIy5LjERnPFG+Ak1/qxRLYwks11+6a2Cmdk1CTSGkkGZNtwM4WiiaWCgOYrbRtNayRx5GwlHw22TN9mVe2luebnRy4qqYoahsAQ4asT//TXaibmbi6mLy6udL0WJ7Jgy8JfHL6iUFVRyOB5M7Fz+Grba0Uikc2T47+fn40digs5qgBk+7bSzOw/Knbq5qYPZ/byFetYe37mj0Zzdef2eyEiEkJEmI0xxrHN6vz4xNTi1dnpu6arlXI6mxdVM/jCAIEVCMOQLBvHWObmSiMdS3S8tTH31szmAxsxhokpFaGVZqO10i4V886p07N/9WYvXLCl4vjOHQ9Va8t733pXwlDCfigiIgKORSyncmHPJxv5tzL/zFNPfPvd94adYVYwAXr3ndNe1788V07GIrNzlYybJYhjiLXf9nxAlGCIrRMLVb1W9fknH7j9junR3ChdW1wC0Ov1nnv26eV6ffOmzVBdWlqqVCq79+7NjxVEiYgZVCjkTh4/LiKDFFVVAu65717f9z2vk8uNNptNVQI0kYgvlssvvvDC+Pj42Pr1nY538dKlO7dufX3XLmYGkYJovrI4sK6+XPPa3uTkTUTUqDfq9XpxvDR0lYySMjOBoEpECqgKFINUIQz9V4LKIHXD8sK1fD6fSqWDoDc/P+9mMm4mo4Ny1f8APx55cp43CXwAAAAASUVORK5CYII="

# ÖBB Cityjet
ICON_CITYJET_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAKCAIAAABJ+IsHAAAAAXNSR0IB2cksfwAAAARnQU1BAACxjwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+oBDQofMFIV2M0AAAOYSURBVDjLPZPNa5xVFMafc+9N3pl3ZvIxkyYZaUwkmBqbaEPQoSCE6qIW9F/wCyFZ2IWI6M6FIqIgCmJdtEWoCwUX1WJBXKlNmyYWa5MZUz9C0jZkmsw7SeZ73nnvOS7eiXdxl+c5vx/Poc372yxc2Cn0JpNKK600IC2/WSwUcitZz/Nmnj4hLE4kUvA8ZgFAAIiICJB0etB13e2dnXq9DhEBCCAiEBmt792563meMeaxqalUMqWNIVA4wFTK5Vxueen6UiaTcaJRRcr3/YVr84meRKNW70sdurG0VCqVtFL3t7cBsLAIAAEIwv0D6ZHhoT9zud1iEaQFgQAAkcCYTqXJGBOLxcnyyvIfL73yau+hfoEAoI8/+XRi8ujw0JClgFgTtVk0gQFmMHGbUhA+IogAgAjbpq3bJomChgI5jqOM7rDsrf3bEemsR+J+o1mt1Lp6u1MiF7+/9MIbrxMUEZmg1ZJK/covV7xi2yQAIQjz5PiRkeHhBtSBQ4GEpGGqgBE0Ku+9/8HjE2OlvUrN9+fm5uYXritSdnfvwYcON4jeefdDJxp9/rlTp549OX1s8nY298jRCQCGgNULX67s7q9rl8WGyQKCtKq/XlsdSP0TcduJRCEnWESECB2BnVHQ5WpfX5/RlJ+/cfWzzy+srjrRmDaYuZU8efzJj15+kZXSMbfbsgyPfPPV16MPj3U6jgFEbdyecM2QckVs26ZAMQZ361uFOxvdh1sUypY2a/sTVas809mUAFqJUuQ2asn15aeiHVBNAwzurNuLf6UEPmlf093Lyfj4keP9/cViMZ1OGxGJxZxxJ2AqK9EUYgmELcXYrQlvrbFSECL8vxUAKE3E1jwQrxSqwiTMDvHYQPxRa/0WCwtA2moWcRR1KNOyRf33bzf35bvNrTffetsI8FO+knXdaqnSJBERAjREC8UcY8lYELMoEaaDdoEUwTZbStOPm+WmcawESmPND77dKLUavNuot4QJINIAopBE1DHglmr8XK6deKJLG9ByNrtwdV5EvjhzRmljrRXhIAhE8Nrp07V6LQhsu3BtZAKgQNK+KhGRRCIeBLZaqxptjNbnz58DELZXaZ1IJGZnZ32/efbsOc/zLv1w2e1K0L18PpyYy2ZLe/vT09MsvL6+kc9vZTIZJxIBaWY+SAyvCSAQKBQaNlwOtmpWa7du/j46OppMJhuNxuLiYk9Pz7GpKVLKWqu1Mdow8B9Ore+f+YBpFgAAAABJRU5ErkJggg=="

# ÖBB Talent
ICON_TALENT_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAMCAIAAACfoWgaAAAAAXNSR0IB2cksfwAAAARnQU1BAACxjwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+oBDQoeLF8PtcMAAAQgSURBVDjLbZRfiNRVFMe/59z7m/8zruu0uq5haflnBd01fYpK7UUNomAlKBBE7UUCo+deih4LeijE1x4iQ4OoEOohkDIjTcUFsXV13dl1dmZ3Zmd2/v5+957Tw+yqRPfl3nMu93PO98D90sxcCQAAJZDif5c+eXwU0MoFQQHS5QyRqhLACiUIABARzMoz6W22h1MiBYge8x9hlQBVBVghKgBouQpBlYhUn2iOQOB6bZGYJiYmFmu1gYGB4eEdRPIfMRZQQMN2W51f1gEApOCevkdYZpw/f/727dsioqLEZG2wa+fIodcOqyqAmULh4sWLbMz9uxNxY5PxuBKcdztGRl5/481EIqGqjwsUinMPCzNn3zu1p1hScqoIwZs/eN9u3S4kJEQqyoZYiBhKgTEQFRFVVVW27BWW2LLxJFBYkZtff9P69feAjZBE1rbUTeX7D5w88cqrB+IcF6j2Rl1eqKBUygdBTKyFABSfrwzuG+wSkYoSQaGsJMTA9et/d1ptEUkmk99duNDqdJRJnbfGpLI5Fem0GmG1HstnW8WSeJ8jrIt8rtP5/uNPig9m3jl2jJgIZEFQuCsumqUgnkjKUjVgY37+JVuY8So2CAgIOx0BsbFht7NhaP2tW7fGxsbGx8fnFxYazU4ynV2sllXc4IZN3U57qVLODaxHIv6wuqDgWjw5rZowwbZO6865c19Bjh4/riALJSi5XK7eP5BMpacmO9bYfDpz7+Z4o1bqf/o5lWh+tpBd/VRuVV9pdnp1X8573+32ARhjstlMPJE01A9IYMgbTmfTQdiipVquGQoDYM9Esfhsfu36+YXL5759af/+ZzZttiBSQtx57TS7otTtqvEmDEkkArcaNYhGYeiiKHIhMYEZRCB470++e3Lb8DAzA2BmFRERL757Z+Luhx+lgkSDyLddm7xrL96nate5dUt07Y/Lm57faqEw4BGVfY2WoSbSCa8aFh/m335r48HDkWEA8KIAFEK4f29y7MiRaqUyMjo6MTmpTB6qquSUmMHGMOc3bigPDtip6Qiy2gSk5IFnYdSQM/jpzNndL+yxgJC4pcjNOamrEwWpEvPdH360O3dl1w4450Q8g5hI1FQqVUNcni/HYrFKpTJXKolIo9FIJdNhGKZSKUvcqFf/WdPXvjfVgiTgWNVBOZNOpnOqrm/3aGrVKioUi43m0m+XLlUX5s988WUmk82k08TUqNUjpVOnT9vAEpFCSaGq3ouqN8YAIOLenKX3vUSMsYG1S/Xa5599mstmkomU865WqzWbrYOHDpWLc5HvHj124sWX91GhOMcKAbzKX39eyefXDA0NRVF048aNIIiN7t1rjenRIapQD132NV0xq8eGt+JA4q9dvRpPJLZs2eK9n34w3Q3D4e3bnXPiPZhT6cy/1/pbXEKBNC4AAAAASUVORK5CYII="

# ÖBB Kiss
ICON_KISS_B64 = "data:image/png;base64,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"


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
    {"name": "Hauptbahnhof", "lat": 48.1850, "lon": 16.3750, "lines": ["U1", "D", "13A", "69A", "O", "18", "S"], "rbl": [150, 151]}
]

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
    "S": "#00549F", "13A": "#E3001B", "D": "#E3001B", "43": "#E3001B", "1": "#E3001B", "WLB": "#00549F"
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

# --- 5. DATEN & LOGIK ---

@st.cache_data(ttl=10)
def fetch_data(lines_to_check):
    if not lines_to_check: return []
    
    relevant_rbls = []
    # Logic: Search stations in database that have these lines. 
    # For GPS: we already filtered stations by distance in main loop
    for s in STATION_MARKERS:
        if not set(s.get("lines", [])).isdisjoint(lines_to_check):
            relevant_rbls.extend(s["rbl"])
    
    # Remove duplicates
    relevant_rbls = list(set(relevant_rbls))

    if not relevant_rbls: return []
            
    url = f"https://www.wienerlinien.at/ogd_realtime/monitor?rbl={'&rbl='.join(map(str, relevant_rbls))}"
    unique_vehicles = {}

    try:
        response = requests.get(url, timeout=4)
        data = response.json()
        
        for mon in data.get("data", {}).get("monitors", []):
            for line in mon.get("lines", []):
                line_name = line.get("name")
                if line_name not in lines_to_check: continue
                
                direction = line.get("towards")
                for i, dep in enumerate(line.get("departures", {}).get("departure", [])):
                    if i >= 4: break 
                    countdown = dep.get("departureTime", {}).get("countdown", 99)
                    
                    if isinstance(countdown, int) and countdown < 40:
                        vh = dep.get("vehicle", {})
                        v_id = vh.get("id")
                        if not v_id: v_id = f"{line_name}_{direction}"
                        
                        v_type = "tram_old" 
                        ac = vh.get("barrierFree", False) or vh.get("foldingRamp", False)
                        
                        if line_name == "U6":
                            v_type = "u6"
                        elif "U" in line_name:
                            if ac: v_type = "v_wagen"
                            else: v_type = "silberpfeil"
                        elif "A" in line_name or "Bus" in line_name:
                            v_type = "bus"
                        elif line_name == "WLB":
                            v_type = "wlb"
                        elif line_name.startswith("S") or line_name.startswith("R"):
                             v_type = "cityjet" # Default für Zug
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
                        
                        if v_id in unique_vehicles:
                            if countdown < unique_vehicles[v_id]["time"]:
                                unique_vehicles[v_id] = new_entry
                        else:
                            unique_vehicles[v_id] = new_entry

        return list(unique_vehicles.values())
    except: return []

# --- 6. SIDEBAR & GPS ---

with st.sidebar:
    st.header("Einstellungen")
    gps_mode = st.toggle("Echtstandort (GPS)", value=False)
    
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

# --- 7. FILTERUNG ---

nearby_lines = set()
# Determine nearby lines based on user location vs defined stations
for s in STATION_MARKERS:
    dist = haversine(user_lat, user_lon, s["lat"], s["lon"])
    if dist < 1200: 
        for l in s.get("lines", []):
            nearby_lines.add(l)

vehicles = fetch_data(nearby_lines)
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

# Draw Strecken (Polylines)
for line_name in nearby_lines:
    route_key = line_name
    if route_key not in SMOOTH_ROUTES:
        if "U" in route_key: route_key = "U1"
        elif "A" in route_key: route_key = "13A"
        else: route_key = "D"
    if route_key in SMOOTH_ROUTES:
        folium.PolyLine(SMOOTH_ROUTES[route_key], color=LINE_COLORS.get(line_name, "#888"), weight=3, opacity=0.5).add_to(m)

# Draw Stations
for s in STATION_MARKERS:
    s_lines = set(s.get("lines", []))
    if not s_lines.isdisjoint(nearby_lines):
        icon = folium.CustomIcon(ICON_STATION_B64, icon_size=(24, 14), icon_anchor=(12, 7))
        folium.Marker([s["lat"], s["lon"]], popup=s['name'], icon=icon, z_index_offset=1000).add_to(m)

# Helper
def get_icon_props(v):
    if v["type"] == "bus": return ICON_BUS_NORMAL_B64, 30, 8
    if v["type"] == "ulf": return ICON_ULF_B64, 30, 6
    if v["type"] == "flexity": return ICON_FLEXITY_B64, 40, 9
    if v["type"] == "silberpfeil": return ICON_SILBERPFEIL_B64, 40, 12
    if v["type"] == "v_wagen": return ICON_VWAGEN_B64, 40, 12
    if v["type"] == "x_wagen": return ICON_XWAGEN_B64, 40, 12
    if v["type"] == "u6": return ICON_TYPET_B64, 40, 13
    if v["type"] == "wlb": return ICON_WLB_B64, 40, 13
    if v["type"] == "cityjet": return ICON_CITYJET_B64, 40, 10
    if v["type"] == "talent": return ICON_TALENT_B64, 40, 12
    if v["type"] == "kiss": return ICON_KISS_B64, 40, 12
    return ICON_BIM_OLD_B64, 32, 8

for v in vehicles:
    lat, lon, rot = get_vehicle_position_and_rotation(v["line"], v["time"])
    if lat and lon:
        border_color = "#0066b3" if v["ac"] else "#d32f2f"
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

# --- 9. NEXT AC TILES (GRID SYSTEM FIXED) ---
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
        # PURE CSS GRID - Fixes the sizing issue completely
        grid_html = """
        <style>
            .grid-container {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
                gap: 12px;
                margin-bottom: 20px;
            }
            .grid-item {
                aspect-ratio: 1 / 1;
                border-radius: 8px;
                color: white;
                padding: 8px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .line-title {
                text-align: center; 
                font-weight: bold; 
                font-size: 1.2em; 
                border-bottom: 1px solid rgba(255,255,255,0.3); 
                padding-bottom: 4px;
                margin-bottom: 4px;
            }
            .dest-row {
                display: flex; 
                justify-content: space-between; 
                margin-bottom: 2px;
                font-size: 0.8em;
            }
            .dest-name {
                white-space: nowrap; 
                overflow: hidden; 
                text-overflow: ellipsis; 
                max-width: 65%;
            }
            .ac-icon {
                text-align: center; 
                font-size: 0.7em; 
                margin-top: 2px; 
                opacity: 0.9;
            }
        </style>
        <div class="grid-container">
        """

        for line, dests in line_data.items():
            bg = LINE_COLORS.get(line, "#555")
            
            dests_html = ""
            for dest_name, min_time in dests.items():
                dests_html += f"""
                <div class="dest-row">
                    <span class="dest-name">{dest_name}</span>
                    <span style="font-weight: bold;">{min_time}m</span>
                </div>
                """
            
            grid_html += f"""
            <div class="grid-item" style="background-color: {bg};">
                <div class="line-title">{line}</div>
                <div style="flex-grow: 1; overflow-y: hidden;">{dests_html}</div>
                <div class="ac-icon">❄️ AC</div>
            </div>
            """
        
        grid_html += "</div>"
        st.markdown(grid_html, unsafe_allow_html=True)
        
    else:
        st.info("Keine klimatisierten Fahrzeuge in Kürze.")
else:
    st.write("Keine Linien in der Nähe.")

# --- 10. TABELLE (LIVE) FIXED ---
st.subheader("📋 Alle Abfahrten (Live)")

if vehicles:
    t_data = []
    for v in vehicles:
        icon_url, _, _ = get_icon_props(v)
        
        type_label = "Fahrzeug"
        if v["type"] == "flexity": type_label = "Flexity"
        elif v["type"] == "ulf": type_label = "ULF"
        elif v["type"] == "bus": type_label = "Bus"
        elif v["type"] == "v_wagen": type_label = "V-Wagen"
        elif v["type"] == "silberpfeil": type_label = "Silberpfeil"
        elif v["type"] == "u6": type_label = "Type T"
        elif v["type"] == "cityjet": type_label = "Cityjet"
        elif v["type"] == "talent": type_label = "Talent"
        elif v["type"] == "kiss": type_label = "Kiss"
        
        # Combined Text for second column
        descr = f"{type_label} ({v['id']})"
        
        t_data.append({
            "Icon": icon_url, 
            "Fahrzeug": descr,
            "Linie": v["line"], 
            "Ziel": v["dest"], 
            "Zeit": f"{v['time']} min", 
            "Klima": "❄️" if v["ac"] else "🔥"
        })
        
    df = pd.DataFrame(t_data)
    
    st.dataframe(
        df, 
        column_config={
            "Icon": st.column_config.ImageColumn("", width="small"), # Small is approx 40-50px
            "Fahrzeug": st.column_config.TextColumn("Typ (ID)"),
            "Linie": st.column_config.TextColumn("Linie", width="small"),
            "Zeit": st.column_config.TextColumn("Abfahrt", width="small"),
            "Klima": st.column_config.TextColumn("AC", width="small")
        },
        hide_index=True, 
        use_container_width=True
    )
