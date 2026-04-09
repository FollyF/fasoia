from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators import csrf
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.conf import settings
from urllib.parse import quote
from django.utils import timezone
from django.core.files.base import ContentFile
from django.http import FileResponse
from datetime import datetime

import os
import json
import csv
import logging
import re

from .forms import InscriptionForm, ConnexionForm
from .models import *
from analyse_ia.models import *
from .services.generateur_cv_public import GenerateurCVPublic
from .generateur import GenerateurDocument
logger = logging.getLogger(__name__)

def test(request):
    return render(request, 'myAppli/test.html')

def home(request):
    """
    Page d'accueil avec les dernières opportunités
    """
    # Récupérer les 5 dernières offres et AMI
    dernieres_offres = Offre_uemoa.objects.all().order_by('-date_scraping')[:5]
    derniers_amis = Ami_uemoa.objects.all().order_by('-date_scraping')[:5]
    derniers_emplois = OffreEmploi.objects.all().order_by('-date_scraping')[:5]
    
    # Compter le total
    total_opportunites = Offre_uemoa.objects.count() + Ami_uemoa.objects.count() + OffreEmploi.objects.count()
    
    context = {
        'dernieres_offres': dernieres_offres,
        'derniers_amis': derniers_amis,
        'derniers_emplois': derniers_emplois,
        'total_opportunites': total_opportunites,
    }
    return render(request, 'myAppli/home.html', context)

def opportunites(request):
    """
    Page publique - Affiche TOUTES les opportunités sans filtre
    """
    offres_uemoa = Offre_uemoa.objects.all().order_by('-date_scraping')
    amis_uemoa = Ami_uemoa.objects.all().order_by('-date_scraping')
    offres_emploi = OffreEmploi.objects.filter(statut='PUBLIEE', est_active=True).order_by('-date_publication')
    
    context = {
        'offres': offres_uemoa,
        'amis': amis_uemoa,
        'offres_emploi': offres_emploi,
        'total_opportunites': offres_uemoa.count() + amis_uemoa.count() + offres_emploi.count(),
    }
    return render(request, 'myAppli/opportunites.html', context)


@login_required
def dashboard_opportunites(request):
    """
    Page dashboard - Affiche les opportunités filtrées selon le profil utilisateur
    """
    offres_uemoa = Offre_uemoa.objects.none()
    amis_uemoa = Ami_uemoa.objects.none()
    offres_emploi = OffreEmploi.objects.none()
    
    # ===== PROFIL ENTREPRISE =====
    if hasattr(request.user, 'entreprise'):
        entreprise = request.user.entreprise
        offres_uemoa = Offre_uemoa.objects.all()
        amis_uemoa = Ami_uemoa.objects.all()
        
    # ===== PROFIL CANDIDAT =====
    elif hasattr(request.user, 'particulier') and hasattr(request.user.particulier, 'candidat'):
        candidat = request.user.particulier.candidat
        offres_emploi = OffreEmploi.objects.filter(statut='PUBLIEE', est_active=True)
        
    # ===== PROFIL RECRUTEUR =====
    elif hasattr(request.user, 'particulier') and hasattr(request.user.particulier, 'recruteur'):
        recruteur = request.user.particulier.recruteur
        offres_emploi = OffreEmploi.objects.filter(
            recruteur=recruteur,
            statut='PUBLIEE'
        ).order_by('-date_publication')
    
    # ===== PARTICULIER SANS RÔLE =====
    elif hasattr(request.user, 'particulier'):
        offres_emploi = OffreEmploi.objects.filter(statut='PUBLIEE', est_active=True).order_by('-date_publication')
    
    total_opportunites = offres_uemoa.count() + amis_uemoa.count() + offres_emploi.count()
    
    context = {
        'offre': offres_uemoa,
        'ami': amis_uemoa,
        'offres_emploi': offres_emploi,
        'total_opportunites': total_opportunites,
    }
    return render(request, 'myAppli/dashboard_opportunites.html', context)


