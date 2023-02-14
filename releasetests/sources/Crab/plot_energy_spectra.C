/*
 * plot yearly energy spectra
 *
 * root -l -q -b 'plot_energy_spectra.C("v483", "SZE")'
 * root -l -q -b 'plot_energy_spectra.C("v483", "MZE")'
 * root -l -q -b 'plot_energy_spectra.C("v483", "LZE")'
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

/*
 * plot fit parameters vs epoch
 *
 */
void plotFitResults( string iParameter, string iFile, string oDir = "./" )
{
    string fformat;
    string ytitle;
    double ymin = 0.;
    double ymax = 0.;
    if( iParameter == "norm" )
    {
        fformat = "%lg %lg %lg";
        ytitle = "normalisation (1/m2/TeV/s)";
        ymin = 2.7e-11;
        ymax = 4.5e-11;
    }
    else if (iParameter == "index" )
    {
        fformat = "%lg %*lg %*lg %lg %lg";
        ytitle = "index";
        ymin = -2.7;
        ymax = -2.1;
    }
    else if (iParameter == "alpha" )
    {
        fformat = "%lg %*lg %*lg %lg %lg";
        ytitle = "alpha";
        ymin = -2.7;
        ymax = -2.1;
    }
    else if (iParameter == "beta" )
    {
        fformat = "%lg %*lg %*lg %*lg %*lg %lg %lg";
        ytitle = "beta";
        ymin = -0.35;
        ymax = -0.00;
    }
    TGraphErrors *gG = new TGraphErrors( (oDir + iFile + ".dat").c_str(), fformat.c_str() );
    gG->SetTitle( "" );
    gG->SetMinimum( ymin );
    gG->SetMaximum( ymax );

    cout << iParameter << endl;
    gG->Print();

    TCanvas *c = new TCanvas( "c", iParameter.c_str(), 10, 10, 600, 400 );
    c->SetGridx( 0 );
    c->SetGridy( 0 );

    gG->SetMarkerStyle( 21 );

    gG->Draw( "ap" );
    gG->GetHistogram()->SetXTitle( "year" );
    gG->GetHistogram()->GetYaxis()->SetTitleOffset(1.05);
    gG->GetHistogram()->SetYTitle( ytitle.c_str() );

    printCanvas( c, iFile + "_" + iParameter, oDir );
}

