"""
impact_calc.py - Deterministic impact, exposure, and mitigation swap calculator for smog & air pollution.

Guiding Rule:
All mathematical calculations relating to emissions, equivalent cigarette exposure,
outdoor exercise thresholds, and daily mitigation swaps must be strictly deterministic,
documented with peer-reviewed or EPA/IPCC emission factors, and verified in Python.
"""

from typing import Dict, Any, List


# -----------------------------------------------------------------------------
# DOCUMENTED EMISSION FACTORS & PEER-REVIEWED CONSTANTS
# -----------------------------------------------------------------------------
# Transport: UK DEFRA & US EPA GHG Emissions Factors for Passenger Transport
# Cooking: RMI & WHO Indoor Air Quality Guidelines for Residential Fuel Combustion
# Waste: US EPA AP-42 & IPCC Municipal Solid Waste Open Burning Emission Factors
# Air Filtration: US EPA "Air Cleaners in the Home" & Corsi-Rosenthal Box Performance Studies
# -----------------------------------------------------------------------------

TRANSIT_FACTORS = {
    "petrol_car": {"co2_per_km": 0.192, "pm25_per_km": 0.030, "label": "Single-Occupancy Petrol Car"},
    "diesel_car": {"co2_per_km": 0.171, "pm25_per_km": 0.050, "label": "Single-Occupancy Diesel Car"},
    "motorcycle": {"co2_per_km": 0.103, "pm25_per_km": 0.040, "label": "Motorcycle / Scooter"},
    "carpool": {"co2_per_km": 0.075, "pm25_per_km": 0.012, "label": "Carpool (3 passengers)"},
    "bus": {"co2_per_km": 0.068, "pm25_per_km": 0.008, "label": "City Bus Transit"},
    "metro": {"co2_per_km": 0.028, "pm25_per_km": 0.001, "label": "Electric Metro / Subway"},
    "electric_car": {"co2_per_km": 0.045, "pm25_per_km": 0.003, "label": "Electric Vehicle (Grid Average)"},
    "bicycle": {"co2_per_km": 0.000, "pm25_per_km": 0.000, "label": "Bicycle / Walking"},
    "wfh": {"co2_per_km": 0.000, "pm25_per_km": 0.000, "label": "Work From Home (Zero Commute)"}
}

COOKING_FACTORS = {
    # Natural gas/LPG burner: ~0.20 kg CO2/kWh thermal at 40% efficiency => ~1.20 kg CO2/day for 2 meals
    # Induction: ~85% efficiency, consuming ~1.8 kWh electricity/day @ 0.40 kg CO2/kWh grid => ~0.72 kg CO2/day
    "gas_daily_co2_kg": 1.20,
    "induction_daily_co2_kg": 0.72,
    "pm25_cooking_reduction_pct": 55.0  # Elimination of fuel combustion emissions in kitchen
}

WASTE_FACTORS = {
    # Burning dry municipal/garden waste produces ~1.45 kg CO2/kg waste (IPCC 2006 Guidelines)
    # and ~9.8 g PM2.5/kg waste (EPA AP-42 Compilation of Air Pollutant Emission Factors)
    "co2_per_kg_waste": 1.45,
    "pm25_grams_per_kg_waste": 9.80,
    "neighborhood_exposure_reduction_pct": 80.0  # Avoidance of toxic near-ground open combustion smoke plume
}

FILTRATION_FACTORS = {
    # Operating a true HEPA air purifier or DIY Corsi-Rosenthal box (MERV 13)
    # CADR 200-300 CFM in standard room removes 80-90% PM2.5 particulates per air cycle
    "indoor_pm25_reduction_pct": 80.0,
    # Running localized 45W HEPA filter vs. continuous whole-home central HVAC fan (450W):
    # Saves ~40 kWh electricity weekly => ~16.0 kg CO2 saved per week @ 0.40 kg CO2/kWh
    "weekly_co2_saved_hvac_sub_kg": 16.00
}


# -----------------------------------------------------------------------------
# CORE SWAP CALCULATIONS
# -----------------------------------------------------------------------------

