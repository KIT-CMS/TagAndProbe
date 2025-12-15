#!/bin/bash

# ===============================
# Konfiguration
# ===============================
INPUT="/work/agaganidze/CMSSW_12_3_2/src/UserCode/TagAndProbe/output_2018UL_variations_muon/best_model_nominal"

BASE_OUTPUT="/work/agaganidze/CMSSW_12_3_2/src/UserCode/TagAndProbe/scripts_yaml/plotting_scripts_yaml/plotting_framework"
RESULTS_DIR="$BASE_OUTPUT/results"

NOMINAL=""

MERGE_SCRIPT="/work/agaganidze/CMSSW_12_3_2/src/UserCode/TagAndProbe/scripts_yaml/merge_jsons_yaml.py"
FULLMERGE_SCRIPT="/work/agaganidze/CMSSW_12_3_2/src/UserCode/TagAndProbe/scripts_yaml/merging_diffmod_with_mine_json.py"

GRID_SCRIPT="/work/agaganidze/CMSSW_12_3_2/src/UserCode/TagAndProbe/scripts_yaml/plotting_scripts_yaml/plotting_framework/json_to_grid.py"

# ===============================
# Output-Ordner vorbereiten
# ===============================
mkdir -p "$RESULTS_DIR"
OUTPUT="$RESULTS_DIR"

echo "Output-Verzeichnis: $OUTPUT"

# ===============================
# Suche Bestmodel JSON
# ===============================
BESTMODEL_DIR=$(find "$INPUT" -type d -iname "*bestmodel*" | head -n 1)
if [ -z "$BESTMODEL_DIR" ]; then
    echo "FEHLER: Kein Ordner mit 'bestmodel' gefunden."
    exit 1
fi

JSON_DIR="$BESTMODEL_DIR/jsons"
if [ ! -d "$JSON_DIR" ]; then
    echo "FEHLER: 'jsons'-Ordner nicht gefunden in $BESTMODEL_DIR"
    exit 1
fi

JSON_FILE=$(find "$JSON_DIR" -maxdepth 1 -type f -name "*.json" | head -n 1)
if [ -z "$JSON_FILE" ]; then
    echo "FEHLER: Keine .json-Datei im Ordner $JSON_DIR gefunden."
    exit 1
fi

BASENAME=$(basename "$JSON_FILE" .json)
BESTMODEL_JSON="$OUTPUT/${BASENAME}_bestmodelL.json"

cp "$JSON_FILE" "$BESTMODEL_JSON"
echo "Bestmodel JSON kopiert: $BESTMODEL_JSON"

# ===============================
# Merge Script ausführen
# ===============================
echo "Starte Merge Script..."

if [ -z "$NOMINAL" ]; then
    python3 "$MERGE_SCRIPT" --input "$INPUT" --output "$OUTPUT"
else
    python3 "$MERGE_SCRIPT" --input "$INPUT" --output "$OUTPUT" --nominal "$NOMINAL"
fi

# ===============================
# Merge-JSON suchen
# ===============================
MERGE_OUTPUT_JSON=$(find "$OUTPUT" -maxdepth 1 -type f -name "*_merged.json" | head -n 1)

if [ -z "$MERGE_OUTPUT_JSON" ]; then
    echo "FEHLER: Keine *_merged.json Datei gefunden."
    exit 1
fi

echo "Gefundene Merge-Datei: $MERGE_OUTPUT_JSON"

# ===============================
# Fullmerge
# ===============================
FULLMERGE_JSON="${MERGE_OUTPUT_JSON%.json}_fullmerge.json"

echo "Starte Fullmerge..."

python3 "$FULLMERGE_SCRIPT" \
    --mine "$MERGE_OUTPUT_JSON" \
    --other "$BESTMODEL_JSON" \
    --out "$FULLMERGE_JSON"

if [ ! -f "$FULLMERGE_JSON" ]; then
    echo "FEHLER: Fullmerge JSON wurde nicht erzeugt."
    exit 1
fi

echo "Fullmerge Datei erstellt: $FULLMERGE_JSON"

# ===============================
# JSON -> Grid (.npz)
# ===============================
GRID_BASENAME=$(basename "$FULLMERGE_JSON" .json)
GRID_FILE="$OUTPUT/${GRID_BASENAME}.npz"

echo "Erzeuge Grid (.npz)..."
echo "Input JSON: $FULLMERGE_JSON"
echo "Output Grid: $GRID_FILE"

python3 "$GRID_SCRIPT" \
    --json "$FULLMERGE_JSON" \
    --out "$GRID_FILE"

if [ ! -f "$GRID_FILE" ]; then
    echo "FEHLER: Grid-Datei wurde nicht erzeugt."
    exit 1
fi

echo "Grid erfolgreich gespeichert: $GRID_FILE"
