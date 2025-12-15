import correctionlib._core as core
import correctionlib.schemav2 as schema
import correctionlib.JSONEncoder as JSONEncoder
import ROOT
import json
import os
import yaml
import math

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Handler für Konsole und Logdatei
console = logging.StreamHandler()
console.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(console)
logger.info("Logger initialisiert")

# set epsilon value to avoid giant scale factors
epsilon = 0.001


class CorrectionSet(object):
    def __init__(self, name):
        self.name = name
        self.corrections = []

    def add_correction_file(self, correction_file):
        with open(correction_file) as file:
            data = json.load(file)
            corr = schema.Correction.parse_obj(data)
            self.add_correction(corr)

    def add_correction(self, correction):
        if isinstance(correction, dict):
            self.corrections.append(correction)
        elif isinstance(correction, Correction):
            self.corrections.append(correction.correctionset)
        else:
            raise TypeError(
                "Correction must be a Correction object or a dictionary, not {}".format(
                    type(correction)
                )
            )

    def write_json(self, outputfile):
        # Create the JSON object
        cset = schema.CorrectionSet(
            schema_version=schema.VERSION, corrections=self.corrections
        )
        print(f">>> Writing {outputfile}...")
        JSONEncoder.write(cset, outputfile)
        JSONEncoder.write(cset, outputfile + ".gz")


class Correction(object):
    def __init__(
        self,
        tag,
        name,
        outdir,
        configfile,
        era,
        fname="",
        data_only=False,
        verbose=False,
    ):
        self.tag = tag
        self.name = name
        self.outdir = outdir
        self.configfile = configfile
        self.ptbinning = []
        self.etabinning = []
        self.inputfiles = []
        self.correction = None
        self.era = era
        self.header = ""
        self.fname = fname
        self.info = ""
        self.verbose = verbose
        self.data_only = data_only
        self.correctionset = None
        self.inputobjects = {}
        self.types = ["Data", "Embedding", "DY"]

    def __repr__(self) -> str:
        return "Correction({})".format(self.name)

    def __str__(self) -> str:
        return "Correction({})".format(self.name)

    def parse_config(self):
        pass

    def setup_scheme(self):
        pass

    def generate_sfs(self):
        pass

    def generate_scheme(self):
        pass

    def GetFromTFile(self, inputfile, object_name):
        print("Getting ", object_name, "from ", inputfile)
        f = ROOT.TFile.Open(inputfile)
        obj = f.Get(object_name)
        if not obj:
            raise ValueError(f"Object {object_name} not found in {inputfile}")
        obj_clone = obj.Clone()        # klonen, um es unabhängig vom File zu machen
        obj_clone.SetDirectory(0)      # WICHTIG: verhindert, dass ROOT das Objekt beim Schließen löscht
        f.Close()
        return obj_clone


    def write_scheme(self):
        if self.verbose >= 2:
            print(JSONEncoder.dumps(self.correction))
        elif self.verbose >= 1:
            print(self.correction)
        if self.fname:
            print(f">>> Writing {self.fname}...")
        JSONEncoder.write(self.correction, self.fname)


