let map;
let marker;

const $ = (id) => document.getElementById(id);

function aqiLabel(value) {
  if (value == null) return "—";
  if (value <= 50) return "Good";
  if (value <= 100) return "Moderate";
  if (value <= 150) return "Unhealthy for Sensitive Groups";
  if (value <= 200) return "Unhealthy";
  if (value <= 300) return "Very Unhealthy";
  return "Hazardous";
}

function weatherLabel(code) {
  const map = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle",
    53: "Moderate drizzle", 55: "Dense drizzle", 61: "Slight rain",
    63: "Moderate rain", 65: "Heavy rain", 71: "Slight snow",
    73: "Moderate snow", 75: "Heavy snow", 80: "Rain showers",
    81: "Moderate rain showers", 82: "Violent rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail"
  };
  return map[code] || "Unknown";
}

function displayValue(value, unit = "") {
  return value == null ? "—" : `${value}${unit}`;
}

function renderNews(news) {
  const list = $("newsList");
  if (!news || news.length === 0) {
    list.innerHTML = '<div class="muted">News API not configured yet. We will connect GNews in the next step.</div>';
    $("newsStatus").textContent = "Not configured";
    return;
  }
  $("newsStatus").textContent = "Online";
  list.innerHTML = news.map((item, i) => `
    <a class="news-item" href="${item.url || '#'}" target="_blank" rel="noopener">
      <span class="rank">${i + 1}</span>
      <div>
        <strong>${item.title || "Untitled story"}</strong>
        <small>${item.source || "Unknown source"} · ${item.publishedAt ? new Date(item.publishedAt).toLocaleString() : ""}</small>
      </div>
    </a>
  `).join("");
}

function renderImage(image, place) {
  const box = $("placeImage");
  if (image && image.url) {
    box.classList.remove("empty");
    box.innerHTML = `<img src="${image.url}" alt="${place}">`;
    $("imageCaption").textContent = image.title || place;
  } else {
    box.classList.add("empty");
    box.textContent = "No place image found";
    $("imageCaption").textContent = place;
  }
}

function updateMap(lat, lon, name) {
  if (!map) {
    map = L.map("map", { zoomControl: true }).setView([lat, lon], 10);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);
  } else {
    map.setView([lat, lon], 10);
  }

  if (marker) marker.remove();
  marker = L.marker([lat, lon]).addTo(map).bindPopup(`<b>${name}</b><br>${lat.toFixed(4)}, ${lon.toFixed(4)}`).openPopup();
}

async function loadPlace(place) {
  $("briefing").textContent = "Connecting to ground-station APIs...";
  $("error").classList.add("hidden");

  try {
    const response = await fetch(`/api/search?place=${encodeURIComponent(place)}`);
    const data = await response.json();

    if (!response.ok) throw new Error(data.error || "Unable to load location.");

    const loc = data.location;
    const weather = data.weather;
    const air = data.air;

    $("placeName").textContent = loc.name;
    $("placeCountry").textContent = `${loc.state}, ${loc.country}`;
    $("country").textContent = loc.country;
    $("state").textContent = loc.state;
    $("lat").textContent = `${Number(loc.latitude).toFixed(4)}°`;
    $("lon").textContent = `${Number(loc.longitude).toFixed(4)}°`;
    $("timezone").textContent = loc.timezone;

    $("temp").textContent = displayValue(weather.temperature_2m, " °C");
    $("condition").textContent = weatherLabel(weather.weather_code);
    $("humidity").textContent = displayValue(weather.relative_humidity_2m, " %");
    $("wind").textContent = displayValue(weather.wind_speed_10m, " km/h");
    $("pressure").textContent = displayValue(weather.surface_pressure, " hPa");

    $("aqi").textContent = displayValue(air.us_aqi);
    $("aqiLabel").textContent = aqiLabel(air.us_aqi);
    $("pm25").textContent = displayValue(air.pm2_5, " µg/m³");
    $("pm10").textContent = displayValue(air.pm10, " µg/m³");
    $("no2").textContent = displayValue(air.nitrogen_dioxide, " µg/m³");
    $("so2").textContent = displayValue(air.sulphur_dioxide, " µg/m³");
    $("o3").textContent = displayValue(air.ozone, " µg/m³");

    $("coords").textContent = `${Number(loc.latitude).toFixed(4)}° N  ${Number(loc.longitude).toFixed(4)}° E`;
    updateMap(loc.latitude, loc.longitude, loc.name);

    renderImage(data.image, loc.name);
    renderNews(data.news);
    $("briefing").textContent = data.briefing;
    $("aiStatus").textContent = data.briefing.startsWith("AI briefing unavailable") || data.briefing.includes("add GROQ_API_KEY") ? "Template" : "Online";
  } catch (error) {
    $("error").textContent = error.message;
    $("error").classList.remove("hidden");
    $("briefing").textContent = "Mission briefing unavailable.";
  }
}

$("searchForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const place = $("placeInput").value.trim();
  if (place) loadPlace(place);
});

$("briefingBtn").addEventListener("click", () => {
  loadPlace($("placeInput").value.trim() || "Patna");
});

loadPlace("Patna");
