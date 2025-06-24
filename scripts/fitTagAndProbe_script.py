import argparse
import ROOT
import os
import plotting as plot
import sys
import array
# def parse_arguments():
#     parser = argparse.ArgumentParser()
#     parser.add_argument('input')
#     parser.add_argument('--sig-model', default='DoubleVCorr')
#     parser.add_argument('--bkg-model', default='Exponential')
#     parser.add_argument('--title', default='Muon ID Efficiency')
#     parser.add_argument('--particle', choices=['e', 'm'], default='m')
#     parser.add_argument('--postfix', default='')
#     parser.add_argument('--plot-dir', '-p', default='./')
#     parser.add_argument('--bin-replace', default=None) #(100,2.3,80,2.3)
#     return parser.parse_args()


def main(
    filename,
    name,
    plot_dir,
    sig_model_,
    bkg_model_,
    title,
    particle,
    postfix,
    bin_replace,
):

    ROOT.PyConfig.IgnoreCommandLineOptions = True
    ROOT.gROOT.SetBatch(ROOT.kTRUE)
    ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.WARNING)

    plot.ModTDRStyle(width=1200, l=0.35, r=0.15)
    # Apparently I don't need to do this...
    # ROOT.gSystem.Load('lib/libICHiggsTauTau.so')

    if plot_dir != "":
        os.system("mkdir -p %s" % plot_dir)

    ROOT.RooWorkspace.imp = getattr(ROOT.RooWorkspace, "import")
    ROOT.TH1.AddDirectory(0)

    # filename = input.split(':')[0]
    # name = input.split(':')[1]

    infile = ROOT.TFile(filename)
    sig_models = ["DoubleVPartcorr", "BWDoubleCBConvCorr", "DoubleVCorr"] # "DoubleVUncorr",
    bkg_models = ["Exponential", "CMSShape",]  #"Chebychev"] # [bkg_model_] #
    #model_results = [[], [], []]
    #sig_model = sig_model_
    bkg_model = bkg_model_
    hist = infile.Get(name)
    pt_bins = []
    eta_bins = []
    pt_bins = [hist.GetXaxis().GetBinLowEdge(i) for i in range(1, hist.GetNbinsX() + 1)]
    pt_bins.append(hist.GetXaxis().GetBinUpEdge(hist.GetNbinsX()))
    eta_bins = [hist.GetYaxis().GetBinLowEdge(i) for i in range(1, hist.GetNbinsY() + 1)]
    eta_bins.append(hist.GetYaxis().GetBinUpEdge(hist.GetNbinsY()))

    h2 = ROOT.TH2D("chi2_map.root", "Chi2 Map; p_{T} bin; #eta bin",
                    len(pt_bins)-1, array.array('d', pt_bins),
                    len(eta_bins)-1, array.array('d', eta_bins))
    #accepted_maps = {}

    #for model in sig_models:
    hmod = ROOT.TH2D(f"accepted_model", f"Accepted model per bin; p_{{T}} bin; #eta bin", len(pt_bins)-1, array.array('d', pt_bins), len(eta_bins)-1, array.array('d', eta_bins))
        #accepted_maps[model] = hmod
    #h_mod = ROOT.TH2D("model_map.root", "Model Map; p_{T} bin; #eta bin",
                    #hist.GetNbinsX(), hist.GetXaxis().GetXmin(), hist.GetXaxis().GetXmax(),
                    #hist.GetNbinsY(), hist.GetYaxis().GetXmin(), hist.GetYaxis().GetXmax())
    chi2s = []
    for run_no, sig_model in enumerate(sig_models):
        wsp = infile.Get("wsp_" + name)
        pdf_args = []
        nparams = 1
        if sig_model == "BWDoubleCBConvCorr":
            nparams = 15
            pdf_args.extend(
                [
                    "BreitWigner::BW(m_vis, meanbw[0], widthbw[2.495])",
                    "CBShape::CBPass1(m_vis, mean[91.2,85,95], sigma[2,1,4], alpha[1,-50,50], n[1,0,50])",
                    "CBShape::CBPass2(m_vis, meanp[91.2,85,95], sigmap[4,4,10], alphap[1,-50,50], np[1,0,50])",
                    "SUM::DoubleCBPass(CBPass1, vFracp[0.01,0,1]*CBPass2)",
                    "FFTConvPdf::signalPass(m_vis,DoubleCBPass,BW)",
                    "CBShape::CBFail1(m_vis, mean[91.2,85,95], sigma[2,1,4], alpha[1,-50,50], n[1,0,50])",
                    "CBShape::CBFail2(m_vis, meanf[91.2,85,95], sigmaf[4,4,10], alphaf[1,-50,50], nf[1,0,50])",
                    "SUM::DoubleCBFail(CBFail1, vFracf[0.01,0,1]*CBFail2)",
                    "FFTConvPdf::signalFail(m_vis,DoubleCBFail,BW)",
                ]
            )
        elif sig_model == "DoubleVUncorr":
            nparams = 12
            pdf_args.extend(
                [
                    "Voigtian::signal1Pass(m_vis, mean1p[91.2,85,95], widthp[2.495], sigma1p[2,0.2,4])",
                    "Voigtian::signal2Pass(m_vis, mean2p[91.2,85,95], widthp,        sigma2p[4,2,10])",
                    "SUM::signalPass(vFracp[0.8,0,1]*signal1Pass, signal2Pass)",
                    "Voigtian::signal1Fail(m_vis, mean1f[91.2,85,95], widthf[2.495], sigma1f[2,0.2,4])",
                    "Voigtian::signal2Fail(m_vis, mean2f[91.2,85,95], widthf,        sigma2f[4,2,10])",
                    "SUM::signalFail(vFracf[0.8,0,1]*signal1Fail, signal2Fail)",
                ]
            )
        elif sig_model == "DoubleVPartcorr":
            nparams = 6
            pdf_args.extend(
                [
                    "Voigtian::signal1Pass(m_vis, mean[90,85,95], width[2.495], sigma[2,0.2,4])",
                    "Voigtian::signal2Pass(m_vis, meanp[90,85,95], width[2.495], sigmap[2,1,10])",
                    "SUM::signalPass(vFracp[0.01,0,1]*signal1Pass, signal2Pass)",
                    "Voigtian::signal1Fail(m_vis, mean[90,85,95], width[2.495], sigma[2,0.2,4])",
                    "Voigtian::signal2Fail(m_vis, meanf[90,85,95], width[2.495], sigmaf[2,1,10])",
                    "SUM::signalFail(vFracf[0.01,0,1]*signal1Fail, signal2Fail)",
                ]
            )
        elif sig_model == "DoubleVCorr":
            nparams = 6
            pdf_args.extend(
                [
                    "Voigtian::signal1Pass(m_vis, mean1[91.2,85,95], width[2.495], sigma1[2,0.2,4])",
                    "Voigtian::signal2Pass(m_vis, mean2[91.2,85,95], width,        sigma2[4,2,10])",
                    "SUM::signalPass(vFrac[0.8,0.6,1]*signal1Pass, signal2Pass)",
                    "Voigtian::signal1Fail(m_vis, mean1[91.2,85,95], width[2.495], sigma1[2,0.2,4])",
                    "Voigtian::signal2Fail(m_vis, mean2[91.2,85,95], width,        sigma2[4,2,10])",
                    "SUM::signalFail(vFrac[0.8,0.6,1]*signal1Fail, signal2Fail)",
                ]
            )
        else:
            raise RuntimeError("Chosen --sig-model %s not supported" % sig_model)

        if bkg_model == "Exponential":
            nparams += 2
            pdf_args.extend(
                [
                    "Exponential::backgroundPass(m_vis, lp[-0.1,-1,0])",
                    "Exponential::backgroundFail(m_vis, lf[-0.1,-1,0])",
                ]
            )
        elif bkg_model == "CMSShape":
            nparams += 4
            pdf_args.extend(
                [
                    "RooCMSShape::backgroundPass(m_vis, alphaPass[60.,50.,85.], betaPass[0.001,0,0.1], gammaPass[0.001,0,1], peak[90])",
                    "RooCMSShape::backgroundFail(m_vis, alphaFail[60.,50.,85.], betaFail[0.001,0,0.1], gammaFail[0.001,0,1], peak[90])",
                ]
            )
        elif bkg_model == "Chebychev":
            nparams += 6
            pdf_args.extend(
                [
                    "RooChebychev::backgroundPass(m_vis, {a0p[0.25,0,0.5], a1p[-0.25,-1,0.1],a2p[0.,-0.25,0.25]})",
                    "RooChebychev::backgroundFail(m_vis, {a0f[0.25,0,0.5], a1f[-0.25,-1,0.1],a2f[0.,-0.25,0.25]})",
                ]
            )
        else:
            raise RuntimeError("Chosen --bkg-model %s not supported" % bkg_model)

        for arg in pdf_args:
            wsp.factory(arg)
            model_args = [
                "expr::nSignalPass('efficiency*fSigAll*numTot',efficiency[0,1], fSigAll[0.9,0,1],numTot[1,0,1e12])",
                "expr::nSignalFail('(1-efficiency)*fSigAll*numTot',efficiency,fSigAll,numTot)",
                "expr::nBkgPass('effBkg*(1-fSigAll)*numTot',effBkg[0.9,0,1],fSigAll,numTot)",
                "expr::nBkgFail('(1-effBkg)*(1-fSigAll)*numTot',effBkg,fSigAll,numTot)",
                "SUM::passing(nSignalPass*signalPass,nBkgPass*backgroundPass)",
                "SUM::failing(nSignalFail*signalFail,nBkgFail*backgroundFail)",
                "cat[fail,pass]",
                "SIMUL::model(cat,fail=failing,pass=passing)",
            ]
        for arg in model_args:
            wsp.factory(arg)

        hist = infile.Get(name)
        bin_cfg = {
            "name": hist.GetName(),
            "binvar_x": hist.GetXaxis().GetTitle(),
            "binvar_y": hist.GetYaxis().GetTitle(),
        }

        bins = []
        
        max_effs = []
        min_effs = []
        for i in range(1, hist.GetNbinsX() + 1):
            for j in range(1, hist.GetNbinsY() + 1):
                bins.append(
                    (
                        i,
                        j,
                        hist.GetXaxis().GetBinLowEdge(i),
                        hist.GetXaxis().GetBinUpEdge(i),
                        hist.GetYaxis().GetBinLowEdge(j),
                        hist.GetYaxis().GetBinUpEdge(j),
                    )
                )
                if run_no == 0:
                    chi2s.append(float('inf'))
                    min_effs.append(float('inf'))
                    max_effs.append(0)


        for i, b in enumerate(bins):
            dat = "%s>=%g && %s<%g && %s>=%g && %s<%g" % (
                bin_cfg["binvar_x"],
                b[2],
                bin_cfg["binvar_x"],
                b[3],
                bin_cfg["binvar_y"],
                b[4],
                bin_cfg["binvar_y"],
                b[5],
            )
            label = "%s.%g_%g.%s.%g_%g" % (
                bin_cfg["binvar_x"],
                b[2],
                b[3],
                bin_cfg["binvar_y"],
                b[4],
                b[5],
            )
            label = label.replace("(", "_")
            label = label.replace(")", "_")
            # Set the initial yield and efficiency values
            yield_tot = wsp.data(dat).sumEntries()
            yield_pass = wsp.data(dat).sumEntries("cat==cat::pass")
            yield_fail = wsp.data(dat).sumEntries("cat==cat::fail")
            rewrite_efficiency_to_zero = any(it == 0 for it in {yield_pass, yield_tot})
            print(
                (
                    "In bin %s, yield_tot = %g, yield_pass = %g, yield_fail = %g"
                    % (label, yield_tot, yield_pass, yield_fail)
                )
            )
            wsp.var("numTot").setVal(yield_tot)
            try:
                wsp.var("efficiency").setVal(yield_pass / yield_tot)
                wsp.var("efficiency").setAsymError(0, 0)
            except ZeroDivisionError:
                wsp.var("efficiency").setVal(0)

            if rewrite_efficiency_to_zero:
                wsp.var("efficiency").setVal(0)
                wsp.var("efficiency").setAsymError(0, 0)

            # wsp.pdf("model").fitTo(wsp.data(dat),
            #                        ROOT.RooFit.Minimizer("Minuit2", "Scan"),
            #                        ROOT.RooFit.Offset(True),
            #                        ROOT.RooFit.Extended(True),
            #                        ROOT.RooFit.PrintLevel(-1))

            # wsp.pdf("model").fitTo(wsp.data(dat),
            #                     ROOT.RooFit.Minimizer("Minuit2", "Migrad"),
            #                     ROOT.RooFit.Strategy(2),
            #                     ROOT.RooFit.Offset(True),
            #                     ROOT.RooFit.Extended(True),
            #                     ROOT.RooFit.SumW2Error(True),
            #                     ROOT.RooFit.PrintLevel(-1),
            #                     ROOT.RooFit.NumCPU(10))
            
            wsp.pdf("model").fitTo(
                wsp.data(dat),
                ROOT.RooFit.Optimize(False),
                ROOT.RooFit.Minimizer("Minuit2", "Migrad"),
                ROOT.RooFit.Offset(True),
                ROOT.RooFit.Extended(True),
                ROOT.RooFit.SumW2Error(False),
                ROOT.RooFit.PrintLevel(-1),
                ROOT.RooFit.Strategy(2),
                #ROOT.RooFit.AsymptoticError(True)
            )
            
            # pdf = wsp.pdf("model")
            # data = wsp.data(dat)

            # nll = pdf.createNLL(
            #     data,
            #     ROOT.RooFit.Optimize(False),
            #     ROOT.RooFit.Offset(True),
            #     ROOT.RooFit.Extended(True),
            #     ROOT.RooFit.SumW2Error(False)
            # )

            # minimizer = ROOT.RooMinimizer(nll)
            # minimizer.setMinimizerType("Minuit2")
            # minimizer.setStrategy(2)
            # minimizer.setPrintLevel(-1)

            # minimizer.migrad()
            # minimizer.hesse()        

            fitres = wsp.pdf("model").fitTo(
                wsp.data(dat),
                ROOT.RooFit.Minimizer("Minuit2", "Migrad"),
                ROOT.RooFit.Optimize(False),
                ROOT.RooFit.Strategy(2),
                ROOT.RooFit.Offset(True),
                ROOT.RooFit.Extended(True),
                ROOT.RooFit.PrintLevel(-1),
                ROOT.RooFit.SumW2Error(False),
                ROOT.RooFit.Save(),
            )

            # ROOT.RooFit.Minos())

            # fitres.Print()
            # fitres.correlationMatrix().Print()

            # print("The Error for this Bin is: {}".format(wsp.var('efficiency').getError()))

            #if rewrite_efficiency_to_zero:
            #    wsp.var("efficiency").setVal(0)
            #    wsp.var("efficiency").setAsymError(0, 0) 
                
            #print('epsilon + err: ', wsp.var("efficiency").getVal(), wsp.var("efficiency").getError())
            #model_results.append([wsp.var("efficiency").getVal(), wsp.var("efficiency").getError()])
            #xframe = wsp.var("m_vis").frame(ROOT.RooFit.Title("Passing"))
            #with open('efficiencies.csv', 'a', newline='\n') as fd:
            #    fd.write(str(sig_model) + ',' + str(bkg_model) + ',' + str(b[2]) + ',' + str(b[3]) + ',' + str(b[4]) + ',' + str(b[5])+','+str(wsp.var("efficiency").getVal()) + ',' + str(wsp.var("efficiency").getError()) + ','+ str(xframe.chiSquare("AllPass", "DataPass", nparams)) + '\n')

            
            # res.append(
            #     (dat, wsp.var("efficiency").getVal(), wsp.var("efficiency").getError())
            # )       
            
            hist.SetBinContent(b[0], b[1], wsp.var("efficiency").getVal())
            hist.SetBinError(b[0], b[1], wsp.var("efficiency").getError()+1000)
            hist.SetBinError(b[0], b[1], wsp.var("efficiency").getError())

            canv = ROOT.TCanvas("%s" % (label), "%s" % (label))
            pad_left = ROOT.TPad("left", "", 0.0, 0.0, 0.5, 1.0)
            pad_left.Draw()
            pad_right = ROOT.TPad("right", "", 0.5, 0.0, 1.0, 1.0)
            pad_right.Draw()
            pads = [pad_left, pad_right]

            latex = ROOT.TLatex()
            latex.SetNDC()

            ROOT.TGaxis.SetExponentOffset(-0.08, -0.02)

            splitData = wsp.data(dat).split(wsp.cat("cat"))
            xframe = wsp.var("m_vis").frame(ROOT.RooFit.Title("Passing"))
            width = (wsp.var("m_vis").getMax() - wsp.var("m_vis").getMin()) / splitData.At(
                1
            ).numEntries()
            splitData.At(1).plotOn(
                xframe,
                ROOT.RooFit.DataError(ROOT.RooAbsData.Poisson),
                ROOT.RooFit.Name("DataPass"),
            )
            wsp.pdf("passing").plotOn(
                xframe,
                ROOT.RooFit.Slice(wsp.cat("cat"), "pass"),
                ROOT.RooFit.LineColor(ROOT.kBlue),
                ROOT.RooFit.Name("AllPass"),
            )
            wsp.pdf("passing").plotOn(
                xframe,
                ROOT.RooFit.Slice(wsp.cat("cat"), "pass"),
                ROOT.RooFit.Components("backgroundPass"),
                ROOT.RooFit.LineStyle(ROOT.kDashed),
                ROOT.RooFit.LineColor(ROOT.kBlue),
                ROOT.RooFit.Name("BkgPass"),
            )
            pads[0].cd()
            xframe.Draw()
            #with open('efficiencies.csv', 'a', newline='\n') as fd:
            #    fd.write(str(dtype) + ',' + str(sig_model) + ',' + str(b[2]) + ',' + str(b[3]) + ',' + str(b[4]) + ',' + str(b[5])+','+ str(wsp.var("efficiency").getVal()) + ',' + str(wsp.var("efficiency").getError()) + ',' + str(bkg_model) + ',' + str(xframe.chiSquare("AllPass", "DataPass", nparams)) + '\n')
            #if wsp.var("efficiency").getVal() > max_effs[i]:
            #    max_effs[i] = wsp.var("efficiency").getVal()
            #if wsp.var("efficiency").getVal() < min_effs[i]:
            #    min_effs[i] = wsp.var("efficiency").getVal() # Work in progress
            if xframe.chiSquare("AllPass", "DataPass", nparams) < chi2s[i]: # Check whether current chi2 is lower than current lowest (starts with inf)
                
                chi2s[i] = xframe.chiSquare("AllPass", "DataPass", nparams)
                h2.SetBinContent(b[0], b[1], xframe.chiSquare("AllPass", "DataPass", nparams)) # update heatmap with new chi2 val for corresponding bin
                hmod.SetBinContent(b[0], b[1], run_no+1) 

                axis = plot.GetAxisHist(pads[0])
                # plot.Set(axis.GetXaxis().SetTitle('m_{tag-probe} (GeV)'))
                if particle == "e":
                    plot.Set(axis.GetXaxis().SetTitle("m_{ee} (GeV)"))
                else:
                    plot.Set(axis.GetXaxis().SetTitle("m_{#mu#mu} (GeV)"))
                plot.Set(axis.GetYaxis().SetTitle("Events / %g GeV" % width))
                # plot.DrawTitle(pads[0], 'Pass Region', 1)
                plot.DrawTitle(pads[0], title, 1)

                latex.SetTextSize(0.035)
                # latex.DrawLatex(0.5, 0.89, args.title)
                # latex.DrawLatex(0.5, 0.84, 'p_{T}: [%g, %g] GeV #eta: [%g, %g]' % (b[2], b[3], b[4], b[5]))
                font = latex.GetTextFont()
                latex.DrawLatex(0.2, 0.9, "pass region")
                latex.SetTextFont(42)
                latex.DrawLatex(
                    0.63,
                    0.75,
                    "#chi^{2}/ndf = %.2f" % (xframe.chiSquare("AllPass", "DataPass", nparams)),
                )
                latex.DrawLatex(
                    0.63,
                    0.7,
                    "#varepsilon = %.4f #pm %.4f"
                    % (wsp.var("efficiency").getVal(), wsp.var("efficiency").getError()),
                )
                
                # eff
                ROOT.gStyle.SetLegendBorderSize(1)
                legend1 = ROOT.TLegend(0.6, 0.8, 0.925, 0.939)
                legend1.AddEntry(xframe.findObject("DataPass"), "data", "ep")
                legend1.AddEntry(xframe.findObject("AllPass"), "Z #rightarrow #mu#mu + BG", "l")
                legend1.AddEntry(xframe.findObject("BkgPass"), "BG", "l")
                legend1.Draw()

                xframe2 = wsp.var("m_vis").frame(ROOT.RooFit.Title("Failing"))
                splitData.At(0).plotOn(
                    xframe2,
                    ROOT.RooFit.DataError(ROOT.RooAbsData.Poisson),
                    ROOT.RooFit.Name("DataFail"),
                )
                wsp.pdf("failing").plotOn(
                    xframe2,
                    ROOT.RooFit.Slice(wsp.cat("cat"), "fail"),
                    ROOT.RooFit.LineColor(ROOT.kRed),
                    ROOT.RooFit.Name("AllFail"),
                )
                wsp.pdf("failing").plotOn(
                    xframe2,
                    ROOT.RooFit.Slice(wsp.cat("cat"), "fail"),
                    ROOT.RooFit.Components("backgroundFail"),
                    ROOT.RooFit.LineStyle(ROOT.kDashed),
                    ROOT.RooFit.LineColor(ROOT.kRed),
                    ROOT.RooFit.Name("BkgFail"),
                )
                pads[1].cd()
                xframe2.Draw()
                axis = plot.GetAxisHist(pads[1])
                # plot.Set(axis.GetXaxis().SetTitle('m_{tag-probe} (GeV)'))
                if particle == "e":
                    plot.Set(axis.GetXaxis().SetTitle("m_{ee} (GeV)"))
                else:
                    plot.Set(axis.GetXaxis().SetTitle("m_{#mu#mu} (GeV)"))
                plot.Set(axis.GetYaxis().SetTitle("Events / %g GeV" % width))
                plot.DrawTitle(
                    pads[1], "p_{T}: [%g, %g] GeV #eta: [%g, %g]" % (b[2], b[3], b[4], b[5]), 1
                )
                # plot.DrawTitle(pads[1], 'Fail Region', 1)
                latex.DrawLatex(
                    0.63,
                    0.75,
                    "#chi^{2}/ndf = %.2f" % (xframe2.chiSquare("AllFail", "DataFail", nparams)),
                )
                latex.SetTextFont(font)
                latex.DrawLatex(0.2, 0.9, "fail region")

                legend2 = ROOT.TLegend(0.6, 0.8, 0.925, 0.939)
                legend2.AddEntry(xframe2.findObject("DataFail"), "data", "ep")
                legend2.AddEntry(
                    xframe2.findObject("AllFail"), "Z #rightarrow #mu#mu + BG", "l"
                )
                legend2.AddEntry(xframe2.findObject("BkgFail"), "BG", "l")
                legend2.Draw()

                canv.Print("%s/%s.png" % (plot_dir, canv.GetName()))
                canv.Print("%s/%s.pdf" % (plot_dir, canv.GetName()))
            #else:
            #    accepted_maps[model].SetBinContent(b[0], b[1], 0.0) 
    #print(model_results)
    if bin_replace is not None:
        replacements = bin_replace.split(":")
        for rep in replacements:
            bins = [float(x) for x in rep.split(",")]
            dest_bin_x = hist.GetXaxis().FindFixBin(bins[0])
            dest_bin_y = hist.GetYaxis().FindFixBin(bins[1])
            src_bin_x = hist.GetXaxis().FindFixBin(bins[2])
            src_bin_y = hist.GetYaxis().FindFixBin(bins[3])
            dest_val, dest_err = hist.GetBinContent(
                dest_bin_x, dest_bin_y
            ), hist.GetBinError(dest_bin_x, dest_bin_y)
            src_val, src_err = hist.GetBinContent(
                src_bin_x, src_bin_y
            ), hist.GetBinError(src_bin_x, src_bin_y)
            print(
                (
                    "Replacing content of bin %g,%g (%g +/- %g) with %g,%g (%g +/- %g)"
                    % (
                        dest_bin_x,
                        dest_bin_y,
                        dest_val,
                        dest_err,
                        src_bin_x,
                        src_bin_y,
                        src_val,
                        src_err,
                    )
                )
            )
            hist.SetBinContent(dest_bin_x, dest_bin_y, src_val)
            hist.SetBinError(dest_bin_x, dest_bin_y, src_err)

    c = ROOT.TCanvas("chi2_colorband", "Chi2 heatmap", 800, 600)
    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetPalette(ROOT.kBird)

    h2.Draw("COLZ")
    
    heat_out = ROOT.TFile(
        filename.replace(".root", "_Fits_%s%s_chi2_map.root" % (name, postfix)), "RECREATE"
    )
    c.Write("chi2 canvas")
    h2.Write()
    #for model, hist in accepted_maps.items():
    #    accepted_maps[model].Write()
    d = ROOT.TCanvas("Model_acceptance", "Model acceptance heatmap", 800, 600)
    hmod.Draw("COL")
    d.Write("model canvas")
    hmod.Write()
    outfile = ROOT.TFile(
        filename.replace(".root", "_Fits_%s%s.root" % (name, postfix)), "RECREATE"
    )
    hist.Write()

    for i in range(1, hist.GetNbinsY() + 1):
        slice = hist.ProjectionX("%s_projx_%i" % (hist.GetName(), i), i, i)
        slice.Write()
        gr = ROOT.TGraphAsymmErrors(slice)
        gr.SetName("gr_" + slice.GetName())
        gr.Write()

    heat_out.Close()
    outfile.Close()
    wsp.Delete()
    


# if __name__ == "__main__":
#     # execute only if run as a script
#     args = parse_arguments()
#     main(args)
