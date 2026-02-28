from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

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

class Utilisateur(models.Model):
    class Meta:
        abstract = True
    
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, unique=True)
    telephone = PhoneNumberField()
    typeProfil = models.CharField(max_length=100)  # 'ENTREPRISE', 'RECRUTEUR', 'CANDIDAT'
    DateInscription = models.DateField(auto_now_add=True)
    statut = models.CharField(max_length=100, default='ACTIF')

    def __str__(self):
        return f"{self.prenom} {self.nom}"

class Entreprise(Utilisateur):
    # Champs existants
    raisonSociale = models.CharField(max_length=100)
    domaineActive = models.CharField(max_length=100, help_text="Secteur d'activité principal")
    competencesCles = models.CharField(max_length=300, help_text="Compétences séparées par des virgules")
    localisation = models.CharField(max_length=100, help_text="Ville, Pays")
    taille = models.IntegerField(help_text="Nombre d'employés")
    
    # NOUVEAUX CHAMPS pour les recommandations
    # 1. Informations complémentaires
    description = models.TextField(blank=True, help_text="Présentation de l'entreprise")
    site_web = models.URLField(blank=True)
    annee_creation = models.IntegerField(null=True, blank=True)
    
    # 2. Capacité financière (pour filtrer par montant)
    chiffre_affaires = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Chiffre d'affaires annuel en FCFA"
    )
    capital_social = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Capital social en FCFA"
    )
    
    # 3. Zones d'intervention (pour matching géographique)
    pays_intervention = models.JSONField(
        default=list, 
        blank=True,
        help_text="Liste des pays où l'entreprise peut intervenir"
    )
    rayon_action = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Rayon d'action en km autour du siège"
    )
    
    # 4. Expérience et références
    annees_experience = models.IntegerField(default=0)
    nb_projets_realises = models.IntegerField(default=0)
    references = models.TextField(blank=True, help_text="Principales références")
    
    # 5. Certifications et agréments
    certifications = models.JSONField(default=list, blank=True)
    agrements = models.JSONField(default=list, blank=True)
    
    # 6. Pour le matching intelligent
    mots_cles_index = models.JSONField(
        default=list, 
        blank=True,
        help_text="Mots-clés extraits automatiquement pour le matching"
    )
    vecteur_embedding = models.JSONField(
        null=True, 
        blank=True,
        help_text="Vecteur sémantique pour la recherche avancée"
    )
    
    # 7. Préférences de recommandation
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
        help_text="Montant minimum recherché"
    )
    montant_max = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Montant maximum recherché"
    )
    
    # 8. Statistiques
    nb_recommandations_envoyees = models.IntegerField(default=0)
    nb_candidatures_emises = models.IntegerField(default=0)
    taux_succes = models.FloatField(default=0.0, help_text="Taux de succès aux candidatures")
    
    # 9. Métadonnées
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

class Recruteur(Utilisateur):
    organisation = models.CharField(max_length=100)
    secteur = models.CharField(max_length=100)
    typeStructure = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.organisation}"

class Candidat(Utilisateur):
    niveauEtude = models.CharField(max_length=300)
    anneesExperiences = models.IntegerField()
    competences = models.CharField(max_length=300)
    disponibilite = models.CharField(max_length=100)
    niveauLangues = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.prenom} {self.nom}"
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
    localisation = models.CharField()
    salaire = models.DecimalField(max_digits=15, decimal_places=2)

class Offre_uemoa(models.Model):
    description =models.TextField()
    date_limite =models.TextField()
    download_url =models.URLField(max_length=500)
    date_scraping = models.DateTimeField(auto_now_add=True)
    traite_par_ia = models.BooleanField(default=False)

    def __str__(self):
        return self.description
    
    
class Ami_uemoa(models.Model):
    description =models.TextField()
    date_limite =models.TextField()
    download_url =models.URLField(max_length=500)
    date_scraping = models.DateTimeField(auto_now_add=True)
    traite_par_ia = models.BooleanField(default=False)

    def __str__(self):
        return self.description
    
    
    