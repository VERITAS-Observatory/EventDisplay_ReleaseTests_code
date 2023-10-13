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

#if ROOT_VERSION_CODE >= ROOT_VERSION(6,00,0)
  R__LOAD_LIBRARY($EVNDISPSYS/lib/libVAnaSum.so);
#endif

void plot( RunParameters* fPar,
           string iCut,
           string iATM, 
           string iElevation,
           string iBck,
           string oDir )
{
    if( !fPar ) return;

    bool fSuccess = false;

    // get epochs vector (with major epoch)
    vector< string > fEpoch = fPar->getEpochsVector( true );
    // check for redHV
    string iMajorEpoch = fPar->fMajorEpoch;
    string iRedHV = "";
    if( fPar->fMajorEpoch.find( "redHV" ) != string::npos )
    {
       iMajorEpoch = "V6_redHV";
       iRedHV = "_redHV";
    }
    if( iATM.size() > 0 ) iATM = "_" + iATM;

    string figureDir = iCut + iRedHV + iATM + "_" + iElevation;
    gSystem->mkdir( (oDir+"/"+figureDir).c_str(), true );


    // each year in one plot
    for( unsigned int i = 0; i < fEpoch.size(); i++ )
    {
        string iEpoch = fEpoch[i];
        iEpoch += iRedHV;
        if( iATM.size() > 0 )
        {
           iEpoch += iATM;
        }
        cout << "Processing " << iEpoch << endl;

        string anasum_dir = fPar->getDataDir() + "anasum_" + iEpoch + "_" + iCut + "_" + iElevation + "_" + iBck;
        cout << "reading " << anasum_dir << endl;

        TFile iT( (anasum_dir+"/anasum.combined.root").c_str() );
        if( iT.IsZombie() )
        {
            continue;
        }
        fSuccess = true;

        VPlotAnasumHistograms f( anasum_dir+"/anasum.combined.root" );
        TCanvas *c = f.plot_radec(0, -3., -3., 3. );
        f.plot_catalogue(c, "tevcat.dat" );
        TCanvas *cSig = f.plot_significanceDistributions(2, 0.4, -8., 8. );

        printCanvas( c,
                     figureDir + "/SkyMapRaDec_" + iEpoch + "_" + iBck,
                     oDir, ".pdf" );
        printCanvas( cSig, 
                     figureDir + "/SkyMapSignificanceDistribution_" + iEpoch + "_" + iBck,
                     oDir, ".pdf" );
 
        // non-rescricted sky map
        c = f.plot_radec(0, -4., -3. );
        f.plot_catalogue(c, "tevcat.dat" );
        printCanvas( c,
                     figureDir + "/SkyMapRaDecMax_" + iEpoch + "_" + iBck,
                     oDir, ".pdf" );
    }

    // check consistency output
    // --> for now anasum file found: remove directory
    if( !fSuccess )
    {
        gSystem->Exec( ("rm -rf " + oDir+"/"+figureDir).c_str() );
    }
}

void plot_skymaps( string runparameterfile, string fElevation = "SZE", 
                   string fBackgroundModel = "RE" )
{
    RunParameters *fPar = new RunParameters( runparameterfile );
    if( fPar->IsZombie() ) return;

    cout << "Plotting sky maps" << endl;

    vector< string > fAtmosphere = fPar->getAtmosphereVector( "ATM" );
    fAtmosphere.push_back( "" );
    vector< string > fCuts = fPar->getCutsVector();

    // output directory
    string oDir = "../../../../EventDisplay_Release_" + fPar->fVersion + "/" + fPar->fSource;
    oDir += "/figures/";
    gSystem->mkdir( oDir.c_str(), true );
    cout << "figures will be written to " << oDir << endl;

    for( unsigned int i = 0; i < fAtmosphere.size(); i++ )
    {
        for( unsigned int c = 0; c < fCuts.size(); c++ )
        {
            plot( fPar,
                  fCuts[c],
                  fAtmosphere[i], 
                  fElevation, 
                  fBackgroundModel,
                  oDir );
        }
    }
}
