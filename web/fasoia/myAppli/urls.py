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

# import API Flutter
from rest_framework_simplejwt.views import TokenRefreshView
from .api_views import *

app_name = 'myAppli'

urlpatterns = [
    # Pages publiques
    path('test/', views.test, name='test'),
    path('', views.home, name='home'),
    path('opportunites/', views.opportunites, name='opportunites'),
    path('connexion/', views.connexion, name='connexion'),
    path('inscription/', views.inscription, name='inscription'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('profil/', views.profil, name='profil'),
    
    # Dashboards
    path('dashboard/opportunites/', views.dashboard_opportunites, name='dashboard_opportunites'),
    path('dashboard/entreprise/', views.dashboard_entreprise, name='dashboard_entreprise'),
    path('dashboard/particulier/', views.dashboard_particulier, name='dashboard_particulier'),
    path('dashboard/recruteur/', views.dashboard_recruteur, name='dashboard_recruteur'),
    path('dashboard/candidat/', views.dashboard_candidat, name='dashboard_candidat'),
    
    # Activation profils
    path('activer/profil/candidat/', views.activer_profil_candidat, name='activer_profil_candidat'),
    path('activer/profil/recruteur/', views.activer_profil_recruteur, name='activer_profil_recruteur'),
    
    # Complétion profils
    path('completer/profil/entreprise/', views.completer_profil_entreprise, name='completer_profil_entreprise'),
    path('completer/profil/candidat/', views.completer_profil_candidat, name='completer_profil_candidat'),
    path('completer/profil/recruteur/', views.completer_profil_recruteur, name='completer_profil_recruteur'),
    path('api/entreprise/upload-entete/', views.api_entreprise_upload_entete, name='api_entreprise_upload_entete'),
    
    # Détails opportunités
    path('offre/<int:pk>/', views.detail_offre, name='detail_offre'),
    path('ami/<int:pk>/', views.detail_ami, name='detail_ami'),
    path('emploi/<int:pk>/', views.detail_emploi, name='detail_emploi'),
    
    # Soumission
    path('soumission/<str:opportunite_type>/<int:opportunite_id>/', 
         views.nouvelle_soumission, name='nouvelle_soumission'),
    
    path('api/dossier/soumettre/', 
         views.api_dossier_soumettre, name='api_dossier_soumettre'),
    

    path('api/dossier/etat/', 
         views.api_dossier_etat, name='api_dossier_etat'),
    
    path('api/dossier/telecharger_complet/', 
         views.api_dossier_telecharger_complet, name='api_dossier_telecharger_complet'),
    
    path('api/dossier/telecharger_complet/<int:dossier_id>/', 
         views.api_dossier_telecharger_complet, name='api_dossier_telecharger_par_id'),

    path('api/document/apercu/', 
         views.api_document_apercu, name='api_document_apercu'),
    
    path('api/document/generer/', 
         views.api_document_generer, name='api_document_generer'),
    
    path('api/document/importer/', 
         views.api_document_importer, name='api_document_importer'),
    
    path('api/document/modifier/', 
         views.api_document_modifier, name='api_document_modifier'),
    
    path('api/document/supprimer/', 
         views.api_document_supprimer, name='api_document_supprimer'),
    
    path('api/document/telecharger/', 
         views.api_document_telecharger, name='api_document_telecharger'),

    path('api/materiel/liste/', 
         views.api_materiel_liste, name='api_materiel_liste'),
    
    path('api/materiel/ajouter/', 
         views.api_materiel_ajouter, name='api_materiel_ajouter'),
    
    path('api/materiel/modifier/', 
         views.api_materiel_modifier, name='api_materiel_modifier'),

    path('api/materiel/supprimer/', 
         views.api_materiel_supprimer, name='api_materiel_supprimer'),

    path('api/personnel/liste/', 
         views.api_personnel_liste, name='api_personnel_liste'),
    
    path('api/personnel/ajouter/', 
         views.api_personnel_ajouter, name='api_personnel_ajouter'),
    
    path('api/personnel/modifier/', 
         views.api_personnel_modifier, name='api_personnel_modifier'),
    
    path('api/personnel/supprimer/', 
         views.api_personnel_supprimer, name='api_personnel_supprimer'),
    
    path('mes_soumissions/', 
         views.mes_soumissions, name='mes_soumissions'),
    
    # Emploi
    path('trouver/emploi/', views.trouver_emploi, name='trouver_emploi'),
    path('offre/modifier/<int:offre_id>/', views.modifier_offre, name='modifier_offre'),
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
    path('recruteur/publier/offre/', views.publier_offre_emploi, name='publier_offre_emploi'),

    # Entretien
    path('convocation/envoyer/', views.envoyer_convocation, name='envoyer_convocation'), 
    path('candidat/repondre/convocation/<int:convocation_id>/', views.repondre_convocation, name='repondre_convocation'),
    path('entretien/', views.preparer_entretien, name='preparer_entretien'),
    path('entretien/demarrer/', views.demarrer_session, name='demarrer_session'),
    path('entretien/session/<int:session_id>/', views.session_entretien, name='session_entretien'),
    path('entretien/session/<int:session_id>/repondre/<int:question_id>/', views.repondre_question, name='repondre_question'),
    path('entretien/session/<int:session_id>/terminer/', views.terminer_session, name='terminer_session'), 
    
    # Candidature
    path('offre/<int:offre_id>/postuler/', views.soumettre_candidature, name='soumettre_candidature'),
    path('offre/<int:offre_id>/analyser/cv/', views.analyser_cv_offre, name='analyser_cv_offre'),
    path('offre/<int:offre_id>/generer/lettre/', views.generer_lettre, name='generer_lettre'),
    path('offre/<int:offre_id>/enregistrer/dossier/', views.enregistrer_dossier, name='enregistrer_dossier'),
    path('candidature/<int:dossier_id>/', views.detail_dossier_candidature, name='detail_dossier_candidature'),
    
    # API endpoints pour mobile
    path('api/register/', RegisterView.as_view(), name='api_register'),
    path('api/login/', LoginView.as_view(), name='api_login'),
    path('api/logout/', LogoutView.as_view(), name='api_logout'),
    path('api/me/', MeView.as_view(), name='api_me'),
    path('api/token/refresh/', TokenRefreshView.as_view()), 
    path('api/entreprise/profil/', EntrepriseProfilView.as_view()),
    path('api/entreprise/recommandations/', EntrepriseRecommandationsView.as_view()),
    path('api/candidat/profil/', CandidatProfilView.as_view(), name='api_candidat_profil'),
    path('api/candidat/offres/recommandees/', CandidatOffresRecommandeesView.as_view(), name='api_candidat_offres'),
    path('api/candidat/convocations/', CandidatConvocationsView.as_view(), name='api_candidat_convocations'),
    path('api/candidat/convocations/<int:convId>/repondre/', RepondreConvocationView.as_view(), name='api_repondre_convocation'),

]