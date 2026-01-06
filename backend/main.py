"""FastAPI backend for Marine Weather Dashboard"""

import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import datetime, timedelta
from typing import Dict, Any, List

from config import STATION_ID, COORDS_GAREOULT, SEUILS
from api import (
    fetch_current, fetch_history_range, fetch_daily_summary, fetch_forecast,
    fetch_all_1day, fetch_history_daily_range, fetch_history_hourly_date,
    fetch_yearly_aggregates
)

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


def calculate_comparison_periods(period: str) -> Dict[str, Any]:
    """Calcule les dates de début/fin pour les périodes current et previous.

    Retourne un dictionnaire avec:
    - current: (start_date, end_date) au format YYYYMMDD
    - previous: (start_date, end_date) au format YYYYMMDD
    - current_label: label pour la légende
    - previous_label: label pour la légende
    """
    today = datetime.now().date()

    if period == "daily":
        # Aujourd'hui vs Hier
        current_start = today
        current_end = today
        previous_start = today - timedelta(days=1)
        previous_end = today - timedelta(days=1)
        current_label = "Aujourd'hui"
        previous_label = "Hier"

    elif period == "weekly":
        # 7 derniers jours vs 7 jours précédents
        current_start = today - timedelta(days=6)
        current_end = today
        previous_start = today - timedelta(days=13)
        previous_end = today - timedelta(days=7)
        current_label = "Cette semaine"
        previous_label = "Semaine dernière"

    elif period == "monthly":
        # 30 derniers jours vs 30 jours précédents
        current_start = today - timedelta(days=29)
        current_end = today
        previous_start = today - timedelta(days=59)
        previous_end = today - timedelta(days=30)
        current_label = "Ce mois"
        previous_label = "Mois dernier"

    elif period == "yearly":
        # Année en cours vs année précédente (agrégats mensuels)
        current_year = today.year
        previous_year = current_year - 1
        return {
            "type": "yearly",
            "current_year": current_year,
            "previous_year": previous_year,
            "current_label": str(current_year),
            "previous_label": str(previous_year)
        }

    else:
        raise ValueError(f"Unknown period: {period}")

    return {
        "type": "range",
        "current": (current_start.strftime("%Y%m%d"), current_end.strftime("%Y%m%d")),
        "previous": (previous_start.strftime("%Y%m%d"), previous_end.strftime("%Y%m%d")),
        "current_label": current_label,
        "previous_label": previous_label
    }


def normalize_comparison_data(current_data: List[Dict], previous_data: List[Dict],
                               value_key: str) -> tuple[List[Dict], List[Dict]]:
    """Normalise les données pour la comparaison en ajoutant un index."""
    # Ajouter un index pour aligner les courbes
    normalized_current = []
    for i, item in enumerate(current_data):
        normalized_current.append({**item, "index": i})

    normalized_previous = []
    for i, item in enumerate(previous_data):
        normalized_previous.append({**item, "index": i})

    return normalized_current, normalized_previous


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

def format_time_label(time_str: str, period: str) -> str:
    """Formate un timestamp en label lisible selon la période."""
    try:
        if "T" in time_str:
            # Format ISO avec heure
            dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            if period == "daily":
                return dt.strftime("%H:%M")
            return dt.strftime("%d/%m")
        else:
            # Format date uniquement
            dt = datetime.strptime(time_str, "%Y-%m-%d")
            return dt.strftime("%d/%m")
    except Exception:
        return time_str


def process_temperature_observations(observations: List[Dict], period: str) -> List[Dict]:
    """Traite les observations de température selon la période."""
    if period == "daily":
        # Données toutes les 5 minutes pour 24h (max 288 observations)
        data_points = []
        for obs in observations[-288:]:
            metric = obs.get("metric", {})
            time_str = obs.get("obsTimeLocal", "")
            data_points.append({
                "time": time_str,
                "label": format_time_label(time_str, period),
                "temp": metric.get("tempAvg", 0),
                "temp_high": metric.get("tempHigh", 0),
                "temp_low": metric.get("tempLow", 0)
            })
        return data_points

    # Agréger par jour pour weekly/monthly
    daily_data = {}
    for obs in observations:
        obs_time = obs.get("obsTimeLocal", "")
        if not obs_time:
            continue

        try:
            date = obs_time.split("T")[0]
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
            "label": format_time_label(date, period),
            "temp": round(sum(temps) / len(temps), 1) if temps else 0,
            "temp_high": max(highs) if highs else 0,
            "temp_low": min(lows) if lows else 0
        })

    return data_points


