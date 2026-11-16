# MC / Data Comparison

**No apptainer usage!**

Scripts and tools to compare Monte Carlo (MC) distributions with observational results from the Crab Nebula.

## Quick Start

```console
./compareDatawithMC.sh <runparameter file> <SZE|MZE|LZE|WOBBLE>
```

Where `<SZE|MZE|LZE|WOBBLE>` specifies the observation conditions:

- `SZE`: Small zenith angles (0-25°, 0.5° wobble)
- `MZE`: Medium zenith angles (40-50°, 0.5° wobble)
- `LZE`: Large zenith angles (50-70°, 0.5° wobble)
- `WOBBLE`: Large wobble offsets (MC at 1° wobble, summer atmosphere only)

NOTE! The zenith angle bins are different compared to those used in the Crab Nebula analysis.

## Prerequisites

### Input Data Requirements

- MC simulation files for each minor epoch (organized by atmosphere type)
- Crab Nebula mscw results and matching `*.mscw.xgb_stereo.root` files for each run
- Run lists for Crab observations (generated separately)

## Preparation Steps

Before running the comparison, you must generate the Crab run lists:

```console
# From release_tests/sources/Crab/
./runlist_generator_from_anasum_log.sh <run parameter file> <anasum-results-directory>
```

This generates run lists for minor epochs, zenith angle ranges, and atmosphere types.
The run lists are saved in `EventDisplay_Release_<version>/Crab/runlists/`.

## Running the Comparison

### Step 1: Prepare Run Parameter File

The `<run parameter file>` must contain the following fields (one per line):

```text
* VERSION         <eventdisplay_version>  # e.g., V6
* SIMTYPE         <simulation_type>       # e.g., CARE, CARE_RedHV
* ATMOSPHERE      <atmosphere_id>         # e.g., 61, 62 (repeat line for multiple values)
* EPOCH           <epoch_id> [nsb]        # e.g., V6_2019_2020s 0
* CRAB_NSB        <nsb_level>             # e.g., 0, 1, or NOTSET
```

The leading `*` is part of the parameter-file syntax. To provide multiple atmospheres or epochs, repeat the corresponding line. If `CRAB_NSB` is `NOTSET`, the script reads the per-epoch NSB value from the optional 4th field of each `* EPOCH ...` line.

### Step 2: Execute Comparison

```console
cd release_tests/montecarlo/mc_data_comparison/
./compareDatawithMC.sh <path/to/run\ parameter\ file> SZE
```

For an MC smearing variant with nominal Crab reconstruction, use the EventDisplay
version supporting separate suffixes and run:

```console
MC_XGB_SUFFIX=xgb_stereo_smear05 DATA_XGB_SUFFIX=xgb_stereo \
  ./compareDatawithMC.sh <path/to/runparameter> SZE
```

Both suffixes default to `xgb_stereo`. They identify the corresponding friend
files, for example `*.mscw.xgb_stereo_smear05.root` for MC and
`*.mscw.xgb_stereo.root` for Crab. Suffixes can contain letters, digits,
underscores and hyphens.

This will:

1. Parse the run parameter file
2. Locate MC simulation files based on epoch and atmosphere
3. Find corresponding Crab observational data
4. Submit Condor jobs for each combination
5. Generate comparison plots as PDF files

### Step 3: Monitor Progress

- Condor jobs are submitted with resource requests: 4000MB RAM, 10GB disk
- Temporary symbolic links are created in: `{output_dir}/tmp/`
- **Note**: Temporary directories must be cleaned up manually after completion

## Output Structure

Results are written to:

```text
EventDisplay_Release_<version>/mc_data_comparison/<analysis_type><disp>/<simulation_type>/[MC-<MC suffix>/DATA-<data suffix>/]
├── <epoch>_ATM<atm>_<ELE>_<wobble>_<nsb>/
│   └── run-<unique-id>/
│       ├── mcdatacomparison.runparameter
│       ├── mcdatacomparison.root
│       ├── mcdatacomparison.log
│       ├── *.pdf                # Comparison plots
│       └── tmp/                 # Job input and symlinks (manual cleanup required)
```

The suffix directories apply to XGB comparisons. Each submission reserves a
new `run-<unique-id>` directory, including for the DispBDT baseline, so repeat
submissions preserve earlier results and can run concurrently. The script prints
each output path. Re-executing the same generated worker script still writes to
its original directory and can overwrite that job's files.

The PDF includes an exploratory r68 versus reconstructed-energy page for MC
and ON−OFF excess. It fits a two-Gaussian radial profile inside
`theta2 < 0.03 deg2` and extrapolates the fitted profile; error bars are
statistical fit errors. Unstable fits are omitted. The estimate depends on the
tail model and reflected-region background, and is not a substitute for the
project's run-bootstrap and closure validation. Input files must have been
produced with the updated EventDisplay executable, `cut=-3`, and a recorded
theta2 cut between 0.03 and 0.035 deg2; older files display an explanatory page.

## Special Cases

- **CARE_RedHV simulations**: Handled with modified BDT cut (BDT=0 instead of 1)
- **Summer vs Winter Atmosphere**: Automatically selected based on epoch suffix ('s' or 'w')
- **Wobble Mode**: Forces atmosphere 61 and 1.0° wobble offset
