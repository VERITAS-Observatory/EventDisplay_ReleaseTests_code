#!/bin/bash
# run script for data - MC comparision
# 

source $EVNDISPSYS/setObservatory.sh VTS

ODIR=OUTDIR
CDIR=CURRENTDIR
EPOCHATM=EEPOCHTM

PP=$(pwd)
cd ${CDIR}

$EVNDISPSYS/bin/compareDatawithMC \
          $ODIR/mcdatacomparison.runparameter \
          -3 \
          $ODIR/mcdatacomparison.root \
          1 $EPOCHATM \
          > $ODIR/mcdatacomparison.log

# prepare all plots
root -l -q -b "plot_compare.C(\"$ODIR\")"
# remove results root file
# rm -f -v $ODIR/mcdatacomparison.root
cd ${PP}
