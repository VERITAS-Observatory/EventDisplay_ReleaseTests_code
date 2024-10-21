# Pedvars (nsb) as function of correction factors

Plotting of mean pedvars from simulations vs throughput correction
factor for different NSB levels plus a linear fitting.

Note that this is showing simply that the correction factors are applied.

Requires MC mscw files to be on disk (which they are usually not)

First run

```console
./read_pedvar.sh <runparameter file>
```

then plot the results with

```console
root -l -q -b 'plot.C("runparameter file")'
```

Results are written and plotted (PDFs) into: `../../<version>/nsb/`
