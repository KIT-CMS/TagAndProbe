# plot_2d.py

import argparse
import os
import numpy as np
import matplotlib.pyplot as plt
import mplhep as hep
from styles_2d import default_2d_style


def extract_2d_values(grid, corr_name, category, value_key):
    entry = grid[corr_name]
    pt_edges = np.array(entry["pt_edges"])
    eta_edges = np.array(entry["eta_edges"])

    eta_bins = entry["eta_bins"]

    # shape [n_eta_bins, n_pt_bins] → wir brauchen [n_pt, n_eta]
    values = np.array([
        [pt_bin[category][value_key] for pt_bin in eta_row]
        for eta_row in eta_bins
    ]).T

    return pt_edges, eta_edges, values


def plot_2d_histogram(pt_edges, eta_edges, values, style, cbar_label, outfile):
    hep.style.use("CMS")
    plt.rcParams['xtick.labelsize'] = style["tick_size"]
    plt.rcParams['ytick.labelsize'] = style["tick_size"]

    fig, ax = plt.subplots(figsize=style["figsize"])

    vmin = style["vmin"]
    vmax = style["vmax"]
    cmap = style["cmap"]

    norm = plt.Normalize(
        vmin=np.nanmin(values) if vmin is None else vmin,
        vmax=np.nanmax(values) if vmax is None else vmax
    )

    mesh = ax.pcolormesh(
        pt_edges,
        eta_edges,
        values.T,
        cmap=cmap,
        norm=norm,
        edgecolors=style["edgecolor"],
        linewidth=style["edgewidth"],
        shading="auto"
    )

    ax.set_xlabel(r"$p_T$ [GeV]", fontsize=style["label_size"], fontweight="bold")
    ax.set_ylabel(r"$|\eta|$",    fontsize=style["label_size"], fontweight="bold")

    # CMS label
    hep.cms.label(ax=ax, label=style["cms_label"], data=True, lumi=style["lumi"], loc=0)

    # log x-scale
    ax.set_xscale("log")

    ax.set_xticks([20, 30, 40, 50, 60, 70, 80, 100, 200])
    ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax.get_xaxis().set_minor_formatter(plt.NullFormatter())

    cbar = plt.colorbar(mesh, ax=ax, pad=0.04)
    cbar.ax.tick_params(labelsize=style["cbar_tick_size"])

    # Standardlabel entfernen
    cbar.set_label("")

    # manuelles zentriertes Label
    cbar.ax.text(
        4.5, 0.5,               # kleine Justierung hängt von Pad und DPI ab
        cbar_label,
        fontsize=style["cbar_label_size"],
        fontweight="bold",
        rotation=90,
        va='center',
        ha='center',
        transform=cbar.ax.transAxes,
)

    plt.tight_layout()
    fig.savefig(outfile, dpi=200)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--grid", required=True, help="npz grid file")
    parser.add_argument("--json-name", required=True, help="json filename to extract era+channel")
    parser.add_argument("--corr-names", required=True, nargs="+", help="'all' or list of correction names")
    parser.add_argument("--variation", required=True, help="nominal or variation key")
    parser.add_argument("--categories", required=True, nargs="+", help="list of categories: mc, emb")
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    npz = np.load(args.grid, allow_pickle=True)
    grid = npz["grid"].item()

    # Korrekte Extraktion der Variationen
    if args.variation == "all":
        detected_vars = set()
        for corr_name in grid:
            corr_data = grid[corr_name]
            # Gehe durch alle eta_bins → pt_bins → Kategorien
            for eta_bin in corr_data.get("eta_bins", []):
                for pt_bin in eta_bin:
                    for category in pt_bin:
                        if category in ["mc", "emb"]:  # Nur gültige Kategorien
                            category_data = pt_bin[category]
                            if isinstance(category_data, dict):
                                detected_vars.update(category_data.keys())
        
        args.variation = sorted(detected_vars)
        print("Detected variations:", args.variation)
        
    base = os.path.basename(args.json_name)
    prefix = base.split("_")
    channel = prefix[0]
    era = prefix[1]

    if "all" in args.corr_names:
        corr_list = list(grid.keys())
    else:
        corr_list = args.corr_names

    os.makedirs(args.outdir, exist_ok=True)

    style = default_2d_style()
    style["cmap"] = "viridis"

    for corr in corr_list:
        if corr not in grid:
            print(f"WARN: correction {corr} not in grid, skipped")
            continue

        for category in args.categories:
            if category not in ["mc", "emb"]:
                print(f"WARN: invalid category {category}, skipped")
                continue

            # variations kann String ("nominal") oder Liste sein (["nominal", ...])
            if isinstance(args.variation, str):
                variations = [args.variation]
            else:
                variations = args.variation

            for variation in variations:
                try:
                    pt_edges, eta_edges, values = extract_2d_values(
                        grid, corr, category, variation
                    )

                    outfile = os.path.join(
                        args.outdir,
                        f"{channel}_{era}_{corr}_{variation}_{category}.png"
                    )

                    plot_2d_histogram(
                        pt_edges,
                        eta_edges,
                        values,
                        style,
                        cbar_label="Scale Factor",
                        outfile=outfile
                    )

                    print(f"Saved {outfile}")
                    
                except Exception as e:
                    print(f"ERROR plotting {corr}/{category}/{variation}: {e}")
                    continue

if __name__ == "__main__":
    main()