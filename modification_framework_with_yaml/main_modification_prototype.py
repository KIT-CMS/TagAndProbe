#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
import tempfile
import yaml
import re
import json
import copy


# ============================================================
# Hilfsfunktionen für Binning-Modifikationen
# ============================================================

def shift_bins(original, percentage, direction, idx_range=None):
    """
    Verschiebt Bin-Grenzen mit Sicherheitsprüfungen.
    """
    if len(original) < 3:
        print(f"    WARNUNG: Zu wenige Bin-Grenzen ({len(original)}), überspringe...")
        return original.copy()

    new_bins = original.copy()

    # Bereichslogik
    if idx_range is None:
        start = 1
        end = len(original) - 2  # -2 weil wir i+1 benötigen
    else:
        start = max(1, idx_range[0] + 1)
        end = min(len(original) - 2, idx_range[1] - 1)
        if start > end:
            print(f"    WARNUNG: Ungültiger Indexbereich, überspringe...")
            return original.copy()

    print(f"    Verschiebe Bins von Index {start} bis {end}")

    for i in range(start, end + 1):
        # Sicherstellen dass wir nicht die äußersten Grenzen verschieben
        if i == 0 or i >= len(original) - 1:
            continue
            
        width = original[i] - original[i - 1]
        shift = width * (percentage / 100.0)

        if direction == "up":
            new_value = original[i] + shift
        else:
            new_value = original[i] - shift

        # Sicherheitsgrenzen
        min_value = original[i - 1] + 0.001
        if i < len(original) - 1:
            max_value = original[i + 1] - 0.001
            new_value = min(new_value, max_value)
        
        new_value = max(new_value, min_value)

        new_bins[i] = new_value
        print(f"      Bin {i}: {original[i]:.2f} -> {new_value:.2f}")

    return new_bins


# ============================================================
# Variable-Änderungen (variable_variation)
# ============================================================

def apply_variable_variation_in_expr(expr, variable, delta, direction):
    """
    Sucht im Ausdruck nach `variable < number` oder `variable > number`
    und verändert die Zahl um ±delta.
    """
    import re

    # Pattern für Vergleiche
    pattern = rf"({re.escape(variable)}\s*[<>]=?\s*)([-+]?[0-9]*\.?[0-9]+)"

    def repl(match):
        prefix = match.group(1)
        value = float(match.group(2))
        if direction == "up":
            value = value + delta
        else:
            value = value - delta
        return f"{prefix}{value}"

    new_expr = re.sub(pattern, repl, expr)
    return new_expr


def apply_variable_variations(entry_dict, variations):
    """
    variations = {"iso_tag": ("up", 0.1), "abs(dz_tag)": ("down", 0.3)}
    """
    expr_fields = ["tag", "probe", "var", "binvar_x", "binvar_y"]

    for variable, (direction, delta) in variations.items():
        for field in expr_fields:
            if field in entry_dict and isinstance(entry_dict[field], str):
                old_value = entry_dict[field]
                new_value = apply_variable_variation_in_expr(
                    old_value,
                    variable,
                    delta,
                    direction
                )
                if old_value != new_value:
                    print(f"    Geändert {variable} in {field}: {old_value} -> {new_value}")
                    entry_dict[field] = new_value

def apply_anchors(yaml_dict):
    """
    Fügt Anchors für systematics ein, sodass mehrere Entries dieselbe Referenz benutzen.
    """
    # Sammle systematics, die als Anchor genutzt werden sollen
    anchors = {}

    for key, entry in yaml_dict.items():
        if not isinstance(entry, dict):
            continue

        if key == "default_systematics":
            continue

        syst = entry.get("systematics")
        if syst is None:
            continue

        # Erzeuge Anchor-Referenz, falls noch nicht vorhanden
        syst_key = json.dumps(syst, sort_keys=True)
        if syst_key not in anchors:
            anchors[syst_key] = copy.deepcopy(syst)
        else:
            # Ersetze systematics durch Referenz auf Anchor
            entry["systematics"] = anchors[syst_key]

    return yaml_dict

