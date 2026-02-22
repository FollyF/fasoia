from django.core.management.base import BaseCommand
from myAppli.models import Citation
from myAppli.utils.web_scraper.scraper import scraper

class Command(BaseCommand):
    help = 'Scrape quotes and save to DB'
    def handle(self, *args, **options):
        base_url ='https://quotes.toscrape.com'
        all_data =scraper(base_url)
        for data in all_data:
            Citation.objects.get_or_create(
                text=data['text'],
                author=data['author'],
                defaults={'tags': data['tags']}
            )
        self.stdout.write(self.style.SUCCESS(f'Successfully saved {len(all_data)} donnees'))