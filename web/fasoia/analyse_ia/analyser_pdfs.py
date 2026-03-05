# analyse_ia/analyser_pdfs.py

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import spacy
import re
import time  # AJOUTER CET IMPORT
from pathlib import Path
import django
import os
import sys

# Configuration Django
sys.path.append('/media/folly/28DC9DDE2CA969AD/DOCS/SEA/UJKZ/COURS/MEMOIRE/fasoia/web/fasoia')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from analyse_ia.models import AnalyseDocument, DocumentSource
from myAppli.models import Offre_uemoa, Ami_uemoa

# Configuration Tesseract
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/5/tessdata/'

class AnalyseurHybride:
    """
    Analyseur PDF intelligent avec :
    - Détection page par page (texte vs scan)
    - OCR uniquement sur les pages scannées
    - Analyse NLP avec spaCy
    - Sauvegarde automatique
    """
    
    def __init__(self):
        print("Chargement du modèle spaCy...")
        self.nlp = spacy.load("fr_core_news_sm")
        print("✅ Modèle spaCy chargé")
    
    def extraire_texte_hybride(self, chemin_pdf):
        """
        Extrait le texte en traitant chaque page selon son type
        """
        try:
            doc = fitz.open(chemin_pdf)
            texte_complet = ""
            stats = {'texte': 0, 'ocr': 0}
            
            print(f"📑 {len(doc)} pages détectées")
            
            for i in range(len(doc)):
                page = doc[i]
                debut_page = time.time()  # AJOUT
                
                # 1. Essayer d'extraire le texte natif
                texte_natif = page.get_text()
                mots_natifs = [w for w in texte_natif.split() if len(w) > 3]
                
                if len(mots_natifs) > 10:  # Page textuelle
                    print(f"   Page {i+1}: 📝 texte ({len(mots_natifs)} mots) - {time.time()-debut_page:.1f}s")
                    texte_complet += f"\n--- Page {i+1} ---\n"
                    texte_complet += texte_natif
                    stats['texte'] += 1
                    
                else:  # Page scannée -> OCR
                    print(f"   Page {i+1}: 🔍 OCR...", end='', flush=True)
                    
                    # Convertir en image
                    pix = page.get_pixmap(dpi=300)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    
                    # OCR
                    texte_ocr = pytesseract.image_to_string(img, lang='fra')
                    duree = time.time() - debut_page  # AJOUT
                    print(f" {len(texte_ocr)} caractères - {duree:.1f}s")
                    
                    texte_complet += f"\n--- Page {i+1} (OCR) ---\n"
                    texte_complet += texte_ocr
                    stats['ocr'] += 1
            
            print(f"✅ Extraction: {stats['texte']} pages texte, {stats['ocr']} pages OCR")
            return texte_complet
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return None
    
    def analyser_texte(self, texte):
        """Analyse le texte avec spaCy"""
        debut = time.time()  # AJOUT
        print(f"   🔄 Analyse NLP en cours...", end='', flush=True)
        
        doc = self.nlp(texte[:100000])
        
        # Mots-clés
        mots = {}
        for token in doc:
            if (not token.is_stop and not token.is_punct and 
                token.pos_ in ['NOUN', 'PROPN', 'VERB'] and len(token.text) > 3):
                mot = token.lemma_.lower()
                mots[mot] = mots.get(mot, 0) + 1
        
        total = sum(mots.values())
        mots_cles = {}
        if total > 0:
            for mot, count in sorted(mots.items(), key=lambda x: x[1], reverse=True)[:30]:
                mots_cles[mot] = round(count / total, 3)
        
        # Entités
        entites = {
            'dates': [], 'lieux': [], 'organisations': [], 'montants': [],
            'emails': [], 'telephones': [], 'reference': ''
        }
        
        for ent in doc.ents:
            if ent.label_ == "DATE" and len(ent.text) > 4:
                entites['dates'].append(ent.text)
            elif ent.label_ in ["LOC", "GPE"]:
                entites['lieux'].append(ent.text)
            elif ent.label_ == "ORG":
                entites['organisations'].append(ent.text)
            elif ent.label_ == "MONEY":
                entites['montants'].append(ent.text)
        
        # Regex pour informations supplémentaires
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', texte)
        entites['emails'] = list(set(emails))
        
        tels = re.findall(r'(?:\+226|0)[1-9](?:[\s.-]?\d{2}){4}', texte)
        entites['telephones'] = list(set(tels))
        
        # Référence
        ref_match = re.search(r'N[°°]\s*([A-Z0-9\-/]+)', texte[:2000], re.IGNORECASE)
        if ref_match:
            entites['reference'] = ref_match.group(1).strip()
        
        # Catégorie
        texte_lower = texte.lower()
        if 'manifestation' in texte_lower or 'ami' in texte_lower:
            categorie = 'AMI'
        elif 'appel' in texte_lower and 'offre' in texte_lower:
            categorie = 'APPEL_OFFRE'
        elif 'addendum' in texte_lower:
            categorie = 'ADDENDUM'
        else:
            categorie = 'AUTRE'
        
        duree = time.time() - debut  # AJOUT
        print(f" ✅ {duree:.1f}s")
        
        return {
            'mots_cles': mots_cles,
            'entites': entites,
            'categorie': categorie,
            'texte_extrait': texte[:1000]
        }
    
    def traiter_document(self, doc_source):
        """Traite un DocumentSource complet"""
        print(f"\n📄 Traitement de: {doc_source.nom_fichier}")
        debut_doc = time.time()  # AJOUT
        
        # 1. Vérifier que le fichier existe
        chemin_complet = f"/media/folly/28DC9DDE2CA969AD/DOCS/SEA/UJKZ/COURS/MEMOIRE/fasoia/web/fasoia/myAppli/pdfs/{doc_source.nom_fichier}"
        
        if not os.path.exists(chemin_complet):
            print(f"   ❌ Fichier non trouvé: {chemin_complet}")
            return None
        
        # 2. Extraction hybride
        texte = self.extraire_texte_hybride(chemin_complet)
        if not texte:
            print("   ❌ Échec extraction")
            return None
        
        # 3. Analyse
        resultats = self.analyser_texte(texte)
        
        # 4. Déterminer l'objet lié
        if doc_source.offre_scrapee:
            obj = doc_source.offre_scrapee
            content_type = ContentType.objects.get_for_model(Offre_uemoa)
            print(f"   🔗 Lié à Offre_uemoa #{obj.id}")
        elif doc_source.ami_scrapee:
            obj = doc_source.ami_scrapee
            content_type = ContentType.objects.get_for_model(Ami_uemoa)
            print(f"   🔗 Lié à Ami_uemoa #{obj.id}")
        else:
            print("   ⚠️ Document non lié")
            return None
        
        # 5. Sauvegarde
        analyse, created = AnalyseDocument.objects.update_or_create(
            content_type=content_type,
            object_id=obj.id,
            defaults={
                'texte_extrait': resultats['texte_extrait'],
                'mots_cles': resultats['mots_cles'],
                'entites': resultats['entites'],
                'categorie': resultats['categorie'],
                'temps_analyse_ms': int((time.time() - debut_doc) * 1000)  # AJOUT
            }
        )
        
        duree_totale = time.time() - debut_doc  # AJOUT
        print(f"   ✅ Analyse {'créée' if created else 'mise à jour'} (ID: {analyse.id})")
        print(f"   📌 Catégorie: {resultats['categorie']}")
        print(f"   🔑 Top mots: {list(resultats['mots_cles'].keys())[:5]}")
        print(f"   ⏱️  Temps total: {duree_totale:.1f}s")  # AJOUT
        
        return analyse

