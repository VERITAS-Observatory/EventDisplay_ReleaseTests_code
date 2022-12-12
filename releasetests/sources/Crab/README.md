# Crab analysis 

Scripts and macros for epoch-dependent Crab analysis.

The following steps need to be done in the described sequence.

Directory structure expected:

- Crab evndisp analysis files in in `$VERITAS_USER_DATA_DIR/analysis/Results/<version>/<anatype>/Crab/evndisp`
- Crab mscw_energy analysis files in `$VERITAS_USER_DATA_DIR/analysis/Results/<version>/<anatype>/Crab/mscw`
- all data files and products from this analysis will be written to ../../../EventDisplay_ReleaseTests_<version>/sources/Crab/

## Runparameter files

Parameters required for the analysis are all listed in parameter files. This includes:

- Eventdisplay version
- Major and minor epochs
- simulation types
- object to be analysed
- ...

see example for [EventDisplay_ReleaseTests_v490/](https://github.com/VERITAS-Observatory/EventDisplay_ReleaseTests_v490/V6.runparameter.dat)

## Analysis of Crab data

Analysis of all Crab data with Eventdisplay for epochs V4, V5, V6, and V6.redHV.

e.g. for V6, do in the Eventdisplay scripts directory:
```
./ANALYSIS.evndisp.sh <this directory/runlist_releaseTestingV6.dat> $VERITAS_USER_DATA_DIR/analysis/Results/<version>/Crab/evndisp
```
followed by:
```
./ANALYSIS.mscw_energy.sh <this directory/runlist_releaseTestingV6.dat> \
                          $VERITAS_USER_DATA_DIR/analysis/Results/<version>/Crab/evndisp \
                          $VERITAS_USER_DATA_DIR/analysis/Results/<version>/Crab/mscw_energy
```

## Linking of MSCW files and run list generation

Generates run lists for each minor epoch, atmospheres, zenith angle range.

MSCW results should be processed all into one single directory.

Run with:
```
./runlist_generator.sh <runparameter file>
```
for
- linking into yearly sets. 
- selection of ATM61 and 62 files
- apply cut on mean elevation of a specific run
- generate run lists

(this may take a while)

## Run anasum analysis:

Individual runs (submission to job queue):
```
./anasum_yearly.sh <runparameter file> SUB SZE RE <V2DL3_DIR>
```
for reflected region model (RE), and small zenith angle files (SZE).

`V2DL3_DIR` is pointing towards the V2DL3 installation directory (necessary at the anasum step already for filling the V2DL3 conversion scripts).

Combine files (local executation):
```
./anasum_yearly.sh <runparameter file> FFF SZE RE
```

Convert each anasum file to DL3 file (local execution):
```
./anasum_yearly.sh <runparameter file> V2DL3 SZE RE <V2DL3_DIR>
```

We need reference spectral flux points to get the Gammapy flux points in same
energy bins, so first run 
```
root -q -l -b 'plot_energy_spectra.C("<runparameter file>", "SZE" )'
```

It writes the csv file with flux points and text file with power law fit parameters in anasum output directory.

Run Gammapy-0.20.1 analysis:
```
./anasum_yearly.sh <runparameter file> GAMMAPY SZE RE V2DL3_DIR GAMMAPY_SCRIPT_DIR
```
It writes the fits file having flux points from Gammapy analysis in anasum dir. This needs to have reference flux point file generated above in the anasum directory


Make spectral comparision plots:
```
./anasum_yearly.sh <runparameter file> VALIDATION_PLOT SZE RE V2DL3_DIR GAMMAPY_SCRIPT_DIR
```
It will plot a spectral comparision plot (as shown [here](https://github.com/VERITAS-Observatory/Eventdisplay_ReleaseTests/tree/main/v487e/Crab/DL3_results) ) in anasum directoy.


**(Text below only for Eventdisplay)**

## Plotting


### Spectra

plot energy spectra 

- pdfs in figures directory

```
root -q -l -b 'plot_energy_spectra.C("<runparameter file>", "SZE" )'
```
- 2. argument: zenith angle range (SZE, MZE, LZE)

Colors / markers in plot for spectra from the literature:
- red: Whipple 1998
- green (light): HESS PL 2006
- blue: HESS PLEC 2006
- yellow: HESS BRPL 2006
- violet: HEGRA 2004
- cyan: MAGIC PL 2008
- green (dark): MAGIC VPL 2014
- orange: VERITAS 2015

### Light curves

```
root -q -l -b 'plot_lightcurves.C("<runparameter file>", "SZE" )'
```
- 2. argument: zenith angle range (SZE, MZE, LZE)

Orange solid/dashed line: average flux over all runs (+-1sigma)
Orange dotted lines: average flux +-20% systematic range

## Sky maps

```
root -l -q -b 'plot_skymaps.C("<runparameter file>", "SZE", "RE" )'
```

- 2. argument: zenith angle range (SZE, MZE, LZE)
- 3. argument: background model (RE=reflected region, RB=ring background)


