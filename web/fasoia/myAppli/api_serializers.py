# myAppli/api_serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Entreprise, Particulier


class RegisterSerializer(serializers.Serializer):
    profile_type = serializers.ChoiceField(choices=['particulier', 'entreprise'])
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    fullname = serializers.CharField(required=False, allow_blank=True, write_only=True)
    raison_sociale = serializers.CharField(required=False, allow_blank=True, write_only=True)
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value
    
    def create(self, validated_data):
        profile_type = validated_data['profile_type']
        email = validated_data['email']
        password = validated_data['password']
        
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )
        
        if profile_type == 'entreprise':
            Entreprise.objects.create(
                user=user,
                email=email,
                raisonSociale=validated_data.get('raison_sociale', ''),
                typeProfil='ENTREPRISE'
            )
        else:
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
        
        self._profile_type = profile_type
        return user
    
    def get_profile_type(self):
        return getattr(self, '_profile_type', None)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Email ou mot de passe incorrect")
        
        user = authenticate(username=user.username, password=password)
        
        if not user:
            raise serializers.ValidationError("Email ou mot de passe incorrect")
        
        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.Serializer):
    """Sérialise les informations utilisateur"""
    
    def to_representation(self, user):
        if hasattr(user, 'entreprise'):
            profile_type = 'entreprise'
            display_name = user.entreprise.raisonSociale
        elif hasattr(user, 'particulier'):
            particulier = user.particulier
            display_name = f"{particulier.prenom} {particulier.nom}"
            
            if hasattr(particulier, 'candidat'):
                profile_type = 'candidat'
            elif hasattr(particulier, 'recruteur'):
                profile_type = 'recruteur'
                display_name = user.recruteur.organisation
            else:
                profile_type = 'particulier'
        else:
            profile_type = 'unknown'
            display_name = user.email
        
        return {
            'id': user.id,
            'email': user.email,
            'profile_type': profile_type,
            'display_name': display_name,
        }