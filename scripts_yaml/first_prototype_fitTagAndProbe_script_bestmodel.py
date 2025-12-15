import argparse
import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kError
ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.ERROR)

import os
import plotting as plot
import sys

class FilteredStream:
    def __init__(self, stream, blacklist_prefixes):
        self.stream = stream
        self.blacklist = blacklist_prefixes

    def write(self, msg):
        if not any(msg.startswith(p) for p in self.blacklist):
            self.stream.write(msg)

    def flush(self):
        self.stream.flush()

# stderr filtern (ROOT-Fehler kommen meist über stderr)
blacklist = [
    "Error in <TList::Clear>",
    "[#0] WARNING:Plotting -- RooHist::addBin",
    "Dumbledraw.dumbledraw - INFO",
    "Dumbledraw.styles - INFO"
]
sys.stderr = FilteredStream(sys.stderr, blacklist)

import array
import yaml

#Weil ich sonst einfach nichts im Terminal printen kann, muss ich mir so ne logging library installieren, crazy
import logging
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
# # Handler für Konsole und Logdatei
# console = logging.StreamHandler()
# console.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
# logger.addHandler(console)
# logger.info("Logger initialisiert")

from Logging import setup_logging

logger = setup_logging(logger=logging.getLogger(__name__), level = logging.DEBUG)
logging.getLogger("Dumbledraw").setLevel(logging.ERROR)
logging.getLogger("Dumbledraw.dumbledraw").setLevel(logging.ERROR)
logging.getLogger("Dumbledraw.styles").setLevel(logging.ERROR)

#plotting ---
import matplotlib
matplotlib.use("Agg")   
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
#-------------

TEST_PT_MIN  = 15.0
TEST_PT_MAX  = 20.0
TEST_ETA_MIN = 0.9
TEST_ETA_MAX = 1.2

ENABLE_TEST_BIN = True

