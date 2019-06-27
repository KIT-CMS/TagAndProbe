#!/bin/env python
import subprocess
import fitTagAndProbe_script
import plotEffSlices_script
import argparse
#from joblib import Parallel, delayed

parser = argparse.ArgumentParser()

parser.add_argument(
    '--channel', default="m", required=True)
parser.add_argument(
    '--fit', action="store_true")
parser.add_argument(
    '--plot', action="store_true")
parser.add_argument(
    "--cores", default=10
)
args = parser.parse_args()
if "sm" in args.channel:
    dir = "output_crosstrigger/tag_and_probe_sm_v17_4/"
elif "dm" in args.channel:
    dir = "output_crosstrigger/tag_and_probe_dm_v17_4/"
elif "e" in args.channel:
    dir = "output_crosstrigger/tag_and_probe_e_v17_4/"
else:
    "Only Options are sm / dm / e !!"
num_cores = args.cores
parameters = {
    "Trg_Mu20_pt_eta_bins": {
        "SMALL": "eff.Trg_Iso",
        "DIR": dir,
        "TITLE": "Trg IsoMu20",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    }
}
el_parameters = {
    "Ele24_Iso_pt_eta_bins": {
        "SMALL": "eff.Trg_Iso",
        "DIR": dir,
        "TITLE": "Trg Ele24",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    }
}
mu_sliceing = {
    "Trg_Mu20_pt_eta_bins": {
        "SMALL": "eff.Trg_Iso",
        "DIR": dir,
        "TITLE": "Trg IsoMu20",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,1.0],
        "ratio_y_range": [0.95,1.2]
    }
}
el_sliceing = {
    "Ele24_Iso_pt_eta_bins": {
        "SMALL": "eff.Trg_Iso",
        "DIR": dir,
        "TITLE": "Trg Ele24",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,1.0],
        "ratio_y_range": [0.95,1.2]
    }
}
if args.fit:
    if "m" in args.channel:
        for label in parameters.keys():
            pass
            if "sm" in args.channel:
                filename = ["output_crosstrigger/ZmmTP_Embedding.root", "output_crosstrigger/ZmmTP_Data_sm.root", "output_crosstrigger/ZmmTP_DY.root"]
            else:
                filename = ["output_crosstrigger/ZmmTP_Embedding.root", "output_crosstrigger/ZmmTP_Data.root", "output_crosstrigger/ZmmTP_DY.root"]
            dir_ext = ["/embedding", "/data", "/DY"]
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
                        plot_dir=dir + label + dir_ext[i],
                        bin_replace=None)
                except AttributeError:
                    pass
                
        # electron plots
    elif "e" in args.channel:
        filename = ["output_crosstrigger/ZeeTP_Embedding.root", "output_crosstrigger/ZeeTP_Data.root", "output_crosstrigger/ZeeTP_DYJetsToLL.root"]
        dir_ext = ["/embedding", "/data", "/DY"]
        for label in el_parameters.keys():
            for i, file in enumerate(filename):
                try:
                    fitTagAndProbe_script.main(
                        filename=file,
                        name=label,
                        sig_model=el_parameters[label]["SIG"],
                        bkg_model=el_parameters[label]["BKG"],
                        title=el_parameters[label]["TITLE"],
                        particle="e",
                        isMC=False,
                        postfix="",
                        plot_dir=dir + label + dir_ext[i],
                        bin_replace=None)
                except AttributeError:
                    pass
if args.plot:
    if "m" in args.channel:
        for label in mu_sliceing.keys():
            files = ["output_crosstrigger/ZmmTP_Data_sm_Fits_" + label + ".root",
                    "output_crosstrigger/ZmmTP_Embedding_Fits_" + label + ".root",
                    "output_crosstrigger/ZmmTP_DY_Fits_" + label + ".root"
                    ]
            draw_options = [
                {
                    'Title':'Data'},
                {
                    'MarkerColor':4,
                    'LineColor':4,
                    'MarkerStyle':21,
                    'Title':"#mu#rightarrow#mu embedded"},
                {
                    'MarkerColor':2,
                    'LineColor':2,
                    'MarkerStyle':21,
                    'Title':"Z#rightarrow#mu#mu simulation"}
                    ]
            try:
                plotEffSlices_script.main(
                    files=files,
                    label=label,
                    draw_options=draw_options,
                    output="efficiency", 
                    title= mu_sliceing[label]["TITLE"], 
                    y_range= mu_sliceing[label]["y_range"], 
                    ratio_y_range= mu_sliceing[label]["ratio_y_range"], 
                    binned_in= "#eta", 
                    x_title= "Muon p_{T} (GeV)", 
                    ratio_to= 0, 
                    plot_dir= dir + label, 
                    label_pos= 3)
            except ReferenceError:
                print label + " Fits do not exist"
                pass
    elif "e" in args.channel:
        for label in el_sliceing.keys():
            files = ["output_crosstrigger/ZeeTP_Data_Fits_" + label + ".root",
                    "output_crosstrigger/ZeeTP_Embedding_Fits_" + label + ".root",
                    "output_crosstrigger/ZeeTP_DYJetsToLL_Fits_" + label + ".root"
                    ]
            draw_options = [
                {
                    'Title':'Data'},
                {
                    'MarkerColor':4,
                    'LineColor':4,
                    'MarkerStyle':21,
                    'Title':"#mu#rightarrow e embedded"},
                {
                    'MarkerColor':2,
                    'LineColor':2,
                    'MarkerStyle':21,
                    'Title':"Z#rightarrow ee simulation"}
                    ]
            try:
                plotEffSlices_script.main(
                    files=files,
                    label=label,
                    draw_options=draw_options,
                    output="efficiency", 
                    title= el_sliceing[label]["TITLE"],# + "Efficiency" , 
                    y_range= el_sliceing[label]["y_range"], 
                    ratio_y_range= el_sliceing[label]["ratio_y_range"], 
                    binned_in= "#eta", 
                    x_title= "Electron p_{T} (GeV)", 
                    ratio_to= 0, 
                    plot_dir= dir + label, 
                    label_pos= 3)
            except ReferenceError:
                print label + " Fits do not exist"
                pass