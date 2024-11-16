/*
 * Plot sensitivity derived from Crab observations.
 * (many hardwired values)
 */

#include <string>

#include "../../utilitities/parameters.C"
#include "../../utilitities/printutilities.C"

R__LOAD_LIBRARY(/afs/ifh.de/group/cta/scratch/maierg/EVNDISP/EVNDISP-400/GITHUB_Eventdisplay/EventDisplay_v491-al9/lib/libVAnaSum.so)


void plot_sensitivity()
{

    string cut = "moderate2tel";
    string data_dir = "$VERITAS_USER_DATA_DIR/analysis/Results/";
    string anasum_file = "anasum_releaseTestingV6_SZE_0.5deg.combined.root";

    VSensitivityCalculator *b = new VSensitivityCalculator();
    b->setFluxRange_CU(1.e-3, 10.);
    b->setPlotCanvasSize( 600, 400 );
    b->setPlottingStyle(633);
    TCanvas *c = b->plotDifferentialSensitivityvsEnergyFromCrabSpectrum(
            0,
            data_dir + "v491/AP/Crab/V6_" + cut + "/" + anasum_file,
            633, "CU"
            );
    b->setPlottingStyle(633);
    b->plotDifferentialSensitivityvsEnergyFromCrabSpectrum(
            c,
            data_dir + "v491/AP/Crab/V6_" + cut + "/" + anasum_file,
            633, "CU"
            );

    b->setPlottingStyle(12);
    b->plotDifferentialSensitivityvsEnergyFromCrabSpectrum(
            c,
            data_dir + "v490/AP/Crab/V6_" + cut + "/" + anasum_file,
            12, "CU"
            );

    TFile *fCTA = new TFile("/lustre/fs22/group/cta/users/maierg/analysis/AnalysisData/prod6-LaPalma-20deg-dark-sq230-LL/Phys-g20240826/DESY.g20240826.V3.ID0NIM3LST3MST3SST3SCMST3.prod6-LaPalma-20deg-dark-sq230-LL.N.Am-4LSTs09MSTs.180000s.root");
    TH1F *hCTA = (TH1F*)fCTA->Get("DiffSensCU");
    hCTA->SetLineStyle(2);
    hCTA->SetLineColor(418);
    hCTA->Draw("hist same");

    printCanvas(c, "/SensitivityCU_" + cut, "./" );
}
