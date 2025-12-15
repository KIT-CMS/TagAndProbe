import os
import yaml
import argparse
import re
import shutil

def format_variation(var_name, value):
    clean_name = var_name.replace("_", "")
    match = re.match(r"([0-9.]+)(up|down)(\[.*\])?", value)
    if not match:
        return None

    val_float = float(match.group(1))
    percent = int(round(val_float * 100))
    direction = match.group(2)
    bracket = match.group(3)

    if bracket:
        bracket = bracket.replace(",", ":")

    return f"{clean_name}{percent}{direction}{bracket if bracket else ''}"


def process_yaml_and_rename(folder, channel, era, add_abm=False):

    # In UL nach *_original.yaml suchen
    yaml_path = None
    for f in os.listdir(folder):
        if f.endswith("_original.yaml"):
            yaml_path = os.path.join(folder, f)
            break

    if yaml_path is None:
        print("Keine *_original.yaml gefunden. Ordner wird nicht umbenannt.")
        return

    # YAML laden
    with open(yaml_path, "r") as stream:
        data = yaml.safe_load(stream)

    syst = data.get("default_systematics", {})
    result_tokens = []

    # binning_variation
    for key, value in syst.get("binning_variation", {}).items():
        token = format_variation(key, value)
        if token:
            result_tokens.append(token)

    # variable_variation
    for key, value in syst.get("variable_variation", {}).items():
        token = format_variation(key, value)
        if token:
            result_tokens.append(token)

    if not result_tokens and not add_abm:
        print("Keine Variationen und kein _abm-Flag. Ordner wird nicht umbenannt.")
        return

    # **********
    # Hier bestimmen wir den Ordner, der umbenannt werden soll:
    # folder = ".../output_muon_2018UL/used_settings/UL/"
    # **********
    ul_folder = folder.rstrip("/")
    used_settings_folder = os.path.dirname(ul_folder)
    output_folder = os.path.dirname(used_settings_folder)

    base_name = os.path.basename(output_folder)
    parent = os.path.dirname(output_folder)

    suffix_parts = []
    if result_tokens:
        suffix_parts.append("_" + "_".join(result_tokens))
    if not suffix_parts:
        suffix_parts.append("_nominal")
    if add_abm:
        suffix_parts.append("_abm")
    
    suffix = "".join(suffix_parts)
    new_name = base_name + suffix
    new_path = os.path.join(parent, new_name)

    print(f"Benenne um: {output_folder} → {new_path}")
    shutil.move(output_folder, new_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", required=True)
    parser.add_argument("--channel", required=True)
    parser.add_argument("--era", required=True)
    parser.add_argument("--add-abm", default="false")

    args = parser.parse_args()
    add_abm_flag = args.add_abm.lower() in ["true", "1", "yes"]

    process_yaml_and_rename(args.folder, args.channel, args.era, add_abm=add_abm_flag)
