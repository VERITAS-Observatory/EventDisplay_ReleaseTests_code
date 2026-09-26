#!/bin/bash
# Prepare analysis results document by combining results markdown files
# into a single file
#
#

if [[ $# -lt 1 ]]; then
echo "
    ./prepare_analysis_results_document.sh <result files directory>

    Combine results markdown files into a single file.
    (requires pandoc installed)

    Example:

    ./prepare_analysis_results_document.sh ../../../EventDisplay_Release_v491/SourceTests

"
exit
fi

IDIR="${1}"

LTARGETS=$(cat TARGETS.dat)

PDOC="AnalysisResults_header.md "

# skip targets without result files (glob that matches nothing is left literal)
shopt -s nullglob
for T in ${LTARGETS}; do
    for F in ${IDIR}/${T}/results_${T}_*.md; do
        PDOC="${PDOC} ${F}"
    done
done
shopt -u nullglob
PDOC="${PDOC} AnalysisResults_footer.md"

# echo "Pandoc command: pandoc -s -o ./AnalysisResults.md ${PDOC}"
pandoc -s -o ./AnalysisResults.md ${PDOC}
