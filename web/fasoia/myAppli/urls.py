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
    path('', views.home,  name='home'),
    path('opportunites/', views.opportunites, name='opportunites'),
    path('connexion/', views.connexion, name='connexion'),
    path('inscription/', views.inscription, name='inscription'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('profil/', views.profil, name='profil'),
    path('tableau_bord_entreprise/', 
         views.tableau_bord_entreprise, 
         name='tableau_bord_entreprise'
    ),
    path('completer-profil-entreprise/', 
         views.completer_profil_entreprise, 
         name='completer_profil_entreprise'
    ),
    path('offre/<int:pk>/', 
         views.detail_offre, name='detail_offre'),
    path('ami/<int:pk>/', views.detail_ami, 
         name='detail_ami'),
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
]
