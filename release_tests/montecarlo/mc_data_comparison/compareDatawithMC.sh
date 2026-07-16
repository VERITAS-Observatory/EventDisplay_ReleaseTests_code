#!/bin/bash

# run script for data - MC comparison
#
# requires:
# - MC files for each minor epoch
# - Crab results for each minor epoch (read from Crab run lists; used pre-processed data)

set -e

if [[ $# < 2 ]]; then
echo "
  ./compareDatawithMC.sh <run parameter file> <SZE/MZE/LZE/WOBBLE>
  --> choose zenith angle / wobble range
      SZE: small zenith angles (0.5 deg wobble)
      MZE: medium large zenith angles (0.5 deg wobble)
      LZE: large zenith angles (0.5 deg wobble)
      WOBBLE: large wobble offsets (MC at 1 deg wobble)

  Input are MC and Crab mscw files.
"
exit
fi

###########################
# read run parameter file
if [[ ! -e ${1} ]]; then
   echo "Error, run parameter file not found: ${1}"
   exit
fi
RUNPAR="${1}"
# Eventdisplay version
VERSION=$(awk '$1 == "*" && $2 == "VERSION" {print $3; exit}' "${RUNPAR}")
# Simulation type
SIMTYPE=$(awk '$1 == "*" && $2 == "SIMTYPE" {print $3; exit}' "${RUNPAR}")
# Atmosphere
ATMOS=($(awk '$1 == "*" && $2 == "ATMOSPHERE" {print $3}' "${RUNPAR}"))
# Epochs
EPOCH=($(awk '$1 == "*" && $2 == "EPOCH" {print $3}' "${RUNPAR}"))
# Wobble (default observing; WOBBLE mode fixed to 1 deg)
MCWOFF="0.5"
# Crab NSB level
CRABNSB=$(awk '$1 == "*" && $2 == "CRAB_NSB" {print $3; exit}' "${RUNPAR}")
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
# Stereo reconstruction method
# (0: dispBDT, 2: XGB)
RECOMETHOD=0
###########################

# elevation range
[[ "$2" ]] && ELE=$2 || ELE="SZE"
case "$ELE" in
    SZE|MZE|LZE|WOBBLE)
        ;;
    *)
        echo "Error: invalid elevation/wobble selection '${ELE}' (expected SZE, MZE, LZE, or WOBBLE)"
        exit 1
        ;;
esac
# Directory for simulations
SIMDIR=${VERITAS_IRFPRODUCTION_DIR}/${VERSION}/${ANALYSISTYPE}/$SIMTYPE/
if [[ ! -e ${SIMDIR} ]]; then
    echo "Error: simulation directory not found: $SIMDIR"
    exit
fi
# Directory for mscw data files
DDIR="$VERITAS_PREPROCESSED_DATA_DIR/${ANALYSISTYPE}/mscw/"
if [[ ! -e ${DDIR} ]]; then
   echo "Error: data directory not found: $DDIR"
   exit
fi

# Directory with Crab run lists
CDIR="../../../../EventDisplay_Release_${VERSION}/Crab/runlists"
if [[ ! -e ${CDIR} ]]; then
   echo "Error: directory with Crab run lists not found: $CDIR"
   exit
fi

# output directory for MC/Data comparison
BDIR="../../../../EventDisplay_Release_${VERSION}/mc_data_comparison/${ANALYSISTYPE}${DIRRECOTYPE}/${SIMTYPE}/"
mkdir -p ${BDIR}
BDIR=$(readlink -f "../../../../EventDisplay_Release_${VERSION}/mc_data_comparison/${ANALYSISTYPE}${DIRRECOTYPE}/${SIMTYPE}/")
echo "Results will be written to $BDIR"

PWDIR=$(pwd)

get_mscw_file()
{
    data_dir="${1}"
    runn="${2}"
    local direct_file="${data_dir}/${runn}.mscw.root"
    local edir=""
    local nested_file=""

    if [[ -e "${direct_file}" ]]; then
        echo "${direct_file}"
        return 0
    fi

    if [[ ${runn} -lt 100000 ]]; then
        edir="${data_dir}/${runn:0:1}"
    else
        edir="${data_dir}/${runn:0:2}"
    fi
    nested_file="${edir}/${runn}.mscw.root"
    if [[ -e "${nested_file}" ]]; then
        echo "${nested_file}"
        return 0
    fi

    return 1
}

