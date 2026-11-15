#!/bin/bash

input=()			# list of files in
output=''			# single file out
method='demux'		# concat or demux
verbose='false'

print_usage() {
	printf "Usage: ..."
}

while getopts 'i:o:m:v' flag; do
	case "${flag}" in
		i) input+=("${OPTARG}") ;;
		o) output="${OPTARG}" ;;
		m) method="${OPTARG}" ;;
		v) verbose='true' ;;
		*) print_usage
			exit 1 ;;
	esac
done

if [[ -e "$output" ]]; then
	echo "Error $output already exists"
	return 1
elif [[ -z "$output" ]]; then
	echo "Error no destination specified"
	return 1
elif [[ -z "$input" ]]; then
	echo "Error nothing to concat"
	return 1
fi

input_abs=()
for file in "${input[@]}"; do
	input_abs+=("$(realpath "$file")")
done

if [[ "$method" == "concat" ]]; then
	printf -v joined '%s|' "${input[@]}"
	#ffmpeg -f data -i "concat:${joined%|}" -map 0 -c copy -f data "$output"
	ffmpeg -i "concat:${joined%|}" -c copy "$output"
elif [[ "$method" == "demux" ]]; then
	#printf "file '%s'\n" "${input_abs[@]}"
	ffmpeg -f concat -safe 0 -i <(printf "file '%s'\n" "${input_abs[@]}") -c copy "$output"
fi
