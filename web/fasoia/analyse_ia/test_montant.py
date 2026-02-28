# test_montant_reel.py

import django
import os
import sys
import re

# Configuration Django
sys.path.append('/media/folly/28DC9DDE2CA969AD/DOCS/SEA/UJKZ/COURS/MEMOIRE/fasoia/web/fasoia')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
django.setup()

from analyse_ia.models import AnalyseDocument

print("1️⃣ Connexion à la base de données...")
try:
    # Récupérer l'analyse #1
    analyse = AnalyseDocument.objects.get(id=1)
    print("✅ Analyse #1 trouvée")
    
    # Récupérer le texte
    if analyse.texte_extrait:
        texte = analyse.texte_extrait
        print(f"📄 Texte extrait: {len(texte)} caractères")
        
        # Afficher un extrait pour voir
        print("\n📝 Extrait du texte (500 premiers caractères):")
        print("-" * 40)
        print(texte[:500])
        print("-" * 40)
        
        # Tester la regex montant
        print("\n2️⃣ Test de la regex montant...")
        
        patterns = [
            r'montant\s*[:\s]+(\d+(?:\s?\d+)*)\s*(?:€|euros|EUR|FCFA)',
            r'(\d+(?:\s?\d+)*)\s*(?:€|euros|EUR|FCFA)'
        ]
        
        for i, pattern in enumerate(patterns, 1):
            print(f"\n   Pattern {i}: {pattern}")
            try:
                match = re.search(pattern, texte[:5000], re.IGNORECASE)
                if match:
                    print(f"   ✅ MATCH TROUVÉ!")
                    print(f"   Groupe 1: '{match.group(1)}'")
                    print(f"   Contexte: '{match.group(0)}'")
                else:
                    print(f"   ❌ Pas de match")
            except Exception as e:
                print(f"   ⚠️ Erreur: {e}")
        
        # Chercher manuellement des motifs de montant
        print("\n3️⃣ Recherche manuelle de 'montant' dans le texte...")
        
        # Chercher les occurrences de "montant"
        positions = []
        start = 0
        while True:
            pos = texte.lower().find('montant', start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        
        if positions:
            print(f"   ✅ 'montant' trouvé {len(positions)} fois")
            for i, pos in enumerate(positions[:3]):  # 3 premiers
                extrait = texte[pos:pos+100].replace('\n', ' ')
                print(f"\n   Occurrence {i+1} à la position {pos}:")
                print(f"   ...{extrait}...")
        else:
            print("   ❌ 'montant' pas trouvé dans le texte")
        
        # Chercher des nombres suivis de €/euros
        print("\n4️⃣ Recherche de motifs monétaires (nombres + devise)...")
        montant_pattern = r'(\d+(?:[.,\s]\d+)*)\s*(?:€|euros|EUR|FCFA)'
        matches = re.findall(montant_pattern, texte[:5000], re.IGNORECASE)
        
        if matches:
            print(f"   ✅ {len(matches)} motifs trouvés:")
            for m in matches[:5]:
                print(f"   • {m}")
        else:
            print("   ❌ Aucun motif monétaire trouvé")
            
    else:
        print("❌ Pas de texte extrait pour cette analyse")
        
except AnalyseDocument.DoesNotExist:
    print("❌ Analyse #1 non trouvée")
except Exception as e:
    print(f"❌ Erreur: {e}")