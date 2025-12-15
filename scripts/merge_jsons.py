#!/usr/bin/env python3
import os
import json
import re
from collections import defaultdict
import argparse

def find_json_files(base_dir):
    """
    Durchsucht alle Unterordner von base_dir nach JSON-Dateien (keine .gz),
    und ordnet sie nach (channel, era).
    """
    grouped = defaultdict(list)

    for folder in os.listdir(base_dir):
        full_path = os.path.join(base_dir, folder)
        if not os.path.isdir(full_path):
            continue

        if not folder.startswith("output_"):
            continue

        # prüfe, ob der Name auf eine Jahreszahl oder 'UL' endet
        if not re.search(r"(?:\d{4}|UL)$", folder):
            continue

        parts = folder.split("_")
        if len(parts) < 4:
            continue

        era = parts[-1]
        channel = parts[-2]
        mod = "_".join(parts[1:-2])

        json_dir = os.path.join(full_path, "jsons")
        if not os.path.isdir(json_dir):
            continue

        for file in os.listdir(json_dir):
            if file.endswith(".json") and not file.endswith(".json.gz"):
                grouped[(channel, era)].append((mod, os.path.join(json_dir, file)))

    return grouped


def merge_jsons(file_list):
    """
    Nimmt eine Liste von (mod_name, file_path) Tupeln,
    lädt alle JSONs und kombiniert sie in der richtigen Reihenfolge.
    """
    # nominal zuerst, dann alphabetisch
    sorted_files = sorted(file_list, key=lambda x: (x[0] != "nominal", x[0]))

    # Nominal als Basis
    nominal_path = None
    for mod, path in sorted_files:
        if mod == "nominal":
            nominal_path = path
            break

    if nominal_path is None:
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
                print(f"Warnung: Keine passende correction '{corr_name}' in {mod}")
                continue

            corr["data"] = merge_nodes(
                corr["data"],
                match["data"],
                mod
            )

    return merged


def main():
    base_dir = "muon_2017UL_variations"
    merged_dir = os.path.join(base_dir, "merged_jsons")
    os.makedirs(merged_dir, exist_ok=True)

    grouped_files = find_json_files(base_dir)
    if not grouped_files:
        print("Keine JSONs gefunden in", base_dir)
        return

    for (channel, era), files in grouped_files.items():
        print(f"==> Merging {len(files)} JSONs for {channel} {era}")
        merged_json = merge_jsons(files)
        out_path = os.path.join(merged_dir, f"{channel}_{era}_merged.json")

        with open(out_path, "w") as f:
            json.dump(merged_json, f, indent=2, separators=(",", ": "))

        print(f"  -> {out_path}")

    print("Alle Merges abgeschlossen.")

main()

# def main(base_dir, merged_dir):
#     os.makedirs(merged_dir, exist_ok=True)

#     grouped_files = find_json_files(base_dir)
#     if not grouped_files:
#         print("Keine JSONs gefunden in", base_dir)
#         return

#     for (channel, era), files in grouped_files.items():
#         merged_json = merge_jsons(files)
#         out_path = os.path.join(merged_dir, f"{channel}_{era}_merged.json")

#         with open(out_path, "w") as f:
#             json.dump(merged_json, f, indent=2, separators=(",", ": "))

#         print(f"  -> {out_path}")

#     print("Alle Merges abgeschlossen.")

#     parser = argparse.ArgumentParser(description="Merge JSONs for corrections.")
#     parser.add_argument("--input", "-i", required=True, help="Pfad zu den Output-Ordnern")
#     parser.add_argument("--output", "-o", required=True, help="Pfad, wo die merged JSONs gespeichert werden sollen")

#     args = parser.parse_args()

#     main(base_dir=args.input, merged_dir=args.output)


