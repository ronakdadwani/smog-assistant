"""
aqi_service.py - Multi-tier real-time Air Quality Index (AQI) fetcher.

Data Ingestion Hierarchy:
1. Live WAQI API (when WAQI_API_TOKEN is provided)
2. Free Open-Meteo Global Air Quality & Weather API (requires NO API key, works for ANY city worldwide)
3. Calibrated Simulation Fallback (offline mode)
"""

import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Pre-calibrated winter smog city profiles for offline / network failure mode
MOCK_CITIES: Dict[str, Dict[str, Any]] = {
    "delhi": {
        "city": "Delhi, India",
        "aqi": 418,
        "pm25": 372.5,
        "pm10": 480.0,
        "temperature": 16.0,
        "humidity": 78,
        "dominant_pollutant": "pm25",
        "station_name": "Anand Vihar, Delhi, India - DPCC",
        "source": "Calibrated Winter Smog Profile"
    },
    "hyderabad": {
        "city": "Hyderabad, India",
        "aqi": 88,
        "pm25": 29.5,
        "pm10": 68.0,
        "temperature": 25.0,
        "humidity": 58,
        "dominant_pollutant": "pm25",
        "station_name": "Sanathnagar, Hyderabad, India - TSPCB",
        "source": "Calibrated Moderate Urban Profile"
    },
    "mumbai": {
        "city": "Mumbai, India",
        "aqi": 175,
        "pm25": 85.0,
        "pm10": 130.0,
        "temperature": 27.0,
        "humidity": 65,
        "dominant_pollutant": "pm25",
        "station_name": "Bandra Kurla Complex, Mumbai",
        "source": "Calibrated Coastal Urban Profile"
    },
    "bengaluru": {
        "city": "Bengaluru, India",
        "aqi": 75,
        "pm25": 24.0,
        "pm10": 55.0,
        "temperature": 23.0,
        "humidity": 52,
        "dominant_pollutant": "pm25",
        "station_name": "BTM Layout, Bengaluru",
        "source": "Calibrated Moderate Urban Profile"
    },
    "kolkata": {
        "city": "Kolkata, India",
        "aqi": 210,
        "pm25": 115.0,
        "pm10": 160.0,
        "temperature": 21.0,
        "humidity": 70,
        "dominant_pollutant": "pm25",
        "station_name": "Victoria Memorial, Kolkata",
        "source": "Calibrated Winter Smog Profile"
    },
    "lahore": {
        "city": "Lahore, Pakistan",
        "aqi": 395,
        "pm25": 345.0,
        "pm10": 420.0,
        "temperature": 15.0,
        "humidity": 82,
        "dominant_pollutant": "pm25",
        "station_name": "Gulberg, Lahore, Pakistan",
        "source": "Calibrated Winter Smog Profile"
    },
    "beijing": {
        "city": "Beijing, China",
        "aqi": 138,
        "pm25": 50.2,
        "pm10": 85.0,
        "temperature": 4.0,
        "humidity": 45,
        "dominant_pollutant": "pm25",
        "station_name": "Chaoyang District, Beijing",
        "source": "Calibrated Winter Smog Profile"
    },
    "london": {
        "city": "London, United Kingdom",
        "aqi": 58,
        "pm25": 15.2,
        "pm10": 26.0,
        "temperature": 8.0,
        "humidity": 85,
        "dominant_pollutant": "pm25",
        "station_name": "London Bloomsbury, UK",
        "source": "Calibrated Clean/Moderate Air Baseline"
    },
    "new york": {
        "city": "New York, USA",
        "aqi": 28,
        "pm25": 6.8,
        "pm10": 12.0,
        "temperature": 5.0,
        "humidity": 52,
        "dominant_pollutant": "pm25",
        "station_name": "CCNY, Manhattan, NY",
        "source": "Calibrated Clean Air Baseline"
    },
    "tokyo": {
        "city": "Tokyo, Japan",
        "aqi": 24,
        "pm25": 5.5,
        "pm10": 10.0,
        "temperature": 11.0,
        "humidity": 48,
        "dominant_pollutant": "pm25",
        "station_name": "Shinjuku, Tokyo",
        "source": "Calibrated Clean Air Baseline"
    }
}


