/*
 * run parameter class to be used for most
 * of the release tests
 *
 * Test: root -l -q -b 'parameters.C()'
 */

#include <algorithm>
#include <fstream>
#include <iostream>
#include <set>
#include <sstream>
#include <string>
#include <vector>

/*
 * Helper for ROOT macros: load libVAnaSum from environment.
 * Search order:
 *   1) $VERITAS_VANASUM_LIBRARY
 *   2) $EVNDISP/lib/libVAnaSum.so
 *   3) ROOT library path via "libVAnaSum.so"
 */
bool loadVAnaSumLibrary()
{
    static bool iLibraryLoaded = false;
    if( iLibraryLoaded )
    {
        return true;
    }

    string iLibPath;
    const char* iEnvLib = gSystem->Getenv( "VERITAS_VANASUM_LIBRARY" );
    if( iEnvLib )
    {
        iLibPath = iEnvLib;
    }
    if( iLibPath.size() == 0 )
    {
        const char* iEvndisp = gSystem->Getenv( "EVNDISP" );
        if( iEvndisp )
        {
            iLibPath = string( iEvndisp ) + "/lib/libVAnaSum.so";
        }
    }

    if( iLibPath.size() > 0 && !gSystem->AccessPathName( iLibPath.c_str() ) )
    {
        if( gSystem->Load( iLibPath.c_str() ) >= 0 )
        {
            iLibraryLoaded = true;
            return true;
        }
    }

    if( gSystem->Load( "libVAnaSum.so" ) >= 0 )
    {
        iLibraryLoaded = true;
        return true;
    }

    cout << "Error: unable to load libVAnaSum.so. "
         << "Set VERITAS_VANASUM_LIBRARY or EVNDISP." << endl;
    return false;
}

/*
 * Helper for release-test Crab products in the standard results tree.
 */
string getCrabAnasumPath( string iVersion,
                          string iCut,
                          string iAnalysisType = "AP",
                          string iAnasumFile = "anasum_releaseTestingV6_SZE_0.5deg.combined.root" )
{
    if( iVersion.size() == 0 )
    {
        const char* iVersionEnv = gSystem->Getenv( "VERITAS_EVNDISP_VERSION" );
        if( iVersionEnv )
        {
            iVersion = iVersionEnv;
        }
    }
    if( iVersion.size() == 0 )
    {
        cout << "Error: release version not set (pass iVersion or set VERITAS_EVNDISP_VERSION)." << endl;
        return "";
    }

    string iDataDir = "$VERITAS_USER_DATA_DIR/analysis/Results/";
    const char* iDataEnv = gSystem->Getenv( "VERITAS_USER_DATA_DIR" );
    if( iDataEnv )
    {
        iDataDir = string( iDataEnv ) + "/analysis/Results/";
    }

    return iDataDir + iVersion + "/" + iAnalysisType + "/Crab/V6_" + iCut + "/" + iAnasumFile;
}

class RunParameterData
{
    public:

    string fVersion;
    string fSimType;
    string fAnaType;
    string fDirectionType;
    string fEpoch;
    string fAtmosphere;
    string fCut;
    string fCutNameAnasum;
    string fTelCombo;

    RunParameterData( string iVersion = "unset",
                      string iSimType = "unset",
                      string iAnaType = "AP",
                      string iDirectionType = "DISP" );
   ~RunParameterData() {}
    string getEffectiveAreaFileName();
    string getFigureDirectory();
    void print();
};

RunParameterData::RunParameterData( string iVersion,
                                    string iSimType,
                                    string iAnaType,
                                    string iDirectionType )
{
   fVersion = iVersion;
   fSimType = iSimType;
   fAnaType = iAnaType;
   fDirectionType = iDirectionType;
}

void RunParameterData::print()
{
    cout << "\t ATMOSPHERE: " <<  fAtmosphere;
    cout << "\t EPOCH: " << fEpoch;
    cout << "\t TELCOMBO: " << fTelCombo;
    cout << "\t CUT: " << fCut;
    cout << " (" << fCutNameAnasum << ")";
    cout << endl;
}

string RunParameterData::getEffectiveAreaFileName()
{
    string i_name = "effArea-";
    i_name += fVersion + "-auxv01-";
    i_name += fSimType + "-Cut-";
    i_name += fCut + "-";
    i_name += fAnaType + "-";
    if( fDirectionType.size() > 0 && fDirectionType != "unset" )
    {
        i_name += fDirectionType + "-";
    }
    i_name += fEpoch + "-ATM" + fAtmosphere;
    i_name += "-T" + fTelCombo;
    i_name += ".root";

    return i_name;
}

