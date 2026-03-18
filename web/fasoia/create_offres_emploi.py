# create_offres_emploi_complet.py
import os
import django
import random
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
django.setup()

from myAppli.models import OffreEmploi, Recruteur
from django.utils import timezone

def create_recruteurs_if_needed():
    """Crée des recruteurs de test si nécessaire"""
    from myAppli.models import Particulier, Recruteur
    
    if Recruteur.objects.count() > 0:
        print(f"👥 {Recruteur.objects.count()} recruteurs déjà existants")
        return
    
    print("👥 Création de recruteurs de test...")
    
    # Récupérer des particuliers existants
    particuliers = Particulier.objects.all()
    
    if not particuliers:
        print("❌ Aucun particulier trouvé. Veuillez d'abord créer des utilisateurs.")
        return
    
    organisations = [
        ("Orange Burkina", "Télécoms"),
        ("Coris Bank", "Finance"),
        ("SONABEL", "Énergie"),
        ("Faso Digital", "Technologies"),
        ("Talentis RH", "Recrutement"),
        ("Emploi Service", "Services"),
    ]
    
    count = 0
    for i, (org, secteur) in enumerate(organisations):
        if i < len(particuliers):
            recruteur, created = Recruteur.objects.get_or_create(
                particulier=particuliers[i],
                defaults={
                    'organisation': org,
                    'secteur': secteur,
                    'typeStructure': random.choice(['PME', 'Grande entreprise', 'Startup']),
                    'poste_occupe': random.choice(['DRH', 'Recruteur', 'Responsable RH']),
                }
            )
            if created:
                count += 1
                print(f"  ✅ Recruteur créé: {org}")
    
    print(f"  ✅ {count} recruteurs créés")

