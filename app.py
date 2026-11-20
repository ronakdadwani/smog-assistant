"""
app.py - Winter Smog GenAI Assistant
Interactive Streamlit Dashboard and Community Decision-Support Application.

Architecture:
- Real-time WAQI API & calibrated simulation mode (aqi_service.py)
- Pure deterministic math for emissions, exposure & swaps (impact_calc.py)
- google-genai Pydantic-validated structured advisory & contextual chat (ai_engine.py)
- Time-blocked daily routine, budget-aware hacks, verified swaps & shareable community messages
"""

import os
import streamlit as st
from dotenv import load_dotenv

import aqi_service
import impact_calc
import ai_engine

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Winter Smog GenAI Assistant",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 12px;
        padding: 1.1rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
        margin-bottom: 0.9rem;
    }
    .metric-title {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #6c757d;
        margin-bottom: 0.3rem;
    }
    .metric-value {
        font-size: 1.9rem;
        font-weight: 700;
        line-height: 1.1;
        margin-bottom: 0.2rem;
    }
    .metric-sub {
        font-size: 0.82rem;
        color: #495057;
    }
    .disclaimer-banner {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeeba;
        padding: 0.85rem 1.1rem;
        border-radius: 8px;
        font-size: 0.86rem;
        margin-top: 2rem;
    }
    .routine-card {
        border-left: 4px solid #3b82f6;
        background-color: #f0f7ff;
        padding: 1rem;
        border-radius: 0 10px 10px 0;
        margin-bottom: 0.8rem;
    }
    .hack-card {
        border-left: 4px solid #10b981;
        background-color: #f0fdf4;
        padding: 1rem;
        border-radius: 0 10px 10px 0;
        margin-bottom: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("⚙️ Settings & Controls")

    # 1. City Selection
    st.subheader("📍 Target City")
    preset_cities = [
        "Delhi (Hazardous Smog)",
        "Hyderabad (Moderate Air)",
        "Mumbai (Urban Air)",
        "Bengaluru (Moderate Air)",
        "Kolkata (Winter Smog)",
        "Lahore (Hazardous Smog)",
        "Beijing (Winter Smog)",
        "London (Moderate Air)",
        "New York (Clean Air)",
        "Tokyo (Clean Air)",
        "Paris (Clean Air)",
        "Custom City Search..."
    ]
    city_choice = st.selectbox("Select location or search any city:", preset_cities, index=0)

    if city_choice == "Custom City Search...":
        selected_city = st.text_input("Enter any city worldwide (e.g. Pune, Chennai, Dubai, Chicago):", value="Pune").strip()
        if not selected_city:
            selected_city = "Pune"
    else:
        selected_city = city_choice.split(" (")[0]

    st.markdown("---")

    # 2. Household Sensitivities
    st.subheader("👨‍👩‍👧‍👦 Household Sensitivities")
    has_infants = st.checkbox("Infants / Young Children", value=True)
    has_elderly = st.checkbox("Elderly Family Members", value=False)
    has_asthma = st.checkbox("Asthma / Respiratory Conditions", value=True)
    has_heart_issue = st.checkbox("Cardiovascular Vulnerability", value=False)
    is_apartment = st.checkbox("Apartment Community / High-Rise", value=False)

    sensitivities = []
    if has_infants:
        sensitivities.append("Infants/young children with developing airways")
    if has_elderly:
        sensitivities.append("Elderly residents")
    if has_asthma:
        sensitivities.append("Active bronchial asthma")
    if has_heart_issue:
        sensitivities.append("Cardiovascular risk")
    if is_apartment:
        sensitivities.append("Apartment community resident (shared shafts, high-rise airflow)")
    household_context_str = "; ".join(sensitivities) if sensitivities else "Healthy general adults"

    st.markdown("---")

    # 3. Budget Tier
    st.subheader("💰 Budget Preference")
    budget_choice = st.radio(
        "Select air protection budget tier:",
        options=["Zero-Cost & Low-Cost DIY (<$20)", "Moderate ($20 - $80)", "Premium / Commercial"],
        index=0
    )

    st.markdown("---")

    # 4. Commute Parameters
    st.subheader("🚗 Daily Commute")
    commute_distance = st.slider("One-Way Commute Distance (km):", min_value=1.0, max_value=50.0, value=10.0, step=1.0)
    current_mode_key = st.selectbox(
        "Current Mode:",
        options=["petrol_car", "diesel_car", "motorcycle"],
        format_func=lambda x: {
            "petrol_car": "Single-Occupancy Petrol Car",
            "diesel_car": "Single-Occupancy Diesel Car",
            "motorcycle": "Two-Wheeler / Scooter / Motorcycle"
        }.get(x, x),
        index=0
    )
    alt_mode_key = st.selectbox(
        "Green Alternative Mode:",
        options=["metro", "bus", "carpool", "electric_car", "wfh", "bicycle"],
        format_func=lambda x: {
            "metro": "Electric Metro / Train",
            "bus": "City Bus Transit",
            "carpool": "Carpool (3+ people)",
            "electric_car": "Electric Car (EV)",
            "wfh": "Work From Home (Zero Commute)",
            "bicycle": "Bicycle / Walking"
        }.get(x, x),
        index=0
    )

    st.markdown("---")

    # 5. API Keys & Configuration
    st.subheader("🔑 API Configuration")
    env_gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    env_waqi_token = os.getenv("WAQI_API_TOKEN", "").strip()

    gemini_key_input = st.text_input(
        "Gemini API Key:",
        value=env_gemini_key if env_gemini_key and env_gemini_key != "your_gemini_api_key_here" else "",
        type="password",
        help="Free key from Google AI Studio (leave empty to run in calibrated offline mode)"
    )
    waqi_token_input = st.text_input(
        "WAQI API Token:",
        value=env_waqi_token if env_waqi_token and env_waqi_token != "your_waqi_api_token_here" else "",
        type="password",
        help="Free token from aqicn.org/api (leave empty to use calibrated simulation mode)"
    )

    if gemini_key_input:
        st.success("Gemini API Connected")
    else:
        st.info("Gemini Offline Schema Mode")

    if waqi_token_input:
        st.success("WAQI Live Sensor Connected")
    else:
        st.info("Calibrated Simulation Mode")


# --- DATA PIPELINE: AQI & DETERMINISTIC CALCULATIONS ---

# 1. Real-time or Fallback AQI
aqi_data = aqi_service.get_city_aqi(selected_city, api_token=waqi_token_input)

# 2. Deterministic Berkeley Earth Cigarette Equivalence & Safe Workout Limits
cigs_data = impact_calc.calculate_cigarette_equivalent(aqi_data["pm25"], exposure_hours=24.0)
safe_time_data = impact_calc.calculate_safe_outdoor_time(aqi_data["aqi"])

# 3. Documented Swaps Summary (Exact weekly CO2 saved & PM2.5 exposure reduction %)
swaps_data = impact_calc.get_all_swaps_summary(
    commute_km=commute_distance,
    transit_alt=alt_mode_key,
    waste_kg=10.0
)

# 4. Generate Structured Advisory via Gemini
advisory_plan = ai_engine.generate_structured_advisory(
    aqi_data=aqi_data,
    swaps_data=swaps_data,
    cigarette_data=cigs_data,
    safe_time_data=safe_time_data,
    household_context=household_context_str,
    budget_tier=budget_choice,
    api_key=gemini_key_input
)


# --- MAIN UI VIEW ---

st.title("🌫️ Winter Smog GenAI Assistant")
st.markdown(
    "A science-backed decision-support system helping families and communities "
    "navigate hazardous urban air pollution through deterministic math and structured GenAI guidance."
)

if aqi_data.get("is_mock"):
    st.info(f"ℹ️ **{aqi_data.get('status_note')}**")

# Hero Status Banner
sev_color = aqi_data.get("severity_color", aqi_data.get("category_color", "#FF0000"))
txt_color = aqi_data.get("text_color", "#ffffff")
sev_label = aqi_data.get("severity_label", aqi_data.get("category", "Unhealthy"))

st.markdown(
    f"""
    <div style="background-color: {sev_color}; color: {txt_color}; border-radius: 12px; padding: 1.3rem; margin-bottom: 1.4rem;">
        <div style="font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.9;">
            Live Sensor Reading • {aqi_data['city']}
        </div>
        <div style="display: flex; align-items: baseline; gap: 1rem; margin-top: 0.3rem;">
            <span style="font-size: 3.1rem; font-weight: 800;">AQI {aqi_data['aqi']}</span>
            <span style="font-size: 1.6rem; font-weight: 600;">{sev_label}</span>
        </div>
        <div style="font-size: 1rem; margin-top: 0.4rem; opacity: 0.95;">
            {aqi_data.get('alert', '')}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Top Metrics Row
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">PM2.5 Fine Particles</div>
        <div class="metric-value">{aqi_data['pm25']} <span style="font-size: 0.9rem; font-weight: normal;">µg/m³</span></div>
        <div class="metric-sub">WHO safe guideline: 15 µg/m³</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">PM10 Coarse Dust</div>
        <div class="metric-value">{aqi_data['pm10']} <span style="font-size: 0.9rem; font-weight: normal;">µg/m³</span></div>
        <div class="metric-sub">Dominant Pollutant: <strong>{aqi_data['dominant_pollutant'].upper()}</strong></div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Inhaled Toxic Load</div>
        <div class="metric-value" style="color: #c9302c;">🚬 {cigs_data['equivalent_cigarettes']} <span style="font-size: 0.9rem; font-weight: normal;">cigs/day</span></div>
        <div class="metric-sub">{cigs_data['description']}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Safe Workout Window</div>
        <div class="metric-value" style="color: #ec971f;">⏱️ {safe_time_data['sensitive_groups_minutes']}m <span style="font-size: 0.9rem; font-weight: normal;">(sensitive)</span></div>
        <div class="metric-sub">General adults: {safe_time_data['general_public_minutes']} mins</div>
    </div>
    """, unsafe_allow_html=True)


# --- TABBED OUTPUT CARDS ---
st.markdown("---")
st.subheader("📋 Personalized Smog Protection & Climate Action Plan")
st.info(f"**{advisory_plan.get('severity_headline')}**\n\n{advisory_plan.get('executive_summary')}")

tab1, tab2, tab3, tab4 = st.tabs([
    "🕒 Daily Routine (Time-Blocked)",
    "💡 Indoor Air Hacks (Budget-Aware)",
    "🔄 Sustainable Swaps & Impact",
    "📢 Community Action (Shareable)"
])

# TAB 1: Daily Routine
with tab1:
    st.markdown("#### Time-Blocked Low-Emission Schedule")
    st.caption("Plan your day around winter nocturnal thermal inversions and peak smog dispersal windows.")
    for block in advisory_plan.get("daily_routine", []):
        st.markdown(f"""
        <div class="routine-card">
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <strong style="font-size: 1.15rem; color: #1e3a8a;">🕒 {block.get('time_window')}</strong>
                <span style="font-size: 0.82rem; font-weight: 600; color: #475569; background: #e2e8f0; padding: 0.2rem 0.5rem; border-radius: 6px;">
                    {block.get('smog_condition')}
                </span>
            </div>
            <div style="margin-top: 0.5rem; font-size: 0.95rem; color: #1e293b;">
                <strong>Guidance:</strong> {block.get('activity_guidance')}
            </div>
            <div style="margin-top: 0.3rem; font-size: 0.88rem; color: #334155;">
                <strong>Transit & Air Tip:</strong> {block.get('ventilation_or_transit_tip')}
            </div>
        </div>
        """, unsafe_allow_html=True)

# TAB 2: Indoor Air Hacks
with tab2:
    st.markdown(f"#### Budget-Friendly Indoor Air Defense ({budget_choice})")
    st.caption("Practical techniques to reduce indoor particulate penetration without expensive installations.")
    for hack in advisory_plan.get("indoor_air_hacks", []):
        st.markdown(f"""
        <div class="hack-card">
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <strong style="font-size: 1.15rem; color: #065f46;">🛠️ {hack.get('hack_title')}</strong>
                <span style="font-size: 0.82rem; font-weight: 600; color: #047857; background: #dcfce7; padding: 0.2rem 0.5rem; border-radius: 6px;">
                    {hack.get('budget_level')}
                </span>
            </div>
            <div style="margin-top: 0.5rem; font-size: 0.95rem; color: #0f172a;">
                <strong>Instructions:</strong> {hack.get('instructions')}
            </div>
            <div style="margin-top: 0.35rem; font-size: 0.88rem; color: #166534;">
                <strong>Air Quality Benefit:</strong> {hack.get('expected_benefit')}
            </div>
        </div>
        """, unsafe_allow_html=True)

# TAB 3: Sustainable Swaps
with tab3:
    st.markdown("#### Documented Daily Mitigation Swaps")
    st.caption("Each swap pairs verified numbers from impact_calc.py with clear scientific explanations.")
    for sw in advisory_plan.get("sustainable_swaps", []):
        st.markdown(f"""
        <div class="metric-card" style="margin-bottom: 0.9rem;">
            <div style="font-size: 1.15rem; font-weight: 700; color: #1f2937;">{sw.get('swap_name')}</div>
            <div style="display: flex; gap: 2.5rem; margin-top: 0.5rem; align-items: center;">
                <div>
                    <span style="font-size: 0.78rem; color: #6b7280; text-transform: uppercase;">Weekly CO₂ Saved</span><br/>
                    <strong style="font-size: 1.35rem; color: #059669;">🌱 {sw.get('weekly_co2_saved_kg')} kg</strong>
                </div>
                <div>
                    <span style="font-size: 0.78rem; color: #6b7280; text-transform: uppercase;">PM2.5 Exposure Reduction</span><br/>
                    <strong style="font-size: 1.35rem; color: #2563eb;">🛡️ {sw.get('pm25_reduction_pct')}%</strong>
                </div>
            </div>
            <div style="margin-top: 0.6rem; padding-top: 0.6rem; border-top: 1px solid #e5e7eb; font-size: 0.92rem; color: #374151;">
                <strong>Why this works:</strong> {sw.get('why_this_works')}
            </div>
        </div>
        """, unsafe_allow_html=True)

# TAB 4: Community Action
with tab4:
    ca = advisory_plan.get("community_action", {})
    st.markdown(f"#### {ca.get('title', 'Community Clean Air Initiative')}")
    st.markdown(f"**Target Goal:** {ca.get('action_goal', 'Reduce community particulate exposure')}")
    st.markdown("Click below to copy this message into your neighborhood WhatsApp, school forum, or Slack group:")

    st.text_area(
        label="Copy-Pasteable Community Message",
        value=ca.get("shareable_message", ""),
        height=210
    )


# --- FOLLOW-UP CONVERSATIONAL CHAT ---
st.markdown("---")
st.subheader("💬 Ask the Winter Smog Assistant")
st.caption("Ask specific follow-up questions for your family, DIY air filters, child safety, or school transit.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": f"Hello! I am ready to help you navigate winter smog in **{aqi_data['city']}**. You can ask about DIY Corsi-Rosenthal box construction, school recess safety for asthmatics, or air purifier filter maintenance."
        }
    ]

