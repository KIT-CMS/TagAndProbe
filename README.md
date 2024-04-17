# TagAndProbe
Muon and electron tag and probe measurements and plotting. The Framework is used to measure several correction factors including

* Selection Efficiency of the DoubleMuon trigger used for Tau-Embedding samples
* Selection Efficiency of the Muon ID used for Tau-Embedding samples

* Muon ID Scale Factors
* Muon Isolation Scale Factors
* Muon Trigger Scale Factors

* Electron ID Scale Factors
* Electron Isolation Scale Factors
* Electron Trigger Scale Factors

The following description of the workflow is using CROWN ntuples and was written in 06/2023. Several steps have to be performed, in order to obtain the finished correction factors:

1. Production of Input NTuples using CROWN and Kingmaker
2. Merging of intput Ntuples into one file for data, embedding and MC
3. Creation of histograms for the tag and probe variables, based on the given Configuration
4. Fitting of the histograms and creation of the final correction factors
5. Plotting of the results
6. Export of the Correction Factors in a valid correctionlib json file


## 0. Installation
To setup Kingmaker an CROWN, run

```bash
git clone --recursive git@github.com:KIT-CMS/KingMaker.git
cd KingMaker
source setup.sh KingMaker
```

This will set up an instance of Kingmaker, including a checkout of CROWN.
In order to add the CROWN configuration needed for the tag and probe measurements, run

```bash
git clone git@github.com:KIT-CMS/TauAnalysis-CROWN.git CROWN/analysis_configurations/tau
```
Finally, the TagAndProbe Framework is setup using the `checkout.sh` script in the `scripts` folder. This will create a CMSSW environment and checkout the TagAndProbe Framework into the `src` folder. The script can be run using

```bash
wget https://raw.githubusercontent.com/KIT-CMS/TagAndProbe/master/scripts/checkout.sh
source checkout.sh
```


## 1. Creating the input files

The configuration used for the TagAndProbe NTuples is located in the collection of Tau Configurations for CROWN. They can be found in the https://github.com/KIT-CMS/TauAnalysis-CROWN repository. For the creation of the TagAndProbe ntuples, the [`tauembedding_tagandprobe.py`](https://github.com/KIT-CMS/TauAnalysis-CROWN/blob/main/tauembedding_tagandprobe.py) configuration is used. Additional information on how CROWN configurations work and how they are used can be found in the [CROWN documentation](https://crown.readthedocs.io/en/latest/py_configuration.html). Adapt the configuration according to your needs.


After the configuration is setup, the user has to define the samples to be processed. The most convenient way to do so is to use the `sample_manager` from KingMaker. First make sure, that the KingMaker environment is setup correctly in your shell (The setup is done using `source setup.sh KingMaker`), then run the Manager using

```bash
sample_manager
```

which will give you an interactive CLI to manage your samples. To create a new production file, select `Create a production file`
```
The database contains 581 samples, split over 4 era(s) and 22 sampletype(s)
? What do you want to do? (Use arrow keys)
   ○ Add a new sample
   ○ Edit a sample (not implemented yet)
   ○ Delete a sample
   ○ Find samples (by nick)
   ○ Find samples (by DAS name)
   ○ Print details of a sample
 » ○ Create a production file
   ○ Update genweight
   ○ Save and Exit
   ○ Exit without Save
  Answer: Create a production file
```
In the next step, select the eras you want to use using the arrow keys and space bar

```
 Select eras to be added  (Use arrow keys to move, <space> to select, <a> to toggle, <i> to invert)
   ○ 2016postVFP
   ○ 2016preVFP
   ● 2018
 » ● 2017
```

and then selection the sampleypes you want to process. For the TagAndProbe measurement, this should be `embedding`, `data` and `dyjets`. Finally, chose a filename, and the manager will create a .txt file containing all selected samples. Double check, that the file contains all samples you want to process.

To produce the ntuples, run

