#!/usr/bin/env python3
import os
import sys
import yaml
import shutil
import argparse
import re
from pathlib import Path

import logging
from Logging import setup_logging

logger = setup_logging(logger=logging.getLogger(__name__), level = logging.DEBUG)

def load_yaml(filepath):
    """YAML-Datei laden."""
    with open(filepath, 'r') as f:
        result = yaml.safe_load(f)
    logger.info(f"Yaml loaded from {filepath} seuccesssfully")
    return result

def update_default_systematics_in_file(filepath, new_systematics):
    """
    Nur default_systematics in einer YAML-Datei überschreiben,
    ohne das Format des Restes zu ändern.
    """
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Finde den default_systematics Abschnitt
    # Pattern: "default_systematics:" gefolgt von beliebigem Text bis zum nächsten Top-Level Key
    pattern = r'^(default_systematics:\s*&defsyst?\s*)(.*?)(?=^\S|\Z)'
    
    # Versuche zuerst mit Anchor (&defsyst)
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    
    if match:
        # Ersetze den gesamten default_systematics Abschnitt
        indent = len(match.group(1)) - len(match.group(1).lstrip())
        
        # Erstelle neuen default_systematics Inhalt mit Anchor
        new_content = "default_systematics: &defsyst\n"
        
        # Füge die neuen Systematics ein (mit korrekter Einrückung)
        lines = yaml.dump(new_systematics, default_flow_style=False, sort_keys=False).split('\n')
        for line in lines:
            if line:
                new_content += " " * 2 + line + "\n"
            else:
                new_content += "\n"
        
        # Ersetze den alten Abschnitt
        new_full_content = content[:match.start()] + new_content + content[match.end():]
    else:
        # Fallback: Einfache Suche ohne Anchor
        pattern2 = r'^(default_systematics:\s*)(.*?)(?=^\S|\Z)'
        match = re.search(pattern2, content, re.MULTILINE | re.DOTALL)
        
        if not match:
            print(f"WARNUNG: default_systematics nicht gefunden in {filepath}")
            return False
        
        # Erstelle neuen default_systematics Inhalt
        indent = len(match.group(1)) - len(match.group(1).lstrip())
        new_content = "default_systematics:\n"
        
        # Füge die neuen Systematics ein (mit korrekter Einrückung)
        lines = yaml.dump(new_systematics, default_flow_style=False, sort_keys=False).split('\n')
        for line in lines:
            if line:
                new_content += " " * 2 + line + "\n"
            else:
                new_content += "\n"
        
        # Ersetze den alten Abschnitt
        new_full_content = content[:match.start()] + new_content + content[match.end():]
    
    # Schreibe die modifizierte Datei zurück
    with open(filepath, 'w') as f:
        f.write(new_full_content)
    
    return True

def update_default_systematics(target_yaml_path, runs_yaml_path, run_name=None):
    """
    Überschreibe default_systematics in target_yaml mit systematics aus runs_yaml.
    """
    # 1. Lade die Runs-Konfiguration
    runs_data = load_yaml(runs_yaml_path)
    
    if "runs" not in runs_data:
        print("FEHLER: Die Runs-YAML muss einen 'runs:' Abschnitt haben!")
        sys.exit(1)
    
    runs = runs_data["runs"]
    
    # 2. Bestimme welcher Run verwendet werden soll
    if run_name:
        if run_name not in runs:
            print(f"FEHLER: Run '{run_name}' nicht in Runs-YAML gefunden!")
            print(f"Verfügbare Runs: {list(runs.keys())}")
            sys.exit(1)
        selected_run = run_name
    else:
        # Verwende den ersten Run
        selected_run = list(runs.keys())[0]
        print(f"Kein spezifischer Run angegeben, verwende '{selected_run}'")
    
    # 3. Hole die Systematics für den ausgewählten Run
    run_config = runs[selected_run]
    
    if "systematics" not in run_config:
        print(f"FEHLER: Run '{selected_run}' hat keinen 'systematics:' Abschnitt!")
        sys.exit(1)
    
    new_systematics = run_config["systematics"]
    
    # 4. Überschreibe nur default_systematics (ohne Format zu ändern)
    success = update_default_systematics_in_file(target_yaml_path, new_systematics)
    
    if success:
        print(f"✓ default_systematics in '{target_yaml_path}' mit Konfiguration von '{selected_run}' überschrieben")
        return selected_run
    else:
        print(f"✗ Fehler beim Überschreiben von default_systematics in '{target_yaml_path}'")
        return None

