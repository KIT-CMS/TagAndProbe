eras=("2016preVFPUL" "2016postVFPUL")
channels=("muon" "embeddingselection")

output_dir=output

mkdir -p $output_dir
cp -r settings $output_dir/used_settings # Copy settings that are used to output directory

for era_idx in $(seq 0 $((${#eras[@]} - 1))); do
	(
		era=${eras[$era_idx]}
		for channel_idx in $(seq 0 $((${#channels[@]} - 1))); do
			(
				channel=${channels[$channel_idx]}
				python3 scripts/TagAndProbe.py --channel $channel --era $era
				if [[ "$channel" == "embeddingselection" ]] && ([[ "$era" == "2016preVFPUL" ]] || [[ "$era" == "2016postVFPUL" ]]); then # Additional dz quantity of trg_Mu17TrkMu8_DZ_Mu17
					python3 scripts/TagAndProbe.py --channel $channel --era $era --no-leg-switching --mode="UPDATE"
				fi
				python3 scripts/runTagAndProbeFits.py --channel $channel --era $era --fit --plot
				python3 scripts/translate_to_crosspog_json.py -e $era -c $channel -o $output_dir
			) &
			pids[${channel_idx}]=$!
		done
		trap "echo kill ${pids[*]}; exit 1" SIGINT
		for pid in ${pids[*]}; do
			wait $pid
		done
		python3 merge_jsons.py \
			-ja $output_dir/jsons/muon_${era}.json \
			-jb $output_dir/jsons/embeddingselection_${era}.json \
			-jo muon_${era}.json
	) &
	pids_eras[${era_idx}]=$!
done
trap "echo kill ${pids_eras[*]}; exit 1" SIGINT
for pid_era in ${pids_eras[*]}; do
	wait $pid_era
done
wait
