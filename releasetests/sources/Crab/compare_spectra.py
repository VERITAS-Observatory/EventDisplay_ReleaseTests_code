import argparse

import astropy.units as u
from astropy.io import ascii
import matplotlib.pyplot as plt
import numpy as np
import yaml

from astropy.coordinates import SkyCoord, Angle
from regions import CircleSkyRegion
from gammapy.maps import MapAxis, WcsGeom, RegionGeom
from gammapy.modeling import Fit
from gammapy.data import DataStore
from gammapy.datasets import (
    Datasets,
    SpectrumDataset,
)
from gammapy.modeling.models import (
    PowerLawSpectralModel,
    SkyModel,
)
from gammapy.makers import (
    SafeMaskMaker,
    SpectrumDatasetMaker,
    ReflectedRegionsBackgroundMaker,
)
from gammapy.estimators import FluxPointsEstimator
from gammapy.visualization import plot_spectrum_datasets_off_regions


def get_crab_fit_para(par, zenith_range, cut):
    """
    Return fit range for Crab.

    """

    try:
        ze_key = zenith_range.lower() + "_fit_para"
        return (
            par[ze_key][cut]["emin"],
            par[ze_key][cut]["emax"],
            par[ze_key][cut]["eref"],
        )
    except KeyError:
        print(
            "type of cut or zenith range not known! Available cuts: moderate2tel, soft2tel, hard2tel, hard3tel"
        )
        return None, None, None


def get_spectral_fit_range(parameter_file, gp_ana_par, zenith_range, cut):
    """
    Get fit ranges. Depend on zenith range and cuts applied.

    """
    if parameter_file is not None:
        gp_ana_par = read_gammapy_analysis_file(parameter_file)

    print("Reading gammapy analysis parameter for source:", gp_ana_par["source"])
    if gp_ana_par["source"].lower() == "crab":
        if (zenith_range is None) or (cut is None):
            raise KeyError(
                "zenith_range and cut arguments are required for Crab release test analysis!"
            )
        return get_crab_fit_para(gp_ana_par, zenith_range, cut)
    try:
        return (
            gp_ana_par["source_fit_para"]["emin"],
            gp_ana_par["source_fit_para"]["emax"],
            gp_ana_par["source_fit_para"]["eref"],
        )
    except KeyError:
        print("Error reading fit range")
        raise


def read_gammapy_analysis_file(parameter_file):
    """
    Read gammapy analysis parameters from file

    """
    print("Reading gammapy analysis parameter from", parameter_file)
    with open(parameter_file) as par_file:
        par = yaml.load(par_file, Loader=yaml.loader.SafeLoader)
    return par


def get_energy_edges(reference_file):
    """ "
    reference_file: sed flux points file (ecsv) from Eventdisplay

    returns: bin edges in Energy for spectral flux point calculation

    """

    data = ascii.read(reference_file)
    e_ref = data["e_ref"]
    e_min = data["e_min"]
    e_max = data["e_max"]
    energy_edges = e_min[0]
    for ie in range(np.size(e_ref)):
        energy_edges = np.append(energy_edges, e_max[ie])

    return energy_edges * u.TeV


def find_exclusion_regions(cat_data, point_ra, point_dec, search_roi):

    cat_ra = []
    cat_dec = []
    pointing_position = SkyCoord(ra=point_ra, dec=point_dec, unit="deg", frame="icrs")

    nn = np.shape(cat_data)[0]
    for i in range(nn):

        star_coord = SkyCoord(cat_data[i][0], cat_data[i][1], unit="deg", frame="icrs")
        sep = pointing_position.separation(star_coord).degree

        # Finding the stars within 3 deg of pointing direction
        if sep <= search_roi:
            cat_ra.append(cat_data[i][0])
            cat_dec.append(cat_data[i][1])

    return cat_ra, cat_dec


def get_max_wobble(datastore):

    obs_table = datastore.obs_table
    obs_ids = obs_table["OBS_ID"]
    NFiles = np.size(obs_ids)
    woff = np.array([])

    for i in range(NFiles):
        ra_obj = obs_table["RA_OBJ"][obs_table["OBS_ID"] == obs_ids[i]]
        dec_obj = obs_table["DEC_OBJ"][obs_table["OBS_ID"] == obs_ids[i]]
        ra_pnt = obs_table["RA_PNT"][obs_table["OBS_ID"] == obs_ids[i]]
        dec_pnt = obs_table["DEC_PNT"][obs_table["OBS_ID"] == obs_ids[i]]
        obj = SkyCoord(ra_obj, dec_obj, unit="deg", frame="icrs")
        pnt = SkyCoord(ra_pnt, dec_pnt, unit="deg", frame="icrs")
        woff = np.append(woff, pnt.separation(obj).degree)

    return np.max(woff)


