"""
This script performs light curve estimation for Crab data using Gammapy v1.3.

Functions:
- read_obs_ids(runlist_path): Reads obs IDs from a runlist file.
- make_exclusion_mask(): Creates an exclusion mask for regions to be excluded from analysis.
- make_datasets(data_store, obs_ids, exclusion_mask): Generates datasets for the
  analysis.
- main(args=None): Main function to parse arguments and run the workflow.
    gc.collect()
    parser = argparse.ArgumentParser()
    parser.add_argument("--runlist", required=True, help="Path to runlist file")
    parser.add_argument(
        "--datastore",
        def        stats_text.append(
            f"{knn_val}:\n"
            f"  Mean: {stats['mean']:.2f}%, Med: {stats['median']:.2f}%, \sigma: {stats['std']:.2f}%"
        )="./hdu-index.fits.gz",
        help="Path to the datastore index file",
    )
    parser.add_argument(
        "--only-relative",
        action="store_true",
        help="Only create relative difference plot",
    )
    parser.add_argument(
        "--no-relative",
        action="store_true",
        help="Skip creating relative difference plot",
    )

    # Parse either command line arguments or the passed arguments
    if args is None:
        parsed_args = parser.parse_args()
    else:
        parsed_args = parser.parse_args(args)

    obs_ids = read_obs_ids(parsed_args.runlist)
    data_store = DataStore.from_file(filename=parsed_args.datastore)

    exclusion_mask = make_exclusion_mask()
    datasets = make_datasets(data_store, obs_ids, exclusion_mask)
    lightcurve = estimate_lightcurve(datasets)
    plot_lightcurve(parsed_args, lightcurve)

    # Generate relative difference plot unless explicitly disabled
    if not hasattr(parsed_args, "no_relative") or not parsed_args.no_relative:
        plot_relative_difference(parsed_args, lightcurve)

    gc.collect() and exclusion mask.
- estimate_lightcurve(datasets): Estimates the light curve for the given datasets
                                 using a predefined spectral model.
- plot_lightcurve(lightcurve): Plots the estimated light curve.
- plot_relative_difference(args, lightcurve): Plots the relative difference between
                                              Gammapy and Anasum values.
- main(): Main function to parse arguments, process data, and generate the light curve.

Usage:
Run the script with the `--runlist` argument pointing to a file containing observation IDs.
"""

import argparse
import datetime
import gc
import logging
import re
import traceback
from pathlib import Path
from gammapy.estimators import FluxPointsEstimator, FluxPoints
import astropy.units as u
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy.time import Time
from gammapy.data import DataStore
from gammapy.datasets import Datasets, SpectrumDataset, FluxPointsDataset
from gammapy.estimators import LightCurveEstimator
from gammapy.makers import (
    ReflectedRegionsBackgroundMaker,
    SafeMaskMaker,
    SpectrumDatasetMaker,
)
from gammapy.maps import MapAxis, RegionGeom, WcsGeom
from gammapy.modeling.models import Models, PowerLawSpectralModel, SkyModel
from regions import CircleSkyRegion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DATA_DIR = "/home/eshita/Documents/VERITAS/"


def read_obs_ids(runlist_path):
    with open(runlist_path) as f:
        obs_ids = [int(line.strip()) for line in f if line.strip()]
    return obs_ids


def make_exclusion_mask():
    axis = MapAxis.from_edges(np.logspace(-1.0, 1.0, 10), unit="TeV", name="energy", interp="log")
    geom = WcsGeom.create(
        skydir=(83.6333, 22.0145), width=(4, 4), binsz=0.01, frame="icrs", axes=[axis]
    )

    target_position = SkyCoord(ra=83.6333, dec=22.0145, unit="deg", frame="icrs")
    on_region_radius = 0.4 * u.deg
    on_region = CircleSkyRegion(center=target_position, radius=on_region_radius)

    exclusions = [
        CircleSkyRegion(SkyCoord(ra, dec, unit="deg", frame="icrs"), radius=radius * u.deg)
        for ra, dec, radius in [
            (81.9087, 21.937, 0.3),
            (82.6806, 22.4623, 0.3),
            (83.4118, 20.4742, 0.3),
            (84.4112, 21.1425, 0.3),
            (84.8629, 21.7629, 0.3),
            (85.4782, 23.3262, 0.3),
        ]
    ]

    regions = [on_region] + exclusions
    exclusion_mask = ~geom.to_image().region_mask(regions)

    fig = plt.figure()
    exclusion_mask.plot()
    plt.savefig("/home/eshita/Documents/VERITAS/EventDisplay_ReleaseTests_code/release_tests/validation_plots/exclusion_mask.png")
    plt.close(fig)
    plt.cla()
    plt.clf()
    gc.collect()
    return exclusion_mask


