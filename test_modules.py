"""
test_modules.py - Integration test verification for smog-assistant core modules.
"""

import unittest
import impact_calc
import aqi_service
import ai_engine


class TestSmogAssistantIntegration(unittest.TestCase):
    def test_impact_calc_cigarette_equivalent(self):
        res = impact_calc.calculate_cigarette_equivalent(22.0, 24.0)
        self.assertEqual(res["equivalent_cigarettes"], 1.0)

    def test_impact_calc_safe_outdoor_time(self):
        good = impact_calc.calculate_safe_outdoor_time(40)
        self.assertEqual(good["category"], "Good")
        haz = impact_calc.calculate_safe_outdoor_time(350)
        self.assertEqual(haz["category"], "Hazardous")

    def test_impact_calc_daily_swaps(self):
        swaps = impact_calc.get_all_swaps_summary(commute_km=10.0, transit_alt="metro", waste_kg=10.0)
        self.assertEqual(len(swaps), 4)

    def test_aqi_service_categories_and_mock(self):
        res = aqi_service.get_city_aqi("Delhi")
        self.assertIn(res["severity_label"], ["Hazardous", "Very Unhealthy", "Unhealthy"])
        self.assertIn("pm25", res)
        self.assertIn("dominant_pollutant", res)

    def test_ai_engine_structured_advisory_schema(self):
        aqi_data = aqi_service.get_city_aqi("Delhi")
        cigs = impact_calc.calculate_cigarette_equivalent(aqi_data["pm25"])
        safe_time = impact_calc.calculate_safe_outdoor_time(aqi_data["aqi"])
        swaps = impact_calc.get_all_swaps_summary(commute_km=10.0, transit_alt="metro", waste_kg=10.0)

        plan = ai_engine.generate_structured_advisory(
            aqi_data=aqi_data,
            swaps_data=swaps,
            cigarette_data=cigs,
            safe_time_data=safe_time,
            household_context="Infant and asthmatic adult",
            budget_tier="Zero-Cost & Low-Cost DIY (<$20)"
        )

        # Verify exact required fields
        self.assertIn("daily_routine", plan)
        self.assertIn("indoor_air_hacks", plan)
        self.assertIn("sustainable_swaps", plan)
        self.assertIn("community_action", plan)
        self.assertIn("disclaimer", plan)

        # Check content in each field
        self.assertGreater(len(plan["daily_routine"]), 0)
        self.assertIn("time_window", plan["daily_routine"][0])

        self.assertGreater(len(plan["indoor_air_hacks"]), 0)
        self.assertIn("hack_title", plan["indoor_air_hacks"][0])

        self.assertGreater(len(plan["sustainable_swaps"]), 0)
        self.assertIn("why_this_works", plan["sustainable_swaps"][0])
        self.assertIn("weekly_co2_saved_kg", plan["sustainable_swaps"][0])
        self.assertIn("pm25_reduction_pct", plan["sustainable_swaps"][0])

        self.assertIn("shareable_message", plan["community_action"])

    def test_ai_engine_chat_fallback(self):
        aqi_data = aqi_service.get_city_aqi("London")
        reply = ai_engine.generate_followup_chat_reply(
            user_query="Can my child go outside?",
            chat_history=[],
            aqi_data=aqi_data,
            impact_context="AQI 58, Moderate"
        )
        self.assertIsInstance(reply, str)
        self.assertGreater(len(reply), 20)


if __name__ == "__main__":
    unittest.main()
