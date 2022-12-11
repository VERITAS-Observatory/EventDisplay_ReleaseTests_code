/* plot pedvars vs correction factors for different NSB values
 *
 * from simulations
 *
 * correction factors from MSCW.sizecal.runparameter
 *
 * requires that read_pedvar.sh was running before this step
 *
*/

#include "../utilitities/parameters.C"

void plot_pedvars( string iFile, string oDir, string SimType )
{
    TCanvas *c = new TCanvas( ("c"+iFile).c_str(), iFile.c_str(), 10, 10, 600, 600 );
    c->SetGridx( 0 );
    c->SetGridy( 0 );
    c->Draw();

    TGraph *g = new TGraph( (oDir+"/" + SimType + "/" + iFile+".dat").c_str() );
    if( g->GetN() == 0 )
    {
        cout << "Error reading " << (oDir+"/" + SimType + "/" + iFile+".dat") << endl;
        return;
    }
    g->SetTitle( "" );
    g->SetMarkerStyle( 20 );
    g->SetMarkerColor( 8 );
    g->SetMarkerSize( 2 );
    g->GetHistogram()->SetMaximum( g->GetHistogram()->GetMaximum()*1.1 );

    g->Draw( "ap" );
    g->GetHistogram()->SetYTitle( "ped var" );
    g->GetHistogram()->SetXTitle( "correction factor s" );

    g->Fit( "pol1" );

    c->Print( (oDir + "/" + SimType + "/" + iFile+".pdf").c_str() );
}
   

void plot( string runparameterfile )
{
    RunParameters *fPar = new RunParameters( runparameterfile );
    if( fPar->IsZombie() ) return;

    vector< string > T;
    T.push_back( "T1" );
    T.push_back( "T2" );
    T.push_back( "T3" );
    T.push_back( "T4" );

    string oDir = "../../" + fPar->fVersion + "/nsb/";

    for( unsigned int t = 0; t < T.size(); t++ )
    {
        for( unsigned int n = 0; n < fPar->MC_nsb.size(); n++ )
        {
            stringstream iFile;
            iFile << T[t] << "_NSB" << fPar->MC_nsb[n];
            plot_pedvars( iFile.str(), oDir, fPar->fSimType );
        }
    }
}
