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

CUTS="soft2tel moderate2tel hard3tel moderatebox"
if [[ $RUNPARA == *"AP"* ]] && [[ $RUNPARA == *"redHV"* ]]; then
    CUTS="softbox"
elif [[ $RUNPARA == *"NN"* ]] && [[ $RUNPARA == *"redHV"* ]]; then
    CUTS="softbox supersoft"
elif [[ $RUNPARA == *"NN"* ]]; then
    CUTS="supersoft supersoftNN2tel"
fi

for T in ${LTARGETS}
do
    for C in $CUTS
    do
        echo "Analysing ${T} with ${C} cuts"
        ./run_analysis.sh \
            ${RUNPARA} \
            ${T} \
            ${ANATYPE} \
            ${C}
    done
done

