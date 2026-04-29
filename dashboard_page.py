import os
import random
import re
from datetime import datetime

import requests
import streamlit as st


AREA_COORDS = {
    "Jayanagar": (12.9299, 77.5827),
    "JP Nagar": (12.9077, 77.5850),
    "Banashankari": (12.9255, 77.5468),
    "BTM Layout": (12.9166, 77.6101),
    "Silk Board": (12.9177, 77.6238),
    "KR Market": (12.9611, 77.5742),
    "Majestic": (12.9767, 77.5713),
    "Koramangala": (12.9352, 77.6245),
    "Indiranagar": (12.9784, 77.6408),
    "Electronic City": (12.8452, 77.6602),
    "Bengaluru": (12.9716, 77.5946),
}

def _load_city_snapshot(load_json, get_traffic_zones, get_waterlogging_zones):
    hospitals = load_json("mock_hospitals.json")
    ambulances = load_json("mock_ambulances.json")
    complaints = load_json("mock_complaints.json")
    traffic_zones = get_traffic_zones()
    waterlogging_zones = get_waterlogging_zones()

    return {
        "hospitals": hospitals,
        "ambulances": ambulances,
        "complaints": complaints,
        "traffic_zones": traffic_zones,
        "waterlogging_zones": waterlogging_zones,
    }


def _run_query(query, run_smartcity_agent):
    if query and query.strip():
        with st.spinner("SmartCity AI is analyzing live civic signals..."):
            intent, answer, deck = run_smartcity_agent(query)

        st.session_state.last_query = query
        st.session_state.last_intent = intent
        st.session_state.last_answer = answer
        st.session_state.last_deck = deck


def _detect_area(query):
    query_lower = query.lower()
    for area in AREA_COORDS:
        if area.lower() in query_lower:
            return area
    return _get_query_location(query)["area"]


def _nearest_area_name(lat, lon):
    candidates = {name: coords for name, coords in AREA_COORDS.items() if name != "Bengaluru"}
    return min(
        candidates,
        key=lambda area: _distance_score(lat, lon, candidates[area][0], candidates[area][1]),
    )


def _capture_exact_location():
    return


def _fetch_current_location():
    if st.session_state.get("exact_location"):
        return st.session_state.exact_location

    if st.session_state.get("current_location"):
        return st.session_state.current_location

    services = [
        ("https://ipapi.co/json/", lambda data: (data.get("latitude"), data.get("longitude"), data.get("city"))),
        ("https://ipinfo.io/json", lambda data: (
            float(data["loc"].split(",")[0]) if data.get("loc") else None,
            float(data["loc"].split(",")[1]) if data.get("loc") else None,
            data.get("city"),
        )),
    ]

    for url, parser in services:
        try:
            response = requests.get(url, timeout=4)
            if response.ok:
                data = response.json()
                lat, lon, city = parser(data)
                if lat is not None and lon is not None:
                    area = _nearest_area_name(lat, lon)
                    location = {
                        "label": city or "Your Location",
                        "lat": float(lat),
                        "lon": float(lon),
                        "area": area,
                        "source": "approximate_ip",
                    }
                    st.session_state.current_location = location
                    st.session_state.current_location_area = area
                    return location
        except Exception:
            continue

    fallback = {
        "label": "Approximate Bengaluru Location",
        "lat": AREA_COORDS["Bengaluru"][0],
        "lon": AREA_COORDS["Bengaluru"][1],
        "area": "Bengaluru",
        "source": "fallback_city",
    }
    st.session_state.current_location = fallback
    st.session_state.current_location_area = "Bengaluru"
    return fallback


def _extract_custom_location_label(query):
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

    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if openai_api_key:
        try:
            response = requests.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
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