string RunParameterData::RunParameterData::getFigureDirectory()
{
   string i_name;
   i_name += fSimType + "-Cut-";
   i_name += fCut + "-";
   i_name += fAnaType + "-";
   if( fDirectionType.size() > 0 && fDirectionType != "unset" )
   {
        i_name += fDirectionType + "-";
   }
   i_name += fEpoch + "-ATM" + fAtmosphere;
   i_name += "-T" + fTelCombo;
   return i_name;
}


class RunParameters
{
    private:
    bool fIsZombie;

    public:

    string fVersion;
    string fSimType;
    string fAnaType;
    string fDirectionType;
    string fMajorEpoch;
    string fSource;

    // MC related values
    int MC_az;
    double MC_index;
    vector< double > MC_woff;
    vector< double > MC_ze;
    vector< int > MC_nsb;

    vector< RunParameterData* > fData;

    RunParameters( string iRunParameterFile = "" );
   ~RunParameters() {};
    vector< string > getAtmosphereVector( string prefix = "" );
    vector< string > getCutsVector();
    vector< string > getEpochsVector( bool iAddMajorEpoch = false );
    string getDataDir(bool addDirectionType=false);
    bool IsZombie() { return fIsZombie; }
    void print();
    void printMCParameter();
    bool readParameters( string iRunParameterFile );
};

RunParameters::RunParameters( string iRunParameterFile )
{
   fIsZombie = true;

   if( iRunParameterFile.size() > 0 )
   {
       readParameters( iRunParameterFile );
   }
}

bool RunParameters::readParameters( string iRunParameterFile )
{
     // analysis and direction reconstruction are read from environmental variable
     // fAnaType, fDirectionType
     const char* ana_type = gSystem->Getenv( "VERITAS_ANALYSIS_TYPE" );
     if( ana_type )
     {
         string itemp = ana_type;
         if( itemp.size() > 1 )
         {
             fAnaType = itemp.substr( 0, 2 );
             if( itemp.find( "DISP" ) != string::npos )
             {
                 fDirectionType = "DISP";
             }
         }
     }

     // all other parameters are read from parameter file
     ifstream is;
     is.open( iRunParameterFile.c_str(), ifstream::in );
     if( !is )
     {
         cout << "Error reading runparameter file: " << iRunParameterFile << endl;
         return false;
     }
     vector< string > iAtmosphere;
     vector< string > iEpoch;
     vector< string > iCut;
     vector< string > iTelCombo;
     vector< string > iCutNameAnasum;
     string is_line;
     string temp1;
     string temp2;
     while( getline( is, is_line ) )
     {
         if( is_line.size() > 0 && is_line.substr( 0, 1 ) == "*" )
         {
             istringstream is_stream( is_line );
             is_stream >> temp1;
             is_stream >> temp1;
             is_stream >> temp2;

             if( temp1 == "VERSION" )
             {
                  fVersion = temp2;
             }
             else if( temp1 == "SIMTYPE" )
             {
                  fSimType = temp2;
             }
             else if( temp1 == "MAJOREPOCH" )
             {
                  fMajorEpoch = temp2;
             }
             else if( temp1 == "EPOCH" )
             {
                  iEpoch.push_back( temp2 );
             }
             else if( temp1 == "SOURCE" )
             {
                  fSource = temp2;
             }
             else if( temp1 == "ATMOSPHERE" )
             {
                  iAtmosphere.push_back( temp2 );
             }
             else if( temp1 == "CUT" )
             {
                  iCut.push_back( temp2 );
                  string temp3;
                  if( is_stream >> temp3 )
                  {
                      iCutNameAnasum.push_back( temp3 );
                  }
                  else
                  {
                      iCutNameAnasum.push_back( temp2 );
                  }
             }
             else if( temp1 == "TELCOMBO" )
             {
                  iTelCombo.push_back( temp2 );
             }
             else if( temp1 == "MC_AZ" )
             {
                  MC_az = atoi( temp2.c_str() );
             }
             else if( temp1 == "MC_INDEX" )
             {
                  MC_index = atof( temp2.c_str() );
             }
             else if( temp1 == "MC_WOFF" )
             {
                  MC_woff.push_back( atof( temp2.c_str() ) );
                  while( is_stream >> temp2 )
                  {
                      MC_woff.push_back( atof( temp2.c_str() ) );
                  }
             }
             else if( temp1 == "MC_ZE" )
             {
                  MC_ze.push_back( atof( temp2.c_str() ) );
                  while( is_stream >> temp2 )
                  {
                      MC_ze.push_back( atof( temp2.c_str() ) );
                  }
             }
             else if( temp1 == "MC_NSB" )
             {
                  MC_nsb.push_back( atoi( temp2.c_str() ) );
                  while( is_stream >> temp2 )
                  {
                      MC_nsb.push_back( atoi( temp2.c_str() ) );
                  }
             }
         }
     }
     is.close();
     fIsZombie = false;

     // fill data sets
     for( unsigned int e = 0; e < iEpoch.size(); e++ )
     {
        for( unsigned int a = 0; a < iAtmosphere.size(); a++ )
        {
           for( unsigned int t = 0; t < iTelCombo.size(); t++ )
           {
               for( unsigned int c = 0; c < iCut.size(); c++ )
               {
                   RunParameterData* iData = new RunParameterData( fVersion, fSimType, fAnaType, fDirectionType );
                   iData->fEpoch = iEpoch[e];
                   iData->fAtmosphere = iAtmosphere[a];
                   iData->fTelCombo = iTelCombo[t];
                   iData->fCut = iCut[c];
                   iData->fCutNameAnasum = iCutNameAnasum[c];
                   fData.push_back( iData );
               }
           }
        }
    }

    return true;
}

