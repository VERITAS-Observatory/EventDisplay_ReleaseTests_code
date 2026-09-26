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

## Crab

- use scripts and macros in ./Crab directory (implementation completed)
- other objects: to be done

Mrk501 (implementation completed):

- The steps to run the validation over sources other than Crab:

This should involve soft and hard sources, moderate and very weak sources.

## Published sources

Sources to test are listed in `TARGETS.dat`. Analyse with `run_analysis_all.sh`,
then summarise and combine per the steps below.

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
