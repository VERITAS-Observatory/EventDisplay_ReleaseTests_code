import numpy as np
from gammapy.estimators import FluxPoints
import sys
import matplotlib.pyplot as plt
from matplotlib import gridspec
from astropy.io import fits
import astropy.units as u
from gammapy.modeling.models import (
    PowerLawSpectralModel,
)
from astropy.io import ascii


file_ed = sys.argv[1]
file_gp = sys.argv[2]
#ind = int(sys.argv[3])

epoch = sys.argv[3]

spec_ed = sys.argv[4]
spec_gp = sys.argv[5]

odir = sys.argv[6]

e_thresh = float(sys.argv[7])

fig_spec = plt.figure(figsize=(8, 6))
gs = fig_spec.add_gridspec(2, 2,  width_ratios=(6, 3), height_ratios=(6, 3),
                      left=0.1, right=0.9, bottom=0.1, top=0.9,
                      wspace=0.03, hspace=0.03)

ax = fig_spec.add_subplot(gs[0, 0])


#ED-487
data = ascii.read(file_ed)
e_ref = data['e_ref']
e_min = data['e_min']
e_max = data['e_max']
dnde = data['dnde']
dnde_errn = data['dnde_errn']
dnde_errp = data['dnde_errp']
dnde_err = (dnde_errp + dnde_errn) / 2.0    #its not uppler and lower bound in ED ecsv file
dnde_ul = data['dnde_ul']
ED_ul = np.zeros(e_ref.size)
for ie in range(np.size(e_ref)):

    if (np.isnan(dnde[ie])): 
       dnde[ie] =  dnde_ul[ie]
       dnde_err[ie] = 0.1 * dnde_ul[ie] 
       ED_ul[ie] = 1

#dp=np.size(e_ref)   #np.size(energy_edges) - 1
print('ed #:', np.size(e_ref))
print(e_ref)
#print(dnde_errn, dnde_errp, dnde_err)

ED_x = e_ref    #data_pt[0:dp, 0]
ED_x_l = e_min  #data_pt[0:dp, 1]
ED_x_u = e_max  #data_pt[0:dp, 2]
ED_xerr = (ED_x_u - ED_x_l) / 2.0
ED_y = dnde    #data_pt[0:dp, 3]
ED_yerr = dnde_err  #data_pt[0:dp, 4]
ED_yul= dnde_ul   #data_pt[0:dp,6]
ED_ul = ED_ul   #np.zeros(ED_x.size)
#print(ED_y, ED_yerr)

ax.plot(ED_x, ED_y*ED_x**2*1.6, 'bo', label='Eventdisplay-v487e', alpha=0.5, ls='none')
ax.errorbar(ED_x, ED_y*ED_x**2*1.6, xerr=ED_xerr, yerr=ED_yerr*ED_x**2*1.6, uplims=ED_ul, marker='o', color='blue', ls='none', mfc='none',alpha=0.5)
#ax.set_ylim(4.0e-12, 3.0e-10)
ax.set_ylim(1.0e-12, 1.0e-10)


#ed487 model
e_min, e_max = e_thresh, 10.0  #(SZE, Moderate)
#e_min, e_max = 0.75, 10  #(MZE, Moderate)
SpecPara = np.genfromtxt(spec_ed)
amplitude = SpecPara[0]
amplitude_err = SpecPara[1]
index = -1.0 * SpecPara[2]
index_err = SpecPara[3]
e_ref = 1.0 #0.3

#e_amplitude, e_amplitude_err, e_index, e_index_err = amplitude[ind], amplitude_err[ind], index[ind], index_err[ind] 
e_amplitude, e_amplitude_err, e_index, e_index_err = amplitude, amplitude_err, index, index_err
print('ed', e_amplitude, e_amplitude_err, e_index, e_index_err)

pwl =  PowerLawSpectralModel(
                index=e_index, amplitude= e_amplitude * u.Unit('1 / (cm2 s TeV)'),
                reference=e_ref * u.TeV
            )
pwl.plot(ax=ax, sed_type="e2dnde", energy_bounds=[e_thresh, e_max] * u.TeV,
         label="Eventdisplay model fit", color='b', ls='--', alpha=0.5)

pwl.index.error = e_index_err
pwl.amplitude.error = e_amplitude_err
pwl.plot_error(ax=ax, sed_type="e2dnde", energy_bounds=[e_thresh, e_max] * u.TeV, color='b', alpha=0.2)


