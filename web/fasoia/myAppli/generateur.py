# myAppli/generateur.py
import os
from datetime import datetime
from django.conf import settings
from docxtpl import DocxTemplate
import traceback

class GenerateurDocument:
    def __init__(self):
        print("🔧 Initialisation du générateur de documents")
    
    def generer(self, modele, entreprise, opportunite, opportunite_type, donnees_supp=None):
        """
        Génère un document Word à partir du template
        
        Args:
            modele: ModeleDocument - le modèle à utiliser
            entreprise: Entreprise - l'entreprise qui soumissionne
            opportunite: Offre_uemoa ou Ami_uemoa - l'opportunité
            opportunite_type: str - 'Offre_uemoa' ou 'Ami_uemoa'
            donnees_supp: dict - données supplémentaires du formulaire
        
        Returns:
            tuple: (chemin_complet, nom_fichier, taille)
        """
        print(f"\n  🚀 GÉNÉRATION DU DOCUMENT")
        print(f"  📄 Modèle ID: {modele.id}")
        print(f"  📄 Modèle Nom: {modele.nom}")
        print(f"  📂 Catégorie: {modele.categorie}")
        print(f"  🏢 Entreprise: {entreprise.raisonSociale}")
        print(f"  📋 Opportunité type: {opportunite_type}")
        
        # Vérifier que le template existe
        if not os.path.exists(modele.fichier_template.path):
            error_msg = f"Template introuvable: {modele.fichier_template.path}"
            print(f"  ❌ {error_msg}")
            raise Exception(error_msg)
        
        print(f"  ✅ Template trouvé: {modele.fichier_template.path}")
        
        # Préparer le contexte avec toutes les données
        context = {
            # === Données de l'entreprise ===
            'entreprise_raison_sociale': entreprise.raisonSociale,
            'entreprise_nom': entreprise.raisonSociale,
            'entreprise_domaine': entreprise.domaineActive or '',
            'entreprise_competences': entreprise.competencesCles or '',
            'entreprise_localisation': entreprise.localisation or '',
            'entreprise_taille': entreprise.taille or 0,
            'entreprise_description': entreprise.description or '',
            'entreprise_site_web': entreprise.site_web or '',
            'entreprise_annee_creation': entreprise.annee_creation or '',
            'entreprise_chiffre_affaires': f"{entreprise.chiffre_affaires:,.0f}" if entreprise.chiffre_affaires else '0',
            'entreprise_capital_social': f"{entreprise.capital_social:,.0f}" if entreprise.capital_social else '0',
            'entreprise_annees_experience': entreprise.annees_experience or 0,
            'entreprise_nb_projets': entreprise.nb_projets_realises or 0,
            'entreprise_references': entreprise.references or '',
            'entreprise_certifications': ', '.join(entreprise.certifications) if entreprise.certifications else 'Aucune',
            'entreprise_agrements': ', '.join(entreprise.agrements) if entreprise.agrements else 'Aucun',
            'entreprise_pays_intervention': ', '.join(entreprise.pays_intervention) if entreprise.pays_intervention else 'Non spécifié',
            'entreprise_rayon_action': f"{entreprise.rayon_action} km" if entreprise.rayon_action else 'Non spécifié',
            
            # === Données de contact ===
            'contact_nom': f"{entreprise.prenom} {entreprise.nom}" if hasattr(entreprise, 'prenom') else '',
            'contact_telephone': str(entreprise.telephone) if entreprise.telephone else '',
            'contact_email': entreprise.email,
            
            # === Données de l'opportunité ===
            'opportunite_titre': opportunite.description[:100] if hasattr(opportunite, 'description') else '',
            'opportunite_description': opportunite.description if hasattr(opportunite, 'description') else '',
            'opportunite_reference': f"{opportunite_type}-{opportunite.id}",
            'opportunite_date_limite': opportunite.date_limite.strftime('%d/%m/%Y') if opportunite.date_limite else 'Non spécifiée',
            'opportunite_url': opportunite.download_url if hasattr(opportunite, 'download_url') else '',
            
            # === Informations générales ===
            'date_generation': datetime.now(),
            'date_generation_str': datetime.now().strftime('%d/%m/%Y à %H:%M'),
            'date_jour': datetime.now().strftime('%d/%m/%Y'),
            'opportunite_type': 'Appel d\'offres UEMOA' if opportunite_type == 'Offre_uemoa' else 'Appel à Manifestation d\'Intérêt UEMOA',
            'opportunite_type_code': opportunite_type,
        }
        
        # Ajouter les données selon la catégorie du modèle
        if donnees_supp:
            # Catégorie TECHNIQUE
            if modele.categorie == 'TECHNIQUE':
                context.update({
                    'methodologie_proposee': donnees_supp.get('methodologie', ''),
                    'moyens_humains': donnees_supp.get('moyens_humains', ''),
                    'moyens_materiels': donnees_supp.get('moyens_materiels', ''),
                })
            
            # Catégorie FINANCIER
            elif modele.categorie == 'FINANCIER':
                montant = donnees_supp.get('montant', '')
                try:
                    montant_float = float(montant) if montant else 0
                    context.update({
                        'montant_propose': f"{montant_float:,.0f}" if montant_float else '',
                        'montant_propose_brut': montant,
                    })
                except:
                    context.update({
                        'montant_propose': montant,
                        'montant_propose_brut': montant,
                    })
                context.update({
                    'delai_paiement': donnees_supp.get('delai_paiement', ''),
                })
            
            # Catégorie ADMINISTRATIF
            elif modele.categorie == 'ADMINISTRATIF':
                context.update({
                    'registre_commerce': donnees_supp.get('registre_commerce', ''),
                    'nif': donnees_supp.get('nif', ''),
                    'statut_juridique': donnees_supp.get('statut_juridique', ''),
                })
            
            # Ajouter toutes les autres variables personnalisées
            for key, value in donnees_supp.items():
                if key not in context:
                    context[f'var_{key}'] = value
        
        # Ajouter une variable de test
        context['test_var'] = "Ceci est un test de génération de document"
        context['entreprise_adresse_complete'] = f"{entreprise.localisation}, {', '.join(entreprise.pays_intervention) if entreprise.pays_intervention else 'Burkina Faso'}"
        
        print(f"  📊 Contexte préparé avec {len(context)} variables")
        
        # Générer le nom du fichier (utilisation de l'id et du nom sans espaces)
        nom_safe = modele.nom.replace(' ', '_').replace('/', '_').replace('\\', '_')
        nom_fichier = f"{modele.id}_{nom_safe}_{entreprise.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        
        # Créer le dossier de destination
        dossier_dest = os.path.join(settings.MEDIA_ROOT, 'soumissions', str(entreprise.id))
        os.makedirs(dossier_dest, exist_ok=True)
        
        chemin_complet = os.path.join(dossier_dest, nom_fichier)
        print(f"  📁 Chemin de destination: {chemin_complet}")
        
        # Générer le document avec docxtpl
        try:
            print(f"  🔄 Chargement du template DocxTemplate...")
            doc = DocxTemplate(modele.fichier_template.path)
            
            print(f"  🔄 Rendu du template avec le contexte...")
            doc.render(context)
            
            print(f"  🔄 Sauvegarde du document...")
            doc.save(chemin_complet)
            
            taille = os.path.getsize(chemin_complet)
            print(f"  ✅ Document sauvegardé avec succès!")
            print(f"  📊 Taille: {taille} octets ({taille/1024:.2f} KB)")
            
            return chemin_complet, nom_fichier, taille
            
        except Exception as e:
            print(f"  ❌ Erreur lors de la génération: {str(e)}")
            traceback.print_exc()
            raise