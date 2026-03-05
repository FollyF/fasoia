from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators import csrf
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.conf import settings
import logging

from .forms import InscriptionForm, ConnexionForm
from .models import *
logger = logging.getLogger(__name__)


def home(request):
    """
    Page d'accueil avec les dernières opportunités
    """
    # Récupérer les 5 dernières offres et AMI
    dernieres_offres = Offre_uemoa.objects.all().order_by('-date_scraping')[:5]
    derniers_amis = Ami_uemoa.objects.all().order_by('-date_scraping')[:5]
    
    # Compter le total
    total_opportunites = Offre_uemoa.objects.count() + Ami_uemoa.objects.count()
    
    context = {
        'dernieres_offres': dernieres_offres,
        'derniers_amis': derniers_amis,
        'total_opportunites': total_opportunites,
    }
    return render(request, 'myAppli/home.html', context)

def opportunites(request):
    offre_uemoa = Offre_uemoa.objects.all()
    ami = Ami_uemoa.objects.all()
    context = {
        'offre': offre_uemoa,
        'ami' : ami    
    }
    return render(request, 'myAppli/opportunites.html', context)


@require_http_methods(["GET", "POST"])
@csrf_protect
def inscription(request):
    """
    Vue d'inscription - Gère les 3 types de profils
    """
    if request.user.is_authenticated:
        messages.info(request, "Vous êtes déjà connecté")
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
                    return redirect('myAppli:tableau_bord_entreprise')
                    
                elif profile_type == 'particulier':
                    particulier = user.particulier
                    messages.success(
                        request, 
                        f"Bienvenue {particulier.prenom} {particulier.nom} ! Votre compte a été créé avec succès."
                    )
                    logger.info(f"Nouvelle inscription particulier : {user.email}")
                    return redirect('myAppli:home')
                    
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
        messages.info(request, f"Vous êtes déjà connecté en tant que {request.user.email}")
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
                return redirect('myAppli:tableau_bord_entreprise')
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
def tableau_bord_entreprise(request):
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
    
    return render(request, 'myAppli/tableau_bord_entreprise.html', {
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
    
    return redirect('myAppli:tableau_bord_entreprise')

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