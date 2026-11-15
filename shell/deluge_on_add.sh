#!/usr/bin/env bash
#
# deluge_on_add.sh - Hook harness for Deluge Execute plugin
#
# Author:		sez
# Version:		0.1.0 (2026-11-15)
#
# SYNOPSIS
# 	deluge_on_add.sh [-v] TORRENT_ID TORRENT_NAME TORRENT_PATH
#
# DESCRIPTION
# 		Execute plugin always calls target program with three positional
# 		arguments. See https://deluge-torrent.org/plugins/execute/ for more
# 		info on the Deluge Execute plugin.
#
# ARGUMENTS
# 		TORRENT_ID		Deluge ID for interacting via the RPC API
# 		TORRENT_NAME	Name of torrent; user facing one-line, and tracker name
# 		TORRENT_PATH	Path to torrent file or root directory; depends on torrent status
# 		-v				Set verbosity; multiple levels
# 		-d				Dry-run; change nothing but log expected actions

print_usage() {
	cat <<END
Usage: deluge_on_add.sh [-dv] TORRENT_ID TORRENT_NAME TORRENT_PATH
       Currently is a placeholder logger.

        -d      dry-run mode
        -v      set verbosity; multiple levels
END
}

verbose=0
dryrun='false'

while getopts 'dv' flag; do
	case "${flag}" in
	d) dryrun='true' ;;
	v) ((verbose++)) ;;
	*)
		print_usage
		exit 1
		;;
	esac
done

log() {
	local level="$1"
	shift
	if [[ ${level} != 'DEBUG' && ${level} != 'INFO' && ${level} != 'WARN' && ${level} != 'ERROR' ]]; then
		printf '[%s] %s: %s\n' "$0" "WARN" "misconfigured log level: '${level}'" >&2
		return
	elif [[ "${level}" == 'DEBUG' && verbose -lt 2 ]]; then
		return
	elif [[ "${level}" == 'INFO' && verbose -lt 1 ]]; then
		return
	fi
	printf '[%s] %s: %s\n' "$0" "$level" "$*" | tee >(logger)
}

main() {
	if [[ $# -lt 3 ]]; then
		log ERROR "Expected 3 arguments, got $#: '$@'"
		return 1
	fi

	local torrent_id="$1"
	local torrent_name="$2"
	local torrent_path="$3"

	log DEBUG "Torrent ID: ${torrent_id}, Torrent Name: ${torrent_name}, Torrent Path: ${torrent_path}"

	# Boilerplate done
}

main "${@:$OPTIND}"
