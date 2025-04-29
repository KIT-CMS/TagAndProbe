eras=("2018UL")
channels=("electron")

output_dir="output"

mkdir -p $output_dir
cp -r settings $output_dir/used_settings         # Copy settings that are used to output directory
cp set_inputfiles.yaml $output_dir/used_settings # Copy input file list to output directory

# ---

for era_idx in $(seq 0 $((${#eras[@]} - 1))); do
	(
		era=${eras[$era_idx]}
		for channel_idx in $(seq 0 $((${#channels[@]} - 1))); do
			(
				channel=${channels[$channel_idx]}
				nice -n 19 python3 scripts/TagAndProbe.py \
					--channel $channel \
					--era $era \
					--settings-folder $output_dir/used_settings \
					--output $output_dir
				if [[ "$channel" == "embeddingselection" ]]; then # Additional dz quantity of trg_Mu17TrkMu8_DZ_Mu17
					nice -n 19 python3 scripts/TagAndProbe.py \
						--channel $channel \
						--era $era \
						--no-leg-switching \
						--mode="UPDATE" \
						--settings-folder $output_dir/used_settings \
						--output $output_dir
				fi
				nice -n 19 python3 scripts/runTagAndProbeFits.py \
					--channel $channel \
					--era $era \
					--fit \
					--plot \
					--settings-folder $output_dir/used_settings \
					--output $output_dir
				nice -n 19 python3 scripts/translate_to_crosspog_json.py \
					--era $era \
					--channel $channel \
					--output $output_dir \
					--settings-folder $output_dir/used_settings
			) &
			pids[${channel_idx}]=$!
		done
		trap "echo kill ${pids[*]}; exit 1" SIGINT
		for pid in ${pids[*]}; do
			wait $pid
		done
		python3 merge_jsons.py \
			--json-a $output_dir/jsons/muon_${era}.json \
			--json-b $output_dir/jsons/embeddingselection_${era}.json \
			--json-output muon_${era}.json \
			--output $output_dir/jsons/merged
	) &
	pids_eras[${era_idx}]=$!
done
trap "echo kill ${pids_eras[*]}; exit 1" SIGINT
for pid_era in ${pids_eras[*]}; do
	wait $pid_era
done
wait

mv $output_dir $output_dir.done

echo "All done"
