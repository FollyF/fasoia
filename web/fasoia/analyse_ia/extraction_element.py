import spacy
import re
from pathlib import Path
import django
import os
import sys

# Configuration Django
sys.path.append('/media/folly/28DC9DDE2CA969AD/DOCS/SEA/UJKZ/COURS/MEMOIRE/fasoia/web/fasoia')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
django.setup()

from analyse_ia.models import AnalyseDocument
from myAppli.models import Offre_uemoa, Ami_uemoa

class ExtracteurElements:
    """
    Extrait les éléments structurés des appels d'offre et AMI
    """
    
    def __init__(self):
        self.nlp = spacy.load("fr_core_news_sm")
        
        # Patterns regex pour les éléments courants
        self.patterns = {
            'reference': [
                r'N[°°]\s*([A-Z0-9\-/]+)',
                r'référence\s*[:\s]+([A-Z0-9\-/]+)',
                r'n[°°]\s*([0-9]+\-[0-9]+)'
            ],
            'date_limite': [
                r'date\s*limite\s*[:\s]+(\d{1,2}\s+\w+\s+\d{4})',
                r'au\s*plus\s*tard\s+le\s+(\d{1,2}\s+\w+\s+\d{4})',
                r'(\d{1,2}/\d{1,2}/\d{4})'
            ],
            'montant': [
                r'(\d+(?:\s?\d+)*)\s*(?:€|euros|EUR|FCFA)',
                r'montant\s*[:\s]+(\d+(?:\s?\d+)*)\s*(?:€|euros|EUR|FCFA)'
            ],
            'email': [
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ],
            'telephone': [
                r'(?:\+226|0)[1-9](?:[\s.-]?\d{2}){4}',
                r'Tél[:\s]+([0-9\s\+\.]+)'
            ],
            'lieu': [
                r'lieu\s*d[ea]\s*exécution\s*[:\s]+([^\n]+)',
                r'à\s+([A-Z][a-zéèêëïî\s]+)(?:\n|\.)'
            ]
        }
    
    def extraire_reference(self, texte):
        """Extrait la référence de l'appel d'offre"""
        for pattern in self.patterns['reference']:
            match = re.search(pattern, texte, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def extraire_date_limite(self, texte):
        """Extrait la date limite"""
        for pattern in self.patterns['date_limite']:
            match = re.search(pattern, texte, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def extraire_montant(self, texte):
        """Extrait le montant estimé"""
        for pattern in self.patterns['montant']:
            match = re.search(pattern, texte, re.IGNORECASE)
            if match:
                montant = match.group(1).replace(' ', '')
                return montant
        return None
    
    def extraire_emails(self, texte):
        """Extrait tous les emails"""
        emails = []
        for pattern in self.patterns['email']:
            matches = re.findall(pattern, texte, re.IGNORECASE)
            emails.extend(matches)
        return list(set(emails))
    
    def extraire_telephones(self, texte):
        """Extrait les numéros de téléphone"""
        tels = []
        for pattern in self.patterns['telephone']:
            matches = re.findall(pattern, texte)
            tels.extend(matches)
        return list(set(tels))
    
    def extraire_autorite(self, doc):
        """Extrait l'autorité contractante (organisation principale)"""
        organisations = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
        if organisations:
            # Prendre la première organisation mentionnée
            return organisations[0]
        return None
    
    def extraire_objet(self, texte):
        """Extrait l'objet de l'appel d'offre"""
        # Chercher après "OBJET :" ou "Objet :"
        match = re.search(r'(?:OBJET|Objet)\s*[:\s]+([^\n.]+)', texte)
        if match:
            return match.group(1).strip()
        
        # Sinon, prendre la première phrase après le titre
        lignes = texte.split('\n')
        for i, ligne in enumerate(lignes):
            if 'manifestation' in ligne.lower() or 'appel' in ligne.lower():
                if i+1 < len(lignes):
                    return lignes[i+1].strip()[:100]
        return None
    
    def extraire_criteres(self, texte):
        """Extrait les critères d'évaluation"""
        criteres = []
        
        # Chercher les sections avec critères
        sections = re.finditer(r'(?:Critères|critères)[^\n]*\n(.*?)(?:\n\n|\Z)', texte, re.DOTALL)
        for section in sections:
            texte_section = section.group(1)
            # Extraire les lignes avec des points
            lignes = texte_section.split('\n')
            for ligne in lignes:
                if '•' in ligne or '-' in ligne or any(str(i) in ligne for i in range(1,6)):
                    criteres.append(ligne.strip())
        
        return criteres[:5]  # 5 premiers critères
    
    def analyser_document(self, analyse_id):
        """
        Analyse un document déjà en base pour en extraire les éléments
        """
        try:
            analyse = AnalyseDocument.objects.get(id=analyse_id)
            
            # Récupérer le texte
            if analyse.texte_extrait:
                texte = analyse.texte_extrait
            else:
                # Chercher l'objet source
                obj = analyse.document_source
                if hasattr(obj, 'description'):
                    texte = obj.description
                else:
                    print("❌ Pas de texte disponible")
                    return
            
            print(f"\n{'='*60}")
            print(f"📄 ANALYSE DÉTAILLÉE - Analyse #{analyse_id}")
            print(f"{'='*60}")
            
            # Analyse avec spaCy
            doc = self.nlp(texte[:50000])
            
            # Extraction
            reference = self.extraire_reference(texte)
            date_limite = self.extraire_date_limite(texte)
            montant = self.extraire_montant(texte)
            emails = self.extraire_emails(texte)
            telephones = self.extraire_telephones(texte)
            autorite = self.extraire_autorite(doc)
            objet = self.extraire_objet(texte)
            criteres = self.extraire_criteres(texte)
            
            # Type de document
            type_doc = analyse.categorie
            
            # Affichage structuré
            print(f"\n📌 TYPE : {type_doc}")
            print(f"\n🔖 RÉFÉRENCE : {reference if reference else 'Non trouvée'}")
            print(f"\n🏛️  AUTORITÉ : {autorite if autorite else 'Non trouvée'}")
            print(f"\n📋 OBJET : {objet if objet else 'Non trouvé'}")
            print(f"\n📅 DATE LIMITE : {date_limite if date_limite else 'Non trouvée'}")
            print(f"\n💰 MONTANT : {montant if montant else 'Non trouvé'}")
            
            if emails:
                print(f"\n📧 EMAILS :")
                for email in emails[:3]:
                    print(f"   • {email}")
            
            if telephones:
                print(f"\n📞 TÉLÉPHONES :")
                for tel in telephones[:3]:
                    print(f"   • {tel}")
            
            if criteres:
                print(f"\n📊 CRITÈRES :")
                for critere in criteres[:3]:
                    print(f"   • {critere}")
            
            # Suggestions d'amélioration
            print(f"\n💡 SUGGESTIONS :")
            if not reference:
                print("   • Ajouter une référence structurée")
            if not date_limite:
                print("   • La date limite n'a pas été détectée")
            if not montant:
                print("   • Le montant estimé n'a pas été détecté")
            
            return {
                'reference': reference,
                'date_limite': date_limite,
                'montant': montant,
                'emails': emails,
                'telephones': telephones,
                'autorite': autorite,
                'objet': objet,
                'criteres': criteres
            }
            
        except AnalyseDocument.DoesNotExist:
            print(f"❌ Analyse #{analyse_id} non trouvée")
            return None

def analyser_tous():
    """Analyse toutes les analyses existantes"""
    extracteur = ExtracteurElements()
    
    analyses = AnalyseDocument.objects.all().order_by('id')
    print(f"\n📊 {len(analyses)} analyses trouvées en base")
    
    for analyse in analyses:
        extracteur.analyser_document(analyse.id)
        print("\n" + "-"*60)

if __name__ == "__main__":
    print("🔍 EXTRACTION DES ÉLÉMENTS STRUCTURÉS")
    print("="*60)
    
    # Analyser une analyse spécifique
    # extracteur.analyser_document(1)  # Pour l'analyse #1
    
    # Ou analyser toutes
    analyser_tous()