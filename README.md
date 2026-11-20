# 🌫️ Winter Smog GenAI Assistant

A science-backed, deterministic decision-support application built with Python, Streamlit, and Google Gemini (`google-genai` SDK) to help families, sensitive groups, and urban communities navigate hazardous winter smog emergencies safely and proactively.

---

## 🚀 Live Local Application
The Streamlit application is currently running locally:
- **Local URL:** [http://localhost:8501](http://localhost:8501)
- **Network URL:** `http://127.0.0.1:8501`

---

## 🌟 Key Architecture & Capabilities

1. **Live & Fallback AQI Service (`aqi_service.py`)**:
   - Fetches real-time $AQI$, $PM_{2.5}$, $PM_{10}$, and dominant pollutants from the [WAQI API](https://aqicn.org/api/).
   - Maps clear severity labels (`Good`, `Moderate`, `Unhealthy for Sensitive Groups`, `Unhealthy`, `Very Unhealthy`, `Hazardous`).
   - Resilient fallback simulation mode for cities like **Delhi, Hyderabad, Lahore, Beijing, London, and New York** if API tokens are omitted.

2. **Deterministic Mathematical Engine (`impact_calc.py`)**:
   - **Inhaled Toxic Load**: Scientific Berkeley Earth equivalence:
     $$\text{Equivalent Cigarettes} = \left(\frac{PM_{2.5}\ (\mu\text{g/m}^3)}{22.0}\right) \times \left(\frac{\text{Exposure Hours}}{24.0}\right)$$
   - **Safe Workout Windows**: Bracket-based limits (general public vs sensitive groups).
   - **Documented Mitigation Swaps**: Calculates exact weekly $\text{CO}_2$ saved ($\text{kg}$) and personal $\text{PM}_{2.5}$ exposure reduction ($\%$) using DEFRA, EPA AP-42, and WHO emission factors:
     - *Petrol car $\rightarrow$ Metro / Carpool*
     - *Gas $\rightarrow$ Induction Cooking*
     - *Avoiding Open Waste Burning*
     - *Indoor HEPA / DIY Corsi-Rosenthal Box-Fan Filtration*

3. **GenAI Advisory Engine (`ai_engine.py`)**:
   - Uses the official `google-genai` SDK (`from google import genai`).
   - Strict Pydantic JSON schema (`SmogAdvisoryPlan`) returning:
     - 🕒 **`daily_routine`**: Time-blocked schedule optimizing around nocturnal thermal inversion traps.
     - 💡 **`indoor_air_hacks`**: Budget-filtered indoor defense tactics (Zero-Cost sealing, DIY Corsi-Rosenthal boxes under $20).
     - 🔄 **`sustainable_swaps`**: Verified numbers paired with scientific "Why this works" explanations.
     - 📢 **`community_action`**: Ready-to-copy-paste WhatsApp / Slack / school forum message.
   - Contextual follow-up Q&A chat.

---

## 🧪 Verified Scenarios

### Scenario 1: Delhi (Severe Smog)
- **Settings:** Delhi, Infants & young children at home, Petrol car commute ($15\text{km}$ one-way), Zero-Cost / Low-Cost DIY budget (<$20).
- **Sensor Findings:** $AQI = 418$ (`Hazardous`), $PM_{2.5} = 372.5\ \mu\text{g/m}^3$.
- **Deterministic Output:**
  - 🚬 Inhaled load: **$16.93\text{ cigarettes/day}$**.
  - ⏱️ Safe outdoor physical exercise: **$0\text{ minutes}$** (emergency conditions).
  - 🌱 Switching to Metro: Saves **$24.60\text{ kg CO}_2/\text{week}$** and cuts personal in-transit particulate exposure by **$70.0\%$**.
- **GenAI Plan:** Recommends DIY Corsi-Rosenthal box cleaner ($CADR > 300\text{ CFM}$), damp towel door threshold sealing, positive pressure clean sanctuary bedroom, and zero morning physical activity.

### Scenario 2: Hyderabad (Moderate Smog)
- **Settings:** Hyderabad, Apartment community resident, Two-wheeler (motorcycle) commute ($12\text{km}$ one-way), Moderate budget ($20–$80).
- **Sensor Findings:** $AQI = 88$ (`Moderate`), $PM_{2.5} = 29.5\ \mu\text{g/m}^3$.
- **Deterministic Output:**
  - 🚬 Inhaled load: **$1.34\text{ cigarettes/day}$**.
  - ⏱️ Safe workout window: **$>180\text{ minutes}$**.
  - 🌱 Two-wheeler to Metro: Saves **$9.00\text{ kg CO}_2/\text{week}$** with a **$70.0\%$** personal exposure reduction.
- **GenAI Plan:** Targeted apartment shaft sealing, balanced cross-ventilation during afternoon hours, and a ready-to-share clean air neighborhood school run pact.

---

## 🛠️ Local Setup Instructions

### 1. Prerequisites
- Python 3.10+ (Verified on Python 3.12)
- Windows / macOS / Linux

### 2. Environment Activation & Dependencies
```powershell
# Navigate to project directory
cd C:\Users\mrced\.gemini\antigravity\scratch\smog-assistant

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install requirements (if running on a fresh clone)
pip install -r requirements.txt
```

### 3. API Keys Configuration (Optional)
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
Edit `.env`:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
WAQI_API_TOKEN=your_waqi_api_token_here
```
> **Note:** If API keys are omitted, the application runs automatically in calibrated simulation mode with pre-loaded profiles for Delhi, Hyderabad, Lahore, Beijing, London, and New York.

### 4. Running the Streamlit App
```powershell
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 5. Running the Automated Test Suite
```powershell
# Run swap and API unit tests
python -m unittest discover -s tests -p "test_*.py" -v

# Run end-to-end scenario runner
python test_scenarios.py
```

---

## ⚠️ Non-Medical Guidance Disclaimer
The calculations, equivalent cigarette comparisons, and GenAI recommendations provided by this application are for general environmental awareness, community risk reduction, and public health education only. They do not constitute clinical diagnoses, individualized medical advice, or prescriptions. Consult licensed medical professionals for clinical guidance.
