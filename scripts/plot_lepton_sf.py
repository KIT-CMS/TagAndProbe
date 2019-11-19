#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import logging
# include dumbledraw package from topfolder
sys.path.append("{}/Dumbledraw".format(os.getcwd()))

import Dumbledraw.dumbledraw as dd
import Dumbledraw.sf_rootfile_parser as rootfile_parser
import Dumbledraw.styles as styles
logger = logging.getLogger(__name__)


def sf_label(type, process):
    # definition of the labels used in the plot
    dict = {
        "electron": {
            "Data": "Data",
            "DY": "Z #rightarrow ee simulation",
            "Embedding": "#mu #rightarrow e embedded"
        },
        "muon": {
            "Data": "Data",
            "DY": "Z#rightarrow #mu#mu simulation",
            "Embedding": "#mu #rightarrow #mu embedded"
        }
    }
    if "muon" in type:
        return dict["muon"][process]
    else:
        return dict["electron"][process]


def sf_color(process):
    # definition of the colors used in the plot
    dict = {
        "Data": 1,
        "DY": 98,
        "Embedding": 60
    }
    return dict[process]


def build_plot(folder, variable, era, type, etabin, plotoptions):

    plot = dd.Plot([[0.25, 0.20]], "ModTDR", r=0.04, l=0.14)

    processes = ["Data", "DY", "Embedding"]
    # iterate over the three rootfiles of the sf fit and load the efficiency curves
    for k, process in enumerate(processes):
        rootfile = rootfile_parser.ScaleFactor_Rootfile_parser(
            "{folder}/{type}_TP_{process}_{era}_Fits_{variable}.root"
            .format(folder=folder,type=type, era=era, variable=variable, process=process))
        plot.add_hist(rootfile.get(variable, etabin + 1), process)
        plot.setGraphStyle(process,
                           "LE",
                           markersize=0.8,
                           linewidth=2,
                           markershape=21,
                           markercolor=sf_color(process),
                           linecolor=sf_color(process))
        # add subplot(1) for the ratio, and add data twice for 2 ratios
        if 'Data' in process:
            for label in ["Data_Embedding_ratio", "Data_DY_ratio"]:
                plot.subplot(1).add_hist(rootfile.get(variable, etabin + 1),
                                         label)
                plot.subplot(1).setGraphStyle(
                    label,
                    "LE",
                    markersize=0.8,
                    linewidth=2,
                    markershape=21,
                    markercolor=sf_color(label.split("_")[1]),
                    linecolor=sf_color(label.split("_")[1]))
        else:
            plot.subplot(1).add_hist(rootfile.get(variable, etabin + 1),
                                     "{}_ratio".format(process))
            plot.subplot(1).setGraphStyle("{}_ratio".format(process),
                                          "LE",
                                          markersize=0.8,
                                          linewidth=2,
                                          markershape=21,
                                          markercolor=sf_color(process),
                                          linecolor=sf_color(process))
        del(rootfile)
    # normalize the two ratios so they represent the sf: Data/Emb and Data/MC
    plot.subplot(1).normalize("Data_Embedding_ratio", "Embedding_ratio")
    plot.subplot(1).normalize("Data_DY_ratio", "DY_ratio")
    logger.debug("y Range: {} - {}".format(plotoptions['y_range'][0], plotoptions['y_range'][1]))
    logger.debug("y Subrange: {} - {}".format(plotoptions['ratio_y_range'][0], plotoptions['ratio_y_range'][1]))
    logger.debug("pT Range: {} - {}".format(plotoptions['ptrange'][0], int(plotoptions['ptrange'][1])))
    # take ranges from the .yaml settings file
    plot.subplot(0).setYlims(plotoptions['y_range'][0], plotoptions['y_range'][1])
    plot.subplot(1).setYlims(plotoptions['ratio_y_range'][0], plotoptions['ratio_y_range'][1])
    plot.subplot(0).setXlims(plotoptions['ptrange'][0], int(plotoptions['ptrange'][1]))
    plot.subplot(1).setXlims(plotoptions['ptrange'][0], int(plotoptions['ptrange'][1]))
    plot.subplot(0).setLogX()
    plot.subplot(1).setLogX()
    if "muon" in type:
        plot.subplot(1).setXlabel("p_{T}^{#mu} (GeV)")
    elif "electron" in type:
        plot.subplot(1).setXlabel("p_{T}^{e} (GeV)")
    plot.subplot(0).setYlabel("Efficiency")
    plot.subplot(1).setYlabel("Scalefactor")

    plot.scaleXTitleSize(0.8)
    plot.scaleXLabelSize(0.8)
    plot.scaleYTitleSize(0.8)
    plot.scaleYLabelSize(0.8)
    plot.scaleXLabelOffset(2.0)
    plot.scaleYTitleOffset(1.1)
    logger.debug("plotting {} - #eta [{}]".format(plotoptions["TITLE"], plotoptions["etarange"].replace("-", ",")))
    # draw subplots. Argument contains names of objects to be drawn in corresponding order.
    plot.subplot(0).Draw(["Data", "Embedding", "DY"])
    plot.subplot(1).Draw(["Data_Embedding_ratio", "Data_DY_ratio"])

    for i in range(2):
        plot.add_legend(width=0.3, height=0.15, pos=6)
        for process in processes:
            plot.legend(i).add_entry(i, process, sf_label(type, process), 'PLE')
        plot.legend(i).setNColumns(1)
    plot.legend(0).Draw()
    plot.legend(1).setAlpha(0.0)
    plot.legend(1).Draw()

    # plot.DrawCMS()
    if "2016" in era:
        plot.DrawLumi("35.9 fb^{-1} (2016, 13 TeV)")
    elif "2017" in era:
        plot.DrawLumi("41.5 fb^{-1} (2017, 13 TeV)")
    elif "2018" in era:
        plot.DrawLumi("59.7 fb^{-1} (2018, 13 TeV)")

    # take plot label from the .yaml settings file
    plot.DrawChannelCategoryLabel("{} - #eta [{}]".format(plotoptions["TITLE"], plotoptions["etarange"].replace("-", ",")), textsize=0.03)
    # save plot
    
    logger.debug("Saving Plot")
    plot.save("{folder}/{variable}_{type}_{era}_{etarange}_scalefactor.pdf".format(
        folder=plotoptions["outputdir"], variable=variable, type=type, era=era, etarange=plotoptions["etarange"]))
    plot.save("{folder}/{variable}_{type}_{era}_{etarange}_scalefactor.png".format(
        folder=plotoptions["outputdir"], variable=variable, type=type, era=era, etarange=plotoptions["etarange"]))