@app.get("/api/history/temperature")
async def get_temperature_history(period: str = "daily", compare: bool = False) -> Dict[str, Any]:
    """Récupère l'historique des températures

    Périodes disponibles: daily (24h), weekly (7j), monthly (30j), yearly
    Paramètre compare: si True, retourne les données de la période précédente aussi
    """
    if not compare:
        # Mode normal (sans comparaison)
        if period == "yearly":
            # Données annuelles agrégées par mois
            current_year = datetime.now().year
            yearly_data = await fetch_yearly_aggregates(STATION_ID, current_year)
            data_points = [{
                "time": item["label"],
                "label": item["label"],
                "temp": item["temp_avg"],
                "temp_high": item["temp_high"],
                "temp_low": item["temp_low"],
                "index": i
            } for i, item in enumerate(yearly_data)]
            return {"period": period, "data": data_points}

        days_map = {"daily": 1, "weekly": 7, "monthly": 30}
        days = days_map.get(period, 1)
        observations = await fetch_history_range(STATION_ID, days)
        data_points = process_temperature_observations(observations, period)
        return {"period": period, "data": data_points}

    # Mode comparaison
    periods = calculate_comparison_periods(period)

    if periods["type"] == "yearly":
        # Comparaison annuelle
        current_data = await fetch_yearly_aggregates(STATION_ID, periods["current_year"])
        previous_data = await fetch_yearly_aggregates(STATION_ID, periods["previous_year"])

        current_points = [{
            "time": item["label"],
            "label": item["label"],
            "temp": item["temp_avg"],
            "temp_high": item["temp_high"],
            "temp_low": item["temp_low"],
            "index": i
        } for i, item in enumerate(current_data)]

        previous_points = [{
            "time": item["label"],
            "label": item["label"],
            "temp": item["temp_avg"],
            "temp_high": item["temp_high"],
            "temp_low": item["temp_low"],
            "index": i
        } for i, item in enumerate(previous_data)]

    else:
        # Comparaison daily/weekly/monthly
        if period == "daily":
            # Aujourd'hui: données 5 min, Hier: données horaires
            current_obs = await fetch_history_range(STATION_ID, 1)
            yesterday = (datetime.now().date() - timedelta(days=1)).strftime("%Y%m%d")
            previous_obs = await fetch_history_hourly_date(STATION_ID, yesterday)
        else:
            # Weekly/Monthly: utiliser les plages de dates
            current_obs = await fetch_history_daily_range(
                STATION_ID, periods["current"][0], periods["current"][1]
            )
            previous_obs = await fetch_history_daily_range(
                STATION_ID, periods["previous"][0], periods["previous"][1]
            )

        current_points = process_temperature_observations(current_obs, period)
        previous_points = process_temperature_observations(previous_obs, period)

        # Ajouter les index
        for i, item in enumerate(current_points):
            item["index"] = i
        for i, item in enumerate(previous_points):
            item["index"] = i

    return {
        "period": period,
        "compare": True,
        "current": {
            "label": periods["current_label"],
            "data": current_points
        },
        "previous": {
            "label": periods["previous_label"],
            "data": previous_points
        }
    }

def process_pressure_observations(observations: List[Dict], period: str) -> List[Dict]:
    """Traite les observations de pression selon la période."""
    if period == "daily":
        data_points = []
        for obs in observations[-288:]:
            metric = obs.get("metric", {})
            time_str = obs.get("obsTimeLocal", "")
            data_points.append({
                "time": time_str,
                "label": format_time_label(time_str, period),
                "pressure": metric.get("pressureMax", 0) or metric.get("pressure", 0)
            })
        return data_points

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
            "label": format_time_label(date, period),
            "pressure": round(sum(pressures) / len(pressures), 1) if pressures else 0
        })
    return data_points