# Render existing chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User prompt handling
if prompt := st.chat_input("e.g. How do I build a Corsi-Rosenthal box on a tight budget?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    context_str = (
        f"City: {aqi_data['city']}, AQI: {aqi_data['aqi']} ({sev_label}), "
        f"PM2.5: {aqi_data['pm25']} ug/m3, Equivalent Cigarettes: {cigs_data['equivalent_cigarettes']}, "
        f"Household: {household_context_str}, Budget: {budget_choice}."
    )

    with st.chat_message("assistant"):
        with st.spinner("Analyzing guidance..."):
            reply = ai_engine.generate_followup_chat_reply(
                user_query=prompt,
                chat_history=st.session_state.messages[:-1],
                aqi_data=aqi_data,
                impact_context=context_str,
                api_key=gemini_key_input
            )
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})


# --- FOOTER: MANDATORY NON-MEDICAL DISCLAIMER ---
st.markdown(
    f"""
    <div class="disclaimer-banner">
        <strong>⚠️ Non-Medical Guidance Disclaimer:</strong> {advisory_plan.get('disclaimer')}
        The data, equivalent cigarette comparisons, and GenAI recommendations presented in this application are intended solely for general environmental awareness, community risk reduction, and public health education. They do not constitute clinical diagnoses, individualized medical advice, or prescriptions. Individuals with pre-existing cardiopulmonary disorders, respiratory illnesses, pregnant individuals, and guardians of infants should consult licensed medical physicians for clinical guidance.
    </div>
    """,
    unsafe_allow_html=True
)
