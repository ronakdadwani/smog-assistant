"""
test_scenarios.py - Automated scenario runner verifying both prompt scenarios.
Scenario 1: Delhi with severe smog, kids at home, petrol car commute, low budget.
Scenario 2: Hyderabad with moderate AQI, two-wheeler commute, apartment community.
"""

import sys
import unittest
import aqi_service
import impact_calc
import ai_engine


class TestScenarios(unittest.TestCase):
    def test_scenario_1_delhi_severe_smog(self):
        print("\n--- Testing Scenario 1: Delhi (Severe Smog) ---")
        # 1. AQI Fetch
        aqi_data = aqi_service.get_city_aqi("Delhi")
        self.assertIn(aqi_data["severity_label"], ["Hazardous", "Very Unhealthy", "Unhealthy"])
        self.assertGreater(aqi_data["aqi"], 100)
        self.assertGreater(aqi_data["pm25"], 50)
        print(f"AQI: {aqi_data['aqi']} ({aqi_data['severity_label']}), PM2.5: {aqi_data['pm25']} ug/m3")

        # 2. Deterministic impact math
        cigs = impact_calc.calculate_cigarette_equivalent(aqi_data["pm25"])
        self.assertGreater(cigs["equivalent_cigarettes"], 10.0)
        print(f"Inhaled toxic equivalent: {cigs['equivalent_cigarettes']} cigs/day ({cigs['description']})")

        safe_time = impact_calc.calculate_safe_outdoor_time(aqi_data["aqi"])
        self.assertEqual(safe_time["sensitive_groups_minutes"], 0)
        self.assertEqual(safe_time["general_public_minutes"], 0)

        # Commute: Petrol car vs metro
        swaps = impact_calc.get_all_swaps_summary(commute_km=15.0, transit_alt="metro", waste_kg=10.0)
        transit_swap = next(s for s in swaps if s["category"] == "transit")
        # 30 km roundtrip * 5 days = 150 km/week
        # 150 * (0.192 - 0.028) = 24.6 kg CO2 saved
        self.assertEqual(transit_swap["weekly_co2_saved_kg"], 24.6)
        self.assertEqual(transit_swap["pm25_exposure_reduction_pct"], 70.0)
        print(f"Transit Swap Saved: {transit_swap['weekly_co2_saved_kg']} kg CO2/wk, {transit_swap['pm25_exposure_reduction_pct']}% PM2.5 reduction")

        # 3. AI Advisory with low budget and kids at home
        advisory = ai_engine.generate_structured_advisory(
            aqi_data=aqi_data,
            swaps_data=swaps,
            cigarette_data=cigs,
            safe_time_data=safe_time,
            household_context="Infants and young children at home",
            budget_tier="Zero-Cost & Low-Cost DIY (<$20)"
        )

        self.assertIn("daily_routine", advisory)
        self.assertIn("indoor_air_hacks", advisory)
        self.assertIn("sustainable_swaps", advisory)
        self.assertIn("community_action", advisory)
        self.assertIn("disclaimer", advisory)

        # Verify low budget hacks exist
        hack_titles = [h["hack_title"] for h in advisory["indoor_air_hacks"]]
        print(f"Budget-Aware Hacks: {hack_titles}")
        self.assertTrue(any("Corsi-Rosenthal" in h or "Sealing" in h or "Mopping" in h for h in hack_titles))

        # Verify exact math was paired in sustainable swaps
        paired_transit = next(s for s in advisory["sustainable_swaps"] if "metro" in s["swap_name"].lower() or "transit" in s["swap_name"].lower() or "car" in s["swap_name"].lower())
        self.assertEqual(paired_transit["weekly_co2_saved_kg"], 24.6)
        self.assertEqual(paired_transit["pm25_reduction_pct"], 70.0)
        self.assertIn("24.6", paired_transit["why_this_works"])
        print(f"Paired Swap Explanation: {paired_transit['why_this_works']}")
        print("Scenario 1 verified successfully!\n")

    def test_scenario_2_hyderabad_moderate_smog(self):
        print("\n--- Testing Scenario 2: Hyderabad (Moderate AQI) ---")
        # 1. AQI Fetch
        aqi_data = aqi_service.get_city_aqi("Hyderabad")
        self.assertEqual(aqi_data["severity_label"], "Moderate")
        self.assertLessEqual(aqi_data["aqi"], 100)
        print(f"AQI: {aqi_data['aqi']} ({aqi_data['severity_label']}), PM2.5: {aqi_data['pm25']} ug/m3")

        # 2. Deterministic impact math
        cigs = impact_calc.calculate_cigarette_equivalent(aqi_data["pm25"])
        print(f"Inhaled toxic equivalent: {cigs['equivalent_cigarettes']} cigs/day")

        safe_time = impact_calc.calculate_safe_outdoor_time(aqi_data["aqi"])
        self.assertGreater(safe_time["general_public_minutes"], 100)

        # Commute: Two-wheeler (motorcycle) vs metro
        # 12 km roundtrip = 24 km/day * 5 days = 120 km/week
        # Motorcycle: 0.103 kg CO2/km, Metro: 0.028 kg CO2/km
        # Saved: 120 * (0.103 - 0.028) = 9.0 kg CO2/week
        motorcycle_swap = impact_calc.calculate_transit_swap(
            distance_km=12.0,
            current_mode="motorcycle",
            alternative_mode="metro",
            days_per_week=5,
            round_trip=True
        )
        self.assertEqual(motorcycle_swap["weekly_co2_saved_kg"], 9.0)
        print(f"Motorcycle -> Metro Saved: {motorcycle_swap['weekly_co2_saved_kg']} kg CO2/week, {motorcycle_swap['pm25_exposure_reduction_pct']}% PM2.5 reduction")

        # 3. AI Advisory for apartment community
        swaps = [motorcycle_swap, impact_calc.calculate_cooking_swap(2), impact_calc.calculate_waste_burning_swap(5.0)]
        advisory = ai_engine.generate_structured_advisory(
            aqi_data=aqi_data,
            swaps_data=swaps,
            cigarette_data=cigs,
            safe_time_data=safe_time,
            household_context="Apartment community resident (shared shafts, high-rise airflow)",
            budget_tier="Moderate ($20 - $80)"
        )

        self.assertIn("daily_routine", advisory)
        self.assertIn("indoor_air_hacks", advisory)
        self.assertIn("community_action", advisory)
        print(f"Community Action Goal: {advisory['community_action']['action_goal']}")
        print("Scenario 2 verified successfully!\n")


if __name__ == "__main__":
    unittest.main()
