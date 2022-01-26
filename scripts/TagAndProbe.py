import ROOT
import glob
import sys
import copy
import yaml
import os
import pprint as pp
import argparse
from array import array
import UserCode.TagAndProbe.analysis as analysis

ROOT.RooWorkspace.imp = getattr(ROOT.RooWorkspace, "import")
ROOT.TH1.AddDirectory(0)

parser = argparse.ArgumentParser()
parser.add_argument("--era", required=True)
parser.add_argument("--channel", required=True)
parser.add_argument("--output", default="output", required=False)
parser.add_argument("--crown", default=True, required=False)

args = parser.parse_args()
# if "crosselectron" in args.channel and args.era=="2016":
#     print "No cross trigger settings available for 2016 yet."
#     sys.exit()
bin_cfgs = yaml.safe_load(
    open("settings/settings_{}_{}.yaml".format(args.channel, args.era))
)
input_files = yaml.safe_load(open("set_inputfiles.yaml"))


def convert_cutstrings(cutstring, tag):
    if "tag" not in cutstring and "probe" not in cutstring:
        raise ValueError("cutstring {} must contain tag and probe".format(cutstring))
    if tag == 1:
        cutstring = cutstring.replace("_tag", "_1")
        cutstring = cutstring.replace("_probe", "_2")
    elif tag == 2:
        cutstring = cutstring.replace("_tag", "_2")
        cutstring = cutstring.replace("_probe", "_1")
    else:
        raise ValueError("tag must be either 1 or 2 - got {}".format(tag))
    return cutstring


def convert_hist_label(label):
    # print("converting label {}".format(label))
    label = label.replace("_1", "_tag").replace("_2", "_probe")
    # print("converted label {}".format(label))
    return label


def translate_from_crown(tag, probe, binvar_x, binvar_y):
    # in the crown ntuples, we do not have a single event per tag and probe pair but rather a single event for both cases. Therefore we have to consider the original event as well as the flipped event (i.e. the event with the probe as tag and the tag as probe)

    # first element are the events, where the first lepton is considered the tag and the second lepton the probe
    converted_cfg = {
        "tag": [],
        "probe": [],
        "binvar_x": [],
        "binvar_y": [],
    }
    converted_cfg["tag"].append(convert_cutstrings(tag, tag=1))
    converted_cfg["probe"].append(convert_cutstrings(probe, tag=1))
    converted_cfg["binvar_x"].append(convert_cutstrings(binvar_x, tag=1))
    converted_cfg["binvar_y"].append(convert_cutstrings(binvar_y, tag=1))
    converted_cfg["tag"].append(convert_cutstrings(tag, tag=2))
    converted_cfg["probe"].append(convert_cutstrings(probe, tag=2))
    converted_cfg["binvar_x"].append(convert_cutstrings(binvar_x, tag=2))
    converted_cfg["binvar_y"].append(convert_cutstrings(binvar_y, tag=2))
    return converted_cfg


drawlist = []
andable = set()
number_of_bins = []

for key, cfg_dict in bin_cfgs.items():
    cfg = cfg_dict
    cfg.update(
        translate_from_crown(cfg["tag"], cfg["probe"], cfg["binvar_x"], cfg["binvar_y"])
    )
    # pp.pprint(cfg)
    cfg["hist"] = []
    cfg["bins"] = []
    # number of bins multiplied by four because of pass / fail and the switching of tag and probe
    number_of_bins.append(4 * ((len(cfg["bins_x"]) - 1) * (len(cfg["bins_y"]) - 1)))
    for n in range(len(cfg["tag"])):
        hist = ROOT.TH2D(
            cfg["name"],
            cfg["name"],
            len(cfg["bins_x"]) - 1,
            array("d", cfg["bins_x"]),
            len(cfg["bins_y"]) - 1,
            array("d", cfg["bins_y"]),
        )
        cfg["hist"].append(hist)
        hist.GetXaxis().SetTitle(cfg["binvar_x"][n])
        hist.GetYaxis().SetTitle(cfg["binvar_y"][n])

        cfg["bins"].append([])

        for i in xrange(1, hist.GetNbinsX() + 1):
            for j in xrange(1, hist.GetNbinsY() + 1):
                cfg["bins"][n].append(
                    "%s>=%g && %s<%g && %s>=%g && %s<%g"
                    % (
                        cfg["binvar_x"][n],
                        hist.GetXaxis().GetBinLowEdge(i),
                        cfg["binvar_x"][n],
                        hist.GetXaxis().GetBinUpEdge(i),
                        cfg["binvar_y"][n],
                        hist.GetYaxis().GetBinLowEdge(j),
                        cfg["binvar_y"][n],
                        hist.GetYaxis().GetBinUpEdge(j),
                    )
                )
                andable.add(
                    "%s>=%g" % (cfg["binvar_x"][n], hist.GetXaxis().GetBinLowEdge(i))
                )
                andable.add(
                    "%s<%g" % (cfg["binvar_x"][n], hist.GetXaxis().GetBinUpEdge(i))
                )
                andable.add(
                    "%s>=%g" % (cfg["binvar_y"][n], hist.GetYaxis().GetBinLowEdge(j))
                )
                andable.add(
                    "%s<%g" % (cfg["binvar_y"][n], hist.GetYaxis().GetBinUpEdge(j))
                )

        for b in cfg["bins"][n]:
            drawlist.append(
                (
                    cfg["var"],
                    "((%s) && !(%s) && (%s))" % (b, cfg["probe"][n], cfg["tag"][n]),
                )
            )
            drawlist.append(
                (
                    cfg["var"],
                    "((%s) && (%s) && (%s)) " % (b, cfg["probe"][n], cfg["tag"][n]),
                )
            )
            andable.add(cfg["probe"][n])
            andable.add(cfg["tag"][n])

