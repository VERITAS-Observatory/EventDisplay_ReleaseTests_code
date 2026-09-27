#!/bin/bash
# Submit V2DL5 reflected-region analyses for all non-Crab release-test sources.

set -u

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
VERSION=$(cat "${VERITAS_EVNDISP_AUX_DIR:?}/IRFVERSION")
MINORVERSION=$(cat "${VERITAS_EVNDISP_AUX_DIR:?}/IRFMINORVERSION")
ANALYSISTYPE="${VERITAS_ANALYSIS_TYPE:0:2}"
TARGETS_FILE="${SCRIPT_DIR}/TARGETS.dat"
CONFIG="${V2DL5_CONFIG:-${SCRIPT_DIR}/ANALYSIS.v2dl5.reflected_region.yml}"

# Override these when the DL3 store or result root is not in the standard
# release-test location.
DL3_BASE="${V2DL5_DL3_BASE:-${VERITAS_DATA_DIR:?}/shared/processed_data_${MINORVERSION}/${ANALYSISTYPE}}"
OUTPUT_ROOT="${V2DL5_OUTPUT_ROOT:-${VERITAS_USER_DATA_DIR:?}/analysis/Results/${VERSION}/${ANALYSISTYPE}/v2dl5}"

if [[ -n "${V2DL5_CUTS:-}" ]]; then
    CUTS="${V2DL5_CUTS}"
elif [[ "${ANALYSISTYPE}" == "NN" ]]; then
    CUTS="supersoftNN2tel"
else
    CUTS="soft2tel moderate2tel hard3tel"
fi

[[ -f "${TARGETS_FILE}" ]] || { echo "Missing target list: ${TARGETS_FILE}" >&2; exit 1; }
[[ -f "${CONFIG}" ]] || { echo "Missing DL5 configuration: ${CONFIG}" >&2; exit 1; }

status=0
while IFS= read -r SOURCE || [[ -n "${SOURCE}" ]]; do
    [[ -z "${SOURCE}" || "${SOURCE}" == \#* ]] && continue
    [[ "${SOURCE}" == "Crab" ]] && continue

    SOURCE_DIR="${SCRIPT_DIR}/${SOURCE}"
    TARGET_FILE="${SOURCE_DIR}/TARGET.txt"
    if [[ ! -f "${TARGET_FILE}" ]]; then
        echo "Skipping ${SOURCE}: missing ${TARGET_FILE}" >&2
        status=1
        continue
    fi
    TARGET=$(<"${TARGET_FILE}")
    if [[ -z "${TARGET}" ]]; then
        echo "Skipping ${SOURCE}: empty ${TARGET_FILE}" >&2
        status=1
        continue
    fi

    shopt -s nullglob
    RUNLISTS=("${SOURCE_DIR}"/runlist_releaseTesting*.dat)
    shopt -u nullglob
    if [[ ${#RUNLISTS[@]} -eq 0 ]]; then
        echo "Skipping ${SOURCE}: no release-test run list" >&2
        status=1
        continue
    fi

    for CUT in ${CUTS}; do
        DL3DIR="${DL3_BASE}/dl3_pointlike_${CUT}"
        if [[ ! -d "${DL3DIR}" ]]; then
            echo "Skipping ${SOURCE} (${CUT}): DL3 store not found: ${DL3DIR}" >&2
            status=1
            continue
        fi
        for RLIST in "${RUNLISTS[@]}"; do
            [[ -s "${RLIST}" ]] || { echo "Skipping empty run list: ${RLIST}" >&2; status=1; continue; }
            EPOCH=$(basename "${RLIST}" .dat)
            EPOCH=${EPOCH#runlist_releaseTesting_}
            EPOCH=${EPOCH#runlist_releaseTesting}
            ODIR="${OUTPUT_ROOT}/${CUT}/${SOURCE}_${EPOCH}"
            echo "Submitting ${SOURCE}, ${EPOCH}, ${CUT}"
            "${SCRIPT_DIR}/ANALYSIS.v2dl5.sh" "${RLIST}" "${TARGET}" "${DL3DIR}" "${ODIR}" "${CONFIG}" || status=1
        done
    done
done < "${TARGETS_FILE}"

exit "${status}"
