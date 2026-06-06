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
- Crab Nebula mscw results for each minor epoch
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
* ATMOSPHERE      <atmosphere_id>         # e.g., 61*, 62*
* EPOCH           <epoch_id>              # e.g., V4*, V5*, V6*
* CRAB_NSB        <nsb_level>             # e.g., 0, 1, or NOTSET
```

Fields marked with `*` support wildcards for multiple values.

### Step 2: Execute Comparison

```console
cd release_tests/montecarlo/mc_data_comparison/
./compareDatawithMC.sh <path/to/run\ parameter\ file> SZE
```

This will:

1. Parse the run parameter file
2. Locate MC simulation files based on epoch and atmosphere
3. Find corresponding Crab observational data
4. Submit Condor jobs for each combination
5. Generate comparison plots as PDF files

### Step 3: Monitor Progress

- Condor jobs are submitted with resource requests: 4000MB RAM, 10GB disk
- Temporary symbolic links are created in: `{output_dir}/tmp/{uuid}/`
- **Note**: Temporary directories must be cleaned up manually after completion

## Output Structure

Results are written to:

```text
EventDisplay_Release_<version>/mc_data_comparison/<analysis_type><disp>/<simulation_type>/
├── <epoch>_ATM<atm>_<ELE>_<wobble>_<nsb>/
│   ├── mcdatacomparison.runparameter
│   ├── mcdatacomparison.root
│   ├── mcdatacomparison.log
│   └── *.pdf                    # Comparison plots
└── tmp/                         # Temporary symlinks (manual cleanup required)
```

## Special Cases

- **CARE_RedHV simulations**: Handled with modified BDT cut (BDT=0 instead of 1)
- **Summer vs Winter Atmosphere**: Automatically selected based on epoch suffix ('s' or 'w')
- **Wobble Mode**: Forces atmosphere 61 (summer) and 1.0° wobble offset
