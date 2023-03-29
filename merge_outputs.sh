#!/bin/bash

NTUPLETAG=$1
CHANNEL=$2
ERA=$3

case ${CHANNEL} in
    "electron")
        scope=ee
        sample="Electron"
        ;;

    "muon")
        scope=mm
        sample="Muon"
        ;;

    *)
        echo "[ERROR] Given channel ${CHANNEL} not implemented"
        exit 42
esac


basedir=/store/user/${USER}/CROWN/ntuples/${NTUPLETAG}/CROWNRun/${ERA}/
gridpath=root://cmsxrootd-kit.gridka.de:1094/
output_dir=/ceph/${USER}/Run2UltraLegacy/scalefactors/${NTUPLETAG}/${ERA}UL
[[ ! -d ${output_dir} ]] && mkdir -p ${output_dir}

# Write out the merge commands for all sample types
# MC
[[ -f merge_DYJetsToLL_files_${ERA}_${scope}.log ]] && rm merge_DYJetsToLL_files_${ERA}_${scope}.log
for ext in "" _ext1; do 
    xrdfs ${gridpath} ls ${basedir}/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8_RunIISummer20UL${ERA: -2}NanoAODv9-106X${ext}/${scope}/
done >> merge_DYJetsToLL_files_${ERA}_${scope}.log
# Modify the written file by appending the redirector to get the full path
sed -i "s#^#${gridpath}#" merge_DYJetsToLL_files_${ERA}_${scope}.log
case ${ERA} in

    "2017")
        # Data
        echo "[INFO] Gathering data file list..."
        [[ -f merge_Single${sample}_files_${ERA}_${scope}.log ]] && rm merge_Single${sample}_files_${ERA}_${scope}.log
        for period in {B..F}; do
            xrdfs ${gridpath} ls ${basedir}/Single${sample}_Run${ERA}${period}-UL${ERA}/${scope}/
        done >> merge_Single${sample}_files_${ERA}_${scope}.log
        # Modify the written file by appending the redirector to get the full path
        sed -i "s#^#${gridpath}#" merge_Single${sample}_files_${ERA}_${scope}.log

        if [[ ${CHANNEL} == "muon" ]]; then
            [[ -f merge_Double${sample}_files_${ERA}_${scope}.log ]] && rm merge_Double${sample}_files_${ERA}_${scope}.log
            for period in {B..F}; do
                xrdfs ${gridpath} ls ${basedir}/Double${sample}_Run${ERA}${period}-UL${ERA}/${scope}/
            done >> merge_Double${sample}_files_${ERA}_${scope}.log
            # Modify the written file by appending the redirector to get the full path
            sed -i "s#^#${gridpath}#" merge_Double${sample}_files_${ERA}_${scope}.log
        fi

        # Embedding
        echo "[INFO] Gathering embedding file list..."
        [[ -f merge_${sample}Embedding_files_${ERA}_${scope}.log ]] && rm merge_${sample}Embedding_files_${ERA}_${scope}.log
        for period in {B..F}; do
            xrdfs ${gridpath} ls ${basedir}/${sample}Embedding_Run${ERA}${period}-UL${ERA}/${scope}/
        done >> merge_${sample}Embedding_files_${ERA}_${scope}.log
        # Modify the written file by appending the redirector to get the full path
        sed -i "s#^#${gridpath}#" merge_${sample}Embedding_files_${ERA}_${scope}.log
        ;;

    *)
        echo "[ERROR] Not implemented yet..."
        exit 42
        ;;
esac

hadd ${output_dir}/DYJetsToLL_${ERA}UL_${scope}.root $(cat merge_DYJetsToLL_files_${ERA}_${scope}.log | tr '\n' ' ') &
hadd ${output_dir}/Single${sample}_${ERA}UL.root $(cat merge_Single${sample}_files_${ERA}_${scope}.log | tr '\n' ' ') &
if [[ ${CHANNEL} == "muon" ]]; then
    hadd ${output_dir}/Double${sample}_${ERA}UL.root $(cat merge_Double${sample}_files_${ERA}_${scope}.log | tr '\n' ' ') &
fi
hadd ${output_dir}/${sample}Embedding_${ERA}UL.root $(cat merge_${sample}Embedding_files_${ERA}_${scope}.log | tr '\n' ' ') &
wait
