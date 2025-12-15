# -*- coding: utf-8 -*-
import os
import json
import argparse

def export_sf_tables(json_path, out_dir):
    """
    Exportiert SF-Daten aus JSON-Datei in Textdateien für 'mc' und 'emb'.
    """
    with open(json_path, "r") as f:
        data = json.load(f)

    os.makedirs(out_dir, exist_ok=True)

    for corr in data.get("corrections", []):
        name = corr["name"]

        path_mc  = os.path.join(out_dir, f"SF_{name}_mc.txt")
        path_emb = os.path.join(out_dir, f"SF_{name}_emb.txt")

        with open(path_mc, "w") as f_mc, open(path_emb, "w") as f_emb:
            header = "# pt_low pt_high eta_low eta_high scale_factor type\n"
            f_mc.write(header)
            f_emb.write(header)

            pt_edges = corr["data"]["edges"]
            pt_bins  = corr["data"]["content"]

            for i_pt, pt_bin in enumerate(pt_bins):
                pt_low, pt_high = pt_edges[i_pt], pt_edges[i_pt+1]

                eta_edges = pt_bin["edges"]
                categories = pt_bin["content"]

                for j_eta, cat in enumerate(categories):
                    eta_low, eta_high = eta_edges[j_eta], eta_edges[j_eta+1]

                    for entry in cat["content"]:
                        typ = entry["key"]
                        val = entry["value"]
                        line = "{:.1f} {:.1f} {:.3f} {:.3f} {:.7f} {}\n".format(
                            pt_low, pt_high, eta_low, eta_high, val, typ
                        )
                        if typ == "mc":
                            f_mc.write(line)
                        elif typ == "emb":
                            f_emb.write(line)

    print(f"Dateien wurden geschrieben nach: {out_dir}")


def compute_sf_quo(folder, era="2017UL", typ="emb", model="ID_pt_eta_bins", var="up", out_dir="."):
    """
    Berechnet Quotienten (up/norm oder down/norm) aus vorhandenen SF TXT-Dateien.
    """
    import glob

    os.makedirs(out_dir, exist_ok=True)

    # Suche die Dateien
    files = os.listdir(folder)
    var_file = None
    norm_file = None

    for f in files:
        if era in f and typ in f and model in f and var in f:
            var_file = os.path.join(folder, f)
        if era in f and typ in f and model in f and "norm" in f:
            norm_file = os.path.join(folder, f)

    if not var_file or not norm_file:
        print("Fehler: passende Dateien für var oder norm nicht gefunden!")
        return

    out_file = os.path.join(out_dir, f"SFQuo_{model}_{typ}_{var}_{era}.txt")

    with open(var_file, "r") as fv, open(norm_file, "r") as fn, open(out_file, "w") as fout:
        header_var = fv.readline()
        header_norm = fn.readline()
        fout.write("# pt_low pt_high eta_low eta_high SF_ratio\n")

        for line_var, line_norm in zip(fv, fn):
            parts_var = line_var.strip().split()
            parts_norm = line_norm.strip().split()

            pt_low, pt_high = float(parts_norm[0]), float(parts_norm[1])
            eta_low, eta_high = float(parts_norm[2]), float(parts_norm[3])
            sf_var = float(parts_var[4])
            sf_norm = float(parts_norm[4])
            ratio = sf_norm / sf_var if sf_var != 0 else 0.0
            if sf_var == 0.0:
                print("variation ist 0")


            fout.write(f"{pt_low:.1f} {pt_high:.1f} {eta_low:.3f} {eta_high:.3f} {ratio:.7f}\n")

    print(f"SF-Quotienten-Datei geschrieben: {out_file}")



parser = argparse.ArgumentParser(description="SF-Utilities: Export oder Quotienten")
subparsers = parser.add_subparsers(dest="command", required=True)

# Parser für JSON -> TXT Export
parser_export = subparsers.add_parser("export", help="Exportiere SF JSON nach Text")
parser_export.add_argument("--json", required=True, help="Pfad zur JSON-Datei")
parser_export.add_argument("--outdir", required=True, help="Verzeichnis für die erzeugten Textdateien")

# Parser für SF-Quotienten
parser_quo = subparsers.add_parser("sfquo", help="Berechne SF-Quotienten aus TXT-Dateien")
parser_quo.add_argument("--folder", required=True, help="Ordner mit SF-TXT-Dateien")
parser_quo.add_argument("--era", default="2017UL", help="Era (z.B. 2017UL)")
parser_quo.add_argument("--type", default="emb", help="Typ: mc oder emb")
parser_quo.add_argument("--model", default="ID_pt_eta_bins", help="Modellname")
parser_quo.add_argument("--var", default="up", help="Variation: up oder down")
parser_quo.add_argument("--outdir", required=True, help="Ausgabeverzeichnis für SFQuo")

args = parser.parse_args()

if args.command == "export":
    export_sf_tables(args.json, args.outdir)
elif args.command == "sfquo":
    compute_sf_quo(
        folder=args.folder,
        era=args.era,
        typ=args.type,
        model=args.model,
        var=args.var,
        out_dir=args.outdir
    )
