#!/bin/bash
# testing lookup tables by analysis
# a run and see if the table tests are
# survived at the start of the run
# (look at the log files for the lines after
# " lookup table file sanity check"
#

VERSION=$(cat $VERITAS_EVNDISP_AUX_DIR/IRFVERSION)

TFV6=$(find $VERITAS_EVNDISP_AUX_DIR/Tables/ -name "*.root")

TESTFILE="$VERITAS_USER_DATA_DIR/analysis/Results/${VERSION}/Crab/evndisp/64080.root"

for T in ${TFV6}
do
     echo "Running mscw analysis for $T"
     TB=$(basename $T .root)

     ODIR="$VERITAS_USER_DATA_DIR/analysis/Results/${VERSION}/table-tests/"
     mkdir -p ${ODIR}
     OFIL="test.$TB.mscw"

     echo $TB $OFIL $ODIR

     rm -f ${ODIR}/${OFIL}.log
     ${EVNDISPSYS}/bin/mscw_energy -tablesfile ${T} -noshorttree -maxnevents=10  -arrayrecid=0 \
                       -inputfile ${TESTFILE} \
                       -writeReconstructedEventsOnly=1 -outputfile ${ODIR}/${OFIL}.root > ${ODIR}/${OFIL}.log
     # (not interested in the root file with events)
     rm -f ${ODIR}/${OFIL}.root
done
