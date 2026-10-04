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

# Optional comparison is explicit in the invocation environment.
COMPAREVERSION=${COMPAREVERSION:-}
COMPARESIMTYPE=${COMPARESIMTYPE:-}
COMPARECUT=${COMPARECUT:-}
mapfile -t CUTLIST < <(awk '$1 == "*" && $2 == "CUT" {print $3}' "$1")
((${#CUTLIST[@]})) || { echo "No CUT entries in $1" >&2; exit 1; }
TESTED=0
SKIPPED=0
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

DDIR="$VERITAS_IRFPRODUCTION_DIR/${VERSION}/${ANALYSISTYPE}/${SIMTYPE}"

for CUT in "${CUTLIST[@]}"; do
PLOT_BASE_DIR="${RELEASE_OUTPUT_DIR:-../../../../EventDisplay_Release_${VERSION}/irf_plotting}/${ANALYSISTYPE}${DIRRECOTYPE}/${SIMTYPE}/${CUT}"
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
                    ODIR="$PLOT_BASE_DIR/${E}_ATM${A}"
                    mkdir -p "$ODIR"
                    if true; then
                        IRFDIR="${DDIR}/${E}_ATM${A}_gamma/EffectiveAreas_Cut-${CUT}_DISP"
                        IRFFILE="EffArea-${SIMTYPE}-${E}-ID0-Ze${Z}deg-${W}wob-${N}-Cut-${CUT}"
                        echo "IRFDIR $IRFDIR"
                        echo "IRFFILE $IRFFILE"
                        if [[ ! -s "$IRFDIR/$IRFFILE.root" ]]; then
                            echo "SKIPPED missing $E ATM$A $CUT Ze$Z Woff$W NSB$N: $IRFDIR/$IRFFILE.root"
                            SKIPPED=$((SKIPPED+1))
                            continue
                        fi
                        echo "TESTED $E ATM$A $CUT Ze$Z Woff$W NSB$N"
                        TESTED=$((TESTED+1))
                        if [[ -n $COMPAREVERSION ]]; then
                            COMPARESIMTYPE=${COMPARESIMTYPE:-$SIMTYPE}
                            COMPARECUT=${COMPARECUT:-$CUT}
                            COMP_IRFDIR=${IRFDIR//"$VERSION"/"$COMPAREVERSION"}
                            COMP_IRFDIR=${COMP_IRFDIR//"$SIMTYPE"/"$COMPARESIMTYPE"}
                            COMP_IRFFILE=${IRFFILE//"$SIMTYPE"/"$COMPARESIMTYPE"}
                            # compare TMVA with XGB file
                            COMP_IRFDIR=${COMP_IRFDIR//"$CUT"/"$COMPARECUT"}
                            COMP_IRFFILE=${COMP_IRFFILE//"$CUT"/"$COMPARECUT"}
                            echo "COMPIRFDIR (comparison): $COMP_IRFDIR"
                            echo "COMPIRFFILE (comparison): $COMP_IRFFILE"
                            root -l -q -b "plot_irf.C(\"${IRFDIR}\",\"${IRFFILE}\",\"${E}\",\"${A}\",\"${CUT}\",\"${Z}\",\"${W}\",\"${N}\",\"${MCAZ}\",\"${ODIR}\", \"${COMP_IRFDIR}\",\"${COMP_IRFFILE}\")"
                        else
                            root -l -q -b "plot_irf.C(\"${IRFDIR}\",\"${IRFFILE}\",\"${E}\",\"${A}\",\"${CUT}\",\"${Z}\",\"${W}\",\"${N}\",\"${MCAZ}\",\"${ODIR}\")"
                        fi
                    fi
                done
            done
        done
    done
done

done
echo "IRF coverage: $TESTED tested; $SKIPPED missing combinations skipped"
((TESTED > 0)) || exit 1
