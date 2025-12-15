#!/bin/bash


eras=("2018UL")
channels=("muon")

settings_dir="settings_yaml"
input_files="set_inputfiles.yaml"

passfail_hist="no"

run_config_yaml="settings_yaml/UL/runs_config.yaml"


#best_model_yaml_muon="output_muon_2018UL_bestmodel_find/best_model_yamls"
best_model_yaml_muon="output_muon_2018UL_bestmodel_1find_after/best_model_yamls"
best_model_yaml_electron="output_2018UL_variations_electron/best_model_nominal/output_electron_2018UL_bestmodel_nominal/best_model_yamls"
# ===============================================================
# Runs auslesen
# ===============================================================
mapfile -t run_names < <(python3 scripts_yaml/more_runs_yaml.py \
    --runs-yaml "$run_config_yaml" \
    --list-runs | sed 's/^[[:space:]]*-[[:space:]]*//;/^Verfügbare Runs/d')

if [[ ${#run_names[@]} -eq 0 ]]; then
    echo "Keine Runs gefunden."
    exit 1
fi

echo "Gefundene Runs:"
printf '  %s\n' "${run_names[@]}"
echo ""


# ===============================================================
# ÄUSSERE RUN-SCHLEIFE
# ===============================================================
for run in "${run_names[@]}"; do
    echo ""
    echo "=========================================================="
    echo " STARTE RUN: $run"
    echo "=========================================================="
    echo ""

    declare -A pids_era

    # ===============================================================
    # Era-Schleife
    # ===============================================================
    for era in "${eras[@]}"; do
        (
            declare -A pids_channel

            # =======================================================
            # Channel-Schleife
            # =======================================================
            for channel in "${channels[@]}"; do
                (
                    # --------------------------------------------------
                    # YAML DEFINIEREN (WICHTIG: jetzt abhängig von era+channel)
                    # --------------------------------------------------
                    target_yaml="settings_yaml/UL/settings_${channel}_${era}.yaml"

                    echo " wende Run $run auf Datei an: $target_yaml"

                    python3 scripts_yaml/more_runs_yaml.py \
                        --target-yaml "$target_yaml" \
                        --runs-yaml "$run_config_yaml" \
                        --run "$run"

                    if [[ $? -ne 0 ]]; then
                        echo "Fehler beim Überschreiben der Systematics in:"
                        echo "  $target_yaml"
                        exit 1
                    fi

                    # --------------------------------------------------
                    # OUTPUT-DIR (ohne Run-Suffix, dein rename script macht Namen)
                    # --------------------------------------------------
                    out_dir="output_${channel}_${era}_bestmodel"
                    mkdir -p "$out_dir/used_settings"

                    echo ""
                    echo "----------------------------------------------------------"
                    echo " Era:      ${era}"
                    echo " Channel:  ${channel}"
                    echo " Run:      ${run}"
                    echo " Output:   ${out_dir}"
                    echo " YAML:     ${target_yaml}"
                    echo "----------------------------------------------------------"
                    echo ""

                    # --------------------------------------------------
                    # Settings kopieren
                    # --------------------------------------------------
                    cp -r "$settings_dir"/* "$out_dir/used_settings/"
                    cp "$input_files" "$out_dir/used_settings/"

                    settings_file=$(find "$out_dir/used_settings" -type f -name "*${channel}_${era}.yaml" | head -n 1)
                    if [[ -z "$settings_file" ]]; then
                        echo "WARNING: Keine Settings gefunden, überspringe..."
                        continue
                    fi

                    # --------------------------------------------------
                    # Modification Framework
                    # --------------------------------------------------
                    python3 modification_framework_with_yaml/main_modification.py \
                        --path "$out_dir/used_settings" \
                        --eras "$era" \
                        --channels "$channel" \
                        --restore

                    python3 modification_framework_with_yaml/main_modification.py \
                        --path "$out_dir/used_settings" \
                        --eras "$era" \
                        --channels "$channel"

                    # --------------------------------------------------
                    # ROOT erzeugen
                    # --------------------------------------------------
                    # nice -n 19 python3 scripts_yaml/TagAndProbe.py \
                    #     --channel "$channel" \
                    #     --era "$era" \
                    #     --settings-folder "$out_dir/used_settings" \
                    #     --output "$out_dir"

                    # --------------------------------------------------
                    # Fitting
                    # --------------------------------------------------
                    # nice -n 19 python3 scripts_yaml/runTagAndProbeFits_bestmodel.py \
                    #     --channel "$channel" \
                    #     --era "$era" \
                    #     --fit \
                    #     --plot \
                    #     --settings-folder "$out_dir/used_settings" \
                    #     --output "$out_dir" \
                    #     $( [ "$passfail_hist" = "yes" ] && echo "--passfail_hist yes" )

                    nice -n 19 python3 scripts_yaml/runTagAndProbeFits_applymodel.py \
                        --channel "$channel" \
                        --era "$era" \
                        --fit \
                        --plot \
                        --settings-folder "$out_dir/used_settings" \
                        --output "$out_dir" \
                        --yaml-base-path "$best_model_yaml_muon" \
                        $( [ "$passfail_hist" = "yes" ] && echo "--passfail_hist yes" )

                    # --------------------------------------------------
                    # JSON erzeugen
                    # --------------------------------------------------
                    # nice -n 19 python3 scripts_yaml/translate_to_crosspog_json_systL.py \
                    #     --era "$era" \
                    #     --channel "$channel" \
                    #     --output "$out_dir" \
                    #     --settings-folder "$out_dir/used_settings"

                    nice -n 19 python3 scripts_yaml/translate_to_crosspog_json.py \
                        --era "$era" \
                        --channel "$channel" \
                        --output "$out_dir" \
                        --settings-folder "$out_dir/used_settings"

                    # python3 scripts_yaml/rename_output_yaml.py \
                    #     --folder "$out_dir/used_settings/UL/" \
                    #     --channel "$channel" \
                    #     --era "$era" \
                    #     --add-abm true

                ) &
                pids_channel[$channel]=$!
            done

            for pid in ${pids_channel[*]}; do
                wait $pid
            done

        ) &
        pids_era[$era]=$!
    done

    for pid in ${pids_era[*]}; do
        wait $pid
    done

    echo ""
    echo "=========================================================="
    echo " RUN $run abgeschlossen"
    echo "=========================================================="
    echo ""

done

echo "Alle Runs abgeschlossen."
exit
