#!/usr/bin/env python3
import os
import json
import re
from collections import defaultdict
import argparse

def find_json_files(base_dir, nominal_dir=None):
    """
    Durchsucht alle Unterordner von base_dir nach JSON-Dateien (keine .gz),
    und ordnet sie nach (channel, era).
    
    Args:
        base_dir: Pfad zu den Output-Ordnern
        nominal_dir: Optionaler Pfad zu einem spezifischen nominal Ordner
                    (muss nicht "nominal" im Namen haben)
    """
    grouped = defaultdict(list)
    
    # 1. ZUERST: nominal_dir verarbeiten (wenn angegeben)
    nominal_folder_name = None
    if nominal_dir and os.path.isdir(nominal_dir):
        print(f"Info: Verwende manuellen nominal-Ordner: {nominal_dir}")
        
        # Extrahiere channel und era aus dem Ordner-Namen
        folder_name = os.path.basename(nominal_dir.rstrip('/'))
        parts = folder_name.split('_')
        
        if len(parts) >= 3:
            # Finde die Era
            era_idx = -1
            for i, part in enumerate(parts):
                if "UL" in part or (len(part) == 4 and part.isdigit()):
                    era_idx = i
                    break
            
            if era_idx != -1:
                era = parts[era_idx]
                channel = parts[1] if len(parts) > 1 else "muon"
                
                # Merke den nominal Ordnernamen für später
                nominal_folder_name = folder_name
                
                # Suche nach jsons Ordner
                json_dir = os.path.join(nominal_dir, "jsons")
                if os.path.isdir(json_dir):
                    # Suche nach JSON-Datei
                    json_files = [f for f in os.listdir(json_dir) 
                                if f.endswith(".json") and not f.endswith(".json.gz")]
                    
                    if json_files:
                        json_path = os.path.join(json_dir, json_files[0])
                        grouped[(channel, era)].append(("nominal", json_path))
                        print(f"  Gefunden: nominal -> {json_path}")
                    else:
                        print(f"Warnung: Keine JSONs gefunden in {json_dir}")
                else:
                    print(f"Warnung: Kein jsons Ordner in {nominal_dir}")

    # 2. DANN: Alle anderen Ordner in base_dir durchsuchen
    for root, dirs, files in os.walk(base_dir):
        for folder in dirs:
            # Nur Ordner betrachten, die output_muon enthalten
            if not folder.startswith("output_muon_"):
                continue

            if "bestmodel" in folder.lower():
                continue
                
            full_path = os.path.join(root, folder)
            
            # Überspringe den nominal_dir wenn er manuell angegeben wurde
            if nominal_dir and os.path.exists(full_path):
                try:
                    if os.path.samefile(full_path, nominal_dir):
                        continue
                except:
                    pass

            # Ordner-Struktur parsen
            parts = folder.split("_")
            
            if len(parts) < 3:
                continue
            
            # Finde die Era
            era_idx = -1
            for i, part in enumerate(parts):
                if "UL" in part or (len(part) == 4 and part.isdigit()):
                    era_idx = i
                    break
            
            if era_idx == -1:
                continue
            
            era = parts[era_idx]
            channel = parts[1]  # "muon"
            
            # Bestimme den Variationsnamen
            # Alles nach der Era ist die Variation (bis zu bekannten Endungen)
            variation_parts = parts[era_idx+1:]
            
            # Entferne bekannte Endungen
            common_endings = ["abm", "bestmodel", "model", "variation", "test", "check"]
            while variation_parts and variation_parts[-1].lower() in common_endings:
                variation_parts = variation_parts[:-1]
            
            # WENN nominal_dir MANUELL ANGEGEBEN WURDE:
            # - Dann ist dieser Ordner "nominal", alle anderen sind Variationen
            # - Außer der Ordner hat selbst "nominal" im Namen
            if nominal_dir:
                # Wenn dieser Ordner "nominal" im Namen hat, ist es auch nominal
                if "nominal" in folder.lower():
                    mod = "nominal"
                else:
                    # Ansonsten ist es eine Variation
                    mod = "_".join(variation_parts) if variation_parts else "variation"
            else:
                # AUTOMATISCHE ERKENNUNG
                if not variation_parts or "nominal" in folder.lower():
                    mod = "nominal"
                else:
                    mod = "_".join(variation_parts)
            
            # Wenn wir schon einen nominal haben, überspringe weitere "nominal" Ordner
            if mod == "nominal":
                if any(name == "nominal" for name, _ in grouped.get((channel, era), [])):
                    print(f"Info: Überspringe zusätzlichen nominal Ordner: {folder}")
                    continue

            # Suche nach jsons Ordner
            json_dir = os.path.join(full_path, "jsons")
            if not os.path.isdir(json_dir):
                continue

            # Suche nach JSON-Datei
            json_files = [f for f in os.listdir(json_dir) 
                         if f.endswith(".json") and not f.endswith(".json.gz")]
            
            if not json_files:
                continue
                
            # Nimm die erste JSON-Datei
            json_path = os.path.join(json_dir, json_files[0])
            grouped[(channel, era)].append((mod, json_path))
            print(f"  Gefunden: {mod} -> {json_path}")

    return grouped

