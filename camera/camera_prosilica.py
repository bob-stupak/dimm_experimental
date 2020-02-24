# /usr/bin/env python camera_prosilica.py
#
import sys
sys.path.append('..')
from numpy import *
import pymba
from pymba.vimbaexception import VimbaException
import threading
import time
import os.path
import pyfits
import platform

import camera_thread as cthread
from common_parms import *

#Program status boolean, <True> if program is running
#                        <False> if program is finished
progStat=True

#GIGE_PARMS is a dictionary of keys that specify the camera functions and info
# See the GigE_Features_Reference.pdf for further information about these settings.
#####  This dictionary is NOT used in the code.  This may be used for something in the future.
GIGE_PARMS={'DeviceModelName':'',\
            'SensorBits':0,\
            'SensorHeight':0,\
            'SensorWidth':0,\
            'SensorType':0,\
            'HeightMax':0,\
            'WidthMax':0,\
            'AcquisitionMode':'SingleFrame',\
            #or 'Continuous' or others
            #The following need to be set as such for <1GByte network, see pg83
            'GevSCPSPacketSize':1500,\
            'GVSPPacketSize':1500,\
            'BandwidthControlMode':'StreamBytesPerSecond',\
            'StreamBytesPerSecond':3500000,\
            'PixelFormat':'Mono14',\
            #or 'Mono8' 8bit, 'Mono14' 14bit, or others, see pg101 
            'TriggerMode':'Off',\
            'TriggerSelector':'FrameStart',\
            'TriggerSource':'Freerun',\
            'ExposureAuto':'Off',\
            'GainAuto':'Off',\
            'ExposureTimeAbs':0.1*1.0e6,\
            'GainRaw':0,\
            'Height':0,\
            'Width':0,\
            #Both Height and Width are defined below from the CAMERA_PARMS defined in camera_thread.py
            'OffsetX':0,\
            'OffsetY':0,\
            'ImageSize':0,\
            'BinningHorizontal':1,\
            'BinningVertical':1}

def testt(camera):
  for each in GIGE_PARMS.keys():
    print '%s=%s' % (each.ljust(25),str(getattr(camera,each)))
  return

def return_vimba(num=1):
  vimba=pymba.Vimba()
  vimba.shutdown()  # To assure that there are no other sessions started
  vimba.startup()
  system=vimba.getSystem()
  if system.GeVTLIsPresent:
    system.runFeatureCommand('GeVDiscoveryAllOnce')
  cnt=0
  cam_list=vimba.getCameraIds()
  while cnt<600 and len(cam_list)<num:
    del system
    vimba.shutdown()  # To close the Vimba object and restart it
    time.sleep(1.0)
    vimba.startup()
    system=vimba.getSystem()
    if system.GeVTLIsPresent:
      #print system.GeVTLIsPresent,system.runFeatureCommand('GeVDiscoveryAllOnce')
      system.runFeatureCommand('GeVDiscoveryAllOnce')
    cam_list=vimba.getCameraIds()
    #print 'Waiting...', cnt, len(cam_list),num,cam_list
    cnt+=1
  return vimba

