#! /bin/bash
set -e

SCRIPT=$(basename ${BASH_SOURCE[0]})

#[[ $# -gt 0 ]] || { echo "Usage: $SCRIPT video [output]"; exit -1; }

log=`mktemp`
errors=`mktemp`

output_options="-show_entries tags=lavfi.black_start,lavfi.black_end,lavfi.scene_score -of flat"
function blackdetect() {
	ffprobe -f lavfi "movie=${1},blackdetect=[out0]" $output_options
}

while getopts ":hno:0123456789-:" flag
do
	case flag in
		-) # long argument, ignore ${OPTARG}
		;;
		h|help) # ignore
		;;
		o|output)
			out="$OPTARG"
		;;
		0) # ignored, default used above
		;;
		1|2|3)
			function blackdetect() {
				ffprobe -f lavfi "movie=${1},blackdetect=d=1[out0]" $output_options
			}
		;;
		4|5|6)
			function blackdetect() {
				ffprobe -f lavfi "movie=${1},blackdetect=d=1/15[out0]" $output_options
			}
		;;
		7|8|9)
			function blackdetect() {
				ffprobe -f lavfi "movie=${1},blackdetect=d=1/30:picture_black_ratio_th=0.75:pixel_black_th=0.50[out0]" $output_options
			}
		;;
		# unrecognized options would cause bash error
	esac
done
shift "$((OPTIND-1))"

file_in="$1"
shift
[[ $out ]] || out="${file_in##*/}.blackdetect"

#[[ "$@" ]] && echo Unused arguments: "$@"

if blackdetect "$file_in" >"$log" 2>"$errors"
then
	if [[ -s "$log" ]]
	then
		mv -b "$log" "$out"
		echo "$out"
		exit 0
	fi
else
	cat "$errors" >&2
fi
exit 1
