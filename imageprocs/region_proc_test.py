
import sys
sys.path.append('..')

from numpy import *
from pylab import *
import threading
import time
import os

import scipy
import scipy.ndimage as ndimage
import scipy.ndimage.filters as filters
from scipy.ndimage.interpolation import shift
from scipy.optimize import leastsq as leastsq

from matplotlib import patches as mtp
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d.axes3d import Axes3D
from mpl_toolkits.axes_grid1 import make_axes_locatable as male
from matplotlib.colors import Normalize,PowerNorm,LogNorm,SymLogNorm
from matplotlib import cm
from os.path import isfile as fexists
from os.path import join as ospjoin
from os.path import isdir
from os import listdir,getcwd
from filecmp import cmp as fcompare

from common_parms import *

from Tkinter import *
import Pmw as pmw
import guis.frame_gui as fg
import guis.imagecanvasgui as icanv

import image_proc_file as ipf
import image_proc_thread as ipt
from image_proc_thread import SIM_IMAGE_NAME,IMG_DIR
from numpy import random

def plot_a_peak(imageclass,index,fig=None,labels=None):
  if not hasattr(imageclass,'peaks'):
    imageclass.find_peaks()
  try:
    peak=imageclass.peaks[index]
    peak.make_fit_data()
  except Exception:
    peak=None
  if not fig:
    fig=figure()
    fig.set_animated(True)
  else:
    fig.clf()
  fig_children=fig.canvas._tkcanvas.winfo_toplevel().children
  fig_child_keys=fig_children.keys()
  for each in fig_child_keys:
    if fig_children[each].widgetName=='label': fig_children[each].destroy()
  canv=fig.canvas
  splot1=fig.add_subplot(221)
  splot2=fig.add_subplot(222)
  splot3=fig.add_subplot(223)
  splot4=fig.add_subplot(224)
  if peak:
    splot1.imshow(peak.data,origin='lower',interpolation='None')
    #splot1.imshow(peak.data,origin='lower',interpolation='None',cmap='coolwarm')
    xlm,ylm=splot1.get_xlim(),splot1.get_ylim()
    splot1.plot(peak.x_center,peak.y_center,marker='x',ms=5,color='Magenta')
    splot1.set_xlim(xlm)
    splot1.set_ylim(ylm)
    splot1.set_title('Raw Image with Contours')
    splot2.imshow(peak.fitted_data,origin='lower',interpolation='None')
    #splot2.imshow(peak.fitted_data,origin='lower',interpolation='None',cmap='coolwarm')
    splot2.set_title('Fitted Data')
    cnt1=splot1.contour(peak.data,origin='lower',colors='Black')
    #splot3.set_aspect('equal')
    splot3.imshow(imageclass.data,origin='lower',interpolation='None')
    #splot3.imshow(imageclass.data,origin='lower',interpolation='None',cmap='coolwarm')
    splot3.plot(peak.abs_x_center,peak.abs_y_center,marker='x',ms=5,color='Magenta')
    splot3.set_xlim(peak.abs_x_center-peak.data.shape[1]/2,peak.abs_x_center+peak.data.shape[1]/2)
    splot3.set_ylim(peak.abs_y_center-peak.data.shape[0]/2,peak.abs_y_center+peak.data.shape[0]/2)
    splot3.set_title('Raw Image Absolute Coords')
  # cnt2=splot4.contour(peak.fitted_data,origin='lower')
  # splot4.set_aspect('equal')
  # splot4.plot(peak.x_center,peak.y_center,marker='x',ms=5,color='Magenta')
  # splot4.set_title('Fitted Data Contours')
    splot4.plot(peak.data[int(peak.x_center),:],color='Blue')
    splot4.plot(peak.fitted_data[int(peak.x_center),:],color='DarkBlue')
    splot4.plot(peak.data[:,int(peak.y_center)],color='Violet')
    splot4.plot(peak.fitted_data[:,int(peak.y_center)],color='DarkViolet')
    splot4.set_title('Profile in X and Y')
    splot4.grid(True)
  # #cnt1.levels are the levels
  # clabel(cnt1)  #cnt1.collections is a list of contours
  # clabel(cnt2)  #cnt1.collections[i].get_paths() returns the paths of each contour
    if labels:
      qq,ww,ee,rr,ss=labels
      qq.configure(text='Peak Data Max:%10.2f'%(peak.data.max()))
      ww.configure(text='Peak Data Max-Background:%10.2f'%(peak.data.max()-imageclass.background))
      ee.configure(text='Fit Data Max:%10.2f'%(peak.fitted_data.max()))
      rr.configure(text='Fit Data Max-Background:%10.2f'%(peak.fitted_data.max()-imageclass.background))
      ss.configure(text='Background:%10.2f'%(imageclass.background))
    else:
      qq=Label(canv._tkcanvas.winfo_toplevel(),text='Peak Data Max:%10.2f'%(peak.data.max()))
      ww=Label(canv._tkcanvas.winfo_toplevel(),text='Peak Data Max-Background:%10.2f'%\
        (peak.data.max()-imageclass.background))
      ee=Label(canv._tkcanvas.winfo_toplevel(),text='Fit Data Max:%10.2f'%(peak.fitted_data.max()))
      rr=Label(canv._tkcanvas.winfo_toplevel(),text='Fit Data Max-Background:%10.2f'%\
        (peak.fitted_data.max()-imageclass.background))
      ss=Label(canv._tkcanvas.winfo_toplevel(),text='Background:%10.2f'%(imageclass.background))
      qq.pack();ww.pack();ee.pack();rr.pack();ss.pack()
    canv.draw()
    return fig,canv,[splot1,splot2,splot3,splot4],[qq,ww,ee,rr,ss]
  return fig,canv,[splot1,splot2,splot3,splot4],[]

