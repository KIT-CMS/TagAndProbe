import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, LogNorm
plt.rcParams.update({
    "text.usetex": True,  # Matplotlib benutzt externes LaTeX
    "font.family": "serif",  # oder 'sans-serif' je nach Wunsch
    "text.latex.preamble": r"\usepackage{amsbsy}"
})
import mplhep as hep
import seaborn as sns

# CMS-Stil
hep.style.use("CMS")

# Standardpaletten
DEFAULT_PALETTES = {
    "blue": ["#f7fbff", "#deebf7", "#9ecae1", "#3182bd", "#08519c"],
    "red": ["#fff5f0", "#fcbba1", "#fb6a4a", "#cb181d", "#67000d"],
    "green": ["#f7fcf5", "#c7e9c0", "#74c476", "#238b45", "#00441b"],
    "purple": ["#f7f0ff", "#d1b7f4", "#a077e9", "#5c1cb7", "#43128c"]
}

def get_color_palette(colors, use_log=False, n_steps=256, name="custom"):
    colors = np.array(colors)
    if use_log:
        positions = np.logspace(0, 1, len(colors), base=10)
        positions = (positions - positions.min()) / (positions.max() - positions.min())
    else:
        positions = np.linspace(0, 1, len(colors))
    return LinearSegmentedColormap.from_list(name, list(zip(positions, colors)), N=n_steps)

def setup_plot(ax, xlabel, ylabel, log_x=False, log_y=False, tick_step_x=None, tick_step_y=None):
    # Achsenskalierung
    if log_x: ax.set_xscale('log')
    if log_y: ax.set_yscale('log')

    # Gitterlinien & Stil
    ax.grid(True, which="both", alpha=0.25, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Achsenbeschriftungen
    ax.set_xlabel(xlabel, fontsize=16, fontweight='bold', labelpad=12)
    ax.set_ylabel(ylabel, fontsize=16, fontweight='bold', labelpad=12)
    ax.tick_params(axis='both', labelsize=13)

    # Ticks falls gewünscht
    if tick_step_x is not None and not log_x:
        start, end = ax.get_xlim()
        ax.set_xticks(np.arange(start, end + tick_step_x, tick_step_x))
    if tick_step_y is not None and not log_y:
        start, end = ax.get_ylim()
        ax.set_yticks(np.arange(start, end + tick_step_y, tick_step_y))

def plot_2d_hist(x_bins, y_bins, values,
                 xlabel=r"$\pmb{p_T}$ \textbf{[GeV]}", ylabel=r"$\pmb{|\eta|}$",
                 title=r"$\chi^2$ Efficiency Map",
                 palette_colors=None, use_log_colors=False,
                 log_x=False, log_y=False, figsize=(9,6),
                 tick_step_x=None, tick_step_y=None,
                 cms_main="CMS", cms_status="Private Work",
                 cms_lumi=r"35.9 fb$^{-1}$ (13 TeV)"):

    sns.set_theme(style="whitegrid")

    if palette_colors is None:
        palette_colors = DEFAULT_PALETTES["blue"]

    cmap = get_color_palette(palette_colors, use_log=use_log_colors)

    fig, ax = plt.subplots(figsize=figsize)

    norm = LogNorm(vmin=np.min(values[values>0]), vmax=np.max(values)) if use_log_colors else None

    # Weiße Kanten zwischen den Bins
    mesh = ax.pcolormesh(x_bins, y_bins, values.T,
                         cmap=cmap, norm=norm,
                         edgecolors='white', linewidth=0.8)

    setup_plot(ax, xlabel, ylabel, log_x=log_x, log_y=log_y,
               tick_step_x=tick_step_x, tick_step_y=tick_step_y)

    # CMS + Private Work nebeneinander, Private Work leicht hochgestellt
    fig.text(0.12, 0.93, rf"\textbf{{{cms_main}}}", fontsize=20, ha="left", va="top")
    fig.text(0.12 + 0.085, 0.921, rf"{cms_status}", fontsize=14, ha="left", va="top")  # etwas höher & enger

    # Mittlerer Titel
    fig.text(0.5, 0.93, title, fontsize=15, ha="center", va="top")

    # Rechts oben Luminosität
    fig.text(0.88, 0.93, rf"{cms_lumi}", fontsize=14, ha="right", va="top")

    # Farbskala
    cbar = plt.colorbar(mesh, ax=ax, pad=0.05)
    cbar.ax.tick_params(labelsize=13)

    # Entferne das Standardlabel
    cbar.set_label("")

    # Manuelles Label mittig platzieren
    cbar.ax.text(
        4.5, 0.5,                # x etwas rechts vom Balken, y = Mitte (in Achsenkoordinaten)
        r"$\pmb{\chi^2}$", 
        fontsize=16,
        fontweight='bold',
        rotation=90,
        va='center', 
        ha='center',
        transform=cbar.ax.transAxes
    )

    plt.subplots_adjust(right=0.88)
    plt.show()


# Beispiel-Daten
# pt_bins = np.linspace(10, 200, 50)      # 50 Bins von 10 bis 200 GeV
# eta_bins = np.linspace(0.0, 2.4, 50)    # 50 Bins in |eta|
# chi2_pass = np.random.uniform(0.7, 1.0, size=(len(pt_bins)-1, len(eta_bins)-1))


# Plot
plot_2d_hist(
    x_bins=pt_bins,
    y_bins=eta_bins,
    values=chi2_pass,
    title=r"$\chi^2$ Efficiency Map",
    palette_colors=DEFAULT_PALETTES["blue"],
    figsize=(10,5),
    tick_step_x=10,
    tick_step_y=0.8
)
