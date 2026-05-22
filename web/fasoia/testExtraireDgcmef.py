import pdfplumber
import re

def extraire_opportunites_dynamique(pdf_path):
    page_debut_avis = 0
    
    print(f"1. Ouverture du fichier : {pdf_path}...")
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"   -> Le document contient {total_pages} pages.")
        
        # Étape 1 : Détection dynamique de la page de début
        print("\n2. Recherche de la section AVIS (analyse des pages)...")
        for i, page in enumerate(pdf.pages):
            texte_page = page.extract_text() or ""
            
            # Détection basée sur les expressions courantes des entêtes d'offres
            # On ignore les deux premières pages (couverture + sommaire)
            if i > 1 and ("AVIS DE DEMANDE DE PRIX" in texte_page.upper() or 
                          "AVIS D’APPEL D’OFFRES" in texte_page.upper() or
                          "AVIS DE MANIFESTATION" in texte_page.upper()):
                page_debut_avis = i
                print(f"   [SUCCÈS] Section AVIS repérée à la PAGE {i + 1} !")
                break
        
        if page_debut_avis == 0:
            print("   [ATTENTION] Aucun mot-clé détecté. Analyse depuis la page 1 par défaut.")

        # Étape 2 : Extraction du texte à partir de cette page détectée
        print(f"\n3. Extraction du texte de la page {page_debut_avis + 1} à {total_pages}...")
        texte_total_avis = ""
        for page_num in range(page_debut_avis, total_pages):
            texte_page = pdf.pages[page_num].extract_text() or ""
            
            # Nettoyage des bas de page pour éviter de polluer les données
            texte_page = re.sub(r"N°\s*\d+\s*–.*", "", texte_page, flags=re.IGNORECASE)
            texte_page = re.sub(r"www\.dgcmef\.gov\.bf.*", "", texte_page, flags=re.IGNORECASE)
            
            texte_total_avis += f"\n--- PAGE {page_num + 1} ---\n" + texte_page

    # Étape 3 : Découpage par offre
    print("\n4. Découpage du texte en blocs d'opportunités distinctes...")
    # Un pattern plus robuste qui cherche le mot-clé principalement en début de section ou avec un numéro de référence direct
    pattern_separation = r'(?=\n(?:Avis de demande de prix|AVIS D’APPEL D’OFFRES|Avis d’appel d’offres|Avis de manifestation d’intérêt|AVIS DE MANIFESTATION)\s*\n|\n?N°\d{4}-)'
    blocs_offres = re.split(pattern_separation, texte_total_avis)
    
    # Nettoyage des blocs vides ou trop courts (bruits de texte)
    offres_finales = [bloc.strip() for bloc in blocs_offres if len(bloc.strip()) > 250]
    
    return offres_finales


# ═══════════════════════════════════════════════════════════════════════
# ÉXÉCUTION DU TEST
# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Nom de ton fichier
    fichier_target = "Quotidien N°4403.pdf"
    
    try:
        offres = extraire_opportunites_dynamique(fichier_target)
        
        print("\n" + "="*50)
        print(f" RESULTAT DU TEST : {len(offres)} opportunités trouvées !")
        print("="*50)
        
        # Affichage d'un aperçu des deux premières offres pour valider le traitement
        if len(offres) > 0:
            for index, offre in enumerate(offres[:2]):
                print(f"\n[OPPORTUNITÉ N°{index + 1}] (Aperçu des 300 premiers caractères) :")
                print("-" * 40)
                # On affiche juste le début pour valider l'ancrage du découpage
                print(offre[:300] + "\n...")
                print("-" * 40)
        else:
            print("[ERREUR] Aucune offre n'a pu être extraite. Vérifie les expressions régulières.")
            
    except FileNotFoundError:
        print(f"\n[ERREUR] Le fichier '{fichier_target}' est introuvable.")
        print("Assure-toi qu'il est placé exactement dans le même dossier que ce script Python.")