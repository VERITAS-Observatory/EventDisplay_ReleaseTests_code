# Radial acceptance calculation

Mostly M82 runs are used for the radial acceptance analysis, see ./runlists

## Calculation of radial acceptances

Submit jobs for radial acceptance calculations:
```
./calculate_radialAcceptances.sh <version>
```

radial acceptances are written to:
```
$VERITAS_USER_DATA_DIR/analysis/Results/RadialAcceptances/
```

## Plotting of radial acceptances

Plot acceptances for all epochs and cuts:
```
root -l -q -b 'plot_radialAcceptances.C("v483")'
```

## Testing radial acceptances

Analyse M82 fields to make sure that skymaps are flat
(this does not work for V4, as this is a list of mixed
runs, not towards one single target)

Step 1 to analyse run-wise with anasum:
```
./test_radialAcceptances.sh <version> SUB <RE/RB>
```
Step 2 to combine anasum file
```
./test_radialAcceptances.sh <version> FFF <RE/RB>
```

Plotting:
```
root -l -q -b 'plot_skymaps.C( "v483", "RE")'
root -l -q -b 'plot_skymaps.C( "v483", "RB")'
```
Output (pdfs) are written to ../../<version>/radialAcceptances/
