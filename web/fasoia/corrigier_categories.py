# corriger_categories.py

import django
import os
import sys

sys.path.append('/media/folly/28DC9DDE2CA969AD/DOCS/SEA/UJKZ/COURS/MEMOIRE/fasoia/web/fasoia')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from myAppli.models import Offre_uemoa, Ami_uemoa
from analyse_ia.models import AnalyseDocument

def corriger_categories():
    print("="*60)
    print("🔧 CORRECTION DES CATÉGORIES")
    print("="*60)
    
    ct_offre = ContentType.objects.get_for_model(Offre_uemoa)
    
    # 1. Trouver les analyses d'offres mal catégorisées
    analyses_offres = AnalyseDocument.objects.filter(content_type=ct_offre)
    
    corrigees = 0
    for ana in analyses_offres:
        if ana.categorie == 'AMI':
            ancienne = ana.categorie
            ana.categorie = 'APPEL_OFFRE'
            ana.save()
            print(f"   Analyse #{ana.id}: {ancienne} → APPEL_OFFRE")
            corrigees += 1
    
    print(f"\n✅ {corrigees} analyses corrigées")

def lister_analyses():
    print("\n" + "="*60)
    print("📋 LISTE DES ANALYSES")
    print("="*60)
    
    ct_offre = ContentType.objects.get_for_model(Offre_uemoa)
    ct_ami = ContentType.objects.get_for_model(Ami_uemoa)
    
    print("\n📦 OFFRES ANALYSÉES:")
    for ana in AnalyseDocument.objects.filter(content_type=ct_offre).order_by('id'):
        print(f"   #{ana.id}: {ana.categorie} - Offre #{ana.object_id}")
    
    print("\n📦 AMIS ANALYSÉS:")
    for ana in AnalyseDocument.objects.filter(content_type=ct_ami).order_by('id'):
        print(f"   #{ana.id}: {ana.categorie} - AMI #{ana.object_id}")

if __name__ == "__main__":
    corriger_categories()
    lister_analyses()