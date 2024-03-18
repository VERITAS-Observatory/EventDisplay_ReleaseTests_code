/*
 * plot sky maps
 *
 * root -l -q -b 'plot_skymaps.C("../../../v483/V6.runparameter.dat", "SZE")'
 * root -l -q -b 'plot_skymaps.C("../../../v483/V6.runparameter.dat", "MZE")'
 * root -l -q -b 'plot_skymaps.C("../../../v483/V6.runparameter.dat", "LZE")'
 *
 *
 */

#include <string>
#include <vector>

#include "../../utilitities/parameters.C"
#include "../../utilitities/printutilities.C"

R__LOAD_LIBRARY(/afs/ifh.de/group/cta/scratch/maierg/EVNDISP/EVNDISP-400/GITHUB_Eventdisplay/EventDisplay_v490-el9/lib/libVAnaSum.so)

void plot_skymaps( string anasumfile, string figureDir, bool skymaps = false )
{
    gSystem->mkdir( figureDir.c_str(), true );

    VPlotAnasumHistograms f( anasumfile.c_str() );
    TCanvas *cSig = f.plot_significanceDistributions(2, 0.4, -8., 8. );
    printCanvas( cSig, "/SkyMapSignificanceDistribution", figureDir, ".pdf" );

    if ( skymaps )
    {
        TCanvas *c = f.plot_radec(0, -3., -3., 3. );
        f.plot_catalogue(c, "tevcat.dat" );
        printCanvas( c, "/SkyMapRaDec", figureDir, ".pdf" );
    // non-rescricted sky map
        c = f.plot_radec(0, -4., -3. );
        f.plot_catalogue(c, "tevcat.dat" );
        printCanvas( c, "/SkyMapRaDecMax", figureDir, ".pdf" );
    }
}
