# plot_pt_dependence.py

import argparse
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, FixedLocator
import mplhep as hep
import math
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from styles_pt import default_pt_plot_style

# def default_pt_plot_style():
#     return {
#         "xscale": "linear",
#         "broken_axis": True,
#         "x_lin_min": 10,
#         "x_lin_max": 40,
#         "x_log_min": 40,
#         "x_log_max": 200,
#         "broken_axis_gap": 0.000,
#         "xlabel": r"$p_T$ [GeV]",
#         "ylabel": "Scale Factor",
#         "title": r"Nominal SF vs. $p_T$",
#         "color": "C0",
#         "marker": "o",
#         "figsize": (15, 8),
#         "label_size": 22,
#         "tick_size": 17,
#         "title_size_main": 20,
#         "title_size": 15,
#         "cms_label": "Preliminary",
#         "lumi": 59.8,
#         "com": 13,
#         "bin_edge_color": "darkgreen",
#         "bin_edge_height_frac": 0.03,
#         "point_size": 6,
#         "grid_style": {"linestyle": "--", "linewidth": 0.8, "alpha": 0.3},
#         "spine_width": 0.8,
#         "tick_direction": "in",
#         "tick_length": 4,
#         "legend_frame_alpha": 0.25,
#         "legend_frame_color": "black",
#         # Parameter für Errorbars
#         "stat_error_color": "black",
#         "total_error_color": "red", 
#         "stat_error_width": 4.0,
#         "total_error_width": 1.0,
#         # Parameter für best_model Rechtecke
#         "best_model_color": "blue",
#         "best_model_alpha": 0.3,
#         "best_model_edge_color": "darkorange", 
#         "best_model_edge_width": 1.0,
#     }

def extract_2d_values(grid, corr_name, category, value_key):
    """Extrahiert 2D-Werte aus dem Grid - gleiche Funktion wie in plot_2d.py"""
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

def build_xy_and_combined_error(pt_edges, eta_bin, category, uncertainty_keys):
    """Gibt (x_values, y_values, combined_errors) zurück."""
    x_vals = []
    y_vals = []
    errs = []

    n_bins = len(pt_edges) - 1
    for i in range(n_bins):
        if category not in eta_bin[i]:
            continue
        vals = eta_bin[i][category]
        nominal = vals.get("nominal", np.nan)
        # build stat
        stat = 0.0
        if "stat_error" in uncertainty_keys:
            stat = float(vals.get("stat_error", 0.0)) if vals.get("stat_error", None) is not None else 0.0

        # build sys contributions
        sys_sq_sum = 0.0
        for key in uncertainty_keys:
            if key == "stat_error":
                continue
            v = vals.get(key, None)
            if v is None:
                continue
            try:
                sys_contrib = abs(float(v) - float(nominal))
            except Exception:
                sys_contrib = 0.0
            sys_sq_sum += sys_contrib * sys_contrib

        combined = math.sqrt(stat * stat + sys_sq_sum)

        pt_low, pt_high = pt_edges[i], pt_edges[i + 1]
        pt_center = 0.5 * (pt_low + pt_high)

        x_vals.append(pt_center)
        y_vals.append(nominal)
        errs.append(combined)

    return np.array(x_vals), np.array(y_vals), np.array(errs)

def build_xy_and_stat_error(pt_edges, eta_bin, category):
    """Gibt (x_values, y_values, stat_errors) zurück - nur statistische Fehler."""
    x_vals = []
    y_vals = []
    stat_errs = []

    n_bins = len(pt_edges) - 1
    for i in range(n_bins):
        if category not in eta_bin[i]:
            continue
        vals = eta_bin[i][category]
        nominal = vals.get("nominal", np.nan)
        
        stat = float(vals.get("stat_error", 0.0)) if vals.get("stat_error", None) is not None else 0.0

        pt_low, pt_high = pt_edges[i], pt_edges[i + 1]
        pt_center = 0.5 * (pt_low + pt_high)

        x_vals.append(pt_center)
        y_vals.append(nominal)
        stat_errs.append(stat)

    return np.array(x_vals), np.array(y_vals), np.array(stat_errs)

