import os

def handle_ntuples_files(folder, do_delete=False):
    if not os.path.isdir(folder):
        raise ValueError(f"Ordner existiert nicht: {folder}")

    print(f"Suche in: {folder}")
    found_any = False

    for filename in os.listdir(folder):
        if filename.startswith("ntuple") or filename.startswith(".nfs000"):
            found_any = True
            filepath = os.path.join(folder, filename)

            if do_delete:
                if os.path.isfile(filepath):
                    print(f"Lösche Datei: {filepath}")
                    os.remove(filepath)
            else:
                print(f"Gefunden: {filepath}")

    if not found_any:
        print("Keine passenden Dateien gefunden.")

handle_ntuples_files("/work/agaganidze/CMSSW_12_3_2/src/UserCode/TagAndProbe/", do_delete=True)