void RunParameters::print()
{
    cout << "Runparameters: " << endl;
    cout << "\t VERSION: " << fVersion << endl;
    cout << "\t MAJOREPOCH: " << fMajorEpoch << endl;
    cout << "\t SIMTYPE: " << fSimType << endl;
    cout << "\t ANATYPE: " << fAnaType << endl;
    if( fSource.size() > 0 ) cout << "\t SOURCE: " << fSource << endl;
    for( unsigned int i = 0; i < fData.size(); i++ )
    {
        if( fData[i] )
        {
            cout << "Set " << i+1 << endl;
            fData[i]->print();
        }
    }
}

/*
 * return anasum data dir
 * (as assumed in the run scripts)
 */
string RunParameters::getDataDir(bool addDirectionType)
{
    string iDataDir;

    iDataDir = "$VERITAS_USER_DATA_DIR/analysis/Results/"
                    + fVersion + "/" + fAnaType + "/"
                    + fSource;
    if( fDirectionType.size() > 0 && addDirectionType )
    {
        iDataDir += "_" + fDirectionType;
    }
    iDataDir += "/anasum/";

    return iDataDir;
}

void RunParameters::printMCParameter()
{
    cout << "MC Parameters: " << endl;
    cout << "\t AZ " << MC_az << endl;
    cout << "\t INDEX " << MC_index << endl;
    cout << "\t WOFF ";
    for( unsigned int i = 0; i < MC_woff.size(); i++ ) cout << MC_woff[i] << " ";
    cout << endl;
    cout << "\t ZE ";
    for( unsigned int i = 0; i < MC_ze.size(); i++ ) cout << MC_ze[i] << " ";
    cout << endl;
    cout << "\t NSB ";
    for( unsigned int i = 0; i < MC_nsb.size(); i++ ) cout << MC_nsb[i] << " ";
    cout << endl;
}

/*
 * returns a unique vector of all Cuts
 *
 */
vector< string > RunParameters::getCutsVector()
{
    set< string > a;
    for( unsigned int i = 0; i < fData.size(); i++ )
    {
       if( fData[i] )
       {
           a.insert( fData[i]->fCutNameAnasum );
       }
    }
    vector< string > b( a.size() );
    std::copy( a.begin(), a.end(), b.begin() );

    return b;
}

/*
 * returns a unique vector of all Atmospheres
 *
 */
vector< string > RunParameters::getAtmosphereVector( string prefix )
{
    set< string > a;
    for( unsigned int i = 0; i < fData.size(); i++ )
    {
       if( fData[i] )
       {
           a.insert( prefix + fData[i]->fAtmosphere );
       }
    }
    vector< string > b( a.size() );
    std::copy( a.begin(), a.end(), b.begin() );

    return b;
}

/*
 * returns a unique vector of all Epochs
 *
 */
vector< string > RunParameters::getEpochsVector( bool iAddMajorEpoch )
{
    set< string > a;
    for( unsigned int i = 0; i < fData.size(); i++ )
    {
       if( fData[i] )
       {
           a.insert( fData[i]->fEpoch );
           if( iAddMajorEpoch )
           {
               if( fMajorEpoch.find( "redHV" ) != string::npos )
               {
                  a.insert( "V6" );
               }
               else
               {
                  a.insert( fMajorEpoch );
               }
           }
       }
    }
    vector< string > b( a.size() );
    std::copy( a.begin(), a.end(), b.begin() );

    return b;
}

/*
 *  test
*/
void parameters( string runparameterfile = "test.runparameter.dat" )
{
   RunParameters *fPar = new RunParameters( runparameterfile );
   if( fPar->IsZombie() ) return;
   fPar->print();
   cout << endl;
   fPar->printMCParameter();

   vector< string > a = fPar->getAtmosphereVector();
   cout << a.size() << endl;
   for( unsigned int i = 0; i < a.size(); i++ )
   {
      cout << "ATM " << a[i] << endl;
   }
}
