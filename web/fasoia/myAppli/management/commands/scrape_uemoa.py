# management/commands/scrape_uemoa.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from myAppli.models import SourceDonnees
from myAppli.scrapers.uemoa_scraper import UEMOAScraper
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scrape les opportunités du site UEMOA'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--source-id',
            type=int,
            help='ID de la source UEMOA dans la base'
        )
        parser.add_argument(
            '--pages',
            type=int,
            default=3,
            help='Nombre de pages à scraper'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Début du scraping UEMOA...'))
        
        # Récupérer la source
        if options['source_id']:
            try:
                source = SourceDonnees.objects.get(id=options['source_id'])
            except SourceDonnees.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Source ID {options['source_id']} non trouvée"))
                return
        else:
            # Chercher une source UEMOA existante
            source = SourceDonnees.objects.filter(
                nom__icontains='UEMOA',
                actif=True
            ).first()
            
            if not source:
                # Créer la source si elle n'existe pas
                source = SourceDonnees.objects.create(
                    nom="UEMOA - Appels d'offres",
                    type="UEMOA",
                    url="https://www.uemoa.int/appel-d-offre",
                    frequence="Quotidienne",
                    actif=True
                )
                self.stdout.write(self.style.SUCCESS(f"Source UEMOA créée: {source.nom}"))
        
        # Initialiser et lancer le scraper
        scraper = UEMOAScraper(source)
        opportunites = scraper.scrape()
        
        # Sauvegarder dans la base via l'orchestrateur
        from myAppli.scrapers.opportunite_scraper import ScrapingOrchestrator
        orchestrator = ScrapingOrchestrator()
        
        compteur = 0
        for opp_data in opportunites:
            if orchestrator.save_opportunite(opp_data):
                compteur += 1
        
        # Mettre à jour la source
        source.frequence = f"Dernier run: {timezone.now().strftime('%d/%m/%Y %H:%M')}"
        source.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Scraping UEMOA terminé: {compteur} nouvelles opportunités sur {len(opportunites)} trouvées'
            )
        )