# ============================================================
# Systematics in YAML auslesen und anwenden
# ============================================================

def parse_binning_variations(syst_dict):
    out = {}

    if "binning_variation" not in syst_dict:
        return out

    # Zwei Patterns: mit und ohne Index-Bereich
    pattern_simple = r"^([0-9]*\.?[0-9]+)(up|down)$"
    pattern_with_idx = r"^([0-9]*\.?[0-9]+)(up|down)\(([0-9]+),([0-9]+)\)$"

    for axis, spec in syst_dict["binning_variation"].items():
        spec_clean = str(spec).replace(" ", "")
        
        m_simple = re.match(pattern_simple, spec_clean)
        m_with_idx = re.match(pattern_with_idx, spec_clean)
        
        if m_simple:
            value_str, direction = m_simple.groups()
            percentage = float(value_str) * 100.0
            idx_range = None
            print(f"    Binning variation: {axis} {direction} {percentage}%")
            
        elif m_with_idx:
            value_str, direction, idx1, idx2 = m_with_idx.groups()
            percentage = float(value_str) * 100.0
            idx_range = (int(idx1), int(idx2))
            print(f"    Binning variation: {axis} {direction} {percentage}% range {idx_range}")
        else:
            print(f"    WARNUNG: Ungültige binning_variation-Spezifikation: {spec}")
            continue

        out[axis] = (direction, percentage, idx_range)

    return out


def parse_variable_variations(syst_dict):
    """
    Erwartet:
      variable_variation:
        iso_tag: 0.1up
        abs(dz_tag): 0.3down
    """
    out = {}

    if "variable_variation" not in syst_dict:
        return out

    pattern = r"^([0-9]*\.?[0-9]+)(up|down)$"

    for var, spec in syst_dict["variable_variation"].items():
        spec_clean = str(spec).replace(" ", "")
        m = re.match(pattern, spec_clean)
        if m:
            value_str, direction = m.groups()
            delta = float(value_str)
            out[var] = (direction, delta)
            print(f"    Variable variation: {var} {direction} {delta}")
        else:
            print(f"    WARNUNG: Ungültige variable_variation-Spezifikation: {spec}")

    return out


def apply_syst_to_yaml(yaml_dict):
    """
    Wendet systematics auf YAML-Dictionary an (rekursiv).
    """
    found_any = False
    
    for key, entry in yaml_dict.items():
        if not isinstance(entry, dict):
            continue
            
        # Prüfe ob dieser Eintrag systematics hat
        if "systematics" in entry:
            found_any = True
            print(f"  Systematics gefunden in {key}, wende an...")
            
            syst = entry["systematics"]
            
            # 1. Binning variations
            binning_var = parse_binning_variations(syst)
            
            # apply binning variations
            for axis, (direction, perc, idx_range) in binning_var.items():
                if axis in ["pt", "pteta"] and "bins_x" in entry:
                    old_bins = entry["bins_x"]
                    print(f"    Original bins_x: {[round(x, 2) for x in old_bins]}")
                    new_bins = shift_bins(old_bins, perc, direction, idx_range)
                    entry["bins_x"] = new_bins
                    print(f"    Geändert bins_x: {[round(x, 2) for x in old_bins]} -> {[round(x, 2) for x in new_bins]}")
                    
                if axis in ["eta", "pteta"] and "bins_y" in entry:
                    old_bins = entry["bins_y"]
                    print(f"    Original bins_y: {[round(x, 2) for x in old_bins]}")
                    new_bins = shift_bins(old_bins, perc, direction, idx_range)
                    entry["bins_y"] = new_bins
                    print(f"    Geändert bins_y: {[round(x, 2) for x in old_bins]} -> {[round(x, 2) for x in new_bins]}")

            # 2. Variable variations
            variable_var = parse_variable_variations(syst)
            apply_variable_variations(entry, variable_var)
        
        # Rekursiv in verschachtelten Einträgen suchen
        else:
            # Prüfe ob dieser Eintrag weitere verschachtelte Dicts enthält
            has_nested_dicts = any(isinstance(v, dict) for v in entry.values())
            if has_nested_dicts:
                # Rekursiver Aufruf für verschachtelte Einträge
                found_in_nested = apply_syst_to_yaml(entry)
                found_any = found_any or found_in_nested

    if not found_any:
        print("  Keine Systematics gefunden")
    
    return yaml_dict


