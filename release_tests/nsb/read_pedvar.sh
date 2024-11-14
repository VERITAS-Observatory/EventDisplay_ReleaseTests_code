#!/bin/bash
# analysis of pedestal variations vs correction factors
#
# - correction factors are read from MSCW.sizecal.runparameter file
# - pedvars are read from MSCW log files
#
#  results are written to data directories
#  use plot.C plot() to plot results
#
# zenith angle fixed (to 20 deg)
#
set -e

if [ ! -n "$1" ]; then
   echo "./read_pedvar.sh <runparameter file>"
   echo ""
   exit
fi

# Eventdisplay version
VERSION=$(grep VERSION ${1} | awk '{print $3}')
# Simulation type
SIMTYPE=$(grep SIMTYPE ${1} | awk '{print $3}')
# Epochs
EPOCH=($(grep EPOCH ${1} | grep -v MAJOR | awk '{print $3}'))
# ATMOSPHERE (fixed to winter)
ATM="61"
# MC NSB
MCNSB=($(grep MC_NSB ${1} | awk '{for(i=3;i<=NF;++i)print $i}'))

ODIR="../../${VERSION}/nsb/${SIMTYPE}/"
mkdir -p ${ODIR}

for T in 1 2 3 4
do
    for N in "${MCNSB[@]}"
    do
        OFIL="${ODIR}/T${T}_NSB${N}.dat"
        rm -f $OFIL
        touch $OFIL
        echo "PROCESSING T${T} NSB ${N} (writing to ${OFIL})"
        for I in "${EPOCH[@]}"
        do
            echo "      $I"

            # read transmission value
            TFILE="$VERITAS_EVNDISP_AUX_DIR/ParameterFiles/ThroughputCorrection.runparameter"
            _sizecallineraw=$(grep "* s " $TFILE | grep " ${I} ")

            MCDIR="$VERITAS_USER_DATA_DIR/analysis/Results/${VERSION}/${SIMTYPE}/${I}_ATM${ATM}_gamma/MSCW_RECID0/"
            _pedvars=$(grep "Mean pedvar per telescope" $MCDIR/20deg_0.5wob_NOISE${N}.log)

            if [[ $T == "1" ]]; then
                EPOCH_SCALE=$(echo "$_sizecallineraw" | awk '{print $4}')
                PEDVARS=$(echo "$_pedvars" | awk '{print $5}')
            elif [[ $T == "2" ]]; then
                EPOCH_SCALE=$(echo "$_sizecallineraw" | awk '{print $5}')
                PEDVARS=$(echo "$_pedvars" | awk '{print $6}')
            elif [[ $T == "3" ]]; then
                EPOCH_SCALE=$(echo "$_sizecallineraw" | awk '{print $6}')
                PEDVARS=$(echo "$_pedvars" | awk '{print $7}')
            elif [[ $T == "4" ]]; then
                EPOCH_SCALE=$(echo "$_sizecallineraw" | awk '{print $7}')
                PEDVARS=$(echo "$_pedvars" | awk '{print $8}')
            fi
            echo "${EPOCH_SCALE} ${PEDVARS}" >> $OFIL
        done
    done
done
