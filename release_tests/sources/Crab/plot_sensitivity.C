/*
 * Plot sensitivity derived from Crab observations.
 * (many hardwired values)
 */

#include <string>

#include "../../utilities/parameters.C"
#include "../../utilities/printutilities.C"

void plot_sensitivity( string iVersion = "",
                                           string iComparisonVersion = "" )
{
        if( !loadVAnaSumLibrary() ) return;

        string iCut = "moderate2tel";
    string anasum_file = "anasum_releaseTestingV6_SZE_0.5deg.combined.root";
        string iCurrentAnasum = getCrabAnasumPath( iVersion, iCut, "AP", anasum_file );
        if( iCurrentAnasum.size() == 0 )
        {
                return;
        }

    VSensitivityCalculator *b = new VSensitivityCalculator();
    b->setFluxRange_CU(1.e-3, 10.);
    b->setPlotCanvasSize( 600, 400 );
    b->setPlottingStyle(633);
    TCanvas *c = b->plotDifferentialSensitivityvsEnergyFromCrabSpectrum(
            0,
                        iCurrentAnasum,
            633, "CU"
            );
    b->setPlottingStyle(633);
    b->plotDifferentialSensitivityvsEnergyFromCrabSpectrum(
            c,
                        iCurrentAnasum,
            633, "CU"
            );

        if( iComparisonVersion.size() > 0 )
        {
                string iComparisonAnasum = getCrabAnasumPath( iComparisonVersion, iCut, "AP", anasum_file );
                if( iComparisonAnasum.size() > 0 )
                {
                        b->setPlottingStyle(12);
                        b->plotDifferentialSensitivityvsEnergyFromCrabSpectrum(
                                        c,
                                        iComparisonAnasum,
                                        12, "CU"
                                        );
                }
        }

    TFile *fCTA = new TFile("/lustre/fs22/group/cta/users/maierg/analysis/AnalysisData/prod6-LaPalma-20deg-dark-sq230-LL/Phys-g20240826/DESY.g20240826.V3.ID0NIM3LST3MST3SST3SCMST3.prod6-LaPalma-20deg-dark-sq230-LL.N.Am-4LSTs09MSTs.180000s.root");
    TH1F *hCTA = (TH1F*)fCTA->Get("DiffSensCU");
    hCTA->SetLineStyle(2);
    hCTA->SetLineColor(418);
    hCTA->Draw("hist same");

        printCanvas(c, "/SensitivityCU_" + iCut, "./" );
}
