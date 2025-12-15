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

    def make_sf_entry(self, sf_value, sf_error):
        return {
            "nodetype": "category",
            "input": "sf",
            "content": [
                {"key": "value", "value": sf_value},
                {"key": "error", "value": sf_error},
            ],
        }


    def get_single_sf(self, pt, eta, data_only, inputtype=None):
        efficiency = {}
        efficiency_err = {}
        for _type in self.types:
            obj = self.inputobjects[_type]["object"]
            efficiency[_type] = obj.GetBinContent(
                obj.GetXaxis().FindBin(pt), obj.GetYaxis().FindBin(eta)
            )
            efficiency_err[_type] = obj.GetBinError(
                obj.GetXaxis().FindBin(pt), obj.GetYaxis().FindBin(eta)
            )

        # SF und Fehler berechnen
        if data_only:
            if efficiency["Data"] < epsilon:
                sf = 0.0
                sf_err = 0.0
            else:
                sf = 1.0 / efficiency["Data"]
                sf_err = efficiency_err["Data"] / (efficiency["Data"]**2)
        else:
            if efficiency[inputtype] < epsilon:
                sf = 1.0
                sf_err = 0.01
            else:
                sf = efficiency["Data"] / efficiency[inputtype]
                sf_err = math.sqrt(
                    (efficiency_err["Data"] / efficiency[inputtype])**2
                    + (efficiency_err[inputtype] * efficiency["Data"] / efficiency[inputtype]**2)**2
                )
                if abs(efficiency["Data"] - efficiency[inputtype]) < epsilon:
                    sf = 1.0
                    sf_err = 0.01

        return self.make_sf_entry(sf, sf_err)


    def get_sfs_for_etas(self, pt, etas, data_only, inputtype=None):
        sfs = []
        for eta in etas[:-1]:
            if data_only:
                sfs.append(self.get_single_sf(pt, eta, data_only))
            else:
                # Für MC/Embedding Typen
                category_content = []
                for typ in ["DY", "Embedding"]:
                    category_content.append({
                        "key": typ.lower(),
                        "value": self.get_single_sf(pt, eta, data_only=False, inputtype=typ)
                    })
                sfs.append({
                    "nodetype": "category",
                    "input": "type",
                    "content": category_content
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
