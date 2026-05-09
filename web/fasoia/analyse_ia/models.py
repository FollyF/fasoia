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
    
class RecommandationEmploi(models.Model):
    """
    Recommandations d'offres d'emploi pour les candidats
    """
    candidat = models.ForeignKey(
        'myAppli.Candidat',
        on_delete=models.CASCADE,
        related_name='recommandations_emploi'
    )

    offre = models.ForeignKey(
        'myAppli.OffreEmploi',
        on_delete=models.CASCADE,
        related_name='recommandations'
    )

    # Scores détaillés
    score_competences = models.FloatField(default=0.0)    # 40%
    score_experience = models.FloatField(default=0.0)     # 20%
    score_formation = models.FloatField(default=0.0)      # 15%
    score_secteur = models.FloatField(default=0.0)        # 15%
    score_localisation = models.FloatField(default=0.0)   # 10%
    score_global = models.FloatField(default=0.0)

    # Détails du matching
    competences_match = models.JSONField(default=list)      # Compétences communes
    competences_manquantes = models.JSONField(default=list) # Ce qui manque

    # Métadonnées
    date_recommandation = models.DateTimeField(auto_now_add=True)
    vue = models.BooleanField(default=False)
    cliquee = models.BooleanField(default=False)
    postule = models.BooleanField(default=False)

    class Meta:
        unique_together = ['candidat', 'offre']
        ordering = ['-score_global']
        indexes = [
            models.Index(fields=['candidat', 'score_global']),
            models.Index(fields=['date_recommandation']),
        ]

    def __str__(self):
        return f"{self.candidat} → {self.offre.titre} ({self.score_global:.0%})"
    
class ElementsCVExtraits(models.Model):
    """
    Éléments structurés extraits de l'analyse d'un CV
    """
    analyse = models.OneToOneField(
        AnalyseDocument,
        on_delete=models.CASCADE,
        related_name='elements_cv'
    )

    candidat = models.OneToOneField(
        'myAppli.Candidat',
        on_delete=models.CASCADE,
        related_name='elements_cv',
        null=True,
        blank=True
    )

    # Compétences extraites du CV
    competences = models.JSONField(
        default=list,
        help_text="Liste des compétences détectées"
    )

    # Formation
    niveau_etude = models.CharField(
        max_length=100,
        blank=True,
        help_text="Bac, Licence, Master, Doctorat..."
    )

    domaine_etude = models.CharField(
        max_length=100,
        blank=True,
        help_text="Informatique, Finance, Marketing..."
    )

    # Expérience
    annees_experience = models.IntegerField(
        default=0,
        help_text="Nombre d'années d'expérience détecté"
    )

    postes_occupes = models.JSONField(
        default=list,
        help_text="Liste des postes occupés"
    )

    # Langues
    langues = models.JSONField(
        default=list,
        help_text="Langues détectées"
    )

    # Secteurs
    secteurs = models.JSONField(
        default=list,
        help_text="Secteurs d'activité détectés"
    )

    # Contact
    emails = models.JSONField(default=list)
    telephones = models.JSONField(default=list)

    # Localisation
    ville = models.CharField(max_length=100, blank=True)
    pays = models.CharField(max_length=100, blank=True)

    # Métadonnées
    date_extraction = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Éléments CV extraits"
        verbose_name_plural = "Éléments CV extraits"
        indexes = [
            models.Index(fields=['niveau_etude']),
            models.Index(fields=['annees_experience']),
        ]

    def __str__(self):
        return f"Éléments CV - Candidat #{self.candidat_id}"
    
class ElementsOffreExtraits(models.Model):
    """
    Éléments structurés extraits de l'analyse d'une OffreEmploi
    """
    analyse = models.OneToOneField(
        AnalyseDocument,
        on_delete=models.CASCADE,
        related_name='elements_offre'
    )

    offre = models.OneToOneField(
        'myAppli.OffreEmploi',
        on_delete=models.CASCADE,
        related_name='elements_extraits',
        null=True,
        blank=True
    )

    # Compétences extraites
    competences_detectees = models.JSONField(
        default=list,
        help_text="Compétences détectées dans le texte/PDF"
    )

    # Formation
    niveau_etude_detecte = models.CharField(
        max_length=100,
        blank=True,
        help_text="Niveau détecté dans le texte"
    )

    domaine_etude_detecte = models.CharField(
        max_length=100,
        blank=True
    )

    # Expérience
    annees_experience_detectees = models.IntegerField(
        default=0,
        help_text="Années d'expérience détectées dans le texte"
    )

    # Langues
    langues_detectees = models.JSONField(
        default=list
    )

    # Secteurs
    secteurs_detectes = models.JSONField(
        default=list
    )

    # Contact
    emails = models.JSONField(default=list)
    telephones = models.JSONField(default=list)

    # Localisation
    ville_detectee = models.CharField(max_length=100, blank=True)
    pays_detecte = models.CharField(max_length=100, blank=True)

    # Salaire détecté dans le texte
    salaire_detecte = models.CharField(max_length=100, blank=True)

    # Métadonnées
    date_extraction = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Éléments Offre extraits"
        verbose_name_plural = "Éléments Offres extraits"
        indexes = [
            models.Index(fields=['niveau_etude_detecte']),
            models.Index(fields=['annees_experience_detectees']),
        ]

    def __str__(self):
        return f"Éléments Offre #{self.offre_id} - {self.offre.titre if self.offre else ''}"