```bash
law run ProduceSamples --analysis tau --config tauembedding_tagandprobe --sample-list your_samplesfile.txt --production-tag your_productiontag --workers 100 --scopes mm,ee
```

The different options are:

* `--analysis` : The analysis to be run. This is used to select the correct configuration file. The analysis is always `tau` for the TagAndProbe ntuples.
* `--config` : The configuration to be used. This is the name of the configuration file without the `.py` extension. For the TagAndProbe ntuples, this is `tauembedding_tagandprobe`.
* `--sample-list` : The name of the file containing the samples to be processed. This is the file created by the sample manager.
* `--production-tag` : The production tag to be used. This is used to create the output directory. The samples will be stored on the grid, using this tag as identifier.
* `--worker` : The number of workers to be used. One worker is able to submit and track one sample at a time. To submit and process all samples in parallel, use a high number of workers.
* `--scopes`: The scopes to be used. This is a comma separated list of scopes. For the TagAndProbe ntuples, this should be `mm` for Emebdding Selection Corrections and Muon Scale Factors and `ee` for Electron Scale Factors.

`law` will now process all samples listed in the `sample-list` file. This will take some time, depending on the number of samples and workers used. After the processing is finished, the output files will be stored on the grid. The default in KingMaker uses the T3 GridKa storage, a different storage location can be configured in the KingMaker configuration file.


## 2. Merging the input files

After the NTuples are produced, the [merge_outputs](./merge_outputs.sh) script via
```
./merge_outputs.sh your_productiontag (muon|electron) your_era
```
The script will collect the samples from the grid and merge them into one file per sample. The merged files will be stored in `/ceph/${USER}/Run2UltraLegacy/scalefactors/${your_productiontag}/${your_era}UL`. After the merging, the [set_inputfiles.yaml](./set_inputfiles.yaml) file has to be adapted to use the merged files as input.

## 3. Configuring the scale factors

The input files

The Configurations can be found in the [configurations folder](./settings/UL/). The configuration files are named according to the era and channel, they are used for. They contain a list of different scale factors to measure. The configuration for each scale factor may look like the example shown below:

```yaml
Iso_pt_eta_bins:
  name: "Iso_pt_eta_bins"
  var: "m_vis(100,50,150)"
  tag: " iso_tag < 0.15 && fsr_photon_veto_tag < 0.5 && fsr_photon_veto_probe < 0.5 && dz_tag < 0.2 && dxy_tag < 0.045 && id_medium_tag && trg_IsoMu27_tag && pt_tag > 28 && id_medium_probe"
  probe: "iso_probe < 0.15"
  binvar_x: "pt_probe"
  bins_x:
    [
      10., 15., 20., 22., 24., 26., 28., 30., 32., 34., 36., 38., 40., 45., 50., 60., 80., 100., 200., 1000.,
    ]
  binvar_y: "abs(eta_probe)"
  bins_y: [0, 0.9, 1.2, 2.1, 2.4]
  # Settings for fits
  BKG: "Exponential"
  SIG: "DoubleVCorr"
  # Settings for plotting
  TITLE: "Iso_{#mu,rel} < 0.15"
  y_range: [0.6, 1.0]
  ratio_y_range: [0.8, 1.2]
  info: "Scale factor for the muon isolation iso_mu < 0.15 (binned in eta). Scale factor is provided for Embedding (emb) and Simulation (mc)"
  header: "Scale factor for the muon isolation iso_mu < 0.15 (binned in eta)"
```

The different required settings are:

