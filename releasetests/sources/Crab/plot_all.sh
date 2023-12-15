#!/bin/bash
# run all plotting scripts for all zenith angle ranges
#

if [[ $# -lt 1 ]]; then
echo "
   $0 <runparameter file>

"
exit
fi

BCKMODEL="IGNOREACCEPTANCE"
PSPACE="SZE_0.5deg MZE_0.5deg LZE_0.5deg SZE MZE LZE WOBBLE"
if [[ $1 == *"redHV"* ]]; then
    PSPACE="SZE_0.5deg MZE_0.5deg LZE_0.5deg"
fi

for N in $PSPACE
do
   root -q -l -b "plot_energy_spectra.C(\"${1}\", \"$N\", \"$BCKMODEL\" )"
   root -q -l -b "plot_lightcurves.C(\"${1}\", \"$N\", \"$BCKMODEL\" )"
#   root -q -l -b "plot_skymaps.C(\"${1}\", \"$N\", \"$BCKMODEL\" )"
#   root -q -l -b "plot_skymaps.C(\"${1}\", \"$N\", \"RB\" )"
done
