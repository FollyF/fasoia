from urllib.parse import urljoin
import os
import requests
import hashlib
from pathlib import Path
from datetime import date

from django.core.management.base import BaseCommand
from myAppli.models import Ami_uemoa
from myAppli.utils.web_scraper.uemoa_scraper import scraper
from analyse_ia.models import DocumentSource

class Command(BaseCommand):
    help = 'Scrape AMIs, download PDFs and save to DB (avec lien stable par hash URL)'
    
    def convertir_date_uemoa(self, date_str):
        """
        Convertit une date du site UEMOA vers le format Django
        Gère différents formats possibles
        """
        if not date_str or date_str == "N/A":
            return None
        
        try:
            # Nettoie la chaîne
            date_str = date_str.strip()
            
            # Format "DD/MM/YYYY - HH:MM" (le plus courant)
            if " - " in date_str:
                date_part, time_part = date_str.split(" - ")
                day, month, year = date_part.split("/")
                return f"{year}-{month}-{day} {time_part}"
            
            # Format "DD/MM/YYYY HH:MM"
            elif " " in date_str and "/" in date_str:
                parts = date_str.split(" ")
                if len(parts) == 2:
                    date_part, time_part = parts
                    day, month, year = date_part.split("/")
                    return f"{year}-{month}-{day} {time_part}"
            
            # Format "YYYY-MM-DD" (déjà bon)
            elif date_str[4] == '-' and date_str[7] == '-':
                return date_str
            
            # Si rien ne correspond, retourne None
            self.stdout.write(self.style.WARNING(
                f"   ⚠️ Format de date non reconnu: '{date_str}'"
            ))
            return None
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"   ❌ Erreur de conversion de date '{date_str}': {e}"
            ))
            return None
    
    def generer_nom_fichier(self, url, prefix="AMI"):
        """
        Génère un nom de fichier basé sur le hash de l'URL
        Ce nom est STABLE même si on relance le scraping
        """
        # Créer un hash de l'URL
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        
        # Format: PREFIX_HASH.pdf
        nom_fichier = f"{prefix}_{url_hash}.pdf"
        
        return nom_fichier
    
    def telecharger_pdf(self, url, nom_fichier):
        """
        Télécharge un PDF avec des headers de navigateur
        """
        try:
            dossier_pdfs = Path(__file__).parent.parent.parent / "pdfs"
            dossier_pdfs.mkdir(exist_ok=True)
            
            chemin = dossier_pdfs / nom_fichier
            
            if chemin.exists():
                self.stdout.write(f"   📁 PDF déjà existant: {nom_fichier}")
                return str(chemin), chemin.stat().st_size
            
            self.stdout.write(f"   📥 Téléchargement: {nom_fichier}")
            
            # Headers plus réalistes
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/pdf,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
            
            # Utiliser une session pour garder les cookies
            session = requests.Session()
            session.headers.update(headers)
            
            # D'abord visiter la page principale pour avoir les cookies
            session.get('https://www.uemoa.int', verify=False, timeout=10)
            
            # Ensuite télécharger le PDF
            response = session.get(url, timeout=30, verify=False, stream=True)
            response.raise_for_status()
            
            # Sauvegarder
            with open(chemin, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            taille = chemin.stat().st_size
            self.stdout.write(self.style.SUCCESS(f"   ✅ Téléchargé: {taille} octets"))
            
            return str(chemin), taille
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Erreur: {e}"))
            return None, 0
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Début du scraping des AMI...'))
        
        base_url = 'https://www.uemoa.int/manifestation_d_interet'
        all_data = scraper(base_url)
        
        self.stdout.write(f"📊 {len(all_data)} AMIs trouvés")
        
        for i, data in enumerate(all_data, 1):
            self.stdout.write(f"\n--- AMI {i}/{len(all_data)} ---")
            
            # Construction de l'URL complète
            download_url = urljoin(base_url, data['download_url'])
            
                      # CONVERSION DE LA DATE - AJOUTEZ CES LIGNES
            date_originale = data['date_limite']
            date_convertie = self.convertir_date_uemoa(date_originale)
            
            self.stdout.write(f"   📅 Date originale: {date_originale}")
            if date_convertie:
                self.stdout.write(f"   📅 Date convertie: {date_convertie}")
            
            # Utilisez date_convertie au lieu de data['date_limite']

            # 1. Sauvegarder dans Ami_uemoa (update_or_create normal)
            ami, created = Ami_uemoa.objects.update_or_create(
                description=data['description'],
                date_limite= date_convertie,
                download_url=download_url
            )
            
            if created:
                self.stdout.write(f"✅ Nouvel AMI #{ami.id} créé")
            else:
                self.stdout.write(f"📝 AMI #{ami.id} mis à jour (ID inchangé)")
            
            # 2. Générer un nom STABLE basé sur l'URL
            nom_fichier = self.generer_nom_fichier(download_url, prefix="AMI")
            self.stdout.write(f"   🏷️  Nom stable: {nom_fichier}")
            
            # 3. Chercher si un DocumentSource existe déjà avec ce nom
            doc_existant = DocumentSource.objects.filter(
                nom_fichier=nom_fichier
            ).first()
            
            if doc_existant:
                # Mise à jour du lien vers le nouvel ami
                doc_existant.ami_scrapee = ami
                doc_existant.url_source = download_url
                doc_existant.save()
                self.stdout.write(f"   🔗 DocumentSource #{doc_existant.id} relié à l'AMI #{ami.id}")
            else:
                # Télécharger le PDF
                chemin_pdf, taille = self.telecharger_pdf(download_url, nom_fichier)
                
                if chemin_pdf:
                    # Créer un nouveau DocumentSource
                    doc = DocumentSource.objects.create(
                        fichier=chemin_pdf,
                        nom_fichier=nom_fichier,
                        taille=taille,
                        ami_scrapee=ami,
                        url_source=download_url
                    )
                    self.stdout.write(f"   ✅ Nouveau DocumentSource #{doc.id} créé")
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Scraping terminé: {len(all_data)} AMIs traités'
        ))