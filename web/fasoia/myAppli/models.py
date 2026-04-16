from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import datetime

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
    entete_image = models.ImageField(
        upload_to='entetes/',
        null=True,
        blank=True,
        help_text="Image d'en-tête (contenant logo + infos entreprise)"
    )

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
    dateLimite = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.titre

class Offre_uemoa(models.Model):
    description = models.TextField()
    date_limite = models.DateTimeField(null=True, blank=True)
    download_url = models.URLField(max_length=500)
    fichier_local = models.FileField(
        upload_to='pdfs/',
        null=True,
        blank=True,
        help_text="Fichier PDF stocké en local"
    )
    date_scraping = models.DateTimeField(auto_now_add=True)
    traite_par_ia = models.BooleanField(default=False)

    def __str__(self):
        return self.description[:50] + "..."
    
class Ami_uemoa(models.Model):
    description = models.TextField()
    date_limite = models.DateTimeField(null=True, blank=True)
    download_url = models.URLField(max_length=500)
    fichier_local = models.FileField(
        upload_to='pdfs/',
        null=True,
        blank=True,
        help_text="Fichier PDF stocké en local"
    )
    date_scraping = models.DateTimeField(auto_now_add=True)
    traite_par_ia = models.BooleanField(default=False)

    def __str__(self):
        return self.description[:50] + "..."

