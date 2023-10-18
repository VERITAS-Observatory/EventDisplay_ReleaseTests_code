#!/bin/bash
# script to run V2DL5 and generate gammapy analysis results
# run point-like 
#

# qsub parameters
h_cpu=11:59:00; h_vmem=8000M; tmpdir_size=5G

# EventDisplay version
EDVERSION=$($EVNDISPSYS/bin/anasum --version | tr -d .)
# Directory with preprocessed data
DEFANASUMDIR="$VERITAS_DATA_DIR/processed_data_${EDVERSION}/${VERITAS_ANALYSIS_TYPE:0:2}/anasum/"
V2DL5="$EVNDISPSYS/../V2DL5/"

if [ $# -lt 4 ]; then
echo "
Reflected region analysis using gammapy

ANALYSIS.v2dl5.sh <run list> <target> <data/obs store director> <output directory> <configuration template>

required parameters:

    <runlist>               simple run list with one run number per line.

    <target>                target name (SIMBAD conform)

    <data/obs store directory> directory with data/obs store
    
    <output directory>      output directory for results

    <configuration template> V2DL5 configuration template file


Expect installation of V2DL5 (https://github.com/VERITAS-Observatory/V2DL5) and
corresponding conda installation (v2dl5)

"
exit
fi
RLIST=$(readlink -f "$1")
TARGET="$2"
DATASTORE=$3
ODIR=$4
CONFIG=$5

# Read runlist
if [ ! -f "$RLIST" ] ; then
    echo "Error, runlist $RLIST not found, exiting..."
    exit 1
fi

# make output directory if it doesn't exist
mkdir -p $ODIR
echo -e "Output files will be written to:\n $ODIR"

# run scripts are written into this directory
DATE=`date +"%y%m%d"`
LOGDIR="$VERITAS_USER_LOG_DIR/${DATE}-$(uuidgen)/V2DL5"
mkdir -p "$LOGDIR"
echo -e "Log files will be written to:\n $LOGDIR"
rm -f ${LOGIDR}/x* 2>/dev/null

# Job submission script
SUBSCRIPT=$( dirname "$0" )"/ANALYSIS.v2dl5_qsub"
TIMETAG=`date +"%s"`

# Prepare template file
if [[ -e $CONFIG ]]; then
    sed -e "s|DATASTORE|$DATASTORE|" \
        -e "s|TARGET|$TARGET|" $CONFIG > ${LOGDIR}/config.yml
fi


FSCRIPT="${LOGDIR}/V2DL5"
rm -f $FSCRIPT.sh

sed -e "s|RRUNLIST|$RLIST|" \
    -e "s|OODIR|$ODIR|" \
    -e "s|CCONFIG|${LOGDIR}/config.yml|" $SUBSCRIPT.sh > $FSCRIPT.sh

chmod u+x $FSCRIPT.sh

$EVNDISPSCRIPTS/helper_scripts/UTILITY.condorSubmission.sh $FSCRIPT.sh $h_vmem $tmpdir_size
echo
echo "-------------------------------------------------------------------------------"
echo "Job submission using HTCondor - run the following script to submit jobs at once:"
echo "$EVNDISPSCRIPTS/helper_scripts/submit_scripts_to_htcondor.sh $LOGDIR submit"
echo "-------------------------------------------------------------------------------"
echo
