#! /bin/bash
: ${FFMPEG=ffmpeg} ${FFPROBE=ffprobe}
set -e


SCRIPT=$(basename ${BASH_SOURCE[0]})


function help() {
	cat <<- EOF
This is help
EOF
	caller 0
	exit -1
}

function usage() {
	cat <<- EOF
This is usage
EOF
	caller 0
	exit -1
}

function die() {
	echo <<< "$@"
	exit -1
}


while getopts ":hF:o:T: -:" OPT
do
	if [[ $OPT == '-' ]] # Long option
	then
		OPT=$OPTARG
		eval $OPT && continue || usage # you may or may not want the continue
	fi
	case $OPT in
		-) # long argument, ignore ${OPTARG}
		;;
		h|help) help
		;;
		o|output) out="$OPTARG"
		;;
		F|frames) frames="$OPTARG"
		;;
		T|times) times="$OPTARG"
		;;
		\?) usage
		;;
	esac
done >&2
shift $((OPTIND-1))

[[ $frames ]] && unset times

#ffmpeg_options="-nostdin -c copy -map 0 -flags +global_header -f segment"
ffmpeg_options="-c:v copy -c:a copy -map 0 -flags +global_header -f segment"
function ffmpeg_split() {
	file_in="$1"
	[[ -f "$file_in" ]] || { echo "file $file_in not found"; return -1; }
	shift
	[[ "$@" ]] && usage
	basename="${file_in##*/}"
	filepart="${basename%.*}"
	[[ $out ]] || out="${filepart}_%03d.MKV"
	
	if [[ $frames ]]
	then
		$FFMPEG -i "$file_in" $ffmpeg_options -segment_frames "$frames" "$out"
	elif [[ $times ]]
	then
		$FFMPEG -i "$file_in" $ffmpeg_options -segment_times "$times" "$out"
	else
		die "Must specify either -T time1,time2,... or -F frame1,frame2,.."
	fi >&2
}

: ${errors=`mktemp`}

if ffmpeg_split "$@" 2> "$errors"
then
	exit 0
else
	cat "$errors" >&2
fi
exit 1
