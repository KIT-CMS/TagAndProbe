#!/bin/bash


json_file="scripts_yaml/plotting_scripts_yaml/plotting_framework/results_muon2018UL/muon_2018UL_merged_fullmerge.json"
grid_file="scripts_yaml/plotting_scripts_yaml/plotting_framework/results_muon2018UL/muon_2018UL_merged_fullmerge.npz"

corr_names=("ID_pt_eta_bins")
eta_values=("0.1" "0.5" "1.0" "1.5" "2.0" "2.29")
categories=("mc" "emb")
uncertainty_keys=("stat_error" "eta10up" "isotag10up")
show_best_model="true"
y_min="0.955"
y_max="1.013"
outdir="scripts_yaml/plotting_scripts_yaml/plotting_framework/pt_dependence_plots"
mc_emb_separated="yes" #mc and emb in seperated folder, yes or no?

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
            
            python3 scripts_yaml/plotting_scripts_yaml/plotting_framework/plot_pt_dependence.py \
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