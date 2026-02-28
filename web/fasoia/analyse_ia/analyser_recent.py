import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import spacy
import os
import re
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

# Configuration Tesseract
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/5/tessdata/'

class AnalyseurPDFFinal:
    """
    Analyseur PDF intelligent avec :
    - Détection page par page (texte vs scan)
    - OCR uniquement sur les pages scannées
    - Analyse NLP avec spaCy
    - Sauvegarde automatique en base
    """
    
    def __init__(self):
        print("Chargement du modèle spaCy...")
        self.nlp = spacy.load("fr_core_news_sm")
        print("✅ Modèle spaCy chargé")
    
    def extraire_texte_intelligent(self, chemin_pdf):
        """
        Extrait le texte en traitant chaque page selon son type
        """
        print(f"\n📄 Analyse de : {Path(chemin_pdf).name}")
        
        try:
            # Ouvrir le PDF avec PyMuPDF
            doc = fitz.open(chemin_pdf)
            texte_complet = ""
            stats = {'texte': 0, 'ocr': 0}
            
            print(f"📑 {len(doc)} pages détectées")
            
            for i in range(len(doc)):
                page = doc[i]
                
                # 1. Essayer d'extraire le texte natif
                texte_natif = page.get_text()
                
                # 2. Compter les mots significatifs (plus de 3 lettres)
                mots_natifs = [w for w in texte_natif.split() if len(w) > 3]
                
                if len(mots_natifs) > 10:  # Page textuelle
                    print(f"   Page {i+1}: 📝 texte ({len(mots_natifs)} mots)")
                    texte_complet += f"\n--- Page {i+1} ---\n"
                    texte_complet += texte_natif
                    stats['texte'] += 1
                    
                else:
                    # 3. Page scannée -> OCR
                    print(f"   Page {i+1}: 🔍 OCR en cours...", end='', flush=True)
                    
                    # Convertir la page en image haute résolution
                    pix = page.get_pixmap(dpi=300)
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))
                    
                    # OCR
                    texte_ocr = pytesseract.image_to_string(image, lang='fra')
                    
                    print(f" {len(texte_ocr)} caractères extraits")
                    
                    texte_complet += f"\n--- Page {i+1} (OCR) ---\n"
                    texte_complet += texte_ocr
                    stats['ocr'] += 1
            
            print(f"✅ Extraction terminée : {stats['texte']} pages texte, {stats['ocr']} pages OCR")
            return texte_complet
            
        except Exception as e:
            print(f"❌ Erreur d'extraction: {e}")
            return None
    
    def analyser_texte(self, texte):
        """
        Analyse le texte avec spaCy pour extraire les informations
        """
        # Limiter pour la performance
        if len(texte) > 200000:
            texte = texte[:200000]
        
        doc = self.nlp(texte)
        
        # Mots à ignorer (bruit fréquent)
        mots_a_ignorer = [
            'heure', 'asin', 'base', 'adresse', 'étage', 'immeuble', 
            'palace', 'center', 'rue', 'avenue', 'bp', 'cotonou',
            'page', 'tel', 'fax', 'email', 'www', 'tél', 'poste',
            'boite', 'postal', 'code', 'ville', 'pays', 'bp', '01',
            '02', '03', '04', '05', '06', '07', '08', '09', '10'
        ]
        
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
        
        # Normaliser les poids
        total = sum(mots_importants.values())
        mots_cles = {}
        for mot, count in sorted(mots_importants.items(), key=lambda x: x[1], reverse=True)[:30]:
            mots_cles[mot] = round(count / total, 3) if total > 0 else 0
        
        # Extraire les entités
        entites = {
            'dates': [],
            'montants': [],
            'organisations': [],
            'lieux': [],
            'emails': [],
            'telephones': []
        }
        
        for ent in doc.ents:
            if ent.label_ == "DATE" and len(ent.text) > 6:
                entites['dates'].append(ent.text)
            elif ent.label_ == "MONEY":
                entites['montants'].append(ent.text)
            elif ent.label_ == "ORG":
                entites['organisations'].append(ent.text)
            elif ent.label_ in ["LOC", "GPE"]:
                entites['lieux'].append(ent.text)
        
        # Emails et téléphones (regex)
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', texte)
        entites['emails'] = list(set(emails))
        
        telephones = re.findall(r'(?:\+226|0)[1-9](?:[\s.-]?\d{2}){4}', texte)
        entites['telephones'] = list(set(telephones))
        
        # Nettoyer les doublons
        for key in entites:
            entites[key] = list(set(entites[key]))
        
        # Détecter le type de document
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
        """
        Sauvegarde dans la base Django
        """
        nom_fichier_lower = nom_fichier.lower()
        
        # Déterminer le modèle cible
        if 'ami' in nom_fichier_lower or resultats['type_document'] == 'AMI':
            modele = Ami_uemoa
            print(f"📌 Lié au modèle AMI")
        else:
            modele = Offre_uemoa
            print(f"📌 Lié au modèle Offre_uemoa")
        
        # Créer ou récupérer l'objet
        obj, created = modele.objects.get_or_create(
            description=texte[:500],
            defaults={
                'date_limite': 'À déterminer',
                'download_url': '',
                'traite_par_ia': True
            }
        )
        
        if created:
            print(f"   Nouvel enregistrement créé (ID: {obj.id})")
        else:
            print(f"   Enregistrement existant (ID: {obj.id})")
        
        # Sauvegarder l'analyse
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

def analyser_tous_pdfs():
    """
    Analyse tous les PDFs du dossier pdfs/
    """
    dossier_pdf = Path(__file__).parent / "pdfs"
    analyseur = AnalyseurPDFFinal()
    
    # Récupérer tous les PDFs
    pdfs = list(dossier_pdf.glob("*.pdf"))
    
    print("="*60)
    print(f"📊 ANALYSE DE {len(pdfs)} PDFS")
    print("="*60)
    
    for i, pdf in enumerate(pdfs, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(pdfs)}] TRAITEMENT DE : {pdf.name}")
        print('='*60)
        
        # 1. Extraction intelligente
        texte = analyseur.extraire_texte_intelligent(str(pdf))
        
        if texte:
            print(f"✅ Texte extrait: {len(texte)} caractères")
            
            # 2. Analyse NLP
            resultats = analyseur.analyser_texte(texte)
            
            # 3. Affichage des résultats
            print(f"\n📌 Type détecté: {resultats['type_document']}")
            
            print("\n🔑 Top 15 mots-clés:")
            for mot, poids in list(resultats['mots_cles'].items())[:15]:
                print(f"   • {mot}: {poids}")
            
            if resultats['entites']['organisations']:
                print(f"\n🏢 Organisations: {', '.join(resultats['entites']['organisations'][:3])}")
            
            if resultats['entites']['lieux']:
                print(f"📍 Lieux: {', '.join(resultats['entites']['lieux'][:3])}")
            
            if resultats['entites']['dates']:
                print(f"📅 Dates: {', '.join(resultats['entites']['dates'][:3])}")
            
            if resultats['entites']['montants']:
                print(f"💰 Montants: {', '.join(resultats['entites']['montants'][:3])}")
            
            # 4. Sauvegarde
            print("\n💾 Sauvegarde en base...")
            analyseur.sauvegarder_analyse(pdf.name, texte, resultats)
            
        else:
            print("❌ ÉCHEC: impossible d'extraire le texte")

if __name__ == "__main__":
    analyser_tous_pdfs()