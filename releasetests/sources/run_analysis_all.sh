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

LTARGETS=$(cat TARGETS.dat)
RUNPARA="../../../EventDisplay_ReleaseTests_v490/V6.runparameter.dat"

for T in ${LTARGETS}
do
    if [[ ${ANATYPE} == "ALL_RESULTS" ]]; then
        echo "ALL_RESULTS"
        echo "ALL_RESULTS ### ${T}"
    fi
    for C in soft2tel moderate2tel hard3tel softbox moderatebox
    do
        echo "Analysing ${T} with ${C} cuts"
        if [[ ${ANATYPE} == "ALL_RESULTS" ]]; then
            echo "ALL_RESULTS"
            echo "ALL_RESULTS #### ${C}"
            echo "ALL_RESULTS"
        fi


        ./run_analysis.sh \
            ${RUNPARA} \
            ${T} \
            ${ANATYPE} \
            ${C}
    done
done

