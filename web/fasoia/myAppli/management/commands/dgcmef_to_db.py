import os
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from myAppli.models import Offre_uemoa, Ami_uemoa, Dp_uemoa, Addendum_uemoa

class Command(BaseCommand):
    help = "Injecte les offres extraites dans les tables UEMOA"

    def convertir_date(self, date_str):
        """Convertit une date du format DD/MM/YYYY en datetime avec fuseau"""
        if not date_str:
            return None
        try:
            # Nettoie la chaîne
            date_str = date_str.strip()
            # Extrait juste la partie date (avant espace ou autre)
            if ' ' in date_str:
                date_str = date_str.split()[0]
            # Convertit
            dt = datetime.strptime(date_str, '%d/%m/%Y')
            return timezone.make_aware(dt)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   Date non convertible: {date_str} - {e}"))
            return None

    def handle(self, *args, **options):
        dossier_commande = os.path.dirname(os.path.abspath(__file__))
        racine_projet = os.path.abspath(os.path.join(dossier_commande, "..", "..", ".."))
        fichier_entree = os.path.join(racine_projet, "analyse_ia", "offres_quotidiens.json")

        if not os.path.exists(fichier_entree):
            self.stdout.write(self.style.ERROR(f"Fichier introuvable : {fichier_entree}"))
            return

        with open(fichier_entree, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))
        self.stdout.write(self.style.MIGRATE_HEADING(" INJECTION DES OFFRES DANS LES TABLES UEMOA "))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))
        self.stdout.write(f"[INFO] {data['total_offres_extraites']} offres à traiter")

        mapping = {
            'APPEL_OFFRE': Offre_uemoa,
            'DP': Dp_uemoa,
            'AMI': Ami_uemoa,
            'ADDENDUM': Addendum_uemoa,
        }

        URL_BASE = 'https://www.dgcmef.gov.bf/fr/revue-de-march-s-pour-tous'
        compteurs = {'APPEL_OFFRE': 0, 'DP': 0, 'AMI': 0, 'ADDENDUM': 0, 'IGNORE': 0}

        for offre in data['offres']:
            categorie = offre.get('categorie', 'AUTRE')
            
            if categorie not in mapping:
                compteurs['IGNORE'] += 1
                continue

            model = mapping[categorie]
            
            # Conversion de la date
            date_limite = self.convertir_date(offre.get('date_limite'))

            # Préparation des champs
            defaults = {
                'description': offre.get('texte_brut', '') or offre.get('objet', ''),
                'autorite_contractante': offre.get('autorite_contractante'),
                'reference': offre.get('reference'),
                'email': offre.get('email'),
                'telephone': offre.get('telephone'),
                'montant_dossier': offre.get('montant_dossier'),
                'montant_previsionnel': offre.get('financement') or offre.get('montant_previsionnel'),
                'garantie_soumission': offre.get('garantie_soumission'),
                'delai_execution': offre.get('delai_execution'),
                'lieu_depot': offre.get('lieu_depot'),
                'date_limite': date_limite,
                'download_url': URL_BASE,
                'fichier_local': f"pdfs/dgcmef/{offre['source_bulletin']}",
                'traite_par_ia': False
            }

            try:
                obj, created = model.all_objects.update_or_create(
                    reference=offre.get('reference') or f"temp_{offre['id_intermediaire']}",
                    defaults=defaults
                )
                if created:
                    compteurs[categorie] += 1
                    self.stdout.write(f"   ✅ {categorie} #{offre['id_intermediaire']} inséré")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Erreur #{offre['id_intermediaire']}: {e}"))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("🏁 INJECTION TERMINÉE"))
        for cat, count in compteurs.items():
            if cat != 'IGNORE':
                self.stdout.write(f"   - {cat:15s} : {count} nouveaux")
        self.stdout.write(self.style.WARNING(f"   - IGNORÉS (AUTRE) : {compteurs['IGNORE']}"))
        self.stdout.write("=" * 60)