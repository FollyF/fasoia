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