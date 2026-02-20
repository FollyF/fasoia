# opportunite_scraper.py
import logging
from django.utils import timezone
from decimal import Decimal
from myAppli.models import AppelOffre, MarchePublic, AMI, OffreEmploi, Opportunite

logger = logging.getLogger(__name__)

class ScrapingOrchestrator:
    """Orchestrateur qui gère tous les scrapers"""
    
    def __init__(self):
        self.scrapers = {}
    
    def save_opportunite(self, opp_data):
        """Sauvegarde une opportunité dans la base Django"""
        try:
            # Vérifier si l'opportunité existe déjà
            if opp_data.type_opportunite == "AO":
                existing = AppelOffre.objects.filter(reference=opp_data.reference).first()
                if not existing:
                    opportunite = AppelOffre.objects.create(
                        reference=opp_data.reference,
                        titre=opp_data.titre,
                        description=opp_data.description,
                        secteur=opp_data.secteur,
                        datePublication=opp_data.datePublication,
                        dateLimite=opp_data.dateLimite,
                        typeAppel="Public",
                        criteresTechniques=opp_data.criteres_techniques or "",
                        criteresFinanciers=opp_data.criteres_financiers or "",
                        caution=opp_data.caution or Decimal('0.00')
                    )
                    logger.info(f"Nouvel appel d'offre créé: {opp_data.titre}")
                    return opportunite
                    
            elif opp_data.type_opportunite == "AMI":
                existing = AMI.objects.filter(reference=opp_data.reference).first()
                if not existing:
                    opportunite = AMI.objects.create(
                        reference=opp_data.reference,
                        titre=opp_data.titre,
                        description=opp_data.description,
                        secteur=opp_data.secteur,
                        datePublication=opp_data.datePublication,
                        dateLimite=opp_data.dateLimite,
                        objet=opp_data.objet or opp_data.titre,
                        conditions=opp_data.conditions or "",
                        documentsRequis=opp_data.documents_requis or ""
                    )
                    logger.info(f"Nouvel AMI créé: {opp_data.titre}")
                    return opportunite
                    
            elif opp_data.type_opportunite == "OFFRE":
                existing = OffreEmploi.objects.filter(reference=opp_data.reference).first()
                if not existing:
                    opportunite = OffreEmploi.objects.create(
                        reference=opp_data.reference,
                        titre=opp_data.titre,
                        description=opp_data.description,
                        secteur=opp_data.secteur,
                        datePublication=opp_data.datePublication,
                        dateLimite=opp_data.dateLimite,
                        typeContrat=opp_data.type_contrat or "Non précisé",
                        niveauRequis=opp_data.niveau_requis or "",
                        experienceMinimale=opp_data.experience_minimale or 0,
                        localisation=opp_data.localisation or "",
                        salaire=opp_data.salaire or Decimal('0.00')
                    )
                    logger.info(f"Nouvelle offre d'emploi créée: {opp_data.titre}")
                    return opportunite
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            return None