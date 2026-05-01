# myAppli/apps.py

from django.apps import AppConfig

class MyAppliConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myAppli'
    
    def ready(self):
        import myAppli.signals  # <--- Ajoute ça dans la méthode ready
        

    