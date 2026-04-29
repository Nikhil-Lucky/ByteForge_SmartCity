# ByteForge SmartCity

SmartCity is a Streamlit-based hackathon prototype for civic decision support. It routes natural-language queries to focused civic workflows such as ambulance dispatch, hospital capacity lookup, traffic-aware route guidance, flood-risk awareness, and complaint registration.

## Features

- Natural-language civic query routing
- Emergency response recommendations
- Hospital capacity recommendations
- Traffic and route-risk analysis
- Rain and waterlogging awareness
- Complaint workflow simulation
- Dedicated pothole complaint desk with photo upload/camera capture
- Session-based pothole complaint tracking with complaint IDs
- PyDeck-based civic visualization
- Local mock datasets with optional live API enrichment

## Project structure

- `app.py`: main Streamlit application and agent/router logic
- `landing_page.py`: landing experience and city snapshot
- `dashboard_page.py`: operational dashboard and result presentation
- `data/`: mock civic datasets
- `components/location_picker/`: unused browser geolocation prototype asset
- `progress.md`: build/status tracker

## Requirements

- Python 3.10+
- `pip`

Python packages are listed in [requirements.txt](e:/Hackathon/ByteForge_SmartCity/requirements.txt).

## Environment variables

Create a `.env` file in the project root if you want live integrations.

Supported variables:

- `OPENAI_API_KEY`: optional, used for query-based location extraction fallback
- `GOOGLE_MAPS_API_KEY`: optional, used for geocoding custom place names

If these keys are missing, the app still works in demo mode using local mock data and fallback location logic.

## Install

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
streamlit run app.py
```

## Demo query examples

- `Ambulance near Indiranagar`
- `Hospital with ICU beds near Koramangala`
- `Best route from Electronic City to Majestic during rain`
- `Pothole near JP Nagar 7th Phase`
- `Waterlogging near Silk Board`

## Pothole complaint flow

The dashboard includes a dedicated `Pothole Complaint` action in the top-right corner.

From that screen, users can:

- open a separate pothole complaint desk
- take a photo using the camera or upload an image
- auto-register a pothole complaint using detected app location
- receive a generated complaint ID
- see the assigned BBMP roads team
- track pothole complaints created during the current session

This is currently a demo workflow that simulates complaint registration and BBMP routing inside the app.

## Notes on location behavior

- Known Bengaluru areas are matched directly from the query.
- Custom locations can be geocoded when API support is available.
- If no explicit location is found, the app falls back to approximate IP-based or city-level location.
- Exact browser GPS capture is not currently wired into the Streamlit flow, so `near me` style queries use approximate fallback logic.
- Pothole complaint auto-location currently uses the app's detected location, not photo EXIF GPS metadata.

## Current status

The app is demo-ready for hackathon presentation, with the main remaining work centered on additional testing, final UI review, and optional production hardening.
