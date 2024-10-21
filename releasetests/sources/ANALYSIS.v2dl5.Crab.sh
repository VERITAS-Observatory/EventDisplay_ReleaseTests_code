# Run V2DL5 analysis for all Crab runs

CUT="soft2tel"
CUT="moderate2tel"
CUT="hard3tel"

RLISTS=$(ls -1 Crab/runlists/*.dat)
DL3DIR="/lustre/fs24/group/veritas/shared/processed_data_v490/AP/dl3_pointlike_${CUT}/"
DDIR="$VERITAS_USER_DATA_DIR/analysis/Results/v490/AP/v2dl5/${CUT}"
TARGET="Crab"
CONFIG="ANALYSIS.v2dl5.reflected_region.yml"

for RLIST in $RLISTS
do
    if [[ $(wc -l < "$RLIST") -eq 0 ]]; then
        echo "Zero lines in $RLIST"
        continue
    fi

    ODIR=$(basename $RLIST .dat)
    ODIR="${ODIR/runlist_releaseTesting/}"
    echo $ODIR

    ./ANALYSIS.v2dl5.sh ${RLIST} ${TARGET} ${DL3DIR} ${DDIR}/${ODIR} ${CONFIG}

done
