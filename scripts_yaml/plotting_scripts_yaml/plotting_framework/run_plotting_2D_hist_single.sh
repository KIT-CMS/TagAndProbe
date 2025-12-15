#!/bin/bash

#############################
# USER SETTINGS
#############################

grid_file="scripts_yaml/plotting_scripts_yaml/plotting_framework/results_muon2018UL/muon_2018UL_merged_fullmerge.npz"
json_file="scripts_yaml/plotting_scripts_yaml/plotting_framework/results_muon2018UL/muon_2018UL_merged_fullmerge.json"

# either corr_names=("all")
# or: corr_names=("ID_pt_eta_bins" "ISO_pt_eta_bins")
corr_names=("ID_pt_eta_bins")

# welche variation keys sollen geplottet werden?
variation_keys=("all") # sowas wie: ("nominal" "modify_binnings_pt_up10") oder auch einfach ("all")

categories=("mc" "emb")
outdir="scripts_yaml/plotting_scripts_yaml/plotting_framework/2D_hist_plots"

#############################################

for variation in "${variation_keys[@]}"; do
    python3 scripts_yaml/plotting_scripts_yaml/plotting_framework/plot_2d_single.py \
        --grid "$grid_file" \
        --json-name "$json_file" \
        --corr-names "${corr_names[@]}" \
        --variation "$variation" \
        --categories "${categories[@]}" \
        --outdir "$outdir"
done

echo "All plots completed."
