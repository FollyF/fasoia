from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import Entreprise, Particulier, Recruteur, Candidat

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
    
    # Champ pour le nom complet (pour particulier/partenaire)
    fullname = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Votre nom complet',
            'class': 'form-input',
            'id': 'fullname-input'
        }),
        required=False  # Pas requis pour entreprise
    )
    
    # Champ pour la raison sociale (pour entreprise)
    raison_sociale = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Nom de votre entreprise',
            'class': 'form-input',
            'id': 'raison-sociale-input'
        }),
        required=False  # Rendu requis dynamiquement
    )
    
    telephone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': 'Téléphone (optionnel)',
            'class': 'form-input'
        }),
        required=False
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
        fields = ('email',)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Récupérer le profile_type depuis les données POST ou depuis initial
        profile_type = 'particulier'  # Valeur par défaut
        
        # Priorité aux données POST (quand le formulaire est soumis)
        if self.data.get('profile_type'):
            profile_type = self.data.get('profile_type')
        # Sinon, utiliser la valeur initiale (pour l'affichage initial)
        elif self.initial.get('profile_type'):
            profile_type = self.initial.get('profile_type')
        
        self.ajuster_champs_selon_profil(profile_type)
    
    def ajuster_champs_selon_profil(self, profile_type):
        """Ajuste les champs requis selon le type de profil"""
        if profile_type == 'entreprise':
            # Pour entreprise : raison_sociale requis, fullname masqué
            self.fields['raison_sociale'].required = True
            self.fields['raison_sociale'].widget = forms.TextInput(attrs={
                'placeholder': 'Nom de votre entreprise',
                'class': 'form-input'
            })
            
            self.fields['fullname'].required = False
            self.fields['fullname'].widget = forms.HiddenInput()
            
        else:
            # Pour particulier/partenaire : fullname requis, raison_sociale masqué
            self.fields['fullname'].required = True
            self.fields['fullname'].widget = forms.TextInput(attrs={
                'placeholder': 'Votre nom complet',
                'class': 'form-input'
            })
            
            self.fields['raison_sociale'].required = False
            self.fields['raison_sociale'].widget = forms.HiddenInput()
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Cet email est déjà utilisé")
        return email
    
    def clean_fullname(self):
        """Validation pour particulier/partenaire"""
        profile_type = self.cleaned_data.get('profile_type')
        fullname = self.cleaned_data.get('fullname', '')
        
        if profile_type != 'entreprise':
            if not fullname:
                raise ValidationError("Le nom complet est requis")
            fullname = ' '.join(fullname.split())
            if len(fullname) < 2:
                raise ValidationError("Le nom doit contenir au moins 2 caractères")
            return fullname
        return ''
    
    def clean_raison_sociale(self):
        """Validation pour entreprise"""
        profile_type = self.cleaned_data.get('profile_type')
        raison_sociale = self.cleaned_data.get('raison_sociale', '')
        
        if profile_type == 'entreprise':
            if not raison_sociale:
                raise ValidationError("Le nom de l'entreprise est requis")
            return raison_sociale
        return ''
    
    def clean(self):
        cleaned_data = super().clean()
        profile_type = cleaned_data.get('profile_type')
        
        # Vérification que le type est valide
        if profile_type not in ['particulier', 'entreprise', 'partenaire']:
            raise ValidationError("Type de profil invalide")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        
        profile_type = self.cleaned_data['profile_type']
        
        if profile_type == 'entreprise':
            # Pour entreprise : pas de nom/prénom dans User
            user.first_name = ''
            user.last_name = ''
        else:
            # Pour particulier/partenaire : on remplit first_name/last_name
            fullname = self.cleaned_data.get('fullname', '')
            if fullname:
                parts = fullname.split(' ', 1)
                user.first_name = parts[0]
                user.last_name = parts[1] if len(parts) > 1 else ''
        
        if commit:
            user.save()
            
            # Création du profil spécifique selon le type
            if profile_type == 'entreprise':
                # Créer une entreprise avec juste l'essentiel
                Entreprise.objects.create(
                    user=user,
                    nom='',  # Sera rempli plus tard
                    prenom='',  # Sera rempli plus tard
                    email=user.email,
                    telephone=self.cleaned_data.get('telephone', ''),
                    typeProfil='ENTREPRISE',
                    raisonSociale=self.cleaned_data['raison_sociale'],
                    # Champs obligatoires avec valeurs par défaut
                    domaineActive='',
                    competencesCles='',
                    localisation='',
                    taille=0
                )
                
            elif profile_type == 'particulier':
                # Créer un particulier
                Particulier.objects.create(
                    user=user,
                    nom=user.last_name,
                    prenom=user.first_name,
                    email=user.email,
                    telephone=self.cleaned_data.get('telephone', ''),
                    typeProfil='PARTICULIER'
                )
                
            elif profile_type == 'partenaire':
                # Créer un partenaire (recruteur)
                Recruteur.objects.create(
                    user=user,
                    nom=user.last_name,
                    prenom=user.first_name,
                    email=user.email,
                    telephone=self.cleaned_data.get('telephone', ''),
                    typeProfil='PARTENAIRE',
                    organisation='',
                    secteur='',
                    typeStructure=''
                )
        
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