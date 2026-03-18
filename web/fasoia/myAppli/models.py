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
        upload_to='pdfs',
        null=True,
        blank=True,
        help_text="Fichier PDF stocké en local"
    )
    date_scraping = models.DateTimeField(auto_now_add=True)
    traite_par_ia = models.BooleanField(default=False)

    def __str__(self):
        return self.description[:50] + "..."

class ModeleDocument(models.Model):
    """Modèles de documents pour les soumissions"""
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
    types_opportunites = models.JSONField(default=list)  # ['Offre_uemoa', 'Ami_uemoa']
    date_creation = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nom} ({self.get_categorie_display()})"

class DossierSoumission(models.Model):
    """Dossier de soumission pour une opportunité"""
    STATUT_CHOICES = [
        ('EN_PREPARATION', 'En préparation'),
        ('COMPLET', 'Complet'),
        ('SOUMIS', 'Soumis'),
    ]
    
    # Entreprise qui soumissionne
    entreprise = models.ForeignKey('Entreprise', on_delete=models.CASCADE, related_name='dossiers')
    
    # Opportunité ciblée (polymorphique)
    opportunite_type = models.CharField(max_length=50)  # 'Offre_uemoa' ou 'Ami_uemoa'
    opportunite_id = models.PositiveIntegerField()
    
    # Métadonnées
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
    
    def __str__(self):
        return f"Dossier {self.reference} - {self.entreprise.raisonSociale}"
    
    @property
    def opportunite(self):
        """Récupère l'objet opportunité"""
        if self.opportunite_type == 'Offre_uemoa':
            return Offre_uemoa.objects.get(id=self.opportunite_id)
        else:
            return Ami_uemoa.objects.get(id=self.opportunite_id)

class DocumentSoumission(models.Model):
    """Document généré pour un dossier"""
    STATUT_CHOICES = [
        ('BROUILLON', 'Brouillon'),
        ('VALIDE', 'Validé'),
        ('A_REVOIR', 'À réviser'),
    ]
    
    dossier = models.ForeignKey(DossierSoumission, on_delete=models.CASCADE, related_name='documents')
    modele = models.ForeignKey(ModeleDocument, on_delete=models.SET_NULL, null=True)
    
    nom_document = models.CharField(max_length=255)
    fichier_genere = models.FileField(upload_to='soumissions/documents/', max_length=255)
    taille_fichier = models.IntegerField(default=0)
    donnees_saisies = models.JSONField(default=dict)  # Données personnalisées
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='BROUILLON')
    
    date_generation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nom_document
    

class OffreEmploi(models.Model):
    """
    Modèle pour les offres d'emploi publiées par les recruteurs
    """
    # Types de contrat
    CDI = 'CDI'
    CDD = 'CDD'
    STAGE = 'STAGE'
    ALTERNANCE = 'ALTERNANCE'
    FREELANCE = 'FREELANCE'
    TEMPORAIRE = 'TEMPORAIRE'
    
    TYPE_CONTRAT_CHOICES = [
        (CDI, 'CDI'),
        (CDD, 'CDD'),
        (STAGE, 'Stage'),
        (ALTERNANCE, 'Alternance'),
        (FREELANCE, 'Freelance'),
        (TEMPORAIRE, 'Temporaire'),
    ]
    
    # Niveaux d'expérience
    DEBUTANT = 'DEBUTANT'
    CONFIRME = 'CONFIRME'
    SENIOR = 'SENIOR'
    EXPERT = 'EXPERT'
    
    NIVEAU_EXPERIENCE_CHOICES = [
        (DEBUTANT, 'Débutant (0-2 ans)'),
        (CONFIRME, 'Confirmé (3-5 ans)'),
        (SENIOR, 'Sénior (6-10 ans)'),
        (EXPERT, 'Expert (10+ ans)'),
    ]
    
    # Statuts de l'offre
    BROUILLON = 'BROUILLON'
    PUBLIEE = 'PUBLIEE'
    POURVOIE = 'POURVOIE'
    ANNULEE = 'ANNULEE'
    EXPIREE = 'EXPIREE'
    
    STATUT_CHOICES = [
        (BROUILLON, 'Brouillon'),
        (PUBLIEE, 'Publiée'),
        (POURVOIE, 'Pourvue'),
        (ANNULEE, 'Annulée'),
        (EXPIREE, 'Expirée'),
    ]
    
    # Télétravail
    NON = 'NON'
    PARTIEL = 'PARTIEL'
    TOTAL = 'TOTAL'
    
    TELETRAVAIL_CHOICES = [
        (NON, 'Non'),
        (PARTIEL, 'Partiel'),
        (TOTAL, 'Total'),
    ]
    
    # Relations
    recruteur = models.ForeignKey(
        'myAppli.Recruteur', 
        on_delete=models.CASCADE,
        related_name='offres_emploi',
        verbose_name="Recruteur"
    )
    
    # Informations générales
    titre = models.CharField(max_length=255, verbose_name="Titre du poste")
    reference = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True, 
        null=True,
        verbose_name="Référence interne"
    )
    
    # Description détaillée
    description = models.TextField(verbose_name="Description du poste")
    missions = models.TextField(verbose_name="Missions principales", blank=True)
    profil_recherche = models.TextField(verbose_name="Profil recherché", blank=True)
    
    # Localisation
    localisation = models.CharField(max_length=255, verbose_name="Lieu de travail")
    pays = models.CharField(max_length=100, default="Burkina Faso", verbose_name="Pays")
    ville = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    
    # Modalités de travail
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
    
    # Expérience requise
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
    
    # Formation requise
    niveau_etude_requis = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Niveau d'étude requis"
    )
    
    # Compétences requises (stockées en JSON)
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
    
    # Rémunération
    salaire_min = models.DecimalField(
        max_digits=10, 
        decimal_places=0,
        null=True, 
        blank=True,
        verbose_name="Salaire minimum (FCFA)"
    )
    
    salaire_max = models.DecimalField(
        max_digits=10, 
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
    
    # Dates
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
    
    # Statut et visibilité
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
    
    # Statistiques
    nb_vues = models.PositiveIntegerField(default=0, verbose_name="Nombre de vues")
    nb_candidatures = models.PositiveIntegerField(default=0, verbose_name="Nombre de candidatures")
    
    # Métadonnées
    class Meta:
        verbose_name = "Offre d'emploi"
        verbose_name_plural = "Offres d'emploi"
        ordering = ['-date_publication']
        indexes = [
            models.Index(fields=['statut', 'est_active']),
            models.Index(fields=['date_publication']),
            models.Index(fields=['recruteur']),
        ]
    
    def __str__(self):
        return f"{self.titre} - {self.recruteur.organisation if self.recruteur else 'Inconnu'}"
    
    def save(self, *args, **kwargs):
        """Génère une référence automatique si nécessaire"""
        if not self.reference:
            prefix = "OFF"
            date_str = timezone.now().strftime("%Y%m")
            # Compter les offres du mois pour générer un numéro séquentiel
            count = OffreEmploi.objects.filter(
                date_publication__year=timezone.now().year,
                date_publication__month=timezone.now().month
            ).count() + 1
            self.reference = f"{prefix}-{date_str}-{count:04d}"
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