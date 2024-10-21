//void makeSpec(string FileName, string OutFile){

void makeSpec(string Idir, string Odir, string Source, string Cut, float fit_emin, float fit_emax, float eref){

R__LOAD_LIBRARY($EVNDISPSYS/lib/libVAnaSum.so);

string FileName = Idir + "anasum.combined.root" ;


cout << "Output dir:" << Odir << endl;

VEnergySpectrum b(FileName);
b.setSignificanceParameters(2.0, 2.0, 0.99, 4);
//b.setSignificanceParameters(-99,-99); // plot all points, even non-significant ones.
b.setEnergyBinning(0.1);
b.setSpectralFitFluxNormalisationEnergy( eref );
TCanvas* c_Spectrum = b.plot();
b.plotEventNumbers(0.02);
b.setSpectralFitRangeLin( fit_emin, fit_emax ); //This value might need slight adjustments, 10 sometimes lead to a d.o.f=9
TF1 *fE = b.fitEnergySpectrum();
b.plotFitValues();
b.printDifferentialFluxes();
b.writeSpectralPointsToCSVFile( Odir + "Eventdisplay_" + Source + "_" + Cut + "_SpecPoints.csv");

string  OutFile = Odir + "Eventdisplay_" + Source + "_" + Cut + "_SpecFit.txt" ;

ofstream Op;
Op.open(OutFile.c_str());

std::cout.precision(5);

Op  << std::scientific << TMath::Abs(fE->GetParameter(1)) << "\t" << fE->GetParError(1) << "\t" ;
Op << fE->GetParameter(0) << "\t" << fE->GetParError(0) << "\n" ;

Op.close();

gSystem->RedirectOutput(0);

}
