/*
 * plot energy threshold and effective areas as 
 * function of zenith angle and NSB level
 *
 * requires as input the combined effective area files
 *
 * root -l -q -b 'plot.C("../../../v483/V6.runparameter.dat")'
 *
*/

#include "../../utilitities/parameters.C"

#if ROOT_VERSION_CODE >= ROOT_VERSION(6,00,0)
  R__LOAD_LIBRARY($EVNDISPSYS/lib/libVAnaSum.so);
#endif

void printCanvas( TCanvas *c,
                  string iName,
                  string iFigDir = "figures",
                  string iSuffix = ".pdf" )
{
    if( c )
    {
        string iPrintName = iName + iSuffix;
        c->Print( (iFigDir+"/"+iPrintName).c_str() );
    }
}

TGraph* getGraph( TTree *t )
{
    TGraph *iG = new TGraph( 1 );
    if( t )
    {
        iG->SetMarkerColor( t->GetMarkerColor() );
        iG->SetLineColor( t->GetLineColor() );
        iG->SetMarkerStyle( t->GetMarkerStyle() );
        iG->SetMarkerSize( iG->GetMarkerSize()*0.5 );
    }
    return iG;
}

void plot_energy_thresholds( TTree *t,
                             string xtitle,
                             string treevar,
                             float xmin, float xmax,
                             string cutstr,
                             string figname, 
                             string figure_directory )
{
    if( !t ) return;
    TCanvas *c = new TCanvas("c1", "", 10, 10, 400, 400 );
    c->SetGridx( 0 );
    c->SetGridy( 0 );

    TH1D *h = new TH1D("h", "", 1000., xmin, xmax );
    h->SetXTitle( xtitle.c_str() );
    h->SetYTitle( "energy threshold (GeV)" );
    h->SetStats( 0 );
    h->SetMinimum( 0.05 );
    h->SetMaximum( 2. );
    h->Draw();

    TLegend *iLN = new TLegend( 0.70, 0.70, 0.85, 0.85 );

    t->SetMarkerStyle( 20 );
    t->SetLineColor(12);
    t->SetMarkerColor(12);
    t->Draw( ("E_effFract_50p:"+treevar).c_str(), cutstr.c_str(), "p same" );
    iLN->AddEntry( getGraph( t ), "E_{th} at 50\% A_{eff}", "pl" );
    t->SetLineColor(633);
    t->SetMarkerColor(633);
    t->Draw( ("E_effFract_20p:"+treevar).c_str(), cutstr.c_str(), "p same" );
    iLN->AddEntry( getGraph( t ), "E_{th} at 20\% A_{eff}", "pl" );

    t->SetMarkerStyle( 21 );
    t->SetLineColor(9);
    t->SetMarkerColor(9);
    t->Draw( ("E_diffmax:"+treevar).c_str(), cutstr.c_str(), "p same" );
    iLN->AddEntry( getGraph( t ), "E_{diffmax}", "pl" );

    t->SetLineColor(418);
    t->SetMarkerColor(418);
    t->SetMarkerStyle( 24 );
    t->Draw( ("E_sys10p:"+treevar).c_str(), cutstr.c_str(), "p same" );
    iLN->AddEntry( getGraph( t ), "E_{sys, 10p}", "pl" );
    iLN->Draw();
    printCanvas( (TCanvas*)c, figname, figure_directory );

    delete h;
    delete c;
}

void plot_effectiveAreas( TTree *t,
                          string xtitle,
                          string treevar,
                          float xmin, float xmax,
                          string cutstr,
                          string figname, 
                          string figure_directory )
{
    if( !t ) return;

     // effective areas
     TCanvas *cA = new TCanvas("c1A", "", 10, 10, 400, 400 );
     cA->SetGridx( 0 );
     cA->SetGridy( 0 );

     TH1D *hA = new TH1D("hA", "", 1000., xmin, xmax );
     hA->SetXTitle( xtitle.c_str() );
     hA->SetYTitle( "effective area (m^{2})" );
     hA->SetStats( 0 );
     hA->SetMinimum( 0.05 );
     hA->SetMaximum( 1.5e5 );
     hA->Draw();

     TLegend *iLA = new TLegend( 0.70, 0.70, 0.85, 0.85 );

     t->SetMarkerStyle( 20 );
     t->SetLineColor(12);
     t->SetMarkerColor(12);
     iLA->AddEntry( getGraph( t ), "300 GeV", "pl" );
     t->Draw( ("EffArea_300GeV:"+treevar).c_str(), cutstr.c_str(), "p same" );
     t->SetLineColor(633);
     t->SetMarkerColor(633);
     iLA->AddEntry( getGraph( t ), "500 GeV", "pl" );
     t->Draw( ("EffArea_500GeV:"+treevar).c_str(), cutstr.c_str(), "p same" );
     t->SetLineColor(9);
     t->SetMarkerColor(9);
     t->Draw( ("EffArea_1TeV:"+treevar).c_str(), cutstr.c_str(), "p same" );
     iLA->AddEntry( getGraph( t ), "1 TeV", "pl" );

     iLA->Draw();

     printCanvas( cA, figname, figure_directory );

     delete hA;
     delete cA;
}