def calculate_transit_swap(
    distance_km: float = 10.0,
    current_mode: str = "petrol_car",
    alternative_mode: str = "metro",
    days_per_week: int = 5,
    round_trip: bool = True
) -> Dict[str, Any]:
    """
    Computes exact weekly CO2 saved (kg) and estimated PM2.5 exposure reduction (%)
    for transit swaps (e.g., petrol car vs. metro or carpool).

    Emission Factors:
        - petrol_car: 0.192 kg CO2/km, 0.030 g PM2.5/km
        - metro: 0.028 kg CO2/km, 0.001 g PM2.5/km
        - carpool: 0.075 kg CO2/km, 0.012 g PM2.5/km
    """
    base = TRANSIT_FACTORS.get(current_mode, TRANSIT_FACTORS["petrol_car"])
    alt = TRANSIT_FACTORS.get(alternative_mode, TRANSIT_FACTORS["metro"])

    dist = max(0.0, float(distance_km))
    daily_km = dist * 2.0 if round_trip else dist
    weekly_km = daily_km * max(1, int(days_per_week))

    co2_base = weekly_km * base["co2_per_km"]
    co2_alt = weekly_km * alt["co2_per_km"]
    weekly_co2_saved = max(0.0, co2_base - co2_alt)

    # In-transit personal PM2.5 exposure reduction:
    # Underground electric metro removes commuter from street-level tailpipe plumes (~70% reduction)
    # Carpooling reduces overall vehicle congestion (~20% reduction)
    # WFH / Bicycle in clean air: 100% or 0%
    if alternative_mode == "metro":
        pm25_reduction_pct = 70.0
    elif alternative_mode == "carpool":
        pm25_reduction_pct = 20.0
    elif alternative_mode == "wfh":
        pm25_reduction_pct = 90.0  # Zero commute exposure
    elif alternative_mode == "bus":
        pm25_reduction_pct = 35.0
    else:
        pm25_reduction_pct = 50.0

    return {
        "swap_name": f"{base['label']} -> {alt['label']}",
        "category": "transit",
        "weekly_co2_saved_kg": round(weekly_co2_saved, 2),
        "pm25_exposure_reduction_pct": pm25_reduction_pct,
        "weekly_km": round(weekly_km, 1),
        "baseline_co2_kg": round(co2_base, 2),
        "alternative_co2_kg": round(co2_alt, 2),
        "emission_factors": {
            "current_mode_co2_per_km": base["co2_per_km"],
            "alternative_mode_co2_per_km": alt["co2_per_km"]
        },
        "description": f"Switching {daily_km} km/day from {base['label']} to {alt['label']} for {days_per_week} days/week."
    }


def calculate_cooking_swap(meals_per_day: int = 2, days_per_week: int = 7) -> Dict[str, Any]:
    """
    Computes exact weekly CO2 saved (kg) and estimated PM2.5 exposure reduction (%)
    for transitioning from gas/LPG cooking to electric induction cooking.

    Factors:
        - Gas cooktop: ~1.20 kg CO2/day (combustion + low 40% thermal efficiency)
        - Induction cooktop: ~0.72 kg CO2/day (85% thermal efficiency on grid)
        - Eliminates indoor unvented combustion particulate emissions.
    """
    days = max(1, int(days_per_week))
    ratio = max(0.5, float(meals_per_day) / 2.0)

    daily_gas_co2 = COOKING_FACTORS["gas_daily_co2_kg"] * ratio
    daily_induction_co2 = COOKING_FACTORS["induction_daily_co2_kg"] * ratio
    daily_saved = max(0.0, daily_gas_co2 - daily_induction_co2)
    weekly_co2_saved = daily_saved * days

    return {
        "swap_name": "Gas Stove -> Induction Cooktop",
        "category": "cooking",
        "weekly_co2_saved_kg": round(weekly_co2_saved, 2),
        "pm25_exposure_reduction_pct": COOKING_FACTORS["pm25_cooking_reduction_pct"],
        "baseline_co2_kg": round(daily_gas_co2 * days, 2),
        "alternative_co2_kg": round(daily_induction_co2 * days, 2),
        "emission_factors": {
            "gas_daily_co2_kg": COOKING_FACTORS["gas_daily_co2_kg"],
            "induction_daily_co2_kg": COOKING_FACTORS["induction_daily_co2_kg"]
        },
        "description": "Switching from natural gas/LPG burners to clean magnetic induction cooking."
    }


