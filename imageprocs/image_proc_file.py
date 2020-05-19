#! /usr/bin/env python image_proc_file.py
#
#
import sys
sys.path.append('..')

from numpy import *
from pylab import imsave,imread
import threading
import Queue
import time
import pyfits
from scipy.optimize import leastsq as leastsq

from os.path import isfile as fexists
from os.path import join as ospjoin
from os.path import exists as ospexists
from os import listdir,getcwd,makedirs
from filecmp import cmp as fcompare

from common_parms import *

#
#   --> Using FITSLIST and FITSDICT is a sloppy way of ordering the Cards in the Header class
#       FITSLIST is simply a list (ordered) with the FITSDICT keys.  With that said, in order to 
#       add header information both module variables, FITSLIST and FITSDICT, have to be edited.
#   --> These are only used in the <create_fits_header> function
#

FITSLIST=['SIMPLE','BITPIX','NAXIS','NAXIS1','NAXIS2',\
  'OBJECT','TELESCOP','INSTRUME','OBSERVER','DATE-OBS','TIME-OBS',\
  'BSCALE','BZERO','BUNIT','EXPTIME','CGAIN','EXPSTATE','XBINNING','YBINNING','TEMP-CCD','TEMP-AMB',\
  'ORIGIN','TELLONG','TELLAT','TELALT',\
  'UT-DATE','UT-TIME','NIGHT','EPOCH','ST',\
  'SCALE','EGAIN','ENOISE','RA','DEC','AZ','ELV','EQUINOX','AIRMASS',\
  'ZDIST','MAGN',\
  'SOFTWARE','FITSVERS','COMMENT']

FITSDICT=\
{'SIMPLE':True,#mandatory keywords
 'BITPIX':CAMERA_BIT,
 'NAXIS':2,
 'NAXIS1':CAMERA_X,
 'NAXIS2':CAMERA_Y,

 'OBJECT':'',
 'TELESCOP':TELE_NAME,
 'INSTRUME':CAMERA_NAME,
 'OBSERVER':'DIMM-OBSERVER',
 'DATE-OBS':'',
 'TIME-OBS':'',

 'BSCALE':1,# scaling 
 'BZERO':0,
 'BUNIT':'',

 'EXPTIME':0.0,
 'CGAIN':0,
 'EXPSTATE':1,
 'XBINNING':1,
 'YBINNING':1,
 'TEMP-CCD':0.0,
 'TEMP-AMB':0.0,

 'ORIGIN':'',

 'TELLONG':DIMLNG,
 'TELLAT':DIMLAT,
 'TELALT':DIMELV,

 'UT-DATE':'',
 'UT-TIME':'',
 'NIGHT':'',
 'EPOCH':2000.0,
 'ST':'',

 'SCALE':'',
 'EGAIN':'',
 'ENOISE':'',

 'RA':'',
 'DEC':'',
 'AZ':'',
 'ELV':'',
 'EQUINOX':2000.0,
 'AIRMASS':'',
 'ZDIST':'',
 'MAGN':'',

 'SOFTWARE':'',
 'FITSVERS':'',

 'COMMENT':''}#must be last one before 'END'

