from django.contrib import admin
from django.utils.html import format_html
from urllib.parse import quote
from .models import *

@admin.register(Offre_uemoa)
class Offre_uemoaAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return Offre_uemoa.all_objects.all()

@admin.register(Ami_uemoa)
class Ami_uemoaAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return Ami_uemoa.all_objects.all()

@admin.register(OffreEmploi)
class OffreEmploiAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return OffreEmploi.all_objects.all()

admin.site.register(Entreprise)
admin.site.register(Particulier)
admin.site.register(Candidat)
admin.site.register(Recruteur)
admin.site.register(ModeleDocument)
admin.site.register(DossierSoumission)
admin.site.register(DocumentGenere)
admin.site.register(ReferenceTechnique)
admin.site.register(PersonnelCle)
admin.site.register(MaterielEntreprise)
admin.site.register(ModeleCV)
admin.site.register(CVGenere)
admin.site.register(LettreMotivationGeneree)
admin.site.register(DossierCandidature)
admin.site.register(Convocation)