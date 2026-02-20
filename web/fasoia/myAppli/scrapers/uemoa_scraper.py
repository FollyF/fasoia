# scrapers/uemoa_scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from django.utils import timezone
from decimal import Decimal
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin

from myAppli.models import SourceDonnees, AppelOffre, AMI, Opportunite
from .base_scraper import BaseScraper, OpportuniteData

logger = logging.getLogger(__name__)

class UEMOAScraper(BaseScraper):
    """
    Scraper spécifique pour le site de l'UEMOA
    URL principale: https://www.uemoa.int/appel-d-offre
    """
    
    def __init__(self, source: SourceDonnees):
        super().__init__(source)
        self.base_url = "https://www.uemoa.int"
        self.appels_offres_url = "https://www.uemoa.int/appel-d-offre"
        self.manifestations_url = "https://www.uemoa.int/manifestation_d_interet"
        
    def scrape(self) -> List[OpportuniteData]:
        """
        Méthode principale de scraping
        """
        logger.info(f"Début du scraping UEMOA - Source: {self.source.nom}")
        toutes_opportunites = []
        
        # Scraper les appels d'offres
        logger.info("Scraping des appels d'offres...")
        appels_offres = self.scrape_appels_offres()
        toutes_opportunites.extend(appels_offres)
        
        # Scraper les manifestations d'intérêt
        logger.info("Scraping des manifestations d'intérêt...")
        manifestations = self.scrape_manifestations()
        toutes_opportunites.extend(manifestations)
        
        # Attendre entre les requêtes (politesse)
        time.sleep(2)
        
        logger.info(f"UEMOA: {len(toutes_opportunites)} opportunités trouvées au total")
        return toutes_opportunites
    
    def scrape_appels_offres(self, max_pages: int = 3) -> List[OpportuniteData]:
        """
        Scrape la page des appels d'offres
        """
        opportunites = []
        
        # Configuration Selenium pour gérer le JavaScript
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            for page in range(0, max_pages):
                url = f"{self.appels_offres_url}?page={page}"
                logger.debug(f"Scraping page {page}: {url}")
                
                driver.get(url)
                
                # Attendre que les éléments soient chargés
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "appel-offre-item"))
                )
                
                # Récupérer tous les éléments d'appel d'offre
                # Note: La classe réelle peut être différente, à adapter selon l'inspection
                items = driver.find_elements(By.CSS_SELECTOR, ".views-row, .appel-offre-item, article")
                
                if not items:
                    # Fallback: chercher par d'autres sélecteurs
                    items = driver.find_elements(By.XPATH, "//div[contains(@class, 'node--type-appel-d-offre')]")
                
                for item in items:
                    try:
                        opp_data = self.extract_appel_offre_from_element(item, driver)
                        if opp_data:
                            opportunites.append(opp_data)
                    except Exception as e:
                        logger.error(f"Erreur sur un élément: {e}")
                        continue
                
                # Vérifier s'il y a une page suivante
                try:
                    next_button = driver.find_element(By.LINK_TEXT, "Suivant")
                    if not next_button.is_enabled():
                        break
                except:
                    break  # Pas de bouton suivant
                
                time.sleep(2)  # Politesse entre les pages
                
        except Exception as e:
            logger.error(f"Erreur lors du scraping UEMOA: {e}")
        finally:
            driver.quit()
        
        return opportunites
    
    def extract_appel_offre_from_element(self, element, driver) -> Optional[OpportuniteData]:
        """
        Extrait les données d'un élément d'appel d'offre
        """
        try:
            # Titre - chercher dans différents sélecteurs possibles
            titre = None
            for selector in ['h2', 'h3', '.title', '.node-title', '.field--name-title']:
                try:
                    titre_elem = element.find_element(By.CSS_SELECTOR, selector)
                    titre = titre_elem.text.strip()
                    if titre:
                        break
                except:
                    continue
            
            if not titre:
                logger.warning("Titre non trouvé pour un élément")
                return None
            
            # Lien de téléchargement ou détail
            lien = None
            for selector in ['a', '.download-link', '.field--name-field-fichier a']:
                try:
                    lien_elem = element.find_element(By.CSS_SELECTOR, selector)
                    lien = lien_elem.get_attribute('href')
                    if lien and not lien.startswith('http'):
                        lien = urljoin(self.base_url, lien)
                    break
                except:
                    continue
            
            # Date de publication
            date_pub = None
            for selector in ['.date-pub', '.field--name-post-date', '.creation-date', 'time']:
                try:
                    date_elem = element.find_element(By.CSS_SELECTOR, selector)
                    date_text = date_elem.text.strip()
                    date_pub = self.extract_date(date_text)
                    if date_pub:
                        break
                except:
                    continue
            
            # Description
            description = ""
            for selector in ['.description', '.field--name-body', '.node-content']:
                try:
                    desc_elem = element.find_element(By.CSS_SELECTOR, selector)
                    description = desc_elem.text.strip()
                    if description:
                        break
                except:
                    continue
            
            # Référence - souvent dans le titre ou un champ spécifique
            reference = self.extract_reference(titre)
            
            # Extraire la date limite (souvent dans la description)
            date_limite = self.extract_date_limite(description)
            
            # Déterminer le secteur d'activité
            secteur = self.extract_secteur(titre, description)
            
            # Créer l'objet opportunité
            opp_data = OpportuniteData(
                reference=reference,
                titre=titre[:200],  # Limiter à 200 caractères
                description=description[:5000],  # Limiter la taille
                secteur=secteur,
                datePublication=date_pub or timezone.now(),
                dateLimite=date_limite or timezone.now() + timezone.timedelta(days=30),
                source_nom=self.source.nom,
                source_url=lien or driver.current_url,
                type_opportunite="AO"  # Appel d'Offre
            )
            
            # Champs spécifiques aux appels d'offres
            opp_data.criteres_techniques = self.extract_criteres_techniques(description)
            opp_data.criteres_financiers = self.extract_criteres_financiers(description)
            
            # Extraire le montant estimé si présent
            montant = self.extract_montant(description)
            if montant:
                opp_data.montant_estime = montant
            
            logger.debug(f"Opportunité extraite: {titre}")
            return opp_data
            
        except Exception as e:
            logger.error(f"Erreur dans extract_appel_offre_from_element: {e}")
            return None
    
    def scrape_manifestations(self, max_pages: int = 3) -> List[OpportuniteData]:
        """
        Scrape la page des manifestations d'intérêt
        """
        opportunites = []
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            for page in range(0, max_pages):
                url = f"{self.manifestations_url}?page={page}"
                
                driver.get(url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "manifestation-item"))
                )
                
                # Sélecteurs à adapter
                items = driver.find_elements(By.CSS_SELECTOR, ".views-row, .manifestation-item")
                
                for item in items:
                    try:
                        opp_data = self.extract_manifestation_from_element(item, driver)
                        if opp_data:
                            opportunites.append(opp_data)
                    except Exception as e:
                        logger.error(f"Erreur sur une manifestation: {e}")
                        continue
                
                time.sleep(2)
                
        except Exception as e:
            logger.error(f"Erreur scraping manifestations: {e}")
        finally:
            driver.quit()
        
        return opportunites
    
    def extract_manifestation_from_element(self, element, driver) -> Optional[OpportuniteData]:
        """
        Extrait les données d'une manifestation d'intérêt
        """
        try:
            # Titre
            titre = element.find_element(By.CSS_SELECTOR, 'h2, h3, .title').text.strip()
            
            # Référence
            reference = self.extract_reference(titre)
            
            # Date
            date_pub = None
            try:
                date_elem = element.find_element(By.CSS_SELECTOR, '.date-pub, time')
                date_pub = self.extract_date(date_elem.text.strip())
            except:
                pass
            
            # Description
            description = ""
            try:
                desc_elem = element.find_element(By.CSS_SELECTOR, '.description')
                description = desc_elem.text.strip()
            except:
                pass
            
            # Lien
            lien = None
            try:
                lien_elem = element.find_element(By.CSS_SELECTOR, 'a')
                lien = lien_elem.get_attribute('href')
                if lien and not lien.startswith('http'):
                    lien = urljoin(self.base_url, lien)
            except:
                pass
            
            # Créer l'objet - type AMI (Appel à Manifestation d'Intérêt)
            opp_data = OpportuniteData(
                reference=reference,
                titre=titre[:200],
                description=description[:5000],
                secteur=self.extract_secteur(titre, description),
                datePublication=date_pub or timezone.now(),
                dateLimite=self.extract_date_limite(description) or timezone.now() + timezone.timedelta(days=30),
                source_nom=self.source.nom,
                source_url=lien or driver.current_url,
                type_opportunite="AMI"
            )
            
            # Champs spécifiques AMI
            opp_data.objet = titre
            opp_data.conditions = self.extract_conditions(description)
            opp_data.documents_requis = self.extract_documents_requis(description)
            
            return opp_data
            
        except Exception as e:
            logger.error(f"Erreur extraction manifestation: {e}")
            return None
    
    def extract_reference(self, text: str) -> str:
        """
        Extrait la référence de l'appel d'offre (ex: N°2025-005)
        """
        patterns = [
            r'N[°°]\s*(\d{4}[-\s]\d{3,4})',
            r'(\d{3,4}/\d{4})',
            r'n[°°]\s*(\d{4})',
            r'(\d{2,4}/\w+/\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Générer une référence par défaut
        return f"UEMOA-{datetime.now().strftime('%Y%m%d')}-{hash(text[:50]) % 10000:04d}"
    
    def extract_date_limite(self, text: str) -> Optional[datetime]:
        """
        Extrait la date limite de soumission
        """
        patterns = [
            r'date\s+limite[:\s]+(\d{1,2}[./]\d{1,2}[./]\d{4})',
            r'avant\s+le\s+(\d{1,2}[./]\d{1,2}[./]\d{4})',
            r'délai[:\s]+(\d{1,2}[./]\d{1,2}[./]\d{4})',
            r'clôture[:\s]+(\d{1,2}[./]\d{1,2}[./]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self.extract_date(match.group(1))
        
        return None
    
    def extract_secteur(self, titre: str, description: str) -> str:
        """
        Détermine le secteur d'activité
        """
        text = (titre + " " + description).lower()
        
        secteurs = {
            'Travaux': ['travaux', 'construction', 'bitumage', 'aménagement', 'voirie', 'bâtiment'],
            'Fournitures': ['fourniture', 'équipement', 'matériel', 'acquisition', 'consommable'],
            'Services': ['prestation', 'service', 'conseil', 'étude', 'assistance', 'nettoyage'],
            'Informatique': ['informatique', 'logiciel', 'matériel informatique', 'datacenter', 'réseau'],
            'Santé': ['médical', 'santé', 'hôpital', 'centre de santé'],
            'Agriculture': ['agricole', 'pisciculture', 'aviculture', 'élevage']
        }
        
        for secteur, mots in secteurs.items():
            if any(mot in text for mot in mots):
                return secteur
        
        return 'Général'
    
    def extract_criteres_techniques(self, text: str) -> str:
        """
        Extrait les critères techniques
        """
        # Chercher une section critères techniques
        pattern = r'(crit[eè]res\s*techniques?[:\s]+)(.*?)(?=crit[eè]res\s*financiers?|$|\.\s*[A-Z])'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(2).strip()
        
        # Fallback: phrases contenant "technique"
        phrases = re.findall(r'[^.]*technique[^.]*\.', text, re.IGNORECASE)
        if phrases:
            return ' '.join(phrases)
        
        return "Non spécifié"
    
    def extract_criteres_financiers(self, text: str) -> str:
        """
        Extrait les critères financiers
        """
        pattern = r'(crit[eè]res\s*financiers?[:\s]+)(.*?)(?=caution|garantie|$|\.\s*[A-Z])'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(2).strip()
        
        return "Non spécifié"
    
    def extract_montant(self, text: str) -> Optional[Decimal]:
        """
        Extrait un montant estimé
        """
        patterns = [
            r'montant\s*(?:estim[ée])?\s*(?:de)?\s*(\d+(?:[.,]\d+)?)\s*(?:millions?)?\s*(?:FCFA|XOF|€|EUR)',
            r'budget\s*(?:pr[eé]vu)?\s*[:\s]+(\d+(?:[.,]\d+)?)\s*(?:millions?)?\s*(?:FCFA|XOF)',
            r'(\d+(?:[.,]\d+)?)\s*(?:millions?)?\s*FCFA'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    valeur = Decimal(match.group(1).replace(',', '.'))
                    # Si c'est en millions, multiplier
                    if 'million' in text.lower():
                        valeur *= 1_000_000
                    return valeur
                except:
                    pass
        
        return None
    
    def extract_conditions(self, text: str) -> str:
        """
        Extrait les conditions pour une AMI
        """
        pattern = r'(conditions?[:\s]+)(.*?)(?=documents?|$|\.\s*[A-Z])'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(2).strip()
        
        return "Voir document original"
    
    def extract_documents_requis(self, text: str) -> str:
        """
        Extrait la liste des documents requis
        """
        pattern = r'(documents?\s*(?:requis?)?[:\s]+)(.*?)(?=date|contact|$|\.\s*[A-Z])'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(2).strip()
        
        return "Voir document original"