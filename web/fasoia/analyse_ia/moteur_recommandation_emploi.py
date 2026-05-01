#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moteur de recommandation d'offres d'emploi pour les candidats
Adapté du MoteurRecommandationSemantique pour les entreprises
"""

import os
import sys
import numpy as np

if __name__ == "__main__":
    import django
    current_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_path)
    if project_root not in sys.path:
        sys.path.append(project_root)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
    django.setup()

import spacy
from myAppli.models import Candidat, OffreEmploi, CVGenere
from analyse_ia.models import RecommandationEmploi, ElementsCVExtraits, ElementsOffreExtraits

class MoteurRecommandationEmploi:
    """
    Moteur de recommandation d'offres d'emploi
    Utilise la similarité sémantique spaCy + scoring structuré
    """

    def __init__(self):
        print("Chargement du modèle NLP...")
        try:
            self.nlp = spacy.load("fr_core_news_md")
            print("✅ Modèle chargé (avec vecteurs sémantiques)")
        except:
            print("⚠️ Modèle medium non trouvé, utilisation du modèle small")
            self.nlp = spacy.load("fr_core_news_sm")

        self.seuil_minimum = 0.55

    # ==========================================
    # VECTEURS SÉMANTIQUES
    # ==========================================

    def get_vecteur_candidat(self, candidat):
        """
        Génère un vecteur sémantique pour le candidat
        Priorité : ElementsCVExtraits → CVGenere.donnees_cv → champs Candidat
        """
        texte = []

        # 1. ElementsCVExtraits (CV uploadé analysé)
        try:
            from django.contrib.contenttypes.models import ContentType
            from analyse_ia.models import AnalyseDocument
            ct = ContentType.objects.get_for_model(Candidat)
            analyse = AnalyseDocument.objects.get(
                content_type=ct,
                object_id=candidat.particulier_id
            )
            elements = analyse.elements_cv
            if elements.competences:
                texte.extend(elements.competences)
            if elements.secteurs:
                texte.extend(elements.secteurs)
            if elements.niveau_etude:
                texte.append(elements.niveau_etude)
            if elements.postes_occupes:
                texte.extend(elements.postes_occupes[:5])
            print(f"   📄 Source vecteur: ElementsCVExtraits")
        except:
            pass

        # 2. CVGenere.donnees_cv
        if not texte:
            cv_genere = CVGenere.objects.filter(
                utilisateur=candidat.particulier.user,
                fichier_pdf__isnull=False
            ).order_by('-date_generation').first()

            if cv_genere and cv_genere.donnees_cv:
                d = cv_genere.donnees_cv
                competences = d.get('competences', [])
                experiences = d.get('experiences', [])
                formations = d.get('formations', [])

                if competences:
                    texte.extend([
                        c.get('nom', c) if isinstance(c, dict) else c
                        for c in competences
                    ])
                if experiences:
                    texte.extend([
                        e.get('poste', '') if isinstance(e, dict) else e
                        for e in experiences
                    ])
                if formations:
                    texte.extend([
                        f.get('diplome', '') if isinstance(f, dict) else f
                        for f in formations
                    ])
                print(f"   📄 Source vecteur: CVGenere #{cv_genere.id}")

        # 3. Champs Candidat directement
        if not texte:
            if candidat.competences:
                texte.extend([c.strip() for c in candidat.competences.split(',')])
            if candidat.secteur_recherche:
                texte.append(candidat.secteur_recherche)
            if candidat.niveauEtude:
                texte.append(candidat.niveauEtude)
            if candidat.niveauLangues:
                texte.append(candidat.niveauLangues)
            print(f"   📄 Source vecteur: champs Candidat")

        if not texte:
            texte = ["candidat", "emploi", "travail"]

        texte_complet = " ".join(str(t) for t in texte if t)
        doc = self.nlp(texte_complet)
        return doc.vector

    def get_vecteur_offre(self, offre):
        """
        Génère un vecteur sémantique pour une OffreEmploi
        Priorité : ElementsOffreExtraits → champs OffreEmploi
        """
        texte = []

        # 1. ElementsOffreExtraits (offre scrapée analysée)
        try:
            from django.contrib.contenttypes.models import ContentType
            from analyse_ia.models import AnalyseDocument
            ct = ContentType.objects.get_for_model(OffreEmploi)
            analyse = AnalyseDocument.objects.get(
                content_type=ct,
                object_id=offre.id
            )
            elements = analyse.elements_offre
            if elements.competences_detectees:
                texte.extend(elements.competences_detectees)
            if elements.secteurs_detectes:
                texte.extend(elements.secteurs_detectes)
            if elements.niveau_etude_detecte:
                texte.append(elements.niveau_etude_detecte)
            print(f"   📄 Source vecteur offre: ElementsOffreExtraits")
        except:
            pass

        # 2. Champs OffreEmploi directement
        if not texte:
            if offre.competences_requises:
                texte.extend(offre.competences_requises)
            if offre.titre:
                texte.append(offre.titre)
            if offre.description:
                texte.append(offre.description[:500])
            if offre.missions:
                texte.append(offre.missions[:300])
            if offre.profil_recherche:
                texte.append(offre.profil_recherche[:300])
            if offre.niveau_etude_requis:
                texte.append(offre.niveau_etude_requis)
            texte.append(offre.get_secteur_display())
            print(f"   📄 Source vecteur offre: champs DB")

        if not texte:
            texte = ["offre", "emploi", "poste"]

        texte_complet = " ".join(str(t) for t in texte if t)
        doc = self.nlp(texte_complet)
        return doc.vector

    # ==========================================
    # SIMILARITÉ COSINUS — même que moteur entreprise
    # ==========================================

    def calculer_similarite(self, vecteur_1, vecteur_2):
        """Calcule la similarité cosinus entre deux vecteurs"""
        if vecteur_1 is None or vecteur_2 is None:
            return 0.0

        norm_1 = np.linalg.norm(vecteur_1)
        norm_2 = np.linalg.norm(vecteur_2)

        if norm_1 == 0 or norm_2 == 0:
            return 0.0

        return float(np.dot(vecteur_1, vecteur_2) / (norm_1 * norm_2))

    # ==========================================
    # SCORING STRUCTURÉ
    # ==========================================

    def score_experience(self, candidat, offre):
        """Compare l'expérience du candidat avec celle requise"""
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
        else:
            return 0.2

    def score_localisation(self, candidat, offre):
        """Compare la localisation du candidat avec celle de l'offre"""
        if candidat.mobilite:
            return 1.0
        if not candidat.localisation_recherche or not offre.ville:
            return 0.5
        if candidat.localisation_recherche.lower() in offre.ville.lower():
            return 1.0
        elif offre.pays.lower() == 'burkina faso':
            return 0.7
        else:
            return 0.3

    # ==========================================
    # RECOMMANDATION PRINCIPALE
    # ==========================================

    def recommander_pour_candidat(self, candidat_id, limit=10):
        """Génère les recommandations pour un candidat"""
        print(f"\n{'='*60}")
        print(f"🎯 RECOMMANDATIONS POUR CANDIDAT #{candidat_id}")
        print(f"{'='*60}")

        # 1. Récupérer le candidat
        try:
            candidat = Candidat.objects.get(particulier_id=candidat_id)
        except Candidat.DoesNotExist:
            print(f"❌ Candidat #{candidat_id} introuvable")
            return []

        print(f"👤 {candidat.prenom} {candidat.nom}")

        # 2. Vecteur du candidat
        vecteur_candidat = self.get_vecteur_candidat(candidat)

        # 3. Récupérer les offres actives publiées
        offres = OffreEmploi.objects.filter(
            est_active=True,
            statut='PUBLIEE'
        )
        print(f"\n📋 {offres.count()} offres disponibles")

        recommandations = []

        for offre in offres:
            # Vecteur de l'offre
            vecteur_offre = self.get_vecteur_offre(offre)

            # Similarité sémantique (70%)
            similarite = self.calculer_similarite(vecteur_candidat, vecteur_offre)

            # Scores structurés (30%)
            s_experience = self.score_experience(candidat, offre)
            s_localisation = self.score_localisation(candidat, offre)

            # Score global
            score_global = (
                similarite    * 0.70 +
                s_experience  * 0.20 +
                s_localisation * 0.10
            )

            if score_global >= self.seuil_minimum:
                recommandations.append({
                    'offre': offre,
                    'score_global': round(score_global, 3),
                    'score_semantique': round(similarite, 3),
                    'score_experience': round(s_experience, 3),
                    'score_localisation': round(s_localisation, 3),
                    'competences_match': [],
                    'competences_manquantes': [],
                })

        # 4. Trier par score
        recommandations.sort(key=lambda x: x['score_global'], reverse=True)
        print(f"\n✅ {len(recommandations)} offres pertinentes trouvées")

        # 5. Sauvegarder en DB
        compteur = 0
        for reco in recommandations[:limit]:
            obj, created = RecommandationEmploi.objects.update_or_create(
                candidat=candidat,
                offre=reco['offre'],
                defaults={
                    'score_global': reco['score_global'],
                    'score_competences': reco['score_semantique'],
                    'score_experience': reco['score_experience'],
                    'score_formation': 0.0,
                    'score_secteur': 0.0,
                    'score_localisation': reco['score_localisation'],
                    'competences_match': reco['competences_match'],
                    'competences_manquantes': reco['competences_manquantes'],
                }
            )
            compteur += 1
            print(f"  {'✅' if created else '🔄'} {reco['offre'].titre[:40]} "
                  f"→ {reco['score_global']:.0%}")

        print(f"\n🏁 {compteur} recommandations sauvegardées")
        return recommandations[:limit]

    def recommander_pour_tous_candidats(self):
        """Génère les recommandations pour tous les candidats"""
        candidats = Candidat.objects.all()
        print("="*60)
        print(f"👥 RECOMMANDATIONS POUR {candidats.count()} CANDIDATS")
        print("="*60)

        total = 0
        for candidat in candidats:
            recos = self.recommander_pour_candidat(candidat.particulier_id)
            total += len(recos)
            print("-" * 60)

        print(f"\n🎉 TOTAL: {total} recommandations générées")


# ==========================================
# POINT D'ENTRÉE
# ==========================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Moteur de recommandation emploi')
    parser.add_argument('--candidat', type=int, help="ID du candidat")
    parser.add_argument('--seuil', type=float, default=0.3, help="Seuil de similarité (0-1)")
    parser.add_argument('--tous', action='store_true', help="Tous les candidats")

    args = parser.parse_args()

    moteur = MoteurRecommandationEmploi()
    moteur.seuil_minimum = args.seuil

    if args.tous:
        moteur.recommander_pour_tous_candidats()
    elif args.candidat:
        try:
            moteur.recommander_pour_candidat(args.candidat)
        except Exception as e:
            print(f"❌ Erreur: {e}")
    else:
        print("Usage:")
        print("  --candidat 1       → recommandations pour candidat #1")
        print("  --tous             → tous les candidats")
        print("  --seuil 0.4        → changer le seuil")