class SessionEntretien(models.Model):
    """
    Session de préparation à l'entretien
    """
    EN_COURS = 'EN_COURS'
    TERMINEE = 'TERMINEE'
    ABANDONNEE = 'ABANDONNEE'

    STATUT_CHOICES = [
        (EN_COURS, 'En cours'),
        (TERMINEE, 'Terminée'),
        (ABANDONNEE, 'Abandonnée'),
    ]

    candidat = models.ForeignKey(
        'myAppli.Candidat',
        on_delete=models.CASCADE,
        related_name='sessions_entretien'
    )

    offre = models.ForeignKey(
        'myAppli.OffreEmploi',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions_entretien',
        help_text="Null = cas général"
    )

    # Contexte
    poste_vise = models.CharField(
        max_length=200,
        blank=True,
        help_text="Poste visé (rempli auto depuis offre ou saisi manuellement)"
    )
    secteur = models.CharField(max_length=100, blank=True)

    # Statut
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default=EN_COURS
    )

    # Résultats
    score_global = models.FloatField(
        default=0.0,
        help_text="Score moyen sur 10"
    )
    feedback_global = models.TextField(blank=True)

    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    duree_minutes = models.IntegerField(default=0)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Session d'entretien"
        verbose_name_plural = "Sessions d'entretien"

    def __str__(self):
        return f"Session {self.candidat} - {self.poste_vise} ({self.statut})"

    @property
    def nb_questions_repondues(self):
        return self.questions.filter(reponse_candidat__isnull=False).exclude(reponse_candidat='').count()

    @property
    def est_complete(self):
        return self.nb_questions_repondues >= 10

class QuestionEntretien(models.Model):
    """
    Question d'entretien dans une session
    """
    TECHNIQUE = 'TECHNIQUE'
    COMPORTEMENTALE = 'COMPORTEMENTALE'
    SITUATIONNELLE = 'SITUATIONNELLE'
    MOTIVATION = 'MOTIVATION'

    TYPE_CHOICES = [
        (TECHNIQUE, 'Technique'),
        (COMPORTEMENTALE, 'Comportementale'),
        (SITUATIONNELLE, 'Situationnelle'),
        (MOTIVATION, 'Motivation'),
    ]

    session = models.ForeignKey(
        SessionEntretien,
        on_delete=models.CASCADE,
        related_name='questions'
    )

    # Question
    ordre = models.IntegerField(help_text="Position dans la session (1-10)")
    type_question = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=COMPORTEMENTALE
    )
    question = models.TextField()

    # Réponse du candidat
    reponse_candidat = models.TextField(blank=True)
    date_reponse = models.DateTimeField(null=True, blank=True)

    # Évaluation Ollama
    feedback_ia = models.TextField(blank=True)
    score = models.FloatField(
        default=0.0,
        help_text="Score sur 10"
    )
    points_forts = models.JSONField(default=list)
    points_amelioration = models.JSONField(default=list)

    class Meta:
        ordering = ['ordre']
        unique_together = ['session', 'ordre']
        verbose_name = "Question d'entretien"

    def __str__(self):
        return f"Q{self.ordre} - {self.session}"
    
class RecommandationCandidatRecruteur(models.Model):
    """
    Candidats recommandés à un recruteur pour une offre
    """
    EN_ATTENTE = 'EN_ATTENTE'
    INVITE = 'INVITE'
    ACCEPTE = 'ACCEPTE'
    REFUSE = 'REFUSE'

    STATUT_CHOICES = [
        (EN_ATTENTE, 'En attente'),
        (INVITE, 'Invité'),
        (ACCEPTE, 'A postulé'),
        (REFUSE, 'Refusé'),
    ]

    offre = models.ForeignKey(
        'myAppli.OffreEmploi',
        on_delete=models.CASCADE,
        related_name='candidats_recommandes'
    )

    candidat = models.ForeignKey(
        'myAppli.Candidat',
        on_delete=models.CASCADE,
        related_name='recommandations_recruteur'
    )

    # Scores
    score_global = models.FloatField(default=0.0)
    score_competences = models.FloatField(default=0.0)
    score_experience = models.FloatField(default=0.0)
    score_formation = models.FloatField(default=0.0)

    # Analyse IA
    explication = models.TextField(
        blank=True,
        help_text="Explication Ollama de la compatibilité"
    )
    points_forts = models.JSONField(default=list)
    points_faibles = models.JSONField(default=list)

    # Statut
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default=EN_ATTENTE
    )

    # Métadonnées
    date_recommandation = models.DateTimeField(auto_now_add=True)
    date_invitation = models.DateTimeField(null=True, blank=True)
    vue = models.BooleanField(default=False)

    class Meta:
        unique_together = ['offre', 'candidat']
        ordering = ['-score_global']
        verbose_name = "Candidat recommandé"
        verbose_name_plural = "Candidats recommandés"

    def __str__(self):
        return f"{self.candidat} → {self.offre.titre} ({self.score_global:.0%})"