from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Entreprise, Particulier

class RegisterMobileSerializer(serializers.Serializer):
    # Champs communs
    profile_type = serializers.ChoiceField(choices=['particulier', 'entreprise'])
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    # Champs spécifiques (optionnels selon le type)
    fullname = serializers.CharField(required=False, allow_blank=True) # Pour Particulier
    raison_sociale = serializers.CharField(required=False, allow_blank=True) # Pour Entreprise

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def create(self, validated_data):
        profile_type = validated_data.get('profile_type')
        email = validated_data.get('email')
        password = validated_data.get('password')

        # 1. Création du User Django (le username sera l'email)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        # 2. Création du profil selon le type
        if profile_type == 'entreprise':
            Entreprise.objects.create(
                user=user,
                email=email,
                raisonSociale=validated_data.get('raison_sociale'),
                typeProfil='ENTREPRISE'
            )
        else:
            # On sépare le nom complet pour remplir nom/prenom
            fullname = validated_data.get('fullname', '')
            parts = fullname.split(' ', 1)
            prenom = parts[0]
            nom = parts[1] if len(parts) > 1 else ''
            
            Particulier.objects.create(
                user=user,
                email=email,
                nom=nom,
                prenom=prenom,
                typeProfil='PARTICULIER'
            )
        return user