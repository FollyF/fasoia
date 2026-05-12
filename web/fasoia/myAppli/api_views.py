# myAppli/api_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login as django_login
from .api_serializers import RegisterSerializer, LoginSerializer, UserProfileSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from decimal import Decimal
from myAppli.models import *
from analyse_ia.models import *

class RegisterView(APIView):
    """Inscription mobile"""
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            refresh = RefreshToken.for_user(user)
            profile_serializer = UserProfileSerializer(user)
            
            
            return Response({
                "success": True,
                "message": "Inscription réussie",
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "profile_type": self._get_profile_type_for_redirect(user),  
                    "display_name": profile_serializer.data['display_name'],
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_profile_type_for_redirect(self, user):
        if hasattr(user, 'entreprise'):
            return 'entreprise'
        elif hasattr(user, 'particulier'):
            p = user.particulier
            if hasattr(p, 'candidat') and not hasattr(p, 'recruteur'):
                return 'candidat'
            if hasattr(p, 'recruteur') and not hasattr(p, 'candidat'):
                return 'recruteur'
            return 'particulier'
        return 'particulier'


class LoginView(APIView):
    """Connexion mobile"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Connecter l'utilisateur (session)
            django_login(request, user)
            
            # Générer les tokens JWT
            refresh = RefreshToken.for_user(user)
            
            # Sérialiser le profil
            profile_serializer = UserProfileSerializer(user)
            
            return Response({
                "success": True,
                "message": self._get_success_message(user),
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "user": profile_serializer.data,
            }, status=status.HTTP_200_OK)
        
        return Response({
            "success": False,
            "message": "Email ou mot de passe incorrect",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_profile_type_for_redirect(self, user):
        """Retourne le type pour la redirection Flutter"""
        if hasattr(user, 'entreprise'):
            return 'entreprise'
        elif hasattr(user, 'particulier'):
            p = user.particulier
            
            # Priorité : les rôles spécifiques
            if hasattr(p, 'candidat') and not hasattr(p, 'recruteur'):
                return 'candidat'
            if hasattr(p, 'recruteur') and not hasattr(p, 'candidat'):
                return 'recruteur'
            
            # Cas par défaut
            return 'particulier'
        return 'particulier'
    
    def _get_success_message(self, user):
        if hasattr(user, 'entreprise'):
            return f"Bon retour parmi nous, {user.entreprise.raisonSociale} !"
        elif hasattr(user, 'particulier'):
            particulier = user.particulier
            if hasattr(particulier, 'candidat'):
                return f"Bon retour parmi nous, {particulier.prenom} !"
            elif hasattr(particulier, 'recruteur'):
                return f"Bon retour parmi nous, {user.recruteur.organisation} !"
            return f"Bon retour parmi nous, {particulier.prenom} !"
        return f"Bon retour parmi nous, {user.email} !"


class LogoutView(APIView):
    """Déconnexion mobile"""
    
    def post(self, request):
        return Response({
            "success": True,
            "message": "Déconnecté"
        })


class MeView(APIView):
    """Profil utilisateur connecté"""
    
    def get(self, request):
        user = request.user
        
        if not user.is_authenticated:
            return Response({
                "success": False,
                "message": "Non authentifié"
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        profile_serializer = UserProfileSerializer(user)
        
        return Response({
            "success": True,
            "user": profile_serializer.data,
        })

class EntrepriseProfilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print('🔐 Auth:', request.user, '| Is auth:', request.user.is_authenticated)
        print('🪙 Header:', request.headers.get('Authorization'))
        user = request.user
        if not hasattr(user, 'entreprise'):
            return Response({'error': 'Profil entreprise introuvable'}, status=404)
        
        e = user.entreprise
        return Response({
            'raisonSociale':          e.raisonSociale,
            'domaineActive':          e.domaineActive,
            'localisation':           e.localisation,
            'taille':                 e.taille,
            'annee_creation':         e.annee_creation,
            'site_web':               e.site_web,
            'description':            e.description,
            'competencesCles':        e.competencesCles,
            'annees_experience':      e.annees_experience,
            'nb_projets_realises':    e.nb_projets_realises,
            'pays_intervention':      e.pays_intervention,      # JSONField → liste
            'rayon_action':           e.rayon_action,
            'chiffre_affaires':       str(e.chiffre_affaires) if e.chiffre_affaires else None,
            'capital_social':         str(e.capital_social) if e.capital_social else None,
            'types_opportunites':     e.types_opportunites,     # JSONField → liste
            'montant_min':            str(e.montant_min) if e.montant_min else None,
            'montant_max':            str(e.montant_max) if e.montant_max else None,
            # Statistiques
            'nb_candidatures_emises': e.nb_candidatures_emises,
            'taux_succes':            e.taux_succes,
            'nb_projets_realises':    e.nb_projets_realises,
            'profil_complet':         e.profil_complet,
        })

    def patch(self, request):
        user = request.user
        if not hasattr(user, 'entreprise'):
            return Response({'error': 'Profil entreprise introuvable'}, status=404)
        
        e = user.entreprise
        data = request.data

        # Champs texte / entier simples
        simple_fields = [
            'domaineActive', 'localisation', 'description', 'site_web',
            'competencesCles', 'references',
            'taille', 'annee_creation', 'annees_experience', 'nb_projets_realises',
            'rayon_action',
        ]
        for field in simple_fields:
            if field in data:
                setattr(e, field, data[field])

        # Champs JSON (listes)
        json_fields = ['pays_intervention', 'types_opportunites', 'certifications', 'agrements']
        for field in json_fields:
            if field in data:
                val = data[field]
                setattr(e, field, val if isinstance(val, list) else [val])

        # Champs Decimal
        decimal_fields = ['chiffre_affaires', 'capital_social', 'montant_min', 'montant_max']
        for field in decimal_fields:
            if field in data and data[field] is not None:
                try:
                    setattr(e, field, Decimal(str(data[field])))
                except Exception:
                    pass

        # Recalculer profil_complet
        e.profil_complet = all([
            e.domaineActive,
            e.localisation,
            e.competencesCles,
            e.pays_intervention,
            e.chiffre_affaires,
            e.types_opportunites,
        ])

        # Mettre à jour l'index des mots-clés pour le matching
        e.sauvegarder_mots_cles()  # appelle aussi e.save()

        return self.get(request)  # Retourne le profil à jour


class EntrepriseRecommandationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not hasattr(user, 'entreprise'):
            return Response({'recommandations': []})

        recommandations = []
        # ✅ related_name='recommandations' (pas recommandation_set)
        recos = user.entreprise.recommandations.all()

        for r in recos:
            try:
                opp = r.opportunite  # @property — pas de select_related
                recommandations.append({
                    'opportunite_type': r.opportunite_type,
                    'score_global':     round(r.score_global, 1),
                    'opportunite': {
                        'id':          opp.id,
                        'description': getattr(opp, 'description', ''),
                        'date_limite': opp.date_limite.strftime('%d/%m/%Y') if getattr(opp, 'date_limite', None) else None,
                    }
                })
            except Exception as e:
                print(f'⚠️ Reco {r.id} ignorée: {e}')
                continue

        return Response({'recommandations': recommandations})

class CandidatProfilView(APIView):
    """Profil candidat pour mobile"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Vérifier que l'utilisateur est un particulier
        if not hasattr(user, 'particulier'):
            return Response({'error': 'Profil particulier introuvable'}, status=404)
        
        particulier = user.particulier
        
        # Vérifier que l'utilisateur est un candidat
        if not hasattr(particulier, 'candidat'):
            return Response({'error': 'Profil candidat introuvable'}, status=404)
        
        candidat = particulier.candidat
        
        # Calculer la progression du profil
        champs_profil = [
            ('nom', particulier.nom),
            ('prenom', particulier.prenom),
            ('email', particulier.email),
            ('telephone', particulier.telephone),
            ('date_naissance', particulier.date_naissance),
            ('adresse', particulier.adresse),
            ('ville', particulier.ville),
            ('pays', particulier.pays),
            ('niveauEtude', candidat.niveauEtude),
            ('competences', candidat.competences),
            ('disponibilite', candidat.disponibilite),
            ('niveauLangues', candidat.niveauLangues),
            ('secteur_recherche', candidat.secteur_recherche),
            ('type_contrat_recherche', candidat.type_contrat_recherche),
            ('localisation_recherche', candidat.localisation_recherche),
            ('anneesExperiences', candidat.anneesExperiences),
            ('salaire_souhaite', candidat.salaire_souhaite),
            ('mobilite', candidat.mobilite),
            ('cv', candidat.cv),
            ('lettre_motivation', candidat.lettre_motivation),
        ]
        
        champs_remplis = 0
        for nom_champ, valeur in champs_profil:
            if nom_champ == 'mobilite':
                est_rempli = True
            elif nom_champ in ['cv', 'lettre_motivation']:
                est_rempli = bool(valeur)
            elif nom_champ in ['anneesExperiences', 'salaire_souhaite']:
                est_rempli = valeur is not None and valeur > 0
            elif nom_champ == 'date_naissance':
                est_rempli = bool(valeur)
            else:
                est_rempli = bool(valeur and str(valeur).strip())
            
            if est_rempli:
                champs_remplis += 1
        
        total_champs = len(champs_profil)
        progression = int((champs_remplis / total_champs) * 100) if total_champs > 0 else 0
        
        # Compter les convocations
        convocations_obtenues = candidat.convocations.count() if hasattr(candidat, 'convocations') else 0
        
        return Response({
            'particulier': {
                'nom': particulier.nom,
                'prenom': particulier.prenom,
                'email': particulier.email,
                'telephone': particulier.telephone,
                'date_naissance': particulier.date_naissance,
                'adresse': particulier.adresse,
                'ville': particulier.ville,
                'pays': particulier.pays,
            },
            'candidat': {
                'niveauEtude': candidat.niveauEtude,
                'anneesExperiences': candidat.anneesExperiences,
                'competences': candidat.competences,
                'disponibilite': candidat.disponibilite,
                'niveauLangues': candidat.niveauLangues,
                'secteur_recherche': candidat.secteur_recherche,
                'type_contrat_recherche': candidat.type_contrat_recherche,
                'localisation_recherche': candidat.localisation_recherche,
                'salaire_souhaite': str(candidat.salaire_souhaite) if candidat.salaire_souhaite else None,
                'mobilite': candidat.mobilite,
                'cv': candidat.cv.name if candidat.cv else None,
                'lettre_motivation': candidat.lettre_motivation.name if candidat.lettre_motivation else None,
                'nb_candidatures_envoyees': candidat.nb_candidatures_envoyees,
            },
            'progression': progression,
            'champs_remplis': champs_remplis,
            'total_champs': total_champs,
            'convocations_obtenues': convocations_obtenues,
        })

    def patch(self, request):
        user = request.user
        
        if not hasattr(user, 'particulier'):
            return Response({'error': 'Profil particulier introuvable'}, status=404)
        
        particulier = user.particulier
        
        if not hasattr(particulier, 'candidat'):
            return Response({'error': 'Profil candidat introuvable'}, status=404)
        
        candidat = particulier.candidat
        data = request.data
        
        # Mettre à jour les champs du particulier
        particulier_fields = ['nom', 'prenom', 'email', 'telephone', 'date_naissance', 'adresse', 'ville', 'pays']
        for field in particulier_fields:
            if field in data:
                setattr(particulier, field, data[field])
        particulier.save()
        
        # Mettre à jour les champs du candidat
        candidat_fields = [
            'niveauEtude', 'anneesExperiences', 'competences', 'disponibilite',
            'niveauLangues', 'secteur_recherche', 'type_contrat_recherche',
            'localisation_recherche', 'salaire_souhaite', 'mobilite'
        ]
        for field in candidat_fields:
            if field in data:
                setattr(candidat, field, data[field])
        
        # Gérer l'upload de CV
        if 'cv' in request.FILES:
            candidat.cv = request.FILES['cv']
        
        # Gérer l'upload de lettre de motivation
        if 'lettre_motivation' in request.FILES:
            candidat.lettre_motivation = request.FILES['lettre_motivation']
        
        candidat.save()
        
        return self.get(request)


class CandidatOffresRecommandeesView(APIView):
    """Offres recommandées pour un candidat"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'particulier'):
            return Response({'offres': []})
        
        particulier = user.particulier
        
        if not hasattr(particulier, 'candidat'):
            return Response({'offres': []})
        
        candidat = particulier.candidat
        
        # Essayer de récupérer les recommandations
        offres = []
        
        try:
            recommandations = RecommandationEmploi.objects.filter(
                candidat=candidat
            ).select_related('offre').order_by('-score_global')[:20]
            
            for reco in recommandations:
                offre = reco.offre
                offres.append({
                    'id': offre.id,
                    'titre': offre.titre,
                    'description': offre.description,
                    'date_limite': offre.date_limite.strftime('%d/%m/%Y') if offre.date_limite else None,
                    'ville': getattr(offre, 'ville', ''),
                    'localisation': getattr(offre, 'localisation', ''),
                    'type_contrat': offre.type_contrat if hasattr(offre, 'type_contrat') else '',
                    'get_type_contrat_display': dict(offre.TYPE_CONTRAT).get(offre.type_contrat, '') if hasattr(offre, 'TYPE_CONTRAT') else '',
                    'score': round(reco.score_global * 100, 1),
                    'recruteur': {
                        'organisation': offre.recruteur.organisation if hasattr(offre, 'recruteur') else ''
                    } if hasattr(offre, 'recruteur') else None,
                })
        except Exception as e:
            print(f"Erreur chargement recommandations: {e}")
        
        return Response({'offres': offres})


class CandidatConvocationsView(APIView):
    """Convocations du candidat"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'particulier'):
            return Response({'convocations': []})
        
        particulier = user.particulier
        
        if not hasattr(particulier, 'candidat'):
            return Response({'convocations': []})
        
        candidat = particulier.candidat
        
        convocations = []
        
        try:
            convs = Convocation.objects.filter(
                dossier__candidat=candidat
            ).order_by('-date_rdv')
            
            for conv in convs:
                convocations.append({
                    'id': conv.id,
                    'type_entretien': conv.type_entretien,
                    'get_type_entretien_display': dict(conv.TYPE_ENTRETIEN).get(conv.type_entretien, ''),
                    'date_rdv': conv.date_rdv.strftime('%d/%m/%Y') if conv.date_rdv else None,
                    'heure_rdv': conv.heure_rdv.strftime('%H:%M') if conv.heure_rdv else None,
                    'lieu_rdv': conv.lieu_rdv,
                    'message': conv.message,
                    'statut': conv.statut,
                    'poste': conv.dossier.offre.titre if hasattr(conv, 'dossier') and conv.dossier and hasattr(conv.dossier, 'offre') else '',
                    'organisation': conv.recruteur.organisation if hasattr(conv, 'recruteur') and conv.recruteur else '',
                })
        except Exception as e:
            print(f"Erreur chargement convocations: {e}")
        
        return Response({'convocations': convocations})


class RepondreConvocationView(APIView):
    """Répondre à une convocation"""
    permission_classes = [IsAuthenticated]

    def post(self, request, convId):
        user = request.user
        action = request.data.get('action')
        
        if action not in ['confirmee', 'annulee']:
            return Response({'success': False, 'error': 'Action invalide'}, status=400)
        
        try:
            conv = Convocation.objects.get(id=convId)
            
            # Vérifier que l'utilisateur est bien le candidat concerné
            if not hasattr(user, 'particulier') or not hasattr(user.particulier, 'candidat'):
                return Response({'success': False, 'error': 'Non autorisé'}, status=403)
            
            if conv.dossier.candidat != user.particulier.candidat:
                return Response({'success': False, 'error': 'Non autorisé'}, status=403)
            
            conv.statut = action
            conv.save()
            
            message = "Convocation confirmée" if action == 'confirmee' else "Convocation annulée"
            
            return Response({'success': True, 'message': message})
            
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=404)


class CandidatProfilView(APIView):
    """Profil candidat pour mobile"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'particulier'):
            return Response({'error': 'Profil particulier introuvable'}, status=404)
        
        particulier = user.particulier
        
        if not hasattr(particulier, 'candidat'):
            return Response({'error': 'Profil candidat introuvable'}, status=404)
        
        candidat = particulier.candidat
        
        a_un_cv = bool(candidat.cv) or CVGenere.objects.filter(
            utilisateur=candidat.particulier.user,
            fichier_pdf__isnull=False
        ).exists()
        
        # Champs obligatoires (les mêmes que dans le template)
        champs_obligatoires = [
            ('nom', bool(particulier.nom and str(particulier.nom).strip())),
            ('prenom', bool(particulier.prenom and str(particulier.prenom).strip())),
            ('email', bool(particulier.email and str(particulier.email).strip())),
            ('telephone', bool(particulier.telephone and str(particulier.telephone).strip())),
            ('niveauEtude', bool(candidat.niveauEtude and str(candidat.niveauEtude).strip())),
            ('competences', bool(candidat.competences and str(candidat.competences).strip())),
            ('disponibilite', bool(candidat.disponibilite and str(candidat.disponibilite).strip())),
            ('cv', a_un_cv),
        ]
        
        # Vérifier si tous les champs obligatoires sont remplis
        profil_complet = all(est_rempli for _, est_rempli in champs_obligatoires)
        champs_manquants = [nom for nom, est_rempli in champs_obligatoires if not est_rempli]
        
        # Calcul de la progression (pour affichage)
        total_champs_obligatoires = len(champs_obligatoires)
        champs_remplis_obligatoires = sum(1 for _, est_rempli in champs_obligatoires if est_rempli)
        progression = int((champs_remplis_obligatoires / total_champs_obligatoires) * 100) if total_champs_obligatoires > 0 else 0
        
        # ===== COMPTER LES CONVOCATIONS =====
        
        convocations_obtenues = Convocation.objects.filter(
            dossier__candidat=candidat,
            statut='confirmee'
        ).count()
        
        # ===== OFFRES RECOMMANDÉES (seulement si profil complet) =====
        offres_recommandees = []
        if profil_complet:
            try:
                
                recommandations = RecommandationEmploi.objects.filter(
                    candidat=candidat
                ).select_related('offre').order_by('-score_global')[:10]
                
                if recommandations.exists():
                    for reco in recommandations:
                        offre = reco.offre
                        offres_recommandees.append({
                            'id': offre.id,
                            'titre': offre.titre,
                            'description': offre.description,
                            'date_limite': offre.date_limite.strftime('%d/%m/%Y') if offre.date_limite else None,
                            'ville': offre.ville,
                            'localisation': offre.localisation,
                            'type_contrat': offre.type_contrat,
                            'get_type_contrat_display': dict(offre.TYPE_CONTRAT_CHOICES).get(offre.type_contrat, ''),
                            'score': round(reco.score_global * 100, 1),
                            'entreprise': offre.entreprise_nom or (offre.recruteur.organisation if offre.recruteur else ''),
                        })
                else:
                    # Fallback: offres récentes
                    offres_recents = OffreEmploi.objects.filter(
                        statut='PUBLIEE',
                        est_active=True
                    ).order_by('-date_publication')[:10]
                    
                    for offre in offres_recents:
                        offres_recommandees.append({
                            'id': offre.id,
                            'titre': offre.titre,
                            'description': offre.description,
                            'date_limite': offre.date_limite.strftime('%d/%m/%Y') if offre.date_limite else None,
                            'ville': offre.ville,
                            'localisation': offre.localisation,
                            'type_contrat': offre.type_contrat,
                            'get_type_contrat_display': dict(offre.TYPE_CONTRAT_CHOICES).get(offre.type_contrat, ''),
                            'score': 50,  # Score par défaut
                            'entreprise': offre.entreprise_nom or (offre.recruteur.organisation if offre.recruteur else ''),
                        })
            except Exception as e:
                print(f"Erreur chargement recommandations: {e}")
        
        print("="*50)
        print(f"🔍 DIAGNOSTIC RECOMMANDATIONS")
        print(f"profil_complet: {profil_complet}")
        print(f"nombre offres: {len(offres_recommandees)}")
        print("="*50)
        return Response({
            'particulier': {
                'nom': particulier.nom,
                'prenom': particulier.prenom,
                'email': particulier.email,
                'telephone': str(particulier.telephone) if particulier.telephone else None,
                'date_naissance': particulier.date_naissance.strftime('%Y-%m-%d') if particulier.date_naissance else None,
                'adresse': particulier.adresse,
                'ville': particulier.ville,
                'pays': particulier.pays,
            },
            'candidat': {
                'niveauEtude': candidat.niveauEtude,
                'anneesExperiences': candidat.anneesExperiences,
                'competences': candidat.competences,
                'disponibilite': candidat.disponibilite,
                'niveauLangues': candidat.niveauLangues,
                'secteur_recherche': candidat.secteur_recherche,
                'type_contrat_recherche': candidat.type_contrat_recherche,
                'localisation_recherche': candidat.localisation_recherche,
                'salaire_souhaite': str(candidat.salaire_souhaite) if candidat.salaire_souhaite else None,
                'mobilite': candidat.mobilite,
                'cv': candidat.cv.name if candidat.cv else None,
                'lettre_motivation': candidat.lettre_motivation.name if candidat.lettre_motivation else None,
                'nb_candidatures_envoyees': candidat.nb_candidatures_envoyees,
            },
            'profil_complet': profil_complet,  # ← AJOUTÉ
            'progression': progression,
            'champs_remplis': champs_remplis_obligatoires,
            'total_champs': total_champs_obligatoires,
            'champs_manquants': champs_manquants,  # ← AJOUTÉ
            'convocations_obtenues': convocations_obtenues,
            'offres_recommandees': offres_recommandees,
        })

class CandidatOffresRecommandeesView(APIView):
    """Offres recommandées pour un candidat"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'particulier'):
            return Response({'offres': []})
        
        particulier = user.particulier
        
        if not hasattr(particulier, 'candidat'):
            return Response({'offres': []})
        
        candidat = particulier.candidat
        
        # Récupérer les offres publiées
        offres = OffreEmploi.objects.filter(
            statut='PUBLIEE',
            est_active=True
        ).order_by('-date_publication')[:20]
        
        resultats = []
        for offre in offres:
            # Calculer un score simple basé sur la correspondance
            score = 50  # Score de base
            
            # Bonus si secteur correspond
            if candidat.secteur_recherche and offre.secteur:
                if candidat.secteur_recherche.lower() in offre.secteur.lower():
                    score += 20
            
            # Bonus si type de contrat correspond
            if candidat.type_contrat_recherche and offre.type_contrat:
                if candidat.type_contrat_recherche == offre.type_contrat:
                    score += 15
            
            # Bonus si localisation correspond
            if candidat.localisation_recherche and offre.ville:
                if candidat.localisation_recherche.lower() in offre.ville.lower():
                    score += 15
            
            resultats.append({
                'id': offre.id,
                'titre': offre.titre,
                'description': offre.description,
                'date_limite': offre.date_limite.strftime('%d/%m/%Y') if offre.date_limite else None,
                'ville': offre.ville,
                'localisation': offre.localisation,
                'type_contrat': offre.type_contrat,
                'get_type_contrat_display': dict(offre.TYPE_CONTRAT_CHOICES).get(offre.type_contrat, ''),
                'score': min(score, 100),
                'entreprise': offre.entreprise_nom or (offre.recruteur.organisation if offre.recruteur else ''),
                'recruteur': {
                    'organisation': offre.recruteur.organisation if offre.recruteur else ''
                } if offre.recruteur else None,
            })
        
        return Response({'offres': resultats})


class CandidatConvocationsView(APIView):
    """Convocations du candidat"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'particulier'):
            return Response({'convocations': []})
        
        particulier = user.particulier
        
        if not hasattr(particulier, 'candidat'):
            return Response({'convocations': []})
        
        candidat = particulier.candidat
        
        convocations = Convocation.objects.filter(
            dossier__candidat=candidat
        ).order_by('-date_rdv')
        
        resultats = []
        for conv in convocations:
            resultats.append({
                'id': conv.id,
                'type_entretien': conv.type_entretien,
                'get_type_entretien_display': dict(conv.TYPE_ENTRETIEN).get(conv.type_entretien, '') if hasattr(conv, 'TYPE_ENTRETIEN') else '',
                'date_rdv': conv.date_rdv.strftime('%d/%m/%Y') if conv.date_rdv else None,
                'heure_rdv': conv.heure_rdv.strftime('%H:%M') if conv.heure_rdv else None,
                'lieu_rdv': conv.lieu_rdv,
                'message': conv.message,
                'statut': conv.statut,
                'poste': conv.dossier.offre.titre if hasattr(conv, 'dossier') and conv.dossier and hasattr(conv.dossier, 'offre') else '',
                'organisation': conv.recruteur.organisation if hasattr(conv, 'recruteur') and conv.recruteur else '',
            })
        
        return Response({'convocations': resultats})


class RepondreConvocationView(APIView):
    """Répondre à une convocation"""
    permission_classes = [IsAuthenticated]

    def post(self, request, convId):
        user = request.user
        action = request.data.get('action')
        
        if action not in ['confirmee', 'annulee']:
            return Response({'success': False, 'error': 'Action invalide'}, status=400)
        
        try:
            
            conv = Convocation.objects.get(id=convId)
            
            # Vérifier que l'utilisateur est bien le candidat concerné
            if not hasattr(user, 'particulier') or not hasattr(user.particulier, 'candidat'):
                return Response({'success': False, 'error': 'Non autorisé'}, status=403)
            
            if conv.dossier.candidat != user.particulier.candidat:
                return Response({'success': False, 'error': 'Non autorisé'}, status=403)
            
            conv.statut = action
            conv.save()
            
            message = "Convocation confirmée" if action == 'confirmee' else "Convocation annulée"
            
            return Response({'success': True, 'message': message})
            
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=404)