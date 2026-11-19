// Compare counted angular containment from existing compareDatawithMC ROOT files.
// Usage: root -l -b -q 'compare_containment.C("configs/nominal-xgb.conf","configs/ml-smear05-xgb.conf")'

#include "TCanvas.h"
#include "TFile.h"
#include "TGraphErrors.h"
#include "TH1D.h"
#include "TH2D.h"
#include "TLegend.h"
#include "TLatex.h"
#include "TParameter.h"
#include "TString.h"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <filesystem>
#include <map>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace
{
struct Series
{
    std::string type;
    std::string label;
    std::string path;
    TFile* file = nullptr;
    TGraphErrors* graph = nullptr;
};

bool countR68( TH1D* h, double theta2Cut, double& r68, double& error )
{
    if( !h || h->Integral( 1, h->GetNbinsX() ) <= 0. ) return false;
    double total = 0.;
    for( int bin = 1; bin <= h->GetNbinsX(); bin++ )
    {
        double low = h->GetXaxis()->GetBinLowEdge( bin );
        double high = h->GetXaxis()->GetBinUpEdge( bin );
        if( low >= theta2Cut ) continue;
        total += h->GetBinContent( bin ) * ( std::min( high, theta2Cut ) - low ) / ( high - low );
    }
    if( total <= 0. ) return false;

    const double target = 0.68 * total;
    double cumulative = 0.;
    for( int bin = 1; bin <= h->GetNbinsX(); bin++ )
    {
        double low = h->GetXaxis()->GetBinLowEdge( bin );
        double high = h->GetXaxis()->GetBinUpEdge( bin );
        if( low >= theta2Cut ) break;
        high = std::min( high, theta2Cut );
        double content = h->GetBinContent( bin ) * ( high - low ) / ( h->GetXaxis()->GetBinUpEdge( bin ) - low );
        if( content < 0. ) return false;
        if( cumulative + content >= target && content > 0. )
        {
            double theta2 = low + ( target - cumulative ) / content * ( high - low );
            r68 = std::sqrt( theta2 );
            // Approximate within-bin quantile resolution; not a full statistical interval.
            error = ( high - low ) / ( 2. * r68 * std::sqrt( 12. * content ) );
            return std::isfinite( r68 ) && r68 > 0.;
        }
        cumulative += content;
    }
    return false;
}

bool configSettings( const std::filesystem::path& path, std::map<std::string, std::string>& values )
{
    std::ifstream input( path );
    if( !input ) return false;
    std::string line;
    while( std::getline( input, line ) )
    {
        auto begin = line.find_first_not_of( " \t\r" );
        if( begin == std::string::npos || line[begin] == '#' ) continue;
        auto eq = line.find( '=' );
        if( eq == std::string::npos ) return false;
        auto trim = []( std::string s ) {
            auto first = s.find_first_not_of( " \t\r" );
            auto last = s.find_last_not_of( " \t\r" );
            return first == std::string::npos ? std::string() : s.substr( first, last - first + 1 );
        };
        std::string key = trim( line.substr( 0, eq ) ), value = trim( line.substr( eq + 1 ) );
        if( key.empty() || value.empty() || !values.emplace( key, value ).second ) return false;
    }
    if( !values.count( "variant" ) || !values.count( "mscw_directory" ) || !values.count( "reconstruction" ) ) return false;
    if( values["reconstruction"] == "DispBDT" )
    {
        values.erase( "mc_xgb_suffix" ); values.erase( "data_xgb_suffix" );
    }
    else if( values["reconstruction"] == "XGB" )
    {
        if( !values.count( "mc_xgb_suffix" ) ) values["mc_xgb_suffix"] = "xgb_stereo";
        if( !values.count( "data_xgb_suffix" ) ) values["data_xgb_suffix"] = "xgb_stereo";
    }
    else return false;
    return true;
}

bool configSeries( const char* config, const char* results, Series& item )
{
    namespace fs = std::filesystem;
    if( fs::path( config ).extension() == ".root" )
    {
        if( !fs::is_regular_file( config ) ) { std::cerr << "ROOT file not found: " << config << "\n"; return false; }
        item.type = "MC"; item.label = fs::path( config ).parent_path().filename().string(); item.path = config;
        std::cout << "Using " << item.path << "\n";
        return true;
    }
    std::map<std::string, std::string> wanted;
    if( !configSettings( config, wanted ) )
    {
        std::cerr << "Invalid configuration: " << config << "\n";
        return false;
    }
    std::cout << "Searching for " << config << " under " << fs::absolute( results ) << std::endl;
    std::cout << "  variant=" << wanted["variant"] << ", mscw_directory=" << wanted["mscw_directory"]
              << ", reconstruction=" << wanted["reconstruction"] << std::endl;
    std::vector<fs::path> matches;
    std::vector<fs::path> legacy;
    unsigned savedCount = 0, missingRoot = 0;
    std::error_code ec;
    fs::recursive_directory_iterator it( results, ec ), end;
    if( ec ) { std::cerr << "Cannot search " << results << ": " << ec.message() << "\n"; return false; }
    for( ; it != end; it.increment( ec ) )
    {
        if( ec ) { std::cerr << "Search failed: " << ec.message() << "\n"; return false; }
        if( it->is_directory() && it->path().filename() == "tmp" )
        {
            it.disable_recursion_pending();
            continue;
        }
        if( it->path().filename() == "mcdatacomparison.root" && wanted["variant"] == "nominal" && ((wanted["reconstruction"] == "DispBDT" && it->path().string().find( "/DispBDT/" ) != std::string::npos) || (wanted["reconstruction"] == "XGB" && it->path().string().find( "/XGB/MC-" + wanted["mc_xgb_suffix"] + "/DATA-" + wanted["data_xgb_suffix"] + "/" ) != std::string::npos)) && !fs::exists( it->path().parent_path() / "comparison.conf" ) ) legacy.push_back( it->path() );
        if( it->path().filename() != "comparison.conf" ) continue;
        ++savedCount;
        std::map<std::string, std::string> found;
        fs::path root = it->path().parent_path() / "mcdatacomparison.root";
        if( !configSettings( it->path(), found ) )
            std::cerr << "  Invalid saved configuration: " << it->path() << "\n";
        else if( found == wanted )
        {
            if( fs::is_regular_file( root ) ) matches.push_back( root );
            else { ++missingRoot; std::cout << "  Matching configuration has no ROOT output: " << it->path() << "\n"; }
        }
    }
    if( matches.empty() && legacy.size() )
    {
        std::cerr << "  Using legacy nominal result; its MC directory is not recorded.\n";
        matches = legacy;
    }
    if( matches.size() > 1 )
    {
        std::vector<fs::path> atm;
        for( const auto& candidate : matches ) if( candidate.string().find( "/data-ATM61/" ) != std::string::npos ) atm.push_back( candidate );
        if( atm.size() == 1 ) { std::cout << "  Selecting ATM61 runlist.\n"; matches = atm; }
    }
    std::cout << "  Checked " << savedCount << " saved configurations; " << matches.size()
              << " completed matches, " << missingRoot << " without ROOT output.\n";
    if( matches.empty() ) std::cerr << "  Older results without comparison.conf cannot be matched automatically.\n";
    if( matches.size() != 1 )
    {
        std::cerr << config << ": expected one completed result, found " << matches.size() << "\n";
        for( const auto& match : matches ) std::cerr << "  " << match << "\n";
        return false;
    }
    std::cout << "  Selected " << matches[0] << "\n";
    item.type = "MC"; item.label = fs::path( config ).stem().string(); item.path = matches[0].string();
    return true;
}

bool fillGraph( TH2D* h, double theta2Cut, TGraphErrors* graph, const std::string& label )
{
    if( !h ) return false;
    for( int bin = 1; bin <= h->GetNbinsX(); bin++ )
    {
        TH1D* projection = h->ProjectionY( Form( "projection_%s_%d", label.c_str(), bin ), bin, bin );
        double radius = 0., error = 0.;
        if( countR68( projection, theta2Cut, radius, error ) )
        {
            int point = graph->GetN();
            graph->SetPoint( point, h->GetXaxis()->GetBinCenter( bin ), radius );
            graph->SetPointError( point, 0., error );
            std::cout << label << ": energy bin " << bin << " log10(E/TeV)="
                      << h->GetXaxis()->GetBinCenter( bin ) << " r68=" << radius << " +/- " << error << " deg\n";
        }
        else std::cout << label << ": omitted energy bin " << bin << " (invalid cumulative profile or no 68% crossing)\n";
        delete projection;
    }
    return graph->GetN() > 0;
}
}

