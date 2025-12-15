#!/bin/bash

eras=("2017UL")          
channels=("muon") 

settings_dir="settings"
input_files="set_inputfiles.yaml"

#names of the files in the folder: /modification_framework/modifications (no model comparison)
modifications=("nominal" "modify_isotag" "modify_isotag") 
model_comparisons=("modify_binnings")

#same order as in modifications 
mod_args=(
    '{}' 
    '{"percentage":30,"variation":"up"}'    
    '{"percentage":30,"variation":"down"}'                
)
model_comp_args=(
    '{"percentage":10,"variation":"down","axis":"pteta"}'
)

passfail_hist="no" # a pass and fail histogram of every "DY/embedding/data" data for every label in all used eras/channels

#main loop
for idx in "${!modifications[@]}"; do
    mod="${modifications[$idx]}"
    args="${mod_args[$idx]}"

    var_label="$mod"
    if [[ "$args" != "{}" ]]; then
        perc=$(echo "$args" | grep -o '"percentage":[0-9]*' | cut -d':' -f2)
        var=$(echo "$args" | grep -o '"variation":"[^"]*"' | cut -d':' -f2 | tr -d '"')
        axis=$(echo "$args" | grep -o '"axis":"[^"]*"' | cut -d':' -f2 | tr -d '"')
        
        var_label="${mod}"
        [[ -n "$axis" ]] && var_label+="_${axis}"
        [[ -n "$var" ]] && var_label+="_${var}"
        [[ -n "$perc" ]] && var_label+="${perc}"
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

        done
    done
done

echo "modifications: all done."

# echo "STARTING MODEL COMPARISONS"

# # Preparing settings for each model comparison
# for idx in "${!model_comparisons[@]}"; do
#     moccomp_mod="${model_comparisons[$idx]}"
#     moccomp_args="${model_comp_args[$idx]}"

#     moccomp_label="$moccomp_mod"

#     if [[ "$moccomp_args" != "{}" ]]; then
#         perc=$(echo "$moccomp_args" | grep -o '"percentage":[0-9]*' | cut -d':' -f2)
#         var=$(echo "$moccomp_args" | grep -o '"variation":"[^"]*"' | cut -d':' -f2 | tr -d '"')
#         axis=$(echo "$moccomp_args" | grep -o '"axis":"[^"]*"' | cut -d':' -f2 | tr -d '"')

#         [[ -n "$axis" ]] && moccomp_label+="_${axis}"
#         [[ -n "$var" ]] && moccomp_label+="_${var}"
#         [[ -n "$perc" ]] && moccomp_label+="${perc}"
#     fi

#     comp_base_dir="output_model_comp_${moccomp_label}"
#     mkdir -p "$comp_base_dir"

#     echo "Preparing model comparison $moccomp_label"

#     for era in "${eras[@]}"; do
#         for channel in "${channels[@]}"; do

#             comp_dir="$comp_base_dir/${channel}_${era}"
#             mkdir -p "$comp_dir/used_settings"

#             cp -r "$settings_dir"/* "$comp_dir/used_settings/"
#             cp "$input_files" "$comp_dir/used_settings/"

#             settings_file=$(find "$comp_dir/used_settings" -type f -name "*${channel}_${era}.yaml" | head -n 1)

#             if [[ -z "$settings_file" ]]; then
#                 echo "WARNING: settings missing for $channel $era in model comparison $moccomp_label"
#                 continue
#             fi

#             python3 modification_framework/main_modification.py \
#                 --path "$comp_dir/used_settings" \
#                 --eras "$era" \
#                 --channels "$channel" \
#                 --modification "$moccomp_mod" \
#                 --args '{}' \
#                 --restore

#             python3 modification_framework/main_modification.py \
#                 --path "$comp_dir/used_settings" \
#                 --eras "$era" \
#                 --channels "$channel" \
#                 --modification "$moccomp_mod" \
#                 --args "$moccomp_args"

#         done
#     done

#     ./run_model_comp.sh \
#         "$moccomp_label" \
#         "$moccomp_args" \
#         "${eras[*]}" \
#         "${channels[*]}" \
#         "$comp_base_dir"

# done