def label_peaks(curraxis,imageclass,color='White',big=True):
  i=0
  for each in imageclass.centers:
    x,y=each[0],each[1]
    xlm,ylm=curraxis.get_xlim(),curraxis.get_ylim()
    if big: 
      curraxis.text(x,y,str(i),color=color,fontsize=20)
      curraxis.plot(x,y,marker='x',ms=20,color=color)
    else: 
      curraxis.text(x,y,str(i),color=color,fontsize=14)
      curraxis.plot(x,y,marker='x',ms=2,color=color)
    curraxis.set_xlim(xlm);curraxis.set_ylim(ylm)
    i+=1
  return
def label_points(curraxis,pnt_array,color='White',big=True):
  i=0
  if pnt_array.shape==(2,):
    x,y=pnt_array[0],pnt_array[1]
    xlm,ylm=curraxis.get_xlim(),curraxis.get_ylim()
    if big: 
      curraxis.text(x,y,str(i),color=color,fontsize=20)
      curraxis.plot(x,y,marker='x',ms=20,color=color)
    else: 
      curraxis.text(x,y,str(i),color=color,fontsize=14)
      curraxis.plot(x,y,marker='x',ms=2,color=color)
    curraxis.set_xlim(xlm);curraxis.set_ylim(ylm)
  else:
    for each in pnt_array:
      x,y=each[0],each[1]
      xlm,ylm=curraxis.get_xlim(),curraxis.get_ylim()
      if big: 
        curraxis.text(x,y,str(i),color=color,fontsize=20)
        curraxis.plot(x,y,marker='x',ms=20,color=color)
      else: 
        curraxis.text(x,y,str(i),color=color,fontsize=14)
        curraxis.plot(x,y,marker='x',ms=2,color=color)
      curraxis.set_xlim(xlm);curraxis.set_ylim(ylm)
      i+=1
  return

def pl_image(image,intp='None',cmap='gray',nrm=Normalize,vmin=1.0,vmax=50000.0):
  mm=imshow(image.data,origin='lower',interpolation=intp)
  mm.set_cmap(cmap)
  ax=mm.get_figure().get_axes()[0]
  # A good example is pl_image(image,cmap='coolwarm',vmin=100.0,vmax=1000.0)
  #cmap='coolwarm','gray','magma','hot','cool','ocean','gnuplot','spectral', etc
  mm.set_norm(nrm(vmin=vmin,vmax=vmax))
  #mm.set_clim(vmin=vmin,vmax=vmax)
  hdr=image.header
  ttl_string='Object: %s, from %s %s, at an airmass of %7.4f using the %s camera\n' %\
    (hdr['OBJECT'],hdr['DATE-OBS'],hdr['TIME-OBS'],hdr['AIRMASS'],hdr['INSTRUME'])
  ttl_string='%san exposure time of  %7.3fsec, Az: %s, Elv: %s, RA: %s, DEC: %s' %\
    (ttl_string,hdr['EXPTIME'],hdr['AZ'],hdr['ELV'],hdr['RA'],hdr['DEC'])
  ax.set_title(ttl_string,size=16)
  return mm

def plot_peak_1(imageclass,peak=0,imageprocclass=None,fig=None):
  if not fig:
    fig=figure()
    fig.set_animated(True)
  else:
    fig.clf()
  fig.clf()
  if not imageprocclass:  imageprocclass=ipt.ImageProcess()
  ret=imageprocclass(imageclass,'pix2peaks')
  splot=fig.add_subplot(111)
  mm=splot.imshow(imageclass.peaks[peak].data,origin='lower',interpolation='None')
  mymm=gca()
  dvd=male(mymm)
  mmx=dvd.append_axes('top',size=1.2,pad=0.1,sharex=mymm)
  mmy=dvd.append_axes('right',size=1.2,pad=0.1,sharey=mymm)
  xcnt,ycnt=imageclass.peaks[peak].x_center,imageclass.peaks[peak].y_center
  xrng,yrng=imageclass.peaks[peak].data.shape
  mmx.plot(imageclass.peaks[peak].data[ycnt,0:xrng],'k-')
  mmx.grid(True)
  mmx.set_xlim(0,xrng)
  mmy.plot(imageclass.peaks[peak].data[0:yrng,xcnt],arange(0,xrng,1),'k-')
  mmy.grid(True)
  mmy.set_ylim(0,xrng)
  return fig

