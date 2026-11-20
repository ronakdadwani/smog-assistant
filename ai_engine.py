"""
ai_engine.py - GenAI Advisory Engine powered by the official google-genai SDK.

Strict Guardrails Enforced:
1. Modern SDK: Uses `from google import genai` and `genai.Client`.
2. Structured JSON Output: Enforces Pydantic schema returning:
   - daily_routine (time-blocked low-emission schedule)
   - indoor_air_hacks (budget-aware)
   - sustainable_swaps (each paired with a clear "Why this works" explanation using impact_calc figures)
   - community_action (ready-to-share neighborhood / school carpool message)
3. Deterministic Numbers: Feeds verified figures from impact_calc.py into the prompt.
4. Non-Medical Disclaimer: Emits non-medical safety disclosures in every plan.
5. Interactive Chat Session: Contextual follow-up Q&A retaining conversation history.
"""

import os
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class RoutineBlock(BaseModel):
    time_window: str = Field(description="Time block e.g., 'Early Morning (06:00 - 09:00)', 'Midday (11:00 - 15:00)'")
    smog_condition: str = Field(description="Expected inversion/pollution behavior (e.g. Peak winter smog trap, Dispersal window)")
    activity_guidance: str = Field(description="Concrete guidance for exercise, school runs, or errands")
    ventilation_or_transit_tip: str = Field(description="Commute or window ventilation protocol for this window")


class IndoorAirHack(BaseModel):
    hack_title: str = Field(description="Name of the budget-friendly hack")
    budget_level: str = Field(description="'Zero-Cost', 'Low-Cost DIY (<$20)', or 'Moderate ($20-$80)'")
    instructions: str = Field(description="Practical step-by-step instructions")
    expected_benefit: str = Field(description="Expected indoor PM2.5 or airflow improvement")


class SustainableSwapAdvice(BaseModel):
    swap_name: str = Field(description="Name of swap (e.g. Petrol Car -> Metro, Gas -> Induction, Avoiding Open Burning, HEPA Filtration)")
    weekly_co2_saved_kg: float = Field(description="Exact weekly kg CO2 saved from impact_calc")
    pm25_reduction_pct: float = Field(description="Exact PM2.5 exposure reduction percentage from impact_calc")
    why_this_works: str = Field(description="Scientific and quantitative explanation connecting the verified numbers to air quality")


class CommunityAction(BaseModel):
    title: str = Field(description="Catchy initiative title (e.g. 'Neighborhood School Carpool & Anti-Idling Pact')")
    shareable_message: str = Field(description="Ready-to-copy-paste WhatsApp / Slack / School community message with emojis and clear action points")
    action_goal: str = Field(description="Concrete collective target (e.g. 'Eliminate 40 cold-start car drop-offs at school gates')")


class SmogAdvisoryPlan(BaseModel):
    severity_headline: str = Field(description="Actionable headline characterizing current smog risk")
    executive_summary: str = Field(description="Concise 2-sentence summary tailored to household sensitivities and budget")
    daily_routine: List[RoutineBlock] = Field(description="Time-blocked low-emission and low-exposure schedule")
    indoor_air_hacks: List[IndoorAirHack] = Field(description="Budget-aware indoor air quality improvement tactics")
    sustainable_swaps: List[SustainableSwapAdvice] = Field(description="Swaps with verified impact figures and 'Why this works' explanations")
    community_action: CommunityAction = Field(description="Ready-to-share message for neighborhood or school carpool")
    disclaimer: str = Field(
        default="Informational guidance only. Not medical advice. Consult qualified healthcare professionals for medical conditions.",
        description="Mandatory non-medical guidance statement"
    )


def _get_api_client(api_key: Optional[str] = None):
    """Instantiates the official Google GenAI client."""
    key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "your_gemini_api_key_here":
        return None
    try:
        from google import genai
        return genai.Client(api_key=key)
    except Exception:
        return None


