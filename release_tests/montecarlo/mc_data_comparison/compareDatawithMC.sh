#!/bin/bash

# run script for data - MC comparison
#
# requires:
# - MC files for each minor epoch
# - Crab results for each minor epoch (read from Crab run lists; used pre-processed data)

set -e

if [[ $# != 3 ]]; then
echo "
  ./compareDatawithMC.sh <run parameter file> <SZE/MZE/LZE/WOBBLE> <comparison config>
  --> choose zenith angle / wobble range
      SZE: small zenith angles (0.5 deg wobble)
      MZE: medium large zenith angles (0.5 deg wobble)
      LZE: large zenith angles (0.5 deg wobble)
      WOBBLE: large wobble offsets (MC at 1 deg wobble)

  Input are MC and Crab mscw files.
"
exit 1
fi

###########################
# read run parameter file
if [[ ! -e ${1} ]]; then
   echo "Error, run parameter file not found: ${1}"
   exit 1
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
# Hardwired MC epoch for major-epoch (non-minor-epoch) run lists.
# The data run-list epoch and output names remain V6, but the MC files come
# from this minor epoch.
NON_EPOCH_MC_EPOCH="V6_2012_2013a"
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
# Read configuration as data, never as shell code. Do not inherit case settings
# from the environment, so the saved file describes the actual comparison.
CONFIG=$3
if [[ ! -f $CONFIG ]]; then
    echo "Error: comparison config not found: $CONFIG" >&2
    exit 1
fi
MC_VARIANT= MC_MSCW_DIR= RECOMETHOD= MC_XGB_SUFFIX=xgb_stereo DATA_XGB_SUFFIX=xgb_stereo
declare -A seen
while IFS= read -r line || [[ -n $line ]]; do
    [[ $line =~ ^[[:space:]]*(#|$) ]] && continue
    if [[ ! $line =~ ^[[:space:]]*([a-z_]+)[[:space:]]*=[[:space:]]*([a-zA-Z0-9_-]+)[[:space:]]*$ ]]; then
        echo "Error: invalid comparison config line: $line" >&2
        exit 1
    fi
    key=${BASH_REMATCH[1]}; value=${BASH_REMATCH[2]}
    if [[ ${seen[$key]+yes} ]]; then
        echo "Error: duplicate comparison setting: $key" >&2
        exit 1
    fi
    seen[$key]=1
    case $key in
        variant) MC_VARIANT=$value ;;
        mscw_directory) MC_MSCW_DIR=$value ;;
        reconstruction) case $value in
            DispBDT) RECOMETHOD=0 ;;
            XGB) RECOMETHOD=2 ;;
            *) echo "Error: reconstruction must be DispBDT or XGB" >&2; exit 1 ;;
        esac ;;
        mc_xgb_suffix) MC_XGB_SUFFIX=$value ;;
        data_xgb_suffix) DATA_XGB_SUFFIX=$value ;;
        *) echo "Error: unknown comparison setting: $key" >&2; exit 1 ;;
    esac
