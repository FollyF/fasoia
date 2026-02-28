import PyPDF2

with open('pdfs/AMI_003_Relance MONITORING_1.pdf', 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    print(f"Nombre de pages: {len(reader.pages)}")
    print(f"Est chiffré ? {reader.is_encrypted}")