def generate_structured_advisory(
    aqi_data: Dict[str, Any],
    swaps_data: List[Dict[str, Any]],
    cigarette_data: Dict[str, Any],
    safe_time_data: Dict[str, Any],
    household_context: str = "General urban household",
    budget_tier: str = "Low-Cost DIY",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a structured, validated smog action plan using Gemini (google-genai).
    Feeds exact deterministic numbers from impact_calc.py into prompt.
    """
    client = _get_api_client(api_key)

    if not client:
        return _get_simulated_advisory_plan(aqi_data, swaps_data, cigarette_data, safe_time_data, household_context, budget_tier)

    from google.genai import types

    # Format verified swaps for prompt
    swaps_prompt_lines = []
    for sw in swaps_data:
        swaps_prompt_lines.append(
            f"- {sw.get('swap_name')}: Saves exactly {sw.get('weekly_co2_saved_kg')} kg CO2/week with {sw.get('pm25_exposure_reduction_pct')}% PM2.5 exposure reduction. Details: {sw.get('description', '')}"
        )
    swaps_text = "\n".join(swaps_prompt_lines)

    system_prompt = (
        "You are an expert environmental health scientist and community resilience advisor "
        "specializing in urban winter smog emergencies. "
        "You provide actionable, practical, and empathetic guidance to families and communities.\n"
        "STRICT RULES:\n"
        "1. Never invent or recalculate numerical emissions or health equivalence figures; "
        "always use the exact numbers supplied in the prompt.\n"
        "2. For each sustainable swap in `sustainable_swaps`, you MUST provide a detailed 'Why this works' "
        "explanation that cites the EXACT weekly CO2 saved and PM2.5 exposure reduction percentage provided.\n"
        "3. Indoor air hacks must specifically address the user's budget tier.\n"
        "4. Include a ready-to-share community action message formatted with emojis and bullets for WhatsApp/Slack.\n"
        "5. Emphasize that all guidance is non-medical public information."
    )

    prompt = f"""
    Current Environmental Sensor Readings for {aqi_data.get('city', 'Selected City')}:
    - Air Quality Index (AQI): {aqi_data.get('aqi')} ({aqi_data.get('severity_label', aqi_data.get('category'))})
    - Dominant Pollutant: {aqi_data.get('dominant_pollutant', 'pm25').upper()}
    - PM2.5 Concentration: {aqi_data.get('pm25')} µg/m³
    - PM10 Concentration: {aqi_data.get('pm10')} µg/m³
    - Temperature: {aqi_data.get('temperature')}°C, Humidity: {aqi_data.get('humidity')}%

    VERIFIED DETERMINISTIC CALCULATIONS (DO NOT ALTER OR INVENT NUMBERS):
    - Inhaled toxic particulate equivalent: {cigarette_data.get('equivalent_cigarettes')} cigarettes/day ({cigarette_data.get('description')}).
    - Safe outdoor activity limit (General Public): {safe_time_data.get('general_public_minutes')} minutes.
    - Safe outdoor activity limit (Sensitive Groups): {safe_time_data.get('sensitive_groups_minutes')} minutes.
    
    VERIFIED SWAP DATA TO PAIR:
    {swaps_text}

    User Household Profile:
    - Sensitivities: {household_context}
    - Budget Preference: {budget_tier}

    Generate a complete, structured action advisory adhering strictly to the SmogAdvisoryPlan JSON schema.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=SmogAdvisoryPlan,
                temperature=0.25
            )
        )
        return json.loads(response.text)
    except Exception as exc:
        simulated = _get_simulated_advisory_plan(aqi_data, swaps_data, cigarette_data, safe_time_data, household_context, budget_tier)
        simulated["executive_summary"] += f" (Gemini API notice: {str(exc)})"
        return simulated


