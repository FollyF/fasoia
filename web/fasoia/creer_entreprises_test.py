# creer_entreprises_test.py

import django
import os
import sys
from datetime import date

sys.path.append('/media/folly/28DC9DDE2CA969AD/DOCS/SEA/UJKZ/COURS/MEMOIRE/fasoia/web/fasoia')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
django.setup()

from myAppli.models import Entreprise

entreprises_test = [
    {
        # Informations Utilisateur (héritage)
        'nom': 'Kouassi',
        'prenom': 'Jean',
        'email': 'contact@informatique.ci',
        'telephone': '+2252722456789',
        'typeProfil': 'ENTREPRISE',
        'statut': 'ACTIF',
        
        # Informations Entreprise
        'raisonSociale': 'INFORMATIQUE CONSEIL AFRIQUE',
        'domaineActive': 'Informatique, Développement web, Conseil IT',
        'competencesCles': 'Python, Django, React, Java, PHP, Base de données, Cloud, Sécurité',
        'localisation': 'Abidjan, Côte d\'Ivoire',
        'taille': 25,
        
        # Nouveaux champs pour matching
        'description': 'Cabinet de conseil en informatique spécialisé dans le développement d\'applications web et mobiles pour les administrations publiques.',
        'site_web': 'https://www.ica.ci',
        'annee_creation': 2015,
        'chiffre_affaires': 150000000,
        'capital_social': 25000000,
        'pays_intervention': ['Côte d\'Ivoire', 'Burkina Faso', 'Sénégal'],
        'rayon_action': 1000,
        'annees_experience': 8,
        'nb_projets_realises': 45,
        'references': 'UEMOA, BOAD, Ministère de l\'Economie Numérique',
        'certifications': ['ISO 27001', 'Qualité ISO 9001'],
        'types_opportunites': ['APPEL_OFFRE', 'AMI'],
        'montant_min': 10000000,
        'montant_max': 200000000,
    },
    {
        'nom': 'Ouedraogo',
        'prenom': 'Mariam',
        'email': 'contact@environnement.bf',
        'telephone': '+22625345678',
        'typeProfil': 'ENTREPRISE',
        'statut': 'ACTIF',
        
        'raisonSociale': "BUREAU D'ÉTUDES ENVIRONNEMENT",
        'domaineActive': 'Environnement, Études d\'impact, Gestion des déchets',
        'competencesCles': 'Études environnementales, Gestion des déchets, Analyse pollution, Évaluation environnementale, Énergies renouvelables',
        'localisation': 'Ouagadougou, Burkina Faso',
        'taille': 8,
        
        'description': "Bureau d'études spécialisé dans les études d'impact environnemental et la gestion durable des déchets.",
        'site_web': 'https://www.bee.bf',
        'annee_creation': 2018,
        'chiffre_affaires': 45000000,
        'capital_social': 5000000,
        'pays_intervention': ['Burkina Faso', 'Mali', 'Niger'],
        'rayon_action': 500,
        'annees_experience': 5,
        'nb_projets_realises': 28,
        'references': 'Projet GIZ, Banque Mondiale, PNUD',
        'certifications': ['Agrément Ministère Environnement'],
        'types_opportunites': ['AMI', 'APPEL_OFFRE'],
        'montant_min': 5000000,
        'montant_max': 80000000,
    },
    {
        'nom': 'Diop',
        'prenom': 'Amadou',
        'email': 'contact@conseil.sn',
        'telephone': '+2213389012345',
        'typeProfil': 'ENTREPRISE',
        'statut': 'ACTIF',
        
        'raisonSociale': 'CABINET CONSEIL EN GESTION',
        'domaineActive': 'Conseil, Audit, Formation, Gestion de projet',
        'competencesCles': 'Audit organisationnel, Formation, Renforcement de capacités, Gestion de projet, Évaluation de politiques publiques',
        'localisation': 'Dakar, Sénégal',
        'taille': 5,
        
        'description': 'Cabinet conseil spécialisé dans l\'accompagnement des institutions publiques et privées.',
        'site_web': 'https://www.ccg.sn',
        'annee_creation': 2020,
        'chiffre_affaires': 80000000,
        'capital_social': 10000000,
        'pays_intervention': ['Sénégal', 'Mauritanie', 'Guinée'],
        'rayon_action': 800,
        'annees_experience': 3,
        'nb_projets_realises': 15,
        'references': 'Projet USAID, Union Européenne',
        'certifications': ['Agrément Consultant National'],
        'types_opportunites': ['AMI'],
        'montant_min': 3000000,
        'montant_max': 50000000,
    },
    {
        'nom': 'Hounsou',
        'prenom': 'Prosper',
        'email': 'contact@btp.bj',
        'telephone': '+22921304050',
        'typeProfil': 'ENTREPRISE',
        'statut': 'ACTIF',
        
        'raisonSociale': 'GROUPE BATIMENT TRAVAUX PUBLICS',
        'domaineActive': 'BTP, Construction, Génie civil',
        'competencesCles': 'Génie civil, Construction bâtiments, Travaux routiers, Rénovation, VRD',
        'localisation': 'Cotonou, Bénin',
        'taille': 45,
        
        'description': 'Entreprise de BTP réalisant des projets d\'infrastructures publiques et privées.',
        'site_web': 'https://www.gbtp.bj',
        'annee_creation': 2010,
        'chiffre_affaires': 350000000,
        'capital_social': 50000000,
        'pays_intervention': ['Bénin', 'Togo', 'Nigeria'],
        'rayon_action': 300,
        'annees_experience': 12,
        'nb_projets_realises': 85,
        'references': 'Construction de 5 écoles, 2 marchés, 10 km de routes',
        'certifications': ['Agrément BTP Catégorie A', 'ISO 9001'],
        'types_opportunites': ['APPEL_OFFRE'],
        'montant_min': 20000000,
        'montant_max': 500000000,
    },
    {
        'nom': 'Lawson',
        'prenom': 'Koffi',
        'email': 'contact@maintenance.tg',
        'telephone': '+22822203040',
        'typeProfil': 'ENTREPRISE',
        'statut': 'ACTIF',
        
        'raisonSociale': 'SERVICE & MAINTENANCE INDUSTRIELLE',
        'domaineActive': 'Maintenance industrielle, Installation équipements',
        'competencesCles': 'Maintenance industrielle, Installation équipements, Dépannage, Fourniture pièces, Climatisation',
        'localisation': 'Lomé, Togo',
        'taille': 12,
        
        'description': 'Spécialiste de la maintenance des équipements industriels et installations techniques.',
        'site_web': 'https://www.smi.tg',
        'annee_creation': 2019,
        'chiffre_affaires': 60000000,
        'capital_social': 15000000,
        'pays_intervention': ['Togo', 'Bénin', 'Ghana'],
        'rayon_action': 200,
        'annees_experience': 4,
        'nb_projets_realises': 35,
        'references': 'Maintenance de 3 usines, Installation clim dans 2 hôpitaux',
        'certifications': ['Agrément Maintenance Industrielle'],
        'types_opportunites': ['APPEL_OFFRE', 'AMI'],
        'montant_min': 5000000,
        'montant_max': 100000000,
    },
]

def creer_entreprises():
    print("="*60)
    print("🏢 CRÉATION D'ENTREPRISES TEST")
    print("="*60)
    
    creees = 0
    for data in entreprises_test:
        # Extraire les mots-clés des compétences
        mots_cles = [mot.strip().lower() for mot in data['competencesCles'].split(',')]
        data['mots_cles_index'] = mots_cles
        
        entreprise, creee = Entreprise.objects.update_or_create(
            email=data['email'],
            defaults=data
        )
        
        if creee:
            creees += 1
            print(f"✅ {data['raisonSociale']} créée")
        else:
            print(f"📝 {data['raisonSociale']} mise à jour")
    
    print(f"\n🎉 {creees} nouvelles entreprises créées")
    
    # Afficher le résumé
    print("\n📊 ENTREPRISES DISPONIBLES:")
    for e in Entreprise.objects.all():
        print(f"\n   • {e.raisonSociale}")
        print(f"     Contact: {e.prenom} {e.nom}")
        print(f"     📍 {e.localisation}")
        print(f"     💰 CA: {e.chiffre_affaires} FCFA")
        print(f"     🔑 Compétences: {', '.join(e.mots_cles_index[:5])}...")

if __name__ == "__main__":
    creer_entreprises()