# dieses Skript, hat das Zeug mit den stat Unsicherheiten von Lukas üebrnommen, aber diesen Modellvergleich sowie die Berechnung der
# systematischen Unsicherheiten weggelassen


import argparse
import ROOT
import os
import plotting as plot
import sys
import array

#Weil ich sonst einfach nichts im Terminal printen kann, muss ich mir so ne logging library installieren, crazy
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Handler für Konsole und Logdatei
console = logging.StreamHandler()
console.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(console)
logger.info("Logger initialisiert")

#plotting ---
import matplotlib
matplotlib.use("Agg")   
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
#-------------

from stuff_for_hists import make_chi2_maps
from stuff_for_hists import plot_2d_hist

def linspace(start, stop, num):
    if num == 1:
        return [start]
    step = (stop - start) / float(num - 1)
    return [start + step * i for i in range(num)]

def safe_sqrt(x):
    if x <= 0.0:
        return 1.0  # default fallback for non-positive input
    return x ** 0.5

def interpolate_crossing(x1, y1, x2, y2, target): 
    """Lineare Interpolation für den Schnittpunkt mit target."""
    if y2 == y1:
        return 0.5 * (x1 + x2)
    return x1 + (target - y1) * (x2 - x1) / (y2 - y1)

def scan_uncertainty(wsp, param_name, nll, data, nsigma=1.0, npoints=5000, scan_range=None):
    param = wsp.var(param_name)
    if param is None:
        raise ValueError(f"Parameter '{param_name}' not found in workspace.")

    best_fit = param.getVal()
    nll_min = nll.getVal()

    if scan_range is None:
        delta = max(0.05 * abs(best_fit), 0.01)
        scan_range = (
            max(param.getMin(), best_fit - 2*delta),
            min(param.getMax(), best_fit + 2*delta)
        )

    scan_vals = linspace(scan_range[0], scan_range[1], npoints)
    nll_vals = []

    param.setConstant(True)
    for val in scan_vals:
        param.setVal(val)
        nll_vals.append(2 * nll.getVal())
    param.setConstant(False)
    nll_min = min(nll_vals)
    delta_nll = [(val - nll_min) for val in nll_vals]
    target = nsigma ** 2

    def find_crossing(direction):
        for i in range(len(scan_vals) - 1):
            x1, x2 = scan_vals[i], scan_vals[i+1]
            y1, y2 = delta_nll[i], delta_nll[i+1]
            
            if direction == "low" and y1 > target >= y2:
                return interpolate_crossing(x1, y1, x2, y2, target)
            if direction == "high" and y1 < target <= y2:
                return interpolate_crossing(x1, y1, x2, y2, target)
        return None

    try:
        low_val = find_crossing("low")
        high_val = find_crossing("high")

        err_lo = abs(best_fit - low_val) if low_val is not None else 0.0
        err_hi = abs(high_val - best_fit) if high_val is not None else 0.0

        if err_lo == 0.0 or err_hi == 0.0:
            try:
                fallback = 1.0 / safe_sqrt(max(1.0, data.sumEntries()))
            except:
                fallback = 1.0 / safe_sqrt(max(1.0, data.numEntries()))
            print("Calculating fallback uncertainty:", fallback)
            err_lo = err_lo or fallback
            err_hi = err_hi or fallback

        return best_fit, err_lo, err_hi

    except Exception as e:
        print("Error in manual scan:", e)
        try:
            fallback = 1.0 / safe_sqrt(max(1.0, data.sumEntries()))
        except:
            fallback = 1.0 / safe_sqrt(max(1.0, data.numEntries()))
        return best_fit, fallback, fallback


