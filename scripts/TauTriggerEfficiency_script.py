import logging
import yaml
import glob

import numpy as np

import ROOT as root
# Disable ROOT internal argument parser.
root.PyConfig.IgnoreCommandLineOptions = True
root.gErrorIgnoreLevel = root.kError
root.gROOT.SetBatch(1)

logger = logging.getLogger(__name__)


class TauLegEfficiencies(object):
    """A class to store Efficiency objects."""

    _available_wp_dict = {
        "vloose": "byVLooseIsolationMVArun2017v2DBoldDMwLT2017_p",
        "loose": "byLooseIsolationMVArun2017v2DBoldDMwLT2017_p",
        "medium": "byMediumIsolationMVArun2017v2DBoldDMwLT2017_p",
        "tight": "byTightIsolationMVArun2017v2DBoldDMwLT2017_p",
        "vtight": "byVTightIsolationMVArun2017v2DBoldDMwLT2017_p",
        "vvtight": "byVVTightIsolationMVArun2017v2DBoldDMwLT2017_p",
    }

    _baseline_selection = [
        #  "trg_singlemuon_27",
         "abs(eta_p) < 2.1",
         "40. < m_ll && m_ll < 80.",
         "mt_t < 30",
         "decayModeFinding_p > 0.5",
         "againstMuonTight3_p > 0.5",
         # "(-1.)*(isOS==false)"
     ]

    _trigger_dict = {
        #"ETau": "trg_monitor_mu20tau27",
        "MuTau": "trg_crossmuon_mu20tau27",
        # "Tau35": "trg_monitor_mu24tau35_tight_tightID",
        # "MedTau40": "trg_monitor_mu24tau35_medium_tightID",
        # "TightTau40": "trg_monitor_mu24tau35_tight",
        # "diTau": "trg_monitor_mu24tau35_medium_tightID||trg_monitor_mu24tau35_tight||trg_monitor_mu24tau35_tight_tightID",  # noqa: E501
        "TauLead": "trg_singletau_leading",
        "TauTrail": "trg_singletau_trailing",
     }

    _file_dict = {
            "MC": "DY*JetsToLLM50*",
            "DATA": "SingleMuon*",
            "EMB": "Embedding*",  # noqa: E501
        }

    def __init__(self, outname, input_dir, treeName="mt/ntuple"):
        self._efficiencies = []
        self._working_points = []
        self._trigger_names = []
        self._filetypes = []
        self._outfile = root.TFile(outname, "recreate")
        self._input_dir = input_dir
        self._tree_name = treeName

    @property
    def working_points(self):
        return self._working_points

    @property
    def trigger_names(self):
        return self._trigger_names

    @property
    def filetypes(self):
        return self._filetypes

    @property
    def input_dir(self):
        return self._input_dir

    @property
    def tree_name(self):
        return self._tree_name

    def add_wp(self, wp):
        if wp not in self._available_wp_dict.keys():
            logger.fatal("Given working point %s is not available."
                         " MVA working point must be one of %s",
                         wp, self._available_wp_dict.keys())
            raise Exception
        self.working_points.append(wp)

    def add_trigger_name(self, trigger):
        if trigger not in self._trigger_dict.keys():
            logger.fatal("Given trigger path %s is not available."
                         " Trigger path must be one of %s",
                         trigger, self._trigger_dict.keys())
            raise Exception
        self._trigger_names.append(trigger)

    def add_filetype(self, filetype):
        if filetype not in self._file_dict.keys():
            logger.fatal("Given trigger path %s is not available."
                         " Trigger path must be one of %s",
                         filetype, self._file_dict.keys())
            raise Exception
        self._filetypes.append(filetype)

    def _create_file_regex(self, filetype):
        file_vector = root.vector("string")()
        glob_exp = "{inp}{fi}/{fi}.root".format(inp=self.input_dir,
                                                fi=self._file_dict[filetype])
        print glob_exp
        for path in glob.glob(glob_exp):
            file_vector.push_back(path)
        if file_vector.size == 0:
            logger.fatal("No files matching the given pattern found.")
            raise Exception
        return file_vector

    def create_efficiencies(self):
        for filetype in self.filetypes:
            dataframe = root.RDataFrame(
                    self.tree_name, self._create_file_regex(filetype))
            # TODO: not necessary with new ntuple. Kept to remember.
            # dataframe_woWeights = root.RDataFrame(
            #         self.tree_name, self._create_file_regex(filetype))
            # if filetype == "MC":
            #     dataframe = dataframe_woWeights.Define(
            #           "bkgSubWeight", "isOS")
            # else:
            #     dataframe = dataframe_woWeights.Define(
            #           "bkgSubWeight", "1.*(isOS) + (-1.)*(!isOS)")
            logger.debug("Cutstring: {}".format(
                            "&&".join(self._baseline_selection)))
            d_baseline = dataframe.Filter("&&".join(self._baseline_selection))
            for wp in self.working_points:
                d_wp = d_baseline.Filter(self._available_wp_dict[wp]+">0.5")
                for trg in self.trigger_names:
                    self._efficiencies.append(
                            Efficiency(d_wp, wp, trg, filetype,
                                       self._trigger_dict))
            logger.info("Writing resulting histograms to %s.", self._outfile)
            for eff in self._efficiencies:
                eff.save_histograms(self._trigger_dict)
            self._efficiencies = []
        self._outfile.Close()
        return