class ImageFile(object):
  ''' <ImageFile> class acts to combine the fits header information and
      the pixel data. It is intended to provide easier access to the fits
      header data and a better ability to create/write new fits files. 
  '''
  def __init__(self,fname=None,data=random.random((CAMERA_X,CAMERA_Y))*1.0e-3):
    ''' <__init__> 
        function accepts <fname> and <data>
        <fname> is either None, a filename, or a camera thread device (from the <camera_thread.py> module)
        a filename will open the fits image file for processing while a camera device will create fits header
        using the camera information and data.
        NOTE:  This initializes the data, image array, to small random numbers
    '''
    self.local_date,self.local_time=None,None
    '''@ivar: Current Local Date and Time '''
    self.obs_date,self.obs_time=None,None
    '''@ivar: Observation Date and Time '''
    self.get_time()
    self.hdulist=[]
    '''@ivar: The HDU list for fits '''
    self.header=None
    '''@ivar: Header information for fits file '''
    self.data=data
    '''@ivar: Image Data '''
    # Check to see if fname is a filename, None, or camera type
    if fname!=None and type(fname)==str:
      # If fname is a filename open the fits file, get the header and data
      if fexists(IMG_DIR+fname) and ('fits' in fname or 'fit' in fname):
        self.open_fits_file(fname)
      elif fexists(IMG_DIR+fname) and 'jpg' in fname:
        self.fname=fname
        self.data=imread(IMG_DIR+fname)[:,:,0]
        self.create_header()
      else:
      # If fname does not exist, set <self.fname> to <fname> and create a new header.  Data provided later.
        self.fname=fname
        self.create_header()
    elif 'CameraThread' in str(type(fname)):
    # If fname is of type CameraThread from the 'camera' directory create the image file
      self.fname=fname.camera_name.replace(' ','').lower()+'-'+self.local_time.replace(':','_')+\
        '-'+self.local_date.replace('/','_')+'.fits'
      self.data=fname.data
      self.create_header(device=fname)
    else:
    # else just create a blank ImageFile class
      self.fname='test_image-'+self.local_time.replace(':','_')+'-'+self.local_date.replace('/','_')+'.fits'
      self.create_header()
    self.peaks=[]
    self.num_peaks=len(self.peaks)
    self.centers=array([])
    self.calc_background=0.0
    self.calc_bckgrnd_std=0.0
    return
  def __repr__(self):
    ss='\n'
    ss=ss+'<image_proc_file.ImageFile object>\n'
    ss=ss+'fname:             %s\n' % self.fname
    ss=ss+'Observed Date/Time:%s %s\n' % (self.obs_time,self.obs_date)
    ss=ss+'Current Date/Time: %s %s\n' % (self.local_time,self.local_date)
    ss=ss+'\n'
    return ss
  def add_keyword(self,key='KEYWORD',value=None,comment=None):
    ''' <add_keyword> adds the keyword <key> to the fits header
    '''
    #More information about header keyword is available in pyfits manual under
    #  class Cards  (the class of one item of header data)
    #self.header.update(key,value,comment)  #OLD USAGE
    self.header.set(key,value=value,comment=comment,before=None,after=None)
    return
  def del_keyword(self,key='KEYWORD'):
    ''' <del_keyword> deletes the header keyword <key>
    '''
    del self.header[key]
    return
  def add2header(self,**kwargs):
    for each in kwargs.keys():
      if each=='source': kwargs['object']=kwargs['source']; each='object'
      if each=='dateobs': kwargs['date-obs']=kwargs['dateobs']; each='date-obs'
      if each=='timeobs': kwargs['time-obs']=kwargs['timeobs']; each='time-obs'
      self.header.set(each[:8],kwargs[each])
      ##Could use self.header.set('object',kwargs('source',kwargs.get('object','NA')))
      ## to set a default value
    return
  def create_header(self,device=None):
    '''<create_header>
         Creates a header with the mandatory keywords and uses the <device> camera if not NONE
         else will create a generic blank header
    '''
    self.header=create_fits_header()
    if device!=None:
      self.get_time()
      self.header.set('SIMPLE',value=True,comment='',before=None,after=None)
      self.header.set('BITPIX',value=device.camera_bits,comment='',before=None,after=None)
      self.header.set('NAXIS',value=2,comment='',before=None,after=None)
      self.header.set('NAXIS1',value=device.data.shape[1],comment='',before=None,after=None)
      self.header.set('NAXIS2',value=device.data.shape[0],comment='',before=None,after=None)
      self.header.set('LC-DATE',value=self.obs_date,comment='',before=None,after=None)
      self.header.set('LC-TIME',value=self.obs_time,comment='',before=None,after=None)
      self.header.set('CUR-DATE',value=self.local_date,comment='',before=None,after=None)
      self.header.set('CUR-TIME',value=self.local_time,comment='',before=None,after=None)
      self.header.set('INSTRUME',value=device.device_name,comment='',before=None,after=None)
    return
  def get_time(self):
    ''' <get_time>
        A standard formatted time routine, format given in the common_parms.py file
        If the <fname> is an existing fits file, get_time will use the header date and time,
        else it will set the date and time.
    '''
    if hasattr(self,'header') and self.header!=None:
      if 'LC-DATE' in self.header:
        self.obs_date,self.obs_time=self.header['LC-DATE'],self.header['LC-TIME']
      else:
        self.obs_date,self.obs_time=time.strftime(DTIME_FORMAT).split(',')
    else:
      self.obs_date,self.obs_time=time.strftime(DTIME_FORMAT).split(',')
    self.local_date,self.local_time=time.strftime(DTIME_FORMAT).split(',')
    return
  def write_new_image(self,fname=None,data=None,header=None,fmt='fits',test_qualifier='-1'):
    ''' <write_new_image> creates/writes the image to either a new fits file in dated IMG_DIR subdirectory
        with the given filename,
        <fname>, with image array data, <data>, and the header information, <header>, or to a .jpg file.
        Note: 
        <test_qualifier> is the test subdirectory qualifier, if =='-1' will write to the dated IMG_DIR directly.
        if <fname>==None, a name will be defined based on time and date
        if <data>==None, current data in <self> will be used
        if <header>==None, current header in <self> will be used
    '''
    subdir1=ospjoin(IMG_DIR,time.strftime('%b%Y',time.strptime(self.local_date+','+self.local_time,DTIME_FORMAT)))
    subdir2=ospjoin(subdir1,time.strftime('%B%d',time.strptime(self.local_date+','+self.local_time,DTIME_FORMAT)))
    if test_qualifier!='-1': test_subdir='test-'+str(test_qualifier)
    else: test_subdir=''
    fullpath=ospjoin(subdir2,test_subdir)
    if not ospexists(fullpath): makedirs(fullpath)
    if fmt=='fits':
      if fname: self.fname=fname
      if fexists(fullpath+'/'+self.fname): 
        self.fname=self.fname.rstrip('.fits')+'-'+str(time.time()).replace('.','')[-2:]+'.fits'
      if not 'fit' in self.fname: self.fname=self.fname+'.fits'
      if data: self.data=data   
      if header: self.header=header
      hdu=pyfits.PrimaryHDU(self.data)
      ####To add header information use
      #hdu.header['keyword']='VALUE' or hdu.header=header
      hdu.header=self.header  ##Care to not overwrite the important header info
      hdu.writeto(fullpath+'/'+self.fname)
      del hdu
    elif fmt=='jpg':
      if not fname: fname=self.fname.split('.fit')[0]+'.jpg'
      if not 'jpg' in fname: fname=fname+'.jpg'
      imsave(fullpath+'/'+fname,self.data,format='jpg',cmap='gray',origin='lower')
    else: pass
    return
  def open_fits_file(self,fname):
    self.fname=fname
    self.hdulist=pyfits.open(IMG_DIR+self.fname)
    self.hdulist.close()
    self.data=pyfits.getdata(IMG_DIR+self.fname)
    self.header=self.hdulist[0].header
    self.get_time()
    return
  def pprint_peaks(self):
    sss='<<>>Peak Index,Boxsize x, Boxsize y, Number of pixels, Height, x_center, x_width, abs_x_center, '+\
      'y_center, y_width, abs_y_center, integrated half max flux, int_hm_flux-background\n'
    if self.peaks:
      ss='\n'.join(['<<>>'+str(i)+','+','.join(map(lambda x: '%10.3f' % x,array(self.peaks[i]))) for i in \
        range(len(self.peaks))])
    else:
      ss=''
    return sss+ss
      
