# run all plotting scripts for all zenith angle ranges
#
if [[ $# < 1 ]]; then
   echo "$0 <runparameter file>"
   echo ""
   exit
fi

BCKMODEL="IGNOREACCEPTANCE"

for Z in SZE MZE LZE WOBBLE LZE_0.5deg MZE_0.5deg SZE_0.5deg
do
   root -q -l -b "plot_energy_spectra.C(\"${1}\", \"$Z\", \"$BCKMODEL\" )"
   root -q -l -b "plot_lightcurves.C(\"${1}\", \"$Z\", \"$BCKMODEL\" )"
   root -q -l -b "plot_skymaps.C(\"${1}\", \"$Z\", \"$BCKMODEL\" )"
#   root -q -l -b "plot_skymaps.C(\"${1}\", \"$Z\", \"RB\" )"
done
