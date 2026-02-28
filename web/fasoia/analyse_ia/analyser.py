import pdfplumber
import PyPDF2
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

class AnalyseurPDF:
    """
    Classe pour analyser les PDFs avec plusieurs méthodes d'extraction
    """
    
    def __init__(self):
        print("Chargement du modèle spaCy...")
        self.nlp = spacy.load("fr_core_news_sm")
        print("Modèle chargé avec succès !")
    
    def extraire_texte_pdf(self, chemin_pdf):
        """
        Extrait le texte d'un PDF en essayant plusieurs méthodes
        """
        texte = None
        
        # Méthode 1 : pdfplumber (meilleur pour les PDFs bien formés)
        try:
            with pdfplumber.open(chemin_pdf) as pdf:
                texte_complet = ""
                for page in pdf.pages:
                    texte_page = page.extract_text()
                    if texte_page:
                        texte_complet += texte_page + "\n"
                if texte_complet.strip():
                    texte = texte_complet
                    print("✅ Extrait avec pdfplumber")
        except Exception as e:
            print(f"⚠️ pdfplumber a échoué: {e}")
        
        # Méthode 2 : PyPDF2 (si pdfplumber a échoué)
        if not texte:
            try:
                with open(chemin_pdf, 'rb') as fichier:
                    lecteur = PyPDF2.PdfReader(fichier)
                    texte_complet = ""
                    for page in lecteur.pages:
                        texte_page = page.extract_text()
                        if texte_page:
                            texte_complet += texte_page + "\n"
                    if texte_complet.strip():
                        texte = texte_complet
                        print("✅ Extrait avec PyPDF2")
            except Exception as e:
                print(f"⚠️ PyPDF2 a échoué: {e}")
        
        return texte
    
    def analyser_texte(self, texte):
        """
        Analyse le texte avec spaCy pour extraire les informations
        """
        if len(texte) > 100000:
            texte = texte[:100000]
        
        doc = self.nlp(texte)
        
        # Mots à ignorer
        mots_a_ignorer = ['heure', 'asin', 'base', 'adresse', 'étage', 'immeuble', 
                         'palace', 'center', 'rue', 'avenue', 'bp', 'cotonou',
                         'page', 'tel', 'fax', 'email', 'www', 'tél', 'poste']
        
        # Compter les mots importants
        mots_importants = {}
        for token in doc:
            if (not token.is_stop and 
                not token.is_punct and 
                token.pos_ in ['NOUN', 'PROPN', 'VERB'] and
                len(token.text) > 3 and
                token.lemma_.lower() not in mots_a_ignorer):
                
                mot = token.lemma_.lower()
                mots_importants[mot] = mots_importants.get(mot, 0) + 1
        
        # Normaliser les mots-clés
        total = sum(mots_importants.values())
        mots_cles = {}
        for mot, count in sorted(mots_importants.items(), key=lambda x: x[1], reverse=True)[:20]:
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
            if ent.label_ == "DATE" and len(ent.text) > 4:
                entites['dates'].append(ent.text)
            elif ent.label_ == "MONEY":
                entites['montants'].append(ent.text)
            elif ent.label_ == "ORG":
                entites['organisations'].append(ent.text)
            elif ent.label_ in ["LOC", "GPE"]:
                entites['lieux'].append(ent.text)
        
        # Extraction manuelle des emails et téléphones (spaCy ne les détecte pas toujours)
        import re
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', texte)
        entites['emails'] = list(set(emails))
        
        telephones = re.findall(r'(?:\+226|0)[1-9](?:[\s.-]?\d{2}){4}', texte)
        entites['telephones'] = list(set(telephones))
        
        # Déduire le type de document
        type_document = self._detecter_type_document(mots_cles, texte)
        
        return {
            'mots_cles': mots_cles,
            'entites': entites,
            'type_document': type_document,
            'longueur_texte': len(texte)
        }
    
    def _detecter_type_document(self, mots_cles, texte):
        """
        Détecte si c'est un Appel d'Offre ou un AMI
        """
        texte_lower = texte.lower()
        
        if 'manifestation' in mots_cles or 'intérêt' in mots_cles or 'ami' in texte_lower:
            return 'AMI'
        elif 'offre' in mots_cles or 'appel' in texte_lower or 'soumission' in texte_lower:
            return 'APPEL_OFFRE'
        else:
            return 'INDETERMINE'
    
    def sauvegarder_analyse(self, nom_fichier, texte, resultats):
        """
        Sauvegarde les résultats dans la base Django
        """
        nom_fichier_lower = nom_fichier.lower()
        
        if 'ami' in nom_fichier_lower:
            modele = Ami_uemoa
            print(f"📌 Lié au modèle AMI")
        else:
            modele = Offre_uemoa
            print(f"📌 Lié au modèle Offre_uemoa")
        
        # Créer ou récupérer l'objet source
        obj, created = modele.objects.get_or_create(
            description=texte[:500],
            defaults={
                'date_limite': 'À déterminer',
                'download_url': '',
                'traite_par_ia': True
            }
        )
        
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
        
        print(f"💾 Analyse sauvegardée dans la base (ID: {analyse.id})")
        return analyse

# Pour tester spécifiquement le PDF qui pose problème
if __name__ == "__main__":
    print("🔍 Test de l'analyseur avec le PDF problématique...")
    analyseur = AnalyseurPDF()
    
    dossier_pdf = Path(__file__).parent / "pdfs"
    fichier_probleme = dossier_pdf / "AMI_003_Relance MONITORING_1.pdf"
    
    if fichier_probleme.exists():
        print(f"\n📄 Test sur : AMI_003_Relance MONITORING_1.pdf")
        
        texte = analyseur.extraire_texte_pdf(str(fichier_probleme))
        
        if texte:
            print(f"✅ Texte extrait ({len(texte)} caractères)")
            print("\n📝 Début du texte extrait :")
            print(texte[:500])
            
            resultats = analyseur.analyser_texte(texte)
            print("\n🔑 Mots-clés trouvés :")
            for mot, poids in list(resultats['mots_cles'].items())[:10]:
                print(f"  • {mot}: {poids}")
            
            # Sauvegarde
            analyseur.sauvegarder_analyse("AMI_003_Relance MONITORING_1.pdf", texte, resultats)
        else:
            print("❌ Échec de l'extraction avec les deux méthodes")
    else:
        print("❌ Fichier non trouvé")