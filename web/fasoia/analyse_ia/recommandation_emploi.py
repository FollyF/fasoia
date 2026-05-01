# analyse_ia/recommandation_emploi.py

import os
import sys
import django
import requests

# --- CONFIGURATION DJANGO ---
current_file_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(current_file_path))

if project_root not in sys.path:
    sys.path.append(project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
django.setup()
# ----------------------------

from myAppli.models import OffreEmploi, Candidat
from analyse_ia.analyser_pdfs import extraire_texte_cv, extraire_texte_offre


def recommander_offres(candidat_id, modele='gemma2:2b', nb_recommandations=3):
    """
    Recommande les meilleures offres d'emploi à un candidat selon son CV
    """

    print("\n" + "="*60)
    print(f"🎯 RECOMMANDATION POUR CANDIDAT #{candidat_id}")
    print("="*60)

    # 1. Extraire le texte du CV
    print("\n📄 Etape 1 - Extraction du CV...")
    cv_texte = extraire_texte_cv(candidat_id)

    if not cv_texte:
        print("❌ Impossible d'extraire le CV")
        return None

    print(f"✅ CV extrait: {len(cv_texte)} caractères")

    # 2. Récupérer les offres actives
    print("\n📋 Etape 2 - Récupération des offres...")
    offres = OffreEmploi.objects.filter(
        est_active=True,
        statut='PUBLIEE'
    ).first()

    """if not offres.exists():
        print("❌ Aucune offre disponible")
        return None"""

    #print(f"✅ {offres.count()} offres trouvées")

    # 3. Extraire le contenu de chaque offre
    print("\n📑 Etape 3 - Extraction du contenu des offres...")
    offres_texte = ""

    """for offre in offres:
        print(f"\n   Offre #{offre.id} - {offre.titre}")
        contenu_offre = extraire_texte_offre(offre)
        offres_texte += f"\n{'='*40}\n"
        offres_texte += f"OFFRE ID: {offre.id}\n"
        offres_texte += contenu_offre"""
    
    print(f"\n   Offre #{offres.id} - {offres.titre}")
    contenu_offre = extraire_texte_offre(offres)
    offres_texte += f"\n{'='*40}\n"
    offres_texte += f"OFFRE ID: {offres.id}\n"
    offres_texte += contenu_offre
    print(offres_texte[:50])
    # 4. Construire le prompt
    print("\n🧠 Etape 4 - Construction du prompt...")
    prompt = f"""
    Tu es un conseiller emploi expert en Afrique de l'Ouest.
    
    Voici le CV du candidat :
    {cv_texte[:30]}
    
    Voici les offres d'emploi disponibles :
    {offres_texte[:50]}
    
    En te basant sur le CV du candidat, recommande les {nb_recommandations} 
    meilleures offres parmi celles disponibles.
    
    Pour chaque offre recommandée, donne OBLIGATOIREMENT :
    - ID de l'offre
    - Titre du poste
    - Pourcentage de compatibilité (ex: 85%)
    - Points forts : pourquoi le candidat correspond
    - Points faibles : ce qui manque au candidat
    - Conseil : comment le candidat peut améliorer sa candidature
    
    Classe les offres de la plus compatible à la moins compatible.
    Réponds en français de manière structurée et précise.
    """

    # 5. Envoyer à Ollama
    print("\n🤖 Etape 5 - Analyse par Ollama...")
    print(f"   Modèle utilisé: {modele}")

    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': modele,
                'prompt': prompt,
                'stream': False
            },
            timeout=120  # 2 minutes max
        )

        resultat = response.json()['response']

        print("\n✅ Recommandations générées !")
        print("\n" + "="*60)
        print(resultat)
        print("="*60)

        return resultat

    except Exception as e:
        print(f"❌ Erreur Ollama: {e}")
        return None


# Point d'entrée pour tester
if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python recommandation_emploi.py <candidat_id>")
        print("Exemple: python recommandation_emploi.py 1")
    else:
        candidat_id = int(sys.argv[1])
        recommander_offres(candidat_id)