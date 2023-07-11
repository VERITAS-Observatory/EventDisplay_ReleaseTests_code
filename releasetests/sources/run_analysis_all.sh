# run test analyses from list of targets
# 
#
if [[ $# < 1 ]]; then
echo "
    ./run_analysis_all.sh <TYPE>

    analysis types: ANASUM_SUB, ANASUM_FFF

"
exit
fi

ANATYPE=${1}
[[ "$2" ]] && RUNPARA=$2 || RUNPARA="../../../EventDisplay_Release_v490/runparameter/V6.${VERITAS_ANALYSIS_TYPE:0:2}.runparameter.dat"

LTARGETS=$(cat TARGETS.dat)

EPOCHS="V4 V5 V6 all"
CUTS="soft2tel moderate2tel hard3tel"
if [[ $RUNPARA == *"AP"* ]] && [[ $RUNPARA == *"redHV"* ]]; then
    CUTS="softbox"
elif [[ $RUNPARA == *"NN"* ]] && [[ $RUNPARA == *"redHV"* ]]; then
    CUTS="softbox supersoft"
elif [[ $RUNPARA == *"NN"* ]]; then
    CUTS="supersoft supersoftNN2tel"
fi

CUTS="hard3tel"

for T in ${LTARGETS}
do
    for C in $CUTS
    do
        for E in $EPOCHS
        do
            echo "Analysing ${T} with ${C} cuts (epoch $E)"
            ./run_analysis.sh \
                ${RUNPARA} \
                ${T} \
                ${ANATYPE} \
                ${C} \
                ${E}
        done
    done
done

