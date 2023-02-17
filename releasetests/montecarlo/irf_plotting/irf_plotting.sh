# 
# IRF plotting
#
#
set -e

if [ ! -n "$1" ]; then
   echo "./irf_plotting.sh <runparameter file>"
   echo ""
   exit
fi

#### TEMP FIXED VALUES
# Box cut
CUT="NTel2-PointSource-Moderate"
# BDT cuts
CUT="NTel2-PointSource-Moderate-TMVA-BDT"
MCAZ="16"
ANATYPE="AP"
COMPAREANA_1="_DISP"
COMPAREANA_2=""
#### (END TEMP FIXED VALUES)

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
# ANALYSIS TYPE
ANALYSISTYPE=$(grep ANALYSISTYPE ${1} | grep "*" | awk '{print $3}')
# DIRECTION RECONSTRUCTION
DIRRECOTYPE=$(grep DIRECTION ${1} | grep "*" | awk '{print $3}')

ODIR="../../../../EventDisplay_ReleaseTests_${VERSION}/irf_plotting/${ANALYSISTYPE}_${DIRRECOTYPE}/${SIMTYPE}/${CUT}_ATM${ATMO}"
mkdir -p ${ODIR}

DDIR="$VERITAS_IRFPRODUCTION_DIR/${VERSION}/${ANATYPE}/${SIMTYPE}/"

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
                    root -l -q -b "plot_irf.C(\"${DDIR}\",\"${E}\",\"${A}\",\"${CUT}\",\"${Z}\",\"${W}\",\"${N}\",\"${ODIR}\", \"${COMPAREANA_1}\",  \"${COMPAREANA_2}\")"
                done
            done
        done
    done
done

