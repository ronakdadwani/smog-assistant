---
trigger: always_on
description: Core architecture and safety rules for the Winter Smog GenAI Assistant
---
- Always use the official `google-genai` Python SDK (`from google import genai`), never the deprecated `google-generativeai` library.
- Keep all secrets (`GEMINI_API_KEY`, `WAQI_API_TOKEN`) in `.env` and ensure `.env` is listed in `.gitignore`.
- Never let the LLM invent emission or health math; compute CO2 savings and PM2.5 exposure estimates deterministically in `impact_calc.py` and pass those verified figures into the prompt.
- Always request structured JSON output from Gemini so the UI renders clean cards instead of raw text walls.
- Include a brief non-medical guidance disclaimer in the UI.
