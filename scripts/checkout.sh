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

