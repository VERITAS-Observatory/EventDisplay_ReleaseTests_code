#!/bin/bash
# Submit V2DL5 reflected-region analyses for the Crab release-test run lists.

set -u

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
VERSION=$(cat "${VERITAS_EVNDISP_AUX_DIR:?}/IRFVERSION")
MINORVERSION=$(cat "${VERITAS_EVNDISP_AUX_DIR:?}/IRFMINORVERSION")
ANALYSISTYPE="${VERITAS_ANALYSIS_TYPE:0:2}"
CONFIG="${V2DL5_CONFIG:-${SCRIPT_DIR}/ANALYSIS.v2dl5.reflected_region.yml}"
DL3_BASE="${V2DL5_DL3_BASE:-${VERITAS_DATA_DIR:?}/shared/processed_data_${MINORVERSION}/${ANALYSISTYPE}}"
OUTPUT_ROOT="${V2DL5_OUTPUT_ROOT:-${VERITAS_USER_DATA_DIR:?}/analysis/Results/${VERSION}/${ANALYSISTYPE}/v2dl5}"
TARGET="${V2DL5_CRAB_TARGET:-Crab}"

if [[ -n "${V2DL5_CUTS:-}" ]]; then
    CUTS="${V2DL5_CUTS}"
elif [[ "${ANALYSISTYPE}" == "NN" ]]; then
    CUTS="supersoftNN2tel"
else
    CUTS="soft2tel moderate2tel hard3tel"
fi

[[ -f "${CONFIG}" ]] || { echo "Missing DL5 configuration: ${CONFIG}" >&2; exit 1; }
shopt -s nullglob
RUNLISTS=("${SCRIPT_DIR}/Crab"/runlist_releaseTesting*.dat)
shopt -u nullglob
[[ ${#RUNLISTS[@]} -gt 0 ]] || { echo "No Crab release-test run lists found" >&2; exit 1; }

status=0
for CUT in ${CUTS}; do
    DL3DIR="${DL3_BASE}/dl3_pointlike_${CUT}"
    if [[ ! -d "${DL3DIR}" ]]; then
        echo "Skipping Crab (${CUT}): DL3 store not found: ${DL3DIR}" >&2
        status=1
        continue
    fi
    for RLIST in "${RUNLISTS[@]}"; do
        [[ -s "${RLIST}" ]] || { echo "Skipping empty run list: ${RLIST}" >&2; status=1; continue; }
        EPOCH=$(basename "${RLIST}" .dat)
        EPOCH=${EPOCH#runlist_releaseTesting_}
        EPOCH=${EPOCH#runlist_releaseTesting}
        ODIR="${OUTPUT_ROOT}/${CUT}/Crab_${EPOCH}"
        echo "Submitting Crab, ${EPOCH}, ${CUT}"
        "${SCRIPT_DIR}/ANALYSIS.v2dl5.sh" "${RLIST}" "${TARGET}" "${DL3DIR}" "${ODIR}" "${CONFIG}" || status=1
    done
done

exit "${status}"
