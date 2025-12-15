

#!/bin/bash
eras=("2017UL") #"2016postVFPUL") # era list: "2018UL" "2018UL" "2016preVFPUL" "2016postVFPUL"
channels=("") # channel list: "embeddingselection"  "muon" noch kein "electron"

#binning variations                  
binning_variations=("nominal" "up")    
binning_percentage=10                 

settings_dir="settings"
input_files="set_inputfiles.yaml"

#iso variations
# iso_variation = ("up" "down")
# iso_percantage = 10%

# output_dir="output"
# temp_dir="temp"

# mkdir -p $output_dir
# mkdir -p $temp_dir
# cp set_inputfiles.yaml $output_dir/used_settings # Copy input file list to output directory


# =====================================================
# Hauptschleife über alle Kombinationen
# =====================================================
for variation in "${binning_variations[@]}"; do
    for era in "${eras[@]}"; do
        for channel in "${channels[@]}"; do

            # === Namen zusammensetzen ===
            case $variation in
                nominal)
                    with_binning=""
                    out_dir="output_nominal_${channel}_${era}"
                    ;;
                up)
                    with_binning="--with-binning"
                    out_dir="output_binup${binning_percentage}_${channel}_${era}"
                    ;;
                down)
                    with_binning="--with-binning"
                    out_dir="output_bindown${binning_percentage}_${channel}_${era}"
                    ;;
                *)
                    echo "Unbekannte Variation: $variation"
                    exit 1
                    ;;
            esac

            echo ""
            echo "=========================================================="
            echo "Starte Verarbeitung für:"
            echo "  Era:      ${era}"
            echo "  Channel:  ${channel}"
            echo "  Variation:${variation}"
            echo "  Output:   ${out_dir}"
            echo "=========================================================="
            echo ""

            # === Output-Verzeichnis vorbereiten ===
            mkdir -p "$out_dir/used_settings"
            cp -r "$settings_dir"/* "$out_dir/used_settings/"
            cp "$input_files" "$out_dir/used_settings/"

            # === Restore vorher durchführen ===
            python3 scripts/setting_variations_binning.py \
                --path "$out_dir/used_settings" \
                --eras "$era" \
                --channels "$channel" \
                --restore

            # === Binning anwenden, falls up/down ===
            if [[ "$variation" != "nominal" ]]; then
                python3 scripts/setting_variations_binning.py \
                    --path "$out_dir/used_settings" \
                    --eras "$era" \
                    --channels "$channel" \
                    --with-binning \
                    --percentage "$binning_percentage" \
                    --variation "$variation"
            fi

            # === Analyse ausführen ===
            nice -n 19 python3 scripts/TagAndProbe.py \
                --channel "$channel" \
                --era "$era" \
                --settings-folder "$out_dir/used_settings" \
                --output "$out_dir" \
                --only-key ID_pt_eta_bins

            # === Optional: Weitere Scripts falls nötig ===
            # nice -n 19 python3 scripts/runTagAndProbeFits.py ...
            # nice -n 19 python3 scripts/translate_to_crosspog_json.py ...

            # === Output abschließen ===
            mv "$out_dir" "${out_dir}.done"
        done
    done
done
echo "All done."

