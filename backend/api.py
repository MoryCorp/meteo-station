"""Weather Underground API client with in-memory caching"""

import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
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

async def fetch_all_1day(station_id: str, is_neighbor: bool = False) -> Optional[Dict]:
    """Récupère toutes les observations sur 24h (granularité 5 minutes)"""
    import logging
    logger = logging.getLogger("uvicorn")

    cache_key = f"all_1day_{station_id}"
    ttl = CACHE_TTL["current_neighbors"] if is_neighbor else CACHE_TTL["current"]
    cached = cache.get(cache_key, ttl)
    if cached:
        logger.info(f"[CACHE HIT] {station_id} - TTL: {ttl}s")
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
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            logger.info(f"[API RESPONSE] {station_id} - Status: {response.status_code}")
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

async def fetch_current(station_id: str, is_neighbor: bool = False) -> Optional[Dict]:
    """Récupère l'observation la plus récente"""
    data = await fetch_all_1day(station_id, is_neighbor=is_neighbor)

    if not data or "observations" not in data or len(data["observations"]) == 0:
        return None

    # Retourner la dernière observation dans le même format que l'ancien endpoint
    latest_obs = data["observations"][-1]

    return {
        "observations": [latest_obs]
    }

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

async def fetch_history_range(station_id: str, days: int, is_neighbor: bool = False) -> list[Dict]:
    """Récupère l'historique sur plusieurs jours

    Pour 1 jour : utilise l'endpoint all/1day (données toutes les 5 minutes)
    Pour plus : utilise dailysummary pour l'agrégation
    """

    if days == 1:
        # Utiliser l'endpoint all/1day pour avoir des données toutes les 5 minutes
        data = await fetch_all_1day(station_id, is_neighbor=is_neighbor)
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
