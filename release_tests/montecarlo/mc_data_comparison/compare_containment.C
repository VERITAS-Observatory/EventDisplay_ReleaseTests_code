// Compare existing compareDatawithMC ROOT files without rerunning event selection.
// Usage:
// root -l -b -q 'compare_containment.C("nominal.root","smear05.root","out.pdf")'

#include "TCanvas.h"
#include "TFile.h"
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
// Direct 68% quantile from the existing linear theta2 histogram. This does not extrapolate
// beyond the comparison theta2 selection. For ON-OFF excess,
// retain signed bins and reject profiles that are not monotonically cumulative.
bool countR68( TH1D* h, double& r68, double& error )
{
    if( !h || h->Integral( 1, h->GetNbinsX() ) <= 0. ) return false;
    const double theta2Cut = 0.035;
    double total = 0.;
    for( int bin = 1; bin <= h->GetNbinsX(); bin++ )
    {
        double theta2Low = h->GetXaxis()->GetBinLowEdge( bin );
        double theta2High = h->GetXaxis()->GetBinUpEdge( bin );
        if( theta2Low >= theta2Cut ) continue;
        double fractionInside = ( std::min( theta2High, theta2Cut ) - theta2Low ) / ( theta2High - theta2Low );
        total += h->GetBinContent( bin ) * fractionInside;
    }
    if( total <= 0. ) return false;
    double target = 0.68 * total;
    double cumulative = 0.;
    for( int bin = 1; bin <= h->GetNbinsX(); bin++ )
    {
        double theta2Low = h->GetXaxis()->GetBinLowEdge( bin );
        double theta2High = h->GetXaxis()->GetBinUpEdge( bin );
        if( theta2Low >= theta2Cut ) break;
        double usedTheta2High = std::min( theta2High, theta2Cut );
        double fractionInside = ( usedTheta2High - theta2Low ) / ( theta2High - theta2Low );
        double content = h->GetBinContent( bin ) * fractionInside;
        if( content < 0. ) return false;
        double next = cumulative + content;
        if( next >= target && content > 0. )
        {
            double fraction = ( target - cumulative ) / content;
            double theta2 = theta2Low + fraction * ( usedTheta2High - theta2Low );
            r68 = sqrt( theta2 );
            error = ( usedTheta2High - theta2Low ) / ( 2. * sqrt( theta2 ) * sqrt( 12. * content ) );
            return std::isfinite( r68 ) && r68 > 0.;
        }
        cumulative = next;
    }
    return false;
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
        if( countR68( projection, r, e ) )
        {
            int point = graph->GetN();
            graph->SetPoint( point, h->GetXaxis()->GetBinCenter( bin ), r );
            graph->SetPointError( point, 0., e );
            std::cout << label << ": energy bin " << bin << " log10(E/TeV)="
                      << h->GetXaxis()->GetBinCenter( bin ) << " r68=" << r << " +/- " << e << " deg\n";
        }
        else std::cout << label << ": omitted energy bin " << bin << " (invalid signed cumulative profile or no 68% crossing)\n";
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
    samples[0].data->SetMarkerStyle( 25 ); samples[0].data->SetMarkerColor( kRed + 1 ); samples[0].data->SetLineColor( kRed + 1 );
    samples[1].data->SetMarkerStyle( 21 ); samples[1].data->SetMarkerColor( kBlue + 1 ); samples[1].data->SetLineColor( kBlue + 1 );

    TCanvas canvas( "containment_comparison", "MC containment comparison", 900, 650 );
    canvas.SetGrid(); canvas.SetBottomMargin( 0.19 );
    TH1F* frame = canvas.DrawFrame( -2., 0., 1.5, 0.2 );
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
    note.DrawLatex( 0.12, 0.09, "Counted 68% radius within selected #theta^{2} profile; no tail extrapolation" );
    canvas.SaveAs( outputPdf );
}
