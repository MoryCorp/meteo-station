"""FastAPI backend for Marine Weather Dashboard"""

import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import datetime, timedelta
from typing import Dict, Any, List

from config import STATION_ID, NEIGHBORING_STATIONS, COORDS_GAREOULT, SEUILS
from api import fetch_current, fetch_history_range, fetch_daily_summary, fetch_forecast, fetch_all_1day

app = FastAPI(title="Station météo Garéoult")

# Configuration CORS - permissif pour le développement, restrictif en prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod, tout vient du même domaine donc pas de CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware pour empêcher le cache navigateur sur les endpoints API
@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)

    # Ajouter headers anti-cache uniquement pour les endpoints /api/*
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return response

def calculate_pressure_trend(current_pressure: float, history_data: List[Dict]) -> Dict[str, Any]:
    """Calcule la tendance de pression sur 3h (36 observations de 5 minutes)"""
    if not history_data or len(history_data) < 36:
        return {"trend": "stable", "change": 0}

    # Prendre la pression d'il y a 3h (36 observations en arrière)
    try:
        three_hours_ago = history_data[-36]
        metric = three_hours_ago.get("metric", {})

        # Récupérer la pression (peut être pressureMax ou pressureMin)
        old_pressure = metric.get("pressureMax", metric.get("pressureMin", 0))

        if not old_pressure:
            return {"trend": "stable", "change": 0}

        change = current_pressure - old_pressure

        trend = "stable"
        if change < -SEUILS["pression_chute"]["danger"]:
            trend = "falling_rapidly"
        elif change < -SEUILS["pression_chute"]["attention"]:
            trend = "falling"
        elif change > SEUILS["pression_chute"]["attention"]:
            trend = "rising"

        return {"trend": trend, "change": round(change, 1)}
    except (IndexError, KeyError):
        return {"trend": "stable", "change": 0}

@app.get("/api/current")
async def get_current() -> Dict[str, Any]:
    """Récupère les observations actuelles"""
    data = await fetch_current(STATION_ID)

    if not data or "observations" not in data or len(data["observations"]) == 0:
        raise HTTPException(status_code=503, detail="No weather data available")

    obs = data["observations"][0]
    metric = obs.get("metric", {})

    # Récupérer historique du jour pour tendance pression
    history = await fetch_history_range(STATION_ID, 1)

    # L'endpoint /current retourne 'pressure' directement
    current_pressure = metric.get("pressure", 1013)
    pressure_trend = calculate_pressure_trend(current_pressure, history)

    # Récupérer données quotidiennes pour stats
    daily = await fetch_daily_summary(STATION_ID)
    daily_obs = daily.get("summaries", []) if daily else []

    # Calculer max rafale et cumul pluie sur 7 jours
    max_gust_7d = 0
    total_rain_7d = 0
    if daily_obs:
        for day in daily_obs:
            day_metric = day.get("metric", {})
            gust = day_metric.get("windgustHigh", 0) or 0
            rain = day_metric.get("precipTotal", 0) or 0
            if gust > max_gust_7d:
                max_gust_7d = gust
            total_rain_7d += rain

    return {
        "station_id": STATION_ID,
        "observation_time": obs.get("obsTimeLocal", ""),
        "current": {
            # L'endpoint /current retourne des valeurs instantanées (pas de Avg/High)
            "wind_speed": metric.get("windSpeed", 0),
            "wind_gust": metric.get("windGust", 0),
            "wind_dir": obs.get("winddir", 0),
            "temp": metric.get("temp", 0),
            "pressure": current_pressure,
            "pressure_trend": pressure_trend,
            "rain_rate": metric.get("precipRate", 0),
            "solar_radiation": obs.get("solarRadiation", 0),
            "uv": obs.get("uv", 0)
        },
        "stats_7d": {
            "max_gust": max_gust_7d,
            "total_rain": round(total_rain_7d, 1)
        },
        "seuils": SEUILS
    }

