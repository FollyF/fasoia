import os
import re
import json
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("[ERREUR] pdfplumber manquant. Installez-le : pip install pdfplumber")
    sys.exit(1)


# Chemins
DOSSIER_SCRIPT = os.path.dirname(os.path.abspath(__file__))
RACINE_PROJET = os.path.abspath(os.path.join(DOSSIER_SCRIPT, ".."))
DOSSIER_PDFS = os.path.join(RACINE_PROJET, "media", "pdfs", "dgcmef")
FICHIER_SORTIE = os.path.join(DOSSIER_SCRIPT, "offres_quotidiens.json")


# ─────────────────────────────────────────────────────────────────
# 1. LECTURE DU SOMMAIRE (page 2)
# ─────────────────────────────────────────────────────────────────

def lire_sommaire(pdf) -> dict:
    """Lit la page 2 du bulletin et retourne les pages de début."""
    try:
        texte = pdf.pages[1].extract_text() or ""
    except:
        texte = ""
    structure = {}

    # Résultats provisoires
    m = re.search(r'RESULTATS?\s+PROVISOIRES?[^\n]*?P\.?\s*(\d+)', texte, re.IGNORECASE)
    if m:
        structure['RESULTATS'] = int(m.group(1))

    # AVIS
    m = re.search(r'\bAVIS\b.*?(?:fournitures|travaux|prestations|march).*?P\.?\s*(\d+)',
                  texte, re.IGNORECASE | re.DOTALL)
    if not m:
        m = re.search(r'\bAVIS\b[^\d]{0,200}P\.?\s*(\d+)', texte, re.IGNORECASE | re.DOTALL)
    if m:
        structure['AVIS'] = int(m.group(1))

    return structure


def _detecter_debut_avis_heuristique(pdf) -> int:
    """Fallback si le sommaire est illisible."""
    mots_cles_avis = [
        'avis de demande de prix',
        "avis d'appel d'offres",
        'avis à manifestation d',
        'manifestation d\'intérêt',
        'demande de prix',
    ]
    for i, page in enumerate(pdf.pages):
        texte = (page.extract_text() or "").lower()
        if any(m in texte for m in mots_cles_avis):
            # Vérifie que ce n'est pas une page de résultat
            if 'soumissionnaire' not in texte and 'attributaire' not in texte:
                return i + 1
    return 1


# ─────────────────────────────────────────────────────────────────
# 2. DÉTECTION D'UNE NOUVELLE OFFRE
# ─────────────────────────────────────────────────────────────────

# Mots qui indiquent une page de résultat (à ignorer ou à fusionner avec l'offre précédente)
MOTS_RESULTAT = ['soumissionnaire', 'attributaire', 'classement', 'montant lu', 'offre conforme']

# Mots qui indiquent une nouvelle offre (autorités contractantes possibles)
PREFIXES_AUTORITE = [
    'MINISTERE', 'ECOLE', 'OFFICE', 'CAISSE', 'CENTRE', 'UNIVERSITE',
    'AGENCE', 'INSTITUT', 'SERVICE', 'DIRECTION', 'SECRETARIAT',
    'CHAMBRE', 'AUTORITE', 'MAIRIE', 'COMMUNE', 'CONSEIL', 'FONDS'
]


def est_nouvelle_offre(texte: str) -> bool:
    """
    Détecte si un texte marque le début d'une nouvelle offre.
    Stratégie: cherche une ligne en majuscules qui ressemble à une autorité.
    """
    lignes = texte.strip().split('\n')
    if not lignes:
        return False
    
    # Examine les 5 premières lignes
    for i in range(min(5, len(lignes))):
        ligne = lignes[i].strip()
        if not ligne:
            continue
        
        # Ignorer les lignes trop courtes
        if len(ligne) < 8:
            continue
        
        # Ignorer les lignes qui contiennent des mots de résultat
        if any(mot in ligne.lower() for mot in MOTS_RESULTAT):
            continue
        
        # Vérifie si la ligne est en majuscules
        if ligne.isupper() or ligne.upper() == ligne:
            # Vérifie si elle contient un préfixe d'autorité
            for prefixe in PREFIXES_AUTORITE:
                if ligne.upper().startswith(prefixe):
                    return True
            # Ou si elle est longue et en majuscules (probablement une autorité)
            if len(ligne) > 15:
                return True
    
    # Vérifie aussi la présence d'un avis dans les premières lignes
    zone = texte[:500].lower()
    motifs_avis = [
        r'avis\s+de\s+demande\s+de\s+prix',
        r'avis\s+d\'appel\s+d\'offres',
        r'avis\s+de\s+manifestation',
        r'demande\s+de\s+prix\s+n[°º]',
    ]
    for motif in motifs_avis:
        if re.search(motif, zone, re.IGNORECASE):
            return True
    
    return False