* `name`: The name of the scale factor. This is used to name the output files.
* `var`: The variable used for the histogram. This is the variable used for the fit. Usually, the mass of the dilepton system called `m_vis` is used.
* `tag`: The selection string used to define the tag lepton. Internally, the terms `_tag` and `_probe` are replaced by `_1` and `_2` to ensure, that every lepton can be used as tag and probe.
* `probe`: The selection string used to define the probe lepton. This is the quantity, for which the efficiency is measured.
* `binvar_x`: The variable used for the x-axis of the histogram. This is usually the `pt` of the probe lepton.
* `bins_x`: The binning used for the x-axis of the histogram. This is a list of bin edges.
* `binvar_y`: The variable used for the y-axis of the histogram. This is usually the `eta` of the probe lepton.
* `bins_y`: The binning used for the y-axis of the histogram. This is a list of bin edges.
* `BKG`: The background model used for the fit. This is the name of the background model as defined in the [./scripts/fitTagAndProbe_script.py](./scripts/fitTagAndProbe_script.py) file.
* `SIG`: The signal model used for the fit. This is the name of the signal model as defined in the [./scripts/fitTagAndProbe_script.py](./scripts/fitTagAndProbe_script.py) file.
* `TITLE`: The title of the histogram. This is used for plotting.
* `y_range`: The range of the y-axis of the efficiency plot.
* `ratio_y_range`: The range of the y-axis of the ratio plot.
* `info`: A short description of the scale factor. This is used for the correctionlib file.
* `header`: A short description of the scale factor. This is used for the correctionlib file.

Quantities, which not requiere leg-switching procedure are stored in `<file>_double_object_quantities.yaml` files and are currently used for e.g. the efficience of the `DZ` filter of `trg_Mu17TrkMu8_DZ_Mu17` trigger.

## 4. Running the fits

Finally, the scale factors are calculated using

```bash
channel="embeddingselection"  # "muon" or "electron"
era="2016postVFPUL"  # "2016preVFPUL", "2017UL", ...

python3 scripts/TagAndProbe.py --channel $channel --era $era
# In case of embeddingselection only: Addition of measured dz quantity of trg_Mu17TrkMu8_DZ_Mu17
if [[ "$channel" == embeddingselection ]]
  then
    python3 scripts/TagAndProbe.py --channel $channel --era $era --no-leg-switching --mode="UPDATE"
  fi
python3 scripts/runTagAndProbeFits.py --channel  $channel --era $era --fit --plot
```
the resulting fits and efficiency plots are all stored in the `output` folder. They should be checked carefully, to and all previous steps should be repeated if necessary.

It is also possible to run multiple eras and channels in parallel, by modifying `channels`, `eras`, `output_dir` in `run_scalefactor_creation.sh` 


## Creating the correctionlib files

In the last step, the scale factors are stored in correctionlib files. This is done using the [translate_to_crosspog_json.py](./scripts/translate_to_crosspog_json.py) script. The script can be run using

```bash
python3 scripts/translate_to_crosspog_json.py -e your_era -c (embeddingselection|muon|electron) -o output
```

Congratulations, you have created the scale factors for the UL Run2 Legacy analysis!

## Retrieving scale factors from the workspace