done < "$CONFIG"
if [[ ! ${MC_VARIANT:-} =~ ^[a-zA-Z0-9_-]+$ || ! ${MC_MSCW_DIR:-} =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "Error: comparison config requires variant and mscw_directory" >&2
    exit 1
fi
if [[ -z $RECOMETHOD ]]; then
    echo "Error: comparison config requires reconstruction" >&2
    exit 1
fi
for suffix in "$MC_XGB_SUFFIX" "$DATA_XGB_SUFFIX"; do
    if [[ ! $suffix =~ ^[a-zA-Z0-9_-]+$ ]]; then
        echo "Error: XGB suffix must contain only letters, numbers, underscores or hyphens: $suffix" >&2
        exit 1
    fi
done
RECONSTRUCTION="DispBDT"
RECONSTRUCTION_DIR="$RECONSTRUCTION"
if [[ $RECOMETHOD == 2 ]]; then
    RECONSTRUCTION="XGB_MC-${MC_XGB_SUFFIX}_DATA-${DATA_XGB_SUFFIX}"
    RECONSTRUCTION_DIR="XGB/MC-${MC_XGB_SUFFIX}/DATA-${DATA_XGB_SUFFIX}"
fi
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
    exit 1
fi
# Directory for mscw data files
DDIR="$VERITAS_PREPROCESSED_DATA_DIR/${ANALYSISTYPE}/mscw/"
if [[ ! -e ${DDIR} ]]; then
   echo "Error: data directory not found: $DDIR"
   exit 1
fi

# Directory with Crab run lists
CDIR="../../../../EventDisplay_Release_${VERSION}/Crab/runlists"
if [[ ! -e ${CDIR} ]]; then
   echo "Error: directory with Crab run lists not found: $CDIR"
   exit 1
fi

# output directory for MC/Data comparison
BDIR="../../../../EventDisplay_Release_${VERSION}/mc_data_comparison/${ANALYSISTYPE}${DIRRECOTYPE}/${SIMTYPE}/MC-${MC_VARIANT}/${RECONSTRUCTION_DIR}"
mkdir -p "$BDIR"
BDIR=$(readlink -f "$BDIR")
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
    MC_EPOCH="${I}"
    if [[ "${I}" == "V6" ]]; then
        MC_EPOCH="${NON_EPOCH_MC_EPOCH}"
    fi
    # Crab NSB level (depends on epoch)
    # If CRAB_NSB is omitted, use the per-epoch value as well. This supports
    # parameter files whose EPOCH lines already contain the NSB value.
    if [[ -z "${CRABNSB}" || $CRABNSB == "NOTSET" ]]; then
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
        echo "Processing $I $A ${atm} $REDHV (MC epoch ${MC_EPOCH})"

        # Crab run lists. If both atmosphere-specific and generic lists exist,
        # analyse both. Generic-list output gets a distinct suffix below.
        RUNLISTS=()
        RUNLISTTAGS=()
        if [[ $ELE = "WOBBLE" ]]; then
            RUNLISTS+=("$CDIR/runlist_releaseTesting${I}${REDHV}_${ELE}.dat")
            RUNLISTTAGS+=("")
        else
            ATM_RUNLIST="$CDIR/runlist_releaseTesting${I}${REDHV}_ATM${atm}_${ELE}_0.5deg.dat"
            if [[ ! -f "$ATM_RUNLIST" ]]; then
                ATM_RUNLIST="$CDIR/runlist_releaseTesting${I}${REDHV}_ATM${atm}_${ELE}.dat"
            fi
            if [[ -f "$ATM_RUNLIST" ]]; then
                RUNLISTS+=("$ATM_RUNLIST")
                RUNLISTTAGS+=("")
            fi

            GENERIC_RUNLIST="$CDIR/runlist_releaseTesting${I}${REDHV}_${ELE}_0.5deg.dat"
            if [[ ! -f "$GENERIC_RUNLIST" ]]; then
                # Major-epoch or combined lists may not carry the 0.5deg suffix,
                # e.g. runlist_releaseTestingV6_SZE.dat.
                GENERIC_RUNLIST="$CDIR/runlist_releaseTesting${I}${REDHV}_${ELE}.dat"
            fi
            if [[ -f "$GENERIC_RUNLIST" ]]; then
                RUNLISTS+=("$GENERIC_RUNLIST")
                RUNLISTTAGS+=("_ALL")
            fi
        fi

        if [[ ${#RUNLISTS[@]} -eq 0 ]]; then
            RUNLISTS+=("$CDIR/runlist_releaseTesting${I}${REDHV}_${ELE}_0.5deg.dat")
            RUNLISTTAGS+=("")
        fi

        for RUNLIST_INDEX in "${!RUNLISTS[@]}"
        do
            RUNLIST="${RUNLISTS[RUNLIST_INDEX]}"
            RUNLISTTAG="${RUNLISTTAGS[RUNLIST_INDEX]}"
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

            # Name MC conditions and the selected Crab runlist separately.
            DATASET="data-generic-runlist"
            if [[ "$RUNLIST" == *"_ATM${atm}_"* ]]; then
                DATASET="data-ATM${atm}"
            fi
            if [[ $SIMTYPE == "CARE_RedHV"* ]]; then
                SIMATM="61"
            fi
            CONFIGDIR="${BDIR}/${I}_MC-ATM${SIMATM}_${ELE}_wobble${MCWOFF}_NSB${NSB}/${DATASET}"
        SIMMSCW="$MC_MSCW_DIR"
        MCFILE="$SIMDIR/${MC_EPOCH}_ATM${SIMATM}_gamma/${SIMMSCW}/${simfile}"
        if [[ ! -f "$MCFILE" ]]; then
            echo "Error: MC mscw file not found: $MCFILE" >&2
            exit 1
        fi
        MCFILE=$(readlink -f "$MCFILE")
        MCFRIEND="${MCFILE%.mscw.root}.mscw.${MC_XGB_SUFFIX}.root"
        if [[ $RECOMETHOD == 2 && ! -f "$MCFRIEND" ]]; then
            echo "Error: MC XGB stereo file not found: $MCFRIEND" >&2
            exit 1
        fi
        mkdir -p "$(dirname "$CONFIGDIR")"
        if ! mkdir "$CONFIGDIR" 2>/dev/null; then
            echo "Error: output directory already exists: $CONFIGDIR (move or remove it before resubmitting)" >&2
            exit 1
        fi
        ODIR="$CONFIGDIR"
        PLOTLABEL="comparison_MC-${MC_VARIANT}_${RECONSTRUCTION}_${DATASET}"
        echo "Comparison output: $ODIR"
        mkdir -p "$ODIR/tmp"
        cp "$RUNLIST" "$ODIR/crab-runlist.dat"
        printf 'MC variant: %s\nMC directory: %s\nMC file: %s\nMC XGB friend: %s\nData XGB suffix: %s\nReconstruction: %s\nCrab runlist: %s\n' \
            "$MC_VARIANT" "$SIMMSCW" "$MCFILE" "$([[ $RECOMETHOD == 2 ]] && printf '%s' "$MCFRIEND" || printf 'not used')" "$DATA_XGB_SUFFIX" "$RECONSTRUCTION" "$(readlink -f "$RUNLIST")" > "$ODIR/comparison-settings.txt"
        cp "$RUNPAR" "$ODIR/input-runparameter.dat"
        cp "$CONFIG" "$ODIR/comparison.conf"

        # tmp mscw file in output directory
        # Each result has its own staging directory and Condor logs.
        DMSCWDIR=${ODIR}/tmp
        mkdir -p "$DMSCWDIR"
        DFILES=$(cat "$RUNLIST")
        for D in $DFILES; do
            if ! MSCWFILE=$(get_mscw_file "$DDIR" "$D"); then
                echo "Error: mscw file not found for run ${D} in ${DDIR}"
                exit 1
            fi
            ln -s -f "${MSCWFILE}" "$DMSCWDIR"/"$D".mscw.root
            printf 'Data mscw: %s\n' "$(readlink -f "$MSCWFILE")" >> "$ODIR/comparison-settings.txt"
            if [[ ${RECOMETHOD} -eq 2 ]]; then
                XGBFILE="${MSCWFILE%.mscw.root}.mscw.${DATA_XGB_SUFFIX}.root"
                if [[ ! -e "${XGBFILE}" ]]; then
                    echo "Error: XGB stereo file not found for run ${D}: ${XGBFILE}"
                    exit 1
                fi
                ln -s -f "${XGBFILE}" "$DMSCWDIR"/"$D".mscw."${DATA_XGB_SUFFIX}".root
                printf 'Data XGB friend: %s\n' "$(readlink -f "$XGBFILE")" >> "$ODIR/comparison-settings.txt"
            fi
        done
        echo "TEMP DIRECTORY (to be deleted by hand): $DMSCWDIR"

        # runparameter file
        RUNPARAMETER="$DMSCWDIR/mcdatacomparison.runparameter"
        echo "Runparameter file $RUNPARAMETER"

        # write run parameter file
        echo "* SIMS $MCFILE 4 ${MCWOFF} 0. 0. 0. ${ZEMIN} ${ZEMAX}" > "$RUNPARAMETER"
        echo "* ON ${DMSCWDIR}/[0-9]*.mscw.root 4 -99. -99. 0. 360. ${ZEMIN} ${ZEMAX}" >> "$RUNPARAMETER"
        echo "* OFF ${DMSCWDIR}/[0-9]*.mscw.root 4 -99. -99. 0. 360. ${ZEMIN} ${ZEMAX}" >> "$RUNPARAMETER"

        cp "$RUNPARAMETER" "$ODIR/mcdatacomparison.runparameter"
        FSCRIPT="$DMSCWDIR/compareDatawithMC_qsub_${SIMTYPE}_${I}${A}${RUNLISTTAG}_${ELE}_${MCWOFF}_${NSB}"
        rm -f ${FSCRIPT}.sh
        sed -e "s|OUTDIR|$ODIR|" \
            -e "s|EEPOCHTM|${MC_EPOCH}_ATM${SIMATM}|" \
            -e "s|CURRENTDIR|$PWDIR|" \
            -e "s|RUNPARAMETERFILE|$RUNPARAMETER|" \
            -e "s|PLOTLABEL|$PLOTLABEL|" \
            -e "s|MCXGBSUFFIX|$MC_XGB_SUFFIX|" \
            -e "s|DATAXGBSUFFIX|$DATA_XGB_SUFFIX|" \
            -e "s|METHODRECO|$RECOMETHOD|" compareDatawithMC_qsub.sh > ${FSCRIPT}.sh

        echo "Run script: $FSCRIPT"
        chmod u+x $FSCRIPT.sh

        $EVNDISPSCRIPTS/helper_scripts/UTILITY.condorSubmission.sh ${FSCRIPT}.sh 4000M 10G
        condor_submit ${FSCRIPT}.sh.condor

        done
    done
done
