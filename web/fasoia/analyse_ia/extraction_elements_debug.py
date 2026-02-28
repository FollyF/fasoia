# extraction_elements_corrige.py

import spacy
import re
from pathlib import Path
import django
import os
import sys
import time

# Configuration Django
sys.path.append('/media/folly/28DC9DDE2CA969AD/DOCS/SEA/UJKZ/COURS/MEMOIRE/fasoia/web/fasoia')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
django.setup()

from analyse_ia.models import AnalyseDocument
from myAppli.models import Offre_uemoa, Ami_uemoa

class ExtracteurElements:
    def __init__(self):
        print("Chargement de spaCy...")
        self.nlp = spacy.load("fr_core_news_sm")
        print("✅ spaCy chargé")
        
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
                # Version simplifiée et sécurisée
                r'montant\s*[:\s]+(\d+(?:\s?\d+)*)\s*(?:€|euros|EUR|FCFA)',
                r'(\d+(?:\s?\d+)*)\s*(?:€|euros|EUR|FCFA)'
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
        print("   🔍 Recherche référence...")
        try:
            for pattern in self.patterns['reference']:
                match = re.search(pattern, texte[:2000], re.IGNORECASE)  # Limiter la recherche
                if match:
                    return match.group(1).strip()
        except Exception as e:
            print(f"   ⚠️ Erreur référence: {e}")
        return None
    
    def extraire_date_limite(self, texte):
        print("   🔍 Recherche date limite...")
        try:
            for pattern in self.patterns['date_limite']:
                match = re.search(pattern, texte[:2000], re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        except Exception as e:
            print(f"   ⚠️ Erreur date: {e}")
        return None
    
    def extraire_montant(self, texte):
        print("   🔍 Recherche montant...")
        try:
            # Chercher seulement dans les 2000 premiers caractères
            for pattern in self.patterns['montant']:
                match = re.search(pattern, texte[:2000], re.IGNORECASE)
                if match:
                    montant = match.group(1).replace(' ', '').replace('\u202f', '')
                    print(f"   ✅ Montant trouvé: {montant}")
                    return montant
        except Exception as e:
            print(f"   ⚠️ Erreur montant: {e}")
        return None
    
    def extraire_emails(self, texte):
        print("   🔍 Recherche emails...")
        try:
            emails = []
            for pattern in self.patterns['email']:
                matches = re.findall(pattern, texte, re.IGNORECASE)
                emails.extend(matches)
            return list(set(emails))[:5]  # Limiter à 5
        except Exception as e:
            print(f"   ⚠️ Erreur emails: {e}")
            return []
    
    def extraire_telephones(self, texte):
        print("   🔍 Recherche téléphones...")
        try:
            tels = []
            for pattern in self.patterns['telephone']:
                matches = re.findall(pattern, texte)
                tels.extend(matches)
            return list(set(tels))[:5]
        except Exception as e:
            print(f"   ⚠️ Erreur téléphones: {e}")
            return []
    
    def extraire_autorite(self, doc):
        print("   🔍 Recherche autorité...")
        try:
            organisations = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
            if organisations:
                return organisations[0]
        except Exception as e:
            print(f"   ⚠️ Erreur autorité: {e}")
        return None
    
    def extraire_objet(self, texte):
        print("   🔍 Recherche objet...")
        try:
            match = re.search(r'(?:OBJET|Objet)\s*[:\s]+([^\n.]+)', texte[:2000])
            if match:
                return match.group(1).strip()
            
            lignes = texte.split('\n')[:20]  # Limiter aux 20 premières lignes
            for i, ligne in enumerate(lignes):
                if 'manifestation' in ligne.lower() or 'appel' in ligne.lower():
                    if i+1 < len(lignes):
                        return lignes[i+1].strip()[:100]
        except Exception as e:
            print(f"   ⚠️ Erreur objet: {e}")
        return None
    
    def extraire_criteres(self, texte):
        print("   🔍 Recherche critères...")
        try:
            criteres = []
            sections = re.finditer(r'(?:Critères|critères)[^\n]*\n(.*?)(?:\n\n|\Z)', texte[:5000], re.DOTALL)
            for section in sections:
                texte_section = section.group(1)
                lignes = texte_section.split('\n')
                for ligne in lignes[:10]:  # Limiter par page
                    if '•' in ligne or '-' in ligne or any(str(i) in ligne for i in range(1,6)):
                        criteres.append(ligne.strip()[:100])
                break  # Prendre seulement la première section
            return criteres[:3]
        except Exception as e:
            print(f"   ⚠️ Erreur critères: {e}")
            return []
    
    def analyser_document(self, analyse_id):
        print(f"\n{'='*60}")
        print(f"📄 ANALYSE DÉTAILLÉE - Analyse #{analyse_id}")
        print(f"{'='*60}")
        
        try:
            print("📂 Récupération de l'analyse...")
            analyse = AnalyseDocument.objects.get(id=analyse_id)
            print(f"   ✅ Analyse trouvée")
            
            if analyse.texte_extrait:
                texte = analyse.texte_extrait
                print(f"   📝 Texte extrait: {len(texte)} caractères")
            else:
                print("   ⚠️ Pas de texte extrait")
                return
            
            # Limiter le texte pour spaCy
            texte_limit = texte[:20000]  # 20k caractères max pour spaCy
            print(f"\n⏳ Analyse spaCy sur {len(texte_limit)} caractères...")
            debut = time.time()
            doc = self.nlp(texte_limit)
            fin = time.time()
            print(f"   ✅ spaCy terminé en {fin-debut:.2f} secondes")
            
            # Extraire chaque élément avec timeout implicite
            reference = self.extraire_reference(texte)
            date_limite = self.extraire_date_limite(texte)
            montant = self.extraire_montant(texte)
            emails = self.extraire_emails(texte)
            telephones = self.extraire_telephones(texte)
            autorite = self.extraire_autorite(doc)
            objet = self.extraire_objet(texte)
            criteres = self.extraire_criteres(texte)
            
            type_doc = analyse.categorie
            
            # Affichage
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
        except Exception as e:
            print(f"❌ Erreur générale: {e}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    print("🔍 EXTRACTION DES ÉLÉMENTS STRUCTURÉS (VERSION CORRIGÉE)")
    print("="*60)
    
    extracteur = ExtracteurElements()
    
    # Analyser les 3 analyses
    for analyse_id in [1, 2, 3]:
        extracteur.analyser_document(analyse_id)
        print("\n" + "-"*60)