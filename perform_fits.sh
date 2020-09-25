#!/bin/bash

ERA=$1
SUFFIX=$2
MVA=$3

MVA_ARG=""
if [ $MVA == 1 ]
then
    MVA_ARG="--mva"
fi

pushd /portal/ekpbms3/home/mburkart/workdir/trigger_studies/taupog/CMSSW_10_2_18/src/TauTriggerTools/TauTriggerFitTool/

source /cvmfs/cms.cern.ch/cmsset_default.sh
eval `scramv1 runtime -sh`

echo "[INFO] Performing fits of the 1D distributions.."
python python/produceFitResults.py -i /portal/ekpbms3/home/mburkart/workdir/trigger_studies/CMSSW_8_0_26_patch1/src/UserCode/TagAndProbe/output_${ERA}_tau_leg${SUFFIX}.root -o data/tauTriggerFitResults${ERA}KIT${SUFFIX}.root -t etau mutau ditau -d DATA MC EMB $MVA_ARG -w vvvloose vvloose vloose loose medium tight vtight vvtight

popd
