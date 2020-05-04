#! /usr/bin/env python new_camera_thread.py
#
#

import sys
sys.path.append('..')
from numpy import *
from Queue import Queue
import threading
import time,datetime
import os
import os.path
import pyfits
import platform

import scipy.ndimage as ndimage
import scipy.ndimage.filters as filters
from scipy.ndimage.interpolation import shift
from pylab import imsave

from common_parms import *

progStat=True

#The 'xxx' in the variables below are replaced to define definitions from the camera names
CAMERA_PARMS=[{'exptime':'xxxEXP_TIME'},\
              {'exposure_mode':1},\
              {'exposure_count':0},\
              {'auto_count':0},\
              {'sequence_count':0},\
              {'sequence_total_number':'xxxSEQ_TOTAL_NUM'},\
              #'sequence_total_number':'SEQ_TOTAL_NUM'},\
              {'auto_delay':'xxxSEQ_DELAY'},\
              {'seq_exp_list':'xxxSEQ_EXPTIMES'},\
              {'camera_name':'xxxNAME'},\
              {'device_name':'xxxDEVICENAME'},\
              {'chip_width':'xxxX'},\
              {'chip_height':'xxxY'},\
              {'width':'xxxX'},\
              {'height':'xxxY'},\
              {'gain':'xxxGAIN'},\
              {'camera_bits':'xxxBIT'},\
              {'pixwidth':'xxxX_PIXSIZE'},\
              {'pixheight':'xxxY_PIXSIZE'},\
              {'binning_x':'xxxX_BINNING'},\
              {'binning_y':'xxxY_BINNING'},\
              {'offset_x':0},\
              {'offset_y':0},\
              {'data':'zeros((xxxY,xxxX))'},\
              {'local_date':'0'},\
              {'local_time':'0'}]

class CameraThread(threading.Thread):
  ''' <CameraThread> inherits the threading.Thread class to be used
      to run a camera in the background.  This is a generic class with generic methods, some
      of which should be overwritten to accommodate a specific camera.
      If used by itself, the camera will be a simulated camera using the <make_image_data> function
      to generate image data.
  '''
  def __init__(self,name='camera_thread',camera_name='CAMERA',sleeptime=CAM_THREAD_TIME,log=False,prnt=False,**kargs):
    ''' <__init__> constructs the CameraThread class with a name of 
        <name> name of thread
        <camera_name> name of the camera
        <sleeptime> is the update rate of the thread, 
        <log> is 'True' for logging messages to file
        <prnt> is 'True' for printing to the std.out for testing.
        <kargs> is left over for future expansions
    '''
    threading.Thread.__init__(self)
    self.camera_name=camera_name
    self.setName(name)
    # The following are a set of events to be flagged for camera operations
    self.thread_stat=threading.Event()
    ''' @ivar: Status of the thread, can be used to pause the thread action'''
    self.thread_stat.set()
    self.exposure_lock=threading.Lock()
    ''' @ivar: Lock used to lock the exposure process until it is done'''
    self.take_exposure_stat=threading.Event()
    ''' @ivar: Status of an exposure, when set true starts exposure, when false
        no exposure is occurring.  the <wait> command will block function until a new 
        exposure starts(the flag is set).
    '''
    self.take_exposure_stat.clear()
    self.read_out_stat=threading.Event()
    ''' @ivar: Status of a readout, when set true will start a readout, when false
        no readout is occurring.  the <wait> command will block a function until
        a new readout flag is set.
    '''
    self.read_out_stat.clear()
    self.new_data_ready_stat=threading.Event()
    ''' @ivar: Indicates the status of the data, when set true new data is present, 
        when false no new data is present.  the <wait> command will block a function until
        new data is ready.  This flag is used for processing the data.
    '''
    self.new_data_ready_stat.set()
    self.auto_sequence_stat=threading.Event()
    ''' @ivar: Is an event that indicates continuous running, when set true will auto
        run a repeating sequence of exposure times given by the variable <self.seq_exp_list>
        (see below), when set false no continuous running.  the <wait> command will block
        a function until the camera is continuously running.
    '''
    self.auto_sequence_stat.clear()
    # The following are the rest of the instance variable definitions
    self.session_driver=None
    ''' @ivar: This defines the session(for prosilica) or driver for other cameras.
        This variable should be overwritten for the specific camera.
    '''
    self.sleeptime=sleeptime
    ''' @ivar: The defined sleeptime for cycling the thread
    '''
    self.message=''
    ''' @ivar: A message variable
    '''
    self._parmsList=CAMERA_PARMS
    self.defineparms()
    self.data_queue=Queue()
    ''' @ivar: A data queue to stash the data as it comes into the camera thread
    '''
    self.data_queue.maxsize=100
