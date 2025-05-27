import gc
import logging
import multiprocessing as mp
import os
import re
from functools import partial
from pathlib import Path

import crab_lightcurve_validation
from gammapy.data import DataStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(processName)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = "/home/eshita/Documents/VERITAS/"


def generate_index_files(runlist_path, runlist_name):
    path = Path(DATA_DIR + "Data/kNN/v2dl3_moderate2tel_point-like_knn05_MinMaxScaler")

    # Extract the runlist subfolder name from the runlist filename
    folder_match = re.search(r"runlist_releaseTestingV6_(.*)", Path(runlist_name).stem)
    if folder_match:
        subfolder = folder_match.group(1)
    else:
        subfolder = Path(runlist_name).stem  # Use full name if pattern doesn't match

    # Read the run numbers from a file
    with open(runlist_path, "r") as f:
        selected_runs = {
            int(line.strip()) for line in f if line.strip().isdigit()
        }  # Convert to a set of integers
    # Find all FITS files and filter by run number
    paths = [
        p
        for p in path.rglob("*.fits.gz")
        if any(f"{run}." in p.name for run in selected_runs)  # Match run number in filename
    ]

    if not paths:
        raise ValueError(f"No matching FITS files found for {runlist_name}")

    data_store = DataStore.from_events_files(paths)

    # Create output directory
    output_dir = Path(f"./FITS/knn05_MinMaxScaler/{subfolder}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write the index files
    data_store.hdu_table.write(output_dir / "hdu-index.fits.gz", overwrite=True)
    data_store.obs_table.write(output_dir / "obs-index.fits.gz", overwrite=True)

    return output_dir


# Function to read all run IDs from a runlist file
def read_runs_from_file(file_path):
    with open(file_path) as f:
        return [int(line.strip()) for line in f if line.strip()]


def process_runlist(download_dir, runlist):
    try:
        local_path = download_dir / runlist
        logger.info(f"Starting to process {runlist}")

        # Check if combined plot already exists
        runlist_name = Path(runlist).stem
        combined_plot_path = Path(
            f"./validation_plots/combined/combined_relative_diff_{runlist_name}.png"
        )

        if combined_plot_path.exists():
            logger.info(f"Combined plot already exists for {runlist}, skipping processing")
            return True

        # Generate index files first if they don't exist
        logger.info(f"Generating index files for {runlist} if needed...")
        output_dir = generate_index_files(local_path, runlist)
        datastore_path = output_dir / "hdu-index.fits.gz"

        logger.info(f"Creating plots for {runlist}")
        crab_lightcurve_validation.main(
            ["--runlist", str(local_path), "--datastore", str(datastore_path), "--no-relative"]
        )
        crab_lightcurve_validation.plot_combined_relative_differences(str(local_path))

        logger.info(f"Successfully completed processing {runlist}")
        return True
    except Exception as e:
        logger.error(f"Error processing {runlist}: {e}")
        return False


if __name__ == "__main__":
    # Directory containing runlists
    download_dir = Path(DATA_DIR + "EventDisplay_Release_v491/Crab/runlists")
    all_files = os.listdir(download_dir)
    runlist_files = [f for f in all_files if re.match(r"runlist_releaseTestingV6_..*\.dat", f)]

    print(f"Found {len(runlist_files)} runlist files")

    # Number of parallel processes to use
    num_processes = max(1, mp.cpu_count() - 1)
    logger.info(f"Using {num_processes} parallel processes")

    # Create a partial function with the download_dir argument fixed
    process_func = partial(process_runlist, download_dir)

    # Process runlists in parallel
    with mp.Pool(processes=num_processes) as pool:
        results = pool.map(process_func, runlist_files)

    # Summary of results
    successful = sum(results)
    logger.info(f"Processing complete: {successful} successful.")
    gc.collect()
