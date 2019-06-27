#!/bin/env python
import subprocess
import fitTagAndProbe_script
import plotEffSlices_script
import argparse
import yaml


parser = argparse.ArgumentParser()

parser.add_argument(
    '--channel', default="muon", required=True)
parser.add_argument(
    '--fit', action="store_true")
parser.add_argument(
    '--plot', action="store_true")
parser.add_argument(
    '--era', required=True)

args = parser.parse_args()
Dir = "output/tag_and_probe_{}/".format(args.channel)

parameters = yaml.load(open("settings_{}_{}.yaml".format(args.channel,args.era)))

if args.fit:
    for label in parameters:
        filename = ["output/{}_TP_Embedding.root".format(args.channel), "output/{}_TP_Data.root".format(args.channel), "output/{}_TP_DY.root".format(args.channel)]
        Dir_ext = ["/embedding", "/data", "/DY"]
        print label
        print parameters[label]
        for i, file in enumerate(filename):
            try:
                fitTagAndProbe_script.main(
                    filename=file,
                    name=label,
                    sig_model=parameters[label]["SIG"],
                    bkg_model=parameters[label]["BKG"],
                    title=parameters[label]["TITLE"],
                    particle="m",
                    isMC=False,
                    postfix="",
                    plot_dir=Dir + label + Dir_ext[i],
                    bin_replace=None)
            except AttributeError:
                pass

if args.plot:
    emb_title = "#mu#rightarrow#mu embedded" if "muon" in args.channel else "#mu#rightarrow e embedded"
    dy_title = "Z#rightarrow#mu#mu simulation" if "muon" in args.channel else "Z#rightarrow ee simulation"
    x_title = "Muon p_{T} (GeV)" if "muon" in args.channel else "Electron p_{T} (GeV)"
    for label in parameters:
        files = ["output/{}_TP_Data_Fits_{}.root".format(args.channel,label),
                "output/{}_TP_Embedding_Fits_{}.root".format(args.channel,label),
                "output/{}_TP_DY_Fits_{}.root".format(args.channel,label)
                ]
        draw_options = [
            {
                'Title':'Data'},
            {
                'MarkerColor':4,
                'LineColor':4,
                'MarkerStyle':21,
                'Title': emb_title},
            {
                'MarkerColor':2,
                'LineColor':2,
                'MarkerStyle':21,
                'Title': dy_title}
                ]
        try:
            plotEffSlices_script.main(
                files=files,
                label=label,
                draw_options=draw_options,
                output="efficiency", 
                title= parameters[label]["TITLE"], 
                y_range= parameters[label]["y_range"], 
                ratio_y_range= parameters[label]["ratio_y_range"], 
                binned_in= "#eta", 
                x_title= x_title, 
                ratio_to= 0, 
                plot_dir= Dir + label, 
                label_pos= 3)
        except ReferenceError:
            print label + " Fits do not exist"
            pass
