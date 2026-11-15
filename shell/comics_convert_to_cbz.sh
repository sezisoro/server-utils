#!/bin/bash
#
# conv-to-cbz.sh - Convert CBR comics to CBZ
#
# Author:	sez
# Version:	1.0.0 (2026-09-26)
#
# SYNOPSIS
# 	conv-to-cbz.sh [list] [-v]
#
# DESCRIPTION
# 	Finds all cbr files passed in as FILES or found in any subdirectories if
# 	FILES contains a folder. Creates a tmp directory at ./, unpack the comic
# 	there, and repack into zip.
# 	TODO(sez): add CB7 functionality
#
# DEPENDENCIES
# 	Bash 4.4 or greater
#
# ARGUMENTS
# 	FILES	List of files and directories
# 	-v		Print all debug logs (optional

print_usage() {
	cat <<END
Usage: conv-to-cbz.sh [list] [-v]
	Default action is to convert any cbr files in list, or under any directories
	in list.

	-v	print all debug logs
	-d	dry-run mode
END
}

err() {
	echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $*" >&2
}

verbose='false'
dryrun='false'

while getopts 'dv' flag; do
	case "${flag}" in
	d) dryrun='true' ;;
	v) verbose='true' ;;
	*)
		print_usage
		exit 1
		;;
	esac
done

args="${@:$OPTIND}"

main() {
	"${verbose}" && echo "Input: ${args}"

	if [[ -z "${args}" ]]; then
		err "Error nothing to do"
		exit 1
	fi

	local targets=()
	local target
	for target in "${args[@]}"; do
		"${verbose}" && echo "Parsing: ${target}"
		if [[ -d "${target}" ]]; then
			local files
			readarray -d '' files < <(find "${target}" -type f -name '*.cbr' ! -name '.*' -print0)
			local file
			for file in "${files[@]}"; do
				targets+=("${file}")
			done
		elif [[ -f "${target}" ]]; then
			targets+=("${target}")
		else
			err "Unknown input '${file}'"
		fi
	done

	"${verbose}" && echo "Converting ${#targets[@]} archives:"
	"${verbose}" && echo "${targets[@]}"

	for target in "${targets[@]}"; do
		if [[ ! "${target}" =~ \.cbr$ ]]; then
			err "Error ${target} not a CBR! Skipping..."
			continue
		fi

		"${verbose}" && echo -e "\nTarget: ${target}\n"

		local target_dir
		target_dir="/${target}"
		target_dir="${target_dir%/*}"
		target_dir="${target_dir#/}"
		local target_short
		target_short="${target%.cbr}"
		target_short="${target_short##*/}"

		if "${dryrun}"; then
			echo "pushd ${target_dir}"
			echo "mkdir ${target_short}"
			echo "pushd ${target_short}"
			echo "unrar e ../${target_short}.cbr"
			echo "popd"
			echo "zip -r ${target_short} ${target_short}"
			echo "mv ${target_short}.zip ${target_short}.cbz"
			echo "rm -r ${target_short}"
			echo "popd"
			continue
		fi

		if [[ -n "${target_dir}" ]]; then
			"${verbose}" && echo "cd ${target_dir}"
			pushd "${target_dir}"
		fi
		"${verbose}" && echo "mkdir tmp dir ${target_short}"
		mkdir "${target_short}"
		"${verbose}" && echo "cd tmp dir ${target_short}"
		pushd "${target_short}"
		"${verbose}" && echo "unrar ${target} from outer to here"
		unrar e "../${target_short}.cbr"
		"${verbose}" && echo "chmod"
		find . -type d -exec chmod 777 {} +
		find . -type f -exec chmod 666 {} +
		"${verbose}" && echo "cd back"
		popd
		"${verbose}" && echo "zip ${target_short}"
		zip -r "${target_short}.zip" "${target_short}"
		"${verbose}" && echo "rename ${target_short}.zip to ${target_short}.cbz"
		mv "${target_short}.zip" "${target_short}.cbz"
		"${verbose}" && echo "rm ${target_short}"
		rm -r "${target_short}"
		"${verbose}" && echo "cd back"
		if [[ -n "${target_dir}" ]]; then
			popd
		fi
	done
}

main "$@"