@require_http_methods(["GET", "POST"])
@csrf_protect
def inscription(request):
    """
    Vue d'inscription - Gère les 3 types de profils
    """
    if request.user.is_authenticated:
    # Utilisateur déjà connecté - rediriger vers son dashboard
        if hasattr(request.user, 'entreprise'):
            return redirect('myAppli:dashboard_entreprise')
        elif hasattr(request.user, 'particulier'):
            particulier = request.user.particulier
            if hasattr(particulier, 'candidat') and hasattr(particulier, 'recruteur'):
                return redirect('myAppli:dashboard_particulier')
            elif hasattr(particulier, 'candidat'):
                return redirect('myAppli:dashboard_candidat')
            elif hasattr(particulier, 'recruteur'):
                return redirect('myAppli:dashboard_recruteur')
            else:
                return redirect('myAppli:dashboard_particulier')
        return redirect('myAppli:home')

    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        
        if form.is_valid():
            try:
                user = form.save()
                
                # Connexion automatique après inscription
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                # Message personnalisé selon le type de profil
                profile_type = form.cleaned_data['profile_type']
                
                if profile_type == 'entreprise':
                    entreprise = user.entreprise
                    messages.success(
                        request, 
                        f"Bienvenue {entreprise.raisonSociale} ! Votre compte entreprise a été créé. Complétez votre profil pour commencer."
                    )
                    logger.info(f"Nouvelle inscription entreprise : {user.email} - {entreprise.raisonSociale}")
                    return redirect('myAppli:dashboard_entreprise')
                    
                elif profile_type == 'particulier':
                    particulier = user.particulier
                    messages.success(
                        request, 
                        f"Bienvenue {particulier.prenom} {particulier.nom} ! Votre compte a été créé avec succès."
                    )
                    logger.info(f"Nouvelle inscription particulier : {user.email}")
                    return redirect('myAppli:dashboard_particulier')
                    
                elif profile_type == 'partenaire':
                    # Si partenaire = recruteur ou autre
                    partenaire = user.recruteur  # À adapter selon ton modèle
                    messages.success(
                        request, 
                        f"Bienvenue ! Votre compte partenaire a été créé avec succès."
                    )
                    logger.info(f"Nouvelle inscription partenaire : {user.email}")
                    return redirect('myAppli:home')
                
            except Exception as e:
                logger.error(f"Erreur lors de l'inscription : {str(e)}")
                messages.error(request, "Une erreur est survenue. Veuillez réessayer.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        # Initialiser le formulaire avec le type par défaut
        initial_data = {'profile_type': 'particulier'}
        form = InscriptionForm(initial=initial_data)
    
    return render(request, 'myAppli/inscription.html', {
        'form': form,
        'title': 'Inscription',
        'no_header_footer': True
    })


@require_http_methods(["GET", "POST"])
@csrf_protect
def connexion(request):
    """
    Vue de connexion
    """
    print("="*50)
    print("VUE CONNEXION APPELEE")
    print(f"Utilisateur authentifié: {request.user.is_authenticated}")
    print(f"Utilisateur: {request.user}")
    print(f"Méthode: {request.method}")
    print("="*50)

    if request.user.is_authenticated:
    # Utilisateur déjà connecté - rediriger vers son dashboard
        if hasattr(request.user, 'entreprise'):
            return redirect('myAppli:dashboard_entreprise')
        elif hasattr(request.user, 'particulier'):
            particulier = request.user.particulier
            if hasattr(particulier, 'candidat') and hasattr(particulier, 'recruteur'):
                return redirect('myAppli:dashboard_particulier')
            elif hasattr(particulier, 'candidat'):
                return redirect('myAppli:dashboard_candidat')
            elif hasattr(particulier, 'recruteur'):
                return redirect('myAppli:dashboard_recruteur')
            else:
                return redirect('myAppli:dashboard_particulier')
        return redirect('myAppli:home')
 
    if request.method == 'POST':
        form = ConnexionForm(request, data=request.POST)
        
        if form.is_valid():
            user = form.get_user()
            
            # Gestion du "remember me"
            remember_me = form.cleaned_data.get('remember_me', False)
            if not remember_me:
                request.session.set_expiry(0)
            
            login(request, user)
            
            # Message personnalisé selon le type de profil
            if hasattr(user, 'entreprise'):
                messages.success(request, f"Bon retour parmi nous, {user.entreprise.raisonSociale} !")
            elif hasattr(user, 'particulier'):
                messages.success(request, f"Bon retour parmi nous, {user.particulier.prenom} !")
            elif hasattr(user, 'recruteur'):
                messages.success(request, f"Bon retour parmi nous, {user.recruteur.organisation} !")
            else:
                messages.success(request, f"Bon retour parmi nous, {user.email} !")
            
            logger.info(f"Connexion réussie : {user.email}")
            
            # Redirection selon le type de profil
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            elif hasattr(user, 'entreprise'):
                return redirect('myAppli:dashboard_entreprise')
            elif hasattr(user, 'particulier'):
                particulier = user.particulier
                if hasattr(particulier, 'candidat') and hasattr(particulier, 'recruteur'):
                    return redirect('myAppli:dashboard_particulier')
                elif hasattr(particulier, 'candidat'):
                    return redirect('myAppli:dashboard_candidat')
                elif hasattr(particulier, 'recruteur'):
                    return redirect('myAppli:dashboard_recruteur')
                else:
                    return redirect('myAppli:dashboard_particulier')
            else:
                return redirect('myAppli:home')
        else:
            logger.warning(f"Tentative de connexion échouée pour : {request.POST.get('username', 'inconnu')}")
            messages.error(request, "Email ou mot de passe incorrect")
    else:
        form = ConnexionForm()
    
    return render(request, 'myAppli/connexion.html', {
        'form': form,
        'title': 'Connexion',
        'no_header_footer': True
    })

@login_required
def deconnexion(request):
    """
    Vue de déconnexion
    """
    email = request.user.email
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès")
    logger.info(f"Déconnexion : {email}")
    return redirect('myAppli:connexion')


@login_required
def profil(request):
    """
    Vue du profil utilisateur (générique)
    """
    context = {'user': request.user}
    
    # Ajouter les données spécifiques selon le type
    if hasattr(request.user, 'entreprise'):
        context['entreprise'] = request.user.entreprise
        context['profil_type'] = 'entreprise'
    elif hasattr(request.user, 'particulier'):
        context['particulier'] = request.user.particulier
        context['profil_type'] = 'particulier'
    elif hasattr(request.user, 'recruteur'):
        context['recruteur'] = request.user.recruteur
        context['profil_type'] = 'recruteur'
    
    return render(request, 'myAppli/profil.html', context)

@login_required
def dashboard_entreprise(request):
    """
    Tableau de bord spécifique pour les entreprises
    """
    # Vérifier que l'utilisateur est bien une entreprise
    if not hasattr(request.user, 'entreprise'):
        messages.error(request, "Accès réservé aux entreprises")
        return redirect('myAppli:home')
    
    entreprise = request.user.entreprise
    
    # ===== CODE POUR LE CALCUL DE PROGRESSION =====
    champs_obligatoires = [
        'domaineActive', 'localisation', 'competencesCles',
        'pays_intervention', 'chiffre_affaires', 'types_opportunites'
    ]
    
    champs_remplis = 0
    details_champs = {}
    
    for champ in champs_obligatoires:
        valeur = getattr(entreprise, champ)
        
        if champ == 'types_opportunites' or champ == 'pays_intervention':
            est_rempli = bool(valeur)
        elif champ == 'chiffre_affaires':
            est_rempli = valeur is not None and valeur > 0
        else:
            est_rempli = bool(valeur and str(valeur).strip())
        
        if est_rempli:
            champs_remplis += 1
            details_champs[champ] = True
        else:
            details_champs[champ] = False
    
    total_champs = len(champs_obligatoires)
    pourcentage = int((champs_remplis / total_champs) * 100) if total_champs > 0 else 0
    champs_manquants = total_champs - champs_remplis
    profil_complet = (champs_manquants == 0)
    
    champs_manquants_liste = []
    libelles_champs = {
        'domaineActive': "Domaine d'activité",
        'localisation': "Localisation",
        'competencesCles': "Compétences clés",
        'pays_intervention': "Pays d'intervention",
        'chiffre_affaires': "Chiffre d'affaires",
        'types_opportunites': "Types d'opportunités"
    }
    
    for champ in champs_obligatoires:
        if not details_champs[champ]:
            champs_manquants_liste.append(libelles_champs.get(champ, champ))
    
    # ===== CODE POUR LES RECOMMANDATIONS (CORRIGÉ) =====
    recommandations = []
    opportunites_correspondantes = 0
    recommandations_count = 0
    
    if profil_complet:
        try:
            from analyse_ia.models import Recommandation  # ← Correction ici !
            
            recommandations = Recommandation.objects.filter(
                entreprise=entreprise
            ).order_by('-score_global')[:10]
            
            recommandations_count = recommandations.count()
            opportunites_correspondantes = recommandations_count
            
        except Exception as e:
            print(f"Erreur lors du chargement des recommandations: {e}")
            recommandations = []
            recommandations_count = 0
            opportunites_correspondantes = 0
    
    return render(request, 'myAppli/dashboard_entreprise.html', {
        'entreprise': entreprise,
        'user': request.user,
        'pourcentage_completion': pourcentage,
        'champs_remplis': champs_remplis,
        'total_champs': total_champs,
        'champs_obligatoires_manquants': champs_manquants,
        'profil_complet': profil_complet,
        'champs_manquants_liste': champs_manquants_liste,
        'details_champs': details_champs,
        'recommandations': recommandations,
        'opportunites_correspondantes': opportunites_correspondantes,
        'recommandations_count': recommandations_count,
    })

@login_required
def dashboard_particulier(request):
    """
    Dashboard principal pour les particuliers
    Permet de choisir son rôle (candidat ou recruteur)
    """
    # Vérifier que l'utilisateur est bien un particulier
    if not hasattr(request.user, 'particulier'):
        messages.error(request, "Accès réservé aux particuliers")
        return redirect('myAppli:home')
    
    particulier = request.user.particulier
    
    # Vérifier si l'utilisateur a déjà des profils
    a_profil_candidat = hasattr(particulier, 'candidat')
    a_profil_recruteur = hasattr(particulier, 'recruteur')
    
    context = {
        'particulier': particulier,
        'a_profil_candidat': a_profil_candidat,
        'a_profil_recruteur': a_profil_recruteur,
    }
    
    return render(request, 'myAppli/dashboard_particulier.html', context)

@login_required
def dashboard_candidat(request):
    """
    Dashboard spécifique pour les demandeurs d'emploi
    """
    if not hasattr(request.user, 'particulier'):
        messages.error(request, "Accès non autorisé")
        return redirect('myAppli:home')
    
    particulier = request.user.particulier
    
    if not hasattr(particulier, 'candidat'):
        messages.warning(request, "Vous devez d'abord activer votre profil candidat")
        return redirect('myAppli:dashboard_particulier')
    
    candidat = particulier.candidat
    
    # Récupérer les offres recommandées
    offres_recommandees = OffreEmploi.objects.filter(
        statut='PUBLIEE',
        est_active=True
    ).order_by('-date_publication')[:10]
    
    # ===== CALCUL CORRIGÉ DE LA PROGRESSION =====
    # Liste de TOUS les champs à prendre en compte (particulier + candidat)
    champs_profil = [
        # Champs du Particulier
        ('nom', particulier.nom),
        ('prenom', particulier.prenom),
        ('email', particulier.email),
        ('telephone', particulier.telephone),
        ('date_naissance', particulier.date_naissance),
        ('adresse', particulier.adresse),
        ('ville', particulier.ville),
        ('pays', particulier.pays),
        
        # Champs du Candidat
        ('niveauEtude', candidat.niveauEtude),
        ('competences', candidat.competences),
        ('disponibilite', candidat.disponibilite),
        ('niveauLangues', candidat.niveauLangues),
        ('secteur_recherche', candidat.secteur_recherche),
        ('type_contrat_recherche', candidat.type_contrat_recherche),
        ('localisation_recherche', candidat.localisation_recherche),
        ('anneesExperiences', candidat.anneesExperiences),
        ('salaire_souhaite', candidat.salaire_souhaite),
        ('mobilite', candidat.mobilite),  # True/False donc toujours rempli
        ('cv', candidat.cv),
        ('lettre_motivation', candidat.lettre_motivation),
    ]
    
    # Compter les champs remplis
    champs_remplis = 0
    details_champs = {}
    
    for nom_champ, valeur in champs_profil:
        # Déterminer si le champ est considéré comme rempli
        if nom_champ == 'mobilite':
            # La mobilité est un boolean, toujours rempli (True ou False)
            est_rempli = True
        elif nom_champ in ['cv', 'lettre_motivation']:
            # Les fichiers sont considérés comme remplis si ils existent
            est_rempli = bool(valeur)
        elif nom_champ in ['anneesExperiences', 'salaire_souhaite']:
            # Les nombres : >0 est considéré comme rempli
            est_rempli = valeur is not None and valeur > 0
        elif nom_champ == 'date_naissance':
            # Date de naissance optionnelle
            est_rempli = bool(valeur)
        else:
            # Champs texte : non vides et non "None"
            est_rempli = bool(valeur and str(valeur).strip())
        
        if est_rempli:
            champs_remplis += 1
            details_champs[nom_champ] = True
        else:
            details_champs[nom_champ] = False
    
    total_champs = len(champs_profil)
    progression = int((champs_remplis / total_champs) * 100) if total_champs > 0 else 0
    
    # Définir les champs obligatoires (ceux avec * dans le formulaire)
    champs_obligatoires = [
        ('nom', particulier.nom),
        ('prenom', particulier.prenom),
        ('email', particulier.email),
        ('telephone', particulier.telephone),
        ('niveauEtude', candidat.niveauEtude),
        ('competences', candidat.competences),
        ('disponibilite', candidat.disponibilite),
        ('cv', candidat.cv),
    ]
    
    # Vérifier si tous les champs obligatoires sont remplis
    profil_complet = True
    champs_manquants = []
    
    for nom_champ, valeur in champs_obligatoires:
        if nom_champ in ['cv']:
            if not bool(valeur):
                profil_complet = False
                champs_manquants.append(nom_champ)
        else:
            if not bool(valeur and str(valeur).strip()):
                profil_complet = False
                champs_manquants.append(nom_champ)
    
    # Gérer l'affichage du formulaire
    show_form = not profil_complet or request.GET.get('edit') == 'true'
    
    # Si on vient juste d'enregistrer, on cache le formulaire
    if request.session.pop('profil_juste_complete', False):
        show_form = False
    
    # Libellés des champs pour l'affichage
    libelles_champs = {
        'nom': 'Nom',
        'prenom': 'Prénom',
        'email': 'Email',
        'telephone': 'Téléphone',
        'date_naissance': 'Date de naissance',
        'adresse': 'Adresse',
        'ville': 'Ville',
        'pays': 'Pays',
        'niveauEtude': "Niveau d'étude",
        'competences': 'Compétences',
        'disponibilite': 'Disponibilité',
        'niveauLangues': 'Niveau en langues',
        'secteur_recherche': 'Secteur recherché',
        'type_contrat_recherche': 'Type de contrat',
        'localisation_recherche': 'Localisation recherchée',
        'anneesExperiences': "Années d'expérience",
        'salaire_souhaite': 'Salaire souhaité',
        'mobilite': 'Mobilité',
        'cv': 'CV',
        'lettre_motivation': 'Lettre de motivation',
    }
    
    context = {
        'candidat': candidat,
        'particulier': particulier,
        'offres_recommandees': offres_recommandees,
        'progression': progression,
        'champs_remplis': champs_remplis,
        'total_champs': total_champs,
        'profil_complet': profil_complet,
        'champs_manquants': champs_manquants,
        'libelles_champs': libelles_champs,
        'details_champs': details_champs,
        'show_form': show_form,
    }
    
    return render(request, 'myAppli/dashboard_candidat.html', context)

@login_required
def dashboard_recruteur(request):
    """
    Dashboard spécifique pour les recruteurs
    """
    if not hasattr(request.user, 'particulier'):
        messages.error(request, "Accès non autorisé")
        return redirect('myAppli:home')
    
    particulier = request.user.particulier
    
    if not hasattr(particulier, 'recruteur'):
        messages.warning(request, "Vous devez d'abord activer votre profil recruteur")
        return redirect('myAppli:dashboard_particulier')
    
    recruteur = particulier.recruteur
    
    # Récupérer les offres publiées
    offres_publiees = OffreEmploi.objects.filter(recruteur=recruteur).order_by('-date_publication')
    
    # ===== CALCUL DE LA PROGRESSION =====
    champs_obligatoires = ['organisation', 'secteur', 'typeStructure', 'poste_occupe']
    champs_remplis = 0
    
    for champ in champs_obligatoires:
        valeur = getattr(recruteur, champ)
        if valeur and str(valeur).strip():
            champs_remplis += 1
    
    total_champs = len(champs_obligatoires)
    progression = int((champs_remplis / total_champs) * 100) if total_champs > 0 else 0
    profil_complet = (champs_remplis == total_champs)
    nombre = 120000

    print(f"🔍 Dashboard recruteur - profil_complet: {profil_complet}")
    
    # Statistiques
    stats = {
        'offres_publiees': offres_publiees.count(),
        'candidatures_recues': 0,
        'talents_recommandes': 0,
    }
    
    talents_recommandes = []
    
    # ===== CONTEXTE AVEC TOUTES LES VARIABLES =====
    context = {
        'recruteur': recruteur,
        'offres_publiees': offres_publiees,
        'talents_recommandes': talents_recommandes,
        'stats': stats,
        'progression': progression,
        'champs_remplis': champs_remplis,
        'total_champs': total_champs,
        'profil_complet': profil_complet,  # ← ESSENTIEL !
        'nombre': nombre
    }
    
    return render(request, 'myAppli/dashboard_recruteur.html', context)

@login_required
def activer_profil_candidat(request):
    """Active le profil candidat pour un particulier"""
    if not hasattr(request.user, 'particulier'):
        messages.error(request, "Vous devez être un particulier")
        return redirect('myAppli:home')
    
    particulier = request.user.particulier
    
    # Vérifier si le profil existe déjà
    if hasattr(particulier, 'candidat'):
        messages.info(request, "Vous avez déjà un profil candidat")
        return redirect('myAppli:dashboard_candidat')
    
    # Créer le profil candidat
    Candidat.objects.create(
        particulier=particulier,
        niveauEtude='',
        competences='',
        disponibilite='',
        secteur_recherche='',
        type_contrat_recherche='',
        localisation_recherche='',
        mobilite=False
    )
    
    messages.success(request, "Profil candidat activé avec succès !")
    return redirect('myAppli:dashboard_candidat')


@login_required
def activer_profil_recruteur(request):
    """Active le profil recruteur pour un particulier"""
    if not hasattr(request.user, 'particulier'):
        messages.error(request, "Vous devez être un particulier")
        return redirect('myAppli:home')
    
    particulier = request.user.particulier
    
    # Vérifier si le profil existe déjà
    if hasattr(particulier, 'recruteur'):
        messages.info(request, "Vous avez déjà un profil recruteur")
        return redirect('myAppli:dashboard_recruteur')
    
    # Créer le profil recruteur
    Recruteur.objects.create(
        particulier=particulier,
        organisation='',
        secteur='',
        typeStructure='',
        poste_occupe=''
    )
    
    messages.success(request, "Profil recruteur activé avec succès !")
    return redirect('myAppli:dashboard_recruteur')

@login_required
@require_http_methods(["POST"])
@csrf_protect
def completer_profil_candidat(request):
    """
    Vue pour enregistrer les modifications du profil candidat
    """
    print("="*50)
    print("DONNÉES REÇUES PROFIL CANDIDAT:")
    print(request.POST)
    print(request.FILES)
    print("="*50)
    
    if not hasattr(request.user, 'particulier'):
        messages.error(request, "Accès réservé aux particuliers")
        return redirect('myAppli:home')
    
    particulier = request.user.particulier
    
    if not hasattr(particulier, 'candidat'):
        messages.warning(request, "Vous devez d'abord activer votre profil candidat")
        return redirect('myAppli:dashboard_particulier')
    
    candidat = particulier.candidat
    
    try:
        # ===== MISE À JOUR DES CHAMPS DU PARTICULIER =====
        particulier.nom = request.POST.get('nom', particulier.nom)
        particulier.prenom = request.POST.get('prenom', particulier.prenom)
        particulier.email = request.POST.get('email', particulier.email)
        particulier.telephone = request.POST.get('telephone', particulier.telephone)
        
        # Date de naissance (optionnelle)
        date_naissance = request.POST.get('date_naissance')
        if date_naissance:
            particulier.date_naissance = datetime.strptime(date_naissance, '%Y-%m-%d').date()
        
        particulier.adresse = request.POST.get('adresse', particulier.adresse)
        particulier.ville = request.POST.get('ville', particulier.ville)
        particulier.pays = request.POST.get('pays', particulier.pays)
        
        # Sauvegarder le particulier
        particulier.save()
        print("✅ Particulier mis à jour")
        
        # ===== MISE À JOUR DES CHAMPS DU CANDIDAT =====
        # Gestion des chaînes vides pour les champs texte
        candidat.niveauEtude = request.POST.get('niveauEtude', '')
        candidat.competences = request.POST.get('competences', '')
        candidat.disponibilite = request.POST.get('disponibilite', '')
        candidat.niveauLangues = request.POST.get('niveauLangues', '')
        candidat.secteur_recherche = request.POST.get('secteur_recherche', '')
        candidat.type_contrat_recherche = request.POST.get('type_contrat_recherche', '')
        candidat.localisation_recherche = request.POST.get('localisation_recherche', '')
        
        # ✅ Gestion des nombres avec valeur par défaut 0
        annees = request.POST.get('anneesExperiences', '0')
        candidat.anneesExperiences = int(annees) if annees and annees.strip() else 0
        
        # ✅ Gestion du salaire (optionnel)
        salaire = request.POST.get('salaire_souhaite', '')
        if salaire and salaire.strip():
            try:
                candidat.salaire_souhaite = float(salaire)
            except ValueError:
                candidat.salaire_souhaite = None
        else:
            candidat.salaire_souhaite = None
        
        # ✅ Gestion de la mobilité (checkbox)
        candidat.mobilite = request.POST.get('mobilite') == 'on'
        
        # ✅ Gestion des fichiers
        if 'cv' in request.FILES:
            candidat.cv = request.FILES['cv']
        if 'lettre_motivation' in request.FILES:
            candidat.lettre_motivation = request.FILES['lettre_motivation']
        
        candidat.save()
        print("✅ Candidat mis à jour")
        
        messages.success(request, "Votre profil a été mis à jour avec succès !")
        
    except Exception as e:
        print(f"❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"Erreur lors de la sauvegarde : {str(e)}")
    
    return redirect('myAppli:dashboard_candidat')

@login_required
@require_http_methods(["POST"])
@csrf_protect
def completer_profil_recruteur(request):
    """
    Vue pour enregistrer les modifications du profil recruteur
    """
    print("="*50)
    print("DONNÉES REÇUES PROFIL RECRUTEUR:")
    print(request.POST)
    print("="*50)
    
    if not hasattr(request.user, 'particulier'):
        messages.error(request, "Accès réservé aux particuliers")
        return redirect('myAppli:home')
    
    particulier = request.user.particulier
    
    if not hasattr(particulier, 'recruteur'):
        messages.warning(request, "Vous devez d'abord activer votre profil recruteur")
        return redirect('myAppli:dashboard_particulier')
    
    recruteur = particulier.recruteur
    
    try:
        # Mise à jour des champs simples
        recruteur.organisation = request.POST.get('organisation', recruteur.organisation)
        recruteur.secteur = request.POST.get('secteur', recruteur.secteur)
        recruteur.typeStructure = request.POST.get('typeStructure', recruteur.typeStructure)
        recruteur.poste_occupe = request.POST.get('poste_occupe', recruteur.poste_occupe)
        
        # Traitement des secteurs recherchés
        secteurs_recherches = request.POST.get('secteurs_recherches', '')
        if secteurs_recherches and secteurs_recherches.strip():
            recruteur.secteurs_recherches = [s.strip() for s in secteurs_recherches.split(',') if s.strip()]
        else:
            recruteur.secteurs_recherches = []
        
        # Traitement des types de contrats
        types_contrats = request.POST.get('types_contrats_proposes', '')
        if types_contrats and types_contrats.strip():
            recruteur.types_contrats_proposes = [t.strip() for t in types_contrats.split(',') if t.strip()]
        else:
            recruteur.types_contrats_proposes = []
        
        recruteur.save()
        
        # ===== VÉRIFICATION DU PROFIL COMPLET =====
        champs_obligatoires = ['organisation', 'secteur', 'typeStructure', 'poste_occupe']
        champs_remplis = 0
        champs_manquants = []
        
        for champ in champs_obligatoires:
            valeur = getattr(recruteur, champ)
            if valeur and str(valeur).strip():
                champs_remplis += 1
            else:
                champs_manquants.append(champ)
        
        total_champs = len(champs_obligatoires)
        progression = int((champs_remplis / total_champs) * 100) if total_champs > 0 else 0
        profil_complet = (champs_remplis == total_champs)
        
        print(f"📊 Progression: {progression}% ({champs_remplis}/{total_champs})")
        print(f"✅ Profil complet: {profil_complet}")
        
        # Message personnalisé
        if profil_complet:
            messages.success(request, "🎉 Félicitations ! Votre profil recruteur est maintenant complet ! Vous pouvez maintenant publier des offres.")
        else:
            messages.success(request, f"Votre profil a été mis à jour ! Il vous manque : {', '.join(champs_manquants)}")
        
    except Exception as e:
        print(f"❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"Erreur : {str(e)}")
    
    return redirect('myAppli:dashboard_recruteur')

@login_required
@require_http_methods(["POST"])
@csrf_protect
def completer_profil_entreprise(request):
    """
    Vue pour enregistrer les modifications du profil entreprise
    """
    print("="*50)
    print("DONNÉES REÇUES:")
    print(request.POST)
    print("="*50)
    
    if not hasattr(request.user, 'entreprise'):
        messages.error(request, "Accès réservé aux entreprises")
        return redirect('myAppli:home')
    
    entreprise = request.user.entreprise
    
    try:
        # Mise à jour des champs simples
        entreprise.domaineActive = request.POST.get('domaineActive', '')
        entreprise.localisation = request.POST.get('localisation', '')
        entreprise.competencesCles = request.POST.get('competencesCles', '')
        
        # Gestion des nombres - NE PAS METTRE DE CHAÎNE VIDE
        taille = request.POST.get('taille')
        entreprise.taille = int(taille) if taille and taille.strip() else 0
        
        annee = request.POST.get('annee_creation')
        entreprise.annee_creation = int(annee) if annee and annee.strip() else None
        
        site_web = request.POST.get('site_web')
        entreprise.site_web = site_web if site_web else ''
        
        description = request.POST.get('description')
        entreprise.description = description if description else ''
        
        annees_exp = request.POST.get('annees_experience')
        entreprise.annees_experience = int(annees_exp) if annees_exp and annees_exp.strip() else 0
        
        nb_projets = request.POST.get('nb_projets_realises')
        entreprise.nb_projets_realises = int(nb_projets) if nb_projets and nb_projets.strip() else 0
        
        references = request.POST.get('references')
        entreprise.references = references if references else ''
        
        rayon = request.POST.get('rayon_action')
        entreprise.rayon_action = int(rayon) if rayon and rayon.strip() else None
        
        montant_min = request.POST.get('montant_min')
        entreprise.montant_min = float(montant_min) if montant_min and montant_min.strip() else None
        
        montant_max = request.POST.get('montant_max')
        entreprise.montant_max = float(montant_max) if montant_max and montant_max.strip() else None
        
        # Chiffre d'affaires (convertir en Decimal)
        ca = request.POST.get('chiffre_affaires')
        if ca and ca.strip():
            entreprise.chiffre_affaires = ca
        
        # Capital social
        cs = request.POST.get('capital_social')
        if cs and cs.strip():
            entreprise.capital_social = cs
        
        # Traitement des champs JSON (listes)
        # Pays d'intervention
        pays = request.POST.get('pays_intervention', '')
        if pays and pays.strip():
            entreprise.pays_intervention = [p.strip() for p in pays.split(',') if p.strip()]
        else:
            entreprise.pays_intervention = []
        
        # Certifications
        certifs = request.POST.get('certifications', '')
        if certifs and certifs.strip():
            entreprise.certifications = [c.strip() for c in certifs.split(',') if c.strip()]
        else:
            entreprise.certifications = []
        
        # Agréments
        agrements = request.POST.get('agrements', '')
        if agrements and agrements.strip():
            entreprise.agrements = [a.strip() for a in agrements.split(',') if a.strip()]
        else:
            entreprise.agrements = []
        
        # Types d'opportunités (select multiple)
        types_opportunites = request.POST.getlist('types_opportunites')
        if types_opportunites:
            entreprise.types_opportunites = list(types_opportunites)
        else:
            entreprise.types_opportunites = []
        
        print(f"AVANT SAUVEGARDE: domaineActive={entreprise.domaineActive}")
        print(f"AVANT SAUVEGARDE: annee_creation={entreprise.annee_creation}")
        
        # Sauvegarder
        entreprise.save()
        print("APRÈS SAUVEGARDE: OK")
        
        # Mettre à jour l'index des mots-clés
        try:
            entreprise.sauvegarder_mots_cles()
            print("Mots-clés sauvegardés")
        except Exception as e:
            print(f"Erreur mots-clés (non bloquante): {e}")
        
        # ===== NOUVELLE VÉRIFICATION CORRIGÉE =====
        # Vérifier si le profil est maintenant complet
        profil_complet = True
        champs_manquants = []
        
        # 1. Domaine d'activité
        if not entreprise.domaineActive or not str(entreprise.domaineActive).strip():
            profil_complet = False
            champs_manquants.append("Domaine d'activité")
        
        # 2. Localisation
        if not entreprise.localisation or not str(entreprise.localisation).strip():
            profil_complet = False
            champs_manquants.append("Localisation")
        
        # 3. Compétences clés
        if not entreprise.competencesCles or not str(entreprise.competencesCles).strip():
            profil_complet = False
            champs_manquants.append("Compétences clés")
        
        # 4. Pays d'intervention (liste)
        if not entreprise.pays_intervention or len(entreprise.pays_intervention) == 0:
            profil_complet = False
            champs_manquants.append("Pays d'intervention")
        
        # 5. Chiffre d'affaires (nombre)
        try:
            ca_value = float(entreprise.chiffre_affaires) if entreprise.chiffre_affaires else 0
            if ca_value <= 0:
                profil_complet = False
                champs_manquants.append("Chiffre d'affaires")
        except (ValueError, TypeError):
            profil_complet = False
            champs_manquants.append("Chiffre d'affaires (invalide)")
        
        # 6. Types d'opportunités (liste)
        if not entreprise.types_opportunites or len(entreprise.types_opportunites) == 0:
            profil_complet = False
            champs_manquants.append("Types d'opportunités")
        
        print(f"Profil complet: {profil_complet}")
        if not profil_complet:
            print(f"Champs manquants: {', '.join(champs_manquants)}")
        # ===== FIN DE LA VÉRIFICATION CORRIGÉE =====
        
        if profil_complet:
            messages.success(request, "Félicitations ! Votre profil est maintenant complet. Vous allez recevoir des recommandations personnalisées.")
            
            # Optionnel : Lancer immédiatement les recommandations
            try:
                from analyse_ia.moteur_recommandation import MoteurRecommandation
                moteur = MoteurRecommandation()
                moteur.recommander_pour_entreprise(entreprise)
                messages.info(request, "Vos recommandations ont été générées.")
            except Exception as e:
                print(f"Erreur lors de la génération des recommandations: {e}")
        else:
            messages.success(request, "Profil mis à jour avec succès ! Continuez à le compléter pour activer les recommandations.")
        
    except Exception as e:
        print(f"ERREUR: {str(e)}")
        messages.error(request, f"Erreur lors de la sauvegarde : {str(e)}")
    
    return redirect('myAppli:dashboard_entreprise')

def detail_offre(request, pk):
    """
    Vue pour afficher les détails d'une offre
    """
    try:
        offre = Offre_uemoa.objects.get(pk=pk)
        return render(request, 'myAppli/detail_offre.html', {'offre': offre})
    except Offre_uemoa.DoesNotExist:
        messages.error(request, "Cette offre n'existe pas.")
        return redirect('myAppli:opportunites')

def detail_ami(request, pk):
    """
    Vue pour afficher les détails d'un AMI
    """
    try:
        ami = Ami_uemoa.objects.get(pk=pk)
        return render(request, 'myAppli/detail_ami.html', {'ami': ami})
    except Ami_uemoa.DoesNotExist:
        messages.error(request, "Cet AMI n'existe pas.")
        return redirect('myAppli:opportunites')

def detail_emploi(request, pk):
    """
    Vue pour afficher les détails d'une offre d'emploi
    """
    try:
        emploi = OffreEmploi.objects.get(pk=pk)
        return render(request, 'myAppli/detail_ami.html', {'emploi': emploi})
    except OffreEmploi.DoesNotExist:
        messages.error(request, "Cette offre d'emploi n'existe pas.")
        return redirect('myAppli:opportunites')


@login_required
def commencer_soumission(request, opportunite_type, opportunite_id):
    """
    Page de pré-soumission - Permet de renseigner matériels, personnel, etc.
    """
    # Récupérer l'opportunité
    if opportunite_type == 'Offre_uemoa':
        opportunite = get_object_or_404(Offre_uemoa, id=opportunite_id)
        type_nom = "Appel d'offres"
    else:
        opportunite = get_object_or_404(Ami_uemoa, id=opportunite_id)
        type_nom = "Appel à manifestation d'intérêt"
    
    # Récupérer l'entreprise
    entreprise = request.user.entreprise if hasattr(request.user, 'entreprise') else None
    
    if not entreprise:
        messages.error(request, "Vous devez avoir une entreprise associée à votre compte.")
        return redirect('myAppli:home')
    
    # Traitement des formulaires POST
    if request.method == 'POST':
        # Ajout de matériel
        if 'ajouter_materiel' in request.POST:
            MaterielEntreprise.objects.create(
                entreprise=entreprise,
                designation=request.POST.get('designation'),
                quantite=request.POST.get('quantite', 1),
                etat_fonctionnement=request.POST.get('etat_fonctionnement', 'Bon état'),
                observations=request.POST.get('observations', '')
            )
            messages.success(request, "Matériel ajouté avec succès!")
            return redirect('myAppli:commencer_soumission', opportunite_type=opportunite_type, opportunite_id=opportunite_id)
        
        # Ajout de personnel
        elif 'ajouter_personnel' in request.POST:
            PersonnelCle.objects.create(
                entreprise=entreprise,
                nom_prenom=request.POST.get('nom_prenom'),
                poste=request.POST.get('poste'),
                qualification=request.POST.get('qualification'),
                annees_experience=request.POST.get('annees_experience', 0)
            )
            messages.success(request, "Personnel ajouté avec succès!")
            return redirect('myAppli:commencer_soumission', opportunite_type=opportunite_type, opportunite_id=opportunite_id)
        
        # Ajout de référence technique
        elif 'ajouter_reference' in request.POST:
            ReferenceTechnique.objects.create(
                entreprise=entreprise,
                client=request.POST.get('client'),
                projet=request.POST.get('projet'),
                montant=request.POST.get('montant'),
                annee=request.POST.get('annee'),
                description=request.POST.get('description', '')
            )
            messages.success(request, "Référence technique ajoutée!")
            return redirect('myAppli:commencer_soumission', opportunite_type=opportunite_type, opportunite_id=opportunite_id)
        
        # Suppression
        elif 'supprimer_materiel' in request.POST:
            MaterielEntreprise.objects.filter(id=request.POST.get('materiel_id'), entreprise=entreprise).delete()
            messages.success(request, "Matériel supprimé")
            return redirect('myAppli:commencer_soumission', opportunite_type=opportunite_type, opportunite_id=opportunite_id)
        
        elif 'supprimer_personnel' in request.POST:
            PersonnelCle.objects.filter(id=request.POST.get('personnel_id'), entreprise=entreprise).delete()
            messages.success(request, "Personnel supprimé")
            return redirect('myAppli:commencer_soumission', opportunite_type=opportunite_type, opportunite_id=opportunite_id)
        
        # Soumission finale
        elif 'soumettre_dossier' in request.POST:
            lettre_motivation = request.POST.get('lettre_motivation', '')
            
            # Vérifier que l'entreprise a au moins du matériel et du personnel
            has_materiel = MaterielEntreprise.objects.filter(entreprise=entreprise).exists()
            has_personnel = PersonnelCle.objects.filter(entreprise=entreprise).exists()
            
            if not has_materiel:
                messages.warning(request, "Veuillez renseigner au moins un équipement/matériel")
                return redirect('myAppli:commencer_soumission', opportunite_type=opportunite_type, opportunite_id=opportunite_id)
            
            if not has_personnel:
                messages.warning(request, "Veuillez renseigner au moins un personnel clé")
                return redirect('myAppli:commencer_soumission', opportunite_type=opportunite_type, opportunite_id=opportunite_id)
            
            # Créer ou mettre à jour le dossier
            dossier, created = DossierSoumission.objects.update_or_create(
                entreprise=entreprise,
                opportunite_type=opportunite_type,
                opportunite_id=opportunite_id,
                defaults={
                    'reference': f"DOS-{timezone.now().strftime('%Y%m%d')}-{entreprise.id}",
                    'lettre_motivation': lettre_motivation,
                    'statut': 'SOUMIS',
                    'date_soumission_effective': timezone.now()
                }
            )
            
            # Mettre à jour les statistiques
            entreprise.nb_candidatures_emises += 1
            entreprise.save()
            
            messages.success(request, f"✅ Votre candidature pour {type_nom} a été soumise avec succès !")
            return redirect('myAppli:dashboard_entreprise')
    
    # Récupérer les données existantes
    materiels = MaterielEntreprise.objects.filter(entreprise=entreprise)
    personnels = PersonnelCle.objects.filter(entreprise=entreprise)
    references_tech = ReferenceTechnique.objects.filter(entreprise=entreprise)
    
    # Vérifier si un dossier existe déjà
    dossier = DossierSoumission.objects.filter(
        entreprise=entreprise,
        opportunite_type=opportunite_type,
        opportunite_id=opportunite_id
    ).first()
    
    context = {
        'opportunite': opportunite,
        'opportunite_type': opportunite_type,
        'type_nom': type_nom,
        'entreprise': entreprise,
        'dossier': dossier,
        'materiels': materiels,
        'personnels': personnels,
        'references_tech': references_tech,
        'profil_complet': entreprise.profil_complet,
        'has_materiel': materiels.exists(),
        'has_personnel': personnels.exists(),
        'has_references': references_tech.exists(),
    }
    
    return render(request, 'myAppli/soumission/commencer_soumission.html', context)

@login_required
def valider_soumission(request, opportunite_type, opportunite_id):
    """
    Valide et soumet le dossier de candidature
    """
    
    if request.method != 'POST':
        return redirect('myAppli:dashboard_entreprise')
    
    # Récupérer le dossier
    try:
        dossier = DossierSoumission.objects.get(
            entreprise=request.user.entreprise,
            opportunite_type=opportunite_type,
            opportunite_id=opportunite_id
        )
    except DossierSoumission.DoesNotExist:
        messages.error(request, "Dossier non trouvé")
        return redirect('myAppli:dashboard_entreprise')
    
    # Récupérer la lettre de motivation
    lettre_motivation = request.POST.get('lettre_motivation', '')
    
    # Mettre à jour le dossier
    dossier.lettre_motivation = lettre_motivation
    dossier.statut = 'SOUMIS'
    dossier.date_soumission_effective = timezone.now()
    dossier.save()
    
    # Mettre à jour les statistiques de l'entreprise
    entreprise = request.user.entreprise
    entreprise.nb_candidatures_emises += 1
    entreprise.save()
    
    messages.success(request, f"✅ Votre candidature pour {opportunite_type}#{opportunite_id} a été soumise avec succès !")
    
    return redirect('myAppli:dashboard_entreprise')


@login_required
def ajouter_materiel(request, entreprise_id):
    """Ajoute du matériel à l'entreprise"""
    if request.method == 'POST':
        entreprise = get_object_or_404(Entreprise, id=entreprise_id)
        MaterielEntreprise.objects.create(
            entreprise=entreprise,
            designation=request.POST.get('designation'),
            quantite=request.POST.get('quantite', 1),
            etat_fonctionnement=request.POST.get('etat', 'Bon état'),
            observations=request.POST.get('observations', '')
        )
        messages.success(request, "Matériel ajouté avec succès!")
    return redirect(request.META.get('HTTP_REFERER', 'myAppli:dashboard_entreprise'))


@login_required
def ajouter_personnel(request, entreprise_id):
    """Ajoute du personnel clé à l'entreprise"""
    if request.method == 'POST':
        entreprise = get_object_or_404(Entreprise, id=entreprise_id)
        PersonnelCle.objects.create(
            entreprise=entreprise,
            nom_prenom=request.POST.get('nom_prenom'),
            poste=request.POST.get('poste'),
            qualification=request.POST.get('qualification'),
            annees_experience=request.POST.get('annees_experience', 0)
        )
        messages.success(request, "Personnel ajouté avec succès!")
    return redirect(request.META.get('HTTP_REFERER', 'myAppli:dashboard_entreprise'))

@login_required
def telecharger_document(request, document_id):
    """Télécharge un document généré"""
    document = get_object_or_404(DocumentSoumission, id=document_id)
    
    if document.dossier.entreprise.user != request.user:
        return HttpResponse("Non autorisé", status=403)
    
    if os.path.exists(document.fichier_genere.path):
        with open(document.fichier_genere.path, 'rb') as f:
            response = HttpResponse(
                f.read(), 
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            response['Content-Disposition'] = f'attachment; filename="{document.nom_document}"'
            return response
    else:
        messages.error(request, "Fichier non trouvé")
        return redirect('myAppli:preparer_soumission', dossier_id=document.dossier.id)

@login_required
def valider_document(request, document_id):
    """Marque un document comme validé"""
    if request.method == 'POST':
        document = get_object_or_404(DocumentSoumission, id=document_id)
        
        if document.dossier.entreprise.user != request.user:
            return JsonResponse({'error': 'Non autorisé'}, status=403)
        
        document.statut = 'VALIDE'
        document.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@login_required
def soumettre_dossier(request, dossier_id):
    """Soumet le dossier final"""
    dossier = get_object_or_404(DossierSoumission, id=dossier_id)
    
    if dossier.entreprise.user != request.user:
        messages.error(request, "Non autorisé")
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Vérifier que tous les documents sont validés
        documents_non_valides = dossier.documents.exclude(statut='VALIDE')
        
        print(f"📊 Documents non valides: {documents_non_valides.count()}")
        for doc in documents_non_valides:
            print(f"  - {doc.nom_document}: {doc.statut}")

        if documents_non_valides.exists():
            messages.warning(request, "Tous les documents doivent être validés")
            return redirect('myAppli:preparer_soumission', dossier_id=dossier.id)
        
        # Mettre à jour le dossier
        dossier.statut = 'SOUMIS'
        dossier.date_soumission_effective = timezone.now()
        dossier.save()
        
        # Mettre à jour les statistiques de l'entreprise
        entreprise = dossier.entreprise
        entreprise.nb_candidatures_emises += 1
        entreprise.save()
        
        messages.success(request, "Dossier soumis avec succès!")
        return redirect('myAppli:mes_soumissions')
    
    # GET : page de confirmation
    context = {
        'dossier': dossier,
        'documents': dossier.documents.all(),
        'now': timezone.now(),
    }
    return render(request, 'myAppli/soumission/confirmer_soumission.html', context)


@login_required
def generer_document_soumission(request, type_doc):
    """
    Génère la première page avec la description complète en majuscules
    """
    if type_doc != 'entete':
        return JsonResponse({'error': 'Type non supporté'}, status=400)
    
    opportunite_type = request.GET.get('opportunite_type')
    opportunite_id = request.GET.get('opportunite_id')
    
    # Récupérer l'opportunité
    if opportunite_type == 'Offre_uemoa':
        opportunite = get_object_or_404(Offre_uemoa, id=opportunite_id)
    else:
        opportunite = get_object_or_404(Ami_uemoa, id=opportunite_id)
    
    description = opportunite.description or ""
    
    # Nettoyer la description
    description = description.replace('\n', ' ').replace('\r', ' ')
    description = description.strip()
    
    # Enlever "Avis à manifestation d'intérêt" qui est déjà dans le titre
    description = re.sub(r'Avis à manifestation d[’\']intérêt\s+', '', description, flags=re.IGNORECASE)
    description = re.sub(r'AVIS À MANIFESTATION D[’\']INTÉRÊT\s+', '', description, flags=re.IGNORECASE)
    
    # Mettre en majuscules
    description = description.upper()
    
    # Créer le document Word
    from docx import Document
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from io import BytesIO
    
    doc = Document()
    
    # Marges
    section = doc.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    
    # ===== TITRE =====
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    texte_complet = f"RÉPONSE À LA MANIFESTATION D'INTÉRÊT {description}"
    
    run = p.add_run(texte_complet)
    run.font.size = Pt(22)
    run.font.bold = True
    
    # Sauvegarder
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    filename = f"page_garde_AMI_{opportunite_id}.docx"
    
    response = FileResponse(
        buffer,
        as_attachment=True,
        filename=filename,
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    return response

@login_required
def apercu_document_soumission(request, type_doc):
    """
    Retourne l'aperçu HTML du document
    """
    if type_doc != 'entete':
        return JsonResponse({'error': 'Type non supporté'}, status=400)
    
    opportunite_type = request.GET.get('opportunite_type')
    opportunite_id = request.GET.get('opportunite_id')
    
    if opportunite_type == 'Offre_uemoa':
        opportunite = get_object_or_404(Offre_uemoa, id=opportunite_id)
    else:
        opportunite = get_object_or_404(Ami_uemoa, id=opportunite_id)
    
    description = opportunite.description or ""
    description = description.replace('\n', ' ').replace('\r', ' ')
    description = description.strip()
    description = re.sub(r'Avis à manifestation d[’\']intérêt\s+', '', description, flags=re.IGNORECASE)
    description = re.sub(r'AVIS À MANIFESTATION D[’\']INTÉRÊT\s+', '', description, flags=re.IGNORECASE)
    description = description.upper()
    
    html = f'''
    <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; background: white;">
        <div style="text-align: justify; font-weight: bold; font-size: 22px; line-height: 1.5;">
            RÉPONSE À LA MANIFESTATION D'INTÉRÊT {description}
        </div>
    </div>
    '''
    
    return JsonResponse({'html': html, 'success': True})

@login_required
def get_donnees_document(request, type_doc):
    """
    Récupère les données existantes pour l'édition
    """
    opportunite_type = request.GET.get('opportunite_type')
    opportunite_id = request.GET.get('opportunite_id')
    
    if opportunite_type == 'Offre_uemoa':
        opportunite = get_object_or_404(Offre_uemoa, id=opportunite_id)
    else:
        opportunite = get_object_or_404(Ami_uemoa, id=opportunite_id)
    
    entreprise = request.user.entreprise
    donnees = {}
    
    if type_doc == 'entete':
        donnees = {
            'reference': getattr(opportunite, 'reference', ''),
            'date_ami': getattr(opportunite, 'date_publication', ''),
            'beneficiaire': getattr(opportunite, 'beneficiaire', ''),
        }
    elif type_doc == 'lettre':
        dossier = DossierSoumission.objects.filter(
            entreprise=entreprise,
            opportunite_type=opportunite_type,
            opportunite_id=opportunite_id
        ).first()
        donnees = {
            'lettre_motivation': dossier.lettre_motivation if dossier else ''
        }
    elif type_doc == 'presentation':
        donnees = {
            'presentation': entreprise.description or ''
        }
    elif type_doc == 'fiche':
        donnees = {
            'ifu': getattr(entreprise, 'ifu', ''),
            'rccm': getattr(entreprise, 'rccm', ''),
            'telephone': entreprise.telephone or '',
            'email': entreprise.email or '',
            'adresse': entreprise.localisation or '',
        }
    else:
        return JsonResponse({'success': False, 'error': 'Type non supporté'})
    
    return JsonResponse({'success': True, 'donnees': donnees})

@login_required
def telecharger_document_soumission(request, type_doc):
    """
    Télécharge le document au format choisi (DOCX ou PDF)
    """
    if type_doc != 'entete':
        return JsonResponse({'error': 'Type non supporté'}, status=400)
    
    format_doc = request.GET.get('format', 'docx')
    opportunite_type = request.GET.get('opportunite_type')
    opportunite_id = request.GET.get('opportunite_id')
    
    if opportunite_type == 'Offre_uemoa':
        opportunite = get_object_or_404(Offre_uemoa, id=opportunite_id)
    else:
        opportunite = get_object_or_404(Ami_uemoa, id=opportunite_id)
    
    description = opportunite.description or ""
    description = description.replace('\n', ' ').replace('\r', ' ')
    description = description.strip()
    description = re.sub(r'Avis à manifestation d[’\']intérêt\s+', '', description, flags=re.IGNORECASE)
    description = re.sub(r'AVIS À MANIFESTATION D[’\']INTÉRÊT\s+', '', description, flags=re.IGNORECASE)
    description = description.upper()
    
    if format_doc == 'pdf':
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from io import BytesIO
        
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        c.setFont("Helvetica-Bold", 22)
        
        margin = 20 * mm
        y = height - margin
        x = margin
        
        text = f"RÉPONSE À LA MANIFESTATION D'INTÉRÊT {description}"
        
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            if c.stringWidth(current_line + " " + word, "Helvetica-Bold", 22) < (width - 2 * margin):
                current_line += " " + word if current_line else word
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        for line in lines:
            c.drawString(x, y, line)
            y -= 30
        
        c.save()
        buffer.seek(0)
        
        response = FileResponse(
            buffer,
            as_attachment=True,
            filename=f"page_garde_AMI_{opportunite_id}.pdf",
            content_type='application/pdf'
        )
        return response
    
    else:
        from docx import Document
        from docx.shared import Pt, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from io import BytesIO
        
        doc = Document()
        
        section = doc.sections[0]
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.5)
        section.right_margin = Inches(0.5)
        
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        texte_complet = f"RÉPONSE À LA MANIFESTATION D'INTÉRÊT {description}"
        
        run = p.add_run(texte_complet)
        run.font.size = Pt(22)
        run.font.bold = True
        
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        response = FileResponse(
            buffer,
            as_attachment=True,
            filename=f"page_garde_AMI_{opportunite_id}.docx",
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        return response

@login_required
@require_http_methods(["POST"])
def sauvegarder_donnees_soumission(request):
    """
    Sauvegarde les données de l'en-tête saisies dans le modal
    """
    try:
        data = request.POST
        doc_type = data.get('type')
        opportunite_type = data.get('opportunite_type')
        opportunite_id = data.get('opportunite_id')
        
        if doc_type != 'entete':
            return JsonResponse({'error': 'Type non supporté'}, status=400)
        
        # Récupérer l'opportunité
        if opportunite_type == 'Offre_uemoa':
            opportunite = get_object_or_404(Offre_uemoa, id=opportunite_id)
        else:
            opportunite = get_object_or_404(Ami_uemoa, id=opportunite_id)
        
        # Sauvegarder la référence
        if data.get('reference_ami'):
            opportunite.reference = data.get('reference_ami')
        
        # Sauvegarder la date
        if data.get('date_ami'):
            from datetime import datetime
            try:
                opportunite.date_publication = datetime.strptime(data.get('date_ami'), '%Y-%m-%d').date()
            except:
                pass
        
        # Sauvegarder le bénéficiaire
        if data.get('beneficiaire'):
            opportunite.beneficiaire = data.get('beneficiaire')
        
        opportunite.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def etat_documents_soumission(request):
    """
    Retourne l'état des documents déjà générés
    """
    opportunite_type = request.GET.get('opportunite_type')
    opportunite_id = request.GET.get('opportunite_id')
    
    if opportunite_type == 'Offre_uemoa':
        opportunite = get_object_or_404(Offre_uemoa, id=opportunite_id)
    else:
        opportunite = get_object_or_404(Ami_uemoa, id=opportunite_id)
    
    # Pour l'en-tête, on considère que c'est toujours possible
    # (pas de champs obligatoires spécifiques)
    etat = {
        'entete': True,  # Toujours disponible
        'lettre': False,
        'presentation': False,
        'fiche': False,
        'materiel': False,
        'personnel': False,
    }
    
    return JsonResponse(etat)

@login_required
def mes_soumissions(request):
    """Liste tous les dossiers de l'entreprise"""
    try:
        entreprise = Entreprise.objects.get(user=request.user)
    except Entreprise.DoesNotExist:
        messages.error(request, "Vous devez être une entreprise")
        return redirect('dashboard')
    
    dossiers = DossierSoumission.objects.filter(
        entreprise=entreprise
    ).order_by('-date_modification')
    
    stats = {
        'en_preparation': dossiers.filter(statut='EN_PREPARATION').count(),
        'soumis': dossiers.filter(statut='SOUMIS').count(),
        'total': dossiers.count(),
    }
    
    context = {
        'dossiers': dossiers,
        'stats': stats,
    }
    return render(request, 'myAppli/soumission/mes_soumissions.html', context)



def trouver_emploi(request):
    """
    Page d'outils et de conseils pour la recherche d'emploi
    """
    # Récupérer les dernières offres d'emploi
    dernieres_offres = OffreEmploi.objects.filter(
        statut='PUBLIEE',
        est_active=True
    ).order_by('-date_publication')[:5]
    
    # Statistiques
    stats = {
        'offres_disponibles': OffreEmploi.objects.filter(
            statut='PUBLIEE', 
            est_active=True
        ).count(),
        'outils': 6,  # Nombre d'outils affichés dans la grille
        'conseils': 6,  # Nombre de conseils affichés
    }
    
    # Si l'utilisateur est un candidat, on peut personnaliser
    if hasattr(request.user, 'particulier'):
        particulier = request.user.particulier
        if hasattr(particulier, 'candidat'):
            candidat = particulier.candidat
            # On pourrait ajouter des recommandations personnalisées ici
            pass
    
    context = {
        'dernieres_offres': dernieres_offres,
        'stats': stats,
    }
    
    return render(request, 'myAppli/outils_emploi/trouver_emploi.html', context)

def generer_cv(request):
    """
    Générateur de CV accessible à tous.
    Gère la création, l'édition et la photo de profil.
    """

    modeles_cv  = ModeleCV.objects.filter(est_actif=True).order_by('ordre_affichage')
    modeles_json = json.dumps([
        {
            'nom':          m.nom,
            'categorie':    m.categorie,
            'est_populaire': m.est_populaire,
            'est_premium':  m.est_premium,
        }
        for m in modeles_cv
    ])

    # ── Mode édition ──────────────────────────────────────────────────────────
    cv_a_modifier = None
    donnees_init  = {}
    is_edit_mode  = False

    if request.GET.get('edit'):
        try:
            cv_id         = int(request.GET.get('edit'))
            cv_a_modifier = CVGenere.objects.get(id=cv_id, utilisateur=request.user)
            donnees_init  = cv_a_modifier.donnees_cv.copy()
            is_edit_mode  = True

            # Reconvertir les listes en chaînes pour le formulaire
            if isinstance(donnees_init.get('competences'), list):
                donnees_init['competences'] = ', '.join(donnees_init['competences'])
            if isinstance(donnees_init.get('langues'), list):
                donnees_init['langues'] = ', '.join(donnees_init['langues'])
            if isinstance(donnees_init.get('centres_interet'), list):
                donnees_init['centres_interet'] = ', '.join(donnees_init['centres_interet'])

            if isinstance(donnees_init.get('experiences'), list):
                exp_text = ''
                for exp in donnees_init['experiences']:
                    exp_text += (
                        f"{exp.get('titre', '')} | {exp.get('entreprise', '')} | "
                        f"{exp.get('date_debut', '')} | {exp.get('date_fin', 'Présent')} | "
                        f"{exp.get('description', '')}\n"
                    )
                donnees_init['experiences'] = exp_text.strip()

            if isinstance(donnees_init.get('formations'), list):
                form_text = ''
                for f in donnees_init['formations']:
                    form_text += f"{f.get('diplome', '')} | {f.get('etablissement', '')} | {f.get('annee', '')}\n"
                donnees_init['formations'] = form_text.strip()

            print(f"📝 Mode édition CV {cv_id} : {cv_a_modifier.titre}")

        except (CVGenere.DoesNotExist, ValueError) as e:
            print(f"Erreur mode édition : {e}")

    # ── Traitement POST ───────────────────────────────────────────────────────
    if request.method == 'POST':
        try:
            format_export = request.POST.get('format', 'pdf')
            style         = request.POST.get('style', 'executive')

            from .services.generateur_cv_public import GenerateurCVPublic
            generateur = GenerateurCVPublic()

            # ✅ On passe request.FILES pour récupérer la photo
            donnees = generateur.preparer_donnees(request.POST, request.FILES)

            # DEBUG
            print("=== VÉRIFICATION FINALE ===")
            print(f"Clés dans donnees: {donnees.keys()}")
            print(f"Formations: {donnees.get('formations')}")
            print(f"Type de formations: {type(donnees.get('formations'))}")
            print(f"Nombre de formations: {len(donnees.get('formations', []))}")
            
            if not donnees['prenom'] or not donnees['nom']:
                messages.error(request, "Le prénom et le nom sont obligatoires.")
                return redirect('myAppli:generer_cv')

            buffer, nom_fichier = generateur.generer_cv_buffer(donnees, format_export, style)

            # ── Mise à jour (mode édition) ────────────────────────────────────
            cv_id = request.POST.get('cv_id')
            if cv_id:
                try:
                    cv_existant             = CVGenere.objects.get(id=cv_id, utilisateur=request.user)
                    cv_existant.titre       = f"CV de {donnees['prenom']} {donnees['nom']}"
                    cv_existant.donnees_cv  = donnees
                    cv_existant.modele      = ModeleCV.objects.filter(categorie=style, est_actif=True).first()

                    buffer.seek(0)
                    if format_export == 'pdf':
                        if cv_existant.fichier_pdf:
                            cv_existant.fichier_pdf.delete()
                        cv_existant.fichier_pdf.save(nom_fichier, ContentFile(buffer.getvalue()))
                    elif format_export == 'docx':
                        if cv_existant.fichier_docx:
                            cv_existant.fichier_docx.delete()
                        cv_existant.fichier_docx.save(nom_fichier, ContentFile(buffer.getvalue()))

                    cv_existant.save()
                    messages.success(request, "✅ CV modifié avec succès !")
                    return redirect('myAppli:mes_cvs')

                except CVGenere.DoesNotExist:
                    messages.error(request, "CV non trouvé.")
                    return redirect('myAppli:generer_cv')

            # ── Création ──────────────────────────────────────────────────────
            else:
                if request.user.is_authenticated:
                    modele_cv  = ModeleCV.objects.filter(categorie=style, est_actif=True).first()
                    cv_nouveau = CVGenere.objects.create(
                        utilisateur=request.user,
                        modele=modele_cv,
                        titre=f"CV de {donnees['prenom']} {donnees['nom']}",
                        donnees_cv=donnees,
                        est_public=False,
                    )
                    buffer.seek(0)
                    if format_export == 'pdf':
                        cv_nouveau.fichier_pdf.save(nom_fichier, ContentFile(buffer.getvalue()))
                    elif format_export == 'docx':
                        cv_nouveau.fichier_docx.save(nom_fichier, ContentFile(buffer.getvalue()))

                    messages.success(request, "✅ CV créé avec succès !")
                    return redirect('myAppli:mes_cvs')
                else:
                    # Utilisateur non connecté → téléchargement direct
                    buffer.seek(0)
                    return FileResponse(buffer, as_attachment=True, filename=nom_fichier)

        except Exception as e:
            print(f"❌ Erreur génération CV : {e}")
            messages.error(request, f"Erreur lors de la génération : {str(e)}")
            return redirect('myAppli:generer_cv')

    # ── GET ───────────────────────────────────────────────────────────────────
    return render(request, 'myAppli/outils_emploi/generer_cv.html', {
        'modeles_cv':   modeles_cv,
        'modeles_json': modeles_json,
        'cv_a_modifier': cv_a_modifier,
        'donnees_init': donnees_init,
        'is_edit_mode': is_edit_mode,
    })

@login_required
def preparer_entretien(request):
    """
    Outil de préparation aux entretiens
    """
    return render(request, 'myAppli/outils_emploi/preparation_entretien.html')

@login_required
def alertes_emploi(request):
    """
    Gestion des alertes emploi
    """
    return render(request, 'myAppli/outils_emploi /alertes_emploi.html')

def apercu_style_cv(request, style):
    """
    Génère un aperçu HTML d'un style de CV
    """
    generateur = GenerateurCVPublic()
    html_apercu = generateur.generer_apercu(style)
    return HttpResponse(html_apercu)

@login_required
def apercu_cv(request, cv_id):
    """Affiche un aperçu du CV en utilisant le template du style et les données sauvegardées"""
    cv = get_object_or_404(CVGenere, id=cv_id, utilisateur=request.user)
    
    # Récupérer les données du CV
    donnees = cv.donnees_cv
    
    # Récupérer le style
    style = donnees.get('style', 'moderne')
    if cv.modele:
        style = cv.modele.categorie
    
    print(f"🎨 Génération aperçu pour style: {style}")
    
    # Utiliser le générateur
    from .services.generateur_cv_public import GenerateurCVPublic
    generateur = GenerateurCVPublic()
    
    # Générer le HTML
    html = generateur.generer_html_avec_donnees(style, donnees)
    
    print(f"✅ HTML généré, longueur: {len(html)} caractères")
    
    return HttpResponse(html)


@login_required
def mes_cvs(request):
    """Affiche tous les CV de l'utilisateur"""
    cvs = CVGenere.objects.filter(utilisateur=request.user).order_by('-date_generation')
    
    # Statistiques avec gestion des champs optionnels
    stats = {
        'total': cvs.count(),
        'telechargements': sum(cv.nb_telechargements for cv in cvs if hasattr(cv, 'nb_telechargements')),
        'favoris': cvs.filter(est_favori=True).count() if hasattr(CVGenere, 'est_favori') else 0,
        'utilises': cvs.filter(est_utilise=True).count() if hasattr(CVGenere, 'est_utilise') else 0,
    }
    
    context = {
        'cvs': cvs,
        'stats': stats,
    }
    return render(request, 'myAppli/outils_emploi/mes_cvs.html', context)

@login_required
def telecharger_cv(request, cv_id, format):
    cv = get_object_or_404(CVGenere, id=cv_id, utilisateur=request.user)
    
    cv.nb_telechargements += 1
    cv.save()
    
    if format == 'pdf' and cv.fichier_pdf:
        return FileResponse(cv.fichier_pdf, as_attachment=True, filename=cv.fichier_pdf.name)
    elif format == 'docx' and cv.fichier_docx:
        return FileResponse(cv.fichier_docx, as_attachment=True, filename=cv.fichier_docx.name)
    
    return JsonResponse({'error': 'Fichier non disponible'}, status=404)

@login_required
def supprimer_cv(request, cv_id):
    cv = get_object_or_404(CVGenere, id=cv_id, utilisateur=request.user)
    cv.delete()
    return JsonResponse({'success': True})

@login_required
def dupliquer_cv(request, cv_id):
    original = get_object_or_404(CVGenere, id=cv_id, utilisateur=request.user)
    
    copie = CVGenere.objects.create(
        utilisateur=request.user,
        modele=original.modele,
        titre=f"{original.titre} (copie)",
        donnees_cv=original.donnees_cv,
        est_public=False
    )
    
    return JsonResponse({'success': True, 'id': copie.id})

@login_required
def importer_cv(request):
    """Importe un CV depuis un fichier"""
    print("="*50)
    print("🚀 FONCTION IMPORTER_CV APPELEE")
    print(f"Méthode: {request.method}")
    print(f"Fichiers: {request.FILES}")
    print("="*50)
    
    if request.method == 'POST':
        if not request.FILES.get('file'):
            print("❌ Aucun fichier trouvé")
            return JsonResponse({'error': 'Aucun fichier fourni'}, status=400)
        
        file = request.FILES['file']
        filename = file.name
        print(f"📁 Fichier reçu: {filename}")
        print(f"📊 Taille: {file.size} octets")
        
        try:
            if filename.endswith('.json'):
                # Lire le fichier JSON
                print("📄 Traitement fichier JSON...")
                data = json.load(file)
                
                # Créer le CV
                cv = CVGenere.objects.create(
                    utilisateur=request.user,
                    titre=data.get('titre', filename),
                    donnees_cv=data,
                    est_public=False
                )
                
                print(f"✅ CV JSON créé avec ID: {cv.id}")
                return JsonResponse({'success': True, 'id': cv.id})
                
            elif filename.endswith('.pdf'):
                print("📄 Traitement fichier PDF...")
                # Créer un CV minimal avec le fichier PDF
                cv = CVGenere.objects.create(
                    utilisateur=request.user,
                    titre=filename.replace('.pdf', ''),
                    donnees_cv={'prenom': filename.replace('.pdf', ''), 'nom': '', 'fichier_original': filename},
                    est_public=False
                )
                
                # Sauvegarder le fichier PDF
                cv.fichier_pdf.save(filename, ContentFile(file.read()))
                
                print(f"✅ CV PDF créé avec ID: {cv.id}")
                return JsonResponse({'success': True, 'id': cv.id})
                
            elif filename.endswith('.docx'):
                print("📄 Traitement fichier DOCX...")
                # Créer un CV minimal avec le fichier DOCX
                cv = CVGenere.objects.create(
                    utilisateur=request.user,
                    titre=filename.replace('.docx', ''),
                    donnees_cv={'prenom': filename.replace('.docx', ''), 'nom': '', 'fichier_original': filename},
                    est_public=False
                )
                
                # Sauvegarder le fichier DOCX
                cv.fichier_docx.save(filename, ContentFile(file.read()))
                
                print(f"✅ CV DOCX créé avec ID: {cv.id}")
                return JsonResponse({'success': True, 'id': cv.id})
                
            else:
                print(f"❌ Format non supporté: {filename}")
                return JsonResponse({'error': 'Format non supporté. Utilisez .pdf, .docx ou .json'}, status=400)
                
        except json.JSONDecodeError as e:
            print(f"❌ Erreur JSON: {e}")
            return JsonResponse({'error': 'Fichier JSON invalide'}, status=400)
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@login_required
def modifier_cv(request, cv_id):
    """Modifier un CV - Version simple"""
    cv = get_object_or_404(CVGenere, id=cv_id, utilisateur=request.user)
    
    if request.method == 'POST':
        # Mettre à jour le titre
        cv.titre = request.POST.get('titre', cv.titre)
        cv.save()
        messages.success(request, "CV modifié avec succès")
        return redirect('myAppli:mes_cvs')
    
    return render(request, 'myAppli/outils_emploi/modifier_cv.html', {'cv': cv})

@login_required
def get_dossier_documents(request, dossier_id):
    """Retourne la liste des documents d'un dossier en JSON"""
    dossier = get_object_or_404(DossierSoumission, id=dossier_id)
    
    # Vérifier que l'entreprise a le droit
    if dossier.entreprise.user != request.user:
        return JsonResponse({'error': 'Non autorisé'}, status=403)
    
    documents = dossier.documents.all()
    
    data = {
        'documents': [
            {
                'id': doc.id,
                'nom_document': doc.nom_document,
                'statut': doc.statut,
                'taille_fichier': doc.taille_fichier,
                'date_generation': doc.date_generation.strftime('%d/%m/%Y %H:%M'),
            }
            for doc in documents
        ]
    }
    
    return JsonResponse(data)

@login_required
def publier_offre_emploi(request):
    """
    Vue pour publier une offre d'emploi
    """
    if request.method == 'POST':
        # Vérifier que l'utilisateur est un recruteur
        if not hasattr(request.user, 'particulier') or not hasattr(request.user.particulier, 'recruteur'):
            messages.error(request, "Vous devez être recruteur pour publier une offre")
            return redirect('myAppli:home')
        
        recruteur = request.user.particulier.recruteur
        
        try:
            # Traitement des compétences
            competences_requises = []
            if request.POST.get('competences_requises'):
                competences_requises = [c.strip() for c in request.POST.get('competences_requises').split(',') if c.strip()]
            
            competences_souhaitees = []
            if request.POST.get('competences_souhaitees'):
                competences_souhaitees = [c.strip() for c in request.POST.get('competences_souhaitees').split(',') if c.strip()]
            
            # Création de l'offre
            offre = OffreEmploi.objects.create(
                recruteur=recruteur,
                titre=request.POST.get('titre'),
                description=request.POST.get('description', ''),
                missions=request.POST.get('missions', ''),
                profil_recherche=request.POST.get('profil_recherche', ''),
                localisation=request.POST.get('localisation'),
                type_contrat=request.POST.get('type_contrat'),
                teletravail='TOTAL' if request.POST.get('teletravail') else 'NON',
                niveau_experience=request.POST.get('niveau_experience'),
                annees_experience_min=request.POST.get('annees_experience_min') or 0,
                niveau_etude_requis=request.POST.get('niveau_etude_requis', ''),
                competences_requises=competences_requises,
                competences_souhaitees=competences_souhaitees,
                salaire_min=request.POST.get('salaire_min') or None,
                salaire_max=request.POST.get('salaire_max') or None,
                salaire_affiche=request.POST.get('salaire_affiche', ''),
                date_limite=request.POST.get('date_limite') or None,
                statut='PUBLIEE',
                est_active=True,
                source='MANUEL'
            )
            
            messages.success(request, f"L'offre '{offre.titre}' a été publiée avec succès !")
            logger.info(f"Offre publiée par {recruteur.organisation} : {offre.titre}")
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la publication : {str(e)}")
            logger.error(f"Erreur publication offre : {e}")
        
        return redirect('myAppli:dashboard_recruteur')
    
    return redirect('myAppli:dashboard_recruteur')

# myAppli/views.py - Ajouter ces fonctions

def generer_lettre_motivation(request):
    """
    Générateur de lettre de motivation personnalisable
    """
    # Récupérer les données du candidat si connecté
    user_data = {}
    if request.user.is_authenticated and hasattr(request.user, 'particulier'):
        particulier = request.user.particulier
        if hasattr(particulier, 'candidat'):
            candidat = particulier.candidat
            user_data = {
                'nom': particulier.nom,
                'prenom': particulier.prenom,
                'email': particulier.email,
                'telephone': str(particulier.telephone),
                'adresse': particulier.adresse,
                'ville': particulier.ville,
                'competences': candidat.competences,
                'niveauEtude': candidat.niveauEtude,
                'experiences': candidat.anneesExperiences,
            }
    
    # Récupérer les offres d'emploi pour le select
    offres = OffreEmploi.objects.filter(statut='PUBLIEE', est_active=True).order_by('-date_publication')[:20]
    
    context = {
        'user_data': user_data,
        'offres': offres,
    }
    return render(request, 'myAppli/outils_emploi/generer_lettre_motivation.html', context)


#@login_required
@require_http_methods(["POST"])
def generer_lettre_pdf(request):
    """
    Génère le PDF de la lettre de motivation
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.pdfgen import canvas
    import io
    from django.http import HttpResponse
    
    # Récupérer les données du formulaire
    data = request.POST
    prenom = data.get('prenom', '')
    nom = data.get('nom', '')
    email = data.get('email', '')
    telephone = data.get('telephone', '')
    adresse = data.get('adresse', '')
    ville = data.get('ville', '')
    
    entreprise_nom = data.get('entreprise_nom', '')
    poste = data.get('poste', '')
    offre_reference = data.get('offre_reference', '')
    
    # Sections personnalisées
    presentation = data.get('presentation', '')
    competences = data.get('competences', '')
    motivations = data.get('motivations', '')
    disponibilite = data.get('disponibilite', '')
    
    # Style choisi
    style = data.get('style', 'classique')
    
    # Créer le PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Styles personnalisés
    style_title = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1ed760'),
        alignment=TA_CENTER,
        spaceAfter=30,
    )
    
    style_subtitle = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    
    style_normal = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=10,
    )
    
    style_signature = ParagraphStyle(
        'Signature',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_LEFT,
        spaceBefore=30,
    )
    
    # En-tête selon le style
    if style == 'moderne':
        # En-tête moderne avec cadre
        header_data = [[
            Paragraph(f"<b>{prenom} {nom}</b>", style_title),
        ]]
        header_table = Table(header_data, colWidths=[doc.width])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1ed760')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 20))
        
        # Coordonnées
        contact_text = f"{adresse}<br/>{ville}<br/>{telephone}<br/>{email}"
        story.append(Paragraph(contact_text, styles['Normal']))
        
    else:  # classique
        # En-tête classique
        story.append(Paragraph(f"{prenom} {nom}", style_title))
        story.append(Paragraph(f"{adresse}", styles['Normal']))
        story.append(Paragraph(f"{ville}", styles['Normal']))
        story.append(Paragraph(f"Tél: {telephone} | Email: {email}", styles['Normal']))
    
    story.append(Spacer(1, 30))
    
    # Date
    from datetime import datetime
    date_obj = timezone.now()()
    story.append(Paragraph(f"Le {date_obj.strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Destinataire
    story.append(Paragraph(f"À l'attention du recruteur", styles['Normal']))
    story.append(Paragraph(f"{entreprise_nom}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Objet
    story.append(Paragraph(f"<b>Objet : Candidature pour le poste de {poste}</b>", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Corps de la lettre
    story.append(Paragraph("Madame, Monsieur,", styles['Normal']))
    story.append(Spacer(1, 10))
    
    # Introduction
    intro = f"Actuellement à la recherche d'un nouveau défi professionnel, j'ai l'honneur de vous présenter ma candidature pour le poste de <b>{poste}</b> au sein de votre structure."
    if offre_reference:
        intro += f" Suite à votre offre d'emploi référencée <b>{offre_reference}</b>, je me permets de vous adresser ma candidature."
    story.append(Paragraph(intro, style_normal))
    story.append(Spacer(1, 10))
    
    # Présentation
    if presentation:
        story.append(Paragraph(presentation, style_normal))
        story.append(Spacer(1, 10))
    else:
        story.append(Paragraph(f"Titulaire d'un {user_data.get('niveauEtude', 'diplôme')}, je dispose d'une expérience de {user_data.get('experiences', 0)} ans dans le domaine.", style_normal))
        story.append(Spacer(1, 10))
    
    # Compétences
    if competences:
        story.append(Paragraph("<b>Mes compétences clés :</b>", styles['Normal']))
        story.append(Paragraph(competences, style_normal))
    else:
        story.append(Paragraph("<b>Mes atouts :</b>", styles['Normal']))
        story.append(Paragraph(f"• {user_data.get('competences', 'Rigueur, autonomie et esprit d\'équipe')}", style_normal))
    story.append(Spacer(1, 10))
    
    # Motivations
    if motivations:
        story.append(Paragraph("<b>Mes motivations :</b>", styles['Normal']))
        story.append(Paragraph(motivations, style_normal))
    else:
        story.append(Paragraph("<b>Pourquoi me rejoindre ?</b>", styles['Normal']))
        story.append(Paragraph("Je suis convaincu que mon profil correspond aux valeurs et aux besoins de votre entreprise. Dynamique et passionné, je saurai m'investir pleinement dans les missions qui me seront confiées.", style_normal))
    story.append(Spacer(1, 10))
    
    # Disponibilité
    if disponibilite:
        story.append(Paragraph(f"Je suis disponible à compter du {disponibilite}.", styles['Normal']))
    else:
        story.append(Paragraph("Je me tiens à votre disposition pour un entretien à votre convenance.", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Formule de politesse
    story.append(Paragraph("Je vous remercie de l'attention que vous porterez à ma candidature et vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.", style_normal))
    story.append(Spacer(1, 30))
    
    # Signature
    story.append(Paragraph(f"{prenom} {nom}", style_signature))
    
    # Générer le PDF
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="lettre_motivation_{nom}_{prenom}.pdf"'
    return response


def telecharger_modele_lettre(request):
    """
    Télécharge un modèle de lettre de motivation au format DOCX
    """
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    import io
    
    buffer = io.BytesIO()
    doc = Document()
    
    # Style du document
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)
    
    # En-tête
    title = doc.add_heading('LETTRE DE MOTIVATION', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()
    
    # Coordonnées
    doc.add_paragraph('[Votre Nom et Prénom]')
    doc.add_paragraph('[Votre Adresse]')
    doc.add_paragraph('[Code Postal, Ville]')
    doc.add_paragraph('[Téléphone]')
    doc.add_paragraph('[Email]')
    
    doc.add_paragraph()
    doc.add_paragraph(f"Le [Date]")
    doc.add_paragraph()
    
    # Destinataire
    doc.add_paragraph("À l'attention du service recrutement")
    doc.add_paragraph("[Nom de l'entreprise]")
    doc.add_paragraph("[Adresse de l'entreprise]")
    
    doc.add_paragraph()
    doc.add_paragraph("Objet : Candidature pour le poste de [Intitulé du poste]")
    doc.add_paragraph()
    
    # Corps
    doc.add_paragraph("Madame, Monsieur,")
    doc.add_paragraph()
    
    p = doc.add_paragraph("Actuellement à la recherche d'un nouveau défi professionnel, j'ai l'honneur de vous présenter ma candidature pour le poste de [Intitulé du poste] au sein de votre structure.")
    doc.add_paragraph()
    
    doc.add_paragraph("[Décrivez votre parcours et vos compétences]")
    doc.add_paragraph()
    
    doc.add_paragraph("Je reste à votre disposition pour un entretien afin de vous exposer plus en détail ma motivation et mes compétences.")
    doc.add_paragraph()
    
    doc.add_paragraph("Je vous remercie de l'attention que vous porterez à ma candidature et vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.")
    doc.add_paragraph()
    
    doc.add_paragraph("[Signature]")
    
    doc.save(buffer)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = 'attachment; filename="modele_lettre_motivation.docx"'
    return response

def apercu_style_lettre(request, style):
    """Génère un aperçu HTML d'un style de lettre"""
    # Données d'exemple pour l'aperçu
    contexte = {
        'style': style,
        'prenom': 'Juste',
        'nom': 'KABORE',
        'email': 'juste.kabore@email.com',
        'telephone': '01 23 45 67',
        'adresse': '123 rue de l\'Exemple',
        'ville': 'Bobo',
        'entreprise_nom': 'Entreprise ABC',
        'poste': 'Développeur Web',
        'date': datetime.now().strftime('%d/%m/%Y')
    }
    
    return render(request, f'lettre/aperçu_{style}.html', contexte)

def gestion_entreprise(request):
    # Liste des outils en développement
    tools_in_development = [
        'facture', 'offre_cout', 'contrat', 'fiche_poste', 'paie', 
        'rapport', 'pv', 'pitch', 'communique', 'plan_com', 
        'profil_ent', 'note_meth', 'biblio_doc'
    ]
    
    # Statistiques pour le hero
    stats = {
        'total_outils': 21,
        'categories': 5,
        'ia_assistee': 6
    }
    
    # Données de démonstration pour le tableau de bord
    dashboard_data = {
        'kpis': {
            'chiffre_affaire_mois': 24500,
            'objectif_mensuel': 30000,
            'taux_realisation': 82,
            'nb_candidats_mois': 12,
            'nb_entretiens_realises': 8,
            'projets_en_cours': 3,
            'taux_activite': 75
        },
        'alertes': [
            {'type': 'warning', 'message': 'Déclaration URSSAF dans 5 jours'},
            {'type': 'info', 'message': 'Entretien annuel à planifier pour 3 employés'},
            {'type': 'success', 'message': 'Votre proposition pour le marché SONABHY a été retenue !'}
        ]
    }
    
    # Date du jour pour les calculs
    today = timezone.now().date()
    
    context = {
        'today': today,
        'tools_in_development': tools_in_development,
        'stats': stats,
        'dashboard': dashboard_data,
        'annee_courante': today.year,
    }
    
    return render(request, 'myAppli/gestion/gestion_entreprise.html', context)