#!/usr/bin/env python3

import os
import yaml
import argparse

import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch()
ROOT.TH1.AddDirectory(0)

from create_crosspog_json import pt_eta_correction, CorrectionSet, emb_doublemuon_correction


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-e", "--era",
        type=str,
        help="Era to be considered"
    )
    parser.add_argument(
        "-c", "--channel",
        type=str,
        help="Considered channel to be written out"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Folder where the outputs will be written and inputs read from"
    )
    parser.add_argument("--settings-folder", default="settings", required=False)
    return parser.parse_args()


def add_corrections(yamlfile, correctionset, era, outdir):
    with open(yamlfile, "r") as stream:
        correction_db = yaml.safe_load(stream)
    for correction in correction_db:
        print(f"Adding {correction}")
        correction = pt_eta_correction(
            tag=correction_db[correction]["name"],
            name=correction,
            configfile=yamlfile,
            era=era,
            outdir=f"{outdir}/jsons",
            data_only=False,
        )
        correction.generate_scheme()
        correctionset.add_correction(correction.correctionset)
    return


def main(args):
    print(os.getcwd())
    outdir = args.output
    # Make json folder if it doesn't already exist
    if not os.path.exists(f"{outdir}/jsons"):
        os.makedirs(f"{outdir}/jsons")
    # Create the container to hold all corrections
    correctionset = CorrectionSet(f"Embedding{args.era}")
    if args.channel == "embeddingselection":
        double_object_quantities_configfile = f"{args.settings_folder}/UL/settings_embeddingselection_{args.era}_double_object_quantities.yaml"
        if not os.path.exists(double_object_quantities_configfile):
            print(f"{double_object_quantities_configfile} does not exist. Double object quantities will not be considered.")
            double_object_quantities_configfile = None
        EmbSelEff = emb_doublemuon_correction(
            tag="EmbSelEff",
            name="m_sel_trg_kit_ratio",
            configfile=f"{args.settings_folder}/UL/settings_embeddingselection_{args.era}_xpog.yaml",
            triggernames=["Trg17_pt_eta_bins", "Trg8_pt_eta_bins"],
            era=args.era,
            outdir=f"{outdir}/jsons",
            data_only=True,
            double_object_quantities_configfile=double_object_quantities_configfile
        )
        EmbSelEff.generate_scheme()
        correctionset.add_correction(EmbSelEff)
        EmbSelEffID = pt_eta_correction(
            tag="EmbSelEffID",
            name="EmbID_pt_eta_bins",
            configfile=f"{args.settings_folder}/UL/settings_embeddingselection_{args.era}.yaml",
            era=args.era,
            outdir=f"{outdir}/jsons",
            data_only=True,
        )
        EmbSelEffID.generate_scheme()
        correctionset.add_correction(EmbSelEffID)
    else:
        add_corrections(f"{args.settings_folder}/UL/settings_{args.channel}_{args.era}.yaml", correctionset, args.era, outdir)
    correctionset.write_json(f"{outdir}/jsons/{args.channel}_{args.era}.json")
    return


if __name__ == "__main__":
    args = parse_args()
    main(args)
