#!/bin/bash

NTUPLETAG=$1
CHANNEL=$2
ERA=$3
if [[ -z "$4" ]]; then
    STEP="all"
else
    STEP=$4  # filelist, hadd, all
fi

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
    ;;
esac

basedir=/store/user/${USER}/CROWN/ntuples/${NTUPLETAG}/CROWNRun/${ERA}/
gridpath=root://cmsxrootd-kit-disk.gridka.de:1094/
output_dir=/ceph/${USER}/HiggsToTauTau/scalefactors/${NTUPLETAG}/${ERA}UL
[[ ! -d ${output_dir} ]] && mkdir -p ${output_dir}

if [[ ${STEP} == "all" || ${STEP} == "filelist" ]]; then
    # Write out the merge commands for all sample types
    if [[ ${ERA} == "2018" ]]; then
        # MC
        [[ -f merge_DYJetsToLL_files_${ERA}_${scope}.log ]] && rm merge_DYJetsToLL_files_${ERA}_${scope}.log
        for ext in "" _ext1; do
            xrdfs ${gridpath} ls ${basedir}/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8_RunIISummer20UL${ERA: -2}NanoAODv9-106X${ext}/${scope}/
        done >>merge_DYJetsToLL_files_${ERA}_${scope}.log
        # Modify the written file by appending the redirector to get the full path
        sed -i "s#^#${gridpath}#" merge_DYJetsToLL_files_${ERA}_${scope}.log
        # remove lines containing .json files
        sed -i '/\.json/d' merge_DYJetsToLL_files_${ERA}_${scope}.log
        # Data
        echo "[INFO] Gathering data file list..."
        [[ -f merge_Single${sample}_files_${ERA}_${scope}.log ]] && rm merge_Single${sample}_files_${ERA}_${scope}.log
        for period in {A..D}; do
            xrdfs ${gridpath} ls ${basedir}/Single${sample}_Run${ERA}${period}-UL${ERA}/${scope}/
        done >>merge_Single${sample}_files_${ERA}_${scope}.log
        # Modify the written file by appending the redirector to get the full path
        sed -i "s#^#${gridpath}#" merge_Single${sample}_files_${ERA}_${scope}.log
        # remove lines containing .json files
        sed -i '/\.json/d' merge_Single${sample}_files_${ERA}_${scope}.log

        if [[ ${CHANNEL} == "muon" ]]; then
            [[ -f merge_Double${sample}_files_${ERA}_${scope}.log ]] && rm merge_Double${sample}_files_${ERA}_${scope}.log
            for period in {A..D}; do
                xrdfs ${gridpath} ls ${basedir}/Double${sample}_Run${ERA}${period}-UL${ERA}/${scope}/
            done >>merge_Double${sample}_files_${ERA}_${scope}.log
            # Modify the written file by appending the redirector to get the full path
            sed -i "s#^#${gridpath}#" merge_Double${sample}_files_${ERA}_${scope}.log
            # remove lines containing .json files
            sed -i '/\.json/d' merge_Double${sample}_files_${ERA}_${scope}.log
        fi
        # Embedding
        echo "[INFO] Gathering embedding file list..."
        [[ -f merge_${sample}Embedding_files_${ERA}_${scope}.log ]] && rm merge_${sample}Embedding_files_${ERA}_${scope}.log
        for period in {A..D}; do
            xrdfs ${gridpath} ls ${basedir}/${sample}Embedding_Run${ERA}${period}-UL${ERA}/${scope}/
        done >>merge_${sample}Embedding_files_${ERA}_${scope}.log
        # Modify the written file by appending the redirector to get the full path
        sed -i "s#^#${gridpath}#" merge_${sample}Embedding_files_${ERA}_${scope}.log
        # remove lines containing .json files
        sed -i '/\.json/d' merge_${sample}Embedding_files_${ERA}_${scope}.log


    elif [[ ${ERA} == "2017" ]]; then
        # MC
        [[ -f merge_DYJetsToLL_files_${ERA}_${scope}.log ]] && rm merge_DYJetsToLL_files_${ERA}_${scope}.log
        for ext in "" _ext1; do
            xrdfs ${gridpath} ls ${basedir}/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8_RunIISummer20UL${ERA: -2}NanoAODv9-106X${ext}/${scope}/
        done >>merge_DYJetsToLL_files_${ERA}_${scope}.log
        # Modify the written file by appending the redirector to get the full path
        sed -i "s#^#${gridpath}#" merge_DYJetsToLL_files_${ERA}_${scope}.log
        # remove lines containing .json files
        sed -i '/\.json/d' merge_DYJetsToLL_files_${ERA}_${scope}.log
        # Data
        echo "[INFO] Gathering data file list..."
        [[ -f merge_Single${sample}_files_${ERA}_${scope}.log ]] && rm merge_Single${sample}_files_${ERA}_${scope}.log
        for period in {B..F}; do
            xrdfs ${gridpath} ls ${basedir}/Single${sample}_Run${ERA}${period}-UL${ERA}/${scope}/
        done >>merge_Single${sample}_files_${ERA}_${scope}.log
        # Modify the written file by appending the redirector to get the full path
        sed -i "s#^#${gridpath}#" merge_Single${sample}_files_${ERA}_${scope}.log
        # remove lines containing .json files
        sed -i '/\.json/d' merge_Single${sample}_files_${ERA}_${scope}.log

        if [[ ${CHANNEL} == "muon" ]]; then
            [[ -f merge_Double${sample}_files_${ERA}_${scope}.log ]] && rm merge_Double${sample}_files_${ERA}_${scope}.log
            for period in {B..F}; do
                xrdfs ${gridpath} ls ${basedir}/Double${sample}_Run${ERA}${period}-UL_DZ/${scope}/
            done >>merge_Double${sample}_files_${ERA}_${scope}.log
            # Modify the written file by appending the redirector to get the full path
            sed -i "s#^#${gridpath}#" merge_Double${sample}_files_${ERA}_${scope}.log
            # remove lines containing .json files
            sed -i '/\.json/d' merge_Double${sample}_files_${ERA}_${scope}.log
            # ---
            [[ -f merge_Double${sample}_files_${ERA}_${scope}_wo_DZ.log ]] && rm merge_Double${sample}_files_${ERA}_${scope}_wo_DZ.log
            for period in {B..F}; do
                xrdfs ${gridpath} ls ${basedir}/Double${sample}_Run${ERA}${period}-UL${ERA}/${scope}/
            done >>merge_Double${sample}_files_${ERA}_${scope}_wo_DZ.log
            # Modify the written file by appending the redirector to get the full path
            sed -i "s#^#${gridpath}#" merge_Double${sample}_files_${ERA}_${scope}_wo_DZ.log
            # remove lines containing .json files
            sed -i '/\.json/d' merge_Double${sample}_files_${ERA}_${scope}_wo_DZ.log
        fi
        # Embedding
        echo "[INFO] Gathering embedding file list..."
        [[ -f merge_${sample}Embedding_files_${ERA}_${scope}.log ]] && rm merge_${sample}Embedding_files_${ERA}_${scope}.log
        for period in {B..F}; do
            xrdfs ${gridpath} ls ${basedir}/${sample}Embedding_Run${ERA}${period}-UL${ERA}/${scope}/
        done >>merge_${sample}Embedding_files_${ERA}_${scope}.log
        # Modify the written file by appending the redirector to get the full path
        sed -i "s#^#${gridpath}#" merge_${sample}Embedding_files_${ERA}_${scope}.log
        # remove lines containing .json files
        sed -i '/\.json/d' merge_${sample}Embedding_files_${ERA}_${scope}.log


    elif [[ ${ERA} == "2016postVFP" ]]; then
        echo "[INFO] Gathering file list for ${ERA}..."
        ERA_SAMPLENAME="2016"
        # MC
        [[ -f merge_DYJetsToLL_files_${ERA}_${scope}.log ]] && rm merge_DYJetsToLL_files_${ERA}_${scope}.log
        for ext in "" _ext1; do
            xrdfs ${gridpath} ls ${basedir}/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8_RunIISummer20UL${ERA_SAMPLENAME: -2}NanoAODv9-106X${ext}/${scope}/
        done >>merge_DYJetsToLL_files_${ERA}_${scope}.log
        # Modify the written file by appending the redirector to get the full path
        sed -i "s#^#${gridpath}#" merge_DYJetsToLL_files_${ERA}_${scope}.log
        # remove lines containing .json files
        sed -i '/\.json/d' merge_DYJetsToLL_files_${ERA}_${scope}.log
        # Data
        echo "[INFO] Gathering data file list..."
        [[ -f merge_Single${sample}_files_${ERA}_${scope}.log ]] && rm merge_Single${sample}_files_${ERA}_${scope}.log
        for period in {F..H}; do
            xrdfs ${gridpath} ls ${basedir}/Single${sample}_Run${ERA_SAMPLENAME}${period}-UL${ERA_SAMPLENAME}/${scope}/
        done >>merge_Single${sample}_files_${ERA}_${scope}.log
        # Modify the written file by appending the redirector to get the full path
        sed -i "s#^#${gridpath}#" merge_Single${sample}_files_${ERA}_${scope}.log
        # remove lines containing .json files
        sed -i '/\.json/d' merge_Single${sample}_files_${ERA}_${scope}.log

        if [[ ${CHANNEL} == "muon" ]]; then
            [[ -f merge_Double${sample}_files_${ERA}_${scope}.log ]] && rm merge_Double${sample}_files_${ERA}_${scope}.log
            for period in {F..H}; do
                xrdfs ${gridpath} ls ${basedir}/Double${sample}_Run${ERA_SAMPLENAME}${period}-UL_DZ/${scope}/
            done >>merge_Double${sample}_files_${ERA}_${scope}.log
            # Modify the written file by appending the redirector to get the full path
            sed -i "s#^#${gridpath}#" merge_Double${sample}_files_${ERA}_${scope}.log
            # remove lines containing .json files
            sed -i '/\.json/d' merge_Double${sample}_files_${ERA}_${scope}.log
            # ---
             [[ -f merge_Double${sample}_files_${ERA}_${scope}_wo_DZ.log ]] && rm merge_Double${sample}_files_${ERA}_${scope}_wo_DZ.log
            for period in {F..H}; do
                xrdfs ${gridpath} ls ${basedir}/Double${sample}_Run${ERA_SAMPLENAME}${period}-UL${ERA_SAMPLENAME}/${scope}/
            done >>merge_Double${sample}_files_${ERA}_${scope}_wo_DZ.log
            # Modify the written file by appending the redirector to get the full path
            sed -i "s#^#${gridpath}#" merge_Double${sample}_files_${ERA}_${scope}_wo_DZ.log
            # remove lines containing .json files
            sed -i '/\.json/d' merge_Double${sample}_files_${ERA}_${scope}_wo_DZ.log
        fi
        # Embedding
        echo "[INFO] Gathering embedding file list..."
        [[ -f merge_${sample}Embedding_files_${ERA}_${scope}.log ]] && rm merge_${sample}Embedding_files_${ERA}_${scope}.log
        for period in {F..H}; do
            xrdfs ${gridpath} ls ${basedir}/${sample}Embedding_Run${ERA_SAMPLENAME}${period}-UL${ERA_SAMPLENAME}/${scope}/
        done >>merge_${sample}Embedding_files_${ERA}_${scope}.log
        # Modify the written file by appending the redirector to get the full path
        sed -i "s#^#${gridpath}#" merge_${sample}Embedding_files_${ERA}_${scope}.log
        # remove lines containing .json files
        sed -i '/\.json/d' merge_${sample}Embedding_files_${ERA}_${scope}.log


    elif [[ ${ERA} == "2016preVFP" ]]; then
        echo "[INFO] Gathering file list for ${ERA}..."
        ERA_SAMPLENAME="2016"
        declare -a data_period=("B-ver1" "B-ver2" "C-HIPM" "D-HIPM" "E-HIPM" "F-HIPM")
        declare -a emb_period=("B_ver1" "B_ver2" "C" "D" "E" "F")
        # MC
        [[ -f merge_DYJetsToLL_files_${ERA}_${scope}.log ]] && rm merge_DYJetsToLL_files_${ERA}_${scope}.log

        xrdfs ${gridpath} ls ${basedir}/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8_RunIISummer20UL16NanoAODAPVv9-106X/${scope}/ >> merge_DYJetsToLL_files_${ERA}_${scope}.log
        # Modify the written file by appending the redirector to get the full path
        sed -i "s#^#${gridpath}#" merge_DYJetsToLL_files_${ERA}_${scope}.log
        # remove lines containing .json files
        sed -i '/\.json/d' merge_DYJetsToLL_files_${ERA}_${scope}.log
        # Data
        echo "[INFO] Gathering data file list..."
        [[ -f merge_Single${sample}_files_${ERA}_${scope}.log ]] && rm merge_Single${sample}_files_${ERA}_${scope}.log
        for period in ${data_period[@]}; do
            xrdfs ${gridpath} ls ${basedir}/Single${sample}_Run${ERA_SAMPLENAME}${period}/${scope}/
        done >>merge_Single${sample}_files_${ERA}_${scope}.log
        # Modify the written file by appending the redirector to get the full path
        sed -i "s#^#${gridpath}#" merge_Single${sample}_files_${ERA}_${scope}.log
        # remove lines containing .json files
        sed -i '/\.json/d' merge_Single${sample}_files_${ERA}_${scope}.log

        if [[ ${CHANNEL} == "muon" ]]; then
            [[ -f merge_Double${sample}_files_${ERA}_${scope}.log ]] && rm merge_Double${sample}_files_${ERA}_${scope}.log
            declare -a data_period_with_dz=("B-ver1-HIPM-UL_DZ" "B-ver2-HIMP-UL_DZ" "C-HIMP-UL_DZ" "D-HIMP-UL_DZ" "E-HIMP-UL_DZ" "F-HIMP-UL_DZ")
            for period in ${data_period_with_dz[@]}; do
                xrdfs ${gridpath} ls ${basedir}/Double${sample}_Run${ERA_SAMPLENAME}${period}/${scope}/
            done >>merge_Double${sample}_files_${ERA}_${scope}.log
            # Modify the written file by appending the redirector to get the full path
            sed -i "s#^#${gridpath}#" merge_Double${sample}_files_${ERA}_${scope}.log
            # remove lines containing .json files
            sed -i '/\.json/d' merge_Double${sample}_files_${ERA}_${scope}.log
            # ---
            [[ -f merge_Double${sample}_files_${ERA}_${scope}_wo_DZ.log ]] && rm merge_Double${sample}_files_${ERA}_${scope}_wo_DZ.log
            for period in ${data_period[@]}; do
                xrdfs ${gridpath} ls ${basedir}/Double${sample}_Run${ERA_SAMPLENAME}${period}/${scope}/
            done >>merge_Double${sample}_files_${ERA}_${scope}_wo_DZ.log
            # Modify the written file by appending the redirector to get the full path
            sed -i "s#^#${gridpath}#" merge_Double${sample}_files_${ERA}_${scope}_wo_DZ.log
            # remove lines containing .json files
            sed -i '/\.json/d' merge_Double${sample}_files_${ERA}_${scope}_wo_DZ.log
        fi
        # Embedding
        echo "[INFO] Gathering embedding file list..."
        [[ -f merge_${sample}Embedding_files_${ERA}_${scope}.log ]] && rm merge_${sample}Embedding_files_${ERA}_${scope}.log
        for period in ${emb_period[@]}; do
            xrdfs ${gridpath} ls ${basedir}/${sample}Embedding_Run${ERA_SAMPLENAME}-HIPM_${period}-UL${ERA_SAMPLENAME}/${scope}/
        done >>merge_${sample}Embedding_files_${ERA}_${scope}.log
        # Modify the written file by appending the redirector to get the full path
        sed -i "s#^#${gridpath}#" merge_${sample}Embedding_files_${ERA}_${scope}.log
        # remove lines containing .json files
        sed -i '/\.json/d' merge_${sample}Embedding_files_${ERA}_${scope}.log
    else

        echo "[ERROR] Era ${ERA} Not implemented yet..."
        exit 42
    fi
fi

if [[ ${STEP} == "all" || ${STEP} == "hadd" ]]; then
    hadd -f ${output_dir}/DYJetsToLL_${ERA}UL_${scope}.root $(cat merge_DYJetsToLL_files_${ERA}_${scope}.log | tr '\n' ' ') &
    hadd -f ${output_dir}/Single${sample}_${ERA}UL.root $(cat merge_Single${sample}_files_${ERA}_${scope}.log | tr '\n' ' ') &
    if [[ ${CHANNEL} == "muon" ]]; then
        hadd -f ${output_dir}/Double${sample}_${ERA}UL.root $(cat merge_Double${sample}_files_${ERA}_${scope}.log | tr '\n' ' ') &
        hadd -f ${output_dir}/Double${sample}_${ERA}UL_wo_DZ.root $(cat merge_Double${sample}_files_${ERA}_${scope}_wo_DZ.log | tr '\n' ' ') &
    fi
    hadd -f ${output_dir}/${sample}Embedding_${ERA}UL.root $(cat merge_${sample}Embedding_files_${ERA}_${scope}.log | tr '\n' ' ') &
    wait
fi
