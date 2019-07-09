# TagAndProbe
Muon and electron tag and probe measurements and plotting

**Setting up the code**
```bash
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh
cmsrel CMSSW_8_0_26_patch1
cd CMSSW_8_0_26_patch1/src
cmsenv

mkdir UserCode 
cd UserCode
git clone https://github.com/KIT-CMS/TagAndProbe

cd -
scramv1 b 

cd UserCode/TagAndProbe
```
**First step**

Create the input files using KIT-Higgs (https://github.com/KIT-CMS/KITHiggsToTauTau):

`HiggsToTauTauAnalysis.py -a tagandprobe -i path_to_skimmed_filelist.txt`


**Running tag and probe for electrons and muon**


1. Set the path to the inputfiles in 

`set_inputfiles.yaml`

2. Create the pass and fail histograms using

`python scripts/TagAndProbe.py --channel (muon|electron|crossmuon|crosselectron) --era (2016|2017|2018)`

3. Run the fits and plot the results

`python scripts/runTagAndProbeFits.py --channel (muon|electron|crossmuon|crosselectron) --fit --plot --era (2016|2017|2018)`



**Running tag and probe for hadronic taus**


1. Get a clean shell environment (no CMSSW can be sourced yet) and do
 * for CentOS7 machines:
`source /cvmfs/sft.cern.ch/lcg/views/LCG_94/x86_64-centos7-gcc7-opt/setup.sh`
 * for SLC6 machines: 
`source /cvmfs/sft.cern.ch/lcg/views/LCG_94/x86_64-slc6-gcc7-opt/setup.sh`

2. Run the fits and plot the results

`python scripts/TauTriggerEfficiency.py  -i /path/to/artus_outputs/ --fit --plot`


