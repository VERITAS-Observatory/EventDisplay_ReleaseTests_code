#!/bin/bash
#  generate run lists and linked directories
# - epochs
# - summer / winter (all, and for epochs)
# - zenith angle ranges (fixed to >50, 40-50, <40 deg)
#
# required input:
# - master run lists with all analysed runs
# - mscw root files from analysis
#
# **hardwired directory names**

if [ $# -ne 2 ]; then
    echo "./runlist_generator_from_anasum_log.sh <runparameter file> <anasum-run wise results"
    echo ""
    echo "  generates run lists for minor epochs, zenith angle ranges, different atmospheres"
    echo "  generates links of anasum files for combined anasum file"
    echo "  (minor epochs are read from anasum log files)"
    echo ""
    echo "  reads runs from major epoch lists (e.g., runlist_releaseTestingV6.dat)"
    echo ""
    exit
fi

###########################
# read runparameter file
if [[ ! -e ${1} ]]; then
   echo "Error, runparameter file not found: ${1}"
   exit
fi
# Eventdisplay version
VERSION=$(grep VERSION ${1} | awk '{print $3}')
# MAJOR EPOCH
MEPOCH=$(grep MAJOREPOCH ${1} | awk '{print $3}')
# Source name
OBJECT=$(grep SOURCE ${1} | awk '{print $3}')
# Analysis type
ANALYSISTYPE="AP"
if [[ ! -z  $VERITAS_ANALYSIS_TYPE ]]; then
    ANALYSISTYPE="${VERITAS_ANALYSIS_TYPE:0:2}"
fi
##############################################
# output directory for all data productions
VDIR="../../../../EventDisplay_Release_${VERSION}/${OBJECT}/"
mkdir -p ${VDIR}

##############################################
# 'main' run list
MLIST="./runlist_releaseTesting${MEPOCH}.dat"
if [[ ! -e ${MLIST} ]]; then
   echo "Runlist not found for epoch ${MEPOCH}: ${MLIST}"
   exit
fi
# 'main' directory with all anasum files
DATADIR="${2}"
if [[ ! -e ${DATADIR} ]]; then
   echo "Error: directory with anasum files not found"
   echo ${DATADIR}
   exit
fi

fill_run()
{
    mkdir -p ${VDIR}/runlists
    RUNLNAME="${VDIR}/runlists/runlist_releaseTesting${LNAME}.dat"
    # check if run lists exists
    if [ -e ${RUNLNAME} ]
    then
        # check if run is already in run list
        if grep -Fxq $R ${RUNLNAME}
        then
           echo "    Run $R already in file list ${RUNLNAME}"
        else
           echo $R >> ${RUNLNAME}
           echo "    Run $R filled in file list ${RUNLNAME}"
        fi
    else
        touch ${RUNLNAME}
        echo "    File list ${RUNLNAME} generated"
        echo $R >> ${RUNLNAME}
        echo "    Run $R filled in file list ${RUNLNAME}"
    fi
}

echo "READING anasum files from ${DATADIR}"
LL=$(cat ${MLIST})
for R in $LL
do
   if [ ! -e ${DATADIR}/$R.anasum.root ]; then
      echo "Run $R - root file not found: ${DATADIR}/$R.anasum.root"
      continue
   fi
   if [ ! -e ${DATADIR}/$R.anasum.log ]; then
      echo "Run $R - log file not found: ${DATADIR}/$R.anasum.log"
      continue
   fi
   echo "DATADIR ${DATADIR}/$R.anasum.log"
   # read and extract run info from files
   INSTRUMENT_EPOCH=$(grep "Instrument epoch selected" "${DATADIR}/$R.anasum.log" | head -n 1 | awk '{print $NF}')
   MAJOREPOCH=$(echo "$INSTRUMENT_EPOCH" | cut -d '_' -f1)
   EPOCH="${INSTRUMENT_EPOCH%_ATM*}"
   EPOCH=$(echo "$INSTRUMENT_EPOCH" | cut -d '_' -f1-3)
   ATM=$(echo "$INSTRUMENT_EPOCH" | grep -oE 'ATM[0-9]+')
   if [[ $EPOCH == *"V4"* ]] || [[ $EPOCH == *"V5"* ]]
   then
       ATM=${ATM/6/2}
   fi
   EFFECTIVEAREA=$(grep "effective areas from" "${DATADIR}/$R.anasum.log")
   if [[ $EFFECTIVEAREA == *"RedHV"* ]]; then
       OBSL="obsLowHV"
   else
       OBSL="stdHV"
   fi
   ELEV=$(grep "mean elevation" "${DATADIR}/$R.anasum.log" | head -n 1 | awk '{print $3}')
   EL=$(echo $ELEV | awk -v e=$ELEV '{if (e > 50 ) {print "SZE"} else if (e > 40 ) {print "MZE"} else if (e > 30 ) {print "LZE"} else {print "BZE"}}')
   WOBBLESTRING=$(grep "Wobble offsets (currE)" "${DATADIR}/$R.anasum.log")
   n_offset=$(echo "$WOBBLESTRING" | head -n 1 | awk '{print $5}')
   w_offset=$(echo "$WOBBLESTRING" | head -n 1 | awk '{print $7}')
   w_offset=${w_offset/,/}
   w_offset=${w_offset/-/}
   n_offset=${n_offset/-/}
   if [[ $n_offset != 0 ]]; then
       WOBB="$n_offset"
   elif [[ $w_offset != 0 ]]; then
       WOBB="$w_offset"
   else
       WOBBB="0"
   fi
   echo "${R}: MAJOREPOCH ${MAJOREPOCH} EPOCH ${EPOCH} ELEVATION ${EL} ATM $ATM  WOBBLE $WOBB OBSL $OBSL"

   # files per major/minor epoch
   for E in ${MAJOREPOCH} ${EPOCH}
   do
       if [[ $OBSL == "obsLowHV" ]]; then
           E="${E}_redHV"
       fi
       #####
       # epoch
       LNAME="${E}"
       fill_run
       # files per epoch and season
       LNAME="${E}_${ATM}"
       fill_run
       # files per elevation range and epoch
       LNAME="${E}_${EL}"
       fill_run
       # files per elevation range and epoch and season
       LNAME="${E}_${ATM}_${EL}"
       fill_run
       # files with non-0.5 deg wobble offsets (all in one directory)
       if [[ $WOBB != "0.5" ]]; then
           LNAME=${E}_WOBBLE
           fill_run
       else
          LNAME="${E}_${ATM}_${EL}_0.5deg"
          fill_run
          LNAME="${E}_${EL}_0.5deg"
          fill_run
          LNAME="${E}_0.5deg"
          fill_run
       fi
   done
done
