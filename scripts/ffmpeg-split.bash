#! /bin/bash
: ${FFMPEG=ffmpeg} ${FFPROBE=ffprobe}
set -e

SCRIPT=$(basename ${BASH_SOURCE[0]})

while getopts ":hf:ot:-:" flag
do
	case $flag in
		-) # long argument, ignore ${OPTARG}
		;;
		h|help) # ignore
			exit
		;;
		o|output)
			out="$OPTARG"
		;;
		f|frames)
			frames="$OPTARG"
		;;
		t|times)
			times="$OPTARG"
		;;
		# unrecognized options would cause bash error
	esac
done >&2
shift $((OPTIND-1))

[[ $frames ]] && times=

function ffmpeg_split() {
	: ${ffmpeg_options="-nostdin -c copy -map 0 -flags +global_header -f segment"}
	file_in="$1"
	shift
	[[ -f "$file_in" ]] || { echo "file $file_in not found"; return -1; }
	shift
	[[ "$@" ]] && { echo "See usage"; return -1; }
	basename="${file_in##*/}"
	shift
	[[ $out ]] || out="${basename%.*}_%03d.MKV"
	
	if [[ $frames ]]
	then
		$FFMPEG -i "$file_in" $ffmpeg_options -segment_frames "$frames" "$out"
	elif [[ $times ]]
	then
		$FFMPEG -i "$file_in" $ffmpeg_options -segment_times "$times" "$out"
	else
		echo "Must specify either -t time1,time2,... or -f frame1,frame2,.."
		return -1
	fi >&2
}

: ${errors=`mktemp`}

if ffmpeg_split "$@" 2> "$errors"
then
	exit 0
else
	cat "$errors"
fi >&2
exit 1
