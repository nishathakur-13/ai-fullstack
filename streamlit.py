import os
import requests
import streamlit as st
import streamlit.components.v1 as components
import folium
from folium.plugins import AntPath
from geopy.geocoders import Nominatim

from streamlit_folium import st_folium
geolocator = Nominatim(user_agent="civicai_nav")


API_URL = os.getenv(
    "BACKEND_API_URL",
    "https://backend-api-duvj.onrender.com"
)


# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="CivicAI — Complaint System",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =====================================================
# GLOBAL CSS — dark theme, clean typography
# =====================================================

st.markdown("""
<style>

/* Base background */
[data-testid="stAppViewContainer"] { background: #0d1117; }
[data-testid="stHeader"]           { background: #0d1117 !important; border-bottom: 1px solid #21262d; }
[data-testid="stMainBlockContainer"]{ padding-top: 60px !important; }
#MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"]        { display: none !important; }

/* Tabs */
[data-testid="stTabs"] button[role="tab"] {
    background: transparent;
    color: #8b949e;
    font-weight: 600;
    font-size: 14px;
    border-radius: 8px 8px 0 0;
    padding: 10px 24px;
    border: none;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #e6edf3;
    border-bottom: 2px solid #1f6feb;
    background: transparent;
}
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid #21262d;
    background: transparent;
    gap: 4px;
}

/* Inputs */
[data-testid="stTextInput"] > div > div > input,
[data-testid="stTextArea"]  > div > div > textarea {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
}
[data-testid="stTextInput"] > div > div > input:focus,
[data-testid="stTextArea"]  > div > div > textarea:focus {
    border-color: #1f6feb !important;
    box-shadow: 0 0 0 2px rgba(31,111,235,0.25) !important;
}
label { color: #8b949e !important; font-size: 13px !important; font-weight: 500 !important; }

/* Button */
[data-testid="stButton"] > button {
    background: #1f6feb !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 24px !important;
    transition: background 0.2s, box-shadow 0.2s !important;
    box-shadow: 0 2px 10px rgba(31,111,235,0.3) !important;
    width: auto !important;
}
[data-testid="stButton"] > button:hover {
    background: #388bfd !important;
    box-shadow: 0 4px 16px rgba(31,111,235,0.45) !important;
}

/* Selectbox */
[data-testid="stSelectbox"] > div > div {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
}

/* Alerts */
[data-testid="stAlert"] {
    border-radius: 8px !important;
}

/* Divider */
hr { border-color: #21262d !important; margin: 24px 0 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 4px; }

/* Spinner text */
[data-testid="stSpinner"] p { color: #8b949e !important; }

</style>
""", unsafe_allow_html=True)


# =====================================================
# TITLE — native Streamlit (no iframe)
# =====================================================

