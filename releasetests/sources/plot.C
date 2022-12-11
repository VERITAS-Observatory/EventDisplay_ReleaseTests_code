/*
 * plot sky maps
 *
 * root -l -q -b 'plot.C("Tycho")'
 *
 */

#include <string>
#include <vector>

void printCanvas( TCanvas *c, string iName, string iSuffix = ".pdf" )
{
    if( c )
    {
        string iPrintName = iName + iSuffix;
        c->Print( (iPrintName).c_str() );
    }
}


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
    // systematic uncertainty bands +-15%
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

void plot_cut( string iSource, string iCut = "BDTmoderate2tel" )
{
    bool bSkyPlots = true;
    bool bLightCurves = true;
    bool bSpectra = true;

    gSystem->mkdir( (iSource + "/figures/" + iCut).c_str(), true );

    string iDataDir = "$VERITAS_USER_DATA_DIR/analysis/Results/v483b/" + iSource + "/anasum/";

    vector< string > fBackgroundModel;
    fBackgroundModel.push_back( "RE" );
    fBackgroundModel.push_back( "RB" );

    // fluxes are calculated above this energy
    double iEnergy_TeV = 0.2;
    double i_Fit_Elow_TeV = 0.15;
    double i_Fit_Ehigh_TeV = 10.;
    if( iCut.find( "hard" ) != string::npos )
    {
        iEnergy_TeV = 1.;
        i_Fit_Elow_TeV = 0.4;
    }
    else if( iCut.find( "moderate" ) != string::npos
      || iCut.find( "Moderate" ) != string::npos )
    {
        iEnergy_TeV = 0.5;
        i_Fit_Elow_TeV = 0.2;
    }
        
    for( unsigned int b = 0; b < fBackgroundModel.size(); b++ )
    {
        string anasum_dir = iDataDir + "/" + iCut + "_" + fBackgroundModel[b];
        cout << "reading " << anasum_dir << endl;

        // test if file exists
        TFile iT( (anasum_dir+"/anasum.combined.root").c_str() );
        if( iT.IsZombie() )
        {
            continue;
        }

        //////////////////////////////////////
        // sky maps
        if( bSkyPlots )
        {
            cout << "--- sky plots --- " << endl;
            VPlotAnasumHistograms f( anasum_dir+"/anasum.combined.root" );
            TCanvas *c = f.plot_radec(0, -3., -3., 3. );
            f.plot_catalogue(c, "tevcat.dat" );
            f.plot_excludedRegions( c );
            printCanvas( c, iSource + "/figures/" + iCut + "/SkyMapRaDecMinMax_" + fBackgroundModel[b] );
            TCanvas *cSig = f.plot_significanceDistributions(2, 0.4, -8., 8. );
            printCanvas( cSig, iSource + "/figures/" + iCut + "/SkyMapSignificanceDistribution_" + fBackgroundModel[b] );
            TCanvas *cU = f.plot_radec(0, -3. );
            f.plot_catalogue(cU, "tevcat.dat" );
            f.plot_excludedRegions( cU );
            printCanvas( cU, iSource + "/figures/" + iCut + "/SkyMapRaDec_" + fBackgroundModel[b] );
        }
        //////////////////////////////////////
        // light curves
        if( bLightCurves )
        {
            cout << "--- light curves --- " << endl;
            VFluxCalculation fFlux( anasum_dir+"/anasum.combined.root" );
            fFlux.calculateIntegralFlux(iEnergy_TeV);
            TGraphErrors *g = fFlux.plotFluxesVSMJD( 0, 0., 0, 1, 24 );
            double dummy = 0.;
            double fAverageFlux = -1.;
            double fAverageFluxErr = -1.;
            fFlux.getFlux( -1, fAverageFlux, fAverageFluxErr, dummy );
            cout << "Average flux: " << fAverageFlux << " +- " << fAverageFluxErr << endl;
            TCanvas *c = fFlux.getFluxesVSMJDCanvas();
            plotAverageFlux( c, g, fAverageFlux, fAverageFluxErr, 800 );
            printCanvas( c, iSource + "/figures/" + iCut + "/LightCurve_" + fBackgroundModel[b] );
            printCanvas( fFlux.plotFluxesVSElevation(), iSource + "/figures/" + iCut + "/LightCurveElevation_" + fBackgroundModel[b] );
            printCanvas( fFlux.plotFluxesVSPedvars(), iSource + "/figures/" + iCut + "/LightCurvePedvars_" + fBackgroundModel[b] );
            // plot flux distribution
            vector< double > Flux_run = fFlux.getFlux();
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
                 h->SetStats( 0 );
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
                printCanvas( cFluxD, iSource + "/figures/" + iCut + "/LightCurveDistribution_" + fBackgroundModel[b] ); 
            } 
        }
        //////////////////////////////////////
        // spectra
        if( bSpectra )
        {
            cout << "--- spectra --- " << endl;
            VEnergySpectrum e( anasum_dir+"/anasum.combined.root" );
            e.setPlottingEnergyRangeLinear( 0.08, 20. );
            e.setPlottingYaxis( 1.e-15, 8.e-10 );
            e.setSignificanceParameters( 0., 0. );
            e.setEnergyBinning( 0.2 );
            TCanvas *cE = e.plot();
            e.setSpectralFitFluxNormalisationEnergy( 1. );
            e.setSpectralFitRangeLin( i_Fit_Elow_TeV, i_Fit_Ehigh_TeV );
            e.fitEnergySpectrum();
            e.plotFitValues();
            e.printDifferentialFluxes();

            printCanvas( cE,
                         iSource + "/figures/" + iCut + "/Spectrum_" + fBackgroundModel[b] );
            
        }
    }
}

void plot( string iSource = "Tycho" )
{
    gSystem->Load( "$EVNDISPSYS/lib/libVAnaSum.so" );

    gSystem->mkdir( (iSource + "/figures").c_str(), true );

    plot_cut( iSource, "BDTmoderate2tel" );
    plot_cut( iSource, "BDTsoft2tel" );
    plot_cut( iSource, "BDThard3tel" );
}

