import logging
import yaml
import glob

import numpy as np

import ROOT as root
# Disable ROOT internal argument parser.
root.PyConfig.IgnoreCommandLineOptions = True
root.gErrorIgnoreLevel = root.kError
root.gROOT.SetBatch(1)
root.ROOT.EnableImplicitMT(10)

logger = logging.getLogger(__name__)


class TauLegEfficiencies(object):
    """A class to store Efficiency objects."""

    def __init__(self, era, outname, input_dir,
                 treeName="mt/ntuple",
                 conf_file="settings/config_tau_legs.yaml",
                 per_dm=False,
                 use_et=False):
        self._efficiencies = []
        self._working_points = []
        self._trigger_names = []
        self._filetypes = []

        self._era = era
        self._outfile = root.TFile(outname, "recreate")
        self._input_dir = input_dir
        self._tree_name = treeName
        self._config = yaml.load(open(conf_file, "r"))[era]
        self._per_dm = per_dm
        self._use_et = use_et

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
        if wp not in self._config["tauId_wps"].keys():
            logger.fatal("Given working point %s is not available."
                         " MVA working point must be one of %s",
                         wp, self._config["tauId_wps"].keys())
            raise Exception
        self.working_points.append(wp)

    def add_trigger_name(self, trigger):
        available_trgs = set(
                key for val in self._config["trigger_dict"].values()
                for key in val.keys())
        logger.debug("Set of possible trigger paths: %s", available_trgs)
        if trigger not in available_trgs:
            logger.fatal("Given trigger path %s is not available."
                         " Trigger path must be one of %s",
                         trigger,
                         list(available_trgs))
            raise Exception
        self._trigger_names.append(trigger)

    def add_filetype(self, filetype):
        if filetype not in self._config["file_dict"].keys():
            logger.fatal("Given trigger path %s is not available."
                         " Trigger path must be one of %s",
                         filetype, self._config["file_dict"].keys())
            raise Exception
        self._filetypes.append(filetype)

    def _create_file_regex(self, filetype, use_et=False):
        if use_et:
            file_dict = self._config["file_dict_et"]
        else:
            file_dict = self._config["file_dict"]
        file_vector = root.vector("string")()
        glob_exp = "{inp}{fi}/{fi}.root".format(inp=self.input_dir,
                                                fi=file_dict[filetype])
        logger.debug("Looking for files matching to glob expression: %s",
                     glob_exp)
        for path in glob.glob(glob_exp):
            file_vector.push_back(path)
        if file_vector.size() == 0:
            logger.fatal("No files matching the given pattern found.")
            raise Exception
        return file_vector

    def create_efficiencies(self):
        for filetype in self.filetypes:
            # Do some list magic to be able to process the
            # etau cross trigger seperately.
            if self._use_et:
                logger.info("Taking etau trigger efficiency from et channel..")
                if "etau" in self._trigger_names:
                    self._trigger_names.remove("etau")

            # Loop over double list to process
            # etau triggers seperately from other triggers.
            dataframe = root.RDataFrame(
                    self.tree_name, self._create_file_regex(filetype))
            logger.debug("Cutstring: {}".format(
                 "(" + ")&&(".join(
                     self._config["baseline_selection"] if filetype == "DATA"
                     else self._config["baseline_selection"]+["isOS"])) + ")")
            d_baseline = dataframe.Filter(
                 "(" + ")&&(".join(
                     self._config["baseline_selection"] if filetype == "DATA"
                     else self._config["baseline_selection"]+["isOS"]) + ")")
            for wp in self.working_points:
                d_wp = d_baseline.Filter(self._config["tauId_wps"][wp]+">0.5")
                if self._per_dm:
                    for trg in self.trigger_names:
                        for dm in [0, 1, 10]:
                            d_dm = d_wp.Filter("decayMode_p == {}".format(dm))
                            self._efficiencies.append(
                                    Efficiency(d_dm, wp, trg, filetype,
                                               self._era,
                                               self._config["trigger_dict"],
                                               decayMode=dm))
                        self._efficiencies.append(
                                Efficiency(d_wp, wp, trg, filetype, self._era,
                                           self._config["trigger_dict"]))
                else:
                    for trg in self.trigger_names:
                        self._efficiencies.append(
                                Efficiency(d_wp, wp, trg, filetype, self._era,
                                           self._config["trigger_dict"]))
            logger.info("Writing resulting histograms to %s.",
                        self._outfile.GetName())
            for eff in self._efficiencies:
                eff.save_histograms()
            self._efficiencies = []

            # Process etau trigger seperately if required.
            if self._use_et:
                dataframe = root.RDataFrame(
                        self.tree_name.replace("mt", "et"),
                        self._create_file_regex(filetype, self._use_et))
                logger.debug("Cutstring: {}".format(
                     "(" + ")&&(".join(
                         self._config["baseline_selection_et"] if filetype == "DATA"
                         else self._config["baseline_selection_et"] + ["isOS"])) + ")")
                d_baseline = dataframe.Filter(
                     "(" + ")&&(".join(
                         self._config["baseline_selection_et"] if filetype == "DATA"
                         else self._config["baseline_selection_et"]+["isOS"]) + ")")
                for wp in self.working_points:
                    d_wp = d_baseline.Filter(self._config["tauId_wps"][wp]+">0.5")
                    if self._per_dm:
                        for dm in [0, 1, 10]:
                            d_dm = d_wp.Filter("decayMode_p == {}".format(dm))
                            self._efficiencies.append(
                                    Efficiency(d_dm, wp, "etau", filetype, self._era,
                                               self._config["trigger_dict_et"],
                                               decayMode=dm))
                        self._efficiencies.append(
                                Efficiency(d_wp, wp, "etau", filetype, self._era,
                                           self._config["trigger_dict_et"]))
                    else:
                        self._efficiencies.append(
                                Efficiency(d_wp, wp, "etau", filetype, self._era,
                                           self._config["trigger_dict_et"]))
                logger.info("Writing resulting histograms to %s.", self._outfile.GetName())
                for eff in self._efficiencies:
                    eff.save_histograms()
                self._efficiencies = []
        self._outfile.Close()
        return


