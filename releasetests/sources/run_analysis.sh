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

if [[ $# < 2 ]]; then
echo "
  ./run_analysis.sh <runparameter file> <SOURCE> <TYPE> <CUT> [V2DL3_PATH] [GAMMAPY_SCRIPT]

   analysis types:
       EVNDISP
       MSCW
       ANASUM_SUB
       ANASUM_FFF
       V2DL3
       GAMMAPY
       VALIDATION_PLOT

   cuts: (i.e., moderate2tel, soft2tel, hard3tel)
"
exit
fi

SOURCE=${2}
ANATYPE=${3}
CUT=${4}
[[ "$5" ]] && V2DL3_PATH=$5 || V2DL3_PATH=""
[[ "$6" ]] && GAMMAPY_SCRIPT=$6 || GAMMAPY_SCRIPT=""

BCKMODEL="RE"
BCKMODEL="IGNOREACCEPTANCE"
BCKMODEL="IGNOREIRF"
EPOCH="V6"

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
# Bright star catalog
CATALOG=($(grep BRIGHTSTARCATALOGUE ${1} | grep "*" | awk '{print $3}'))

echo "Analysis of ${SOURCE} for Eventdisplay Version ${VERSION}"
DDIR=${VERITAS_USER_DATA_DIR}/analysis/Results/${VERSION}/${ANALYSISTYPE}/SourceTests/${SOURCE}/
echo "Results are written to ${DDIR}"
EVDIR=${VERITAS_USER_DATA_DIR}/analysis/Results/${VERSION}/${ANALYSISTYPE}/
MSCWDIR="${VERITAS_USER_DATA_DIR}/analysis/Results/${VERSION}/${ANALYSISTYPE}/mscw${DIRRECOTYPE}/"
SDIR=`pwd`

cd ${EVNDISPSCRIPTS}

if [[ ${ANATYPE} == "EVNDISP" ]]; then
   ./ANALYSIS.evndisp.sh ${SDIR}/${SOURCE}/runlist_releaseTesting_${EPOCH}.dat ${DDIR}/evndisp

elif [[ ${ANATYPE} == "MSCW" ]]; then
   ./ANALYSIS.mscw_energy.sh ${SDIR}/${SOURCE}/runlist_releaseTesting_${EPOCH}.dat ${EVDIR}/evndisp ${MSCWDIR}

elif [ ${ANATYPE} == "ANASUM_SUB" ]; then
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

elif [ ${ANATYPE} == "V2DL3" ] ; then
    if [[ -d ${V2DL3_PATH} ]]; then
        export PYTHONPATH=$PYTHONPATH:"${V2DL3_PATH}"
        ${DDIR}/${CUT}/v2dl3_from_runlist_${CUT}.sh
    else
        echo "error: V2DL3 path not given"
        exit
    fi

elif [ "$ANATYPE" == "INDEX" ]; then
    if [[ -d ${V2DL3_PATH} ]]; then
        export PYTHONPATH=$PYTHONPATH:"${V2DL3_PATH}"
        source activate base
        conda activate v2dl3Eventdisplay
        python ${V2DL3_PATH}/pyV2DL3/script/generate_index_file.py \
             -f ${DDIR}/${CUT} \
             -i ${DDIR}/${CUT} -r
        conda deactivate
    else
        echo "error: V2DL3 path not given"
        exit 
    fi

elif [ ${ANATYPE} == "GAMMAPY" ] ; then
     if [[ -d ${GAMMAPY_SCRIPT} ]]; then
         source activate base
         conda activate gammapy-0.20.1
         python ${GAMMAPY_SCRIPT}/compare_spectra.py \
             -d ${DDIR}/${CUT} \
             -t release_test_${SOURCE}_${CUT} \
             -r ${DDIR}/${CUT}/Eventdisplay_${SOURCE}_${CUT}_SpecPoints.csv \
             -o ${DDIR}/${CUT} \
             -c ${VERITAS_EVNDISP_AUX_DIR}/AstroData/Catalogues/${CATALOG} \
             -p ${SDIR}/${SOURCE}/gammapy_analysis_parameter.yaml \
             -z NONE \
             -s ${CUT}
         conda deactivate
      else
          echo "error: GAMMAPY script path not given"
      fi

elif [ ${ANATYPE} == "VALIDATION_PLOT" ] ; then
     if [[ -d ${GAMMAPY_SCRIPT} ]]; then
        source activate base
        conda activate gammapy-0.20.1
        python ${GAMMAPY_SCRIPT}/plot_all_spec_comparison.py \
              ${DDIR}/${CUT}/Eventdisplay_${SOURCE}_${CUT} \
              ${DDIR}/${CUT}/release_test_${SOURCE}_${CUT} \
              release_test_${SOURCE}_${CUT} \
              ${DDIR}/${CUT} \
              ${SDIR}/${SOURCE}/gammapy_analysis_parameter.yaml \
              NONE \
              ${CUT} \
              ${VERSION}
       conda deactivate
     else
         echo "error: GAMMAPY script path not given"
     fi
elif [ ${ANATYPE} == "ALL_RESULTS" ]; then
    if [[ ! -e ${DDIR}/${CUT}/anasum.combined.log ]]; then
        echo "ANASUM result not found in ${DDIR}/${CUT}/anasum.combined.log"
        return
    fi
    RESULT=$(grep "ALL RUNS" ${DDIR}/${CUT}/anasum.combined.log)
    echo "ALL_RESULTS ${RESULT/ALL RUNS/v490}"
elif [ ${ANATYPE} == "COPY_RESULTS" ]; then
    if [[ -e ${DDIR}/${CUT}/anasum.combined.log ]]; then
        ODIR="${VERITAS_USER_DATA_DIR}/analysis/Results/${VERSION}/${ANALYSISTYPE}/SourceTests/anasum.combined/${SOURCE}"
        mkdir -p ${ODIR}/${CUT}
        cp -v ${DDIR}/${CUT}/anasum.combined.log ${ODIR}/${CUT}
    fi
else
        echo "error: ANALYSIS type not given"
fi

cd ${SDIR}
