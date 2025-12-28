#!/bin/bash

# Script pour initialiser Git et pousser sur GitHub

echo "🔧 Initialisation de Git..."
git init

echo "📝 Configuration Git (ajuste avec tes infos)..."
git config user.name "Ton Nom"
git config user.email "ton@email.com"

echo "📦 Ajout des fichiers..."
git add .

echo "💾 Premier commit..."
git commit -m "Initial commit - Station météo Garéoult"

echo ""
echo "✅ Git initialisé !"
echo ""
echo "📌 PROCHAINES ÉTAPES :"
echo "1. Va sur https://github.com/new"
echo "2. Nom du repo : meteo-gareoult (ou ce que tu veux)"
echo "3. Privé ou Public : ton choix"
echo "4. NE PAS initialiser avec README/gitignore (on les a déjà)"
echo "5. Clique 'Create repository'"
echo ""
echo "6. Ensuite, exécute ces commandes (GitHub te les donnera) :"
echo "   git remote add origin https://github.com/TON_USERNAME/meteo-gareoult.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