One can extract scale factors from the ROOT workspace and write it to the correction lib format. The code is based on KIT  [Tag and Probe](https://github.com/KIT-CMS/TagAndProbe) repoditory

Before the execution, one should activate CROWN's tau environment, e.g

```bash
source /work/${USER}/CROWN/init.sh tau
```

Execution:

```bash
python3 create_crosspog_json_workspace.py -e your_era -c muon -o output
```

## Custom NanoAODs for 2016preVFPUL, 2016postVFPUL

Due to the drop in DZ efficiency of the used double muon trigger (`HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ`) that was not accounted for, an additional measurement of this efficiency is required. Unfortunately, the information of this efficiency is not available at NanoAOD level, requiring to create a custom NanoAOD (discussed here) or a FriendTree (to be updated) containing this filter information as a qualitybit.

For the NanoAOD creation, you require `CMSSW_10_6_35` with `PhysicsTools` package (`git cms-addpkg PhysicsTools/NanoAOD`). [grid-control](https://github.com/KIT-CMS/grid-control) is advisable, if the production should be performed non locally.

Modify the 2016 muon trigger table in `CMSSW_10_6_35/src/PhysicsTools/NanoAOD/python/triggerObjects_cff.py` with the following two lines:

```
"4096*filter('hltDiMuonGlb17Glb8RelTrkIsoFiltered0p4') + " \  # -> "bit 12"
"8192*filter('hltDiMuonGlb17Glb8RelTrkIsoFiltered0p4DzFiltered0p2')"  # -> "bit 13"
```

Compile and execute the according run config. Starting from [here](https://pdmv-pages.web.cern.ch/rereco_ul/?input_dataset=DoubleMuon%2FRun2016): MiniAODNanoAOD->ReReco-Run2016 link of your choice ->ReqMgr->ConfigCacheID. Ther you need to modify the execution string according to your needs to


```
RECO --conditions 106X_dataRun2_v35 --customise Configuration/DataProcessing/Utils.addMonitoring --datatier NANOAOD --era Run2_2016,run2_nanoAOD_106Xv2 --eventcontent NANOAOD --filein _placeholder_.root --fileout file:ReReco-Run2016G-DoubleMuon-UL2016_MiniAODv2_NanoAODv9-00002.root --nThreads 2 --no_exec --python_filename ReReco-Run2016G-DoubleMuon-UL2016_MiniAODv2_NanoAODv9-00002_0_cfg.py --scenario pp --step NANO --data -n 10000
```

If grid-control is used the generated `.py` file needs to be extended with

<details>
 <summary>This</summary>

```python
####@FILE_NAMES@, @SKIP_EVENTS@, @MAX_EVENTS@
from IOMC.RandomEngine.RandomServiceHelper import RandomNumberServiceHelper

randSvc = RandomNumberServiceHelper(process.RandomNumberGeneratorService)
randSvc.populate()
print(
    "Generator random seed: %s"
    % process.RandomNumberGeneratorService.generator.initialSeed
)


def customise_for_gc(process):
    import FWCore.ParameterSet.Config as cms
    from IOMC.RandomEngine.RandomServiceHelper import RandomNumberServiceHelper

    try:
        maxevents = int(__MAX_EVENTS__)
        process.maxEvents = cms.untracked.PSet(
            input=cms.untracked.int32(max(-1, maxevents))
        )
    except Exception:
        pass

    # Dataset related setup
    try:
        primaryFiles = [__FILE_NAMES__]
        if not hasattr(process, "source"):
            print("creating input source for grid-control")
            process.source = cms.Source(
                "PoolSource",
                skipEvents=cms.untracked.uint32(__SKIP_EVENTS__),
                fileNames=cms.untracked.vstring(primaryFiles),
            )
        else:
            print("input source already exists, adapting it for grid-control")
            process.source.skipEvents = cms.untracked.uint32(__SKIP_EVENTS__)
            process.source.fileNames = cms.untracked.vstring(primaryFiles)
        try:
            secondaryFiles = [__FILE_NAMES2__]
            process.source.secondaryFileNames = cms.untracked.vstring(secondaryFiles)
        except Exception:
            pass
        try:
            lumirange = [__LUMI_RANGE__]
            if len(lumirange) > 0:
                process.source.lumisToProcess = cms.untracked.VLuminosityBlockRange(
                    lumirange
                )
                process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(-1))
        except Exception:
            pass
    except Exception:
        pass
    if hasattr(process, "RandomNumberGeneratorService"):
        randSvc = RandomNumberServiceHelper(process.RandomNumberGeneratorService)
        randSvc.populate()
        print(
            "Generator random seed: %s"
            % process.RandomNumberGeneratorService.generator.initialSeed
        )

    process.AdaptorConfig = cms.Service(
        "AdaptorConfig",
        enable=cms.untracked.bool(True),
        stats=cms.untracked.bool(True),
    )

    # Generator related setup
    try:
        if hasattr(process, "generator") and process.source.type_() != "PoolSource":
            process.source.firstLuminosityBlock = cms.untracked.uint32(
                1 + __GC_JOB_ID__
            )
            print(
                "Generator random seed: %s"
                % process.RandomNumberGeneratorService.generator.initialSeed
            )
    except Exception:
        pass

    # Print GlobalTag for DBS3 registration - output is taken from edmConfigHash
    try:
        print("globaltag:%s" % process.GlobalTag.globaltag.value())
    except Exception:
        pass
    return process


process = customise_for_gc(process)
```

An possible grid-control config-file might look like this:
```
[global]
task = CMSSW
backend = condor
;;backend = cream
;;cmdargs = -G -c -m 0
workdir create = True

;; ADAPT
workdir = /work/${USER}/GridControlNanoAODProduction/DoubleMuon_Run2016G-UL/workdir

[jobs]
in flight = 1000
wall time = 05:00:00
memory = 3500
max retry = 1

[CMSSW]
dataset refresh = 4:00:00
project area = $CMSSW_BASE/

;; ADAPT
config file = ReReco-Run2016G-DoubleMuon-UL2016_MiniAODv2_NanoAODv9-00002_0_cfg.py
instrumentation = False
dataset splitter = EventBoundarySplitter
events per job   = 100000

;; ADAPT
dataset = DoubleMuon_Run2016G-UL : list:/work/${USER}/GridControlNanoAODProduction/DoubleMuon_Run2016G-UL/filelist-DoubleMuon_Run2016G-UL.txt  # filelist via i.e. dasgoclient



se runtime = True
partition lfn modifier = <xrootd>
depends = glite

parameter factory = ModularParameterFactory

partition lfn modifier dict =
   <xrootd>    => root://cms-xrd-global.cern.ch//
   <xrootd:eu> => root://xrootd-cms.infn.it//
   <xrootd:us> => root://cmsxrootd.fnal.gov//
   <xrootd:desy> => root://dcache-cms-xrootd.desy.de:1094/
   <srm:nrg> => srm://cmssrm-kit.gridka.de:8443/srm/managerv2?SFN=/pnfs/gridka.de/cms/disk-only/
   <dcap:nrg> => dcap://dcnrgdcap.gridka.de:22125//pnfs/gridka.de/dcms/disk-only/
   <xrootd:nrg> => root://cmsxrootd-redirectors.gridka.de/
   <dcap:gridka> => dcap://dccmsdcap.gridka.de:22125//pnfs/gridka.de/cms/disk-only/
   <xrootd:gridka> => root://cmsxrootd.gridka.de//
   <dcap:aachen> => dcap://grid-dcap-extern.physik.rwth-aachen.de/pnfs/physik.rwth-aachen.de/cms/


[storage]

;; ADAPT
se output files = ReReco-Run2016G-DoubleMuon-UL2016_MiniAODv2_NanoAODv9-00002.root

;; ADAPT
se output pattern = ReReco-Run2016G-DoubleMuon-UL2016_MiniAODv2_NanoAODv9-00002/@FOLDER@/@XBASE@_@GC_JOB_ID@.@XEXT@

;; ADAPT
se path = srm://cmssrm-kit.gridka.de:8443/srm/managerv2?SFN=/pnfs/gridka.de/cms/disk-only/store/user/${USER}/gc_storage/PrivateNanoAODProduction/ReReco-Run2016G-DoubleMuon-UL2016_MiniAODv2_NanoAODv9-00002

scratch space used = 7500
[condor]
JDLData = Requirements=(TARGET.ProvidesCPU==True)&&(TARGET.ProvidesIO==True) +REMOTEJOB=True accounting_group=cms.higgs request_disk=8000 universe=docker docker_image=mschnepf/slc7-condocker
proxy = VomsProxy


[constants]
GC_GLITE_LOCATION  = /cvmfs/grid.cern.ch/umd-c7ui-latest/etc/profile.d/setup-c7-ui-example.sh

[parameters]
parameters = transform('FOLDER', 'GC_JOB_ID % 100 + 1')

```

Adjust at least the `;;Adapt` marked lines according to your needs. For details on how to set up and execute grid-control please refer to grid-control documentation and examples

</details>