def extract_best_model_uncertainties(pt_edges, eta_bin, category):
    """Extrahiert die best_model Unsicherheiten als Rechtecke."""
    best_model_rectangles = []
    
    n_bins = len(pt_edges) - 1
    for i in range(n_bins):
        if category not in eta_bin[i]:
            continue
            
        vals = eta_bin[i][category]
        
        if ('best_model_nominal' not in vals or 
            'best_model_stat_up' not in vals or 
            'best_model_syst_up' not in vals):
            continue
            
        nominal = vals.get('best_model_nominal')
        stat_up = vals.get('best_model_stat_up')
        syst_up = vals.get('best_model_syst_up')
        
        if nominal is None or stat_up is None or syst_up is None:
            continue
            
        try:
            nominal_val = float(nominal)
            stat_up_val = float(stat_up)
            syst_up_val = float(syst_up)
        except (ValueError, TypeError):
            continue
            
        pt_low, pt_high = pt_edges[i], pt_edges[i + 1]
        total_error = math.sqrt(stat_up_val**2 + syst_up_val**2)
        
        best_model_rectangles.append({
            'pt_low': pt_low,
            'pt_high': pt_high,
            'nominal': nominal_val,
            'stat_up': stat_up_val,
            'syst_up': syst_up_val,
            'total_error': total_error
        })
    
    return best_model_rectangles

