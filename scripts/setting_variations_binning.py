#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
import tempfile
from binning_variations import apply_percentage_bin_variation_2d

# ======================================================
# Hilfsfunktion: Binning anwenden (nur im temp dir)
# ======================================================

def apply_binning(file_path, percentage, variation, axis):
    """Wendet Binning-Variation auf eine Datei an."""
    apply_percentage_bin_variation_2d(
        bin_cfgs=None,
        percentage=percentage,
        variation=variation,
        axis=axis,
        file=file_path,
    )


# ======================================================
# Hauptprozess: Sicheres Arbeiten mit temporärem Verzeichnis
# ======================================================

def process_all(base_dir, eras, channels, with_binning, percentage, variation, axis, restore_mode=False):
    if not os.path.exists(base_dir):
        raise FileNotFoundError(f"Der angegebene Pfad '{base_dir}' existiert nicht.")

    print(f"Suche nach Dateien in: {base_dir}")
    print(f"Eras: {eras}")
    print(f"Channels: {channels}\n")

    matched_files = []

    # === 1. Dateien finden ===
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
                full_path = os.path.join(root, file)
                matched_files.append(full_path)

    # === 2. Validierung: Eras und Dateien prüfen ===
    if not matched_files:
        raise FileNotFoundError("Keine passenden YAML-Dateien gefunden.")

    found_eras = {era for f in matched_files for era in eras if era in f}
    missing_eras = [era for era in eras if era not in found_eras]
    if missing_eras:
        raise ValueError(
            f"Keine Dateien gefunden für folgende Eras: {', '.join(missing_eras)}. "
            "Abbruch – keine Änderungen vorgenommen."
        )

    print(f"Gefundene Dateien ({len(matched_files)}):")
    for f in matched_files:
        print(f"  {f}")
    print()

    # === 3. RESTORE-MODUS ===
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

    # === 4. Normaler Modus: sichere Verarbeitung mit temporärem Verzeichnis ===
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_mapping = []

        try:
            # 4a. Dateien ins tempdir kopieren
            for orig_path in matched_files:
                rel_path = os.path.relpath(orig_path, base_dir)
                tmp_path = os.path.join(tmpdir, rel_path)
                os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
                shutil.copy2(orig_path, tmp_path)
                tmp_mapping.append((orig_path, tmp_path))

            # 4b. Änderungen nur im tempdir durchführen
            if with_binning:
                print("Wende Binning-Variationen im temporären Bereich an...")
                for _, tmp_path in tmp_mapping:
                    fname = os.path.basename(tmp_path)
                    print(f"  → {fname} ({variation}, {axis}, {percentage}%)")
                    apply_binning(tmp_path, percentage, variation, axis)

            # 4c. Backups anlegen & Änderungen übernehmen
            for orig_path, tmp_path in tmp_mapping:
                dirname, fname = os.path.split(orig_path)
                base, ext = os.path.splitext(fname)
                backup_path = os.path.join(dirname, f"{base}_original{ext}")

                if not os.path.exists(backup_path):
                    shutil.copy2(orig_path, backup_path)

                shutil.copy2(tmp_path, orig_path)

        except Exception as e:
            # tempfile wird automatisch gelöscht
            raise RuntimeError(f"Fehler während der Binning-Verarbeitung: {e}")

    print("\nVerarbeitung erfolgreich abgeschlossen.")
    print(f"Anzahl bearbeiteter Dateien: {len(matched_files)}")


# ======================================================
# Argumente & Hauptaufruf
# ======================================================

def main():
    parser = argparse.ArgumentParser(
        description="Führt Binning-Variationen atomar auf YAML-Dateien aus (mit Backup/Restore)."
    )
    parser.add_argument("--path", required=True, help="Pfad zum Hauptordner (rekursiv durchsucht).")
    parser.add_argument("--eras", nargs="+", required=True, help="Liste der Eras, z. B. --eras 2017UL 2016preVFPUL")
    parser.add_argument("--channels", nargs="+", required=True, help="Liste der Channels, z. B. --channels muon embeddingselection")
    parser.add_argument("--with-binning", action="store_true", help="Binning-Variation anwenden")
    parser.add_argument("--percentage", type=float, default=10, help="Prozentuale Änderung (Standard: 10)")
    parser.add_argument("--variation", choices=["up", "down"], default="up", help="Richtung der Variation (Standard: up)")
    parser.add_argument("--axis", choices=["pt", "eta", "pteta"], default="pteta", help="Achse der Variation (Standard: pteta)")
    parser.add_argument("--restore", action="store_true", help="Alle Originaldateien wiederherstellen (löscht geänderte Dateien)")

    args = parser.parse_args()

    try:
        process_all(
            base_dir=args.path,
            eras=args.eras,
            channels=args.channels,
            with_binning=args.with_binning,
            percentage=args.percentage,
            variation=args.variation,
            axis=args.axis,
            restore_mode=args.restore,
        )
    except Exception as e:
        sys.stderr.write(f"\n[FEHLER] {e}\n")
        sys.exit(1)

main()