@app.get("/api/history/temperature")
async def get_temperature_history(period: str = "daily") -> Dict[str, Any]:
    """Récupère l'historique des températures

    Périodes disponibles: daily (24h), weekly (7j), monthly (30j)
    """
    days_map = {"daily": 1, "weekly": 7, "monthly": 30}
    days = days_map.get(period, 1)

    observations = await fetch_history_range(STATION_ID, days)

    # Agréger les données selon la période
    if period == "daily":
        # Données toutes les 5 minutes pour 24h (max 288 observations)
        data_points = []
        for obs in observations[-288:]:
            metric = obs.get("metric", {})
            data_points.append({
                "time": obs.get("obsTimeLocal", ""),
                "temp": metric.get("tempAvg", 0),
                "temp_high": metric.get("tempHigh", 0),
                "temp_low": metric.get("tempLow", 0)
            })
    else:
        # Agréger par jour
        daily_data = {}
        for obs in observations:
            obs_time = obs.get("obsTimeLocal", "")
            if not obs_time:
                continue

            try:
                date = obs_time.split("T")[0]  # Extraire la date
                if date not in daily_data:
                    daily_data[date] = {"temps": [], "high": [], "low": []}

                metric = obs.get("metric", {})
                temp = metric.get("tempAvg", 0)
                if temp:
                    daily_data[date]["temps"].append(temp)

                temp_high = metric.get("tempHigh", 0)
                if temp_high:
                    daily_data[date]["high"].append(temp_high)

                temp_low = metric.get("tempLow", 0)
                if temp_low:
                    daily_data[date]["low"].append(temp_low)
            except Exception:
                continue

        data_points = []
        for date in sorted(daily_data.keys()):
            temps = daily_data[date]["temps"]
            highs = daily_data[date]["high"]
            lows = daily_data[date]["low"]

            data_points.append({
                "time": date,
                "temp": round(sum(temps) / len(temps), 1) if temps else 0,
                "temp_high": max(highs) if highs else 0,
                "temp_low": min(lows) if lows else 0
            })

    return {"period": period, "data": data_points}

@app.get("/api/history/pressure")
async def get_pressure_history(period: str = "daily") -> Dict[str, Any]:
    """Récupère l'historique de la pression atmosphérique"""
    days_map = {"daily": 1, "weekly": 7, "monthly": 30}
    days = days_map.get(period, 1)

    observations = await fetch_history_range(STATION_ID, days)

    if period == "daily":
        # Données toutes les 5 minutes pour 24h (max 288 observations)
        data_points = []
        for obs in observations[-288:]:
            metric = obs.get("metric", {})
            data_points.append({
                "time": obs.get("obsTimeLocal", ""),
                "pressure": metric.get("pressureMax", 0) or metric.get("pressure", 0)
            })
    else:
        # Agréger par jour
        daily_data = {}
        for obs in observations:
            obs_time = obs.get("obsTimeLocal", "")
            if not obs_time:
                continue

            try:
                date = obs_time.split("T")[0]
                if date not in daily_data:
                    daily_data[date] = []

                metric = obs.get("metric", {})
                pressure = metric.get("pressureMax", 0) or metric.get("pressure", 0)
                if pressure:
                    daily_data[date].append(pressure)
            except Exception:
                continue

        data_points = []
        for date in sorted(daily_data.keys()):
            pressures = daily_data[date]
            data_points.append({
                "time": date,
                "pressure": round(sum(pressures) / len(pressures), 1) if pressures else 0
            })

    return {"period": period, "data": data_points}

@app.get("/api/history/wind")
async def get_wind_history(period: str = "daily") -> Dict[str, Any]:
    """Récupère l'historique du vent (vitesse et direction)"""
    days_map = {"daily": 1, "weekly": 7, "monthly": 30}
    days = days_map.get(period, 1)

    observations = await fetch_history_range(STATION_ID, days)

    if period == "daily":
        # Données toutes les 5 minutes pour 24h (max 288 observations)
        data_points = []
        for obs in observations[-288:]:
            metric = obs.get("metric", {})
            data_points.append({
                "time": obs.get("obsTimeLocal", ""),
                "wind_speed": metric.get("windspeedAvg", 0),
                "wind_gust": metric.get("windgustHigh", 0),
                "wind_dir": metric.get("winddirAvg", 0)
            })
    else:
        # Agréger par jour
        daily_data = {}
        for obs in observations:
            obs_time = obs.get("obsTimeLocal", "")
            if not obs_time:
                continue

            try:
                date = obs_time.split("T")[0]
                if date not in daily_data:
                    daily_data[date] = {"speeds": [], "gusts": [], "dirs": []}

                metric = obs.get("metric", {})

                speed = metric.get("windspeedAvg", 0)
                if speed:
                    daily_data[date]["speeds"].append(speed)

                gust = metric.get("windgustHigh", 0)
                if gust:
                    daily_data[date]["gusts"].append(gust)

                wind_dir = metric.get("winddirAvg", 0)
                if wind_dir:
                    daily_data[date]["dirs"].append(wind_dir)
            except Exception:
                continue

        data_points = []
        for date in sorted(daily_data.keys()):
            speeds = daily_data[date]["speeds"]
            gusts = daily_data[date]["gusts"]
            dirs = daily_data[date]["dirs"]

            data_points.append({
                "time": date,
                "wind_speed": round(sum(speeds) / len(speeds), 1) if speeds else 0,
                "wind_gust": max(gusts) if gusts else 0,
                "wind_dir": round(sum(dirs) / len(dirs), 0) if dirs else 0
            })

    return {"period": period, "data": data_points}

