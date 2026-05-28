/*
 * Plot sensitivity for different cuts derived from Crab observations.
 * (many hardwired values)
 *
 * Significant requirements: 3 sigma and at least event events
 * (different to CTAO curves)
 */

#include <sstream>
#include <string>
#include <vector>

#include "../../utilities/parameters.C"
#include "../../utilities/printutilities.C"

void plot_sensitivity_compare_one_cuts( double iObsTime = 20.,
                                        double iMinSigma = 3.,
                                        int iMinEvents = 5,
                                        string iVersion = "",
                                        string iReferenceVersion = "" )
{
    if( !loadVAnaSumLibrary() ) return;

    double dE_log10 = 0.2;
    vector< string > cut;
    cut.push_back( "moderate2tel" );
    cut.push_back( "soft2tel" );
    cut.push_back( "hard2tel" );
    cut.push_back( "hard3tel" );
    string anasum_file = "anasum_releaseTestingV6_SZE_0.5deg.combined.root";

    vector< TGraphAsymmErrors* > sens_graph;

    VSensitivityCalculator *b = new VSensitivityCalculator();
    b->setSignificanceParameter( iMinSigma, iMinEvents, iObsTime);
    b->setFluxRange_CU(1.e-3, 10.);
    b->setPlotCanvasSize( 600, 400 );
    TCanvas *c = 0;
    for( unsigned int i = 0; i < cut.size(); i++ )
    {
        string iCurrentAnasum = getCrabAnasumPath( iVersion, cut[i], "AP", anasum_file );
        if( iCurrentAnasum.size() == 0 ) return;

        int color = VUtilities::color_id(i);
        b->setPlottingStyle(color, 1, 1., 20., 0.75);
        if( i == 0 )
        {
            c = b->plotDifferentialSensitivityvsEnergyFromCrabSpectrum(
                    0,
                    iCurrentAnasum,
                    color, "CU", dE_log10
                    );
        }
        b->plotDifferentialSensitivityvsEnergyFromCrabSpectrum(
                c,
                iCurrentAnasum,
                color, "CU", dE_log10
                );
        sens_graph.push_back( b->getSensitivityGraph() );
    }
    if( iReferenceVersion.size() > 0 )
    {
        string iReferenceAnasum = getCrabAnasumPath( iReferenceVersion, "supersoftNN2tel", "NN", anasum_file );
        if( iReferenceAnasum.size() > 0 )
        {
            b->setPlottingStyle(VUtilities::color_id(cut.size()), 1, 1., 20., 0.75);
            b->plotDifferentialSensitivityvsEnergyFromCrabSpectrum(
                c,
                iReferenceAnasum,
                VUtilities::color_id(cut.size()), "CU", dE_log10
                );
            sens_graph.push_back( b->getSensitivityGraph() );
        }
    }

    TFile *fCTA = new TFile("/lustre/fs22/group/cta/users/maierg/analysis/AnalysisData/prod6-LaPalma-20deg-dark-sq230-LL/Phys-g20240826/DESY.g20240826.V3.ID0NIM3LST3MST3SST3SCMST3.prod6-LaPalma-20deg-dark-sq230-LL.N.Am-4LSTs09MSTs.180000s.root");
    TH1F *hCTA = (TH1F*)fCTA->Get("DiffSensCU");
    hCTA->SetLineStyle(2);
    hCTA->SetLineColor(418);
    hCTA->Draw("hist same");

    stringstream print_name;
    print_name << "/SensitivityCU_" << (int)iObsTime << "h" << (int)iMinSigma << "Sigma" << iMinEvents << "Events";
    printCanvas(c, print_name.str(), "./" );

 // relative sensitivity
    double energy_min = 0.003;
    double energy_max = 200.;
    TCanvas *cRel = new TCanvas( "relative_sensitivity", "", 10, 10, 600, 400 );
    cRel->SetGridx( 0 );
    cRel->SetGridy( 0 );
    cRel->SetLeftMargin( 0.10 );
    TH1D *h = new TH1D( "hnullSens", "", 10, -1.9, 2.1 );
    h->SetStats( 0 );
    h->SetXTitle( "log_{10} energy [TeV]" );
    h->SetYTitle( "Relative sensitivity (to moderate cuts)" );
    h->SetMinimum( 0. );
    h->SetMaximum( 2. );
    b->plot_nullHistogram( cRel, h, true, false, 1.7, energy_min, energy_max );
    cRel->SetLogy( 0 );
    TLine *iL = new TLine( -1.9, 1., 2.1, 1. );
    iL->SetLineStyle( 2 );
    iL->Draw();
    for( unsigned int i = 1; i < sens_graph.size(); i++ )
    {
        if( !sens_graph[i] ) continue;

        TGraphAsymmErrors *g_rel = new TGraphAsymmErrors(1);
        b->divide(g_rel, sens_graph[i], sens_graph[0] );
        g_rel->SetLineColor( sens_graph[i]->GetLineColor() );
        g_rel->SetMarkerColor( sens_graph[i]->GetMarkerColor() );
        g_rel->SetMarkerStyle( sens_graph[i]->GetMarkerStyle() );
        g_rel->Draw("p");
    }
    printCanvas(cRel, print_name.str() + "Rel", "./" );
}

void plot_sensitivity_compare_cuts( string iVersion = "",
                                    string iReferenceVersion = "" )
{
    if( iVersion.size() == 0 )
    {
        const char* iVersionEnv = gSystem->Getenv( "VERITAS_EVNDISP_VERSION" );
        if( iVersionEnv ) iVersion = iVersionEnv;
    }

    vector< double > obs_time;
    obs_time.push_back( 100. );
    obs_time.push_back( 50. );
    obs_time.push_back( 20. );
    obs_time.push_back( 10. );
    obs_time.push_back( 5. );

    for( unsigned int i = 0; i < obs_time.size(); i++ )
    {
        plot_sensitivity_compare_one_cuts( obs_time[i], 3., 5, iVersion, iReferenceVersion );
        plot_sensitivity_compare_one_cuts( obs_time[i], 5., 10, iVersion, iReferenceVersion );
    }
}
