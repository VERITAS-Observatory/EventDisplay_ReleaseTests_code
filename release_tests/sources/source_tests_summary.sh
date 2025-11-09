#!/bin/bash
# Summary of source tests - prepare markdown files
# for each object / epoch / cut type
#
#
if [[ $# -lt 4 ]]; then
echo "
    ./source_tests_summary.sh <data dir with anasum log files> <directory of last version with results> <output directory> <new version>

    Extract results from anasum log files and prepare markdown files for each object / epoch / cut type.

    Builds up on markdown files of previous version (given as second argument).

    Read list of targets from TARGETS.dat

    Intiial method is v490.7, to run this:

    ```console
    ./source_tests_summary.sh $VERITAS_USER_DATA_DIR/analysis/Results/v490/AP/SourceTests . ../../../EventDisplay_Release_v490/SourceTests v490.7
    ```

    Follow up runs based on this, e.g.:

    ```console
    ./source_tests_summary.sh $VERITAS_USER_DATA_DIR/analysis/Results/v491/AP/SourceTests ../../../EventDisplay_Release_v490/SourceTests ../../../EventDisplay_Release_v491/SourceTests v491.0
    ```

"
exit
fi

IDIR="${1}"
SDIR="${2}"
ODIR="${3}"
VERSION="${4}"

LTARGETS=$(cat TARGETS.dat)

EPOCHS="V4 V5 V4V5 V6 all"
# AP/NN redHV
CUTS="softbox"
# nominal AP and NN cuts
CUTS="hard2tel soft2tel moderate2tel hard3tel supersoftNN2tel"

for T in ${LTARGETS}
do
    for C in $CUTS
    do
        for E in $EPOCHS
        do
            # Result from anasum log file
            LFILE="${IDIR}/${T}/${C}/${E}.log"
            if [[ ! -e ${LFILE} ]]; then
                echo "No anasum log file with results: ${LFILE}"
                continue
            fi
            # Parse results FIRST to avoid using stale/empty variables when creating files
            RESULT=$(grep "ALL RUNS" ${LFILE} | sed 's/ALL RUNS //' | sed 's/  */ /g')
            RESULT=$(echo "$RESULT" | sed 's/),/),\n/g')
            RESULT_l1=$(echo "$RESULT" | sed -n '1p' | sed "s/(//" | sed "s/)//" | sed "s/^/$VERSION: /")
            RESULT_l2=$(echo "$RESULT" | sed -n '2p' | sed "s/^[[:space:]]*//" | sed "s/^/$VERSION: /")
            echo "RESULT_l1 $RESULT_l1"
            echo "RESULT_l2 $RESULT_l2"
            mkdir -p ${ODIR}/${T}/
            # Output file
            OFILE="${ODIR}/${T}/results_${T}_${E}_${C}.md"
            # Initital result markdown file
            IFILE="${SDIR}/${T}/results_${T}_${E}_${C}.md"
            if [[ ! -e "$IFILE" ]]; then
                echo "No initial results file $IFILE; creating empty file"
                if [[ ! -e ${OFILE} ]]; then
                    echo "## ${T} ${E} ${C}" > "$OFILE"
                    printf "\`\`\`text\n\`\`\`\n" >> "$OFILE"
                fi
            else
                echo "Initial result file copied to ${ODIR}/${T}/"
                cp -f "$IFILE" "${ODIR}/${T}/"
            fi
            # Ensure we don't keep stale lines for the same version; remove any existing lines starting with VERSION (portable, no sed -i)
            awk -v ver="$VERSION" '($0 ~ ("^" ver ": ")){next} {print}' "$OFILE" > temp_file && mv -f temp_file "$OFILE"
            # Insert the two result lines just BEFORE the closing code fence
            last_line=$(grep -n "\`\`\`" "$OFILE" | tail -n 1 | cut -d ":" -f 1)
            awk -v line_num="$last_line" -v l1="$RESULT_l1" -v l2="$RESULT_l2" 'NR == line_num {print l1; print l2} {print}' "$OFILE" > temp_file && mv -f temp_file "$OFILE"
            cp -v -f "$LFILE" "$ODIR/${T}/${C}_$(basename $LFILE)"
        done
    done
done
