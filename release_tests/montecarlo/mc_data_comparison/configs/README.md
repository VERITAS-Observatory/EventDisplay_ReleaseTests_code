# Comparison configurations

These files select the MC production, reconstruction method and, for XGB,
friend-file suffixes. Pass one to `../compareDatawithMC.sh` when submitting a
comparison. They describe the inputs; they do not contain the results.

For release v492, results are stored under
`EventDisplay_Release_v492/mc_data_comparison/`, in directories for the analysis,
simulation type, MC variant, reconstruction, observing conditions and Crab
runlist. Each result directory contains `comparison.conf`,
`comparison-settings.txt`, `mcdatacomparison.root` and the comparison PDF.
Older results can lack `comparison.conf`. A repeat submission to an existing
result directory is rejected to preserve its files.

From the parent directory, compare two configurations with:

```sh
root -l -b -q 'compare_containment.C("configs/nominal-xgb.conf", "configs/mscw-smear-v1-xgb.conf")'
```

The macro searches the v492 results by default and writes
`containment_comparison.pdf` in the current directory, printing its full path.
It plots MC from both results and Crab from the first. When several results
match, it selects a unique ATM61 result if available; otherwise it reports the
ambiguity. Check the printed paths and input settings for the intended conditions.
The parent [README](../README.md) describes the settings and optional arguments.
