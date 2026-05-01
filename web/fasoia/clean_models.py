# clean_models.py

import django
import os
import sys

# Configuration Django
sys.path.append('/media/folly/28DC9DDE2CA969AD/DOCS/SEA/UJKZ/COURS/MEMOIRE/fasoia/web/fasoia')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
django.setup()

from myAppli.models import Offre_uemoa, Ami_uemoa
from analyse_ia.models import DocumentSource, AnalyseDocument

def vider_tables():
    """
    Vide toutes les tables dans le bon ordre
    """
    print("="*60)
    print("🧹 NETTOYAGE DES MODÈLES")
    print("="*60)
    
    # 1. Compter avant suppression
    print("\n📊 ÉTAT ACTUEL:")
    print(f"   AnalyseDocument: {AnalyseDocument.objects.count()}")
    print(f"   DocumentSource: {DocumentSource.objects.count()}")
    print(f"   Offre_uemoa: {Offre_uemoa.objects.count()}")
    print(f"   Ami_uemoa: {Ami_uemoa.objects.count()}")
    
    # 2. Demander confirmation
    reponse = input("\n⚠️  Êtes-vous sûr de vouloir tout supprimer ? (oui/non): ")
    
    if reponse.lower() != 'oui':
        print("❌ Annulation")
        return
    
    # 3. Supprimer dans l'ordre (respecter les clés étrangères)
    print("\n🗑️  Suppression en cours...")
    
    # D'abord les analyses (qui dépendent des documents)
    nb_analyse = AnalyseDocument.objects.all().delete()
    print(f"   ✅ AnalyseDocument supprimés")
    
    # Ensuite les documents sources (qui dépendent des offres/amis)
    nb_doc = DocumentSource.objects.all().delete()
    print(f"   ✅ DocumentSource supprimés")
    
    # Enfin les offres et AMI
    nb_offre = Offre_uemoa.objects.all().delete()
    print(f"   ✅ Offre_uemoa supprimés")
    
    nb_ami = Ami_uemoa.objects.all().delete()
    print(f"   ✅ Ami_uemoa supprimés")
    
    # 4. Vérification
    print("\n📊 ÉTAT FINAL:")
    print(f"   AnalyseDocument: {AnalyseDocument.objects.count()}")
    print(f"   DocumentSource: {DocumentSource.objects.count()}")
    print(f"   Offre_uemoa: {Offre_uemoa.objects.count()}")
    print(f"   Ami_uemoa: {Ami_uemoa.objects.count()}")
    
    print("\n" + "="*60)
    print("✅ NETTOYAGE TERMINÉ")
    print("="*60)

if __name__ == "__main__":
    vider_tables()