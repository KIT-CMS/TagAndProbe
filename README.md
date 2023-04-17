# TagAndProbe
Muon and electron tag and probe measurements and plotting

**Setting up the code**

Either use the checkout script provided under `scripts/checkout.sh` or do the following:
```bash
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh
cmsrel CMSSW_12_3_2
cd CMSSW_12_3_2/src
cmsenv

git clone --recursive git@github.com:KIT-CMS/TagAndProbe.git UserCode/TagAndProbe

scramv1 b
```

**First step**

Create the input files using KIT-Higgs (https://github.com/KIT-CMS/KITHiggsToTauTau):

`HiggsToTauTauAnalysis.py -a tagandprobe -i path_to_skimmed_filelist.txt`


## Running tag and probe for electrons and muon


1. Set the path to the inputfiles in 

`set_inputfiles.yaml`

2. Create the pass and fail histograms using

`python scripts/TagAndProbe.py --channel (muon|electron|crossmuon|crosselectron) --era (2016|2017|2018)`

3. Run the fits and plot the results

`python scripts/runTagAndProbeFits.py --channel (muon|electron|crossmuon|crosselectron) --fit --plot --era (2016|2017|2018)`



## Running tag and probe for hadronic taus (Outdated - use GP fit from Tau POG now)


1. Get a clean shell environment (no CMSSW can be sourced yet) and do
 * for CentOS7 machines:
`source /cvmfs/sft.cern.ch/lcg/views/LCG_94/x86_64-centos7-gcc7-opt/setup.sh`
 * for SLC6 machines: 
`source /cvmfs/sft.cern.ch/lcg/views/LCG_94/x86_64-slc6-gcc7-opt/setup.sh`

2. Run the fits and plot the results

`python scripts/TauTriggerEfficiency.py  -i /ceph/jbechtel/artus_outputs/TagAndProbe/TauTrigger/new/ --fit --plot --era (2016|2017|2018) --per-dm --use-et`


**Obtaining final results for trigger efficiencies for hadronic taus**

1. Extract the 2D histograms from the created output file and create binned distributions from them.

`python scripts/translate_2d_hists.py -i output_(2016|2017|2018)_tau_leg.root -o etaphi_out.root -e (2016|2017|2018)`

2. Get the tau pog codes to run the fits and read out the efficiencies.
```bash
cd $CMSSW_BASE/src
git clone git@github.com:cms-tau-pog/TauTriggerTools.git
git clone -b run2_SFs https://github.com/cms-tau-pog/TauTriggerSFs $CMSSW_BASE/src/TauAnalysisTools/TauTriggerSFs
scram b -j 8
```

3. Perform the fits of the 1D efficiency histograms. They are performed using the script `TauTriggerTools/TauTriggerFitTool/python/produceFitResults.py`. In order to do so the created output file has to be put under `TauTriggerTools/TauTriggerFitTool/data` and the corresponding script has to be adapted to the new file.

4. Copy the resulting file to `$CMSSW_BASE/src/TauAnalysisTools/TauTriggerSFs/data` and run
```bash
cd $CMSSW_BASE/src/TauAnalysisTools/TauTriggerSFs/
python copyEfficiencies.py
```
Here again the script has to be adapted to the correct paths.

5. Add the fit results and the previously created file containing the 2D distributions to a common root file.