class OffreEmploi(models.Model):
    """
    Modèle pour les offres d'emploi avec support multi-sources
    """
    
    # ===== TYPES DE CONTRAT =====
    CDI = 'CDI'
    CDD = 'CDD'
    STAGE = 'STAGE'
    ALTERNANCE = 'ALTERNANCE'
    FREELANCE = 'FREELANCE'
    TEMPORAIRE = 'TEMPORAIRE'
    CONSULTANCE = 'CONSULTANCE'
    VOLONTARIAT = 'VOLONTARIAT'
    
    TYPE_CONTRAT_CHOICES = [
        (CDI, 'CDI'),
        (CDD, 'CDD'),
        (STAGE, 'Stage'),
        (ALTERNANCE, 'Alternance'),
        (FREELANCE, 'Freelance'),
        (TEMPORAIRE, 'Temporaire'),
        (CONSULTANCE, 'Consultance'),
        (VOLONTARIAT, 'Volontariat'),
    ]
    
    # ===== NIVEAUX D'EXPÉRIENCE =====
    DEBUTANT = 'DEBUTANT'
    CONFIRME = 'CONFIRME'
    SENIOR = 'SENIOR'
    EXPERT = 'EXPERT'
    SANS_EXPERIENCE = 'SANS_EXP'
    
    NIVEAU_EXPERIENCE_CHOICES = [
        (SANS_EXPERIENCE, 'Sans expérience'),
        (DEBUTANT, 'Débutant (0-2 ans)'),
        (CONFIRME, 'Confirmé (3-5 ans)'),
        (SENIOR, 'Sénior (6-10 ans)'),
        (EXPERT, 'Expert (10+ ans)'),
    ]
    
    # ===== STATUTS DE L'OFFRE =====
    BROUILLON = 'BROUILLON'
    PUBLIEE = 'PUBLIEE'
    POURVOIE = 'POURVOIE'
    ANNULEE = 'ANNULEE'
    EXPIREE = 'EXPIREE'
    EN_ATTENTE = 'EN_ATTENTE'
    
    STATUT_CHOICES = [
        (BROUILLON, 'Brouillon'),
        (EN_ATTENTE, 'En attente de validation'),
        (PUBLIEE, 'Publiée'),
        (POURVOIE, 'Pourvue'),
        (ANNULEE, 'Annulée'),
        (EXPIREE, 'Expirée'),
    ]
    
    # ===== TÉLÉTRAVAIL =====
    NON = 'NON'
    PARTIEL = 'PARTIEL'
    TOTAL = 'TOTAL'
    
    TELETRAVAIL_CHOICES = [
        (NON, 'Non'),
        (PARTIEL, 'Partiel'),
        (TOTAL, 'Total'),
    ]
    
    # ===== SOURCES DE L'OFFRE =====
    SOURCE_MANUEL = 'MANUEL'
    SOURCE_SCRAPING = 'SCRAPING'
    SOURCE_API = 'API'
    SOURCE_IMPORT = 'IMPORT'
    SOURCE_PARTENAIRE = 'PARTENAIRE'
    
    SOURCE_CHOICES = [
        (SOURCE_MANUEL, 'Création manuelle'),
        (SOURCE_SCRAPING, 'Scraping automatique'),
        (SOURCE_API, 'API externe'),
        (SOURCE_IMPORT, 'Import de fichier'),
        (SOURCE_PARTENAIRE, 'Partenaire'),
    ]
    
    # ===== SECTEURS D'ACTIVITÉ =====
    SECTEUR_AGRICULTURE = 'AGRICULTURE'
    SECTEUR_COMMERCE = 'COMMERCE'
    SECTEUR_CONSTRUCTION = 'CONSTRUCTION'
    SECTEUR_EDUCATION = 'EDUCATION'
    SECTEUR_FINANCE = 'FINANCE'
    SECTEUR_HEALTH = 'HEALTH'
    SECTEUR_IT = 'IT'
    SECTEUR_MARKETING = 'MARKETING'
    SECTEUR_SERVICE = 'SERVICE'
    SECTEUR_TRANSPORT = 'TRANSPORT'
    SECTEUR_AUTRE = 'AUTRE'
    
    SECTEUR_CHOICES = [
        (SECTEUR_AGRICULTURE, 'Agriculture'),
        (SECTEUR_COMMERCE, 'Commerce / Distribution'),
        (SECTEUR_CONSTRUCTION, 'Construction / BTP'),
        (SECTEUR_EDUCATION, 'Éducation / Formation'),
        (SECTEUR_FINANCE, 'Finance / Comptabilité'),
        (SECTEUR_HEALTH, 'Santé / Social'),
        (SECTEUR_IT, 'Informatique / Télécoms'),
        (SECTEUR_MARKETING, 'Marketing / Communication'),
        (SECTEUR_SERVICE, 'Services'),
        (SECTEUR_TRANSPORT, 'Transport / Logistique'),
        (SECTEUR_AUTRE, 'Autre'),
    ]
    
    # ===== RELATIONS =====
    recruteur = models.ForeignKey(
        'myAppli.Recruteur',
        on_delete=models.CASCADE,
        related_name='offres_emploi',
        verbose_name="Recruteur",
        null=True,
        blank=True,
        help_text="Recruteur associé (pour les offres créées manuellement)"
    )
    
    # ===== INFORMATIONS SUR LA SOURCE =====
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default=SOURCE_MANUEL,
        verbose_name="Source de l'offre"
    )
    
    source_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="URL source",
        help_text="URL d'origine si issue de scraping/API"
    )
    
    source_id = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="ID source",
        help_text="Identifiant unique dans le système source"
    )
    
    source_nom = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Nom de la source",
        help_text="Ex: EmploiBurkinA, LinkedIn, etc."
    )
    
    date_scraping = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de scraping"
    )
    
    # ===== INFORMATIONS SUR L'ENTREPRISE (pour les offres scrapées) =====
    entreprise_nom = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nom de l'entreprise",
        help_text="Pour les offres sans recruteur associé"
    )
    
    entreprise_logo = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Logo de l'entreprise"
    )
    
    entreprise_description = models.TextField(
        blank=True,
        verbose_name="Description de l'entreprise"
    )
    
    entreprise_site_web = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Site web de l'entreprise"
    )
    
    entreprise_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Email de contact"
    )
    
    entreprise_telephone = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Téléphone de contact"
    )
    
    # ===== INFORMATIONS PRINCIPALES =====
    titre = models.CharField(max_length=255, verbose_name="Titre du poste")
    reference = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Référence interne"
    )
    
    secteur = models.CharField(
        max_length=20,
        choices=SECTEUR_CHOICES,
        default=SECTEUR_AUTRE,
        verbose_name="Secteur d'activité"
    )
    
    # ===== DESCRIPTION DÉTAILLÉE =====
    description = models.TextField(verbose_name="Description du poste")
    missions = models.TextField(verbose_name="Missions principales", blank=True)
    profil_recherche = models.TextField(verbose_name="Profil recherché", blank=True)
    
    # ===== LOCALISATION =====
    localisation = models.CharField(max_length=255, verbose_name="Lieu de travail")
    pays = models.CharField(max_length=100, default="Burkina Faso", verbose_name="Pays")
    region = models.CharField(max_length=100, blank=True, verbose_name="Région")
    ville = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    
    # ===== MODALITÉS DE TRAVAIL =====
    type_contrat = models.CharField(
        max_length=20,
        choices=TYPE_CONTRAT_CHOICES,
        default=CDI,
        verbose_name="Type de contrat"
    )
    
    teletravail = models.CharField(
        max_length=10,
        choices=TELETRAVAIL_CHOICES,
        default=NON,
        verbose_name="Télétravail possible"
    )
    
    # ===== EXPÉRIENCE REQUISE =====
    niveau_experience = models.CharField(
        max_length=20,
        choices=NIVEAU_EXPERIENCE_CHOICES,
        default=DEBUTANT,
        verbose_name="Niveau d'expérience requis"
    )
    
    annees_experience_min = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        verbose_name="Années d'expérience minimum"
    )
    
    annees_experience_max = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        verbose_name="Années d'expérience maximum"
    )
    
    # ===== FORMATION REQUISE =====
    niveau_etude_requis = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Niveau d'étude requis"
    )
    
    domaine_etude = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Domaine d'étude"
    )
    
    # ===== COMPÉTENCES =====
    competences_requises = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Compétences requises"
    )
    
    competences_souhaitees = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Compétences souhaitées"
    )
    
    # ===== LANGUES =====
    langues_requises = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Langues requises"
    )
    
    # ===== RÉMUNÉRATION =====
    salaire_min = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        verbose_name="Salaire minimum (FCFA)"
    )
    
    salaire_max = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        verbose_name="Salaire maximum (FCFA)"
    )
    
    salaire_affiche = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Salaire (texte libre)"
    )
    
    salaire_devise = models.CharField(
        max_length=10,
        default="FCFA",
        verbose_name="Devise"
    )
    
    # ===== DATES =====
    date_publication = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de publication"
    )
    
    date_limite = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date limite de candidature"
    )
    
    date_debut = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de début souhaitée"
    )
    
    date_mise_a_jour = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière mise à jour"
    )
    
    # ===== STATUT ET VISIBILITÉ =====
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default=BROUILLON,
        verbose_name="Statut"
    )
    
    est_active = models.BooleanField(
        default=True,
        verbose_name="Offre active"
    )
    
    est_urgente = models.BooleanField(
        default=False,
        verbose_name="Offre urgente"
    )
    
    est_confirmee = models.BooleanField(
        default=False,
        verbose_name="Offre confirmée",
        help_text="Pour les offres scrapées, indique si les infos ont été vérifiées"
    )
    
    # ===== MÉTADONNÉES POUR SCRAPING =====
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Données brutes",
        help_text="Données originales du scraping"
    )
    
    hash_contenu = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Hash du contenu",
        help_text="Pour détecter les doublons"
    )
    
    # ===== STATISTIQUES =====
    nb_vues = models.PositiveIntegerField(default=0, verbose_name="Nombre de vues")
    nb_candidatures = models.PositiveIntegerField(default=0, verbose_name="Nombre de candidatures")
    nb_partages = models.PositiveIntegerField(default=0, verbose_name="Nombre de partages")
    nb_clics = models.PositiveIntegerField(default=0, verbose_name="Nombre de clics")
    
    # ===== MÉTADONNÉES =====
    class Meta:
        verbose_name = "Offre d'emploi"
        verbose_name_plural = "Offres d'emploi"
        ordering = ['-date_publication']
        indexes = [
            models.Index(fields=['statut', 'est_active']),
            models.Index(fields=['date_publication']),
            models.Index(fields=['recruteur']),
            models.Index(fields=['source']),
            models.Index(fields=['secteur']),
            models.Index(fields=['type_contrat']),
            models.Index(fields=['ville', 'pays']),
            models.Index(fields=['hash_contenu']),
        ]
        unique_together = ['source', 'source_id']  # Évite les doublons par source
    
    def __str__(self):
        if self.recruteur:
            return f"{self.titre} - {self.recruteur.organisation}"
        elif self.entreprise_nom:
            return f"{self.titre} - {self.entreprise_nom}"
        return f"{self.titre} - Source: {self.get_source_display()}"
    
    def save(self, *args, **kwargs):
        """Génère une référence automatique si nécessaire"""
        if not self.reference:
            prefix = "OFF"
            date_str = timezone.now().strftime("%Y%m")
            count = OffreEmploi.objects.filter(
                date_publication__year=timezone.now().year,
                date_publication__month=timezone.now().month
            ).count() + 1
            self.reference = f"{prefix}-{date_str}-{count:04d}"
        
        # Générer un hash du contenu pour détecter les doublons
        if not self.hash_contenu:
            import hashlib
            content_string = f"{self.titre}{self.description}{self.entreprise_nom}".lower()
            self.hash_contenu = hashlib.sha256(content_string.encode()).hexdigest()
        
        super().save(*args, **kwargs)
    
    def est_expiree(self):
        """Vérifie si l'offre est expirée"""
        if self.date_limite and self.date_limite < timezone.now().date():
            return True
        return False
    
    def incrementer_vues(self):
        """Incrémente le compteur de vues"""
        self.nb_vues += 1
        self.save(update_fields=['nb_vues'])
    
    def incrementer_candidatures(self):
        """Incrémente le compteur de candidatures"""
        self.nb_candidatures += 1
        self.save(update_fields=['nb_candidatures'])
    
    @classmethod
    def depuis_scraping(cls, data, source_nom):
        """
        Crée ou met à jour une offre à partir de données de scraping
        """
        import hashlib
        
        # Créer un hash unique
        content_string = f"{data.get('titre', '')}{data.get('description', '')}{data.get('entreprise', '')}".lower()
        hash_contenu = hashlib.sha256(content_string.encode()).hexdigest()
        
        # Vérifier si l'offre existe déjà
        offre_existante = cls.objects.filter(
            hash_contenu=hash_contenu
        ).first()
        
        if offre_existante:
            return offre_existante
        
        # Créer une nouvelle offre
        offre = cls(
            source=cls.SOURCE_SCRAPING,
            source_nom=source_nom,
            source_url=data.get('url'),
            source_id=data.get('external_id'),
            date_scraping=timezone.now(),
            titre=data.get('titre', 'Offre sans titre'),
            entreprise_nom=data.get('entreprise', ''),
            entreprise_logo=data.get('logo'),
            description=data.get('description', ''),
            missions=data.get('missions', ''),
            profil_recherche=data.get('profil', ''),
            localisation=data.get('localisation', 'Non précisée'),
            pays=data.get('pays', 'Burkina Faso'),
            ville=data.get('ville', ''),
            type_contrat=data.get('type_contrat', cls.CDI),
            niveau_experience=data.get('niveau_experience', cls.DEBUTANT),
            date_limite=data.get('date_limite'),
            salaire_affiche=data.get('salaire', ''),
            competences_requises=data.get('competences', []),
            statut=cls.EN_ATTENTE,
            est_active=True,
            raw_data=data,
            hash_contenu=hash_contenu,
        )
        offre.save()
        return offre


