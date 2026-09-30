# 🛰️ Satellite Ground Station

A Linux/Kali-based location intelligence dashboard with a satellite-ground-station theme.

## V1 currently includes

- Place-name search
- Latitude / longitude
- Country / state / timezone
- Live weather
- U.S. AQI
- PM2.5 / PM10 / NO2 / SO2 / O3
- Interactive map
- Wikipedia place image when available
- Black + electric-blue dashboard
- Existing satellite telemetry simulator panel

## Optional integrations

- `GNEWS_API_KEY` → five local/relevant news stories
- `GROQ_API_KEY` → AI mission briefing

Open-Meteo supplies the geocoding, weather, and air-quality data. Its current documentation exposes geocoding search, current weather variables, and current U.S. AQI/pollutant variables. https://open-meteo.com/

## Run in Kali

```bash
cd ~/satellite-ground-station
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 app.py
```

Then open:

http://127.0.0.1:5000


