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
- Crab Nebula mscw results; XGB comparisons also need matching MC and Crab
  stereo friend files for the chosen suffixes
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

Run the examples below from `release_tests/montecarlo/mc_data_comparison/`.
`RECOMETHOD` is set **inside `compareDatawithMC.sh`**; edit it before running
the desired reconstruction. It is not selected by the suffix environment
variables. The worker uses energy reconstruction method 0 for all three examples.

**DispBDT direction and energy:** set `RECOMETHOD=0` in the script, then run:

```console
./compareDatawithMC.sh ../../../../EventDisplay_Release_v492/runparameter/V6.AP.runparameter.precuts.dat SZE
```

This mode does not read XGB stereo friends. The direction-reconstruction
DispBDT is separate from any BDT used for gamma/hadron selection.

**Nominal XGB direction:** set `RECOMETHOD=2` in the script, then run:

```console
MC_XGB_SUFFIX=xgb_stereo DATA_XGB_SUFFIX=xgb_stereo \
  ./compareDatawithMC.sh ../../../../EventDisplay_Release_v492/runparameter/V6.AP.runparameter.precuts.dat SZE
```

**Smeared XGB MC and nominal Crab XGB direction:** keep `RECOMETHOD=2`, then run:

```console
MC_XGB_SUFFIX=xgb_stereo_smear05 DATA_XGB_SUFFIX=xgb_stereo \
  ./compareDatawithMC.sh ../../../../EventDisplay_Release_v492/runparameter/V6.AP.runparameter.precuts.dat SZE
```

Switch between the two XGB cases by changing `MC_XGB_SUFFIX` on the command
line. These inline environment assignments apply only to that invocation. If
the variables are unset, both suffixes default to `xgb_stereo`; explicitly
setting them as above also avoids surprises from previously exported values.
They identify existing friend files, for example
`*.mscw.xgb_stereo_smear05.root` for MC and `*.mscw.xgb_stereo.root` for
Crab. Every selected MC file needs the requested friend. The wrapper does not
run XGB inference or create friends; inspect the inference log or frozen YAML
to establish the smearing configuration. Separate MC/data suffixes require the
updated, rebuilt `compareDatawithMC` executable. Suffixes can contain letters,
digits, underscores and hyphens.

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

For example, DispBDT results are written to:

```text
mc_data_comparison/AP_DISP/CARE_202404/DispBDT/
└── V6_2023_2024w_MC-ATM61_SZE_wobble0.5_NSB400/
    ├── data-ATM61/<date-time>-<unique-id>/comparison_DispBDT_data-ATM61.pdf
    └── data-generic-runlist/<date-time>-<unique-id>/comparison_DispBDT_data-generic-runlist.pdf
```

For XGB, `DispBDT/` is replaced by `XGB/MC-<MC suffix>/DATA-<data suffix>/`,
and the PDF name includes both suffixes. Each dated directory also contains
`mcdatacomparison.root`, `mcdatacomparison.log`, a run-parameter copy, the
selected `crab-runlist.dat`, `comparison-settings.txt` and `tmp/`.
The `data-ATM61` and `data-generic-runlist` directories represent different
Crab runlists; the generic list is not necessarily restricted to that atmosphere.

Each submission reserves a new dated directory, so repeat submissions preserve
earlier results and can run concurrently. The script prints each output path.
Re-executing the same generated worker script still writes to its original
directory and can overwrite that job's files. Existing results in the previous
directory layout are left in place.

The PDF includes an exploratory r68 versus reconstructed-energy page for MC
and ON−OFF excess. It fits a two-Gaussian radial profile inside
`theta2 < 0.03 deg2` and extrapolates the fitted profile; error bars are
statistical fit errors. Unstable fits are omitted. The estimate depends on the
tail model and reflected-region background, and is not a substitute for the
project's run-bootstrap and closure validation. Input files must have been
produced with the updated EventDisplay executable, `cut=-3`, and a recorded
theta2 cut between 0.03 and 0.035 deg2; older files display an explanatory page.

## Special Cases

- **Gamma/hadron BDT**: The current worker script sets `BDT=0`; inspect its
  `BDT` setting when choosing gamma/hadron cuts independently of direction reconstruction.
- **Summer vs Winter Atmosphere**: Automatically selected based on epoch suffix ('s' or 'w')
- **Wobble Mode**: Forces atmosphere 61 and 1.0° wobble offset