def process_all_runs(target_yaml_path, runs_yaml_path):
    """
    Verarbeite alle Runs sequentiell.
    """
    # Lade Runs-Konfiguration
    runs_data = load_yaml(runs_yaml_path)
    
    if "runs" not in runs_data:
        print("FEHLER: Die Runs-YAML muss einen 'runs:' Abschnitt haben!")
        sys.exit(1)
    
    runs = runs_data["runs"]
    run_names = list(runs.keys())
    
    print(f"Gefundene Runs in '{runs_yaml_path}': {run_names}")
    
    # Lade Originalinhalt für Backup
    with open(target_yaml_path, 'r') as f:
        original_content = f.read()
    
    # Backup der Original-YAML
    backup_path = target_yaml_path + ".backup"
    if not os.path.exists(backup_path):
        with open(backup_path, 'w') as f:
            f.write(original_content)
        print(f"✓ Backup der Original-YAML erstellt: {backup_path}")
    
    processed_runs = []
    
    # Verarbeite jeden Run
    for i, run_name in enumerate(run_names):
        print("\n" + "="*60)
        print(f"Verarbeite Run {i+1}/{len(run_names)}: '{run_name}'")
        print("="*60)
        
        # 1. Setze YAML auf Original zurück
        with open(target_yaml_path, 'w') as f:
            f.write(original_content)
        print(f"✓ YAML auf Originalzustand zurückgesetzt")
        
        # 2. Hole Run-Konfiguration
        run_config = runs[run_name]
        
        if "systematics" not in run_config:
            print(f"WARNUNG: Run '{run_name}' hat keinen 'systematics:' Abschnitt, überspringe...")
            continue
        
        new_systematics = run_config["systematics"]
        
        # 3. Überschreibe default_systematics
        success = update_default_systematics_in_file(target_yaml_path, new_systematics)
        
        if success:
            print(f"✓ default_systematics mit Konfiguration von '{run_name}' überschrieben")
            processed_runs.append(run_name)
            
            # Hier würde das Bash-Skript aufgerufen werden
            print(f"✓ YAML bereit für Run '{run_name}'")
            print(f"  Führen Sie nun Ihr Bash-Skript aus...")
        else:
            print(f"✗ Fehler bei Run '{run_name}'")
    
    # Setze am Ende auf Original zurück
    print("\n" + "="*60)
    print("Alle Runs verarbeitet - setze YAML auf Original zurück")
    print("="*60)
    with open(target_yaml_path, 'w') as f:
        f.write(original_content)
    print("✓ YAML auf Originalzustand zurückgesetzt")
    
    return processed_runs

def main():
    parser = argparse.ArgumentParser(
        description="Überschreibt default_systematics in einer YAML-Datei mit Systematics aus einer Runs-YAML."
    )

    # --list-runs zuerst, da es independent ist
    parser.add_argument(
        "--list-runs",
        action="store_true",
        help="Liste alle verfügbaren Runs auf und beende"
    )

    # --runs-yaml ist immer erforderlich
    parser.add_argument(
        "--runs-yaml", 
        required=True,
        help="Pfad zur Runs-YAML-Datei mit den Run-Konfigurationen"
    )

    # --target-yaml nur erforderlich, wenn kein --list-runs
    parser.add_argument(
        "--target-yaml",
        help="Pfad zur YAML-Datei, deren default_systematics überschrieben werden soll"
    )

    parser.add_argument(
        "--run",
        help="Name eines spezifischen Runs (z.B. 'run1'). Wenn nicht angegeben, werden alle Runs verarbeitet."
    )

    args = parser.parse_args()

    # Prüfen, ob target-yaml fehlt, aber list-runs nicht gesetzt ist
    if not args.list_runs and not args.target_yaml:
        parser.error("--target-yaml ist erforderlich, wenn --list-runs nicht gesetzt ist")
    
    # Prüfe ob Dateien existieren
    if not args.list_runs:
        if not os.path.exists(args.target_yaml):
            print(f"FEHLER: Target-YAML '{args.target_yaml}' nicht gefunden!")
            sys.exit(1)
    
    if not os.path.exists(args.runs_yaml):
        print(f"FEHLER: Runs-YAML '{args.runs_yaml}' nicht gefunden!")
        sys.exit(1)
    
    # Option: Nur Runs auflisten
    if args.list_runs:
        runs_data = load_yaml(args.runs_yaml)
        if "runs" in runs_data:
            print("Verfügbare Runs:")
            for run_name in runs_data["runs"].keys():
                print(f"  - {run_name}")
        else:
            print("Keine Runs in der YAML-Datei gefunden!")
        sys.exit(0)
    
    # Option: Bestimmten Run verarbeiten
    if args.run:
        selected_run = update_default_systematics(
            args.target_yaml, 
            args.runs_yaml, 
            args.run
        )
        if selected_run:
            print(f"\nRun '{selected_run}' wurde auf '{args.target_yaml}' angewendet.")
            print("Nur default_systematics wurde geändert, der Rest der Datei bleibt unverändert.")
        
    # Option: Alle Runs sequentiell verarbeiten
    else:
        print("Verarbeite alle Runs sequentiell...")
        processed = process_all_runs(args.target_yaml, args.runs_yaml)
        print(f"\nVerarbeitete Runs: {processed}")

if __name__ == "__main__":
    main()