def merge_jsons(file_list):
    """
    Nimmt eine Liste von (mod_name, file_path) Tupeln,
    lädt alle JSONs und kombiniert sie in der richtigen Reihenfolge.
    """
    # nominal zuerst, dann alphabetisch
    sorted_files = sorted(file_list, key=lambda x: (x[0] != "nominal", x[0]))
    
    print(f"  Dateien in Reihenfolge: {[f[0] for f in sorted_files]}")

    # Nominal als Basis
    nominal_path = None
    for mod, path in sorted_files:
        if mod == "nominal":
            nominal_path = path
            break

    if nominal_path is None:
        print(f"  FEHLER: Kein nominal-JSON gefunden in Dateiliste!")
        print(f"  Verfügbare Dateien: {[f[0] for f in sorted_files]}")
        raise RuntimeError("Kein nominal-JSON gefunden!") 

    with open(nominal_path, "r") as f:
        merged = json.load(f)

    # jetzt iteriere über alle anderen
    for mod, path in sorted_files:
        if mod == "nominal":
            continue

        with open(path, "r") as f:
            data = json.load(f)

        def merge_nodes(nom_node, var_node, label):
            """Hängt die Werte des Variation-JSONs unter neuem Key an das nominale JSON."""
            if isinstance(nom_node, dict):
                if nom_node.get("nodetype") == "category" and nom_node.get("input") == "type":
                    for i, cat in enumerate(nom_node["content"]):
                        var_cat = var_node["content"][i]
                        existing_content = cat["value"]["content"]
                        var_values = var_cat["value"]["content"]

                        # hier hängen wir für jeden bestehenden Wert die neue Variation dran
                        if label == "nominal":
                            # Für nominal alles übernehmen (inkl. stat)
                            for var_entry in var_values:
                                existing_content.append({
                                    "key": label,
                                    "value": var_entry["value"]
                                })
                        else:
                            # Für Variationen nur den ersten Eintrag (Zentralwert) übernehmen
                            if var_values:
                                first_val = var_values[0]["value"]
                                existing_content.append({
                                    "key": label,
                                    "value": first_val
                                })
                    return nom_node

                elif "content" in nom_node:
                    for i in range(len(nom_node["content"])):
                        nom_node["content"][i] = merge_nodes(
                            nom_node["content"][i],
                            var_node["content"][i],
                            label
                        )
                    return nom_node

                else:
                    return nom_node

            elif isinstance(nom_node, list):
                for i in range(len(nom_node)):
                    nom_node[i] = merge_nodes(nom_node[i], var_node[i], label)
                return nom_node

            else:
                return nom_node

        for corr in merged.get("corrections", []):
            corr_name = corr.get("name")
            match = next((c for c in data.get("corrections", []) if c.get("name") == corr_name), None)
            if match is None:
                print(f"  Warnung: Keine passende correction '{corr_name}' in {mod}")
                continue

            corr["data"] = merge_nodes(
                corr["data"],
                match["data"],
                mod
            )

    return merged

def main():
    parser = argparse.ArgumentParser(description="Merge JSONs for corrections.")
    parser.add_argument("--input", "-i", required=True, 
                       help="Pfad zu den Output-Ordnern (wo die Variations-Ordner sind)")
    parser.add_argument("--output", "-o", required=True, 
                       help="Pfad, wo die merged JSONs gespeichert werden sollen")
    parser.add_argument("--nominal", "-n", 
                       help="Optional: Pfad zum nominal Ordner (falls kein 'nominal' im Namen)")

    args = parser.parse_args()

    base_dir = args.input
    merged_dir = args.output
    nominal_dir = args.nominal
    
    os.makedirs(merged_dir, exist_ok=True)

    print(f"Suche JSONs in: {base_dir}")
    if nominal_dir:
        print(f"Manueller nominal-Ordner: {nominal_dir}")
    
    grouped_files = find_json_files(base_dir, nominal_dir)
    
    if not grouped_files:
        print("Keine JSONs gefunden!")
        return

    print(f"\nGefundene Gruppen:")
    for (channel, era), files in grouped_files.items():
        print(f"  {channel} {era}: {len(files)} Dateien")

    for (channel, era), files in grouped_files.items():
        print(f"\n==> Merging {len(files)} JSONs für {channel} {era}")
        print(f"    Dateien: {[f[0] for f in files]}")
        
        try:
            merged_json = merge_jsons(files)
            out_path = os.path.join(merged_dir, f"{channel}_{era}_merged.json")

            with open(out_path, "w") as f:
                json.dump(merged_json, f, indent=2, separators=(",", ": "))

            print(f"  -> {out_path}")
        except Exception as e:
            print(f"  FEHLER beim Mergen: {e}")

    print("\nAlle Merges abgeschlossen.")

if __name__ == "__main__": 
    main()

# input: /work/agaganidze/CMSSW_12_3_2/src/UserCode/TagAndProbe/output_2018UL_variations_muon/best_model_nominal
# output: /work/agaganidze/CMSSW_12_3_2/src/UserCode/TagAndProbe/output_2018UL_variations_muon/best_model_nominal 