st.markdown("""
<div style="display:flex; align-items:center; gap:14px; padding:0 0 20px 0;">
  <div style="
    width:54px; height:54px;
    background:linear-gradient(135deg,#1f6feb,#388bfd);
    border-radius:12px;
    display:flex; align-items:center; justify-content:center;
    font-size:26px; flex-shrink:0;
    box-shadow: 0 4px 12px rgba(31,111,235,0.4);
  ">🚨</div>
  <div>
    <div style="font-size:32px; font-weight:800; color:#e6edf3; letter-spacing:-0.3px; line-height:1.2;">
      CivicAI Complaint System
    </div>
    <div style="font-size:14px; color:#8b949e; margin-top:2px;">
      Multi-Agent AI &nbsp;·&nbsp; Real-time &nbsp;·&nbsp; Location-aware
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# =====================================================
# SESSION STATE
# =====================================================

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "_selected_complaint" not in st.session_state:
    st.session_state["_selected_complaint"] = None


# =====================================================
# HELPERS
# =====================================================

import math

def distance_meters(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def is_off_route(user_lat, user_lon, route_coords, threshold=30):
    for coord in route_coords:
        if distance_meters(user_lat, user_lon, coord[1], coord[0]) < threshold:
            return False
    return True

@st.cache_data(ttl=30)
def fetch_complaints():
    response = requests.get(f"{API_URL}/complaints")
    return response.json()


@st.cache_data(ttl=3600)
def reverse_geocode(lat, lon):
    try:
        url = (
            "https://nominatim.openstreetmap.org/"
            f"reverse?format=json&lat={lat}&lon={lon}"
        )
        headers = {"User-Agent": "civic-ai-system"}
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        address = data.get("address", {})
        return (
            address.get("road")
            or address.get("neighbourhood")
            or address.get("suburb")
            or address.get("city")
            or address.get("town")
            or address.get("village")
            or data.get("display_name")
        )
    except:
        return None


def safe_location(location, lat, lon):
    invalid_values = ["none", "none, none", "null", "null, null", ""]
    if not location or str(location).strip().lower() in invalid_values:
        if lat is not None and lon is not None:
            return reverse_geocode(lat, lon) or "Location unavailable"
        return "Location unavailable"
    return location


@st.cache_data(ttl=60)
def get_route(start_lat, start_lon, end_lat, end_lon):

    try:

        # -----------------------------------
        # OSRM ROUTE API
        # -----------------------------------

        url = (
            "https://router.project-osrm.org/"
            f"route/v1/driving/"
            f"{start_lon},{start_lat};"
            f"{end_lon},{end_lat}"
            f"?overview=full&geometries=geojson&steps=true&annotations=true"
        )

        print("\n======================")
        print("🚗 ROUTE REQUEST")
        print("======================")
        print(url)

        response = requests.get(
            url,
            timeout=10
        )

        print("\nSTATUS CODE:")
        print(response.status_code)

        if response.status_code != 200:

            print("\n❌ ROUTE API FAILED")

            return None

        data = response.json()

        print("\nROUTE RESPONSE:")
        print(data)

        routes = data.get("routes")

        if not routes:

            print("\n❌ NO ROUTES FOUND")

            return None

        route = routes[0]
        legs = route.get("legs", [])

        steps = []

        for leg in legs:

            for step in leg.get("steps", []):

                maneuver = step.get("maneuver", {})
                m_type = maneuver.get("type", "")
                m_mod  = maneuver.get("modifier", "")

                # Road name: prefer name, then ref, then reverse-geocode
                road_name = step.get("name") or step.get("ref") or ""
                if not road_name:
                    loc = maneuver.get("location")  # [lon, lat]
                    if loc:
                        try:
                            rev = geolocator.reverse(
                                f"{loc[1]}, {loc[0]}", language="en", timeout=3
                            )
                            if rev:
                                addr = rev.raw.get("address", {})
                                road_name = (
                                    addr.get("road")
                                    or addr.get("neighbourhood")
                                    or addr.get("suburb")
                                    or addr.get("city_district")
                                    or addr.get("city")
                                    or ""
                                )
                        except Exception:
                            pass
                if not road_name:
                    road_name = "the road ahead"

                # Build human-readable instruction
                turn_map = {
                    "turn left":          "Turn left",
                    "turn right":         "Turn right",
                    "turn slight left":   "Slight left",
                    "turn slight right":  "Slight right",
                    "turn sharp left":    "Sharp left",
                    "turn sharp right":   "Sharp right",
                    "turn uturn":         "Make a U-turn",
                    "depart":             "Head",
                    "arrive":             "You have arrived at",
                    "roundabout":         "Enter the roundabout",
                    "rotary":             "Enter the rotary",
                    "merge":              "Merge",
                    "fork left":          "Keep left at the fork",
                    "fork right":         "Keep right at the fork",
                    "on ramp left":       "Take the ramp on the left",
                    "on ramp right":      "Take the ramp on the right",
                    "off ramp left":      "Take the exit on the left",
                    "off ramp right":     "Take the exit on the right",
                    "end of road left":   "Turn left at the end of the road",
                    "end of road right":  "Turn right at the end of the road",
                    "continue":           "Continue straight on",
                    "new name":           "Continue onto",
                }
                key = f"{m_type} {m_mod}".strip().lower()
                verb = turn_map.get(key) or turn_map.get(m_type.lower(), "Continue on")
                instruction = f"{verb} {road_name}".strip()

                distance = round(step.get("distance", 0))

                steps.append({
                    "instruction": instruction,
                    "road": road_name,
                    "distance": distance
                })

        geometry = route.get("geometry")

        if not geometry:

            print("\n❌ NO GEOMETRY FOUND")

            return None

        coordinates = geometry.get(
            "coordinates",
            []
        )

        if not coordinates:

            print("\n❌ EMPTY COORDINATES")

            return None

        print("\n✅ ROUTE SUCCESS")
        return {
            "coordinates": coordinates,
            "steps": steps,
            "distance": round(route.get("distance", 0) / 1000, 2),
            "duration": round(route.get("duration", 0) / 60, 2)
        }

    except Exception as e:

        print("\n❌ ROUTE ERROR")
        print(str(e))

        return None


URGENCY_CONFIG = {
    "LOW":      {"emoji": "🟢", "color": "#3fb950", "bg": "#0d2b1b", "border": "#238636"},
    "MEDIUM":   {"emoji": "🟡", "color": "#d29922", "bg": "#2b1b0d", "border": "#9e6a03"},
    "HIGH":     {"emoji": "🟠", "color": "#f0883e", "bg": "#2b160d", "border": "#bd561d"},
    "CRITICAL": {"emoji": "🔴", "color": "#f85149", "bg": "#2b0d0d", "border": "#da3633"},
    "UNKNOWN":  {"emoji": "⚪", "color": "#8b949e", "bg": "#161b22", "border": "#30363d"},
}

FOLIUM_COLOR = {
    "LOW": "green", "MEDIUM": "blue", "HIGH": "orange", "CRITICAL": "red"
}


# =====================================================
# TABS
# =====================================================

tab1, tab2 = st.tabs(["📝  Submit Complaint", "📊  Dashboard"])


# =====================================================
# TAB 1 — SUBMIT
# =====================================================

with tab1:

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    left, right = st.columns([1, 1], gap="large")

    # ── LEFT: Form ──────────────────────────────────
    with left:

        st.markdown("""
        <div style="margin-bottom:20px;">
          <div style="font-size:18px; font-weight:700; color:#e6edf3; margin-bottom:4px;">
            File a New Complaint
          </div>
          <div style="font-size:13px; color:#8b949e; line-height:1.5;">
            Describe the civic issue — our AI agents will classify,
            prioritize, and route it to the right department automatically.
          </div>
        </div>
        """, unsafe_allow_html=True)

        complaint_text = st.text_area(
            "Issue description",
            height=150,
            placeholder="e.g. There is a large pothole on MG Road near the bus stop that is causing accidents..."
        )

        location_text = st.text_input(
            "📍 Location",
            placeholder="e.g. MG Road, Sector 14, near bus stop"
        )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        if st.button("🚀  Analyze with AI Agents"):
            if not complaint_text:
                st.warning("Please describe the complaint.")
            elif not location_text:
                st.warning("Please enter a location.")
            else:
                with st.spinner("AI agents are analyzing your complaint..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/analyze",
                            json={"text": complaint_text, "location": location_text}
                        )
                        if response.status_code != 200:
                            st.error(response.text)
                        else:
                            st.session_state.analysis_result = response.json()
                            st.cache_data.clear()
                    except Exception as e:
                        st.error(str(e))

    # ── RIGHT: Result ────────────────────────────────
    with right:

        if st.session_state.analysis_result:

            data    = st.session_state.analysis_result
            urgency = data.get("urgency", "UNKNOWN")
            cfg     = URGENCY_CONFIG.get(urgency, URGENCY_CONFIG["UNKNOWN"])
            dept    = data.get("department", "N/A")
            eta     = data.get("estimated_resolution_time", "N/A")
            expl    = data.get("explanation", "")

            # Urgency pill
            st.markdown(f"""
            <div style="margin-bottom:16px;">
              <span style="
                display:inline-flex; align-items:center; gap:8px;
                background:{cfg['bg']}; border:1px solid {cfg['border']};
                border-radius:999px; padding:6px 16px;
                font-size:13px; font-weight:700; color:{cfg['color']};
              ">{cfg['emoji']} &nbsp; {urgency} PRIORITY</span>
            </div>
            """, unsafe_allow_html=True)

            # Department + ETA
            m1, m2 = st.columns(2)
            with m1:
                st.markdown(f"""
                <div style="
                  background:#161b22; border:1px solid #21262d; border-radius:10px;
                  padding:16px 18px; margin-bottom:12px;
                ">
                  <div style="font-size:11px; color:#8b949e; font-weight:600;
                              text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">
                    🏢 Department
                  </div>
                  <div style="font-size:18px; font-weight:700; color:#e6edf3;">{dept}</div>
                </div>
                """, unsafe_allow_html=True)
            with m2:
                st.markdown(f"""
                <div style="
                  background:#161b22; border:1px solid #21262d; border-radius:10px;
                  padding:16px 18px; margin-bottom:12px;
                ">
                  <div style="font-size:11px; color:#8b949e; font-weight:600;
                              text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">
                    ⏳ Resolution ETA
                  </div>
                  <div style="font-size:18px; font-weight:700; color:#e6edf3;">{eta}</div>
                </div>
                """, unsafe_allow_html=True)

            # Explanation
            st.markdown(f"""
            <div style="
              background:#161b22; border:1px solid #21262d;
              border-left:3px solid #1f6feb;
              border-radius:10px; padding:16px 18px;
            ">
              <div style="font-size:11px; color:#8b949e; font-weight:600;
                          text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">
                🧠 AI Explanation
              </div>
              <div style="font-size:14px; color:#c9d1d9; line-height:1.7;">{expl}</div>
            </div>
            """, unsafe_allow_html=True)

        else:
            # Empty state — uses st.markdown so it respects dark bg
            st.markdown("""
            <div style="
              border: 2px dashed #21262d;
              border-radius: 14px;
              padding: 56px 32px;
              text-align: center;
              margin-top: 32px;
            ">
              <div style="font-size:38px; margin-bottom:16px;">🤖</div>
              <div style="font-size:16px; font-weight:600; color:#e6edf3; margin-bottom:8px;">
                AI Analysis will appear here
              </div>
              <div style="font-size:13px; color:#484f58;">
                Submit a complaint on the left to get started
              </div>
            </div>
            """, unsafe_allow_html=True)


# =====================================================
# TAB 2 — DASHBOARD
# =====================================================

with tab2:

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # =================================================
    # GPS
    # =================================================

    lat = st.query_params.get("lat")
    lon = st.query_params.get("lon")

    # Only auto-refresh if GPS coords not yet received
    if lat is None or lon is None:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=30000, key="gps_refresh")

    if lat is not None and lon is not None:
        user_lat = float(lat)
        user_lon = float(lon)
        detected_location = safe_location(None, user_lat, user_lon)
        is_live = True
    else:
        user_lat = 29.2144809
        user_lon = 79.5279012
        detected_location = "Location access not granted"
        is_live = False

    dot_color = "#22c55e" if is_live else "#f59e0b"
    dot_label = "LIVE"    if is_live else "DEFAULT"

    # =================================================
    # STATS
    # =================================================

    try:
        all_complaints = fetch_complaints()
    except:
        all_complaints = []

    total      = len(all_complaints)
    critical_n = sum(1 for c in all_complaints if c.get("urgency") == "CRITICAL")
    high_n     = sum(1 for c in all_complaints if c.get("urgency") == "HIGH")
    resolved_n = sum(1 for c in all_complaints if c.get("status", "").upper() == "RESOLVED")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Location card + stats side by side using native st.markdown
    loc_col, s1, s2, s3, s4 = st.columns([2.2, 0.7, 0.7, 0.7, 0.7], gap="small")

    with loc_col:
        coords_line = (
            f"<div style='font-size:11px; color:rgba(255,255,255,0.45); margin-top:6px;'>"
            f"🌐 {round(user_lat, 5)}, {round(user_lon, 5)}</div>"
            if is_live else ""
        )
        st.markdown(f"""
        <div style="
          background: linear-gradient(135deg, #0f2460 0%, #1a3a9f 55%, #2563eb 100%);
          border-radius: 14px; padding: 18px 22px; color: white;
          box-shadow: 0 6px 24px rgba(37,99,235,0.3);
          position: relative; overflow: hidden; height: 100%;
        ">
          <div style="position:absolute; top:-40px; right:-40px; width:140px; height:140px;
            background:radial-gradient(circle, rgba(96,165,250,0.18) 0%, transparent 70%);
            border-radius:50%;"></div>
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px;">
            <div style="font-size:10px; font-weight:600; letter-spacing:2px;
                        text-transform:uppercase; opacity:0.6;">📡 Active Location</div>
            <div style="display:flex; align-items:center; gap:5px;
              background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.18);
              border-radius:999px; padding:3px 10px; font-size:10px; font-weight:700;
              letter-spacing:1.2px; text-transform:uppercase;">
              <div style="width:6px; height:6px; border-radius:50%;
                background:{dot_color}; box-shadow:0 0 5px {dot_color};"></div>
              {dot_label}
            </div>
          </div>
          <div style="font-size:20px; font-weight:800; line-height:1.3;
                      word-break:break-word; position:relative; z-index:1;">
            📍 &nbsp;{detected_location}
          </div>
          {coords_line}
          <div style="font-size:11px; opacity:0.4; margin-top:10px;
            border-top:1px solid rgba(255,255,255,0.1); padding-top:8px;">
            🛰️ GPS via browser geolocation
          </div>
        </div>
        """, unsafe_allow_html=True)

    for col, icon, val, lbl in [
        (s1, "📋", total,      "Total"),
        (s2, "🔴", critical_n, "Critical"),
        (s3, "🟠", high_n,     "High"),
        (s4, "✅", resolved_n, "Resolved"),
    ]:
        with col:
            st.markdown(f"""
            <div style="
              background:#161b22; border:1px solid #21262d; border-radius:12px;
              padding:16px 14px; text-align:center; height:100%;
            ">
              <div style="font-size:22px; margin-bottom:6px;">{icon}</div>
              <div style="font-size:24px; font-weight:800; color:#e6edf3; line-height:1;">{val}</div>
              <div style="font-size:11px; color:#8b949e; margin-top:4px;">{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    # =================================================
    # FILTER
    # =================================================

    fc, _ = st.columns([0.28, 0.72])
    with fc:
        filter_option = st.selectbox(
            "Filter by Urgency",
            ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"]
        )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    try:
        complaints = all_complaints.copy()

        if filter_option != "ALL":
            complaints = [c for c in complaints if c.get("urgency") == filter_option]

        complaints = complaints[:20]

        # =================================================
        # HOTSPOT MAP
        # =================================================

        hotspot_map = folium.Map(
            location=[user_lat, user_lon],
            zoom_start=13,
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri"
        )

        folium.Marker(
            [user_lat, user_lon],
            popup=f"📍 You: {detected_location}",
            tooltip="Your Location",
            icon=folium.Icon(color="blue", icon="home", prefix="fa")
        ).add_to(hotspot_map)

        valid_complaints = []

        for item in complaints:
            try:
                _lat = float(item.get("latitude"))
                _lon = float(item.get("longitude"))
            except (TypeError, ValueError):
                continue
            valid_complaints.append(item)
            _urgency       = item.get("urgency", "LOW")
            _location_name = safe_location(item.get("location"), _lat, _lon)
            _rd            = get_route(user_lat, user_lon, _lat, _lon)
            _distance      = f"{_rd['distance']} km" if _rd else "N/A"

            _popup_html = f"""
            <div style="width:230px; font-family:sans-serif; padding:4px;">
              <b style="font-size:13px;">🚨 {_urgency}</b><br><br>
              <b>Complaint:</b><br>
              <span style="font-size:12px;">{item.get('complaint_text','')[:100]}...</span><br><br>
              <b>📍</b> {_location_name}<br>
              <b>📏</b> {_distance} &nbsp;|&nbsp; <b>🏢</b> {item.get('department','N/A')}
            </div>
            """

            folium.Marker(
                [_lat, _lon],
                popup=folium.Popup(_popup_html, max_width=250),
                tooltip=f"{_urgency}: {item.get('complaint_text','')[:40]}...",
                icon=folium.Icon(color=FOLIUM_COLOR.get(_urgency, "gray"), icon="warning", prefix="fa")
            ).add_to(hotspot_map)

        # =================================================
        # ROUTE NAVIGATION
        # =================================================

        st.markdown("""
        <div style="font-size:16px; font-weight:700; color:#e6edf3; margin-bottom:10px;">
          🚗 Route Navigation
        </div>
        """, unsafe_allow_html=True)

        route_map  = None
        route_data = None

        if valid_complaints:

            # Index-based selectbox — avoids duplicate label & dict instability
            complaint_labels = []
            for idx, item in enumerate(valid_complaints):
                label = (
                    f"{idx + 1}. "
                    f"{URGENCY_CONFIG.get(item.get('urgency','UNKNOWN'), URGENCY_CONFIG['UNKNOWN'])['emoji']} "
                    f"{item.get('complaint_text','Unknown')[:60]}"
                )
                complaint_labels.append(label)

            selected_index = st.selectbox(
                "Select complaint to navigate to",
                range(len(complaint_labels)),
                format_func=lambda i: complaint_labels[i]
            )

            selected = valid_complaints[selected_index]

            # Force float — silently breaks Folium if coords are strings
            try:
                sel_lat = float(selected["latitude"])
                sel_lon = float(selected["longitude"])
            except Exception:
                st.error("Invalid complaint coordinates.")
                selected = None

            if selected is not None:

                if (
                    abs(float(user_lat) - sel_lat) < 0.0001
                    and
                    abs(float(user_lon) - sel_lon) < 0.0001
                ):
                    st.warning("User and complaint location are identical.")

                route_data = get_route(
                    float(user_lat),
                    float(user_lon),
                    sel_lat,
                    sel_lon
                )

                if route_data:
                    st.session_state["current_route"] = route_data
                    if is_off_route(float(user_lat), float(user_lon), route_data["coordinates"]):
                        st.error("⚠️ You are off-route. Rerouting...")
                        route_data = get_route(float(user_lat), float(user_lon), sel_lat, sel_lon)
                        st.session_state["current_route"] = route_data

                dept = selected.get("department", "N/A")

                selected_location = safe_location(
                    selected.get("location"),
                    sel_lat,
                    sel_lon
                )

                # ETA banner
                if route_data:
                    dist = route_data["distance"]
                    dur  = route_data["duration"]
                    st.markdown(f"""
                    <div style="
                      background:#0d2b1b; border:1px solid #238636; border-radius:10px;
                      padding:14px 20px; display:flex; align-items:center;
                      margin-bottom:12px;
                    ">
                      <div style="flex:1; text-align:center;">
                        <div style="font-size:10px; color:#3fb950; font-weight:600;
                                    text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;">
                          📏 Distance
                        </div>
                        <div style="font-size:22px; font-weight:800; color:#e6edf3;" id="live-dist-card">{dist} km</div>
                      </div>
                      <div style="width:1px; background:#21262d; align-self:stretch; margin:0 8px;"></div>
                      <div style="flex:1; text-align:center;">
                        <div style="font-size:10px; color:#3fb950; font-weight:600;
                                    text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;">
                          ⏱ Drive Time
                        </div>
                        <div style="font-size:22px; font-weight:800; color:#e6edf3;" id="live-eta-card">{dur} mins</div>
                      </div>
                      <div style="width:1px; background:#21262d; align-self:stretch; margin:0 8px;"></div>
                      <div style="flex:1; text-align:center;">
                        <div style="font-size:10px; color:#3fb950; font-weight:600;
                                    text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;">
                          🏢 Department
                        </div>
                        <div style="font-size:18px; font-weight:700; color:#e6edf3;">{dept}</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("Could not fetch driving route. Showing markers only.")

                # Always build map
                mid_lat = (float(user_lat) + sel_lat) / 2
                mid_lon = (float(user_lon) + sel_lon) / 2

                route_map = folium.Map(
                    location=[mid_lat, mid_lon],
                    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                    attr="Esri"
                )

                # Route line if OSRM succeeded
                if route_data:
                    points = [
                        [coord[1], coord[0]]
                        for coord in route_data["coordinates"]
                    ]
                    AntPath(
                        locations=points,
                        color="yellow",
                        pulse_color="red",
                        weight=6,
                        delay=800
                    ).add_to(route_map)
                    route_map.fit_bounds(points)

                # Your location marker
                folium.Marker(
                    [float(user_lat), float(user_lon)],
                    popup="📍 Your Location",
                    tooltip="You",
                    icon=folium.Icon(color="blue")
                ).add_to(route_map)

                # Complaint marker
                popup_route = f"""
                <div style="width:250px;">
                    <b>Complaint:</b><br>{selected.get('complaint_text', '')}<br><br>
                    <b>📍 Location:</b><br>{selected_location}<br><br>
                    {"<b>📏 Distance:</b><br>" + str(route_data['distance']) + " km<br><br><b>⏱ ETA:</b><br>" + str(route_data['duration']) + " mins" if route_data else ""}
                </div>
                """

                folium.Marker(
                    [sel_lat, sel_lon],
                    popup=folium.Popup(popup_route, max_width=300),
                    tooltip="🚨 Complaint Location",
                    icon=folium.Icon(color="red")
                ).add_to(route_map)

        # =================================================
        # Force maps iframe to full width via JS (CSS can't override inline width attr)
        components.html("""<script>
(function(){
  function fixWidth(){
    document.querySelectorAll('iframe').forEach(f=>{
      f.style.width='100%';
      f.setAttribute('width','100%');
    });
  }
  fixWidth();
  new MutationObserver(fixWidth).observe(document.body,{childList:true,subtree:true});
})();
</script>""", height=0)

        # MAPS SIDE BY SIDE
        # =================================================

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        import json as _json
        _dest_lat = float(sel_lat) if route_data else user_lat
        _dest_lon = float(sel_lon) if route_data else user_lon
        _route_coords_js = _json.dumps(
            [[c[1], c[0]] for c in route_data["coordinates"]] if route_data else []
        )
        _steps_js = _json.dumps(route_data["steps"] if route_data else [])

        # Build complaint markers JSON for hotspot map
        _hotspot_markers = []
        for item in valid_complaints:
            try:
                _hotspot_markers.append({
                    "lat": float(item.get("latitude")),
                    "lon": float(item.get("longitude")),
                    "urgency": item.get("urgency", "LOW"),
                    "text": item.get("complaint_text", "")[:80],
                    "dept": item.get("department", "N/A"),
                })
            except (TypeError, ValueError):
                continue
        _markers_js = _json.dumps(_hotspot_markers)

        _urgency_colors = _json.dumps({
            "CRITICAL": "#ef4444", "HIGH": "#f97316",
            "MEDIUM": "#eab308", "LOW": "#22c55e"
        })

        components.html(f"""<!DOCTYPE html><html><head><meta charset="utf-8"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
html,body{{margin:0;padding:0;background:#0d1117;width:100%;overflow:hidden}}
#wrap{{display:flex;width:100%;gap:8px}}
.map-box{{flex:1;min-width:0}}
.map-label{{font-size:13px;font-weight:600;color:#8b949e;font-family:sans-serif;margin-bottom:4px;padding-left:2px}}
.map{{width:100%;height:420px}}
</style></head><body>
<div id="wrap">
  <div class="map-box">
    <div class="map-label">🗺️ Complaint Hotspots</div>
    <div id="map1" class="map"></div>
  </div>
  <div class="map-box">
    <div class="map-label">🚗 Live Route Map</div>
    <div style="position:relative">
      <div id="map2" class="map"></div>
      <button id="start-btn" onclick="startNav()" style="position:absolute;bottom:16px;left:50%;transform:translateX(-50%);z-index:1000;background:#2563eb;color:#fff;border:none;border-radius:24px;padding:10px 24px;font-size:14px;font-weight:700;cursor:pointer;box-shadow:0 4px 12px rgba(37,99,235,0.5)">▶ Start Navigation</button>
    </div>
  </div>
</div>
<script>
const TILES='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}';
const INIT=[{user_lat},{user_lon}];
const DEST=[{_dest_lat},{_dest_lon}];
const routeCoords={_route_coords_js};
const steps={_steps_js};
const markers={_markers_js};
const COLORS={_urgency_colors};

// ── Map 1: Hotspot ────────────────────────────────
const map1=L.map('map1').setView(INIT,13);
L.tileLayer(TILES,{{maxZoom:19,attribution:'Esri'}}).addTo(map1);
L.marker(INIT,{{icon:L.divIcon({{html:'<div style="font-size:20px">📍</div>',iconSize:[24,24],iconAnchor:[12,12],className:''}})}}
).bindTooltip('You').addTo(map1);
markers.forEach(m=>{{
  const color=COLORS[m.urgency]||'#6b7280';
  L.circleMarker([m.lat,m.lon],{{radius:8,color:color,fillColor:color,fillOpacity:0.85,weight:2}})
   .bindPopup(`<b>${{m.urgency}}</b><br>${{m.text}}<br><small>${{m.dept}}</small>`)
   .bindTooltip(m.urgency+': '+m.text.slice(0,40))
   .addTo(map1);
}});

// ── Map 2: Live Route ─────────────────────────────
const map2=L.map('map2').setView(INIT,15);
L.tileLayer(TILES,{{maxZoom:19,attribution:'Esri'}}).addTo(map2);
L.marker(DEST,{{icon:L.divIcon({{html:'<div style="font-size:24px">🚨</div>',iconSize:[28,28],iconAnchor:[14,14],className:''}})}}
).bindTooltip('Destination').addTo(map2);
const userIcon=L.divIcon({{html:'<div style="width:16px;height:16px;border-radius:50%;background:#3b82f6;border:3px solid #fff;box-shadow:0 0 0 5px rgba(59,130,246,0.3)"></div>',iconSize:[16,16],iconAnchor:[8,8],className:''}});
const userMarker=L.marker(INIT,{{icon:userIcon,zIndexOffset:1000}}).bindTooltip('You').addTo(map2);
let routeLine=routeCoords.length?L.polyline(routeCoords,{{color:'#facc15',weight:5,opacity:0.85}}).addTo(map2):null;
setTimeout(()=>{{map1.invalidateSize();map2.invalidateSize();if(routeLine)map2.fitBounds(routeLine.getBounds(),{{padding:[30,30]}});}},300);

// Prime speechSynthesis on first user interaction (required by browsers)
// ── Live tracking ─────────────────────────────────
function haversine(a,b){{const R=6371000,dLat=(b[0]-a[0])*Math.PI/180,dLon=(b[1]-a[1])*Math.PI/180;const s=Math.sin(dLat/2)**2+Math.cos(a[0]*Math.PI/180)*Math.cos(b[0]*Math.PI/180)*Math.sin(dLon/2)**2;return R*2*Math.atan2(Math.sqrt(s),Math.sqrt(1-s));}}
function minDistToRoute(pos){{if(!routeCoords.length)return 0;let min=Infinity;for(let i=0;i<routeCoords.length-1;i++){{const a=routeCoords[i],b=routeCoords[i+1],dx=b[1]-a[1],dy=b[0]-a[0],len2=dx*dx+dy*dy;let t=len2?Math.max(0,Math.min(1,((pos[1]-a[1])*dx+(pos[0]-a[0])*dy)/len2)):0;min=Math.min(min,haversine(pos,[a[0]+t*dy,a[1]+t*dx]));}}return min;}}
function headingWaypoint(from,to,d){{const R=6371000,la=from[0]*Math.PI/180,lo=from[1]*Math.PI/180,br=Math.atan2(Math.sin((to[1]-from[1])*Math.PI/180)*Math.cos(to[0]*Math.PI/180),Math.cos(from[0]*Math.PI/180)*Math.sin(to[0]*Math.PI/180)-Math.sin(from[0]*Math.PI/180)*Math.cos(to[0]*Math.PI/180)*Math.cos((to[1]-from[1])*Math.PI/180)),dd=d/R,la2=Math.asin(Math.sin(la)*Math.cos(dd)+Math.cos(la)*Math.sin(dd)*Math.cos(br));return[la2*180/Math.PI,(lo+Math.atan2(Math.sin(br)*Math.sin(dd)*Math.cos(la),Math.cos(dd)-Math.sin(la)*Math.sin(la2)))*180/Math.PI];}}
let stepIdx=0,lastSpoken='',rerouting=false,lastPos=null, navActive = false;

window.addEventListener("message", (event) => {{
  if(event.data.type === "LIVE_LOCATION"){{
    const lat = event.data.latitude;
    const lon = event.data.longitude;

    userMarker.setLatLng([lat, lon]);
    map2.panTo([lat, lon], {{ animate: true, duration: 0.5 }});
    map1.panTo([lat, lon], {{ animate: true, duration: 0.5 }});

    if(navActive){{
      if(steps.length && stepIdx < steps.length){{
        steps[stepIdx].distance = Math.max(0, Math.round(haversine([lat, lon], DEST)));
      }}
      updateNav();
      if(minDistToRoute([lat, lon]) > 30){{ reroute(lat, lon); }}
    }}
    lastPos = [lat, lon];
  }}
}});
function speak(t){{if(t===lastSpoken)return;lastSpoken=t;const u=new SpeechSynthesisUtterance(t);u.lang='en-IN';u.rate=0.9;u.pitch=1;u.volume=1;window.speechSynthesis.cancel();window.speechSynthesis.speak(u);}}
function updateNav(){{if(!steps.length)return;while(stepIdx<steps.length-1&&steps[stepIdx].distance<30)stepIdx++;const s=steps[stepIdx];speak((s.instruction||'Continue')+(s.road?' on '+s.road:'')+(s.distance?', in '+s.distance+' meters':''));}}
async function reroute(lat,lon){{if(rerouting)return;rerouting=true;speak('Rerouting');try{{let via='';if(lastPos&&haversine(lastPos,[lat,lon])>5){{const wp=headingWaypoint(lastPos,[lat,lon],200);via=wp[1]+','+wp[0]+';';}}const r=await fetch('https://router.project-osrm.org/route/v1/driving/'+lon+','+lat+';'+via+DEST[1]+','+DEST[0]+'?overview=full&geometries=geojson&steps=true');const d=await r.json();const route=d.routes[0];if(routeLine)map2.removeLayer(routeLine);routeLine=L.polyline(route.geometry.coordinates.map(c=>[c[1],c[0]]),{{color:'#facc15',weight:5,opacity:0.85}}).addTo(map2);routeCoords.length=0;route.geometry.coordinates.forEach(c=>routeCoords.push([c[1],c[0]]));steps.length=0;stepIdx=0;for(const leg of route.legs)for(const step of leg.steps){{const m=step.maneuver||{{}};steps.push({{instruction:m.instruction||(m.type||'Continue'),road:step.name||step.ref||'the road ahead',distance:Math.round(step.distance||0)}});}}
  const d_card = document.getElementById('live-dist-card');
  const t_card = document.getElementById('live-eta-card');
  if (d_card) d_card.textContent = (route.distance/1000).toFixed(2) + ' km';
  if (t_card) t_card.textContent = (route.duration/60).toFixed(1) + ' mins';
  }}catch(e){{console.error(e);}}rerouting=false;}}
function startNav(){{
  document.getElementById('start-btn').style.display='none';
  navActive = true;
  const go=()=>{{
    const u=new SpeechSynthesisUtterance('Navigation started. Follow the route.');
    u.lang='en-IN'; u.rate=0.9; u.volume=1;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  }};
  const voices=window.speechSynthesis.getVoices();
  if(voices.length){{ go(); }} else {{ window.speechSynthesis.onvoiceschanged=go; }}
}}
</script></body></html>""", height=460, width=10000, scrolling=False)

        if route_data and route_data.get("steps"):
            s = route_data["steps"][0]
            st.markdown(f"""
            <div style="position:relative;background:#111827;border:2px solid #2563eb;border-radius:16px;
              padding:20px;margin-top:16px;box-shadow:0 0 20px rgba(37,99,235,0.35);animation:pulse 2s infinite;">
              <style>@keyframes pulse{{0%,100%{{box-shadow:0 0 20px rgba(37,99,235,0.35)}}50%{{box-shadow:0 0 32px rgba(37,99,235,0.7)}}}}</style>
              <div style="font-size:12px;color:#60a5fa;font-weight:700;letter-spacing:1px;margin-bottom:10px;">LIVE NAVIGATION</div>
              <div style="font-size:28px;font-weight:800;color:white;margin-bottom:12px;">{s.get('instruction','Continue')}</div>
              <div style="font-size:18px;color:#d1d5db;">🛣️ {s.get('road','')}</div>
              <div style="margin-top:10px;font-size:16px;color:#facc15;font-weight:700;">📍 in {s.get('distance',0)} meters</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # =================================================
        # COMPLAINT LIST
        # =================================================

        st.markdown(f"""
        <div style="font-size:16px; font-weight:700; color:#e6edf3; margin-bottom:14px;">
          📋 Complaints &nbsp;
          <span style="font-size:13px; color:#8b949e; font-weight:400;">({len(complaints)} shown)</span>
        </div>
        """, unsafe_allow_html=True)

        if not complaints:
            st.markdown("""
            <div style="text-align:center; padding:40px; color:#484f58;">
              No complaints match this filter.
            </div>
            """, unsafe_allow_html=True)

        for item in complaints:
            urgency  = item.get("urgency", "UNKNOWN")
            cfg      = URGENCY_CONFIG.get(urgency, URGENCY_CONFIG["UNKNOWN"])
            lat      = item.get("latitude")
            lon      = item.get("longitude")
            loc_name = safe_location(item.get("location"), lat, lon)
            status   = item.get("status", "N/A")
            dept     = item.get("department", "N/A")
            eta      = item.get("eta", "N/A")
            created  = str(item.get("created_at", ""))[:16]
            text     = item.get("complaint_text", "")
            expl     = item.get("explanation", "")

            st.markdown(f"""
            <div style="
              background:#161b22;
              border:1px solid #21262d;
              border-left:4px solid {cfg['border']};
              border-radius:10px;
              padding:16px 20px;
              margin-bottom:10px;
            ">
              <!-- Top row -->
              <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
                <span style="
                  display:inline-flex; align-items:center; gap:6px;
                  background:{cfg['bg']}; border:1px solid {cfg['border']};
                  border-radius:999px; padding:4px 12px;
                  font-size:12px; font-weight:700; color:{cfg['color']};
                ">{cfg['emoji']} &nbsp;{urgency}</span>
                <span style="font-size:11px; color:#484f58;">🕒 {created}</span>
              </div>
              <!-- Meta row -->
              <div style="display:flex; gap:20px; flex-wrap:wrap; margin-bottom:12px;">
                <span style="font-size:12px; color:#8b949e;">🏢 <b style="color:#c9d1d9;">{dept}</b></span>
                <span style="font-size:12px; color:#8b949e;">📌 <b style="color:#c9d1d9;">{status}</b></span>
                <span style="font-size:12px; color:#8b949e;">⏳ <b style="color:#c9d1d9;">{eta}</b></span>
                <span style="font-size:12px; color:#8b949e;">📍 <b style="color:#c9d1d9;">{loc_name}</b></span>
              </div>
              <!-- Complaint text -->
              <div style="
                background:#0d1117; border:1px solid #21262d; border-radius:8px;
                padding:10px 14px; font-size:13px; color:#c9d1d9;
                line-height:1.6; margin-bottom:10px; font-family:monospace;
              ">{text}</div>
              <!-- Explanation -->
              <div style="
                background:#0d1117; border-left:3px solid #1f6feb;
                border-radius:0 8px 8px 0; padding:10px 14px;
                font-size:13px; color:#8b949e; line-height:1.6;
              ">🧠 &nbsp;{expl}</div>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
        
