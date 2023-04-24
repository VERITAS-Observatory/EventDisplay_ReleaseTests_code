# run all plotting scripts for all zenith angle ranges
#

if [[ $# < 1 ]]; then
echo "
   $0 <runparameter file>
   
"
exit
fi

BCKMODEL="IGNOREACCEPTANCE"

for N in SZE MZE LZE WOBBLE SZE_0.5deg MZE_0.5deg LZE_0.5deg
do
   root -q -l -b "plot_energy_spectra.C(\"${1}\", \"$N\", \"$BCKMODEL\" )"
   root -q -l -b "plot_lightcurves.C(\"${1}\", \"$N\", \"$BCKMODEL\" )"
#   root -q -l -b "plot_skymaps.C(\"${1}\", \"$N\", \"$BCKMODEL\" )"
#   root -q -l -b "plot_skymaps.C(\"${1}\", \"$N\", \"RB\" )"
done
