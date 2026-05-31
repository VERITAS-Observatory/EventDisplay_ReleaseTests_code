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

#include "../../utilities/parameters.C"
#include "../../utilities/printutilities.C"

void plot_skymaps( string anasumfile, string figureDir, bool skymaps = false )
{
    if( !loadVAnaSumLibrary() ) return;

    gSystem->mkdir( figureDir.c_str(), true );

    VPlotAnasumHistograms f( anasumfile.c_str() );
    TCanvas *cSig = f.plot_significanceDistributions(2, 0.4, -8., 8. );
    printCanvas( cSig, "/SkyMapSignificanceDistribution", figureDir, ".pdf" );

    if ( skymaps )
    {
        TCanvas *c = f.plot_radec(0, -3., -3., 3. );
        f.plot_catalogue(c, "BrightStarCatalogue.txt" );
        f.plot_catalogue(c, "tevcat.dat" );
        printCanvas( c, "/SkyMapRaDec", figureDir, ".png" );
    // non-rescricted sky map
        c = f.plot_radec(0, -4., -3. );
        f.plot_catalogue(c, "tevcat.dat" );
        printCanvas( c, "/SkyMapRaDecMax", figureDir, ".png" );
    }

    TCanvas *cTh2 = f.plot_theta2(0., 0.15, 5., -9999., -9999., true);
    printCanvas( cTh2, "/Theta2", figureDir, ".pdf" );
}
