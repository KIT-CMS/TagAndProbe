#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
import tempfile
import importlib
import json


# ======================================================
# Hauptprozess: sichere Verarbeitung mit Modulimport
# ======================================================

def process_all(base_dir, eras, channels, modification_module, mod_args, restore_mode=False):
    """
    Führt eine beliebige Änderungsoperation auf alle passenden YAML-Dateien aus.
    - base_dir: Hauptverzeichnis mit den YAMLs
    - eras: Liste der Eras (Filter)
    - channels: Liste der Channels (Filter)
    - modification_module: Name des Änderungsmoduls (z. B. "modify_iso")
    - mod_args: Dictionary mit Argumenten für apply_change()
    - restore_mode: Wenn True, werden Backups wiederhergestellt
    """

    # 1. Modul laden
    try:
        mod = importlib.import_module(f"modifications.{modification_module}")
    except ModuleNotFoundError:
        raise ImportError(f"Änderungsmodul '{modification_module}' wurde nicht gefunden "
                          f"(erwarte Datei: modifications/{modification_module}.py).")

    if not hasattr(mod, "apply_change"):
        raise AttributeError(f"Das Modul '{modification_module}' enthält keine Funktion 'apply_change'.")

    print(f"Verwende Änderungsmodul: {modification_module}")
    print(f"Mit Argumenten: {mod_args}\n")

    # 2. Pfad prüfen
    if not os.path.exists(base_dir):
        raise FileNotFoundError(f"Der angegebene Pfad '{base_dir}' existiert nicht.")

    matched_files = []

    # 3. Dateien finden
    for root, _, files in os.walk(base_dir):
        for file in files:
            if not file.endswith(".yaml"):
                continue
            if file.endswith("_original.yaml"):
                continue
            if "xpog" in file.lower() or "double" in file.lower():
                continue

            matching_eras = [era for era in eras if era in file]
            matching_channels = [ch for ch in channels if ch in file]

            if matching_eras and matching_channels:
                matched_files.append(os.path.join(root, file))

    if not matched_files:
        raise FileNotFoundError("Keine passenden YAML-Dateien gefunden.")

    print(f"Gefundene Dateien ({len(matched_files)}):")
    for f in matched_files:
        print(f"  {f}")
    print()

    # 4. RESTORE-MODUS
    if restore_mode:
        restored = 0
        for f in matched_files:
            dirname, fname = os.path.split(f)
            base, ext = os.path.splitext(fname)
            backup_path = os.path.join(dirname, f"{base}_original{ext}")

            if os.path.exists(backup_path):
                os.remove(f)
                shutil.move(backup_path, f)
                restored += 1

        print(f"Restore abgeschlossen ({restored}/{len(matched_files)} Dateien).")
        return

    # 5. Normalmodus – sichere Bearbeitung im temporären Verzeichnis
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_mapping = []

        try:
            # 5a. Dateien ins tempdir kopieren
            for orig_path in matched_files:
                rel_path = os.path.relpath(orig_path, base_dir)
                tmp_path = os.path.join(tmpdir, rel_path)
                os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
                shutil.copy2(orig_path, tmp_path)
                tmp_mapping.append((orig_path, tmp_path))

            # 5b. Änderung im tempdir anwenden
            for _, tmp_path in tmp_mapping:
                print(f"Wende Änderung auf {os.path.basename(tmp_path)} an ...")
                mod.apply_change(tmp_path, **mod_args)

            # 5c. Backups anlegen & Änderungen übernehmen
            for orig_path, tmp_path in tmp_mapping:
                dirname, fname = os.path.split(orig_path)
                base, ext = os.path.splitext(fname)
                backup_path = os.path.join(dirname, f"{base}_original{ext}")

                if not os.path.exists(backup_path):
                    shutil.copy2(orig_path, backup_path)

                shutil.copy2(tmp_path, orig_path)

        except Exception as e:
            raise RuntimeError(f"Fehler während der Verarbeitung: {e}")

    print("\nVerarbeitung erfolgreich abgeschlossen.")
    print(f"Anzahl bearbeiteter Dateien: {len(matched_files)}")


# ======================================================
# Argumente & Hauptaufruf
# ======================================================

def main():
    parser = argparse.ArgumentParser(
        description="Allgemeines Framework zum Anwenden beliebiger YAML-Modifikationen mit Backup/Restore."
    )
    parser.add_argument("--path", required=True, help="Pfad zum Hauptordner (rekursiv durchsucht).")
    parser.add_argument("--eras", nargs="+", required=True, help="Liste der Eras, z. B. 2017UL 2016preVFPUL.")
    parser.add_argument("--channels", nargs="+", required=True, help="Liste der Channels, z. B. muon electron.")
    parser.add_argument("--modification", required=True, help="Name des Moduls in modifications/, z. B. modify_iso.")
    parser.add_argument("--args", type=str, default="{}", help="JSON-String mit Argumenten für apply_change(), z. B. '{\"percentage\":10, \"variation\":\"up\"}'.")
    parser.add_argument("--restore", action="store_true", help="Alle Originaldateien wiederherstellen (löscht geänderte Dateien).")

    args = parser.parse_args()

    try:
        mod_args = json.loads(args.args)
        if not isinstance(mod_args, dict):
            raise ValueError("--args muss ein JSON-Dictionary sein.")
    except json.JSONDecodeError:
        raise ValueError("Ungültiger JSON-String in --args.")

    try:
        process_all(
            base_dir=args.path,
            eras=args.eras,
            channels=args.channels,
            modification_module=args.modification,
            mod_args=mod_args,
            restore_mode=args.restore,
        )
    except Exception as e:
        sys.stderr.write(f"\n[FEHLER] {e}\n")
        sys.exit(1)

main()