def plot_rect(curraxis,x,y,boxsize,color='White'):
  if type(boxsize)==tuple:  dx,dy=boxsize[0],boxsize[1]
  else:  dx,dy=boxsize,boxsize
  xlm,ylm=curraxis.get_xlim(),curraxis.get_ylim()
  rect=Rectangle((x-dx/2,y-dy/2),dx,dy,fc='none',ec=color,lw=1)
  curraxis.add_patch(rect,)
  curraxis.plot(x+dx/2,y+dy/2,marker='x',ms=4,color=color)
  curraxis.set_xlim(xlm);curraxis.set_ylim(ylm)
  return

def plot_wire(curraxis,imageclass,peak_index=0,center=zeros((2))):
  data=imageclass.peaks[peak_index].data
  h,w=data.shape[1],data.shape[0] 
  x,y=arange(0,h),arange(0,w)
  X,Y=meshgrid(x,y)
  curraxis.cla()
  caxis=gca(projection='3d')
  caxis.plot_wireframe(X,Y,data)
  return

def plot_peak2peak(curraxis,imageclass,ind1=0,ind2=1,center=False,coords=(-1,-1),north=0.0,east_dir='cw'):
  #north should always be a positive angle, ie -90deg=270.0
  if east_dir=='cw': east=north-90.0
  else: east=north+90.0
  curraxis.cla()
  ind1,ind2,dx,dy,ds,center1,center2,ds_vect,drt,card_dir=\
    imageclass.find_pix2peaks(ind1=ind1,ind2=ind2,center=center,coords=coords,north_deg=north,east_dir=east_dir)
  curraxis.imshow(imageclass.data,origin='lower',interpolation='None')
  xlm,ylm=curraxis.get_xlim(),curraxis.get_ylim()
  curraxis.plot([center2[0],center1[0]],[center2[1],center1[1]],'-o',mew=1,ms=5,color='White')
  curraxis.text(center2[0],center2[1]+10,'dist:%7.3f,angle:%7.3f,%s' % (drt[0],drt[1],card_dir),family='serif',\
    color='White',fontsize=12)
  curraxis.text(center2[0],center2[1]+25,'%s@(%d,%d)' % ('Defined Center',center2[0],center2[1]),family='serif',\
    color='White',fontsize=12)
  curraxis.arrow(center1[0],center1[1],100,0,head_width=3,head_length=5,fc='White',ec='White')
  curraxis.arrow(center1[0],center1[1],100.0*cos(deg2rad(north)),100.0*sin(deg2rad(north)),head_length=5,head_width=3,\
    fc='White',ec='White')
  curraxis.text(center1[0]+100.0*cos(deg2rad(north))+10,center1[1]+100.0*sin(deg2rad(north))+10,'North',family='serif',\
    color='White',fontsize=12)
  curraxis.arrow(center1[0],center1[1],100.0*cos(deg2rad(east)),100.0*sin(deg2rad(east)),head_length=5,head_width=3,\
    fc='White',ec='White')
  curraxis.text(center1[0]+100.0*cos(deg2rad(east))+10,center1[1]+100.0*sin(deg2rad(east))+10,'East',family='serif',\
    color='White',fontsize=12)
  curraxis.text(center1[0]+120,center1[1],'0deg',family='serif',color='White',fontsize=12)
  curraxis.set_title('The distance and direction to the defined optical center of the telescope.',\
    family='serif',fontsize=16)
  curraxis.set_xlim(xlm);curraxis.set_ylim(ylm)
  return

