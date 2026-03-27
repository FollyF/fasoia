#!/usr/bin/env bash
# Arrêter le script en cas d'erreur
set -o errexit

# 1. Installation des dépendances
pip install -r requirements.txt

# 2. Collecter les fichiers statiques (pour le CSS/JS)
# On s'assure d'être dans le bon dossier pour manage.py
python fasoia/manage.py collectstatic --no-input

# 3. Appliquer les migrations
python fasoia/manage.py migrate

# 4. L'IMPORTATION UNIQUE
if [ -f "fasoia/db_locale.json" ]; then
    echo "--- DEBUT DE L'IMPORTATION DES DONNÉES ---"
    python fasoia/manage.py loaddata fasoia/db_locale.json
    echo "--- IMPORTATION REUSSIE ---"
fi