#   self.auto_delay=SEQ_DELAY
#   ''' @ivar: The delay time between exposures in auto_sequence mode.
#   '''
#   self.seq_exp_list=SEQ_EXPTIMES
#   ''' @ivar: A list of exposure times to be sequenced if continuously running.  Note
#       this can be one exposure time in a list also.
#   '''
    self.get_time()
    self.stdout_flag=prnt
    ''' @ivar: A general boolean to indicate whether or not to print to stdoutthe camera parms to file.
    '''
####
    subdir1=os.path.join(LOG_DIR,time.strftime('%b%Y'))
    fullpath=os.path.join(subdir1,time.strftime('%B%d'))
    if not os.path.exists(fullpath): os.makedirs(fullpath)
    self.logfile_name=os.path.join(fullpath,CAM_LOGBASENAME+'-'+self.camera_name+'.'+time.strftime('%m.%d.%Y'))
    '''@ivar: Log filename '''
####
    #self.logfile_name=LOG_DIR+CAM_LOGBASENAME+'-'+self.camera_name+'.'+self.local_date.replace('/','.')
    #''' @ivar: The logfile name given in the common_parms.py file in the home directory.
    #'''
    self.logging_flag=log
    ''' @ivar: A general boolean to indicate whether or not to log the camera parms to file.
    '''
    self.set_message('Camera Started and Opened')
    self.shift=False ####Only for simulation MODE
    self.movement=(0,0)  ####Only for simulation MODE
    self.orig_data=None  ####ONLY FOR SIMULATION MODE
    self.init_data=None  ####YET another ONLY FOR SIMULATION MODE
    self.change_data=False  ####ONLY FOR SIMULATION MODE
    return
  def __repr__(self):
    ''' <__repr__>
        Expresses the camera thread information
    '''
    ss='\n'
    ss=ss+'<CameraThread> class is Alive? %s\n' % (self.isAlive())
    ss=ss+'\n'
    ss=ss+'%s %s\n' % (self.local_time,self.local_date)
    ss=ss+'\n'
    ss=ss+'Name: %s\n' % (self.camera_name)
    ss=ss+'Size: x,y %dx%d  pixels\n' % (self.width,self.height)
    ss=ss+'Pixel: x,y %7.3fx%7.3f um\n' % (self.pixwidth,self.pixheight)
    ss=ss+'\n'
    ss=ss+'Exposure Count: %d\n' % (self.exposure_count)
    ss=ss+'Exposure Time: %7.3f\n' % (self.exptime)
    return ss
  def run(self):
    ''' <run>
        This is the thread run(start) routine
        Note: Two conditions must be met to take data.
          1) <new_data_ready_stat> must be false or cleared
          2) <take_exposure_stat> must be true or set
    '''
    self.thread_stat.set()
    while progStat==True and self.thread_stat.isSet():
      time.sleep(self.sleeptime)
      if self.take_exposure_stat.isSet():
        self.exposure_lock.acquire()
        self.take_exposure()
        self.exposure_lock.release()
      if self.auto_sequence_stat.isSet() and self.sequence_count<self.sequence_total_number:
        time.sleep(self.auto_delay)
        if self.auto_count>=len(self.seq_exp_list): 
          self.auto_count=0
          self.sequence_count+=1
        self.exptime=self.seq_exp_list[self.auto_count]
        self.take_exposure_stat.set()
        self.auto_count+=1
      else:
        self.auto_sequence_stat.clear()
        self.sequence_count=0
    self.set_message('Camera Thread Stopped!!!!')
    return
  def defineparms(self):
    ''' <defineparms>
        Sets the defined attributes from the CAMERA_PARMS dictionary.  Used as an attempt
        to more readily/easily set up camera attribute variables.  This is based on the name
        of the camera.
    '''
    if self.camera_name!='CAMERA':
      name='CAMERA_'+self.camera_name+'_'
    else: 
      name='CAMERA_'
    for each in self._parmsList:
      if type(each[each.keys()[0]])!=str:
        self.__dict__[each.keys()[0]]=each[each.keys()[0]]
      else:
        self.__dict__[each.keys()[0]]=eval(each[each.keys()[0]].replace('xxx',name))
    return
  def take_exposure(self):
    ''' <take_exposure>
        Used to set up exposure parameters and update counts.  This method should be overwritten
        to accommodate a specific camera, or if left unchanged will create simulated images of 
        CAMERA_X, CAMERA_Y size.
    '''
    self.set_message('Taking exposure number %d' % (self.exposure_count))
    #<make_image_data> will create simulation data
    time.sleep(self.exptime)
    if self.exposure_count==0 or self.change_data:
      self.data=make_image_data(number=2)
      #self.data=make_image_data(number=15)
      self.orig_data=self.data
      self.init_data=self.data
    else:
      if self.shift:
        self.data=shift_image(self.data,dr=self.movement[0],dtheta=self.movement[1])
      else:
        self.data=add_noise(self.orig_data)
    self.data_queue.put(self.data)
    self.exposure_count+=1
    self.change_data=False
    self.take_exposure_stat.clear()
    self.do_readout()
    return
  def acquire_image(self):
    ''' <acquire_image>
        Used only to set the proper flags to start an exposure
    '''
    self.new_data_ready_stat.clear()
    self.take_exposure_stat.set()
    self.new_data_ready_stat.wait()
    return
  def do_readout(self):
    ''' <do_readout>
        Used to readout or acquire data from camera.  This method can be overwritten
        to accommodate a specific camera
    '''
    self.set_message('Doing Readout')
    self.new_data_ready_stat.set()
    return
  def temp_regulation(self,onstat):
    ''' <temp_regulation>
        This method is meant to be overwritten for the specific camera
    '''
    return
  def set_binning(self,hor=1,vert=1):
    ''' <set_binning>
        This method is meant to be overwritten for the specific camera
    '''
    if hor>4: hor=4
    if hor<1: hor=1
    if vert>4: vert=4
    if vert<1: vert=1
    self.binning_x=hor
    self.binning_y=vert
    return
  def set_roi(self,h=None,w=None,offx=None,offy=None):
    ''' <set_roi>
        This method is meant to be overwritten for the specific camera
    '''
    if not h and not w and not offx and not offy:
      offx,offy=0,0
      h,w=self.chip_height,self.chip_width
      self.data=self.init_data
    else: pass
    self.set_message('ROI set h=%s, w=%s, offx=%s, offy=%s' % (str(h),str(w),str(offx),str(offy)))
    self.width=min(w,self.chip_width)
    self.height=min(h,self.chip_height)
    self.offset_x=max(min(offx,self.chip_width-self.width),0)
    self.offset_y=max(min(offy,self.chip_height-self.height),0)
    self.set_message('ROI set h=%s, w=%s, offx=%s, offy=%s' % (str(self.height),str(self.width),\
      str(self.offset_x),str(self.offset_y)))
    try:
      self.data=self.data[self.offset_y:self.offset_y+self.height,self.offset_x:self.offset_x+self.width]
      self.orig_data=self.data
    except TypeError as err:
      self.set_message('CAMERA THREAD ERROR: %s' % (err))
      pass
    return
  def get_time(self):
    ''' <get_time>
        A standard formatted time routine, format given in the common_parms.py file
    '''
