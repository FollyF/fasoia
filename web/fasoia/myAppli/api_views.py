# myAppli/api_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login as django_login
from .api_serializers import RegisterSerializer, LoginSerializer, UserProfileSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from decimal import Decimal

class RegisterView(APIView):
    """Inscription mobile"""
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            refresh = RefreshToken.for_user(user)
            
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
                    "profile_type": serializer.get_profile_type(),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


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