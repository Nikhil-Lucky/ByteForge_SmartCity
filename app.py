import json
import os
import random
import re
from pathlib import Path

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st
from dotenv import load_dotenv

from landing_page import render_landing_page
from dashboard_page import render_dashboard_page


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()

st.set_page_config(
    page_title="SmartCity",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# UI CSS - COMPACT GLASS THEME
# =========================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at 12% 10%, rgba(239, 68, 68, 0.20), transparent 25%),
            radial-gradient(circle at 80% 10%, rgba(99, 102, 241, 0.22), transparent 30%),
            radial-gradient(circle at 55% 85%, rgba(236, 72, 153, 0.16), transparent 35%),
            linear-gradient(135deg, #020617 0%, #090b1a 48%, #130f24 100%);
        color: #f8fafc;
        overflow-x: hidden;
    }

    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        background:
            linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
        background-size: 48px 48px;
        mask-image: linear-gradient(to bottom, rgba(0,0,0,0.70), transparent 82%);
        z-index: 0;
    }

    [data-testid="stSidebar"],
    [data-testid="collapsedControl"] {
        display: none;
    }

    header {
        background: rgba(2, 6, 23, 0.58) !important;
        backdrop-filter: blur(18px) saturate(170%);
        -webkit-backdrop-filter: blur(18px) saturate(170%);
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }

    .block-container {
        padding-left: 2.2rem;
        padding-right: 2.2rem;
        padding-top: 2.4rem;
        padding-bottom: 2rem;
        max-width: 1180px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background:
            linear-gradient(135deg, rgba(255,255,255,0.09), rgba(255,255,255,0.025));
        backdrop-filter: blur(22px) saturate(175%);
        -webkit-backdrop-filter: blur(22px) saturate(175%);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 22px;
        box-shadow:
            0 18px 45px rgba(0, 0, 0, 0.30),
            inset 0 1px 0 rgba(255,255,255,0.14);
        padding: 8px;
    }

    .hero {
        position: relative;
        overflow: hidden;
        padding: 30px 32px;
        border-radius: 28px;
        margin-top: 6px;
        margin-bottom: 30px;
        background:
            linear-gradient(135deg, rgba(255,255,255,0.13), rgba(255,255,255,0.035)),
            radial-gradient(circle at 15% 20%, rgba(239,68,68,0.20), transparent 34%),
            radial-gradient(circle at 82% 20%, rgba(99,102,241,0.28), transparent 40%),
            rgba(15, 23, 42, 0.54);
        backdrop-filter: blur(26px) saturate(180%);
        -webkit-backdrop-filter: blur(26px) saturate(180%);
        border: 1px solid rgba(255,255,255,0.15);
        box-shadow:
            0 24px 70px rgba(0,0,0,0.38),
            inset 0 1px 0 rgba(255,255,255,0.18);
        animation: fadeUp 0.65s ease both;
    }

    .hero:before {
        content: "";
        position: absolute;
        width: 260px;
        height: 260px;
        border-radius: 999px;
        background: linear-gradient(135deg, rgba(239,68,68,0.25), rgba(99,102,241,0.20));
        filter: blur(70px);
        top: -110px;
        right: -70px;
        animation: floatGlow 6s ease-in-out infinite alternate;
    }

    .hero-title {
        position: relative;
        z-index: 2;
        font-size: 48px;
        line-height: 1;
        font-weight: 950;
        letter-spacing: -1.5px;
        color: #ffffff;
        margin-bottom: 14px;
        text-shadow: 0 12px 38px rgba(0,0,0,0.32);
    }

    .hero-gradient {
        background: linear-gradient(90deg, #fb7185 0%, #f97316 34%, #a78bfa 70%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-subtitle {
        position: relative;
        z-index: 2;
        font-size: 16px;
        line-height: 1.65;
        color: rgba(226, 232, 240, 0.90);
        max-width: 980px;
        margin-bottom: 18px;
    }

    .chip {
        position: relative;
        z-index: 2;
        display: inline-block;
        padding: 8px 13px;
        margin: 5px 7px 5px 0;
        border-radius: 999px;
        background:
            linear-gradient(135deg, rgba(255,255,255,0.15), rgba(255,255,255,0.055));
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255,255,255,0.16);
        color: #f8fafc;
        font-size: 12px;
        font-weight: 850;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.18), 0 8px 20px rgba(0,0,0,0.16);
    }

    .section-heading {
        font-size: 27px;
        font-weight: 950;
        color: #f8fafc;
        margin-top: 28px;
        margin-bottom: 16px;
        letter-spacing: -0.5px;
        text-shadow: 0 12px 32px rgba(0,0,0,0.35);
    }

    .query-title {
        font-size: 22px;
        font-weight: 900;
        color: #f8fafc;
        margin-bottom: 6px;
    }

    .query-sub {
        color: rgba(203, 213, 225, 0.86);
        font-size: 13px;
        margin-bottom: 14px;
        line-height: 1.6;
    }

    .kpi-card {
        position: relative;
        overflow: hidden;
        min-height: 118px;
        height: 100%;
        padding: 20px 22px;
        border-radius: 26px;
        background:
            linear-gradient(135deg, rgba(255,255,255,0.11), rgba(255,255,255,0.03)),
            radial-gradient(circle at 85% 12%, rgba(251,113,133,0.18), transparent 38%),
            rgba(15,23,42,0.52);
        backdrop-filter: blur(24px) saturate(175%);
        -webkit-backdrop-filter: blur(24px) saturate(175%);
        border: 1px solid rgba(255,255,255,0.13);
        box-shadow:
            0 20px 55px rgba(0,0,0,0.30),
            inset 0 1px 0 rgba(255,255,255,0.15);
        transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
        animation: fadeUp 0.65s ease both;
        margin-bottom: 20px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .kpi-card:hover {
        transform: translateY(-5px) scale(1.01);
        border-color: rgba(251,113,133,0.48);
        box-shadow:
            0 26px 70px rgba(239,68,68,0.14),
            0 22px 60px rgba(0,0,0,0.34),
            inset 0 1px 0 rgba(255,255,255,0.22);
    }

    .kpi-icon {
        position: relative;
        font-size: 27px;
        margin-bottom: 10px;
        filter: drop-shadow(0 10px 18px rgba(0,0,0,0.28));
    }

    .kpi-label {
        position: relative;
        color: rgba(203, 213, 225, 0.76);
        font-size: 11px;
        font-weight: 950;
        text-transform: uppercase;
        letter-spacing: 0.12em;
    }

    .kpi-value {
        position: relative;
        color: #ffffff;
        font-size: 38px;
        font-weight: 950;
        line-height: 1.05;
        margin-top: 7px;
        text-shadow: 0 12px 34px rgba(0,0,0,0.35);
    }

    .kpi-note {
        position: relative;
        color: #fda4af;
        font-size: 12px;
        font-weight: 850;
        margin-top: 8px;
    }

    .status-row {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 14px;
        margin-bottom: 24px;
    }

    .status-pill {
        min-height: 108px;
        height: 100%;
        padding: 16px 16px 15px 16px;
        border-radius: 22px;
        background:
            linear-gradient(135deg, rgba(255,255,255,0.10), rgba(255,255,255,0.025)),
            rgba(15,23,42,0.50);
        backdrop-filter: blur(22px) saturate(170%);
        -webkit-backdrop-filter: blur(22px) saturate(170%);
        border: 1px solid rgba(255,255,255,0.13);
        color: #e2e8f0;
        box-shadow: 0 14px 36px rgba(0,0,0,0.24), inset 0 1px 0 rgba(255,255,255,0.14);
        display: flex;
        flex-direction: column;
    }

    .status-pill b {
        color: #ffffff;
        font-size: 14px;
    }

    .status-pill span {
        display: block;
        color: rgba(203,213,225,0.75);
        font-size: 12px;
        margin-top: 6px;
        line-height: 1.45;
    }

    .legend-box {
        padding: 20px;
        border-radius: 24px;
        background:
            linear-gradient(135deg, rgba(255,255,255,0.10), rgba(255,255,255,0.025)),
            rgba(15,23,42,0.52);
        backdrop-filter: blur(24px) saturate(175%);
        -webkit-backdrop-filter: blur(24px) saturate(175%);
        border: 1px solid rgba(255,255,255,0.13);
        margin-bottom: 16px;
        box-shadow: 0 18px 50px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.14);
    }

    .legend-item {
        font-size: 13px;
        margin-bottom: 12px;
        color: #e2e8f0;
        font-weight: 750;
    }

    .dot {
        height: 11px;
        width: 11px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 9px;
        box-shadow: 0 0 16px currentColor;
    }

    .priority-card {
        padding: 16px;
        border-radius: 22px;
        background:
            linear-gradient(135deg, rgba(255,255,255,0.09), rgba(255,255,255,0.025)),
            rgba(15,23,42,0.50);
        backdrop-filter: blur(22px) saturate(170%);
        -webkit-backdrop-filter: blur(22px) saturate(170%);
        border: 1px solid rgba(255,255,255,0.12);
        margin-bottom: 13px;
        color: #e2e8f0;
        line-height: 1.55;
        font-size: 13px;
        box-shadow: 0 14px 40px rgba(0,0,0,0.22);
    }

    .priority-card b {
        color: #ffffff;
    }

    .priority-high {
        border-left: 5px solid #fb7185;
    }

    .priority-medium {
        border-left: 5px solid #f97316;
    }

    .priority-low {
        border-left: 5px solid #a78bfa;
    }

    .map-note {
        color: rgba(203,213,225,0.72);
        font-size: 12px;
        margin-top: -5px;
        margin-bottom: 12px;
    }

    .status-card {
        padding: 14px 18px;
        border-radius: 20px;
        background:
            linear-gradient(135deg, rgba(239,68,68,0.22), rgba(168,85,247,0.10));
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(251,113,133,0.34);
        color: #fecdd3;
        font-weight: 950;
        margin: 22px 0 14px 0;
        animation: fadeUp 0.5s ease both;
        box-shadow: 0 16px 44px rgba(239,68,68,0.12);
    }

    .stTextInput input {
        background: rgba(2, 6, 23, 0.50) !important;
        backdrop-filter: blur(16px) saturate(175%) !important;
        -webkit-backdrop-filter: blur(16px) saturate(175%) !important;
        border: 1px solid rgba(251, 113, 133, 0.38) !important;
        border-radius: 18px !important;
        color: #f8fafc !important;
        padding: 14px 16px !important;
        font-size: 15px !important;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.09),
            0 12px 30px rgba(0,0,0,0.17) !important;
    }

    .stTextInput input:focus {
        border-color: rgba(244,63,94,0.86) !important;
        box-shadow:
            0 0 0 3px rgba(244,63,94,0.16),
            0 16px 38px rgba(239,68,68,0.15) !important;
    }

    .stButton button {
        border-radius: 18px !important;
        padding: 13px 20px !important;
        font-weight: 900 !important;
        font-size: 14px !important;
        border: 1px solid rgba(255,255,255,0.14) !important;
        background:
            linear-gradient(135deg, #ef4444 0%, #f97316 45%, #a855f7 100%) !important;
        color: white !important;
        box-shadow:
            0 16px 42px rgba(239,68,68,0.24),
            inset 0 1px 0 rgba(255,255,255,0.23) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
    }

    .stButton button:hover {
        transform: translateY(-2px) scale(1.006);
        filter: brightness(1.08);
        box-shadow:
            0 22px 58px rgba(239,68,68,0.30),
            inset 0 1px 0 rgba(255,255,255,0.28) !important;
    }

    .stButton button:active {
        transform: translateY(0px) scale(0.99);
    }

    .stDataFrame {
        border-radius: 22px;
        overflow: hidden;
    }

    canvas,
    iframe {
        border-radius: 18px;
    }

    @media (max-width: 1050px) {
        .status-row {
            grid-template-columns: repeat(2, 1fr);
        }

        .hero-title {
            font-size: 42px;
        }

        .block-container {
            padding-left: 1.5rem;
            padding-right: 1.5rem;
        }
    }

    @media (max-width: 720px) {
        .status-row {
            grid-template-columns: 1fr;
        }

        .hero-title {
            font-size: 34px;
        }

        .hero {
            padding: 24px;
            border-radius: 24px;
        }

        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }

    @keyframes fadeUp {
        from {
            opacity: 0;
            transform: translateY(16px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes floatGlow {
        from {
            transform: translateY(0px) scale(1);
        }
        to {
            transform: translateY(30px) scale(1.06);
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# DATA HELPERS
# =========================================================

def load_json(filename):
    file_path = DATA_DIR / filename
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def safe_load_json(filename, fallback):
    file_path = DATA_DIR / filename

    if not file_path.exists():
        return fallback

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_area_coordinates(area):
    coords = {
        "Jayanagar": [12.9299, 77.5827],
        "JP Nagar": [12.9077, 77.5850],
        "Banashankari": [12.9255, 77.5468],
        "BTM Layout": [12.9166, 77.6101],
        "Silk Board": [12.9177, 77.6238],
        "KR Market": [12.9611, 77.5742],
        "Majestic": [12.9767, 77.5713],
        "Koramangala": [12.9352, 77.6245],
        "Indiranagar": [12.9784, 77.6408],
        "Electronic City": [12.8452, 77.6602],
        "Bengaluru": [12.9716, 77.5946],
    }

    if area in coords:
        return coords[area]

    geocoded = geocode_location_label(area)
    return [geocoded["lat"], geocoded["lon"]]


def extract_custom_location_label(query):
    query_text = (query or "").strip()
    if not query_text:
        return None

    patterns = [
        r"\bnear\s+([a-zA-Z0-9\s\-]+)",
        r"\bin\s+([a-zA-Z0-9\s\-]+)",
        r"\bfrom\s+([a-zA-Z0-9\s\-]+)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, query_text, flags=re.IGNORECASE)
        if match:
            label = match.group(1).strip(" .?,")
            if label:
                return label.title()

    if OPENAI_API_KEY:
        try:
            response = requests.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4.1-mini",
                    "input": [
                        {
                            "role": "system",
                            "content": (
                                "Extract the main Bengaluru area or place name from the user's civic query. "
                                "Return only the place name, or NONE if missing."
                            ),
                        },
                        {"role": "user", "content": query_text},
                    ],
                    "max_output_tokens": 40,
                },
                timeout=8,
            )
            if response.ok:
                data = response.json()
                output_text = data.get("output_text", "").strip()
                if output_text and output_text.upper() != "NONE":
                    return output_text.strip(" .?,").title()
        except Exception:
            pass
    return None


def fallback_coordinates_for_label(label):
    base_lat, base_lon = coords = [12.9716, 77.5946]
    seed = abs(hash(label))
    lat_offset = (((seed % 900) / 10000) - 0.045)
    lon_offset = ((((seed // 900) % 900) / 10000) - 0.045)
    return [round(base_lat + lat_offset, 6), round(base_lon + lon_offset, 6)]


def geocode_location_label(label):
    cache = st.session_state.setdefault("app_geocode_cache", {})
    cache_key = label.strip().lower()
    if cache_key in cache:
        return cache[cache_key]

    if GOOGLE_MAPS_API_KEY:
        queries = [
            f"{label}, Bengaluru, Karnataka, India",
            f"{label}, Bangalore, Karnataka, India",
            f"{label}, India",
        ]
        for search_query in queries:
            try:
                response = requests.get(
                    "https://maps.googleapis.com/maps/api/geocode/json",
                    params={"address": search_query, "key": GOOGLE_MAPS_API_KEY},
                    timeout=5,
                )
                if not response.ok:
                    continue
                data = response.json()
                if data.get("status") != "OK" or not data.get("results"):
                    continue

                location = data["results"][0]["geometry"]["location"]
                geocoded = {
                    "label": label.title(),
                    "lat": float(location["lat"]),
                    "lon": float(location["lng"]),
                }
                cache[cache_key] = geocoded
                return geocoded
            except Exception:
                continue

    queries = [
        f"{label}, Bengaluru, Karnataka, India",
        f"{label}, Bangalore, Karnataka, India",
        f"{label}, India",
    ]
    headers = {"User-Agent": "ByteForge-SmartCity/1.0"}

    for search_query in queries:
        try:
            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": search_query, "format": "jsonv2", "limit": 1},
                headers=headers,
                timeout=4,
            )
            if not response.ok:
                continue
            data = response.json()
            if not data:
                continue

            geocoded = {
                "label": label.title(),
                "lat": float(data[0]["lat"]),
                "lon": float(data[0]["lon"]),
            }
            cache[cache_key] = geocoded
            return geocoded
        except Exception:
            continue

    lat, lon = fallback_coordinates_for_label(label)
    fallback = {"label": label.title(), "lat": lat, "lon": lon}
    cache[cache_key] = fallback
    return fallback


def build_local_hospital_pool(area):
    area_lat, area_lon = get_area_coordinates(area)
    hospitals = load_json("mock_hospitals.json")
    local_hospitals = [
        item for item in hospitals
        if item.get("area") == area or abs(item["lat"] - area_lat) + abs(item["lon"] - area_lon) <= 0.10
    ]

    names = [
        f"{area} General Hospital",
        f"{area} Care Center",
        f"{area} Emergency Clinic",
        f"{area} Metro Hospital",
    ]
    offsets = [
        (0.0038, 0.0031),
        (-0.0042, 0.0028),
        (0.0047, -0.0036),
        (-0.0033, -0.0048),
    ]
    beds = [14, 9, 6, 11]
    icu_beds = [6, 4, 3, 5]
    loads = [58, 66, 49, 61]
    seen_names = {item["name"] for item in local_hospitals}

    for index, name in enumerate(names):
        if name in seen_names:
            continue
        offset_lat, offset_lon = offsets[index]
        local_hospitals.append({
            "name": name,
            "area": area,
            "lat": round(area_lat + offset_lat, 6),
            "lon": round(area_lon + offset_lon, 6),
            "emergency_beds": beds[index],
            "icu_beds": icu_beds[index],
            "load_percent": loads[index],
        })

    return local_hospitals


def build_local_traffic_pool(area):
    area_lat, area_lon = get_area_coordinates(area)
    base_zones = get_traffic_zones()
    local_zones = [
        item for item in base_zones
        if item.get("area") == area or abs(item["lat"] - area_lat) + abs(item["lon"] - area_lon) <= 0.10
    ]

    generated = [
        {
            "zone": f"{area} Main Junction",
            "area": area,
            "lat": round(area_lat + 0.0045, 6),
            "lon": round(area_lon + 0.0035, 6),
            "traffic_level": "High",
            "avg_delay_min": 22,
            "risk": "Peak junction congestion",
        },
        {
            "zone": f"{area} Market Road",
            "area": area,
            "lat": round(area_lat - 0.0038, 6),
            "lon": round(area_lon + 0.0029, 6),
            "traffic_level": "Medium",
            "avg_delay_min": 14,
            "risk": "Mixed local traffic",
        },
        {
            "zone": f"{area} Signal Circle",
            "area": area,
            "lat": round(area_lat + 0.0027, 6),
            "lon": round(area_lon - 0.0042, 6),
            "traffic_level": "Medium",
            "avg_delay_min": 11,
            "risk": "Signal delay and turning traffic",
        },
    ]

    seen = {item["zone"] for item in local_zones}
    for zone in generated:
        if zone["zone"] not in seen:
            local_zones.append(zone)

    return local_zones


def build_local_waterlogging_pool(area):
    area_lat, area_lon = get_area_coordinates(area)
    base_zones = get_waterlogging_zones()
    local_zones = [
        item for item in base_zones
        if item.get("area") == area or abs(item["lat"] - area_lat) + abs(item["lon"] - area_lon) <= 0.10
    ]

    generated = [
        {
            "zone": f"{area} Underpass",
            "area": area,
            "lat": round(area_lat + 0.0031, 6),
            "lon": round(area_lon - 0.0037, 6),
            "risk_level": "High",
            "reason": "Low-lying stretch during heavy rain",
        },
        {
            "zone": f"{area} Main Road",
            "area": area,
            "lat": round(area_lat - 0.0044, 6),
            "lon": round(area_lon + 0.0025, 6),
            "risk_level": "Medium",
            "reason": "Water stagnation near drains",
        },
    ]

    seen = {item["zone"] for item in local_zones}
    for zone in generated:
        if zone["zone"] not in seen:
            local_zones.append(zone)

    return local_zones


def build_local_complaint_pool(area, category, department, priority):
    area_lat, area_lon = get_area_coordinates(area)
    complaints = load_json("mock_complaints.json")
    similar = [
        item for item in complaints
        if item["area"].lower() == area.lower() or category.lower() in item["category"].lower()
    ]

    generated = [
        {
            "id": "CMP-LOCAL-01",
            "category": category,
            "area": area,
            "priority": priority,
            "status": "In Progress",
            "department": department,
            "lat": round(area_lat + 0.0038, 6),
            "lon": round(area_lon + 0.0028, 6),
        },
        {
            "id": "CMP-LOCAL-02",
            "category": category,
            "area": area,
            "priority": "Medium" if priority == "High" else priority,
            "status": "Registered",
            "department": department,
            "lat": round(area_lat - 0.0032, 6),
            "lon": round(area_lon - 0.0041, 6),
        },
        {
            "id": "CMP-LOCAL-03",
            "category": category,
            "area": area,
            "priority": priority,
            "status": "Assigned",
            "department": department,
            "lat": round(area_lat + 0.0024, 6),
            "lon": round(area_lon - 0.0027, 6),
        },
    ]

    seen = {item["id"] for item in similar}
    for item in generated:
        if item["id"] not in seen:
            similar.append(item)

    return similar


def detect_route_endpoints(query):
    query_lower = query.lower()
    from_match = re.search(r"\bfrom\s+([a-zA-Z0-9\s\-]+?)\s+to\s+([a-zA-Z0-9\s\-]+)", query_lower)
    if from_match:
        start = from_match.group(1).strip(" .?,").title()
        end = from_match.group(2).strip(" .?,").title()
        return start, end

    area = detect_area(query)
    return area, "Bengaluru"


def get_traffic_zones():
    fallback = [
        {
            "zone": "Silk Board Junction",
            "area": "Silk Board",
            "lat": 12.9177,
            "lon": 77.6238,
            "traffic_level": "High",
            "avg_delay_min": 28,
            "risk": "Severe congestion during peak hours"
        },
        {
            "zone": "KR Market",
            "area": "KR Market",
            "lat": 12.9611,
            "lon": 77.5742,
            "traffic_level": "High",
            "avg_delay_min": 22,
            "risk": "Heavy market traffic and slow movement"
        },
        {
            "zone": "Majestic",
            "area": "Majestic",
            "lat": 12.9767,
            "lon": 77.5713,
            "traffic_level": "Medium",
            "avg_delay_min": 16,
            "risk": "Bus and railway station congestion"
        },
        {
            "zone": "Jayanagar 4th Block",
            "area": "Jayanagar",
            "lat": 12.9299,
            "lon": 77.5827,
            "traffic_level": "Medium",
            "avg_delay_min": 12,
            "risk": "Commercial area congestion"
        }
    ]

    return safe_load_json("traffic_zones.json", fallback)


def get_waterlogging_zones():
    fallback = [
        {
            "zone": "Silk Board Underpass",
            "area": "Silk Board",
            "lat": 12.9172,
            "lon": 77.6229,
            "risk_level": "High",
            "reason": "Low-lying junction with heavy traffic"
        },
        {
            "zone": "KR Market Side Roads",
            "area": "KR Market",
            "lat": 12.9609,
            "lon": 77.5735,
            "risk_level": "Medium",
            "reason": "Drainage pressure during heavy rain"
        },
        {
            "zone": "BTM Layout Main Road",
            "area": "BTM Layout",
            "lat": 12.9166,
            "lon": 77.6101,
            "risk_level": "Medium",
            "reason": "Water stagnation during peak rain"
        }
    ]

    return safe_load_json("waterlogging_zones.json", fallback)


def render_kpi_card(icon, label, value, note):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# MAPS
# =========================================================

MAP_STYLE = "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json"


def build_point_records():
    hospitals = load_json("mock_hospitals.json")
    ambulances = load_json("mock_ambulances.json")
    complaints = load_json("mock_complaints.json")
    traffic_zones = get_traffic_zones()
    waterlogging_zones = get_waterlogging_zones()

    records = []

    for h in hospitals:
        records.append({
            "name": h["name"],
            "category": "Hospital",
            "lat": h["lat"],
            "lon": h["lon"],
            "details": f"Emergency beds: {h['emergency_beds']} | ICU beds: {h['icu_beds']} | Load: {h['load_percent']}%",
            "priority": "Medical",
            "color": [34, 197, 94, 220],
            "radius": 270
        })

    for a in ambulances:
        color = [239, 68, 68, 230] if a["status"] == "Available" else [148, 163, 184, 210]
        records.append({
            "name": a["id"],
            "category": "Ambulance",
            "lat": a["lat"],
            "lon": a["lon"],
            "details": f"Driver: {a['driver']} | ETA: {a['eta_min']} min | Status: {a['status']}",
            "priority": "Emergency",
            "color": color,
            "radius": 240
        })

    for c in complaints:
        lat, lon = get_area_coordinates(c["area"])
        color = [245, 158, 11, 220] if c["priority"] == "Medium" else [249, 115, 22, 230]
        records.append({
            "name": c["id"],
            "category": f"Complaint: {c['category']}",
            "lat": lat,
            "lon": lon,
            "details": f"Area: {c['area']} | Department: {c['department']} | Status: {c['status']}",
            "priority": c["priority"],
            "color": color,
            "radius": 235
        })

    for t in traffic_zones:
        records.append({
            "name": t["zone"],
            "category": "Traffic Hotspot",
            "lat": t["lat"],
            "lon": t["lon"],
            "details": f"Traffic: {t['traffic_level']} | Delay: {t['avg_delay_min']} min | Risk: {t['risk']}",
            "priority": t["traffic_level"],
            "color": [168, 85, 247, 230],
            "radius": 340
        })

    for w in waterlogging_zones:
        color = [14, 165, 233, 220] if w["risk_level"] == "Medium" else [37, 99, 235, 230]
        records.append({
            "name": w["zone"],
            "category": "Waterlogging Risk",
            "lat": w["lat"],
            "lon": w["lon"],
            "details": f"Risk: {w['risk_level']} | Reason: {w['reason']}",
            "priority": w["risk_level"],
            "color": color,
            "radius": 330
        })

    return records


def create_smartcity_deck_map(selected_records=None, zoom=11.85, pitch=25):
    records = selected_records if selected_records else build_point_records()
    df = pd.DataFrame(records)

    if df.empty:
        df = pd.DataFrame([{
            "name": "Bengaluru",
            "category": "City Center",
            "lat": 12.9716,
            "lon": 77.5946,
            "details": "Default city center",
            "priority": "Info",
            "color": [59, 130, 246, 230],
            "radius": 300,
            "marker_text": "📍",
            "elevation": 1000,
        }])

    if "marker_text" not in df.columns:
        df["marker_text"] = ""
    if "elevation" not in df.columns:
        df["elevation"] = 0

    ambulance_df = df[df["category"] == "Ambulance"]
    elevated_df = df[(df["elevation"] > 0) & (df["category"] != "Ambulance")]

    point_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position="[lon, lat]",
        get_fill_color="color",
        get_radius="radius",
        pickable=True,
        opacity=0.9,
        stroked=True,
        filled=True,
        radius_scale=1,
        radius_min_pixels=13,
        radius_max_pixels=46,
        line_width_min_pixels=2,
        get_line_color=[255, 255, 255, 230]
    )

    layers = [point_layer]

    if not ambulance_df.empty:
        ambulance_highlight_layer = pdk.Layer(
            "ScatterplotLayer",
            data=ambulance_df,
            get_position="[lon, lat]",
            get_fill_color=[239, 68, 68, 235],
            get_radius=420,
            pickable=True,
            opacity=0.35,
            stroked=True,
            filled=True,
            radius_min_pixels=20,
            radius_max_pixels=58,
            line_width_min_pixels=3,
            get_line_color=[255, 255, 255, 255]
        )
        layers.insert(0, ambulance_highlight_layer)

    if not elevated_df.empty:
        column_layer = pdk.Layer(
            "ColumnLayer",
            data=elevated_df,
            get_position="[lon, lat]",
            get_fill_color="color",
            get_elevation="elevation",
            elevation_scale=1,
            radius=60,
            pickable=True,
            extruded=True,
            opacity=0.75,
        )
        layers.insert(0, column_layer)

    marker_df = df[df["marker_text"] != ""]
    if not marker_df.empty:
        marker_layer = pdk.Layer(
            "TextLayer",
            data=marker_df,
            get_position="[lon, lat]",
            get_text="marker_text",
            get_size=20,
            size_scale=1,
            size_min_pixels=16,
            size_max_pixels=24,
            get_color=[255, 255, 255, 255],
            get_alignment_baseline="'center'",
            pickable=False,
        )
        layers.append(marker_layer)

    view_state = pdk.ViewState(
        latitude=float(df["lat"].mean()),
        longitude=float(df["lon"].mean()),
        zoom=zoom,
        pitch=pitch,
        bearing=0
    )

    tooltip = {
        "html": """
        <div style="font-family: Inter, Arial; padding: 8px; min-width: 230px;">
            <b style="font-size: 14px;">{name}</b><br/>
            <span>{category}</span><br/>
            <hr style="border: 0.5px solid #334155;">
            <span>{details}</span><br/>
            <b>Priority:</b> {priority}
        </div>
        """,
        "style": {
            "backgroundColor": "#0f172a",
            "color": "white",
            "borderRadius": "12px",
            "padding": "10px"
        }
    }

    return pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style=MAP_STYLE
    )


def create_route_deck_map(route_points, extra_records):
    route_df = pd.DataFrame(route_points)
    records_df = pd.DataFrame(extra_records)

    line_layer = pdk.Layer(
        "PathLayer",
        data=[{"path": [[p["lon"], p["lat"]] for p in route_points]}],
        get_path="path",
        get_width=8,
        get_color=[37, 99, 235, 230],
        width_min_pixels=5,
        pickable=True
    )

    point_layer = pdk.Layer(
        "ScatterplotLayer",
        data=records_df,
        get_position="[lon, lat]",
        get_fill_color="color",
        get_radius="radius",
        pickable=True,
        opacity=0.9,
        stroked=True,
        filled=True,
        radius_min_pixels=13,
        radius_max_pixels=46,
        get_line_color=[255, 255, 255, 230]
    )

    view_state = pdk.ViewState(
        latitude=float(route_df["lat"].mean()),
        longitude=float(route_df["lon"].mean()),
        zoom=12,
        pitch=25
    )

    return pdk.Deck(
        layers=[line_layer, point_layer],
        initial_view_state=view_state,
        tooltip={
            "html": "<b>{name}</b><br/>{category}<br/>{details}",
            "style": {
                "backgroundColor": "#0f172a",
                "color": "white",
                "borderRadius": "12px",
                "padding": "10px"
            }
        },
        map_style=MAP_STYLE
    )


# =========================================================
# ROUTER + AGENTS
# =========================================================

def detect_intent(query):
    query = query.lower()

    emergency_words = ["ambulance", "emergency", "accident", "heart attack", "urgent", "medical help", "injured"]
    hospital_words = ["hospital", "icu", "bed", "doctor", "clinic"]
    traffic_words = ["traffic", "route", "directions", "go to", "from", " to ", "majestic", "silk board", "travel"]
    complaint_words = ["pothole", "garbage", "water supply", "power cut", "street light", "drainage", "complaint", "waste"]
    weather_words = ["rain", "weather", "flood", "waterlogging", "water logged"]

    if any(word in query for word in emergency_words):
        return "Emergency Response Agent"

    if any(word in query for word in complaint_words):
        return "Civic Complaint Agent"

    if any(word in query for word in weather_words):
        return "Traffic & Flood Risk Agent"

    if any(word in query for word in hospital_words):
        return "Hospital Capacity Agent"

    if any(word in query for word in traffic_words):
        return "Traffic Optimization Agent"

    return "General Civic Assistant"


def detect_area(query):
    query_lower = query.lower()
    areas = [
        "jayanagar", "jp nagar", "banashankari", "btm layout", "silk board",
        "kr market", "majestic", "koramangala", "indiranagar", "electronic city"
    ]

    for area in areas:
        if area in query_lower:
            return area.title().replace("Jp", "JP").replace("Kr", "KR").replace("Btm", "BTM")

    if "near me" in query_lower or "nearby" in query_lower:
        return st.session_state.get("current_location_area", "Bengaluru")

    custom_location = extract_custom_location_label(query)
    if custom_location:
        return custom_location

    return "Bengaluru"


def emergency_agent(query):
    area = detect_area(query)
    area_lat, area_lon = get_area_coordinates(area)

    ambulances = load_json("mock_ambulances.json")
    hospitals = build_local_hospital_pool(area)
    traffic_zones = get_traffic_zones()

    available_ambulances = [a for a in ambulances if a["status"] == "Available"]
    selected_ambulance = min(available_ambulances, key=lambda x: x["eta_min"])

    selected_hospital = max(
        hospitals,
        key=lambda h: (
            (h["emergency_beds"] + h["icu_beds"])
            - (h["load_percent"] / 10)
            - ((abs(h["lat"] - area_lat) + abs(h["lon"] - area_lon)) * 100)
        )
    )

    nearest_traffic = min(
        traffic_zones,
        key=lambda t: abs(t["lat"] - area_lat) + abs(t["lon"] - area_lon)
    )

    answer = f"""
## 🚑 Emergency Dispatch Recommendation

SmartCity detected an emergency request in **{area}** and activated the Emergency Response Agent.

### Recommended Action

| Decision | Recommendation |
|---|---|
| Dispatch Ambulance | {selected_ambulance["id"]} |
| Driver | {selected_ambulance["driver"]} |
| Estimated Arrival | {selected_ambulance["eta_min"]} minutes |
| Recommended Hospital | {selected_hospital["name"]} |
| Emergency Beds | {selected_hospital["emergency_beds"]} |
| ICU Beds | {selected_hospital["icu_beds"]} |
| Priority Level | Critical |

### Traffic Context

Nearest traffic risk zone: **{nearest_traffic["zone"]}**  
Current delay estimate: **{nearest_traffic["avg_delay_min"]} minutes**  
Risk: **{nearest_traffic["risk"]}**

### Why this recommendation?

The ambulance was selected because it is available and has the lowest ETA.  
The hospital was selected because it has the best combination of emergency beds, ICU beds and manageable load.  
Traffic context is included so emergency movement can avoid high-risk road segments.
"""

    records = [
        {
            "name": "Emergency Location",
            "category": "Patient Location",
            "lat": area_lat,
            "lon": area_lon,
            "details": f"Detected emergency area: {area}",
            "priority": "Critical",
            "color": [220, 38, 38, 240],
            "radius": 330
        },
        {
            "name": selected_ambulance["id"],
            "category": "Assigned Ambulance",
            "lat": selected_ambulance["lat"],
            "lon": selected_ambulance["lon"],
            "details": f"ETA: {selected_ambulance['eta_min']} min | Driver: {selected_ambulance['driver']}",
            "priority": "Emergency",
            "color": [239, 68, 68, 230],
            "radius": 280
        },
        {
            "name": selected_hospital["name"],
            "category": "Recommended Hospital",
            "lat": selected_hospital["lat"],
            "lon": selected_hospital["lon"],
            "details": f"Emergency beds: {selected_hospital['emergency_beds']} | ICU: {selected_hospital['icu_beds']}",
            "priority": "Medical",
            "color": [34, 197, 94, 230],
            "radius": 300
        },
        {
            "name": nearest_traffic["zone"],
            "category": "Traffic Risk",
            "lat": nearest_traffic["lat"],
            "lon": nearest_traffic["lon"],
            "details": f"Delay: {nearest_traffic['avg_delay_min']} min | {nearest_traffic['risk']}",
            "priority": nearest_traffic["traffic_level"],
            "color": [168, 85, 247, 230],
            "radius": 330
        }
    ]

    return answer, create_smartcity_deck_map(records, zoom=12.25, pitch=25)


def hospital_agent(query):
    area = detect_area(query)
    area_lat, area_lon = get_area_coordinates(area)
    hospitals = build_local_hospital_pool(area)

    sorted_hospitals = sorted(
        hospitals,
        key=lambda h: (
            (h["emergency_beds"] + h["icu_beds"])
            - (h["load_percent"] / 10)
            - ((abs(h["lat"] - area_lat) + abs(h["lon"] - area_lon)) * 100)
        ),
        reverse=True
    )

    best = sorted_hospitals[0]

    answer = f"""
## 🏥 Hospital Capacity Recommendation

SmartCity analyzed hospital capacity and selected the best emergency-ready option.
SmartCity analyzed hospital capacity around **{area}** and selected the best emergency-ready options nearby.

| Detail | Information |
|---|---|
| Best Hospital | {best["name"]} |
| Area | {best["area"]} |
| Emergency Beds | {best["emergency_beds"]} |
| ICU Beds | {best["icu_beds"]} |
| Current Load | {best["load_percent"]}% |

### Why this recommendation?

This hospital has the strongest combination of emergency beds, ICU beds and lower current load.
"""

    records = []

    for h in sorted_hospitals:
        records.append({
            "name": h["name"],
            "category": "Hospital",
            "lat": h["lat"],
            "lon": h["lon"],
            "details": f"Emergency beds: {h['emergency_beds']} | ICU beds: {h['icu_beds']} | Load: {h['load_percent']}%",
            "priority": "Recommended" if h["name"] == best["name"] else "Available",
            "color": [34, 197, 94, 235] if h["name"] == best["name"] else [74, 222, 128, 210],
            "radius": 330 if h["name"] == best["name"] else 250
        })

    return answer, create_smartcity_deck_map(records, zoom=12.2, pitch=25)


def traffic_agent(query):
    start_area, end_area = detect_route_endpoints(query)
    start_lat, start_lon = get_area_coordinates(start_area)
    end_lat, end_lon = get_area_coordinates(end_area)
    traffic_zones = build_local_traffic_pool(start_area)
    water_zones = build_local_waterlogging_pool(start_area)

    worst_traffic = max(traffic_zones, key=lambda t: t["avg_delay_min"])
    high_water = max(water_zones, key=lambda w: 3 if w["risk_level"] == "High" else 2)
    estimated_time = max(18, 12 + worst_traffic["avg_delay_min"])

    answer = f"""
## 🚦 Traffic & Route Optimization

SmartCity analyzed the route request from **{start_area}** to **{end_area}** and checked traffic plus rain and flood risk.

### Recommended Route

| Detail | Recommendation |
|---|---|
| Suggested Route | {start_area} -> safer connector roads -> {end_area} |
| Estimated Time | {estimated_time} minutes |
| Traffic Level | Medium |
| Safer During Rain | Yes |
| Avoid | {worst_traffic["zone"]} |

### Risk Zones Detected

- **Traffic Hotspot:** {worst_traffic["zone"]} — {worst_traffic["avg_delay_min"]} min delay  
- **Waterlogging Risk:** {high_water["zone"]} — {high_water["risk_level"]} risk  

### Why this recommendation?

This route balances travel time, congestion and waterlogging risk around the requested location.
"""

    mid_lat = round((start_lat + end_lat) / 2, 6)
    mid_lon = round((start_lon + end_lon) / 2, 6)
    route_points = [
        {"lat": start_lat, "lon": start_lon},
        {"lat": round((start_lat + mid_lat) / 2, 6), "lon": round((start_lon + mid_lon) / 2 + 0.01, 6)},
        {"lat": mid_lat, "lon": mid_lon},
        {"lat": round((mid_lat + end_lat) / 2, 6), "lon": round((mid_lon + end_lon) / 2 - 0.008, 6)},
        {"lat": end_lat, "lon": end_lon}
    ]

    records = [
        {
            "name": f"Start: {start_area}",
            "category": "Route Start",
            "lat": start_lat,
            "lon": start_lon,
            "details": "Starting point",
            "priority": "Start",
            "color": [34, 197, 94, 230],
            "radius": 280
        },
        {
            "name": f"Destination: {end_area}",
            "category": "Destination",
            "lat": end_lat,
            "lon": end_lon,
            "details": "Destination point",
            "priority": "End",
            "color": [239, 68, 68, 230],
            "radius": 280
        },
        {
            "name": worst_traffic["zone"],
            "category": "Avoid Traffic Hotspot",
            "lat": worst_traffic["lat"],
            "lon": worst_traffic["lon"],
            "details": f"Delay: {worst_traffic['avg_delay_min']} min | {worst_traffic['risk']}",
            "priority": worst_traffic["traffic_level"],
            "color": [168, 85, 247, 230],
            "radius": 350
        },
        {
            "name": high_water["zone"],
            "category": "Waterlogging Risk",
            "lat": high_water["lat"],
            "lon": high_water["lon"],
            "details": f"Risk: {high_water['risk_level']} | {high_water['reason']}",
            "priority": high_water["risk_level"],
            "color": [14, 165, 233, 230],
            "radius": 350
        }
    ]

    return answer, create_route_deck_map(route_points, records)


def complaint_agent(query):
    area = detect_area(query)
    complaint_id = f"CMP-2026-{random.randint(1000, 9999)}"

    query_lower = query.lower()

    if "pothole" in query_lower:
        category = "Pothole"
        department = "BBMP Roads Department"
        priority = "High"
    elif "garbage" in query_lower or "waste" in query_lower:
        category = "Garbage Collection"
        department = "BBMP Solid Waste Management"
        priority = "Medium"
    elif "street light" in query_lower:
        category = "Street Light"
        department = "BESCOM / BBMP"
        priority = "Medium"
    elif "water" in query_lower:
        category = "Water Supply"
        department = "BWSSB"
        priority = "High"
    elif "power" in query_lower:
        category = "Power Cut"
        department = "BESCOM"
        priority = "High"
    else:
        category = "General Civic Issue"
        department = "City Civic Department"
        priority = "Medium"

    similar = build_local_complaint_pool(area, category, department, priority)

    answer = f"""
## 📝 Civic Complaint Registered

SmartCity converted the citizen message into a structured complaint for authority action around **{area}**.

| Detail | Information |
|---|---|
| Complaint ID | {complaint_id} |
| Category | {category} |
| Area | {area} |
| Priority | {priority} |
| Assigned Department | {department} |
| Status | Registered |

### Similar Complaints Nearby

"""

    for complaint in similar:
        answer += f"- **{complaint['id']}** — {complaint['category']} in {complaint['area']} — {complaint['status']}\n"

    answer += """

### Why this action?

SmartCity categorized the issue, assigned the correct department and checked similar complaints to support faster grouped resolution.
"""

    lat, lon = get_area_coordinates(area)

    records = [
        {
            "name": complaint_id,
            "category": f"New Complaint: {category}",
            "lat": lat,
            "lon": lon,
            "details": f"Area: {area} | Department: {department}",
            "priority": priority,
            "color": [249, 115, 22, 240],
            "radius": 350
        }
    ]

    for c in similar[:3]:
        c_lat = c.get("lat", get_area_coordinates(c["area"])[0])
        c_lon = c.get("lon", get_area_coordinates(c["area"])[1])

        records.append({
            "name": c["id"],
            "category": f"Existing Complaint: {c['category']}",
            "lat": c_lat,
            "lon": c_lon,
            "details": f"Area: {c['area']} | Status: {c['status']} | Department: {c['department']}",
            "priority": c["priority"],
            "color": [245, 158, 11, 220],
            "radius": 260
        })

    return answer, create_smartcity_deck_map(records, zoom=12.2, pitch=25)


def weather_agent(query):
    area = detect_area(query)
    lat, lon = get_area_coordinates(area)
    water_zones = build_local_waterlogging_pool(area)
    traffic_zones = build_local_traffic_pool(area)

    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,precipitation,rain,weather_code"
        }

        response = requests.get(url, params=params, timeout=10)
        weather = response.json().get("current", {})

        temp = weather.get("temperature_2m", "N/A")
        rain = weather.get("rain", 0)
        precipitation = weather.get("precipitation", 0)

        risk = "Low"

        if isinstance(rain, (int, float)) and rain > 1:
            risk = "High"
        elif isinstance(precipitation, (int, float)) and precipitation > 0:
            risk = "Medium"

    except Exception:
        temp = "N/A"
        rain = "N/A"
        precipitation = "N/A"
        risk = "Medium"

    high_water = max(water_zones, key=lambda w: 3 if w["risk_level"] == "High" else 2)

    answer = f"""
## 🌧️ Weather, Rain & Flood Risk Analysis

SmartCity checked weather and waterlogging risk for **{area}**.

| Detail | Information |
|---|---|
| Temperature | {temp}°C |
| Rain | {rain} mm |
| Precipitation | {precipitation} mm |
| Estimated Waterlogging Risk | {risk} |

### Priority Warning Zone

**{high_water["zone"]}**  
Risk Level: **{high_water["risk_level"]}**  
Reason: {high_water["reason"]}

### Suggested Action

Avoid underpasses, low-lying roads and traffic-heavy junctions if rain increases.

### Why this recommendation?

SmartCity combines weather data, known waterlogging zones and traffic hotspots to estimate safer movement decisions.
"""

    records = [
        {
            "name": area,
            "category": "Weather Check Area",
            "lat": lat,
            "lon": lon,
            "details": f"Rain: {rain} mm | Risk: {risk}",
            "priority": risk,
            "color": [59, 130, 246, 230],
            "radius": 330
        }
    ]

    for w in water_zones:
        records.append({
            "name": w["zone"],
            "category": "Waterlogging Risk",
            "lat": w["lat"],
            "lon": w["lon"],
            "details": f"Risk: {w['risk_level']} | {w['reason']}",
            "priority": w["risk_level"],
            "color": [14, 165, 233, 230],
            "radius": 330
        })

    for t in traffic_zones:
        records.append({
            "name": t["zone"],
            "category": "Traffic Hotspot",
            "lat": t["lat"],
            "lon": t["lon"],
            "details": f"Delay: {t['avg_delay_min']} min | {t['risk']}",
            "priority": t["traffic_level"],
            "color": [168, 85, 247, 230],
            "radius": 310
        })

    return answer, create_smartcity_deck_map(records, zoom=12.0, pitch=25)


def general_agent(query):
    answer = f"""
## 🤖 SmartCity Civic Assistant

I understood your query:

**"{query}"**

SmartCity is designed for civic decision making. It can help with:

- Ambulance dispatch and emergency hospital recommendation
- Hospital bed availability analysis
- Traffic and rain-safe route advice
- Waterlogging and flood risk guidance
- Civic complaint generation and tracking
- Authority dashboard insights

Try asking:

**Ambulance near Whitefield**  
**Best route from Cubbon Park to Majestic during rain**  
**Pothole near Yelahanka**  
**Hospitals in Hebbal**  
**Waterlogging near MG Road**
"""

    return answer, create_smartcity_deck_map()


def run_smartcity_agent(query):
    intent = detect_intent(query)

    if intent == "Emergency Response Agent":
        return intent, *emergency_agent(query)

    if intent == "Hospital Capacity Agent":
        return intent, *hospital_agent(query)

    if intent == "Traffic Optimization Agent":
        return intent, *traffic_agent(query)

    if intent == "Civic Complaint Agent":
        return intent, *complaint_agent(query)

    if intent == "Traffic & Flood Risk Agent":
        return intent, *weather_agent(query)

    return intent, *general_agent(query)


def render_context_analytics(intent, hospitals, traffic_zones, complaints, waterlogging_zones):
    st.markdown('<div class="section-heading">📈 Context Analytics</div>', unsafe_allow_html=True)

    if intent in ["Emergency Response Agent", "Hospital Capacity Agent"]:
        col1, col2 = st.columns(2, gap="large")

        with col1:
            with st.container(border=True):
                st.markdown("### Hospital Capacity")
                capacity_df = pd.DataFrame(hospitals)
                capacity_df["total_critical_beds"] = capacity_df["emergency_beds"] + capacity_df["icu_beds"]

                st.bar_chart(
                    capacity_df,
                    x="name",
                    y="total_critical_beds",
                    use_container_width=True
                )

        with col2:
            with st.container(border=True):
                st.markdown("### Hospital Load")
                load_df = pd.DataFrame(hospitals)

                st.bar_chart(
                    load_df,
                    x="name",
                    y="load_percent",
                    use_container_width=True
                )

    elif intent in ["Traffic Optimization Agent", "Traffic & Flood Risk Agent"]:
        col1, col2 = st.columns(2, gap="large")

        with col1:
            with st.container(border=True):
                st.markdown("### Traffic Delay by Zone")
                traffic_df = pd.DataFrame(traffic_zones)

                st.bar_chart(
                    traffic_df,
                    x="zone",
                    y="avg_delay_min",
                    use_container_width=True
                )

        with col2:
            with st.container(border=True):
                st.markdown("### Waterlogging Risk Zones")
                water_df = pd.DataFrame(waterlogging_zones)
                st.dataframe(water_df, use_container_width=True, hide_index=True)

    elif intent == "Civic Complaint Agent":
        col1, col2 = st.columns(2, gap="large")

        with col1:
            with st.container(border=True):
                st.markdown("### Active Civic Complaints")
                complaint_df = pd.DataFrame(complaints)
                st.dataframe(complaint_df, use_container_width=True, hide_index=True)

        with col2:
            with st.container(border=True):
                st.markdown("### Complaint Priority Count")
                complaint_df = pd.DataFrame(complaints)
                priority_count = complaint_df["priority"].value_counts().reset_index()
                priority_count.columns = ["priority", "count"]
                st.bar_chart(priority_count, x="priority", y="count", use_container_width=True)

    else:
        with st.container(border=True):
            st.markdown("### City Operations Snapshot")
            st.write("Ask an emergency, hospital, traffic, weather, or complaint query to load specific analytics.")


# =========================================================
# SESSION STATE
# =========================================================

if "entered_dashboard" not in st.session_state:
    st.session_state.entered_dashboard = False

if "last_query" not in st.session_state:
    st.session_state.last_query = ""

if "last_intent" not in st.session_state:
    st.session_state.last_intent = None

if "last_answer" not in st.session_state:
    st.session_state.last_answer = None

if "last_deck" not in st.session_state:
    st.session_state.last_deck = None


# =========================================================
# PAGE ROUTER
# =========================================================

if not st.session_state.entered_dashboard:
    render_landing_page(
        load_json,
        get_traffic_zones,
        get_waterlogging_zones,
        render_kpi_card
    )
else:
    render_dashboard_page(
        load_json,
        get_traffic_zones,
        get_waterlogging_zones,
        run_smartcity_agent,
        create_smartcity_deck_map,
        render_context_analytics
    )