def calculate_waste_burning_swap(waste_kg_per_week: float = 10.0) -> Dict[str, Any]:
    """
    Computes exact weekly CO2 saved (kg) and estimated PM2.5 exposure reduction (%)
    by avoiding open municipal or garden waste burning (diverting to composting/collection).

    Factors (IPCC & US EPA AP-42):
        - 1.45 kg CO2 per kg dry waste burned
        - 9.80 g PM2.5 per kg dry waste burned
        - Eliminates high-concentration neighborhood ground-level toxic smoke plumes.
    """
    kg_waste = max(0.0, float(waste_kg_per_week))
    weekly_co2_saved = kg_waste * WASTE_FACTORS["co2_per_kg_waste"]
    weekly_pm25_prevented_g = kg_waste * WASTE_FACTORS["pm25_grams_per_kg_waste"]

    return {
        "swap_name": "Open Waste Burning -> Composting / Municipal Disposal",
        "category": "waste_management",
        "weekly_co2_saved_kg": round(weekly_co2_saved, 2),
        "pm25_exposure_reduction_pct": WASTE_FACTORS["neighborhood_exposure_reduction_pct"],
        "waste_diverted_kg_week": round(kg_waste, 1),
        "pm25_prevented_g_week": round(weekly_pm25_prevented_g, 2),
        "emission_factors": {
            "co2_per_kg_waste": WASTE_FACTORS["co2_per_kg_waste"],
            "pm25_grams_per_kg_waste": WASTE_FACTORS["pm25_grams_per_kg_waste"]
        },
        "description": f"Avoiding open burning of {kg_waste} kg of organic/domestic waste per week."
    }


def calculate_filtration_swap(
    filter_type: str = "hepa",
    substitute_central_fan: bool = True
) -> Dict[str, Any]:
    """
    Computes exact weekly CO2 saved (kg) and estimated PM2.5 exposure reduction (%)
    from indoor HEPA or DIY box-fan (Corsi-Rosenthal) air filtration.

    Factors (US EPA & Corsi-Rosenthal):
        - Particle capture efficiency: 80% to 92% per air pass in sealed room.
        - Replacing continuous whole-house HVAC furnace circulation fan (~450W)
          with targeted room HEPA/Corsi-Rosenthal fan (~45W) saves ~40 kWh/week (~16 kg CO2/week).
    """
    label = "True HEPA Air Purifier" if filter_type.lower() == "hepa" else "DIY Corsi-Rosenthal Box-Fan (MERV 13)"
    weekly_co2_saved = FILTRATION_FACTORS["weekly_co2_saved_hvac_sub_kg"] if substitute_central_fan else 0.0

    return {
        "swap_name": f"Unfiltered Indoor Air -> {label}",
        "category": "indoor_air_filtration",
        "weekly_co2_saved_kg": round(weekly_co2_saved, 2),
        "pm25_exposure_reduction_pct": FILTRATION_FACTORS["indoor_pm25_reduction_pct"],
        "filter_type": label,
        "emission_factors": {
            "hepa_power_watts": 45,
            "central_hvac_fan_power_watts": 450,
            "weekly_kwh_saved": 40.0 if substitute_central_fan else 0.0
        },
        "description": f"Running {label} indoors while optimizing home airflow."
    }


def get_all_swaps_summary(
    commute_km: float = 10.0,
    transit_alt: str = "metro",
    waste_kg: float = 10.0
) -> List[Dict[str, Any]]:
    """
    Returns an aggregated list of all standard daily swaps with documented factors,
    exact weekly CO2 saved (kg), and PM2.5 exposure reduction (%).
    """
    swaps = [
        calculate_transit_swap(distance_km=commute_km, current_mode="petrol_car", alternative_mode=transit_alt),
        calculate_cooking_swap(meals_per_day=2),
        calculate_waste_burning_swap(waste_kg_per_week=waste_kg),
        calculate_filtration_swap(filter_type="hepa", substitute_central_fan=True)
    ]
    return swaps


# -----------------------------------------------------------------------------
# LEGACY & HEALTH EQUIVALENT FUNCTIONS (PRESERVED FOR APP COMPATIBILITY)
# -----------------------------------------------------------------------------

def calculate_cigarette_equivalent(pm25_ug_m3: float, exposure_hours: float = 24.0) -> Dict[str, Any]:
    """
    Computes equivalent cigarettes inhaled based on the Berkeley Earth scientific formula:
    One cigarette per day is roughly equivalent to a PM2.5 level of 22 µg/m³ over 24 hours.

    Formula:
        equivalent_cigarettes = (pm25_ug_m3 / 22.0) * (exposure_hours / 24.0)
    """
    pm25 = max(0.0, float(pm25_ug_m3))
    hours = max(0.0, float(exposure_hours))
    cigarettes = (pm25 / 22.0) * (hours / 24.0)

    if cigarettes < 0.2:
        level_desc = "Negligible particulate intake"
    elif cigarettes < 1.0:
        level_desc = "Mild exposure equivalent to fraction of a cigarette"
    elif cigarettes < 5.0:
        level_desc = f"Moderate-to-high exposure equivalent to ~{round(cigarettes, 1)} cigarettes"
    elif cigarettes < 15.0:
        level_desc = f"Severe toxic exposure equivalent to smoking {round(cigarettes, 1)} cigarettes/day"
    else:
        level_desc = f"Hazardous extreme exposure equivalent to smoking {round(cigarettes, 1)} cigarettes/day (heavy smoker equivalent)"

    return {
        "pm25_ug_m3": round(pm25, 1),
        "exposure_hours": round(hours, 1),
        "equivalent_cigarettes": round(cigarettes, 2),
        "description": level_desc
    }


