import os
from io import BytesIO
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt

class GenerateurCVPublic:
    """
    Service de génération de CV accessible à tous
    """
    
    def __init__(self):
        self.templates_dir = 'cv/'
    
    def preparer_donnees(self, form_data):
        """Prépare les données du formulaire"""
        experiences = []
        if form_data.get('experiences'):
            for ligne in form_data['experiences'].split('\n'):
                if ligne.strip():
                    parts = [p.strip() for p in ligne.split('|')]
                    if len(parts) >= 3:
                        exp = {
                            'titre': parts[0],
                            'entreprise': parts[1] if len(parts) > 1 else '',
                            'date_debut': parts[2] if len(parts) > 2 else '',
                            'date_fin': parts[3] if len(parts) > 3 else 'Présent',
                            'description': parts[4] if len(parts) > 4 else '',
                        }
                        experiences.append(exp)
        
        formations = []
        if form_data.get('formations'):
            for ligne in form_data['formations'].split('\n'):
                if ligne.strip():
                    parts = [p.strip() for p in ligne.split('|')]
                    if len(parts) >= 3:
                        formation = {
                            'diplome': parts[0],
                            'etablissement': parts[1] if len(parts) > 1 else '',
                            'annee': parts[2] if len(parts) > 2 else '',
                        }
                        formations.append(formation)
        
        competences = []
        if form_data.get('competences'):
            competences = [c.strip() for c in form_data['competences'].split(',') if c.strip()]
        
        langues = []
        if form_data.get('langues'):
            langues = [l.strip() for l in form_data['langues'].split(',') if l.strip()]
        
        centres_interet = []
        if form_data.get('centres_interet'):
            centres_interet = [ci.strip() for ci in form_data['centres_interet'].split(',') if ci.strip()]
        
        return {
            'style': form_data.get('style', 'moderne'),
            'prenom': form_data.get('prenom', '').strip(),
            'nom': form_data.get('nom', '').strip(),
            'email': form_data.get('email', '').strip(),
            'telephone': form_data.get('telephone', '').strip(),
            'adresse': form_data.get('adresse', '').strip(),
            'ville': form_data.get('ville', '').strip(),
            'pays': form_data.get('pays', '').strip(),
            'code_postal': form_data.get('code_postal', '').strip(),
            'permis': form_data.get('permis', '').strip(),
            'resume': form_data.get('resume', '').strip(),
            'competences': competences,
            'langues': langues,
            'centres_interet': centres_interet,
            'experiences': experiences,
            'formations': formations,
            'date_generation': datetime.now().strftime('%d/%m/%Y'),
        }
    
    def generer_html(self, donnees):
        """Génère le HTML à partir du template"""
        template_name = f"{self.templates_dir}{donnees['style']}.html"
        
        try:
            return render_to_string(template_name, donnees)
        except Exception as e:
            # Template de secours minimal
            return f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8"></head>
            <body>
                <h1>{donnees['prenom']} {donnees['nom']}</h1>
                <p>{donnees['email']} | {donnees['telephone']}</p>
            </body>
            </html>
            """
    
    def generer_pdf(self, donnees):
        """Génère un PDF"""
        html_string = self.generer_html(donnees)
        return HTML(string=html_string, base_url=settings.BASE_DIR).write_pdf()
    
    def generer_docx(self, donnees):
        """Génère un DOCX avec python-docx"""
        doc = Document()
        
        # Titre
        doc.add_heading(f"{donnees['prenom']} {donnees['nom']}", 0)
        
        # Contact
        if donnees['email'] or donnees['telephone']:
            contact = doc.add_paragraph()
            if donnees['email']:
                contact.add_run(f"Email: {donnees['email']}\n")
            if donnees['telephone']:
                contact.add_run(f"Tél: {donnees['telephone']}")
        
        # Résumé
        if donnees['resume']:
            doc.add_heading('PROFIL', level=1)
            doc.add_paragraph(donnees['resume'])
        
        # Expériences
        if donnees.get('experiences'):
            doc.add_heading('EXPÉRIENCES PROFESSIONNELLES', level=1)
            for exp in donnees['experiences']:
                p = doc.add_paragraph()
                p.add_run(f"{exp['titre']} - {exp['entreprise']}").bold = True
                p.add_run(f" ({exp['date_debut']} - {exp.get('date_fin', 'Présent')})")
                if exp.get('description'):
                    doc.add_paragraph(exp['description'], style='List Bullet')
        
        # Formations
        if donnees.get('formations'):
            doc.add_heading('FORMATION', level=1)
            for formation in donnees['formations']:
                p = doc.add_paragraph()
                p.add_run(f"{formation['diplome']} - {formation['etablissement']}").bold = True
                p.add_run(f" ({formation['annee']})")
        
        # Compétences
        if donnees.get('competences'):
            doc.add_heading('COMPÉTENCES', level=1)
            doc.add_paragraph(', '.join(donnees['competences']))
        
        # Langues
        if donnees.get('langues'):
            doc.add_heading('LANGUES', level=1)
            doc.add_paragraph(', '.join(donnees['langues']))
        
        # Centres d'intérêt
        if donnees.get('centres_interet'):
            doc.add_heading('CENTRES D\'INTÉRÊT', level=1)
            doc.add_paragraph(', '.join(donnees['centres_interet']))
        
        # Sauvegarder dans un buffer
        docx_buffer = BytesIO()
        doc.save(docx_buffer)
        docx_buffer.seek(0)
        
        return docx_buffer.getvalue()
    
    def generer_apercu(self, style):
        """
        Génère un aperçu HTML du style sans données utilisateur
        """
        # Données d'exemple pour l'aperçu
        donnees_exemple = {
            'style': style,
            'prenom': 'Jean',
            'nom': 'DUPONT',
            'email': 'jean.dupont@email.com',
            'telephone': '+33 6 12 34 56 78',
            'adresse': '15 Rue de la Paix',
            'ville': 'Paris',
            'pays': 'France',
            'code_postal': '75001',
            'permis': 'B',
            'resume': 'Professionnel dynamique avec 5 ans d\'expérience dans le développement web. Passionné par les nouvelles technologies et le travail en équipe.',
            'competences': ['Python', 'Django', 'JavaScript', 'React', 'SQL', 'Git'],
            'langues': ['Français (courant)', 'Anglais (professionnel)', 'Espagnol (notions)'],
            'centres_interet': ['Lecture', 'Sport (running)', 'Voyages', 'Photographie'],
            'experiences': [
                {
                    'titre': 'Développeur Full Stack',
                    'entreprise': 'TechCorp',
                    'date_debut': '2021',
                    'date_fin': 'Présent',
                    'description': 'Développement d\'applications web avec Django et React. Gestion d\'une équipe de 3 développeurs.'
                },
                {
                    'titre': 'Développeur Junior',
                    'entreprise': 'StartupIA',
                    'date_debut': '2019',
                    'date_fin': '2021',
                    'description': 'Maintenance et évolution d\'applications existantes. Participation à la refonte du site principal.'
                }
            ],
            'formations': [
                {
                    'diplome': 'Master en Informatique',
                    'etablissement': 'Université de Paris',
                    'annee': '2019'
                },
                {
                    'diplome': 'Licence en Mathématiques',
                    'etablissement': 'Université de Lyon',
                    'annee': '2017'
                }
            ],
            'date_generation': datetime.now().strftime('%d/%m/%Y'),
        }
        
        template_name = f"{self.templates_dir}{style}.html"
        
        try:
            html_string = render_to_string(template_name, donnees_exemple)
            return html_string
        except Exception as e:
            print(f"❌ Erreur génération aperçu pour {style}: {e}")
            # Template de secours
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; }}
                    h1 {{ color: #1ed760; }}
                    .preview-box {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="preview-box">
                    <h1>Aperçu du style {style}</h1>
                    <p><strong>Jean DUPONT</strong></p>
                    <p>Développeur Full Stack</p>
                    <hr>
                    <h2>EXPÉRIENCES</h2>
                    <p><strong>Développeur Full Stack</strong> - TechCorp (2021-Présent)</p>
                    <p>Développement d'applications web avec Django et React.</p>
                    <p><strong>Développeur Junior</strong> - StartupIA (2019-2021)</p>
                    <p>Maintenance et évolution d'applications existantes.</p>
                    
                    <h2>FORMATION</h2>
                    <p><strong>Master en Informatique</strong> - Université de Paris (2019)</p>
                    
                    <h2>COMPÉTENCES</h2>
                    <p>Python, Django, JavaScript, React, SQL</p>
                </div>
            </body>
            </html>
            """
    
    def generer_cv(self, donnees, format='pdf'):
        """Génère un CV dans le format demandé"""
        if format == 'pdf':
            contenu = self.generer_pdf(donnees)
            content_type = 'application/pdf'
            extension = 'pdf'
        elif format == 'docx':
            contenu = self.generer_docx(donnees)
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            extension = 'docx'
        else:
            raise ValueError(f"Format non supporté: {format}")
        
        nom_fichier = f"CV_{donnees['prenom']}_{donnees['nom']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}".replace(' ', '_')
        
        response = HttpResponse(contenu, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{nom_fichier}.{extension}"'
        
        return response