#!/bin/bash
ERA=$1
SUFFIX=$2
INPUT=$3
MVA=$4

MVA_ARG=""
if [ $MVA == 1 ]
then
    MVA_ARG="--mva"
fi

if [[ "$hostname" =~ "bms2" ]]
then
    source /cvmfs/sft.cern.ch/lcg/views/LCG_94/x86_64-slc6-gcc7-opt/setup.sh
elif [[ "$hostname" =~ "bms1" ]] || [[ "$hostname" =~ "bms3" ]]
then 
    source /cvmfs/sft.cern.ch/lcg/views/LCG_94/x86_64-centos7-gcc7-opt/setup.sh
else
    echo "[FATAL] Host currently not known. Aborting..."
    exit 1
fi

echo "[INFO] Producing efficiencies for ${ERA}.."
if [[ $ERA =~ "2016" ]]; then
    python scripts/TauTriggerEfficiency.py -w vloose loose medium tight vtight vvtight -i $INPUT -e $ERA -o output_${ERA}_tau_leg${SUFFIX}.root -f DATA MC -t mutau etau ditau --per-dm --fit -n 20 $MVA_ARG
else
    python scripts/TauTriggerEfficiency.py -w vloose loose medium tight vtight vvtight -i $INPUT -e $ERA -o output_${ERA}_tau_leg${SUFFIX}.root -f DATA MC -t mutau etau ditau --per-dm --fit -n 20 $MVA_ARG #--use-et
fi


echo "[INFO] Creating 2D efficiency maps for era ${ERA}.."
./scripts/translate_2d_hists.py -i output_${ERA}_tau_leg${SUFFIX}.root -o etaphimapKIT_${ERA}${SUFFIX}.root -e $ERA