def plot_peak0tocenter(curraxis,meas_thread_class,peak_index=0):
  parms_dict=meas_thread_class.process_args
  cent_measure=meas_thread_class.process_thread.measurements
  imageclass=meas_thread_class.process_thread.image_queue.get(timeout=2.0)
  shp=imageclass.data.shape
  north=parms_dict['north_deg']
  if parms_dict['east_dir']=='cw': east=north-90.0
  else: east=north+90.0
  curraxis.cla()
  peakx,peaky=cent_measure[0][5][0],cent_measure[0][5][1]
  center,ds,drt,card_dir=cent_measure[0][6],cent_measure[0][-2][0],cent_measure[0][-2],cent_measure[0][-1]
  curraxis.imshow(imageclass.data,origin='lower',interpolation='None')
  xlm,ylm=curraxis.get_xlim(),curraxis.get_ylim()
  curraxis.plot([center[0],peakx],[center[1],peaky],'-o',mew=1,ms=5,color='White')
  tdisp1,tdisp2,tdisp3=0.026*shp[1],0.059*shp[1],0.132*shp[1]
  llength=0.045*(shp[1]+shp[0])/2.0
  lxtra=0.0045*(shp[1]+shp[0])/2.0
  hl,hw=0.021*(shp[1]+shp[0])/2.0,0.0142*(shp[1]+shp[0])/2.0
  curraxis.text(center[0],center[1]+tdisp1,'dist:%7.3f,angle:%7.3f,%s' % (drt[0],drt[1],card_dir),family='serif',\
    color='White',fontsize=12)
  curraxis.text(center[0],center[1]+tdisp2,'%s@(%d,%d)' % ('Defined Center',center[0],center[1]),family='serif',\
    color='White',fontsize=12)
  curraxis.arrow(peakx,peaky,llength,0,head_width=hw,head_length=hl,fc='White',ec='White')
  curraxis.arrow(peakx,peaky,llength*cos(deg2rad(north)),llength*sin(deg2rad(north)),head_length=hl,head_width=hw,\
    fc='White',ec='White')
  curraxis.text(peakx+llength*cos(deg2rad(north))+lxtra,peaky+llength*sin(deg2rad(north))+lxtra,'North',family='serif',\
    color='White',fontsize=12)
  curraxis.arrow(peakx,peaky,llength*cos(deg2rad(east)),llength*sin(deg2rad(east)),head_length=hl,head_width=hw,\
    fc='White',ec='White')
  curraxis.text(peakx+llength*cos(deg2rad(east))+lxtra,peaky+llength*sin(deg2rad(east))+lxtra,'East',family='serif',\
    color='White',fontsize=12)
  curraxis.text(peakx+tdisp3,peaky,'0deg',family='serif',color='White',fontsize=12)
  curraxis.set_title('The distance and direction to the defined optical center of the telescope.',\
    family='serif',fontsize=12)
  curraxis.set_xlim(xlm);curraxis.set_ylim(ylm)
  return

def plot_peak2center(curraxis,imageclass,peak_index=0,center=zeros((2)),north=0.0,east_dir='cw'):
  #north should always be a positive angle, ie -90deg=270.0
  if east_dir=='cw': east=north-90.0
  else: east=north+90.0
  curraxis.cla()
  peakx,peaky=imageclass.peaks[peak_index].abs_x_center,imageclass.peaks[peak_index].abs_y_center
  center,ds,drt,card_dir,junk=ipt.move_to_center(imageclass,peak_index,new_center=center,north=north,\
    east_dir=east_dir,output=False)
  curraxis.imshow(imageclass.data,origin='lower',interpolation='None')
  xlm,ylm=curraxis.get_xlim(),curraxis.get_ylim()
  curraxis.plot([center[0],peakx],[center[1],peaky],'-o',mew=1,ms=5,color='White')
  curraxis.text(center[0],center[1]+10,'dist:%7.3f,angle:%7.3f,%s' % (drt[0],drt[1],card_dir),family='serif',\
    color='White',fontsize=12)
  curraxis.text(center[0],center[1]+25,'%s@(%d,%d)' % ('Defined Center',center[0],center[1]),family='serif',\
    color='White',fontsize=12)
  curraxis.arrow(peakx,peaky,100,0,head_width=3,head_length=5,fc='White',ec='White')
  curraxis.arrow(peakx,peaky,100.0*cos(deg2rad(north)),100.0*sin(deg2rad(north)),head_length=5,head_width=3,\
    fc='White',ec='White')
  curraxis.text(peakx+100.0*cos(deg2rad(north))+10,peaky+100.0*sin(deg2rad(north))+10,'North',family='serif',\
    color='White',fontsize=12)
  curraxis.arrow(peakx,peaky,100.0*cos(deg2rad(east)),100.0*sin(deg2rad(east)),head_length=5,head_width=3,\
    fc='White',ec='White')
  curraxis.text(peakx+100.0*cos(deg2rad(east))+10,peaky+100.0*sin(deg2rad(east))+10,'East',family='serif',\
    color='White',fontsize=12)
  curraxis.text(peakx+120,peaky,'0deg',family='serif',color='White',fontsize=12)
  curraxis.set_title('The distance and direction to the defined optical center of the telescope.',\
    family='serif',fontsize=16)
  curraxis.set_xlim(xlm);curraxis.set_ylim(ylm)
  return
def test_move(imageclass,center=zeros((2)),steps=10,north=0.0,east_dir='cw'):
  imageclass.find_peaks()
  imshow(imageclass.data,origin='lower',interpolation='None')
  zz=gca()
  cent,ds,drt,card_dir,junk=ipt.move_to_center(imageclass,0,new_center=center,north=north,\
    east_dir=east_dir,output=False)
  plot_peak2center(zz,imageclass,center=center,north=north,east_dir=east_dir)
  drt[1]=drt[1]+random.uniform(-15.0,15.0)
  raw_input('Plotting and shifting in (r,theta)'+str(drt)+' or the '+card_dir)
  newimage=ipt.shift_image(imageclass,dr=steps,dtheta=drt[1])
  newimage.find_peaks()
  plot_peak2center(zz,newimage,center=center,north=north,east_dir=east_dir)
  while drt[0]>steps/2:
    raw_input('Plotting and shifting in (r,theta)'+str(drt)+' or the '+card_dir)
    cent,ds,drt,card_dir,junk=ipt.move_to_center(newimage,0,new_center=center,north=north,\
      east_dir=east_dir,output=False)
    drt[1]=drt[1]+random.uniform(-90.0,90.0)
    newimage=ipt.shift_image(newimage,dr=steps,dtheta=drt[1])
    newimage.find_peaks()
    plot_peak2center(zz,newimage,center=center,north=north,east_dir=east_dir)
  print 'Finished CENTERING to optical axis!!!!'
  return

