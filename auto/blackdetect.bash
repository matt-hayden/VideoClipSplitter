#! /bin/bash
: ${FFMPEG=ffmpeg} ${FFPROBE=ffprobe}
set -e

SCRIPT=$(basename ${BASH_SOURCE[0]})

: ${log=`mktemp`} ${errors=`mktemp`}

output_options="-show_entries tags=lavfi.black_start,lavfi.black_end,lavfi.scene_score -of flat"
function blackdetect() {
	$FFPROBE -f lavfi "movie=${1},blackdetect=[out0]" $output_options
}

while getopts ":hno:q0123456789-:" flag
do
	case $flag in
		-) # long argument, ignore ${OPTARG}
		;;
		h|help) # ignore
			exit
		;;
		f|overwrite)
			overwrite=1
		;;
		o|output)
			out="$OPTARG"
		;;
		q|quiet)
			quiet=1
		;;
		0) # ignored, default used above
		;;
		1|2|3)
			function blackdetect() {
				$FFPROBE -f lavfi "movie=${1},blackdetect=d=1[out0]" $output_options
			}
		;;
		4|5|6)
			function blackdetect() {
				$FFPROBE -f lavfi "movie=${1},blackdetect=d=1/15[out0]" $output_options
			}
		;;
		7|8|9)
			function blackdetect() {
				$FFPROBE -f lavfi "movie=${1},blackdetect=d=1/30:picture_black_ratio_th=0.75:pixel_black_th=0.50[out0]" $output_options
			}
		;;
		# unrecognized options would cause bash error
	esac
done >&2
shift $((OPTIND-1))

file_in="$1"
shift
[[ $out ]] || out="${file_in##*/}.blackdetect"
if [[ -e "$out" ]] && ! [[ $overwrite ]]
then
	echo "Refusing to overwrite $out"
	exit -1
fi >&2
[[ "$@" ]] && { echo "See usage" >&2; exit -1; }

if blackdetect "$file_in" >"$log" 2>"$errors"
then
	if [[ -s "$log" ]]
	then
		if mv -b "$log" "$out"
		then
			[[ $quiet ]] || echo "$file_in => $out"
		fi
		exit 0
	fi
else
	cat "$errors" >&2
fi
exit 1
