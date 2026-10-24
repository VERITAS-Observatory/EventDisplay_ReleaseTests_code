#!/bin/bash
# Execute in the installed v2dl5 environment; propagate failures to the scheduler.
set -eo pipefail
source "$EVNDISPSYS/setObservatory.sh" VTS
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "${V2DL5_CONDA_ENV:-v2dl5}"
RUNLIST="RRUNLIST"
ODIR="OODIR"
CONFIG="CCONFIG"
mkdir -p "$ODIR"
export MPLBACKEND=Agg
exec python -m v2dl5.scripts.reflected_region_analysis \
    --output_dir "$ODIR" --config "$CONFIG" --run_list "$RUNLIST" \
    > "$ODIR/v2dl5.log" 2>&1
