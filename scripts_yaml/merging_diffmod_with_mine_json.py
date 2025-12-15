#!/usr/bin/env python3
import json
import argparse
import sys

# mapping of names from the second json
RENAME = {
    "nominal": "best_model_nominal",
    "stat_up": "best_model_stat_up",
    "stat_down": "best_model_stat_down",
    "syst_up": "best_model_syst_up",
    "syst_down": "best_model_syst_down",
}


def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Could not load {path}: {e}")
        sys.exit(1)


def find_category(node, input_name):
    """
    Recursively search for node with nodetype:'category' and input==input_name.
    """
    if isinstance(node, dict):
        if node.get("nodetype") == "category" and node.get("input") == input_name:
            return node
        if isinstance(node.get("content"), list):
            for c in node["content"]:
                out = find_category(c, input_name)
                if out is not None:
                    return out
    return None


def extract_best_model_block(other_category):
    """
    Other category has input='uncertainty'.
    Remove syst2 and rename keys.
    Returns a list of dicts: [{"key":..., "value":...}, ...]
    """
    result = []
    for entry in other_category.get("content", []):
        key = entry.get("key")
        if key == "syst2":
            continue
        if key not in RENAME:
            continue
        renamed = RENAME[key]
        result.append({
            "key": renamed,
            "value": entry.get("value")
        })
    return result


def merge_into_my_category(my_cat, other_cat):
    """
    my_cat: category with input='values'
    other_cat: category with input='uncertainty'
    """
    add_entries = extract_best_model_block(other_cat)
    my_cat["content"].extend(add_entries)


def merge_jsons(my_json, other_json):
    """
    Merges content of other_json into my_json.
    Both follow the correction->binning->eta->type tree.
    """
    my_corrs = {c["name"]: c for c in my_json.get("corrections", [])}
    other_corrs = {c["name"]: c for c in other_json.get("corrections", [])}

    for name, my_corr in my_corrs.items():
        if name not in other_corrs:
            continue

        other_corr = other_corrs[name]

        my_pt_bins = my_corr["data"]["content"]
        other_pt_bins = other_corr["data"]["content"]

        # iterate pt bins
        for idx_pt, my_eta_block in enumerate(my_pt_bins):
            if idx_pt >= len(other_pt_bins):
                continue

            other_eta_block = other_pt_bins[idx_pt]

            my_eta_bins = my_eta_block["content"]
            other_eta_bins = other_eta_block["content"]

            # iterate eta bins
            for idx_eta, my_type_block in enumerate(my_eta_bins):
                if idx_eta >= len(other_eta_bins):
                    continue

                other_type_block = other_eta_bins[idx_eta]

                my_types = {t["key"]: t for t in my_type_block["content"]}
                other_types = {t["key"]: t for t in other_type_block["content"]}

                # merge mc and emb blocks
                for flv in ("mc", "emb"):
                    if flv not in my_types or flv not in other_types:
                        continue

                    my_values_cat = find_category(my_types[flv]["value"], "values")
                    other_uncert_cat = find_category(other_types[flv]["value"], "uncertainty")

                    if my_values_cat is None or other_uncert_cat is None:
                        continue

                    merge_into_my_category(my_values_cat, other_uncert_cat)

    return my_json


def main():
    parser = argparse.ArgumentParser(description="Merge two correction JSON files.")
    parser.add_argument("--mine", required=True, help="Your JSON file (base)")
    parser.add_argument("--other", required=True, help="Other JSON file (best model)")
    parser.add_argument("--out", required=True, help="Output merged JSON file")

    args = parser.parse_args()

    my_json = load_json(args.mine)
    other_json = load_json(args.other)

    merged = merge_jsons(my_json, other_json)

    with open(args.out, "w") as f:
        json.dump(merged, f, indent=2)

    print(f"Merged JSON written to {args.out}")

main()
