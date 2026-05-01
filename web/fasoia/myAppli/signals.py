from django.db.models.signals import post_save
from django.dispatch import receiver
from myAppli.models import Entreprise
import threading
import os
import sys

@receiver(post_save, sender=Entreprise)
def declencher_recommandations(sender, instance, created, **kwargs):
    """Déclenche automatiquement les recommandations quand une entreprise est créée"""
    if created:
        print(f"\n🔄 Nouvelle entreprise créée: {instance.raisonSociale}")
        print("   Lancement des recommandations en arrière-plan...")
        
        def run_recommandations():
            # Configuration dynamique du chemin
            current_path = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_path)
            
            if project_root not in sys.path:
                sys.path.append(project_root)
                
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
            
            import django
            django.setup()
            
            from analyse_ia.moteur_recommandation import MoteurRecommandationSemantique
            moteur = MoteurRecommandationSemantique()
            moteur.recommander_pour_entreprise(instance)
        
        thread = threading.Thread(target=run_recommandations)
        thread.start()