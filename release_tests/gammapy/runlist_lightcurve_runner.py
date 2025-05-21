import os
import re
import sys
from pathlib import Path
from gammapy.data import DataStore
import crab_lightcurve_validation


# Function to read all run IDs from a runlist file
def read_runs_from_file(file_path):
    with open(file_path) as f:
        return [int(line.strip()) for line in f if line.strip()]

# Directory containing runlists
download_dir = Path("/EventDisplay_Release_v491/Crab/runlists")
all_files = os.listdir(download_dir)
runlist_files = [f for f in all_files if re.match(r'runlist_releaseTesting.*\.dat', f)]

print(f"Found {len(runlist_files)} runlist files.")


# Collect all unique run IDs
all_runs = set()
for runlist in runlist_files:
    local_path = download_dir / runlist
    runs = read_runs_from_file(local_path)
    all_runs.update(runs)

print(f"Found {len(all_runs)} unique runs across all runlists.")

# Create a combined runlist file
combined_runlist_path = Path("./combined_runlist.dat")
with open(combined_runlist_path, "w") as f:
    for run in sorted(all_runs):
        f.write(f"{run}\n")

print(f"Created combined runlist with {len(all_runs)} runs at {combined_runlist_path}")


combined_runlist_path = Path("./combined_runlist.dat")

for runlist in runlist_files:
    local_path = download_dir / runlist
    print(f"Processing {runlist}")
    sys.argv = [
        "crab_lightcurve_validation.py",
        "--runlist",
        str(local_path)
    ]
    crab_lightcurve_validation.main()