# To simulate moving and centering use the following as an example
#>>> mm=ipt.ImageFile(fname='test_mizar.fits')
#>>> mm.find_peaks()
#>>> reload(rpt);reload(rpt.ipt);rpt.plot_peak2center(zz,mm,center=array([400,150]))
#>>> newmm=ipt.shift_image(mm,dr=50,dtheta=-78.961);newmm.find_peaks()
#>>> reload(rpt);reload(rpt.ipt);rpt.plot_peak2center(zz,newmm,center=array([400,150]))
#>>> newmm=ipt.shift_image(newmm,dr=50,dtheta=-78.961);newmm.find_peaks()
#>>> reload(rpt);reload(rpt.ipt);rpt.plot_peak2center(zz,newmm,center=array([400,150]))
def angle_width(x_width,y_width,device_name=None):
  '''<dist2peaks>
     used to calculate the distances from one peak to another given a device
     returns dx, dy, ds in arcsecs
  '''
  if device_name!=None and device_name in ['GT1290','GX2750','SBIG','Video']:
    pixsize_x=eval('CAMERA_'+device_name+'_X_PIXSIZE')
    pixsize_y=eval('CAMERA_'+device_name+'_Y_PIXSIZE')
  else:
    pixsize_x=CAMERA_PIXSIZE
    pixsize_y=CAMERA_PIXSIZE
  try:
    dx=2.0*arctan(x_width*pixsize_x*1.0e-3/(2.0*TELE_FLENGTH))*180.0/pi*3600.0
    dy=2.0*arctan(y_width*pixsize_y*1.0e-3/(2.0*TELE_FLENGTH))*180.0/pi*3600.0
    ds=(dx**2.0+dy**2.0)**0.5
  except Exception:
    dx,dy,ds=0,0,0
  return dx,dy,ds

def test_coadd(imageclass1,imageclass2,index=0,coords=(0,0)):
  dst=imageclass1.pix2peaks(coords=(imageclass2.peaks[index].abs_x_center,imageclass2.peaks[index].abs_y_center))
  shift_image1=ipt.shift_image(imageclass1,dx=dst[-3][0],dy=dst[-3][1])
  newimage=ipt.ImageFile()
  newimage.header=imageclass1.header
  newimage.fname=imageclass1.fname+'added'
  newimage.data=shift_image1.data+imageclass2.data
  return newimage

def pix2angle(pixel_distance,device_name=None,bin_x=1,bin_y=1,tele_d=TELE_DIAM,fratio=TELE_FRATIO):
  #tele_d=TELE_DIAM      #Telescope diameter [m]
  #fratio=TELE_FRATIO    #Telescope fratio
  tele_f=fratio*tele_d  #Telescope focal length [m]
  if device_name!=None and device_name in ['GT1290','GX2750','SBIG','Video']:
    pixsize_x=eval('CAMERA_'+device_name+'_X_PIXSIZE')*1.0e-6*bin_x
    pixsize_y=eval('CAMERA_'+device_name+'_Y_PIXSIZE')*1.0e-6*bin_y
    pix_size=(pixsize_x+pixsize_y)/2.0
  else:
    pixsize_x=CAMERA_X_PIXSIZE*1.0e-6*bin_x
    pixsize_y=CAMERA_Y_PIXSIZE*1.0e-6*bin_y
    pix_size=(pixsize_x+pixsize_y)/2.0
  arcsec_per_pixel=2.0*arctan(pix_size/(2.0*tele_f))*180.0/pi*3600.0
  radperpix=arcsec_per_pixel/3600.0*pi/180.0
  ang_dist=pixel_distance*arcsec_per_pixel
  print 'A pixel separation of %10.3f is %10.3f\"(%7.3e radians)' % (pixel_distance,ang_dist,pixel_distance*radperpix)
  return ang_dist

def print_peak_dists(imageclass,imageprocclass=None):
  if not imageprocclass:  imageprocclass=ipt.ImageProcess()
  ret=imageprocclass(imageclass,'pix2peaks')
  ret_list=[]
  print 'Distance and direction from indexed peak i to indexed peak j'
  if ret[2:5]!=[0.0,0.0,0.0] and imageclass.num_peaks>=2:
    for i in range(imageclass.num_peaks):
      for j in range(imageclass.num_peaks):
        if i!=j:
          ret=imageprocclass(imageclass,'pix2peaks',ind1=i,ind2=j)
          print ' %d -> %d, (%7.3f,%7.3f)' % (i,j,ret[-2][0],ret[-2][1])
          ret_list.append(ret)
  return ret_list

