# Make the markdown file containg the spectral comparision plot
# and diagnostic plots in two columns table.
#
# run:
# ./make_v2dl3_release_test_doc.sh <runparameter file> SZE RE FIGURE_DIR
# 


set -e

if [[ ! -e ${1} ]]; then
   echo "/make_v2dl3_release_test_doc.sh <runparameter file> [SZE/MZE/LZE/WOBBLE] [RE/RB/IGNOREACCEPTANCE] [FIGURE_DIR]"
   exit
fi
# Eventdisplay version
VERSION=$(grep VERSION ${1} | awk '{print $3}')
# Analysis type
ANALYSISTYPE=$(grep ANALYSISTYPE ${1} | awk '{print $3}')
# eventdisplay version --> defines script directory
EDVERSION=$($EVNDISPSYS/bin/evndisp --version | tr -d .)
EDVERSION=${EDVERSION:1}
echo ${EDVERSION}
# directory with scripts and cuts
if [[ $EDVERSION -lt "485" ]]; then
  SCRIPTDIR=$EVNDISPSYS/scripts/VTS/
else
  SCRIPTDIR=${EVNDISPSCRIPTS}
fi
# Epochs
MEPOCH=$(grep MAJOREPOCH ${1} | grep "*" | awk '{print $3}')
EPOCH=($(grep EPOCH ${1} | grep "*" | grep -v MAJOR | awk '{print $3}'))
# Atmopsphere
ATMOS=($(grep ATMOSPHERE ${1} | grep "*" | awk '{print $3}'))
# CUTS
CUTS=($(grep CUT ${1} | grep "*"| awk '{print $4}'))
# Source NAme
OBJECT=$(grep SOURCE ${1} | grep "*" | awk '{print $3}')
# Bright star catalog
CATALOG=$(grep BRIGHTSTARCATALOGUE ${1} | grep "*" | awk '{print $3}')
# Minimum brightness of stars
BRIGHTSTARSETTINGS=$(grep BRIGHTSTARSETTINGS ${1} | grep "*" | awk '{print $3}')

#########################
# Directory for data files
DDIR="$VERITAS_USER_DATA_DIR/analysis/Results/${VERSION}/${ANALYSISTYPE}/${OBJECT}/"
echo $DDIR

# Directory with run lists
RDIR=`pwd`
# elevation range

[[ "$2" ]] && ELE=$2 || ELE="SZE"
[[ "$3" ]] && BCK=$3 || BCK="RE"

[[ "$4" ]] && FIGUREDIR=$4 || FIGUREDIR="" 


# mscw_energy subdirectory
# (old style scripts: "evndisp/RecID0")
FORCEDATMO=""
# forced for redHV (only available for ATM61)
if [[ ${MEPOCH} == *"redHV"* ]]
then
    FORCEDATMO="61"
fi

cd ${FIGUREDIR}
cd ../

filename="Releasetest-Summary-${ELE}-${BCK}.md"
echo "# Release test document" > ${filename}


for I in "${EPOCH[@]}"
do
    if [[ ${MEPOCH} == *"redHV"* ]] && [[ ${I} != "V6redHV" ]]; then
       I="${I}_redHV"
    elif [[ ${I} == "V6redHV" ]]; then
       I="V6_redHV"
    fi
    for A in "" "${ATMOS[@]}"
    do
        # prepare run list
        ATM=${A}
        if [[ ${I: -1} == "w" ]] && [[ ${A} == *"62"* ]]; then
           continue
        elif [[ ${I: -1} == "s" ]] && [[ ${A} == *"61"* ]]; then
           continue
        fi
        if [[ ! -z ${ATM} ]]; then
           ATM="_ATM${ATM}"
        fi
        echo "Processing $I ($ELE $ATM $BCK $FORCEDATMO)"

        cd ${EVNDISPSCRIPTS}

        # list of cuts
        for C in "${CUTS[@]}"
        do
            ANASUMDIR=$DDIR/anasum/anasum_${I}${ATM}_${C}_${ELE}_${BCK}

            echo "ANASUM output directory: $ANASUMDIR"
            
            if [ -f "${ANASUMDIR}/release_test_${C}_${I}${ATM}_Spectra_Comparision.png" ] ; then

                echo "${ANASUMDIR}/release_test_${C}_${I}${ATM}_Spectra_Comparision.png"
           
                cp ${ANASUMDIR}/release_test_${C}_${I}${ATM}_Spectra_Comparision.png  ${FIGUREDIR}
                cp ${ANASUMDIR}/release_test_${C}_${I}${ATM}_Off_region.png ${FIGUREDIR} 
            else 
                echo  "${ANASUMDIR}/release_test_${C}_${I}${ATM}_Spectra_Comparision.png does not exist"    
                continue
            fi
       done

    cd ${FIGUREDIR} 
    cd ../
       echo " " >> ${filename}
       echo "- ${I}${ATM} " >> ${filename}
 
       echo " " >> ${filename}
       echo "| Soft | Moderate |" >> ${filename}
       echo "| ---- | ---- | " >> ${filename}
       echo "| <img src=\"./figures/release_test_soft2tel_${I}${ATM}_Spectra_Comparision.png\" alt=\"spec\" width=\"500\"/> | <img src=\"./figures/release_test_moderate2tel_${I}${ATM}_Spectra_Comparision.png\" alt=\"spec\" width=\"500\"/> |" >> ${filename}
       echo "| Hard | Zenith |" >> ${filename}
       echo  "<img src=\"./figures/release_test_hard2tel_${I}${ATM}_Spectra_Comparision.png\" alt=\"spec\" width=\"500\"/> |  <img src=\"./figures/${I}${ATM}_SZE_0.5deg_Crab_dignostic_zenith_dist.png\" alt=\"zenith\" width=\"500\"/> | " >> ${filename}
       echo "| Off regions |" >> ${filename}
       echo "<img src=\"./figures/release_test_moderate2tel_${I}${ATM}_Off_region.png\" alt=\"zenith\" width=\"300\"/> |" >> ${filename} 

       echo "Release test summary file written to $(readlink -f ${filename})"
    done 
done
cd ${RDIR}


