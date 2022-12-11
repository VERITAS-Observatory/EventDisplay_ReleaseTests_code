/*  
 *  print and plot sensitivities calculated
 *  from Crab rates for different cuts
 *
 *  missing: 
 *  - main plotting routine
 *  - loop over all epochs / cuts
 *  - print and testing
 *
 */

void printCanvas( TCanvas *c, string iName )
{
    string iSuffix = ".pdf";
    if( c )
    {
        string iPrintName = iName + iSuffix;
        c->Print( iPrintName.c_str() );
    }
}

void crab_rates( string result_file_suffix = "" )
{
    string data_dir = "$VERITAS_USER_DATA_DIR/analysis/Results/g500//Crab/g500_V6_anasum_TL5025/";
    vector< string > fCrabFiles;

    /*fCrabFiles.push_back( "TL5025_ID0_NTel2-PointSource-Soft-TMVA-BDT_RE_N8" );
    fCrabFiles.push_back( "TL5025_ID0_NTel2-PointSource-Moderate-TMVA-BDT_RE_N8" );
    fCrabFiles.push_back( "TL5025_ID0_NTel3-PointSource-Moderate-TMVA-BDT_RE_N8" );
    fCrabFiles.push_back( "TL5025_ID0_NTel4-PointSource-Moderate-TMVA-BDT_RE_N8" );
    fCrabFiles.push_back( "TL5025_ID0_NTel3-PointSource-Hard-TMVA-BDT_RE_N8" );
    fCrabFiles.push_back( "TL5025_ID0_NTel4-PointSource-Hard-TMVA-BDT_RE_N8" ); */

    fCrabFiles.push_back( "TL5025_ID0_NTel3-PointSource-Moderate-TMVA-BDT_RE_N8" );
    fCrabFiles.push_back( "TL5025_ID0_NTel2-PointSource-Soft-TMVA-BDT_RE_N8" );
    fCrabFiles.push_back( "TL5025_ID0_NTel3-PointSource-Hard-TMVA-BDT_RE_N8" );

    vector< double > gamma_rate;
    vector< double > bck_rate;

    // output is written to a text file
    ofstream result_file;
    result_file.open( ("sensitivities"+result_file_suffix+".txt").c_str() );


    for( unsigned int i = 0; i < fCrabFiles.size(); i++ )
    {
        TFile *f = new TFile( (data_dir+fCrabFiles[i]+".root").c_str() );
        if( f->IsZombie() || !f->cd( "total_1/stereo" ) ) 
        {
            continue;
        }
        TTree *t = (TTree*)gDirectory->Get( "tRunSummary" );
        if( !t )
        {
            continue;
        }
        int runOn = 0;
        double Rate = 0.;
        double RateOff = 0.;
        t->SetBranchAddress( "runOn", &runOn );
        t->SetBranchAddress( "Rate", &Rate  );
        t->SetBranchAddress( "RateOff", &RateOff  );
        for( int j = 0; j < t->GetEntries(); j++ )
        {
            t->GetEntry( j );
            if( runOn < 0 )
            {
                 break;
            }
        }
        result_file << "---" << endl;
        result_file << fCrabFiles[i] << endl;
        result_file << "\t Gamma-ray rate: " << Rate << endl;
        result_file<< "\t Bck rate: " << RateOff << endl;
        VSensitivityCalculator a;
        a.addDataSet( Rate, RateOff, 1./6 );
        a.list_sensitivity( 0, result_file );

        printCanvas( a.plotObservationTimevsFlux(), fCrabFiles[i] + result_file_suffix );
    }
    result_file.close();
}

void crab_sensitivity()
{
    VSensitivityCalculator a;
    a.setFluxRange_CU( 5.e-3, 10. );
     a.plotDifferentialSensitivityvsEnergyFromCrabSpectrum( 0, "anasum_V6_2012_2013a_ATM62_BDTmoderate2tel_SZE_RE/anasum.combined.root");
}
