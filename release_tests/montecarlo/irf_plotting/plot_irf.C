/*
 * plot IRFs
 *
 * use ./irf_plotting.sh to run this macro
 */

#include <string>
#include <vector>

#include "TImage.h"

R__LOAD_LIBRARY($EVNDISPSYS/lib/libVAnaSum.so);

void printCanvas( TCanvas *c, string iName, string oDir )
{
    string iSuffix = ".png";
    if( c )
    {
        string iPrintName = iName + iSuffix;
        c->SetCanvasSize(c->GetWw()*2, c->GetWh()*2);
        c->Modified();
        c->Update();
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
        string az = "0",
        string odir = "./figures/",
        string IRFDirectory_compare = "",
        string IRFFile_compare = ""
        )
{
    float base_index = 1.5;

    VPlotInstrumentResponseFunction a;
    a.addInstrumentResponseData(
            (IRFDirectory+"/"+IRFFile+".root").c_str(),
            atoi(ze.c_str()), atof(woff.c_str()), atoi(az.c_str()), base_index, atoi(nsb.c_str()), "A_MC",
            -99, -99, -99, 1.5 );
    if( IRFDirectory_compare.size() > 0 && IRFFile.size() > 0 )
    {
        a.addInstrumentResponseData(
            (IRFDirectory_compare+"/"+IRFFile_compare+".root").c_str(),
            atoi(ze.c_str()), atof(woff.c_str()), atoi(az.c_str()), base_index, atoi(nsb.c_str()), "A_MC",
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

    c = a.plotEnergyReconstructionBias("mean", -0.4, 0.4);
    printCanvas( c, "EBias_"+IRFFile, odir);

    /*
    // plot comparision of 4 and 3-telescope effective areas
    VPlotInstrumentResponseFunction b;
    b.addInstrumentResponseData(
            (IRFDirectory+"/"+IRFFile+".root").c_str(),
            atoi(ze.c_str()), atof(woff.c_str()), 0, base_index, atoi(nsb.c_str()), "A_MC",
            -99, -99, -99, 1.5 );
    for( unsigned int i = 2; i <=5; i++ )
    {
        string IRFFile3Tel = IRFFile;
        IRFFile3Tel.replace(IRFFile3Tel.find("ID0"), 3, "ID" + std::to_string(i) );
        b.addInstrumentResponseData(
            (IRFDirectory+"/"+IRFFile3Tel+".root").c_str(),
            atoi(ze.c_str()), atof(woff.c_str()), 0, base_index, atoi(nsb.c_str()), "A_MC",
            -99, -99, -99, 1.5 );
    }
    b.setPlottingAxis( "energy_Lin", "X", false, 0.05, 100., "energy [TeV]" );
    c = b.plotEffectiveArea( 1.e3, 5.e5 );
    printCanvas( c, "EffArea3Tel_"+IRFFile, odir);

    c = b.plotEffectiveAreaRatio( 0, 0., 2. );
    printCanvas( c, "EffArea3TelRatio_"+IRFFile, odir); */

}