def make_exclusion_masks(catalog, datastore, vmag):

    print("Make exclusion mask from {} for magnitude {}".format(catalog, vmag))
    cat_data = []
    try:
        with open(catalog) as f:
            lines = (line for line in f if not line.startswith("#"))
            for line in lines:
                p = line.split()
                if np.size(p) == 5 and float(p[3]) <= vmag:
                    cat_data.append([float(p[0]), float(p[1])])
    except FileNotFoundError as e:
        print("{}".format(e))
    print("Done reading star list ({} stars)".format(len(cat_data)))

    obs_table = datastore.obs_table
    obs_ids = obs_table["OBS_ID"]

    cat_ra, cat_dec = find_exclusion_regions(
        cat_data,
        point_ra=obs_table["RA_PNT"][obs_table["OBS_ID"] == obs_ids[0]][0],
        point_dec=obs_table["DEC_PNT"][obs_table["OBS_ID"] == obs_ids[0]][0],
        search_roi=get_max_wobble(datastore) + 3.5
    )

    _, ind = np.unique(cat_ra, return_index=True)
    ra = np.array(cat_ra)[ind]
    dec = np.array(cat_dec)[ind]

    exclusion_mask = []

    reg_pos = SkyCoord(ra, dec, unit="deg", frame="icrs")
    reg = [CircleSkyRegion(reg_pos[i], radius=0.3 * u.deg) for i in range(np.size(ra))]
    print("Exclusion region found:", reg)

    target_position = SkyCoord(
        ra=obs_table["RA_OBJ"][0], dec=obs_table["DEC_OBJ"][0], unit="deg", frame="icrs"
    )
    skydir = target_position.galactic
    geom = WcsGeom.create(
        npix=(1000, 1000), binsz=0.005, skydir=skydir, proj="TAN", frame="icrs"
    )

    exclusion_mask = ~geom.region_mask(reg)

    return exclusion_mask


def write_fit_parameters(parameter_file, Fit_para):
    """
    Write fit parameter to file

    """
    para_file = open(parameter_file, "w")
    para_file.write(
        "{}\t {}\t {}\t {}\t {}\n".format(
            Fit_para[0][2],
            Fit_para[0][4],
            Fit_para[1][2],
            Fit_para[1][4],
            Fit_para[2][2],
        )
    )

    return Fit_para[0][2], Fit_para[1][2]


def plot_off_regions(datasets, on_region, exclusion_mask, off_region_file):
    """
    Plot off and exclusion regions

    """
    fig = plt.figure(figsize=(8, 8))
    ax = exclusion_mask.plot()
    on_region.to_pixel(ax.wcs).plot(ax=ax, edgecolor="k")
# TODO: this does not work with gammapy 0.20.1
    # plot_spectrum_datasets_off_regions(ax=ax, datasets=datasets)
    print("Writing off region plot to ", off_region_file)
    fig.savefig(off_region_file)


def stack_dataset(energy_axis, on_region, obs_ids, observations, exclusion_mask):
    """
    Stack the dataset for the given observations

    """
    energy_axis_true = MapAxis.from_energy_bounds(
        0.05, 100, nbin=200, unit="TeV", name="energy_true"
    )

    geom = RegionGeom.create(region=on_region, axes=[energy_axis])
    dataset_empty = SpectrumDataset.create(geom=geom, energy_axis_true=energy_axis_true)

    dataset_maker = SpectrumDatasetMaker(
        containment_correction=False, selection=["counts", "exposure", "edisp"]
    )
    bkg_maker = ReflectedRegionsBackgroundMaker(
        exclusion_mask=exclusion_mask, max_region_number=6
    )
    safe_mask_masker = SafeMaskMaker(methods=["aeff-max"], aeff_percent=10)

    datasets = Datasets()
    for obs_id, observation in zip(obs_ids, observations):
        dataset = dataset_maker.run(dataset_empty.copy(name=str(obs_id)), observation)
        dataset_on_off = bkg_maker.run(dataset, observation)
        dataset_on_off = safe_mask_masker.run(dataset_on_off, observation)
        datasets.append(dataset_on_off)

    dataset_stacked = Datasets(datasets).stack_reduce(name="stacked")
    return dataset_stacked, datasets


def get_on_region(obs_table, object_name, on_region_radius):
    """
    Return on region

    """

    on_region_radius = Angle("{} deg".format(on_region_radius))

    target_position = SkyCoord(
        ra=obs_table["RA_OBJ"][obs_table["OBJECT"] == object_name][0],
        dec=obs_table["DEC_OBJ"][obs_table["OBJECT"] == object_name][0],
        unit="deg",
        frame="icrs",
    )
    print("\nTarget position of {}".format(object_name))
    print(target_position)

    print("\nOnregion radius: {}".format(on_region_radius))
    return CircleSkyRegion(center=target_position, radius=on_region_radius)


