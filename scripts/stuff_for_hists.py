import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap, LogNorm
import os

def plot_2d_hist(x_bins, y_bins, values,
                       xlabel="pT [GeV]", ylabel="|eta|",
                       title="Effizienz 2D",
                       output_file="efficiency_map.png",
                       log_x=False, log_y=False,
                       ctype="pass",
                       log_color = True):
    """
    Zeichnet ein 2D-Histogramm (pt vs eta) mit optional logarithmischen Achsen
    und Farbschema abhängig von 'ctype' ('pass' -> blau, 'fail' -> rot, 'passfail' -> lila).

    Parameters
    ----------
    x_bins, y_bins : array-like
        Bin-Grenzen der Achsen (müssen >0 sein, wenn log_x/log_y=True).
    values : 2D array
        Effizienzwerte [len(x_bins)-1, len(y_bins)-1].
    ctype : str
        'pass', 'fail' oder 'passfail' für die Farbpalette.
    """

    plt.style.use('seaborn-whitegrid')
    sns.set_palette("husl")

    # --- Farbpaletten definieren ---
    if ctype.lower() == "pass":
        colors = ["#f7feff", "#deebf7", "#c6dbef", "#9ecae1",
                  "#6baed6", "#4292c6", "#2171b5", "#08519c", "#08306b"]
    elif ctype.lower() == "fail":
        colors = ["#fff5f0", "#fee0d2", "#fcbba1", "#fc9272",
                  "#fb6a4a", "#ef3b2c", "#cb181d", "#a50f15", "#67000d"]
    elif ctype.lower() == "passfail":
        # Magenta/Lila-Palette (Richtung Mangan-Lila)
        colors = ["#f7f0ff", "#e8d9fa", "#d1b7f4", "#b998ef",
                  "#a077e9", "#894ee3", "#7326dd", "#5c1cb7", "#43128c"]
    else:
        raise ValueError("ctype muss 'pass', 'fail' oder 'passfail' sein")

    custom_cmap = LinearSegmentedColormap.from_list('custom_map', colors, N=256)

    fig, ax = plt.subplots(figsize=(10, 6))

    if log_color:
        min_val = np.min(values[values > 0]) if np.any(values > 0) else 1e-6
        norm = LogNorm(vmin=min_val, vmax=np.max(values))
    else:
        norm = None

    # 2D-Plot
    mesh = ax.pcolormesh(x_bins, y_bins, values.T, cmap=custom_cmap, norm=norm,
                         edgecolors='white', linewidth=0.5)

    # Optionale Log-Skalen
    if log_x:
        ax.set_xscale('log')
    if log_y:
        ax.set_yscale('log')

    # Achsenbeschriftung und Titel
    ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold')

    # Farbbalken
    cbar = plt.colorbar(mesh, ax=ax)
    cbar.set_label('Chi2', fontsize=10)

    # Gitter und Rahmen
    ax.grid(True, which="both", alpha=0.2, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close(fig)

def make_chi2_maps(chi2_pass_array, 
                   chi2_fail_array,
                   pt_bins_set, 
                   eta_bins_set,
                   output_dir,
                   plot_2d_hist_func):
    # --- Binning sortieren ---
    pt_bins = np.array(sorted(pt_bins_set))
    eta_bins = np.array(sorted(eta_bins_set))

    # Leere Grids
    chi2_pass_grid = np.zeros((len(pt_bins)-1, len(eta_bins)-1))
    chi2_fail_grid = np.zeros((len(pt_bins)-1, len(eta_bins)-1))

    # Pass-Werte befüllen
    for (pt_bin, eta_bin, val) in chi2_pass_array:
        ix = np.where(pt_bins == pt_bin[0])[0][0]
        iy = np.where(eta_bins == eta_bin[0])[0][0]
        chi2_pass_grid[ix, iy] = val

    # Fail-Werte befüllen
    for (pt_bin, eta_bin, val) in chi2_fail_array:
        ix = np.where(pt_bins == pt_bin[0])[0][0]
        iy = np.where(eta_bins == eta_bin[0])[0][0]
        chi2_fail_grid[ix, iy] = val

    # Sicherstellen, dass Output-Ordner existiert
    os.makedirs(output_dir, exist_ok=True)

    # --- Plots erstellen ---
    plot_2d_hist_func(
        x_bins=pt_bins,
        y_bins=eta_bins,
        values=chi2_pass_grid,
        title="Chi² Map - PASS",
        output_file=os.path.join(output_dir, "chi2_pass_map.png"),
        ctype="pass"
    )

    plot_2d_hist_func(
        x_bins=pt_bins,
        y_bins=eta_bins,
        values=chi2_fail_grid,
        title="Chi² Map - FAIL",
        output_file=os.path.join(output_dir, "chi2_fail_map.png"),
        ctype="fail"
    )

# # --- Dummy-Binning ---
# pt_bins_set = [10, 20, 40, 80]      # z. B. pT-Bins in GeV
# eta_bins_set = [0.0, 0.8, 1.6, 2.4] # |eta|-Bins

# # --- Zufallswerte für PASS und FAIL ---
# # Jede Zeile: ((pt_bin_low, pt_bin_high), (eta_bin_low, eta_bin_high), wert)
# chi2_pass_array = []
# chi2_fail_array = []

# for i in range(len(pt_bins_set)-1):
#     for j in range(len(eta_bins_set)-1):
#         pt_bin = (pt_bins_set[i], pt_bins_set[i+1])
#         eta_bin = (eta_bins_set[j], eta_bins_set[j+1])
#         val_pass = np.random.uniform(0.7, 1.0)  # z. B. Effizienz 70-100%
#         val_fail = np.random.uniform(0.0, 0.3)  # Fail-Werte 0-30%
#         chi2_pass_array.append((pt_bin, eta_bin, val_pass))
#         chi2_fail_array.append((pt_bin, eta_bin, val_fail))

# # --- Output-Verzeichnis ---
# output_dir = "AHHHHHHHHHHHHHHHHHHHHHHHHHHHH"
# os.makedirs(output_dir, exist_ok=True)

# # --- Aufruf der Plotfunktion ---
# make_chi2_maps(
#     chi2_pass_array=chi2_pass_array,
#     chi2_fail_array=chi2_fail_array,
#     pt_bins_set=pt_bins_set,
#     eta_bins_set=eta_bins_set,
#     output_dir=output_dir,
#     plot_2d_hist_func=plot_2d_hist
# )

# print(f"Plots gespeichert in: {output_dir}")