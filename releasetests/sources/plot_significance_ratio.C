void plot_significance_ratio( string iPath )
{
    string fv490_file = "/lustre/fs23/group/veritas/users/maierg/analysis/Results/v490/AP/SourceTests/";
    string fv487_file = "/lustre/fs23/group/veritas/users/maierg/analysis/Results/v487f/SourceTests/";

    // check that there is the same number of entries in both files
    TFile *fv490 = new TFile( (fv490_file + iPath + "/anasum.combined.root" ).c_str() );
    if( fv490->IsZombie() ) return;
    TTree *fv490_t = (TTree*)fv490->Get("total_1/stereo/tRunSummary" );
    if( !fv490_t ) return;
    int fv490_n = fv490_t->GetEntries();

    TFile *fv487 = new TFile( (fv487_file + iPath + "/anasumCombined.root" ).c_str() );
    if( fv487->IsZombie() ) return;
    TTree *fv487_t = (TTree*)fv487->Get("total_1/stereo/tRunSummary" );
    if( !fv487_t ) return;
    int fv487_n = fv487_t->GetEntries();

    if( fv490_n != fv487_n )
    {
        cout << "Different number of entries in " << iPath << endl;
        return;
    }
    cout << "Found " << fv490_n << " entries in " << iPath << endl;

    fv490_t->AddFriend( "t=total_1/stereo/tRunSummary", (fv487_file + iPath + "/anasumCombined.root" ).c_str() );

    TCanvas *c = new TCanvas( "c", "", 10, 10, 600, 600 );
    c->Draw();

    TH1D *h = new TH1D( "h", iPath.c_str(), 50, 0., 3. );

    fv490_t->Draw("Signi/t.Signi>>h", "runOn>0&&Signi>2.&&t.Signi>2.", "" );

    h->Draw();

    c->Print( (fv490_file + iPath + "/SignificanceRatioTov487.pdf").c_str() );
    c->Print( (fv490_file + iPath + "/SignificanceRatioTov487.png").c_str() );


}