def fusionner_pages_en_offres(pages_texte):
    """
    Fusionne les pages qui appartiennent à la même offre.
    Une nouvelle offre commence quand on détecte une autorité contractante.
    """
    offres = []
    offre_courante = ""
    pages_offre = []
    
    for page in pages_texte:
        texte = page["texte"]
        
        if est_nouvelle_offre(texte):
            # Sauvegarde l'offre précédente
            if offre_courante:
                offres.append({
                    "texte": offre_courante,
                    "pages": pages_offre
                })
            # Commence une nouvelle offre
            offre_courante = texte
            pages_offre = [page["num"]]
        else:
            # Continue l'offre courante
            if offre_courante:
                offre_courante += "\n\n" + texte
                pages_offre.append(page["num"])
            else:
                # Première page (avant d'avoir détecté une offre)
                offre_courante = texte
                pages_offre = [page["num"]]
    
    # Dernière offre
    if offre_courante:
        offres.append({
            "texte": offre_courante,
            "pages": pages_offre
        })
    
    return offres


# ─────────────────────────────────────────────────────────────────
# 3. CLASSIFICATION ET EXTRACTION
# ─────────────────────────────────────────────────────────────────

def determiner_categorie(texte: str) -> str:
    zone = texte[:2000].lower()
    
    # 1. ADDENDUM
    if re.search(r'(addendum|rectificatif|prorogation|additif)', zone):
        return 'ADDENDUM'
    
    # 2. APPEL D'OFFRES
    if re.search(r'(avis\s+d[\'’]?appel\s+d[\'’]?offres|appel\s+d[\'’]?offres)', zone):
        return 'APPEL_OFFRE'
    
    # 3. AMI
    if re.search(r'(manifestation\s+d[\'’]?int[eé]r[eê]t|avis\s+[àa]\s+manifestation)', zone):
        return 'AMI'
    
    # 4. DEMANDE DE PRIX
    if re.search(r'(demande\s+de\s+prix|avis\s+de\s+demande\s+de\s+prix)', zone):
        return 'DP'
    
    return 'AUTRE'

def extraire_reference(texte: str) -> str | None:
    patterns = [
        r'[Nn][°º]\s*(20\d{2}[-\s]\d+/[A-Z][A-Z0-9/\-]+)',
        r'[Nn][°º]\s*(20\d{2}-\d{4}/[A-Z0-9/\-]+)',
        r'demande\s+de\s+prix\s+[Nn][°º]\s*([A-Z0-9\-/\.]+)',
        r'appel\s+d[.\']?offres[^Nn]{0,30}[Nn][°º]\s*([A-Z0-9\-/\.]+)',
        r'[Nn][°º]\s*([A-Z0-9\-/]{8,30})',
    ]
    for p in patterns:
        m = re.search(p, texte[:1500], re.IGNORECASE)
        if m:
            ref = m.group(1).strip().rstrip('/')
            if len(ref) > 5 and 'PRES/PM' not in ref and not ref.isdigit():
                return ref
    return None


