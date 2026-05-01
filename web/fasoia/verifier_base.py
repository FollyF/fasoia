# verifier_base.py

import django
import os
import sys

sys.path.append('/media/folly/28DC9DDE2CA969AD/DOCS/SEA/UJKZ/COURS/MEMOIRE/fasoia/web/fasoia')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from myAppli.models import Offre_uemoa, Ami_uemoa
from analyse_ia.models import AnalyseDocument

def verifier_integrite():
    print("="*60)
    print("🔍 VÉRIFICATION DE L'INTÉGRITÉ DES DONNÉES")
    print("="*60)
    
    # 1. Vérifier les offres
    ct_offre = ContentType.objects.get_for_model(Offre_uemoa)
    offres_avec_analyse = AnalyseDocument.objects.filter(content_type=ct_offre).count()
    offres_total = Offre_uemoa.objects.count()
    
    print(f"\n📦 OFFRES:")
    print(f"   Total: {offres_total}")
    print(f"   Avec analyse: {offres_avec_analyse}")
    
    # 2. Vérifier les AMI
    ct_ami = ContentType.objects.get_for_model(Ami_uemoa)
    amis_avec_analyse = AnalyseDocument.objects.filter(content_type=ct_ami).count()
    amis_total = Ami_uemoa.objects.count()
    
    print(f"\n📦 AMI:")
    print(f"   Total: {amis_total}")
    print(f"   Avec analyse: {amis_avec_analyse}")
    
    # 3. Vérifier la cohérence
    print(f"\n🔗 TOTAL ANALYSES: {AnalyseDocument.objects.count()}")
    
    # 4. Afficher un exemple
    print("\n📄 EXEMPLE:")
    exemple = AnalyseDocument.objects.first()
    if exemple:
        obj = exemple.document_source
        print(f"   Analyse #{exemple.id}")
        print(f"   Liée à: {obj.__class__.__name__} #{obj.id}")
        print(f"   Catégorie: {exemple.categorie}")
        print(f"   Mots-clés: {list(exemple.mots_cles.keys())[:5]}")

if __name__ == "__main__":
    verifier_integrite()