import os
import requests
import streamlit as st
import folium

from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation


API_URL = os.getenv("BACKEND_API_URL", "https://backend-api-duvj.onrender.com")


# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Multi-Agent AI Complaint System",
    layout="wide"
)

st.title("🚨 Multi-Agent AI Complaint System")


# =====================================================
# SESSION STATE
# =====================================================

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None


# =====================================================
# FETCH COMPLAINTS
# =====================================================

@st.cache_data(ttl=30)
def fetch_complaints():

    response = requests.get(
        f"{API_URL}/complaints"
    )

    return response.json()


# =====================================================
# REVERSE GEOCODING
# =====================================================

# =====================================================
# SMART REVERSE GEOCODING
# =====================================================

@st.cache_data(ttl=3600)
def reverse_geocode(lat, lon):

    try:

        url = (
            "https://nominatim.openstreetmap.org/"
            f"reverse?format=json&lat={lat}&lon={lon}"
        )

        headers = {
            "User-Agent": "civic-ai-system"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=5
        )

        data = response.json()

        address = data.get(
            "address",
            {}
        )

        # 🔥 smarter readable location extraction

        location_name = (

            address.get("road")

            or

            address.get("neighbourhood")

            or

            address.get("suburb")

            or

            address.get("city")

            or

            address.get("town")

            or

            address.get("village")

            or

            data.get("display_name")
        )

        return location_name

    except:

        return None


# =====================================================
# ROUTE FUNCTION
# =====================================================

@st.cache_data(ttl=300)
def get_route(
    start_lat,
    start_lon,
    end_lat,
    end_lon
):

    try:

        url = (

            "http://router.project-osrm.org/"
            f"route/v1/driving/"
            f"{start_lon},{start_lat};"
            f"{end_lon},{end_lat}"
            f"?overview=full&geometries=geojson"
        )

        response = requests.get(
            url,
            timeout=5
        )

        data = response.json()

        routes = data.get("routes")

        if not routes:
            return None

        route = routes[0]

        return {

            "coordinates":
            route["geometry"]["coordinates"],

            "distance":
            round(
                route["distance"] / 1000,
                2
            ),

            "duration":
            round(
                route["duration"] / 60,
                2
            )
        }

    except:
        return None


# =====================================================
# BADGES
# =====================================================

def urgency_badge(level):

    badges = {

        "LOW": "🟢",

        "MEDIUM": "🟡",

        "HIGH": "🟠",

        "CRITICAL": "🔴"
    }

    return badges.get(level, "⚪")


# =====================================================
# TABS
# =====================================================

tab1, tab2 = st.tabs([

    "📝 Submit Complaint",

    "📜 Dashboard"
])


# =====================================================
# TAB 1
# =====================================================

