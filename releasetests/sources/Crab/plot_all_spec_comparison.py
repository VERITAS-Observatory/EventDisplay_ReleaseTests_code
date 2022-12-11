import numpy as np
from gammapy.estimators import FluxPoints
import sys
import matplotlib.pyplot as plt
import astropy.units as u
from gammapy.modeling.models import PowerLawSpectralModel
from astropy.io import ascii
import yaml
from yaml.loader import SafeLoader

import compare_spectra


def read_eventdisplay_spectral_results(eventdisplay_file):
    """
    Read eventdisplay spectral results from file.

    """
    print("Reading eventdisplay spectral results from", eventdisplay_file)
    data = ascii.read(eventdisplay_file)
    ED_ul = np.isnan(data["dnde"])
    dnde = [
        xv if not c else yv for c, xv, yv in zip(ED_ul, data["dnde"], data["dnde_ul"])
    ]
    dnde_err = (data["dnde_errp"] + data["dnde_errn"]) / 2.0
    for iu in range(np.size(ED_ul)):
        if ED_ul[iu] == 1:
            dnde_err[iu] = 0.1 * data["dnde_ul"][iu]

    print("\t found {} eventdisplay spectral points".format(np.size(ED_ul)))
    return data["e_ref"], dnde, 0.5 * (data["e_max"] - data["e_min"]), dnde_err, ED_ul, data["n_on"], data["signi"]


def plot_eventdisplay_spectral_points(ax, eventdisplay_file, eventdisplay_version, para):
    """
    Plot eventdisplay spectral points.

    """
    ED_x, ED_y, ED_xerr, ED_yerr, ED_ul, ED_on, ED_signi = read_eventdisplay_spectral_results(
        eventdisplay_file
    )

    ax.plot(
        ED_x,
        ED_y * ED_x**2 * 1.6,
        "bo",
        label="Eventdisplay-{}".format(eventdisplay_version),
        alpha=0.5,
        ls="none",
    )
    ax.errorbar(
        ED_x,
        ED_y * ED_x**2 * 1.6,
        xerr=ED_xerr,
        yerr=ED_yerr * ED_x**2 * 1.6,
        uplims=ED_ul,
        marker="o",
        color="blue",
        ls="none",
        mfc="none",
        alpha=0.5,
    )
    ax.set_ylim(para['plotting']['ymin'], para['plotting']['ymax'])
    return ED_x, ED_y, ED_xerr, ED_yerr, ED_ul, ED_on, ED_signi


def plot_gammapy_spectral_points(ax, gammapy_file):
    """
    Read and plot gammapy spectral points

    """
    print("Reading gammapy spectral results from", gammapy_file)
    flux_gp = FluxPoints.read(gammapy_file)
    flux_gp.plot(
        ax=ax, sed_type="e2dnde", label="gammapy", color="r", marker="o", mfc="none"
    )
    flux_points_table = flux_gp.to_table(sed_type="dnde", formatted=True)
    return flux_points_table


def plot_spectral_fit(ax, spectral_fit_file, e_min, e_max, e_ref, label, para):
    """
    Read and plot spectral fit.

    """
    print(
        "Reading spectral fit results for {} from {}".format(label, spectral_fit_file)
    )
    SpecPara = np.genfromtxt(spectral_fit_file)
    index = SpecPara[0]
    index_error = SpecPara[1]
    amplitude = SpecPara[2]
    amplitude_error = SpecPara[3]
    if label == "gammapy":
        color = "r"
        txt_y = para['plotting']['ymin'] + 1.0 * para['plotting']['ymin']
    else:
        color = "b"
        txt_y = para['plotting']['ymin'] + 2.0 * para['plotting']['ymin']

    print(
        "\t {:.3}+-{:.3}; {:.3}+-{:.3}".format(
            index, index_error, amplitude, amplitude_error
        )
    )
    pwl = PowerLawSpectralModel(
        index=index,
        amplitude=amplitude * u.Unit("1 / (cm2 s TeV)"),
        reference=e_ref * u.TeV,
    )
    pwl.plot(
        ax=ax,
        sed_type="e2dnde",
        energy_bounds=[e_min, e_max] * u.TeV,
        label=label + " model fit",
        color=color,
        ls="-",
        alpha=0.5,
    )
    pwl.index.error = index_error
    pwl.amplitude.error = amplitude_error
    pwl.plot_error(ax=ax, sed_type="e2dnde", energy_bounds=[e_min, e_max] * u.TeV, color='b', alpha=0.2)
    plt.text(
        0.15,
        txt_y,
        "{}: {:.3}±{:.3}, {:.3}±{:.3}".format(
            label, amplitude, amplitude_error, index, index_error
        ),
        size=10,
        color=color,
    )


def plot_ratio(ax2, x, gammapy_flux_table_column, ED_y, ED_ul, e_min, e_max, label):
    """ 
    Plot ratio between gammapy and Eventdisplay results (for Flux point, ON counts)

    """
    y_ratio = np.divide(gammapy_flux_table_column, ED_y, where=np.logical_not(ED_ul))

    ax2.plot(x, y_ratio, "bo")
    ax2.set_ylim(0.9, 1.1)
    ax2.set_ylabel(label)
    ax2.set_xscale('log')
    ax2.hlines(xmin=e_min, xmax=e_max, y=1)
    ax2.hlines(xmin=e_min, xmax=e_max, y=0.9)
    ax2.hlines(xmin=e_min, xmax=e_max, y=1.1)
    ax2.hlines(xmin=e_min, xmax=e_max, y=0.975, color="red", ls="--")
    ax2.hlines(xmin=e_min, xmax=e_max, y=1.025, color="red", ls="--")
    ax2.set_xlabel("Energy [TeV]")

    return y_ratio


