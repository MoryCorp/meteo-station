"""Configuration for Weather Underground API"""

import os

API_KEY = os.getenv("WEATHER_API_KEY", "084a331bff4940c08a331bff49b0c09d")
BASE_URL = os.getenv("WEATHER_BASE_URL", "https://api.weather.com")

# Station principale extérieure
STATION_ID = "IGAROU17"

# Autres stations de Garéoult pour comparaison
NEIGHBORING_STATIONS = ["IGAROU16", "IGAROU15", "IGAROU14", "IGAROU3", "IGAROU9"]

COORDS_GAREOULT = {"lat": 43.3279, "lon": 6.0456}

# Cache TTL en secondes
CACHE_TTL = {
    "current": 120,           # 2 minutes pour station principale
    "current_neighbors": 900, # 15 minutes pour stations voisines
    "history": 600,           # 10 minutes
    "forecast": 3600          # 1 heure
}

# Seuils d'alerte
SEUILS = {
    "vent": {"attention": 60, "danger": 90},
    "pression_chute": {"attention": 2, "danger": 4}
}
