#!/usr/bin/env python
import ROOT
import plotting as plot
import os
import argparse

# Boilerplate


def plot_lepton(
    files,
    label,
    era,
    output,
    draw_options,
    title,
    y_range,
    ratio_y_range,
    binned_in,
    x_title,
    ratio_to,
    plot_dir,
    label_pos,
):
    ROOT.PyConfig.IgnoreCommandLineOptions = True
    ROOT.gROOT.SetBatch(ROOT.kTRUE)
    ROOT.TH1.AddDirectory(0)
    plot.ModTDRStyle()

    # parser = argparse.ArgumentParser()

    # parser.add_argument(
    #     'input', nargs='+', help="""Input files""")
    # parser.add_argument(
    #     '--output', '-o', default='efficiency', help="""Name of the output
    #     plot without file extension""")
    # parser.add_argument('--title', default='Muon ID Efficiency')
    # parser.add_argument('--y-range', default='0,1')
    # parser.add_argument('--ratio-y-range', default='0.5,1.5')
    # parser.add_argument('--binned-in', default='#eta')
    # parser.add_argument('--x-title', default='p_{T} (GeV)')
    # parser.add_argument('--ratio-to', default=None, type=int)
    # parser.add_argument('--plot-dir', '-p', default='./')
    # parser.add_argument('--label-pos', default=1)
    # args = parser.parse_args()

    if plot_dir != "":
        os.system("mkdir -p %s" % plot_dir)

    hists = []

    # file = ROOT.TFile('%s.root' % target)

    # Process each input argument
    for src in files:
        # splitsrc = src.split(':')
        file = ROOT.TFile(src)
        if src.find("gen") >= 0:
            hists.append(file.Get(label + "_tot").Clone())
        else:
            hists.append(file.Get(label).Clone())
        file.Close()

    print(hists)

    hist = hists[0]

    latex = ROOT.TLatex()
    latex.SetNDC()

    for i in xrange(1, hist.GetNbinsY() + 1):
        bin_label = "%s: [%g,%g]" % (
            binned_in,
            hist.GetYaxis().GetBinLowEdge(i),
            hist.GetYaxis().GetBinUpEdge(i),
        )
        canv = ROOT.TCanvas("%s_%i" % (output, i), output)

        if ratio_to is not None:
            pads = plot.TwoPadSplit(0.50, 0.01, 0.01)
        else:
            pads = plot.OnePad()
        slices = []

        if label_pos == 1:
            text = ROOT.TPaveText(0.55, 0.37, 0.9, 0.50, "NDC")
            legend = ROOT.TLegend(0.18, 0.37, 0.5, 0.50, "", "NDC")
        elif label_pos == 2:
            text = ROOT.TPaveText(0.55, 0.67, 0.9, 0.80, "NDC")
            legend = ROOT.TLegend(0.18, 0.67, 0.5, 0.80, "", "NDC")
        else:
            text = ROOT.TPaveText(0.55, 0.54, 0.9, 0.67, "NDC")
            legend = ROOT.TLegend(0.55, 0.67, 0.9, 0.80, "", "NDC")
        text = ROOT.TPaveText(0.55, 0.54, 0.9, 0.67, "NDC")
        legend = ROOT.TLegend(0.6, 0.54, 0.95, 0.74, "", "NDC")
        # ~ if 'ID' in splitsrc[1]:
        # ~ legend = ROOT.TLegend(0.18, 0.67, 0.5, 0.85, '', 'NDC')
        for j, src in enumerate(files):
            # splitsrc = src.split(':')
            htgr = hists[j].ProjectionX("%s_projx_%i" % (hists[j].GetName(), j), i, i)
            # if len(splitsrc) >= 3:
            #    settings = {x.split('=')[0]: eval(x.split('=')[1]) for x in splitsrc[2].split(',')}
            if draw_options[j] != None:
                settings = draw_options[j]
                plot.Set(htgr, **settings)
            htgr.Draw("HIST LP SAME")  # htgr.Draw('SAME')
            legend.AddEntry(htgr)
            slices.append(htgr)
        latex.SetTextSize(0.06)
        # ~ text.AddText(args.title)
        # ~ text.AddText(bin_label)
        # ~ text.SetTextAlign(13)
        # ~ text.SetBorderSize(0)
        # ~ text.Draw()
        legend.Draw()
        # pads[0].SetLogx(True)
        axis = plot.GetAxisHist(pads[0])
        axis.GetYaxis().SetTitle("Efficiency")
        axis.GetXaxis().SetTitle(x_title)
        axis.GetXaxis().SetRangeUser(1, 1000)
        axis.SetMinimum(float(y_range[0]))
        axis.SetMaximum(float(y_range[1]))
        # ~ pads[0].SetGrid(0, 1)
        pads[0].RedrawAxis("g")

        # ~ plot.DrawCMSLogo(pads[0], args.title, bin_label, 0, 0.16, 0.035, 1.2, cmsTextSize=0.5)
        plot.DrawTitle(pads[0], title + " - " + bin_label, 1)

        # plot.DrawTitle(pads[0], '18.99 fb^{-1} (13 TeV)', 3)
        if "2016preVFP" in era:
            plot.DrawTitle(pads[0], "19.5 fb^{-1} (2016preVFP, 13 TeV)", 3)
        if "2016postVFP" in era:
            plot.DrawTitle(pads[0], "16.8 fb^{-1} (2016postVFP, 13 TeV)", 3)
        elif era == "2017":
            plot.DrawTitle(pads[0], "41.5 fb^{-1} (2017, 13 TeV)", 3)
        elif era == "2018":
            plot.DrawTitle(pads[0], "59.7 fb^{-1} (2018, 13 TeV)", 3)

        if ratio_to is not None:
            pads[1].cd()
            # pads[1].SetLogx(True)
            ratios = []
            for slice in slices:
                ratios.append(slice.Clone())
                ratios[-1].Divide(slices[ratio_to])
            ratios[0].Draw("AXIS")
            plot.SetupTwoPadSplitAsRatio(
                pads,
                plot.GetAxisHist(pads[0]),
                plot.GetAxisHist(pads[1]),
                "Ratio to data",
                True,
                float(ratio_y_range[0]),
                float(ratio_y_range[1]),
            )
            for j, ratio in enumerate(ratios):
                if j == ratio_to:
                    continue
                ratio.Draw("HIST LP SAME")  # ('SAME E0')
            pads[1].SetGrid(0, 1)
            pads[1].RedrawAxis("g")

        outname = "%s.%s.%g_%g" % (
            output,
            hist.GetYaxis().GetTitle(),
            hist.GetYaxis().GetBinLowEdge(i),
            hist.GetYaxis().GetBinUpEdge(i),
        )
        outname = outname.replace("(", "_")
        outname = outname.replace(")", "_")
        outname = outname.replace(".", "_")

        canv.Print("%s/%s.png" % (plot_dir, outname))
        canv.Print("%s/%s.pdf" % (plot_dir, outname))


