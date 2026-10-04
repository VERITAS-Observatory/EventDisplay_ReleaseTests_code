"""Check actual ROOT library loading failures, retries and successful caching."""

import json
import os
from pathlib import Path
import subprocess
import tempfile


helper = Path(__file__).resolve().parents[1] / "release_tests/utilities/parameters.C"
with tempfile.TemporaryDirectory() as temporary:
    directory = Path(temporary)
    library = directory / "valid-library.so"
    subprocess.run(["g++", "-shared", "-fPIC", "-x", "c++", "-", "-o", str(library)],
                   input='extern "C" int review_library_marker() { return 42; }\n',
                   text=True, check=True)
    invalid = directory / "invalid-library.so"
    invalid.write_text("This is not a shared library.\n")
    environment = os.environ.copy()
    for variable in ("EVNDISPSYS", "EVNDISP", "VERITAS_VANASUM_LIBRARY"):
        environment.pop(variable, None)
    for candidate in (directory / "missing-library.so", invalid):
        macro = directory / "test_library_load.C"
        macro.write_text(f"""
#include {json.dumps(str(helper))}
#include <iostream>
void test_library_load()
{{
    gSystem->SetDynamicPath({json.dumps(str(directory))});
    gSystem->Setenv("VERITAS_VANASUM_LIBRARY", {json.dumps(str(candidate))});
    if (loadVAnaSumLibrary()) {{ std::cerr << "Failed load reported success" << std::endl; gSystem->Exit(1); }}
    if (loadVAnaSumLibrary()) {{ std::cerr << "Failed load reported success" << std::endl; gSystem->Exit(1); }} // failure must not populate the success cache
    gSystem->Setenv("VERITAS_VANASUM_LIBRARY", {json.dumps(str(library))});
    if (!loadVAnaSumLibrary()) {{ std::cerr << "Successful load reported failure" << std::endl; gSystem->Exit(1); }} // a failed first attempt permits a real retry
    gSystem->Setenv("VERITAS_VANASUM_LIBRARY", "missing-after-success.so");
    if (!loadVAnaSumLibrary()) {{ std::cerr << "Successful load reported failure" << std::endl; gSystem->Exit(1); }} // an actually loaded library stays cached
}}
""")
        result = subprocess.run(["root", "-l", "-b", "-q", str(macro)], env=environment,
                                cwd=directory, text=True, capture_output=True)
        assert result.returncode == 0, result.stdout + result.stderr

print("PASS actual ROOT missing/invalid library, uncached failure, successful retry and cache")
