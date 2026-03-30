from django.core.management.base import BaseCommand
from myAppli.models import ModeleCV

class Command(BaseCommand):
    help = 'Initialise les modèles de CV'

    def handle(self, *args, **options):
        modeles = [
            {'nom': 'Moderne', 'categorie': 'moderne', 'est_populaire': True, 'ordre_affichage': 1},
            {'nom': 'Classique', 'categorie': 'classique', 'ordre_affichage': 2},
            {'nom': 'Minimaliste', 'categorie': 'minimaliste', 'ordre_affichage': 3},
            {'nom': 'Professionnel', 'categorie': 'professionnel', 'ordre_affichage': 4},
            {'nom': 'Créatif', 'categorie': 'creatif', 'ordre_affichage': 5, 'est_premium': True},
        ]
        
        for modele_data in modeles:
            ModeleCV.objects.get_or_create(
                categorie=modele_data['categorie'],
                defaults=modele_data
            )
            self.stdout.write(self.style.SUCCESS(f"✅ Modèle {modele_data['nom']} créé"))