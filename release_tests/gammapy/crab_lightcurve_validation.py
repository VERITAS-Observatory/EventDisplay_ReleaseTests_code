
"""
This script performs light curve estimation for Crab data using Gammapy v1.3.

Functions:
- read_obs_ids(runlist_path): Reads obs IDs from a runlist file.
- make_exclusion_mask(): Creates an exclusion mask for regions to be excluded from analysis.
- make_datasets(data_store, obs_ids, exclusion_mask): Generates datasets for the given observations and exclusion mask.
- estimate_lightcurve(datasets): Estimates the light curve for the given datasets using a predefined spectral model.
- plot_lightcurve(lightcurve): Plots the estimated light curve.
- main(): Main function to parse arguments, process data, and generate the light curve.

Usage:
Run the script with the `--runlist` argument pointing to a file containing observation IDs.
"""
import argparse
import logging
from pathlib import Path

import astropy.units as u
import matplotlib.pyplot as plt
import numpy as np
from astropy.coordinates import SkyCoord
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


def read_obs_ids(runlist_path):
    with open(runlist_path) as f:
        obs_ids = [int(line.strip()) for line in f if line.strip()]
    return obs_ids

def make_exclusion_mask():
    axis = MapAxis.from_edges(
        np.logspace(-1.0, 1.0, 10), unit="TeV", name="energy", interp="log"
    )
    geom = WcsGeom.create(
        skydir=(83.6333, 22.0145), width=(4, 4), binsz=0.01, frame="icrs", axes=[axis]
    )

    target_position = SkyCoord(ra=83.6333, dec=22.0145, unit="deg", frame="icrs")
    on_region_radius = 0.3 * u.deg
    on_region = CircleSkyRegion(center=target_position, radius=on_region_radius)

    exclusions = [
        CircleSkyRegion(SkyCoord(ra, dec, unit="deg", frame="icrs"), radius=0.3 * u.deg)
        for ra, dec in [
            (81.9087, 21.937), (82.6806, 22.4623), (83.4118, 20.4742),
            (84.1099, 21.9931), (84.4112, 21.1425), (84.8629, 21.7629),
            (85.4782, 23.3262), (85.5166, 22.6603)
        ]
    ]

    regions = [on_region] + exclusions
    exclusion_mask = ~geom.to_image().region_mask(regions)

    plt.figure()
    exclusion_mask.plot()
    return exclusion_mask

def make_datasets(data_store, obs_ids, exclusion_mask):
    observations = data_store.get_observations(obs_ids, required_irf="point-like")

    energy_axis = MapAxis.from_energy_bounds("0.5 TeV", "10 TeV", nbin=15)
    energy_axis_true = MapAxis.from_energy_bounds("0.3 TeV", "20 TeV", nbin=40, name="energy_true")

    geom = RegionGeom.create(region="icrs;circle(83.63,22.01,0.08944272)", axes=[energy_axis])
    dataset_empty = SpectrumDataset.create(geom=geom, energy_axis_true=energy_axis_true, name="crab")

    wcsgeom = WcsGeom.create(skydir=geom.center_skydir, width=5, binsz=0.02)
    exclusion_mask = wcsgeom.region_mask(geom.region, inside=False)

    maker = SpectrumDatasetMaker(
    containment_correction=False, selection=["counts", "exposure", "edisp"]
    )
    safe_mask_maker = SafeMaskMaker(methods=["aeff-max"], aeff_percent=10)
    bkg_maker = ReflectedRegionsBackgroundMaker(exclusion_mask=exclusion_mask)

    datasets = Datasets()
    for obs in observations:
        dataset = maker.run(dataset_empty.copy(name=f'{obs.obs_id}'), obs)
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

    lc_maker = LightCurveEstimator(energy_edges=[1, 10] * u.TeV, reoptimize=False)
    return lc_maker.run(datasets)

def plot_lightcurve(args, lightcurve):
    fig, ax = plt.subplots(
        figsize=(8, 6),
        gridspec_kw={"left": 0.16, "bottom": 0.2, "top": 0.98, "right": 0.98},
    )
    lightcurve.plot(ax=ax, marker="o", label="1D")
    plt.legend()
    runlist_name = Path(args.runlist).stem
    output_path = Path(f"./validation_plots/lightcurve_plot_{runlist_name}.png")
    fig.savefig(output_path)
    logging.info(f"Lightcurve plot saved to {output_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runlist", required=True, help="Path to runlist file")
    args = parser.parse_args()

    obs_ids = read_obs_ids(args.runlist)
    data_store = DataStore.from_file(filename="./FITS/hdu-index.fits.gz")

    exclusion_mask = make_exclusion_mask()
    datasets = make_datasets(data_store, obs_ids, exclusion_mask)
    lightcurve = estimate_lightcurve(datasets)
    plot_lightcurve(args, lightcurve)

if __name__ == "__main__":
    main()