class Efficiency(object):
    """A class to store and produce trigger efficiencies."""

    bins = yaml.load(open("setting_tau_trigger.yaml", "r"))["bins"]
    _mod_th1d_pT = root.RDF.TH1DModel(
            "mod_th1d_pT", "mod_th1d_pT",
            len(bins["pT"])-1, np.array(bins["pT"], dtype=float))
    _mod_th2d_eta_phi = root.RDF.TH2DModel(
            "mod_th2d_eta_phi", "mod_th2d_eta_phi",
            len(bins["eta"])-1, np.array(bins["eta"], dtype=float),
            len(bins["phi"])-1, np.array(bins["phi"], dtype=float))
    _mod_th2d_eta_phi_AVG = root.RDF.TH2DModel(
            "mod_th2d_eta_phi_AVG", "mod_th2d_eta_phi_AVG",
            len(bins["etaAVG"])-1, np.array(bins["etaAVG"], dtype=float),
            len(bins["phiAVG"])-1, np.array(bins["phiAVG"], dtype=float))

    def __init__(self, dataframe, working_point,
                 trigger, filetype, trigger_dict):
        """Init method of Efficiency class."""
        self._working_point = working_point
        self._trigger_name = trigger
        self._suffix = filetype
        self._create_histogram_pointers(dataframe, trigger_dict)

    @property
    def working_point(self):
        return self._working_point

    @property
    def trigger_name(self):
        return self._trigger_name

    @property
    def suffix(self):
        return self._suffix

    def save_histograms(self, trigger_dict):
        logger.info("Saving %s histograms for tau leg of the %s trigger and"
                    " %s MVA working point",
                    self.suffix,
                    self.trigger_name,
                    self.working_point)

        self._save_1Dhistogram()
        self._save_2Dhistograms()
        return

    def _create_histogram_pointers(self, dataframe, trigger_dict):
        logger.debug("Creating %s histograms for tau leg of the %s trigger"
                     " and %s MVA working point",
                     self.suffix,
                     self.trigger_name,
                     self.working_point)

        self.hist1d_total = dataframe.Histo1D(
                self._mod_th1d_pT, "pt_p", "bkgSubWeight")
        self.hist2d_total = dataframe.Histo2D(
                self._mod_th2d_eta_phi, "eta_p", "phi_p", "bkgSubWeight")
        self.hist2d_AVG_total = dataframe.Histo2D(
                self._mod_th2d_eta_phi_AVG, "eta_p", "phi_p", "bkgSubWeight")

        dataframe_pass = dataframe.Filter(trigger_dict[self.trigger_name])

        self.hist1d_pass = dataframe_pass.Histo1D(
                self._mod_th1d_pT, "pt_p", "bkgSubWeight")
        self.hist2d_pass = dataframe_pass.Histo2D(
                self._mod_th2d_eta_phi, "eta_p", "phi_p", "bkgSubWeight")
        self.hist2d_AVG_pass = dataframe_pass.Histo2D(
                self._mod_th2d_eta_phi_AVG, "eta_p", "phi_p", "bkgSubWeight")
        return

    def _save_1Dhistogram(self):
        h_eff = root.TH1D(self.hist1d_pass.GetValue())
        h_eff.Sumw2()
        h_eff.Divide(self.hist1d_pass.GetValue(), self.hist1d_total.GetValue(),
                     1., 1., "b(1,1) cl=0.683 mode")

        g_eff = root.TGraphAsymmErrors(self.hist1d_pass.GetValue(),
                                       self.hist1d_total.GetValue())

        h_fail = root.TH1D(self.hist1d_total.GetValue())
        h_fail.Add(self.hist1d_pass.GetValue(), -1.)
        g_eff_v2 = root.RooHist(self.hist1d_pass.GetValue(), h_fail,
                                0, 1., root.RooAbsData.Poisson, 1.,
                                root.kTRUE, 1.)

        g_eff.SetName("graph_{}TriggerEfficiency_{}TauMVA_{}".format(
            self.trigger_name, self.working_point, self.suffix))
        g_eff.SetTitle("graph_{}TriggerEfficiency_{}TauMVA_{}".format(
            self.trigger_name, self.working_point, self.suffix))
        g_eff.Write("graph_{}TriggerEfficiency_{}TauMVA_{}".format(
            self.trigger_name, self.working_point, self.suffix))
        g_eff_v2.SetName("graphv2_{}TriggerEfficiency_{}TauMVA_{}".format(
            self.trigger_name, self.working_point, self.suffix))
        g_eff_v2.SetTitle("graphv2_{}TriggerEfficiency_{}TauMVA_{}".format(
            self.trigger_name, self.working_point, self.suffix))
        g_eff_v2.Write("graphv2_{}TriggerEfficiency_{}TauMVA_{}".format(
            self.trigger_name, self.working_point, self.suffix))
        h_eff.SetName("hist_{}TriggerEfficiency_{}TauMVA_{}".format(
            self.trigger_name, self.working_point, self.suffix))
        h_eff.SetTitle("hist_{}TriggerEfficiency_{}TauMVA_{}".format(
            self.trigger_name, self.working_point, self.suffix))
        h_eff.Write("hist_{}TriggerEfficiency_{}TauMVA_{}".format(
            self.trigger_name, self.working_point, self.suffix))
        return

    def _save_2Dhistograms(self):
        h_eff = root.TH2D(self.hist2d_pass.GetValue())
        h_eff.Sumw2()
        h_eff.Divide(self.hist2d_pass.GetValue(), self.hist2d_total.GetValue(),
                     1., 1., "b(1,1) cl=0.683 mode")
        h_eff.SetTitle("{}_{}_{}".format(
            self.trigger_name, self.working_point, self.suffix))
        h_eff.SetName("{}_{}_{}".format(
            self.trigger_name, self.working_point, self.suffix))
        h_eff.Write("{}_{}_{}".format(
            self.trigger_name, self.working_point, self.suffix))

        h_eff_AVG = root.TH2D(self.hist2d_AVG_pass.GetValue())
        h_eff_AVG.Sumw2()
        h_eff_AVG.Divide(self.hist2d_AVG_pass.GetValue(),
                         self.hist2d_AVG_total.GetValue(),
                         1., 1., "b(1,1) cl=0.683 mode")
        h_eff_AVG.SetTitle("{}_{}_AVG_{}".format(
            self.trigger_name, self.working_point, self.suffix))
        h_eff_AVG.SetName("{}_{}_AVG_{}".format(
            self.trigger_name, self.working_point, self.suffix))
        h_eff_AVG.Write("{}_{}_AVG_{}".format(
            self.trigger_name, self.working_point, self.suffix))
        return
