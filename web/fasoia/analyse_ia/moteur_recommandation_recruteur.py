"""
Moteur de recommandation de candidats pour les recruteurs
spaCy (présélection) + Ollama (analyse détaillée) + Groq (résumé)
"""

import os
import sys
import json
import requests as req

def setup_django():
    import sys, os, django
    from pathlib import Path
    
    BASE_DIR = Path(__file__).resolve().parent.parent  # plus robuste
    sys.path.append(str(BASE_DIR))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
    django.setup()

if __name__ == "__main__":
    setup_django()

import spacy
import numpy as np
from django.db import models
from myAppli.models import Candidat, OffreEmploi, CVGenere
from analyse_ia.models import RecommandationCandidatRecruteur
from analyse_ia.ia_client import IAClient


class MoteurRecommandationRecruteur:
    """
    Recommande des candidats à un recruteur pour une offre
    spaCy  → présélection par similarité sémantique (instantané)
    Ollama → analyse détaillée par candidat (local, privé)
    Groq   → résumé global de la proposition (rapide)
    """

    def __init__(self):
        print("Chargement du modèle NLP...")
        try:
            self.nlp = spacy.load("fr_core_news_md")
            print("✅ Modèle medium chargé")
        except:
            self.nlp = spacy.load("fr_core_news_sm")
            print("⚠️ Modèle small chargé")

        self.ia = IAClient()
        self.seuil_minimum = 0.2
        self.ollama_url = 'http://localhost:11434'
        self.ollama_model = 'gemma2:2b'

    # ==========================================
    # VECTEURS SÉMANTIQUES — spaCy
    # ==========================================

    def get_vecteur_offre(self, offre):
        """Génère un vecteur sémantique pour l'offre"""
        texte = []

        if offre.titre:
            texte.append(offre.titre)
        if offre.competences_requises:
            texte.extend(offre.competences_requises)
        if offre.description:
            texte.append(offre.description[:500])
        if offre.profil_recherche:
            texte.append(offre.profil_recherche[:300])
        if offre.niveau_etude_requis:
            texte.append(offre.niveau_etude_requis)
        if offre.missions:
            texte.append(offre.missions[:300])
        texte.append(offre.get_secteur_display())

        texte_complet = " ".join(str(t) for t in texte if t)
        doc = self.nlp(texte_complet)
        return doc.vector

    def get_vecteur_candidat(self, candidat):
        """Génère un vecteur sémantique pour le candidat"""
        texte = []

        # Depuis CVGenere si disponible
        cv_genere = CVGenere.objects.filter(
            utilisateur=candidat.particulier.user,
            fichier_pdf__isnull=False
        ).order_by('-date_generation').first()

        if cv_genere and cv_genere.donnees_cv:
            d = cv_genere.donnees_cv
            competences = d.get('competences', [])
            experiences = d.get('experiences', [])
            formations = d.get('formations', [])

            if competences or experiences:
                texte.extend([
                    c.get('nom', c) if isinstance(c, dict) else c
                    for c in competences
                ])
                texte.extend([
                    e.get('poste', '') if isinstance(e, dict) else e
                    for e in experiences
                ])
                if formations:
                    texte.append(
                        formations[0].get('diplome', '')
                        if isinstance(formations[0], dict)
                        else formations[0]
                    )

        # Sinon champs Candidat directement
        if not texte:
            if candidat.competences:
                texte.extend([c.strip() for c in candidat.competences.split(',')])
            if candidat.niveauEtude:
                texte.append(candidat.niveauEtude)
            if candidat.secteur_recherche:
                texte.append(candidat.secteur_recherche)
            if candidat.niveauLangues:
                texte.append(candidat.niveauLangues)

        if not texte:
            texte = ["candidat", "emploi"]

        texte_complet = " ".join(str(t) for t in texte if t)
        doc = self.nlp(texte_complet)
        return doc.vector

    # ==========================================
    # SIMILARITÉ COSINUS
    # ==========================================

    def calculer_similarite(self, v1, v2):
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    # ==========================================
    # SCORING STRUCTURÉ
    # ==========================================

    def score_experience(self, candidat, offre):
        annees = candidat.anneesExperiences
        requis = offre.annees_experience_min
        if requis == 0:
            return 1.0
        if annees >= requis:
            return 1.0
        elif annees >= requis * 0.7:
            return 0.7
        elif annees >= requis * 0.5:
            return 0.5
        return 0.2

    def score_formation(self, candidat, offre):
        niveaux = {
            'bac': 1, 'bts': 2, 'dut': 2,
            'licence': 3, 'bachelor': 3,
            'master': 4, 'mba': 4, 'ingénieur': 4,
            'doctorat': 5, 'phd': 5
        }
        nc = niveaux.get(candidat.niveauEtude.lower(), 0) if candidat.niveauEtude else 0
        no = niveaux.get(offre.niveau_etude_requis.lower(), 0) if offre.niveau_etude_requis else 0
        if no == 0:
            return 1.0
        if nc >= no:
            return 1.0
        elif nc == no - 1:
            return 0.6
        return 0.2

    # ==========================================
    # OLLAMA — Analyse détaillée par candidat
    # ==========================================

    def analyser_candidat_ollama(self, candidat, offre):
        """
        Analyse détaillée d'un candidat pour une offre via Ollama
        Données privées → local
        """
        prompt = f"""
        Tu es un recruteur expert. Analyse la compatibilité entre ce candidat et cette offre.

        OFFRE:
        Titre: {offre.titre}
        Compétences requises: {', '.join(offre.competences_requises)}
        Niveau requis: {offre.niveau_etude_requis}
        Expérience requise: {offre.annees_experience_min} ans minimum
        Description: {offre.description[:300]}

        CANDIDAT:
        Compétences: {candidat.competences}
        Niveau d'étude: {candidat.niveauEtude}
        Années d'expérience: {candidat.anneesExperiences}
        Secteur recherché: {candidat.secteur_recherche}
        Langues: {candidat.niveauLangues}

        Réponds UNIQUEMENT en JSON valide :
        {{
            "explication": "Explication courte de la compatibilité en 2 phrases",
            "points_forts": ["Point fort 1", "Point fort 2"],
            "points_faibles": ["Point faible 1", "Point faible 2"]
        }}
        """

        try:
            response = req.post(
                f'{self.ollama_url}/api/generate',
                json={
                    'model': self.ollama_model,
                    'prompt': prompt,
                    'stream': False
                },
                timeout=120
            )

            texte = response.json()['response'].strip()
            if '```json' in texte:
                texte = texte.split('```json')[1].split('```')[0]
            elif '```' in texte:
                texte = texte.split('```')[1].split('```')[0]

            data = json.loads(texte.strip())
            return {
                'explication': data.get('explication', ''),
                'points_forts': data.get('points_forts', []),
                'points_faibles': data.get('points_faibles', []),
            }

        except Exception as e:
            print(f"   ⚠️ Erreur Ollama: {e}")
            return {
                'explication': '',
                'points_forts': [],
                'points_faibles': [],
            }

    # ==========================================
    # GROQ — Résumé global pour le recruteur
    # ==========================================

    def generer_resume_groq(self, offre, scores):
        """
        Génère un résumé global de la proposition de candidats via Groq
        Données non sensibles → cloud
        """
        if not scores:
            return "Aucun candidat compatible trouvé pour cette offre."

        top_candidats = "\n".join([
            f"- {item['candidat'].prenom} {item['candidat'].nom} : "
            f"{item['score_global']:.0%} de compatibilité "
            f"({item['candidat'].anneesExperiences} ans d'exp, "
            f"{item['candidat'].niveauEtude})"
            for item in scores[:5]
        ])

        prompt = f"""
        Tu es un assistant RH expert. Rédige un résumé professionnel pour un recruteur.

        OFFRE: {offre.titre}
        Nombre de candidats compatibles trouvés: {len(scores)}

        Top 5 candidats:
        {top_candidats}

        Rédige un résumé en 3-4 phrases qui :
        - Présente le nombre de candidats trouvés
        - Décrit le profil général des meilleurs candidats
        - Donne une recommandation sur la suite à donner
        - Est professionnel et encourageant

        Réponds en français.
        """

        try:
            response = self.ia.groq.chat.completions.create(
                model=self.ia.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=300,
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"⚠️ Erreur Groq résumé: {e}")
            return f"{len(scores)} candidats compatibles trouvés pour cette offre."

    # ==========================================
    # RECOMMANDATION PRINCIPALE
    # ==========================================

    def recommander_pour_offre(self, offre_id, limit=20):
        """
        Recommande des candidats pour une offre
        """
        print(f"\n{'='*60}")
        print(f"🎯 RECOMMANDATION CANDIDATS POUR OFFRE #{offre_id}")
        print(f"{'='*60}")

        # 1. Récupérer l'offre
        try:
            offre = OffreEmploi.objects.get(id=offre_id)
        except OffreEmploi.DoesNotExist:
            print(f"❌ Offre #{offre_id} introuvable")
            return []

        print(f"💼 {offre.titre}")

        # 2. Vecteur de l'offre
        vecteur_offre = self.get_vecteur_offre(offre)

        # 3. Récupérer candidats avec profil
        candidats_avec_cv = CVGenere.objects.filter(
            fichier_pdf__isnull=False
        ).values_list('utilisateur_id', flat=True)

        candidats = Candidat.objects.filter(
            models.Q(competences__isnull=False) & ~models.Q(competences='') |
            models.Q(cv__isnull=False) |
            models.Q(particulier__user_id__in=candidats_avec_cv)
        ).distinct()

        print(f"\n👥 {candidats.count()} candidats à analyser")

        # 4. Présélection spaCy
        print("\n⚡ Présélection sémantique (spaCy)...")
        scores = []

        for candidat in candidats:
            vecteur_candidat = self.get_vecteur_candidat(candidat)
            similarite = self.calculer_similarite(vecteur_offre, vecteur_candidat)
            s_experience = self.score_experience(candidat, offre)
            s_formation = self.score_formation(candidat, offre)

            score_global = (
                similarite   * 0.60 +
                s_experience * 0.25 +
                s_formation  * 0.15
            )

            if score_global >= self.seuil_minimum:
                scores.append({
                    'candidat': candidat,
                    'score_global': round(score_global, 3),
                    'score_competences': round(similarite, 3),
                    'score_experience': round(s_experience, 3),
                    'score_formation': round(s_formation, 3),
                    'explication': '',
                    'points_forts': [],
                    'points_faibles': [],
                })

        scores.sort(key=lambda x: x['score_global'], reverse=True)
        scores = scores[:limit]
        print(f"✅ {len(scores)} candidats présélectionnés")

        # 5. Analyse Ollama — TOUS les présélectionnés
        print(f"\n🤖 Analyse Ollama des {len(scores)} candidats...")
        for i, item in enumerate(scores):
            candidat = item['candidat']
            print(f"   {i+1}/{len(scores)} — {candidat.prenom} {candidat.nom}")
            analyse = self.analyser_candidat_ollama(candidat, offre)
            item['explication'] = analyse['explication']
            item['points_forts'] = analyse['points_forts']
            item['points_faibles'] = analyse['points_faibles']

        # 6. Résumé Groq
        print(f"\n✍️ Génération du résumé (Groq)...")
        resume = self.generer_resume_groq(offre, scores)
        print(f"✅ Résumé généré")
        print(f"\n📋 RÉSUMÉ:\n{resume}")

        # 7. Sauvegarder en DB
        print(f"\n💾 Sauvegarde...")
        for item in scores:
            obj, created = RecommandationCandidatRecruteur.objects.update_or_create(
                offre=offre,
                candidat=item['candidat'],
                defaults={
                    'score_global': item['score_global'],
                    'score_competences': item['score_competences'],
                    'score_experience': item['score_experience'],
                    'score_formation': item['score_formation'],
                    'explication': item['explication'],
                    'points_forts': item['points_forts'],
                    'points_faibles': item['points_faibles'],
                }
            )
            print(f"  {'✅' if created else '🔄'} {item['candidat'].prenom} "
                  f"{item['candidat'].nom} → {item['score_global']:.0%}")

        print(f"\n🏁 {len(scores)} candidats recommandés sauvegardés")
        return scores, resume

    def recommander_pour_toutes_offres(self):
        offres = OffreEmploi.objects.filter(est_active=True, statut='PUBLIEE')
        print(f"💼 {offres.count()} offres à traiter")
        for offre in offres:
            self.recommander_pour_offre(offre.id)


# Point d'entrée
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--offre', type=int, help="ID de l'offre")
    parser.add_argument('--toutes', action='store_true')
    parser.add_argument('--seuil', type=float, default=0.2)

    args = parser.parse_args()

    moteur = MoteurRecommandationRecruteur()
    moteur.seuil_minimum = args.seuil

    if args.toutes:
        moteur.recommander_pour_toutes_offres()
    elif args.offre:
        moteur.recommander_pour_offre(args.offre)
    else:
        print("Usage:")
        print("  --offre 1    → candidats pour offre #1")
        print("  --toutes     → toutes les offres actives")
        print("  --seuil 0.3  → changer le seuil")