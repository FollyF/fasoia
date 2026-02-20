from django.contrib import admin

# Register your models here.
# admin.py - Ajoutez cette configuration
from django.contrib import admin
from myAppli.models import SourceDonnees

@admin.register(SourceDonnees)
class SourceDonneesAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type', 'url', 'frequence', 'actif', 'get_last_run']
    list_filter = ['type', 'actif']
    search_fields = ['nom', 'url']
    
    def get_last_run(self, obj):
        return obj.frequence if 'Dernier run' in obj.frequence else '-'
    get_last_run.short_description = 'Dernier scraping'
    
    actions = ['scrape_maintenant']
    
    def scrape_maintenant(self, request, queryset):
        from django.core.management import call_command
        for source in queryset:
            if source.type == 'UEMOA':
                call_command('scrape_uemoa', source_id=source.id)
                self.message_user(request, f"Scraping lancé pour {source.nom}")
    scrape_maintenant.short_description = "Lancer le scraping maintenant"