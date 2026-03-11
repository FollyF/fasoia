from django.contrib import admin
from django.utils.html import format_html
from urllib.parse import quote
from .models import *

# =============================================
# FONCTION UTILITAIRE POUR WHATSAPP
# =============================================

def construire_message_whatsapp(entreprise, recommandations):
    """Construit un message WhatsApp avec les recommandations"""
    prenom = entreprise.prenom if entreprise.prenom else "cher partenaire"
    
    message = f"🔔 *RECOMMANDATIONS POUR {entreprise.raisonSociale.upper()}*\n\n"
    message += f"Bonjour {prenom},\n\n"
    message += f"Nous avons trouvé *{len(recommandations)} opportunités* pour vous :\n\n"
    
    for i, reco in enumerate(recommandations[:3], 1):
        opportunite = reco.opportunite
        type_opp = "📄 OFFRE" if reco.opportunite_type == 'Offre_uemoa' else "📋 AMI"
        
        message += f"{i}. *{type_opp}*\n"
        message += f"   📌 {opportunite.description[:50]}...\n"
        message += f"   🎯 Score: {reco.score_global}%\n\n"
    
    message += "Connectez-vous sur https://fasoia.com pour postuler !\n"
    message += "L'équipe FasoIA"
    
    return message

# =============================================
# ADMIN ENTREPRISE
# =============================================

class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ['raisonSociale', 'prenom', 'nom', 'email', 'telephone', 
                    'profil_complet', 'nb_recommandations', 'whatsapp_button']
    list_filter = ['profil_complet', 'domaineActive', 'localisation']
    search_fields = ['raisonSociale', 'email', 'nom', 'prenom', 'telephone']
    
    def nb_recommandations(self, obj):
        from analyse_ia.models import Recommandation
        count = Recommandation.objects.filter(entreprise=obj).count()
        if count > 0:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
                count
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 5px 10px; border-radius: 3px;">0</span>'
        )
    nb_recommandations.short_description = 'Recommandations'
    
    def whatsapp_button(self, obj):
        from analyse_ia.models import Recommandation
        
        recommandations = Recommandation.objects.filter(entreprise=obj).order_by('-score_global')[:3]
        nb_recos = recommandations.count()
        
        if nb_recos == 0:
            return format_html('<span style="color: #999;">-</span>')
        
        # Construire le message et le lien
        message = construire_message_whatsapp(obj, recommandations)
        message_encoded = quote(message)
        telephone = str(obj.telephone).replace('+', '').replace(' ', '')
        whatsapp_link = f"https://wa.me/{telephone}?text={message_encoded}"
        
        return format_html(
            '<a href="{}" target="_blank" style="background-color:#25D366; color:white; padding:5px 10px; border-radius:3px; text-decoration:none; display:inline-block; font-size:12px;">'
            '<i class="fab fa-whatsapp"></i> Envoyer</a>',
            whatsapp_link
        )
    whatsapp_button.short_description = 'WhatsApp'

# =============================================
# ENREGISTREMENT DES MODÈLES
# =============================================

admin.site.register(Offre_uemoa)
admin.site.register(Ami_uemoa)
admin.site.register(Entreprise, EntrepriseAdmin)
admin.site.register(ModeleDocument)
admin.site.register(DossierSoumission)
admin.site.register(DocumentSoumission)