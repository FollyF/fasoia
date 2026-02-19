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
        abstract=True
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)
    telephone = PhoneNumberField()
    typeProfil = models.CharField(max_length=100)
    DateInscription = models.DateField(auto_now_add=True, auto_now=False)
    statut = models.CharField(max_length=100)

    def __str__(self):
        return self.nom

class Recruteur(Utilisateur):
    organisation = models.CharField(max_length=100)
    secteur = models.CharField(max_length=100)
    typeStructure = models.CharField(max_length=100)
    
class Entreprise(Utilisateur):
    raisonSociale = models.CharField(max_length=100)
    domaineActive = models.CharField(max_length=100)
    competencesCles = models.CharField(max_length=300)
    localisation = models.CharField(max_length=100)
    taille = models.IntegerField()
    attribut = models.IntegerField()

class Candidat(Utilisateur):
    niveauEtude = models.CharField(max_length=300)
    anneesExperiences = models.IntegerField()
    competences = models.CharField(max_length=300)
    disponibilite = models.CharField(max_length=100)
    niveauLangues = models.CharField(max_length=100)

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