@app.get("/api/history/rain")
async def get_rain_history(period: str = "daily") -> Dict[str, Any]:
    """Récupère l'historique de la pluviométrie"""
    days_map = {"daily": 1, "weekly": 7, "monthly": 30}
    days = days_map.get(period, 1)

    observations = await fetch_history_range(STATION_ID, days)

    if period == "daily":
        # Données toutes les 5 minutes pour 24h (max 288 observations)
        data_points = []
        for obs in observations[-288:]:
            metric = obs.get("metric", {})
            data_points.append({
                "time": obs.get("obsTimeLocal", ""),
                "rain": metric.get("precipTotal", 0),
                "rain_rate": metric.get("precipRate", 0)
            })
    else:
        # Agréger par jour
        daily_data = {}
        for obs in observations:
            obs_time = obs.get("obsTimeLocal", "")
            if not obs_time:
                continue

            try:
                date = obs_time.split("T")[0]
                if date not in daily_data:
                    daily_data[date] = []

                metric = obs.get("metric", {})
                rain = metric.get("precipTotal", 0)
                if rain:
                    daily_data[date].append(rain)
            except Exception:
                continue

        data_points = []
        for date in sorted(daily_data.keys()):
            rains = daily_data[date]
            data_points.append({
                "time": date,
                "rain": round(sum(rains), 1) if rains else 0
            })

    return {"period": period, "data": data_points}

@app.get("/api/forecast")
async def get_forecast() -> Dict[str, Any]:
    """Récupère les prévisions 5 jours"""
    data = await fetch_forecast(COORDS_GAREOULT["lat"], COORDS_GAREOULT["lon"])

    if not data:
        raise HTTPException(status_code=503, detail="Forecast unavailable")

    # Formater les prévisions - l'API retourne des tableaux parallèles
    forecasts = []

    if "dayOfWeek" in data and len(data.get("dayOfWeek", [])) > 0:
        num_days = min(5, len(data.get("dayOfWeek", [])))

        for i in range(num_days):
            # Récupérer la probabilité de précipitation depuis daypart
            precip_chance = 0
            if "daypart" in data and len(data["daypart"]) > 0:
                daypart = data["daypart"][0]
                if "precipChance" in daypart and daypart["precipChance"]:
                    # Le daypart contient day et night entrelacés
                    # Index i*2 = jour, i*2+1 = nuit
                    if i * 2 < len(daypart["precipChance"]) and daypart["precipChance"][i * 2] is not None:
                        precip_chance = daypart["precipChance"][i * 2]

            forecasts.append({
                "day": data["dayOfWeek"][i],
                "temp_max": data.get("temperatureMax", [])[i] if i < len(data.get("temperatureMax", [])) and data.get("temperatureMax", [])[i] is not None else 0,
                "temp_min": data.get("temperatureMin", [])[i] if i < len(data.get("temperatureMin", [])) and data.get("temperatureMin", [])[i] is not None else 0,
                "precip_chance": precip_chance,
                "precip_amount": data.get("qpf", [])[i] if i < len(data.get("qpf", [])) and data.get("qpf", [])[i] is not None else 0,
                "narrative": data.get("narrative", [])[i] if i < len(data.get("narrative", [])) else ""
            })

    return {"forecasts": forecasts}

@app.get("/api/stations")
async def get_neighboring_stations() -> Dict[str, Any]:
    """Récupère les données actuelles de toutes les stations de Garéoult"""
    stations_data = []

    # Station principale
    main_data = await fetch_current(STATION_ID)
    if main_data and "observations" in main_data and len(main_data["observations"]) > 0:
        obs = main_data["observations"][0]
        metric = obs.get("metric", {})
        current_pressure = metric.get("pressure", 0)

        stations_data.append({
            "id": STATION_ID,
            "name": obs.get("neighborhood", STATION_ID),
            "is_main": True,
            "temp": metric.get("temp", 0),
            "pressure": current_pressure,
            "wind_speed": metric.get("windSpeed", 0),
            "wind_dir": obs.get("winddir", 0),
            "observation_time": obs.get("obsTimeLocal", "")
        })

    # Stations voisines
    for station_id in NEIGHBORING_STATIONS:
        try:
            data = await fetch_current(station_id, is_neighbor=True)
            if data and "observations" in data and len(data["observations"]) > 0:
                obs = data["observations"][0]
                metric = obs.get("metric", {})
                current_pressure = metric.get("pressure", 0)

                stations_data.append({
                    "id": station_id,
                    "name": obs.get("neighborhood", station_id),
                    "is_main": False,
                    "temp": metric.get("temp", 0),
                    "pressure": current_pressure,
                    "wind_speed": metric.get("windSpeed", 0),
                    "wind_dir": obs.get("winddir", 0),
                    "observation_time": obs.get("obsTimeLocal", "")
                })
        except Exception as e:
            print(f"Error fetching data for station {station_id}: {e}")
            continue

    return {"stations": stations_data}

