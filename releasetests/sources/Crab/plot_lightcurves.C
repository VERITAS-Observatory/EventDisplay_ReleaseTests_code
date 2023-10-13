/*
 * plot light curves
 *
 * root -l -q -b 'plot_lightcurves.C("../../../v483/V6.runparameter.dat", "SZE")'
 * root -l -q -b 'plot_lightcurves.C("../../../v483/V6.runparameter.dat", "MZE")'
 * root -l -q -b 'plot_lightcurves.C("../../../v483/V6.runparameter.dat", "LZE")'
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

double getMinMax( vector< double > iMJD, bool bMax )
{
    double iMin = 1.e9;
    double iMax = 0.;
    for( unsigned int i = 0; i < iMJD.size(); i++ )
    {
         if( iMJD[i] < 100 ) continue;
         if( iMJD[i] > iMax ) iMax = iMJD[i];
         if( iMin > iMJD[i] ) iMin = iMJD[i];
    }
    if( bMax ) return iMax;

    return iMin;
}

/*
 * plot Average fluxes plus errors
 *
 * fA: average flux
 * fAE: error on average flux
 * script assumes 20% systematic uncertainty
 */
void plotAverageFlux( TCanvas *c, TGraphErrors *g, double fA, double fAE, int iColor )
{
    if( !c || fAE < 0. || !g )
    {
        return;
    }
    TLine* iL3 = new TLine( 
                       g->GetHistogram()->GetXaxis()->GetXmin(), fA,
                       g->GetHistogram()->GetXaxis()->GetXmax(), fA );
    iL3->SetLineColor( iColor );
    iL3->Draw();

    TLine* iL3b = new TLine( 
                       g->GetHistogram()->GetXaxis()->GetXmin(), fA-fAE,
                       g->GetHistogram()->GetXaxis()->GetXmax(), fA-fAE );
    iL3b->SetLineColor( iColor );
    iL3b->SetLineStyle( 2 );
    iL3b->Draw();
    TLine* iL3c = new TLine( 
                       g->GetHistogram()->GetXaxis()->GetXmin(), fA+fAE,
                       g->GetHistogram()->GetXaxis()->GetXmax(), fA+fAE );
    iL3c->SetLineColor( iColor );
    iL3c->SetLineStyle( 2 );
    iL3c->Draw();
    // systematic uncertainty bands +-20%
    double iSys = 0.2;
    TLine* iS3b = new TLine( 
                       g->GetHistogram()->GetXaxis()->GetXmin(), (1.-iSys)*fA,
                       g->GetHistogram()->GetXaxis()->GetXmax(), (1.-iSys)*fA );
    iS3b->SetLineColor( iColor );
    iS3b->SetLineStyle( 3 );
    iS3b->Draw();
    TLine* iS3c = new TLine( 
                       g->GetHistogram()->GetXaxis()->GetXmin(), (1.+iSys)*fA,
                       g->GetHistogram()->GetXaxis()->GetXmax(), (1.+iSys)*fA);
    iS3c->SetLineColor( iColor );
    iS3c->SetLineStyle( 3 );
    iS3c->Draw();
    
}

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
    // fluxes are calculated above this energy
    double iEnergy_TeV = 0.2;
    if( iCut.find( "hard" ) != string::npos )
    {
        iEnergy_TeV = 1.;
    }
    else if( iCut.find( "moderate" ) != string::npos
      || iCut.find( "Moderate" ) != string::npos )
    {
        iEnergy_TeV = 0.5;
    }

    // average flux+error for whole period
    double fAverageFlux = -1.;
    double fAverageFluxErr = -1.;
    string anasum_dir = fPar->getDataDir() + "anasum_" + iMajorEpoch + "_" + iCut + "_" + iElevation + "_" + iBck;
    TFile iT( (anasum_dir+"/anasum.combined.root").c_str() );
    if( !iT.IsZombie() )
    {
        VFluxCalculation f( anasum_dir+"/anasum.combined.root" );
        if( f.IsZombie() )
        {
            return;
        }
        f.calculateIntegralFlux(iEnergy_TeV);
        double dummy = 0.;
        f.getFlux( -1, fAverageFlux, fAverageFluxErr, dummy );
        cout << "Average flux: " << fAverageFlux << " +- " << fAverageFluxErr << endl;
    }

    // plotting of yearly averages
    vector< double > MJDmin;
    vector< double > MJDmax;
    vector< double > Flux;
    vector< double > FluxError;

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

        // test if file exists
        TFile iT( (anasum_dir+"/anasum.combined.root").c_str() );
        if( iT.IsZombie() )
        {
            continue;
        }
        fSuccess = true;

        VFluxCalculation f( anasum_dir+"/anasum.combined.root" );
        f.calculateIntegralFlux(iEnergy_TeV);
        TGraphErrors *g = f.plotFluxesVSMJD( 0, 0., 0, 1, 24 );
        TCanvas *c = f.getFluxesVSMJDCanvas();
        plotAverageFlux( c, g, fAverageFlux, fAverageFluxErr, 800 );

        // plot average flux for this epoch
        double dummy = 0.;
        double i_av_flux = 0.;
        double i_av_fluxE = 0.;
        f.getFlux( -1, i_av_flux, i_av_fluxE, dummy );
        cout << "Average flux for " << iEpoch << " " << iCut << ": ";
        cout << i_av_flux << " +- " << i_av_fluxE << endl;
        if( fEpoch[i] != "V6" )
        {
            plotAverageFlux( c, g, i_av_flux, i_av_fluxE, 13 );
            Flux.push_back( i_av_flux );
            FluxError.push_back( i_av_fluxE );
            vector< double > iMJD = f.getMJD();
            MJDmin.push_back( getMinMax( iMJD, false ) );
            MJDmax.push_back( getMinMax( iMJD, true ) );
        }
        else
        {
            for( unsigned int l = 0; l < Flux.size(); l++ )
            {
                 TLine *iL = new TLine( MJDmin[l], Flux[l], MJDmax[l], Flux[l] );
                 iL->SetLineColor(2);
                 iL->SetLineWidth( 2 );
                 iL->Draw();
                 TLine *iLM = new TLine( MJDmin[l], Flux[l]-FluxError[l], MJDmax[l], Flux[l]-FluxError[l] );
                 iLM->SetLineColor(2);
                 iLM->SetLineStyle( 2 );
                 iLM->Draw();
                 TLine *iLP = new TLine( MJDmin[l], Flux[l]+FluxError[l], MJDmax[l], Flux[l]+FluxError[l] );
                 iLP->SetLineColor(2);
                 iLP->SetLineStyle( 2 );
                 iLP->Draw();
            }
        }

        // plot flux distribution
        vector< double > Flux_run = f.getFlux();
        TCanvas *cFluxD = 0;
        if( Flux_run.size() > 2 )
        {
            double i_flux_min = 1.e10;
            double i_flux_max = 0.;
            TCanvas *cFluxD = 0;
            cout << "FLUX " << Flux_run.size() << endl;
            for( unsigned int j = 0; j < Flux_run.size(); j++ )
            { 
                 if( Flux_run[j] > 0. && Flux_run[j] < i_flux_min )
                 {
                     i_flux_min = Flux_run[j];
                 }
                 if( Flux_run[j] > 0. && Flux_run[j] > i_flux_max )
                 {
                     i_flux_max = Flux_run[j];
                 }
             }
             cout << "\t" << i_flux_min << "\t" << i_flux_max << endl;
             TH1D *h = new TH1D( "hfl", "", 100, 0.75*i_flux_min, 1.25*i_flux_max );
             h->SetStats( 1 );
             gStyle->SetOptStat( 200 );
             gStyle->SetOptFit( 0 );
             char hname[200];
             sprintf( hname, "Fluxes (E > %.2f TeV) [cm^{-2} s^{-1}]", iEnergy_TeV );
             h->SetXTitle( hname );
             h->SetYTitle( "Number of runs" );
             h->SetLineWidth( 2 );
             cFluxD = new TCanvas( "cFL", "", 10, 10, 600, 600 );
             cFluxD->SetGridx( 0 );
             cFluxD->SetGridy( 0 );
             cFluxD->Draw();
             for( unsigned int j = 0; j < Flux_run.size(); j++ )
             { 
                  h->Fill( Flux_run[j] );
             }
             h->Fit("gaus");
             h->Draw();
            printCanvas( cFluxD, figureDir + "/LightCurveDistribution" + iEpoch, oDir ); 
        } 

        printCanvas( c, figureDir + "/LightCurve_" + iEpoch, oDir );

        TCanvas *cElCanvas = f.plotFluxesVSElevation();
        plotAverageFlux( cElCanvas, f.getFluxvsElevation(), i_av_flux, i_av_fluxE, 13 );
        printCanvas( cElCanvas, figureDir + "/LightCurveElevation_" + iEpoch, oDir );
        TCanvas *cElPedVars = f.plotFluxesVSPedvars();
        plotAverageFlux( cElPedVars, f.getFluxvsPedvars(), i_av_flux, i_av_fluxE, 13 );
        printCanvas( cElPedVars, figureDir + "/LightCurvePedvars" + iEpoch, oDir );
        TCanvas *cWOCanvas = f.plotFluxesVSWobbleOffset();
        plotAverageFlux( cWOCanvas, f.getFluxvsWobbleOffset(), i_av_flux, i_av_fluxE, 13 );
        printCanvas( cWOCanvas, figureDir + "/LightCurveOffset" + iEpoch, oDir );
    }

    // check consistency output
    // --> for now anasum file found: remove directory
    if( !fSuccess )
    {
        gSystem->Exec( ("rm -rf " + oDir+"/"+figureDir).c_str() );
    }
}

void plot_lightcurves( string runparameterfile, string fElevation = "SZE",
                   string fBackgroundModel = "RE" )
{
    RunParameters *fPar = new RunParameters( runparameterfile );
    if( fPar->IsZombie() ) return;

    cout << "Plotting light curves" << endl;

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
