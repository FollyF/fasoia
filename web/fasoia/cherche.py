import fitz
import pytesseract
from PIL import Image
import io

# Configuration
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# Ouvre le PDF
doc = fitz.open('media/pdfs/dgcmef/Quotidien%20N%C2%B04403.pdf')

print("=== TEST OCR SUR CHAQUE PAGE ===")

for page_num in range(doc.page_count):
    page = doc[page_num]
    
    # Texte natif
    texte_natif = page.get_text()
    
    # Cherche dans les images
    image_list = page.get_images()
    
    for img_index, img in enumerate(image_list):
        try:
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            
            if pix.n - pix.alpha < 4:
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                texte_ocr = pytesseract.image_to_string(image, lang='fra')
                
                if 'APPELS' in texte_ocr.upper() or 'APPELS' in texte_natif.upper():
                    print(f"\n--- PAGE {page_num + 1} ---")
                    print(f"Texte natif: {texte_natif[:200]}")
                    print(f"OCR trouvé: {texte_ocr[:200]}")
                    
            pix = None
        except Exception as e:
            pass

doc.close()
print("\n=== FIN DU TEST ===")