import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import spacy
import re
import time  # AJOUTER CET IMPORT
from pathlib import Path

# --- CONFIGURATION DYNAMIQUE DU CHEMIN ---
import os
import sys
import django

# Récupère le chemin du dossier où se trouve ce script (analyse_ia/)
current_file_path = os.path.abspath(__file__)
# Remonte d'un cran pour atteindre la racine du projet (là où est manage.py)
project_root = os.path.dirname(os.path.dirname(current_file_path))

if project_root not in sys.path:
    sys.path.append(project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
django.setup()
# -----------------------------------------

from django.contrib.contenttypes.models import ContentType
from analyse_ia.models import *
from myAppli.models import *

# Configuration Tesseract
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/5/tessdata/'

class AnalyseurHybride:
    """
    Analyseur PDF intelligent avec :
    - Détection page par page (texte vs scan)
    - OCR uniquement sur les pages scannées
    - Analyse NLP avec spaCy
    - Sauvegarde automatique
    """
    
    def __init__(self):
        print("Chargement du modèle spaCy...")
        self.nlp = spacy.load("fr_core_news_sm")
        print("✅ Modèle spaCy chargé")
    
    def extraire_texte_hybride(self, chemin_pdf):
        """
        Extrait le texte en traitant chaque page selon son type
        """
        try:
            doc = fitz.open(chemin_pdf)
            texte_complet = ""
            stats = {'texte': 0, 'ocr': 0}
            
            print(f"📑 {len(doc)} pages détectées")
            
            for i in range(len(doc)):
                page = doc[i]
                debut_page = time.time()  # AJOUT
                
                # 1. Essayer d'extraire le texte natif
                texte_natif = page.get_text()
                mots_natifs = [w for w in texte_natif.split() if len(w) > 3]
                
                if len(mots_natifs) > 10:  # Page textuelle
                    print(f"   Page {i+1}: 📝 texte ({len(mots_natifs)} mots) - {time.time()-debut_page:.1f}s")
                    texte_complet += f"\n--- Page {i+1} ---\n"
                    texte_complet += texte_natif
                    stats['texte'] += 1
                    
                else:  # Page scannée -> OCR
                    print(f"   Page {i+1}: 🔍 OCR...", end='', flush=True)
                    
                    # Convertir en image
                    pix = page.get_pixmap(dpi=300)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    
                    # OCR
                    texte_ocr = pytesseract.image_to_string(img, lang='fra')
                    duree = time.time() - debut_page  # AJOUT
                    print(f" {len(texte_ocr)} caractères - {duree:.1f}s")
                    
                    texte_complet += f"\n--- Page {i+1} (OCR) ---\n"
                    texte_complet += texte_ocr
                    stats['ocr'] += 1
            
            print(f"✅ Extraction: {stats['texte']} pages texte, {stats['ocr']} pages OCR")
            return texte_complet
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return None
    
    def analyser_texte(self, texte):
        """Analyse le texte avec spaCy"""
        debut = time.time()  # AJOUT
        print(f"   🔄 Analyse NLP en cours...", end='', flush=True)
        
        doc = self.nlp(texte[:100000])
        
        # Mots-clés
        mots = {}
        for token in doc:
            if (not token.is_stop and not token.is_punct and 
                token.pos_ in ['NOUN', 'PROPN', 'VERB'] and len(token.text) > 3):
                mot = token.lemma_.lower()
                mots[mot] = mots.get(mot, 0) + 1
        
        total = sum(mots.values())
        mots_cles = {}
        if total > 0:
            for mot, count in sorted(mots.items(), key=lambda x: x[1], reverse=True)[:30]:
                mots_cles[mot] = round(count / total, 3)
        
        # Entités
        entites = {
            'dates': [], 'lieux': [], 'organisations': [], 'montants': [],
            'emails': [], 'telephones': [], 'reference': ''
        }
        
        for ent in doc.ents:
            if ent.label_ == "DATE" and len(ent.text) > 4:
                entites['dates'].append(ent.text)
            elif ent.label_ in ["LOC", "GPE"]:
                entites['lieux'].append(ent.text)
            elif ent.label_ == "ORG":
                entites['organisations'].append(ent.text)
            elif ent.label_ == "MONEY":
                entites['montants'].append(ent.text)
        
        # Regex pour informations supplémentaires
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', texte)
        entites['emails'] = list(set(emails))
        
        tels = re.findall(r'(?:\+226|0)[1-9](?:[\s.-]?\d{2}){4}', texte)
        entites['telephones'] = list(set(tels))
        
        # Référence
        ref_match = re.search(r'N[°°]\s*([A-Z0-9\-/]+)', texte[:2000], re.IGNORECASE)
        if ref_match:
            entites['reference'] = ref_match.group(1).strip()
        
        # Catégorie
        texte_lower = texte.lower()
        if 'manifestation' in texte_lower or 'ami' in texte_lower:
            categorie = 'AMI'
        elif 'appel' in texte_lower and 'offre' in texte_lower:
            categorie = 'APPEL_OFFRE'
        elif 'addendum' in texte_lower:
            categorie = 'ADDENDUM'
        else:
            categorie = 'AUTRE'
        
        duree = time.time() - debut  # AJOUT
        print(f" ✅ {duree:.1f}s")
        
        return {
            'mots_cles': mots_cles,
            'entites': entites,
            'categorie': categorie,
            'texte_extrait': texte[:1000]
        }
    
    def analyser_cv(self, texte):
        """
        Extrait les éléments structurés d'un CV
        Uniquement pour les CVs uploadés (PDF externe)
        """
        print(f"   🔄 Analyse CV en cours...", end='', flush=True)
        debut = time.time()

        texte_lower = texte.lower()

        # 1. Compétences — mots techniques détectés
        competences_tech = [
            'python', 'django', 'javascript', 'react', 'sql', 'mysql',
            'postgresql', 'mongodb', 'java', 'php', 'html', 'css',
            'excel', 'word', 'powerpoint', 'autocad', 'photoshop',
            'comptabilité', 'audit', 'marketing', 'communication',
            'gestion', 'management', 'logistique', 'finance', 'rh',
            'anglais', 'français', 'leadership', 'analyse', 'reporting'
        ]
        competences = [c for c in competences_tech if c in texte_lower]

        # 2. Niveau d'étude
        niveau_etude = ''
        niveaux = {
            'doctorat': ['doctorat', 'phd', 'thèse'],
            'master': ['master', 'mba', 'bac+5', 'ingénieur'],
            'licence': ['licence', 'bachelor', 'bac+3'],
            'bts': ['bts', 'dut', 'bac+2'],
            'bac': ['baccalauréat', 'bac ']
        }
        for niveau, mots in niveaux.items():
            if any(mot in texte_lower for mot in mots):
                niveau_etude = niveau
                break

        # 3. Années d'expérience
        annees_experience = 0
        patterns_exp = [
            r"(\d+)\s*ans?\s*d.exp",
            r"experience\s*[\:\s]+(\d+)\s*an",
            r"(\d+)\s*ans?\s*anciennete",
        ]
        for pattern in patterns_exp:
            match = re.search(pattern, texte_lower)
            if match:
                annees_experience = int(match.group(1))
                break

        # 4. Langues
        langues_possibles = {
            'français': ['français', 'french', 'francais'],
            'anglais': ['anglais', 'english', 'anglophone'],
            'arabe': ['arabe', 'arabic'],
            'espagnol': ['espagnol', 'spanish'],
            'allemand': ['allemand', 'german'],
            'mooré': ['mooré', 'moore'],
            'dioula': ['dioula'],
        }
        langues = [
            langue for langue, mots in langues_possibles.items()
            if any(mot in texte_lower for mot in mots)
        ]

        # 5. Secteurs
        secteurs_possibles = {
            'IT': ['informatique', 'développement', 'logiciel', 'web', 'réseau'],
            'Finance': ['comptabilité', 'finance', 'audit', 'banque', 'trésorerie'],
            'Marketing': ['marketing', 'communication', 'publicité', 'digital'],
            'Education': ['enseignement', 'formation', 'éducation', 'pédagogie'],
            'Santé': ['santé', 'médical', 'infirmier', 'pharmacie'],
            'BTP': ['construction', 'bâtiment', 'génie civil', 'architecture'],
            'Logistique': ['logistique', 'transport', 'supply chain'],
            'Agriculture': ['agriculture', 'agronomie', 'élevage'],
        }
        secteurs = [
            secteur for secteur, mots in secteurs_possibles.items()
            if any(mot in texte_lower for mot in mots)
        ]

        # 6. Localisation
        villes_bf = ['ouagadougou', 'bobo-dioulasso', 'koudougou', 'banfora', 'ouahigouya']
        ville = ''
        for v in villes_bf:
            if v in texte_lower:
                ville = v.capitalize()
                break

        # 7. Contact
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', texte)
        tels = re.findall(r'(?:\+226|0)[1-9](?:[\s.-]?\d{2}){4}', texte)

        # 8. Postes occupés
        postes = []
        doc = self.nlp(texte[:50000])
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                postes.append(ent.text)

        duree = time.time() - debut
        print(f" ✅ {duree:.1f}s")

        return {
            'competences': list(set(competences)),
            'niveau_etude': niveau_etude,
            'annees_experience': annees_experience,
            'langues': langues,
            'secteurs': secteurs,
            'ville': ville,
            'pays': 'Burkina Faso',
            'emails': list(set(emails))[:5],
            'telephones': list(set(tels))[:5],
            'postes_occupes': list(set(postes))[:10],
        }

    def analyser_offre(self, texte, offre):
        """
        Extrait les éléments structurés d'une OffreEmploi scrapée (PDF)
        Complète les champs DB avec ce qui est dans le PDF
        """
        print(f"   🔄 Analyse offre en cours...", end='', flush=True)
        debut = time.time()

        texte_lower = texte.lower()

        # 1. Compétences détectées dans le PDF
        competences_tech = [
            'python', 'django', 'javascript', 'react', 'sql', 'mysql',
            'postgresql', 'java', 'php', 'html', 'css', 'excel',
            'comptabilité', 'audit', 'marketing', 'gestion', 'management',
            'logistique', 'finance', 'anglais', 'leadership', 'reporting'
        ]
        competences_detectees = [c for c in competences_tech if c in texte_lower]

        # Combiner avec celles de la DB
        competences_db = offre.competences_requises or []
        toutes_competences = list(set(competences_detectees + competences_db))

        # 2. Niveau d'étude détecté
        niveau_detecte = offre.niveau_etude_requis or ''
        if not niveau_detecte:
            niveaux = {
                'master': ['master', 'bac+5', 'ingénieur'],
                'licence': ['licence', 'bac+3'],
                'bts': ['bts', 'bac+2'],
                'bac': ['baccalauréat']
            }
            for niveau, mots in niveaux.items():
                if any(mot in texte_lower for mot in mots):
                    niveau_detecte = niveau
                    break

        # 3. Années d'expérience détectées
        annees_detectees = offre.annees_experience_min or 0
        if not annees_detectees:
            for pattern in [r"(\d+)\s*ans?\s*experience", r"(\d+)\s*ans?\s*anciennete"]:
                match = re.search(pattern, texte_lower)
                if match:
                    annees_detectees = int(match.group(1))
                    break

        # 4. Langues
        langues_possibles = {
            'français': ['français', 'francais'],
            'anglais': ['anglais', 'english'],
            'arabe': ['arabe'],
        }
        langues_detectees = [
            langue for langue, mots in langues_possibles.items()
            if any(mot in texte_lower for mot in mots)
        ]
        # Combiner avec DB
        langues_db = offre.langues_requises or []
        toutes_langues = list(set(langues_detectees + langues_db))

        # 5. Contact
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', texte)
        tels = re.findall(r'(?:\+226|0)[1-9](?:[\s.-]?\d{2}){4}', texte)

        # 6. Salaire détecté
        salaire_detecte = offre.salaire_affiche or ''
        if not salaire_detecte:
            match = re.search(r'(\d[\d\s]+)\s*(?:fcfa|cfa|xof)', texte_lower)
            if match:
                salaire_detecte = match.group(1).strip()

        # 7. Documents exigés
        documents_possibles = {
            'CV': ['cv', 'curriculum vitae'],
            'Lettre de motivation': ['lettre de motivation', 'lettre motivat'],
            'Diplôme': ['diplôme', 'attestation de diplôme', 'copie diplôme'],
            'CNI': ['cni', "carte nationale", "pièce d'identité"],
            'Casier judiciaire': ['casier judiciaire', 'extrait de casier'],
            'Photo': ['photo d\'identité', 'photographie'],
            'Références': ['références', 'lettre de référence'],
            'Certificat de travail': ['certificat de travail', 'attestation de travail'],
            'Passeport': ['passeport'],
        }

        documents_exiges = []
        for doc, mots_cles in documents_possibles.items():
            if any(mot in texte_lower for mot in mots_cles):
                documents_exiges.append(doc)

        # CV et Lettre toujours inclus par défaut
        if 'CV' not in documents_exiges:
            documents_exiges.insert(0, 'CV')
        if 'Lettre de motivation' not in documents_exiges:
            documents_exiges.insert(1, 'Lettre de motivation')

        duree = time.time() - debut
        print(f" ✅ {duree:.1f}s")

        return {
            'competences_detectees': toutes_competences,
            'niveau_etude_detecte': niveau_detecte,
            'annees_experience_detectees': annees_detectees,
            'langues_detectees': toutes_langues,
            'secteurs_detectes': [offre.get_secteur_display()],
            'ville_detectee': offre.ville or '',
            'pays_detecte': offre.pays or 'Burkina Faso',
            'emails': list(set(emails))[:5],
            'telephones': list(set(tels))[:5],
            'salaire_detecte': salaire_detecte,
            'documents_exiges': documents_exiges,
        }

    def traiter_document(self, doc_source):
        """Traite un DocumentSource complet"""
        print(f"\n📄 Traitement de: {doc_source.nom_fichier}")
        debut_doc = time.time()  # AJOUT
        
        # 1. Vérifier que le fichier existe
        # Construit le chemin dynamiquement
        chemin_complet = os.path.join(project_root, "media", "pdfs", os.path.basename(doc_source.nom_fichier))
        
        if not os.path.exists(chemin_complet):
            print(f"   ❌ Fichier non trouvé: {chemin_complet}")
            return None
        
        # 2. Extraction hybride
        texte = self.extraire_texte_hybride(chemin_complet)
        if not texte:
            print("   ❌ Échec extraction")
            return None
        
        # 3. Analyse
        resultats = self.analyser_texte(texte)
        
        # 4. Déterminer l'objet lié
        if doc_source.offre_scrapee:
            obj = doc_source.offre_scrapee
            content_type = ContentType.objects.get_for_model(Offre_uemoa)
            print(f"   🔗 Lié à Offre_uemoa #{obj.id}")
        elif doc_source.ami_scrapee:
            obj = doc_source.ami_scrapee
            content_type = ContentType.objects.get_for_model(Ami_uemoa)
            print(f"   🔗 Lié à Ami_uemoa #{obj.id}")
        else:
            print("   ⚠️ Document non lié")
            return None
        
        # 5. Sauvegarde
        analyse, created = AnalyseDocument.objects.update_or_create(
            content_type=content_type,
            object_id=obj.id,
            defaults={
                'texte_extrait': resultats['texte_extrait'],
                'mots_cles': resultats['mots_cles'],
                'entites': resultats['entites'],
                'categorie': resultats['categorie'],
                'temps_analyse_ms': int((time.time() - debut_doc) * 1000)  # AJOUT
            }
        )
        
        duree_totale = time.time() - debut_doc  # AJOUT
        print(f"   ✅ Analyse {'créée' if created else 'mise à jour'} (ID: {analyse.id})")
        print(f"   📌 Catégorie: {resultats['categorie']}")
        print(f"   🔑 Top mots: {list(resultats['mots_cles'].keys())[:5]}")
        print(f"   ⏱️  Temps total: {duree_totale:.1f}s")  # AJOUT
        
        return analyse

    def traiter_cv(self, candidat_id):
        debut_doc = time.time()

        print(f"\n👤 Traitement CV du candidat #{candidat_id}")

        try:
            candidat = Candidat.objects.get(particulier_id=candidat_id)
        except Candidat.DoesNotExist:
            print(f"   ❌ Candidat #{candidat_id} introuvable")
            return None

        # Vérifier si CV uploadé seulement
        if not candidat.cv:
            print(f"   ⚠️ Pas de CV uploadé — on utilise les champs DB")
            return None

        texte = extraire_texte_cv(candidat_id)
        if not texte:
            return None

        # Analyse générale
        resultats = self.analyser_texte(texte)

        # Analyse spécifique CV
        elements = self.analyser_cv(texte)

        # Sauvegarder AnalyseDocument
        content_type = ContentType.objects.get_for_model(Candidat)
        analyse, created = AnalyseDocument.objects.update_or_create(
            content_type=content_type,
            object_id=candidat.particulier_id,
            defaults={
                'texte_extrait': resultats['texte_extrait'],
                'mots_cles': resultats['mots_cles'],
                'entites': resultats['entites'],
                'categorie': 'CV',
                'temps_analyse_ms': int((time.time() - debut_doc) * 1000)
            }
        )

        # Sauvegarder ElementsCVExtraits
        ElementsCVExtraits.objects.update_or_create(
            analyse=analyse,
            defaults={
                'candidat': candidat,
                'competences': elements['competences'],
                'niveau_etude': elements['niveau_etude'],
                'annees_experience': elements['annees_experience'],
                'langues': elements['langues'],
                'secteurs': elements['secteurs'],
                'ville': elements['ville'],
                'pays': elements['pays'],
                'emails': elements['emails'],
                'telephones': elements['telephones'],
                'postes_occupes': elements['postes_occupes'],
            }
        )

        print(f"   ✅ CV analysé et éléments extraits")
        print(f"   🔑 Compétences: {elements['competences']}")
        print(f"   📚 Niveau: {elements['niveau_etude']}")
        print(f"   ⏱️  Temps: {time.time() - debut_doc:.1f}s")

        return analyse

    def traiter_offre_emploi(self, offre):
        from myAppli.models import OffreEmploi
        from analyse_ia.models import ElementsOffreExtraits
        debut_doc = time.time()

        print(f"\n💼 Traitement offre #{offre.id} - {offre.titre}")

        texte = extraire_texte_offre(offre)
        if not texte:
            return None

        # Analyse générale
        resultats = self.analyser_texte(texte)

        # Analyse spécifique offre
        elements = self.analyser_offre(texte, offre)

        # Sauvegarder AnalyseDocument
        content_type = ContentType.objects.get_for_model(OffreEmploi)
        analyse, created = AnalyseDocument.objects.update_or_create(
            content_type=content_type,
            object_id=offre.id,
            defaults={
                'texte_extrait': resultats['texte_extrait'],
                'mots_cles': resultats['mots_cles'],
                'entites': resultats['entites'],
                'categorie': 'OFFRE_EMPLOI',
                'temps_analyse_ms': int((time.time() - debut_doc) * 1000)
            }
        )

        # Sauvegarder ElementsOffreExtraits
        ElementsOffreExtraits.objects.update_or_create(
            analyse=analyse,
            defaults={
                'offre': offre,
                'competences_detectees': elements['competences_detectees'],
                'niveau_etude_detecte': elements['niveau_etude_detecte'],
                'annees_experience_detectees': elements['annees_experience_detectees'],
                'langues_detectees': elements['langues_detectees'],
                'secteurs_detectes': elements['secteurs_detectes'],
                'ville_detectee': elements['ville_detectee'],
                'pays_detecte': elements['pays_detecte'],
                'emails': elements['emails'],
                'telephones': elements['telephones'],
                'salaire_detecte': elements['salaire_detecte'],
                'documents_exiges': elements['documents_exiges'],
            }
        )

        print(f"   ✅ Offre analysée et éléments extraits")
        print(f"   🔑 Compétences: {elements['competences_detectees'][:5]}")
        print(f"   ⏱️  Temps: {time.time() - debut_doc:.1f}s")

        return analyse

def extraire_texte_cv(candidat_id):

    try:
        candidat = Candidat.objects.get(particulier_id=candidat_id)
    except Candidat.DoesNotExist:
        print(f"❌ Candidat {candidat_id} introuvable")
        return None

    chemin_cv = None
    source_cv = None

    # 1. CV généré marqué est_utilise
    cv_genere = CVGenere.objects.filter(
        utilisateur=candidat.particulier.user,
        est_utilise=True,
        fichier_pdf__isnull=False
    ).first()

    if cv_genere:
        chemin_cv = os.path.join(project_root, "media", cv_genere.fichier_pdf.name)
        source_cv = f"CV généré (utilisé) : {cv_genere.titre}"

    # 2. CV généré favori
    if not chemin_cv:
        cv_genere = CVGenere.objects.filter(
            utilisateur=candidat.particulier.user,
            est_favori=True,
            fichier_pdf__isnull=False
        ).first()

        if cv_genere:
            chemin_cv = os.path.join(project_root, "media", cv_genere.fichier_pdf.name)
            source_cv = f"CV généré (favori) : {cv_genere.titre}"

    # 3. CV généré le plus récent
    if not chemin_cv:
        cv_genere = CVGenere.objects.filter(
            utilisateur=candidat.particulier.user,
            fichier_pdf__isnull=False
        ).order_by('-date_generation').first()

        if cv_genere:
            chemin_cv = os.path.join(project_root, "media", cv_genere.fichier_pdf.name)
            source_cv = f"CV généré (récent) : {cv_genere.titre}"

    # 4. CV uploadé manuellement
    if not chemin_cv and candidat.cv:
        chemin_cv = os.path.join(project_root, "media", candidat.cv.name)
        source_cv = "CV uploadé manuellement"

    # 5. Aucun CV
    if not chemin_cv:
        print(f"❌ Candidat {candidat_id} n'a aucun CV disponible")
        return None

    # Extraction du texte
    print(f"\n📄 Source CV: {source_cv}")
    print(f"   Chemin: {chemin_cv}")

    if not os.path.exists(chemin_cv):
        print(f"❌ Fichier CV non trouvé: {chemin_cv}")
        return None

    doc = fitz.open(chemin_cv)
    texte_complet = ""

    for i in range(len(doc)):
        page = doc[i]
        texte_natif = page.get_text()
        mots = [w for w in texte_natif.split() if len(w) > 3]

        if len(mots) > 10:
            print(f"   Page {i+1}: 📝 texte ({len(mots)} mots)")
            texte_complet += texte_natif
        else:
            print(f"   Page {i+1}: 🔍 OCR...")
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            texte_complet += pytesseract.image_to_string(img, lang='fra')

    print(f"✅ CV extrait: {len(texte_complet)} caractères")
    return texte_complet

def extraire_texte_offre(offre):
    texte = f"""
        Titre: {offre.titre}
        Entreprise: {offre.entreprise_nom}
        Secteur: {offre.get_secteur_display()}
        Type de contrat: {offre.get_type_contrat_display()}
        Lieu: {offre.ville}, {offre.region}, {offre.pays}
        Télétravail: {offre.get_teletravail_display()}
        
        Expérience requise: {offre.get_niveau_experience_display()}
        Années expérience minimum: {offre.annees_experience_min}
        Années expérience maximum: {offre.annees_experience_max or 'Non précisé'}
        
        Niveau étude requis: {offre.niveau_etude_requis}
        Domaine étude: {offre.domaine_etude}
        
        Compétences requises: {', '.join(offre.competences_requises)}
        Compétences souhaitées: {', '.join(offre.competences_souhaitees)}
        Langues requises: {', '.join(offre.langues_requises)}
        
        Salaire: {offre.salaire_affiche or f"{offre.salaire_min} - {offre.salaire_max} {offre.salaire_devise}"}
        Date limite: {offre.date_limite}
        
        Description: {offre.description}
        Missions: {offre.missions}
        Profil recherché: {offre.profil_recherche}
        """
    if offre.fichier_local:
        chemin_pdf = os.path.join(project_root, "media", offre.fichier_local.name)
        if os.path.exists(chemin_pdf):
            analyseur = AnalyseurHybride()
            texte += analyseur.extraire_texte_hybride(chemin_pdf)  # ✅ réutilise ton code

    return texte

if __name__ == "__main__":
    import time  # AJOUT
    debut_global = time.time()  # AJOUT
    
    print("="*60)
    print("🔍 ANALYSEUR HYBRIDE PDF (TEXTE + OCR)")
    print("="*60)
    
    analyseur = AnalyseurHybride()
    
    # Récupérer tous les documents sans analyse
    from django.contrib.contenttypes.models import ContentType
    
    docs_a_traiter = []
    for doc in DocumentSource.objects.all():
        if doc.offre_scrapee:
            ct = ContentType.objects.get_for_model(Offre_uemoa)
            if not AnalyseDocument.objects.filter(content_type=ct, object_id=doc.offre_scrapee.id).exists():
                docs_a_traiter.append(doc)
        elif doc.ami_scrapee:
            ct = ContentType.objects.get_for_model(Ami_uemoa)
            if not AnalyseDocument.objects.filter(content_type=ct, object_id=doc.ami_scrapee.id).exists():
                docs_a_traiter.append(doc)
    
    print(f"\n📊 {len(docs_a_traiter)} documents à analyser")
    
    for i, doc in enumerate(docs_a_traiter, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(docs_a_traiter)}]")
        analyseur.traiter_document(doc)
    
    duree_globale = time.time() - debut_global  # AJOUT
    print(f"\n{'='*60}")
    print(f"🏁 ANALYSE TERMINÉE en {duree_globale:.1f} secondes")
    print(f"📊 Moyenne: {duree_globale/len(docs_a_traiter):.1f}s par document")
    print("="*60)