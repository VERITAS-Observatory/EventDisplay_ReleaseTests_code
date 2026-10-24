# Gammapy point source campaign

Install `V2DL5-Binary-Analysis` in the `v2dl5` environment. If
`v2dl3-generate-index-file` is not already on `PATH`, install V2DL3 there once
with `pip install -e /path/to/V2DL3`. The campaign command uses that V2DL3 tool
to index existing converted DL3 FITS files; it does not create DL3 data. Run
from `release_tests/sources`:

```bash
conda activate v2dl5
python source_checks.py prepare \
    --output /absolute/path/to/new-campaign \
    --dl3-base /absolute/path/to/processed_data_<minor>/AP \
    --release v492 --analysis-type AP \
    --workers 4 \
    --cache /absolute/path/to/reduction-cache
```

By default, this single preparation command discovers every `dl3_pointlike_*`
directory under `--dl3-base`, builds campaign-local `hdu-index.fits.gz` and
`obs-index.fits.gz` for each cut from its DL3 FITS files, then prepares every
source and science selection in `TARGETS.dat`. The
`v2dl3-generate-index-file` command must be on
`PATH`; override it with `--indexer /path/to/v2dl3-generate-index-file` if
needed. To select cuts explicitly, pass `--cuts moderate2tel soft2tel`.
Preparation uses up to two workers by default. Set `--workers N` (or `-j N`)
to index cuts concurrently, then prepare targets concurrently, in one campaign.
Each target's selections stay together so overlap accounting is preserved.
The manifest and reports are written once after all preparation tasks finish,
in source and cut order. An indexing failure blocks that cut's jobs while other
cuts continue. Use `--workers 1` for serial preparation.

For NN use `--analysis-type NN`; the available NN cuts are discovered the same
way. Use `--source Crab` only for an optional pilot.

Without `--source`, indexing covers every DL3 file for each selected cut. With
`--source`, the campaign gathers that source's normalized run IDs (intersected
with `--reference` when supplied) and passes a run-list file to the V2DL3
indexer. It filters by numeric FITS filename prefix before opening files for
indexing. The manifest records the
index scope and selected run IDs. The command prints the input and output paths,
elapsed indexing time, available observation count, and selection preparation
progress. Pass only needed cuts with `--cuts` to limit the number of stores
indexed.

Index files live in the new campaign directory, so preparation does not rewrite
the release's DL3 store. The output directory must be new. Preparation does not
submit or run analyses. It writes `manifest.json`, normalized run lists,
campaign-local indexes, per-job configurations and eligible `run.sh`/`job.sub`
files. Review `report.md` and the manifest before running. A cut with no
converted DL3 FITS files or a failed index generation is marked blocked with
the indexer's error.

Original lists stay intact. Duplicate IDs are recorded and removed from generated
selections, overlaps are recorded, and the annotated Crab `runs_with_problems`
file is diagnostic only. The unfiltered inventory has 94 science selections.
Requested runs missing from the DL3 store are listed in the job's `missing` field
but do not block it. Workers check HDUs, IRFs, timing and exposure before
reduction; unusable runs are skipped and listed in `availability.ecsv` and
`data/selection.ecsv` (job status `partial`). Only a job without any usable run fails.

## Source definitions

Each source directory's `TARGET.txt` supplies the target name, falling back to
the directory name when that file is absent (for example, Crab). V2DL5 resolves
its coordinates through Astropy's name resolver when the analysis runs and
records them in `config.resolved.yaml`. Preparation needs no coordinate catalogue
or name-resolution network access. To change a source name, edit its `TARGET.txt`
and prepare a new campaign.

Background exclusions remain configurable through the analysis template
(`--config`), including `datasets.exclusion_region.regions_file` for a DS9 region
file. Use an absolute path for that file.

## Execution and reports

```bash
python source_checks.py run /absolute/path/to/new-campaign --workers 2
# Or submit individual eligible jobs on the analysis host:
condor_submit /absolute/path/to/new-campaign/<release>/AP/<cut>/<source>/<selection>/job.sub
python source_checks.py collect /absolute/path/to/new-campaign
```

Workers use the absolute Python executable active during preparation. All paths
must be accessible on execute nodes. Initial resources are 8 GB memory and 5 GB
disk per job; start with two local workers and raise `--workers` only when the
machine has memory for more concurrent analyses. Set `--workers 1` for serial
execution. Local execution prints each job's start, completion or failure, with
a 60-second heartbeat for long jobs; detailed output is written to that job's
`v2dl5.log`. It continues independent jobs and returns nonzero if any declared
job is blocked or fails. `collect` regenerates ECSV/Markdown reports without
running analyses. Plots are optional
(`prepare --plots`). Nightly light curves are disabled in the release template;
enable them through a custom `--config` when needed.

Each result contains resolved configuration, checksums/versions, availability and
selection tables, run-wise on/off datasets, masks, the fitted model and covariance,
flux points, `data/significance.yaml` and `status.json`. `collect` writes
`summary.ecsv` and `report.md` with, per source/selection/cut:

- Significance: Li & Ma (WStat `sqrt(TS)`) from the summed ON/OFF counts of all
  events in the reflected regions, without energy range or safe-energy cut
  (`n_on`, `n_off`, effective `alpha`, `excess`, `ontime_h`).
- Spectrum: power law `dN/dE = N0 (E / 1 TeV)^-index`, forward-folded fit of
  the stacked ON/OFF spectrum of all runs in the safe energy range (effective area > 10% of maximum).
  `summary.ecsv` keeps all fit values; `report.md` shows index and `N0` only for
  detections (significance >= 5 and successful fit).

A failed spectral fit (expected for weak sources) does not fail the job.
Differential flux points are in `data/flux_points.ecsv`.

`run` reuses results whose inputs, settings and code are unchanged (`--resume`);
otherwise the job is analysed again in place. An optional
shared cache reuses only identical reductions, including input contents, IRFs,
coordinates/radius, mask geometry, axes, fit bounds, BTIs and engine versions.

## Release comparisons and validation

Prepare common-run campaigns with `prepare --reference /path/to/other-campaign`
on both releases. Keep full-coverage campaigns separately. Then:

```bash
python source_checks.py compare /path/to/current-common /path/to/previous-common
```

`comparison.ecsv` reports the significance ratio, index difference and `N0` ratio
for matched jobs and flags different numbers of accepted runs. Correlated releases
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
campaign command for normalized selections and complete accounting.