def generate_followup_chat_reply(
    user_query: str,
    chat_history: List[Dict[str, str]],
    aqi_data: Dict[str, Any],
    impact_context: str,
    api_key: Optional[str] = None
) -> str:
    """
    Handles interactive follow-up questions from the user with full environmental and swap context.
    """
    client = _get_api_client(api_key)
    if not client:
        return (
            "*(Operating in simulated offline mode - enter your GEMINI_API_KEY in the sidebar or .env for live Gemini answers)*\n\n"
            f"Based on the current AQI of **{aqi_data.get('aqi')}** ({aqi_data.get('severity_label', aqi_data.get('category'))}):\n"
            "- **Indoor Protection**: Keep windows tightly sealed during morning thermal inversion (6 AM - 10 AM). Run true HEPA or DIY box-fan filtration in occupied bedrooms.\n"
            "- **Masks**: Use an N95 or FFP2 respirator with tight seal whenever stepping outside.\n"
            "- **Vulnerable Members**: Keep asthmatic children and elderly family members indoors when AQI exceeds 150.\n\n"
            "⚠️ *Reminder: This is non-medical general guidance.*"
        )

    from google.genai import types

    sys_instruction = (
        f"You are the Winter Smog GenAI Assistant pair-programming with the user. "
        f"Location: {aqi_data.get('city')}, AQI: {aqi_data.get('aqi')} ({aqi_data.get('severity_label', aqi_data.get('category'))}), "
        f"PM2.5: {aqi_data.get('pm25')} µg/m³, Dominant: {aqi_data.get('dominant_pollutant')}. "
        f"Impact Context: {impact_context}. "
        "Answer the user's specific follow-up questions helpfully, practically, and concisely. "
        "Always remind the user that guidance is educational/non-medical."
    )

    contents = []
    for msg in chat_history[-6:]:
        contents.append(f"{msg['role'].upper()}: {msg['content']}")
    contents.append(f"USER: {user_query}")
    conversation_prompt = "\n\n".join(contents)

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=conversation_prompt,
            config=types.GenerateContentConfig(
                system_instruction=sys_instruction,
                temperature=0.3
            )
        )
        return response.text
    except Exception as exc:
        return f"Unable to generate response via Gemini API ({str(exc)}). Please check your GEMINI_API_KEY."


