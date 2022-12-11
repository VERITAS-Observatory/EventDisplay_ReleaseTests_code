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
CUT="NTel2-PointSource-Moderate"
MCAZ="16"
ANATYPE="AP"
COMPAREANA="_DISP"
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

ODIR="../../../${VERSION}/irf_plotting/${SIMTYPE}/${CUT}_ATM${ATMO}"
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
                for A in "${ATMO[@]}"
                do
                    root -l -q -b "plot_irf.C(\"${DDIR}\",\"${E}\",\"${A}\",\"${CUT}\",\"${Z}\",\"${W}\",\"${N}\",\"${ODIR}\", \"${COMPAREANA}\")"
                done
            done
        done
    done
done