def create_offres_emploi():
    print("🚀 Création des offres d'emploi...")
    
    # Récupérer tous les recruteurs existants
    recruteurs = Recruteur.objects.all()
    
    if not recruteurs:
        print("⚠️ Aucun recruteur trouvé, les offres seront sans recruteur")
    
    # Liste des entreprises pour les offres sans recruteur
    entreprises = [
        "Orange Burkina", "Moov Africa", "Coris Bank", "Ecobank", 
        "Société Générale", "TotalEnergies", "Air Liquide", "Bolloré",
        "SONABEL", "ONEA", "Faso Digital", "Startup 241", "InnovaTech",
        "AfricSearch", "Talentis", "Emploi Service"
    ]
    
    # Liste des titres d'emploi
    titres = [
        "Développeur Python Django",
        "Développeur Full Stack JavaScript",
        "Ingénieur DevOps",
        "Chef de projet IT",
        "Administrateur Systèmes et Réseaux",
        "Data Scientist",
        "Analyste Programmeur",
        "Community Manager",
        "Chargé de communication",
        "Comptable",
        "Responsable RH",
        "Assistant de direction",
        "Commercial B2B",
        "Technicien de maintenance",
        "Ingénieur génie civil",
        "Architecte",
        "Chef de chantier",
        "Infirmier",
        "Médecin généraliste",
        "Enseignant",
        "Formateur en informatique"
    ]
    
    # Descriptions
    descriptions = [
        "Nous recherchons un professionnel passionné pour rejoindre notre équipe dynamique.",
        "Dans le cadre de notre expansion, nous recrutons un talent pour renforcer nos équipes.",
        "Rejoignez une entreprise innovante et participez à des projets challengeants.",
        "Offre d'emploi pour un profil expérimenté souhaitant évoluer dans un environnement stimulant.",
        "Opportunité unique de carrière au sein d'un groupe international.",
        "Recherchons candidat motivé avec un bon esprit d'équipe.",
        "Poste à pourvoir immédiatement dans une structure en pleine croissance.",
    ]
    
    # Missions
    missions_list = [
        "Développer et maintenir les applications",
        "Participer aux réunions clients",
        "Rédiger la documentation technique",
        "Assurer le suivi des projets",
        "Former les nouveaux collaborateurs",
        "Gérer les relations avec les fournisseurs",
        "Optimiser les processus existants",
        "Analyser les besoins utilisateurs",
    ]
    
    # Compétences
    competences_pool = [
        "Python", "Django", "JavaScript", "React", "Angular", "Vue.js",
        "Java", "Spring Boot", "PHP", "Symfony", "Laravel",
        "SQL", "PostgreSQL", "MySQL", "MongoDB",
        "Docker", "Kubernetes", "AWS", "Azure",
        "Git", "Jira", "Confluence",
        "Gestion de projet", "SCRUM", "Agile",
        "Communication", "Travail d'équipe", "Leadership",
        "Français", "Anglais", "Espagnol"
    ]
    
    # Localisations
    localisations = [
        "Ouagadougou, Burkina Faso",
        "Bobo-Dioulasso, Burkina Faso",
        "Abidjan, Côte d'Ivoire",
        "Dakar, Sénégal",
        "Bamako, Mali",
        "Cotonou, Bénin",
        "Lomé, Togo",
        "Niamey, Niger",
        "Paris, France",
        "Montréal, Canada"
    ]
    
    # Types de contrat
    types_contrat = ['CDI', 'CDD', 'Stage', 'Alternance', 'Freelance']
    
    # Niveaux d'expérience
    niveaux_exp = ['Débutant', 'Intermédiaire', 'Confirmé', 'Expert']
    
    # Statuts
    statuts = ['BROUILLON', 'PUBLIEE', 'FERMEE', 'EXPIREE']
    
    # Sources - Respect de ton modèle
    sources = ['RECRUTEUR', 'SCRAPING', 'ADMIN', 'API']
    
    # Distribution des sources
    source_weights = {
        'RECRUTEUR': 0.6,  # 60% - Publiées par recruteur
        'SCRAPING': 0.25,  # 25% - Importées automatiquement
        'ADMIN': 0.1,      # 10% - Créées par admin
        'API': 0.05,       # 5% - Importées via API
    }
    
    count = 0
    
    # Créer 30 offres d'emploi
    for i in range(30):
        # Choisir un recruteur aléatoire (parfois None)
        recruteur = random.choice(recruteurs) if recruteurs and random.random() > 0.3 else None
        
        # Choisir une source selon la distribution
        source = random.choices(
            population=list(source_weights.keys()),
            weights=list(source_weights.values())
        )[0]
        
        # Générer une date aléatoire dans les 30 derniers jours
        date_pub = timezone.now() - timedelta(days=random.randint(1, 30))
        
        # Date limite aléatoire (entre aujourd'hui et +30 jours)
        date_limite = timezone.now().date() + timedelta(days=random.randint(1, 30))
        
        # Sélectionner 3-5 compétences aléatoires
        competences_requises = random.sample(competences_pool, random.randint(3, 5))
        competences_souhaitees = random.sample(competences_pool, random.randint(2, 4))
        
        # Salaire aléatoire
        salaire_min = random.randint(200000, 500000)
        salaire_max = salaire_min + random.randint(100000, 500000)
        
        # Titre aléatoire
        titre = random.choice(titres)
        
        # Ajouter un suffixe parfois
        if random.random() > 0.5:
            titre += f" {random.choice(['H/F', 'Junior', 'Senior', 'Confirmé'])}"
        
        # Description
        description = random.choice(descriptions)
        description += "\n\n" + random.choice(descriptions)
        
        # Missions
        missions = "\n".join([f"- {m}" for m in random.sample(missions_list, random.randint(3, 5))])
        
        # Profil recherché
        profil = "Profil recherché :\n"
        profil += f"- {random.randint(2, 5)} ans d'expérience minimum\n"
        profil += "- Formation Bac+5 ou équivalent\n"
        profil += "- Autonomie et rigueur\n"
        profil += "- Bonnes capacités relationnelles"
        
        try:
            offre = OffreEmploi.objects.create(
                recruteur=recruteur,
                source=source,
                source_url=f"https://emploiburkina.com/offre-{i}" if source in ['SCRAPING', 'API'] else "",
                date_importation=timezone.now() if source in ['SCRAPING', 'API'] else None,
                titre=titre,
                description=description,
                missions=missions,
                profil_recherche=profil,
                localisation=random.choice(localisations),
                teletravail=random.choice([True, False]),
                type_contrat=random.choice(types_contrat),
                salaire_min=salaire_min if random.random() > 0.3 else None,
                salaire_max=salaire_max if random.random() > 0.3 else None,
                salaire_affiche=f"{salaire_min} - {salaire_max} FCFA/mois" if random.random() > 0.5 else "À négocier",
                niveau_experience=random.choice(niveaux_exp),
                annees_experience_min=random.randint(0, 5),
                competences_requises=competences_requises,
                competences_souhaitees=competences_souhaitees,
                niveau_etude_requis=random.choice(["Bac+2", "Bac+3", "Bac+5", "Master", "Doctorat", ""]),
                date_publication=date_pub,
                date_limite=date_limite if random.random() > 0.3 else None,
                statut=random.choice(statuts),
                est_active=random.choice([True, False]),
                nombre_vues=random.randint(0, 500),
                nombre_candidatures=random.randint(0, 50),
            )
            count += 1
            source_display = dict(OffreEmploi.SOURCES).get(source, source)
            recruteur_info = offre.recruteur.organisation if offre.recruteur else "Sans recruteur"
            print(f"  ✅ {i+1:2d}. {offre.titre[:30]}... - {recruteur_info} - [{source_display}]")
            
        except Exception as e:
            print(f"  ❌ Erreur pour {titre}: {e}")
    
    print(f"\n📊 Total: {count} offres d'emploi créées")

if __name__ == '__main__':
    print("="*60)
    print("🏢 CRÉATION D'OFFRES D'EMPLOI")
    print("="*60)
    
    create_recruteurs_if_needed()
    create_offres_emploi()
    
    print("\n✅ Terminé!")
    print(f"📈 Total dans la base: {OffreEmploi.objects.count()} offres")