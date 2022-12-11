#!/bin/bash
# calculate radial acceptances for different epochs
# 
set -e

if [ $# -lt 2 ]; then
echo "
./calculate_radialAcceptances.sh <version> <analysis step>

   <analysis step> = EVNDISP/MSCW/ACCEPTANCES
"
exit
fi

VERSION=${1}

DDIR="$VERITAS_USER_DATA_DIR/analysis/Results/${VERSION}/RadialAcceptances/"
CDIR=`pwd`
ODIR="../../${VERSION}/radialAcceptances"
mkdir -p ${ODIR}

RUNLIST_V4="${CDIR}/runlists/runlist-V4.dat"
RUNLIST_V5="${CDIR}/runlists/runlist-m82-V5.dat"
RUNLIST_V6="${CDIR}/runlists/runlist-m82-V6.dat"

# correct script directory
EDVERSION=$($EVNDISPSYS/bin/evndisp --version | tr -d .)
EDVERSION=${EDVERSION:1}
if [[ $EDVERSION -lt "485" ]]; then
    cd $EVNDISPSYS/scripts/VTS
    RPARA="EVNDISP.reconstruction.runparameter"
else
    cd $EVNDISPSCRIPTS/
    RPARA="EVNDISP.reconstruction.runparameter.v48x"
fi

for E in V4 V5 V6
do
    if [[ $E == "V4" ]]; then
       RLIST=${RUNLIST_V4}
       SIMTYPE="GRISU"
    elif [[ $E == "V5" ]]; then
       RLIST=${RUNLIST_V5}
       SIMTYPE="GRISU"
    elif [[ $E == "V6" ]]; then
       RLIST=${RUNLIST_V6}
       if [[ $EDVERSION -lt "485" ]]; then
           SIMTYPE="CARE_June1702"
       else
           SIMTYPE="CARE_June2020"
       fi
    fi

    if [[ $2 == "EVNDISP" ]]; then
        ./ANALYSIS.evndisp.sh ${RLIST} ${DDIR}/evndisp ${RPARA}
    else
        for I in 0 2 3 4 5
        do
           if [[ $2 == "ACCEPTANCES" ]]; then
               ./IRF.generate_radial_acceptance.sh  ${RLIST} ${DDIR} ${CDIR}/cuts.dat ${E} ${SIMTYPE} ${I}
           else
               ./ANALYSIS.mscw_energy.sh ${RLIST} ${DDIR}/evndisp ${DDIR}/RecID${I} ${I}
           fi
        done
    fi
done
cd ${CDIR}
