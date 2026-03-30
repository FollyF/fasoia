# analyse_ia/moteur_recommandation.py

import os
import sys
from collections import Counter

if __name__=="__main__":
    import django
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
        Compare les compétences de l'entreprise avec les mots-clés de l'offre
        """
        if not analyse or not analyse.mots_cles:
            return 0.0
        
        mots_entreprise = set(entreprise.mots_cles_index or [])
        mots_offre = set(analyse.mots_cles.keys())
        
        if not mots_offre:
            return 0.0
        
        # Compétences communes
        communs = mots_entreprise & mots_offre
        
        if not communs:
            return 0.0
        
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
        Compare le lieu de l'offre avec les pays d'intervention de l'entreprise
        """
        if not elements or not elements.lieu:
            return 0.5  # Score neutre si pas d'info
        
        lieu_offre = elements.lieu.lower()
        pays_entreprise = [p.lower() for p in entreprise.pays_intervention or []]
        
        # Si l'entreprise n'a pas défini de pays d'intervention
        if not pays_entreprise:
            return 0.5
        
        # Vérifier si le lieu est dans les pays d'intervention
        for pays in pays_entreprise:
            if pays in lieu_offre or lieu_offre in pays:
                return 1.0  # Match parfait
        
        return 0.3  # Pas de match géographique
    
    def calculer_score_financier(self, entreprise, elements):
        """
        Score basé sur la capacité financière
        Compare le montant de l'offre avec le chiffre d'affaires de l'entreprise
        """
        if not elements or not elements.montant_estime:
            return 0.5  # Score neutre si pas de montant
        
        try:
            montant = float(elements.montant_estime)
            ca_entreprise = float(entreprise.chiffre_affaires or 0)
        except (ValueError, TypeError):
            return 0.3
        
        if ca_entreprise <= 0:
            return 0.3  # Pas d'info financière fiable
        
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
        Compare le secteur de l'offre avec le domaine d'activité de l'entreprise
        """
        if not analyse or not analyse.categorie:
            return 0.5
        
        categorie_offre = analyse.categorie.lower()
        domaine_entreprise = entreprise.domaineActive.lower()
        
        # Mots-clés du secteur
        mots_secteur = {
            'informatique': ['informatique', 'digital', 'logiciel', 'développement', 'programmation', 'site', 'application'],
            'environnement': ['environnement', 'déchet', 'pollution', 'écologie', 'étude', 'impact'],
            'btp': ['construction', 'bâtiment', 'travaux', 'génie civil', 'route', 'infrastructure'],
            'conseil': ['conseil', 'audit', 'étude', 'consultant', 'formation', 'accompagnement'],
            'maintenance': ['maintenance', 'installation', 'dépannage', 'équipement', 'industriel'],
        }
        
        # Vérifier d'abord par catégorie
        for secteur, mots in mots_secteur.items():
            if secteur in categorie_offre:
                # Vérifier si l'entreprise opère dans ce secteur
                if any(mot in domaine_entreprise for mot in mots):
                    return 1.0
                break
        
        # Si pas de match par catégorie, vérifier par mots-clés
        mots_offre = set(analyse.mots_cles.keys() if analyse.mots_cles else [])
        for secteur, mots in mots_secteur.items():
            if any(mot in mots_offre for mot in mots) and any(mot in domaine_entreprise for mot in mots):
                return 0.8
        
        return 0.3
    
    def recommander_pour_entreprise(self, entreprise, limit=10):
        """
        Génère les recommandations pour une entreprise spécifique
        """
        print(f"\n🔍 Recommandations pour {entreprise.raisonSociale}")
        print("-" * 60)
        
        # Récupérer toutes les analyses avec leurs éléments
        analyses = AnalyseDocument.objects.select_related(
            'elements'
        ).filter(
            elements__isnull=False  # Seulement celles avec éléments extraits
        )
        
        print(f"📊 {analyses.count()} opportunités analysées")
        
        recommandations = []
        
        for analyse in analyses:
            # Récupérer les éléments extraits
            elements = getattr(analyse, 'elements', None)
            if not elements:
                continue
            
            # Identifier le type d'opportunité
            obj = analyse.document_source
            if isinstance(obj, Offre_uemoa):
                type_opp = "OFFRE"
            elif isinstance(obj, Ami_uemoa):
                type_opp = "AMI"
            else:
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
            
            # Ne garder que les recommandations avec un score minimum
            if score_global >= 0.3:  # Seuil minimum de pertinence
                recommandations.append({
                    'analyse': analyse,
                    'elements': elements,
                    'type': type_opp,
                    'objet': obj,
                    'scores': {
                        'competences': score_comp,
                        'geographique': score_geo,
                        'financier': score_fin,
                        'secteur': score_sec,
                        'global': round(score_global, 2)
                    },
                    'competences_match': competences_match
                })
        
        # Trier par score global décroissant
        recommandations.sort(key=lambda x: x['scores']['global'], reverse=True)
        
        print(f"\n📌 {len(recommandations)} opportunités pertinentes trouvées")
        
        # Sauvegarder les top recommandations
        for i, reco in enumerate(recommandations[:limit]):
            obj = reco['objet']
            
            # Déterminer le type et l'ID de l'opportunité
            if isinstance(obj, Offre_uemoa):
                opp_type = 'Offre_uemoa'
                opp_id = obj.id
                description = obj.description[:100]
            else:  # Ami_uemoa
                opp_type = 'Ami_uemoa'
                opp_id = obj.id
                description = obj.description[:100]
            
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
            
            # Afficher un résumé
            status = "✨ NOUVELLE" if created else "📝 MISE À JOUR"
            print(f"\n  {status} {opp_type} #{opp_id}")
            print(f"     Score global: {reco['scores']['global']:.2f}")
            print(f"     Détail: C:{reco['scores']['competences']:.2f} "
                  f"G:{reco['scores']['geographique']:.2f} "
                  f"F:{reco['scores']['financier']:.2f} "
                  f"S:{reco['scores']['secteur']:.2f}")
            if reco['competences_match']:
                print(f"     Compétences match: {', '.join(reco['competences_match'][:5])}")
            if reco['elements'].lieu:
                print(f"     Lieu: {reco['elements'].lieu}")
            print(f"     {description}")
        
        return recommandations[:limit]
    
    def recommander_pour_toutes_entreprises(self):
        """
        Génère les recommandations pour toutes les entreprises
        """
        entreprises = Entreprise.objects.all()
        print("="*60)
        print(f"🏢 GÉNÉRATION DES RECOMMANDATIONS POUR {entreprises.count()} ENTREPRISES")
        print("="*60)
        
        total_recommandations = 0
        
        for i, entreprise in enumerate(entreprises, 1):
            print(f"\n[{i}/{entreprises.count()}] ", end="")
            recos = self.recommander_pour_entreprise(entreprise)
            total_recommandations += len(recos)
            print("\n" + "-"*60)
        
        print("\n" + "="*60)
        print(f"✅ TOTAL: {total_recommandations} recommandations générées")
        print("="*60)

def afficher_stats():
    """
    Affiche des statistiques sur les recommandations
    """
    from django.db.models import Count, Avg
    
    total_recos = Recommandation.objects.count()
    if total_recos == 0:
        print("📊 Aucune recommandation en base")
        return
    
    print("\n" + "="*60)
    print("📊 STATISTIQUES DES RECOMMANDATIONS")
    print("="*60)
    
    print(f"\n📦 Total: {total_recos} recommandations")
    
    # Moyenne des scores
    avg_score = Recommandation.objects.aggregate(Avg('score_global'))['score_global__avg']
    print(f"📈 Score moyen: {avg_score:.2f}")
    
    # Répartition par type d'opportunité
    print(f"\n📌 Par type:")
    for type_opp in ['Offre_uemoa', 'Ami_uemoa']:
        count = Recommandation.objects.filter(opportunite_type=type_opp).count()
        if count > 0:
            print(f"   {type_opp}: {count}")
    
    # Top 5 entreprises
    print(f"\n🏢 Top entreprises:")
    top_entreprises = Recommandation.objects.values(
        'entreprise__raisonSociale'
    ).annotate(
        total=Count('id'),
        avg_score=Avg('score_global')
    ).order_by('-total')[:5]
    
    for e in top_entreprises:
        print(f"   {e['entreprise__raisonSociale']}: {e['total']} recos (score moy. {e['avg_score']:.2f})")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Moteur de recommandation FasoIA')
    parser.add_argument('--stats', action='store_true', help='Afficher les statistiques')
    parser.add_argument('--entreprise', type=int, help='ID de l\'entreprise à traiter')
    
    args = parser.parse_args()
    
    if args.stats:
        afficher_stats()
    elif args.entreprise:
        moteur = MoteurRecommandation()
        try:
            entreprise = Entreprise.objects.get(id=args.entreprise)
            moteur.recommander_pour_entreprise(entreprise)
        except Entreprise.DoesNotExist:
            print(f"❌ Entreprise #{args.entreprise} non trouvée")
    else:
        moteur = MoteurRecommandation()
        moteur.recommander_pour_toutes_entreprises()
        afficher_stats()