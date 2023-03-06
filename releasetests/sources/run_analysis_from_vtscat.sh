# run release testing analysis using
# VTSCat runlists
#

if [[ $# < 2 ]]; then
echo "
  ./run_analysis_from_vtscat.sh <runparameter file> <ANASUM_SUB/ANASUM_FFF> <CUT> <paper directory>

   analysis types:
       ANASUM_SUB
       ANASUM_FFF

   for cuts: (i.e., moderate2tel, soft2tel, hard3tel)
"
exit
fi

ANATYPE=${2}
CUT=${3}
PDIR=${4}
BCKMODEL="RE"
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
# Bright star catalog
CATALOG=($(grep BRIGHTSTARCATALOGUE ${1} | grep "*" | awk '{print $3}'))

# SOURCE == Paper DIR
SOURCE=$(basename "$PDIR")

echo "Analysis of ${SOURCE} for Eventdisplay Version ${VERSION}"
DDIR=${VERITAS_USER_DATA_DIR}/analysis/Results/${VERSION}/${ANALYSISTYPE}/SourceTests/${SOURCE}/
echo "Results are written to ${DDIR}"
MSCWDIR=${DDIR}
MSCWDIR="${VERITAS_USER_DATA_DIR}/analysis/Results/${VERSION}/${ANALYSISTYPE}/mscw_DISP/"
SDIR=`pwd`

cd ${EVNDISPSCRIPTS}

if [ ${ANATYPE} == "ANASUM_SUB" ]; then
       ./ANALYSIS.anasum_parallel_from_runlist.sh \
           ${PDIR}/analysis/runlist_V6.dat \
           ${DDIR}/${CUT} \
           ${CUT} ${BCKMODEL} \
           ${PDIR}/analysis/runparameter.dat \
           ${MSCWDIR} ""

elif [ ${ANATYPE} == "ANASUM_FFF" ] ; then
       ./ANALYSIS.anasum_combine.sh \
           ${PDIR}/analysis/runlist_releaseTesting.dat \
           ${DDIR}/${CUT} \
           anasum.combined.root \
           ${PDIR}/analysis/runparameter.dat
fi

cd ${SDIR}
