# Gammapy point source campaign

Install `V2DL5-Binary-Analysis` in the `v2dl5` environment (`pip install -e .`
in that repository). Use indexed DL3 stores for the intended release, AP/NN and
cuts. This workflow does not create DL3 data. Run from `release_tests/sources`:

```bash
conda activate v2dl5
python source_checks.py prepare \
    --output /absolute/path/to/new-campaign \
    --dl3-base /absolute/path/to/processed_data_<minor>/AP \
    --release v492 --analysis-type AP \
    --cuts moderate2tel soft2tel hard3tel \
    --cache /absolute/path/to/reduction-cache
```

Start with `--source Crab` (repeatable). For NN specify
`--analysis-type NN --cuts supersoftNN2tel`. Declare moderate2tel as the primary
AP result; other cuts share events and are diagnostics. The output directory
must be new. Preparation does not submit jobs. It writes `manifest.json`,
normalized run lists, per-job configurations and eligible `run.sh`/`job.sub`
files. Review `report.md` and the manifest before running.

Original lists stay intact. Duplicate IDs are recorded and removed from generated
selections, overlaps are recorded, and the annotated Crab `runs_with_problems`
file is diagnostic only. The unfiltered inventory has 94 science selections.
A missing requested run blocks its job rather than silently reducing coverage.
Workers perform deeper HDU, IRF, timing and exposure checks before reduction.

## Source definitions

`source_checks.yml` freezes numeric ICRS positions from the local VERITAS catalogue.
LHAASO_J2108p5157, RGBJ1310p323, SS433 and TXS1452p516 need reviewed coordinates
and field exclusions; Tycho needs exclusion review. Complete their entries and
remove `blocked` after review, then prepare a new campaign. SS433 central-object
and jet positions are different hypotheses. Point source results do not represent
an extended-source total flux. Optional `regions_file` is a DS9 sky region file,
resolved relative to the registry, for neighbouring/extended emission.

## Execution and reports

```bash
python source_checks.py run /absolute/path/to/new-campaign
# Or submit individual eligible jobs on the analysis host:
condor_submit /absolute/path/to/new-campaign/<release>/AP/<cut>/<source>/<selection>/job.sub
python source_checks.py collect /absolute/path/to/new-campaign
```

Workers use the absolute Python executable active during preparation. All paths
must be accessible on execute nodes. Initial resources are 8 GB memory and 5 GB
disk; measure the pilot before scaling. Local execution continues independent
jobs and returns nonzero if any declared job is blocked or fails. `collect`
regenerates ECSV/Markdown reports without running analyses. Plots are optional
(`prepare --plots`). Nightly light curves are disabled in the release template;
enable them through a custom `--config` when needed.

Each result contains resolved configuration, checksums/versions, availability and
selection tables, run-wise on/off datasets and geometry, masks, fitted model and
covariance, flux points, fixed-index integral flux/TS/limit, and `status.json`.
Numerical products precede plotting. Fit and background failures stay visible.
Weak-source fixed-index products can survive a failed free-index fit.

The default integral test uses a PL index of 2.5. It is separate from the free-index
spectral fit. Requested 1–20 TeV edges snap to the data grid; ECSV/Markdown record
the actual band (approximately 1–19.95 TeV for the template). Unsupported bands
fail explicitly. Limits are one-sided 95%. Gammapy's `UL_CONF` denotes the
corresponding central probability (90% for 1.64485 sigma); `ONE_SIDED_CONF` records
the one-sided convention explicitly. TS here is the normalization-only test in
that band, not a trials-corrected discovery claim.

Exact completed attempts resume after input/settings/code/product checks. Failed,
partial or changed attempts require a new campaign/output directory. An optional
shared cache reuses only identical reductions, including input contents, IRFs,
coordinates/radius, mask geometry, axes, fit bounds, BTIs and engine versions.

## Release comparisons and validation

Prepare common-run campaigns with `prepare --reference /path/to/other-campaign`
on both releases. Keep full-coverage campaigns separately. Then:

```bash
python source_checks.py compare /path/to/current-common /path/to/previous-common
```

`comparison.ecsv` reports flux changes only for completed jobs with identical
accepted IDs, scientific settings and effective flux bands. Correlated releases
are not assigned an independent-error significance. Compare exposure and run
statistics in `data/runs.ecsv` and investigate changes in energy coverage and OFF
geometry. Existing anasum summaries remain independent reference products.

Before a production campaign validate Crab, a non-Crab target, a weak source,
epoch/red-HV/offset controls and invalid inputs. Match anasum runs, energy and
direction cuts, deadtime/BTIs and background exclusions. Freeze numerical
regression tolerances from those comparisons. Software completion alone does
not establish scientific release validity. Production-store coverage, source
hypotheses and exclusions, IRF support and energy policy still need that pilot.

For individual jobs the legacy `ANALYSIS.v2dl5*.sh` wrappers remain available.
They use the installed package/catalogue and propagate worker failures. Use the
campaign command for registry, normalized selections and complete accounting.
