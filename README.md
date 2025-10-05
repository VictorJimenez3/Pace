# Pace

Pace helps you design a sustainable cadence across your week by combining reflective voice notes, stress scoring, pacing rituals, and Google Calendar automation.

## Features

- 🔐 **Google sign-in landing page** that introduces the Pace flow and routes returning users directly to their next best action.
- 🎤 **Weekly Vent** page with in-browser audio capture, ElevenLabs transcription, and placeholder insight prompts for downstream agents.
- 📊 **Stress Score** page that quantifies load, interprets the results, and can request tailored strategies.
- 🧭 **Pacing Advice** hub preloaded with rituals plus a local draft planner ready to sync with an assistant.
- 📅 **Calendar integration** to review upcoming events, add restorative blocks, and refresh break suggestions.

## Getting started

```powershell
pip install -r backend/requirements.txt
python backend/app.py
```

Create a `.env` file with your API keys (ElevenLabs, etc.) and provide valid Google OAuth client secrets plus Firebase credentials in the `backend/` directory. Then visit `http://localhost:5000`.

## Roadmap

- Swap placeholder `/api/insights` responses with your production LLM/agent pipeline.
- Store stress scores and pacing plans in Firestore for longitudinal tracking.
- Feed agent-generated breaks directly into the calendar page for one-click scheduling.

Pace keeps you ambitious without burning out—iterate and make it yours.