if args.channel == "embeddingselection":
    trees = {
        "Data": analysis.TTreeEvaluator(
            input_files[args.era][args.channel]["folder"],
            input_files[args.era][args.channel]["Data"],
        ),
    }
else:
    trees = {
        "Embedding": analysis.TTreeEvaluator(
            input_files[args.era][args.channel]["folder"],
            input_files[args.era][args.channel]["Embedding"],
        ),
        "DY": analysis.TTreeEvaluator(
            input_files[args.era][args.channel]["folder"],
            input_files[args.era][args.channel]["DY"],
        ),
        "Data": analysis.TTreeEvaluator(
            input_files[args.era][args.channel]["folder"],
            input_files[args.era][args.channel]["Data"],
        ),
    }

for sample in trees:
    out_dir = args.output
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    outputfilepath = "{}/{}_TP_{}_{}.root".format(
        out_dir, args.channel, sample, args.era
    )
    if os.path.exists(outputfilepath):
        os.remove(outputfilepath)
    outfile = ROOT.TFile(
        outputfilepath,
        "RECREATE",
    )
    outfile.cd()

    hists = trees[sample].Draw(drawlist, compiled=True)

    # if we are using crown, we have to add identical histograms together
    total_hists = len(hists)
    # print("Total number of histograms: {}".format(total_hists))
    # print("Bins per histogram: {}".format(number_of_bins))
    cleaned_hists = []
    counter = 0
    for nbins in number_of_bins:
        nentries = 0
        for bin in range(nbins / 2):
            cleaned_hists.append(
                hists[counter + bin] + hists[counter + bin + nbins / 2]
            )
            # print(
            #     "Ading histogram with {} Entries to {} existing Entries ".format(
            #         hists[counter + bin + nbins / 2].Integral(),
            #         hists[counter + bin].Integral(),
            #     )
            # )
            nentries += cleaned_hists[-1].Integral()
            cleaned_hists[-1].SetName(convert_hist_label(cleaned_hists[-1].GetName()))
            # print(
            #     "Combined histogram {} has {} entries ".format(
            #         cleaned_hists[-1].GetName(), cleaned_hists[-1].Integral()
            #     )
            # )
        # print("Total number of entries: {}".format(nentries))
        counter += nbins

    i = 0

    for key, cfg in bin_cfgs.items():
        wsp = ROOT.RooWorkspace("wsp_" + cfg["name"], "")
        var = wsp.factory("m_vis[100,65,115]")

        outfile.cd()
        outfile.mkdir(cfg["name"])
        ROOT.gDirectory.cd(cfg["name"])
        for b in cfg["bins"][0]:
            cleaned_hists[2 * i].SetName(convert_hist_label(b) + ":fail")
            cleaned_hists[2 * i + 1].SetName(convert_hist_label(b) + ":pass")
            cleaned_hists[2 * i].Write()
            cleaned_hists[2 * i + 1].Write()
            dat = wsp.imp(
                ROOT.RooDataHist(
                    convert_hist_label(b),
                    "",
                    ROOT.RooArgList(var),
                    ROOT.RooFit.Index(wsp.factory("cat[fail,pass]")),
                    ROOT.RooFit.Import("fail", cleaned_hists[2 * i]),
                    ROOT.RooFit.Import("pass", cleaned_hists[2 * i + 1]),
                )
            )
            i += 1
        outfile.cd()
        wsp.Write()
        xaxis_label = cfg["hist"][0].GetXaxis().GetTitle()
        yaxis_label = cfg["hist"][0].GetYaxis().GetTitle()
        cfg["hist"][0].GetXaxis().SetTitle(convert_hist_label(xaxis_label))
        cfg["hist"][0].GetYaxis().SetTitle(convert_hist_label(yaxis_label))
        cfg["hist"][0].Write()
        # outfile.Close()
        wsp.Delete()

    outfile.Close()