with tab1:

    st.header("Submit Complaint")

    complaint_text = st.text_area(
        "Enter Complaint",
        height=180
    )

    location_text = st.text_input(
        "📍 Exact Location"
    )

    if st.button("Analyze Complaint"):

        if not complaint_text:

            st.warning(
                "Please enter complaint"
            )

        elif not location_text:

            st.warning(
                "Please enter location"
            )

        else:

            with st.spinner(
                "Running AI Agents..."
            ):

                try:

                    response = requests.post(

                        f"{API_URL}/analyze",

                        json={

                            "text":
                            complaint_text,

                            "location":
                            location_text
                        }
                    )

                    if (
                        response.status_code
                        != 200
                    ):

                        st.error(
                            response.text
                        )

                    else:

                        st.session_state.analysis_result = (
                            response.json()
                        )

                        st.cache_data.clear()

                except Exception as e:

                    st.error(str(e))

    # =================================================
    # RESULT
    # =================================================

    if st.session_state.analysis_result:

        data = (
            st.session_state.analysis_result
        )

        urgency = data.get(
            "urgency",
            "UNKNOWN"
        )

        badge = urgency_badge(
            urgency
        )

        st.success(
            "Analysis Complete"
        )

        st.markdown(
            f"## {badge} {urgency}"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.metric(

                "🏢 Department",

                data.get(
                    "department"
                )
            )

        with col2:

            st.metric(

                "⏳ ETA",

                data.get(
                    "estimated_resolution_time"
                )
            )

        st.subheader(
            "🧠 Explanation"
        )

        st.info(
            data.get(
                "explanation"
            )
        )


# =====================================================
# TAB 2
# =====================================================

with tab2:

    st.header(
        "📜 Complaint Dashboard"
    )

    # =================================================
    # GPS
    # =================================================

    geo = streamlit_geolocation()

    if geo["latitude"] is not None:

        user_lat = geo["latitude"]
        user_lon = geo["longitude"]

    else:

        user_lat = 29.2144809
        user_lon = 79.5279012

    # =================================================
    # FILTER
    # =================================================

    filter_option = st.selectbox(

        "🔍 Filter by Urgency",

        [

            "ALL",

            "LOW",

            "MEDIUM",

            "HIGH",

            "CRITICAL"
        ]
    )

    try:

        complaints = fetch_complaints()

        # =================================================
        # FILTERING
        # =================================================

        if filter_option != "ALL":

            complaints = [

                c for c in complaints

                if c.get(
                    "urgency"
                ) == filter_option
            ]

        complaints = complaints[:20]

        # =================================================
        # HOTSPOT MAP
        # =================================================

        hotspot_map = folium.Map(

            location=[
                user_lat,
                user_lon
            ],

            zoom_start=12
        )

        # =================================================
        # USER LOCATION
        # =================================================

        folium.Marker(

            [
                user_lat,
                user_lon
            ],

            popup="📍 Your Location",

            icon=folium.Icon(
                color="blue"
            )

        ).add_to(
            hotspot_map
        )

        valid_complaints = []

        # =================================================
        # COMPLAINT MARKERS
        # =================================================

        for item in complaints:

            lat = item.get("latitude")
            lon = item.get("longitude")

            if (
                lat is not None
                and
                lon is not None
            ):

                valid_complaints.append(
                    item
                )

                urgency = item.get(
                    "urgency",
                    "LOW"
                )

                location_name = (

                    item.get("location")

                    or

                    reverse_geocode(
                        lat,
                        lon
                    )

                    or

                    f"{lat}, {lon}"
                )

                color_map = {

                    "LOW":
                    "green",

                    "MEDIUM":
                    "blue",

                    "HIGH":
                    "orange",

                    "CRITICAL":
                    "red"
                }

                route_data = get_route(

                    user_lat,
                    user_lon,

                    lat,
                    lon
                )

                distance = "N/A"

                if route_data:

                    distance = (
                        f"{route_data['distance']} km"
                    )

                popup_html = f"""

                <div style="width:250px;">

                    <h3>
                    🚨 Complaint Event
                    </h3>

                    <b>Complaint:</b><br>
                    {item.get('complaint_text')}
                    <br><br>

                    <b>📍 Location:</b><br>
                    {location_name}
                    <br><br>

                    <b>🚦 Urgency:</b><br>
                    {urgency}
                    <br><br>

                    <b>📏 Distance:</b><br>
                    {distance}

                </div>

                """

                folium.Marker(

                    [lat, lon],

                    popup=folium.Popup(
                        popup_html,
                        max_width=300
                    ),

                    tooltip=item.get(
                        "complaint_text"
                    ),

                    icon=folium.Icon(

                        color=color_map.get(
                            urgency,
                            "gray"
                        )
                    )

                ).add_to(
                    hotspot_map
                )

        # =================================================
        # ROUTE NAVIGATION
        # =================================================

        st.subheader(
            "🚗 Route Navigation"
        )

        selected = None

        if valid_complaints:

            selected = st.selectbox(

                "Select complaint",

                valid_complaints,

                format_func=lambda x:
                x.get(
                    "complaint_text",
                    "Unknown"
                )[:50]
            )

        route_map = None
        route_data = None

        # =================================================
        # ROUTE MAP
        # =================================================

        if selected:

            route_data = get_route(

                user_lat,
                user_lon,

                selected["latitude"],
                selected["longitude"]
            )

            if route_data:

                route_map = folium.Map(

                    location=[
                        user_lat,
                        user_lon
                    ],

                    zoom_start=12
                )

                points = [

                    [p[1], p[0]]

                    for p in
                    route_data[
                        "coordinates"
                    ]
                ]

                folium.PolyLine(

                    points,

                    weight=6,

                    color="blue"

                ).add_to(
                    route_map
                )

                # USER MARKER

                folium.Marker(

                    [
                        user_lat,
                        user_lon
                    ],

                    popup="📍 YOU",

                    icon=folium.Icon(
                        color="blue"
                    )

                ).add_to(
                    route_map
                )

                # LOCATION

                selected_location = (

                    selected.get("location")

                    or

                    reverse_geocode(

                        selected["latitude"],

                        selected["longitude"]
                    )

                    or

                    f"{selected['latitude']}, "
                    f"{selected['longitude']}"
                )

                popup_route = f"""

                <div style="width:250px;">

                    <h3>
                    🚨 Event Location
                    </h3>

                    <b>Complaint:</b><br>
                    {selected.get('complaint_text')}
                    <br><br>

                    <b>📍 Location:</b><br>
                    {selected_location}
                    <br><br>

                    <b>📏 Distance:</b><br>
                    {route_data['distance']} km
                    <br><br>

                    <b>⏱ ETA:</b><br>
                    {route_data['duration']} mins

                </div>

                """

                folium.Marker(

                    [

                        selected["latitude"],

                        selected["longitude"]
                    ],

                    popup=folium.Popup(
                        popup_route,
                        max_width=300
                    ),

                    tooltip="🚨 Event",

                    icon=folium.Icon(
                        color="red"
                    )

                ).add_to(
                    route_map
                )

        # =================================================
        # ETA DISPLAY
        # =================================================

        if route_data:

            st.success(

                f"📏 Distance: "

                f"{route_data['distance']} km "

                f"| "

                f"⏱ ETA: "

                f"{route_data['duration']} mins"
            )

        # =================================================
        # MAPS SIDE BY SIDE
        # =================================================

        col1, col2 = st.columns(2)

        with col1:

            st.subheader(
                "🗺️ Complaint Hotspots"
            )

            st_folium(

                hotspot_map,

                height=600,

                width=None
            )

        with col2:

            st.subheader(
                "🚗 Route Map"
            )

            if route_map:

                st_folium(

                    route_map,

                    height=600,

                    width=None
                )

        st.divider()

        # =================================================
        # COMPLAINT LIST
        # =================================================

        for item in complaints:

            urgency = item.get(
                "urgency",
                "UNKNOWN"
            )

            badge = urgency_badge(
                urgency
            )

            lat = item.get("latitude")
            lon = item.get("longitude")

            location_name = (

                item.get("location")

                or

                reverse_geocode(
                    lat,
                    lon
                )

                or

                f"{lat}, {lon}"
            )

            with st.container():

                st.markdown(
                    f"### {badge} {urgency}"
                )

                c1, c2, c3 = st.columns(3)

                with c1:

                    st.write(

                        f"🏢 Department: "

                        f"{item.get('department')}"
                    )

                with c2:

                    st.write(

                        f"📌 Status: "

                        f"{item.get('status')}"
                    )

                with c3:

                    st.write(

                        f"🕒 "

                        f"{item.get('created_at')}"
                    )

                st.write(
                    "📝 Complaint"
                )

                st.code(
                    item.get(
                        "complaint_text"
                    )
                )

                st.write(

                    f"📍 Location: "

                    f"{location_name}"
                )

                st.write(

                    f"⏳ ETA: "

                    f"{item.get('eta')}"
                )

                st.info(
                    item.get(
                        "explanation"
                    )
                )

                st.divider()

    except Exception as e:

        st.error(str(e))