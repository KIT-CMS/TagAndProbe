# TagAndProbe
Muon and electron tag and probe measurements and plotting

*Setting up the code*
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

*Running tag and probe*

1. Create the input files using KIT-Higgs (https://github.com/KIT-CMS/KITHiggsToTauTau):
`HiggsToTauTauAnalysis.py -a tagandprobe -i path_to_skimmed_filelist.txt`

2. Set the path to the inputfiles in `set_inputfiles.yaml`

3. Create the pass and fail histograms using
`python scripts/TagAndProbe.py --channel (muon|electron) --era (2016|2017|2018)`


