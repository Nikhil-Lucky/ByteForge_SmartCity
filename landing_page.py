import pandas as pd
import streamlit as st


def _load_city_snapshot(load_json, get_traffic_zones, get_waterlogging_zones):
    hospitals = load_json("mock_hospitals.json")
    ambulances = load_json("mock_ambulances.json")
    complaints = load_json("mock_complaints.json")
    traffic_zones = get_traffic_zones()
    waterlogging_zones = get_waterlogging_zones()

    hospital_df = pd.DataFrame(hospitals)

    return {
        "hospitals": hospitals,
        "ambulances": ambulances,
        "complaints": complaints,
        "traffic_zones": traffic_zones,
        "waterlogging_zones": waterlogging_zones,
        "available_ambulances": len([a for a in ambulances if a["status"] == "Available"]),
        "emergency_beds": int(hospital_df["emergency_beds"].sum()),
        "icu_beds": int(hospital_df["icu_beds"].sum()),
        "open_complaints": len([c for c in complaints if c["status"] != "Resolved"]),
        "high_traffic_zones": len([t for t in traffic_zones if t["traffic_level"] == "High"]),
        "flood_risk_zones": sum(
            1 for w in waterlogging_zones
            if w["risk_level"] in ["High", "Medium"]
        ),
    }


def render_landing_page(load_json, get_traffic_zones, get_waterlogging_zones, render_kpi_card):
    snapshot = _load_city_snapshot(load_json, get_traffic_zones, get_waterlogging_zones)

    st.markdown(
        """
        <div class="hero">
            <div class="hero-title">🏙️ <span class="hero-gradient">SmartCity</span></div>
            <div class="hero-subtitle">
                Intelligent Multi-Agent System for Real-Time Civic Decision Making.
                SmartCity helps citizens and authorities make faster decisions during emergencies,
                hospital capacity issues, traffic congestion, rain/flood risks, and civic complaints.
            </div>
            <span class="chip">Emergency Response</span>
            <span class="chip">Hospital Capacity</span>
            <span class="chip">Traffic Risk</span>
            <span class="chip">Flood Alerts</span>
            <span class="chip">Civic Complaints</span>
            <span class="chip">Explainable AI</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="section-heading">🚀 How SmartCity Works</div>', unsafe_allow_html=True)

    flow_col1, flow_col2, flow_col3, flow_col4 = st.columns(4, gap="large")

    with flow_col1:
        st.markdown(
            """
            <div class="status-pill">
                <b>1. Citizen Query</b>
                <span>User asks in natural language like ambulance, pothole, route, rain risk or hospital bed query.</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with flow_col2:
        st.markdown(
            """
            <div class="status-pill">
                <b>2. Router Agent</b>
                <span>SmartCity understands the query and sends it to the right civic agent.</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with flow_col3:
        st.markdown(
            """
            <div class="status-pill">
                <b>3. Decision Agents</b>
                <span>Emergency, traffic, hospital, flood or complaint agents analyze the situation.</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with flow_col4:
        st.markdown(
            """
            <div class="status-pill">
                <b>4. Action + Map</b>
                <span>The system gives a recommendation, explanation, priority and decision map.</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown('<div class="section-heading">📊 Live City Snapshot</div>', unsafe_allow_html=True)

    row1_col1, row1_col2, row1_col3 = st.columns(3, gap="large")

    with row1_col1:
        render_kpi_card("🚑", "Available Ambulances", snapshot["available_ambulances"], "Ready for dispatch")

    with row1_col2:
        render_kpi_card("🏥", "Emergency Beds", snapshot["emergency_beds"], "Across connected hospitals")

    with row1_col3:
        render_kpi_card("🫁", "ICU Beds", snapshot["icu_beds"], "Critical care capacity")

    row2_col1, row2_col2, row2_col3 = st.columns(3, gap="large")

    with row2_col1:
        render_kpi_card("🚦", "High Traffic Zones", snapshot["high_traffic_zones"], "Need route optimization")

    with row2_col2:
        render_kpi_card("🌧️", "Flood Risk Alerts", snapshot["flood_risk_zones"], "Rain-sensitive zones")

    with row2_col3:
        render_kpi_card("📝", "Open Complaints", snapshot["open_complaints"], "Pending civic issues")

    enter_col1, enter_col2, enter_col3 = st.columns([1, 1.4, 1])

    with enter_col2:
        if st.button("Enter SmartCity Dashboard", type="primary", use_container_width=True):
            st.session_state.entered_dashboard = True
            st.rerun()

    st.markdown('<div class="section-heading">🧠 Multi-Agent Architecture</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="status-row">
            <div class="status-pill">
                <b>Router Agent</b>
                <span>Detects whether the query is emergency, traffic, hospital, flood, or complaint related.</span>
            </div>
            <div class="status-pill">
                <b>Data Agent</b>
                <span>Loads weather, traffic, hospital, ambulance and civic issue data.</span>
            </div>
            <div class="status-pill">
                <b>Optimization Agent</b>
                <span>Selects best ambulance, hospital, route or complaint priority.</span>
            </div>
            <div class="status-pill">
                <b>Explanation Agent</b>
                <span>Explains why the recommendation was made in simple language.</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()
    st.caption(
        "SmartCity by Team ByteForge | Hackathon MVP using Streamlit, PyDeck, mock civic data and live weather API."
    )