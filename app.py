import os
from urllib.parse import quote

import requests
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from telemetry import generate_telemetry

load_dotenv()

app = Flask(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WIKI_SEARCH_URL = "https://en.wikipedia.org/w/rest.php/v1/search/page"
GNEWS_URL = "https://gnews.io/api/v4/search"

TIMEOUT = 12


def get_location(place):
    response = requests.get(
        GEOCODING_URL,
        params={
            "name": place,
            "count": 1,
            "language": "en",
            "format": "json",
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    results = response.json().get("results", [])
    if not results:
        raise ValueError(f"No location found for '{place}'")

    item = results[0]
    return {
        "name": item.get("name", place),
        "latitude": item["latitude"],
        "longitude": item["longitude"],
        "country": item.get("country", "Unknown"),
        "country_code": item.get("country_code", ""),
        "state": item.get("admin1", "Unknown"),
        "timezone": item.get("timezone", "Unknown"),
    }


def get_weather(latitude, longitude):
    response = requests.get(
        WEATHER_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,relative_humidity_2m,"
                "apparent_temperature,weather_code,wind_speed_10m,"
                "surface_pressure,visibility"
            ),
            "timezone": "auto",
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json().get("current", {})


def get_air_quality(latitude, longitude):
    response = requests.get(
        AIR_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "us_aqi,pm2_5,pm10,nitrogen_dioxide,sulphur_dioxide,ozone",
            "timezone": "auto",
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json().get("current", {})

def get_place_image(place):
    try:
        response = requests.get(
            WIKI_SEARCH_URL,
            params={"q": place, "limit": 1},
            headers={"User-Agent": "SatelliteGroundStation/1.0"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()

        pages = response.json().get("pages", [])

        if not pages:
            return {"url": None, "title": None, "description": None}

        page = pages[0]
        title = page.get("title")

        # Ask Wikimedia for a larger image
        image_response = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "prop": "pageimages",
                "titles": title,
                "piprop": "thumbnail",
                "pithumbsize": 1200,
            },
            headers={"User-Agent": "SatelliteGroundStation/1.0"},
            timeout=TIMEOUT,
        )
        image_response.raise_for_status()

        data = image_response.json()
        pages_data = data.get("query", {}).get("pages", {})

        image_url = None

        for page_data in pages_data.values():
            thumbnail = page_data.get("thumbnail", {})
            image_url = thumbnail.get("source")
            break

        return {
            "url": image_url,
            "title": title,
            "description": page.get("description"),
        }

    except requests.RequestException:
        pass

    return {
        "url": None,
        "title": None,
        "description": None,
    }

def get_news(place):
    api_key = os.getenv("GNEWS_API_KEY")
    if not api_key:
        return []

    try:
        response = requests.get(
            GNEWS_URL,
            params={
                "q": f'"{place}"',
                "lang": "en",
                "max": 5,
                "apikey": api_key,
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        articles = response.json().get("articles", [])
        return [
            {
                "title": article.get("title"),
                "source": (article.get("source") or {}).get("name"),
                "publishedAt": article.get("publishedAt"),
                "url": article.get("url"),
                "image": article.get("image"),
            }
            for article in articles[:5]
        ]
    except requests.RequestException:
        return []


def get_ai_briefing(location, weather, air, news):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        aqi = air.get("us_aqi")
        temp = weather.get("temperature_2m")
        return (
            f"{location['name']} is currently at {temp}°C with a U.S. AQI of "
            f"{aqi}. This dashboard is using live API data; add GROQ_API_KEY "
            f"to generate the AI mission briefing."
        )

    try:
        from groq import Groq

        client = Groq(api_key=api_key)
        news_text = "\n".join(
            f"- {item.get('title', '')} ({item.get('source', '')})"
            for item in news
        ) or "No local news API data is configured."

        prompt = f"""
Create a concise 3-4 sentence mission briefing for a satellite ground station dashboard.

Location:
- Place: {location['name']}
- State: {location['state']}
- Country: {location['country']}
- Latitude: {location['latitude']}
- Longitude: {location['longitude']}

Weather:
- Temperature: {weather.get('temperature_2m')}
- Humidity: {weather.get('relative_humidity_2m')}
- Wind: {weather.get('wind_speed_10m')} km/h

Air quality:
- U.S. AQI: {air.get('us_aqi')}
- PM2.5: {air.get('pm2_5')}
- PM10: {air.get('pm10')}

Recent news:
{news_text}

Use only the supplied facts. Do not invent news, measurements, causes, or health advice.
"""
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": "You write concise factual dashboard briefings.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return completion.choices[0].message.content.strip()
    except Exception as exc:
        return f"AI briefing unavailable: {exc.__class__.__name__}"


def build_dashboard_data(place):
    location = get_location(place)

    try:
        weather = get_weather(
            location["latitude"],
            location["longitude"]
        )
    except requests.RequestException:
        weather = {}

    try:
        air = get_air_quality(
            location["latitude"],
            location["longitude"]
        )
    except requests.RequestException:
        air = {}

    image = get_place_image(location["name"])
    news = get_news(location["name"])
    briefing = get_ai_briefing(location, weather, air, news)

    return {
        "location": location,
        "weather": weather,
        "air": air,
        "image": image,
        "news": news,
        "briefing": briefing,
    }

@app.route("/api/telemetry")
def telemetry():
    return jsonify(generate_telemetry())

@app.route("/")
def index():
    return render_template("index.html")


@app.get("/api/search")
def api_search():
    place = request.args.get("place", "").strip()
    if not place:
        return jsonify({"error": "Enter a place name."}), 400

    try:
        return jsonify(build_dashboard_data(place))
    except requests.RequestException as exc:
        return jsonify({"error": f"External API error: {exc}"}), 502
    except (ValueError, KeyError) as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        return jsonify({"error": f"Unexpected error: {exc}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
