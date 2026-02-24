from urllib.parse import urljoin

from django.core.management.base import BaseCommand
from myAppli.models import Citation
from myAppli.utils.web_scraper.uemoa_scraper import scraper

class Command(BaseCommand):
    help = 'Scrape quotes and save to DB'
    def handle(self, *args, **options):
        base_url ='https://www.uemoa.int/appel-d-offre'
        all_data =scraper(base_url)
        for data in all_data:
            Citation.objects.update_or_create(
                description=data['description'],
                date_limite=data['date_limite'],
                download_url=urljoin(base_url,data['download_url'])
            )
        self.stdout.write(self.style.SUCCESS(f'Successfully saved {len(all_data)} opportunities'))