def _get_simulated_advisory_plan(
    aqi_data: Dict[str, Any],
    swaps_data: List[Dict[str, Any]],
    cigarette_data: Dict[str, Any],
    safe_time_data: Dict[str, Any],
    household_context: str,
    budget_tier: str
) -> Dict[str, Any]:
    """Generates a high-quality schema-compliant fallback when API key is missing."""
    aqi = aqi_data.get("aqi", 150)
    city = aqi_data.get("city", "Selected Location")
    cigs = cigarette_data.get("equivalent_cigarettes", 1.0)
    sev = aqi_data.get("severity_label", "Unhealthy")

    # Time-blocked schedule
    routine = [
        {
            "time_window": "Early Morning (06:00 - 09:30)",
            "smog_condition": "Severe nocturnal thermal inversion; particulate matter trapped at ground level.",
            "activity_guidance": "Strictly cancel all outdoor morning jogging, cycling, and walks. Keep children indoors.",
            "ventilation_or_transit_tip": "Keep all windows sealed. If commuting, travel via closed transit (metro/bus) with fitted N95."
        },
        {
            "time_window": "Midday & Early Afternoon (11:30 - 15:00)",
            "smog_condition": "Solar heating temporarily lifts thermal inversion layer, dispersing lowest ground particles.",
            "activity_guidance": f"Safest window for essential outdoor errands. Healthy individuals outdoor limit: {safe_time_data.get('general_public_minutes', 60)} mins.",
            "ventilation_or_transit_tip": "Perform brief cross-ventilation (5-10 mins) only if indoor CO2 is elevated and outdoor PM2.5 has dropped."
        },
        {
            "time_window": "Evening Rush (17:30 - 20:30)",
            "smog_condition": "Evening vehicular traffic surge combines with returning thermal cooling, spiking PM2.5 and NOx.",
            "activity_guidance": "Avoid walking near major arterial roads. Encourage indoor playtime for children.",
            "ventilation_or_transit_tip": "Car recirculate mode strictly ON. Avoid open windows in vehicles or transit."
        },
        {
            "time_window": "Night & Sleep (21:00 - 06:00)",
            "smog_condition": "Cold stillness locks in settled particulates.",
            "activity_guidance": "Sleep in rooms with active HEPA or Corsi-Rosenthal box filtration.",
            "ventilation_or_transit_tip": "Draft-seal bedroom door and window seams to maintain clean air bubble."
        }
    ]

    # Budget-aware indoor air hacks
    hacks = [
        {
            "hack_title": "Damp Towel & Foam Window Edge Sealing",
            "budget_level": "Zero-Cost",
            "instructions": "Roll damp towels or use cheap foam strips along bottom exterior door thresholds and window sill gaps where smog drafts seep in.",
            "expected_benefit": "Blocks up to 40% of ambient outdoor particulate draft intrusion without spending money."
        },
        {
            "hack_title": "DIY Corsi-Rosenthal Box Air Cleaner",
            "budget_level": "Low-Cost DIY (<$20)",
            "instructions": "Tape four standard furnace filters (MERV 13 rating) into a cube with a 20-inch box fan on top pulling air through the filters.",
            "expected_benefit": "Delivers over 300 CFM Clean Air Delivery Rate (CADR), rivaling $300 commercial HEPA purifiers at ~80% PM2.5 removal."
        },
        {
            "hack_title": "Positive Pressure Clean-Room Strategy",
            "budget_level": "Zero-Cost",
            "instructions": "Designate one central bedroom as the 'clean sanctuary'. Keep its door closed, seal windows, and run your best filter there continuously.",
            "expected_benefit": "Maintains an indoor PM2.5 level under 25 µg/m³ even when outdoor ambient AQI exceeds 300."
        },
        {
            "hack_title": "Wet Mopping & Anti-Resuspension Protocol",
            "budget_level": "Zero-Cost",
            "instructions": "Mop floors with a damp microfiber cloth instead of dry sweeping or using non-HEPA vacuum cleaners which resuspend toxic PM2.5 into breathing zones.",
            "expected_benefit": "Eliminates secondary indoor dust resuspension by up to 60%."
        }
    ]

    # Paired sustainable swaps
    paired_swaps = []
    for sw in swaps_data:
        name = sw.get("swap_name", "Swap")
        co2_saved = sw.get("weekly_co2_saved_kg", 0.0)
        pm_pct = sw.get("pm25_exposure_reduction_pct", 50.0)

        if "metro" in name.lower() or "transit" in name.lower():
            why = (
                f"Switching from solo car commuting to electric metro saves exactly {co2_saved} kg CO2 each week "
                f"while providing a {pm_pct}% personal PM2.5 exposure reduction by moving your commute out of street-level vehicle exhaust queues."
            )
        elif "cooking" in name.lower() or "induction" in name.lower():
            why = (
                f"Transitioning to induction cooking avoids {co2_saved} kg CO2 weekly from fossil methane combustion "
                f"and cuts kitchen PM2.5 exposure by {pm_pct}% by completely eliminating burner soot and nitrogen dioxide."
            )
        elif "waste" in name.lower():
            why = (
                f"Eliminating open waste burning saves {co2_saved} kg CO2 weekly and prevents localized toxic ground smoke plumes, "
                f"reducing neighborhood PM2.5 exposure by {pm_pct}%."
            )
        else:
            why = (
                f"Targeted room filtration saves {co2_saved} kg CO2 weekly compared to continuous central HVAC blower use "
                f"while slashing indoor particulate inhalation by {pm_pct}%."
            )

        paired_swaps.append({
            "swap_name": name,
            "weekly_co2_saved_kg": co2_saved,
            "pm25_reduction_pct": pm_pct,
            "why_this_works": why
        })

    # Community Action
    community = {
        "title": "🏫 Neighborhood School Run & Anti-Idling Clean Air Pact",
        "shareable_message": (
            f"🚨 *Clean Air Alert for {city} Parents & Neighbors (AQI: {aqi})* 🚨\n\n"
            f"Hi everyone! Today's air quality is in the *{sev}* zone (breathing ~{cigs} cigarettes/day outdoors). "
            f"To protect our kids' lungs at school drop-off and around our blocks, let's take two easy steps today:\n\n"
            "1️⃣ *Strict Zero Idling:* Please turn off car engines completely while waiting at the school gate or curb. Exhaust concentrates right at children's breathing height!\n"
            "2️⃣ *Neighborhood Carpool:* We have 3 open seats in our metro/carpool run this week—reply here to team up and eliminate car trips!\n"
            "3️⃣ *No Open Burning:* Please ensure no leaves or yard waste are burned.\n\n"
            "Let's work together to keep our street air breathable! 🌿😷"
        ),
        "action_goal": "Eliminate 30 idling cars around school zones and reduce neighborhood peak morning PM2.5 by 25%."
    }

    return {
        "severity_headline": f"{sev.upper()} AIR WARNING: Peak Smog Advisory for {city}",
        "executive_summary": (
            f"Outdoor air quality has reached AQI {aqi} ({sev}), creating an inhaled toxic particulate load "
            f"equivalent to ~{cigs} cigarettes per day. Given your profile ({household_context}) and {budget_tier} preference, "
            "prioritize immediate indoor clean-room protocols, zero-cost window draft sealing, and low-emission transit swaps."
        ),
        "daily_routine": routine,
        "indoor_air_hacks": hacks,
        "sustainable_swaps": paired_swaps,
        "community_action": community,
        "disclaimer": "Informational guidance only. Not medical advice. Consult qualified healthcare professionals for medical conditions."
    }
