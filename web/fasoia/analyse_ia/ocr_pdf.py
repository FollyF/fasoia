import pytesseract
from pdf2image import convert_from_path
import os
from pathlib import Path

# Configurer explicitement le chemin de Tesseract
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/5/tessdata/'

def extraire_texte_pdf_ocr(chemin_pdf):
    """
    Extrait le texte d'un PDF scanné en utilisant l'OCR
    """
    print(f"📄 Conversion du PDF en images...")
    
    # Convertir chaque page en image
    images = convert_from_path(chemin_pdf, dpi=300)
    
    print(f"✅ {len(images)} pages converties")
    print("🔍 Lancement de l'OCR (peut prendre quelques minutes)...")
    
    texte_complet = ""
    
    for i, image in enumerate(images):
        print(f"   Traitement page {i+1}/{len(images)}...")
        
        # OCR sur l'image (français)
        texte_page = pytesseract.image_to_string(image, lang='fra')
        texte_complet += f"\n--- Page {i+1} ---\n"
        texte_complet += texte_page
        texte_complet += "\n"
    
    return texte_complet

if __name__ == "__main__":
    # Chemin vers votre PDF problématique
    chemin_pdf = "pdfs/AMI_003_Relance MONITORING_1.pdf"
    
    if os.path.exists(chemin_pdf):
        print("="*50)
        print("OCR SUR LE PDF PROBLEMATIQUE")
        print("="*50)
        
        try:
            texte = extraire_texte_pdf_ocr(chemin_pdf)
            
            print("\n" + "="*50)
            print("TEXTE EXTRAIT (début):")
            print("="*50)
            print(texte[:1000])
            
            # Sauvegarder dans un fichier
            with open("texte_extrait_final.txt", "w", encoding="utf-8") as f:
                f.write(texte)
            print("\n✅ Texte sauvegardé dans 'texte_extrait_final.txt'")
            
        except Exception as e:
            print(f"❌ Erreur détaillée: {e}")
            
    else:
        print("❌ Fichier non trouvé")