#!/bin/bash
# run release testing analysis
#
# requires run list (simple format) as
# ${SOURCE}/runlist_releaseTesting.dat
#
# for anasum:
# ${SOURCE}/ANASUM.runparameter
# ${SOURCE}/ANASUM.timemask.dat
#
# is exected to be in DDIR
#

if [[ $# -lt 2 ]]; then
echo "
  ./run_analysis.sh <runparameter file> <SOURCE> <TYPE> <CUT> <EPOCH>

   analysis types:
       EVNDISP
       MSCW
       ANASUM_SUB
       ANASUM_FFF

   cuts: (i.e., moderate2tel, soft2tel, hard3tel)
"
exit
fi

SOURCE=${2}
ANATYPE=${3}
CUT=${4}
EPOCH=${5}

BCKMODEL="RE"
BCKMODEL="IGNOREIRF"
BCKMODEL="IGNOREACCEPTANCE"

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
DIRRECOTYPE="_DISP"
if [[ ! -z  $VERITAS_ANALYSIS_TYPE ]]; then
    ANALYSISTYPE="${VERITAS_ANALYSIS_TYPE:0:2}"
    if [[ ${VERITAS_ANALYSIS_TYPE} == *"DISP"* ]]; then
        DIRRECOTYPE="_DISP"
    else
        DIRRECOTYPE=""
    fi
fi
if [[ ${VERSION} == "v487"* ]]; then
    ANALYSISTYPE=""
    DIRRECOTYPE=""
fi

echo "Analysis of ${SOURCE} for Eventdisplay Version ${VERSION}"
DDIR=${VERITAS_USER_DATA_DIR}/analysis/Results/${VERSION}/${ANALYSISTYPE}/SourceTests//${SOURCE}/${EPOCH}/
echo "Results are written to ${DDIR}"
MSCWDIR="${VERITAS_USER_DATA_DIR}/analysis/Results/${VERSION}/${ANALYSISTYPE}/mscw${DIRRECOTYPE}/"
MSCWDIR="$VERITAS_DATA_DIR/processed_data_v490/${ANALYSISTYPE}/mscw/"
SDIR=$(pwd)

if [[ ! -e ${SDIR}/${SOURCE}/runlist_releaseTesting_${EPOCH}.dat ]]; then
    echo "Runlist for epoch $EPOCH not found: ${SDIR}/${SOURCE}/runlist_releaseTesting_${EPOCH}.dat"
    exit
fi

cd ${EVNDISPSCRIPTS} || exit

if [ ${ANATYPE} == "ANASUM_SUB" ]; then
       ./ANALYSIS.anasum_parallel_from_runlist.sh \
           ${SDIR}/${SOURCE}/runlist_releaseTesting_${EPOCH}.dat \
           ${DDIR}/${CUT} \
           ${CUT} ${BCKMODEL} \
           ${SDIR}/runparameter.dat \
           ${MSCWDIR} ${V2DL3_PATH}

elif [ ${ANATYPE} == "ANASUM_FFF" ] ; then
       ./ANALYSIS.anasum_combine.sh \
           ${SDIR}/${SOURCE}/runlist_releaseTesting_${EPOCH}.dat \
           ${DDIR}/${CUT} \
           anasum.combined.root \
           ${SDIR}/runparameter.dat

fi

cd ${SDIR}
