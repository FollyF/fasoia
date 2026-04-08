#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moteur de recommandation sémantique avec spaCy
Version 2.0 - Matching intelligent sans mots-clés exacts
"""

import os
import sys
from collections import Counter

if __name__ == "__main__":
    import django
    current_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_path)
    if project_root not in sys.path:
        sys.path.append(project_root)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
    django.setup()

from django.contrib.contenttypes.models import ContentType
from myAppli.models import Entreprise, Offre_uemoa, Ami_uemoa
from analyse_ia.models import AnalyseDocument, Recommandation
import spacy

class MoteurRecommandationSemantique:
    """
    Moteur de recommandation utilisant la similarité sémantique
    Pas besoin de mots-clés exacts !
    """
    
    def __init__(self):
        print("Chargement du modèle NLP...")
        try:
            self.nlp = spacy.load("fr_core_news_md")
            print("✅ Modèle chargé (avec vecteurs sémantiques)")
        except:
            print("⚠️ Modèle medium non trouvé, utilisation du modèle small")
            self.nlp = spacy.load("fr_core_news_sm")
        
        self.seuil_minimum = 0.4  # Seuil de similarité (0 à 1)
    
    def get_vecteur_entreprise(self, entreprise):
        """Génère un vecteur sémantique pour l'entreprise"""
        texte = []
        
        # 1. Domaine d'activité
        if entreprise.domaineActive:
            texte.append(entreprise.domaineActive)
        
        # 2. Mots-clés existants (si présents)
        if entreprise.mots_cles_index:
            texte.extend(entreprise.mots_cles_index)
        
        # 3. Description si disponible
        if hasattr(entreprise, 'description') and entreprise.description:
            texte.append(entreprise.description[:500])
        
        # Si vide, utiliser des mots génériques
        if not texte:
            texte = ["prestation", "service", "entreprise"]
        
        texte_complet = " ".join(texte)
        doc = self.nlp(texte_complet)
        return doc.vector
    
    def get_vecteur_opportunite(self, analyse):
        """Génère un vecteur sémantique pour l'opportunité"""
        texte = []
        
        # 1. Catégorie (AMI, APPEL_OFFRE, etc.)
        if analyse.categorie:
            texte.append(analyse.categorie)
        
        # 2. Mots-clés de l'analyse
        if analyse.mots_cles:
            mots = list(analyse.mots_cles.keys())[:20]  # Top 20 mots
            texte.extend(mots)
        
        # 3. Texte extrait (les 1000 premiers caractères)
        if analyse.texte_extrait:
            texte.append(analyse.texte_extrait[:1000])
        
        texte_complet = " ".join(texte)
        doc = self.nlp(texte_complet)
        return doc.vector
    
    def calculer_similarite(self, vecteur_ent, vecteur_offre):
        """Calcule la similarité cosinus entre deux vecteurs"""
        import numpy as np
        
        if vecteur_ent is None or vecteur_offre is None:
            return 0.0
        
        norm_ent = np.linalg.norm(vecteur_ent)
        norm_offre = np.linalg.norm(vecteur_offre)
        
        if norm_ent == 0 or norm_offre == 0:
            return 0.0
        
        return float(np.dot(vecteur_ent, vecteur_offre) / (norm_ent * norm_offre))
    
    def recommander_pour_entreprise(self, entreprise, limit=20):
        """Génère des recommandations sémantiques"""
        print(f"\n🔍 Recommandations sémantiques pour {entreprise.raisonSociale}")
        print("-" * 60)
        
        # Vecteur de l'entreprise
        vecteur_entreprise = self.get_vecteur_entreprise(entreprise)
        
        # Récupérer toutes les analyses
        analyses = AnalyseDocument.objects.all()
        print(f"📊 {analyses.count()} opportunités à analyser")
        
        recommandations = []
        
        for analyse in analyses:
            # Vecteur de l'opportunité
            vecteur_offre = self.get_vecteur_opportunite(analyse)
            
            # Calcul de similarité
            similarite = self.calculer_similarite(vecteur_entreprise, vecteur_offre)
            
            if similarite >= self.seuil_minimum:
                # Déterminer le type d'opportunité
                offre_ct = ContentType.objects.get_for_model(Offre_uemoa)
                if analyse.content_type == offre_ct:
                    opp_type = "Offre_uemoa"
                    try:
                        obj = Offre_uemoa.objects.get(id=analyse.object_id)
                        description = obj.description[:100] if obj.description else ""
                    except:
                        continue
                else:
                    opp_type = "Ami_uemoa"
                    try:
                        obj = Ami_uemoa.objects.get(id=analyse.object_id)
                        description = obj.description[:100] if obj.description else ""
                    except:
                        continue
                
                recommandations.append({
                    'analyse': analyse,
                    'type': opp_type,
                    'objet': obj,
                    'score': round(similarite, 3),
                    'description': description
                })
        
        # Trier par score
        recommandations.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"📌 {len(recommandations)} opportunités pertinentes trouvées (seuil: {self.seuil_minimum})")
        
        # Sauvegarder les recommandations
        compteur = 0
        for reco in recommandations[:limit]:
            rec, created = Recommandation.objects.update_or_create(
                entreprise=entreprise,
                opportunite_type=reco['type'],
                opportunite_id=reco['objet'].id,
                defaults={
                    'score_global': reco['score'],
                    'analyse': reco['analyse'],
                    'score_competences': reco['score'],
                    'score_geographique': reco['score'] * 0.8,
                    'score_financier': reco['score'] * 0.7,
                }
            )
            compteur += 1
            if compteur <= 10:
                print(f"  ✅ {reco['type']}#{reco['objet'].id} - Similarité: {reco['score']:.2f}")
                print(f"     {reco['description'][:80]}...")
        
        print(f"\n✅ {compteur} recommandations sauvegardées")
        return recommandations[:limit]
    
    def recommander_pour_toutes_entreprises(self):
        """Génère les recommandations pour toutes les entreprises"""
        entreprises = Entreprise.objects.all()
        print("="*60)
        print(f"🏢 RECOMMANDATIONS SÉMANTIQUES POUR {entreprises.count()} ENTREPRISES")
        print("="*60)
        
        total_recos = 0
        for entreprise in entreprises:
            recos = self.recommander_pour_entreprise(entreprise)
            total_recos += len(recos)
            print("-" * 60)
        
        print(f"\n🎉 TOTAL: {total_recos} recommandations générées")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Moteur de recommandation sémantique')
    parser.add_argument('--entreprise', type=int, help='ID de l\'entreprise')
    parser.add_argument('--seuil', type=float, default=0.4, help='Seuil de similarité (0-1)')
    
    args = parser.parse_args()
    
    moteur = MoteurRecommandationSemantique()
    moteur.seuil_minimum = args.seuil
    
    if args.entreprise:
        try:
            entreprise = Entreprise.objects.get(id=args.entreprise)
            moteur.recommander_pour_entreprise(entreprise)
        except Entreprise.DoesNotExist:
            print(f"❌ Entreprise #{args.entreprise} non trouvée")
    else:
        moteur.recommander_pour_toutes_entreprises()