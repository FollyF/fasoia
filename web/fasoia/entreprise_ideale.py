#!/usr/bin/env python
import os
import django
import sys

# Configuration pour FASOIA
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
django.setup()

from myAppli.models import Entreprise
from django.contrib.auth.models import User
from django.db import transaction

def creer_entreprise_ideale():
    """
    Crée l'entreprise idéale avec un compte utilisateur pour se connecter à FASOIA
    Version avec champs tronqués pour respecter max_length
    """
    
    # Vérifier si l'email existe déjà
    if User.objects.filter(email="entrepriseideale@gmail.com").exists():
        print("⚠️  Un utilisateur avec cet email existe déjà !")
        return None, None
    
    # Vérifier si l'entreprise existe déjà
    if Entreprise.objects.filter(raisonSociale="GUIC SA").exists():
        print("⚠️  L'entreprise idéale existe déjà dans la base !")
        return None, None
    
    try:
        with transaction.atomic():
            # 1. CRÉER L'UTILISATEUR DJANGO
            username = "entreprise_ideale"
            email = "entrepriseideale@gmail.com"
            password = "rosaline"
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name="Direction",
                last_name="Générale",
                is_staff=False,
                is_active=True
            )
            print(f"✅ Utilisateur créé: {username}")
            
            # 2. CRÉER L'ENTREPRISE LIÉE - Version avec champs tronqués
            entreprise = Entreprise(
                user=user,
                nom="Direction",
                prenom="Générale",
                email=email,
                telephone="+226 70 12 34 56",
                typeProfil="ENTREPRISE",
                statut="ACTIF",
                
                # === CHAMPS CORRIGÉS POUR RESPECTER LES LIMITES ===
                
                # max_length=100
                raisonSociale="GUIC SA",  # Raccourci au lieu de "Groupe UEMOA Ingénierie & Conseil (GUIC SA)"
                
                # max_length=100
                domaineActive="Ingénierie, BTP, Numérique, Conseil",
                
                # max_length=300 - COMPÉTENCES CONDENSÉES
                competencesCles=(
                    "Construction bâtiments publics, Aménagement urbain, Génie civil, "
                    "Routes, Ponts, Assainissement, Hydraulique, Systèmes d'information, "
                    "Datacenters, Cybersécurité, Réseaux électriques, Énergies solaires, "
                    "Études faisabilité, Audit, Conseil"
                ),
                
                # max_length=100
                localisation="Ouagadougou, Burkina Faso",
                
                taille=180,
                
                # TextField - PAS DE LIMITE
                description=(
                    "Leader régional en ingénierie pluridisciplinaire avec 18 ans d'expertise "
                    "en BTP, infrastructures, transformation numérique et conseil stratégique. "
                    "Certifiée ISO 27001, ISO 9001 et ISO 14001. Partenaire des institutions UEMOA. "
                    "Présents dans 8 pays, 180 collaborateurs, CA 10 milliards FCFA."
                ),
                
                site_web="https://www.groupe-uemoa-ingenierie.ci",
                annee_creation=2008,
                
                chiffre_affaires=10000000000,
                capital_social=800000000,
                
                # JSONField - PAS DE LIMITE
                pays_intervention=[
                    "Bénin", "Burkina Faso", "Côte d'Ivoire", "Mali", 
                    "Niger", "Sénégal", "Togo", "Guinée-Bissau"
                ],
                
                rayon_action=2500,
                annees_experience=18,
                nb_projets_realises=450,
                
                # TextField - PAS DE LIMITE
                references=(
                    "CNHUP Allada (12 Mds FCFA), Pistes rurales Atacora (8 Mds), "
                    "Datacenter CAM (1,2 Md), SDSI UEMOA, Réseaux électriques SBEE (3,5 Mds), "
                    "Mini-réseaux solaires Guinée-Bissau (4 Mds), Audit PAPVS"
                ),
                
                # JSONField - PAS DE LIMITE
                certifications=[
                    "ISO 9001:2015", "ISO 14001:2015", "ISO 45001:2018",
                    "ISO 27001:2022", "Agrément BTP catégorie A", "Agrément UEMOA"
                ],
                
                agrements=[
                    "Agrément BTP", "Agrément UEMOA", "Agrément SBEE"
                ],
                
                # JSONField - PAS DE LIMITE
                mots_cles_index=[
                    "construction", "travaux", "aménagement", "bâtiment", "route", "pont",
                    "assainissement", "hydraulique", "système d'information", "numérique",
                    "datacenter", "réseau", "sécurité", "cybersécurité", "énergie",
                    "électrique", "solaire", "étude", "audit", "conseil", "UEMOA"
                ],
                
                types_opportunites=["APPEL_OFFRE", "AMI"],
                montant_min=100000000,
                montant_max=5000000000,
                nb_recommandations_envoyees=450,
                nb_candidatures_emises=120,
                taux_succes=35.0,
                profil_complet=True
            )
            
            entreprise.save()
            
            # Sauvegarder les mots-clés
            entreprise.sauvegarder_mots_cles()
            
            print("\n" + "="*60)
            print("🎉 SUCCÈS ! L'entreprise idéale a été créée dans FASOIA")
            print("="*60)
            print(f"🔐 IDENTIFIANTS DE CONNEXION :")
            print(f"   👤 Username: {username}")
            print(f"   📧 Email: {email}")
            print(f"   🔑 Mot de passe: {password}")
            print(f"\n🏢 ENTREPRISE :")
            print(f"   ID: {entreprise.id}")
            print(f"   Raison sociale: {entreprise.raisonSociale}")
            print(f"   Compétences: {entreprise.competencesCles[:100]}...")
            
            return user, entreprise
            
    except Exception as e:
        print(f"❌ Erreur lors de la création : {e}")
        # Afficher plus de détails sur l'erreur
        import traceback
        traceback.print_exc()
        return None, None

def tester_connexion():
    """Teste si la connexion fonctionne"""
    from django.contrib.auth import authenticate
    
    username = "entreprise_ideale"
    password = "rosaline"
    
    user = authenticate(username=username, password=password)
    if user is not None:
        print("\n✅ TEST DE CONNEXION RÉUSSI !")
        try:
            entreprise = user.entreprise
            print(f"   Entreprise: {entreprise.raisonSociale}")
        except:
            pass
        return True
    else:
        print("\n❌ TEST DE CONNEXION ÉCHOUÉ")
        return False

if __name__ == "__main__":
    print("🚀 CRÉATION DE L'ENTREPRISE IDÉALE DANS FASOIA")
    print("="*60)
    
    user, entreprise = creer_entreprise_ideale()
    
    if user and entreprise:
        print("\n" + "="*60)
        print("🧪 TEST DE CONNEXION...")
        tester_connexion()
    else:
        print("\n❌ La création a échoué.")