#!/bin/bash
# run script for data - MC comparision
# 

source $EVNDISPSYS/setObservatory.sh VTS

ODIR=OUTDIR
CDIR=CURRENTDIR

PP=$(pwd)
cd ${CDIR}

$EVNDISPSYS/bin/compareDatawithMC \
          $ODIR/mcdatacomparison.runparameter \
          -3 \
          $ODIR/mcdatacomparison.root \
          > $ODIR/mcdatacomparison.log

# prepare all plots
root -l -q -b "plot_compare.C(\"$ODIR\")"
# remove results root file
# rm -f -v $ODIR/mcdatacomparison.root
cd ${PP}
