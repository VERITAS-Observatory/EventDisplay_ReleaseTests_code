# run script for data - MC comparision
# 
# requires:
# - MC files for each minor epoch
# - Crab results for each minor epoch
# atmospheres)
#
set -e

if [[ $# < 2 ]]; then
echo "
  ./compareDatawithMC.sh <runparameter file> <SZE/MZE/LZE/WOBBLE>
  --> choose zenith angle range
  SZE: small zenith angles
  MZE: medium large zenith angles
  LZE: large zenith angles

  this script needs some adjust dependent on the atmosphere or epoch to be studied

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
# Simulation type
SIMTYPE=$(grep SIMTYPE ${1} | awk '{print $3}')
# Atmosphere
ATMOS=($(grep ATMOSPHERE ${1} | grep "*" | awk '{print $3}'))
# Epochs
EPOCH=($(grep EPOCH ${1} | grep "*" | grep -v MAJOR | awk '{print $3}'))
# Wobble
MCWOFF=$(grep MC_WOFF ${1} | awk '{print $3}')
# Crab NSB level
CRABNSB=$(grep CRAB_NSB ${1} | awk '{print $3}')
# Analysis type
ANALYSISTYPE=$(grep ANALYSISTYPE ${1} | grep "*" | awk '{print $3}')
# Direction reconstruction
DIRRECOTYPE=$(grep DIRECTION ${1} | grep "*" | awk '{print $3}')
###########################

# elevation range
[[ "$2" ]] && ELE=$2 || ELE="SZE"
# Directory for simulations
#SIMDIR=$VERITAS_USER_DATA_DIR/analysis/Results/${VERSION}/$SIMTYPE/
SIMDIR=${VERITAS_IRFPRODUCTION_DIR}/${VERSION}/${ANALYSISTYPE}/$SIMTYPE/
# SIMDIR=${VERITAS_IRFPRODUCTION_DIR}/v486/${ANALYSISTYPE}/$SIMTYPE/
if [[ ! -e ${SIMDIR} ]]; then
   # remove patch version and try again
   if [ ${#VERSION} -eq 5 ]; then
       TVERSION=${VERSION::-1}
       SIMDIR=${VERITAS_IRFPRODUCTION_DIR}/${TVERSION}/${ANALYSISTYPE}/$SIMTYPE/
   fi
   if [[ ! -e ${SIMDIR} ]]; then
       echo "Error: simulation directory not found: $SIMDIR"
       exit
   fi
fi
# Directory for data files
DDIR="$VERITAS_USER_DATA_DIR/analysis/Results/${VERSION}/${ANALYSISTYPE}/Crab/"
if [[ ! -e ${DDIR} ]]; then
   echo "Error: data directory not found: $DDIR"
   exit
fi

# output directory
BDIR="../../../../EventDisplay_ReleaseTests_${VERSION}/mc_data_comparision/${ANALYSISTYPE}/${SIMTYPE}/"
mkdir -p ${BDIR}

mkdir -p tmpdir/logdir
PWDIR=$(pwd)

for I in "${EPOCH[@]}"
do
    if [[ $I == "V6" ]]; then
       continue
    fi
    # Crab NSB level (depends on epoch)
    if [[ $CRABNSB == "NOTSET" ]]; then
        NSB=$(grep ${I} ${1} | grep -v MAJOR | awk '{print $4}')
    else
        NSB=${CRABNSB}
    fi
    # Simulation file (elevation depedent)
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
        ZEMIN="50"
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
        elif [[ ${I: -1} == "s" ]] && [[ ${A} == *"61"* ]]; then
           continue
        fi

        A="_ATM${atm}"
        if [[ $ELE == "WOBBLE" ]]; then
           A=""
        fi
        echo "Processing $I $A ${atm}"
        
        # check if data files are availabe
        MSCWS="mscw_energy"
        DMSCWDIR="${DDIR}/${MSCWS}_${I}${REDHV}${A}_${ELE}_0.5deg"
        if [[ $ELE = "WOBBLE" ]]; then
            DMSCWDIR="${DDIR}/${MSCWS}_${I}${REDHV}${A}_${ELE}"
        fi
        # make sure that files are available for the given 
        # epoch (not all epochs have Crab runs available)
        if [[ ! -d ${DMSCWDIR} ]]; then
           echo "Directory ${DMSCWDIR} not found, trying mscw directory"
           DMSCWDIR=${DMSCWDIR/mscw_energy/mscw}
            if [[ ! -d ${DMSCWDIR} ]]; then
               echo "Directory ${DMSCWDIR} not found; skipping"
               continue
            fi
        fi
        NMSWC=$(ls -1 ${DMSCWDIR}/*.mscw.root | wc -l)
        # require at least 3 runs
        echo ${DMSCWDIR} $NMSWC
        if [[ ${NMSWC} -lt 3 ]]; then
           echo "Less then 3 files found in ${DMSCWDIR}"
           continue
        else
           echo "Found ${NMSWC} mscw file in ${DMSCWDIR}"
        fi
        # output directory
        ODIR=${BDIR}/${I}${A}_${ELE}_${MCWOFF}_${NSB}
        mkdir -p ${ODIR}

        # runparameter file
        if [[ -e $ODIR/mcdatacomparison.runparameter ]]
        then
            rm -f $ODIR/mcdatacomparison.runparameter
        fi 
        REDHV=""
        if [[ $SIMTYPE == "CARE_RedHV" ]]; then
            REDHV="_redHV"
        fi

        if [[ $DIRRECOTYPE == "DISP" ]]; then
            SIMMSCW="MSCW_RECID0_DISP"
        else
            SIMMSCW="MSCW_RECID0"
        fi

        # write run parameter file
        if [[ $SIMTYPE == "CARE_RedHV" ]]; then
            echo "* SIMS $SIMDIR/${I}_ATM61_gamma/${SIMMSCW}/${simfile} 4 ${MCWOFF} 0. 110. 250. ${ZEMIN} ${ZEMAX}" > $ODIR/mcdatacomparison.runparameter
        else
            if [[ $ELE == "WOBBLE" ]] && [[ ${I: -1} == "s" ]]; then
                echo "* SIMS $SIMDIR/${I}_ATM62_gamma/${SIMMSCW}/${simfile} 4 ${MCWOFF} 0. 110. 250. ${ZEMIN} ${ZEMAX}" > $ODIR/mcdatacomparison.runparameter
            else
                echo "* SIMS $SIMDIR/${I}_ATM${atm}_gamma/${SIMMSCW}/${simfile} 4 ${MCWOFF} 0. 110. 250. ${ZEMIN} ${ZEMAX}" > $ODIR/mcdatacomparison.runparameter
            fi
        fi
        echo "* ON ${DMSCWDIR}/[0-9]*.mscw.root 4 -99. -99. 0. 360. ${ZEMIN} ${ZEMAX}" >> $ODIR/mcdatacomparison.runparameter
        echo "* OFF ${DMSCWDIR}/[0-9]*.mscw.root 4 -99. -99. 0. 360. ${ZEMIN} ${ZEMAX}" >> $ODIR/mcdatacomparison.runparameter
        echo "   run parameter file: $ODIR/mcdatacomparison.runparameter"

        FSCRIPT="tmpdir/compareDatawithMC_qsub_${SIMTYPE}_${I}${A}_${ELE}_${MCWOFF}_${NSB}"
        rm -f ${FSCRIPT}.sh
        sed -e "s|OUTDIR|$ODIR|" \
            -e "s|CURRENTDIR|$PWDIR|" compareDatawithMC_qsub.sh > ${FSCRIPT}.sh

        echo "Run script: $FSCRIPT"
        chmod u+x $FSCRIPT

        $EVNDISPSCRIPTS/helper_scripts/UTILITY.condorSubmission.sh ${FSCRIPT}.sh 4000M 10G 
        condor_submit ${FSCRIPT}.sh.condor
    done
done
