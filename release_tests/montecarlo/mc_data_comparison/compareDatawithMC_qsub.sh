#!/bin/bash
# run script for data - MC comparison
#
set -e

source "$EVNDISPSYS/setObservatory.sh" VTS

ODIR=OUTDIR
CDIR=CURRENTDIR
EPOCHATM=EEPOCHTM
RECOMETHOD=METHODRECO

BDT="0"
if [[ ${ODIR} == *"CARE_RedHV"* ]]; then
    BDT="0"
fi

CUT="-3"
T2="0.035"
MC_XGB_SUFFIX="MCXGBSUFFIX"
DATA_XGB_SUFFIX="DATAXGBSUFFIX"
RUNPARAMETER="RUNPARAMETERFILE"
MAXZE="20."
ERECOMETHOD="0"

PP=$(pwd)
cd "$CDIR"

if [[ $RECOMETHOD == 2 && $MC_XGB_SUFFIX != "$DATA_XGB_SUFFIX" ]]; then
    if ! "$EVNDISPSYS/bin/compareDatawithMC" | grep -q 'data XGB stereo file suffix'; then
        echo "Error: compareDatawithMC does not support a separate data XGB suffix" >&2
        exit 1
    fi
fi

cp "$RUNPARAMETER" "$ODIR/mcdatacomparison.runparameter"
"$EVNDISPSYS/bin/compareDatawithMC" \
          "$RUNPARAMETER" \
          $CUT \
          "$ODIR/mcdatacomparison.root" \
          ${BDT} $EPOCHATM $ERECOMETHOD \
          "$MC_XGB_SUFFIX" ${MAXZE} ${T2} "$RECOMETHOD" "$DATA_XGB_SUFFIX" \
          > "$ODIR/mcdatacomparison.log"

# prepare all plots
root -l -q -b "plot_compare.C(\"$ODIR\",\"PLOTLABEL\")"
# remove results root file
# rm -f -v $ODIR/mcdatacomparison.root
cd "$PP"
