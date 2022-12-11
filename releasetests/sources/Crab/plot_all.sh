# run all plotting scripts for all zenith angle ranges
#
if [[ $# < 1 ]]; then
   echo "$0 <runparameter file>"
   echo ""
   exit
fi

# for Z in SZE MZE LZE WOBBLE
for Z in SZE
do
   root -q -l -b "plot_energy_spectra.C(\"${1}\", \"$Z\" )"
   root -q -l -b "plot_lightcurves.C(\"${1}\", \"$Z\" )"
   root -q -l -b "plot_skymaps.C(\"${1}\", \"$Z\", \"RE\" )"
#   root -q -l -b "plot_skymaps.C(\"${1}\", \"$Z\", \"RB\" )"
done
