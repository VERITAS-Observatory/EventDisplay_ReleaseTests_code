/*
 * compare effective areas between two epochs
 *
 *
 *  root -l -q -b 'plot_effectiveAreas.C'
 *
 */

#include <string>
#include <vector>

void printCanvas( TCanvas *c, string iName )
{
    string iSuffix = ".pdf";
    if( c )
    {
        string iPrintName = iName + iSuffix;
        c->Print( ("figures/"+iPrintName).c_str() );
    }
}


void plot_effectiveAreas( string Epoch1 = "2012_2013a", string Epoch2 = "2019_2020", string iCut = "Soft", bool iRedHV = false )
{
        int i_load = gSystem->Load( "$EVNDISPSYS/lib/libVAnaSum.so" );
        if( i_load < 0 )
        {
            cout << "Error loading shared library" << endl;
            return;
        }

        string iEffAreaDir = "$VERITAS_EVNDISP_AUX_DIR/EffectiveAreas/";

        string Epoch1_file = "effArea-v483-auxv01-CARE_RedHV-Cut-NTel2-PointSource-" + iCut + "-TMVA-BDT-GEO-V6_";
        Epoch1_file += Epoch1 + "-ATM61-T1234.root";
        string Epoch2_file = "effArea-v483-auxv01-CARE_RedHV-Cut-NTel2-PointSource-" + iCut + "-TMVA-BDT-GEO-V6_";
        Epoch2_file += Epoch2 + "-ATM61-T1234.root";

        string v480_file = "/lustre/fs19/group/cta/VERITAS//analysis/AnalysisData-VTS-v470/EffectiveAreas/";
        v480_file += "effArea-v470-auxv01-CARE-Cut-NTel2-PointSource-Soft-GEO-V6-ATM21-redHV-T1234.root";

        VPlotInstrumentResponseFunction a;
        a.addInstrumentResponseData( (iEffAreaDir+Epoch1_file).c_str(), 20., 0.5, 0, 1.6, 150);
        a.addInstrumentResponseData( (iEffAreaDir+Epoch2_file).c_str(), 20., 0.5, 0, 1.6, 150);
        //a.addInstrumentResponseData( v480_file.c_str(), 20., 0.5, 0, 1.5, 200);
        //a.addInstrumentResponseData("/lustre/fs19/group/cta/users/maierg/VERITAS/analysis/Results/v483/CARE_RedHV/V6_2012_2013a_ATM61_gamma/EffectiveAreas_Cut-NTel2-PointSource-Soft/EffArea-CARE_RedHV-V6_2012_2013a-ID0-Ze20deg-0.5wob-150-Cut-NTel2-PointSource-Soft.root", 20., 0.5, 0, 1.6, 150);

        TCanvas *cEff = (TCanvas*)a.plotEffectiveArea( 4.e5 );
        printCanvas( cEff, "effArea_" + iCut + "_" + Epoch1 + "-" + Epoch2 );
        TCanvas *cEffRatio = (TCanvas*)a.plotEffectiveAreaRatio();
        printCanvas( cEffRatio, "effAreaRatio_" + iCut + "_" + Epoch1 + "-" + Epoch2 );
}
