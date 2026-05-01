from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

from .serializers import RegisterMobileSerializer

class RegisterMobileView(APIView):
    def post(self, request):
        serializer = RegisterMobileSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # On génère les tokens pour que Flutter puisse connecter l'utilisateur tout de suite
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "message": "Utilisateur créé avec succès",
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "user": {
                    "email": user.email,
                    "profile_type": request.data.get('profile_type')
                }
            }, status=status.HTTP_201_CREATED)
        print("Erreurs de validation :", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer