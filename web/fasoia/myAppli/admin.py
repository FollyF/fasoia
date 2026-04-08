from django.contrib import admin
from django.utils.html import format_html
from urllib.parse import quote
from .models import *

# =============================================
# ENREGISTREMENT DES MODÈLES
# =============================================

admin.site.register(Offre_uemoa)
admin.site.register(Ami_uemoa)
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
admin.site.register(OffreEmploi)
admin.site.register(Candidature)
admin.site.register(ModeleCV)
admin.site.register(CVGenere)