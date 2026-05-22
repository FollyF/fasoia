import os
import requests
import json
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Détermination dynamique de la racine du projet FASOIA (deux niveaux au-dessus de ce fichier)
DOSSIER_SCRIPT = os.path.dirname(os.path.abspath(__file__))
RACINE_PROJET = os.path.abspath(os.path.join(DOSSIER_SCRIPT, "..", "..", ".."))

# Le fichier historique reste dans le dossier du scraper
HISTORIQUE_FILE = os.path.join(DOSSIER_SCRIPT, "historique_telechargements.json")


def generer_hash_url(url):
    """ Calcule l'empreinte unique MD5 d'une URL """
    return hashlib.md5(url.encode('utf-8')).hexdigest()


def charger_historique():
    """ Charge le dictionnaire des hashs déjà connus """
    if os.path.exists(HISTORIQUE_FILE):
        try:
            with open(HISTORIQUE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def sauvegarder_dans_historique(hash_url, nom_fichier):
    """ Enregistre le couple {hash: nom_du_fichier} """
    historique = charger_historique()
    if hash_url not in historique:
        historique[hash_url] = nom_fichier
        with open(HISTORIQUE_FILE, 'w', encoding='utf-8') as f:
            json.dump(historique, f, ensure_ascii=False, indent=4)


def telecharger_les_revues(dossier_destination):
    URL_SITE = "https://www.dgcmef.gov.bf/index.php/fr/home-5"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    print(f"1. Analyse de la page : {URL_SITE}")
    try:
        response = requests.get(URL_SITE, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"[ERREUR] Code HTTP : {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        historique = charger_historique()
        
        fichiers_a_prendre = []
        
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            if '.pdf' in href.lower():
                lien_complet = urljoin(URL_SITE, href)
                
                hash_url = generer_hash_url(lien_complet)
                nom_fichier = lien_complet.split('/')[-1].split('?')[0]
                
                if hash_url not in historique and lien_complet not in [l[2] for l in fichiers_a_prendre]:
                    fichiers_a_prendre.append((hash_url, nom_fichier, lien_complet))

        if not fichiers_a_prendre:
            print("[INFO] Aucun nouveau PDF détecté par le système de hachage. Tout est à jour.")
            return []

        print(f"\n[INFO] Repéré {len(fichiers_a_prendre)} nouveau(x) fichier(s) non présent(s) dans l'historique.")
        fichiers_sauvegardes = []

        for hash_url, nom_fichier, url_pdf in fichiers_a_prendre:
            chemin_final = os.path.join(dossier_destination, nom_fichier)
            print(f"   -> Récupération (MD5: {hash_url[:8]}) : {nom_fichier}...")
            
            try:
                with requests.get(url_pdf, headers=headers, stream=True) as r:
                    r.raise_for_status()
                    with open(chemin_final, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                
                print(f"   [OK] Téléchargé.")
                sauvegarder_dans_historique(hash_url, nom_fichier)
                fichiers_sauvegardes.append(chemin_final)
                
            except Exception as e:
                print(f"   [ERREUR] Impossible de télécharger {nom_fichier} : {e}")

        return fichiers_sauvegardes

    except Exception as e:
        print(f"[ERREUR] Échec de l'opération : {e}")
        return []


if __name__ == "__main__":
    # Correction ici : Construction du chemin vers racine / media / pdfs / dgcmef
    DOSSIER_CIBLE = os.path.join(RACINE_PROJET, "media", "pdfs", "dgcmef")
    
    if not os.path.exists(DOSSIER_CIBLE):
        os.makedirs(DOSSIER_CIBLE)
        print(f"[SYSTEM] Création du répertoire de stockage : {DOSSIER_CIBLE}")
        
    telecharger_les_revues(dossier_destination=DOSSIER_CIBLE)