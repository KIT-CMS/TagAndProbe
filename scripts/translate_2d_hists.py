#!/usr/bin/env python
import yaml
import argparse
from array import array

import ROOT as root

root.PyConfig.IgnoreCommandLineOptions = True
root.gROOT.SetBatch(True)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str,
                        help="Input root file.")
    parser.add_argument("-o", "--output", type=str,
                        help="Output root file.")
    parser.add_argument("-e", "--era",
                        choices=[2016, 2017, 2018], type=int,
                        help="Era.")
    return parser.parse_args()


def get_hist_params(input_file):
    trs = set(key.GetName().split("_")[0] for key in input_file.GetListOfKeys()
              if isinstance(input_file.Get(key.GetName()), root.TH2D))
    wps = set(key.GetName().split("_")[1] for key in input_file.GetListOfKeys()
              if isinstance(input_file.Get(key.GetName()), root.TH2D))
    dms = set(key.GetName().split("_")[2] for key in input_file.GetListOfKeys()
              if isinstance(input_file.Get(key.GetName()), root.TH2D))
    fts = set(key.GetName().split("_")[3] for key in input_file.GetListOfKeys()
              if isinstance(input_file.Get(key.GetName()), root.TH2D))
    return list(trs), list(wps), list(dms), list(fts)
    # return map(lambda x: list(set(x)),
    #            (key.GetName().split("_") for key in input_file.GetListOfKeys()
    #             if isinstance(input_file.Get(key.GetName()), root.TH2D))
    #            )


def fill_hist(h_to_write, hname, in_file, conf_dict):
    for cat, vals in conf_dict["categories"].iteritems():
        hist = in_file.Get("_".join([hname, cat]))
        if isinstance(hist, root.TObject) and not isinstance(hist, root.TH2D):
            print "Hist object {} not found in file {}".format(
                    "_".join([hname, cat]), in_file.GetName())
            raise Exception
        for tup in vals:
            h_to_write.SetBinContent(tup[0], tup[1], hist.GetBinContent(1, 1))
    return h_to_write


def fill_avg_hist(h_to_write, hname, in_file, conf_dict):
    avg_hist = in_file.Get("_".join([hname, "Average"]))
    for tup in conf_dict["AVG"]:
        h_to_write.SetBinContent(tup[0], tup[1], avg_hist.GetBinContent(1, 1))
    return h_to_write


def main(args):
    inp_file = root.TFile(args.input, "read")
    out_file = root.TFile(args.output, "recreate")
    config = yaml.load(open("settings/settings_translate.yaml", "r"))[args.era]
    trgs, wps, dms, filetypes = get_hist_params(inp_file)
    for trg in trgs:
        for wp in wps:
            for dm in dms:
                for ft in filetypes:
                    hname = "{}_{}_{}_{}".format(trg, wp, dm, ft)
                    h_to_write = root.TH2F(
                            hname, hname,
                            len(config["binning"]["eta"])-1,
                            array("f", config["binning"]["eta"]),
                            len(config["binning"]["phi"])-1,
                            array("f", config["binning"]["phi"]))
                    fill_hist(h_to_write, hname, inp_file, config).Write()

                    havg_to_write = root.TH2F(
                            hname + "_AVG", hname + "_AVG",
                            len(config["binning"]["eta_avg"])-1,
                            array("f", config["binning"]["eta_avg"]),
                            len(config["binning"]["phi_avg"])-1,
                            array("f", config["binning"]["phi_avg"]))
                    fill_avg_hist(havg_to_write, hname, inp_file, config).Write()
    out_file.Close()
    return


if __name__ == "__main__":
    args = parse_args()
    main(args)
