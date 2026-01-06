"""Weather Underground API client with in-memory caching"""

import asyncio
import httpx
from datetime import datetime, timedelta
from calendar import monthrange
from typing import Optional, Dict, Any, List
from config import API_KEY, BASE_URL, CACHE_TTL

class WeatherCache:
    def __init__(self):
        self._cache: Dict[str, tuple[Any, datetime]] = {}

    def get(self, key: str, ttl_seconds: int) -> Optional[Any]:
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.now() - timestamp < timedelta(seconds=ttl_seconds):
                return data
        return None

    def set(self, key: str, data: Any):
        self._cache[key] = (data, datetime.now())

cache = WeatherCache()

async def fetch_all_1day(station_id: str) -> Optional[Dict]:
    """Récupère toutes les observations sur 24h (granularité 5 minutes)"""
    import logging
    logger = logging.getLogger("uvicorn")

    cache_key = f"all_1day_{station_id}"
    cached = cache.get(cache_key, CACHE_TTL["current"])
    if cached:
        logger.info(f"[CACHE HIT] {station_id}")
        return cached

    logger.info(f"[CACHE MISS] {station_id} - Fetching fresh data from API")
    url = f"{BASE_URL}/v2/pws/observations/all/1day"
    params = {
        "stationId": station_id,
        "format": "json",
        "units": "m",
        "apiKey": API_KEY
    }

    try:
        # Add cache-busting headers to force fresh data
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Connection": "close"  # Force new connection, prevent connection reuse
        }

        # Use limits to disable connection pooling and force fresh connections
        limits = httpx.Limits(max_keepalive_connections=0, max_connections=10)
        async with httpx.AsyncClient(timeout=10.0, limits=limits) as client:
            response = await client.get(url, params=params, headers=headers)
            logger.info(f"[API RESPONSE] {station_id} - Status: {response.status_code}")
            logger.info(f"[API REQUEST] Full URL: {response.url}")
            response.raise_for_status()
            data = response.json()

            # Log dernière observation
            if "observations" in data and len(data["observations"]) > 0:
                last_obs_time = data["observations"][-1].get("obsTimeLocal", "N/A")
                logger.info(f"[API DATA] {station_id} - Last observation: {last_obs_time}")

            cache.set(cache_key, data)
            return data
    except Exception as e:
        logger.error(f"[API ERROR] {station_id} - {type(e).__name__}: {e}")
        return None

async def fetch_current(station_id: str) -> Optional[Dict]:
    """Récupère l'observation actuelle (instantanée)"""
    import logging
    logger = logging.getLogger("uvicorn")

    cache_key = f"current_{station_id}"
    cached = cache.get(cache_key, CACHE_TTL["current"])
    if cached:
        logger.info(f"[CACHE HIT] current_{station_id}")
        return cached

    logger.info(f"[CACHE MISS] current_{station_id} - Fetching fresh data from API")
    url = f"{BASE_URL}/v2/pws/observations/current"
    params = {
        "stationId": station_id,
        "format": "json",
        "units": "m",
        "numericPrecision": "decimal",
        "apiKey": API_KEY
    }

    try:
        # Add cache-busting headers to force fresh data
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Connection": "close"  # Force new connection, prevent connection reuse
        }

        # Use limits to disable connection pooling and force fresh connections
        limits = httpx.Limits(max_keepalive_connections=0, max_connections=10)
        async with httpx.AsyncClient(timeout=10.0, limits=limits) as client:
            response = await client.get(url, params=params, headers=headers)
            logger.info(f"[API RESPONSE] current_{station_id} - Status: {response.status_code}")
            logger.info(f"[API REQUEST] Full URL: {response.url}")
            response.raise_for_status()
            data = response.json()

            # Log observation time
            if "observations" in data and len(data["observations"]) > 0:
                obs_time = data["observations"][0].get("obsTimeLocal", "N/A")
                logger.info(f"[API DATA] current_{station_id} - Observation time: {obs_time}")

            cache.set(cache_key, data)
            return data
    except Exception as e:
        logger.error(f"[API ERROR] current_{station_id} - {type(e).__name__}: {e}")
        return None