def close(a, b, eps=1e-6):
    return abs(a - b) < eps

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
        #print(f"Finding crossing for {direction}:")
        for i in range(len(scan_vals) - 1):
            x1, x2 = scan_vals[i], scan_vals[i+1]
            y1, y2 = delta_nll[i], delta_nll[i+1]
            
            #if abs(y1 - target) < 50:
            #    print(x1, y1, x2, y2, target, best_fit)
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
        #print(err_lo, err_hi)
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
    sig_model_,
    bkg_model_,
    title,
    particle,
    postfix,
    bin_replace,
    passfail_hist = "no"
):

    ROOT.PyConfig.IgnoreCommandLineOptions = True
    ROOT.gROOT.SetBatch(ROOT.kTRUE)
    ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.ERROR)

    plot.ModTDRStyle(width=1200, l=0.35, r=0.15)
    # Apparently I don't need to do this...
    # ROOT.gSystem.Load('lib/libICHiggsTauTau.so')

    if plot_dir != "":
        os.system("mkdir -p %s" % plot_dir)

    output_base = plot_dir.split('/')[0]  # Nimmt "output" aus dem Pfad
    yaml_output_dir = os.path.join(output_base, "best_model_yamls")
    os.makedirs(yaml_output_dir, exist_ok=True)

    ROOT.RooWorkspace.imp = getattr(ROOT.RooWorkspace, "import")
    ROOT.TH1.AddDirectory(0)

    infile = ROOT.TFile(filename)
    sig_models = ["DoubleVPartcorr", "DoubleVCorr", "DoubleVUncorr", "BWDoubleCBConvCorr"] # , #"BWDoubleCBConvCorr"]#, "DoubleVUncorr"]
    bkg_models = ["CMSShape", "Exponential"] # , "Chebychev"]
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

    hsyst = ROOT.TH2D("sys_%s" % name, "Systematic signal model uncertainties; p_{T} bin; #eta bin",
                    len(pt_bins)-1, array.array('d', pt_bins),
                    len(eta_bins)-1, array.array('d', eta_bins))
    hsyst2 = ROOT.TH2D("sys2_%s" % name, "Systematic background model uncertainties; p_{T} bin; #eta bin",
                    len(pt_bins)-1, array.array('d', pt_bins),
                    len(eta_bins)-1, array.array('d', eta_bins))

    hmod = ROOT.TH2D(f"accepted_model", f"Accepted signal model per bin; p_{{T}} bin; #eta bin", 
                     len(pt_bins)-1, array.array('d', pt_bins), 
                     len(eta_bins)-1, array.array('d', eta_bins))
    
    hmod2 = ROOT.TH2D(f"accepted_model2", f"Accepted background model per bin; p_{{T}} bin; #eta bin", 
                     len(pt_bins)-1, array.array('d', pt_bins), 
                     len(eta_bins)-1, array.array('d', eta_bins))

    chi2s = [] # Tracks chi2 in 
    effs_sig =  [[] for _ in range(len(sig_models))] # Tracks efficiency for signal
    effs_bkg = [[] for _ in range(len(bkg_models))] # Tracks minimum efficiency for each bin
    effs = [
                    [
                        [0.0 for _ in range(hist.GetNbinsX() * hist.GetNbinsY())]
                        for _ in range(len(bkg_models))
                    ]
                    for _ in range(len(sig_models))
                    ]
    best_comb = [[] for _ in range(2)]
    man_calc = []

    def build_pdf_args(sig_model, bkg_model):
            pdf_args = []
            nparams = 1
            if sig_model == "BWDoubleCBConvCorr":
                nparams = 15
                
                pdf_args.extend(
                    [
                        "BreitWigner::BW(m_vis, meanbw[0], widthbw[2.495])",
                        "CBShape::CBPass1(m_vis, mean[91.2,85,95], sigma[2,1,4], alpha[3,1.5,6], n[10,5,50])", # alpha[1,-50,50], n[1,0,50], sigma[2,1,4], alpha[1,0.5,3]
                        "CBShape::CBPass2(m_vis, meanp[91.2,85,95], sigmap[4,4,6], alphap[3,1.5,6], np[10,5,50])", #alphap[1,-50,50], np[1,0,50], sigmap[4,4,10]
                        "SUM::DoubleCBPass(CBPass1, vFracp[0.01,0,1]*CBPass2)",
                        "FFTConvPdf::signalPass(m_vis,DoubleCBPass,BW)",
                        "CBShape::CBFail1(m_vis, mean[91.2,85,95], sigma[2,1,4], alpha[3,1.5,6], n[10,5,50])",
                        "CBShape::CBFail2(m_vis, meanf[91.2,85,95], sigmaf[4,4,6], alphaf[3,1.5,6], nf[10,5,50])", # alphaf[1,-50,50], nf[1,0,50]
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
                        "RooCMSShape::backgroundPass(m_vis, alphaPass[60.,50.,85.], betaPass[0.001,0,0.1], gammaPass[0.001,0,1], peak[90])", #alphaPass[60.,50.,85.], betaPass[0.001,0,0.1], gammaPass[0.001,0,1], peak[90]
                        "RooCMSShape::backgroundFail(m_vis, alphaFail[60.,50.,85.], betaFail[0.001,0,0.1], gammaFail[0.001,0,1], peak[90])", #alphaPass[60.,50.,100.], betaPass[0.001,0,0.5], gammaPass[0.001,0,1], peak[90]
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
            
            return pdf_args, nparams
    
    def build_model_args():
        return [
            "expr::nSignalPass('efficiency*fSigAll*numTot',efficiency[0,1], fSigAll[0.9,0,1],numTot[1,0,1e12])",
            "expr::nSignalFail('(1-efficiency)*fSigAll*numTot',efficiency,fSigAll,numTot)",
            "expr::nBkgPass('effBkg*(1-fSigAll)*numTot',effBkg[0.9,0,1],fSigAll,numTot)",
            "expr::nBkgFail('(1-effBkg)*(1-fSigAll)*numTot',effBkg,fSigAll,numTot)",
            "SUM::passing(nSignalPass*signalPass,nBkgPass*backgroundPass)",
            "SUM::failing(nSignalFail*signalFail,nBkgFail*backgroundFail)",
            "cat[fail,pass]",
            "SIMUL::model(cat,fail=failing,pass=passing)",
            ]
    
    bin_cfg = {
                "name": hist.GetName(),
                "binvar_x": hist.GetXaxis().GetTitle(),
                "binvar_y": hist.GetYaxis().GetTitle(),
            }

    for run_no, sig_model in enumerate(sig_models):
        if (sig_model != "BWDoubleCBConvCorr") and ENABLE_TEST_BIN:
            continue
        for run_no2, bkg_model in enumerate(bkg_models): # remove
            if (bkg_model != "CMSShape") and ENABLE_TEST_BIN:
                continue
            wsp = infile.Get("wsp_" + name)
            print(wsp)
            # pdf_args = []
            # nparams = 1
            # if sig_model == "BWDoubleCBConvCorr":
            #     nparams = 15
                
            #     pdf_args.extend(
            #         [
            #             "BreitWigner::BW(m_vis, meanbw[0], widthbw[2.495])",
            #             "CBShape::CBPass1(m_vis, mean[91.2,85,95], sigma[2,1,4], alpha[3,1.5,6], n[10,5,50])", # alpha[1,-50,50], n[1,0,50], sigma[2,1,4], alpha[1,0.5,3]
            #             "CBShape::CBPass2(m_vis, meanp[91.2,85,95], sigmap[4,4,6], alphap[3,1.5,6], np[10,5,50])", #alphap[1,-50,50], np[1,0,50], sigmap[4,4,10]
            #             "SUM::DoubleCBPass(CBPass1, vFracp[0.01,0,1]*CBPass2)",
            #             "FFTConvPdf::signalPass(m_vis,DoubleCBPass,BW)",
            #             "CBShape::CBFail1(m_vis, mean[91.2,85,95], sigma[2,1,4], alpha[3,1.5,6], n[10,5,50])",
            #             "CBShape::CBFail2(m_vis, meanf[91.2,85,95], sigmaf[4,4,6], alphaf[3,1.5,6], nf[10,5,50])", # alphaf[1,-50,50], nf[1,0,50]
            #             "SUM::DoubleCBFail(CBFail1, vFracf[0.01,0,1]*CBFail2)",
            #             "FFTConvPdf::signalFail(m_vis,DoubleCBFail,BW)",
            #         ]
            #     )
            # elif sig_model == "DoubleVUncorr":
            #     nparams = 12
            #     pdf_args.extend(
            #         [
            #             "Voigtian::signal1Pass(m_vis, mean1p[91.2,85,95], widthp[2.495], sigma1p[2,0.2,4])",
            #             "Voigtian::signal2Pass(m_vis, mean2p[91.2,85,95], widthp,        sigma2p[4,2,10])",
            #             "SUM::signalPass(vFracp[0.8,0,1]*signal1Pass, signal2Pass)",
            #             "Voigtian::signal1Fail(m_vis, mean1f[91.2,85,95], widthf[2.495], sigma1f[2,0.2,4])",
            #             "Voigtian::signal2Fail(m_vis, mean2f[91.2,85,95], widthf,        sigma2f[4,2,10])",
            #             "SUM::signalFail(vFracf[0.8,0,1]*signal1Fail, signal2Fail)",
            #         ]
            #     )
            # elif sig_model == "DoubleVPartcorr":
            #     nparams = 6
            #     pdf_args.extend(
            #         [
            #             "Voigtian::signal1Pass(m_vis, mean[90,85,95], width[2.495], sigma[2,0.2,4])",
            #             "Voigtian::signal2Pass(m_vis, meanp[90,85,95], width[2.495], sigmap[2,1,10])",
            #             "SUM::signalPass(vFracp[0.01,0,1]*signal1Pass, signal2Pass)",
            #             "Voigtian::signal1Fail(m_vis, mean[90,85,95], width[2.495], sigma[2,0.2,4])",
            #             "Voigtian::signal2Fail(m_vis, meanf[90,85,95], width[2.495], sigmaf[2,1,10])",
            #             "SUM::signalFail(vFracf[0.01,0,1]*signal1Fail, signal2Fail)",
            #         ]
            #     )
            # elif sig_model == "DoubleVCorr":
            #     nparams = 6
            #     pdf_args.extend(
            #         [
            #             "Voigtian::signal1Pass(m_vis, mean1[91.2,85,95], width[2.495], sigma1[2,0.2,4])",
            #             "Voigtian::signal2Pass(m_vis, mean2[91.2,85,95], width,        sigma2[4,2,10])",
            #             "SUM::signalPass(vFrac[0.8,0.6,1]*signal1Pass, signal2Pass)",
            #             "Voigtian::signal1Fail(m_vis, mean1[91.2,85,95], width[2.495], sigma1[2,0.2,4])",
            #             "Voigtian::signal2Fail(m_vis, mean2[91.2,85,95], width,        sigma2[4,2,10])",
            #             "SUM::signalFail(vFrac[0.8,0.6,1]*signal1Fail, signal2Fail)",
            #         ]
            #     )
            # else:
            #     raise RuntimeError("Chosen --sig-model %s not supported" % sig_model)

            # if bkg_model == "Exponential":
            #     nparams += 2
            #     pdf_args.extend(
            #         [
            #             "Exponential::backgroundPass(m_vis, lp[-0.1,-1,0])",
            #             "Exponential::backgroundFail(m_vis, lf[-0.1,-1,0])",
            #         ]
            #     )
            # elif bkg_model == "CMSShape":
            #     nparams += 4
            #     pdf_args.extend(
            #         [
            #             "RooCMSShape::backgroundPass(m_vis, alphaPass[60.,50.,85.], betaPass[0.001,0,0.1], gammaPass[0.001,0,1], peak[90])", #alphaPass[60.,50.,85.], betaPass[0.001,0,0.1], gammaPass[0.001,0,1], peak[90]
            #             "RooCMSShape::backgroundFail(m_vis, alphaFail[60.,50.,85.], betaFail[0.001,0,0.1], gammaFail[0.001,0,1], peak[90])", #alphaPass[60.,50.,100.], betaPass[0.001,0,0.5], gammaPass[0.001,0,1], peak[90]
            #         ]
            #     )
            # elif bkg_model == "Chebychev":
            #     nparams += 6
            #     pdf_args.extend(
            #         [
            #             "RooChebychev::backgroundPass(m_vis, {a0p[0.25,0,0.5], a1p[-0.25,-1,0.1],a2p[0.,-0.25,0.25]})",
            #             "RooChebychev::backgroundFail(m_vis, {a0f[0.25,0,0.5], a1f[-0.25,-1,0.1],a2f[0.,-0.25,0.25]})",
            #         ]
            #     )
            # else:
            #     raise RuntimeError("Chosen --bkg-model %s not supported" % bkg_model)
            
            # for arg in pdf_args:
            #             wsp.factory(arg)
            #             model_args = [
            #                 "expr::nSignalPass('efficiency*fSigAll*numTot',efficiency[0,1], fSigAll[0.9,0,1],numTot[1,0,1e12])",
            #                 "expr::nSignalFail('(1-efficiency)*fSigAll*numTot',efficiency,fSigAll,numTot)",
            #                 "expr::nBkgPass('effBkg*(1-fSigAll)*numTot',effBkg[0.9,0,1],fSigAll,numTot)",
            #                 "expr::nBkgFail('(1-effBkg)*(1-fSigAll)*numTot',effBkg,fSigAll,numTot)",
            #                 "SUM::passing(nSignalPass*signalPass,nBkgPass*backgroundPass)",
            #                 "SUM::failing(nSignalFail*signalFail,nBkgFail*backgroundFail)",
            #                 "cat[fail,pass]",
            #                 "SIMUL::model(cat,fail=failing,pass=passing)",
            #             ]
            # for arg in model_args:
            #     wsp.factory(arg)

            # bin_cfg = {
            #     "name": hist.GetName(),
            #     "binvar_x": hist.GetXaxis().GetTitle(),
            #     "binvar_y": hist.GetYaxis().GetTitle(),
            # }

            pdf_args, nparams = build_pdf_args(sig_model, bkg_model)
            model_args = build_model_args()

            for arg in pdf_args:
                wsp.factory(arg)
            for arg in model_args:
                wsp.factory(arg)
                
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
                    if not ENABLE_TEST_BIN and (run_no == 0 and run_no2 == 0): 
                        chi2s.append(float('inf'))
                        best_comb[0].append(0)
                        best_comb[1].append(0)
                        man_calc.append(0)

                    elif ENABLE_TEST_BIN and (run_no == 3 and run_no2 == 0):
                        chi2s.append(float('inf'))
                        best_comb[0].append(0)
                        best_comb[1].append(0)
                        man_calc.append(0)
                    effs_sig[run_no].append(0)
                    effs_bkg[run_no2].append(0)

            for i, b in enumerate(bins):

                if ENABLE_TEST_BIN:
                    pt_low  = b[2]
                    pt_high = b[3]
                    eta_low = b[4]
                    eta_high = b[5]

                    if not (close(pt_low,  TEST_PT_MIN) and
                            close(pt_high, TEST_PT_MAX) and
                            close(eta_low, TEST_ETA_MIN) and
                            close(eta_high, TEST_ETA_MAX)):
                        continue

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
                
                logger.info(f"DEBUG BIN {label}:")
                logger.info(f"  yield_tot = {yield_tot}")
                logger.info(f"  yield_pass = {yield_pass}")
                logger.info(f"  yield_fail = {yield_fail}")
                logger.info(f"  eff_initial = {yield_pass / yield_tot if yield_tot > 0 else 0}")
                wsp.var("numTot").setVal(yield_tot)

                try:
                    wsp.var("efficiency").setVal(yield_pass / yield_tot)
                    wsp.var("efficiency").setAsymError(0, 0)
                    sds = yield_pass / yield_tot
                    logger.info(f"eff nach setzen {wsp.var('efficiency').getVal()}")
                except ZeroDivisionError:
                    wsp.var("efficiency").setVal(0)
                    sds = 0
                if rewrite_efficiency_to_zero:
                    wsp.var("efficiency").setVal(0)
                    wsp.var("efficiency").setAsymError(0, 0)

                try:
                    wsp.pdf("model").fitTo(
                        wsp.data(dat),
                        ROOT.RooFit.PrintLevel(-1),
                        # ROOT.RooFit.Verbose(True),
                        # ROOT.RooFit.Save(),
                    ) # this fixes issues with the convergence of the second fit
                except Exception as e:
                    logger.exception(f"Pre-fit failed in bin {label}")
                    continue
                try:
                    fitr = wsp.pdf("model").fitTo(
                        wsp.data(dat),
                        ROOT.RooFit.Optimize(False),
                        #ROOT.RooFit.PrintLevel(2),
                        ROOT.RooFit.Minimizer("Minuit2", "Migrad"),
                        ROOT.RooFit.Offset(True),
                        ROOT.RooFit.Extended(True),
                        ROOT.RooFit.SumW2Error(True),
                        ROOT.RooFit.PrintLevel(-1),
                        # ROOT.RooFit.Verbose(True),
                        ROOT.RooFit.Strategy(2),
                        ROOT.RooFit.Save()
                    )
                except Exception as e:
                    logger.exception(f"Main fit failed in bin {label}")
                    continue
                # fitr.Print()
                # fitr.correlationMatrix().Print()
                # cov_matrix = fitr.covarianceMatrix()  # returns TMatrixDSym
                # print(cov_matrix.Print())
                # compare_uncertainties(wsp, wsp.data(dat), param_name="efficiency", nsigma=1.0, plot_file="nlllex.png") #f"{filename[:-5]}_nll_efficiency_{i}_k.png"))

                nll = wsp.pdf("model").createNLL(wsp.data(dat), ROOT.RooFit.Extended(True), ROOT.RooFit.Offset(True))

                val, err_lo, err_hi = scan_uncertainty(wsp, "efficiency", nll, wsp.data(dat))

                eff = wsp.var("efficiency")
                eff.setVal(val)
                eff.setError((err_hi + err_lo) / 2.0)
                wsp.var("efficiency").setError(eff.getError())

                print(f"Deviation yields for : {eff.getVal()-sds}")
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
                effs_sig[run_no][i] = wsp.var("efficiency").getVal()
                effs_bkg[run_no2][i] = wsp.var("efficiency").getVal()
                effs[run_no][run_no2][i] = wsp.var("efficiency").getVal()

                if xframe.chiSquare("AllPass", "DataPass", nparams) < chi2s[i]: # Check whether current chi2 is lower than current lowest (starts with inf)
                    # man_calc[i] = yield_pass / yield_tot
                    best_comb[0][i] = run_no
                    best_comb[1][i] = run_no2
                    chi2s[i] = xframe.chiSquare("AllPass", "DataPass", nparams)
                    hist.SetBinContent(b[0], b[1], wsp.var("efficiency").getVal())
                    hist.SetBinError(b[0], b[1], wsp.var("efficiency").getError())

                    hsyst.SetBinContent(b[0], b[1], wsp.var("efficiency").getVal())
                    hsyst2.SetBinContent(b[0], b[1], wsp.var("efficiency").getVal())
                    
                    
                    h2.SetBinContent(b[0], b[1], xframe.chiSquare("AllPass", "DataPass", nparams)) # update heatmap with new chi2 val for corresponding bin
                    hmod.SetBinContent(b[0], b[1], run_no + 1) 
                    hsyst.SetBinContent(b[0], b[1], wsp.var("efficiency").getVal())
                    hsyst2.SetBinContent(b[0], b[1], wsp.var("efficiency").getVal())
                    hmod2.SetBinContent(b[0], b[1], run_no2 + 1)


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
                    latex.DrawLatex(0.2, 0.8555, "Private work")
                    latex.DrawLatex(0.2, 0.825, "(CMS data/simulation)")
                    # latex.DrawLatex(0.2, 0.75, bkg_model)
                    latex.DrawLatex(
                        0.63,
                        0.75,
                        "#chi^{2}/ndf = %.2f" % (abs(xframe.chiSquare("AllPass", "DataPass", nparams))),
                    )
                    val = wsp.var("efficiency").getVal()
                    err = wsp.var("efficiency").getError()

                    if err < 1e-4:
                        label = "#varepsilon = %.4f #pm %.1e" % (val, err)
                    else:
                        label = "#varepsilon = %.4f #pm %.4f" % (val, err)

                    latex.DrawLatex(0.63, 0.7, label)

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
                        "#chi^{2}/ndf = %.2f" % (abs(xframe2.chiSquare("AllFail", "DataFail", nparams))),
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

                    canv.Print("%s/%s_%s_%s.png" % (plot_dir, canv.GetName(), sig_model, bkg_model))
                        #canv.Print("%s/%s.png" % (plot_dir, canv.GetName()))
                        # canv.Print("%s/%s.pdf" % (plot_dir, canv.GetName())) uncomment
                
                if ENABLE_TEST_BIN:
                    sig_mean = effs[run_no][run_no2][i]  
                    kek = [effs[run_no][run_no2][i]]
                    bkg_dev = [0.0] 
                    new = 0.0 
                    max_sig_dev = 0.0
                    max_bkg_dev = 0.0
                
                elif (run_no == (len(sig_models)-1)) and (bkg_model == bkg_models[-1]):
                    sig_mean = sum([effs[j][best_comb[1][i]][i] for j in range(len(sig_models))]) / len(sig_models) if sig_models else 0.0
                    
                    sig_dev = [abs(effs[j][best_comb[1][i]][i] - effs[best_comb[0][i]][best_comb[1][i]][i]) for j in range(len(sig_models))] # Calulate efficiency deviation for signal models
                    kek = [effs[j][best_comb[1][i]][i] for j in range(len(sig_models))]
                    print(sig_mean, kek)
                    bkg_dev = [abs(effs[best_comb[0][i]][j][i] - effs[best_comb[0][i]][best_comb[1][i]][i]) for j in range(len(bkg_models))]
                    new = abs(sig_mean - effs[best_comb[0][i]][best_comb[1][i]][i])
                    max_sig_dev = max(sig_dev) if sig_dev else 0.0
                    max_bkg_dev = max(bkg_dev) if bkg_dev else 0.0
        
                    hsyst.SetBinError(b[0], b[1], new)
                    hsyst2.SetBinError(b[0], b[1], max_bkg_dev)

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

    logger.info("="*50)
    logger.info(f"Beginne Dateierstellung für {filename}, name={name}")
    logger.info(f"Arbeitsverzeichnis: {os.getcwd()}")

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
    d = ROOT.TCanvas("Signal_Model_acceptance", "Signal model acceptance heatmap", 800, 600)
    hmod.Draw("COLZ")
    d.Write("signal model canvas")
    hmod.Write()

    e = ROOT.TCanvas("Background_Model_acceptance", "Background model acceptance heatmap", 800, 600)
    hmod2.Draw("COLZ")
    e.Write("background model canvas")
    hmod2.Write()

    try:
        outfile = ROOT.TFile(
            filename.replace(".root", "_Fits_%s%s.root" % (name, postfix)), "RECREATE"
        )

        hist.Write()
        hsyst.Write()
        hsyst2.Write()

        for i in range(1, hist.GetNbinsY() + 1):
            slice = hist.ProjectionX("%s_projx_%i" % (hist.GetName(), i), i, i)
            slice.Write()
            gr = ROOT.TGraphAsymmErrors(slice)
            gr.SetName("gr_" + slice.GetName())
            gr.Write()

        heat_out.Close()

        def save_bin_summary(filename, hist, hmod, hmod2, h2, hsyst, hsyst2, sig_models, bkg_models, output_dir=None, measurement_name = ""):
            """
            Speichert ein Dictionary pro pt-eta-Bin mit den besten Signal/Background-Kombinationen und Chi2/Effizienz.
            """
            bin_summary = {"bins": []}

            for i in range(1, hist.GetNbinsX() + 1):
                for j in range(1, hist.GetNbinsY() + 1):
                    pt_min = hist.GetXaxis().GetBinLowEdge(i)
                    pt_max = hist.GetXaxis().GetBinUpEdge(i)
                    eta_min = hist.GetYaxis().GetBinLowEdge(j)
                    eta_max = hist.GetYaxis().GetBinUpEdge(j)

                    best_sig_idx = int(hmod.GetBinContent(i, j)) - 1
                    best_bkg_idx = int(hmod2.GetBinContent(i, j)) - 1

                    sig_chi2 = h2.GetBinContent(i, j)  # Chi2 des besten kombinierten Fits
                    bkg_chi2 = sig_chi2  # Optional: kann angepasst werden, wenn getrennt

                    sig_uncertainty = hsyst.GetBinError(i, j)
                    bkg_uncertainty = hsyst2.GetBinError(i, j)
                    eff = hist.GetBinContent(i, j)

                    bin_summary["bins"].append({
                        "pt": [pt_min, pt_max],
                        "eta": [eta_min, eta_max],
                        "best_sig": sig_models[best_sig_idx] if best_sig_idx >= 0 else None,
                        "best_bkg": bkg_models[best_bkg_idx] if best_bkg_idx >= 0 else None,
                        "sig_chi2": sig_chi2,
                        "bkg_chi2": bkg_chi2,
                        "eff": eff,
                        "sig_uncertainty": sig_uncertainty,
                        "bkg_uncertainty": bkg_uncertainty
                    })

            # Bestimme den Typ aus dem Dateinamen
            if "Data" in filename:
                type_suffix = "_data"
            elif "Embedding" in filename:
                type_suffix = "_emb"
            elif "DY" in filename or "MC" in filename:
                type_suffix = "_mc"
            else:
                type_suffix = "_unknown"

            name_suffix = f"_{measurement_name}" if measurement_name else ""

            # Speicherpfad
            out_dir = output_dir if output_dir else os.path.dirname(filename)
            os.makedirs(out_dir, exist_ok=True)

            base_name = os.path.basename(filename).replace(".root", "")
            yaml_filename = os.path.join(out_dir, f"{base_name}{name_suffix}{type_suffix}_pt_eta_bins.yaml")

            with open(yaml_filename, 'w') as yaml_file:
                yaml.dump(bin_summary, yaml_file, default_flow_style=False, indent=2)
        
            logger.info(f"YAML-Zusammenfassung gespeichert in: {yaml_filename}")


        save_bin_summary(filename, hist, hmod, hmod2, h2, hsyst, hsyst2, sig_models, bkg_models, output_dir=yaml_output_dir, measurement_name=name)

        outfile.Close()

    except Exception as e:
        logger.exception("Writing output ROOT file failed")

    wsp.Delete()
    
