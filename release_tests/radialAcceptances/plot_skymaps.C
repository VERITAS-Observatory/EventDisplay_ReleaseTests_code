/*
 * testing radial acceptances: plotting sky maps  for
 * data sample used for the generation of acceptances
 * --> should be uniform and N(0,1)
 *
 * plot sky maps
 *
 * root -l -q -b 'plot_skymaps.C( "v483", "RE")'
 * root -l -q -b 'plot_skymaps.C( "v483", "RB")'
 *
 *
 */

#include <string>
#include <vector>

void printCanvas( TCanvas *c, string iName, string iSuffix = ".pdf", string oDir = "./" )
{
    if( c )
    {
        string iPrintName = iName + iSuffix;
        c->Print( (oDir + "/"+iPrintName).c_str() );
    }
}

void plot( string version,
           string iCut = "BDTmoderate2tel", string iBck = "RE",
           string oDir = "./" )
{
    gSystem->mkdir( (oDir + iCut).c_str(), true );

    string iDataDir = "$VERITAS_USER_DATA_DIR/analysis/Results/" + version + "/RadialAcceptances/anasum/";

    vector< string > fEpoch;
// No sky map tests for V4 (mixed set of runs)
//    fEpoch.push_back( "V4" );
//    fEpoch.push_back( "V5" );
    fEpoch.push_back( "V6" );

    vector< string > fTelToAna;
    fTelToAna.push_back( "ID0" );
    fTelToAna.push_back( "ID2" );
    fTelToAna.push_back( "ID3" );
    fTelToAna.push_back( "ID4" );
    fTelToAna.push_back( "ID5" );

    // each year in one plot
    for( unsigned int i = 0; i < fEpoch.size(); i++ )
    {
        string iEpoch = fEpoch[i];
        for( unsigned int t = 0; t < fTelToAna.size(); t++ )
        {
            cout << "Processing " << iEpoch << "  " << fTelToAna[t] << endl;

            string anasum_dir = iDataDir + "anasum_" + fTelToAna[t] + "_" + iEpoch + "_" + iCut + "_" + iBck;
            cout << "reading " << anasum_dir << endl;

            // test if file exists
            TFile iT( (anasum_dir+"/anasum.combined.root").c_str() );
            if( iT.IsZombie() )
            {
                continue;
            }

            VPlotAnasumHistograms f( anasum_dir+"/anasum.combined.root" );
            TCanvas *c = f.plot_radec(0, -3., -3., 3. );
            f.plot_catalogue(c, "tevcat.dat" );
            TCanvas *cSig = f.plot_significanceDistributions(2, 0.4, -8., 8. );

            printCanvas( c, iCut + "/SkyMapRaDec_" + fTelToAna[t] + "_" + iEpoch + "_" + iBck, ".pdf", oDir );
            printCanvas( cSig, iCut + "/SkyMapSignificanceDistribution_" + fTelToAna[t] + "_" + iEpoch + "_" + iBck, ".pdf", oDir );
        }
    }

}

void plot_skymaps( string version, string fBackgroundModel = "RB" )
{
    gSystem->Load( "$EVNDISPSYS/lib/libVAnaSum.so" );
    cout << "Plotting sky maps" << endl;

    string oDir = "../../" + version + "/radialAcceptances/";
    gSystem->mkdir( oDir.c_str(), true );

/*    plot( version, "BDTmoderate2tel", fBackgroundModel, oDir );
    plot( version, "BDTsoft2tel",     fBackgroundModel, oDir );
    plot( version, "BDThard3tel",     fBackgroundModel, oDir ); */
    plot( version, "BDTExtended025moderate2tel", fBackgroundModel, oDir );
    plot( version, "BDTExtended050moderate2tel", fBackgroundModel, oDir );
}
