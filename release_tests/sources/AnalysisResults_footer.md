## Technical

Preparation of markdown files for each sources uses the script `source_tests_summary.sh` which is located in the `release_tests` directory. The script is run from the `release_tests` directory and takes the following arguments:

```bash
./source_tests_summary.sh <data dir with anasum log files> <directory of last version with results> <output directory> <new version>
```

Prepare the full document (requires pandoc) with:

```bash
./prepare_analysis_results_document.sh ../../../EventDisplay_Release_v491/SourceTests
```
