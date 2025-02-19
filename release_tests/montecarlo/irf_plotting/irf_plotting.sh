#!/bin/bash
#
# IRF plotting
#
#
set -e

if [ ! -n "$1" ]; then
   echo "./irf_plotting.sh <runparameter file>"
   echo ""
   echo "(note hardwired epoch)"
   echo ""
   exit
fi

#### TEMP FIXED VALUES
CUT="NTel3-PointSource-Hard-TMVA-BDT"
CUT="NTel2-PointSource-Moderate-TMVA-BDT"
CUT="NTel2-PointSource-Soft-TMVA-BDT"
CUT="NTel2-PointSource-Moderate"
# Comparision plots - version and simtype hardwired
COMPAREVERSION="v490"
COMPARESIMTYPE="CARE_June2020"
#### (END TEMP FIXED VALUES)

# Analysis type
ANATYPE="${VERITAS_ANALYSIS_TYPE:0:2}"
# Eventdisplay version
VERSION=$(grep VERSION ${1} | grep '*' | awk '{print $3}')
# Simulation type
SIMTYPE=$(grep SIMTYPE ${1} | grep '*' | awk '{print $3}')
# Epochs
EPOCH=($(grep EPOCH ${1} | grep '*' | grep -v MAJOR | awk '{print $3}'))
# Atmosphere
ATMO=($(grep ATMOSPHERE ${1} | grep '*' | awk '{print $3}'))
# MC Ze
MCZE=($(grep MC_ZE ${1} | grep '*' | awk '{for(i=3;i<=NF;++i)print $i}'))
# MC Woff
MCWOFF=($(grep MC_WOFF ${1} | grep '*' | awk '{for(i=3;i<=NF;++i)print $i}'))
# MC NSB
MCNSB=($(grep MC_NSB ${1} | grep '*' | awk '{for(i=3;i<=NF;++i)print $i}'))
# MC AZ
MCAZ=($(grep MC_AZ ${1} | grep '*' | awk '{print $3}'))
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

ODIR="../../../../EventDisplay_Release_${VERSION}/irf_plotting/${ANALYSISTYPE}${DIRRECOTYPE}/${SIMTYPE}/${CUT}_ATM${ATMO}"
mkdir -p ${ODIR}

DDIR="$VERITAS_IRFPRODUCTION_DIR/${VERSION}/${ANATYPE}/${SIMTYPE}"

for Z in "${MCZE[@]}"
do
    for W in "${MCWOFF[@]}"
    do
        for N in "${MCNSB[@]}"
        do
            for E in "${EPOCH[@]}"
            do
                if [[ ${E} == "V6" ]]; then
                    continue
                fi
                for A in "${ATMO[@]}"
                do
                    if [[ ${E} == "V6_2023_2024w" ]] && [[ ${A} == "61" ]]; then
                        IRFDIR="${DDIR}/${E}_ATM${A}_gamma/EffectiveAreas_Cut-${CUT}_DISP"
                        IRFFILE="EffArea-${SIMTYPE}-${E}-ID0-Ze${Z}deg-${W}wob-${N}-Cut-${CUT}"
                        echo "IRFDIR $IRFDIR"
                        echo "IRFFILE $IRFFILE"
                        if [[ -n $COMPAREVERSION ]]; then
                            COMP_IRFDIR=${IRFDIR//"$VERSION"/"$COMPAREVERSION"}
                            COMP_IRFDIR=${COMP_IRFDIR//"$SIMTYPE"/"$COMPARESIMTYPE"}
                            COMP_IRFFILE=${IRFFILE//"$SIMTYPE"/"$COMPARESIMTYPE"}
                            echo "IRFDIR (comparision): $COMP_IRFDIR"
                            echo "IRFFILE (comparision): $COMP_IRFFILE"
                            root -l -q -b "plot_irf.C(\"${IRFDIR}\",\"${IRFFILE}\",\"${E}\",\"${A}\",\"${CUT}\",\"${Z}\",\"${W}\",\"${N}\",\"${ODIR}\", \"${COMP_IRFDIR}\",\"${COMP_IRFFILE}\")"
                        else
                            root -l -q -b "plot_irf.C(\"${IRFDIR}\",\"${IRFFILE}\",\"${E}\",\"${A}\",\"${CUT}\",\"${Z}\",\"${W}\",\"${N}\",\"${ODIR}\")"
                        fi
                    fi
                done
            done
        done
    done
done