##
# An example of building a header in pyfits
# >>>header=pyfits.Header()
# >>>card=pyfits.Card('TELESCOP','Meade LX-200','DIMM')
# >>>header.append(card=card)
#
# or use a list and update values and comments
# >>>for each in ['TELESCOP','OBSERVER','LC-TIME']:
# >>>  header.set(each,'')
# >>>header.update('OBSERVER','Bob Stupak','Jerk')
##
def create_fits_header():
  '''<create_fits_header>
     Creates and returns a new fits header with 'cards' as defined in the FITSDICT at the top of this module
     --> Using FITSLIST and FITSDICT is a sloppy way of ordering the Cards in the Header.
  '''
  hdr=pyfits.header.Header()
  for each in FITSLIST:
    card=pyfits.Card(each,FITSDICT[each],'')
    hdr.append(card=card)
  return hdr
#
#
#
def create_hdu(image_list,wr=False):
  '''<create_hdu>
     Creates a fits header data unit given a list of ImageFile class.  This can be used to write
     fits data cubes to a file.  
  '''
  fits_hdu=pyfits.HDUList([pyfits.PrimaryHDU(image_list[0].data,header=image_list[0].header)])
  try:
    src=image_list[0].header['OBJECT'].lower().replace(' ','').replace('-','_')
  except Exception as err:
    src='test_image'
  [fits_hdu.append(pyfits.ImageHDU(image_list[i].data,header=image_list[i].header,name='%s_%d' % (src,i))) \
    for i in range(len(image_list[1:]))]
  if wr:
    dtstamp='%s_%s' % \
      (image_list[0].header['DATE-OBS'].replace('/','_'),image_list[0].header['TIME-OBS'].replace(':',''))
    fits_hdu.writeto('%s_%s' % (src,dtstamp))
  #fits_hdu.close()
  #    To open this use testhdu=pyfits.open(<filename>)
  #    To get information use testhdu.info()
  return fits_hdu
