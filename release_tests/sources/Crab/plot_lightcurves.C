/*
 * plot light curves
 *
 * root -l -q -b 'plot_lightcurves.C("../../../v483/V6.runparameter.dat", "SZE")'
 * root -l -q -b 'plot_lightcurves.C("../../../v483/V6.runparameter.dat", "MZE")'
 * root -l -q -b 'plot_lightcurves.C("../../../v483/V6.runparameter.dat", "LZE")'
 *
 *
 */

#include <fstream>
#include <iomanip>
#include <string>
#include <vector>

R__LOAD_LIBRARY($EVNDISPSYS/lib/libVAnaSum.so)

#include "../../utilities/parameters.C"
#include "../../utilities/printutilities.C"

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
 * Write light curve to CSV file
*/
void write_fluxes(string iFileName, VFluxCalculation *f)
{
    cout << "Writing light curve to " << iFileName << endl;
    std::ofstream out(iFileName.c_str());
    out << "MJD,MJD_width,Run,flux,flux_err\n";
    for (unsigned int i = 0; i < f->getMJD().size(); i++ )
    {
        if( f->getRunList()[i] < 0 ) continue;

        out << fixed << setprecision(4) << f->getMJD()[i] << ", "
            << f->getTOn()[i] / 86400. / 2. << ", "
            << setprecision(0) << (int)f->getRunList()[i] << ", "
            << scientific << setprecision(6)
            << f->getFlux()[i] << ", "
            << f->getFluxError()[i] << "\n";
    }
    out.close();
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

void plot_lightcurves( string anasumfile, string figureDir, double iEnergy_TeV )
{
    if( !loadVAnaSumLibrary() ) return;

    gSystem->mkdir( figureDir.c_str(), true );
    if( iEnergy_TeV < 0. )
    {
        iEnergy_TeV = 0.2;
        if( anasumfile.find( "hard" ) != string::npos )
        {
            iEnergy_TeV = 1.;
        }
        else if( anasumfile.find( "moderate" ) != string::npos
          || anasumfile.find( "Moderate" ) != string::npos )
        {
            iEnergy_TeV = 0.5;
        }
    }

    // average flux+error for whole period
    double fAverageFlux = -1.;
    double fAverageFluxErr = -1.;
    VFluxCalculation f( anasumfile.c_str() );
    if( f.IsZombie() )
    {
        return;
    }
    f.calculateIntegralFlux(iEnergy_TeV);
    double dummy = 0.;
    f.getFlux( -1, fAverageFlux, fAverageFluxErr, dummy );
    cout << "Average flux: " << fAverageFlux << " +- " << fAverageFluxErr << endl;

    // plotting of yearly averages
    vector< double > MJDmin;
    vector< double > MJDmax;
    vector< double > Flux;
    vector< double > FluxError;

    TGraphErrors *g = f.plotFluxesVSMJD( 0, 0., 0, 1, 24 );
    write_fluxes(figureDir + "/LightCurve.csv", &f );
    TCanvas *c = f.getFluxesVSMJDCanvas();
    plotAverageFlux( c, g, fAverageFlux, fAverageFluxErr, 800 );

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
        printCanvas( cFluxD, "/LightCurveDistribution", figureDir );
    }
    printCanvas( c, "/LightCurve", figureDir );

    TCanvas *cElCanvas = f.plotFluxesVSElevation();
    plotAverageFlux( cElCanvas, f.getFluxvsElevation(), fAverageFlux, fAverageFluxErr, 13 );
    printCanvas( cElCanvas, "/LightCurveElevation", figureDir );
    TCanvas *cElPedVars = f.plotFluxesVSPedvars();
    plotAverageFlux( cElPedVars, f.getFluxvsPedvars(), fAverageFlux, fAverageFluxErr, 13 );
    printCanvas( cElPedVars, "/LightCurvePedvars", figureDir );
    TCanvas *cWOCanvas = f.plotFluxesVSWobbleOffset();
    plotAverageFlux( cWOCanvas, f.getFluxvsWobbleOffset(), fAverageFlux, fAverageFluxErr, 13 );
    printCanvas( cWOCanvas, "/LightCurveOffset", figureDir );
}