class SourceScraping(models.Model):
    """
    Configuration des sources de scraping
    """
    nom = models.CharField(max_length=100, unique=True)
    url_base = models.URLField(max_length=500)
    type = models.CharField(
        max_length=20,
        choices=[
            ('API', 'API REST'),
            ('HTML', 'Site HTML'),
            ('RSS', 'Flux RSS'),
            ('JSON', 'Fichier JSON'),
        ]
    )
    actif = models.BooleanField(default=True)
    frequence = models.IntegerField(
        default=24,
        help_text="Fréquence de scraping en heures"
    )
    dernier_scraping = models.DateTimeField(null=True, blank=True)
    configuration = models.JSONField(default=dict, help_text="Configuration spécifique")
    
    class Meta:
        verbose_name = "Source de scraping"
        verbose_name_plural = "Sources de scraping"
    
    def __str__(self):
        return self.nom


class LogScraping(models.Model):
    """
    Journal des opérations de scraping
    """
    source = models.ForeignKey(SourceScraping, on_delete=models.CASCADE)
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(
        max_length=20,
        choices=[
            ('SUCCES', 'Succès'),
            ('ECHEC', 'Échec'),
            ('EN_COURS', 'En cours'),
        ]
    )
    offres_trouvees = models.IntegerField(default=0)
    offres_nouvelles = models.IntegerField(default=0)
    offres_mises_a_jour = models.IntegerField(default=0)
    message_erreur = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Log de scraping"
        verbose_name_plural = "Logs de scraping"
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.source.nom} - {self.date_debut.strftime('%d/%m/%Y %H:%M')}"