def extraire_autorite(texte: str) -> str | None:
    """Extrait l'autorité contractante (premières lignes en majuscules)"""
    lignes = texte.strip().split('\n')
    for ligne in lignes[:10]:
        ligne = ligne.strip()
        if not ligne:
            continue
        # Ignorer les lignes d'en-tête de page
        if re.match(r'^N°\d+', ligne):
            continue
        if re.match(r'^\d+$', ligne):
            continue
        if ligne.startswith('www.') or ligne.startswith('http'):
            continue
        # Cherche une ligne en majuscules et longue
        if (ligne.isupper() or ligne.upper() == ligne) and len(ligne) > 10:
            # Ignorer les faux positifs
            mots_ignores = ['AVIS', 'RESULTAT', 'CONCLUSION', 'SOMMAIRE', 'PAGE', 'N°']
            if not any(mot in ligne.upper() for mot in mots_ignores):
                return ligne[:200]
    return None


def extraire_objet(texte: str) -> str | None:
    """Extrait l'objet du marché"""
    m = re.search(r'(?:ayant\s+pour\s+objet|OBJET\s*:)\s*(.{20,400}?)(?:\n\n|\n(?:[A-Z]|$))', texte, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r'\s+', ' ', m.group(1)).strip()[:400]
    
    # Sinon, prend la ligne après l'autorité
    lignes = texte.strip().split('\n')
    for i, ligne in enumerate(lignes[:15]):
        if ligne.strip() and (ligne.isupper() or ligne.upper() == ligne) and len(ligne) > 10:
            if i + 1 < len(lignes):
                objet = lignes[i + 1].strip()
                if len(objet) > 15 and not objet.isupper():
                    return objet[:400]
    return None


def extraire_date_limite(texte: str) -> str | None:
    # Nettoie le texte
    texte_clean = ' '.join(texte[:4000].split())
    
    patterns = [
        # Format JJ/MM/AAAA
        r'avant\s+le\s+(\d{1,2}/\d{2}/20\d{2})',
        r'au\s+plus\s+tard\s+le\s+(\d{1,2}/\d{2}/20\d{2})',
        r'date\s+limite[^:]*:\s*(\d{1,2}/\d{2}/20\d{2})',
        r'dépôt\s+des\s+offres.*?(\d{1,2}/\d{2}/20\d{2})',
        r'remises?\s+[àa]\s+l[‘\']?adresse.*?(\d{1,2}/\d{2}/20\d{2})',
        r'clôture\s+le\s+(\d{1,2}/\d{2}/20\d{2})',
        
        # Format JJ Mois AAAA (ex: 29 mai 2026)
        r'avant\s+le\s+(\d{1,2}\s+\w+\s+20\d{2})',
        r'au\s+plus\s+tard\s+le\s+(\d{1,2}\s+\w+\s+20\d{2})',
        r'dépôt\s+des\s+offres.*?(\d{1,2}\s+\w+\s+20\d{2})',
        r'clôture\s+le\s+(\d{1,2}\s+\w+\s+20\d{2})',
        
        # Format seul JJ/MM/AAAA
        r'(\d{1,2}/\d{2}/20\d{2})\s+[àa]\s+\d{1,2}h',
        r'\b(\d{1,2}/\d{2}/20\d{2})\b',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, texte_clean, re.IGNORECASE)
        if m:
            date_str = m.group(1).strip()
            
            # Convertit "29 mai 2026" en "29/05/2026"
            if ' ' in date_str and '/' not in date_str:
                mois_map = {
                    'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
                    'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
                    'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
                }
                parties = date_str.split()
                if len(parties) >= 3:
                    jour = parties[0].zfill(2)
                    mois = parties[1].lower()
                    annee = parties[2]
                    if mois in mois_map:
                        date_str = f"{jour}/{mois_map[mois]}/{annee}"
            return date_str
    
    return None

def extraire_montant_dossier(texte: str) -> str | None:
    m = re.search(r'montant\s+non\s+remboursable\s+de\s+([\d\s]{3,15})\s*(?:F\s*)?CFA', texte[:4000], re.IGNORECASE)
    if m:
        return m.group(1).strip() + " FCFA"
    return None


