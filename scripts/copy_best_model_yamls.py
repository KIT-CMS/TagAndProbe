import os
import shutil
import argparse
from pathlib import Path

def should_skip_directory(path):
    return "settings" in path.name.lower()

def find_and_copy_yaml_files(source_dir, output_dir_name="output_yamls"):
    source_path = Path(source_dir)
    output_path = source_path / output_dir_name
    output_path.mkdir(parents=True, exist_ok=True)
    
    yaml_files = []
    skipped_files = []
    
    for yaml_file in source_path.rglob("*.yaml"):
        if any(should_skip_directory(part) for part in yaml_file.parents):
            skipped_files.append(yaml_file)
            continue
        yaml_files.append(yaml_file)
    
    for yaml_file in source_path.rglob("*.yml"):
        if any(should_skip_directory(part) for part in yaml_file.parents):
            skipped_files.append(yaml_file)
            continue
        yaml_files.append(yaml_file)
    
    if not yaml_files and not skipped_files:
        print(f"Keine YAML-Dateien in {source_dir} gefunden.")
        return
    
    for yaml_file in yaml_files:
        try:
            destination = output_path / yaml_file.name
            counter = 1
            original_destination = destination
            while destination.exists():
                stem = original_destination.stem
                suffix = original_destination.suffix
                destination = output_path / f"{stem}_{counter}{suffix}"
                counter += 1
            
            shutil.copy2(yaml_file, destination)
            print(f"Kopiert: {yaml_file} -> {destination}")
            
        except Exception as e:
            print(f"Fehler beim Kopieren von {yaml_file}: {e}")
    
    if skipped_files:
        print(f"\nÜbersprungene Dateien (in 'settings' Ordnern):")
        for skipped in skipped_files:
            print(f"  - {skipped}")
    
    print(f"\n{len(yaml_files)} YAML-Dateien wurden nach {output_path} kopiert.")
    print(f"{len(skipped_files)} Dateien wurden übersprungen.")

def main():
    parser = argparse.ArgumentParser(
        description="Findet und kopiert alle YAML-Dateien aus einem Verzeichnis (inkl. Unterordner), überspringt 'settings' Ordner"
    )
    parser.add_argument(
        "source_dir",
        help="Pfad zum Quellverzeichnis"
    )
    parser.add_argument(
        "-o", "--output",
        default="output_yamls",
        help="Name des Ausgabeverzeichnisses (Standard: output_yamls)"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.source_dir):
        print(f"Fehler: Quellverzeichnis '{args.source_dir}' existiert nicht.")
        return
    
    find_and_copy_yaml_files(args.source_dir, args.output)

if __name__ == "__main__":
    main()