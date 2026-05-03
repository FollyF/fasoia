# analyse_ia/recommandation_emploi.py

import os
import sys
import django
import requests
import json
import re

# --- CONFIGURATION DJANGO ---
current_file_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(current_file_path))

if project_root not in sys.path:
    sys.path.append(project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
django.setup()
# ----------------------------

from myAppli.models import OffreEmploi, Candidat, DossierCandidature
from analyse_ia.analyser_pdfs import extraire_texte_cv, extraire_texte_offre
from analyse_ia.ia_client import IAClient


def analyser_compatibilite(candidat_id, offre_id):
    """
    Analyse la compatibilité via GROQ
    """

    ia = IAClient()
    
    print("\n" + "="*60)
    print(f"🎯 ANALYSE COMPATIBILITE")
    print(f"   Candidat #{candidat_id} ↔ Offre #{offre_id}")
    print("="*60)

    # 1. Extraire le texte du CV
    print("\n📄 Etape 1 - Extraction du CV...")
    cv_texte = extraire_texte_cv(candidat_id)

    if not cv_texte:
        print("❌ Impossible d'extraire le CV")
        return None

    print(f"✅ CV extrait: {len(cv_texte)} caractères")

    # 2. Extraire le texte de l'offre
    print("\n📋 Etape 2 - Extraction de l'offre...")
    try:
        offre = OffreEmploi.objects.get(id=offre_id)
        offre_texte = extraire_texte_offre(offre)
        print(f"✅ Offre extraite: {len(offre_texte)} caractères")
    except OffreEmploi.DoesNotExist:
        print(f"❌ Offre #{offre_id} non trouvée")
        return None

    # 3. Construire le prompt pour Ollama
    print("\n🧠 Etape 3 - Construction du prompt...")
    
    prompt = f"""
    Tu es un recruteur expert en Afrique de l'Ouest spécialisé dans l'analyse de CV.
    
    ## CV DU CANDIDAT :
    {cv_texte[:3000]}
    
    ## OFFRE D'EMPLOI :
    {offre_texte[:3000]}
    
    Analyse la compatibilité entre ce candidat et cette offre.
    
    Réponds UNIQUEMENT au format JSON suivant, sans aucun texte avant ou après :
    
    {{
        "score_global": 85,
        "score_competences": 90,
        "score_experience": 75,
        "score_formation": 80,
        "points_forts": ["Expérience pertinente dans le secteur", "Maîtrise des outils requis"],
        "points_faibles": ["Manque de certification spécifique", "Expérience un peu légère"],
        "analyse": "Ce candidat correspond bien au poste. Ses compétences techniques sont solides..."
    }}
    """

    # 4. Envoyer à GROQ
    print(f"\n🤖 Etape 4 - Analyse par GROQ (Model: {ia.groq_model})...")

    try:
        # On utilise le client groq de ton IAClient
        completion = ia.groq.chat.completions.create(
            model=ia.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"} # Force Groq à renvoyer du JSON pur
        )

        # 5. Récupérer et transformer le résultat
        resultat_texte = completion.choices[0].message.content
        scores = json.loads(resultat_texte)
        
        # --- DÉBOGAGE : VÉRIFICATION DES TYPES DE DONNÉES ---
        print(f"DEBUG - Type score_global: {type(scores.get('score_global'))}")
        print(f"DEBUG - Valeur points_forts: {scores.get('points_forts')}")

        resultat_final = {
            'score_global': float(scores.get('score_global', 0)),
            'score_competences': float(scores.get('score_competences', 0)),
            'score_experience': float(scores.get('score_experience', 0)),
            'score_formation': float(scores.get('score_formation', 0)),
            'points_forts': scores.get('points_forts', []),
            'points_faibles': scores.get('points_faibles', []),
            'analyse': scores.get('analyse', 'Aucune analyse disponible')
        }
        
        print(f"✅ Analyse réussie ! Score Global: {resultat_final['score_global']}%")
        return resultat_final

    except Exception as e:
        print(f"❌ Erreur Groq: {e}")
        return None


def mettre_a_jour_scores_dossier(dossier_id, force=False):
    """
    Met à jour les scores IA d'un dossier de candidature
    """
    
    try:
        dossier = DossierCandidature.objects.select_related('candidat', 'offre').get(id=dossier_id)
    except DossierCandidature.DoesNotExist:
        print(f"❌ Dossier #{dossier_id} non trouvé")
        return False
    
    # Ne pas recalculer si déjà fait (sauf force=True)
    if not force and dossier.score_compatibilite > 0:
        print(f"⚠️ Dossier #{dossier_id} déjà noté (score: {dossier.score_compatibilite}%)")
        return True
    
    print(f"\n📝 Analyse du dossier #{dossier_id}...")
    
    # Analyser la compatibilité
    resultat = analyser_compatibilite(
        candidat_id=dossier.candidat.particulier.id,
        offre_id=dossier.offre.id,
    )
    
    if resultat:
        # Mettre à jour le dossier
        dossier.score_compatibilite = resultat['score_global']
        dossier.score_competences = resultat['score_competences']
        dossier.score_experience = resultat['score_experience']
        dossier.score_formation = resultat['score_formation']
        dossier.points_forts = resultat['points_forts']
        dossier.points_faibles = resultat['points_faibles']
        dossier.analyse_cv = resultat['analyse']
        dossier.save()
        print(f"SCORE FINAL EN BASE : {dossier.score_compatibilite}")
        dossier.refresh_from_db()
        print(f"SCORE FINAL EN BASE : {dossier.score_compatibilite}")
        
        print(f"\n✅ Dossier #{dossier_id} mis à jour avec succès !")
        return True
    
    return False


# Point d'entrée pour tester
if __name__ == "__main__":
    if len(sys.argv) >= 3:
        resultat = analyser_compatibilite(int(sys.argv[1]), int(sys.argv[2]))