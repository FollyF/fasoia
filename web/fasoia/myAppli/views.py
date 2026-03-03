from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.conf import settings
import logging

from .forms import InscriptionForm, ConnexionForm
from .models import *

logger = logging.getLogger(__name__)


def home(request):
    return render(request, 'myAppli/home.html')

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
    Vue d'inscription
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
                
                messages.success(
                    request, 
                    f"Bienvenue {form.cleaned_data['fullname']} ! Votre compte a été créé avec succès."
                )
                
                logger.info(f"Nouvelle inscription : {user.email}")
                return redirect('myAppli:home')
                
            except Exception as e:
                logger.error(f"Erreur lors de l'inscription : {str(e)}")
                messages.error(request, "Une erreur est survenue. Veuillez réessayer.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = InscriptionForm()
    
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
            
            # Met à jour la dernière connexion
            if hasattr(user, 'profil'):
                from django.utils import timezone
                user.profil.derniere_connexion = timezone.now()
                user.profil.save()
            
            messages.success(request, f"Bon retour parmi nous, {user.first_name or user.email} !")
            logger.info(f"Connexion réussie : {user.email}")
            
            next_url = request.GET.get('next', 'myAppli:home')
            return redirect(next_url)
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
    Vue du profil utilisateur
    """
    return render(request, 'myAppli/profil.html', {
        'user': request.user,
        'profil': request.user.profil if hasattr(request.user, 'profil') else None
    })