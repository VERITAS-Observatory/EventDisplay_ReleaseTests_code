# MC / Data Comparison

**No apptainer usage!**

Scripts and tools to compare Monte Carlo (MC) distributions with observational results from the Crab Nebula.

## Quick Start

```console
./compareDatawithMC.sh <runparameter file> <SZE|MZE|LZE|WOBBLE> <comparison config>
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

Choose a comparison configuration from `configs/`. For example, from this
folder run the mscw-smeared XGB comparison with:

```console
./compareDatawithMC.sh ../../../../EventDisplay_Release_v492/runparameter/V6.AP.runparameter.precuts.dat SZE configs/mscw-smear-v1-xgb.conf
```

The provided cases are:

| Configuration | MC mscw | Reconstruction |
| --- | --- | --- |
| `configs/nominal-dispbdt.conf` | Nominal | DispBDT |
| `configs/nominal-xgb.conf` | Nominal | XGB without ML smearing |
| `configs/ml-smear05-xgb.conf` | Nominal | XGB with ML-level smear05 |
| `configs/mscw-smear-v1-dispbdt.conf` | mscw-smear v1 | DispBDT |
| `configs/mscw-smear-v1-xgb.conf` | mscw-smear v1 | XGB from the smeared mscw |

A configuration is a plain text file, for example:

```text
variant = mscwsmear_v1
mscw_directory = MSCW_RECID0_DISP_mscwsmear_v1
reconstruction = XGB
mc_xgb_suffix = xgb_stereo
data_xgb_suffix = xgb_stereo
```

Copy and edit a configuration for another case. `variant` labels the output;
`mscw_directory` is the actual directory under each
`<epoch>_ATM<atmosphere>_gamma`. Both use letters, numbers, underscores or
hyphens. `reconstruction` is `XGB` or `DispBDT`. The suffixes identify MC and
Crab friend files; both default to `xgb_stereo` and are unused for DispBDT.
The same mscw directory name must exist for each selected epoch and atmosphere.
Separate MC/data suffixes require the updated `compareDatawithMC` executable.

A label does not verify the smearing recipe. Inspect the production logs and
settings and ensure each MC friend was generated from its adjacent mscw file.
The wrapper does not run inference. The worker uses energy method 0.

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

Each result is stored directly in its runlist directory, for example:

```text
mc_data_comparison/AP_DISP/CARE_202404/
└── MC-nominal/XGB/MC-xgb_stereo/DATA-xgb_stereo/
    └── V6_2023_2024w_MC-ATM61_SZE_wobble0.5_NSB400/
        └── data-ATM61/
            ├── comparison.conf
            ├── comparison-settings.txt
            ├── input-runparameter.dat
            ├── crab-runlist.dat
            ├── mcdatacomparison.runparameter
            ├── mcdatacomparison.root
            ├── mcdatacomparison.log
            └── tmp/  # includes the generated worker and Condor logs
```

`MC-mscwsmear_v1` separates the mscw-smeared input, while the XGB suffix
separates ML-only variants. Each submission records resolved MC and data paths,
friend paths, and input settings; inspect the saved worker script for its exact
cut and reconstruction parameters. Preserve the production logs and smearing
configuration separately: a name alone does not establish provenance. A repeated submission to an existing result directory is rejected; move or remove the existing directory before submitting again. Previous outputs are not moved or relabeled. The
`data-ATM61` and `data-generic-runlist` directories represent different Crab
runlists; the generic list is not necessarily restricted to that atmosphere.

The PDF includes an exploratory r68 versus reconstructed-energy page for MC
and ON−OFF excess. It counts the 68% quantile in the existing linear-theta²
histograms and does not extrapolate the tail. It is therefore the containment
inside the selected theta² cut, not an estimate of the untruncated PSF. The standalone ROOT macro compares two saved configurations:

```console
root -l -b -q 'compare_containment.C("configs/nominal-xgb.conf","configs/ml-smear05-xgb.conf")'
```

It searches `../../../../EventDisplay_Release_v492/mc_data_comparison` for
completed results with matching saved configurations. Optional third and fourth
arguments set the search directory and output PDF. Each configuration must
match exactly one result; ambiguous matches are listed. The MC curves and the
Crab excess from the first result are plotted. Check that the selected results
use comparable Crab runlists and observing conditions. Older outputs without
saved configurations cannot be found. All inputs must have matching
`angularTheta2Cut` metadata. The within-bin error estimate is not a statistical
containment uncertainty; use run bootstrapping for that.

## Special Cases

- **Gamma/hadron BDT**: The current worker script sets `BDT=0`; inspect its
  `BDT` setting when choosing gamma/hadron cuts independently of direction reconstruction.
- **Summer vs Winter Atmosphere**: Automatically selected based on epoch suffix ('s' or 'w')
- **Wobble Mode**: Forces atmosphere 61 and 1.0° wobble offset