void compare_containment( const char* firstConfig, const char* secondConfig, const char* results = "../../../../EventDisplay_Release_v492/mc_data_comparison", const char* outputPdf = "containment_comparison.pdf" )
{
    std::vector<Series> series( 2 );
    bool firstFound = configSeries( firstConfig, results, series[0] );
    bool secondFound = configSeries( secondConfig, results, series[1] );
    if( !firstFound || !secondFound ) return;
    if( std::filesystem::path( firstConfig ).extension() == ".root" ) series[0].label = "nominal";
    if( std::filesystem::path( secondConfig ).extension() == ".root" ) series[1].label = "comparison";
    Series data = series[0]; data.type = "DATA"; data.label = "Crab"; series.push_back( data );

    double theta2Cut = -1.;
    double xMin = 1.e9, xMax = -1.e9, yMax = 0.;
    const int colors[] = {kRed + 1, kBlue + 1, kGreen + 2, kMagenta + 1, kOrange + 7, kCyan + 2, kViolet + 1, kBlack};
    const int markers[] = {20, 21, 22, 23, 33, 34, 29, 30};

    for( Series& item : series )
    {
        item.file = TFile::Open( item.path.c_str() );
        if( !item.file || item.file->IsZombie() )
        {
            std::cerr << "Cannot open ROOT file for " << item.label << ": " << item.path << "\n";
            return;
        }
        TParameter<double>* cut = dynamic_cast<TParameter<double>*>( item.file->Get( "angularTheta2Cut" ) );
        if( !cut || cut->GetVal() <= 0. )
        {
            std::cerr << "Missing valid angularTheta2Cut metadata in " << item.path << "\n";
            return;
        }
        if( theta2Cut < 0. ) theta2Cut = cut->GetVal();
        else if( std::abs( cut->GetVal() - theta2Cut ) > 1.e-9 )
        {
            std::cerr << "Input files have different theta2 cuts (" << theta2Cut << " and " << cut->GetVal() << ")\n";
            return;
        }
        const char* histogram = item.type == "MC" ? "htheta2Erec_SIMS" : "htheta2Erec_DIFF";
        TH2D* h = dynamic_cast<TH2D*>( item.file->Get( histogram ) );
        if( !h )
        {
            std::cerr << "Missing " << histogram << " in " << item.path << "\n";
            return;
        }
        item.graph = new TGraphErrors();
        if( !fillGraph( h, theta2Cut, item.graph, item.label ) )
        {
            std::cerr << "No valid containment points for " << item.label << "\n";
            return;
        }
        std::size_t style = (&item - series.data()) % ( sizeof( colors ) / sizeof( colors[0] ) );
        item.graph->SetMarkerStyle( markers[style] );
        item.graph->SetMarkerColor( colors[style] );
        item.graph->SetLineColor( colors[style] );
        for( int point = 0; point < item.graph->GetN(); point++ )
        {
            double x = 0., y = 0.;
            item.graph->GetPoint( point, x, y );
            xMin = std::min( xMin, x ); xMax = std::max( xMax, x ); yMax = std::max( yMax, y );
        }
    }

    double xPadding = std::max( 0.1, 0.05 * ( xMax - xMin ) );
    TCanvas canvas( "containment_comparison", "Angular containment comparison", 1000, 700 );
    canvas.SetGrid(); canvas.SetBottomMargin( 0.18 );
    TH1F* frame = canvas.DrawFrame( xMin - xPadding, 0., xMax + xPadding, yMax * 1.25 );
    frame->SetTitle( "68% angular containment versus reconstructed energy;log_{10}(E_{rec}/TeV);r_{68} [deg]" );
    TLegend legend( 0.58, 0.68, 0.88, 0.88 );
    for( Series& item : series )
    {
        item.graph->Draw( "P SAME" );
        legend.AddEntry( item.graph, item.label.c_str(), "p" );
    }
    legend.Draw();
    TLatex note; note.SetNDC(); note.SetTextSize( 0.026 );
    note.DrawLatex( 0.12, 0.07, Form( "Counted within #theta^{2} < %.4g deg^{2}; no tail extrapolation", theta2Cut ) );
    canvas.SaveAs( outputPdf );
    std::cout << "Comparison output: " << std::filesystem::absolute( outputPdf ).lexically_normal() << std::endl;
}