class Candidature(models.Model):
    """
    Modèle pour les candidatures aux offres d'emploi
    """
    EN_ATTENTE = 'EN_ATTENTE'
    EN_COURS = 'EN_COURS'
    ACCEPTEE = 'ACCEPTEE'
    REFUSEE = 'REFUSEE'
    ANNULEE = 'ANNULEE'
    
    STATUT_CHOICES = [
        (EN_ATTENTE, 'En attente'),
        (EN_COURS, 'En cours de traitement'),
        (ACCEPTEE, 'Acceptée'),
        (REFUSEE, 'Refusée'),
        (ANNULEE, 'Annulée'),
    ]
    
    offre = models.ForeignKey(
        OffreEmploi,
        on_delete=models.CASCADE,
        related_name='candidatures',
        verbose_name="Offre d'emploi"
    )
    
    candidat = models.ForeignKey(
        'myAppli.Candidat',
        on_delete=models.CASCADE,
        related_name='candidatures',
        verbose_name="Candidat"
    )
    
    date_candidature = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de candidature"
    )
    
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default=EN_ATTENTE,
        verbose_name="Statut"
    )
    
    # Documents
    cv_envoye = models.FileField(
        upload_to='candidatures/cv/',
        null=True,
        blank=True,
        verbose_name="CV envoyé"
    )
    
    lettre_motivation_envoyee = models.FileField(
        upload_to='candidatures/lettres/',
        null=True,
        blank=True,
        verbose_name="Lettre de motivation envoyée"
    )
    
    # Notes et suivi
    notes_recruteur = models.TextField(
        blank=True,
        verbose_name="Notes du recruteur"
    )
    
    date_entretien = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'entretien"
    )
    
    feedback = models.TextField(
        blank=True,
        verbose_name="Feedback"
    )
    
    class Meta:
        verbose_name = "Candidature"
        verbose_name_plural = "Candidatures"
        unique_together = ['offre', 'candidat']  # Empêche les doublons
        ordering = ['-date_candidature']
    
    def __str__(self):
        return f"{self.candidat} - {self.offre.titre}"


