/*
 * prepare long pdfs with data MC plots for all periods
 *
 * call this from compareDatawithMC.sh
 *
 */

#if ROOT_VERSION_CODE >= ROOT_VERSION(6,00,0)
  R__LOAD_LIBRARY($EVNDISPSYS/lib/libVAnaSum.so);
#endif


void plot_compare( string oDir )
{
    if( gROOT->GetVersionInt()/10000 == 5 )
    {
        int i_load = gSystem->Load( "$EVNDISPSYS/lib/libVAnaSum.so" );
        if( i_load < 0 )
        {
            cout << "Error loading shared library" << endl;
            return;
        }
    }

    string i_name = oDir + "/mcdatacomparison";

    cout << "Running " << i_name << endl;
    VPlotCompareDataWithMC a( i_name + ".root" );
    if( !a.isZombie() )
    {
        a.plot( i_name );
    }
}
