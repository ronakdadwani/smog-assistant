"""
tests/test_impact.py - Comprehensive Unit Tests for impact_calc.py and aqi_service.py.

Verifies:
1. Documented daily swaps:
   - Petrol car vs. metro / carpool (weekly CO2 saved kg & PM2.5 exposure reduction %)
   - Gas vs. induction cooking
   - Avoiding open waste burning
   - Indoor HEPA / DIY box-fan filtration
2. AQI Service live query & mock fallback with clear severity labels
"""

import unittest
import sys
import os

# Add parent directory to sys.path so tests can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import impact_calc
import aqi_service


class TestImpactSwaps(unittest.TestCase):
    def test_transit_swap_petrol_to_metro(self):
        # 10 km one-way (20 km round trip) for 5 days = 100 km/week
        # petrol car: 100 * 0.192 = 19.2 kg CO2
        # metro: 100 * 0.028 = 2.8 kg CO2
        # saved: 16.4 kg CO2/week
        res = impact_calc.calculate_transit_swap(
            distance_km=10.0,
            current_mode="petrol_car",
            alternative_mode="metro",
            days_per_week=5,
            round_trip=True
        )
        self.assertEqual(res["weekly_co2_saved_kg"], 16.4)
        self.assertEqual(res["pm25_exposure_reduction_pct"], 70.0)
        self.assertIn("emission_factors", res)
        self.assertAlmostEqual(res["emission_factors"]["current_mode_co2_per_km"], 0.192)
        self.assertAlmostEqual(res["emission_factors"]["alternative_mode_co2_per_km"], 0.028)

    def test_transit_swap_petrol_to_carpool(self):
        # 100 km/week:
        # petrol car: 19.2 kg CO2
        # carpool: 100 * 0.075 = 7.5 kg CO2
        # saved: 11.7 kg CO2/week
        res = impact_calc.calculate_transit_swap(
            distance_km=10.0,
            current_mode="petrol_car",
            alternative_mode="carpool",
            days_per_week=5,
            round_trip=True
        )
        self.assertEqual(res["weekly_co2_saved_kg"], 11.7)
        self.assertEqual(res["pm25_exposure_reduction_pct"], 20.0)

    def test_cooking_swap_gas_to_induction(self):
        # 2 meals/day, 7 days/week
        # Gas: 1.20 kg CO2/day, Induction: 0.72 kg CO2/day
        # daily saved = 0.48 kg CO2 => weekly saved = 0.48 * 7 = 3.36 kg CO2/week
        res = impact_calc.calculate_cooking_swap(meals_per_day=2, days_per_week=7)
        self.assertEqual(res["weekly_co2_saved_kg"], 3.36)
        self.assertEqual(res["pm25_exposure_reduction_pct"], 55.0)
        self.assertIn("emission_factors", res)

    def test_waste_burning_swap(self):
        # 10 kg waste per week
        # 1.45 kg CO2/kg => 14.5 kg CO2 saved/week
        # 9.8 g PM2.5/kg => 98.0 g PM2.5 prevented/week
        res = impact_calc.calculate_waste_burning_swap(waste_kg_per_week=10.0)
        self.assertEqual(res["weekly_co2_saved_kg"], 14.5)
        self.assertEqual(res["pm25_exposure_reduction_pct"], 80.0)
        self.assertEqual(res["pm25_prevented_g_week"], 98.0)

    def test_filtration_swap_hepa(self):
        # HEPA localized filtration replacing central whole-home HVAC circulation
        # Saves 40 kWh weekly => 16.0 kg CO2 saved/week
        # Reduces indoor PM2.5 by 80%
        res = impact_calc.calculate_filtration_swap(filter_type="hepa", substitute_central_fan=True)
        self.assertEqual(res["weekly_co2_saved_kg"], 16.0)
        self.assertEqual(res["pm25_exposure_reduction_pct"], 80.0)

    def test_get_all_swaps_summary(self):
        swaps = impact_calc.get_all_swaps_summary(commute_km=10.0, transit_alt="metro", waste_kg=10.0)
        self.assertEqual(len(swaps), 4)
        for swap in swaps:
            self.assertIn("weekly_co2_saved_kg", swap)
            self.assertIn("pm25_exposure_reduction_pct", swap)
            self.assertGreater(swap["weekly_co2_saved_kg"], 0.0)
            self.assertGreater(swap["pm25_exposure_reduction_pct"], 0.0)


class TestAqiService(unittest.TestCase):
    def test_aqi_severity_labels(self):
        # Test severity label mapping
        good = aqi_service.get_aqi_category(35)
        self.assertEqual(good["severity_label"], "Good")

        moderate = aqi_service.get_aqi_category(75)
        self.assertEqual(moderate["severity_label"], "Moderate")

        unhealthy_sens = aqi_service.get_aqi_category(125)
        self.assertEqual(unhealthy_sens["severity_label"], "Unhealthy for Sensitive Groups")

        unhealthy = aqi_service.get_aqi_category(175)
        self.assertEqual(unhealthy["severity_label"], "Unhealthy")

        very_unhealthy = aqi_service.get_aqi_category(250)
        self.assertEqual(very_unhealthy["severity_label"], "Very Unhealthy")

        hazardous = aqi_service.get_aqi_category(380)
        self.assertEqual(hazardous["severity_label"], "Hazardous")

    def test_get_city_aqi_delhi_mock(self):
        res = aqi_service.get_city_aqi("Delhi")
        self.assertIn(res["severity_label"], ["Hazardous", "Very Unhealthy", "Unhealthy"])
        self.assertEqual(res["dominant_pollutant"], "pm25")
        self.assertIn("pm25", res)
        self.assertIn("pm10", res)
        self.assertGreater(res["aqi"], 100)

    def test_get_city_aqi_graceful_error_handling(self):
        # Empty city name
        res_empty = aqi_service.get_city_aqi("")
        self.assertIn("severity_label", res_empty)
        self.assertIn("dominant_pollutant", res_empty)

        # Unlisted / unknown city without token
        res_unknown = aqi_service.get_city_aqi("Atlantis999")
        self.assertIn("severity_label", res_unknown)
        self.assertTrue(res_unknown["is_mock"])


if __name__ == "__main__":
    unittest.main()
