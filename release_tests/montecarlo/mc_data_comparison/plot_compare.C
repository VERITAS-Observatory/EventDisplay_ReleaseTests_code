/*
 * prepare long PDFs with data MC plots for all periods
 *
 * call this from compareDatawithMC.sh
 *
 */

R__LOAD_LIBRARY($EVNDISPSYS/lib/libVAnaSum.so);

void plot_compare( string oDir )
{
    string i_name = oDir + "/mcdatacomparison";

    cout << "Running " << i_name << endl;
    VPlotCompareDataWithMC a( i_name + ".root" );
    if( !a.isZombie() )
    {
        a.plot( i_name );
    }
}
