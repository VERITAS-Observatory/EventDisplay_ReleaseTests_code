/*
 * plot radial acceptances for all epochs
 *
 * root -l -q -b 'plot_radialAcceptances.C("v485")'
 *
 *
 */

#include <string>
#include <vector>

void printCanvas( TCanvas *c, string iName, string iSuffix = ".pdf", string oDir = "./" )
{
    if( c )
    {
        string iPrintName = iName + iSuffix;
        c->Print( (oDir + "/"+iPrintName).c_str() );
    }
}

void plot( string version,
           string oDir,
           string oName,
           string radName )
{
    string iDataDir = "$VERITAS_EVNDISP_AUX_DIR/RadialAcceptances/";

    VPlotRadialAcceptance a( iDataDir + radName );
    TCanvas *c = a.plotRadialAcceptance();

    printCanvas( c, oName, ".pdf", oDir );
}

void plot_radialAcceptances( string version )
{
    gSystem->Load( "$EVNDISPSYS/lib/libVAnaSum.so" );
    cout << "Plotting radial acceptances" << endl;

    string oDir = "../../" + version + "/radialAcceptances/";
    gSystem->mkdir( oDir.c_str(), true );

    vector< string > fEpoch;
*   fEpoch.push_back( "V4" );
    fEpoch.push_back( "V5" ); 
    fEpoch.push_back( "V6" );

    vector< string > telCombo;
    telCombo.push_back( "T1234" );
    telCombo.push_back( "T123" );
    telCombo.push_back( "T124" );
    telCombo.push_back( "T134" );
    telCombo.push_back( "T234" );

    vector< string > fCuts;
    fCuts.push_back( "NTel2-Moderate-TMVA-BDT" );
    fCuts.push_back( "NTel2-Soft-TMVA-BDT" );
    fCuts.push_back( "NTel2-Hard-TMVA-BDT" );
    fCuts.push_back( "NTel3-Hard-TMVA-BDT" );
    fCuts.push_back( "NTel2-SuperSoft" );
    fCuts.push_back( "NTel2-Soft" );
    fCuts.push_back( "NTel2-Extended050-Moderate-TMVA-BDT" );
    fCuts.push_back( "NTel2-Extended025-Moderate-TMVA-BDT" );

    for( unsigned int e = 0; e < fEpoch.size(); e++ )
    {
        for( unsigned int t = 0; t < telCombo.size(); t++ )
        {
            for( unsigned int c = 0; c < fCuts.size(); c++ )
            {
                string radName = "radialAcceptance-" + version + "-auxv01-";
                if( fEpoch[e] == "V6" )
                {
                    if( version.find( "v483" ) != string::npos )
                    {
                        radName += "CARE_June1702-Cut-";
                    }
                    else
                    {
                        radName += "CARE_June2020-Cut-";
                    }
                }
                else
                {
                    radName += "GRISU-Cut-";
                }
                radName += fCuts[c];
                radName += "-GEO-";
                radName += fEpoch[e] + "-";
                radName += telCombo[t] + ".root";
                cout << radName << endl;

                string oName = "radialAcceptance-" + fCuts[c] + "-" + fEpoch[e] + "-";
                oName += telCombo[t];
                plot( version, oDir, oName, radName );
             }
        }
    }
}