def print_fluxes(subdir,proc=None):
  if not proc:  proc=ipt.ImageProcess()
  a,b=return_images(subdir)
  for each in a:
    proc(each,'peaks')
    i=0
    c=pl_image(each,nrm=LogNorm,vmin=100,vmax=5000)
    for every in each.peaks:
      i+=1
      #try: print 'Peak:%d  Name: %s  HM_flux: %10.3f  HM_flux-background: %10.3f\n  Data size: %d,'+\
      #       'Number HM pixels: %d\n Height: %10.3f,(abs_x,abs_y): (%10.3f,%10.3f)' %\
      #       (i,each.header['OBJECT'],every.int_flux_hm,every.reducd_flux,\
      #       every.x_pixels*every.y_pixels,every.half_max_pixels.size,every.height,\
      #       every.abs_x_center,every.abs_y_center)
      #except Exception as err:  print 'Peak:%d  Name: N/A HM_flux: %10.3f  HM_flux-background: %10.3f\n'+\
      #       '  Data size: %d, Number HM pixels: %d\nHeight: %10.3f,(abs_x,abs_y): (%10.3f,%10.3f)' %\
      #       (i,every.int_flux_hm,every.reducd_flux,\
      #       every.x_pixels*every.y_pixels,every.half_max_pixels.size,every.height,\
      #       every.abs_x_center,every.abs_y_center)
      try: print 'Peak:%d  Name: %s  HM_flux: %10.3f  HM_flux-background: %10.3f,Height: %10.3f' % \
             (i,each.header['OBJECT'],every.int_flux_hm,every.reducd_flux,every.height)
      except Exception as err:  print 'Peak:%d  Name: N/A HM_flux: %10.3f  HM_flux-background: %10.3f,Height: %10.3f' %\
             (i,every.int_flux_hm,every.reducd_flux,every.height)
    if raw_input('>>')=='x':  return each
  return
#
#
#To run through images
#
def pl_pk_im(proc=None,subdir='',fig1=None,fig2=None,fig3=None,info_box=None,peak1=0,peak2=1):
  if subdir: subdir=subdir+'/'
  if not proc:  proc=ipt.ImageProcess()
  if not fig1:  fig1=figure()
  if not fig2:  fig2=figure()
  if not fig3:  fig3=figure()
  if not info_box: info_box=Text(Tk(),width=100,height=60)
  info_box.grid()
  #subdir='04apr18-zosma-a'
  ll=[each for each in os.listdir('../imgdata/'+subdir) if 'fits' in each]
  for each in ll:
    info_box.delete('1.0','end')
    mm=ipf.ImageFile(fname=subdir+each)
    proc(mm,'peaks')
    if 'OBJECT' not in mm.header.keys(): mm.header['OBJECT']='N/A'
    fig1.clf()
    gg=fig1.gca().imshow(proc.image.data,origin='lower',cmap='gray')
    gg.set_norm(LogNorm(vmin=1,vmax=50000))
    fig1.get_axes()[-1].set_title('Filename: %s, Source: %s\nSubdirectory: %s' % (each,mm.header['OBJECT'],subdir))
    fig1.show()
    label_peaks(fig1.gca(),proc,color='Red')
    fig2.clf()
    try: kk=plot_a_peak(proc,peak1,fig=fig2)
    except Exception: pass
    fig2.suptitle('Filename: %s, Source: %s\nSubdirectory: %s' % (each,mm.header['OBJECT'],subdir))
    fig2.canvas._master.title('Peak Number: %d' % (peak1))
    #mm;mm.header['INSTRUME'];proc.peaks[0]
    fig3.clf()
    try: kk=plot_a_peak(proc,peak2,fig=fig3)
    except Exception: pass
    fig3.suptitle('Filename: %s, Source: %s\nSubdirectory: %s' % (each,mm.header['OBJECT'],subdir))
    fig3.canvas._master.title('Peak Number: %d' % (peak2))
    [info_box.insert('end',each+'\n') for each in [str(every)+': '+str(mm.header[every]) for every in mm.header]]
    if raw_input()=='x':  return fig1,fig2,fig3,info_box
  return fig1,fig2,fig3,info_box