for I in "${EPOCH[@]}"
do
    # ignore major epoch
    if [[ $I == "V6" ]]; then
       continue
    fi
    # Crab NSB level (depends on epoch)
    if [[ $CRABNSB == "NOTSET" ]]; then
        NSB=$(awk -v epoch="${I}" '$1 == "*" && $2 == "EPOCH" && $3 == epoch {print $4; exit}' "${RUNPAR}")
    else
        NSB=${CRABNSB}
    fi
    if [[ -z "${NSB}" ]]; then
        echo "Error: no NSB value found for epoch ${I} in ${RUNPAR}"
        exit 1
    fi
    # Simulation file (elevation dependent)
    if [[ $ELE = "SZE" ]]
    then
        simfile="20deg_${MCWOFF}wob_NOISE${NSB}.mscw.root"
        ZEMIN="0."
        ZEMAX="25."
    elif [[ $ELE = "MZE" ]]
    then
        simfile="45deg_${MCWOFF}wob_NOISE${NSB}.mscw.root"
        ZEMIN="40."
        ZEMAX="50."
    elif [[ $ELE = "LZE" ]]
    then
        ZEMIN="50."
        ZEMAX="70."
        simfile="55deg_${MCWOFF}wob_NOISE${NSB}.mscw.root"
    # wobble set (everything not 0.5 deg)
    # - using only summer
    else
        simfile="20deg_1.0wob_NOISE${NSB}.mscw.root"
        ZEMIN="0."
        ZEMAX="25."
        ATMOS=( 61 )
        MCWOFF="1.0"
    fi
    for atm in "${ATMOS[@]}"
    do
        if [[ ${I: -1} == "w" ]] && [[ ${atm} == *"62"* ]]; then
           continue
        elif [[ ${I: -1} == "s" ]] && [[ ${atm} == *"61"* ]]; then
           continue
        fi

        A="_ATM${atm}"
        if [[ $ELE == "WOBBLE" ]]; then
           A=""
        fi
        REDHV=""
        if [[ $SIMTYPE == "CARE_RedHV"* ]]; then
            REDHV="_redHV"
        fi
        SIMATM="${atm}"
        echo "Processing $I $A ${atm} $REDHV"

        # Crab run list
        RUNLIST="$CDIR/runlist_releaseTesting${I}${REDHV}_${ELE}_0.5deg.dat"
        if [[ $ELE = "WOBBLE" ]]; then
            RUNLIST="$CDIR/runlist_releaseTesting${I}${REDHV}_${ELE}.dat"
        fi
        echo "RUNLIST $RUNLIST"
        if [[ ! -f "$RUNLIST" ]]; then
            echo "..not found, skipping"
            continue
        fi
        NFIL=$(wc -l < "$RUNLIST")
        if [ "$NFIL" -lt 3 ]; then
            echo "..not enough runs ($NFIL), skipping"
            continue
        fi

        # output directory
        ODIR=${BDIR}/${I}${A}_${ELE}_${MCWOFF}_${NSB}
        mkdir -p ${ODIR}

        # tmp mscw file in output directory
        DMSCWDIR=${ODIR}/tmp/$(uuidgen)
        mkdir -p "$DMSCWDIR"
        DFILES=$(cat $RUNLIST)
        for D in $DFILES; do
            if ! MSCWFILE=$(get_mscw_file "$DDIR" "$D"); then
                echo "Error: mscw file not found for run ${D} in ${DDIR}"
                exit 1
            fi
            ln -s -f "${MSCWFILE}" "$DMSCWDIR"/"$D".mscw.root
        done
        echo "TEMP DIRECTORY (to be deleted by hand): $DMSCWDIR"

        # runparameter file
        if [[ -e $ODIR/mcdatacomparison.runparameter ]]
        then
            rm -f $ODIR/mcdatacomparison.runparameter
        fi
        echo "Runparameter file $ODIR/mcdatacomparison.runparameter"
        SIMMSCW="MSCW_RECID0${DIRRECOTYPE}"

        # write run parameter file
        if [[ $SIMTYPE == "CARE_RedHV"* ]]; then
            SIMATM="61"
            echo "* SIMS $SIMDIR/${I}_ATM${SIMATM}_gamma/${SIMMSCW}/${simfile} 4 ${MCWOFF} 0. 0. 0. ${ZEMIN} ${ZEMAX}" > $ODIR/mcdatacomparison.runparameter
        else
            echo "* SIMS $SIMDIR/${I}_ATM${SIMATM}_gamma/${SIMMSCW}/${simfile} 4 ${MCWOFF} 0. 0. 0. ${ZEMIN} ${ZEMAX}" > $ODIR/mcdatacomparison.runparameter
        fi
        echo "* ON ${DMSCWDIR}/[0-9]*.mscw.root 4 -99. -99. 0. 360. ${ZEMIN} ${ZEMAX}" >> $ODIR/mcdatacomparison.runparameter
        echo "* OFF ${DMSCWDIR}/[0-9]*.mscw.root 4 -99. -99. 0. 360. ${ZEMIN} ${ZEMAX}" >> $ODIR/mcdatacomparison.runparameter
        echo "   run parameter file: $ODIR/mcdatacomparison.runparameter"

        FSCRIPT="$DMSCWDIR/compareDatawithMC_qsub_${SIMTYPE}_${I}${A}_${ELE}_${MCWOFF}_${NSB}"
        rm -f ${FSCRIPT}.sh
        sed -e "s|OUTDIR|$ODIR|" \
            -e "s|EEPOCHTM|${I}_ATM${SIMATM}|" \
            -e "s|CURRENTDIR|$PWDIR|" \
            -e "s|METHODRECO|$RECOMETHOD|" compareDatawithMC_qsub.sh > ${FSCRIPT}.sh

        echo "Run script: $FSCRIPT"
        chmod u+x $FSCRIPT.sh

        $EVNDISPSCRIPTS/helper_scripts/UTILITY.condorSubmission.sh ${FSCRIPT}.sh 4000M 10G
        condor_submit ${FSCRIPT}.sh.condor

    done
done
