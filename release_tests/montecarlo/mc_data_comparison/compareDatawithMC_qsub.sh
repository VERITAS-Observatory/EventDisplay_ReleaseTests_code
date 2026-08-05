#!/bin/bash
# run script for data - MC comparison
#

source $EVNDISPSYS/setObservatory.sh VTS

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
XGBSUFFIX="xgb_stereo"
MAXZE="20."
ERECOMETHOD="0"

PP=$(pwd)
cd ${CDIR}

$EVNDISPSYS/bin/compareDatawithMC \
          $ODIR/mcdatacomparison.runparameter \
          $CUT \
          $ODIR/mcdatacomparison.root \
          ${BDT} $EPOCHATM $ERECOMETHOD \
          ${XGBSUFFIX} ${MAXZE} ${T2} $RECOMETHOD \
          > $ODIR/mcdatacomparison.log

# prepare all plots
root -l -q -b "plot_compare.C(\"$ODIR\")"
# remove results root file
# rm -f -v $ODIR/mcdatacomparison.root
cd ${PP}
