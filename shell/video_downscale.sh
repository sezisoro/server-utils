#!/bin/bash

input=''			# Single file in; if recursive, expects directory
output=''			# Single file out; if recursive, expects directory
recursive='true'	# Recursively convert
scale=720			#
verbose='false'

SUPPORTED_FILETYPES=('mkv' 'mp4' 'mov' 'avi' 'hevc' 'webm')
QUEUE=()

print_usage() {
	printf "Usage: ..."
}

# Scans directory looking for files ending in one of SUPPORTED_FILETYPES above
# using find.
#
# @arg path of directory to be scanned
# @returns 0 if QUEUE is set and 1 otherwise
find_video_files_1() {
	QUEUE=()
	for ext in ${SUPPORTED_FILETYPES[@]}; do
		${verbose} && echo "Gathering $ext targets from $1"
		QUEUE+="$(find "$1" -type f -iname "*.$ext")"
	done
}

# Scans directory looking for files ending in one of SUPPORTED_FILETYPES above
# using globbing.
#
# @arg path of directory to be scanned
# @returns 0 if QUEUE is set and 1 otherwise
find_video_files_2() {
	for ext in ${SUPPORTED_FILETYPES[@]}; do
		QUEUE+=($1/**/*.$ext)
	done
}

while getopts 'i:o:s:rv' flag; do
	case "${flag}" in
		i) input="${OPTARG}" ;;
		o) output="${OPTARG}" ;;
		s) scale="${OPTARG}" ;;
		r) recursive="${OPTARG}" ;;
		v) verbose="${OPTARG}" ;;
		*) print_usage
			exit 1 ;;
	esac
done

if [[ -z "$output" ]]; then
	echo "Error no destination specified"
	exit 1
elif [[ -z "$input" ]]; then
	echo "Error no input specified"
	exit 1
fi

full_input="$(realpath "$input")"
full_output="$(realpath "$output")"

if ${recursive}; then
	if [[ ! -d "$output" ]]; then
		echo "Error output isn't a directory"
		exit 1
	elif [[ ! -d "$input" ]]; then
		echo "Error input isn't a directory"
		exit 1
	fi

	find_video_files_1 "$full_input"
else
	if [[ -e "$output" ]]; then
		echo "Error output already exists"
		exit 1
	elif [[ ! -e "$input" ]]; then
		echo "Error input not found"
		exit 1
	fi

	QUEUE=("$input")
fi

${verbose} && echo "Converting the following files:" && printf '%s\n' "${QUEUE[@]}"

for from in ${QUEUE[@]}; do
	echo "Target: $from"
	filename="${from#$full_input}"
	filepath="${filename%/*}"
	echo "FN: $filename FP: $filepath"
	to="$full_output/$filepath/$filename"
	#${verbose} && echo "Converting $from to $to"
	#ffmpeg -i $in -vf scale=-1:720 -c:v libx265 -crf 18 -preset slower -c:a copy -scodec copy $out
done
