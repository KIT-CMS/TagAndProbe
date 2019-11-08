#!/bin/env python
import subprocess
import fitTagAndProbe_script
import plotEffSlices_script
import argparse
import yaml
from multiprocessing import Process
import plot_lepton_sf
import sys
import logging

logger = logging.getLogger("")
parser = argparse.ArgumentParser()

parser.add_argument('--channel', required=True)
parser.add_argument('--fit', action="store_true")
parser.add_argument('--plot', action="store_true")
parser.add_argument('--era', required=True )
parser.add_argument('--output', default = "output", required = False)

args = parser.parse_args()

def setup_logging(output_file, level=logging.DEBUG):
    logger.setLevel(level)
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    file_handler = logging.FileHandler(output_file, "w")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


out_dir = args.output
Dir = "{}/tag_and_probe_{}_{}/".format(out_dir, args.channel, args.era)

setup_logging("{}/fits_plots.log".format(out_dir), logging.INFO)

parameters = yaml.load(open("settings/settings_{}_{}.yaml".format(args.channel,args.era)))

if args.fit:
    particle = "m" if ("muon" in args.channel or "embedding" in args.channel) else "e"
    expression_list = []
    for label in parameters:
        if args.channel == "embeddingselection": 
            filename = ["{}/{}_TP_Data_{}.root".format(out_dir, args.channel, args.era)]
            Dir_ext = ["/data"]
        else:
            filename = ["{}/{}_TP_Embedding_{}.root".format(out_dir, args.channel, args.era),
            "{}/{}_TP_Data_{}.root".format(out_dir, args.channel, args.era),
            "{}/{}_TP_DY_{}.root".format(out_dir, args.channel, args.era)
            ]
            Dir_ext = ["/embedding", "/data", "/DY"]  
        for i, file_ in enumerate(filename):
            expression_list.append([file_, label, Dir + label + Dir_ext[i], parameters[label]["SIG"], parameters[label]["BKG"], parameters[label]["TITLE"], particle, "", None]) 
     #       fitTagAndProbe_script.main(
     #           filename=file_,
     #           name=label,
     #           sig_model=parameters[label]["SIG"],
     #           bkg_model=parameters[label]["BKG"],
     #           title=parameters[label]["TITLE"],
     #           particle=particle,
     #           postfix="",
     #           plot_dir=Dir + label + Dir_ext[i],
     #           bin_replace=None)
    procs = []
    for expression in expression_list:
        p = Process(target=fitTagAndProbe_script.main, args=(expression))
        procs.append(p)
        p.start()
    for p in procs:
        p.join()

if args.plot:
    for label in parameters:
        eta_binning = parameters[label]["bins_y"]
        for i,etalimit in enumerate(eta_binning[:-1:]):
            plotoptions = parameters[label]
            plotoptions["etarange"] = "{}-{}".format(eta_binning[i],eta_binning[i+1])
            plotoptions["ptrange"] = [min(plotoptions['bins_x']),max(plotoptions['bins_x'])]
            plot_lepton_sf.build_plot(out_dir, label, args.era, args.channel, i, plotoptions)
