#!/bin/env python
import subprocess
import fitTagAndProbe_script
import plotEffSlices_script
import argparse
import yaml


parser = argparse.ArgumentParser()

parser.add_argument('--channel', required=True)
parser.add_argument('--fit', action="store_true")
parser.add_argument('--plot', action="store_true")
parser.add_argument('--era', required=True )
parser.add_argument('--output', default = "output", required = False)

args = parser.parse_args()

out_dir = args.output
Dir = "{}/tag_and_probe_{}_{}/".format(out_dir, args.channel, args.era)

parameters = yaml.load(open("settings_{}_{}.yaml".format(args.channel,args.era)))

if args.fit:
    for label in parameters:
        filename = ["{}/{}_TP_Embedding_{}.root".format(out_dir, args.channel, args.era), "{}/{}_TP_Data_{}.root".format(out_dir, args.channel, args.era), "{}/{}_TP_DY_{}.root".format(out_dir, args.channel, args.era)]
        Dir_ext = ["/embedding", "/data", "/DY"]
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
                print label + " could not be created. "

if args.plot:
    emb_title = "#mu#rightarrow#mu embedded" if "muon" in args.channel else "#mu#rightarrow e embedded"
    dy_title = "Z#rightarrow#mu#mu simulation" if "muon" in args.channel else "Z#rightarrow ee simulation"
    x_title = "Muon p_{T} (GeV)" if "muon" in args.channel else "Electron p_{T} (GeV)"
    for label in parameters:
        files = ["{}/{}_TP_Data_{}_Fits_{}.root".format(out_dir, args.channel, args.era, label),
                "{}/{}_TP_Embedding_{}_Fits_{}.root".format(out_dir, args.channel, args.era, label),
                "{}/{}_TP_DY_{}_Fits_{}.root".format(out_dir, args.channel, args.era, label)
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
                era = args.era,
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
            print label + " Fits do not exist. "
