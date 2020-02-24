#
#
#

import os
import sys
sys.path.append('..')

from pylab import *
ion()
from numpy import *
from common_parms import *

import region_proc_test as rpt
import image_proc_thread as ipt

#From astro-physic-measurements.pdf pg11
#F_lambda(m=0)=3.7e-9 erg*cm-2*sec-1*angstrom-1  Definition of specific flux for a m=0 star, at the top
#  of the atmosphere at lambda=5500A.  Note 'per wavelength', means for the total flux, one has to integrate
#  F_12=int_(lambda_1)^(lambda_2){F_lambda*d(lambda)}
#
# For the Johnson V band, 4000A-7000A or lambda_center=5500A
#Therefore,
# F_V(m=0)=F_lambda(m=0)*d(lambda)=3.7e-9erg/cm**2/sec/A*3000A
# F_V(m=0)~1.0e-5 erg/cm**2/sec
def f_v_m0(lam1=4000.0,lam2=7000.0):
  #Assuming a constant flux across the band
  return 3.7e-9*(lam2-lam1)
fv0=f_v_m0()  # in erg/cm**2/sec
# For photons E=hc/lambda
#Therefore,
#F(m=0)=1.0e-5[erg/cm**2/sec]*1[photon]/3.6e-12[erg]
#F(m=0)~3.0e6[photons/cm**2/sec]
def ehc_lam(lam=5500.0):
  #lam in angstroms
  lam=lam*1.0/1.0e8
  h=6.63e-27 #erg*sec
  c=3.0e10 #cm/sec
  return h*c/lam  # in ergs/photon

ehv=fv0/ehc_lam() # in photons/cm**2/sec

# The dimm telescope has a diameter of 25.4cm so that
tele_area=pi*(25.4/2.0)**2.0
subaperture=pi*(0.0946*100.0/2.0)**2.0

def zero_mag_flux(tau=0.01,area=tele_area,lam1=4000.0,lam2=7000.0):
  avg_lam=(lam1+lam2)/2.0
  flux=f_v_m0(lam1=lam1,lam2=lam2)  # in erg/cm**2/sec
  e_const=ehc_lam(lam=avg_lam)      # in ergs/photon
  zero_m=flux*area*tau/e_const      # in photons
  #print 'Zero magnitude above the atmosphere, number of photons:  %7.4e Photons' % (zero_m)
  return zero_m  # in photons

def atm_zero(airmass=1.0,tau=0.01,area=subaperture,k_lambda=0.21,lam1=4000.0,lam2=7000.0):
  ## Assuming a value for K(lambda)~0.21 at 5500A at sea level
  ##   The number of photons through an airmass of <airmass> is
  mag0_flux=zero_mag_flux(tau=tau,area=area,lam1=lam1,lam2=lam2)
  mag0_flux_atm=mag0_flux/(10.0**(k_lambda*airmass/2.5))
  return mag0_flux_atm

def numb_atm(magn=0.0,airmass=1.0,tau=0.01,area=subaperture,k_lambda=0.21,lam1=4000.0,lam2=7000.0):
  star=10.0**(-1.0*(magn+k_lambda*airmass)/2.5)
  nphot0=atm_zero(airmass=airmass,tau=tau,area=area,k_lambda=k_lambda,lam1=lam1,lam2=lam2)
  return star*nphot0  # The theoretical number of photons for a mag <magn> star through the atmosphere.

def test_theory(image,mag=0.0,tau=0.01,area=subaperture,proc=None):
  if not proc:  proc=ipt.ImageProcess()
  ret=proc(image,'peaks')
  try:
    av_reduced_flux=(proc.peaks[0].reducd_flux+proc.peaks[1].reducd_flux)/2.0
  except Exception:
    av_reduced_flux=0.0
  try:
    am=image.header['AIRMASS']
  except Exception:
    am=1.0
  try:
    mag=float(os.system('grep \"'+image.header['OBJECT']+'\" ../catalogs/dimm.edb')[-2])
  except Exception:
    try:
      mag=float(os.system('grep \"'+image.header['OBJECT']+'\" ../catalogs/bsc5.edb')[-2])
    except Exception:
      mag=mag
  try:
    tau=image.header['EXPTIME']
  except Exception:
    tau=tau
  theor_counts=numb_atm(magn=mag,airmass=am,tau=tau,area=area)
  return av_reduced_flux,theor_counts,av_reduced_flux/theor_counts

