#!/usr/bin/env python
# pipeline_manager.py

"""
Orchestrateur du pipeline complet FasoIA
Usage:
    python pipeline_manager.py --scraping      # Lance scraping + toute la suite
    python pipeline_manager.py --analyse       # Lance analyse + extraction + recommandations
    python pipeline_manager.py --extraction    # Lance extraction + recommandations
    python pipeline_manager.py --recommandations  # Lance juste les recommandations
    python pipeline_manager.py --all           # Lance tout
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
import subprocess

class PipelineOrchestrateur:
    def __init__(self, config_file='pipeline_config.json'):
        # Les fichiers sont à la racine, donc chemin direct
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.base_dir = self.config['settings']['base_dir']
        self.python = self.config['settings']['python']
        self.log_dir = self.config['settings']['log_dir']
        self.timeout = self.config['settings']['timeout']
        
        self.log_file = f"{self.log_dir}/pipeline_{datetime.now().strftime('%Y%m%d')}.log"
        self._init_logging()
    
    def _init_logging(self):
        """Crée le dossier de logs si nécessaire"""
        os.makedirs(self.log_dir, exist_ok=True)
    
    def log(self, message, niveau="INFO"):
        """Log avec timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{niveau}] {message}"
        
        # Affichage console avec couleurs
        if niveau == "ERROR":
            print(f"\033[91m{log_line}\033[0m")
        elif niveau == "SUCCESS":
            print(f"\033[92m{log_line}\033[0m")
        elif niveau == "WARNING":
            print(f"\033[93m{log_line}\033[0m")
        else:
            print(log_line)
        
        # Écriture fichier
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    
    def executer_script(self, script_info):
        """Exécute un script individuel"""
        self.log(f"🚀 {script_info['name']}: {script_info['description']}")
        debut = time.time()
        
        chemin_complet = os.path.join(self.base_dir, script_info['path'])
        commande = f"cd {self.base_dir} && {self.python} {chemin_complet}"
        
        try:
            resultat = subprocess.run(
                commande,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            duree = time.time() - debut
            
            if resultat.returncode == 0:
                self.log(f"✅ {script_info['name']} terminé ({duree:.2f}s)", "SUCCESS")
                if resultat.stdout:
                    # Afficher les 5 dernières lignes
                    lignes = resultat.stdout.strip().split('\n')
                    for ligne in lignes[-5:]:
                        if ligne.strip():
                            self.log(f"   {ligne}")
                return True
            else:
                self.log(f"❌ {script_info['name']} échoué (code {resultat.returncode})", "ERROR")
                if resultat.stderr:
                    for ligne in resultat.stderr.strip().split('\n')[-5:]:
                        if ligne.strip():
                            self.log(f"   ERREUR: {ligne}", "ERROR")
                return not script_info.get('required', True)  # False si requis, True si optionnel
                
        except subprocess.TimeoutExpired:
            self.log(f"⏰ Timeout: {script_info['name']} (> {self.timeout}s)", "ERROR")
            return not script_info.get('required', True)
        except Exception as e:
            self.log(f"❌ Exception: {e}", "ERROR")
            return False
    
    def executer_phase(self, phase_name):
        """Exécute tous les scripts d'une phase"""
        if phase_name not in self.config['scripts']:
            self.log(f"❌ Phase inconnue: {phase_name}", "ERROR")
            return False
        
        scripts = self.config['scripts'][phase_name]
        self.log("\n" + "="*60)
        self.log(f"📦 PHASE: {phase_name.upper()}")
        self.log("="*60)
        
        tous_reussis = True
        for script in scripts:
            success = self.executer_script(script)
            if not success:
                if script.get('required', True):
                    self.log(f"❌ Script requis a échoué, phase interrompue", "ERROR")
                    return False
                else:
                    self.log(f"⚠️ Script optionnel a échoué, mais on continue", "WARNING")
                    tous_reussis = False
            time.sleep(2)
        
        return tous_reussis
    
    def scraping_et_suite(self):
        """Scraping + toute la suite"""
        if self.executer_phase('scraping'):
            return self.analyse_et_suite()
        return False
    
    def analyse_et_suite(self):
        """Analyse + extraction + recommandations"""
        if self.executer_phase('analyse'):
            return self.extraction_et_suite()
        return False
    
    def extraction_et_suite(self):
        """Extraction + recommandations"""
        if self.executer_phase('extraction'):
            return self.recommandations()
        return False
    
    def recommandations(self):
        """Recommandations uniquement"""
        return self.executer_phase('recommandations')
    
    def pipeline_complet(self):
        """Pipeline complet"""
        self.log("\n" + "="*60)
        self.log("🚀 DÉMARRAGE DU PIPELINE COMPLET")
        self.log("="*60)
        
        success = (
            self.executer_phase('scraping') and
            self.executer_phase('analyse') and
            self.executer_phase('extraction') and
            self.executer_phase('recommandations')
        )
        
        if success:
            self.log("\n" + "="*60)
            self.log("✅ PIPELINE COMPLET TERMINÉ AVEC SUCCÈS", "SUCCESS")
            self.log(f"📝 Logs: {self.log_file}")
            self.log("="*60)
        else:
            self.log("\n" + "="*60)
            self.log("❌ PIPELINE INTERROMPU", "ERROR")
            self.log(f"📝 Voir les logs: {self.log_file}")
            self.log("="*60)
        
        return success

def main():
    parser = argparse.ArgumentParser(description='Orchestrateur du pipeline FasoIA')
    parser.add_argument('--config', default='pipeline_config.json', help='Fichier de configuration')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--scraping', action='store_true', help='Scraping + toute la suite')
    group.add_argument('--analyse', action='store_true', help='Analyse + extraction + recommandations')
    group.add_argument('--extraction', action='store_true', help='Extraction + recommandations')
    group.add_argument('--recommandations', action='store_true', help='Recommandations uniquement')
    group.add_argument('--all', action='store_true', help='Pipeline complet')
    
    args = parser.parse_args()
    
    pipeline = PipelineOrchestrateur(args.config)
    
    if args.scraping:
        pipeline.scraping_et_suite()
    elif args.analyse:
        pipeline.analyse_et_suite()
    elif args.extraction:
        pipeline.extraction_et_suite()
    elif args.recommandations:
        pipeline.recommandations()
    elif args.all:
        pipeline.pipeline_complet()

if __name__ == "__main__":
    main()