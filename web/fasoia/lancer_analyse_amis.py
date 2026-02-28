# reparer_amis_manquants.py

import django
import os
import sys
import fitz
import spacy

sys.path.append('/media/folly/28DC9DDE2CA969AD/DOCS/SEA/UJKZ/COURS/MEMOIRE/fasoia/web/fasoia')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from myAppli.models import Ami_uemoa
from analyse_ia.models import AnalyseDocument, DocumentSource

# Chemin CORRECT vers les PDFs
DOSSIER_PDFS = "/media/folly/28DC9DDE2CA969AD/DOCS/SEA/UJKZ/COURS/MEMOIRE/fasoia/web/fasoia/myAppli/pdfs/"

class CorrecteurAMI:
    def __init__(self):
        self.nlp = spacy.load("fr_core_news_sm")
        self.ct_ami = ContentType.objects.get_for_model(Ami_uemoa)
    
    def analyser_ami(self, ami_id):
        print(f"\n🔧 Réparation AMI #{ami_id}")
        
        try:
            ami = Ami_uemoa.objects.get(id=ami_id)
            doc_source = DocumentSource.objects.filter(ami_scrapee=ami).first()
            
            if not doc_source:
                print(f"   ❌ Pas de DocumentSource pour AMI #{ami_id}")
                return False
            
            # Construire le chemin CORRECT
            chemin_pdf = os.path.join(DOSSIER_PDFS, doc_source.nom_fichier)
            print(f"   📁 Chemin: {chemin_pdf}")
            
            if not os.path.exists(chemin_pdf):
                print(f"   ❌ Fichier introuvable")
                return False
            
            # Lire le PDF
            doc = fitz.open(chemin_pdf)
            texte = ""
            for page in doc:
                texte += page.get_text()
            
            # Analyser
            doc_nlp = self.nlp(texte[:50000])
            
            # Mots-clés
            mots = {}
            for token in doc_nlp:
                if (not token.is_stop and not token.is_punct and 
                    token.pos_ in ['NOUN', 'PROPN', 'VERB'] and len(token.text) > 3):
                    mot = token.lemma_.lower()
                    mots[mot] = mots.get(mot, 0) + 1
            
            total = sum(mots.values())
            mots_cles = {}
            if total > 0:
                for mot, count in sorted(mots.items(), key=lambda x: x[1], reverse=True)[:30]:
                    mots_cles[mot] = round(count / total, 3)
            
            # Sauvegarder
            analyse, creee = AnalyseDocument.objects.update_or_create(
                content_type=self.ct_ami,
                object_id=ami.id,
                defaults={
                    'texte_extrait': texte[:1000],
                    'mots_cles': mots_cles,
                    'entites': {},
                    'categorie': 'AMI',
                    'temps_analyse_ms': 0
                }
            )
            
            print(f"   ✅ Analyse #{analyse.id} créée")
            print(f"   🔑 Mots: {list(mots_cles.keys())[:5]}")
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            return False

if __name__ == "__main__":
    correcteur = CorrecteurAMI()
    
    for ami_id in [171, 172, 173]:
        correcteur.analyser_ami(ami_id)