def make_datasets(data_store, obs_ids, exclusion_mask):
    observations = data_store.get_observations(obs_ids, required_irf="point-like")

    energy_axis = MapAxis.from_energy_bounds("0.5 TeV", "50 TeV", nbin=25)
    energy_axis_true = MapAxis.from_energy_bounds("0.3 TeV", "70 TeV", nbin=50, name="energy_true")

    geom = RegionGeom.create(region="icrs;circle(83.63,22.01,0.08944272)", axes=[energy_axis])
    dataset_empty = SpectrumDataset.create(
        geom=geom, energy_axis_true=energy_axis_true, name="crab"
    )

    maker = SpectrumDatasetMaker(
        containment_correction=False, selection=["counts", "exposure", "edisp"]
    )
    safe_mask_maker = SafeMaskMaker(methods=["aeff-max"], aeff_percent=10)
    bkg_maker = ReflectedRegionsBackgroundMaker(exclusion_mask=exclusion_mask)

    datasets = Datasets()
    for obs in observations:
        dataset = maker.run(dataset_empty.copy(name=f"{obs.obs_id}"), obs)
        dataset_on_off = bkg_maker.run(dataset, obs)
        dataset_on_off = safe_mask_maker.run(dataset, obs)
        datasets.append(dataset_on_off)

    return datasets


def estimate_lightcurve(datasets):
    spectral_model = PowerLawSpectralModel(
        index=2.5,
        amplitude=3.5e-11 * u.Unit("1 / (cm2 s TeV)"),
        reference=1 * u.TeV,
    )
    sky_model = SkyModel(spectral_model=spectral_model, name="crab")
    datasets.models = Models([sky_model])

    lc_maker = LightCurveEstimator(energy_edges=[0.5, 50] * u.TeV, reoptimize=False)
    lightcurve = lc_maker.run(datasets)

    return lightcurve