# ============================================================
# Prozesslogik
# ============================================================

def process_all(path, eras, channels, restore=False):
    print(f"Suche YAML-Dateien in: {path}")
    print(f"Eras: {eras}")
    print(f"Channels: {channels}")

    yaml_files = []

    for root, _, files in os.walk(path):
        for f in files:
            if not f.endswith(".yaml"):
                continue
            if f.endswith("_original.yaml"):
                continue

            full_path = os.path.join(root, f)
            matches_era = any(e in f for e in eras)
            matches_ch = any(c in f for c in channels)

            print(f"  Gefunden: {f} -> Era: {matches_era}, Channel: {matches_ch}")
            
            if matches_era and matches_ch:
                yaml_files.append(full_path)
                print(f"    → WIRD VERARBEITET")

    if not yaml_files:
        raise FileNotFoundError("Keine passenden YAML-Dateien gefunden.")

    print(f"\nGefundene Dateien zur Verarbeitung: {len(yaml_files)}")
    for f in yaml_files:
        print(f"  - {f}")

    if restore:
        restored = 0
        for f in yaml_files:
            base, ext = os.path.splitext(f)
            backup = base + "_original.yaml"
            if os.path.exists(backup):
                os.remove(f)
                shutil.move(backup, f)
                restored += 1
                print(f"Wiederhergestellt: {f}")
        print(f"Wiederherstellung abgeschlossen: {restored}/{len(yaml_files)}")
        return

    # Normalmodus
    with tempfile.TemporaryDirectory() as tmp:
        mapping = []
        for orig in yaml_files:
            rel = os.path.relpath(orig, path)
            tmp_path = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
            shutil.copy2(orig, tmp_path)
            mapping.append((orig, tmp_path))

        # Bearbeitung im Tempdir
        for orig, tmp_path in mapping:
            print(f"\nBearbeite {os.path.basename(orig)}...")
            with open(tmp_path) as f:
                data = yaml.safe_load(f)
            for key, cfg in data.items():
                if isinstance(cfg, dict):
                    print(f"DEBUG: {key} keys: {list(cfg.keys())}")
                else:
                    print(f"DEBUG: {key} ist kein dict, type={type(cfg)}")

            if data is None:
                raise ValueError(f"YAML {orig} konnte nicht geladen werden.")

            new_data = apply_syst_to_yaml(data)
            new_data = apply_anchors(new_data)

            # in Tempdatei zurückschreiben
            with open(tmp_path, "w") as f:
                yaml.dump(new_data, f, sort_keys=False, default_flow_style=False)

        # Änderungen übernehmen + Backups erstellen
        for orig, tmp_path in mapping:
            base, ext = os.path.splitext(orig)
            backup = base + "_original.yaml"

            if not os.path.exists(backup):
                print(f"Erstelle Backup: {backup}")
                shutil.copy2(orig, backup)

            print(f"Kopiere modifizierte Datei: {tmp_path} -> {orig}")
            shutil.copy2(tmp_path, orig)

    print("\nModifikationen abgeschlossen.")


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="YAML-basierte Modifikationen für Systematics.")
    parser.add_argument("--path", required=True, help="Pfad wo YAML-Dateien gesucht werden")
    parser.add_argument("--eras", nargs="+", required=True, help="Eras die verarbeitet werden (z.B. 2018UL 2017UL)")
    parser.add_argument("--channels", nargs="+", required=True, help="Channels die verarbeitet werden (z.B. muon electron)")
    parser.add_argument("--restore", action="store_true", help="Originaldateien wiederherstellen")

    args = parser.parse_args()

    try:
        process_all(
            path=args.path,
            eras=args.eras,
            channels=args.channels,
            restore=args.restore,
        )
    except Exception as e:
        sys.stderr.write(f"Fehler: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()