void plot( string runparameterfile )
{
    RunParameters *fPar = new RunParameters( runparameterfile );
    if( fPar->IsZombie() ) return;
    fPar->print();

    string e_dir = "$VERITAS_EVNDISP_AUX_DIR/EffectiveAreas/";
    string oDir = "../../../" + fPar->fVersion + "/energythresholds/";
    if( gROOT->GetVersionInt()/10000 == 5 )
    {
        int i_load = gSystem->Load( "$EVNDISPSYS/lib/libVAnaSum.so" );
        if( i_load < 0 )
        {
            cout << "Error loading shared library" << endl;
            return;
        }
    }

    // NSB axis depend on HV
    int min_nsb = 45;
    int max_nsb = 500;
    if( runparameterfile.find( "redHV" ) != string::npos )
    {
       min_nsb = 100;
       max_nsb = 1000;
    }

    // loop over all data sets and plot
    for( unsigned int i = 0; i < fPar->fData.size(); i++ )
    {
        if( !fPar->fData[i] ) continue;

        string figure_directory = oDir + fPar->fData[i]->getFigureDirectory();
        gSystem->mkdir( figure_directory.c_str(), kTRUE );

        string iTresholdFile = figure_directory +"/Etresh-"+fPar->fData[i]->getEffectiveAreaFileName();
        cout << figure_directory << endl;
        cout << iTresholdFile << endl;
        VEnergyThreshold a( iTresholdFile );
        if( !a.openEffectiveAreaFile( e_dir + fPar->fData[i]->getEffectiveAreaFileName() ) )
        {
            continue;
        }
        a.calculateEnergyThreshold( false );
        a.writeResults(); 
        a.closeOutputFile();

        cout << "Plotting " << figure_directory << endl;
        TFile iF( iTresholdFile.c_str() );
        if( iF.IsZombie() ) continue;
        TTree *t = (TTree*)iF.Get( "fTreeEth" );
        if( !t ) continue; 
        t->SetMarkerStyle( 20 );
        
        //////////////////////////
       // plotting 

       // this macro only works with a single wobble offset defined
       stringstream iWoffString;
       iWoffString << "-FixedWoff";
       if( fPar->MC_woff.size() > 0 ) iWoffString << (int)(fPar->MC_woff[0]*100);

       // plots as function of nsb
       for( unsigned int n = 0; n < fPar->MC_nsb.size(); n++ )
       {
           stringstream cutstr;
           cutstr << "TMath::Abs(index-" << fPar->MC_index << ")<0.01&&";
           cutstr << "az==" << fPar->MC_az << "&&";
           cutstr << "noise==" << fPar->MC_nsb[n] << "&&";
           if( fPar->MC_woff.size() > 0 ) cutstr << "TMath::Abs(Woff-" << fPar->MC_woff[0] << ")<0.1";
           else cutstr << "TMath::Abs(Woff-0.5)<0.1";

           stringstream figname;
           figname << "ETh-FixedNSB" << fPar->MC_nsb[n] << iWoffString.str();

           plot_energy_thresholds( t,
                                   "zenith angle (deg)",
                                   "ze",
                                   0., 65.,
                                   cutstr.str(),
                                   figname.str(),
                                   figure_directory );

           figname.str( "" );
           figname << "Aeff-FixedNSB" << int(fPar->MC_ze[n]) << iWoffString.str();

           plot_effectiveAreas( t,
                                "zenith angle (deg)",
                                "ze",
                                0., 65.,
                                cutstr.str(),
                                figname.str(),
                                figure_directory );
       }
       /////////////////////////////////////////
       // plots as function of ze
       for( unsigned int n = 0; n < fPar->MC_ze.size(); n++ )
       {
           stringstream cutstr;
           cutstr << "TMath::Abs(index-" << fPar->MC_index << ")<0.01&&";
           cutstr << "az==" << fPar->MC_az << "&&";
           cutstr << "TMath::Abs(ze-" << fPar->MC_ze[n] << ")<0.1&&";
           if( fPar->MC_woff.size() > 0 ) cutstr << "TMath::Abs(Woff-" << fPar->MC_woff[0] << ")<0.1";
           else cutstr << "TMath::Abs(Woff-0.5)<0.1";
 
           stringstream figname;
           figname << "ETh-FixedZe" << int(fPar->MC_ze[n]) << iWoffString.str();

           plot_energy_thresholds( t,
                                   "noise level",
                                   "noise",
                                   min_nsb, max_nsb,
                                   cutstr.str(),
                                   figname.str(),
                                   figure_directory );
           figname.str( "" );
           figname << "Aeff-FixedZe" << int(fPar->MC_ze[n]) << iWoffString.str();

           plot_effectiveAreas( t,
                                "noise level",
                                "noise",
                                min_nsb, max_nsb,
                                cutstr.str(),
                                figname.str(),
                                figure_directory );
       }
   }
}
