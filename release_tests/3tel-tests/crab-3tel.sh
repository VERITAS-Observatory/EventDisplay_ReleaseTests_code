#!/bin/bash
# Run 4 / 3 telescope Crab analysis

if [ $# -lt 2 ]; then
    echo "
./crab-3tel.sh <run list> <output dir>
"
exit
fi

RUNLIST="$1"
OUTPUTDIR="$2"
RUNTYPE="mscw"

ANATYPE="${VERITAS_ANALYSIS_TYPE:0:2}"
VERSION=$(cat $VERITAS_EVNDISP_AUX_DIR/IRFMINORVERSION)

for ID in 0 1 2 3 4; do
    echo "Running $ID"
    if [[ $ID == "0" ]]; then
        ODIR="$OUTPUTDIR/4tel/$RUNTYPE"
    else
        ODIR="$OUTPUTDIR/3tel_ID$ID/$RUNTYPE"
    fi
    mkdir -p "$ODIR"
    if [[ $RUNTYPE == "mscw" ]]; then
        $EVNDISPSCRIPTS/ANALYSIS.mscw_energy.sh \
            "$RUNLIST" \
            "$ODIR" \
            $VERITAS_DATA_DIR/shared/processed_data_"$VERSION"/"$ANATYPE"/evndisp \
            0 $ID
    fi
done
