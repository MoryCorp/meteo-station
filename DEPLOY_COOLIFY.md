# Déploiement sur Coolify - meteo.amaury-cleuziou.fr

## Configuration complète

### Informations du projet
- **Repo Git** : https://github.com/MoryCorp/meteo-station.git (privé)
- **Domaine** : meteo.amaury-cleuziou.fr
- **DNS** : ✅ Déjà configuré et pointe sur Hetzner

---

## Étapes dans Coolify

### 1. Créer un nouveau service

1. Se connecter à ton interface Coolify
2. Cliquer sur **"+ New Resource"**
3. Sélectionner **"Private Repository"** (le repo est privé)

### 2. Connexion au repo GitHub

**Source :**
- Type : `GitHub`
- Repository : `https://github.com/MoryCorp/meteo-station.git`

**Authentication :**
- Coolify va te demander de connecter ton compte GitHub
- Autoriser Coolify à accéder au repo privé
- Ou utiliser un Deploy Key / Personal Access Token

**Branch :**
- `main`

**Auto-deploy :**
- ✅ Cocher si tu veux que chaque push redéploie automatiquement

### 3. Configuration du build

**Build Pack :**
- Sélectionner : `Dockerfile`

**Dockerfile Location :**
- Laisser : `Dockerfile` (il est à la racine)

**Build Arguments :** (laisser vide)

### 4. Configuration réseau

**Port :**
- Container port : `8000`
- Published port : `8000`

**Domain :**
- Entrer : `meteo.amaury-cleuziou.fr`
- Coolify configurera automatiquement :
  - Reverse proxy Traefik
  - Certificat SSL Let's Encrypt

### 5. Variables d'environnement

Dans la section **Environment Variables**, ajouter (optionnel) :

```
WEATHER_API_KEY=084a331bff4940c08a331bff49b0c09d
```

> Note : Même si tu ne l'ajoutes pas, ça marchera car il y a une valeur par défaut dans le code

### 6. Health Check (recommandé)

**Health Check Path :**
- `/health`

**Health Check Port :**
- `8000`

**Health Check Interval :**
- `30s` (par défaut)

### 7. Ressources (optionnel)

**Limits (si tu veux limiter) :**
- CPU : `1` core
- Memory : `512 MB` (largement suffisant)

**Restart Policy :**
- `unless-stopped`

### 8. Déployer

1. Cliquer sur **"Deploy"** ou **"Start"**
2. Coolify va :
   - ✅ Cloner le repo depuis GitHub
   - ✅ Installer Node.js et build le frontend React (`npm ci && npm run build`)
   - ✅ Installer Python et les dépendances
   - ✅ Copier le build frontend dans `/app/static`
   - ✅ Créer l'image Docker
   - ✅ Démarrer le container sur le port 8000
   - ✅ Configurer Traefik pour router meteo.amaury-cleuziou.fr
   - ✅ Générer le certificat SSL

**Durée estimée du premier déploiement : 3-5 minutes**

---

## Vérification

### Une fois le déploiement terminé :

1. **Vérifier le statut** dans Coolify : doit être "Running" (vert)

2. **Tester l'URL** :
   ```
   https://meteo.amaury-cleuziou.fr
   ```

3. **Vérifier le SSL** : Le cadenas doit être visible dans le navigateur

4. **Tester l'API** :
   ```
   https://meteo.amaury-cleuziou.fr/health
   ```
   Doit retourner : `{"status":"ok"}`

5. **Vérifier les données** : Le dashboard doit afficher les données météo

---

## Logs et Monitoring

### Consulter les logs

Dans Coolify :
- Aller dans le service
- Onglet **"Logs"**
- Voir les logs en temps réel

### Logs applicatifs

Les logs Python (print, erreurs) s'afficheront dans les logs du container.

### Redéployer

**Automatique :**
- Si auto-deploy activé : chaque `git push` sur `main` redéploie

**Manuel :**
- Aller dans le service Coolify
- Cliquer **"Redeploy"** ou **"Restart"**

---

## Troubleshooting

### Le build échoue

**Problème :** Erreur pendant `npm install`
- **Solution :** Vérifier que `frontend/package.json` est bien commité

**Problème :** Erreur pendant `pip install`
- **Solution :** Vérifier que `backend/requirements.txt` existe

### Le site ne s'affiche pas

**Problème :** 502 Bad Gateway
- **Solution :** Le container n'a pas démarré, vérifier les logs

**Problème :** Frontend vide ou 404
- **Solution :** Le build React a échoué, vérifier les logs du build

### Les APIs ne répondent pas

**Problème :** `/api/current` retourne 500
- **Solution :** Vérifier les logs Python, probablement un problème avec l'API Weather Underground

**Problème :** Données vides
- **Solution :** Vérifier que `WEATHER_API_KEY` est correcte

### SSL ne fonctionne pas

**Problème :** Certificat invalide
- **Solution :**
  1. Vérifier que le DNS pointe bien (test : `ping meteo.amaury-cleuziou.fr`)
  2. Attendre 2-3 minutes (propagation + génération SSL)
  3. Vérifier les logs Traefik dans Coolify

---

## Commandes utiles

### Se connecter au container (si besoin de débugger)

Dans Coolify, onglet "Terminal" ou via SSH :

```bash
# Lister les containers
docker ps

# Se connecter au container
docker exec -it <container_id> bash

# Vérifier que les fichiers statiques existent
ls -la /app/static

# Tester l'API en interne
curl http://localhost:8000/health
```

---

## Performance et Monitoring

### Cache
- Le cache est en mémoire (Python dict)
- Tant que le container tourne, le cache persiste
- En cas de redémarrage : cache reconstruit progressivement

### Utilisation API
- ~1200-1400 appels/jour avec les caches optimisés
- Bien sous la limite de 1500 appels/jour

### Ressources serveur
- Le container est léger : ~100-200 MB RAM
- CPU très faible (sauf pendant les requêtes API)

---

## Mise à jour du code

Pour déployer des changements :

1. **Modifier le code localement**
2. **Commit et push** :
   ```bash
   git add .
   git commit -m "Description des changements"
   git push origin main
   ```
3. **Si auto-deploy activé** : Coolify redéploie automatiquement
4. **Sinon** : Cliquer "Redeploy" dans Coolify

---

## Backup

Le code est sur GitHub (déjà sauvegardé).

Aucune base de données, donc pas de backup de données nécessaire.