def get_aqi_category(aqi: int) -> Dict[str, str]:
    """Returns EPA-standard severity label, color code, and alert description."""
    aqi_val = max(0, int(aqi))
    if aqi_val <= 50:
        return {
            "severity_label": "Good",
            "name": "Good",
            "color": "#00E400",
            "text_color": "#004d00",
            "alert": "Air quality is satisfactory, and air pollution poses little or no risk."
        }
    elif aqi_val <= 100:
        return {
            "severity_label": "Moderate",
            "name": "Moderate",
            "color": "#FFFF00",
            "text_color": "#4d4d00",
            "alert": "Air quality is acceptable; however, sensitive individuals may experience mild symptoms."
        }
    elif aqi_val <= 150:
        return {
            "severity_label": "Unhealthy for Sensitive Groups",
            "name": "Unhealthy for Sensitive Groups",
            "color": "#FF7E00",
            "text_color": "#663300",
            "alert": "Members of sensitive groups may experience health effects. The general public is less likely to be affected."
        }
    elif aqi_val <= 200:
        return {
            "severity_label": "Unhealthy",
            "name": "Unhealthy",
            "color": "#FF0000",
            "text_color": "#ffffff",
            "alert": "Some members of the general public may experience health effects; sensitive groups may experience more serious effects."
        }
    elif aqi_val <= 300:
        return {
            "severity_label": "Very Unhealthy",
            "name": "Very Unhealthy",
            "color": "#8F3F97",
            "text_color": "#ffffff",
            "alert": "Health alert: The risk of health effects is increased for everyone."
        }
    else:
        return {
            "severity_label": "Hazardous",
            "name": "Hazardous",
            "color": "#7E0023",
            "text_color": "#ffffff",
            "alert": "Health warning of emergency conditions: The entire population is more likely to be severely affected."
        }


