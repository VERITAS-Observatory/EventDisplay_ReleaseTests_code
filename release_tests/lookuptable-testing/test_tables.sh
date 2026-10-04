#!/bin/bash
# Supply a reference observation matched to the tables under test.
VERSION=$(cat "$VERITAS_EVNDISP_AUX_DIR/IRFVERSION") || exit 1
TESTFILE=${1:-${TESTFILE:-$VERITAS_USER_DATA_DIR/analysis/Results/${VERSION}/Crab/evndisp/64080.root}}
[[ -s $TESTFILE ]] || { echo "Usage: $0 <reference evndisp ROOT file> (or set TESTFILE)" >&2; exit 1; }
ODIR="$VERITAS_USER_DATA_DIR/analysis/Results/$VERSION/table-tests"
mkdir -p "$ODIR" || exit 1
mapfile -t TABLES < <(find "$VERITAS_EVNDISP_AUX_DIR/Tables" -type f -name "${TABLE_PATTERN:-*.root}")
((${#TABLES[@]})) || { echo "No lookup tables found" >&2; exit 1; }
failed=0
for T in "${TABLES[@]}"; do
    TB=$(basename "$T" .root)
    OFIL="$ODIR/test.$TB.mscw"
    echo "TEST reference=$TESTFILE table=$T"
    rm -f "$OFIL.root"
    if ! "$EVNDISPSYS/bin/mscw_energy" -tablesfile "$T" -noshorttree -maxnevents=10 -arrayrecid=0 \
        -inputfile "$TESTFILE" -writeReconstructedEventsOnly=1 -outputfile "$OFIL.root" > "$OFIL.log" 2>&1; then
        echo "FAILED executable: $T" >&2
        failed=$((failed+1))
    elif [[ ! -s $OFIL.root ]] || ! grep -q 'survived test of table file!' "$OFIL.log"; then
        echo "FAILED missing output/sanity marker: $T" >&2
        failed=$((failed+1))
    else
        echo "PASSED table sanity: $T"
        rm -f "$OFIL.root"
    fi
done
echo "Lookup coverage: ${#TABLES[@]} tested; $failed failed"
((failed == 0))
