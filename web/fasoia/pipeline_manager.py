#!/usr/bin/env python
"""
Pipeline Manager - Version DGCMEF + UEMOA

Utilisation:
    python pipeline_manager.py --all             # Tout le cycle
    python pipeline_manager.py --uemoa           # Pipeline UEMOA seulement
    python pipeline_manager.py --dgcmef          # Pipeline DGCMEF seulement
    python pipeline_manager.py --recommandation  # Matching seulement
"""

import os
import sys
import django
import subprocess
import argparse
import json
from pathlib import Path

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fasoia.settings')
django.setup()

class PipelineManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.manage_py = self.project_root / 'manage.py'
        self.config_file = self.project_root / 'pipeline_config.json'
        self.config = self.charger_configuration()
        
    def charger_configuration(self):
        if not self.config_file.exists():
            print(f"❌ Fichier {self.config_file} introuvable!")
            sys.exit(1)
            
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def run_commande(self, cmd_config, description):
        print(f"\n  ⚡ {description}")
        
        if cmd_config['type'] == 'django':
            commande = f"python {self.manage_py} {cmd_config['commande']}"
        else:  # type python
            args = ' '.join(cmd_config.get('args', []))
            commande = f"python {cmd_config['chemin']} {args}"
        
        try:
            result = subprocess.run(
                commande,
                shell=True,
                check=True,
                text=True,
                capture_output=True
            )
            
            if result.stdout:
                print(f"  📄 {result.stdout[:200]}..." if len(result.stdout) > 200 else f"  📄 {result.stdout}")
            if result.stderr:
                print(f"  ⚠️  {result.stderr}")
            
            print(f"  ✅ Terminé")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Erreur: {e.stderr if e.stderr else str(e)}")
            return False
    
    def executer_etape(self, nom_etape):
        if nom_etape not in self.config['etapes']:
            print(f"❌ Étape inconnue: {nom_etape}")
            return False
        
        etape = self.config['etapes'][nom_etape]
        print(f"\n📌 ÉTAPE: {nom_etape.upper()}")
        print(f"   {etape['description']}")
        print(f"   {'='*40}")
        
        for i, cmd in enumerate(etape['commandes'], 1):
            if not self.run_commande(cmd, f"Commande {i}: {cmd.get('description', '')}"):
                if self.config['options']['stop_on_error']:
                    return False
        
        print(f"\n✅ Étape {nom_etape} terminée")
        return True
    
    def executer_pipeline(self, pipeline_name):
        if pipeline_name not in self.config['pipelines']:
            print(f"❌ Pipeline inconnu: {pipeline_name}")
            print(f"   Disponibles: {list(self.config['pipelines'].keys())}")
            return False
        
        pipeline = self.config['pipelines'][pipeline_name]
        print(f"\n🚀 PIPELINE: {pipeline_name.upper()}")
        print(f"   {pipeline['description']}")
        print(f"{'='*50}")
        
        etapes = pipeline['etapes']
        for i, etape in enumerate(etapes, 1):
            print(f"\n📋 Étape {i}/{len(etapes)}")
            if not self.executer_etape(etape):
                print(f"\n❌ Pipeline arrêté à l'étape {i}")
                return False
        
        print(f"\n🎉 Pipeline {pipeline_name} terminé avec succès!")
        return True

def main():
    manager = PipelineManager()
    
    parser = argparse.ArgumentParser(
        description='Pipeline Manager - UEMOA + DGCMEF',
        usage='python pipeline_manager.py [--all | --uemoa | --dgcmef | --recommandation]'
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true', help='Exécute tout le pipeline')
    group.add_argument('--uemoa', action='store_true', help='Exécute pipeline UEMOA seulement')
    group.add_argument('--dgcmef', action='store_true', help='Exécute pipeline DGCMEF seulement')
    group.add_argument('--recommandation', action='store_true', help='Exécute la recommandation seulement')
    
    args = parser.parse_args()
    
    if args.all:
        manager.executer_pipeline('all')
    elif args.uemoa:
        manager.executer_pipeline('uemoa')
    elif args.dgcmef:
        manager.executer_pipeline('dgcmef')
    elif args.recommandation:
        manager.executer_pipeline('recommandation_only')

if __name__ == '__main__':
    main()