def _fetch_open_meteo_live(city_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetches real-time live air quality & weather for ANY city worldwide using Open-Meteo.
    Requires NO API KEY.
    """
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1"
        geo_resp = requests.get(geo_url, timeout=5)
        if geo_resp.status_code != 200:
            return None

        geo_data = geo_resp.json()
        results = geo_data.get("results")
        if not results:
            return None

        place = results[0]
        lat = place["latitude"]
        lon = place["longitude"]
        resolved_city = f"{place['name']}, {place.get('country', '')}".strip(", ")

        # 1. Fetch live Air Quality
        aq_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=us_aqi,pm2_5,pm10,carbon_monoxide,nitrogen_dioxide,ozone"
        aq_resp = requests.get(aq_url, timeout=5)
        if aq_resp.status_code != 200:
            return None

        curr_aq = aq_resp.json().get("current", {})
        raw_aqi = curr_aq.get("us_aqi")
        if raw_aqi is None:
            return None

        aqi = int(raw_aqi)
        pm25 = float(curr_aq.get("pm2_5") or (aqi * 0.7))
        pm10 = float(curr_aq.get("pm10") or (pm25 * 1.3))

        # 2. Fetch live Temperature & Humidity
        temp = 22.0
        humidity = 55.0
        try:
            w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m"
            w_resp = requests.get(w_url, timeout=4)
            if w_resp.status_code == 200:
                curr_w = w_resp.json().get("current", {})
                temp = float(curr_w.get("temperature_2m", temp))
                humidity = float(curr_w.get("relative_humidity_2m", humidity))
        except Exception:
            pass

        cat = get_aqi_category(aqi)
        return {
            "city": resolved_city,
            "aqi": aqi,
            "pm25": round(pm25, 1),
            "pm10": round(pm10, 1),
            "dominant_pollutant": "pm25",
            "severity_label": cat["severity_label"],
            "category": cat["name"],
            "category_color": cat["color"],
            "severity_color": cat["color"],
            "text_color": cat["text_color"],
            "alert": cat["alert"],
            "temperature": round(temp, 1),
            "humidity": round(humidity, 1),
            "station_name": f"{resolved_city} Sensor Network",
            "is_mock": False,
            "status_note": "Live global sensor feed via Open-Meteo (Real-Time)."
        }
    except Exception:
        return None


def get_city_aqi(city: str, api_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetches real-time AQI, PM2.5, PM10, and dominant pollutant by city.
    Order of precedence:
    1. WAQI API (if valid token provided)
    2. Open-Meteo Global Air Quality API (live worldwide, no key required)
    3. Calibrated Simulation Fallback
    """
    if not city or not city.strip():
        city = "Delhi"

    clean_city = city.strip()
    city_normalized = clean_city.lower()
    token = api_token or os.getenv("WAQI_API_TOKEN", "").strip()

    # 1. Try WAQI if user entered a real token
    if token and token != "your_waqi_api_token_here" and token.lower() != "demo":
        url = f"https://api.waqi.info/feed/{clean_city}/?token={token}"
        try:
            response = requests.get(url, timeout=6)
            if response.status_code == 200:
                payload = response.json()
                if payload.get("status") == "ok":
                    data = payload.get("data", {})
                    raw_aqi = data.get("aqi")
                    try:
                        aqi = int(raw_aqi)
                    except (ValueError, TypeError):
                        aqi = 50

                    iaqi = data.get("iaqi", {})
                    pm25 = float(iaqi.get("pm25", {}).get("v", aqi * 0.8))
                    pm10 = float(iaqi.get("pm10", {}).get("v", pm25 * 1.3))
                    temp = float(iaqi.get("t", {}).get("v", 20.0))
                    humidity = float(iaqi.get("h", {}).get("v", 50.0))
                    dom_pol = str(data.get("dominentpol", "pm25")).lower()
                    city_name = data.get("city", {}).get("name", clean_city)

                    cat = get_aqi_category(aqi)
                    return {
                        "city": city_name,
                        "aqi": aqi,
                        "pm25": round(pm25, 1),
                        "pm10": round(pm10, 1),
                        "dominant_pollutant": dom_pol,
                        "severity_label": cat["severity_label"],
                        "category": cat["name"],
                        "category_color": cat["color"],
                        "severity_color": cat["color"],
                        "text_color": cat["text_color"],
                        "alert": cat["alert"],
                        "temperature": round(temp, 1),
                        "humidity": round(humidity, 1),
                        "station_name": city_name,
                        "is_mock": False,
                        "status_note": "Live data from WAQI monitoring station."
                    }
        except Exception:
            pass

    # 2. Try Open-Meteo Global Air Quality API (Live, works for ANY city worldwide)
    live_open_meteo = _fetch_open_meteo_live(clean_city)
    if live_open_meteo:
        return live_open_meteo

    # 3. Fallback to calibrated database
    return _get_mock_aqi(
        city_normalized,
        requested_name=clean_city,
        reason="Network unavailable or city not found in live databases. Using calibrated simulation profile."
    )


def _get_mock_aqi(city_key: str, requested_name: str, reason: str) -> Dict[str, Any]:
    """Generates realistic mock data when live APIs are unavailable."""
    profile = None
    for key, data in MOCK_CITIES.items():
        if key in city_key or city_key in key:
            profile = data
            break

    if not profile:
        profile = {
            "city": requested_name.title(),
            "aqi": 165,
            "pm25": 82.5,
            "pm10": 115.0,
            "temperature": 18.0,
            "humidity": 65,
            "dominant_pollutant": "pm25",
            "station_name": f"{requested_name.title()} Sensor (Calibrated Simulation)",
            "source": "Standard Urban Smog Simulation"
        }

    cat = get_aqi_category(profile["aqi"])
    return {
        "city": profile["city"],
        "aqi": profile["aqi"],
        "pm25": profile["pm25"],
        "pm10": profile["pm10"],
        "dominant_pollutant": profile["dominant_pollutant"],
        "severity_label": cat["severity_label"],
        "category": cat["name"],
        "category_color": cat["color"],
        "severity_color": cat["color"],
        "text_color": cat["text_color"],
        "alert": cat["alert"],
        "temperature": profile["temperature"],
        "humidity": profile["humidity"],
        "station_name": profile["station_name"],
        "is_mock": True,
        "status_note": f"Simulation Mode: {reason}"
    }
