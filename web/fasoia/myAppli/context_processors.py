from .models import Offre_uemoa, Ami_uemoa, OffreEmploi

def total_opportunites(request):
    """Ajoute le nombre total d'opportunités selon le profil de l'utilisateur"""
    
    total = 0
    
    if request.user.is_authenticated:
        # Profil ENTREPRISE
        if hasattr(request.user, 'entreprise'):
            total = Offre_uemoa.objects.count() + Ami_uemoa.objects.count()
        
        # Profil CANDIDAT (particulier avec profil candidat)
        elif hasattr(request.user, 'particulier') and hasattr(request.user.particulier, 'candidat'):
            total = OffreEmploi.objects.filter(statut='PUBLIEE', est_active=True).count()
        
        # Profil RECRUTEUR (particulier avec profil recruteur)
        elif hasattr(request.user, 'particulier') and hasattr(request.user.particulier, 'recruteur'):
            recruteur = request.user.particulier.recruteur
            total = OffreEmploi.objects.filter(recruteur=recruteur, statut='PUBLIEE').count()
        
        # Particulier simple (sans rôle spécifique)
        elif hasattr(request.user, 'particulier'):
            total = OffreEmploi.objects.filter(statut='PUBLIEE', est_active=True).count()
    else:
        total = Offre_uemoa.objects.count() + Ami_uemoa.objects.count() + OffreEmploi.objects.count()
    
    return {
        'total_opportunites': total
    }