def plot_hadronic(
    input_file,
    triggers,
    working_points,
    file_types,
    era,
    per_dm,
    output,
    draw_options,
    title,
    y_range,
    ratio_y_range,
    binned_in,
    x_title,
    ratio_to,
    plot_dir,
    label_pos,
):

    ROOT.PyConfig.IgnoreCommandLineOptions = True
    ROOT.gROOT.SetBatch(ROOT.kTRUE)
    ROOT.TH1.AddDirectory(0)
    plot.ModTDRStyle()
    plot_dir = "plots"
    hists = {}
    graphs = {}
    if plot_dir != "":
        os.system("mkdir -p %s" % plot_dir)
    if per_dm:
        decayModes = ["inclusive", 0, 1, 10]
    else:
        decayModes = ["inclusive"]
    file = ROOT.TFile(input_file)
    for trg in triggers:
        hists[trg] = {}
        graphs[trg] = {}
        for decayMode in decayModes:
            dm_label = "" if decayMode == "inclusive" else "dm{}_".format(decayMode)
            hists[trg][decayMode] = {}
            graphs[trg][decayMode] = {}
            for wp in working_points:
                hists[trg][decayMode][wp] = []
                graphs[trg][decayMode][wp] = []

                for ft in file_types:
                    hists[trg][decayMode][wp].append(
                        file.Get(
                            "hist_{}TriggerEfficiency_{}TauMVA_{}{}".format(
                                trg, wp, dm_label, ft
                            )
                        ).Clone()
                    )
                    graphs[trg][decayMode][wp].append(
                        file.Get(
                            "hist_{}TriggerEfficiency_{}TauMVA_{}{}".format(
                                trg, wp, dm_label, ft
                            )
                        ).Clone()
                    )

    file.Close()

    latex = ROOT.TLatex()
    latex.SetNDC()
    for trg in triggers:
        for decayMode in decayModes:
            dm_label = "" if decayMode == "inclusive" else "dm{}_".format(decayMode)
            for wp in working_points:
                bin_label = "{}".format(wp)
                canv = ROOT.TCanvas("%s_%s" % (output, wp), output)

                if ratio_to is not None:
                    pads = plot.TwoPadSplit(0.50, 0.01, 0.01)
                else:
                    pads = plot.OnePad()
                slices = []

                if label_pos == 1:
                    text = ROOT.TPaveText(0.55, 0.37, 0.9, 0.50, "NDC")
                    legend = ROOT.TLegend(0.18, 0.37, 0.5, 0.50, "", "NDC")
                elif label_pos == 2:
                    text = ROOT.TPaveText(0.55, 0.67, 0.9, 0.80, "NDC")
                    legend = ROOT.TLegend(0.18, 0.67, 0.5, 0.80, "", "NDC")
                else:
                    text = ROOT.TPaveText(0.55, 0.54, 0.9, 0.67, "NDC")
                    legend = ROOT.TLegend(0.55, 0.67, 0.9, 0.80, "", "NDC")
                text = ROOT.TPaveText(0.55, 0.54, 0.9, 0.67, "NDC")
                legend = ROOT.TLegend(0.6, 0.54, 0.95, 0.74, "", "NDC")
                # ~ if 'ID' in splitsrc[1]:
                # ~ legend = ROOT.TLegend(0.18, 0.67, 0.5, 0.85, '', 'NDC')
                for j, hist in enumerate(graphs[trg][decayMode][wp]):
                    # splitsrc = src.split(':')
                    # htgr = hists[j].ProjectionX('%s_projx_%i' % (hists[j].GetName(), j), i, i)
                    # if len(splitsrc) >= 3:
                    #    settings = {x.split('=')[0]: eval(x.split('=')[1]) for x in splitsrc[2].split(',')}
                    if draw_options[j] != None:
                        settings = draw_options[j]
                        plot.Set(hist, **settings)
                    hist.Draw("LP SAME")  # htgr.Draw('SAME')
                    legend.AddEntry(hist)
                for j, hist in enumerate(hists[trg][decayMode][wp]):
                    if draw_options[j] != None:
                        settings = draw_options[j]
                        plot.Set(hist, **settings)
                    slices.append(hist)
                latex.SetTextSize(0.06)
                # ~ text.AddText(args.title)
                # ~ text.AddText(bin_label)
                # ~ text.SetTextAlign(13)
                # ~ text.SetBorderSize(0)
                # ~ text.Draw()
                legend.Draw()
                # pads[0].SetLogx(True)
                axis = plot.GetAxisHist(pads[0])
                axis.GetYaxis().SetTitle("Efficiency")
                axis.GetXaxis().SetTitle(x_title)
                # axis.GetXaxis().SetRangeUser(1,1000)
                axis.SetMinimum(float(y_range[0]))
                axis.SetMaximum(float(y_range[1]))
                # ~ pads[0].SetGrid(0, 1)
                pads[0].RedrawAxis("g")

                # ~ plot.DrawCMSLogo(pads[0], args.title, bin_label, 0, 0.16, 0.035, 1.2, cmsTextSize=0.5)
                plot.DrawTitle(
                    pads[0],
                    trg
                    + " "
                    + title
                    + dm_label.replace("_", "").replace("dm", " - dm")
                    + " - "
                    + bin_label,
                    1,
                )

                # plot.DrawTitle(pads[0], '18.99 fb^{-1} (13 TeV)', 3)
                if "2016preVFP" in era:
                    plot.DrawLumi("19.5 fb^{-1} (2016preVFP, 13 TeV)")
                if "2016postVFP" in era:
                    plot.DrawLumi("16.8 fb^{-1} (2016postVFP, 13 TeV)")
                elif era == "2017":
                    plot.DrawTitle(pads[0], "41.5 fb^{-1} (2017, 13 TeV)", 3)
                elif era == "2018":
                    plot.DrawTitle(pads[0], "59.7 fb^{-1} (2018, 13 TeV)", 3)

                if ratio_to is not None:
                    pads[1].cd()
                    # pads[1].SetLogx(True)
                    ratios = []
                    for slice in slices:
                        ratios.append(slice.Clone())
                        ratios[-1].Divide(slices[ratio_to])
                    ratios[0].Draw("AXIS")
                    plot.SetupTwoPadSplitAsRatio(
                        pads,
                        plot.GetAxisHist(pads[0]),
                        plot.GetAxisHist(pads[1]),
                        "Ratio to data",
                        True,
                        float(ratio_y_range[0]),
                        float(ratio_y_range[1]),
                    )
                    for j, ratio in enumerate(ratios):
                        if j == ratio_to:
                            continue
                        ratio.Draw("LP SAME")  # ('SAME E0')
                    pads[1].SetGrid(0, 1)
                    pads[1].RedrawAxis("g")

                outname = "{}_{}_{}_{}{}".format(trg, era, output, dm_label, wp)
                outname = outname.replace("(", "_")
                outname = outname.replace(")", "_")
                outname = outname.replace(".", "_")

                canv.Print("%s/%s.png" % (plot_dir, outname))
                canv.Print("%s/%s.pdf" % (plot_dir, outname))