async def fetch_daily_summary(station_id: str) -> Optional[Dict]:
    """Récupère le résumé quotidien des 7 derniers jours"""
    cache_key = f"daily_{station_id}"
    cached = cache.get(cache_key, CACHE_TTL["history"])
    if cached:
        return cached

    url = f"{BASE_URL}/v2/pws/dailysummary/7day"
    params = {
        "stationId": station_id,
        "format": "json",
        "units": "m",
        "apiKey": API_KEY
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            cache.set(cache_key, data)
            return data
    except Exception as e:
        print(f"Error fetching daily summary for {station_id}: {e}")
        return None

async def fetch_forecast(lat: float, lon: float) -> Optional[Dict]:
    """Récupère les prévisions 5 jours"""
    cache_key = f"forecast_{lat}_{lon}"
    cached = cache.get(cache_key, CACHE_TTL["forecast"])
    if cached:
        return cached

    url = f"{BASE_URL}/v3/wx/forecast/daily/5day"
    params = {
        "geocode": f"{lat},{lon}",
        "units": "m",  # Paramètre OBLIGATOIRE manquant !
        "language": "fr-FR",
        "format": "json",
        "apiKey": API_KEY
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            cache.set(cache_key, data)
            return data
    except Exception as e:
        print(f"Error fetching forecast: {e}")
        print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
        print(f"Response text: {response.text if 'response' in locals() else 'N/A'}")
        return None

async def fetch_history_range(station_id: str, days: int) -> list[Dict]:
    """Récupère l'historique sur plusieurs jours

    Pour 1 jour : utilise l'endpoint all/1day (données toutes les 5 minutes)
    Pour plus : utilise dailysummary pour l'agrégation
    """

    if days == 1:
        # Utiliser l'endpoint all/1day pour avoir des données toutes les 5 minutes
        data = await fetch_all_1day(station_id)
        if data and "observations" in data:
            return data["observations"]
        return []

    # Pour 7j et 30j, utiliser le daily summary
    daily_data = await fetch_daily_summary(station_id)

    if not daily_data or "summaries" not in daily_data:
        return []

    # Convertir les summaries en format compatible avec les observations
    observations = []
    for summary in daily_data["summaries"][:days]:
        observations.append(summary)

    return observations


async def fetch_history_daily_range(station_id: str, start_date: str, end_date: str) -> list[Dict]:
    """Récupère l'historique journalier entre deux dates (max 31 jours).

    Format dates: YYYYMMDD
    Endpoint: /v2/pws/history/daily?startDate=...&endDate=...
    """
    import logging
    logger = logging.getLogger("uvicorn")

    cache_key = f"daily_range_{station_id}_{start_date}_{end_date}"
    cached = cache.get(cache_key, CACHE_TTL["history"])
    if cached:
        logger.info(f"[CACHE HIT] daily_range_{station_id}_{start_date}_{end_date}")
        return cached

    logger.info(f"[CACHE MISS] daily_range_{station_id} - Fetching {start_date} to {end_date}")
    url = f"{BASE_URL}/v2/pws/history/daily"
    params = {
        "stationId": station_id,
        "startDate": start_date,
        "endDate": end_date,
        "format": "json",
        "units": "m",
        "apiKey": API_KEY
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            logger.info(f"[API RESPONSE] daily_range_{station_id} - Status: {response.status_code}")
            response.raise_for_status()
            data = response.json()

            observations = data.get("observations", [])
            cache.set(cache_key, observations)
            return observations
    except Exception as e:
        logger.error(f"[API ERROR] daily_range_{station_id} - {type(e).__name__}: {e}")
        return []


async def fetch_history_hourly_date(station_id: str, date: str) -> list[Dict]:
    """Récupère l'historique horaire d'une date spécifique.

    Format date: YYYYMMDD
    Endpoint: /v2/pws/history/hourly?date=...
    Utilisé pour: comparaison 24H (hier)
    """
    import logging
    logger = logging.getLogger("uvicorn")

    cache_key = f"hourly_{station_id}_{date}"
    cached = cache.get(cache_key, CACHE_TTL["history"])
    if cached:
        logger.info(f"[CACHE HIT] hourly_{station_id}_{date}")
        return cached

    logger.info(f"[CACHE MISS] hourly_{station_id} - Fetching date {date}")
    url = f"{BASE_URL}/v2/pws/history/hourly"
    params = {
        "stationId": station_id,
        "date": date,
        "format": "json",
        "units": "m",
        "apiKey": API_KEY
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            logger.info(f"[API RESPONSE] hourly_{station_id}_{date} - Status: {response.status_code}")
            response.raise_for_status()
            data = response.json()

            observations = data.get("observations", [])
            cache.set(cache_key, observations)
            return observations
    except Exception as e:
        logger.error(f"[API ERROR] hourly_{station_id}_{date} - {type(e).__name__}: {e}")
        return []


async def fetch_month_data(station_id: str, year: int, month: int) -> Dict:
    """Récupère les données d'un mois spécifique et les agrège."""
    # Calculer les dates de début et fin du mois
    start_date = f"{year}{month:02d}01"
    last_day = monthrange(year, month)[1]
    end_date = f"{year}{month:02d}{last_day:02d}"

    observations = await fetch_history_daily_range(station_id, start_date, end_date)

    if not observations:
        return {
            "month": month,
            "year": year,
            "temp_avg": None,
            "temp_high": None,
            "temp_low": None,
            "pressure_avg": None,
            "wind_avg": None,
            "wind_gust_max": None,
            "rain_total": None
        }

    # Agréger les données du mois
    temps = []
    temps_high = []
    temps_low = []
    pressures = []
    winds = []
    gusts = []
    rain = 0

    for obs in observations:
        metric = obs.get("metric", {})

        temp = metric.get("tempAvg")
        if temp is not None:
            temps.append(temp)

        temp_high = metric.get("tempHigh")
        if temp_high is not None:
            temps_high.append(temp_high)

        temp_low = metric.get("tempLow")
        if temp_low is not None:
            temps_low.append(temp_low)

        pressure = metric.get("pressureMax") or metric.get("pressureMin")
        if pressure is not None:
            pressures.append(pressure)

        wind = metric.get("windspeedAvg")
        if wind is not None:
            winds.append(wind)

        gust = metric.get("windgustHigh")
        if gust is not None:
            gusts.append(gust)

        precip = metric.get("precipTotal")
        if precip is not None:
            rain += precip

    return {
        "month": month,
        "year": year,
        "label": datetime(year, month, 1).strftime("%b %Y"),
        "temp_avg": round(sum(temps) / len(temps), 1) if temps else None,
        "temp_high": max(temps_high) if temps_high else None,
        "temp_low": min(temps_low) if temps_low else None,
        "pressure_avg": round(sum(pressures) / len(pressures), 1) if pressures else None,
        "wind_avg": round(sum(winds) / len(winds), 1) if winds else None,
        "wind_gust_max": max(gusts) if gusts else None,
        "rain_total": round(rain, 1)
    }


async def fetch_yearly_aggregates(station_id: str, year: int) -> List[Dict]:
    """Récupère les données d'une année complète, agrégées par mois.

    Stratégie: 12 appels parallèles avec asyncio.gather()
    Retourne: 12 points (un par mois)
    """
    import logging
    logger = logging.getLogger("uvicorn")

    cache_key = f"yearly_{station_id}_{year}"
    # Utiliser un TTL plus long pour les données annuelles (1 heure)
    ttl = CACHE_TTL.get("yearly", 3600)
    cached = cache.get(cache_key, ttl)
    if cached:
        logger.info(f"[CACHE HIT] yearly_{station_id}_{year}")
        return cached

    logger.info(f"[CACHE MISS] yearly_{station_id} - Fetching year {year} (12 parallel requests)")

    # Déterminer les mois à récupérer
    current_date = datetime.now()
    if year == current_date.year:
        # Année en cours: seulement les mois passés + mois actuel
        months_to_fetch = list(range(1, current_date.month + 1))
    else:
        # Année passée: tous les 12 mois
        months_to_fetch = list(range(1, 13))

    # Lancer les requêtes en parallèle
    tasks = [fetch_month_data(station_id, year, month) for month in months_to_fetch]
    results = await asyncio.gather(*tasks)

    # Filtrer les résultats valides (avec des données)
    monthly_data = [r for r in results if r.get("temp_avg") is not None]

    cache.set(cache_key, monthly_data)
    logger.info(f"[API DATA] yearly_{station_id}_{year} - Got {len(monthly_data)} months of data")

    return monthly_data
