#!/usr/bin/env python3
import os
import shutil
import tempfile
import argparse
import yaml
import re

# ============================================================
# Strings nur in Quotes, wenn nötig
# ============================================================
def quoted_str_representer(dumper, data):
    if re.match(r'^[a-zA-Z0-9_]+$', data):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style=None)
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

yaml.add_representer(str, quoted_str_representer)

# ============================================================
# Flow-Style Listen
# ============================================================
class FlowList(list): pass

def flow_list_representer(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)

yaml.add_representer(FlowList, flow_list_representer)

# ============================================================
# Preserve original style of lists
# ============================================================
def preserve_list_style(data):
    if isinstance(data, dict):
        return {k: preserve_list_style(v) for k, v in data.items()}
    elif isinstance(data, list):
        if getattr(data, "_flow_style", False):
            return FlowList([preserve_list_style(v) for v in data])
        return [preserve_list_style(v) for v in data]
    else:
        return data

def mark_flow_lists(entry, keys_to_flow=None):
    if keys_to_flow is None:
        keys_to_flow = ["bins_x", "bins_y", "y_range", "ratio_y_range"]
    if isinstance(entry, dict):
        for k, v in entry.items():
            if k in keys_to_flow and isinstance(v, list):
                fl = FlowList(v)
                fl._flow_style = True
                entry[k] = fl
            elif isinstance(v, dict):
                mark_flow_lists(v, keys_to_flow)
    return entry

# ============================================================
# Bin-Grenzen verschieben
# ============================================================
def shift_bins(original, percentage, direction, idx_range=None):
    if len(original) < 3:
        return original.copy()
    new_bins = original.copy()
    start = 1 if idx_range is None else max(1, idx_range[0]+1)
    end = len(original)-2 if idx_range is None else min(len(original)-2, idx_range[1]-1)
    if start > end: return original.copy()
    for i in range(start, end+1):
        width = original[i] - original[i-1]
        shift = width * (percentage/100.0)
        new_value = original[i]+shift if direction=="up" else original[i]-shift
        min_value = original[i-1]+0.001
        max_value = original[i+1]-0.001 if i < len(original)-1 else new_value
        new_bins[i] = max(min(new_value, max_value), min_value)
    return new_bins

# ============================================================
# Variable-Variationen
# ============================================================
def apply_variable_variation_in_expr(expr, variable, delta, direction):
    pattern = rf"({re.escape(variable)}\s*[<>]=?\s*)([-+]?[0-9]*\.?[0-9]+)"
    def repl(match):
        prefix = match.group(1)
        value = float(match.group(2))
        value = value + delta if direction=="up" else value - delta
        return f"{prefix}{value}"
    return re.sub(pattern, repl, expr)

def apply_variable_variations(entry_dict, variations):
    expr_fields = ["tag", "probe", "var", "binvar_x", "binvar_y"]
    for variable, (direction, delta) in variations.items():
        for field in expr_fields:
            if field in entry_dict and isinstance(entry_dict[field], str):
                entry_dict[field] = apply_variable_variation_in_expr(entry_dict[field], variable, delta, direction)

# ============================================================
# Systematics anwenden (rekursiv)
# ============================================================
def apply_syst_to_entry(entry, default_syst=None):
    if not isinstance(entry, dict): return entry
    if default_syst is None: default_syst = {}
    syst = entry.pop("systematics", default_syst)

    # Bin-Grenzen
    binning = syst.get("binning_variation", {})
    for var, val in binning.items():
        match = re.match(r"([0-9]*\.?[0-9]+)(up|down)(?:\[(\d+):(\d+)\])?", str(val))
        if match:
            perc = float(match.group(1))*100
            dirn = match.group(2)
            idx_range = None
            # Wenn Bereich angegeben wurde
            if match.group(3) and match.group(4):
                idx_range = (int(match.group(3)), int(match.group(4)))

            if var=="pt" and "bins_x" in entry: entry["bins_x"] = shift_bins(entry["bins_x"], perc, dirn, idx_range)
            if var=="eta" and "bins_y" in entry: entry["bins_y"] = shift_bins(entry["bins_y"], perc, dirn, idx_range)

    # Variable Variationen
    varvar = syst.get("variable_variation", {})
    for var, val in varvar.items():
        match = re.match(r"([0-9]*\.?[0-9]+)(up|down)", str(val))
        if match:
            delta = float(match.group(1))
            direction = match.group(2)
            apply_variable_variations(entry, {var: (direction, delta)})

    # Rekursion
    for k,v in entry.items():
        if isinstance(v, dict): entry[k] = apply_syst_to_entry(v, default_syst)
    return entry

def apply_syst_to_yaml(data):
    default_syst = data.pop("default_systematics", {})
    new_data = {}
    for key, entry in data.items():
        if isinstance(entry, dict):
            new_data[key] = apply_syst_to_entry(entry, default_syst)
        else:
            new_data[key] = entry
    return new_data

# ============================================================
# Dateien verarbeiten
# ============================================================
def process_all(path, eras, channels, restore=False):
    yaml_files = []
    for root, _, files in os.walk(path):
        for f in files:
            if f.endswith(".yaml") and not f.endswith("_original.yaml"):
                if any(e in f for e in eras) and any(c in f for c in channels):
                    yaml_files.append(os.path.join(root,f))

    if not yaml_files: raise FileNotFoundError("Keine passenden YAML-Dateien gefunden.")

    if restore:
        for f in yaml_files:
            backup = f.replace(".yaml","_original.yaml")
            if os.path.exists(backup):
                os.remove(f)
                shutil.move(backup,f)
        return

    with tempfile.TemporaryDirectory() as tmp:
        mapping=[]
        for orig in yaml_files:
            rel=os.path.relpath(orig,path)
            tmp_path=os.path.join(tmp,rel)
            os.makedirs(os.path.dirname(tmp_path),exist_ok=True)
            shutil.copy2(orig,tmp_path)
            mapping.append((orig,tmp_path))

        for orig,tmp_path in mapping:
            with open(tmp_path) as f: data=yaml.safe_load(f)
            new_data=apply_syst_to_yaml(data)

            # Preserve original list styles
            for key, cfg in new_data.items():
                if isinstance(cfg, dict):
                    mark_flow_lists(cfg)

            with open(tmp_path,"w") as f:
                yaml.dump(new_data,f,sort_keys=False, default_flow_style=False, width=4096)

        # Backup & Kopie
        for orig,tmp_path in mapping:
            backup=orig.replace(".yaml","_original.yaml")
            if not os.path.exists(backup): shutil.copy2(orig,backup)
            shutil.copy2(tmp_path,orig)

# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="YAML-basierte Modifikationen für Systematics.")
    parser.add_argument("--path",required=True)
    parser.add_argument("--eras",nargs="+",required=True)
    parser.add_argument("--channels",nargs="+",required=True)
    parser.add_argument("--restore",action="store_true")
    args = parser.parse_args()
    process_all(args.path,args.eras,args.channels,args.restore)

if __name__=="__main__":
    main()
