/*
 *  printing functions used in the most of the
 *  plotting macros
 *
 */

/*
 * print a given canvas to a pdf files
 */

#include "TCanvas.h"

#include <string>

void printCanvas( TCanvas *c,
                  string iName,
                  string iFigDir = "figures",
                  string iSuffix = ".pdf" )
{
    if( c )
    {
        string iPrintName = iName + iSuffix;
        c->Print( (iFigDir+"/"+iPrintName).c_str() );
    }
}
