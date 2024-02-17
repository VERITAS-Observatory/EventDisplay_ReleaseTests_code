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

Most important parameter files are:

- [AP StdHV V6](https://github.com/VERITAS-Observatory/EventDisplay_Release_v490/blob/main/runparameter/V6.AP.runparameter.dat)
- [AP RedHV V6](https://github.com/VERITAS-Observatory/EventDisplay_Release_v490/blob/main/runparameter/V6redHV.AP.runparameter.dat)
- [NN StdHV V6](https://github.com/VERITAS-Observatory/EventDisplay_Release_v490/blob/main/runparameter/V6.NN.runparameter.dat)
- [NN RedHV V6](https://github.com/VERITAS-Observatory/EventDisplay_Release_v490/blob/main/runparameter/V6redHV.NN.runparameter.dat)
- [AP StdHV V5](https://github.com/VERITAS-Observatory/EventDisplay_Release_v490/blob/main/runparameter/V5.AP.runparameter.dat)
- [AP StdHV V4](https://github.com/VERITAS-Observatory/EventDisplay_Release_v490/blob/main/runparameter/V4.AP.runparameter.dat)

## Run list generation using anasum log file

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
