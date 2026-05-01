from django.core.management.base import BaseCommand
from myAppli.models import Entreprise
from analyse_ia.models import Recommandation
from urllib.parse import quote
from datetime import datetime

class Command(BaseCommand):
    help = 'Génère tous les liens WhatsApp pour les entreprises'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='liens_whatsapp.txt',
            help='Fichier de sortie'
        )
        parser.add_argument(
            '--entreprise',
            type=int,
            help='ID de l\'entreprise spécifique'
        )
    
    def handle(self, *args, **options):
        output_file = options['output']
        
        self.stdout.write(self.style.SUCCESS('🚀 GÉNÉRATION DES LIENS WHATSAPP'))
        self.stdout.write('='*50)
        
        # Fonction pour construire le message (à copier depuis views.py)
        def construire_message(entreprise, recommandations):
            prenom = entreprise.prenom if entreprise.prenom else "cher partenaire"
            
            message = f"🔔 *RECOMMANDATIONS FASOIA POUR {entreprise.raisonSociale.upper()}*\n\n"
            message += f"Bonjour {prenom},\n\n"
            message += f"Nous avons trouvé *{len(recommandations)} opportunités* pour vous :\n\n"
            
            for i, reco in enumerate(recommandations, 1):
                opportunite = reco.opportunite
                type_opp = "📄 APPEL D'OFFRE" if reco.opportunite_type == 'Offre_uemoa' else "📋 AMI"
                titre = opportunite.description[:80] + "..." if len(opportunite.description) > 80 else opportunite.description
                
                message += f"{i}. *{type_opp}*\n"
                message += f"   📌 {titre}\n"
                
                if opportunite.date_limite:
                    if hasattr(opportunite.date_limite, 'strftime'):
                        date_limite = opportunite.date_limite.strftime('%d/%m/%Y')
                    else:
                        date_limite = str(opportunite.date_limite)
                    message += f"   ⏰ Date limite: {date_limite}\n"
                
                message += f"   🎯 Score: {reco.score_global}%\n"
                
                if reco.competences_match:
                    competences = ", ".join(reco.competences_match[:3])
                    message += f"   🔑 Compétences: {competences}\n"
                
                message += "\n"
            
            message += "💡 Connectez-vous sur https://fasoia.com pour postuler !\n\n"
            message += "L'équipe FasoIA"
            
            return message
        
        # Récupérer les entreprises
        if options['entreprise']:
            entreprises = Entreprise.objects.filter(id=options['entreprise'])
        else:
            entreprises = Entreprise.objects.filter(profil_complet=True)
        
        self.stdout.write(f"📊 {entreprises.count()} entreprises à traiter")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"🔗 LIENS WHATSAPP GÉNÉRÉS LE {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
            f.write("="*80 + "\n\n")
            
            count = 0
            for entreprise in entreprises:
                recommandations = Recommandation.objects.filter(
                    entreprise=entreprise
                ).order_by('-score_global')[:5]
                
                if recommandations:
                    message = construire_message(entreprise, recommandations)
                    message_encoded = quote(message)
                    telephone = str(entreprise.telephone).replace('+', '').replace(' ', '')
                    lien = f"https://wa.me/{telephone}?text={message_encoded}"
                    
                    f.write(f"🏢 {entreprise.raisonSociale}\n")
                    f.write(f"👤 {entreprise.prenom} {entreprise.nom}\n")
                    f.write(f"📞 {entreprise.telephone}\n")
                    f.write(f"📧 {entreprise.email}\n")
                    f.write(f"📊 {len(recommandations)} recommandations\n")
                    f.write(f"🔗 {lien}\n")
                    f.write("-"*80 + "\n\n")
                    
                    count += 1
                    self.stdout.write(f"  ✅ {entreprise.raisonSociale} ({len(recommandations)} recos)")
            
            self.stdout.write(self.style.SUCCESS(f"\n✅ {count} liens générés dans {output_file}"))