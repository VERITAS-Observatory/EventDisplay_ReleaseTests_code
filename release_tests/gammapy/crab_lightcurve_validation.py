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
            f"  Mean: {stats['mean']:.2f}%, Med: {stats['median']:.2f}%, σ: {stats['std']:.2f}%"
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

import astropy.units as u
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy.time import Time
from gammapy.data import DataStore
from gammapy.datasets import Datasets, SpectrumDataset
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
    on_region_radius = 0.3 * u.deg
    on_region = CircleSkyRegion(center=target_position, radius=on_region_radius)

    exclusions = [
        CircleSkyRegion(SkyCoord(ra, dec, unit="deg", frame="icrs"), radius=0.3 * u.deg)
        for ra, dec in [
            (81.9087, 21.937),
            (82.6806, 22.4623),
            (83.4118, 20.4742),
            (84.1099, 21.9931),
            (84.4112, 21.1425),
            (84.8629, 21.7629),
            (85.4782, 23.3262),
            (85.5166, 22.6603),
        ]
    ]

    regions = [on_region] + exclusions
    exclusion_mask = ~geom.to_image().region_mask(regions)

    fig = plt.figure()
    exclusion_mask.plot()
    plt.close(fig)
    return exclusion_mask


def make_datasets(data_store, obs_ids, exclusion_mask):
    observations = data_store.get_observations(obs_ids, required_irf="point-like")

    energy_axis = MapAxis.from_energy_bounds("0.5 TeV", "50 TeV", nbin=25)
    energy_axis_true = MapAxis.from_energy_bounds("0.3 TeV", "70 TeV", nbin=50, name="energy_true")

    geom = RegionGeom.create(region="icrs;circle(83.63,22.01,0.08944272)", axes=[energy_axis])
    dataset_empty = SpectrumDataset.create(
        geom=geom, energy_axis_true=energy_axis_true, name="crab"
    )

    wcsgeom = WcsGeom.create(skydir=geom.center_skydir, width=5, binsz=0.02)
    exclusion_mask = wcsgeom.region_mask(geom.region, inside=False)

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
    ax.set_ylim(1e-12, 1e-9)
    lightcurve.plot(ax=ax, sed_type="flux", marker="o", label="Gammapy")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()

    runlist_name = Path(args.runlist).stem
    folder_match = re.search(r"runlist_releaseTestingV6_(.*)", runlist_name)

    if folder_match:
        folder_name = folder_match.group(1)
        # Try to find and load the reference CSV file
        base_path = f"{DATA_DIR}/EventDisplay_Release_v491/Crab/V6_moderate2tel"
        csv_path = Path(f"{base_path}/V6_{folder_name}/LightCurve.csv")

        if csv_path.exists():
            try:
                ref_data = pd.read_csv(csv_path)

                if "MDJ" in ref_data.columns and "Flux" in ref_data.columns:
                    times = Time(ref_data["MDJ"], format="mjd")
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

                    if "MJD_width" in ref_data.columns:
                        for i, (mjd, flux, width) in enumerate(
                            zip(ref_data["MDJ"], ref_data["Flux"], ref_data["MJD_width"])
                        ):
                            left = Time(mjd - width / 2, format="mjd").plot_date
                            right = Time(mjd + width / 2, format="mjd").plot_date
                            ax.hlines(flux, left, right, colors="red", lw=1.5)

                    logging.info(f"Added reference data from {csv_path}")
                else:
                    logging.warning("CSV file missing required columns (MDJ, Flux)")
            except Exception as e:
                logging.warning(f"Failed to load or plot reference data: {e}")

    plt.legend()

    output_dir = Path("./validation_plots/knn05_MinMaxScaler")
    output_dir.mkdir(exist_ok=True, parents=True)

    output_path = output_dir / f"lightcurve_plot_{runlist_name}.png"
    fig.savefig(output_path)
    logging.info(f"Lightcurve plot saved to {output_path}")
    plt.close()
    plt.clf()
    gc.collect()


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

    # Continue with existing code...
    folder_match = re.search(r"runlist_releaseTestingV6_(.*)", runlist_name)

    if not folder_match:
        logger.warning(f"Could not extract folder name from {runlist_name}, skipping relative plot")
        return

    folder_name = folder_match.group(1)
    csv_path = Path(
        f"{DATA_DIR}/EventDisplay_Release_v491/Crab/V6_moderate2tel/V6_{folder_name}/LightCurve.csv"
    )

    if not csv_path.exists():
        logger.warning(f"No reference CSV found at {csv_path}, skipping relative plot")
        return

    try:
        try:
            ref_data = pd.read_csv(csv_path)
            if len(ref_data) == 0:
                logger.warning("Anasum CSV file is empty, skipping relative plot")
                return
        except Exception as e:
            logger.warning(f"Failed to load Anasum data: {e}")
            return

        temp_fig, temp_ax = plt.subplots()
        lightcurve.plot(ax=temp_ax, sed_type="flux")
        lines = [child for child in temp_ax.get_children() if isinstance(child, plt.Line2D)]
        if not lines or len(lines[0].get_xdata()) == 0:
            logger.warning("No Gammapy flux data found, skipping relative plot")
            plt.close(temp_fig)
            return

        gammapy_times_plot = lines[0].get_xdata()
        gammapy_flux = lines[0].get_ydata()

        if len(gammapy_times_plot) == 0:
            logger.warning("No Gammapy time points found, skipping relative plot")
            plt.close(temp_fig)
            return

        gammapy_flux_err = lightcurve.to_table(format="lightcurve", sed_type="flux")[
            "flux_err"
        ].quantity.value

        # Convert plot x-values (dates) to MJD format for comparison
        if isinstance(gammapy_times_plot[0], float):
            gammapy_times = np.array([mdates.num2date(t).timestamp() for t in gammapy_times_plot])
            gammapy_times = Time(gammapy_times, format="unix").mjd
        elif isinstance(gammapy_times_plot[0], (np.datetime64, datetime.datetime)):
            gammapy_times = Time(
                [t.isoformat() if hasattr(t, "isoformat") else t for t in gammapy_times_plot]
            ).mjd
        plt.close(temp_fig)

        ref_data = pd.read_csv(csv_path)

        anasum_times = Time(ref_data["MDJ"], format="mjd")
        anasum_flux = ref_data["Flux"]
        anasum_flux_err = ref_data.get("FluxError", np.zeros_like(anasum_flux))

        rel_diffs = []
        rel_diff_errors = []
        matched_times = []

        total_gammapy_points = len(gammapy_times)
        logger.info(f"Total Gammapy points: {total_gammapy_points}")

        for g_time, g_flux, g_err in zip(gammapy_times, gammapy_flux, gammapy_flux_err):
            # Find closest Anasum time point within tolerance
            g_time_value = g_time.value if hasattr(g_time, "value") else g_time
            time_diffs = np.abs(anasum_times.mjd - g_time_value)
            closest_idx = np.argmin(time_diffs)

            if float(time_diffs[closest_idx]) < (30 / 1440):  # 30 minutes in days
                a_flux = anasum_flux.iloc[closest_idx]

                # Skip extreme outliers where flux is too low
                if hasattr(g_flux, "to_value"):
                    g_flux_val = g_flux.to_value(u.Unit("1 / (cm2 s)"))
                else:
                    g_flux_val = float(g_flux)
                if g_flux_val < 1e-15 or float(a_flux) < 1e-15:
                    continue

                a_flux_val = float(a_flux)
                rel_diff = (g_flux_val - a_flux_val) / a_flux_val * 100

                if hasattr(g_err, "to_value"):
                    g_rel_err = g_err.to_value("") / a_flux_val * 100
                else:
                    g_rel_err = float(g_err) / a_flux_val * 100

                # Calculate error on relative difference
                g_rel_err = float(g_err) / a_flux_val * 100
                a_rel_err = 0
                if anasum_flux_err is not None and not pd.isna(anasum_flux_err.iloc[closest_idx]):
                    a_err = float(anasum_flux_err.iloc[closest_idx])
                    a_rel_err = a_err / a_flux_val * 100

                # Combine errors in quadrature
                rel_diff_err = np.sqrt(g_rel_err**2 + a_rel_err**2)

                # Only append if finite
                if np.isfinite(rel_diff) and np.isfinite(rel_diff_err):
                    rel_diffs.append(rel_diff)
                    rel_diff_errors.append(rel_diff_err)
                    matched_times.append(g_time)

        if not rel_diffs:
            logger.warning("No valid matching time points found for relative difference plot")
            return

        fig, ax = plt.subplots(
            figsize=(8, 6),
            gridspec_kw={"left": 0.16, "bottom": 0.2, "top": 0.98, "right": 0.98},
        )

        matched_times = Time(matched_times, format="mjd")

        ax.errorbar(
            matched_times.plot_date,
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

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
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

        output_dir = Path("./validation_plots/knn05_MinMaxScaler")
        output_dir.mkdir(exist_ok=True, parents=True)

        output_path = output_dir / f"relative_diff_{runlist_name}.png"
        fig.savefig(output_path, bbox_inches="tight")
        plt.close(fig)
        plt.clf()
        gc.collect()
        logger.info(f"Relative difference plot saved to {output_path}")

    except Exception as e:
        logger.error(f"Error creating relative difference plot: {e}", exc_info=True)

        logger.error(traceback.format_exc())


def plot_combined_relative_differences(runlist_path):
    """Create a combined plot showing relative differences compared to Anasum."""

    # Get runlist name and subfolder
    runlist_name = Path(runlist_path).stem
    folder_match = re.search(r"runlist_releaseTestingV6_(.*)", runlist_name)

    if not folder_match:
        logger.warning(f"Could not extract folder name from {runlist_name}, skipping combined plot")
        return

    folder_name = folder_match.group(1)
    base_path = f"{DATA_DIR}EventDisplay_Release_v491/Crab/V6_moderate2tel"
    anasum_csv_path = Path(f"{base_path}/V6_{folder_name}/LightCurve.csv")

    if not anasum_csv_path.exists():
        logger.warning(f"No reference CSV found at {anasum_csv_path}, skipping combined plot")
        return

    # Load Anasum reference data
    try:
        ref_data = pd.read_csv(anasum_csv_path)
        anasum_times = Time(ref_data["MDJ"], format="mjd")
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
            datastore_path = Path(f"./FITS/{knn_val}/{folder_name}/hdu-index.fits.gz")
            if not datastore_path.exists():
                logger.warning(f"No datastore found at {datastore_path}, skipping {knn_val}")
                continue

            obs_ids = read_obs_ids(runlist_path)
            data_store = DataStore.from_file(filename=str(datastore_path))
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

                if float(time_diffs[closest_idx]) < (30 / 1440):  # 30 minutes in days
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
            f"  Mean: {stats['mean']:.2f}%, Med: {stats['median']:.2f}%, c3: {stats['std']:.2f}%"
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
    data_store = DataStore.from_file(filename=parsed_args.datastore)

    exclusion_mask = make_exclusion_mask()
    datasets = make_datasets(data_store, obs_ids, exclusion_mask)
    lightcurve = estimate_lightcurve(datasets)

    # Only create the plots specified by the arguments
    if not hasattr(parsed_args, "only_relative") or not parsed_args.only_relative:
        plot_lightcurve(parsed_args, lightcurve)

    if (not hasattr(parsed_args, "no_relative") or not parsed_args.no_relative) and (
        not hasattr(parsed_args, "only_relative") or parsed_args.only_relative
    ):
        plot_relative_difference(parsed_args, lightcurve)

    gc.collect()


if __name__ == "__main__":
    main()
