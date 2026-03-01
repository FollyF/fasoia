# myAppli/apps.py

from django.apps import AppConfig

class MyAppliConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myAppli'
    
    def ready(self):
        # C'est ici que les signaux sont chargés
        import myAppli.signals
        print("✅ Signaux chargés avec succès !")