def pl_one_pk(img_file,proc=None,fig1=None,fig2=None,fig3=None,info_box=None,peak1=0,peak2=1):
  if not proc:  proc=ipt.ImageProcess()
  if not fig1:  fig1=figure()
  if not fig2:  fig2=figure()
  if not fig3:  fig3=figure()
  if not info_box: info_box=Text(Tk(),width=100,height=60)
  info_box.grid()
  info_box.delete('1.0','end')
  proc(img_file,'peaks')
  if 'OBJECT' not in img_file.header.keys(): img_file.header['OBJECT']='N/A'
  fig1.clf()
  gg=fig1.gca().imshow(proc.image.data,origin='lower',cmap='gray')
  gg.set_norm(LogNorm(vmin=1,vmax=50000))
  fig1.get_axes()[-1].set_title('Filename: %s, Source: %s' % (img_file.fname,img_file.header['OBJECT']))
  fig1.show()
  label_peaks(fig1.gca(),proc,color='Red')
  fig2.clf()
  try: kk=plot_a_peak(proc,peak1,fig=fig2)
  except Exception: pass
  fig2.suptitle('Filename: %s, Source: %s' % (img_file.fname,img_file.header['OBJECT']))
  fig2.canvas._master.title('Peak Number: %d' % (peak1))
  fig3.clf()
  try: kk=plot_a_peak(proc,peak2,fig=fig3)
  except Exception: pass
  fig3.suptitle('Filename: %s, Source: %s' % (img_file.fname,img_file.header['OBJECT']))
  fig3.canvas._master.title('Peak Number: %d' % (peak2))
  [info_box.insert('end',each+'\n') for each in [str(every)+': '+str(img_file.header[every]) for every in img_file.header]]
  return fig1,fig2,fig3,info_box

def add_seeing_images(subdir=''):
  proc=ipt.ImageProcess()
  if subdir: subdir=subdir+'/'
  ll=[each for each in os.listdir('../imgdata/'+subdir) if 'fits' in each]
  mm_list=[ipf.ImageFile(fname=subdir+each) for each in ll]
  see_list=[each for each in mm_list if each.data.shape==(500,500)]
  ddlist=[]
  for each in see_list:
    ddlist.append(proc(each,'pix2peaks')[-2])
  dist_array=array(ddlist).transpose()
  see_string=ipt.calc_seeing(dist_array[0].std(),device_name='GX2750')
  widths_list=[]
  for each in see_list:
    widths_list.append([each.peaks[0].x_width,each.peaks[0].y_width,each.peaks[1].x_width,each.peaks[1].y_width])
  widths_array=array(widths_list)
  # use '>>> widths_array.mean(axis=1)' to get the mean of both peaks over both axes.
  # use '>>> ipt.calc_ang_sep(widths_array.mean(axis=1).mean(),device_name='GX2750') to get average fwhm angle of peaks
  return mm_list,see_list,dist_array,see_string,widths_array
def calc_seeing_from_images(see_list,proc=None):
  if not proc:  proc=ipt.ImageProcess()
  ddlist=[]
  for each in see_list:
    ddlist.append(proc(each,'pix2peaks')[-2])
  dist_array=array(ddlist).transpose()
  d_indx=where((dist_array[0]<dist_array[0].mean()+3.0*dist_array[0].std()) & \
    (dist_array[0]>dist_array[0].mean()-3.0*dist_array[0].std()))
  dist_array=dist_array[:,d_indx]
  exclde=setdiff1d(arange(len(see_list)),d_indx)
  for i in exclde[::-1]:
    see_list.pop(i)
  see_string=ipt.calc_seeing(dist_array[0].std(),device_name='GX2750')
  widths_list=[]
  flux_list=[]
  for each in see_list:
    widths_list.append([each.peaks[0].x_width,each.peaks[0].y_width,each.peaks[1].x_width,each.peaks[1].y_width])
    flux_list.append([array(each.peaks[0]),array(each.peaks[1])])
  widths_array=array(widths_list)
  flux_arrays=array(flux_list)
  # use '>>> widths_array.mean(axis=1)' to get the mean of both peaks over both axes.
  # use '>>> ipt.calc_ang_sep(widths_array.mean(axis=1).mean(),device_name='GX2750') to get average fwhm angle of peaks
  ang_widths=array([map(lambda x:pix2angle(x,device_name='GX2750'),widths_array[i]) for i in range(len(widths_array))])
  avr_red_flux=flux_arrays[:,:,-1].mean(axis=1)
  return dist_array,see_string,widths_array,ang_widths,flux_arrays,avr_red_flux

def return_images(subdir=''):
  proc=ipt.ImageProcess()
  if 'imgdata' in subdir: subdir=subdir.split('imgdata/')[1]
  if subdir: subdir=subdir+'/'
  ll=[each for each in os.listdir('../imgdata/'+subdir) if 'fits' in each]
  mm_list=[ipf.ImageFile(fname=subdir+each) for each in ll]
  see_list=[each for each in mm_list if each.data.shape==(500,500)]
  return mm_list,see_list

def get_dir_info(mon=5,day=5,year=2018):
  tme=time.strptime(str(mon)+'/'+str(day)+'/'+str(year),'%m/%d/%Y')
  topdir=time.strftime('%b%Y',tme)
  subdir=time.strftime('%B%d',tme)
  dr=ospjoin(DIMM_DIR,'imgdata',topdir,subdir)
  if isdir(dr):
    mm=os.listdir(dr)
  else:
    mm=[]
  all_dirs=[]
  i=0
  for each in mm:
    all_dirs.append(ospjoin(dr,each))
    print i,len(os.listdir(ospjoin(dr,each))),ospjoin(dr,each)
    i+=1
  return all_dirs
