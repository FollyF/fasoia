from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class AnalyseDocument(models.Model):
    """
    Stocke les résultats de l'analyse IA pour n'importe quel type de document
    """
    
    # Pour lier à n'importe quel modèle (Offre_uemoa, AppelOffre, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    document_source = GenericForeignKey('content_type', 'object_id')
    
    # Le texte extrait du PDF (pour référence)
    texte_extrait = models.TextField(blank=True)
    
    # Résultats de l'analyse
    mots_cles = models.JSONField(default=dict, help_text="Mots-clés avec leur poids")
    entites = models.JSONField(default=dict, help_text="Entités nommées extraites")
    categorie = models.CharField(max_length=100, blank=True)
    
    # Métadonnées
    date_analyse = models.DateTimeField(auto_now_add=True)
    temps_analyse_ms = models.IntegerField(default=0)
    
    class Meta:
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
        unique_together = ['content_type', 'object_id']  # Une seule analyse par document
    
    def __str__(self):
        return f"Analyse #{self.object_id} - {self.date_analyse.strftime('%d/%m/%Y')}"
    

class DocumentSource(models.Model):
    """
    Stockage physique des PDFs téléchargés
    Lien stable avec les offres/AMI via le nom de fichier (hash de l'URL)
    """
    # Le fichier PDF
    fichier = models.FileField(upload_to='pdfs/', max_length=500)
    nom_fichier = models.CharField(max_length=255, unique=True)  # Basé sur hash URL
    taille = models.IntegerField(default=0, help_text="Taille en octets")
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    # Liens vers les modèles scrapés (peuvent changer)
    offre_scrapee = models.ForeignKey(
        'myAppli.Offre_uemoa', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='documents_pdf'
    )
    ami_scrapee = models.ForeignKey(
        'myAppli.Ami_uemoa', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='documents_pdf'
    )
    
    # Métadonnées
    url_source = models.URLField(max_length=500, blank=True)
    date_telechargement = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nom_fichier
    
    class Meta:
        indexes = [
            models.Index(fields=['nom_fichier']),  # Pour recherche rapide
            models.Index(fields=['offre_scrapee']),
            models.Index(fields=['ami_scrapee']),
        ]

# analyse_ia/models.py (nouveau modèle)

class ElementsExtraits(models.Model):
    """
    Éléments structurés extraits d'une analyse
    """
    analyse = models.OneToOneField(
        AnalyseDocument, 
        on_delete=models.CASCADE,
        related_name='elements'
    )
    
    # Éléments extraits
    reference = models.CharField(max_length=200, blank=True)
    montant_estime = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    date_limite = models.DateField(null=True, blank=True)
    lieu = models.CharField(max_length=200, blank=True)
    autorite = models.CharField(max_length=300, blank=True)
    emails = models.JSONField(default=list)
    telephones = models.JSONField(default=list)
    
    # Métadonnées d'extraction
    date_extraction = models.DateTimeField(auto_now_add=True)
    version_extraction = models.CharField(max_length=20, default="1.0")
    
    class Meta:
        indexes = [
            models.Index(fields=['date_limite']),
            models.Index(fields=['lieu']),
        ]
    
    def __str__(self):
        return f"Éléments de l'analyse #{self.analyse_id}"
    

# analyse_ia/models.py (ajoutez ce modèle)

class Recommandation(models.Model):
    """
    Stocke les recommandations faites aux entreprises
    """
    entreprise = models.ForeignKey(
        'myAppli.Entreprise',
        on_delete=models.CASCADE,
        related_name='recommandations'
    )
    opportunite_type = models.CharField(max_length=50)  # 'Offre_uemoa' ou 'Ami_uemoa'
    opportunite_id = models.PositiveIntegerField()
    
    # Pour accéder facilement à l'objet
    @property
    def opportunite(self):
        from myAppli.models import Offre_uemoa, Ami_uemoa
        if self.opportunite_type == 'Offre_uemoa':
            return Offre_uemoa.objects.get(id=self.opportunite_id)
        else:
            return Ami_uemoa.objects.get(id=self.opportunite_id)
    
    # Scores
    score_competences = models.FloatField(default=0.0)
    score_geographique = models.FloatField(default=0.0)
    score_financier = models.FloatField(default=0.0)
    score_global = models.FloatField(default=0.0)
    
    # Détails du matching
    competences_match = models.JSONField(default=list)  # Compétences communes
    analyse = models.ForeignKey(
        'AnalyseDocument',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Métadonnées
    date_recommandation = models.DateTimeField(auto_now_add=True)
    vue = models.BooleanField(default=False)
    cliquee = models.BooleanField(default=False)
    candidatee = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['entreprise', 'opportunite_type', 'opportunite_id']
        indexes = [
            models.Index(fields=['entreprise', 'score_global']),
            models.Index(fields=['date_recommandation']),
        ]
        ordering = ['-score_global']
    
    def __str__(self):
        return f"Recommandation {self.entreprise.raisonSociale} - {self.opportunite_type} #{self.opportunite_id} ({self.score_global:.2f})"