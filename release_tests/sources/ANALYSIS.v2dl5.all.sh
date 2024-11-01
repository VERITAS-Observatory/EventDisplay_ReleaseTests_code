# Run V2DL5 analysis for all test sources except Crab
# expect a TARGET.txt file in each directory with a
# one line entry containing the SIMBAD identifier

CUT="soft2tel"
CUT="moderate2tel"
CUT="hard3tel"

RLISTS=$(find . -type d -name Crab -prune -o -name 'runlist_releaseTesting*.dat' -print)
DL3DIR="/lustre/fs24/group/veritas/shared/processed_data_v490/AP/dl3_pointlike_${CUT}/"
DDIR="$VERITAS_USER_DATA_DIR/analysis/Results/v490/AP/v2dl5/${CUT}"
CONFIG="ANALYSIS.v2dl5.reflected_region.yml"

for RLIST in $RLISTS
do
    if [[ $(wc -l < "$RLIST") -eq 0 ]]; then
        echo "Zero lines in $RLIST"
        continue
    fi
    DIRN=$(dirname $RLIST)
    echo $DIRN
    TDIR=$(basename $DIRN)
    EPOCH=$(basename $RLIST .dat)
    EPOCH="${EPOCH/runlist_releaseTesting_/}"
    ODIR="${TDIR}_${EPOCH}"
    echo "Processing $ODIR"

    if [[ -e ${DIRN}/TARGET.txt ]]; then
        TARGET=$(cat ${DIRN}/TARGET.txt)
        echo "   TARGET $TARGET"
        ./ANALYSIS.v2dl5.sh ${RLIST} "${TARGET}" ${DL3DIR} ${DDIR}/${ODIR} ${CONFIG}
    else
        echo "No target file found in ${DIRN}"
    fi
done
