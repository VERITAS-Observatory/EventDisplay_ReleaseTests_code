#!/bin/bash
# run all plotting scripts for all zenith angle ranges
#

if [[ $# -lt 1 ]]; then
echo "
   $0 <anasum directory> <output directory>

"
exit
fi

LFIL="$(ls -1 ${1}/*.combined.root)"

CUT=$(basename $1)
CUT=${CUT/anasum_/}
echo "CUT: $CUT"
ODIR="${2}/$CUT"
echo "Output directory: $ODIR"
mkdir -p "$ODIR"

PDIR=$(pwd)
# cd $ROOTSYS

for F in $LFIL; do
    echo "Analysing $F"
    TF=$(basename $F .combined.root)
    TF=${TF/anasum_releaseTesting/}
    OTF="${ODIR}/${TF}"
    echo "Output per analysis: $OTF"
    mkdir -p "${OTF}"
    # root -q -l -b "plot_energy_spectra.C(\"$F\", \"${OTF}\" )"
    root -q -l -b "plot_lightcurves.C(\"$F\", \"${OTF}\" )"
    exit
done

exit

for N in $PSPACE
do
   #root -q -l -b "plot_energy_spectra.C(\"${1}\", \"$N\", \"$BCKMODEL\" )"
   root -q -l -b "plot_lightcurves.C(\"${1}\", \"$N\", \"$BCKMODEL\" )"
#   root -q -l -b "plot_lightcurves.C(\"${1}\", \"$N\", \"$BCKMODEL\" )"
#   root -q -l -b "plot_skymaps.C(\"${1}\", \"$N\", \"$BCKMODEL\" )"
#   root -q -l -b "plot_skymaps.C(\"${1}\", \"$N\", \"RB\" )"
done
