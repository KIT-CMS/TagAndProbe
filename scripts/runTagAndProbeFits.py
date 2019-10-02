#!/bin/env python
import subprocess
import fitTagAndProbe_script
import plotEffSlices_script
import argparse
import yaml
from multiprocessing import Process

parser = argparse.ArgumentParser()

parser.add_argument('--channel', required=True)
parser.add_argument('--fit', action="store_true")
parser.add_argument('--plot', action="store_true")
parser.add_argument('--era', required=True )
parser.add_argument('--output', default = "output", required = False)

args = parser.parse_args()

out_dir = args.output
Dir = "{}/tag_and_probe_{}_{}/".format(out_dir, args.channel, args.era)

parameters = yaml.load(open("settings/settings_{}_{}.yaml".format(args.channel,args.era)))

if args.fit:
    particle = "m" if ("muon" in args.channel or "embedding" in args.channel) else "e"
    expression_list = []
    for label in parameters:
        if args.channel == "embeddingselection": 
            filename = ["{}/{}_TP_Data_{}.root".format(out_dir, args.channel, args.era)]
            Dir_ext = ["/data"]
        else:
            filename = ["{}/{}_TP_Data_{}.root".format(out_dir, args.channel, args.era)]
            Dir_ext = ["/embedding", "/old_emb", "/data", "/DY"]  
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
    emb_title = "#mu#rightarrow#mu embedded" if "muon" in args.channel else "#mu#rightarrow e embedded"
    dy_title = "Z#rightarrow#mu#mu simulation" if "muon" in args.channel else "Z#rightarrow ee simulation"
    x_title = "Muon p_{T} (GeV)" if "muon" in args.channel else "Electron p_{T} (GeV)"
    for label in parameters:
        if args.channel == "embeddingselection": 
            files = ["{}/{}_TP_Data_{}_Fits_{}.root".format(out_dir, args.channel, args.era, label)]
        else:
            files = ["{}/{}_TP_Data_{}_Fits_{}.root".format(out_dir, args.channel, args.era, label),
                "{}/{}_TP_Embedding_{}_Fits_{}.root".format(out_dir, args.channel, args.era, label),
                "{}/{}_TP_old_emb_{}_Fits_{}.root".format(out_dir, args.channel, args.era, label),
                "{}/{}_TP_DY_{}_Fits_{}.root".format(out_dir, args.channel, args.era, label)
                ]        
        draw_options = [
            {
                'Title':'Data'},
            {
                'MarkerColor':4,
                'LineColor':4,
                'MarkerStyle':21,
                'Title': emb_title+" legacy"},
            {
                'MarkerColor':8,
                'LineColor':8,
                'MarkerStyle':21,
                'Title': emb_title+" old"},
            {
                'MarkerColor':2,
                'LineColor':2,
                'MarkerStyle':21,
                'Title': dy_title}
                ]
        try:
            plotEffSlices_script.plot_lepton(
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