if __name__ == "__main__":
    import time  # AJOUT
    debut_global = time.time()  # AJOUT
    
    print("="*60)
    print("🔍 ANALYSEUR HYBRIDE PDF (TEXTE + OCR)")
    print("="*60)
    
    analyseur = AnalyseurHybride()
    
    # Récupérer tous les documents sans analyse
    from django.contrib.contenttypes.models import ContentType
    
    docs_a_traiter = []
    for doc in DocumentSource.objects.all():
        if doc.offre_scrapee:
            ct = ContentType.objects.get_for_model(Offre_uemoa)
            if not AnalyseDocument.objects.filter(content_type=ct, object_id=doc.offre_scrapee.id).exists():
                docs_a_traiter.append(doc)
        elif doc.ami_scrapee:
            ct = ContentType.objects.get_for_model(Ami_uemoa)
            if not AnalyseDocument.objects.filter(content_type=ct, object_id=doc.ami_scrapee.id).exists():
                docs_a_traiter.append(doc)
    
    print(f"\n📊 {len(docs_a_traiter)} documents à analyser")
    
    for i, doc in enumerate(docs_a_traiter, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(docs_a_traiter)}]")
        analyseur.traiter_document(doc)
    
    duree_globale = time.time() - debut_global  # AJOUT
    print(f"\n{'='*60}")
    print(f"🏁 ANALYSE TERMINÉE en {duree_globale:.1f} secondes")
    print(f"📊 Moyenne: {duree_globale/len(docs_a_traiter):.1f}s par document")
    print("="*60)