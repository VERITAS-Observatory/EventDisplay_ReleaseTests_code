/*
 * plot IRFs
 *
 * use ./irf_plotting.sh to run this macro
 */

#include <string>
#include <vector>

R__LOAD_LIBRARY($EVNDISPSYS/lib/libVAnaSum.so);

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
        string IRFDirectory,
        string IRFFile,
        string epoch,
        string atmosphere,
        string cut,
        string ze = "20",
        string woff = "0.5",
        string nsb = "200",
        string odir = "./figures/",
        string IRFDirectory_compare = "",
        string IRFFile_compare = ""
        )
{
    VPlotInstrumentResponseFunction a;
    a.addInstrumentResponseData(
            (IRFDirectory+"/"+IRFFile+".root").c_str(),
            atoi(ze.c_str()), atof(woff.c_str()), 0, 1.6, atoi(nsb.c_str()), "A_MC",
            -99, -99, -99, 1.5 );
    if( IRFDirectory_compare.size() > 0 && IRFFile.size() > 0 )
    {
        a.addInstrumentResponseData(
            (IRFDirectory_compare+"/"+IRFFile_compare+".root").c_str(),
            atoi(ze.c_str()), atof(woff.c_str()), 0, 1.6, atoi(nsb.c_str()), "A_MC",
            -99, -99, -99, 1.5 );
    }
    a.setPlottingAxis( "energy_Lin", "X", false, 0.05, 100., "energy [TeV]" );
    // energies for theta2 plot
    vector< double > iE;
    if( atof(ze.c_str()) < 45. )
    {
        iE.push_back( 0.15 );
        iE.push_back( 0.3 );
        iE.push_back( 0.5 );
        iE.push_back( 1. );
        iE.push_back( 5. );
        iE.push_back( 10. );
        iE.push_back( 30. );
        iE.push_back( 50. );
    }
    else if( atof(ze.c_str()) < 55. )
    {
        iE.push_back( 0.5 );
        iE.push_back( 0.8 );
        iE.push_back( 1. );
        iE.push_back( 5. );
        iE.push_back( 10. );
        iE.push_back( 30. );
        iE.push_back( 50. );
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

    c = a.plotTheta(iE, 0.3, false);
    printCanvas( c, "Theta_"+IRFFile, odir);

    a.setPlottingAxis( "energy", "X", true, 1.5, 2. );
    c = a.plotAngularResolution("energy", "68", 0.25 );
    printCanvas( c, "AngRes_"+IRFFile, odir);

    a.setPlottingAxis( "energy", "X", true, 1.5, 2. );
    c = a.plotAngularResolution("energy", "95", 0.45 );
    printCanvas( c, "AngRes95p_"+IRFFile, odir);

    c = a.plotEffectiveArea( 1.e3, 5.e5 );
    printCanvas( c, "EffArea_"+IRFFile, odir);

    c = a.plotEffectiveAreaRatio( 0, 0., 2. );
    printCanvas( c, "EffAreaRatio_"+IRFFile, odir);

    c = a.plotEnergyResolution( 0.5 );
    printCanvas( c, "ERes_"+IRFFile, odir);
}
