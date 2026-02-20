# base_scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from decimal import Decimal
from typing import Optional, List, Dict
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

@dataclass
class OpportuniteData:
    """Structure de données pour une opportunité scrapée"""
    reference: str
    titre: str
    description: str
    secteur: str
    datePublication: datetime
    dateLimite: datetime
    source_nom: str
    source_url: str
    type_opportunite: str  # 'AO', 'MP', 'AMI', 'OFFRE'
    
    # Champs spécifiques
    criteres_techniques: Optional[str] = None
    criteres_financiers: Optional[str] = None
    caution: Optional[Decimal] = None
    autorite_contractant: Optional[str] = None
    type_marche: Optional[str] = None
    montant_estime: Optional[Decimal] = None
    procedure: Optional[str] = None
    objet: Optional[str] = None
    conditions: Optional[str] = None
    documents_requis: Optional[str] = None
    type_contrat: Optional[str] = None
    niveau_requis: Optional[str] = None
    experience_minimale: Optional[int] = None
    localisation: Optional[str] = None
    salaire: Optional[Decimal] = None

class BaseScraper(ABC):
    """Classe de base abstraite pour tous les scrapers"""
    
    def __init__(self, source):
        self.source = source
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    @abstractmethod
    def scrape(self) -> List[OpportuniteData]:
        """Méthode à implémenter par chaque scraper spécifique"""
        pass
    
    def clean_text(self, text: str) -> str:
        """Nettoie le texte"""
        if text:
            return ' '.join(text.strip().split())
        return ''
    
    def extract_date(self, date_text: str) -> Optional[datetime]:
        """Extrait une date à partir de texte"""
        if not date_text:
            return None
        
        # Patterns de dates courants
        patterns = [
            (r'(\d{2})[./-](\d{2})[./-](\d{4})', '%d/%m/%Y'),
            (r'(\d{4})[./-](\d{2})[./-](\d{2})', '%Y-%m-%d'),
            (r'(\d{1,2})\s+(\w+)\s+(\d{4})', '%d %B %Y')
        ]
        
        for pattern, date_format in patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    # Tentative de conversion
                    if '%B' in date_format:
                        # Gestion des mois en français
                        mois_fr = {
                            'janvier': '01', 'février': '02', 'mars': '03',
                            'avril': '04', 'mai': '05', 'juin': '06',
                            'juillet': '07', 'août': '08', 'septembre': '09',
                            'octobre': '10', 'novembre': '11', 'décembre': '12'
                        }
                        jour, mois, annee = match.groups()
                        mois_num = mois_fr.get(mois.lower(), '01')
                        return datetime.strptime(f"{jour}/{mois_num}/{annee}", '%d/%m/%Y')
                    else:
                        return datetime.strptime(match.group(), date_format)
                except Exception as e:
                    logger.debug(f"Erreur conversion date: {e}")
                    continue
        return None
    
    def extract_decimal(self, text: str) -> Optional[Decimal]:
        """Extrait un nombre décimal (prix, montant)"""
        if not text:
            return None
        
        pattern = r'(\d+(?:[.,]\d+)?)'
        match = re.search(pattern, text.replace(' ', ''))
        if match:
            try:
                return Decimal(match.group(1).replace(',', '.'))
            except:
                return None
        return None