class pt_eta_correction(Correction):
    def __init__(
        self,
        tag,
        name,
        configfile,
        era,
        outdir,
        fname="",
        data_only=False,
        verbose=False,
        variation="nominal"
    ):
        super(pt_eta_correction, self).__init__(
            tag,
            name,
            outdir,
            configfile,
            era,
            fname,
            data_only,
            verbose,
        )
        self.variation = variation
        if self.data_only:
            self.types = ["Data"]

    def parse_config(self):
        config = yaml.safe_load(open(self.configfile))
        self.ptbinning = config[self.name]["bins_x"]
        self.etabinning = config[self.name]["bins_y"]
        basename = str(os.path.basename(self.configfile)).split("_")[1]
        self.inputfiles = {}
        for _type in self.types:
            self.inputfiles[_type] = {
                "name": self.name,
                "file": os.path.join(
                    self.outdir.replace("/jsons", ""),
                    "{basename}_TP_{_type}_{era}_Fits_{name}.root".format(
                        basename=basename, _type=_type, era=self.era, name=self.name
                    ),
                ),
            }
        for _input in self.inputfiles.keys():
            histogram = self.GetFromTFile(
                self.inputfiles[_input]["file"], self.inputfiles[_input]["name"]
            )
            self.inputobjects[_input] = self.inputfiles[_input]
            self.inputobjects[_input]["object"] = histogram
        self.info = config[self.name]["info"]
        self.header = config[self.name]["header"]

    def setup_scheme(self):
        self.correctionset = {
            "version": 0,
            "name": self.name,
            "description": self.info,
            "inputs": [
                {
                    "name": "pt",
                    "type": "real",
                    "description": "Reconstructed muon pT",
                },
                {
                    "name": "abs(eta)",
                    "type": "real",
                    "description": "Reconstructed muon eta",
                },
            ],
            "output": {
                "name": "sf",
                "type": "real",
                "description": "pT-eta-dependent scale factor",
            },
            "data": None,
        }
        if not self.data_only:
            self.correctionset["inputs"].append(
                {
                    "name": "type",
                    "type": "string",
                    "description": "Type of correction: Embedding or MC",
                }
            )

    def generate_sfs(self):
        sfs = {}
        if self.data_only:
            sfs = {
                "nodetype": "binning",
                "input": "pt",
                "edges": self.ptbinning,
                "flow": "clamp",
                "content": [
                    {
                        "nodetype": "binning",
                        "input": "abs(eta)",
                        "edges": self.etabinning,
                        "flow": "clamp",
                        "content": self.get_sfs_for_etas(
                            pt, self.etabinning, self.data_only
                        ),
                    }
                    for pt in self.ptbinning[:-1]
                ],
            }
        else:
            # without data only, we add both the mc and the embedding sfs
            sfs = {
                "nodetype": "binning",
                "input": "pt",
                "edges": self.ptbinning,
                "flow": "clamp",
                "content": [
                    {
                        "nodetype": "binning",
                        "input": "abs(eta)",
                        "edges": self.etabinning,
                        "flow": "clamp",
                        "content": [
                            {
                                "nodetype": "category",
                                "input": "type",
                                "content": [
                                    {
                                        "key": "mc",
                                        "value": self.get_single_sf(
                                            pt,
                                            eta,
                                            self.data_only,
                                            inputtype="DY",
                                        ),
                                    },
                                    {
                                        "key": "emb",
                                        "value": self.get_single_sf(
                                            pt,
                                            eta,
                                            self.data_only,
                                            inputtype="Embedding",
                                        ),
                                    },
                                ],
                            }
                            for eta in self.etabinning[:-1]
                        ],
                    }
                    for pt in self.ptbinning[:-1]
                ],
            }
        return schema.Binning.parse_obj(sfs)

    def make_values_category(self, sf_value, sf_error):
        content = [{"key": self.variation, "value": sf_value}]
        if self.variation == "nominal":
            content.append({"key": "stat_error", "value": sf_error})
        return {
            "nodetype": "category",
            "input": "values",
            "content": content
        }


    def get_single_sf(self, pt, eta, data_only, inputtype=None):
        """
        Berechnet SF und nur den statistischen Fehler für ein pt/eta-Bin.
        Gibt (nominal, stat_err) zurück (beides floats).
        """
        efficiency = {}
        efficiency_err = {}
        for _type in self.types:
            obj = self.inputobjects[_type]["object"]
            binx = obj.GetXaxis().FindBin(pt)
            biny = obj.GetYaxis().FindBin(eta)
            efficiency[_type] = obj.GetBinContent(binx, biny)
            efficiency_err[_type] = obj.GetBinError(binx, biny)

        # Default-Fallbacks
        if data_only:
            if efficiency["Data"] < epsilon:
                nominal = 0.0
                stat_err = 0.0
            else:
                nominal = 1.0 / efficiency["Data"]
                stat_err = efficiency_err["Data"] / (efficiency["Data"] ** 2)
        else:
            # für MC/Embedding-Fälle
            if efficiency.get(inputtype, 0.0) < epsilon:
                # Input efficiency zu klein -> sanitizing
                nominal = 1.0
                stat_err = 0.01
            else:
                nominal = efficiency["Data"] / efficiency[inputtype]
                # Fehlerpropagation für Quotient Data / Input:
                # sigma_sf = sf * sqrt( (sigma_data / data)^2 + (sigma_input / input)^2 )
                # (äquivalent zu der bisherigen Form)
                if efficiency["Data"] > 0 and efficiency[inputtype] > 0:
                    rel2 = (efficiency_err["Data"] / efficiency["Data"]) ** 2 + (
                        efficiency_err[inputtype] / efficiency[inputtype]
                    ) ** 2
                    stat_err = abs(nominal) * math.sqrt(rel2)
                else:
                    stat_err = 0.01

                # Sanitize: wenn Effizienzen praktisch gleich oder beide sehr klein
                if abs(efficiency["Data"] - efficiency[inputtype]) < epsilon or (
                    efficiency["Data"] < 0.01 and efficiency[inputtype] < 0.01
                ):
                    nominal = 1.0
                    stat_err = 0.0

        # Optional: weitere sanity-caps
        if stat_err is None or not (isinstance(stat_err, float) or isinstance(stat_err, int)):
            stat_err = 0.0

        return self.make_values_category(nominal, stat_err)



    def get_sfs_for_etas(self, pt, etas, data_only, inputtype=None):
        """
        Baut für ein gegebenes pt die Liste der eta-contents auf.
        - Bei data_only: für jedes eta eine 'values' category direkt.
        - Bei nicht-data_only: für jedes eta eine 'type' category, die für 'mc' und 'emb'
          jeweils eine 'values' category als value enthält.
        """
        sfs = []
        for eta in etas[:-1]:
            if data_only:
                nominal, stat_err = self.get_single_sf(pt, eta, data_only=True)
                sfs.append(self.make_values_category(nominal, stat_err))
            else:
                # Für MC und Embedding Typen: erstelle die values-category für jede
                mc_nom, mc_err = self.get_single_sf(pt, eta, data_only=False, inputtype="DY")
                emb_nom, emb_err = self.get_single_sf(pt, eta, data_only=False, inputtype="Embedding")

                sfs.append({
                    "nodetype": "category",
                    "input": "type",
                    "content": [
                        {
                            "key": "mc",
                            "value": self.make_values_category(mc_nom, mc_err)
                        },
                        {
                            "key": "emb",
                            "value": self.make_values_category(emb_nom, emb_err)
                        }
                    ]
                })
        return sfs


    def generate_scheme(self):
        self.parse_config()
        self.setup_scheme()
        self.correctionset["data"] = self.generate_sfs()
        output_corr = schema.Correction.parse_obj(self.correctionset)
        self.correction = output_corr
        # print(JSONEncoder.dumps(self.correction))