@app.get("/api/history/average/{metric_name}")
async def get_average_history(metric_name: str, period: str = "daily") -> Dict[str, Any]:
    """Récupère la moyenne des stations voisines pour une métrique donnée

    Métriques supportées: temperature, pressure, wind
    """
    days_map = {"daily": 1, "weekly": 7, "monthly": 30}
    days = days_map.get(period, 1)

    # Récupérer les données de toutes les stations
    all_stations_data = {}

    for station_id in NEIGHBORING_STATIONS:
        try:
            observations = await fetch_history_range(station_id, days, is_neighbor=True)
            if observations:
                all_stations_data[station_id] = observations
        except Exception as e:
            print(f"Error fetching history for {station_id}: {e}")
            continue

    if not all_stations_data:
        return {"period": period, "data": []}

    # Calculer la moyenne par timestamp
    averaged_data = []

    if period == "daily":
        # Données toutes les 5 minutes - utiliser le timestamp comme clé
        time_buckets = {}

        for station_id, observations in all_stations_data.items():
            for obs in observations:
                time_key = obs.get("obsTimeLocal", "")
                if not time_key:
                    continue

                if time_key not in time_buckets:
                    time_buckets[time_key] = {
                        "time": time_key,
                        "values": []
                    }

                metric = obs.get("metric", {})

                if metric_name == "temperature":
                    value = metric.get("tempAvg", 0)
                elif metric_name == "pressure":
                    value = metric.get("pressureMax", metric.get("pressureMin", 0))
                elif metric_name == "wind":
                    value = metric.get("windspeedAvg", 0)
                else:
                    value = 0

                if value:
                    time_buckets[time_key]["values"].append(value)

        # Calculer les moyennes
        for time_key in sorted(time_buckets.keys()):
            bucket = time_buckets[time_key]
            if bucket["values"]:
                avg_value = sum(bucket["values"]) / len(bucket["values"])

                # Utiliser les bons noms de champs selon la métrique
                data_point = {"time": bucket["time"]}
                if metric_name == "temperature":
                    data_point["temp"] = round(avg_value, 1)
                elif metric_name == "pressure":
                    data_point["pressure"] = round(avg_value, 1)
                elif metric_name == "wind":
                    data_point["wind_speed"] = round(avg_value, 1)

                averaged_data.append(data_point)

    else:
        # Pour weekly et monthly : agréger par jour
        daily_buckets = {}

        for station_id, observations in all_stations_data.items():
            for obs in observations:
                obs_time = obs.get("obsTimeLocal", "")
                if not obs_time:
                    continue

                try:
                    date = obs_time.split("T")[0]
                    if date not in daily_buckets:
                        daily_buckets[date] = []

                    metric = obs.get("metric", {})

                    if metric_name == "temperature":
                        value = metric.get("tempAvg", 0)
                    elif metric_name == "pressure":
                        value = metric.get("pressureMax", metric.get("pressureMin", 0))
                    elif metric_name == "wind":
                        value = metric.get("windspeedAvg", 0)
                    else:
                        value = 0

                    if value:
                        daily_buckets[date].append(value)
                except Exception:
                    continue

        # Calculer les moyennes journalières
        for date in sorted(daily_buckets.keys()):
            values = daily_buckets[date]
            if values:
                avg_value = sum(values) / len(values)

                data_point = {"time": date}
                if metric_name == "temperature":
                    data_point["temp"] = round(avg_value, 1)
                elif metric_name == "pressure":
                    data_point["pressure"] = round(avg_value, 1)
                elif metric_name == "wind":
                    data_point["wind_speed"] = round(avg_value, 1)

                averaged_data.append(data_point)

    return {"period": period, "data": averaged_data[-288 if period == "daily" else -30:]}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/cache/clear")
async def clear_cache():
    """Vide le cache manuellement (utile pour debug)"""
    from api import cache
    cache._cache.clear()
    return {"status": "cache cleared", "message": "All cached data has been removed"}

# Serve static files (production)
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    # Mount static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    # Serve index.html for all non-API routes (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # If it's an API route, let FastAPI handle it (this won't match due to route priority)
        # Otherwise serve index.html
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"error": "Frontend not built"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
