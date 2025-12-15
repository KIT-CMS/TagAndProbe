#!/bin/bash

eras=("2017UL" "2016postVFPUL")          
channels=("muon" "electron") #noch probleme bei embeddingselection, aber electron geht

settings_dir="settings"
input_files="set_inputfiles.yaml"

modifications=("nominal" "modify_binnings" "modify_isotag") #names of the files in the folder: /modification_framework/modifications

#same order as in modifications 
mod_args=(
    '{}' 
    '{"percentage":10,"variation":"up","axis":"pt"}'   
    '{"percentage":10,"variation":"up"}'                 
)

passfail_hist="yes" # a pass and fail histogram of every "DY/embedding/data" data for every label in all used eras/channels

#main loop
for idx in "${!modifications[@]}"; do
    mod="${modifications[$idx]}"
    args="${mod_args[$idx]}"

    var_label="$mod"
    if [[ "$args" != "{}" ]]; then
        perc=$(echo "$args" | grep -o '"percentage":[0-9]*' | cut -d':' -f2)
        var=$(echo "$args" | grep -o '"variation":"[^"]*"' | cut -d':' -f2 | tr -d '"')
        if [[ -n "$perc" && -n "$var" ]]; then
            var_label="${mod}_${var}${perc}"
        fi
    fi

    for era in "${eras[@]}"; do
        for channel in "${channels[@]}"; do

            if [[ "$mod" == "nominal" ]]; then
                out_dir="output_${mod}_${channel}_${era}"
            else
                out_dir="output_${var_label}_${channel}_${era}"
            fi

            echo ""
            echo "=========================================================="
            echo "  modification: ${mod}"
            echo "  era:         ${era}"
            echo "  channel:     ${channel}"
            echo "  output:      ${out_dir}"
            echo "=========================================================="
            echo ""

            # output folder
            mkdir -p "$out_dir/used_settings"
            cp -r "$settings_dir"/* "$out_dir/used_settings/"
            cp "$input_files" "$out_dir/used_settings/"

            settings_file=$(find "$out_dir/used_settings" -type f -name "*${channel}_${era}.yaml" | head -n 1)

            if [[ -z "$settings_file" ]]; then
                echo "WARNING: Settings für $channel/$era existieren nicht (auch in Unterordnern nicht), überspringe..."
                continue
            fi

            # restoration
            python3 modification_framework/main_modification.py \
                --path "$out_dir/used_settings" \
                --eras "$era" \
                --channels "$channel" \
                --modification "$mod" \
                --args '{}' \
                --restore

            # modification
            if [[ "$mod" != "nominal" ]]; then
                python3 modification_framework/main_modification.py \
                    --path "$out_dir/used_settings" \
                    --eras "$era" \
                    --channels "$channel" \
                    --modification "$mod" \
                    --args "$args"
            fi

            # creating root files
            nice -n 19 python3 scripts/TagAndProbe.py \
                --channel "$channel" \
                --era "$era" \
                --settings-folder "$out_dir/used_settings" \
                --output "$out_dir"

            if [[ "$channel" == "embeddingselection" ]]; then
                nice -n 19 python3 scripts/TagAndProbe.py \
                    --channel "$channel" \
                    --era "$era" \
                    --no-leg-switching \
                    --mode="UPDATE" \
                    --settings-folder "$out_dir/used_settings" \
                    --output "$out_dir"
            fi 

            # fitting root files
            nice -n 19 python3 scripts/runTagAndProbeFits.py \
                --channel "$channel" \
                --era "$era" \
                --fit \
                --plot \
                --settings-folder "$out_dir/used_settings" \
                --output "$out_dir" \
                $( [ "$passfail_hist" = "yes" ] && echo "--passfail_hist yes" )

            # creating jsons
            nice -n 19 python3 scripts/translate_to_crosspog_json.py \
                --era "$era" \
                --channel "$channel" \
                --output "$out_dir" \
                --settings-folder "$out_dir/used_settings"

            # changing json format
            if [[ -d "$out_dir/jsons" ]]; then
                python3 scripts/changing_json_format.py \
                    --input-folder "$out_dir/jsons" \
                    --variation "$var_label"
            fi

        done
    done
done

for dir in output_*; do
    [[ -d "$dir" ]] && mv "$dir" "${dir}.done"
done

final_output="output.done"
mkdir -p "$final_output"
for dir in *.done; do
    [[ -d "$dir" ]] && mv "$dir" "$final_output/"
done

echo "All outputs can be found in $final_output"

# ======================================================
# MERGE JSONS
# ======================================================
merged_dir="$final_output/merged_jsons"
mkdir -p "$merged_dir"

echo "Starting merging JSONs..."
python3 scripts/merge_jsons.py \
    --input-folder "$final_output" \
    --output-folder "$merged_dir"

echo "JSONs merged in $merged_dir"
echo "All done."

