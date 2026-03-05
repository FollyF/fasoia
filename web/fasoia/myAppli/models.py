from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class CarnevasDocument(models.Model):
    nom = models.CharField(max_length=100)
    categorie = models.CharField(max_length=100)
    contenuBase = models.TextField(null=True)
    variable = models.CharField(max_length=100)

    def __str__(self):
        return self.nom

class Dossier(models.Model):
    typeDossier = models.CharField(max_length=100)
    dateCreation = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name="Date de création")
    statut = models.CharField(max_length=100)
    version = models.CharField(max_length=10)

    def __str__(self):
        return self.typeDossier
    
class Document(models.Model):
    nom = models.CharField(max_length=100)
    contenu = models.TextField(null=True)
    taille = models.DecimalField(max_digits=10, decimal_places=2)
    typeDocument = models.CharField(max_length=100)
    dateUpload = models.DateField(auto_now_add=True, auto_now=False)
    fileUpload = models.FileField(upload_to=None, max_length=100)

    def __str__(self):
        return self.nom

class Profil(models.Model):
    role = models.CharField(max_length=100)
    autorisation = models.CharField(max_length=300)
    cycleVie = models.CharField(max_length=100)

    def __str__(self):
        return self.role

# Classe abstraite Utilisateur avec le OneToOneField vers User
class Utilisateur(models.Model):
    class Meta:
        abstract = True
    
    # Le OneToOneField est placé ici, dans la classe abstraite
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='%(class)s',  # Dynamique : entreprise, particulier
        null=True, 
        blank=True
    )
    
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, unique=True)
    telephone = PhoneNumberField()
    typeProfil = models.CharField(max_length=100)  # 'ENTREPRISE', 'PARTICULIER'
    dateInscription = models.DateField(auto_now_add=True)
    statut = models.CharField(max_length=100, default='ACTIF')

    def __str__(self):
        return f"{self.prenom} {self.nom}"

# Entreprise hérite de Utilisateur
class Entreprise(Utilisateur):
    # Champs spécifiques à l'entreprise
    raisonSociale = models.CharField(max_length=100)
    domaineActive = models.CharField(max_length=100, help_text="Secteur d'activité principal")
    competencesCles = models.CharField(max_length=300, help_text="Compétences séparées par des virgules")
    localisation = models.CharField(max_length=100, help_text="Ville, Pays")
    taille = models.IntegerField(help_text="Nombre d'employés")
    
    # Informations complémentaires
    description = models.TextField(blank=True, help_text="Présentation de l'entreprise", default='')
    site_web = models.URLField(blank=True, default='')
    annee_creation = models.IntegerField(null=True, blank=True, default=None)
    
    # Capacité financière
    chiffre_affaires = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Chiffre d'affaires annuel en FCFA",
        default=None
    )
    capital_social = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Capital social en FCFA",
        default=None
    )
    
    # Zones d'intervention
    pays_intervention = models.JSONField(
        default=list, 
        blank=True,
        help_text="Liste des pays où l'entreprise peut intervenir"
    )
    rayon_action = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Rayon d'action en km autour du siège",
        default=None
    )
    
    # Expérience et références
    annees_experience = models.IntegerField(default=0)
    nb_projets_realises = models.IntegerField(default=0)
    references = models.TextField(blank=True, help_text="Principales références", default='')
    
    # Certifications et agréments
    certifications = models.JSONField(default=list, blank=True)
    agrements = models.JSONField(default=list, blank=True)
    
    # Pour le matching intelligent
    mots_cles_index = models.JSONField(
        default=list, 
        blank=True,
        help_text="Mots-clés extraits automatiquement pour le matching"
    )
    vecteur_embedding = models.JSONField(
        null=True, 
        blank=True,
        help_text="Vecteur sémantique pour la recherche avancée",
        default=None
    )
    
    # Préférences de recommandation
    types_opportunites = models.JSONField(
        default=list,
        blank=True,
        help_text="Types d'opportunités souhaités (AMI, APPEL_OFFRE)"
    )
    montant_min = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Montant minimum recherché",
        default=None
    )
    montant_max = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Montant maximum recherché",
        default=None
    )
    
    # Statistiques
    nb_recommandations_envoyees = models.IntegerField(default=0)
    nb_candidatures_emises = models.IntegerField(default=0)
    taux_succes = models.FloatField(default=0.0, help_text="Taux de succès aux candidatures")
    
    # Métadonnées
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    profil_complet = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"
        indexes = [
            models.Index(fields=['domaineActive']),
            models.Index(fields=['localisation']),
            models.Index(fields=['taille']),
        ]
    
    def __str__(self):
        return self.raisonSociale
    
    def extraire_mots_cles(self):
        """Extrait les mots-clés depuis competencesCles"""
        if self.competencesCles:
            return [mot.strip().lower() for mot in self.competencesCles.split(',')]
        return []
    
    def sauvegarder_mots_cles(self):
        """Met à jour l'index des mots-clés"""
        self.mots_cles_index = self.extraire_mots_cles()
        self.save()

# Particulier hérite de Utilisateur
class Particulier(Utilisateur):
    # Champs spécifiques au particulier
    date_naissance = models.DateField(null=True, blank=True, default=None)
    adresse = models.CharField(max_length=255, blank=True, default='')
    ville = models.CharField(max_length=100, blank=True, default='')
    pays = models.CharField(max_length=100, blank=True, default='')
    photo = models.ImageField(upload_to='photos/', null=True, blank=True, default=None)
    
    class Meta:
        verbose_name = "Particulier"
        verbose_name_plural = "Particuliers"
    
    def __str__(self):
        return f"{self.prenom} {self.nom}"