#
#
#
def create_hdu_table(image_list):
  ##A fits table can never be a primary HDU
  ##Note also that this table hdu can be appended to the hdu_list returned from <create_hdu>
  c1=pyfits.Column(name='datetime',format='22A',array=
    array(['%s %s' % (each.header['DATE-OBS'],each.header['TIME-OBS']) for each in image_list]))
  c2=pyfits.Column(name='object',format='20A',array=array([each.header['OBJECT'] for each in image_list]))
  ip_proc=ipt.ImageProcess()
  for each in image_list:
    try: ip_proc(each,'peaks')
    except: pass
  mmbb=array([array([each.calc_background,each.calc_bckgrnd_std]) for each in image_list])
  c3=pyfits.Column(name='background',format='D',unit='DN',array=mmbb.transpose()[0])
  c4=pyfits.Column(name='backg_std',format='D',unit='DN',array=mmbb.transpose()[1])
  c5=pyfits.Column(name='exptime',format='D',array=array([each.header['EXPTIME'] for each in image_list]))
  c6=pyfits.Column(name='cgain',format='D',array=array([each.header['CGAIN'] for each in image_list]))
  tbhdu=pyfits.new_table([c4,c1,c2,c3,c5,c6])
  return tbhdu
  #Use, for example, like:
  #>>> mask=tbdata.field('exptime')==0.1
  #>>> newtbdata=tbdata[mask]
  #>>> hdu=pyfits.BinTableHDU(newtbdata)
  #>>> hdu.writeto('newtable.fits')
#
#
#
class RegionData(object):
  ''' <RegionData> is a class that contains pixeldata for the region of interest
      centered at the <centroid> with a box <box_slices> around it.  <box_slices>
      is of type <slices> from the scipy module.  Refer to the scipy manual for
      details.  It offers the ability to fit a 2d gaussian to an image of a star.
  '''
  def __init__(self,data,box_slices,centroid,background):
    ''' <__init__> accepts <data>(an image array), <box_slices>(type slices from
        scipy) which defines box around the centroid, and <centroid> which is the
        center(center of mass for the star's image) in the full image coordinates.
    '''
    x1,x2=box_slices[1].start,box_slices[1].stop
    y1,y2=box_slices[0].start,box_slices[0].stop
    x,y=centroid[1]-x1,centroid[0]-y1
    self.data=data
    self.background=background
    #
    #print 'Data SHAPE:',self.data.shape
    #print '\nx slices:',box_slices[1]
    #print 'x:',int(x),x,x1+x,centroid[1],x1,x2
    #print '\ny slices:',box_slices[0]
    #print 'y:',int(y),y,y1+y,centroid[0],y1,y2,'\n'
    #
    self.x_pixels=data.shape[1] #######
    self.x_slice=data[:,int(x)]
    self.x_width=sqrt(abs((arange(self.x_slice.size)-x)**2.0*self.x_slice).sum()/self.x_slice.sum())
    self.x_center=x
    self.abs_x_center=centroid[1]
    self.y_pixels=data.shape[0] #######
    self.y_slice=data[int(y),:]
    self.y_width=sqrt(abs((arange(self.y_slice.size)-y)**2.0*self.y_slice).sum()/self.y_slice.sum())
    self.y_center=y
    self.abs_y_center=centroid[0]
    #Maybe need to change finding the max of data?
    self.height=data.max()
    self.half_max_pixels=data[data>self.height/2]
    self.int_flux_hm=self.half_max_pixels.sum()
    self.reducd_flux=self.int_flux_hm-self.background*len(self.half_max_pixels)
    self.parms=self.height,self.x_center,self.y_center,self.x_width,self.y_width
    return
  def __repr__(self):
    ss='\n'
    ss=ss+'<image_proc_thread.RegionData object>\n\n'
    ss=ss+'Data Shape:       (%d,%d)\n' % (self.x_pixels,self.y_pixels)
    ss=ss+'Number of pixels: %d\n' % (self.x_pixels*self.y_pixels)
    ss=ss+'Height:           %10.3f\n' % self.height
    ss=ss+'Relative x_center:%10.4f\n' % self.x_center
    ss=ss+'x_width:          %10.4f\n' % self.x_width
    ss=ss+'abs_x_center:     %10.4f\n' % self.abs_x_center
    ss=ss+'Relative y_center:%10.4f\n' % self.y_center
    ss=ss+'y_width:          %10.4f\n' % self.y_width
    ss=ss+'abs_y_center:     %10.4f\n' % self.abs_y_center
    ss=ss+'\n'
    ss=ss+'Half Max Int Flux:%10.2f\n' % self.int_flux_hm
    ss=ss+'HM flux-backgrnd: %10.2f\n' % self.reducd_flux
    return ss
  def __array__(self):
    sarray=array([self.x_pixels,self.y_pixels,self.x_pixels*self.y_pixels,\
                  self.height,self.x_center,self.x_width,self.abs_x_center,\
                  self.y_center,self.y_width,self.abs_y_center,\
                  self.int_flux_hm,self.reducd_flux])
    return sarray
  def gaussian(self,height,x_center,y_center,x_width,y_width):
    '''Returns a gaussian function with the given parameters '''
    gfunc=lambda x,y: height*exp(-(((x_center-x)/x_width)**2.0+((y_center-y)/y_width)**2.0)/2.0)
    return gfunc
  def fit_gaussian(self,data):
    '''Returns (height, x_center, y_center, x_width, y_width)
       the parameters of a 2D gaussian distribution found by a least squares fit
    '''
    erf=lambda p: ravel(self.gaussian(*p)(*indices(data.shape))-data)
    p,success=leastsq(erf,self.parms)
    return p
  def make_fit_data(self):
    self.fit_parms=self.fit_gaussian(self.data.transpose())
    fitdata=self.gaussian(*self.fit_parms)
    w,h=self.data.shape
    x,y=arange(0,h),arange(0,w)
    X,Y=meshgrid(x,y)
    self.fitted_data=fitdata(X,Y)
    return
