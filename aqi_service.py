"""
aqi_service.py - Air Quality Index (AQI) fetcher supporting real-time WAQI API and realistic fallback mock mode.

Handles:
- Live sensor data queries to the World Air Quality Index (WAQI / aqicn.org) API
- Graceful error handling for invalid tokens, unknown cities, timeouts, and connection errors
- Standardized data schema with clear severity labels, PM2.5, PM10, dominant pollutant, temperature, and humidity
"""

import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Pre-calibrated winter smog city profiles for mock / fallback mode
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
        "source": "Simulated Winter Peak Smog Calibration"
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
        "source": "Simulated Winter Peak Smog Calibration"
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
        "source": "Simulated Winter Calibration"
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
        "source": "Simulated Moderate Winter Calibration"
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
        "source": "Simulated Clean Air Baseline"
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
        "source": "Simulated Moderate Urban Calibration"
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
        "source": "Simulated Clean Air Baseline"
    }
}


def get_aqi_category(aqi: int) -> Dict[str, str]:
    """
    Returns EPA-standard severity label, color code, and alert description.
    """
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


def get_city_aqi(city: str, api_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetches real-time AQI, PM2.5, PM10, and dominant pollutant by city using WAQI API.
    Handles errors gracefully with clear severity labels and simulated fallback mode.
    """
    if not city or not city.strip():
        city = "Delhi"

    clean_city = city.strip()
    city_normalized = clean_city.lower()
    token = api_token or os.getenv("WAQI_API_TOKEN", "").strip()

    # Fallback to calibrated simulation when token is absent or default placeholder
    if not token or token == "your_waqi_api_token_here":
        return _get_mock_aqi(
            city_normalized,
            requested_name=clean_city,
            reason="No WAQI_API_TOKEN provided. Operating in calibrated simulation mode."
        )

    # Live WAQI API query
    url = f"https://api.waqi.info/feed/{clean_city}/?token={token}"
    try:
        response = requests.get(url, timeout=7)
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

                # Extract individual pollutants with safe fallbacks
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
            else:
                err_msg = payload.get("data", "Unknown city or station")
                return _get_mock_aqi(
                    city_normalized,
                    requested_name=clean_city,
                    reason=f"WAQI API notice: {err_msg}"
                )
        else:
            return _get_mock_aqi(
                city_normalized,
                requested_name=clean_city,
                reason=f"HTTP status {response.status_code} from WAQI API"
            )
    except requests.exceptions.Timeout:
        return _get_mock_aqi(
            city_normalized,
            requested_name=clean_city,
            reason="WAQI request timed out. Switched to fallback calibration."
        )
    except Exception as exc:
        return _get_mock_aqi(
            city_normalized,
            requested_name=clean_city,
            reason=f"Connection error: {str(exc)}"
        )


def _get_mock_aqi(city_key: str, requested_name: str, reason: str) -> Dict[str, Any]:
    """Generates realistic mock data when live API is unavailable."""
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