def plot_pt_dependence_single(
    grid,
    corr_name,
    eta_value,
    category="mc",
    style=None,
    y_min=None,
    y_max=None,
    uncertainty_keys=None,
    show_best_model=True,
    outfile=None
):
    """Plottet pT-Abhängigkeit für einen einzelnen Eta-Bin und speichert als Datei."""
    
    if style is None:
        style = default_pt_plot_style()

    if corr_name not in grid:
        raise KeyError(f"Correction '{corr_name}' nicht im Grid gefunden.")
    corr = grid[corr_name]

    eta_edges = np.array(corr["eta_edges"])
    pt_edges = np.array(corr["pt_edges"])
    eta_bins = corr["eta_bins"]

    eta_idx = None
    for i in range(len(eta_edges) - 1):
        if eta_edges[i] <= abs(float(eta_value)) < eta_edges[i + 1]:
            eta_idx = i
            break
    if eta_idx is None:
        raise ValueError(f"|eta|={abs(float(eta_value))} liegt außerhalb der Bins {eta_edges}")

    eta_bin = eta_bins[eta_idx]

    if uncertainty_keys is None:
        uncertainty_keys = ["stat_error"]

    # Berechne beide Fehlertypen
    x_values, y_values, total_errs = build_xy_and_combined_error(pt_edges, eta_bin, category, uncertainty_keys)
    x_values_stat, y_values_stat, stat_errs = build_xy_and_stat_error(pt_edges, eta_bin, category)

    # Extrahiere best_model Unsicherheiten
    best_model_rectangles = []
    if show_best_model:
        best_model_rectangles = extract_best_model_uncertainties(pt_edges, eta_bin, category)

    # Stelle sicher, dass beide Arrays die gleichen Datenpunkte haben
    if not np.array_equal(x_values, x_values_stat) or not np.array_equal(y_values, y_values_stat):
        common_mask = np.isin(x_values, x_values_stat)
        x_values = x_values[common_mask]
        y_values = y_values[common_mask]
        total_errs = total_errs[common_mask]
        stat_mask = np.isin(x_values_stat, x_values)
        x_values_stat = x_values_stat[stat_mask]
        y_values_stat = y_values_stat[stat_mask]
        stat_errs = stat_errs[stat_mask]

    hep.style.use("CMS")
    plt.rcParams['xtick.labelsize'] = style["tick_size"]
    plt.rcParams['ytick.labelsize'] = style["tick_size"]

    # Broken axis plot
    fig, (ax_lin, ax_log) = plt.subplots(
        1, 2, figsize=style["figsize"],
        gridspec_kw={'width_ratios': [1, 1],
                     'wspace': style["broken_axis_gap"]}
    )
    ax_log.sharey(ax_lin)

    ax_lin.set_xlim(style["x_lin_min"], style["x_lin_max"])
    ax_log.set_xlim(style["x_log_min"], style["x_log_max"])

    ax_lin.set_xscale("linear")
    ax_log.set_xscale("log")

    # Masks für die Punkte
    mask_lin = (x_values >= style["x_lin_min"]) & (x_values <= style["x_lin_max"])
    mask_log = (x_values >= style["x_log_min"]) & (x_values <= style["x_log_max"])

    # BEST_MODEL RECHTSECKE ZEICHEN
    if show_best_model and best_model_rectangles:
        for rect in best_model_rectangles:
            pt_low, pt_high = rect['pt_low'], rect['pt_high']
            nominal = rect['nominal']
            total_error = rect['total_error']
            
            # Für lineare Achse
            if (style["x_lin_min"] <= pt_low <= style["x_lin_max"] or 
                style["x_lin_min"] <= pt_high <= style["x_lin_max"] or
                (pt_low <= style["x_lin_min"] and pt_high >= style["x_lin_max"])):
                
                rect_low = max(pt_low, style["x_lin_min"])
                rect_high = min(pt_high, style["x_lin_max"])
                
                if rect_high > rect_low:
                    ax_lin.add_patch(plt.Rectangle(
                        (rect_low, nominal - total_error),
                        rect_high - rect_low,
                        2 * total_error,
                        facecolor=style["best_model_color"],
                        edgecolor=style["best_model_edge_color"],
                        linewidth=style["best_model_edge_width"],
                        alpha=style["best_model_alpha"],
                        zorder=1
                    ))
            
            # Für logarithmische Achse
            if (style["x_log_min"] <= pt_low <= style["x_log_max"] or 
                style["x_log_min"] <= pt_high <= style["x_log_max"] or
                (pt_low <= style["x_log_min"] and pt_high >= style["x_log_max"])):
                
                rect_low = max(pt_low, style["x_log_min"])
                rect_high = min(pt_high, style["x_log_max"])
                
                if rect_high > rect_low:
                    ax_log.add_patch(plt.Rectangle(
                        (rect_low, nominal - total_error),
                        rect_high - rect_low,
                        2 * total_error,
                        facecolor=style["best_model_color"],
                        edgecolor=style["best_model_edge_color"],
                        linewidth=style["best_model_edge_width"],
                        alpha=style["best_model_alpha"],
                        zorder=1
                    ))

    # ERRORBARS ZEICHEN
    if np.any(mask_lin):
        ax_lin.errorbar(
            x_values[mask_lin], y_values[mask_lin],
            yerr=total_errs[mask_lin],
            fmt=style["marker"], linestyle="", ms=style["point_size"],
            ecolor=style["total_error_color"], capsize=3, elinewidth=style["total_error_width"], 
            markerfacecolor=style["color"], markeredgecolor=style["color"],
            zorder=3
        )
        ax_lin.errorbar(
            x_values[mask_lin], y_values[mask_lin],
            yerr=stat_errs[mask_lin],
            fmt=style["marker"], linestyle="", ms=style["point_size"],
            ecolor=style["stat_error_color"], capsize=3, elinewidth=style["stat_error_width"],
            markerfacecolor=style["color"], markeredgecolor=style["color"],
            zorder=4
        )
        
    if np.any(mask_log):
        ax_log.errorbar(
            x_values[mask_log], y_values[mask_log],
            yerr=total_errs[mask_log],
            fmt=style["marker"], linestyle="", ms=style["point_size"],
            ecolor=style["total_error_color"], capsize=3, elinewidth=style["total_error_width"],
            markerfacecolor=style["color"], markeredgecolor=style["color"],
            zorder=3
        )
        ax_log.errorbar(
            x_values[mask_log], y_values[mask_log],
            yerr=stat_errs[mask_log],
            fmt=style["marker"], linestyle="", ms=style["point_size"],
            ecolor=style["stat_error_color"], capsize=3, elinewidth=style["stat_error_width"],
            markerfacecolor=style["color"], markeredgecolor=style["color"],
            zorder=4
        )

    # Achsen formatieren
    ax_log.xaxis.set_major_locator(FixedLocator([40, 60, 100, 200]))
    ax_log.xaxis.set_major_formatter(ScalarFormatter())

    for axis in [ax_lin, ax_log]:
        axis.grid(True, axis='x', **style["grid_style"])
        axis.tick_params(axis="both", labelsize=style["tick_size"],
                        direction=style["tick_direction"], length=style["tick_length"], pad=8)
        for spine in axis.spines.values():
            spine.set_linewidth(style["spine_width"])
        axis.set_facecolor("white")

    ax_lin.set_xlabel("")
    ax_lin.set_ylabel(style["ylabel"], fontsize=style["label_size"])

    ax_log.set_xlabel(style["xlabel"], fontsize=style["label_size"])
    ax_log.set_ylabel("")
    ax_log.tick_params(axis="y", which="both", left=False, labelleft=False)

    ax_lin.spines["right"].set_visible(False)
    ax_log.spines["left"].set_visible(False)
    ax_log.spines["left"].set_linestyle("--")

    ax_log.spines["top"].set_visible(False)
    ax_log.spines["bottom"].set_visible(True)
    ax_log.spines["right"].set_visible(True)
    ax_log.spines["right"].set_linewidth(style["spine_width"])
    ax_log.spines["top"].set_visible(True)
    ax_log.spines["top"].set_linewidth(style["spine_width"])

    # Y-Limits setzen
    if y_min is not None and y_max is not None:
        ax_lin.set_ylim(float(y_min), float(y_max))

    ymin_lin, ymax_lin = ax_lin.get_ylim()
    bin_bottom = ymin_lin
    bin_top = ymin_lin + style["bin_edge_height_frac"] * (ymax_lin - ymin_lin)

    # bin edges zeichnen
    for edge in pt_edges:
        if style["x_lin_min"] <= edge <= style["x_lin_max"]:
            ax_lin.plot([edge, edge], [bin_bottom, bin_top],
                        color=style["bin_edge_color"], lw=1, alpha=0.9, clip_on=True,
                        zorder=5)
        if style["x_log_min"] <= edge <= style["x_log_max"]:
            ax_log.plot([edge, edge], [bin_bottom, bin_top],
                        color=style["bin_edge_color"], lw=1, alpha=0.9, clip_on=True,
                        zorder=5)

    # Legende
    correction_label = f"{corr_name}, |η| in [{eta_edges[eta_idx]:.1f}, {eta_edges[eta_idx+1]:.1f}]"
    
    h_nominal = Line2D([0], [0], marker=style["marker"], linestyle="", 
                      color=style["color"], ms=style["point_size"])
    h_stat_bar = Line2D([0], [0], color=style["stat_error_color"], 
                       linewidth=style["stat_error_width"], marker='', linestyle='-')
    h_total_bar = Line2D([0], [0], color=style["total_error_color"], 
                        linewidth=style["total_error_width"], marker='', linestyle='-')
    h_edges = Line2D([0], [0], color=style["bin_edge_color"], linewidth=2, linestyle='-')
    h_corr = Line2D([0], [0], color='none', marker='', linestyle='')

    legend_elements = [h_corr, h_nominal, h_stat_bar, h_total_bar, h_edges]
    legend_labels = [correction_label, "nominal values", "stat. uncertainty", 
                    "stat. and syst. uncertainty", "pT bin edges"]
    
    if show_best_model and best_model_rectangles:
        h_best_model = Patch(facecolor=style["best_model_color"], 
                           edgecolor=style["best_model_edge_color"],
                           alpha=style["best_model_alpha"], label='Best Model Uncertainty')
        legend_elements.append(h_best_model)
        legend_labels.append("Best Model Uncertainty")

    leg = ax_log.legend(
        legend_elements,
        legend_labels,
        fontsize=style["label_size"] - 2,
        frameon=True,
        loc="lower right",
    )
    leg.get_frame().set_alpha(style["legend_frame_alpha"])
    leg.get_frame().set_edgecolor(style["legend_frame_color"])

    # Titel & CMS Label
    fig.suptitle(style["title"], fontsize=style["title_size_main"], y=0.98)
    hep.cms.label(ax=ax_lin, label=style["cms_label"], data=True, 
                  lumi=style["lumi"], loc=0)

    # Entferne doppelte Texte
    for text in list(ax_lin.texts):
        if ('TeV' in text.get_text()) or ('fb' in text.get_text()):
            text.set_text("")

    hep.cms.label(ax=ax_log, label=" ", data=False, lumi=style["lumi"], loc=0)
    for text in list(ax_log.texts):
        content = text.get_text()
        if ("TeV" not in content) and ("fb" not in content):
            text.remove()

    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    
    # Speichern statt anzeigen
    if outfile:
        plt.savefig(outfile, dpi=300, bbox_inches='tight')
        print(f"Saved: {outfile}")
    else:
        plt.show()
    
    plt.close(fig)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--grid", required=True, help="npz grid file")
    parser.add_argument("--json-name", required=True, help="json filename to extract era+channel")
    parser.add_argument("--corr-name", required=True, help="correction name")
    parser.add_argument("--eta-value", required=True, type=float, help="eta value for the slice")
    parser.add_argument("--category", required=True, help="category: mc or emb")
    parser.add_argument("--uncertainty-keys", nargs="+", default=["stat_error"], 
                       help="list of uncertainty keys")
    parser.add_argument("--show-best-model", type=lambda x: x.lower() == "true", default=True,
                       help="show best model uncertainties (true/false)")
    parser.add_argument("--y-min", type=float, help="y-axis minimum")
    parser.add_argument("--y-max", type=float, help="y-axis maximum")
    parser.add_argument("--outdir", required=True, help="output directory")
    args = parser.parse_args()

    npz = np.load(args.grid, allow_pickle=True)
    grid = npz["grid"].item()

    # Dateiname erstellen
    base = os.path.basename(args.json_name)
    prefix = base.split("_")
    channel = prefix[0]
    era = prefix[1]

    os.makedirs(args.outdir, exist_ok=True)

    # Finde den tatsächlichen Eta-Bin-Bereich
    corr_data = grid[args.corr_name]
    eta_edges = np.array(corr_data["eta_edges"])
    
    eta_idx = None
    for i in range(len(eta_edges) - 1):
        if eta_edges[i] <= abs(float(args.eta_value)) < eta_edges[i + 1]:
            eta_idx = i
            break
    
    if eta_idx is None:
        raise ValueError(f"|eta|={abs(float(args.eta_value))} liegt außerhalb der Bins {eta_edges}")

    # Eta-Bin-Bereich für den Dateinamen
    eta_bin_low = eta_edges[eta_idx]
    eta_bin_high = eta_edges[eta_idx + 1]
    eta_bin_str = f"eta[{eta_bin_low:.1f}to{eta_bin_high:.1f}]"

    # Uncertainty-Keys für den Dateinamen (mit Unterstrichen verbunden)
    uncertainty_str = "_".join(args.uncertainty_keys)

    # Best-Model zur Uncertainty-String hinzufügen falls aktiviert
    if args.show_best_model:
        if uncertainty_str:  # Falls schon Uncertainty-Keys vorhanden
            uncertainty_str += "_bestmodel"
        else:  # Falls nur best_model
            uncertainty_str = "bestmodel"

    outfile = os.path.join(
        args.outdir,
        f"{channel}_{era}_{args.corr_name}_{eta_bin_str}_{args.category}_{uncertainty_str}_pt_dependence.png"
    )

    # Style anpassen
    style = default_pt_plot_style()
    
    # Best Model Farbe anpassen (wie in deinem Beispiel)
    both_colors = "darkgreen"
    style["best_model_color"] = both_colors
    style["best_model_alpha"] = 0.7
    style["best_model_edge_color"] = both_colors

    try:
        plot_pt_dependence_single(
            grid=grid,
            corr_name=args.corr_name,
            eta_value=args.eta_value,
            category=args.category,
            style=style,
            y_min=args.y_min,
            y_max=args.y_max,
            uncertainty_keys=args.uncertainty_keys,
            show_best_model=args.show_best_model,
            outfile=outfile
        )
    except Exception as e:
        print(f"ERROR plotting {args.corr_name}/eta{args.eta_value}/{args.category}: {e}")

if __name__ == "__main__":
    main()