#gammapy-0.19
flux_gp = FluxPoints.read(file_gp)
flux_gp.plot(ax=ax, sed_type="e2dnde", label="gammapy-0.19", color='r', marker='o', mfc='none')
flux_points_table = flux_gp.to_table(sed_type="dnde", formatted=True)
fp_e_ref = flux_points_table['e_ref']
fp_ref_dnde = flux_points_table['dnde']
fp_dnde_err = flux_points_table['dnde_err']
fp_sqrt_ts = flux_points_table['sqrt_ts']
fp_is_ul = flux_points_table['is_ul']

print('gp #:', np.size(fp_e_ref))
print(fp_e_ref)
#print(fp_ref_dnde, fp_dnde_err)

#gammapy-0.19 model
SpecPara_gp = np.genfromtxt(spec_gp)
gp_amplitude = SpecPara_gp[2]
gp_amplitude_err = SpecPara_gp[3]
gp_index = SpecPara_gp[0]
gp_index_err = SpecPara_gp[1]

#s_amplitude, s_amplitude_err, s_index, s_index_err = gp_amplitude[ind], gp_amplitude_err[ind], gp_index[ind], gp_index_err[ind]
s_amplitude, s_amplitude_err, s_index, s_index_err = gp_amplitude, gp_amplitude_err, gp_index, gp_index_err
print('gp;', s_amplitude, s_amplitude_err, s_index, s_index_err)
#print(fp_is_ul)

pwl =  PowerLawSpectralModel(
                index=s_index, amplitude= s_amplitude * u.Unit('1 / (cm2 s TeV)'),
                reference=e_ref * u.TeV
            )
pwl.plot(ax=ax, sed_type="e2dnde", energy_bounds=[e_thresh, e_max] * u.TeV,
         label="gammapy model fit", color='r', ls='-', alpha=0.5)

pwl.index.error = s_index_err
pwl.amplitude.error = s_amplitude_err
pwl.plot_error(ax=ax, sed_type="e2dnde", energy_bounds=[e_thresh, e_max] * u.TeV, color='r', alpha=0.2)


plt.text(0.15, 0.15e-11,
                 'gp: {:.3}±{:.3}, {:.3}±{:.3}'.format(s_amplitude, s_amplitude_err, s_index, s_index_err),
                 size=12, color='r')
plt.text(0.15, 0.25e-11,
                 'ed: {:.3}±{:.3}, {:.3}±{:.3}'.format(e_amplitude, e_amplitude_err, e_index, e_index_err),
                 size=12, color='b')


#ax.set_xlim(0.1,30.0)
ax.set_xlim(0.1,20)
plt.legend(title='{} (RE)'.format(epoch),loc='upper right', prop={'size': 6})


#y_ratio
ax2 = fig_spec.add_subplot(gs[1, 0], sharex=ax)

y_ratio = fp_ref_dnde / ED_y
y_ratio_err = np.sqrt ( (fp_dnde_err/fp_ref_dnde)**2  + (ED_yerr/ED_y)**2 )
print(y_ratio)
#print(y_ratio_err)


for ip in range(ED_x.size):
    if(ED_ul[ip] == 1 ):
       y_ratio[ip] = 9999.0


ax2.plot(ED_x, y_ratio, 'bo')
#ax2.errorbar(ED_x, y_ratio, xerr=0, yerr=y_ratio_err, marker='o', color='blue', ls='none', mfc='none',alpha=0.5)
ax2.set_ylim(0.9,1.1)
ax2.set_ylabel('F_gp/F_ed')
ax2.hlines(xmin=e_thresh, xmax=e_max, y=1)
ax2.hlines(xmin=e_thresh, xmax=e_max, y=0.9)
ax2.hlines(xmin=e_thresh, xmax=e_max, y=1.1)
ax2.hlines(xmin=e_thresh, xmax=e_max, y=0.975, color='red', ls='--')
ax2.hlines(xmin=e_thresh, xmax=e_max, y=1.025, color='red', ls='--')
ax2.set_xlabel('Energy [TeV]')


# y_ratio histogram
ax2_histy = fig_spec.add_subplot(gs[1, 1], sharey=ax2)
ax2_histy.tick_params(axis="y", labelleft=False)
bins=np.linspace(0.5,1.5,101)
ax2_histy.hist(y_ratio, bins=bins, orientation='horizontal', alpha=0.7, histtype='step', color='blue')


fig_spec.savefig("{}/{}_Spectra_Comparision.png".format(odir, epoch))

