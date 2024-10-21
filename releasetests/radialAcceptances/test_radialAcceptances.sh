#!/bin/bash
# testing radial acceptances
# --> analyse runs used for radial
#     acceptance calculations
# skymaps should be flat / N(0,1)
#
set -e

if [[ $# < 2 ]]; then
echo "
  ./test_radialAcceptances.sh <version> SUB <RE/RB>
  --> Step 1 to analyse run-wise with anasum

  ./test_radialAcceptances.sh <version> FFF <RE/RB>
  --> Step 2 to combine anasum file
"
exit
fi

# Eventdisplay version
VERSION=${1}
# run mode
MODE=$2
# background model (RB is the improtant test)
[[ "$3" ]] && BCK=$3 || BCK="RB"
DDIR="$VERITAS_USER_DATA_DIR/analysis/Results/${VERSION}/RadialAcceptances/"
CDIR=`pwd`

RUNLIST_V4="${CDIR}/runlists/runlist-V4.dat"
RUNLIST_V5="${CDIR}/runlists/runlist-m82-V5.dat"
RUNLIST_V6="${CDIR}/runlists/runlist-m82-V6.dat"

cd ${EVNDISPSCRIPTS}

#for E in V4 V5 V6
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
       if [[ $VERSION == *"v483"* ]]; then
           SIMTYPE="CARE_June1702"
       else
           SIMTYPE="CARE_June2020"
       fi
    fi

    #for I in 2 3 4 5
    for I in 0
    do
#       for C in BDTmoderate2tel BDTsoft2tel BDThard3tel
       for C in BDTExtended025moderate2tel BDTExtended050moderate2tel
       do
            ANASUMDIR=${DDIR}/anasum/anasum_ID${I}_${E}_${C}_${BCK}
            if [ "$MODE" == "SUB" ]
            then
               mkdir -p ${ANASUMDIR}
               echo ${ANASUMDIR}
               echo $CDIR/runparameter.dat
                ./ANALYSIS.anasum_parallel_from_runlist.sh \
                            $RLIST ${ANASUMDIR} \
                            $C ${BCK} \
                            $CDIR/runparameter.dat \
                            $DDIR/RecID0 \
                            DEFAULT 0
             else
                 ./ANALYSIS.anasum_combine.sh \
                            ${ANASUMDIR}/${C}.anasum.dat \
                            $ANASUMDIR \
                            anasum.combined.root \
                            $CDIR/runparameter.dat
             fi
       done
    done
done
cd ${CDIR}
