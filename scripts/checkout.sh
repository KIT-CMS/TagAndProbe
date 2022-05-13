export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh
cmsrel CMSSW_12_3_2
cd CMSSW_12_3_2/src
cmsenv

mkdir UserCode 
cd UserCode

git clone --recursive https://github.com/KIT-CMS/TagAndProbe -b crown

cd -

scramv1 b

