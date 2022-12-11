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

###
# V2DL3: run v2dl3 for each anasum rootfile
#      - set python path to V2DL3 directory
#      - run v2dl3
#      - generate IACT storage for all runs in the anasum directory at the end
# 
# GAMMAPY: runs gammapy analysis
#      - run python script
#
# VALIDATION_PLOT: to plot the eventdisplay and Gammapy comparision plots 
#      - run python script
###


set -e

if [[ $# < 2 ]]; then
echo "
  ./anasum_yearly.sh <runparameter file> SUB <SZE/MZE/LZE/WOBBLE> <RE/RB/IGNOREACCEPTANCE> [V2DL3_PATH]
  --> Step 1 to analyse run-wise with anasum

  ./anasum_yearly.sh <runparameter file> FFF <SZE/MZE/LZE/WOBBLE> <RE/RB/IGNOREACCEPTANCE> [V2DL3_PATH]
  --> Step 2 to combine anasum file

  ./anasum_yearly.sh <runparameter file> V2DL3 <SZE/MZE/LZE/WOBBLE> <RE/RB/IGNOREACCEPTANCE> <V2DL3_PATH>
  --> Step 3 to convert anasum files to V2DL3 
  (or use UTILITY.condorSubmission.sh script for cluster submission)

  ./anasum_yearly.sh <runparameter file> INDEX <SZE/MZE/LZE/WOBBLE> <RE/RB/IGNOREACCEPTANCE> <V2DL3_PATH>
  --> Step 4 to generate INDEX files for gammapy analysis 

  ./anasum_yearly.sh <runparameter file> GAMMAPY <SZE/MZE/LZE/WOBBLE> <RE/RB/IGNOREACCEPTANCE>
  --> Step 5 to analyse DL3 products with gammapy (spectral analysis)

  ./anasum_yearly.sh <runparameter file> VALIDATION_PLOT <SZE/MZE/LZE/WOBBLE> <RE/RB/IGNOREACCEPTANCE>
  --> Step 6 to prepare plots comparing Eventdisplay and Gammapy results
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
ANALYSISTYPE=$(grep ANALYSISTYPE ${1} | grep "*" | awk '{print $3}')
# eventdisplay version --> defines script directory
EDVERSION=$($EVNDISPSYS/bin/evndisp --version | tr -d .)
EDVERSION=${EDVERSION:1}
echo ${EDVERSION}
# directory with scripts and cuts
if [[ $EDVERSION -lt "485" ]]; then
  SCRIPTDIR=$EVNDISPSYS/scripts/VTS/
else
  SCRIPTDIR=${EVNDISPSCRIPTS}
fi
# Epochs
MEPOCH=$(grep MAJOREPOCH ${1} | grep "*" | awk '{print $3}')
EPOCH=($(grep EPOCH ${1} | grep "*" | grep -v MAJOR | awk '{print $3}'))
# Atmopsphere
ATMOS=($(grep ATMOSPHERE ${1} | grep "*" | awk '{print $3}'))
# CUTS
CUTS=($(grep CUT ${1} | grep "*"| awk '{print $4}'))
# Source name
OBJECT=($(grep SOURCE ${1} | grep "*" | awk '{print $3}'))
# Bright star catalog
CATALOG=($(grep BRIGHTSTARCATALOGUE ${1} | grep "*" | awk '{print $3}'))
# Minimum brightness of stars
BRIGHTSTARSETTINGS=($(grep BRIGHTSTARSETTINGS ${1} | grep "*" | awk '{print $3}'))

#########################
# run mode
MODE=$2
# Directory for data files
DDIR="$VERITAS_USER_DATA_DIR/analysis/Results/${VERSION}/${ANALYSISTYPE}/${OBJECT}/"
echo $DDIR
SDIR=`pwd`

# Directory with run lists
RDIR=`pwd`
# elevation range

[[ "$3" ]] && ELE=$3 || ELE="SZE"
[[ "$4" ]] && BCK=$4 || BCK="RE"

[[ "$5" ]] && V2DL3_PATH=$5 || V2DL3_PATH="NOTSET"
[[ "$6" ]] && GAMMAPY_SCRIPT=$6 || GAMMAPY_SCRIPT="$(pwd)"

# mscw_energy subdirectory
# (old style scripts: "evndisp/RecID0")
MSCWSDIR="mscw_energy"
FORCEDATMO=""
# forced for redHV (only available for ATM61)
if [[ ${MEPOCH} == *"redHV"* ]]
then
    FORCEDATMO="61"
fi

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
        if [[ ! -z ${ATM} ]]; then
           ATM="_ATM${ATM}"
        fi
        echo "Processing $I ($ELE $ATM $BCK $FORCEDATMO)"

        MDIR="$DDIR/${MSCWSDIR}_${I}${ATM}_${ELE}"
        if [[ ! -d ${MDIR} ]]; then
           MDIR=${MDIR/mscw_energy/mscw}
           if [[ ! -d ${MDIR} ]]; then
              echo "error: data directory not found: ${MDIR}"
              echo "continuing..."
              continue
           fi
        fi
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
                            ${V2DL3_PATH} \
                            DEFAULT 0 $FORCEDATMO
             elif [ "$MODE" == "FFF" ] ; then
                 if [[ ! -e ${ANASUMDIR} ]]; then
                     echo "error: no anasum directory with files to be combined"
                     echo "continuing..."
                     continue
                 fi
                 echo "  combining files from ${ANASUMDIR}/${C}.anasum.dat"
                 ./ANALYSIS.anasum_combine.sh \
                            ${ANASUMDIR}/${C}.anasum.dat \
                            $ANASUMDIR \
                            anasum.combined.root \
                            $RDIR/runparameter.dat
             elif [ "$MODE" == "V2DL3" ]; then
                 if [[ -d ${V2DL3_PATH} ]]; then
                     export PYTHONPATH=$PYTHONPATH:"${V2DL3_PATH}"
                     ${ANASUMDIR}/v2dl3_from_runlist_${C}.sh
                 else
                     echo "error: V2DL3 path not given"
                     exit
                 fi
             elif [ "$MODE" == "INDEX" ]; then
                 if [[ -d ${V2DL3_PATH} ]]; then
                     export PYTHONPATH=$PYTHONPATH:"${V2DL3_PATH}"
                     source activate base
                     conda activate v2dl3Eventdisplay
                     python ${V2DL3_PATH}/pyV2DL3/script/generate_index_file.py \
                         -f ${ANASUMDIR} \
                         -i ${ANASUMDIR} -r
                     conda deactivate
                 else
                     echo "error: V2DL3 path not given"
                     exit
                 fi
             elif [ "$MODE" == "GAMMAPY" ]; then
                 if [[ -d ${GAMMAPY_SCRIPT} ]]; then
                     source activate base
                     conda activate gammapy-0.20.1
                     python ${GAMMAPY_SCRIPT}/compare_spectra.py \
                         -d ${ANASUMDIR} \
                         -t release_test_${C}_${I}${ATM} \
                         -r ${ANASUMDIR}/Eventdisplay_${I}${ATM}_SpecPoints.csv \
                         -o ${ANASUMDIR} \
                         -c ${VERITAS_EVNDISP_AUX_DIR}/AstroData/Catalogues/${CATALOG} \
                         -p ${SDIR}/gammapy_analysis_parameter.yaml \
                         -z ${ELE} \
                         -s ${C}
                     conda deactivate
                 else
                     echo "error: GAMMAPY script path not given"
                 fi
             elif [ "$MODE" == "VALIDATION_PLOT" ]; then
                 if [[ -d ${GAMMAPY_SCRIPT} ]]; then
                     source activate base
                     conda activate gammapy-0.20.1
                     python ${GAMMAPY_SCRIPT}/plot_all_spec_comparison.py \
                            ${ANASUMDIR}/Eventdisplay_${I}${ATM} \
                            ${ANASUMDIR}/release_test_${C}_${I}${ATM} \
                            release_test_${C}_${I}${ATM} \
                            ${ANASUMDIR} \
                            ${SDIR}/gammapy_analysis_parameter.yaml \
                            ${ELE} \
                            ${C}  \
                            ${EDVERSION}
                     conda deactivate
                 else
                     echo "error: GAMMAPY script path not given"
                     exit
                 fi
             fi
       done
    done
done


