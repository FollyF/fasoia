"""
URL configuration for fasoia project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views
app_name = 'myAppli'

urlpatterns = [
    path('test/', views.test, name='test'),
    path('', views.home,  name='home'),
    path('opportunites/', views.opportunites, name='opportunites'),
    path('connexion/', views.connexion, name='connexion'),
    path('inscription/', views.inscription, name='inscription'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('profil/', views.profil, name='profil'),
    path('dashboard/entreprise/', 
         views.dashboard_entreprise, 
         name='dashboard_entreprise'
    ),
    path('dashboard/particulier/', 
         views.dashboard_particulier, 
         name='dashboard_particulier'
    ),
    path('dashboard/recruteur/', 
         views.dashboard_recruteur, 
         name='dashboard_recruteur'
    ),
    path('dashboard/candidat/', 
         views.dashboard_candidat, 
         name='dashboard_candidat'
    ),
    path('activer/profil/candidat/', views.activer_profil_candidat, name='activer_profil_candidat'),

    path('activer/profil/recruteur/', views.activer_profil_recruteur, name='activer_profil_recruteur'),

    path('completer/profil/entreprise/', 
         views.completer_profil_entreprise, 
         name='completer_profil_entreprise'
    ),
    path('completer/profil/candidat/', 
         views.completer_profil_candidat, 
         name='completer_profil_candidat'
    ),
    path('offre/<int:pk>/', 
         views.detail_offre, name='detail_offre'),

    path('ami/<int:pk>/', views.detail_ami, 
         name='detail_ami'),

    path('emploi/<int:pk>/', views.detail_emploi, 
         name='detail_emploi'),

    path('soumission/<str:opportunite_type>/<int:opportunite_id>/commencer/', 
          views.commencer_soumission, name='commencer_soumission'),

    path('soumission/dossier/<int:dossier_id>/preparer/', views.preparer_soumission, 
         name='preparer_soumission'),
    
    path('soumission/dossier/<int:dossier_id>/generer/<int:modele_id>/', 
          views.generer_document, name='generer_document'),
    
    path('soumission/document/<int:document_id>/telecharger/', 
         views.telecharger_document, name='telecharger_document'),
    
    path('soumission/document/<int:document_id>/valider/', 
         views.valider_document, name='valider_document'),
    
    path('soumission/dossier/<int:dossier_id>/soumettre/', 
         views.soumettre_dossier, name='soumettre_dossier'),
    
    path('mes_soumissions/', 
         views.mes_soumissions, name='mes_soumissions'),

    path('admin/whatsapp/', views.tous_liens_whatsapp, name='tous_liens_whatsapp'),
    path('admin/whatsapp/export/csv/', views.exporter_liens_whatsapp_csv, name='exporter_liens_whatsapp'),
    path('admin/whatsapp/export/txt/', views.exporter_liens_whatsapp_txt, name='exporter_liens_whatsapp_txt'),
    path('api/whatsapp/lien/<int:entreprise_id>/', views.get_whatsapp_link, name='get_whatsapp_link'),
    path('trouver/emploi/', views.trouver_emploi, name='trouver_emploi'),
    path('generer/cv/', views.generer_cv, name='generer_cv'),
    path('generer/lettre_motivation/', views.generer_lettre_motivation, name='generer_lettre_motivation'),
    path('preparer/entretien/', views.preparer_entretien, name='preparer_entretien'),
    path('alerte/emploi/', views.alertes_emploi, name='alertes_emploi'),
    path('gestion/entreprise/', views.gestion_entreprise, name='gestion_entreprise'),
    path('faq/', views.faq, name='faq'),
    path('contact/', views.contact, name='contact'),
    path('guide/', views.guide, name='guide'),
    path('parametres/', views.parametres, name='parametres'),
    path('mes_candidatures/', views.mes_candidatures, name='mes_candidatures'),
    path('mes_offres/', views.mes_offres, name='mes_offres'),
    path('mes_cvs/', views.mes_cvs, name='mes_cvs'),
    path('cv/importer/', views.importer_cv, name='importer_cv'),
    path('cv/telecharger/<int:cv_id>/<str:format>/', views.telecharger_cv, name='telecharger_cv'),
    path('cv/supprimer/<int:cv_id>/', views.supprimer_cv, name='supprimer_cv'),
    path('cv/dupliquer/<int:cv_id>/', views.dupliquer_cv, name='dupliquer_cv'),
    path('cv/modifier/<int:cv_id>/', views.modifier_cv, name='modifier_cv'),
    path('cv/apercu/<int:cv_id>/', views.apercu_cv, name='apercu_cv'), 
    path('cv/apercu/<str:style>/', views.apercu_style_cv, name='apercu_style_cv'),
    path('soumission/dossier/<int:dossier_id>/documents/', views.get_dossier_documents, name='get_dossier_documents'),
    path('soumission/document/<int:document_id>/telecharger/', views.telecharger_document, name='telecharger_document'),
]
