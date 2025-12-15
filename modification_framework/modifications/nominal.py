import os

def apply_change(file_path, **kwargs):
    # Dummy-Funktion
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"{file_path} doesnt exist")
    print(f"[nominal] file {os.path.basename(file_path)}")