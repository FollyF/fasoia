import django
import os
import sys
import re
from datetime import datetime

sys.path.append('/media/folly/28DC9DDE2CA969AD/DOCS/SEA/UJKZ/COURS/MEMOIRE/fasoia/web/fasoia')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
django.setup()

from analyse_ia.models import AnalyseDocument, ElementsExtraits

def extraire_et_sauvegarder():
    print("="*60)
    print("📦 EXTRACTION ET SAUVEGARDE DES ÉLÉMENTS")
    print("="*60)
    
    # Patterns (simplifiés)
    patterns = {
        'reference': r'N[°°]\s*([A-Z0-9\-/]+)',
        'montant': r'montant\s*[:\s]+([0-9\s]+)\s*(?:€|euros|FCFA)',
        'date_limite': r'date\s*limite\s*[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        'email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
    }
    
    analyses = AnalyseDocument.objects.all()
    print(f"📊 {analyses.count()} analyses à traiter")
    
    cree = 0
    for analyse in analyses:
        texte = analyse.texte_extrait or ""
        
        # Extraire
        ref_match = re.search(patterns['reference'], texte, re.IGNORECASE)
        mt_match = re.search(patterns['montant'], texte, re.IGNORECASE)
        date_match = re.search(patterns['date_limite'], texte, re.IGNORECASE)
        emails = re.findall(patterns['email'], texte, re.IGNORECASE)
        
        # Sauvegarder
        elements, created = ElementsExtraits.objects.update_or_create(
            analyse=analyse,
            defaults={
                'reference': ref_match.group(1).strip() if ref_match else '',
                'montant_estime': mt_match.group(1).replace(' ', '') if mt_match else None,
                'date_limite': date_match.group(1) if date_match else None,
                'emails': list(set(emails))[:5],
                'autorite': '',  # À améliorer
                'lieu': '',      # À améliorer
            }
        )
        
        if created:
            cree += 1
            print(f"   ✅ Éléments pour analyse #{analyse.id} créés")
    
    print(f"\n✅ {cree} nouveaux éléments créés")

if __name__ == "__main__":
    extraire_et_sauvegarder()