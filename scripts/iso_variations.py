import os
import re
import sys
import shutil
import argparse

def modify_iso_tag_line(line, percentage, variation):
    """
    Sucht in einer Zeile nach (iso_tag < X) und ändert X um den angegebenen Prozentsatz.
    Beispiel: (iso_tag < 0.15) -> (iso_tag < 0.165) bei +10%
    """
    pattern = r"\(iso_tag\s*<\s*([0-9]*\.?[0-9]+)\)"
    match = re.search(pattern, line)
    if not match:
        return line  # keine Änderung, falls kein iso_tag gefunden

    value = float(match.group(1))
    if variation == "up":
        new_value = value * (1 + percentage / 100.0)
    elif variation == "down":
        new_value = value * (1 - percentage / 100.0)
    else:
        raise ValueError("Variation muss 'up' oder 'down' sein.")

    new_line = re.sub(pattern, f"(iso_tag < {new_value:.4f})", line)
    print(f"iso_tag Schwelle geändert: {value:.4f} -> {new_value:.4f}")
    return new_line


def apply_iso_variation(file_path, percentage, variation):
    """
    Lädt YAML-Datei, ändert iso_tag-Schwelle in tag-Zeilen, überschreibt Datei.
    """
    if not os.path.isfile(file_path):
        print(f"Fehler: Datei {file_path} existiert nicht.")
        return

    with open(file_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    inside_tag = False
    for line in lines:
        # erkennen, wann wir im "tag:"-Block sind
        if re.match(r"^\s*tag\s*:", line):
            inside_tag = True
        elif inside_tag and re.match(r"^\s*\w+\s*:", line):
            # Ende des tag-Blocks, z.B. bei 'probe:' oder 'binvar_x:'
            inside_tag = False

        if inside_tag:
            line = modify_iso_tag_line(line, percentage, variation)

        new_lines.append(line)

    with open(file_path, "w") as f:
        f.writelines(new_lines)

    print(f"Datei {file_path} erfolgreich angepasst.")


def toggle_file(path, with_iso=False, percentage=10, variation="up"):
    """
    Wie dein ursprüngliches toggle_file, aber für iso_tag-Änderungen.
    """
    if not os.path.isfile(path):
        print(f"Fehler: Datei {path} existiert nicht.")
        return

    dirname, fname = os.path.split(path)
    base, ext = os.path.splitext(fname)
    backup_name = f"{base}_original{ext}"
    backup_path = os.path.join(dirname, backup_name)

    if os.path.exists(backup_path):
        # Backup existiert -> wiederherstellen
        os.remove(path)
        shutil.move(backup_path, path)
        print(f"Backup {backup_name} wurde wiederhergestellt als {fname}.")
    else:
        # Backup anlegen und optional Variation anwenden
        shutil.copy2(path, backup_path)
        print(f"Backup {backup_name} wurde erstellt.")

        if with_iso:
            print(f"Iso-Variation wird auf {fname} angewendet...")
            apply_iso_variation(
                file_path=path,
                percentage=percentage,
                variation=variation
            )
            print(f"Iso-Variation abgeschlossen ({variation}, {percentage}%).")


# === CLI ===

parser = argparse.ArgumentParser(description="Toggle YAML-Datei und optional iso_tag-Variation anwenden.")
parser.add_argument("filepath", help="Pfad zur YAML-Datei")
parser.add_argument("--with-iso", action="store_true", help="iso_tag-Variation anwenden")
parser.add_argument("--percentage", type=float, default=10, help="Prozentuale Änderung")
parser.add_argument("--variation", choices=["up", "down"], default="up", help="Richtung der Variation")

args = parser.parse_args()

toggle_file(
    args.filepath,
    with_iso=args.with_iso,
    percentage=args.percentage,
    variation=args.variation
)
