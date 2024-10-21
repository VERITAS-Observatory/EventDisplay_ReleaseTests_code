/*
 * plot yearly energy spectra
 *
 * root -l -q -b 'plot_energy_spectra.C("v483", "SZE")'
 * root -l -q -b 'plot_energy_spectra.C("v483", "MZE")'
 * root -l -q -b 'plot_energy_spectra.C("v483", "LZE")'
 *
 *
 */

#include <fstream>
#include <string>
#include <vector>

#include "TF1.h"

#include "../../utilitities/parameters.C"
#include "../../utilitities/printutilities.C"

R__LOAD_LIBRARY(/afs/ifh.de/group/cta/scratch/maierg/EVNDISP/EVNDISP-400/GITHUB_Eventdisplay/EventDisplay_v491-al9/lib/libVAnaSum.so)

using namespace std;

void plot_energy_spectra( string anasumfile, string figureDir )
{

    // file with fit results
    ofstream osPL;
    osPL.open( ( figureDir + "/PLfit.dat" ).c_str() );
    ofstream osCPL;
    if( anasumfile.find( "soft" ) != string::npos || anasumfile.find( "Soft" ) != string::npos )
    {
        osCPL.open( (figureDir + "/CPLfit.dat" ).c_str() );
    }
    vector< string > fFitResultsParameterNames;

    // adjust fit range according to cuts
    double i_Fit_Elow_TeV = 0.2;
    double i_Fit_Ehigh_TeV = 10.;
    if( anasumfile.find( "soft" ) != string::npos
    || anasumfile.find( "Soft" ) != string::npos )
    {
        i_Fit_Elow_TeV = 0.14;
    }
    else if( anasumfile.find( "moderate" ) != string::npos )
    {
        i_Fit_Elow_TeV = 0.190;
    }
    else if( anasumfile.find( "hard" ) != string::npos )
    {
        i_Fit_Elow_TeV = 0.330;
    }

    VEnergySpectrum e( anasumfile.c_str() );
    e.setSignificanceParameters( 2., 3 );
    if( e.isZombie() ) return;
    // power law fits
    printCanvas( e.plotCrabNebulaSpectrum( 0., i_Fit_Elow_TeV, i_Fit_Ehigh_TeV ),
                 "/Spectrum", figureDir );
    TF1 *fPL = 0;
    if( e.getSpectralFitFunction() )
    {
        fPL = (TF1*)e.getSpectralFitFunction()->Clone();
        if( fPL )
        {
            osPL << fPL->GetParameter( 0 ) << "\t";
            osPL << fPL->GetParError( 0 ) << "\t";
            osPL << fPL->GetParameter( 1 ) << "\t";
            osPL << fPL->GetParError( 1 );
            osPL << endl;
        }

        e.writeSpectralPointsToCSVFile( figureDir + "/SpecPoints.csv") ;
     }

    // scale by spectral index of ICRC 2015
    // (decided in analysis calls)
    TCanvas *c = e.plotCrabNebulaSpectrum( 2.467, i_Fit_Elow_TeV, i_Fit_Ehigh_TeV );
    if( c && fPL )
    {
        fPL->SetParameter( 1, fPL->GetParameter( 1 ) + 2.467 );
        fPL->SetLineColor( 2 );
        fPL->Draw( "same" );
        printCanvas( c, "/Spectrum25", figureDir );
    }
    // curved power law fits (not for hard cuts)
    if( anasumfile.find( "hard" ) == string::npos
    && anasumfile.find( "Hard" ) == string::npos )
    {
        printCanvas( e.plotCrabNebulaSpectrum( 0., i_Fit_Elow_TeV, i_Fit_Ehigh_TeV, 0.1, 4 ),
                     "/SpectrumCPL", figureDir );
        TF1 *f = 0;
        if( e.getSpectralFitFunction() )
        {
            f = (TF1*)e.getSpectralFitFunction()->Clone();
            osCPL << f->GetParameter( 0 ) << "\t";
            osCPL << f->GetParError( 0 ) << "\t";
            osCPL << f->GetParameter( 1 ) << "\t";
            osCPL << f->GetParError( 1 ) << "\t";
            osCPL << f->GetParameter( 2 ) << "\t";
            osCPL << f->GetParError( 2 );
            osCPL << endl;
        }
        // scale by spectral index of ICRC 2015
        // (decided in analysis calls)
        TCanvas *cPL = e.plotCrabNebulaSpectrum( 2.467, i_Fit_Elow_TeV, i_Fit_Ehigh_TeV, 0.1, -1 );
        if( f && cPL )
        {
            f->SetParameter( 1, f->GetParameter( 1 ) + 2.467 );
            f->SetLineColor( 2 );
            f->Draw( "same" );
            printCanvas( cPL, "/SpectrumCPL25_", figureDir );
        }
    }
}