#Using test_theory
def use_th(mon=6,day=4,year=2018,indx=0,fig1=None,fig2=None,fig3=None,infbox=None):
  mymm=ipt.ImageProcess()
  aa=rpt.get_dir_info(mon=mon,day=day,year=year)
  if indx==0: indx=int(raw_input())
  print 'For %d/%d/%d running on index, %d' %(mon,day,year,indx)
  a,b=rpt.return_images(subdir=aa[indx].split('imgdata')[1])
  for each in a:
    a,b,c=test_theory(each,proc=mymm)
    print 'Measured:%10.3f  Theoretical:%10.3f   Ratio:%10.6f' % (a,b,c)
    try: print 'Peak 0 width x,y: %7.3f\",%7.3f\"' % (rpt.pix2angle(mymm.peaks[0].x_width,device_name='GX2750'),\
      rpt.pix2angle(mymm.peaks[0].y_width,device_name='GX2750'))
    except: print 'NNNNNN'
    try: print 'Peak 1 width x,y: %7.3f\",%7.3f\"' % (rpt.pix2angle(mymm.peaks[1].x_width,device_name='GX2750'),\
      rpt.pix2angle(mymm.peaks[1].y_width,device_name='GX2750'))
    except: print 'MMMMMM'
    #rpt.pl_image(each,nrm=rpt.LogNorm,vmin=10,vmax=1500)
    fig1,fig2,fig3,infbox=rpt.pl_one_pk(each,fig1=fig1,fig2=fig2,fig3=fig3,info_box=infbox)
    if raw_input()=='x':  break
  return fig1,fig2,fig3,infbox

def mag_flux(flux2=1.0,tau=0.01,area=tele_area):
  m1=0.0
  f1=zero_mag_flux(tau=tau,area=area)
  m2=2.5*log10(f1/flux2)+m1
  return m2

def flux_ratio(mag1=0.0,mag2=1.0):
  b1_b2=10.0**(0.4*(mag2-mag1))
  return b1_b2

def calc_mag_from_flux(mag1,flux1,flux2):
  mag2=2.5*log10(flux1/flux2)+mag1
  return mag2

def avr_fluxes(image,peak1=-1,peak2=-1,mag=0.0,tau=0.01,area=subaperture,proc=None):
  if not proc:  proc=ipt.ImageProcess()
  ret=proc(image,'peaks')
  #print ret[0],peak1,peak2
  if ret[0]>=2 and peak1==-1 and peak2==-1:
    av_reduced_flux=(proc.peaks[0].reducd_flux+proc.peaks[1].reducd_flux)/2.0
    av_flux=(proc.peaks[0].int_flux_hm+proc.peaks[1].int_flux_hm)/2.0
    av_height=(proc.peaks[0].height+proc.peaks[1].height)/2.0
  elif ret[0]>=1 and peak1!=-1 and peak2==-1:
    av_reduced_flux=proc.peaks[peak1].reducd_flux
    av_flux=proc.peaks[peak1].int_flux_hm
    av_height=proc.peaks[peak1].height
  elif ret[0]>=2 and peak1!=-1 and peak2!=-1:
    av_reduced_flux=(proc.peaks[peak1].reducd_flux+proc.peaks[peak2].reducd_flux)/2.0
    av_flux=(proc.peaks[peak1].int_flux_hm+proc.peaks[peak2].int_flux_hm)/2.0
    av_height=(proc.peaks[peak1].height+proc.peaks[peak2].height)/2.0
  else:
    av_reduced_flux=0.0
    av_flux=0.0
    av_height=0.0
  fluxR=flux_ratio(mag2=mag)
  fluxO=zero_mag_flux(tau=tau,area=area)
  return av_reduced_flux,fluxO,fluxO/fluxR
