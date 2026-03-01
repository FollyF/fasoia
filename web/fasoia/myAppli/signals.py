# myAppli/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Entreprise
import threading
from datetime import datetime

# Import direct du moteur
from analyse_ia.moteur_recommandation import MoteurRecommandation

def log_message(message):
    """Logger simple"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [SIGNAL] {message}")

def generer_recommandations_async(entreprise_id):
    """
    Lance la génération des recommandations pour une entreprise
    en appelant DIRECTEMENT le moteur
    """
    try:
        log_message(f"🚀 Début des recommandations pour entreprise #{entreprise_id}")
        
        # Récupérer l'entreprise
        from .models import Entreprise
        entreprise = Entreprise.objects.get(id=entreprise_id)
        
        # Appeler le moteur directement
        moteur = MoteurRecommandation()
        recommandations = moteur.recommander_pour_entreprise(entreprise)
        
        log_message(f"✅ {len(recommandations)} recommandations générées")
        
    except Exception as e:
        log_message(f"❌ Erreur: {e}")

@receiver(post_save, sender=Entreprise)
def declencher_recommandations(sender, instance, created, **kwargs):
    """
    Déclenché à la création d'une entreprise
    """
    if created:
        log_message(f"🎉 Nouvelle entreprise: {instance.raisonSociale} (ID: {instance.id})")
        
        # Lancer en arrière-plan
        thread = threading.Thread(
            target=generer_recommandations_async,
            args=(instance.id,)
        )
        thread.daemon = True
        thread.start()
        
        log_message(f"⚙️ Génération lancée en arrière-plan")