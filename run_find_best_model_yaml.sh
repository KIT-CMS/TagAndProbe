#!/bin/bash

eras=("2018UL")
channels=("electron")

settings_dir="settings_yaml"
input_files="set_inputfiles.yaml"

passfail_hist="no"

# ======================================================
# Hauptschleife (parallelisiert)
# ======================================================

for era in "${eras[@]}"; do
    (
        for channel in "${channels[@]}"; do
            (
                # ===========================
                # 1) Output-Verzeichnis
                # ===========================
                out_dir="output_${channel}_${era}_bestmodel"
                mkdir -p "$out_dir/used_settings"

                echo ""
                echo "=========================================================="
                echo "   Era:      ${era}"
                echo "   Channel:  ${channel}"
                echo "   Output:   ${out_dir}"
                echo "=========================================================="
                echo ""

                #Kopieren der Settings
                cp -r "$settings_dir"/* "$out_dir/used_settings/"
                cp "$input_files" "$out_dir/used_settings/"

                #-------------------------
                settings_file=$(find "$out_dir/used_settings" -type f -name "*${channel}_${era}.yaml" | head -n 1)
                if [[ -z "$settings_file" ]]; then
                    echo "WARNING: Keine Settings gefunden, überspringe..."
                    continue
                fi

                python3 modification_framework_with_yaml/main_modification.py \
                    --path "$out_dir/used_settings" \
                    --eras "$era" \
                    --channels "$channel" \
                    --restore

                python3 modification_framework_with_yaml/main_modification.py \
                    --path "$out_dir/used_settings" \
                    --eras "$era" \
                    --channels "$channel"
                #------------------------

                # ===========================
                # 4) ROOT erzeugen
                # ===========================
                nice -n 19 python3 scripts_yaml/TagAndProbe.py \
                    --channel "$channel" \
                    --era "$era" \
                    --settings-folder "$out_dir/used_settings" \
                    --output "$out_dir"

                # ===========================
                # 5) Fitting
                # ===========================
                nice -n 19 python3 scripts_yaml/runTagAndProbeFits_bestmodel.py \
                    --channel "$channel" \
                    --era "$era" \
                    --fit \
                    --plot \
                    --settings-folder "$out_dir/used_settings" \
                    --output "$out_dir" \
                    $( [ "$passfail_hist" = "yes" ] && echo "--passfail_hist yes" )

                # ===========================
                # 6) JSON erzeugen
                # ===========================
                nice -n 19 python3 scripts_yaml/translate_to_crosspog_json_systL.py \
                    --era "$era" \
                    --channel "$channel" \
                    --output "$out_dir" \
                    --settings-folder "$out_dir/used_settings"

                python3 scripts_yaml/rename_output_yaml.py \
                    --folder "$out_dir/used_settings/UL/" \
                    --channel "$channel" \
                    --era "$era" \
                    --add-abm false

            ) &
            pids_channel[$channel]=$!
        done

        # Warten bis alle channels fertig sind
        for pid in ${pids_channel[*]}; do
            wait $pid
        done
    ) &
    pids_era[$era]=$!
done

# Warten bis alle eras fertig sind
for pid in ${pids_era[*]}; do
    wait $pid
done



echo "All done."
exit
