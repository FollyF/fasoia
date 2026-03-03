from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import ProfilUtilisateur

class InscriptionForm(UserCreationForm):
    """
    Formulaire d'inscription avec gestion du profil
    """
    PROFILE_CHOICES = [
        ('particulier', 'Particulier'),
        ('entreprise', 'Entreprise'),
        ('partenaire', 'Partenaire'),
    ]
    
    profile_type = forms.ChoiceField(
        choices=PROFILE_CHOICES, 
        initial='particulier',
        widget=forms.HiddenInput(),
        required=True
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'nom@domaine.com',
            'class': 'form-input',
            'autocomplete': 'email'
        }),
        required=True
    )
    
    fullname = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Votre nom complet',
            'class': 'form-input',
            'id': 'fullname-input'
        }),
        required=True
    )
    
    password1 = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Créez un mot de passe',
            'class': 'form-input',
            'autocomplete': 'new-password'
        }),
        required=True
    )
    
    password2 = forms.CharField(
        label='Confirmation',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirmez votre mot de passe',
            'class': 'form-input',
            'autocomplete': 'new-password'
        }),
        required=True
    )
    
    class Meta:
        model = User
        fields = ('email', 'fullname')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Cet email est déjà utilisé")
        return email
    
    def clean_fullname(self):
        fullname = self.cleaned_data.get('fullname')
        fullname = ' '.join(fullname.split())
        if len(fullname) < 2:
            raise ValidationError("Le nom doit contenir au moins 2 caractères")
        return fullname
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # Utilise l'email comme username
        user.email = self.cleaned_data['email']
        
        # Sépare le nom complet en prénom et nom
        parts = self.cleaned_data['fullname'].split(' ', 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ''
        
        if commit:
            user.save()
            # Met à jour le type de profil
            if hasattr(user, 'profil'):
                user.profil.type_profil = self.cleaned_data['profile_type']
                user.profil.save()
        
        return user


class ConnexionForm(AuthenticationForm):
    """
    Formulaire de connexion personnalisé
    """
    username = forms.EmailField(
        label='Adresse e-mail',
        widget=forms.EmailInput(attrs={
            'placeholder': 'nom@domaine.com',
            'class': 'form-input',
            'autocomplete': 'email'
        }),
        required=True
    )
    
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Votre mot de passe',
            'class': 'form-input',
            'autocomplete': 'current-password'
        }),
        required=True
    )
    
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'remember-checkbox'})
    )
    
    error_messages = {
        'invalid_login': "Email ou mot de passe incorrect",
        'inactive': "Ce compte est désactivé",
    }