class ModeleCV(models.Model):
    """
    Modèles de CV disponibles
    """
    nom = models.CharField(max_length=100, help_text="Nom affiché du style")
    categorie = models.CharField(max_length=50, unique=True, help_text="Identifiant unique du style (moderne, classique, etc.)")
    description = models.TextField(blank=True, help_text="Description du style")
    image_apercu = models.ImageField(upload_to='modeles/apercus/', null=True, blank=True)
    
    # Statistiques et classement
    est_populaire = models.BooleanField(default=False)
    ordre_affichage = models.IntegerField(default=0, help_text="Ordre d'apparition dans le sélecteur")
    nb_utilisations = models.IntegerField(default=0, help_text="Nombre de fois que ce style a été utilisé")
    
    # Gestion
    est_actif = models.BooleanField(default=True, help_text="Visible dans le sélecteur")
    est_premium = models.BooleanField(default=False, help_text="Réservé aux utilisateurs premium")
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Modèle de CV"
        verbose_name_plural = "Modèles de CV"
        ordering = ['ordre_affichage', 'nom']
    
    def __str__(self):
        return self.nom
    
    def incrementer_utilisation(self):
        """Incrémente le compteur d'utilisations"""
        self.nb_utilisations += 1
        self.save(update_fields=['nb_utilisations'])


