#!/bin/bash

ERA=$1
SUFFIX=$2
MVA=$3

MVA_ARG=""
if [ $MVA == 1 ]; then
    MVA_ARG="--mva"
fi

echo "[INFO] Change to directory of scale factor tool.."
pushd /portal/ekpbms3/home/mburkart/workdir/trigger_studies/taupog/CMSSW_10_2_18/src/TauAnalysisTools/TauTriggerSFs/

# Clean up older plots
ls plots
rm plots/*.{png,pdf}

source /cvmfs/cms.cern.ch/cmsset_default.sh
eval `scramv1 runtime -sh`

echo "[INFO] Switching naming scheme of efficiencies.."
python python/copyEfficiencies.py \
    /portal/ekpbms3/home/mburkart/workdir/trigger_studies/taupog/CMSSW_10_2_18/src/TauTriggerTools/TauTriggerFitTool/data/tauTriggerFitResults${ERA}KIT${SUFFIX}.root \
    data/tauTriggerEfficiencies${ERA}KIT_copied${SUFFIX}.root\
    -s MC DATA EMB \
    $MVA_ARG

hadd -f data/tauTriggerEfficiencies${ERA}KIT${SUFFIX}.root data/tauTriggerEfficiencies${ERA}KIT_copied${SUFFIX}.root /portal/ekpbms3/home/mburkart/workdir/trigger_studies/CMSSW_8_0_26_patch1/src/UserCode/TagAndProbe/etaphimapKIT_${ERA}${SUFFIX}.root

# Plotting resulting efficiencies in comparison to the old ones and upload them to the plots archive
# echo "[INFO] Plotting efficiency comparison.."
# python plot_differences.py -i data/tauTriggerEfficiencies${ERA}.root data/tauTriggerEfficiencies${ERA}KIT${SUFFIX}.root $MVA_ARG

# echo "[INFO] Uploading comparison plots to webspace.."
# TODAY=$(date +'%Y_%m_%d')
# if [ ! -d /etpwww/web/mburkart/public_html/plots_archive/$TODAY/sf_comp/$ERA ]; then
#     mkdir -p /etpwww/web/mburkart/public_html/plots_archive/$TODAY/sf_comp/$ERA
# fi
# cp plots/* /etpwww/web/mburkart/public_html/plots_archive/$TODAY/sf_comp/$ERA
# gallery.py /etpwww/web/mburkart/public_html/plots_archive/$TODAY/

popd
