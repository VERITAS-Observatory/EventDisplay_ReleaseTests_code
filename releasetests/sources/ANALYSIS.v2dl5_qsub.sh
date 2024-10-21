#!/bin/bash
# script to run V2DL5

# set observatory environmental variables
source $EVNDISPSYS/setObservatory.sh VTS
# Don't do set -e.
# set -e

# parameters replaced by parent script using sed
RUNLIST=RRUNLIST
ODIR=OODIR
CONFIG=CCONFIG

# V2DL5 code
V2DL5="$EVNDISPSYS/../V2DL5/"

# make output directory if it doesn't exist
mkdir -p ${ODIR}
echo -e "Output files will be written to:\n ${ODIR}"

check_conda_installation()
{
    if command -v conda &> /dev/null; then
        echo "Found conda installation."
    else
        echo "Error: found no conda installation."
        echo "exiting..."
        exit
    fi
    env_info=$(conda info --envs)
    env_name="v2dl5"
    if [[ "$env_info" == *"$env_name"* ]]; then
        echo "Found conda environment '$env_name'"
    else
        echo "Error: the conda environment '$env_name' does not exist."
        echo "exiting..."
        exit
    fi
}

check_conda_installation

source activate base
conda activate v2dl5
export PYTHONPATH=\$PYTHONPATH:${V2DL5}

python ${V2DL5}/v2dl5/scripts/reflected_region_analysis.py \
    --output_dir ${ODIR} \
    --config ${CONFIG} \
    --run_list ${RUNLIST} > ${ODIR}/v2dl5.log 2>&1

exit
