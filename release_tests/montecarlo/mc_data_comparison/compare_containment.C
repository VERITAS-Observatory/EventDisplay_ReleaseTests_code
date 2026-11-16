// Compare existing compareDatawithMC ROOT files without rerunning event selection.
// Usage:
// root -l -b -q 'compare_containment.C("nominal.root","smear05.root","out.pdf")'

#include "TCanvas.h"
#include "TFile.h"
#include "TF1.h"
#include "TFitResult.h"
#include "TFitResultPtr.h"
#include "TGraphErrors.h"
#include "TH1D.h"
#include "TH2D.h"
#include "TLegend.h"
#include "TLatex.h"
#include "TParameter.h"
#include "TString.h"

#include <cmath>
#include <iostream>
#include <string>
#include <vector>

namespace
{
double containmentRadius( double fraction, double scale1, double scale2 )
{
    double low = 0.;
    double high = 50. * std::max( scale1, scale2 );
    for( int i = 0; i < 100; i++ )
    {
        double mid = 0.5 * ( low + high );
        if( fraction * exp( -mid / scale1 ) + ( 1. - fraction ) * exp( -mid / scale2 ) > 0.32 ) low = mid;
        else high = mid;
    }
    return sqrt( 0.5 * ( low + high ) );
}

bool fitR68( TH1D* h, double& r68, double& error )
{
    if( !h || h->Integral() <= 0. ) return false;
    TF1 model( Form( "containment_model_%s", h->GetName() ), "[0]*([1]/[2]*exp(-x/[2])+(1-[1])/[3]*exp(-x/[3]))", 0., 0.03 );
    model.SetParameters( h->Integral() * h->GetBinWidth( 1 ), 0.7, 0.005, 0.025 );
    model.SetParLimits( 0, 1.e-9, h->Integral() * h->GetBinWidth( 1 ) * 100. );
    model.SetParLimits( 1, 0.01, 0.99 );
    model.SetParLimits( 2, 0.00005, 0.3 );
    model.SetParLimits( 3, 0.00005, 0.3 );
    TFitResultPtr fit = h->Fit( &model, "QSNRI" );
    if( int( fit ) || !fit.Get() || fit->CovMatrixStatus() != 3 || fit->Ndf() <= 0 || fit->Chi2() / fit->Ndf() > 5. ) return false;
    double p[3] = {fit->Parameter( 1 ), fit->Parameter( 2 ), fit->Parameter( 3 )};
    if( p[0] < 0.02 || p[0] > 0.98 || p[1] < 0.0001 || p[2] < 0.0001 || p[1] > 0.29 || p[2] > 0.29 ) return false;
    r68 = containmentRadius( p[0], p[1], p[2] );
    if( r68 * r68 >= 0.03 ) return false;
    double grad[3];
    for( int i = 0; i < 3; i++ )
    {
        double step = p[i] * 1.e-4, saved = p[i];
        p[i] = saved + step; double up = containmentRadius( p[0], p[1], p[2] );
        p[i] = saved - step; double down = containmentRadius( p[0], p[1], p[2] );
        p[i] = saved; grad[i] = ( up - down ) / ( 2. * step );
    }
    double variance = 0.;
    for( int i = 0; i < 3; i++ ) for( int j = 0; j < 3; j++ ) variance += grad[i] * fit->CovMatrix( i + 1, j + 1 ) * grad[j];
    if( !std::isfinite( variance ) || variance <= 0. ) return false;
    error = sqrt( variance );
    return error < 0.5 * r68;
}

struct Sample
{
    std::string label;
    TFile* file;
    TGraphErrors* mc;
    TGraphErrors* data;
};

bool fillGraph( TH2D* h, TGraphErrors* graph, const char* label )
{
    if( !h ) return false;
    for( int bin = 1; bin <= h->GetNbinsX(); bin++ )
    {
        TH1D* projection = h->ProjectionY( Form( "proj_%s_%d", label, bin ), bin, bin );
        double r = 0., e = 0.;
        if( fitR68( projection, r, e ) )
        {
            int point = graph->GetN();
            graph->SetPoint( point, h->GetXaxis()->GetBinCenter( bin ), r );
            graph->SetPointError( point, 0., e );
        }
        else std::cout << label << ": omitted energy bin " << bin << " (fit failed quality checks)\n";
        delete projection;
    }
    return true;
}
}