class CameraThread(cthread.CameraThread):
  camera_count=0
  def __init__(self,session=None,name=None,camera_name='GX2750',sleeptime=CAM_THREAD_TIME,prnt=False,log=False):
    cthread.CameraThread.__init__(self,camera_name=camera_name,log=log,prnt=prnt)
    if session==None:
      self.session_driver=return_vimba()
    else:
      self.session_driver=session
    if name!=None: self.setName(name)
    else: self.setName('camera_thread')
    self.camera=self.session_driver.getCamera(self.device_name)
    self.camera.openCamera()
    time.sleep(0.2)
    self.frame=self.camera.getFrame()
    self.init_gige_parms()
    self.frame.announceFrame()
    self.set_message('Camera Started and Opened')
    CameraThread.camera_count+=1
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
    ss=ss+'\n'
    ss=ss+'Class, Chip, Camera, CameraMax, Frame\n'
    ss=ss+'Width: %d, %d, %d,%d, %d\n' % (self.width,self.chip_width,self.camera.Width,self.camera.WidthMax,\
      self.frame.width)
    ss=ss+'OffsetX: %d, %d\n' % (self.offset_x,self.camera.OffsetX)
    ss=ss+'Binning X: %d, %d\n' % (self.binning_x,self.camera.BinningHorizontal)
    ss=ss+'\n'
    ss=ss+'Height: %d, %d, %d,%d, %d\n' % (self.height,self.chip_height,self.camera.Height,self.camera.HeightMax,\
      self.frame.height)
    ss=ss+'OffsetY: %d, %d\n' % (self.offset_y,self.camera.OffsetY)
    ss=ss+'Binning Y: %d, %d\n' % (self.binning_y,self.camera.BinningVertical)
    return ss
  def init_gige_parms(self):
    self.camera.GevSCPSPacketSize=1500
    self.camera.GVSPPacketSize=1500
    self.camera.BandwidthControlMode='StreamBytesPerSecond'
    self.camera.StreamBytesPerSecond=7500000
    self.camera.PixelFormat='Mono14'
    self.camera.AcquisitionMode='SingleFrame'
    self.camera.TriggerMode='Off'
    self.camera.TriggerSelector='FrameStart'
    self.camera.TriggerSource='Freerun'
    self.camera.ExposureAuto='Off'
    self.camera.ExposureMode='Timed'
    self.camera.GainAuto='Off'
    self.camera.ExposureTimeAbs=self.exptime*1.0e6
    self.camera.GainRaw=int(self.gain)
    self.camera.BinningHorizontal=1
    self.camera.BinningVertical=1
    self.camera.OffsetY=0
    self.camera.OffsetX=0
    self.camera.Height=self.camera.HeightMax
    self.frame.height=self.camera.HeightMax
    self.camera.Width=self.camera.WidthMax
    self.frame.width=self.camera.WidthMax
#   self.set_binning(vert=self.camera.BinningVertical,hor=self.camera.BinningHorizontal)
    self.set_binning()
    time.sleep(0.2)
    return
  def init_roi(self):
    self.set_roi(h=self.chip_height,w=self.chip_width,offx=0,offy=0)
    return
  def close_camera(self):
    self.init_gige_parms()
    self.set_message('Closeing Camera')
    self.thread_stat.clear()
    self.take_exposure_stat.clear()
    self.auto_sequence_stat.clear()
    time.sleep(0.1)
    try: self.camera.runFeatureCommand('AcquisitionAbort')
    except Exception as err:
      self.set_message('close_camera ERROR: %s' % (err))
      pass
    self.camera.revokeAllFrames()
    time.sleep(0.5)
    self.camera.closeCamera()
    time.sleep(0.5)
    if CameraThread.camera_count<=1:
      try: self.session_driver.shutdown()
      except Exception as err:
        self.set_message('close_camera ERROR: %s' % (err))
        pass
      finally: pass
    else:
      CameraThread.camera_count-=1
    return
  def take_exposure(self):
    #capture a camera image
    self.exposure_count+=1
    #self.take_exposure_stat.clear()
    self.camera.ExposureTimeAbs=self.exptime*1.0e6
    self.camera.GainRaw=int(self.gain)
    self.new_data_ready_stat.clear()
    self.get_time()
    #print 'Starting capture for exposure %d' % (self.exposure_count)
    try:
      self.camera.startCapture()
      try:
        ######  Used after power up for some reason the first exposure after power flags a pointer error
        ######  This re-announces the frame to allow the program to continue.
        ######  Maybe a better way of doing this in the future, but this works for now.
        #print 'Queue frame capture for exposure %d' % (self.exposure_count)
        self.frame.queueFrameCapture()
      except VimbaException as err:
        self.set_message('take_exposure: Queue Frame Capture: Vimba ERROR: %s' % (err))
        #print 'ERROR: Announcing fram again and re-Queuing frame capture for exposure %d' % (self.exposure_count)
        self.frame.announceFrame()
        self.frame.queueFrameCapture()
      #print 'Acquisition starting for exposure %d' % (self.exposure_count)
      self.camera.runFeatureCommand('AcquisitionStart')
      #print 'Stopping acquisition for exposure %d' % (self.exposure_count)
      self.camera.runFeatureCommand('AcquisitionStop')
      #print 'Waiting frame capture for exposure %d' % (self.exposure_count)
      self.frame.waitFrameCapture(500)
#2nov #print 'Stopping acquisition for exposure %d' % (self.exposure_count)
#2nov self.camera.runFeatureCommand('AcquisitionStop')
      #get image data ...
      try:
        #print 'Setting <self.data> to buffer for exposure %d' % (self.exposure_count)
        self.data=ndarray(buffer=self.frame.getBufferByteData(),
              dtype=uint16,shape=(self.frame.height,self.frame.width))
      except TypeError as err:
        self.set_message('take_exposure ERROR: Data TypeError: %s' % (err))
        #print 'TypeError <junk> for data for exposure %d' % (self.exposure_count)
        junk=self.frame.getBufferByteData()
        self.frame=self.camera.getFrame()
      #clean up after capture
      #print 'Flushing capture queue for exposure %d' % (self.exposure_count)
      self.camera.flushCaptureQueue()