#   self.local_date,self.local_time=time.strftime(DTIME_FORMAT).split(',')
    dt_string=datetime.datetime.strftime(datetime.datetime.now(),DTIME_FORMAT_FLT)[:-4]
    self.local_date,self.local_time=dt_string.split(',')
    return
  def close_camera(self):
    ''' <close_camera>
        This method is meant to be overwritten for the specific camera
    '''
    return
  def close(self):
    ''' <close>
        Will reset all of the events, close the camera and message to log
    '''
    self.auto_sequence_stat.clear()
    self.take_exposure_stat.clear()
    self.read_out_stat.clear()
    self.new_data_ready_stat.clear()
    self.set_message('Closing Camera and Exiting')
    self.close_camera()
    self.thread_stat.clear()
    progStat=False
    return
  def set_message(self,msg):
    ''' <set_message>
        Will set the message for display or for whatever else the message is 
        to be used, and will log to file if the <self.logging_flag> is True
    '''
    self.get_time()
    self.message='%s %s:  %s' % (self.local_date,self.local_time,msg)
    if self.logging_flag: self.write_to_log(self.message)
    if self.stdout_flag: sys.stdout.write('Message %s\n' % self.message)
    return
  def write_to_log(self,arg):
    ''' <write_to_log>
        Will write the arg to the logfile
    '''
    cur_date=self.local_date.replace('/','.')
    subdir1=os.path.join(LOG_DIR,time.strftime('%b%Y'))
    fullpath=os.path.join(subdir1,time.strftime('%B%d'))
    if not os.path.exists(fullpath): os.makedirs(fullpath)
    if cur_date not in self.logfile_name:
      self.logfile_name=os.path.join(fullpath,CAM_LOGBASENAME+'-'+self.camera_name+'.'+cur_date)
    #if cur_date not in self.logfile_name:
    #  self.logfile_name=LOG_DIR+CAM_LOGBASENAME+'-'+self.camera_name+'.'+cur_date
    if os.path.exists(self.logfile_name): appendfile='a'
    else: appendfile='w'
    fp=open(self.logfile_name,appendfile)
    fp.write(arg+'\n')
    fp.close()
    return
  def save_image(self,fname=None,fmt='fits'):
    ''' <save_image>
        A generic save routine to save the image to either a 'fits' file or 'jpg' 
        depending on fmt.
    '''
    self.get_time()
    if fname==None:
      fname=IMG_DIR+'test'
      if not self.exposure_mode:
        fname=fname+'_dark_'
      fname=fname+self.local_time.replace(':','')+self.local_date.replace('/','_')+'.fits'
    else:
      fname=IMG_DIR+fname+'.'+fmt
    if fmt=='fits':
      hdu=pyfits.PrimaryHDU(self.data)
      hdu.header.set('SIMPLE',value=True,comment='',before=None,after=None)
      hdu.header.set('BITPIX',value=CAMERA_BIT,comment='',before=None,after=None)
      hdu.header.set('NAXIS',value=2,comment='',before=None,after=None)
