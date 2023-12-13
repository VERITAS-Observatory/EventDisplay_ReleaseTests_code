# Crab analysis

Scripts and macros for epoch-, zenith, and observation-type dependent Crab analysis.

Steps need to be executed in the described sequence.

## Expected directory structure

- Crab evndisp analysis files in in `$VERITAS_USER_DATA_DIR/analysis/Results/<version>/<anatype>/Crab/evndisp`
- Crab mscw_energy analysis files in `$VERITAS_USER_DATA_DIR/analysis/Results/<version>/<anatype>/Crab/mscw`
- all data files and products from this analysis will be written to `../../../EventDisplay_Release_<version>/sources/Crab/`

## Run parameter files

Parameters required for the analysis are all listed in parameter files. This includes:

- Eventdisplay version
- Major and minor epochs
- simulation types
- object to be analyzed
- ...

see example for [EventDisplay_Release_v490/](https://github.com/VERITAS-Observatory/EventDisplay_Release_v490/runparameter/V6.runparameter.dat)

## Analysis

Analysis of all Crab data with Eventdisplay for epochs V4, V5, V6, and V6.redHV.
Result files should be written to a single directory (linked in the next steps to epochs and elevation ranges).

e.g. for V6, do in the Eventdisplay scripts directory:

```bash
./ANALYSIS.evndisp.sh <this directory/runlist_releaseTestingV6.dat> $VERITAS_USER_DATA_DIR/analysis/Results/<version>/Crab/evndisp
```

followed by:

```bash
./ANALYSIS.mscw_energy.sh <this directory/runlist_releaseTestingV6.dat> \
                          $VERITAS_USER_DATA_DIR/analysis/Results/<version>/Crab/evndisp \
                          $VERITAS_USER_DATA_DIR/analysis/Results/<version>/Crab/mscw_energy
```

## Linking of MSCW files and run list generation

Generates run lists for each minor epoch, atmospheres, zenith angle range.

MSCW results should be processed all into one single directory (or: mscw files of Crab observations should be linked into one single directory).

Generate links with:

```bash
./runlist_generator.sh <runparameter file>
```

for

- linking into yearly sets.
- selection of ATM61 and 62 files
- apply cut on mean elevation of a specific run
- generate run lists

(this may take a while)

## Run anasum analysis

Individual runs (submission to job queue):

```bash
./anasum_yearly.sh <runparameter file> SUB SZE RE
```

for reflected region model (RE), and small zenith angle files (SZE).

Combine files:

```bash
./anasum_yearly.sh <runparameter file> FFF SZE RE
```

## Plotting

### Spectra

plot energy spectra

- pdfs in figures directory

```bash
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

```bash
root -q -l -b 'plot_lightcurves.C("<runparameter file>", "SZE" )'
```

- 2. argument: zenith angle range (SZE, MZE, LZE)

Orange solid/dashed line: average flux over all runs (+-1sigma)
Orange dotted lines: average flux +-20% systematic range

## Sky maps

```bash
root -l -q -b 'plot_skymaps.C("<runparameter file>", "SZE", "RE" )'
```

- 2. argument: zenith angle range (SZE, MZE, LZE)
- 3. argument: background model (RE=reflected region, RB=ring background)