void compare_containment( const char* nominalPath, const char* smearPath, const char* outputPdf = "containment_nominal_vs_smear05.pdf" )
{
    Sample samples[2] = {{"Nominal MC", TFile::Open( nominalPath ), 0, 0}, {"Smear05 MC", TFile::Open( smearPath ), 0, 0}};
    for( Sample& s : samples )
    {
        if( !s.file || s.file->IsZombie() ) { std::cerr << "Cannot open comparison ROOT file for " << s.label << "\n"; return; }
        TH2D* mc = dynamic_cast<TH2D*>( s.file->Get( "htheta2Erec_SIMS" ) );
        TH2D* data = dynamic_cast<TH2D*>( s.file->Get( "htheta2Erec_DIFF" ) );
        TParameter<double>* cut = dynamic_cast<TParameter<double>*>( s.file->Get( "angularTheta2Cut" ) );
        if( !mc || !data || !cut || cut->GetVal() < 0.03 || cut->GetVal() > 0.035 )
        { std::cerr << "Missing histograms or unsupported theta2 cut in " << s.file->GetName() << "\n"; return; }
        s.mc = new TGraphErrors(); s.data = new TGraphErrors();
        fillGraph( mc, s.mc, Form( "%s MC", s.label.c_str() ) );
        fillGraph( data, s.data, Form( "%s excess", s.label.c_str() ) );
    }

    samples[0].mc->SetMarkerStyle( 20 ); samples[0].mc->SetMarkerColor( kRed + 1 ); samples[0].mc->SetLineColor( kRed + 1 );
    samples[1].mc->SetMarkerStyle( 21 ); samples[1].mc->SetMarkerColor( kBlue + 1 ); samples[1].mc->SetLineColor( kBlue + 1 );
    samples[0].data->SetMarkerStyle( 24 ); samples[0].data->SetMarkerColor( kRed + 1 ); samples[0].data->SetLineColor( kRed + 1 );
    samples[1].data->SetMarkerStyle( 25 ); samples[1].data->SetMarkerColor( kBlue + 1 ); samples[1].data->SetLineColor( kBlue + 1 );

    TCanvas canvas( "containment_comparison", "MC containment comparison", 900, 650 );
    canvas.SetGrid(); canvas.SetBottomMargin( 0.19 );
    TH1F* frame = canvas.DrawFrame( -2., 0., 1.5, 0.4 );
    frame->SetTitle( "68% angular containment versus reconstructed energy;log_{10}(E_{rec}/TeV);r_{68} [deg]" );
    samples[0].mc->Draw( "P SAME" ); samples[1].mc->Draw( "P SAME" );
    // Both data histograms should be identical. Draw one data series once so
    // the markers do not fully obscure each other.
    samples[0].data->Draw( "P SAME" );
    TLegend legend( 0.58, 0.68, 0.88, 0.88 );
    legend.AddEntry( samples[0].mc, "Nominal XGB MC", "p" );
    legend.AddEntry( samples[1].mc, "Smear05 XGB MC", "p" );
    legend.AddEntry( samples[0].data, "Crab ON - #alpha OFF (same data)", "p" );
    legend.Draw();
    TLatex note; note.SetNDC(); note.SetTextSize( 0.026 );
    note.DrawLatex( 0.12, 0.09, "Two-Gaussian extrapolation from #theta^{2} < 0.03 deg^{2}; statistical fit errors; exploratory" );
    canvas.SaveAs( outputPdf );
}
