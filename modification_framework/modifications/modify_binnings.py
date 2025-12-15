import yaml
import copy
import os

def apply_percentage_bin_variation(original_bins, percentage, variation="up"):

    if len(original_bins) < 2:
        return original_bins.copy()
    # erste und letzte Grenze bleiben gleich
    new_bins = [original_bins[0]]
    
    for i in range(1, len(original_bins) - 1):
        bin_width = original_bins[i] - original_bins[i-1]
        shift_amount = (percentage / 100.0) * bin_width
        
        if variation == "up":
            new_boundary = original_bins[i] + shift_amount
        elif variation == "down":
            new_boundary = original_bins[i] - shift_amount
        else:
            raise ValueError("Variation muss 'up' oder 'down' sein")
        
        # sicherstellen, dass die neue Grenze zw. den Nachbarn liegt
        new_boundary = max(new_boundary, original_bins[i-1] + 0.1)  
        new_boundary = min(new_boundary, original_bins[i+1] - 0.1) 
        
        new_bins.append(new_boundary)
    
    new_bins.append(original_bins[-1])
    return new_bins

def apply_percentage_bin_variation_2d(bin_cfgs, percentage, variation="up", axis="pt", file=False):
    """
    - Wenn file=False: arbeitet wie bisher und gibt modifizierte bin_cfgs zurück.
    - Wenn file=pfad/zur/file.yaml: lädt YAML, ändert bins, schreibt YAML zurück.
    """
    if file and isinstance(file, str):
        # Lade YAML
        with open(file, "r") as f:
            yaml_cfg = yaml.safe_load(f)

        if not isinstance(yaml_cfg, dict):
            raise ValueError(f"Datei {file} enthält keine gültige YAML-Konfiguration.")

        bin_cfgs_modified = copy.deepcopy(yaml_cfg)
    else:
        if bin_cfgs is None:
            raise ValueError("Entweder 'file' oder 'bin_cfgs' muss angegeben sein.")
        bin_cfgs_modified = copy.deepcopy(bin_cfgs)

    for key, cfg in bin_cfgs_modified.items():
        axes_to_modify = []

        if axis in ["pt", "pteta"] and "bins_x" in cfg:
            axes_to_modify.append(("bins_x", "pt"))
        if axis in ["eta", "pteta"] and "bins_y" in cfg:
            axes_to_modify.append(("bins_y", "eta"))

        for bin_key, axis_name in axes_to_modify:
            original_bins = cfg[bin_key]
            new_bins = apply_percentage_bin_variation(original_bins, percentage, variation)
            cfg[bin_key] = new_bins
            #print(f"Geändert {key}: {axis_name}-Binning von {original_bins} zu {[round(x, 2) for x in new_bins]}")

    if file and isinstance(file, str):

        class MyDumper(yaml.SafeDumper):
            pass
        def repr_list_flow(dumper, data):
            return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)
        MyDumper.add_representer(list, repr_list_flow)

        # Datei überschreiben mit Flow-Style
        with open(file, "w") as f:
            yaml.dump(bin_cfgs_modified, f, Dumper=MyDumper, sort_keys=False)

        print(f"Datei {file} wurde überschrieben.")
        return None
    else:
        return bin_cfgs_modified
    
def apply_change(file_path, percentage=10, variation="up", axis="pteta"):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Datei {file_path} existiert nicht.")

    print(f"Ändere Binning in {os.path.basename(file_path)} ({variation}, {axis}, {percentage}%)")

    apply_percentage_bin_variation_2d(
        bin_cfgs=None,
        percentage=percentage,
        variation=variation,
        axis=axis,
        file=file_path,
    )

    print(f"Fertig: {os.path.basename(file_path)} wurde angepasst.")
