# Déploiement sur Coolify

## Prérequis

1. **DNS configuré** : Pointer `meteo.tondomaine.com` (A record) vers l'IP de ton serveur Hetzner
2. **Repo Git** : Code pushé sur GitHub/GitLab
3. **Coolify installé** sur ton serveur Hetzner

## Étapes de déploiement

### 1. Créer un nouveau service dans Coolify

1. Se connecter à Coolify
2. Cliquer sur **"+ New Resource"**
3. Choisir **"Public Repository"** ou **"Private Repository"** (selon ton repo)
4. Coller l'URL de ton repo Git

### 2. Configuration du service

**Type de build :**
- Sélectionner : `Dockerfile`

**Dockerfile path :**
- Laisser : `Dockerfile` (à la racine)

**Port :**
- Port exposé : `8000`

**Domaine :**
- Entrer : `meteo.tondomaine.com`
- Coolify configurera automatiquement le SSL (Let's Encrypt)

### 3. Variables d'environnement

Dans la section **Environment Variables**, ajouter :

```
WEATHER_API_KEY=084a331bff4940c08a331bff49b0c09d
```

(Optionnel, il y a une valeur par défaut, mais mieux de l'externaliser)

### 4. Options de déploiement

**Health Check :**
- Path : `/health`
- Port : `8000`

**Restart Policy :**
- Laisser : `unless-stopped`

### 5. Déployer

1. Cliquer sur **"Deploy"**
2. Coolify va :
   - Cloner le repo
   - Build l'image Docker (build frontend + backend)
   - Démarrer le container
   - Configurer le reverse proxy Traefik
   - Générer le certificat SSL

### 6. Vérification

Une fois déployé :
- Aller sur `https://meteo.tondomaine.com`
- Vérifier que le frontend s'affiche
- Vérifier que les données API se chargent

## Architecture déployée

```
https://meteo.tondomaine.com/
  ├── /                  → Frontend React (fichiers statiques)
  ├── /api/current       → API FastAPI
  ├── /api/forecast      → API FastAPI
  ├── /api/history/*     → API FastAPI
  └── /assets/*          → JS/CSS/images du build Vite
```

## Redéploiement

**Automatique :**
- Si configuré dans Coolify, chaque push sur la branche `main` redéploie automatiquement

**Manuel :**
- Aller dans le service Coolify
- Cliquer sur **"Redeploy"**

## Logs et monitoring

- **Logs** : Disponibles dans l'interface Coolify
- **Métriques** : CPU/RAM/Réseau visibles dans Coolify
- **Health check** : Coolify vérifie `/health` automatiquement

## Troubleshooting

**Le frontend ne s'affiche pas :**
- Vérifier les logs : `docker logs <container_id>`
- Vérifier que le build s'est bien fait : le dossier `static/` doit exister dans le container

**Les APIs ne répondent pas :**
- Vérifier que le port 8000 est bien exposé
- Vérifier les logs pour les erreurs Python
- Tester le health check : `curl https://meteo.tondomaine.com/health`

**SSL ne fonctionne pas :**
- Vérifier que le DNS pointe bien vers le serveur
- Attendre quelques minutes (propagation DNS + génération SSL)
- Vérifier les logs Traefik dans Coolify

## Performance

**Cache en mémoire :**
- Le cache reste en mémoire tant que le container tourne
- Si redémarrage, le cache est recréé progressivement

**Limites API Weather Underground :**
- ~1200-1400 appels/jour avec les caches optimisés
- Bien sous la limite de 1500 appels/jour