def plot_lightcurve(args, lightcurve):
    # Create output path
    runlist_name = Path(args.runlist).stem
    output_dir = Path("./validation_plots/knn05_MinMaxScaler")
    output_dir.mkdir(exist_ok=True, parents=True)
    output_path = output_dir / f"lightcurve_plot_{runlist_name}.png"

    # Check if the plot already exists
    if output_path.exists():
        logging.info(f"Lightcurve plot already exists at {output_path}, skipping generation")
        return

    plt.figure(figsize=(10, 6))

    fig, ax = plt.subplots(
        figsize=(8, 6),
        gridspec_kw={"left": 0.16, "bottom": 0.2, "top": 0.98, "right": 0.98},
    )
    ax.set_ylim(1e-11, 0.5e-9)
    lightcurve.plot(ax=ax, sed_type="flux", marker="o", label="Gammapy")
    
    # Calculate statistics for Gammapy data
    flux_table = lightcurve.to_table(format="lightcurve", sed_type="flux")
    gammapy_flux = flux_table['flux'].quantity.value
    
    gammapy_mean = np.nanmean(gammapy_flux)
    gammapy_median = np.nanmedian(gammapy_flux)
    gammapy_std = np.nanstd(gammapy_flux)

    # Format for scientific notation
    gammapy_stats_text = (
        f"Gammapy Stats:\n"
        f"Mean: {gammapy_mean:.2e} cm$^{{-2}}$ s$^{{-1}}$\n"
        f"Median: {gammapy_median:.2e} cm$^{{-2}}$ s$^{{-1}}$\n"
        f"$\sigma$: {gammapy_std:.2e} cm$^{{-2}}$ s$^{{-1}}$"
    )

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()

    runlist_name = Path(args.runlist).stem
    folder_match = re.search(r"runlist_releaseTestingV6(.*)", runlist_name)

    if True: #folder_match:
        folder_name = folder_match.group(1)
        # Try to find and load the reference CSV file
        #base_path = f"{DATA_DIR}/EventDisplay_Release_v491/Crab/V6_moderate2tel"
        csv_path = Path('/home/eshita/Documents/VERITAS/EventDisplay_Release_v491/Crab/V6_moderate2tel/V6/LightCurve.csv') #Path(f"{base_path}/V6_{folder_name}/LightCurve.csv")

        if csv_path.exists():
            print()
            print(f"Loading reference data from {csv_path}")
            print()
            try:
                ref_data = pd.read_csv(csv_path)

                if "MJD" in ref_data.columns and "Flux" in ref_data.columns:
                    times = Time(ref_data["MJD"], format="mjd")
                    plot_times = [t.plot_date for t in times]

                    yerr = None
                    if "FluxError" in ref_data.columns:
                        yerr = ref_data["FluxError"]

                    ax.errorbar(
                        plot_times,
                        ref_data["Flux"],
                        yerr=yerr,
                        fmt="s",
                        color="red",
                        label="Anasum",
                    )

                    # Calculate statistics for Anasum data
                    anasum_flux = ref_data["Flux"].values
                    anasum_mean = np.mean(anasum_flux)
                    anasum_median = np.median(anasum_flux)
                    anasum_std = np.std(anasum_flux)

                    # Add Anasum stats to the text
                    anasum_stats_text = (
                        f"Anasum Stats:\n"
                        f"Mean: {anasum_mean:.2e} cm$^{{-2}}$ s$^{{-1}}$\n"
                        f"Median: {anasum_median:.2e} cm$^{{-2}}$ s$^{{-1}}$\n"
                        f"$\sigma$: {anasum_std:.2e} cm$^{{-2}}$ s$^{{-1}}$"
                    )
                    
                    # Combined stats text
                    stats_text = f"{gammapy_stats_text}\n\n{anasum_stats_text}"
                    
                    if "MJD_width" in ref_data.columns:
                        for i, (mjd, flux, width) in enumerate(
                            zip(ref_data["MJD"], ref_data["Flux"], ref_data["MJD_width"])
                        ):
                            left = Time(mjd - width / 2, format="mjd").plot_date
                            right = Time(mjd + width / 2, format="mjd").plot_date
                            ax.hlines(flux, left, right, colors="red", lw=1.5)

                    logging.info(f"Added reference data from {csv_path}")
                else:
                    logging.warning("CSV file missing required columns (MJD, Flux)")
                    stats_text = gammapy_stats_text
            except Exception as e:
                logging.warning(f"Failed to load or plot reference data: {e}")
                stats_text = gammapy_stats_text
        else:
            stats_text = gammapy_stats_text
        
    # Add stats text box
    ax.text(
        0.05,
        0.05,
        stats_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="bottom",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    plt.legend(loc='upper left')

    output_dir = Path("./validation_plots/knn05_MinMaxScaler")
    output_dir.mkdir(exist_ok=True, parents=True)

    output_path = output_dir / f"lightcurve_plot_{runlist_name}.png"
    fig.savefig(output_path)
    logging.info(f"Lightcurve plot saved to {output_path}")
    plt.close()
    plt.clf()
    plt.cla()
    gc.collect()


def get_anasum_runs_with_zenith(log_path):
    """
    Parse the anasum log file and return a set of run numbers with specified zenith
    """
    runs = set()
    pattern = re.compile(r"RUN\s+(\d+).*?at\s+(\d+),")
    with open(log_path) as f:
        for line in f:
            match = pattern.search(line)
            if match:
                run = int(match.group(1))
                elevation = float(match.group(2))
                zenith = 90 - elevation
                if zenith < 55:
                    runs.add(run)
    return runs


def plot_relative_difference(args, lightcurve):
    """Create a plot showing the relative difference between Gammapy and Anasum values."""
    runlist_name = Path(args.runlist).stem
    output_dir = Path("./validation_plots/knn05_MinMaxScaler")
    output_dir.mkdir(exist_ok=True, parents=True)
    output_path = output_dir / f"relative_diff_{runlist_name}.png"

    # Check if the plot already exists
    if output_path.exists():
        logger.info(
            f"Relative difference plot already exists at {output_path}, skipping generation"
        )
        return

    log_path = "/home/eshita/Documents/VERITAS/EventDisplay_Release_v491/Crab/V6_moderate2tel/V6/anasum_releaseTestingV6.combined.log"
    zenith_runs = get_anasum_runs_with_zenith(log_path)

    # Read runs from runlist
    with open(args.runlist) as f:
        all_run_ids = [int(line.strip()) for line in f if line.strip()]
    # Filter to only those with zenith < 55
    filtered_run_ids = [run for run in all_run_ids if run in zenith_runs]

    # Get Gammapy data
    flux_table = lightcurve.to_table(format="lightcurve", sed_type="flux")
    gammapy_flux = flux_table['flux'].quantity.value
    gammapy_flux_err = flux_table['flux_err'].quantity.value

    # Filter Gammapy data by run id
    gammapy_run_ids = all_run_ids[:len(gammapy_flux)] if len(gammapy_flux) < len(all_run_ids) else all_run_ids
    gammapy_flux_by_run = dict(zip(gammapy_run_ids, gammapy_flux))
    gammapy_flux_err_by_run = dict(zip(gammapy_run_ids, gammapy_flux_err))

    # Get Anasum data
    csv_path = Path('/home/eshita/Documents/VERITAS/EventDisplay_Release_v491/Crab/V6_moderate2tel/V6/LightCurve.csv')
    ref_data = pd.read_csv(csv_path)
    anasum_flux = ref_data["Flux"].values
    anasum_flux_err = ref_data.get("FluxError", np.zeros_like(anasum_flux))
    for col in ref_data.columns:
        if col.lower() in ["run", "runid", "obs_id", "obsid"]:
            anasum_run_col = col
            break
    if anasum_run_col is not None:
        print('anasum run col not none')
        anasum_run_ids = ref_data[anasum_run_col].astype(int).values
        anasum_flux_by_run = dict(zip(anasum_run_ids, anasum_flux))
        anasum_flux_err_by_run = dict(zip(anasum_run_ids, anasum_flux_err))
    else:
        logger.error("No run number column found in Anasum CSV")
        return

    # Now match only filtered runs
    matched_gammapy_flux = []
    matched_gammapy_flux_err = []
    matched_anasum_flux = []
    matched_anasum_flux_err = []
    valid_run_ids = []
    for run_id in filtered_run_ids:
        if run_id in gammapy_flux_by_run and run_id in anasum_flux_by_run:
            matched_gammapy_flux.append(gammapy_flux_by_run[run_id])
            matched_gammapy_flux_err.append(gammapy_flux_err_by_run[run_id])
            matched_anasum_flux.append(anasum_flux_by_run[run_id])
            matched_anasum_flux_err.append(anasum_flux_err_by_run[run_id])
            valid_run_ids.append(run_id)
    if len(matched_gammapy_flux) == 0:
        logger.error("No matching runs found between Gammapy and Anasum")
        return
    logger.info(f"Comparing {len(matched_gammapy_flux)} runs between Gammapy and Anasum")
    gc.collect()
    # Calculate relative differences
    rel_diffs = []
    rel_diff_errors = []
    for g_flux, g_err, a_flux, a_err in zip(matched_gammapy_flux, matched_gammapy_flux_err, matched_anasum_flux, matched_anasum_flux_err):
        if not np.isfinite(g_flux) or not np.isfinite(a_flux):
            continue
        rel_diff = (g_flux - a_flux) / a_flux * 100
        if a_err > 0:
            rel_diff_err = np.sqrt((g_err / a_flux) ** 2 + (a_err * g_flux / (a_flux ** 2)) ** 2) * 100
        else:
            rel_diff_err = g_err / a_flux * 100
        if np.isfinite(rel_diff) and np.isfinite(rel_diff_err):
            rel_diffs.append(rel_diff)
            rel_diff_errors.append(rel_diff_err)
    if not rel_diffs:
        logger.warning("No valid matching points found for relative difference plot")
        return
    fig, ax = plt.subplots(
        figsize=(8, 6),
        gridspec_kw={"left": 0.16, "bottom": 0.2, "top": 0.98, "right": 0.98},
    )
    rel_diffs = np.array(rel_diffs).flatten()
    rel_diff_errors = np.array(rel_diff_errors).flatten()
    ax.errorbar(
        np.arange(len(rel_diffs)),
        rel_diffs,
        yerr=rel_diff_errors,
        fmt="o",
        color="purple",
        label="Relative Difference",
    )
    ax.axhline(y=0, color="k", linestyle="-", alpha=0.3)
    ax.set_ylabel(
        r"$\frac{\mathrm{Gammapy} - \mathrm{Anasum}}{\mathrm{Anasum}} \times 100\,(\%)$"
    )
    ax.set_title(f"Relative Flux Difference\n{runlist_name}")
    ax.set_xlabel("Index")
    fig.autofmt_xdate()
    rel_diffs_array = np.array(rel_diffs)
    mean_diff = np.mean(rel_diffs_array)
    median_diff = np.median(rel_diffs_array)
    std_diff = np.std(rel_diffs_array)
    stats_text = (
        f"Mean: {mean_diff:.2f}%\n" f"Median: {median_diff:.2f}%\n" f"Std Dev: {std_diff:.2f}%"
    )
    ax.text(
        0.05,
        0.95,
        stats_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    plt.clf()
    gc.collect()
    logger.info(f"Relative difference plot saved to {output_path}")
    



def plot_combined_relative_differences(runlist_path):
    """Create a combined plot showing relative differences compared to Anasum."""

    # Get runlist name and subfolder
    runlist_name = Path(runlist_path).stem
    folder_match = re.search(r"runlist_releaseTestingV6(.*)", runlist_name)

    if not folder_match:
        logger.warning(f"Could not extract folder name from {runlist_name}, skipping combined plot")
        return

    folder_name = folder_match.group(1)
    base_path = f"{DATA_DIR}EventDisplay_Release_v491/Crab/V6_moderate2tel"
    anasum_csv_path = Path('/home/eshita/Documents/VERITAS/EventDisplay_Release_v491/Crab/V6_moderate2tel/V6/LightCurve.csv') #Path(f"{base_path}/V6_{folder_name}/LightCurve.csv")

    if not anasum_csv_path.exists():
        logger.warning(f"No reference CSV found at {anasum_csv_path}, skipping combined plot")
        return

    # Load Anasum reference data
    try:
        ref_data = pd.read_csv(anasum_csv_path)
        anasum_times = Time(ref_data["MJD"], format="mjd")
        anasum_flux = ref_data["Flux"]
    except Exception as e:
        logger.warning(f"Failed to load Anasum data: {e}")
        return

    fig, ax = plt.subplots(
        figsize=(10, 6),
        gridspec_kw={"left": 0.14, "bottom": 0.14, "top": 0.92, "right": 0.92},
    )

    # List of kNN values to process
    knn_values = ["knn05_sec", "knn05", "knn05_MinMaxScaler"]
    markers = ["o", "s", "^"]
    colors = ["purple", "green", "orange"]

    all_stats = {}

    for idx, knn_val in enumerate(knn_values):
        try:
            datastore_path = Path('/home/eshita/Documents/VERITAS/EventDisplay_ReleaseTests_code/FITS/knn05_MinMaxScaler/V6/') #Path(f"./FITS/{knn_val}/{folder_name}/hdu-index.fits.gz")
            if not datastore_path.exists():
                logger.warning(f"No datastore found at {datastore_path}, skipping {knn_val}")
                continue

            obs_ids = read_obs_ids(runlist_path)
            data_store = DataStore.from_dir(filename=str(datastore_path))
            exclusion_mask = make_exclusion_mask()
            datasets = make_datasets(data_store, obs_ids, exclusion_mask)
            lightcurve = estimate_lightcurve(datasets)

            flux_points_table = lightcurve.to_table(format="lightcurve", sed_type="flux")
            if (
                "flux" not in flux_points_table.colnames
                or "flux_err" not in flux_points_table.colnames
            ):
                logger.error(f"Missing flux or flux_err columns in lightcurve data for {knn_val}")
                continue

            gammapy_flux = flux_points_table["flux"].quantity.value
            gammapy_flux_err = flux_points_table["flux_err"].quantity.value

            time_col = flux_points_table["time_min"]
            if hasattr(time_col, "mjd"):
                # Already a Time object or Quantity with .mjd
                gammapy_times = time_col.mjd
            elif isinstance(time_col[0], (float, np.floating, int)):
                # Already MJD floats
                gammapy_times = time_col
            else:
                # Try to convert to Time, then get mjd
                gammapy_times = Time(time_col).mjd

            logger.info(
                f"Retrieved {len(gammapy_flux)} flux points with proper errors for {knn_val}"
            )

            if len(gammapy_times) == 0:
                logger.warning(f"No valid time points found for {knn_val}, skipping")
                continue

            rel_diffs = []
            rel_diff_errors = []
            matched_times = []

            total_gammapy_points = len(gammapy_times)
            logger.info(f"Total Gammapy points for {knn_val}: {total_gammapy_points}")

            for g_time, g_flux, g_err in zip(gammapy_times, gammapy_flux, gammapy_flux_err):
                g_time_value = g_time.value if hasattr(g_time, "value") else g_time
                time_diffs = np.abs(anasum_times.mjd - g_time_value)
                closest_idx = np.argmin(time_diffs)

                if float(time_diffs[closest_idx]) <= 0.001:
                    a_flux = anasum_flux.iloc[closest_idx]

                    # Skip points with very low flux
                    if hasattr(g_flux, "to_value"):
                        g_flux_val = g_flux.to_value(u.Unit("1 / (cm2 s)"))
                    else:
                        g_flux_val = float(g_flux)
                    if g_flux_val < 1e-15 or float(a_flux) < 1e-15:
                        continue


                    try:
                        g_flux_val = float(g_flux)
                        a_flux_val = float(a_flux)

                        rel_diff = (g_flux_val - a_flux_val) / a_flux_val * 100

                        if not np.isfinite(rel_diff):
                            continue

                        g_rel_err = float(g_err) / a_flux_val * 100

                        if np.isfinite(rel_diff) and np.isfinite(g_rel_err):
                            rel_diffs.append(rel_diff)
                            rel_diff_errors.append(g_rel_err)
                            matched_times.append(g_time)

                    except (ValueError, ZeroDivisionError):
                        continue

            if not rel_diffs:
                logger.warning(f"No valid matching time points found for {knn_val}, skipping")
                continue

            # Plot this kNN's relative difference
            matched_times = Time(matched_times, format="mjd")
            ax.errorbar(
                matched_times.plot_date,
                rel_diffs,
                yerr=rel_diff_errors,
                fmt=markers[idx],
                color=colors[idx],
                label=f"{knn_val}",
                alpha=0.7,
            )

            # Calculate statistics for this kNN value
            rel_diffs_array = np.array(rel_diffs)
            all_stats[knn_val] = {
                "mean": np.mean(rel_diffs_array),
                "median": np.median(rel_diffs_array),
                "std": np.std(rel_diffs_array),
            }

        except Exception:
            logger.error(f"Error processing {knn_val}")
            continue

    # If we didn't plot anything, return
    if not all_stats:
        logger.warning("No data to plot for any kNN value, skipping combined plot")
        plt.close(fig)
        return

    ax.axhline(y=0, color="k", linestyle="-", alpha=0.3)

    ax.set_ylabel(r"$\frac{\mathrm{Gammapy} - \mathrm{Anasum}}{\mathrm{Anasum}} \times 100\,(\%)$")

    ax.set_title(f"Relative Flux Difference\n{runlist_name}")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()
    handles, labels = ax.get_legend_handles_labels()

    stats_text = []
    for knn_val in all_stats:
        stats = all_stats[knn_val]
        stats_text.append(
            f"{knn_val}:\n"
            f"  Mean: {stats['mean']:.2f}%, Med: {stats['median']:.2f}%, $\sigma$: {stats['std']:.2f}%"
        )

    ax.legend(handles, labels)

    stat_box = "\n".join(stats_text)
    ax.text(
        0.02,
        0.02,
        stat_box,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="bottom",
        horizontalalignment="left",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    # Save the combined plot
    output_dir = Path("./validation_plots/combined")
    output_dir.mkdir(exist_ok=True, parents=True)
    output_path = output_dir / f"combined_relative_diff_{runlist_name}.png"
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)

    logger.info(f"Combined relative difference plot saved to {output_path}")


def main(args=None):
    gc.collect()
    parser = argparse.ArgumentParser()
    parser.add_argument("--runlist", required=True, help="Path to runlist file")
    parser.add_argument(
        "--datastore",
        default="./hdu-index.fits.gz",
        help="Path to the datastore index file",
    )
    parser.add_argument(
        "--only-relative",
        action="store_true",
        help="Only create relative difference plot",
    )
    parser.add_argument(
        "--no-relative",
        action="store_true",
        help="Skip creating relative difference plot",
    )

    if args is None:
        parsed_args = parser.parse_args()
    else:
        parsed_args = parser.parse_args(args)

    obs_ids = read_obs_ids(parsed_args.runlist)
    data_store = DataStore.from_dir(parsed_args.datastore)


    exclusion_mask = make_exclusion_mask()
    datasets = make_datasets(data_store, obs_ids, exclusion_mask)
    lightcurve = estimate_lightcurve(datasets)
    
    # Use the correct, index-based function
    identify_and_plot_high_diff_runs(parsed_args, lightcurve, threshold=50)

    # Only create the plots specified by the arguments
    if not hasattr(parsed_args, "only_relative") or not parsed_args.only_relative:
        plot_lightcurve(parsed_args, lightcurve)

    if (not hasattr(parsed_args, "no_relative") or not parsed_args.no_relative) and (
        not hasattr(parsed_args, "only_relative") or parsed_args.only_relative
    ):
        plot_relative_difference(parsed_args, lightcurve)

    #plot_energy_spectra(parsed_args, lightcurve)

    gc.collect()


if __name__ == "__main__":
    main()

def identify_and_plot_high_diff_runs(args, lightcurve, threshold=50):
    """
    Identifies indices with relative flux difference > threshold percent (or < -threshold percent)
    and creates a plot showing just these indices for both Gammapy and Anasum.
    Applies zenith cuts using the anasum log file.
    """
    runlist_name = Path(args.runlist).stem
    csv_path = Path('/home/eshita/Documents/VERITAS/EventDisplay_Release_v491/Crab/V6_moderate2tel/V6/LightCurve.csv')
    log_path = "/home/eshita/Documents/VERITAS/EventDisplay_Release_v491/Crab/V6_moderate2tel/V6/anasum_releaseTestingV6.combined.log"
    if not csv_path.exists():
        logger.warning(f"No reference CSV found at {csv_path}, skipping high diff analysis")
        return
    try:
        zenith_runs = get_anasum_runs_with_zenith(log_path)

        # Read runs from runlist and filter by zenith cut
        with open(args.runlist) as f:
            all_run_ids = [int(line.strip()) for line in f if line.strip()]
        filtered_run_ids = [run for run in all_run_ids if run in zenith_runs]

        # Get Gammapy data
        flux_table = lightcurve.to_table(format="lightcurve", sed_type="flux")
        gammapy_flux = flux_table['flux'].quantity.value
        gammapy_flux_err = flux_table['flux_err'].quantity.value

        # Filter Gammapy data by run id
        gammapy_run_ids = all_run_ids[:len(gammapy_flux)] if len(gammapy_flux) < len(all_run_ids) else all_run_ids
        gammapy_flux_by_run = dict(zip(gammapy_run_ids, gammapy_flux))
        gammapy_flux_err_by_run = dict(zip(gammapy_run_ids, gammapy_flux_err))

        # Get Anasum data
        anasum_data = pd.read_csv(csv_path)
        anasum_flux = anasum_data["Flux"].values
        anasum_flux_err = anasum_data.get("FluxError", np.zeros_like(anasum_flux))
        anasum_run_col = None
        for col in anasum_data.columns:
            if col.lower() in ["run", "runid", "obs_id", "obsid"]:
                anasum_run_col = col
                break
        if anasum_run_col is not None:
            anasum_run_ids = anasum_data[anasum_run_col].astype(int).values
            anasum_flux_by_run = dict(zip(anasum_run_ids, anasum_flux))
            anasum_flux_err_by_run = dict(zip(anasum_run_ids, anasum_flux_err))
        else:
            logger.error("No run number column found in Anasum CSV")
            return

        # Now match only filtered runs (zenith < 55 deg)
        matched_gammapy_flux = []
        matched_gammapy_flux_err = []
        matched_anasum_flux = []
        matched_anasum_flux_err = []
        valid_run_ids = []
        for run_id in filtered_run_ids:
            if run_id in gammapy_flux_by_run and run_id in anasum_flux_by_run:
                matched_gammapy_flux.append(gammapy_flux_by_run[run_id])
                matched_gammapy_flux_err.append(gammapy_flux_err_by_run[run_id])
                matched_anasum_flux.append(anasum_flux_by_run[run_id])
                matched_anasum_flux_err.append(anasum_flux_err_by_run[run_id])
                valid_run_ids.append(run_id)
        if len(matched_gammapy_flux) == 0:
            logger.error("No matching runs with zenith < 55found between Gammapy and Anasum")
            return
        logger.info(f"Comparing {len(matched_gammapy_flux)} runs with zenith < 55 between Gammapy and Anasum")

        # Calculate relative differences
        rel_diffs = np.array([((g - a) / a) * 100 for g, a in zip(matched_gammapy_flux, matched_anasum_flux)])
        high_diff_indices = np.where((rel_diffs > threshold) | (rel_diffs < -threshold))[0]
        if len(high_diff_indices) == 0:
            logger.info(f"No indices found with >{threshold}% absolute difference")
            return
        # Save high difference runs to file
        output_dir = Path("./validation_plots/high_diff_runs")
        output_dir.mkdir(exist_ok=True, parents=True)
        high_diff_runlist = output_dir / f"high_diff_runs_{runlist_name}.dat"
        with open(high_diff_runlist, 'w') as f:
            for idx in high_diff_indices:
                f.write(f"{valid_run_ids[idx]}\n")
        high_diff_details = output_dir / f"high_diff_details_{runlist_name}.csv"
        with open(high_diff_details, 'w') as f:
            f.write("Run,RelativeDifferencePercent\n")
            for idx in high_diff_indices:
                f.write(f"{valid_run_ids[idx]},{float(rel_diffs[idx]):.2f}\n")
        logger.info(f"Found {len(high_diff_indices)} indices with >{threshold}% absolute difference")
        logger.info(f"High difference runs saved to {high_diff_runlist}")
        logger.info(f"Detailed information saved to {high_diff_details}")
        # Extract data just for these indices
        high_diff_gammapy_flux = [float(matched_gammapy_flux[i]) for i in high_diff_indices]
        high_diff_anasum_flux = [float(matched_anasum_flux[i]) for i in high_diff_indices]
        high_diff_times = [anasum_data["MJD"].values[anasum_data[anasum_run_col] == valid_run_ids[i]][0] if "MJD" in anasum_data.columns else i for i in high_diff_indices]
        # Create the plot for high difference indices
        output_path = output_dir / f"high_diff_{threshold}pct_{runlist_name}.png"
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_yscale('log')
        plot_times = Time(high_diff_times, format="mjd").plot_date if "MJD" in anasum_data.columns else high_diff_times
        ax.errorbar(
            plot_times,
            high_diff_gammapy_flux,
            fmt='o',
            label="Gammapy",
            color='blue'
        )
        ax.errorbar(
            plot_times,
            high_diff_anasum_flux,
            fmt='s',
            label="Anasum",
            color='red'
        )
        for i, (x, y, run_id, rel_diff) in enumerate(zip(
            plot_times, high_diff_gammapy_flux, [valid_run_ids[i] for i in range(len(high_diff_indices))],
            [rel_diffs[idx] for idx in high_diff_indices]
        )):
            ax.annotate(
                f"Run {run_id}\n({float(rel_diff):.1f}%)",
                (x, y),
                xytext=(0, 10),
                textcoords='offset points',
                ha='center',
                fontsize=8
            )
        ax.set_title(f"Indices with >{threshold}% for zenith < 55deg, Flux Difference \n{runlist_name}")
        ax.set_xlabel("Date" if "MJD" in anasum_data.columns else "Index")
        ax.set_ylabel("Flux (cm$^{-2}$ s$^{-1}$)")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate()
        plt.legend()
        plt.tight_layout()
        fig.savefig(output_path)
        plt.close(fig)
        logger.info(f"High difference plot saved to {output_path}")
        return [valid_run_ids[i] for i in range(len(high_diff_indices))]
    except Exception as e:
        logger.error(f"Error identifying high difference indices: {e}", exc_info=True)
        logger.error(traceback.format_exc())
        return []