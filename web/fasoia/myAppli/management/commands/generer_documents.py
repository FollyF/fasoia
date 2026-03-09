# myAppli/management/commands/generer_documents.py
from django.core.management.base import BaseCommand
from myAppli.models import Entreprise, DossierSoumission, ModeleDocument, DocumentSoumission
from analyse_ia.models import Offre_uemoa, Ami_uemoa
from myAppli.services.generateur_document import GenerateurDocument

class Command(BaseCommand):
    help = 'Génère des documents de soumission en lot'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dossier',
            type=int,
            help='ID du dossier spécifique à traiter'
        )
        parser.add_argument(
            '--entreprise',
            type=int,
            help='ID de l\'entreprise (tous ses dossiers en préparation)'
        )
        parser.add_argument(
            '--modele',
            type=int,
            help='ID du modèle de document à utiliser'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la régénération même si le document existe'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Démarrage de la génération de documents...'))
        
        generateur = GenerateurDocument()
        
        # Cas 1: Dossier spécifique
        if options['dossier']:
            self._traiter_dossier(options['dossier'], generateur, options)
        
        # Cas 2: Tous les dossiers d'une entreprise
        elif options['entreprise']:
            self._traiter_entreprise(options['entreprise'], generateur, options)
        
        # Cas 3: Tous les dossiers en préparation
        else:
            self._traiter_tous_dossiers(generateur, options)
    
    def _traiter_dossier(self, dossier_id, generateur, options):
        """Traite un dossier spécifique"""
        try:
            dossier = DossierSoumission.objects.get(id=dossier_id)
            self.stdout.write(f"\n📁 Dossier #{dossier_id}: {dossier.reference}")
            
            # Récupérer les modèles à générer
            if options['modele']:
                modeles = [ModeleDocument.objects.get(id=options['modele'])]
            else:
                modeles = ModeleDocument.objects.filter(
                    types_opportunites__contains=[dossier.opportunite_type],
                    actif=True
                )
            
            # Générer chaque document
            for modele in modeles:
                self._generer_document(dossier, modele, generateur, options)
                
        except DossierSoumission.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Dossier #{dossier_id} non trouvé"))
    
    def _traiter_entreprise(self, entreprise_id, generateur, options):
        """Traite tous les dossiers d'une entreprise"""
        try:
            entreprise = Entreprise.objects.get(id=entreprise_id)
            self.stdout.write(f"\n🏢 Entreprise: {entreprise.raisonSociale}")
            
            dossiers = DossierSoumission.objects.filter(
                entreprise=entreprise,
                statut='EN_PREPARATION'
            )
            
            self.stdout.write(f"📊 {dossiers.count()} dossier(s) en préparation")
            
            for dossier in dossiers:
                self._traiter_dossier(dossier.id, generateur, options)
                
        except Entreprise.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Entreprise #{entreprise_id} non trouvée"))
    
    def _traiter_tous_dossiers(self, generateur, options):
        """Traite tous les dossiers en préparation"""
        dossiers = DossierSoumission.objects.filter(statut='EN_PREPARATION')
        self.stdout.write(f"\n📊 {dossiers.count()} dossier(s) en préparation au total")
        
        for dossier in dossiers:
            self._traiter_dossier(dossier.id, generateur, options)
    
    def _generer_document(self, dossier, modele, generateur, options):
        """Génère un document pour un dossier"""
        
        # Vérifier si le document existe déjà
        doc_existant = dossier.documents.filter(modele=modele).first()
        if doc_existant and not options['force']:
            self.stdout.write(f"  ⏭️  {modele.nom} existe déjà (utilisez --force pour régénérer)")
            return
        
        try:
            # Récupérer l'opportunité
            if dossier.opportunite_type == 'Offre_uemoa':
                opportunite = Offre_uemoa.objects.get(id=dossier.opportunite_id)
            else:
                opportunite = Ami_uemoa.objects.get(id=dossier.opportunite_id)
            
            # Générer le document
            chemin, nom_fichier, taille = generateur.generer(
                modele=modele,
                entreprise=dossier.entreprise,
                opportunite=opportunite,
                opportunite_type=dossier.opportunite_type,
                donnees_supp={'mode_generation': 'batch'}
            )
            
            # Sauvegarder ou mettre à jour
            if doc_existant:
                doc_existant.fichier_genere = chemin
                doc_existant.taille_fichier = taille
                doc_existant.save()
                self.stdout.write(self.style.SUCCESS(f"  ✅ {modele.nom} régénéré"))
            else:
                DocumentSoumission.objects.create(
                    dossier=dossier,
                    modele=modele,
                    nom_document=nom_fichier,
                    fichier_genere=chemin,
                    taille_fichier=taille,
                    donnees_saisies={'mode_generation': 'batch'}
                )
                self.stdout.write(self.style.SUCCESS(f"  ✅ {modele.nom} créé"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ {modele.nom}: {str(e)}"))