@app.get("/api/history/pressure")
async def get_pressure_history(period: str = "daily", compare: bool = False) -> Dict[str, Any]:
    """Récupère l'historique de la pression atmosphérique

    Périodes disponibles: daily (24h), weekly (7j), monthly (30j), yearly
    Paramètre compare: si True, retourne les données de la période précédente aussi
    """
    if not compare:
        if period == "yearly":
            current_year = datetime.now().year
            yearly_data = await fetch_yearly_aggregates(STATION_ID, current_year)
            data_points = [{
                "time": item["label"],
                "label": item["label"],
                "pressure": item["pressure_avg"],
                "index": i
            } for i, item in enumerate(yearly_data)]
            return {"period": period, "data": data_points}

        days_map = {"daily": 1, "weekly": 7, "monthly": 30}
        days = days_map.get(period, 1)
        observations = await fetch_history_range(STATION_ID, days)
        data_points = process_pressure_observations(observations, period)
        return {"period": period, "data": data_points}

    # Mode comparaison
    periods = calculate_comparison_periods(period)

    if periods["type"] == "yearly":
        current_data = await fetch_yearly_aggregates(STATION_ID, periods["current_year"])
        previous_data = await fetch_yearly_aggregates(STATION_ID, periods["previous_year"])

        current_points = [{"time": item["label"], "label": item["label"], "pressure": item["pressure_avg"], "index": i}
                          for i, item in enumerate(current_data)]
        previous_points = [{"time": item["label"], "label": item["label"], "pressure": item["pressure_avg"], "index": i}
                           for i, item in enumerate(previous_data)]
    else:
        if period == "daily":
            current_obs = await fetch_history_range(STATION_ID, 1)
            yesterday = (datetime.now().date() - timedelta(days=1)).strftime("%Y%m%d")
            previous_obs = await fetch_history_hourly_date(STATION_ID, yesterday)
        else:
            current_obs = await fetch_history_daily_range(
                STATION_ID, periods["current"][0], periods["current"][1]
            )
            previous_obs = await fetch_history_daily_range(
                STATION_ID, periods["previous"][0], periods["previous"][1]
            )

        current_points = process_pressure_observations(current_obs, period)
        previous_points = process_pressure_observations(previous_obs, period)

        for i, item in enumerate(current_points):
            item["index"] = i
        for i, item in enumerate(previous_points):
            item["index"] = i

    return {
        "period": period,
        "compare": True,
        "current": {"label": periods["current_label"], "data": current_points},
        "previous": {"label": periods["previous_label"], "data": previous_points}
    }

def process_wind_observations(observations: List[Dict], period: str) -> List[Dict]:
    """Traite les observations de vent selon la période."""
    if period == "daily":
        data_points = []
        for obs in observations[-288:]:
            metric = obs.get("metric", {})
            time_str = obs.get("obsTimeLocal", "")
            data_points.append({
                "time": time_str,
                "label": format_time_label(time_str, period),
                "wind_speed": metric.get("windspeedAvg", 0),
                "wind_gust": metric.get("windgustHigh", 0),
                "wind_dir": obs.get("winddirAvg", 0)
            })
        return data_points

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

            wind_dir = obs.get("winddirAvg", 0)
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
            "label": format_time_label(date, period),
            "wind_speed": round(sum(speeds) / len(speeds), 1) if speeds else 0,
            "wind_gust": max(gusts) if gusts else 0,
            "wind_dir": round(sum(dirs) / len(dirs), 0) if dirs else 0
        })
    return data_points


@app.get("/api/history/wind")
async def get_wind_history(period: str = "daily", compare: bool = False) -> Dict[str, Any]:
    """Récupère l'historique du vent (vitesse et direction)

    Périodes disponibles: daily (24h), weekly (7j), monthly (30j), yearly
    Paramètre compare: si True, retourne les données de la période précédente aussi
    """
    if not compare:
        if period == "yearly":
            current_year = datetime.now().year
            yearly_data = await fetch_yearly_aggregates(STATION_ID, current_year)
            data_points = [{
                "time": item["label"],
                "label": item["label"],
                "wind_speed": item["wind_avg"],
                "wind_gust": item["wind_gust_max"],
                "index": i
            } for i, item in enumerate(yearly_data)]
            return {"period": period, "data": data_points}

        days_map = {"daily": 1, "weekly": 7, "monthly": 30}
        days = days_map.get(period, 1)
        observations = await fetch_history_range(STATION_ID, days)
        data_points = process_wind_observations(observations, period)
        return {"period": period, "data": data_points}

    # Mode comparaison
    periods = calculate_comparison_periods(period)

    if periods["type"] == "yearly":
        current_data = await fetch_yearly_aggregates(STATION_ID, periods["current_year"])
        previous_data = await fetch_yearly_aggregates(STATION_ID, periods["previous_year"])

        current_points = [{
            "time": item["label"],
            "label": item["label"],
            "wind_speed": item["wind_avg"],
            "wind_gust": item["wind_gust_max"],
            "index": i
        } for i, item in enumerate(current_data)]
        previous_points = [{
            "time": item["label"],
            "label": item["label"],
            "wind_speed": item["wind_avg"],
            "wind_gust": item["wind_gust_max"],
            "index": i
        } for i, item in enumerate(previous_data)]
    else:
        if period == "daily":
            current_obs = await fetch_history_range(STATION_ID, 1)
            yesterday = (datetime.now().date() - timedelta(days=1)).strftime("%Y%m%d")
            previous_obs = await fetch_history_hourly_date(STATION_ID, yesterday)
        else:
            current_obs = await fetch_history_daily_range(
                STATION_ID, periods["current"][0], periods["current"][1]
            )
            previous_obs = await fetch_history_daily_range(
                STATION_ID, periods["previous"][0], periods["previous"][1]
            )

        current_points = process_wind_observations(current_obs, period)
        previous_points = process_wind_observations(previous_obs, period)

        for i, item in enumerate(current_points):
            item["index"] = i
        for i, item in enumerate(previous_points):
            item["index"] = i

    return {
        "period": period,
        "compare": True,
        "current": {"label": periods["current_label"], "data": current_points},
        "previous": {"label": periods["previous_label"], "data": previous_points}
    }

