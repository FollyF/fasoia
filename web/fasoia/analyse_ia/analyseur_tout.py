import pdfplumber
import PyPDF2
import pytesseract
from pdf2image import convert_from_path
import spacy
import os
from pathlib import Path
import django
import sys

# Configuration Django
sys.path.append('/media/folly/28DC9DDE2CA969AD/DOCS/SEA/UJKZ/COURS/MEMOIRE/fasoia/web/fasoia')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from analyse_ia.models import AnalyseDocument
from myAppli.models import Offre_uemoa, Ami_uemoa

# Configuration Tesseract pour OCR
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/5/tessdata/'

class AnalyseurPDFComplet:
    """
    Analyseur PDF avec 3 méthodes : pdfplumber -> PyPDF2 -> OCR
    """
    
    def __init__(self):
        print("Chargement du modèle spaCy...")
        self.nlp = spacy.load("fr_core_news_sm")
        print("✅ Modèle spaCy chargé")
    
    def extraire_texte(self, chemin_pdf):
        """
        Essaie les 3 méthodes d'extraction dans l'ordre
        """
        print(f"\n📄 Tentatives d'extraction pour : {Path(chemin_pdf).name}")
        
        # MÉTHODE 1 : pdfplumber
        texte = self._extraire_pdfplumber(chemin_pdf)
        if texte:
            print("✅ Méthode 1 : pdfplumber a réussi")
            return texte
        
        # MÉTHODE 2 : PyPDF2
        texte = self._extraire_pypdf2(chemin_pdf)
        if texte:
            print("✅ Méthode 2 : PyPDF2 a réussi")
            return texte
        
        # MÉTHODE 3 : OCR
        print("⚠️ Méthodes 1 et 2 ont échoué, passage à l'OCR...")
        texte = self._extraire_ocr(chemin_pdf)
        if texte:
            print("✅ Méthode 3 : OCR a réussi")
            return texte
        
        print("❌ ÉCHEC : Aucune méthode n'a fonctionné")
        return None
    
    def _extraire_pdfplumber(self, chemin_pdf):
        """Extraction avec pdfplumber"""
        try:
            with pdfplumber.open(chemin_pdf) as pdf:
                texte = ""
                for page in pdf.pages:
                    texte_page = page.extract_text()
                    if texte_page:
                        texte += texte_page + "\n"
                return texte if texte.strip() else None
        except:
            return None
    
    def _extraire_pypdf2(self, chemin_pdf):
        """Extraction avec PyPDF2"""
        try:
            with open(chemin_pdf, 'rb') as f:
                lecteur = PyPDF2.PdfReader(f)
                texte = ""
                for page in lecteur.pages:
                    texte_page = page.extract_text()
                    if texte_page:
                        texte += texte_page + "\n"
                return texte if texte.strip() else None
        except:
            return None
    
    def _extraire_ocr(self, chemin_pdf):
        """Extraction par OCR (pour PDFs scannés)"""
        try:
            # Convertir PDF en images
            images = convert_from_path(chemin_pdf, dpi=300)
            texte = ""
            
            for i, image in enumerate(images):
                print(f"   OCR page {i+1}/{len(images)}...")
                texte_page = pytesseract.image_to_string(image, lang='fra')
                texte += f"\n--- Page {i+1} ---\n"
                texte += texte_page
            
            return texte if texte.strip() else None
        except Exception as e:
            print(f"   Erreur OCR: {e}")
            return None
    
    def analyser_texte(self, texte):
        """Analyse le texte avec spaCy"""
        doc = self.nlp(texte[:100000])  # Limiter
        
        # Mots à ignorer
        mots_a_ignorer = ['heure', 'asin', 'base', 'adresse', 'étage', 'immeuble', 
                         'palace', 'center', 'rue', 'avenue', 'bp', 'cotonou',
                         'page', 'tel', 'fax', 'email', 'www', 'tél', 'poste']
        
        # Mots-clés
        mots_importants = {}
        for token in doc:
            if (not token.is_stop and 
                not token.is_punct and 
                token.pos_ in ['NOUN', 'PROPN', 'VERB'] and
                len(token.text) > 3 and
                token.lemma_.lower() not in mots_a_ignorer):
                
                mot = token.lemma_.lower()
                mots_importants[mot] = mots_importants.get(mot, 0) + 1
        
        total = sum(mots_importants.values())
        mots_cles = {}
        for mot, count in sorted(mots_importants.items(), key=lambda x: x[1], reverse=True)[:20]:
            mots_cles[mot] = round(count / total, 3) if total > 0 else 0
        
        # Entités
        entites = {
            'dates': [], 'montants': [], 'organisations': [], 
            'lieux': [], 'emails': [], 'telephones': []
        }
        
        for ent in doc.ents:
            if ent.label_ == "DATE" and len(ent.text) > 4:
                entites['dates'].append(ent.text)
            elif ent.label_ == "MONEY":
                entites['montants'].append(ent.text)
            elif ent.label_ == "ORG":
                entites['organisations'].append(ent.text)
            elif ent.label_ in ["LOC", "GPE"]:
                entites['lieux'].append(ent.text)
        
        import re
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', texte)
        entites['emails'] = list(set(emails))
        
        telephones = re.findall(r'(?:\+226|0)[1-9](?:[\s.-]?\d{2}){4}', texte)
        entites['telephones'] = list(set(telephones))
        
        # Type de document
        texte_lower = texte.lower()
        if 'manifestation' in texte_lower or 'ami' in texte_lower:
            type_doc = 'AMI'
        elif 'appel' in texte_lower and 'offre' in texte_lower:
            type_doc = 'APPEL_OFFRE'
        else:
            type_doc = 'INDETERMINE'
        
        return {
            'mots_cles': mots_cles,
            'entites': entites,
            'type_document': type_doc,
            'longueur_texte': len(texte)
        }
    
    def sauvegarder_analyse(self, nom_fichier, texte, resultats):
        """Sauvegarde dans la base Django"""
        nom_fichier_lower = nom_fichier.lower()
        
        if 'ami' in nom_fichier_lower or resultats['type_document'] == 'AMI':
            modele = Ami_uemoa
            print("📌 Lié au modèle AMI")
        else:
            modele = Offre_uemoa
            print("📌 Lié au modèle Offre_uemoa")
        
        obj, created = modele.objects.get_or_create(
            description=texte[:500],
            defaults={
                'date_limite': 'À déterminer',
                'download_url': '',
                'traite_par_ia': True
            }
        )
        
        content_type = ContentType.objects.get_for_model(modele)
        analyse, created = AnalyseDocument.objects.update_or_create(
            content_type=content_type,
            object_id=obj.id,
            defaults={
                'texte_extrait': texte[:1000],
                'mots_cles': resultats['mots_cles'],
                'entites': resultats['entites'],
                'categorie': resultats['type_document'],
                'temps_analyse_ms': 0
            }
        )
        
        print(f"💾 Analyse sauvegardée (ID: {analyse.id})")
        return analyse

# Test
if __name__ == "__main__":
    print("="*50)
    print("ANALYSEUR PDF COMPLET (3 MÉTHODES)")
    print("="*50)
    
    analyseur = AnalyseurPDFComplet()
    dossier_pdf = Path(__file__).parent / "pdfs"
    
    # Tester sur les 3 PDFs
    pdfs = list(dossier_pdf.glob("*.pdf"))
    
    for pdf in pdfs:
        print("\n" + "="*60)
        print(f"TRAITEMENT DE : {pdf.name}")
        print("="*60)
        
        # 1. Extraction
        texte = analyseur.extraire_texte(str(pdf))
        
        if texte:
            print(f"✅ Texte extrait : {len(texte)} caractères")
            
            # 2. Analyse
            resultats = analyseur.analyser_texte(texte)
            
            # 3. Affichage
            print(f"\n📌 Type : {resultats['type_document']}")
            print("\n🔑 Top 10 mots-clés :")
            for mot, poids in list(resultats['mots_cles'].items())[:10]:
                print(f"  • {mot}: {poids}")
            
            # 4. Sauvegarde
            analyseur.sauvegarder_analyse(pdf.name, texte, resultats)
        else:
            print("❌ ÉCHEC : impossible d'extraire le texte")