def main(
    filename,
    name,
    plot_dir,
    sig_model,
    bkg_model,
    title,
    particle,
    postfix,
    bin_replace,
    passfail_hist = "no"
):

    ROOT.PyConfig.IgnoreCommandLineOptions = True
    ROOT.gROOT.SetBatch(ROOT.kTRUE)
    ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.WARNING)

    plot.ModTDRStyle(width=1200, l=0.35, r=0.15)

    if plot_dir != "":
        os.system("mkdir -p %s" % plot_dir)

    ROOT.RooWorkspace.imp = getattr(ROOT.RooWorkspace, "import")
    ROOT.TH1.AddDirectory(0)

    infile = ROOT.TFile(filename)
    wsp = infile.Get("wsp_" + name)

    pdf_args = []
    nparams = 1
    if sig_model == "DoubleVCorr":
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
    elif sig_model == "BWDoubleCBConvCorr":
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

    res = []

    chi2_pass_array = []
    chi2_fail_array = []
    pt_bins_set = set()
    eta_bins_set = set()

    for b in bins:
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
        sds = 0.0
        try:
            wsp.var("efficiency").setVal(yield_pass / yield_tot)
            wsp.var("efficiency").setAsymError(0, 0)
            sds = yield_pass / yield_tot
        except ZeroDivisionError:
            wsp.var("efficiency").setVal(0)

        if rewrite_efficiency_to_zero:
            wsp.var("efficiency").setVal(0)
            wsp.var("efficiency").setAsymError(0, 0)

        # Improved fitting procedure from Lukas
        wsp.pdf("model").fitTo(
             wsp.data(dat),
             ROOT.RooFit.PrintLevel(-1),
         )
        wsp.pdf("model").fitTo(
            wsp.data(dat),
            ROOT.RooFit.Optimize(False),
            ROOT.RooFit.PrintLevel(-1),
            ROOT.RooFit.Minimizer("Minuit2", "Migrad"),
            ROOT.RooFit.Offset(True),
            ROOT.RooFit.Extended(True),
            ROOT.RooFit.SumW2Error(True),
            ROOT.RooFit.Strategy(2),
        )

        # Use NLL scan for better uncertainty estimation
        nll = wsp.pdf("model").createNLL(wsp.data(dat), ROOT.RooFit.Extended(True), ROOT.RooFit.Offset(True))
        val, err_lo, err_hi = scan_uncertainty(wsp, "efficiency", nll, wsp.data(dat))

        eff = wsp.var("efficiency")
        eff.setVal(val)
        eff.setError((err_hi + err_lo) / 2.0)
        wsp.var("efficiency").setError(eff.getError())

        print(f"Deviation yields for : {eff.getVal()-sds}")

        res.append(
            (dat, wsp.var("efficiency").getVal(), wsp.var("efficiency").getError())
        )

        hist.SetBinContent(b[0], b[1], wsp.var("efficiency").getVal())
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

        axis = plot.GetAxisHist(pads[0])
        if particle == "e":
            plot.Set(axis.GetXaxis().SetTitle("m_{ee} (GeV)"))
        else:
            plot.Set(axis.GetXaxis().SetTitle("m_{#mu#mu} (GeV)"))
        plot.Set(axis.GetYaxis().SetTitle("Events / %g GeV" % width))
        plot.DrawTitle(pads[0], title, 1)

        latex.SetTextSize(0.035)
        font = latex.GetTextFont()
        latex.DrawLatex(0.2, 0.9, "pass region")
        latex.SetTextFont(42)
        latex.DrawLatex(0.2, 0.8555, "Private work")
        latex.DrawLatex(0.2, 0.825, "(CMS data/simulation)")
        latex.DrawLatex(
            0.63,
            0.75,
            "#chi^{2}/ndf = %.2f" % (abs(xframe.chiSquare("AllPass", "DataPass", nparams))),
        )

        chi2_pass = abs(xframe.chiSquare("AllPass", "DataPass", nparams))

        val = wsp.var("efficiency").getVal()
        err = wsp.var("efficiency").getError()

        if err < 1e-4:
            label_text = "#varepsilon = %.4f #pm %.1e" % (val, err)
        else:
            label_text = "#varepsilon = %.4f #pm %.4f" % (val, err)

        latex.DrawLatex(0.63, 0.7, label_text)

        ROOT.gStyle.SetLegendBorderSize(1)
        legend1 = ROOT.TLegend(0.6, 0.8, 0.925, 0.939)
        legend1.AddEntry(xframe.findObject("DataPass"), "data", "ep")
        legend1.AddEntry(xframe.findObject("AllPass"), "$Z #rightarrow #mu#mu + BG$", "l")
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
        if particle == "e":
            plot.Set(axis.GetXaxis().SetTitle("m_{ee} (GeV)"))
        else:
            plot.Set(axis.GetXaxis().SetTitle("m_{#mu#mu} (GeV)"))
        plot.Set(axis.GetYaxis().SetTitle("Events / %g GeV" % width))
        plot.DrawTitle(
            pads[1], "p_{T}: [%g, %g] GeV #eta: [%g, %g]" % (b[2], b[3], b[4], b[5]), 1
        )
        latex.DrawLatex(
            0.63,
            0.75,
            "#chi^{2}/ndf = %.2f" % (abs(xframe2.chiSquare("AllFail", "DataFail", nparams))),
        )
        latex.SetTextFont(font)
        latex.DrawLatex(0.2, 0.9, "fail region")

        legend2 = ROOT.TLegend(0.6, 0.8, 0.925, 0.939)
        legend2.AddEntry(xframe2.findObject("DataFail"), "data", "ep")
        legend2.AddEntry(
            xframe2.findObject("AllFail"), r"Z \rightarrow \mu\mu + BG", "l"
        )
        legend2.AddEntry(xframe2.findObject("BkgFail"), "BG", "l")
        legend2.Draw()

        canv.Print("%s/%s.png" % (plot_dir, canv.GetName()))
        canv.Print("%s/%s.pdf" % (plot_dir, canv.GetName()))

        chi2_fail = abs(xframe2.chiSquare("AllFail", "DataFail", nparams))

        pt_bin = (b[2], b[3])
        eta_bin = (b[4], b[5])
        pt_bins_set.add(b[2])
        pt_bins_set.add(b[3])
        eta_bins_set.add(b[4])
        eta_bins_set.add(b[5])
        chi2_pass_array.append((pt_bin, eta_bin, chi2_pass))
        chi2_fail_array.append((pt_bin, eta_bin, chi2_fail))

    if passfail_hist.lower() == "yes":
    # Pfad für die temporären Chi²-Histogramme
        pic_path = "/work/agaganidze/CMSSW_12_3_2/src/UserCode/TagAndProbe/chi2_failpass_2DHist" 
        os.makedirs(pic_path, exist_ok=True)

        logger.info("Starte Erstellung der Chi²-Maps...")
        logger.info(f"Anzahl pass Bins: {len(chi2_pass_array)}, fail Bins: {len(chi2_fail_array)}")
        logger.info(f"Speicherpfad für PNGs: {pic_path}")

        make_chi2_maps(
            chi2_pass_array,
            chi2_fail_array,
            pt_bins_set,
            eta_bins_set,
            pic_path,           
            plot_2d_hist
        )
        logger.info("make_chi2_maps() wurde erfolgreich aufgerufen.")
        logger.info(f"Inhalt von {pic_path} nach Erstellung: {os.listdir(pic_path)}")

        # Verschiebe die erzeugten Dateien in den endgültigen Ordner
        import shutil
        label_name = os.path.basename(os.path.dirname(plot_dir))
        data_type = os.path.basename(plot_dir)  # data / DY / embedding
        chi_target_dir = os.path.join(os.path.dirname(plot_dir), f"chi_pass_fail_{label_name}_{data_type}")
        os.makedirs(chi_target_dir, exist_ok=True)
        for f in os.listdir(pic_path):
            if f.endswith(".png") or f.endswith(".pdf"):
                shutil.move(os.path.join(pic_path, f), os.path.join(chi_target_dir, f))
        logger.info(f"Chi² Pass/Fail Bilder verschoben nach: {chi_target_dir}")


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

    outfile.Close()
    wsp.Delete()


# if __name__ == "__main__":
#     # execute only if run as a script
#     args = parse_arguments()
#     main(args)