#     hdu.header.set('NAXIS1',value=CAMERA_X,comment='',before=None,after=None)
#     hdu.header.set('NAXIS2',value=CAMERA_Y,comment='',before=None,after=None)
      hdu.header.set('NAXIS1',value=self.data.shape[1],comment='',before=None,after=None)
      hdu.header.set('NAXIS2',value=self.data.shape[0],comment='',before=None,after=None)
      hdu.header.set('EXPTIME',value=self.exptime,comment='',before=None,after=None)
      hdu.header.set('EGAIN',value=self.gain,comment='',before=None,after=None)
      hdu.header.set('LC-DATE',value=self.local_date,comment='',before=None,after=None)
      hdu.header.set('LC-TIME',value=self.local_time,comment='',before=None,after=None)
      hdu.writeto(fname)
    else:
      imsave(fname,self.data,format='jpg')
    return
#
# The following is for Simulation Data
#
def make_image_data(xsize=CAMERA_X,ysize=CAMERA_Y,height=65536.0,minimum=0.0,number=20):
  '''
    Will return an image with random gaussians.  Stolen from some python website.
  '''
  def g(X,Y,xo,yo,amp=100,sigmax=4,sigmay=4):
    return  amp*exp(-(X-xo)**2/(2*sigmax**2) - (Y-yo)**2/(2*sigmay**2))
  x=linspace(0,xsize,xsize)
  y=linspace(0,ysize,ysize)
  X,Y=meshgrid(x,y)
  Z=X*0
  if number==2:
    for xo,yo in array([xsize/2.0,ysize/2.0])+array([xsize/3.5,ysize/3.5])*random.rand(2,2):
      widthx=5+random.randn(1)
      widthy=5+random.randn(1)
      Z+=g(X,Y,xo,yo,amp=height*random.rand(),sigmax=widthx,sigmay=widthy)
  else:
    for xo,yo in (xsize+ysize)/2.0*random.rand(number,2):
      widthx=5+random.randn(1)
      widthy=5+random.randn(1)
      Z+=g(X,Y,xo,yo,amp=height*random.rand(),sigmax=widthx,sigmay=widthy)
  Z=Z+minimum
  Z[Z<0]=0
  return Z

def add_noise(data):
  '''
    Will take the grid data and add noise and filter, rotate, and shift it.  Used to simulate noisy image.
  '''
  mm=copy(data)
  background=median(mm)
  mm2=ndimage.gaussian_filter(mm,random.normal(scale=10.0),cval=background)
  background=mean(mm2)
  newdata=ndimage.rotate(mm2,random.normal(scale=0.5),cval=background)
  background=median(newdata)
  newdata=shift(newdata,(random.random(2)-0.5)*25.0,cval=background)  # will shift data by dx and dy
  newdata[newdata<0]=0
  return newdata

def shift_image(data,dx=0,dy=0,dr=1111.0,dtheta=1111.0):
  '''
    Will take the grid data and shift it by dx,dy or dr,dtheta in pixels.  Used to simulate moving image.
  '''
  if dr!=1111.0 and dtheta!=1111.0:
    dx=dr*cos(deg2rad(dtheta))
    dy=dr*sin(deg2rad(dtheta))
  background=median(data)
  newdata=shift(data,(dy,dx),cval=background)
  return newdata

