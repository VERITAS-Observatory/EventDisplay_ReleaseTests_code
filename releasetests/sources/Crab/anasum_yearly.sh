#!/bin/bash

# run epoch wise anasum analysis
# (also analysis of the data divided in
# atmospheres)
#
# do:
# ./anasum_yearly.sh <version> SUB
# to submit jobs

# ./anasum_yearly.sh <version> FFF
# to combine anasum files
set -e

if [[ $# -lt 4 ]]; then
echo "
  ./anasum_yearly.sh <runparameter file> SUB <SZE/MZE/LZE/WOBBLE> <RE/RB/IGNOREACCEPTANCE>
  --> Step 1 to analyse run-wise with anasum

  ./anasum_yearly.sh <runparameter file> FFF <SZE/MZE/LZE/WOBBLE> <RE/RB/IGNOREACCEPTANCE>
  --> Step 2 to combine anasum file

"
exit
fi

###########################
# read runparameter file
if [[ ! -e ${1} ]]; then
   echo "Error, runparameter file not found: ${1}"
   exit
fi
# Eventdisplay version
VERSION=$(grep VERSION ${1} | awk '{print $3}')
# Analysis type
ANALYSISTYPE="AP"
if [[ ! -z  $VERITAS_ANALYSIS_TYPE ]]; then
    ANALYSISTYPE="${VERITAS_ANALYSIS_TYPE:0:2}"
fi
# eventdisplay version --> defines script directory
EDVERSION=$($EVNDISPSYS/bin/evndisp --version | tr -d .)
EDVERSION=${EDVERSION:1}
# Epochs
MEPOCH=$(grep MAJOREPOCH ${1} | grep "*" | awk '{print $3}')
EPOCH=($(grep EPOCH ${1} | grep "*" | grep -v MAJOR | awk '{print $3}'))
# Atmopsphere
ATMOS=($(grep ATMOSPHERE ${1} | grep "*" | awk '{print $3}'))
# CUTS
CUTS=($(grep CUT ${1} | grep "*"| awk '{print $4}'))
# Source name
OBJECT=($(grep SOURCE ${1} | grep "*" | awk '{print $3}'))
#########################
# run mode
MODE=$2
# Directory for data files
DDIR="$VERITAS_USER_DATA_DIR/analysis/Results/${VERSION}/${ANALYSISTYPE}/${OBJECT}/"
echo $DDIR
# Directory with run lists
RDIR=$(pwd)
# elevation range
[[ "$3" ]] && ELE=$3 || ELE="SZE"
[[ "$4" ]] && BCK=$4 || BCK="RE"

# mscw_energy subdirectory
MSCWSDIR="mscw"
FORCEDATMO=""

for I in "${EPOCH[@]}"
#for I in ${MEPOCH}
do
    if [[ ${MEPOCH} == *"redHV"* ]] && [[ ${I} != "V6redHV" ]]; then
       I="${I}_redHV"
    elif [[ ${I} == "V6redHV" ]]; then
       I="V6_redHV"
    fi
    for A in "" "${ATMOS[@]}"
    do
        # prepare run list
        ATM=${A}
        if [[ ${I: -1} == "w" ]] && [[ ${A} == *"62"* ]]; then
           continue
        elif [[ ${I: -1} == "s" ]] && [[ ${A} == *"61"* ]]; then
           continue
        fi
        if [[ -n ${ATM} ]]; then
           ATM="_ATM${ATM}"
           if [[ $MODE == "WOBBLE" ]]; then
             continue
           fi
        fi
        echo "Processing $I ($ELE $ATM $BCK $FORCEDATMO)"

        MDIR="$DDIR/${MSCWSDIR}_${I}${ATM}_${ELE}"
        if [[ ! -d ${MDIR} ]]; then
           echo "   Data directory not found: ${MDIR}"
           echo "   skipping (this might be due to an error; or there are simply no runs available for this epoch)"
           continue
        fi
        echo ${MDIR}
        RLIST=${MDIR}/runlist.dat
        rm -f $RLIST
        find ${MDIR} -name "*.root" -exec basename {} .mscw.root \; | sort > $RLIST

        if [[ ! -e $RLIST ]]; then
           echo "Run list not found: $RLIST"
           continue
        fi
        echo "Run list ${RLIST}"

        cd ${EVNDISPSCRIPTS}

        # list of cuts
        for C in "${CUTS[@]}"
        do

            ANASUMDIR=$DDIR/anasum/anasum_${I}${ATM}_${C}_${ELE}_${BCK}

            echo "ANASUM output directory: $ANASUMDIR"

            if [ "$MODE" == "SUB" ]
            then
               mkdir -p ${ANASUMDIR}
               ./ANALYSIS.anasum_parallel_from_runlist.sh  \
                            $RLIST ${ANASUMDIR} \
                            $C ${BCK} \
                            $RDIR/runparameter.dat \
                            ${MDIR} \
                            DEFAULT 0 $FORCEDATMO
             elif [ "$MODE" == "FFF" ] ; then
                 if [[ ! -e ${ANASUMDIR} ]]; then
                     echo "error: no anasum directory with files to be combined"
                     echo "continuing..."
                     continue
                 fi
                 echo "  combining files from ${ANASUMDIR}/${C}.anasum.dat"
                 ./ANALYSIS.anasum_combine.sh \
                            $RLIST \
                            $ANASUMDIR \
                            anasum.combined.root \
                            $RDIR/runparameter.dat
                fi
       done
    done
done