#     #print 'Revoking all frames for exposure %d' % (self.exposure_count)
#     self.camera.revokeAllFrames()
      #print 'Ending capture for exposure %d' % (self.exposure_count)
      self.camera.endCapture()
      #print 'Revoking all frames for exposure %d' % (self.exposure_count)
      self.camera.revokeAllFrames()
      self.set_message('%s:%d' % ('Taking exposure, count:',self.exposure_count))
      cpdata=copy(self.data)
      #print 'Putting copied data in queue for exposure %d' % (self.exposure_count)
      self.data_queue.put(cpdata)
      self.set_message('mean=%7.3f std=%7.3f mean value' % (cpdata.mean(),cpdata.std()))
      #print 'Clearing events for exposure %d' % (self.exposure_count)
    except VimbaException as err:
      self.set_message('take_exposure: Capture Error: Vimba ERROR: %s' % (err))
      try:
#       self.camera.revokeAllFrames()
        self.camera.endCapture()
        self.camera.revokeAllFrames()
      except VimbaException as err:
        self.set_message('take_exposure: Revoke and End Capture Error: Vimba ERROR: %s' % (err))
        pass
      except Exception as err:
        self.set_message('take_exposure: Revoke and End Capture Error: ERROR: %s' % (err))
        pass
    except Exception as err:
      self.set_message('take_exposure: Capture Error: ERROR: %s' % (err))
      pass
    self.new_data_ready_stat.set()
    self.take_exposure_stat.clear()
    return
  def set_binning(self,hor=1,vert=1):
    self.exposure_lock.acquire()
    time.sleep(0.05)  #Added 29 Jan 2020
    if hor>4: hor=4
    if hor<1: hor=1
    if vert>4: vert=4
    if vert<1: vert=1
    old_x,old_y=self.binning_x,self.binning_y
    self.set_message('Binning Set to hor=%d vert=%d' % (hor,vert))
    self.camera.BinningHorizontal=hor
    self.camera.BinningVertical=vert
    self.binning_x=self.camera.BinningHorizontal
    self.binning_y=self.camera.BinningVertical
    self.chip_height=self.camera.HeightMax
    self.chip_width=self.camera.WidthMax
    time.sleep(0.05)  #Added 29 Jan 2020
    self.exposure_lock.release()
    self.set_roi(h=self.height*old_y/vert,w=self.width*old_x/hor,offx=self.offset_x*old_x/hor,
      offy=self.offset_y*old_y/vert)
    return
  def set_roi(self,h=None,w=None,offx=None,offy=None):
    self.exposure_lock.acquire()
    time.sleep(0.05)  #Added 29 Jan 2020
    if not h and not w and not offx and not offy:
      offx,offy=0,0
      self.chip_height=self.camera.HeightMax
      self.chip_width=self.camera.WidthMax
      h,w=self.chip_height,self.chip_width
    else: pass
    self.set_message('ROI set h=%s, w=%s, offx=%s, offy=%s' % (str(h),str(w),str(offx),str(offy)))
    self.width=min(w,self.chip_width)
    self.height=min(h,self.chip_height)
    self.offset_x=max(min(offx,self.chip_width-self.width),0)
    self.offset_y=max(min(offy,self.chip_height-self.height),0)
    self.set_message('ROI set h=%s, w=%s, offx=%s, offy=%s' % (str(self.height),str(self.width),\
      str(self.offset_x),str(self.offset_y)))
    #To assure that the camera offsets do not exceed the chip width or height
    time.sleep(0.05)  #Added 29 Jan 2020
    if self.camera.OffsetX+self.width>self.chip_width:
      self.camera.OffsetX=self.offset_x
      self.camera.Width=self.width
    else:
      self.camera.Width=self.width
      self.camera.OffsetX=self.offset_x
    if self.camera.OffsetY+self.height>self.chip_height:
      self.camera.OffsetY=self.offset_y
      self.camera.Height=self.height
    else:
      self.camera.Height=self.height
      self.camera.OffsetY=self.offset_y
    self.frame.width=self.width
    self.frame.height=self.height
    self.exposure_lock.release()
    return