def calculate_safe_outdoor_time(aqi: int) -> Dict[str, Any]:
    """
    Computes safe outdoor physical activity and exposure limits based on AQI brackets.
    Returns recommended max exposure in minutes for both general public and sensitive individuals.
    """
    aqi_val = max(0, int(aqi))

    if aqi_val <= 50:
        return {
            "aqi": aqi_val,
            "category": "Good",
            "general_public_minutes": 1440,
            "sensitive_groups_minutes": 1440,
            "exercise_recommendation": "Ideal conditions for outdoor sports, running, and activities.",
            "mask_needed": False
        }
    elif aqi_val <= 100:
        return {
            "aqi": aqi_val,
            "category": "Moderate",
            "general_public_minutes": 480,
            "sensitive_groups_minutes": 180,
            "exercise_recommendation": "Acceptable for outdoor exercise. Unusually sensitive people should monitor symptoms.",
            "mask_needed": False
        }
    elif aqi_val <= 150:
        return {
            "aqi": aqi_val,
            "category": "Unhealthy for Sensitive Groups",
            "general_public_minutes": 180,
            "sensitive_groups_minutes": 45,
            "exercise_recommendation": "Reduce prolonged outdoor exertion. Sensitive groups (asthma, children, elderly) should move activities indoors.",
            "mask_needed": True,
            "mask_type": "N95/FFP2 recommended for sensitive groups"
        }
    elif aqi_val <= 200:
        return {
            "aqi": aqi_val,
            "category": "Unhealthy",
            "general_public_minutes": 60,
            "sensitive_groups_minutes": 15,
            "exercise_recommendation": "Avoid strenuous outdoor exertion. Move workouts indoors.",
            "mask_needed": True,
            "mask_type": "Well-fitted N95 / FFP2 mask required outdoors"
        }
    elif aqi_val <= 300:
        return {
            "aqi": aqi_val,
            "category": "Very Unhealthy",
            "general_public_minutes": 20,
            "sensitive_groups_minutes": 0,
            "exercise_recommendation": "Strictly cancel all outdoor workouts. Keep doors and windows closed.",
            "mask_needed": True,
            "mask_type": "N95 / FFP2 / N99 mask mandatory for any outdoor transit"
        }
    else:
        return {
            "aqi": aqi_val,
            "category": "Hazardous",
            "general_public_minutes": 0,
            "sensitive_groups_minutes": 0,
            "exercise_recommendation": "Health emergency alert. Everyone must avoid all outdoor physical activity. Seal rooms and run HEPA filtration.",
            "mask_needed": True,
            "mask_type": "N95 / FFP3 / respirator with tight silicone seal strictly mandatory outdoors"
        }


def calculate_commute_savings(
    commute_distance_km: float,
    current_mode: str = "petrol_car",
    alternative_mode: str = "metro",
    round_trip: bool = True
) -> Dict[str, Any]:
    """
    Computes daily and weekly emission savings for the UI.
    """
    res = calculate_transit_swap(
        distance_km=commute_distance_km,
        current_mode=current_mode,
        alternative_mode=alternative_mode,
        days_per_week=5,
        round_trip=round_trip
    )
    dist = max(0.0, float(commute_distance_km))
    total_km = dist * 2.0 if round_trip else dist
    base_factors = TRANSIT_FACTORS.get(current_mode, TRANSIT_FACTORS["petrol_car"])
    alt_factors = TRANSIT_FACTORS.get(alternative_mode, TRANSIT_FACTORS["metro"])

    daily_co2 = total_km * (base_factors["co2_per_km"] - alt_factors["co2_per_km"])
    daily_pm25 = total_km * (base_factors["pm25_per_km"] - alt_factors["pm25_per_km"])

    return {
        "commute_km": dist,
        "round_trip_km": total_km,
        "current_mode": base_factors["label"],
        "alternative_mode": alt_factors["label"],
        "co2_saved_kg_day": round(max(0.0, daily_co2), 2),
        "co2_saved_kg_week": res["weekly_co2_saved_kg"],
        "co2_saved_kg_month": round(max(0.0, daily_co2) * 22.0, 2),
        "pm25_avoided_g_day": round(max(0.0, daily_pm25), 3),
        "pm25_exposure_reduction_pct": res["pm25_exposure_reduction_pct"],
        "equivalent_trees_planted_monthly": round((max(0.0, daily_co2) * 22.0) / 1.83, 1)
    }
