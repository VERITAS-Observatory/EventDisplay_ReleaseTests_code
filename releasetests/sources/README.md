# Release testing - Crab and published sources

**not completely implemented yet**

Crab:
- use scripts and macros in ./Crab directory (implementation completed)
- other objects: to be done

Mrk501 (implementation completed):
- The steps to run the validation over sources other than Crab:

- Main script: ./run_analysis.sh  [SOURCE] [TYPE] [CUT] [V2DL3_PATH] [GAMMAPY_SCRIPT]

    - ./run_analysis.sh <runparameter file> Mrk501 MSCW moderate2tel
    - ./run_analysis.sh <runparameter file> Mrk501 ANASUM_SUB moderate2tel <V2DL3_PATH>
    - ./run_analysis.sh <runparameter file> Mrk501 ANASUM_FFF moderate2tel 
    - ./run_analysis.sh <runparameter file> Mrk501 V2DL3 moderate2tel <V2DL3_PATH> 
    - root -l 'makeSpec.C(string Idir, string Odir, string Source, string Cut, float fit_emin, float fit_emax, float eref)'
    - ./run_analysis.sh <runparameter file> Mrk501 GAMMAPY moderate2tel <V2DL3_PATH> <GAMMAPY_SCRIPT>
    - ./run_analysis.sh <runparameter file> Mrk501 VALIDATION_PLOT moderate2tel <V2DL3_PATH> <GAMMAPY_SCRIPT>
- The results and plots are saved in $ {VERITAS\_USER\_DATA\_DIR}/analysis/Results/${EDVERSION}/${SOURCE}/${CUT} $ directory

## Introduction

Test code and IRFs with a couple of different (preferable published) results.
This should involve soft and hard sources, moderate and very weak sources.

## TODO

- copy over run lists
- scripts and run lists per major epoch