#
#
#
#123456##########################################################
class FileDevice(object):
  '''<FileDevice>
       is used to mimic the CameraThread so that files can be processed.  This is the device
       used in ImageProcThread class
  '''
  def __init__(self,fname=None):
    self.camera_name='file'
    self.filename=fname
    self.exposure_count=1
    self.seq_exp_list=CAMERA_SEQ_EXPTIMES
    self.auto_delay=CAMERA_SEQ_DELAY
    self.sequence_count=0
    self.sequence_total_number=CAMERA_SEQ_TOTAL_NUM
    self.exptime=0.1
    self.data=zeros((500,500))
    self.width,self.height=500,500
    self.offset_x,self.offset_y=0,0
    self.binning_x,self.binning_y=1,1
    self.gain=0
    self.data_queue=Queue.Queue()
    self.take_exposure_stat=threading.Event()
    self.read_out_stat=threading.Event()
    self.new_data_ready_stat=threading.Event()
    self.auto_sequence_stat=threading.Event()
    self.take_exposure_stat.clear()
    self.new_data_ready_stat.clear()
    self.auto_sequence_stat.clear()
    self.message=''
    return
  def change_file(self,fname=None):
    self.new_data_ready_stat.clear()
    self.filename=fname
    self.data=ImageFile(fname=self.filename).data
    self.data_queue.put(self.data)
    self.take_exposure_stat.clear()
    self.new_data_ready_stat.set()
    return
  def isAlive(self):
    return True
  def start(self):
    return
  def acquire_image(self):
    return
  def close(self):
    self.auto_sequence_stat.clear()
    return
  def save_image(self,fname=None,fmt='fits'):
    ''' <save_image>
        A generic save routine to save the image to either a 'fits' file or 'jpg' 
        depending on fmt.
    '''
    self.local_date,self.local_time=time.strftime(DTIME_FORMAT).split(',')
    if fname==None:
      fname=IMG_DIR+'test'
    else:
      fname=IMG_DIR+fname+'.'+fmt
    if fmt=='fits':
      hdu=pyfits.PrimaryHDU(self.data)
      hdu.header.set('SIMPLE',value=True,comment='',before=None,after=None)
      hdu.header.set('BITPIX',value=8,comment='',before=None,after=None)
      hdu.header.set('NAXIS',value=2,comment='',before=None,after=None)
      hdu.header.set('NAXIS1',value=self.data.shape[1],comment='',before=None,after=None)
      hdu.header.set('NAXIS2',value=self.data.shape[0],comment='',before=None,after=None)
      hdu.header.set('LC-DATE',value=self.local_date,comment='',before=None,after=None)
      hdu.header.set('LC-TIME',value=self.local_time,comment='',before=None,after=None)
      hdu.writeto(fname)
    else:
      imsave(fname,self.data,format='jpg',cmap='gray',origin='lower')
    return
#
