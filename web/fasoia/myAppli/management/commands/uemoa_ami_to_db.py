from urllib.parse import urljoin
import os
import requests
import hashlib

from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from myAppli.models import Ami_uemoa
from myAppli.utils.web_scraper.uemoa_scraper import scraper
from analyse_ia.models import DocumentSource
from django.utils import timezone
from datetime import datetime

class Command(BaseCommand):
    help = 'Scrape AMIs, download PDFs and save to DB (avec vrai FileField)'
    
    def convertir_date_uemoa(self, date_str):
        """
        Convertit une date du site UEMOA vers le format Django avec fuseau horaire
        """
        if not date_str or date_str == "N/A":
            return None
        
        try:
            date_str = date_str.strip()
            
            # Format "DD/MM/YYYY - HH:MM"
            if " - " in date_str:
                date_part, time_part = date_str.split(" - ")
                day, month, year = date_part.split("/")
                naive = datetime.strptime(f"{year}-{month}-{day} {time_part}", "%Y-%m-%d %H:%M")
                return timezone.make_aware(naive)
            
            # Format "DD/MM/YYYY HH:MM"
            elif " " in date_str and "/" in date_str:
                parts = date_str.split(" ")
                if len(parts) == 2:
                    date_part, time_part = parts
                    day, month, year = date_part.split("/")
                    naive = datetime.strptime(f"{year}-{month}-{day} {time_part}", "%Y-%m-%d %H:%M")
                    return timezone.make_aware(naive)
            
            # Format "YYYY-MM-DD"
            elif len(date_str) >= 10 and date_str[4] == '-' and date_str[7] == '-':
                if len(date_str) == 10:
                    naive = datetime.strptime(date_str, "%Y-%m-%d")
                else:
                    naive = datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
                return timezone.make_aware(naive)
            
            self.stdout.write(self.style.WARNING(f"   ⚠️ Format non reconnu: '{date_str}'"))
            return None
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Erreur: {e}"))
            return None
    
    def generer_nom_fichier(self, url, prefix="AMI"):
        """Génère un nom de fichier basé sur le hash de l'URL"""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        return f"{prefix}_{url_hash}.pdf"
    
    def telecharger_pdf(self, url, nom_fichier):
        """Télécharge un PDF et retourne le chemin et la taille"""
        try:
            dossier_pdfs = Path(settings.MEDIA_ROOT) / "pdfs"
            dossier_pdfs.mkdir(parents=True, exist_ok=True)
            
            chemin = dossier_pdfs / nom_fichier
            
            if chemin.exists():
                self.stdout.write(f"   📁 PDF déjà existant: {nom_fichier}")
                return str(chemin), chemin.stat().st_size
            
            self.stdout.write(f"   📥 Téléchargement: {nom_fichier}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Accept': 'application/pdf,text/html,application/xhtml+xml',
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
            
            session = requests.Session()
            session.headers.update(headers)
            session.get('https://www.uemoa.int', verify=False, timeout=10)
            
            response = session.get(url, timeout=30, verify=False, stream=True)
            response.raise_for_status()
            
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
            
            download_url = urljoin(base_url, data['download_url'])
            date_convertie = self.convertir_date_uemoa(data['date_limite'])
            
            # 1. Sauvegarder dans Ami_uemoa
            ami, created = Ami_uemoa.objects.update_or_create(
                download_url=download_url,
                defaults={
                    'description': data['description'],
                    'date_limite': date_convertie,
                }
            )
            
            if created:
                self.stdout.write(f"✅ Nouvel AMI #{ami.id} créé")
            else:
                self.stdout.write(f"📝 AMI #{ami.id} mis à jour")
            
            # 2. Générer un nom stable
            nom_fichier = self.generer_nom_fichier(download_url, prefix="AMI")
            self.stdout.write(f"   🏷️  Nom: {nom_fichier}")
            
            # 3. Vérifier si DocumentSource existe déjà
            doc_existant = DocumentSource.objects.filter(nom_fichier=nom_fichier).first()
            
            if doc_existant and doc_existant.fichier:
                # Mise à jour du lien
                doc_existant.ami_scrapee = ami
                doc_existant.url_source = download_url
                doc_existant.save()
                self.stdout.write(f"   🔗 DocumentSource #{doc_existant.id} relié")
                
                # ⬇️ CORRECTION IMPORTANTE ⬇️
                if not ami.fichier_local:
                    chemin = os.path.join(settings.MEDIA_ROOT, doc_existant.fichier.name)
                    if os.path.exists(chemin):
                        with open(chemin, 'rb') as f:
                            ami.fichier_local.save(nom_fichier, File(f))
                        self.stdout.write(f"   📁 fichier_local attaché")
            else:
                # Télécharger le PDF
                chemin_pdf, taille = self.telecharger_pdf(download_url, nom_fichier)
                
                if chemin_pdf:
                    chemin_relatif = os.path.relpath(chemin_pdf, settings.MEDIA_ROOT)
                    
                    # Créer DocumentSource
                    doc = DocumentSource.objects.create(
                        fichier=chemin_relatif,
                        nom_fichier=nom_fichier,
                        taille=taille,
                        ami_scrapee=ami,
                        url_source=download_url
                    )
                    self.stdout.write(f"   ✅ DocumentSource #{doc.id} créé")
                    
                    # ⬇️ CORRECTION IMPORTANTE ⬇️
                    with open(chemin_pdf, 'rb') as f:
                        ami.fichier_local.save(nom_fichier, File(f))
                    self.stdout.write(f"   📁 fichier_local attaché")
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Scraping terminé: {len(all_data)} AMIs traités'
        ))