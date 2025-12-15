#!/bin/bash

#############################
# USER SETTINGS
#############################

json_file="muon_2017UL_fullmerge.json"

# either corr_names=("all")
# or: corr_names=("ID_pt_eta_bins" "ISO_pt_eta_bins")
corr_names=("ID_pt_eta_bins")

# welche variation keys sollen geplottet werden?
variation_keys=("nominal" "modify_binnings_pt_up10") # sowas wie: ("nominal" "modify_binnings_pt_up10") oder auch einfach ("all")

categories=("mc" "emb")
outdir="2D_hist_plots"


#############################
# INTERNAL STEPS
#############################

grid_file="grid_tmp.npz"

# 1) Grid erzeugen
python3 json_to_grid.py \
    --json "$json_file" \
    --out "$grid_file"

# 2) Für jede Variation → Plots erzeugen
for variation in "${variation_keys[@]}"; do
    python3 plot_2d_single.py \
        --grid "$grid_file" \
        --json-name "$json_file" \
        --corr-names "${corr_names[@]}" \
        --variation "$variation" \
        --categories "${categories[@]}" \
        --outdir "$outdir"
done

echo "All plots completed."