def process_rain_observations(observations: List[Dict], period: str) -> List[Dict]:
    """Traite les observations de pluie selon la période."""
    if period == "daily":
        data_points = []
        for obs in observations[-288:]:
            metric = obs.get("metric", {})
            time_str = obs.get("obsTimeLocal", "")
            data_points.append({
                "time": time_str,
                "label": format_time_label(time_str, period),
                "rain": metric.get("precipTotal", 0),
                "rain_rate": metric.get("precipRate", 0)
            })
        return data_points

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
            "label": format_time_label(date, period),
            "rain": round(sum(rains), 1) if rains else 0
        })
    return data_points


@app.get("/api/history/rain")
async def get_rain_history(period: str = "daily", compare: bool = False) -> Dict[str, Any]:
    """Récupère l'historique de la pluviométrie

    Périodes disponibles: daily (24h), weekly (7j), monthly (30j), yearly
    Paramètre compare: si True, retourne les données de la période précédente aussi
    """
    if not compare:
        if period == "yearly":
            current_year = datetime.now().year
            yearly_data = await fetch_yearly_aggregates(STATION_ID, current_year)
            data_points = [{
                "time": item["label"],
                "label": item["label"],
                "rain": item["rain_total"],
                "index": i
            } for i, item in enumerate(yearly_data)]
            return {"period": period, "data": data_points}

        days_map = {"daily": 1, "weekly": 7, "monthly": 30}
        days = days_map.get(period, 1)
        observations = await fetch_history_range(STATION_ID, days)
        data_points = process_rain_observations(observations, period)
        return {"period": period, "data": data_points}

    # Mode comparaison
    periods = calculate_comparison_periods(period)

    if periods["type"] == "yearly":
        current_data = await fetch_yearly_aggregates(STATION_ID, periods["current_year"])
        previous_data = await fetch_yearly_aggregates(STATION_ID, periods["previous_year"])

        current_points = [{"time": item["label"], "label": item["label"], "rain": item["rain_total"], "index": i}
                          for i, item in enumerate(current_data)]
        previous_points = [{"time": item["label"], "label": item["label"], "rain": item["rain_total"], "index": i}
                           for i, item in enumerate(previous_data)]
    else:
        if period == "daily":
            current_obs = await fetch_history_range(STATION_ID, 1)
            yesterday = (datetime.now().date() - timedelta(days=1)).strftime("%Y%m%d")
            previous_obs = await fetch_history_hourly_date(STATION_ID, yesterday)
        else:
            current_obs = await fetch_history_daily_range(
                STATION_ID, periods["current"][0], periods["current"][1]
            )
            previous_obs = await fetch_history_daily_range(
                STATION_ID, periods["previous"][0], periods["previous"][1]
            )

        current_points = process_rain_observations(current_obs, period)
        previous_points = process_rain_observations(previous_obs, period)

        for i, item in enumerate(current_points):
            item["index"] = i
        for i, item in enumerate(previous_points):
            item["index"] = i

    return {
        "period": period,
        "compare": True,
        "current": {"label": periods["current_label"], "data": current_points},
        "previous": {"label": periods["previous_label"], "data": previous_points}
    }

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