def parse():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-d", "--datastore", help="path of IACT datastore", required=True
    )
    parser.add_argument(
        "-t",
        "--figure_tag",
        help="string added in the beginning for all output file name",
        required=True,
    )
    parser.add_argument(
        "-r",
        "--reference_file",
        help="ecsv file with Eventdisplay spectral flux points",
        required=True,
    )
    parser.add_argument("-o", "--outdir", help="path for output files", required=True)
    parser.add_argument(
        "-c", "--catalog", help="Bright star catalog file", required=True
    )
    parser.add_argument(
        "-p",
        "--parameter_file",
        help="yaml file containing gammapy analysis parameters",
        required=True,
    )
    parser.add_argument("-z", "--zenith_range", help="Zenith angle range for Crab")
    parser.add_argument("-s", "--cut", help="Type of cut for Crab")

    return parser.parse_args()


def main():

    args = parse()

    par = read_gammapy_analysis_file(args.parameter_file)
    emin, emax, _ = get_spectral_fit_range(None, par, args.zenith_range, args.cut)
    print("\t fit range: min: {} TeV, max: {} TeV".format(emin, emax))

    datastore = DataStore.from_dir(args.datastore)
    datastore.info()

    obs_table = datastore.obs_table
    datastore_sources = np.unique(obs_table["OBJECT"])

    print("No. of sources in datastore:", np.size(datastore_sources))
    print("", datastore_sources)
    object_name = datastore_sources[0]

    spec_type = "pl"
    print("Reference spectral type:", spec_type)

    # Get the spectrum of the first source
    print("\nDoing 1D spectral analysis of", object_name)
    obs_ids = obs_table["OBS_ID"][obs_table["OBJECT"] == object_name]

    print(
        "\nNo. of DL3 files avaliable in datastore for {}: {}".format(
            object_name, np.size(obs_ids)
        )
    )
    print("\nObservation IDs of {}: \n{}".format(object_name, obs_ids))

    available_irf = ["aeff", "edisp"]
    observations = datastore.get_observations(obs_ids, required_irf=available_irf)

    on_region = get_on_region(obs_table, object_name, np.sqrt(float(par["theta2_cut"])))
    exclusion_mask = make_exclusion_masks(
        args.catalog, datastore, float(par["min_magnitude"])
    )

    energy_axis = MapAxis.from_energy_bounds(
        emin, emax, nbin=100, unit="TeV", name="energy"
    )
    dataset_stacked, datasets = stack_dataset(
        energy_axis, on_region, obs_ids, observations, exclusion_mask
    )

    plot_off_regions(
        datasets,
        on_region,
        exclusion_mask,
        "{}/{}_Off_region.png".format(args.outdir, args.figure_tag),
    )

    if spec_type == "pl":
        spectral_model = PowerLawSpectralModel(
            index=2, amplitude=2e-11 * u.Unit("cm-2 s-1 TeV-1"), reference=1.0 * u.TeV
        )
        spectral_model.index.min = 0.5
        spectral_model.index.max = 5.0
    dataset_stacked.models = [SkyModel(spectral_model=spectral_model, name="crab")]
    fit = Fit()
    fit.run([dataset_stacked])
    s_index, s_amplitude = write_fit_parameters(
        args.outdir + "/{}_SpecFit.txt".format(args.figure_tag),
        dataset_stacked.models[0].parameters.to_table(),
    )

    ## Edges from Eventdisplay
    energy_edges = get_energy_edges(args.reference_file)
    print("Eventdisplay energy bins #", np.size(energy_edges) - 1)
    print(energy_edges)

    ##Do the data reduction step again over broad energy range
    energy_axis = MapAxis(
        energy_edges, interp="lin", name="energy", unit="", node_type="edges"
    )
    dataset_stacked, _ = stack_dataset(
        energy_axis, on_region, obs_ids, observations, exclusion_mask
    )

    # Model with parameter obtained from fitting
    spectral_model = PowerLawSpectralModel(
        index=s_index,
        amplitude=s_amplitude * u.Unit("cm-2 s-1 TeV-1"),
        reference=1.0 * u.TeV,
    )
    dataset_stacked.models = [
        SkyModel(spectral_model=spectral_model, name="{}".format(object_name))
    ]

    # compute flux points
    fpe = FluxPointsEstimator(
        energy_edges=energy_edges,
        source="{}".format(object_name),
        n_sigma_ul=3,
        selection_optional="all",
    )
    flux_points = fpe.run(datasets=[dataset_stacked])
    print(
        "Writing flux points to {}/{}_SpecPoints.fits".format(
            args.outdir, args.figure_tag
        )
    )
    flux_points.write(
        "{}/{}_SpecPoints.fits".format(args.outdir, args.figure_tag),
        sed_type="dnde",
        format="gadf-sed",
        overwrite=True,
    )


if __name__ == "__main__":
    main()
