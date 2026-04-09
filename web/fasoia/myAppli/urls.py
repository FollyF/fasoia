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
     path('dashboard/opportunites/', views.dashboard_opportunites, name='dashboard_opportunites'),
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
     path('completer/profil/recruteur/', 
          views.completer_profil_recruteur, 
          name='completer_profil_recruteur'
     ),
     path('offre/<int:pk>/', 
          views.detail_offre, name='detail_offre'),

     path('ami/<int:pk>/', views.detail_ami, 
          name='detail_ami'),

     path('emploi/<int:pk>/', views.detail_emploi, 
          name='detail_emploi'),

     path('soumission/<str:opportunite_type>/<int:opportunite_id>/commencer/', 
               views.commencer_soumission, name='commencer_soumission'),

     path('soumission/generer/document/<str:type_doc>/', 
          views.generer_document_soumission, name='generer_document_soumission'),

     path('soumission/apercu/document/<str:type_doc>/', 
          views.apercu_document_soumission, name='apercu_document_soumission'),
     
     path('soumission/get/donnees/<str:type_doc>/', 
          views.get_donnees_document, name='get_donnees_document'),
     
     path('soumission/telecharger/document/<str:type_doc>/', 
          views.telecharger_document_soumission, name='telecharger_document_soumission'),
     
     path('soumission/sauvegarder/donnees/', 
          views.sauvegarder_donnees_soumission, name='sauvegarder_donnees_soumission'),
     
     path('soumission/etat/documents/', 
          views.etat_documents_soumission, name='etat_documents_soumission'),

     path('entreprise/ajouter/materiel/<int:entreprise_id>/', 
               views.ajouter_materiel, name='ajouter_materiel'),

     path('entreprise/ajouter/personnel/<int:entreprise_id>/', 
               views.ajouter_personnel, name='ajouter_personnel'),

     path('soumission/confirmer/<str:opportunite_type>/<int:opportunite_id>/valider/', 
          views.valider_soumission, name='valider_soumission'),

     path('soumission/document/<int:document_id>/valider/', 
          views.valider_document, name='valider_document'),

     path('soumission/dossier/<int:dossier_id>/soumettre/', 
          views.soumettre_dossier, name='soumettre_dossier'),

     path('mes_soumissions/', 
          views.mes_soumissions, name='mes_soumissions'),
     path('trouver/emploi/', views.trouver_emploi, name='trouver_emploi'),
     path('generer/cv/', views.generer_cv, name='generer_cv'),
     path('preparer/entretien/', views.preparer_entretien, name='preparer_entretien'),
     path('alerte/emploi/', views.alertes_emploi, name='alertes_emploi'),
     path('gestion/entreprise/', views.gestion_entreprise, name='gestion_entreprise'),
     path('mes_cvs/', views.mes_cvs, name='mes_cvs'),
     path('cv/importer/', views.importer_cv, name='importer_cv'),
     path('cv/telecharger/<int:cv_id>/<str:format>/', views.telecharger_cv, name='telecharger_cv'),
     path('cv/supprimer/<int:cv_id>/', views.supprimer_cv, name='supprimer_cv'),
     path('cv/dupliquer/<int:cv_id>/', views.dupliquer_cv, name='dupliquer_cv'),
     path('cv/modifier/<int:cv_id>/', views.modifier_cv, name='modifier_cv'),
     path('cv/apercu/cv/<int:cv_id>/', views.apercu_cv, name='apercu_cv'), 
     path('cv/apercu/style/<str:style>/', views.apercu_style_cv, name='apercu_style_cv'),
     path('generer/lettre_motivation/', views.generer_lettre_motivation, name='generer_lettre_motivation'),
     path('generer/lettre/pdf/', views.generer_lettre_pdf, name='generer_lettre_pdf'),
     path('generer/lettre/modele/', views.telecharger_modele_lettre, name='telecharger_modele_lettre'),
     path('lettre/apercu/style/<str:style>/', views.apercu_style_lettre, name='apercu_style_lettre'),
     path('soumission/dossier/<int:dossier_id>/documents/', views.get_dossier_documents, name='get_dossier_documents'),
     path('soumission/document/<int:document_id>/telecharger/', views.telecharger_document, name='telecharger_document'),
     path('recruteur/publier/offre/', views.publier_offre_emploi, name='publier_offre_emploi'),
]