# To get images from a directory use:
#>>>mm=get_dir_info(mon=6,day=4)
#>>>a,b=return_images(mm[0].split('/imgdata/')[1])

def sort_img_time(image_list):
  srt_list=[]
  for i in range(len(image_list)):
    ddt=datetime.datetime.strptime(image_list[i].header['DATE-OBS']+' '+image_list[i].header['TIME-OBS'],\
      '%m/%d/%Y %H:%M:%S')
    srt_list.append([i,ddt])
  srt_array=array(srt_list).transpose()
  ndce=srt_array.argsort(axis=1)[1]
  srt_list=map(lambda i: image_list[i],ndce)
  return srt_list

def calc_seeing(std_dev,device_name=None,bin_x=1,bin_y=1,b=TELE_SUBSEPARATION,d=TELE_SUBAPERTURE):
#def calc_seeing(dist_array,device_name=None,bin_x=1,bin_y=1):
  #b=TELE_SUBSEPARATION  #Sub-aperture separation in [m]
  #d=TELE_SUBAPERTURE    #Sub-aperture diameter in [m]
  tele_d=TELE_DIAM      #Telescope diameter [m]
  fratio=TELE_FRATIO    #Telescope fratio
  tele_f=fratio*tele_d  #Telescope focal length [m]
  #pix_size=CAMERA_PIXSIZE*1.0e-6 #Pixel size in [m], here is the average of the two, assuming square pixels???
  if device_name!=None and device_name in ['GT1290','GX2750','SBIG','Video']:
    pixsize_x=eval('CAMERA_'+device_name+'_X_PIXSIZE')*1.0e-6*bin_x
    pixsize_y=eval('CAMERA_'+device_name+'_Y_PIXSIZE')*1.0e-6*bin_y
#   pix_size=eval('CAMERA_'+device_name+'_PIXSIZE')*1.0e-6*bin_x
    pix_size=(pixsize_x+pixsize_y)/2.0
  else:
    pixsize_x=CAMERA_X_PIXSIZE*1.0e-6*bin_x
    pixsize_y=CAMERA_Y_PIXSIZE*1.0e-6*bin_y
#   pix_size=CAMERA_PIXSIZE*1.0e-6*bin_x
    pix_size=(pixsize_x+pixsize_y)/2.0
  arcsec_per_pixel=2.0*arctan(pix_size/(2.0*tele_f))*180.0/pi*3600.0
  radperpix=arcsec_per_pixel/3600.0*pi/180.0
  bdratio=b/d
  klg=0.340*(1.0-0.570*bdratio**(-1.0/3.0)-0.040*bdratio**(-7.0/3.0))
  klz=0.364*(1.0-0.532*bdratio**(-1.0/3.0)-0.024*bdratio**(-7.0/3.0))
  ktg=0.340*(1.0-0.855*bdratio**(-1.0/3.0)-0.030*bdratio**(-7.0/3.0))
  ktz=0.364*(1.0-0.798*bdratio**(-1.0/3.0)-0.018*bdratio**(-7.0/3.0))
# rad_dists=dist_array*radperpix
# st_var_rads=(dist_array.std()*radperpix)**2.0
# var_rads=rad_dists.var()
  var_rads=(std_dev*radperpix)**2.0
  wavelen=0.5e-6
  ro_lg=var_rads**(-0.6)*d**(-0.2)*klg**(0.6)*wavelen**(0.2)*wavelen
  ro_tg=var_rads**(-0.6)*d**(-0.2)*ktg**(0.6)*wavelen**(0.2)*wavelen
  ro_lz=var_rads**(-0.6)*d**(-0.2)*klz**(0.6)*wavelen**(0.2)*wavelen
  ro_tz=var_rads**(-0.6)*d**(-0.2)*ktz**(0.6)*wavelen**(0.2)*wavelen
# ro_lg=((var_rads*d**(1.0/3.0))/(klg*wavelen**2.0))**(-3.0/5.0)
# ro_tg=((var_rads*d**(1.0/3.0))/(ktg*wavelen**2.0))**(-3.0/5.0)
# ro_lz=((var_rads*d**(1.0/3.0))/(klz*wavelen**2.0))**(-3.0/5.0)
# ro_tz=((var_rads*d**(1.0/3.0))/(ktz*wavelen**2.0))**(-3.0/5.0)
  eps_lg=0.98*wavelen/ro_lg*180.0/pi*3600.0  #arcsec fwhm seeing
  eps_tg=0.98*wavelen/ro_tg*180.0/pi*3600.0  #arcsec fwhm seeing
  eps_lz=0.98*wavelen/ro_lz*180.0/pi*3600.0  #arcsec fwhm seeing
  eps_tz=0.98*wavelen/ro_tz*180.0/pi*3600.0  #arcsec fwhm seeing
  #res=1.22*wavelen/tele_d*180.0/pi*3600.0
  res=1.22*wavelen/d*180.0/pi*3600.0
  return eps_lg,eps_lz,eps_tg,eps_tz,res

