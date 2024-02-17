#!/bin/bash
# run test analyses from list of targets
#
#
if [[ $# -lt 1 ]]; then
echo "
    ./run_analysis_all.sh

"
exit
fi

VERSION="v490"
ANALYSISTYPE="${VERITAS_ANALYSIS_TYPE:0:2}"
LTARGETS=$(cat TARGETS.dat)

EPOCHS="V4 V5 V6 all"
CUTS="soft2tel moderate2tel hard3tel"
if [[ $RUNPARA == *"AP"* ]] && [[ $RUNPARA == *"redHV"* ]]; then
    CUTS="softbox"
elif [[ $RUNPARA == *"NN"* ]] && [[ $RUNPARA == *"redHV"* ]]; then
    CUTS="softbox supersoft"
elif [[ $RUNPARA == *"NN"* ]]; then
    CUTS="supersoft supersoftNN2tel"
fi

CUTS="hard3tel"

# current directory with run lists
SDIR=$(pwd)
# data directory
DDIR="$VERITAS_USER_DATA_DIR/analysis/Results/${VERSION}/processed_data_v490.7/"
# output directory
ODIR="${VERITAS_USER_DATA_DIR}/analysis/Results/${VERSION}/${ANALYSISTYPE}/SourceTests/"

cd ${EVNDISPSCRIPTS} || exit

for T in ${LTARGETS}
do
    for C in $CUTS
    do
        for E in $EPOCHS
        do
            if [[ ! -e "${SDIR}/${T}/runlist_releaseTesting_${E}.dat" ]]; then
                echo "No run list ${SDIR}/${T}/runlist_releaseTesting_${E}.dat"
                continue
            fi

            echo "Analysing ${T} with ${C} cuts (epoch $E)"
            echo "   input file list: ${SDIR}/${T}/runlist_releaseTesting_${E}.dat"
            echo "   input directory: ${DDIR}/${ANALYSISTYPE}/anasum_${C}"
            echo "   output directory: ${ODIR}/${T}/${E}"
            continue
           ./ANALYSIS.anasum_combine.sh \
               ${SDIR}/${T}/runlist_releaseTesting_${E}.dat \
               ${DDIR}/${ANALYSISTYPE}/anasum_${C} \
               ${ODIR}/${T}/${E}
        done
    done
done
