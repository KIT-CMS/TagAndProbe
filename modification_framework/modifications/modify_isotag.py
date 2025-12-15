import os
import re
import shutil

# ======================================================
# Hilfsfunktion: iso_tag in einer Zeile anpassen
# ======================================================
def modify_iso_tag_line(line, percentage, variation):
    """
    Sucht in einer Zeile nach (iso_tag < X) und ändert X um den angegebenen Prozentsatz.
    """
    pattern = r"\(iso_tag\s*<\s*([0-9]*\.?[0-9]+)\)"
    match = re.search(pattern, line)
    if not match:
        return line  # keine Änderung nötig

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


# ======================================================
# Hauptfunktion zum Anwenden der Iso-Variation
# ======================================================
def apply_iso_variation(file_path, percentage=10, variation="up"):
    """
    Lädt YAML-Datei, ändert iso_tag-Schwellen in tag-Blöcken.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Datei {file_path} existiert nicht.")

    with open(file_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    inside_tag = False
    for line in lines:
        # Beginn eines tag-Blocks erkennen
        if re.match(r"^\s*tag\s*:", line):
            inside_tag = True
        elif inside_tag and re.match(r"^\s*\w+\s*:", line):
            # Ende des tag-Blocks
            inside_tag = False

        if inside_tag:
            line = modify_iso_tag_line(line, percentage, variation)

        new_lines.append(line)

    with open(file_path, "w") as f:
        f.writelines(new_lines)

    print(f"Datei {file_path} erfolgreich angepasst.")


# ======================================================
# Zentrale apply_change-Funktion für das Main-Skript
# ======================================================
def apply_change(file_path, percentage=10, variation="up", restore=False):
    """
    Backup/Restore-Mechanismus + iso_tag-Änderung.
    Wird vom main_modification.py Framework aufgerufen.
    """
    dirname, fname = os.path.split(file_path)
    base, ext = os.path.splitext(fname)
    backup_path = os.path.join(dirname, f"{base}_original{ext}")

    if restore:
        if os.path.exists(backup_path):
            os.remove(file_path)
            shutil.move(backup_path, file_path)
            print(f"Backup wiederhergestellt: {fname}")
        else:
            print(f"Kein Backup zum Wiederherstellen gefunden für {fname}")
        return

    # Backup anlegen, falls nicht vorhanden
    if not os.path.exists(backup_path):
        shutil.copy2(file_path, backup_path)
        print(f"Backup erstellt: {fname}")

    # Iso-Variation anwenden
    apply_iso_variation(file_path, percentage=percentage, variation=variation)