class Efficiency(object):
    """A class to store and produce trigger efficiencies."""

    def __init__(self, dataframe, working_point,
                 trigger, filetype, era, trigger_dict,
                 decayMode=None):
        """Init method of Efficiency class."""
        self._working_point = working_point
        self._trigger_name = trigger
        self._suffix = filetype
        self._era = era
        self._decayMode = decayMode
        self._create_histogram_models()
        self._categories = yaml.load(open("settings/config_tau_legs.yaml", "r"))[self._era]["etaphi_cats"]
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

    @property
    def decayMode(self):
        return self._decayMode

    def save_histograms(self):
        logger.info("Saving %s histograms for tau leg of the %s trigger and"
                    " %s MVA working point",
                    self.suffix,
                    self.trigger_name,
                    self.working_point)

        self._save_1Dhistogram()
        self._save_2Dhistograms()
        return

    def _create_histogram_models(self):
        bin_settings = yaml.load(
                open("settings/settings_tau_trigger.yaml", "r"))
        if self._decayMode is None:
            bins = bin_settings["bins_fits"][self._era][self.trigger_name]
        else:
            bins = bin_settings["bins_fits_dm"][self._era][self.trigger_name][self.decayMode][self.suffix]
        self._mod_th1d_pT = root.RDF.TH1DModel(
                "mod_th1d_pT", "mod_th1d_pT",
                len(bins["pT"])-1, np.array(bins["pT"], dtype=float))
        self._mod_th2d_eta_phi = root.RDF.TH2DModel(
                "mod_th2d_eta_phi", "mod_th2d_eta_phi",
                len(bins["eta"])-1, np.array(bins["eta"], dtype=float),
                len(bins["phi"])-1, np.array(bins["phi"], dtype=float))
        self._mod_th2d_eta_phi_AVG = root.RDF.TH2DModel(
                "mod_th2d_eta_phi_AVG", "mod_th2d_eta_phi_AVG",
                len(bins["etaAVG"])-1, np.array(bins["etaAVG"], dtype=float),
                len(bins["phiAVG"])-1, np.array(bins["phiAVG"], dtype=float))
        return

    def _create_histogram_pointers(self, dataframe, trigger_dict):
        logger.debug("Creating %s histograms for tau leg of the %s trigger"
                     " and %s MVA working point",
                     self.suffix,
                     self.trigger_name,
                     self.working_point)

        self.hist1d_total = dataframe.Histo1D(
                self._mod_th1d_pT, "pt_p", "bkgSubWeight")

        dataframe_pass = dataframe.Filter(trigger_dict[self.suffix][self.trigger_name])

        self.hist1d_pass = dataframe_pass.Histo1D(
                self._mod_th1d_pT, "pt_p", "bkgSubWeight")

        # Read cuts to be applied before calculating the eta phi histograms.
        pt_cut = yaml.load(open("settings/settings_tau_trigger.yaml", "r"))["pt_cuts_2d"][self._era][self.trigger_name]

        dataframe_2d = dataframe.Filter(pt_cut)
        self._hist2d_pointers = {}
        for cat, cutstr in self._categories.iteritems():
            self._hist2d_pointers[cat] = {}
            self._hist2d_pointers[cat]["total"] = dataframe_2d \
                .Filter("("+")&&(".join(cutstr)+")") \
                .Histo2D(self._mod_th2d_eta_phi, "eta_p", "phi_p", "bkgSubWeight")
            self._hist2d_pointers[cat]["pass"] = dataframe_2d \
                .Filter("("+")&&(".join(cutstr)+")") \
                .Filter(trigger_dict[self.suffix][self.trigger_name]) \
                .Histo2D(self._mod_th2d_eta_phi, "eta_p", "phi_p", "bkgSubWeight")
        return

    def _save_1Dhistogram(self):
        h_eff = root.TH1D(self.hist1d_pass.GetValue())
        h_eff.Sumw2()
        h_eff.Divide(self.hist1d_pass.GetValue(), self.hist1d_total.GetValue(),
                     1., 1., "b(1,1) cl=0.683 mode")

        g_eff = root.TGraphAsymmErrors(self.hist1d_pass.GetValue(),
                                       self.hist1d_total.GetValue())

        h_fail = root.TH1D(self.hist1d_total.GetValue())
        h_fail.Sumw2()
        h_fail.Add(self.hist1d_pass.GetValue(), -1.)
        g_eff_v2 = root.RooHist(self.hist1d_pass.GetValue(), h_fail,
                                0, 1., root.RooAbsData.Poisson, 1.,
                                root.kTRUE, 1.)

        form_opts = [self.trigger_name, self.working_point]
        if self.decayMode is None:
            ti_tmpl = "{}_{}TriggerEfficiency_{}TauMVA_{}"
        else:
            ti_tmpl = "{}_{}TriggerEfficiency_{}TauMVA_dm{}_{}"
            form_opts.append(self.decayMode)
        form_opts.append(self.suffix)

        self._save_root_object(g_eff, ti_tmpl.format("graph", *form_opts))
        self._save_root_object(g_eff_v2, ti_tmpl.format("graphv2", *form_opts))
        self._save_root_object(h_eff, ti_tmpl.format("hist", *form_opts))
        return

    def _save_2Dhistograms(self):
        for cat, hist_ptrs in self._hist2d_pointers.iteritems():
            h_eff = root.TH2D(hist_ptrs["pass"].GetValue())
            h_eff.Sumw2()
            h_eff.Divide(hist_ptrs["pass"].GetValue(), hist_ptrs["total"].GetValue(),
                         1., 1., "b(1,1) cl=0.683 mode")
            self._save_root_object(h_eff, self._get_2dhist_name(cat))
        return

    def _get_2dhist_name(self, cat_name):
        form_opts = [self.trigger_name, self.working_point]
        ti_tmpl = "{}_{}MVAv2_dm{}_{}_{}"
        if self.decayMode is None:
            form_opts.append("Cmb")
        else:
            form_opts.append(self.decayMode)
        form_opts.extend([self.suffix, cat_name])
        return ti_tmpl.format(*form_opts)

    def _save_root_object(self, root_obj, title):
        root_obj.SetName(title)
        root_obj.SetTitle(title)
        root_obj.Write(title)
        return
