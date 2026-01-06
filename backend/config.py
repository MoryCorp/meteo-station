"""Configuration for Weather Underground API"""

import os

API_KEY = os.getenv("WEATHER_API_KEY", "084a331bff4940c08a331bff49b0c09d")
BASE_URL = os.getenv("WEATHER_BASE_URL", "https://api.weather.com")

# Station principale extérieure
STATION_ID = "IGAROU17"

COORDS_GAREOULT = {"lat": 43.3279, "lon": 6.0456}

# Cache TTL en secondes (backend in-memory cache)
CACHE_TTL = {
    "current": 300,           # 5 minutes pour station principale
    "history": 600,           # 10 minutes pour historique (aligné sur frontend refresh)
    "forecast": 3600,         # 1 heure pour prévisions
    "comparison": 900,        # 15 minutes pour données de comparaison
    "yearly": 3600            # 1 heure pour données annuelles (stables)
}

# Seuils d'alerte
SEUILS = {
    "vent": {"attention": 60, "danger": 90},
    "pression_chute": {"attention": 2, "danger": 4}
}