# Candidat lié à Particulier (OneToOne)
class Candidat(models.Model):
    particulier = models.OneToOneField(
        Particulier, 
        on_delete=models.CASCADE, 
        related_name='candidat',
        primary_key=True
    )
    
    niveauEtude = models.CharField(max_length=300, default='')
    anneesExperiences = models.IntegerField(default=0)
    competences = models.CharField(max_length=300, help_text="Compétences séparées par des virgules", default='')
    disponibilite = models.CharField(max_length=100, default='')
    niveauLangues = models.CharField(max_length=100, default='')
    
    # Recherche d'emploi
    secteur_recherche = models.CharField(max_length=100, blank=True, default='')
    type_contrat_recherche = models.CharField(max_length=50, blank=True, 
                                              help_text="CDI, CDD, Stage, etc.", default='')
    localisation_recherche = models.CharField(max_length=100, blank=True, default='')
    salaire_souhaite = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None)
    mobilite = models.BooleanField(default=False, help_text="Prêt à se déplacer")
    
    # CV et documents
    cv = models.FileField(upload_to='cvs/', null=True, blank=True, default=None)
    lettre_motivation = models.FileField(upload_to='lettres/', null=True, blank=True, default=None)
    
    # Statistiques
    nb_candidatures_envoyees = models.IntegerField(default=0)
    nb_entretiens_obtenus = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Candidat"
        verbose_name_plural = "Candidats"
    
    def __str__(self):
        return f"Candidat: {self.particulier.prenom} {self.particulier.nom}"
    
    # Propriétés pour accéder aux champs de Particulier directement
    @property
    def nom(self):
        return self.particulier.nom
    
    @property
    def prenom(self):
        return self.particulier.prenom
    
    @property
    def email(self):
        return self.particulier.email
    
    @property
    def telephone(self):
        return self.particulier.telephone

# Recruteur lié à Particulier (OneToOne)
class Recruteur(models.Model):
    particulier = models.OneToOneField(
        Particulier, 
        on_delete=models.CASCADE, 
        related_name='recruteur',
        primary_key=True
    )
    
    organisation = models.CharField(max_length=100, default='')
    secteur = models.CharField(max_length=100, default='')
    typeStructure = models.CharField(max_length=100, help_text="PME, Grande entreprise, Administration, etc.", default='')
    poste_occupe = models.CharField(max_length=100, default='')
    
    # Préférences de recrutement
    secteurs_recherches = models.JSONField(default=list, blank=True)
    types_contrats_proposes = models.JSONField(default=list, blank=True)
    
    # Statistiques
    nb_offres_publiees = models.IntegerField(default=0)
    nb_candidatures_recues = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Recruteur"
        verbose_name_plural = "Recruteurs"
    
    def __str__(self):
        return f"Recruteur: {self.particulier.prenom} {self.particulier.nom} - {self.organisation}"
    
    @property
    def nom(self):
        return self.particulier.nom
    
    @property
    def prenom(self):
        return self.particulier.prenom
    
    @property
    def email(self):
        return self.particulier.email

# Signaux pour créer automatiquement le bon type de profil
@receiver(post_save, sender=User)
def creer_profil_utilisateur(sender, instance, created, **kwargs):
    """
    Ce signal est utile pour les admins ou les inscriptions via admin
    """    
    if created:
        # Par défaut, on ne fait rien - on laisse les formulaires spécialisés créer les profils
        pass

class ServiceIA(models.Model):
    modeleIA = models.CharField(max_length=100)

    def __str__(self):
        return self.modeleIA
    
class SourceDonnees(models.Model):
    nom = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    url = models.URLField(max_length=200)
    frequence = models.CharField(max_length=100)
    actif = models.BooleanField()

    def __str__(self):
        return self.nom
    
class Opportunite(models.Model):
    class Meta:
        abstract=True

    reference = models.CharField(max_length=100)
    titre = models.CharField(max_length=100)
    description = models.TextField()
    secteur = models.CharField(max_length=100)
    datePublication = models.DateField()
    dateLimite = models.DateField()

    def __str__(self):
        return self.titre

class AppelOffre(Opportunite):
    typeAppel = models.CharField(max_length=100)
    criteresTechniques = models.TextField()
    criteresFinanciers = models.TextField()
    caution = models.DecimalField(max_digits=15, decimal_places=2)

class MarchePublic(Opportunite):
    autoriteContractant = models.CharField(max_length=100)
    typeMarche = models.CharField(max_length=100)
    montantEstime = models.DecimalField(max_digits=15, decimal_places=2)
    procedure = models.TextField()

class AMI(Opportunite):
    objet = models.CharField(max_length=100)
    conditions = models.TextField()
    documentsRequis = models.TextField()

class OffreEmploi(Opportunite):
    typeContrat = models.CharField(max_length=100)
    niveauRequis = models.CharField(max_length=100)
    experienceMinimale = models.IntegerField()
    localisation = models.CharField(max_length=100)
    salaire = models.DecimalField(max_digits=15, decimal_places=2)

class Offre_uemoa(models.Model):
    description = models.TextField()
    date_limite = models.TextField()
    download_url = models.URLField(max_length=500)
    date_scraping = models.DateTimeField(auto_now_add=True)
    traite_par_ia = models.BooleanField(default=False)

    def __str__(self):
        return self.description[:50] + "..."
    
class Ami_uemoa(models.Model):
    description = models.TextField()
    date_limite = models.TextField()
    download_url = models.URLField(max_length=500)
    date_scraping = models.DateTimeField(auto_now_add=True)
    traite_par_ia = models.BooleanField(default=False)

    def __str__(self):
        return self.description[:50] + "..."