void write_fit_para(TF1 *fP, string OutFile)
{
     ofstream Op; 
     Op.open( gSystem->ExpandPathName(OutFile.c_str()) );
         
     std::cout.precision(5); 
     Op << TMath::Abs(fP->GetParameter( 1 )) << "\t";
     Op << fP->GetParError( 1 ) << "\t";
     Op << fP->GetParameter( 0 ) << "\t";
     Op << fP->GetParError( 0 );
     Op << endl;
     cout << "Parameter file written to : "  ;

     Op.close();

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

    // file with fit results
    ofstream osPL;
    osPL.open( (oDir + "/" + figureDir + "/PLfit_" + fPar->fMajorEpoch + ".dat" ).c_str() );
    ofstream osCPL;
    vector< string > fFitResultsParameterNames;
    if( iCut.find( "soft" ) != string::npos ||
      iCut.find( "Soft" ) != string::npos )
    {
        osCPL.open( (oDir + "/" + figureDir + "/CPLfit_" + fPar->fMajorEpoch + ".dat" ).c_str() );
    }

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
       
        // adjust fit range according to cuts
        double i_Fit_Elow_TeV = 0.2;
        double i_Fit_Ehigh_TeV = 10.;
        if( iCut.find( "soft" ) != string::npos 
        || iCut.find( "Soft" ) != string::npos )
        {
            i_Fit_Elow_TeV = 0.14;
        }
        else if( iCut.find( "moderate" ) != string::npos )
        {
            i_Fit_Elow_TeV = 0.190;
        }
        else if( iCut.find( "hard" ) != string::npos )
        {
            i_Fit_Elow_TeV = 0.330;
        }

        VEnergySpectrum e( anasum_dir+"/anasum.combined.root" );
        if( e.isZombie() ) continue;
        // power law fits
        printCanvas( e.plotCrabNebulaSpectrum( 0., i_Fit_Elow_TeV, i_Fit_Ehigh_TeV ),
                     figureDir + "/Spectrum_" + iEpoch, oDir );
        TF1 *fPL = 0;
        if( e.getSpectralFitFunction() )
        {
            fPL = (TF1*)e.getSpectralFitFunction()->Clone();
            if( fPL && iEpoch.size() > 3 )
            {
                osPL << iEpoch.substr( 3, 4 ) << "\t";
                osPL << fPL->GetParameter( 0 ) << "\t";
                osPL << fPL->GetParError( 0 ) << "\t";
                osPL << fPL->GetParameter( 1 ) << "\t";
                osPL << fPL->GetParError( 1 );
                osPL << endl;
                fSuccess = true;
            }
            
            e.writeSpectralPointsToCSVFile( anasum_dir+"/Eventdisplay_" + iEpoch + "_SpecPoints.csv") ;
            write_fit_para(fPL, anasum_dir+"/Eventdisplay_" + iEpoch + "_SpecFit.txt") ;
         }
        // scale by spectral index of ICRC 2015
        // (decided in analysis calls)
        TCanvas *c = e.plotCrabNebulaSpectrum( 2.467, i_Fit_Elow_TeV, i_Fit_Ehigh_TeV );
        if( c && fPL )
        {
            fPL->SetParameter( 1, fPL->GetParameter( 1 ) + 2.467 );
            fPL->SetLineColor( 2 );
            fPL->Draw( "same" );
            printCanvas( c, figureDir + "/Spectrum25_" + iEpoch, oDir );
        }

        // curved power law fits (soft cuts only)
        if( iCut.find( "soft" ) != string::npos 
        || iCut.find( "Soft" ) != string::npos )
        {
            printCanvas( e.plotCrabNebulaSpectrum( 0., i_Fit_Elow_TeV, i_Fit_Ehigh_TeV, 0.1, 4 ), 
                         figureDir + "/SpectrumCPL_" + iEpoch, oDir );
            TF1 *f = 0;
            if( e.getSpectralFitFunction() )
            {
                f = (TF1*)e.getSpectralFitFunction()->Clone();
                if( iEpoch.size() > 3 )
                {
                    osCPL << iEpoch.substr( 3, 4 ) << "\t";
                    osCPL << f->GetParameter( 0 ) << "\t";
                    osCPL << f->GetParError( 0 ) << "\t";
                    osCPL << f->GetParameter( 1 ) << "\t";
                    osCPL << f->GetParError( 1 ) << "\t";
                    osCPL << f->GetParameter( 2 ) << "\t";
                    osCPL << f->GetParError( 2 );
                    osCPL << endl;
                }
            }
            // scale by spectral index of ICRC 2015
            // (decided in analysis calls)
            TCanvas *cPL = e.plotCrabNebulaSpectrum( 2.467, i_Fit_Elow_TeV, i_Fit_Ehigh_TeV, 0.1, -1 );
            if( f && cPL )
            {
                f->SetParameter( 1, f->GetParameter( 1 ) + 2.467 );
                f->SetLineColor( 2 );
                f->Draw( "same" );
                printCanvas( cPL, figureDir + "/SpectrumCPL25_" + iEpoch, oDir );
            }
        }
    }
    if( fEpoch.size() > 1 )
    {
        plotFitResults( "norm", figureDir  + "/PLfit_"+fPar->fMajorEpoch, oDir );
        plotFitResults( "index", figureDir + "/PLfit_"+fPar->fMajorEpoch, oDir );

        osPL.close();
        if( osCPL.is_open() )
        {
            osCPL.close();
            plotFitResults( "norm", figureDir + "/CPLfit_"+fPar->fMajorEpoch, oDir );
            plotFitResults( "alpha", figureDir + "/CPLfit_"+fPar->fMajorEpoch, oDir );
            plotFitResults( "beta", figureDir + "/CPLfit_"+fPar->fMajorEpoch, oDir );
        }
    }

    // check consistency output
    // --> for now anasum file found: remove directory
/*    if( !fSuccess )
    {
        gSystem->Exec( ("rm -rf " + oDir+"/"+figureDir).c_str() );
    } */
}



void plot_energy_spectra( string runparameterfile, string fElevation = "SZE",
                   string fBackgroundModel = "RE" )
{
    RunParameters *fPar = new RunParameters( runparameterfile );
    if( fPar->IsZombie() ) return;
    fPar->print();

    cout << "Plotting energy spectra" << endl;

    vector< string > fAtmosphere = fPar->getAtmosphereVector( "ATM" );
    fAtmosphere.push_back( "" );
    vector< string > fCuts = fPar->getCutsVector();

    // output directory
    string oDir = "../../../../EventDisplay_ReleaseTests_" + fPar->fVersion + "/" + fPar->fSource + "/figures/";
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
