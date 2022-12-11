/*
 * plot IRFs
 *
 *
 *  root -l -q -b 'plot_irf.C("/lustre/fs23/group/veritas/IRFPRODUCTION/v490/TS/CARE_June2020/", "V6_2019_2020w", "61", "NTel2-PointSource-Moderate" )'
 *
 */

#include <string>
#include <vector>

#if ROOT_VERSION_CODE >= ROOT_VERSION(6,00,0)
  R__LOAD_LIBRARY($EVNDISPSYS/lib/libVAnaSum.so);
#endif

void printCanvas( TCanvas *c, string iName, string oDir )
{
    string iSuffix = ".pdf";
    if( c )
    {
        string iPrintName = iName + iSuffix;
        c->Print( (oDir+"/"+iPrintName).c_str() );
    }
}

/*
 * plot IRFs as function for a given set of parameter
 *
 */
void plot_irf( 
        string IRFdirectory,
        string epoch,
        string atmosphere,
        string cut,
        string ze = "20",
        string woff = "0.5",
        string nsb = "200",
        string odir = "./figures/",
        string dir_suff_2 = "_DISP"
        )
{
    string IRFDirectory = 
        IRFdirectory + "/" +
        epoch + "_ATM" + 
        atmosphere + "_gamma/" +
        "EffectiveAreas_Cut-" + cut;

    cout << "IRFDIR: " << IRFDirectory << endl;

    string IRFFile =
        "EffArea-CARE_June2020-" +
        epoch + "-ID0-Ze" +
        ze + "deg-" +
        woff + "wob-" +
        nsb + "-Cut-" +
        cut;

    VPlotInstrumentResponseFunction a;
    a.addInstrumentResponseData(
            (IRFDirectory+"/"+IRFFile+".root").c_str(),
            atoi(ze.c_str()), atof(woff.c_str()), 0, 1.6, atoi(nsb.c_str()), "A_MC",
            -99, -99, -99, 1.5 );
    if( dir_suff_2.size() > 0 )
    {
        a.addInstrumentResponseData(
                (IRFDirectory+dir_suff_2+"/"+IRFFile+".root").c_str(),
                atoi(ze.c_str()), atof(woff.c_str()), 0, 1.6, atoi(nsb.c_str()), "A_MC",
                -99, -99, -99, 1.5 );
    }
    // energies for theta2 plot
    vector< double > iE;
    if( atof(ze.c_str()) < 45. )
    {
        iE.push_back( 0.3 );
        iE.push_back( 0.5 );
        iE.push_back( 1. );
        iE.push_back( 10. );
        iE.push_back( 20. );
        iE.push_back( 30. );
    }
    else if( atof(ze.c_str()) < 55. )
    {
        iE.push_back( 0.5 );
        iE.push_back( 0.8 );
        iE.push_back( 1. );
        iE.push_back( 10. );
        iE.push_back( 20. );
        iE.push_back( 30. );
    }
    else
    {
        iE.push_back( 0.8 );
        iE.push_back( 1. );
        iE.push_back( 5. );
        iE.push_back( 10. );
        iE.push_back( 30. );
        iE.push_back( 50. );
    }
    TCanvas *c = 0;
    c = a.plotTheta(iE, 0.3, true);
    printCanvas( c, "ThetaCumulative_"+IRFFile, odir);

    a.setPlottingAxis( "energy", "X", true, 1.5, 2. );
    c = a.plotAngularResolution("energy", "68", 0.25 );
    printCanvas( c, "AngRes_"+IRFFile, odir);

    c = a.plotEffectiveArea( 1.e2, 8.e5 );
    printCanvas( c, "EffArea_"+IRFFile, odir);

    c = a.plotEffectiveAreaRatio( 0, 0., 2. );
    printCanvas( c, "EffAreaRatio_"+IRFFile, odir);

    c = a.plotEnergyResolution();
    printCanvas( c, "ERes_"+IRFFile, odir);

    c = a.plotCoreResolution();
    printCanvas( c, "CoreRes_"+IRFFile, odir);
}
