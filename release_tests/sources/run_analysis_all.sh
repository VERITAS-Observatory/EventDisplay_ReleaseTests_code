#!/bin/bash
# run test analyses from list of targets
#
#
if [[ $# -lt 1 ]]; then
echo "
    ./run_analysis_all.sh

    (one random command line argument required)

"
exit
fi

VERSION="$(cat $VERITAS_EVNDISP_AUX_DIR/IRFVERSION)"
MINORVERSION="$(cat $VERITAS_EVNDISP_AUX_DIR/IRFMINORVERSION)"
ANALYSISTYPE="${VERITAS_ANALYSIS_TYPE:0:2}"
LTARGETS=$(cat TARGETS.dat)

EPOCHS="V4 V5 V4V5 V6 all"
# AP/NN redHV
CUTS="softbox"
if [[ $ANALYSISTYPE == "NN" ]]; then
    # NN nominal
    CUTS="supersoftNN2tel"
else
    # AP nominal
    CUTS="hard2tel soft2tel moderate2tel hard3tel"
fi
echo "$CUTS"

# current directory with run lists
SDIR=$(pwd)
# archive directory
DDIR="${VERITAS_DATA_DIR}/shared/processed_data_${MINORVERSION}"
# output directory
ODIR="${VERITAS_USER_DATA_DIR}/analysis/Results/${VERSION}/${ANALYSISTYPE}/SourceTests"

cd "${EVNDISPSCRIPTS}" || exit

for T in ${LTARGETS}
do
    for C in $CUTS
    do
        for E in $EPOCHS
        do
            RUNLIST="${SDIR}/${T}/runlist_releaseTesting_${E}.dat"
            if [[ ! -e "$RUNLIST" ]]; then
                RUNLIST="${SDIR}/${T}/runlist_releaseTesting${E}.dat"
                if [[ ! -e "$RUNLIST" ]]; then
                    echo "No run list ${SDIR}/${T}/runlist_releaseTesting_${E}.dat"
                    continue
                fi
            fi

            echo "Analyzing ${T} with ${C} cuts (epoch $E)"
            echo "   input file list: $RUNLIST"
            echo "   input directory: ${DDIR}/${ANALYSISTYPE}/anasum_${C}"
            echo "   output directory: ${ODIR}/${T}/${C}/${E}"

           ./ANALYSIS.anasum_combine.sh \
               "${RUNLIST}" \
               "${DDIR}"/"${ANALYSISTYPE}"/anasum_"${C}" \
               "${ODIR}"/"${T}"/"${C}"/"${E}"
        done
    done
done
