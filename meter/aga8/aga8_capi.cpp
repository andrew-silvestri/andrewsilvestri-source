// Plain-C entry points over the NIST AGA8 reference code in this folder
// (github.com/usnistgov/AGA8, public domain under 17 USC 105; LICENSE beside it).
// Units: T K, P kPa, D mol/L, x = 21 mole fractions in NIST order
// (GERG2008.cpp: 1 methane ... 14 n-decane, 15 hydrogen, 16 oxygen, 17 CO,
// 18 water, 19 H2S, 20 helium, 21 argon). Built by meter/build_aga8.py.
#include <vector>
#include <string>
#include "GERG2008.h"
#include "Detail.h"
#include "Gross.h"
static std::vector<double> vec(const double *x){ std::vector<double> v(22,0.0); for(int i=0;i<21;i++) v[i+1]=x[i]; return v; }
#ifdef _WIN32
#define API extern "C" __declspec(dllexport)
#else
#define API extern "C"
#endif
API void setup(){ SetupGERG(); SetupDetail(); SetupGross(); }
API void p_gerg(double T,double D,const double*x,double*P,double*Z){ PressureGERG(T,D,vec(x),*P,*Z); }
API void p_detail(double T,double D,const double*x,double*P,double*Z){ std::vector<double> v=vec(x); PressureDetail(T,D,v,*P,*Z); }
API int d_gerg(double T,double P,const double*x,double*D){ int ierr=0; std::string h; DensityGERG(0,T,P,vec(x),*D,ierr,h); return ierr; }
API int d_detail(double T,double P,const double*x,double*D){ int ierr=0; std::string h; DensityDetail(T,P,vec(x),*D,ierr,h); return ierr; }
API void mm_gerg(const double*x,double*M){ MolarMassGERG(vec(x),*M); }
API void mm_detail(const double*x,double*M){ MolarMassDetail(vec(x),*M); }
// Isentropic exponent kappa from GERG-2008 at (T, D).
API void kappa_gerg(double T,double D,const double*x,double*K){
    double P,Z,dPdD,d2PdD2,d2PdTD,dPdT,U,H,S,Cv,Cp,W,G,JT,A;
    PropertiesGERG(T,D,vec(x),P,Z,dPdD,d2PdD2,d2PdTD,dPdT,U,H,S,Cv,Cp,W,G,JT,*K,A); }
// Molar ideal gross heating value of the mixture, kJ/mol at 298.15 K (Gross.cpp GrossHv).
API void hv_gross(const double*x,double*HN){ std::vector<double> g; double HCH; GrossHv(vec(x),g,*HN,HCH); }
