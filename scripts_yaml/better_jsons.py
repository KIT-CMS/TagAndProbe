import json
import os

def convert_old_to_new(input_json_path, output_json_path):
    with open(input_json_path, "r") as f:
        data = json.load(f)

    def convert_category(cat):
        # cat = {"key": "mc", "value": float}
        return {
            "key": cat["key"],
            "value": {
                "nodetype": "category",
                "input": "values",
                "content": [
                    {"key": "nominal", "value": cat["value"]}
                ]
            }
        }

    def convert_content(node):
        if isinstance(node, dict):
            if node.get("nodetype") == "category" and node.get("input") == "type":
                # Ersetze die einfache Typ-Kategorie-Struktur durch die neue mit "nominal"
                node["content"] = [convert_category(c) for c in node["content"]]
                return node
            elif "content" in node:
                node["content"] = [convert_content(c) for c in node["content"]]
                return node
            else:
                return node
        elif isinstance(node, list):
            return [convert_content(c) for c in node]
        else:
            return node

    # Wandle alle Korrekturen um, nicht nur die erste
    for corr in data.get("corrections", []):
        corr["data"] = convert_content(corr["data"])

    # Falls kein Dateiname angegeben ist, automatisch generieren
    if os.path.isdir(output_json_path):
        base_name = os.path.basename(input_json_path)
        name, ext = os.path.splitext(base_name)
        output_json_path = os.path.join(output_json_path, f"{name}_converted{ext}")

    with open(output_json_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Converted JSON saved to {output_json_path}")


def add_binning_var(nominal_json_path, up_json_path, down_json_path, percentage, output_json_path):
    with open(nominal_json_path) as f:
        nominal = json.load(f)
    with open(up_json_path) as f:
        up_var = json.load(f)
    with open(down_json_path) as f:
        down_var = json.load(f)

    def add_binvars(nom_node, up_node, down_node):
        if isinstance(nom_node, dict):
            if nom_node.get("nodetype") == "category" and nom_node.get("input") == "type":
                for i, cat in enumerate(nom_node["content"]):
                    # hier behalten wir den bestehenden nominal Wert
                    existing_content = cat["value"]["content"]
                    up_val = up_node["content"][i]["value"]
                    down_val = down_node["content"][i]["value"]

                    # Füge Up/Down direkt in denselben content Block ein
                    existing_content.append({"key": f"binvar_up_{percentage}", "value": up_val})
                    existing_content.append({"key": f"binvar_down_{percentage}", "value": down_val})
                return nom_node
            elif "content" in nom_node:
                nom_node["content"] = [
                    add_binvars(n, u, d) for n, u, d in zip(nom_node["content"], up_node["content"], down_node["content"])
                ]
                return nom_node
            else:
                return nom_node
        elif isinstance(nom_node, list):
            return [add_binvars(n, u, d) for n, u, d in zip(nom_node, up_node, down_node)]
        else:
            return nom_node

    for idx, corr in enumerate(nominal.get("corrections", [])):
        corr["data"] = add_binvars(
            corr["data"],
            up_var["corrections"][idx]["data"],
            down_var["corrections"][idx]["data"]
        )

    with open(output_json_path, "w") as f:
        json.dump(nominal, f, indent=2)

    print(f"Final JSON saved to {output_json_path}")





old_json_path = "/work/agaganidze/CMSSW_12_3_2/src/UserCode/TagAndProbe/output_modify_binnings_muon_2017UL.done/jsons/muon_2017UL.json"
new_json_path = old_json_path
convert_old_to_new(old_json_path, new_json_path)

# nominal_json_path = "/work/agaganidze/CMSSW_12_3_2/src/UserCode/TagAndProbe/gathered_data/2017UL/norm_2017UL_muon_ID_pt_eta/SF/better_muon_2017UL.json"
# up_json_path = "/work/agaganidze/CMSSW_12_3_2/src/UserCode/TagAndProbe/gathered_data/2017UL/10_percent_up_2017UL_muon_ID_pt_era/SF/muon_2017UL_up.json"
# down_json_path = "/work/agaganidze/CMSSW_12_3_2/src/UserCode/TagAndProbe/gathered_data/2017UL/10_percent_down_2017UL_muon_ID_pt_era/SF/muon_2017UL.json"
# output_json_path = "/work/agaganidze/CMSSW_12_3_2/src/UserCode/TagAndProbe/gathered_data/2017UL/SF/merged_with_binning.json"
# percentage = 10
# add_binning_var(nominal_json_path, up_json_path, down_json_path, percentage, output_json_path)