def _coords_for_custom_location(label):
    base_lat, base_lon = AREA_COORDS["Bengaluru"]
    seed = abs(hash(label))
    lat_offset = (((seed % 900) / 10000) - 0.045)
    lon_offset = ((((seed // 900) % 900) / 10000) - 0.045)
    return round(base_lat + lat_offset, 6), round(base_lon + lon_offset, 6)


def _geocode_location_label(label):
    cache = st.session_state.setdefault("geocode_cache", {})
    cache_key = label.strip().lower()
    if cache_key in cache:
        return cache[cache_key]

    google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if google_maps_api_key:
        queries = [
            f"{label}, Bengaluru, Karnataka, India",
            f"{label}, Bangalore, Karnataka, India",
            f"{label}, India",
        ]
        for search_query in queries:
            try:
                response = requests.get(
                    "https://maps.googleapis.com/maps/api/geocode/json",
                    params={"address": search_query, "key": google_maps_api_key},
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
                    "area": label.title(),
                    "source": "geocoded_query",
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

            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            geocoded = {
                "label": label.title(),
                "lat": lat,
                "lon": lon,
                "area": label.title(),
                "source": "geocoded_query",
            }
            cache[cache_key] = geocoded
            return geocoded
        except Exception:
            continue

    lat, lon = _coords_for_custom_location(label)
    fallback = {
        "label": label.title(),
        "lat": lat,
        "lon": lon,
        "area": label.title(),
        "source": "custom_query",
    }
    cache[cache_key] = fallback
    return fallback


def _get_query_location(query):
    query_lower = (query or "").lower()
    for area, coords in AREA_COORDS.items():
        if area.lower() in query_lower:
            return {
                "label": area,
                "lat": coords[0],
                "lon": coords[1],
                "area": area,
            }

    custom_label = _extract_custom_location_label(query)
    if custom_label:
        return _geocode_location_label(custom_label)

    current = _fetch_current_location()
    if "near me" in query_lower or "nearby" in query_lower:
        return current

    return current


def _location_status_text(query):
    location = _get_query_location(query)
    source = location.get("source", "unknown")
    if source == "exact":
        accuracy = location.get("accuracy")
        return f"Using exact browser location{f' (accuracy ~{int(accuracy)} m)' if accuracy else ''}."
    if _query_needs_exact_location(query):
        return "Exact location permission not granted yet. Map is using an approximate city/IP location."
    return f"Using detected location: {location['label']}."


def _query_needs_exact_location(query):
    query_lower = (query or "").lower()
    exact_location_phrases = [
        "near me",
        "nearby",
        "closest",
        "my location",
        "around me",
    ]
    return any(phrase in query_lower for phrase in exact_location_phrases)


def _phone_for(label, seed):
    return f"+91 80 {seed:04d} {abs(hash(label)) % 10000:04d}"


def _distance_score(origin_lat, origin_lon, target_lat, target_lon):
    return abs(origin_lat - target_lat) + abs(origin_lon - target_lon)


def _build_nearby_ambulance_pool(snapshot, query):
    location = _get_query_location(query)
    area = location["area"]
    area_lat, area_lon = location["lat"], location["lon"]
    base_units = list(snapshot["ambulances"])

    nearby_units = [
        item for item in base_units
        if _distance_score(area_lat, area_lon, item["lat"], item["lon"]) <= 0.08
    ]
    if len(nearby_units) >= 3:
        return base_units

    driver_names = [
        "Ravi Kumar",
        "Suresh R",
        "Manjunath",
        "Asha N",
        "Imran S",
        "Deepa K",
    ]
    offsets = [
        (0.0042, 0.0038),
        (-0.0036, 0.0046),
        (0.0051, -0.0032),
        (-0.0044, -0.0040),
        (0.0028, 0.0053),
        (-0.0050, 0.0024),
    ]
    target_count = 5
    generated = []

    for index in range(target_count):
        offset_lat, offset_lon = offsets[index]
        generated.append({
            "id": f"AMB-{index + 1:02d}",
            "driver": driver_names[index],
            "area": area,
            "lat": round(area_lat + offset_lat, 6),
            "lon": round(area_lon + offset_lon, 6),
            "status": "Available" if index < 4 else "Busy",
            "eta_min": 4 + (index * 2),
        })

    return generated


def _build_nearby_hospital_pool(snapshot, query):
    location = _get_query_location(query)
    area = location["area"]
    area_lat, area_lon = location["lat"], location["lon"]
    base_hospitals = list(snapshot["hospitals"])
    local_hospitals = [
        item for item in base_hospitals
        if item.get("area") == area or _distance_score(area_lat, area_lon, item["lat"], item["lon"]) <= 0.10
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
    generated = []
    seen_names = {item["name"] for item in local_hospitals}

    for index, name in enumerate(names):
        if name in seen_names:
            continue
        offset_lat, offset_lon = offsets[index]
        generated.append({
            "name": name,
            "area": area,
            "lat": round(area_lat + offset_lat, 6),
            "lon": round(area_lon + offset_lon, 6),
            "emergency_beds": beds[index],
            "icu_beds": icu_beds[index],
            "load_percent": loads[index],
        })

    merged_hospitals = local_hospitals + generated
    if len(merged_hospitals) < 4:
        return sorted(
            base_hospitals,
            key=lambda item: _distance_score(area_lat, area_lon, item["lat"], item["lon"]),
        )
    return merged_hospitals


def _build_location_record(area):
    location = _get_query_location(area)
    lat, lon = location["lat"], location["lon"]
    return {
        "name": location["label"],
        "category": "Selected Location",
        "lat": lat,
        "lon": lon,
        "details": f"Focused dashboard view for {location['label']}",
        "priority": "Focus",
        "color": [59, 130, 246, 240],
        "radius": 320,
        "marker_text": "YOU",
        "elevation": 1200,
    }


def _build_context_map(snapshot, intent, query, create_smartcity_deck_map):
    location = _get_query_location(query)
    area = location["area"]
    area_lat, area_lon = location["lat"], location["lon"]
    nearby_cutoff = 0.07
    hospital_cutoff = 0.12
    records = [_build_location_record(query)]
    ambulances = _build_nearby_ambulance_pool(snapshot, query) if intent == "Emergency Response Agent" else snapshot["ambulances"]
    hospitals = _build_nearby_hospital_pool(snapshot, query) if intent in ["Emergency Response Agent", "Hospital Capacity Agent"] else snapshot["hospitals"]
    traffic_zones = _build_local_traffic_pool(snapshot, query) if intent in ["Traffic Optimization Agent", "Traffic & Flood Risk Agent"] else snapshot["traffic_zones"]
    waterlogging_zones = _build_local_waterlogging_pool(snapshot, query) if intent == "Traffic & Flood Risk Agent" else snapshot["waterlogging_zones"]
    show_hospitals = intent == "Hospital Capacity Agent"
    show_ambulances = intent == "Emergency Response Agent"
    show_traffic = intent in ["Traffic Optimization Agent", "Traffic & Flood Risk Agent"]
    show_waterlogging = intent == "Traffic & Flood Risk Agent"
    show_complaints = intent == "Civic Complaint Agent"

    def is_near(lat, lon):
        return _distance_score(area_lat, area_lon, lat, lon) <= nearby_cutoff

    def is_hospital_near(lat, lon):
        return _distance_score(area_lat, area_lon, lat, lon) <= hospital_cutoff

    for hospital in hospitals:
        if show_hospitals and is_hospital_near(hospital["lat"], hospital["lon"]):
            records.append({
                "name": hospital["name"],
                "category": "Hospital",
                "lat": hospital["lat"],
                "lon": hospital["lon"],
                "details": f"Beds: {hospital['emergency_beds']} | ICU: {hospital['icu_beds']} | Load: {hospital['load_percent']}%",
                "priority": "Medical",
                "color": [34, 197, 94, 225],
                "radius": 270,
                "marker_text": "HOSP",
                "elevation": 850,
            })

    for ambulance in ambulances:
        if show_ambulances and is_near(ambulance["lat"], ambulance["lon"]):
            color = [239, 68, 68, 235] if ambulance["status"] == "Available" else [148, 163, 184, 215]
            records.append({
                "name": ambulance["id"],
                "category": "Ambulance",
                "lat": ambulance["lat"],
                "lon": ambulance["lon"],
                "details": f"Driver: {ambulance['driver']} | ETA: {ambulance['eta_min']} min | Status: {ambulance['status']}",
                "priority": ambulance["status"],
                "color": color,
                "radius": 260,
                "marker_text": ambulance["id"],
                "elevation": 1600 if ambulance["status"] == "Available" else 900,
            })

    for traffic in traffic_zones:
        if show_traffic and is_near(traffic["lat"], traffic["lon"]):
            records.append({
                "name": traffic["zone"],
                "category": "Traffic Hotspot",
                "lat": traffic["lat"],
                "lon": traffic["lon"],
                "details": f"Delay: {traffic['avg_delay_min']} min | {traffic['risk']}",
                "priority": traffic["traffic_level"],
                "color": [168, 85, 247, 225],
                "radius": 300,
            })

    for zone in waterlogging_zones:
        if show_waterlogging and is_near(zone["lat"], zone["lon"]):
            records.append({
                "name": zone["zone"],
                "category": "Waterlogging Risk",
                "lat": zone["lat"],
                "lon": zone["lon"],
                "details": f"Risk: {zone['risk_level']} | {zone['reason']}",
                "priority": zone["risk_level"],
                "color": [14, 165, 233, 225],
                "radius": 300,
            })

    complaints = [item for item in snapshot["complaints"] if item["area"] == area]
    if show_complaints and not complaints:
        complaints = [
            {"id": "CMP-LOCAL-01", "category": "General Civic Issue", "area": area, "status": "Registered", "department": "City Civic Department", "priority": "Medium"},
            {"id": "CMP-LOCAL-02", "category": "Drainage", "area": area, "status": "Assigned", "department": "Drainage Cell", "priority": "High"},
        ]

    for complaint in complaints:
        complaint_area = complaint["area"]
        if show_complaints and complaint_area == area:
            complaint_lat, complaint_lon = location["lat"], location["lon"]
            records.append({
                "name": complaint["id"],
                "category": f"Complaint: {complaint['category']}",
                "lat": complaint_lat,
                "lon": complaint_lon,
                "details": f"Area: {complaint_area} | Status: {complaint['status']} | Department: {complaint['department']}",
                "priority": complaint["priority"],
                "color": [245, 158, 11, 225],
                "radius": 245,
            })

    return create_smartcity_deck_map(records, zoom=12.6, pitch=32)


def _build_emergency_payload(snapshot, query):
    location = _get_query_location(query)
    area = location["area"]
    area_lat, area_lon = location["lat"], location["lon"]
    hospitals = _build_nearby_hospital_pool(snapshot, query)
    ambulances = _build_nearby_ambulance_pool(snapshot, query)
    available_ambulances = [item for item in ambulances if item["status"] == "Available"]
    nearby_ambulances = sorted(
        ambulances,
        key=lambda item: _distance_score(area_lat, area_lon, item["lat"], item["lon"]),
    )[:6]
    nearby_hospitals = sorted(
        hospitals,
        key=lambda item: _distance_score(area_lat, area_lon, item["lat"], item["lon"]),
    )[:3]
    ambulance = min(
        available_ambulances,
        key=lambda item: item["eta_min"] + (_distance_score(area_lat, area_lon, item["lat"], item["lon"]) * 100),
    )
    hospital = min(
        hospitals,
        key=lambda item: _distance_score(area_lat, area_lon, item["lat"], item["lon"]) - (item["emergency_beds"] * 0.002),
    )
    traffic = min(
        snapshot["traffic_zones"],
        key=lambda item: _distance_score(area_lat, area_lon, item["lat"], item["lon"]),
    )

    return {
        "headline": f"Nearby ambulances for {location['label']}",
        "status": "Nearby ambulance drivers ready to contact",
        "metrics": [
            ("Nearest Unit", ambulance["id"], f"{ambulance['driver']} is closest to you"),
            ("ETA", f"{ambulance['eta_min']} min", f"Current movement from {ambulance['area']}"),
            ("Units Nearby", str(len(nearby_ambulances)), "Closest ambulance drivers in this area"),
            ("Updated", datetime.now().strftime("%I:%M %p"), "Demo live operations feed"),
        ],
        "cards": [
            {
                "title": "Nearby Ambulance Drivers",
                "rows": [
                    (
                        f"{item['id']} • {item['driver']}",
                        f"{_phone_for(item['id'], 4455)} • {item['eta_min']} min • {item['status']}",
                    )
                    for item in nearby_ambulances
                ],
            },
            {
                "title": "Best Unit To Contact",
                "rows": [
                    ("Unit", ambulance["id"]),
                    ("Driver", ambulance["driver"]),
                    ("Current Area", ambulance["area"]),
                    ("ETA", f"{ambulance['eta_min']} minutes"),
                    ("Contact", _phone_for(ambulance["id"], 4455)),
                    ("Status", "Moving toward caller"),
                ],
            },
            {
                "title": "Nearest Hospitals",
                "rows": [
                    (
                        item["name"],
                        f"{item['area']} • Beds {item['emergency_beds']} • ICU {item['icu_beds']}",
                    )
                    for item in nearby_hospitals
                ],
            },
        ],
        "feed": [
            f"{ambulance['id']} is the best nearby ambulance to contact for {location['label']}.",
            f"Estimated arrival to {location['label']} is {ambulance['eta_min']} minutes under current demo traffic conditions.",
            f"Nearest traffic concern is {traffic['zone']} with about {traffic['avg_delay_min']} minutes of delay.",
        ],
        "summary": [
            ("Location", location["label"]),
            ("Best Driver", ambulance["driver"]),
            ("Contact", _phone_for(ambulance["id"], 4455)),
            ("ETA", f"{ambulance['eta_min']} min"),
        ],
    }


def _build_hospital_payload(snapshot, query):
    location = _get_query_location(query)
    area = location["area"]
    area_lat, area_lon = location["lat"], location["lon"]
    hospitals_source = _build_nearby_hospital_pool(snapshot, query)
    hospitals = sorted(
        hospitals_source,
        key=lambda item: _distance_score(area_lat, area_lon, item["lat"], item["lon"]) + (item["load_percent"] / 100),
    )
    nearby_hospitals = [
        item for item in hospitals
        if _distance_score(area_lat, area_lon, item["lat"], item["lon"]) <= 0.12
    ] or hospitals
    best = hospitals[0]
    backup = hospitals[1] if len(hospitals) > 1 else hospitals[0]
    return {
        "headline": f"Nearby hospital capacity for {location['label']}",
        "status": "Capacity board refreshed",
        "metrics": [
            ("Best Match", best["name"].split()[0], "Closest with emergency support"),
            ("Emergency Beds", str(best["emergency_beds"]), "Current demo capacity"),
            ("ICU Beds", str(best["icu_beds"]), "Critical care availability"),
            ("Updated", datetime.now().strftime("%I:%M %p"), "Capacity refresh"),
        ],
        "cards": [
            {
                "title": "Primary Hospital",
                "rows": [
                    ("Hospital", best["name"]),
                    ("Area", best["area"]),
                    ("Emergency Beds", str(best["emergency_beds"])),
                    ("ICU Beds", str(best["icu_beds"])),
                    ("Load", f"{best['load_percent']}%"),
                    ("Contact", _phone_for(best["name"], 2211)),
                ],
            },
            {
                "title": "Nearby Hospitals",
                "rows": [
                    (
                        item["name"],
                        f"{item['area']} | Beds {item['emergency_beds']} | ICU {item['icu_beds']} | Load {item['load_percent']}%",
                    )
                    for item in nearby_hospitals
                ],
            },
        ],
        "feed": [
            "Hospitals are ranked using distance, bed capacity, and current load.",
            f"{len(nearby_hospitals)} nearby hospitals are shown for this query.",
        ],
    }


def _build_local_traffic_pool(snapshot, query):
    location = _get_query_location(query)
    area = location["area"]
    area_lat, area_lon = location["lat"], location["lon"]
    local_zones = [
        item for item in snapshot["traffic_zones"]
        if item.get("area") == area or _distance_score(area_lat, area_lon, item["lat"], item["lon"]) <= 0.10
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
    ]
    seen = {item["zone"] for item in local_zones}
    for zone in generated:
        if zone["zone"] not in seen:
            local_zones.append(zone)
    return local_zones


def _build_local_waterlogging_pool(snapshot, query):
    location = _get_query_location(query)
    area = location["area"]
    area_lat, area_lon = location["lat"], location["lon"]
    local_zones = [
        item for item in snapshot["waterlogging_zones"]
        if item.get("area") == area or _distance_score(area_lat, area_lon, item["lat"], item["lon"]) <= 0.10
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


def _build_traffic_payload(snapshot, query):
    location = _get_query_location(query)
    traffic_zones = _build_local_traffic_pool(snapshot, query)
    water_zones = _build_local_waterlogging_pool(snapshot, query)
    traffic = max(traffic_zones, key=lambda item: item["avg_delay_min"])
    water = max(water_zones, key=lambda item: 2 if item["risk_level"] == "High" else 1)
    return {
        "headline": f"Live route risk overview for {location['label']}",
        "status": "Traffic and rain-sensitive route reviewed",
        "metrics": [
            ("Congestion", traffic["traffic_level"], traffic["zone"]),
            ("Delay", f"{traffic['avg_delay_min']} min", "Slowest current hotspot"),
            ("Flood Risk", water["risk_level"], water["zone"]),
            ("Updated", datetime.now().strftime("%I:%M %p"), "Route snapshot"),
        ],
        "cards": [
            {
                "title": "Traffic Hotspot",
                "rows": [
                    ("Zone", traffic["zone"]),
                    ("Area", traffic["area"]),
                    ("Traffic Level", traffic["traffic_level"]),
                    ("Delay", f"{traffic['avg_delay_min']} minutes"),
                    ("Risk", traffic["risk"]),
                ],
            },
            {
                "title": "Rain Alert",
                "rows": [
                    ("Zone", water["zone"]),
                    ("Area", water["area"]),
                    ("Risk Level", water["risk_level"]),
                    ("Reason", water["reason"]),
                    ("Suggested Mode", "Use safer alternate route"),
                ],
            },
        ],
        "feed": [
            f"Traffic and flood risk are centered around {location['label']}.",
            f"Avoid {traffic['zone']} first if you are moving around {location['label']}.",
        ],
    }


def _build_complaint_payload(snapshot, query):
    area = _get_query_location(query)["area"]
    nearby = _build_local_complaint_pool(snapshot, query)
    top = nearby[0]
    return {
        "headline": f"Complaint operations for {area}",
        "status": "Ticket routing simulated",
        "metrics": [
            ("Area", area, "Detected service zone"),
            ("Similar Issues", str(len(nearby)), "Nearby complaint cluster"),
            ("Priority", top["priority"], "Auto-assigned based on issue type"),
            ("Updated", datetime.now().strftime("%I:%M %p"), "Workflow snapshot"),
        ],
        "cards": [
            {
                "title": "Assigned Workflow",
                "rows": [
                    ("Department", top["department"]),
                    ("Priority", top["priority"]),
                    ("Current Status", top["status"]),
                    ("Zone Office", _phone_for(area, 5510)),
                    ("Citizen Helpline", "+91 1912 000 000"),
                ],
            },
            {
                "title": "Nearby Similar Complaints",
                "rows": [(item["id"], f"{item['category']} - {item['status']}") for item in nearby[:3]],
            },
        ],
        "feed": [
            "The complaint layer shows the new issue together with nearby similar tickets.",
            "This helps explain why a department and priority were selected.",
        ],
    }


def _build_local_complaint_pool(snapshot, query):
    area = _get_query_location(query)["area"]
    nearby = [item for item in snapshot["complaints"] if item["area"] == area]
    if not nearby:
        nearby = [
            {
                "id": "CMP-LOCAL-01",
                "category": "General Civic Issue",
                "area": area,
                "priority": "Medium",
                "status": "Registered",
                "department": "City Civic Department",
            },
            {
                "id": "CMP-LOCAL-02",
                "category": "Drainage",
                "area": area,
                "priority": "High",
                "status": "Assigned",
                "department": "Drainage Cell",
            },
            {
                "id": "CMP-LOCAL-03",
                "category": "Road Maintenance",
                "area": area,
                "priority": "Medium",
                "status": "In Progress",
                "department": "BBMP Roads Department",
            },
        ]
    return nearby


def _build_weather_payload(snapshot, query):
    location = _get_query_location(query)
    water_zones = _build_local_waterlogging_pool(snapshot, query)
    traffic_zones = _build_local_traffic_pool(snapshot, query)
    water = max(water_zones, key=lambda item: 2 if item["risk_level"] == "High" else 1)
    traffic = min(traffic_zones, key=lambda item: item["avg_delay_min"])
    rain_risk = random.choice(["Medium", "High"])
    return {
        "headline": f"Rain and waterlogging status for {location['label']}",
        "status": "Live weather-linked demo insight",
        "metrics": [
            ("Rain Risk", rain_risk, "Based on weather and street condition layers"),
            ("Waterlogging", water["risk_level"], water["zone"]),
            ("Safer Corridor", traffic["area"], f"{traffic['avg_delay_min']} min delay"),
            ("Updated", datetime.now().strftime("%I:%M %p"), "Weather operations sync"),
        ],
        "cards": [
            {
                "title": "Alert Zone",
                "rows": [
                    ("Zone", water["zone"]),
                    ("Area", water["area"]),
                    ("Risk Level", water["risk_level"]),
                    ("Reason", water["reason"]),
                    ("Field Desk", _phone_for(water["zone"], 6610)),
                ],
            },
            {
                "title": "Travel Advisory",
                "rows": [
                    ("Preferred Area", traffic["area"]),
                    ("Traffic Delay", f"{traffic['avg_delay_min']} minutes"),
                    ("Advisory", "Avoid underpasses if rain increases"),
                    ("Operations Line", "+91 80 4400 2200"),
                ],
            },
        ],
        "feed": [
            f"Waterlogging hotspots are focused around {location['label']}.",
            "Traffic and rain-sensitive zones are combined for a local area warning.",
        ],
    }


def _build_general_payload():
    return {
        "headline": "SmartCity routed your query",
        "status": "Waiting for a more specific civic request",
        "metrics": [
            ("Mode", "Live/Demo", "Dashboard orchestration"),
            ("Coverage", "5 agents", "Emergency, hospital, route, weather, complaint"),
            ("Map", "Ready", "City signal layers loaded"),
            ("Updated", datetime.now().strftime("%I:%M %p"), "Session snapshot"),
        ],
        "cards": [],
        "feed": [
            "Try an ambulance, hospital, traffic, weather, or complaint query to unlock richer operations detail.",
        ],
        "summary": [],
    }


def _build_live_payload(snapshot, intent, query):
    if intent == "Emergency Response Agent":
        return _build_emergency_payload(snapshot, query)
    if intent == "Hospital Capacity Agent":
        return _build_hospital_payload(snapshot, query)
    if intent == "Traffic Optimization Agent":
        return _build_traffic_payload(snapshot, query)
    if intent == "Civic Complaint Agent":
        return _build_complaint_payload(snapshot, query)
    if intent == "Traffic & Flood Risk Agent":
        return _build_weather_payload(snapshot, query)
    return _build_general_payload()


def _inject_dashboard_css():
    st.markdown(
        """
        <style>
        .dashboard-mini-hero {
            position: relative;
            overflow: hidden;
            padding: 28px 32px;
            border-radius: 30px;
            margin-bottom: 30px;
            background:
                linear-gradient(135deg, rgba(255,255,255,0.18), rgba(255,255,255,0.05)),
                radial-gradient(circle at top left, rgba(148, 163, 184, 0.18), transparent 36%),
                rgba(15, 23, 42, 0.42);
            backdrop-filter: blur(28px) saturate(145%);
            -webkit-backdrop-filter: blur(28px) saturate(145%);
            border: 1px solid rgba(255,255,255,0.20);
            box-shadow: 0 22px 55px rgba(15, 23, 42, 0.20), inset 0 1px 0 rgba(255,255,255,0.22);
        }

        .dashboard-title {
            font-size: 42px;
            line-height: 1.05;
            font-weight: 950;
            letter-spacing: -1.4px;
            margin-bottom: 12px;
            color: #f8fafc;
            text-shadow: 0 10px 30px rgba(15, 23, 42, 0.22);
        }

        .dashboard-subtitle {
            color: rgba(226,232,240,0.84);
            font-size: 15px;
            line-height: 1.65;
            max-width: 980px;
        }

        .ai-shell {
            padding: 24px;
            border-radius: 28px;
            background:
                linear-gradient(135deg, rgba(255,255,255,0.15), rgba(255,255,255,0.045)),
                rgba(15, 23, 42, 0.36);
            backdrop-filter: blur(24px) saturate(145%);
            -webkit-backdrop-filter: blur(24px) saturate(145%);
            border: 1px solid rgba(255,255,255,0.18);
            box-shadow: 0 18px 48px rgba(15, 23, 42, 0.16), inset 0 1px 0 rgba(255,255,255,0.18);
            margin-bottom: 18px;
        }

        .ai-title {
            font-size: 26px;
            font-weight: 950;
            color: #f8fafc;
            margin-bottom: 8px;
        }

        .ai-subtitle {
            color: rgba(203,213,225,0.82);
            font-size: 14px;
            line-height: 1.6;
            margin-bottom: 18px;
        }

        .example-label {
            margin-top: 10px;
            margin-bottom: 12px;
            color: #e2e8f0;
            font-size: 18px;
            font-weight: 900;
        }

        .section-heading {
            color: #f8fafc;
            text-shadow: none;
        }

        .live-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            margin: 18px 0 22px 0;
        }

        .ops-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 14px;
            margin: 14px 0 10px 0;
        }

        .live-card {
            padding: 16px;
            border-radius: 22px;
            background:
                linear-gradient(135deg, rgba(255,255,255,0.14), rgba(255,255,255,0.04)),
                rgba(15,23,42,0.34);
            backdrop-filter: blur(20px) saturate(140%);
            -webkit-backdrop-filter: blur(20px) saturate(140%);
            border: 1px solid rgba(255,255,255,0.17);
            box-shadow: 0 14px 34px rgba(15,23,42,0.14), inset 0 1px 0 rgba(255,255,255,0.16);
        }

        .ops-card {
            padding: 18px;
            border-radius: 22px;
            background:
                linear-gradient(135deg, rgba(255,255,255,0.14), rgba(255,255,255,0.04)),
                rgba(15,23,42,0.34);
            border: 1px solid rgba(255,255,255,0.17);
            box-shadow: 0 14px 34px rgba(15,23,42,0.14), inset 0 1px 0 rgba(255,255,255,0.16);
        }

        .ops-title {
            color: #f8fafc;
            font-size: 17px;
            font-weight: 900;
            margin-bottom: 12px;
        }

        .ops-row {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }

        .ops-row:last-child {
            border-bottom: none;
        }

        .ops-key {
            color: rgba(203,213,225,0.72);
            font-size: 12px;
            font-weight: 700;
        }

        .ops-value {
            color: #f8fafc;
            font-size: 12px;
            font-weight: 800;
            text-align: right;
        }

        .feed-shell {
            margin-top: 14px;
            padding: 18px;
            border-radius: 22px;
            background:
                linear-gradient(135deg, rgba(255,255,255,0.14), rgba(255,255,255,0.04)),
                rgba(15,23,42,0.30);
            border: 1px solid rgba(255,255,255,0.16);
        }

        .feed-title {
            color: #f8fafc;
            font-size: 16px;
            font-weight: 900;
            margin-bottom: 8px;
        }

        .feed-item {
            color: #dbe4f0;
            font-size: 13px;
            line-height: 1.6;
            margin-bottom: 8px;
        }

        .live-label {
            color: rgba(203,213,225,0.72);
            font-size: 11px;
            font-weight: 950;
            text-transform: uppercase;
            letter-spacing: 0.10em;
            margin-bottom: 8px;
        }

        .live-value {
            color: #f8fafc;
            font-size: 23px;
            font-weight: 950;
            margin-bottom: 5px;
        }

        .live-note {
            color: #cbd5e1;
            font-size: 12px;
            font-weight: 700;
        }

        .result-tag {
            display: inline-block;
            padding: 9px 14px;
            border-radius: 999px;
            background: linear-gradient(135deg, rgba(255,255,255,0.16), rgba(255,255,255,0.06));
            border: 1px solid rgba(255,255,255,0.18);
            color: #e2e8f0;
            font-size: 13px;
            font-weight: 900;
            margin-bottom: 14px;
            box-shadow: 0 10px 26px rgba(15, 23, 42, 0.12);
        }

        .empty-state {
            padding: 28px;
            border-radius: 28px;
            background:
                linear-gradient(135deg, rgba(255,255,255,0.12), rgba(255,255,255,0.04)),
                rgba(15,23,42,0.30);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.16);
            color: rgba(226,232,240,0.84);
            text-align: center;
            margin-top: 18px;
            box-shadow: 0 14px 36px rgba(15, 23, 42, 0.12);
        }

        .legend-box,
        .priority-card {
            background:
                linear-gradient(135deg, rgba(255,255,255,0.15), rgba(255,255,255,0.045)),
                rgba(15,23,42,0.34);
            backdrop-filter: blur(22px) saturate(140%);
            -webkit-backdrop-filter: blur(22px) saturate(140%);
            border: 1px solid rgba(255,255,255,0.16);
            box-shadow: 0 16px 38px rgba(15,23,42,0.14), inset 0 1px 0 rgba(255,255,255,0.14);
        }

        .legend-item,
        .map-note,
        .priority-card {
            color: #dbe4f0;
        }

        .priority-high,
        .priority-medium,
        .priority-low {
            border-left-width: 4px;
            border-left-color: rgba(148, 163, 184, 0.65);
        }

        .dot {
            box-shadow: none;
        }

        .stTextInput input {
            background: rgba(255,255,255,0.10) !important;
            backdrop-filter: blur(18px) saturate(135%) !important;
            -webkit-backdrop-filter: blur(18px) saturate(135%) !important;
            border: 1px solid rgba(255,255,255,0.18) !important;
            color: #f8fafc !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.12), 0 12px 26px rgba(15,23,42,0.10) !important;
        }

        .stTextInput input:focus {
            border-color: rgba(191, 219, 254, 0.75) !important;
            box-shadow: 0 0 0 3px rgba(191, 219, 254, 0.14), 0 14px 28px rgba(15,23,42,0.12) !important;
        }

        .stButton button {
            border-radius: 18px !important;
            border: 1px solid rgba(255,255,255,0.18) !important;
            background: linear-gradient(135deg, rgba(255,255,255,0.18), rgba(255,255,255,0.07)) !important;
            color: #f8fafc !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.18), 0 14px 28px rgba(15,23,42,0.12) !important;
        }

        .stButton button:hover {
            border-color: rgba(255,255,255,0.24) !important;
            background: linear-gradient(135deg, rgba(255,255,255,0.22), rgba(255,255,255,0.09)) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.22), 0 18px 34px rgba(15,23,42,0.14) !important;
            filter: none !important;
        }

        div[data-testid="stVerticalBlock"] div[data-testid="stContainer"] {
            border-radius: 24px;
        }

        canvas,
        iframe {
            border-radius: 18px;
        }

        @media (max-width: 900px) {
            .live-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .ops-grid {
                grid-template-columns: 1fr;
            }
            .dashboard-title {
                font-size: 34px;
            }
        }

        @media (max-width: 650px) {
            .live-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def _render_live_metrics(payload):
    metrics = payload["metrics"]
    cols = st.columns(len(metrics))
    for col, (label, value, note) in zip(cols, metrics):
        with col:
            with st.container(border=True):
                st.caption(label)
                st.markdown(f"### {value}")
                st.caption(note)


def _render_operations_cards(payload):
    if payload["cards"]:
        card_cols = st.columns(2)
        for index, card in enumerate(payload["cards"]):
            with card_cols[index % 2]:
                with st.container(border=True):
                    st.markdown(f"#### {card['title']}")
                    for label, value in card["rows"]:
                        row_left, row_right = st.columns([0.45, 0.55])
                        with row_left:
                            st.caption(label)
                        with row_right:
                            st.markdown(f"**{value}**")

    if payload["feed"]:
        with st.container(border=True):
            st.markdown("#### Operations Feed")
            for item in payload["feed"]:
                st.write(f"- {item}")


def _render_summary_strip(payload):
    summary = payload.get("summary", [])
    if not summary:
        return

    st.markdown("### Quick Contact")
    cols = st.columns(len(summary))
    for col, (label, value) in zip(cols, summary):
        with col:
            with st.container(border=True):
                st.caption(label)
                st.markdown(f"**{value}**")


def render_dashboard_page(
    load_json,
    get_traffic_zones,
    get_waterlogging_zones,
    run_smartcity_agent,
    create_smartcity_deck_map,
    render_context_analytics,
):
    _inject_dashboard_css()
    snapshot = _load_city_snapshot(load_json, get_traffic_zones, get_waterlogging_zones)

    back_col, _ = st.columns([0.20, 0.80])
    with back_col:
        if st.button("← Back", use_container_width=True):
            st.session_state.entered_dashboard = False
            st.session_state.last_query = ""
            st.session_state.last_intent = None
            st.session_state.last_answer = None
            st.session_state.last_deck = None
            st.rerun()

    st.markdown(
        """
        <div class="dashboard-mini-hero">
            <div class="dashboard-title">🏙️ SmartCity AI Console</div>
            <div class="dashboard-subtitle">
                Ask one civic question. SmartCity routes it to the correct agent and returns an explainable recommendation with a decision map.
                Real APIs are used where available, and restricted civic operations are shown through demo live data.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="section-heading">🤖 Ask SmartCity</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="ai-shell">
            <div class="ai-title">What civic issue do you want to solve?</div>
            <div class="ai-subtitle">
                Type naturally. Example: ambulance request, hospital beds, pothole complaint, rain risk, waterlogging, or best route during traffic.
            </div>
        """,
        unsafe_allow_html=True
    )

    query = st.text_input(
        "Ask SmartCity",
        placeholder="Example: Ambulance near Indiranagar",
        label_visibility="collapsed"
    )

    ask_button = st.button("Send to SmartCity AI", type="primary", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    _capture_exact_location()

    if ask_button:
        _run_query(query, run_smartcity_agent)

    if st.session_state.last_answer is None:
        st.markdown('<div class="example-label">Try an example</div>', unsafe_allow_html=True)

        quick_queries = [
            "Ambulance near Indiranagar",
            "Hospital with ICU beds near Koramangala",
            "Best route from Electronic City to Majestic during rain",
            "Pothole near JP Nagar 7th Phase",
            "Waterlogging near Silk Board",
        ]

        quick_cols = st.columns(5, gap="medium")
        for col, quick_query in zip(quick_cols, quick_queries):
            with col:
                if st.button(quick_query, use_container_width=True):
                    _run_query(quick_query, run_smartcity_agent)
                    st.rerun()

    if st.session_state.last_answer is None:
        st.markdown(
            """
            <div class="empty-state">
                SmartCity is ready. Enter a question above to generate live/demo civic intelligence, recommendation, explanation, and map.
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    payload = _build_live_payload(snapshot, st.session_state.last_intent, st.session_state.last_query)
    focused_map = _build_context_map(
        snapshot,
        st.session_state.last_intent,
        st.session_state.last_query,
        create_smartcity_deck_map,
    )
    map_to_render = st.session_state.last_deck or focused_map
    map_caption = (
        "Agent-generated civic map based on the current recommendation."
        if st.session_state.last_deck is not None
        else "Red markers show nearby ambulances. Blue marks your location. Green markers show nearby hospitals when needed."
    )

    st.markdown('<div class="section-heading">⚡ Live Civic Intelligence</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="result-tag">
            Active Agent: {st.session_state.last_intent}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.caption(f"Last query: {st.session_state.last_query}")
    st.caption(f"Operations status: {payload['status']}")
    st.caption(_location_status_text(st.session_state.last_query))

    _render_live_metrics(payload)
    _render_summary_strip(payload)

    with st.container(border=True):
        st.markdown("### Live Operations Snapshot")
        st.caption(payload["headline"])
        _render_operations_cards(payload)

    if st.session_state.last_intent != "Emergency Response Agent":
        with st.container(border=True):
            st.markdown("### Recommendation")
            st.markdown(st.session_state.last_answer)

    st.markdown('<div class="section-heading">🗺️ City Signal Map</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("### Nearby Civic Map")
        st.markdown(
            f'<div class="map-note">{map_caption}</div>',
            unsafe_allow_html=True
        )
        st.pydeck_chart(map_to_render, use_container_width=True)

    analytics_hospitals = _build_nearby_hospital_pool(snapshot, st.session_state.last_query)
    analytics_traffic_zones = _build_local_traffic_pool(snapshot, st.session_state.last_query)
    analytics_complaints = _build_local_complaint_pool(snapshot, st.session_state.last_query)
    analytics_waterlogging_zones = _build_local_waterlogging_pool(snapshot, st.session_state.last_query)

    render_context_analytics(
        st.session_state.last_intent,
        analytics_hospitals,
        analytics_traffic_zones,
        analytics_complaints,
        analytics_waterlogging_zones,
    )

    st.divider()
    st.caption(
        "SmartCity by Team ByteForge | Live APIs where available + demo civic operations data for hackathon presentation."
    )
