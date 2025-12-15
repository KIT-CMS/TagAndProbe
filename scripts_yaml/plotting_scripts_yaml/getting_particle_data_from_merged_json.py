import json

with open("muon_2017UL_merged.json", "r") as f:
    json_data = json.load(f)
    
def extract_sf_eta_pt_grid(json_data):
    result = {}

    for corr in json_data.get("corrections", []):
        corr_name = corr.get("name")
        data = corr.get("data")

        if data.get("nodetype") != "binning" or "content" not in data:
            continue

        pt_bins = data["content"]  # obere Ebene: pt
        # Anzahl der eta-Bins bestimmen
        num_eta_bins = len(pt_bins[0]["content"])
        eta_grid = []

        for eta_idx in range(num_eta_bins):
            pt_list = []

            for pt_bin in pt_bins:
                eta_bin = pt_bin["content"][eta_idx]
                cat_dict = {}

                for cat in eta_bin.get("content", []):  # z.B. "mc" oder "emb"
                    key = cat["key"]
                    values = cat.get("value", {}).get("content", [])
                    val_dict = {v["key"]: v["value"] for v in values}
                    cat_dict[key] = val_dict

                pt_list.append(cat_dict)

            eta_grid.append(pt_list)

        result[corr_name] = eta_grid

    return result
