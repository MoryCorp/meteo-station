# Dashboard Météo Marine - Garéoult

Dashboard météo style "Command Center" naval avec graphiques historiques pour la station Weather Underground IGAROU17 à Garéoult (Var).

## Caractéristiques

- **Backend FastAPI** : API REST avec cache mémoire et endpoints historiques
- **Frontend React** : Interface Command Center avec graphiques interactifs
- **Design militaire** : Fond sombre, typographie monospace, accents cyan
- **Graphiques historiques** : Évolution des métriques sur 24h, 7j et 30j
- **Métriques principales** :
  - Température (avec min/max)
  - Pression atmosphérique (avec tendances)
  - Vent (vitesse, rafales, direction)
  - Pluviométrie
  - Indice UV
- **Prévisions 5 jours**

## Structure du projet

```
meteo-dashboard/
├── backend/
│   ├── main.py           # Application FastAPI avec endpoints historiques
│   ├── api.py            # Client Weather Underground avec cache
│   ├── config.py         # Configuration API (station IGAROU17 uniquement)
│   └── requirements.txt  # Dépendances Python
├── frontend/
│   ├── src/
│   │   ├── App.jsx       # Dashboard React avec graphiques
│   │   ├── main.jsx      # Point d'entrée
│   │   └── index.css     # Styles Tailwind
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js    # Proxy /api vers backend
│   ├── tailwind.config.js
│   └── postcss.config.js
└── README.md
```

## Installation

### Backend

```bash
cd backend
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Lancement

### 1. Démarrer le backend (port 8000)

```bash
cd backend
python main.py
```

Le backend sera accessible sur `http://localhost:8000`

### 2. Démarrer le frontend (port 3000)

Dans un nouveau terminal :

```bash
cd frontend
npm run dev
```

Le dashboard sera accessible sur `http://localhost:3000`

## Endpoints API

| Endpoint | Paramètres | Description |
|----------|------------|-------------|
| `GET /api/current` | - | Observations actuelles et stats 7j |
| `GET /api/history/temperature` | `period` (daily/weekly/monthly) | Historique température |
| `GET /api/history/pressure` | `period` (daily/weekly/monthly) | Historique pression |
| `GET /api/history/wind` | `period` (daily/weekly/monthly) | Historique vent |
| `GET /api/history/rain` | `period` (daily/weekly/monthly) | Historique pluviométrie |
| `GET /api/forecast` | - | Prévisions 5 jours |
| `GET /health` | - | Health check |

## Configuration

La station est configurée dans `backend/config.py` :

```python
# Station unique extérieure
STATION_ID = "IGAROU17"

API_KEY = "084a331bff4940c08a331bff49b0c09d"
BASE_URL = "https://api.weather.com"
```

## Fonctionnalités

### Cache intelligent
- Current observations : 5 minutes
- Historique : 1 heure
- Prévisions : 4 heures

### Périodes historiques
- **Daily (24H)** : Données horaires des dernières 24 heures
- **Weekly (7J)** : Données quotidiennes agrégées sur 7 jours
- **Monthly (30J)** : Données quotidiennes agrégées sur 30 jours

### Métriques actuelles

#### Vent
- Vitesse actuelle avec alertes (60 km/h, 90 km/h)
- Rafales
- Direction avec rose des vents

#### Température
- Température actuelle
- Min/Max 7 jours

#### Pression atmosphérique
- Pression QFF actuelle
- Tendance sur 3h avec indicateur visuel

#### Indice UV
- Valeur actuelle avec code couleur
- Niveau (Faible/Modéré/Élevé/Très élevé)

### Graphiques historiques

#### Température
- Courbe principale : température moyenne
- Zones : min et max
- Filtres : 24H / 7J / 30J

#### Pression atmosphérique
- Courbe de pression
- Auto-scaling pour meilleure lisibilité
- Filtres : 24H / 7J / 30J

#### Vent
- Courbe cyan : vitesse moyenne
- Courbe orange pointillée : rafales
- Filtres : 24H / 7J / 30J

#### Pluviométrie
- Barres bleues : quantité de pluie
- Filtres : 24H / 7J / 30J

### Seuils d'alerte

```python
vent:
  attention: 60 km/h
  danger: 90 km/h

pression_chute:
  attention: 2 hPa/3h
  danger: 4 hPa/3h
```

## Interface utilisateur

### Composants affichés

1. **Header** : Station, heure locale, heure Zulu, statut online
2. **Métriques actuelles** (4 colonnes) :
   - Vent (vitesse, rafales, direction, rose des vents)
   - Température (actuelle, min/max 7j)
   - Pression QFF (valeur, tendance 3h)
   - Indice UV (valeur, niveau, jauge)
3. **Graphiques historiques avec filtres** :
   - Température (avec min/max)
   - Pression atmosphérique
   - Vent (vitesse + rafales)
   - Pluviométrie
4. **Prévisions 5 jours** : Températures, probabilité et quantité de pluie

### Codes couleurs

- **Fond** : slate-900 (#0f172a)
- **Bordures** : slate-700
- **Données live** : cyan-400
- **Attention** : orange-400
- **Danger** : red-400
- **Normal** : green-400
- **Temperature** : cyan (courbe), rouge/bleu (min/max)
- **Pression** : violet
- **Vent** : cyan (vitesse), orange (rafales)
- **Pluie** : bleu

## Développement

### Backend
- Framework : FastAPI 0.115
- HTTP client : httpx
- Cache : En mémoire avec TTL
- Agrégation des données par période

### Frontend
- Framework : React 18
- Build : Vite
- Styles : Tailwind CSS
- Graphiques : Recharts (ComposedChart, LineChart, Bar)
- Filtres : daily/weekly/monthly indépendants par métrique

### Proxy de développement
Le frontend (Vite) est configuré pour proxifier `/api/*` vers `http://localhost:8000`

## Production

### Backend
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm run build
npm run preview
```

## Dépannage

### Le backend ne démarre pas
- Vérifier que Python 3.8+ est installé
- Vérifier que toutes les dépendances sont installées : `pip install -r requirements.txt`

### Le frontend ne charge pas les données
- Vérifier que le backend est démarré sur le port 8000
- Vérifier la console navigateur pour les erreurs CORS
- Tester l'API directement : `http://localhost:8000/api/current`

### Les graphiques ne s'affichent pas
- Vérifier que recharts est installé : `npm install`
- Ouvrir la console navigateur pour voir les erreurs
- Vérifier que les données sont bien reçues de l'API

### Données historiques manquantes
- Les données horaires peuvent ne pas être disponibles pour toutes les périodes
- L'API Weather Underground peut avoir des limites
- Le cache peut prendre jusqu'à 1h pour se rafraîchir

## Optimisations

- Les données actuelles se rafraîchissent automatiquement toutes les 5 minutes
- Les graphiques sont mis en cache côté frontend
- Les données historiques sont agrégées intelligemment selon la période
- Le changement de filtre ne recharge que les données nécessaires

## Auteur

Dashboard développé pour un utilisateur retraité de la Marine Nationale, passionné de météorologie.

Focus sur l'évolution temporelle et l'analyse des tendances météorologiques.

## Licence

Usage personnel uniquement.
