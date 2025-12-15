#!/bin/bash

#############################
# USER SETTINGS
#############################

json_file="muon_2017UL_fullmerge.json"
corr_names=("ID_pt_eta_bins")
eta_values=("0.1" "0.5" "1.0" "1.5" "2.0" "2.29")
categories=("mc" "emb")
uncertainty_keys=("stat_error" "modify_binnings_eta_up10" "modify_isotag_up10")
show_best_model="true"
y_min="0.955"
y_max="1.013"
outdir="pt_dependence_plots"
mc_emb_separated="yes" #mc and emb in seperated folder, yes or no?

#############################
# INTERNAL STEPS
#############################

grid_file="grid_tmp.npz"

# 1) Grid erzeugen
echo "Creating grid from JSON..."
python3 json_to_grid.py \
    --json "$json_file" \
    --out "$grid_file"

# 2) Für jede Korrektur, jeden Eta-Wert, jede Kategorie → Plots erzeugen
for corr in "${corr_names[@]}"; do
    for eta in "${eta_values[@]}"; do
        for category in "${categories[@]}"; do
            echo "Plotting: corr=$corr, eta=$eta, category=$category"

            if [[ "$mc_emb_separated" == "yes" ]]; then
                category_outdir="${outdir}/${category}"
            else
                category_outdir="${outdir}"
            fi
            
            mkdir -p "$category_outdir"
            
            python3 plot_pt_dependence.py \
                --grid "$grid_file" \
                --json-name "$json_file" \
                --corr-name "$corr" \
                --eta-value "$eta" \
                --category "$category" \
                --uncertainty-keys "${uncertainty_keys[@]}" \
                --show-best-model "$show_best_model" \
                --y-min "$y_min" \
                --y-max "$y_max" \
                --outdir "$category_outdir"
        done
    done
done

echo "All pT dependence plots completed."