class emb_doublemuon_correction(Correction):
    def __init__(
        self,
        tag,
        name,
        configfile,
        era,
        outdir,
        triggernames,
        fname="",
        data_only=True,
        verbose=False,
        double_object_quantities_configfile=None,
    ):
        super(emb_doublemuon_correction, self).__init__(
            tag,
            name,
            outdir,
            configfile,
            era,
            fname,
            data_only,
            verbose,
        )
        self.types = ["Data"]
        self.names = triggernames

        self.double_object_quantities_configfile = double_object_quantities_configfile
        self.double_object_quantities = None
        self.parse_double_object_quantities_config()

    def parse_double_object_quantities_config(self):
        if self.double_object_quantities_configfile is not None:
            config = yaml.safe_load(open(self.double_object_quantities_configfile))
            basename = os.path.basename(
                self.double_object_quantities_configfile,
            ).split("_")[1].replace("_double_object_quantities", "").replace("settings_", "")
            self.double_object_quantities = {
                name: {
                    "name": name,
                    "file": os.path.join(
                        self.outdir.replace("/jsons", ""),
                        f"{basename}_TP_{_type}_{self.era}_Fits_{name}.root",
                    ),
                }
                for name in config.keys() for _type in self.types
            }
            for name in self.double_object_quantities:
                self.double_object_quantities[name]["object"] = self.GetFromTFile(
                    self.double_object_quantities[name]["file"],
                    self.double_object_quantities[name]["name"],
                )
                self.double_object_quantities[name]["config"] = config[name]

    def parse_config(self):
        config = yaml.safe_load(open(self.configfile))
        self.ptbinning = config[self.name]["bins_x"]
        self.etabinning = config[self.name]["bins_y"]
        basename = (
            str(os.path.basename(self.configfile)).split("_")[1].replace(".yaml", "")
        )
        self.inputfiles = {}
        for _type in self.types:
            for name in self.names:
                self.inputfiles[name] = {
                    "name": name,
                    "file": os.path.join(
                        self.outdir.replace("/jsons", ""),
                        "{basename}_TP_{_type}_{era}_Fits_{name}.root".format(
                            basename=basename, _type=_type, era=self.era, name=name
                        ),
                    ),
                }
        for _input in self.inputfiles.keys():
            histogram = self.GetFromTFile(
                self.inputfiles[_input]["file"], self.inputfiles[_input]["name"]
            )
            self.inputobjects[_input] = self.inputfiles[_input]
            self.inputobjects[_input]["object"] = histogram
        self.info = config[self.name]["info"]
        self.header = config[self.name]["header"]

    def setup_scheme(self):
        self.correctionset = {
            "version": 0,
            "name": self.name,
            "description": self.info,
            "inputs": [
                {
                    "name": "pt_1",
                    "type": "real",
                    "description": "Reconstructed leading genparticle pT",
                },
                {
                    "name": "abs(eta_1)",
                    "type": "real",
                    "description": "Reconstructed leading genparticle eta",
                },
                {
                    "name": "pt_2",
                    "type": "real",
                    "description": "Reconstructed trailing genparticle pT",
                },
                {
                    "name": "abs(eta_2)",
                    "type": "real",
                    "description": "Reconstructed trailing genparticle eta",
                },
            ],
            "output": {
                "name": "sf",
                "type": "real",
                "description": "pT-eta-dependent scale factor",
            },
            "data": None,
        }
        if not self.data_only:
            self.correctionset["inputs"].append(
                {
                    "name": "type",
                    "type": "string",
                    "description": "Type of correction: Embedding or MC",
                }
            )

    def generate_sfs(self):
        sfs = {
            "nodetype": "binning",
            "input": "pt",
            "edges": self.ptbinning,
            "flow": "clamp",
            "content": [
                {
                    "nodetype": "binning",
                    "input": "abs(eta)",
                    "edges": self.etabinning,
                    "flow": "clamp",
                    "content": self.get_sfs_for_etas(pt, self.etabinning, self.data_only)
                }
                for pt in self.ptbinning[:-1]
            ]
        }
        return schema.Binning.parse_obj(sfs)



    def generate_scheme(self):
        self.parse_config()
        self.setup_scheme()
        self.correctionset["data"] = self.generate_sfs()
        output_corr = schema.Correction.parse_obj(self.correctionset)
        self.correction = output_corr

    def write_scheme(self):
        if self.verbose >= 2:
            print(JSONEncoder.dumps(self.correction))
        elif self.verbose >= 1:
            print(self.correction)
        if self.fname:
            print(f">>> Writing {self.fname}...")
        JSONEncoder.write(self.correction, self.fname)


if __name__ == "__main__":
    pass
    # ROOT.PyConfig.IgnoreCommandLineOptions = True
    # ROOT.gROOT.SetBatch(ROOT.kTRUE)
    # # for keeping the histograms in memory
    # ROOT.TH1.AddDirectory(0)
    # test = pt_eta_correction(
    #     tag="test",
    #     name="EmbID_pt_eta_bins",
    #     outdir="output/jsons",
    #     configfile="settings/settings_embeddingselection_2018UL.yaml",
    #     era="2018UL",
    #     fname="{}/{}.json".format("output/jsons", "test"),
    #     data_only=True,
    #     verbose=False,
    # )
    # test.generate_scheme()