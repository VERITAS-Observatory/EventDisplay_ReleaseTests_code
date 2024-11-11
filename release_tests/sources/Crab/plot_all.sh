#!/bin/bash
# run all plotting scripts for a given cut
#

if [[ $# -lt 1 ]]; then
echo "
   $0 <anasum directory> <output directory>

"
exit
fi

LFIL="$(ls -1 ${1}/*.combined.root | sort -r)"

CUT=$(basename $1)
CUT=${CUT/anasum_/}
echo "CUT: $CUT"
ODIR="${2}/$CUT"
echo "Output directory: $ODIR"
mkdir -p "$ODIR"

PDIR=$(pwd)

for F in $LFIL; do
    echo "Analysing $F"
    TF=$(basename $F .combined.root)
    TF=${TF/anasum_releaseTesting/}
    OTF="${ODIR}/${TF}"
    echo "Output per analysis: $OTF"
    mkdir -p "${OTF}"
    root -q -l -b "plot_energy_spectra.C(\"$F\", \"${OTF}\" )"
    root -q -l -b "plot_lightcurves.C(\"$F\", \"${OTF}\", -1. )"
    root -q -l -b "plot_skymaps.C(\"$F\", \"${OTF}\", true )"
    OTF="${ODIR}/${TF}_05TeV"
    root -q -l -b "plot_lightcurves.C(\"$F\", \"${OTF}\", 5. )"
    OTF="${ODIR}/${TF}_10TeV"
    root -q -l -b "plot_lightcurves.C(\"$F\", \"${OTF}\", 10. )"
done