class CVGenere(models.Model):
    """
    CV généré par un utilisateur
    """
    utilisateur = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='cvs_generes'
    )
    
    # Liaison avec le modèle de CV
    modele = models.ForeignKey(
        ModeleCV, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='cvs'
    )
    
    # Informations du CV
    titre = models.CharField(max_length=200)
    donnees_cv = models.JSONField(default=dict, help_text="Toutes les données du CV au format JSON")
    
    # Fichiers générés
    fichier_pdf = models.FileField(upload_to='cvs/pdf/', null=True, blank=True)
    fichier_docx = models.FileField(upload_to='cvs/docx/', null=True, blank=True)
    
    # Métadonnées
    date_generation = models.DateTimeField(auto_now_add=True)
    est_public = models.BooleanField(default=False, help_text="Rendre le CV visible pour les recruteurs")
    
    nb_telechargements = models.IntegerField(default=0)  # Compteur de téléchargements
    nb_utilisations = models.IntegerField(default=0)     # Compteur d'utilisations
    est_favori = models.BooleanField(default=False)      # CV favori
    est_utilise = models.BooleanField(default=False)     # CV utilisé pour candidature
    derniere_utilisation = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "CV généré"
        verbose_name_plural = "CVs générés"
        ordering = ['-date_generation']
    
    def __str__(self):
        if self.utilisateur:
            return f"CV de {self.utilisateur.username} - {self.modele.nom if self.modele else 'Sans style'}"
        return f"CV anonyme - {self.date_generation.strftime('%d/%m/%Y')}"
    

# ==========================================
# 1. RÉFÉRENTIEL DES DOCUMENTS (TEMPLATES)
# ==========================================
class ModeleDocument(models.Model):
    CATEGORIE_CHOICES = [
        ('TECHNIQUE', 'Dossier Technique'),
        ('FINANCIER', 'Dossier Financier'),
        ('ADMINISTRATIF', 'Dossier Administratif'),
        ('CANDIDATURE', 'Dossier de Candidature'),
    ]
    
    nom = models.CharField(max_length=200)
    categorie = models.CharField(max_length=50, choices=CATEGORIE_CHOICES)
    description = models.TextField(blank=True)
    fichier_template = models.FileField(upload_to='templates/documents/')
    
    # Indispensable pour lier le bouton "Générer" au bon formulaire
    code_technique = models.SlugField(max_length=100, unique=True, help_text="Ex: liste-materiel")
    
    # Filtrage flexible : ['Offre_uemoa', 'Ami_uemoa']
    types_opportunites = models.JSONField(default=list)  
    
    date_creation = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nom} ({self.get_categorie_display()})"


# ==========================================
# 2. DONNÉES DE RÉFÉRENCE (REMPLISSAGE PDF)
# ==========================================

class MaterielEntreprise(models.Model):
    """Données pour le tableau page 5 du PDF APEX-B"""
    entreprise = models.ForeignKey('Entreprise', on_delete=models.CASCADE, related_name='parc_materiel')
    designation = models.CharField(max_length=200)
    quantite = models.PositiveIntegerField(default=1)
    etat_fonctionnement = models.CharField(max_length=100, default="Bon état")
    observations = models.CharField(max_length=200, blank=True)

class PersonnelCle(models.Model):
    """Données pour le tableau page 4 du PDF APEX-B"""
    entreprise = models.ForeignKey('Entreprise', on_delete=models.CASCADE, related_name='equipe')
    nom_prenom = models.CharField(max_length=200)
    poste = models.CharField(max_length=200)
    qualification = models.CharField(max_length=200)
    annees_experience = models.PositiveIntegerField()

