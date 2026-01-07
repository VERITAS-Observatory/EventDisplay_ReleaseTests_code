# Crab analysis

Scripts and macros for epoch-, zenith, and observation-type dependent Crab analysis.
Analysis depends on pre-processed data products (up to anasum-per run).

## Run parameter files

Parameters required for the analysis are all listed in parameter files. This includes:

- Eventdisplay version
- Major and minor epochs
- simulation types
- object to be analyzed
- ...

Most important parameter files are (examples for v491)::

- [AP StdHV V6](https://github.com/VERITAS-Observatory/EventDisplay_Release_v491/blob/main/runparameter/V6.AP.runparameter.dat)
- [AP RedHV V6](https://github.com/VERITAS-Observatory/EventDisplay_Release_v491/blob/main/runparameter/V6redHV.AP.runparameter.dat)
- [NN StdHV V6](https://github.com/VERITAS-Observatory/EventDisplay_Release_v491/blob/main/runparameter/V6.NN.runparameter.dat)
- [NN RedHV V6](https://github.com/VERITAS-Observatory/EventDisplay_Release_v491/blob/main/runparameter/V6redHV.NN.runparameter.dat)
- [AP StdHV V5](https://github.com/VERITAS-Observatory/EventDisplay_Release_v491/blob/main/runparameter/V5.AP.runparameter.dat)
- [AP StdHV V4](https://github.com/VERITAS-Observatory/EventDisplay_Release_v491/blob/main/runparameter/V4.AP.runparameter.dat)

## Run list generation using anasum log file

Generates run lists for each minor epoch, atmospheres, zenith angle range.

```bash
./runlist_generator_from_anasum_log.sh \
   ../../../../EventDisplay_Release_v491/runparameter/V6redHV.AP.runparameter.dat \
   $VERITAS_USER_DATA_DIR/analysis/Results/v491/AP/PreProcessing/anasum_moderate2tel
```

for

- generate run lists
- selection of ATM61 and ATM62 files
- apply cut on mean elevation of a specific run

## Run anasum analysis

Combine files using pre-processed anasum files and run list generated in step before:

```bash
./anasum_yearly.sh <runparameter file> <anasum-run-wise directory>
```

## Plotting

use `plot_all.sh` to generate spectra and light curves for each of above run lists:

```bash
./plot_all.sh <anasum directory> <output directory>
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
