# update_fichier_local.py
import os
import django
import hashlib
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
django.setup()

from myAppli.models import Offre_uemoa, Ami_uemoa
from django.core.files import File
from django.conf import settings

def trouver_chemin_fichier(nom_fichier):
    """
    Cherche le fichier dans media/pdfs/
    Utilise MEDIA_ROOT défini dans settings.py
    """
    # Utiliser MEDIA_ROOT pour le chemin de base
    base_path = Path(settings.MEDIA_ROOT) / "pdfs"
    chemin = base_path / nom_fichier
    return chemin if chemin.exists() else None

def update_offres():
    print("\n📄 MISE À JOUR DES OFFRES UEMOA")
    print("-" * 40)
    
    offres = Offre_uemoa.objects.all()
    total = offres.count()
    success = 0
    errors = 0
    
    print(f"📊 {total} offres à traiter\n")
    
    for i, offre in enumerate(offres, 1):
        print(f"[{i}/{total}] Traitement offre #{offre.id}...")
        
        # Générer le nom de fichier attendu (basé sur l'URL)
        url_hash = hashlib.md5(offre.download_url.encode()).hexdigest()[:12]
        nom_fichier = f"OFFRE_{url_hash}.pdf"
        
        chemin_fichier = trouver_chemin_fichier(nom_fichier)
        
        if chemin_fichier:
            try:
                with open(chemin_fichier, 'rb') as f:
                    # Le champ fichier_local attend un chemin relatif à MEDIA_ROOT
                    offre.fichier_local.save(f"pdfs/{nom_fichier}", File(f), save=True)
                    print(f"  ✅ Fichier lié: pdfs/{nom_fichier}")
                    success += 1
            except Exception as e:
                print(f"  ❌ Erreur: {e}")
                errors += 1
        else:
            print(f"  ⚠️ Fichier non trouvé: {nom_fichier}")
            # Chercher dans l'ancien emplacement au cas où
            ancien_chemin = Path(__file__).parent / "myAppli" / "pdfs" / nom_fichier
            if ancien_chemin.exists():
                print(f"     📁 Trouvé dans l'ancien emplacement! À déplacer vers media/pdfs/")
            errors += 1
    
    return success, errors

def update_amis():
    print("\n📋 MISE À JOUR DES AMI")
    print("-" * 40)
    
    amis = Ami_uemoa.objects.all()
    total = amis.count()
    success = 0
    errors = 0
    
    print(f"📊 {total} AMI à traiter\n")
    
    for i, ami in enumerate(amis, 1):
        print(f"[{i}/{total}] Traitement AMI #{ami.id}...")
        
        url_hash = hashlib.md5(ami.download_url.encode()).hexdigest()[:12]
        nom_fichier = f"AMI_{url_hash}.pdf"
        
        chemin_fichier = trouver_chemin_fichier(nom_fichier)
        
        if chemin_fichier:
            try:
                with open(chemin_fichier, 'rb') as f:
                    ami.fichier_local.save(f"pdfs/{nom_fichier}", File(f), save=True)
                    print(f"  ✅ Fichier lié: pdfs/{nom_fichier}")
                    success += 1
            except Exception as e:
                print(f"  ❌ Erreur: {e}")
                errors += 1
        else:
            print(f"  ⚠️ Fichier non trouvé: {nom_fichier}")
            # Chercher dans l'ancien emplacement
            ancien_chemin = Path(__file__).parent / "myAppli" / "pdfs" / nom_fichier
            if ancien_chemin.exists():
                print(f"     📁 Trouvé dans l'ancien emplacement! À déplacer vers media/pdfs/")
            errors += 1
    
    return success, errors

def verifier_fichiers_manquants():
    """Liste tous les PDFs présents dans le dossier media/pdfs/"""
    print("\n📁 VÉRIFICATION DES FICHIERS PRÉSENTS")
    print("-" * 40)
    
    pdfs_path = Path(settings.MEDIA_ROOT) / "pdfs"
    
    if not pdfs_path.exists():
        print(f"❌ Dossier {pdfs_path} non trouvé")
        return
    
    fichiers = list(pdfs_path.glob("*.pdf"))
    print(f"📊 {len(fichiers)} fichiers PDF trouvés dans media/pdfs/")
    
    # Affiche les 10 premiers pour vérifier
    print("\n📄 Aperçu des fichiers:")
    for f in fichiers[:10]:
        print(f"  - {f.name}")
    
    return fichiers

def deplacer_fichiers_anciens():
    """Déplace les fichiers de myAppli/pdfs/ vers media/pdfs/"""
    print("\n📦 DÉPLACEMENT DES FICHIERS ANCIENS")
    print("-" * 40)
    
    ancien_path = Path(__file__).parent / "myAppli" / "pdfs"
    nouveau_path = Path(settings.MEDIA_ROOT) / "pdfs"
    
    if not ancien_path.exists():
        print("✅ Aucun ancien dossier trouvé")
        return 0
    
    fichiers = list(ancien_path.glob("*.pdf"))
    if not fichiers:
        print("✅ Aucun fichier à déplacer")
        return 0
    
    nouveau_path.mkdir(parents=True, exist_ok=True)
    
    count = 0
    for fichier in fichiers:
        destination = nouveau_path / fichier.name
        if not destination.exists():
            fichier.rename(destination)
            print(f"  ✅ Déplacé: {fichier.name}")
            count += 1
        else:
            print(f"  ⏭️  Déjà existant: {fichier.name}")
    
    print(f"\n📊 {count} fichiers déplacés")
    return count

if __name__ == '__main__':
    print("="*60)
    print("🔗 MISE À JOUR DES FICHIERS LOCAUX")
    print("="*60)
    
    # D'abord déplacer les anciens fichiers si nécessaire
    deplaces = deplacer_fichiers_anciens()
    if deplaces > 0:
        print(f"\n✅ {deplaces} fichiers déplacés vers media/pdfs/")
    
    # Vérifier les fichiers présents
    verifier_fichiers_manquants()
    
    # Demander confirmation
    print("\n" + "="*60)
    input("Appuie sur Entrée pour commencer la mise à jour...")
    
    # Mise à jour des offres
    offres_ok, offres_ko = update_offres()
    
    # Mise à jour des AMI
    amis_ok, amis_ko = update_amis()
    
    # Résumé final
    print("\n" + "="*60)
    print("📊 RÉSUMÉ FINAL")
    print("="*60)
    print(f"✅ Offres: {offres_ok} liées, {offres_ko} en erreur")
    print(f"✅ AMI: {amis_ok} liés, {amis_ko} en erreur")
    print(f"\n📦 Total: {offres_ok + amis_ok} fichiers liés avec succès")
    print("="*60)