class ReferenceTechnique(models.Model):
    """Données pour les expériences page 3 du PDF APEX-B"""
    entreprise = models.ForeignKey('Entreprise', on_delete=models.CASCADE, related_name='liste_references')
    projet_nom = models.CharField(max_length=255)
    client = models.CharField(max_length=200)
    annee = models.IntegerField()
    attestation_bonne_fin = models.FileField(upload_to='attestations/', blank=True, null=True)


# ==========================================
# 3. LE DOSSIER DE SOUMISSION (LE MODÈLE)
# ==========================================
class DossierSoumission(models.Model):
    STATUT_CHOICES = [
        ('EN_PREPARATION', 'En préparation'),
        ('COMPLET', 'Complet'),
        ('SOUMIS', 'Soumis'),
    ]
    
    entreprise = models.ForeignKey('Entreprise', on_delete=models.CASCADE, related_name='dossiers')
    
    # Opportunité ciblée (Polymorphique)
    opportunite_type = models.CharField(max_length=50)  # 'Offre_uemoa' ou 'Ami_uemoa'
    opportunite_id = models.PositiveIntegerField()
    
    reference = models.CharField(max_length=100, unique=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_PREPARATION')
    
    date_soumission_prevue = models.DateField()
    date_soumission_effective = models.DateTimeField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['entreprise', 'opportunite_type', 'opportunite_id']
        indexes = [
            models.Index(fields=['entreprise', 'statut']),
        ]
    
    def est_complet(self):
        """Vérifie si tous les documents sont prêts"""
        documents = self.documents_prepares.all()
        if documents.count() < 6:  # 6 types de documents
            return False
        return all(doc.est_prete() for doc in documents)
    
    def get_document_par_type(self, type_document):
        """Récupère ou crée un DocumentGenere pour un type donné"""
        doc, created = DocumentGenere.objects.get_or_create(
            dossier=self,
            type_document=type_document,
            defaults={'statut': 'MISSING'}
        )
        return doc
    
    def __str__(self):
        return f"Dossier {self.reference} - {self.entreprise.raisonSociale}"


# ==========================================
# 4. INSTANCES DE DOCUMENTS GÉNÉRÉS
# ==========================================
    
class DocumentGenere(models.Model):
    TYPE_CHOICES = [
        ('ENVELOPPE', 'Message enveloppe'),
        ('LETTRE', 'Lettre de motivation'),
        ('PRESENTATION', 'Présentation entreprise'),
        ('FICHE', 'Fiche de renseignement'),
        ('MATERIEL', 'Liste matériel'),
        ('PERSONNEL', 'Liste personnel'),
    ]
    
    STATUT_CHOICES = [
        ('MISSING', 'Manquant'),
        ('GENERATED', 'Généré'),
        ('IMPORTED', 'Importé'),
        ('MODIFIED', 'Modifié'),
        ('ARCHIVED', 'Archivé'),
    ]
    
    # Relations
    dossier = models.ForeignKey('DossierSoumission', on_delete=models.CASCADE, related_name='documents_prepares')
    type_document = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    # Statut et versions
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='MISSING')
    version = models.PositiveIntegerField(default=1)
    
    # Contenu (selon le type de document)
    contenu_html = models.TextField(blank=True, null=True, help_text="Pour les documents textuels modifiables")
    fichier_docx = models.FileField(upload_to='documents_generes/docx/', null=True, blank=True)
    fichier_pdf = models.FileField(upload_to='documents_generes/pdf/', null=True, blank=True)
    fichier_source = models.FileField(upload_to='documents/sources/', null=True, blank=True, help_text="Fichier original importé")
    
    # Métadonnées
    date_generation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_archivage = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['dossier', 'type_document']
        ordering = ['type_document']
    
    def __str__(self):
        return f"{self.get_type_document_display()} - {self.get_statut_display()} - {self.dossier.reference}"
    
    def archiver(self):
        """Suppression douce"""
        self.statut = 'ARCHIVED'
        self.date_archivage = timezone.now()
        self.save()
    
    def est_prete(self):
        """Vérifie si le document est prêt pour la soumission"""
        return self.statut in ['GENERATED', 'IMPORTED', 'MODIFIED']