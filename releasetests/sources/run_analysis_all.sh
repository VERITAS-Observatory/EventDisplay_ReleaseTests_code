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
    for C in soft2tel moderate2tel hard3tel softbox
    do
        echo "Analysing ${T} with ${C} cuts"

        ./run_analysis.sh \
            ${RUNPARA} \
            ${T} \
            ${ANATYPE} \
            ${C}
    done
done

