# analyse_ia/moteur_recommandation.py

import django
import os
import sys
from collections import Counter

sys.path.append('/media/folly/28DC9DDE2CA969AD/DOCS/SEA/UJKZ/COURS/MEMOIRE/fasoia/web/fasoia')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from myAppli.models import Entreprise, Offre_uemoa, Ami_uemoa
from analyse_ia.models import AnalyseDocument, ElementsExtraits, Recommandation

class MoteurRecommandation:
    """
    Moteur qui calcule les scores de pertinence entre entreprises et opportunités
    """
    
    def __init__(self):
        self.poids = {
            'competences': 0.4,    # 40% du score total
            'geographique': 0.3,    # 30% du score total
            'financier': 0.2,       # 20% du score total
            'secteur': 0.1,         # 10% du score total
        }
    
    def calculer_score_competences(self, entreprise, analyse):
        """
        Score basé sur les compétences (mots-clés)
        """
        if not analyse or not analyse.mots_cles:
            return 0.0
        
        mots_entreprise = set(entreprise.mots_cles_index or [])
        mots_offre = set(analyse.mots_cles.keys())
        
        if not mots_offre:
            return 0.0
        
        # Compétences communes
        communs = mots_entreprise & mots_offre
        
        # Compétences pondérées par leur importance dans l'offre
        score = 0.0
        for mot in communs:
            poids = analyse.mots_cles.get(mot, 0.1)
            score += poids * 2  # Bonus pour les compétences importantes
        
        # Normaliser entre 0 et 1
        max_possible = sum(analyse.mots_cles.values()) * 2
        if max_possible > 0:
            score = min(score / max_possible, 1.0)
        
        return round(score, 2)
    
    def calculer_score_geographique(self, entreprise, elements):
        """
        Score basé sur la localisation
        """
        if not elements or not elements.lieu:
            return 0.5  # Score neutre si pas d'info
        
        lieu_offre = elements.lieu.lower()
        pays_entreprise = [p.lower() for p in entreprise.pays_intervention or []]
        
        # Vérifier si le lieu est dans les pays d'intervention
        for pays in pays_entreprise:
            if pays in lieu_offre or lieu_offre in pays:
                return 1.0  # Match parfait
        
        return 0.3  # Pas de match géographique
    
    def calculer_score_financier(self, entreprise, elements):
        """
        Score basé sur la capacité financière
        """
        if not elements or not elements.montant_estime:
            return 0.5  # Score neutre si pas de montant
        
        montant = float(elements.montant_estime)
        ca_entreprise = float(entreprise.chiffre_affaires or 0)
        
        if ca_sequence == 0:
            return 0.3  # Pas d'info financière
        
        # Règle: le montant ne doit pas dépasser 50% du CA
        ratio = montant / ca_entreprise
        
        if ratio <= 0.1:
            return 1.0  # Très largement dans les capacités
        elif ratio <= 0.3:
            return 0.8  # Confortable
        elif ratio <= 0.5:
            return 0.6  # Limite acceptable
        else:
            return 0.2  # Trop élevé
    
    def calculer_score_secteur(self, entreprise, analyse):
        """
        Score basé sur le secteur d'activité
        """
        if not analyse or not analyse.categorie:
            return 0.5
        
        categorie_offre = analyse.categorie.lower()
        domaine_entreprise = entreprise.domaineActive.lower()
        
        # Mots-clés du secteur
        mots_secteur = {
            'informatique': ['informatique', 'digital', 'logiciel', 'développement'],
            'environnement': ['environnement', 'déchet', 'pollution', 'écologie'],
            'btp': ['construction', 'bâtiment', 'travaux', 'génie civil'],
            'conseil': ['conseil', 'audit', 'étude', 'consultant'],
        }
        
        for secteur, mots in mots_secteur.items():
            if secteur in categorie_offre:
                # Vérifier si l'entreprise opère dans ce secteur
                if any(mot in domaine_entreprise for mot in mots):
                    return 1.0
                break
        
        return 0.3
    
    def recommander_pour_entreprise(self, entreprise, limit=10):
        """
        Génère les recommandations pour une entreprise
        """
        print(f"\n🔍 Recommandations pour {entreprise.raisonSociale}")
        print("-" * 50)
        
        # Récupérer toutes les analyses avec leurs éléments
        analyses = AnalyseDocument.objects.select_related(
            'elements'
        ).filter(
            elements__isnull=False  # Seulement celles avec éléments extraits
        )
        
        recommandations = []
        
        for analyse in analyses:
            # Récupérer les éléments extraits
            elements = getattr(analyse, 'elements', None)
            if not elements:
                continue
            
            # Calculer les sous-scores
            score_comp = self.calculer_score_competences(entreprise, analyse)
            score_geo = self.calculer_score_geographique(entreprise, elements)
            score_fin = self.calculer_score_financier(entreprise, elements)
            score_sec = self.calculer_score_secteur(entreprise, analyse)
            
            # Score global pondéré
            score_global = (
                self.poids['competences'] * score_comp +
                self.poids['geographique'] * score_geo +
                self.poids['financier'] * score_fin +
                self.poids['secteur'] * score_sec
            )
            
            # Compétences communes
            competences_match = list(
                set(entreprise.mots_cles_index or []) & 
                set(analyse.mots_cles.keys() if analyse.mots_cles else [])
            )[:10]
            
            recommandations.append({
                'analyse': analyse,
                'elements': elements,
                'scores': {
                    'competences': score_comp,
                    'geographique': score_geo,
                    'financier': score_fin,
                    'secteur': score_sec,
                    'global': round(score_global, 2)
                },
                'competences_match': competences_match
            })
        
        # Trier par score global
        recommandations.sort(key=lambda x: x['scores']['global'], reverse=True)
        
        # Sauvegarder les top recommandations
        for i, reco in enumerate(recommandations[:limit]):
            obj = reco['analyse'].document_source
            
            # Déterminer le type et l'ID de l'opportunité
            if isinstance(obj, Offre_uemoa):
                opp_type = 'Offre_uemoa'
                opp_id = obj.id
            else:
                opp_type = 'Ami_uemoa'
                opp_id = obj.id
            
            # Sauvegarder ou mettre à jour
            rec, created = Recommandation.objects.update_or_create(
                entreprise=entreprise,
                opportunite_type=opp_type,
                opportunite_id=opp_id,
                defaults={
                    'score_competences': reco['scores']['competences'],
                    'score_geographique': reco['scores']['geographique'],
                    'score_financier': reco['scores']['financier'],
                    'score_global': reco['scores']['global'],
                    'competences_match': reco['competences_match'],
                    'analyse': reco['analyse'],
                }
            )
            
            print(f"\n  {'✨' if created else '📝'} {opp_type} #{opp_id}")
            print(f"     Score: {reco['scores']['global']}")
            print(f"     Compétences: {reco['competences_match'][:3]}")
            print(f"     Lieu: {reco['elements'].lieu or 'N/A'}")
        
        return recommandations[:limit]
    
    def recommander_pour_toutes_entreprises(self):
        """
        Génère les recommandations pour toutes les entreprises
        """
        entreprises = Entreprise.objects.all()
        print(f"🏢 {entreprises.count()} entreprises à traiter")
        
        for entreprise in entreprises:
            self.recommander_pour_entreprise(entreprise)
            print("\n" + "="*50)

if __name__ == "__main__":
    print("="*60)
    print("🚀 MOTEUR DE RECOMMANDATION")
    print("="*60)
    
    moteur = MoteurRecommandation()
    
    # Recommander pour une entreprise spécifique
    # entreprise = Entreprise.objects.first()
    # moteur.recommander_pour_entreprise(entreprise)
    
    # Ou pour toutes les entreprises
    moteur.recommander_pour_toutes_entreprises()