#!/bin/bash
# calculate radial acceptances for different epochs
# 
set -e

if [ $# -lt 1 ]; then
echo "
./calculate_radialAcceptances.sh <version>

"
exit
fi

VERSION=${1}

DDIR="$VERITAS_DATA_DIR/processed_data_${VERSION}/${VERITAS_ANALYSIS_TYPE:0:2}/mscw/"
CDIR=`pwd`
ODIR="../../../EventDisplay_Release_${VERSION}/${VERITAS_ANALYSIS_TYPE:0:2}/radialAcceptances"
mkdir -p ${ODIR}

RUNLIST_V4="${CDIR}/runlists/runlist-V4.dat"
RUNLIST_V5="${CDIR}/runlists/runlist-m82-V5.dat"
RUNLIST_V6="${CDIR}/runlists/runlist-m82-V6.dat"

cd $EVNDISPSCRIPTS/

# for E in V4 V5 V6
for E in V6
do
    if [[ $E == "V4" ]]; then
       RLIST=${RUNLIST_V4}
       SIMTYPE="GRISU"
    elif [[ $E == "V5" ]]; then
       RLIST=${RUNLIST_V5}
       SIMTYPE="GRISU"
    elif [[ $E == "V6" ]]; then
       RLIST=${RUNLIST_V6}
       SIMTYPE="CARE_June2020"
    fi

    # for I in 0 2 3 4 5
    for I in 0
    do
       ./IRF.generate_radial_acceptance.sh ${RLIST} ${DDIR} ${CDIR}/cuts.dat ${E} ${SIMTYPE} ${I}
    done
done
cd ${CDIR}
