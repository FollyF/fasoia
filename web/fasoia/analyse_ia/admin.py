from django.contrib import admin
from .models import AnalyseDocument, DocumentSource, ElementsExtraits, Recommandation

admin.site.register(AnalyseDocument)
admin.site.register(DocumentSource)
admin.site.register(ElementsExtraits)
admin.site.register(Recommandation)