def extraire_delai_execution(texte: str) -> str | None:
    m = re.search(r'délai\s+d[ée]x[ée]cution\s+(?:est\s+de|ne\s+devrait\s+pas\s+excéder)\s*:?\s*([^.\n]{5,60})', texte, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def extraire_telephone(texte: str) -> str | None:
    m = re.search(r'(?:\(226\)|\+226)\s*[\d\s\-]{10,15}', texte)
    if m:
        return m.group(0).strip()
    m = re.search(r'[Tt]él[ée]?\.?\s*:?\s*((?:\d{2}[\s\-]?){4,5})', texte)
    if m:
        return m.group(1).strip()
    return None


def extraire_email(texte: str) -> str | None:
    m = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', texte)
    if m:
        return m.group(0).lower()
    return None


# ─────────────────────────────────────────────────────────────────
# 4. TRAITEMENT DE TOUS LES PDFS
# ─────────────────────────────────────────────────────────────────

def executer_traitement_lots():
    print("="*70)
    print(" EXTRACTION DES OFFRES (fusion pages multipages)")
    print("="*70)

    if not os.path.exists(DOSSIER_PDFS):
        print(f"[ERREUR] Dossier introuvable : {DOSSIER_PDFS}")
        return

    fichiers = [f for f in os.listdir(DOSSIER_PDFS) if f.lower().endswith('.pdf')]
    print(f"[INFO] {len(fichiers)} fichier(s) PDF détecté(s)")

    toutes_les_offres = []
    compteur_global = 1

    for nom_fichier in sorted(fichiers):
        chemin_complet = os.path.join(DOSSIER_PDFS, nom_fichier)
        print(f"\n[TRAITEMENT] {nom_fichier}...")

        try:
            with pdfplumber.open(chemin_complet) as pdf:
                nb_pages = len(pdf.pages)
                print(f"   -> {nb_pages} pages")

                # Lit le sommaire
                sommaire = lire_sommaire(pdf)
                page_debut = sommaire.get('AVIS', None)

                if page_debut is None:
                    page_debut = _detecter_debut_avis_heuristique(pdf)
                    print(f"   -> Début des avis (heuristique) : page {page_debut}")
                else:
                    print(f"   -> Début des avis (sommaire) : page {page_debut}")

                # Extrait les pages à partir de la page de début
                pages_extraites = []
                for num_page in range(page_debut - 1, nb_pages):
                    texte = pdf.pages[num_page].extract_text() or ""
                    if texte.strip():
                        pages_extraites.append({
                            "num": num_page + 1,
                            "texte": texte
                        })

                print(f"   -> {len(pages_extraites)} pages extraites")

                # Fusionne les pages en offres
                offres_fusionnees = fusionner_pages_en_offres(pages_extraites)
                print(f"   -> {len(offres_fusionnees)} offre(s) après fusion")

                # Traite chaque offre
                for offre in offres_fusionnees:
                    texte = offre["texte"]
                    toutes_les_offres.append({
                        "id_intermediaire": compteur_global,
                        "source_bulletin": nom_fichier,
                        "pages": offre["pages"],
                        "categorie": determiner_categorie(texte),
                        "reference": extraire_reference(texte),
                        "autorite_contractante": extraire_autorite(texte),
                        "objet": extraire_objet(texte),
                        "date_limite": extraire_date_limite(texte),
                        "montant_dossier": extraire_montant_dossier(texte),
                        "delai_execution": extraire_delai_execution(texte),
                        "telephone": extraire_telephone(texte),
                        "email": extraire_email(texte),
                        "texte_brut": texte[:5000]
                    })
                    compteur_global += 1

        except Exception as e:
            print(f"   [ERREUR] {e}")
            import traceback
            traceback.print_exc()

    # Sauvegarde
    resultat = {
        "total_offres_extraites": len(toutes_les_offres),
        "offres": toutes_les_offres
    }

    with open(FICHIER_SORTIE, 'w', encoding='utf-8') as f:
        json.dump(resultat, f, ensure_ascii=False, indent=4)

    print("\n" + "="*70)
    print(f"[SUCCÈS] Extraction terminée !")
    print(f"   -> Total offres : {len(toutes_les_offres)}")
    print(f"   -> Fichier : {FICHIER_SORTIE}")
    print("="*70)


if __name__ == "__main__":
    executer_traitement_lots()