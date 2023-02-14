# Energy thresholds

plots energy thresholds and effective areas for different zenith / NSB combinations

This is a consistency check to make sure that the thresholds follow
the expected dependencies as function of zenith and NSB.

```
root -l -q -b 'plot.C("V6.runparameter.dat")'
```

Expect as input the combined effective area files.

It is usually enough to scan through these plots and search for any outliers by eye:
```
<version>/energythresholds/NTel2-PointSource-*/Aeff-Fix*
```

