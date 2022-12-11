# Energy thresholds

plots energy thresholds and effective areas for different zenith / NSB combinations

Mostly a consistency check to make sure that the thresholds follow
the expected dependencies as function of zenith and NSB.

```
root -l -q -b 'plot.C("../../../v483/V6.runparameter.dat")'
```

Expect as input the combined effective area files.

For consistency checks, it is usually enough to scan through these plots:
```
<version>/energythresholds/NTel2-PointSource-*/Aeff-Fix*
```