def plot_sig(ax, x, xerr, sqrt_ts, signi, e_min, e_max):
    """
    Plot the difference of sqrt_ts (from gammapy) and significance (from Eventdisplay)
    """

    y_diff = sqrt_ts - signi
    ax.plot(x, y_diff, 'bo', label='sqrt_ts - significance')
    ax.set_xscale('log')
    ax.set_ylim(-4, 4)
    ax.hlines(xmin=e_min, xmax=e_max, y=-1, color="red", ls="--")
    ax.hlines(xmin=e_min, xmax=e_max, y=1, color="red", ls="--")
    ax.set_xlabel("Energy [TeV]")
    ax.set_ylabel("sqrt_ts - significance")
    plt.legend(loc='upper left')

    ax2 = ax.twinx()
    ax2.bar(x, sqrt_ts,width=xerr, color='r', label='sqrt_ts', alpha=0.2)
    ax2.bar(x, signi,width=xerr, color='b', label='significance', alpha=0.2)
    ax2.set_ylabel('sqrt_ts or significnace')
    plt.legend(loc='upper right')

    return y_diff

def main():

    eventdisplay_file = sys.argv[1]
    gammapy_file = sys.argv[2]

    epoch = sys.argv[3]
    odir = sys.argv[4]
    parameter_file = sys.argv[5]
    zenith_range = sys.argv[6]
    cut = sys.argv[7]
    eventdisplay_version = sys.argv[8]

    e_min, e_max, e_ref = compare_spectra.get_spectral_fit_range(parameter_file, None, zenith_range, cut)
    print(
        "\t fit range: min: {} TeV, max: {} TeV, ref: {} TeV ".format(
            e_min, e_max, e_ref
        )
    )

    fig_spec = plt.figure(figsize=(8, 6))
    gs = fig_spec.add_gridspec(
        2,
        2,
        width_ratios=(6, 3),
        height_ratios=(6, 3),
        left=0.1,
        right=0.9,
        bottom=0.1,
        top=0.9,
        wspace=0.03,
        hspace=0.03,
    )

    para = compare_spectra.read_gammapy_analysis_file(parameter_file)

    ## SED plotting
    ax = fig_spec.add_subplot(gs[0, 0])
    ED_x, ED_y, ED_xerr, ED_yerr, ED_ul, ED_on, ED_signi = plot_eventdisplay_spectral_points(
        ax, eventdisplay_file + "_SpecPoints.csv", eventdisplay_version, para,
    )
    plot_spectral_fit(
        ax, eventdisplay_file + "_SpecFit.txt", e_min, e_max, e_ref, "Eventdisplay", para
    )

    gammapy_flux_table = plot_gammapy_spectral_points(ax, gammapy_file+"_SpecPoints.fits")
    plot_spectral_fit(ax, gammapy_file+"_SpecFit.txt", e_min, e_max, e_ref, "gammapy", para)

    ax.set_xlim(para['plotting']['xmin'], para['plotting']['xmax'])
    plt.legend(title="{} (RE)".format(epoch), loc="upper right", prop={"size": 6})

    ## SED ratio plotting
    ax2 = fig_spec.add_subplot(gs[1, 0], sharex=ax)
    y_ratio = plot_ratio(ax2, gammapy_flux_table["e_ref"],  gammapy_flux_table["dnde"], ED_y, ED_ul, e_min, e_max, "F_gp/F_ed")

    ## SED ratio histogram
    ax2_histy = fig_spec.add_subplot(gs[1, 1], sharey=ax2)
    ax2_histy.tick_params(axis="y", labelleft=False)
    bins = np.linspace(0.5, 1.5, 101)
    ax2_histy.hist(
        y_ratio,
        bins=bins,
        orientation="horizontal",
        alpha=0.7,
        histtype="step",
        color="blue",
    )

    print("Saving results to {}/{}_Spectra_Comparision.png".format(odir, epoch))
    fig_spec.savefig("{}/{}_Spectra_Comparision.png".format(odir, epoch))

    fig_cs = plt.figure(figsize=(8, 6))
    gs = fig_cs.add_gridspec(
        2,  
        1,  
        height_ratios=(5, 5), 
        left=0.1,
        right=0.9,
        bottom=0.1,
        top=0.9,
        wspace=0.03,
        hspace=0.03,
    )
    
    ## ON events ratio plotting
    ax = fig_cs.add_subplot(gs[0])    
    y_ratio_c = plot_ratio(ax, gammapy_flux_table["e_ref"],  gammapy_flux_table["counts"][:,0], ED_on, ED_ul, e_min, e_max, "Counts/Non")
    ax.set_xlim(para['plotting']['xmin'], para['plotting']['xmax'])

    ax2 = fig_cs.add_subplot(gs[1], sharex=ax)
    y_diff = plot_sig(ax2, ED_x, ED_xerr, gammapy_flux_table["sqrt_ts"], ED_signi, e_min, e_max)    

    print("Saving results to {}/{}_Non_Comparision.png".format(odir, epoch))
    fig_cs.savefig("{}/{}_Non_Comparision.png".format(odir, epoch))


if __name__ == "__main__":
    main()
