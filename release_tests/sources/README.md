# Release testing - Crab and published sources

## Overview

Source tests validate an EventDisplay release against a set of published
sources (hard/soft, moderate/weak) over epochs and cut types. Results are
produced in two stages:

1. **Per source** – `source_tests_summary.sh` writes one
   `results_<target>_<epoch>_<cut>.md` per target/epoch/cut into the new
   release's `SourceTests` directory.
2. **Combined** – `prepare_analysis_results_document.sh` concatenates all
   per-source files into a single `AnalysisResults.md`.

## Published sources

Sources to test are listed in `TARGETS.dat`, spanning hard/soft and
moderate/weak targets. Use `run_analysis_all.sh` for the EventDisplay/anasum
results, then summarise and combine per the steps below. Crab-specific plotting
macros remain in `Crab/`.

## DL5 / Gammapy reflected-region analysis

The `ANALYSIS.v2dl5*.sh` scripts are a separate, batch-submitted DL5 workflow.
They call V2DL5's `reflected_region_analysis.py`, which runs the configured
Gammapy 1D reflected-region analysis (dataset creation, reflected background,
power-law fit, flux points, and light curve).  Their results are not consumed by
`source_tests_summary.sh` or by `AnalysisResults.md`; those scripts summarise
the EventDisplay/anasum analysis above.

### What must exist first

The DL5 scripts do **not** create DL3 data.  Before submitting an analysis,
make a DL3 observation store for the same EventDisplay release, analysis type,
and cut configuration, and ensure that it contains every run in the selected
run list and its required `aeff` and `edisp` IRFs.  Install/checkout V2DL5 at
`$EVNDISPSYS/../V2DL5`, including its `data/hip_mag9.fits.gz` star catalogue,
and create the `v2dl5` conda environment.  The submit host also needs the
EventDisplay observatory setup, HTCondor helper scripts, and writable
`$VERITAS_USER_LOG_DIR` and result locations.

For every non-Crab source, a `TARGET.txt` file must contain a SIMBAD-resolvable
target name, because it is substituted into the `on_region.target` setting.
Seven current `TARGETS.dat` entries do not meet this requirement:
`B20912p029`, `IC310`, `LHAASO_J2108p5157`, `RBS1366`, `RGBJ1310p323`,
`SS433`, and `UMA2` lack `TARGET.txt`. `Crab` is handled separately with the
default target name `Crab`. Thus the repository cannot yet complete the full
list. Add and validate the missing target names (and suitable run lists) before
calling it a full-list analysis.

### Submit the analyses

Run these commands from `release_tests/sources`. The launchers read the active
`IRFVERSION`, `IRFMINORVERSION`, and analysis type, then use the standard
release-test locations:

- DL3 stores: `$VERITAS_DATA_DIR/shared/processed_data_${IRFMINORVERSION}/`
  `${VERITAS_ANALYSIS_TYPE:0:2}/dl3_pointlike_<cut>`;
- output: `$VERITAS_USER_DATA_DIR/analysis/Results/${IRFVERSION}/`
  `${VERITAS_ANALYSIS_TYPE:0:2}/v2dl5/<cut>`.

For AP, all launchers submit `soft2tel`, `moderate2tel`, and `hard3tel`; for
NN they submit `supersoftNN2tel`. Override the defaults without editing code:

```bash
export V2DL5_DL3_BASE=/path/to/processed_data_<minor-version>/<AP-or-NN>
export V2DL5_OUTPUT_ROOT=/path/to/results/v2dl5
export V2DL5_CUTS="soft2tel moderate2tel hard3tel"
```

The non-Crab launcher reads `TARGETS.dat` and skips Crab; the Crab launcher
uses the run lists directly in `Crab/`. Both process every matching
`runlist_releaseTesting*.dat`, including special red-HV or offset selections.
Review those lists before submission, or select an explicit set by moving them
out of the matching pattern.

```bash
./ANALYSIS.v2dl5.all.sh

./ANALYSIS.v2dl5.Crab.sh
```

Each call to `ANALYSIS.v2dl5.sh` creates a temporary Condor submission script
under `$VERITAS_USER_LOG_DIR/.../V2DL5`; submit the generated jobs using the
printed command:

```bash
$EVNDISPSCRIPTS/helper_scripts/submit_scripts_to_htcondor.sh <V2DL5-log-dir> submit
```

The actual analysis output and `v2dl5.log` are written below
`$V2DL5_OUTPUT_ROOT/<cut>/<source>_<epoch>` (or the default output root shown
above). Inspect every `v2dl5.log` after the jobs finish, verify that the
requested observations were selected, and retain the generated
fit/flux-point/light-curve products as the DL5 validation artefacts. There is
currently no repository script to collect, compare, or add these DL5 outputs
to `AnalysisResults.md`.

## Updating the source tests summary

### Setup

`run_analysis_all.sh` writes analysis results into:

```text
$VERITAS_USER_DATA_DIR/analysis/Results/${VERSION}/${ANALYSISTYPE}/SourceTests
```

with `${VERSION}` from `$VERITAS_EVNDISP_AUX_DIR/IRFVERSION` (e.g. `v491`),
`${ANALYSISTYPE}` from `$VERITAS_ANALYSIS_TYPE` (`AP`/`NN`).

### 1. Run analyses (only if the anasum logs are missing)

`run_analysis_all.sh` runs the anasum combination and writes anasum **log files**
`<SourceTests>/<target>/<cut>/<epoch>.log` (note: a single command line argument
is required):

```bash
./run_analysis_all.sh run
```

### 2. Per-source summary

`source_tests_summary.sh` parses the anasum log files and writes/updates one
markdown file per target/epoch/cut:

```text
<output directory>/<target>/results_<target>_<epoch>_<cut>.md
```

It builds on the **previous** release: the previous version's markdown files are
copied into the output directory, stale lines for the new version are removed,
and freshly parsed results inserted before the closing code fence (anasum logs
are also copied over).

```bash
./source_tests_summary.sh <data dir with anasum log files> \
                          <directory of last version with results> \
                          <output directory> \
                          <new version>
```

Initial run (no previous version, e.g. v490.7):

```bash
./source_tests_summary.sh \
    $VERITAS_USER_DATA_DIR/analysis/Results/v490/AP/SourceTests \
    . \
    ../../../EventDisplay_Release_v490/SourceTests \
    v490.7
```

Follow-up run (e.g. v491 built on v490 results):

```bash
./source_tests_summary.sh \
    $VERITAS_USER_DATA_DIR/analysis/Results/v491/AP/SourceTests \
    ../../../EventDisplay_Release_v490/SourceTests \
    ../../../EventDisplay_Release_v491/SourceTests \
    v491.0
```

The script iterates over all targets/epochs/cuts in `TARGETS.dat`; all per-source
files land in `<output directory>`.

### 3. Combine into full document

`prepare_analysis_results_document.sh` loops over targets in `TARGETS.dat`,
appends each target's `results_<target>_*.md`, wraps with
`AnalysisResults_header.md`/`AnalysisResults_footer.md`, and concatenates with
`pandoc`:

```bash
./prepare_analysis_results_document.sh ../../../EventDisplay_Release_v491/SourceTests
```

Produces `./AnalysisResults.md`.

### Workflow

```text
run_analysis_all.sh            -> anasum log files  (<T>/<C>/<E>.log)
        |
        v  (per source)
source_tests_summary.sh        -> results_<T>_<E>_<C>.md  (one per source/epoch/cut)
        |
        v  (combined)
prepare_analysis_results_document.sh -> AnalysisResults.md  (single combined document)
```
