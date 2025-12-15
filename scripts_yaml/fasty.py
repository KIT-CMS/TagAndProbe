import yaml
import os
from pathlib import Path

class TupleToListLoader(yaml.SafeLoader):
    pass

def construct_python_tuple(loader, node):
    seq = loader.construct_sequence(node)
    return list(seq)

# Registriere den Konstruktor für !!python/tuple
TupleToListLoader.add_constructor(
    u"tag:yaml.org,2002:python/tuple",
    construct_python_tuple
)

def convert_yaml_file(path_in, path_out=None):
    with open(path_in, "r") as f:
        data = yaml.load(f, Loader=TupleToListLoader)

    # Optional anderen Ausgabepfad erlauben
    if path_out is None:
        path_out = path_in

    with open(path_out, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)

def convert_yaml_folder(folder_in, folder_out=None):
    folder_in = Path(folder_in)
    if folder_out is not None:
        folder_out = Path(folder_out)
        folder_out.mkdir(parents=True, exist_ok=True)

    for file in folder_in.iterdir():
        if file.suffix.lower() in [".yml", ".yaml"]:
            if folder_out is None:
                out_path = file
            else:
                out_path = folder_out / file.name

            convert_yaml_file(file, out_path)

if __name__ == "__main__":
    # Beispiel:
    # convert_yaml_folder("input_yamls")
    # oder Ausgabe in getrennten Ordner:
    # convert_yaml_folder("input_yamls", "converted_yamls")

    convert_yaml_folder("/work/agaganidze/CMSSW_12_3_2/src/UserCode/TagAndProbe/output_muon_2018UL_bestmodel/best_model_yamls copy")
