#!/bin/bash
# split runlist according to major epoch
#
if [[ $# -lt 1 ]]; then
echo "
    ./split_runlists.sh <runlist>
"
exit
fi

RLIST=${1}
DIRN=$(dirname $RLIST)

for E in V4 V5 V6
do
    touch $DIRN/runlist_releaseTesting_${E}.dat
done

FF=$(cat $RLIST)

for F in $FF
do
    if [ "$F" -lt "46642" ]; then
        echo $F >> $DIRN/runlist_releaseTesting_V4.dat
    elif [ "$F" -lt "63373" ]; then
        echo $F >> $DIRN/runlist_releaseTesting_V5.dat
    else
        echo $F >> $DIRN/runlist_releaseTesting_V6.dat
    fi
done

for E in V4 V5 V6
do
    echo "RUNLIST ${1}: $(wc -l $DIRN/runlist_releaseTesting_${E}.dat)"
    if [ ! -s $DIRN/runlist_releaseTesting_${E}.dat ]; then
        rm -f $DIRN/runlist_releaseTesting_${E}.dat
    fi
done
