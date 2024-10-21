# MC / data comparison

Scripts and tools to compare MC distributions with results from the Crab Nebula.

Fill and plot distributions with

```console
./compareDatawithMC.sh <runparameter file> <SZE/MZE/LZE/WOBBLE>
```

Requires as input:

- MC files for each minor epoch
- Crab results for each minor epoch

**important:**
first run linking of epochs from `../../sources/Crab/`: `./runlist_generator.sh V6`
(or for any other epoch)

Output and plots are written as PDFs into the `../../../../EventDisplay_Release_<version>/mc_data_comparison/` directories
