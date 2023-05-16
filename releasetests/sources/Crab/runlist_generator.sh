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

if [ $# -ne 1 ]; then
    echo "./runlist_generator.sh <runparameter file>"
    echo ""
    echo "  generates run lists for minor epochs, zenith angle ranges, different atmospheres"
    echo "  generates links of mscw_energy files for anasum analysis"
    echo "  (minor epochs are read from mscw_energy files)"
    echo ""
    echo "  reads runs from master list (e.g., runlist_releaseTestingV6.dat)"
    echo ""
    echo "IMPORTANT: requires files an a directory like $VERITAS_USER_DATA_DIR/analysis/Results/v490/AP/Crab_DISP/mscw"
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
DIRRECOTYPE="_DISP"
if [[ ! -z  $VERITAS_ANALYSIS_TYPE ]]; then
    ANALYSISTYPE="${VERITAS_ANALYSIS_TYPE:0:2}"
    if [[ ${VERITAS_ANALYSIS_TYPE} == *"DISP"* ]]; then
        DIRRECOTYPE="_DISP"
    else
        DIRRECOTYPE=""
    fi
fi
##############################################
# output directory for all data productions
VDIR="../../../../EventDisplay_Release_${VERSION}/${OBJECT}${DIRRECOTYPE}/"
mkdir -p ${VDIR}

##############################################
# 'master' run list
MLIST="./runlist_releaseTesting${MEPOCH}.dat"
if [[ ! -e ${MLIST} ]]; then
   echo "Runlist not found for epoch ${MEPOCH}: ${MLIST}"
   exit
fi
# 'master' directory with all mscw file 
MSCWSDIR="mscw-redHV"
MSCWSDIR="mscw"
MSCWDDIR="$VERITAS_USER_DATA_DIR/analysis/Results/${VERSION}/${ANALYSISTYPE}/${OBJECT}${DIRRECOTYPE}/${MSCWSDIR}"
if [[ ! -e ${MSCWDDIR} ]]; then
   echo "Error: directory with MSCW files not found" 
   echo ${MSCWDDIR}
   exit
fi
echo "READING mscw files from ${MSCWDDIR}"
LL=`cat ${MLIST}`
# fill new run lists
FILLRUNLISTS="TRUE"
# link mscw files into the epoch/etc directories
MAKELINKDDIR="TRUE"

fill_run()
{
    if [ $FILLRUNLISTS != "TRUE" ]
    then
       return
    fi
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

link_run()
{
    if [ $MAKELINKDDIR != "TRUE" ]
    then
       return
    fi
    PWDIR=`pwd`
    LINKDIR=${MSCWDDIR}"_"${LNAME}
    echo "    Link directory ${LINKDIR}"
    mkdir -p ${LINKDIR}
    if [ -e ${LINKDIR}/$R.mscw.root ]
    then
       rm -f ${LINKDIR}/$R.mscw.root
    fi
    cd ${LINKDIR}
    ln -s ../${1}/${R}.mscw.root .
    cd ${PWDIR}
}

for R in $LL
do
   if [ ! -e ${MSCWDDIR}/$R.mscw.root ]; then
      echo "Run $R - file not found: ${MSCWDDIR}/$R.mscw.root"
      continue
   fi
   # read and extract run info from files
   RUNINFO="$($EVNDISPSYS/bin/printRunParameter ${MSCWDDIR}/$R.mscw.root -runinfo)"
   ELEVATION="$($EVNDISPSYS/bin/printRunParameter ${MSCWDDIR}/$R.mscw.root -elevation)"
   WOBBLE="$($EVNDISPSYS/bin/printRunParameter ${MSCWDDIR}/$R.mscw.root -wobbleInt)"
   EPOCH=$(echo $RUNINFO | awk '{print $1}')
   MAJOREPOCH=$(echo $RUNINFO | awk '{print $2}')
   ATM=$(echo $RUNINFO | awk '{print $3}')
   if [[ $EPOCH == *"V4"* ]] || [[ $EPOCH == *"V5"* ]]
   then
       ATM=${ATM/6/2}
   fi
   ELEV=$(echo $ELEVATION | awk '{print $3}')
   WOBB=$(echo $WOBBLE | awk '{print $3}')
   OBSL=$(echo $RUNINFO | awk '{print $4}')
   EL=$(echo $ELEV | awk -v e=$ELEV '{if (e > 50 ) {print "SZE"} else if (e > 40 ) {print "MZE"} else {print "LZE"}}')
   # print run info
   echo "${R}: ${RUNINFO}   ${ELEV}   ${EL}  $ATM   $WOBB"

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
       link_run ${MSCWSDIR}
       # files per epoch and season
       LNAME="${E}_ATM${ATM}"
       fill_run
       link_run ${MSCWSDIR}
       # files per elevation range and epoch
       LNAME="${E}_${EL}"
       fill_run
       link_run ${MSCWSDIR}
       # files per elevation range and epoch and season
       LNAME="${E}_ATM${ATM}_${EL}"
       fill_run
       link_run ${MSCWSDIR}
       # files with non-0.5 deg wobble offsets (all in one directory)
       if [[ $WOBB != "50" ]]; then
           LNAME=${E}_WOBBLE
           fill_run
           link_run ${MSCWSDIR}
       else
          LNAME="${E}_ATM${ATM}_${EL}_0.5deg"
          fill_run
          link_run ${MSCWSDIR}
          LNAME="${E}_${EL}_0.5deg"
          fill_run
          link_run ${MSCWSDIR}
          LNAME="${E}_0.5deg"
          fill_run
          link_run ${MSCWSDIR}
       fi
   done
done
