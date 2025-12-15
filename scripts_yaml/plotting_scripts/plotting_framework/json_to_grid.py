# transforms json file to a grid/dict so its easier to use in plots
import json
import numpy as np
import argparse
import os

with open("muon_2017UL_fullmerge.json", "r") as f:
    json_data = json.load(f)
    
def extract_sf_eta_pt_grid(json_data):
    """
    Gibt Dictionary zurück:
      result[correction_name] = {
          "pt_edges": [...],
          "eta_edges": [...],
          "eta_bins": [
              [ { "mc": {...}, "emb": {...} },  # alle pt bins für eta 0
                { ... },
                ... ],
              [ ... ],  # eta 1
              ...
          ]
      }
    """
    result = {}

    for corr in json_data.get("corrections", []):
        corr_name = corr.get("name")
        data = corr.get("data")

        if data.get("nodetype") != "binning" or "content" not in data:
            continue

        pt_edges = data.get("edges", [])
        pt_bins = data["content"]  # obere Ebene: pT
        # n_eta_bins aus dem ersten pT-Bin bestimmen
        num_eta_bins = len(pt_bins[0]["content"])

        # Die η-Kanten aus dem ersten pT-Bin lesen
        eta_edges = pt_bins[0].get("edges", [])

        eta_grid = []

        for eta_idx in range(num_eta_bins):
            pt_list = []

            for pt_bin in pt_bins:
                eta_bin = pt_bin["content"][eta_idx]
                cat_dict = {}

                for cat in eta_bin.get("content", []):  # "mc" / "emb"
                    key = cat["key"]
                    values = cat.get("value", {}).get("content", [])
                    val_dict = {v["key"]: v["value"] for v in values}
                    cat_dict[key] = val_dict

                pt_list.append(cat_dict)

            eta_grid.append(pt_list)

        result[corr_name] = {
            "pt_edges": pt_edges,
            "eta_edges": eta_edges,
            "eta_bins": eta_grid
        }

    return result

# extract_grid.py

def extract_sf_eta_pt_grid(json_data):
    result = {}

    for corr in json_data.get("corrections", []):
        corr_name = corr.get("name")
        data = corr.get("data")

        if data.get("nodetype") != "binning" or "content" not in data:
            continue

        pt_edges = data.get("edges", [])
        pt_bins = data["content"]
        num_eta_bins = len(pt_bins[0]["content"])
        eta_edges = pt_bins[0].get("edges", [])

        eta_grid = []

        for eta_idx in range(num_eta_bins):
            pt_list = []
            for pt_bin in pt_bins:
                eta_bin = pt_bin["content"][eta_idx]
                cat_dict = {}
                for cat in eta_bin.get("content", []):
                    key = cat["key"]
                    values = cat.get("value", {}).get("content", [])
                    val_dict = {v["key"]: v["value"] for v in values}
                    cat_dict[key] = val_dict
                pt_list.append(cat_dict)
            eta_grid.append(pt_list)

        result[corr_name] = {
            "pt_edges": pt_edges,
            "eta_edges": eta_edges,
            "eta_bins": eta_grid
        }

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, help="path to input json")
    parser.add_argument("--out", required=True, help="output .npz file for grid")
    args = parser.parse_args()

    with open(args.json, "r") as f:
        data = json.load(f)

    grid = extract_sf_eta_pt_grid(data)

    # speichere alles als numpy-kompatible npz
    np.savez(args.out, grid=grid)

    print(f"Grid saved to {args.out}")

if __name__ == "__main__":
    main()
