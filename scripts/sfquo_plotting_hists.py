# -*- coding: utf-8 -*-
import os
import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap

plt.rcParams["text.usetex"] = True


def plot_sf_ratio(file_path, output_dir=".", vmin=None, vmax=None, comp_mode=False):
    """
    Liest eine SFQuo-Datei und erstellt ein 2D-Plot (pt vs eta).
    Optional kann vmin/vmax für eine globale Farbskala angegeben werden.
    """
    fname = os.path.basename(file_path)

    # --- Infos aus Dateiname extrahieren ---
    parts = fname.replace(".txt", "").split("_")
    model = parts[1] if len(parts) > 1 else "model"
    typ   = "embedding" if "emb" in parts else "MC"
    var   = "up" if "up" in parts else "down"
    era = [p for p in parts if "UL" in p][0] if any("UL" in p for p in parts) else "unknown"

    # --- Daten einlesen ---
    data = np.loadtxt(file_path, comments="#")
    pt_low, pt_high = data[:,0], data[:,1]
    eta_low, eta_high = data[:,2], data[:,3]
    sf_ratio = data[:,4]

    # Bin-Grenzen
    x_bins = np.unique(np.concatenate([pt_low, pt_high]))
    y_bins = np.unique(np.concatenate([eta_low, eta_high]))

    # 2D-Werte befüllen
    values = np.zeros((len(x_bins)-1, len(y_bins)-1))
    for i in range(len(data)):
        x_idx = np.where(x_bins == pt_low[i])[0][0]
        y_idx = np.where(y_bins == eta_low[i])[0][0]
        values[x_idx, y_idx] = sf_ratio[i]

    # --- Colormap zentriert um 1 ---
    if vmin is None or vmax is None:
        max_dev = max(np.max(values)-1, 1-np.min(values))
        vmin_plot = 1 - max_dev
        vmax_plot = 1 + max_dev
    else:
        vmin_plot = vmin
        vmax_plot = vmax
    norm = TwoSlopeNorm(vmin=vmin_plot, vcenter=1, vmax=vmax_plot)
    cmap = LinearSegmentedColormap.from_list("blue_white_red", ["blue", "white", "red"])

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(10,6))
    mesh = ax.pcolormesh(x_bins, y_bins, values.T, cmap=cmap, norm=norm,
                         edgecolors='white', linewidth=0.5)

    ax.set_xlabel(r"$p_T$ bins [GeV]", fontsize=12, fontweight='bold')
    ax.set_ylabel(r"$\eta$ bins", fontsize=12, fontweight='bold')

    cbar = plt.colorbar(mesh, ax=ax)
    cbar.set_label(r"Quotient $\displaystyle \frac{SF_{norm}}{SF_{var}}$", fontsize=10)

    ax.grid(True, which="both", alpha=0.2, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()

    out_fname = fname.replace(".txt", "_comp.png") if comp_mode else fname.replace(".txt", ".png")
    out_path = os.path.join(output_dir, out_fname)
    plt.savefig(out_path, dpi=300)
    plt.close(fig)
    print(f"Plot gespeichert: {out_path}")



def main():
    parser = argparse.ArgumentParser(description="Plot SFQuo scale factor ratio maps.")
    parser.add_argument("--folder", required=True, help="Ordner mit SFQuo Dateien")
    parser.add_argument("--outdir", required=True, help="Ordner zum Speichern der Plots")
    parser.add_argument("--mode", choices=["nocomp", "comp"], default="nocomp", help="Vergleichsmodus für Farbskala")

    args = parser.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    # Alle relevanten Dateien finden
    file_list = [os.path.join(args.folder, f) for f in os.listdir(args.folder)
                 if f.startswith("SFQuo") and f.endswith(".txt")]

    if args.mode == "comp":
        # --- globale Min/Max über alle Dateien ---
        global_min = float('inf')
        global_max = float('-inf')
        for file_path in file_list:
            data = np.loadtxt(file_path, comments="#")
            sf_ratio = data[:,4]
            global_min = min(global_min, sf_ratio.min())
            global_max = max(global_max, sf_ratio.max())
        max_dev = max(global_max-1, 1-global_min)
        vmin_global = 1 - max_dev
        vmax_global = 1 + max_dev

        # Plots erstellen mit globaler Farbskala
        for file_path in file_list:
            plot_sf_ratio(file_path, args.outdir, vmin=vmin_global, vmax=vmax_global, comp_mode=True)
    else:
        # normale Einzel-Plot-Farbskala
        for file_path in file_list:
            plot_sf_ratio(file_path, args.outdir)

main()


