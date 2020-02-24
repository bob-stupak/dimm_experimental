#! /usr/bin/env python camera_sbig.py
#
import sys
sys.path.append('..')
from numpy import *
import sbigudrv as sbig
import time
import os.path

import camera_thread as cthread
from common_parms import *

#Program status boolean, <True> if program is running
#                        <False> if program is finished
progStat=True

#CAMERA_PARMS is a list of dictionary keys that define the necessary
# camera parameters.  These are for the SBIG camera in addition with 
#the general camera_thread.py CAMERA_PARMS
cthread.CAMERA_PARMS=[{'temp_setpoint':0.0},\
                      {'ccdtemp':-99.0},\
                      {'ambtemp':-99.0},\
                      {'power':0.0},\
                      {'cmd_setpoint':-5.0}]+cthread.CAMERA_PARMS
#SBIG_PARMS is a list of dictionary keys that define the necessary
# SBIG driver camera parameters.  
SBIG_PARMS=[{'start_exposure_parms':'sbig.StartExposureParams()'},\
            {'end_exposure_parms':'sbig.EndExposureParams()'},\
            {'query_cmdstat_parms':'sbig.QueryCommandStatusParams()'},\
            {'query_cmdresults_parms':'sbig.QueryCommandStatusResults()'},\
            {'start_readout_parms':'sbig.StartReadoutParams()'},\
            {'dump_line_parms':'sbig.DumpLinesParams()'},\
            {'readout_line_parms':'sbig.ReadoutLineParams()'},\
            {'end_readout_parms':'sbig.EndReadoutParams()'},\
            {'open_device_parms':'sbig.OpenDeviceParams()'},\
            {'ccd_temps_results':'sbig.QueryTemperatureStatusResults()'},\
            {'set_temp_reg_parms':'sbig.SetTemperatureRegulationParams()'},\
            {'query_usb_results':'sbig.QueryUSBResults()'},\
            {'link_stats':'sbig.GetLinkStatusResults()'},\
            {'ccd_info':'sbig.GetCCDInfoParams()'},\
            {'ccd_info_results':'sbig.GetCCDInfoResults0()'}]

class CameraThread(cthread.CameraThread):
  def __init__(self,name=None,session=None,camera_name='SBIG',sleeptime=CAM_THREAD_TIME,\
    prnt=False,log=False,devmode='-'):
    '''<__init__> constructs the CameraThread class with a name of <name>
       <sleeptime> is the update rate of the thread, <prnt> is 'True' for
       printing to the std.out for testing, <devmode> is the device type '-'
       for simulation, 's' for usb, 'h' for ethernet.
    '''
    self.device_mode=devmode
    '''@ivar: Determines the deviceType, '-' is simulation, 'h' is ip, and 's' is usb'''
    cthread.CameraThread.__init__(self,camera_name=camera_name,log=log,prnt=prnt)
    if name!=None: self.setName(name)
    else: self.setName('camera_thread')
    self.error_code=''
    '''@ivar: The camera driver error code'''
    #Define and set the SBIG driver parameters
    self._sbig_parmsList=SBIG_PARMS
    self.define_sbig_parms()
    self.open_camera()
    self.get_ccd_info()
    self.set_message('Camera Started and Opened')
    return
  def run(self):
    '''<run>
         the thread run(start) routine 
    '''
    self.thread_stat.set()
    while progStat==True and self.thread_stat.isSet():
      time.sleep(self.sleeptime)
      if progStat==True and self.take_exposure_stat.isSet():
        self.take_exposure()
      if progStat==True and self.read_out_stat.isSet() and not self.take_exposure_stat.isSet():
        self.do_readout()
      if progStat==True and not self.read_out_stat.isSet() \
        and not self.take_exposure_stat.isSet():
        self.get_temps_info()
      if progStat==True and self.auto_sequence_stat.isSet() \
        and not self.read_out_stat.isSet() and not self.take_exposure_stat.isSet():
        if self.sequence_count<self.sequence_total_number:
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
    return
  def define_sbig_parms(self):
    for each in self._sbig_parmsList:
      self.__dict__[each.keys()[0]]=eval(each[each.keys()[0]])
    # Sets device type
    if self.device_mode=='-':
      # For simulation deviceType can be set to sbig.DEV_NONE
      self.open_device_parms.deviceType=sbig.DEV_NONE
      self.ccd_temps_results.ccdSetpoint=cnvtemp(-5.0,mode='set')
      self.ccd_temps_results.ccdThermistor=cnvtemp(20.0,mode='set')
      self.ccd_temps_results.ambientThermistor=cnvtemp(25.0,mode='set')
    else:# self.device_mode=='s':
      # This will set the device type to sbig.DEV_USB for the USB port
      self.open_device_parms.deviceType=sbig.DEV_USB
    return
  def take_exposure(self):
    self.new_data_ready_stat.clear()
    self.exposure_count+=1
    self.get_time()
    exp_time=self.exptime
    smode=self.exposure_mode
    #print 'STARTING AN EXPOSURE: ',self.exposureStat.isSet(),self.gettime()
    self.get_time()
    self.set_message('%s %d ' % ('Starting Exposure number:',self.exposure_count))
    tres=100.0 #since exposure time is in hundredths of a second
    tics=int(floor(tres*exp_time+0.5)) #Sets exposure time in hundredths
    tmin=sbig.MIN_ST7_EXPOSURE  #The min exposure time for the ST7 is 120msec
    if tics<tmin: tics=tmin
    self.start_exposure_parms.ccd=sbig.CCD_IMAGING
    self.start_exposure_parms.exposureTime=tics #Exposure time in 0.01secs
    self.start_exposure_parms.abgState=0   #Anti-blooming OFF
    if smode==1: self.start_exposure_parms.openShutter=sbig.SC_OPEN_SHUTTER
    elif smode==0: self.start_exposure_parms.openShutter=sbig.SC_CLOSE_SHUTTER
    else: self.start_exposure_parms.openShutter=sbig.SC_LEAVE_SHUTTER
    self.error_code=sbig.SBIGUnivDrvCommand(sbig.CC_START_EXPOSURE,\
      self.start_exposure_parms,None)
    if (exp_time>0.1): time.sleep(exp_time+0.2)
    ###  NEED to understand the QUERY STATUS 
    self.end_exposure_parms.ccd=sbig.CCD_IMAGING
    self.error_code=sbig.SBIGUnivDrvCommand(sbig.CC_END_EXPOSURE,\
      self.end_exposure_parms,None)
    self.take_exposure_stat.clear()
    self.read_out_stat.set()
    #print 'ENDING THE EXPOSURE: ',self.take_exposure_stat.isSet(),self.message
    #self.get_time()
    self.set_message('%s %d ' % ('Ending Exposure number:',self.exposure_count))
    self.get_temps_info()
    return
  def do_readout(self):
    #print 'READING OUT CCD: ',self.read_out_stat.isSet(),self.message
    self.get_time()
    self.set_message('Reading out CCD')
    self.start_readout_parms.ccd=sbig.CCD_IMAGING
    self.start_readout_parms.top=0
    self.start_readout_parms.left=0
    self.start_readout_parms.height=510
    self.start_readout_parms.width=765
    self.readout_line_parms.ccd=sbig.CCD_IMAGING
    self.readout_line_parms.readoutMode=0
    self.readout_line_parms.pixelStart=0
    self.readout_line_parms.pixelLength=765
    self.end_readout_parms.ccd=sbig.CCD_IMAGING
    self.data=zeros((self.start_readout_parms.height,self.start_readout_parms.width),\
      dtype=ushort)
    if self.device_mode!='-':
      for i in range(self.start_readout_parms.height):
        self.error_code=sbig.SBIGUnivDrvCommand(sbig.CC_READOUT_LINE,\
          self.readout_line_parms,self.data[i,:])
    else: #Use simulation data.
      if self.exposure_mode==1:
        self.data=cthread.make_image_data(number=5)
      else:
        self.data=cthread.make_image_data(number=5)
    self.error_code=sbig.SBIGUnivDrvCommand(sbig.CC_END_READOUT,\
      self.end_readout_parms,None)
    self.data_queue.put(self.data)
    self.read_out_stat.clear()
    self.new_data_ready_stat.set()
    #print 'READOUT FINISHED: ',self.read_out_stat.isSet(),self.message
    self.get_time()
    self.set_message('%10.3f %10.3f, %s ' % (self.data.mean(),self.data.std(),'Readout Finished'))
    self.get_temps_info()
    return
  def open_camera(self):
#   self.get_time()
#   self.set_message('Reading out CCD')
    self.message='Device located on '+str(hex(self.open_device_parms.deviceType))
    # Open the driver
    self.error_code=sbig.SBIGUnivDrvCommand(sbig.CC_OPEN_DRIVER,None,None)
    if self.error_code!=sbig.CE_NO_ERROR:
      self.message='DRIVER open with ERROR '+str(self.error_code)
    else:
      self.message='DRIVER opened with response '+str(self.error_code)
    # Query USB port and state the number of camera, should be 1(sanity check)
#   self.error_code=sbig.SBIGUnivDrvCommand(sbig.CC_QUERY_USB,None,self.query_usb_results)
#   self.message='Number of Cameras Found'+str(self.query_usb_results.camerasFound)
    # Open the device
    self.error_code=sbig.SBIGUnivDrvCommand(sbig.CC_OPEN_DEVICE,\
      self.open_device_parms,None)
    if self.error_code!=sbig.CE_NO_ERROR:
      self.message='DEVICE open with ERROR '+str(self.error_code)
    else:
      self.message='DEVICE opened with response '+str(self.error_code)
    # Establish link
    self.error_code=sbig.SBIGUnivDrvCommand(sbig.CC_ESTABLISH_LINK,None,None)
    if self.error_code!=sbig.CE_NO_ERROR:
      self.message='LINK NOT established with ERROR '+str(self.error_code)
    else:
      self.message='LINK established with response '+str(self.error_code)
    # Check link status
    self.error_code=sbig.SBIGUnivDrvCommand(sbig.CC_GET_LINK_STATUS,None,self.link_stats)
    self.link_up=self.link_stats.linkEstablished
    return
  def close_camera(self):
    # Turn OFF temperature regulation
    self.temp_regulation(False)
    # Close device
    self.error_code=sbig.SBIGUnivDrvCommand(sbig.CC_CLOSE_DEVICE,None,None)
    if self.error_code!=sbig.CE_NO_ERROR:
      self.message='DEVICE close with ERROR '+str(self.error_code)
    else:
      self.message='DEVICE closed with response '+str(self.error_code)
    # Close Driver
    self.error_code=sbig.SBIGUnivDrvCommand(sbig.CC_CLOSE_DRIVER,None,None)
    if self.error_code!=sbig.CE_NO_ERROR:
      self.message='DRIVER close with ERROR '+str(self.error_code)
    else:
      self.message='DRIVER closed with response '+str(self.error_code)
    return
  def get_ccd_info(self):
    self.message='Getting CCD inforamation:'
    self.error_code=sbig.SBIGUnivDrvCommand(sbig.CC_GET_CCD_INFO,\
      self.ccd_info,self.ccd_info_results)
    self.message='firmware version:'+str(self.ccd_info_results.firmwareVersion)
    self.message='camera type:'+str(self.ccd_info_results.cameraType)
    self.message='camera name:'+str(self.ccd_info_results.name)
    self.camera_name=self.ccd_info_results.name
    self.message='readout modes:'+str(self.ccd_info_results.readoutModes)
    self.message='MODE:'+str(self.ccd_info_results.readoutInfo[0].mode)
    self.message='WIDTH:'+str(self.ccd_info_results.readoutInfo[0].width)
    self.width=self.ccd_info_results.readoutInfo[0].width
    self.message='HEIGHT:'+str(self.ccd_info_results.readoutInfo[0].height)
    self.height=self.ccd_info_results.readoutInfo[0].height
#   self.message='GAIN:'+hex(self.ccd_info_results.readoutInfo[0].gain)
#   self.gain=float(hex(self.ccd_info_results.readoutInfo[0].gain)[2:-1])/100.0
#   self.message='PIXEL WIDTH:'+hex(self.ccd_info_results.readoutInfo[0].pixel_width)
#   self.pixwidth=float(hex(self.ccd_info_results.readoutInfo[0].pixel_width)[2:-1])/100.0
#   self.message='PIXEL HEIGHT:'+hex(self.ccd_info_results.readoutInfo[0].pixel_height)
#   self.pixheight=float(\
#     hex(self.ccd_info_results.readoutInfo[0].pixel_height)[2:-1])/100.0
    return
  def temp_regulation(self,onstat):
    self.set_temp_reg_parms.regulation=int(onstat)
    self.set_temp_reg_parms.ccdSetpoint=cnvtemp(self.cmd_setpoint,mode='set')
    self.error_code=sbig.SBIGUnivDrvCommand(\
      sbig.CC_SET_TEMPERATURE_REGULATION,self.set_temp_reg_parms,None)
    return 
  def get_temps_info(self):
    try:
      self.error_code=sbig.SBIGUnivDrvCommand(sbig.CC_QUERY_TEMPERATURE_STATUS,\
        None,self.ccd_temps_results)
      self.treg_enabled=self.ccd_temps_results.enabled
      self.temp_setpoint=cnvtemp(self.ccd_temps_results.ccdSetpoint,mode='get',temp='ccd')
      self.power=self.ccd_temps_results.power
      self.ccdtemp=cnvtemp(self.ccd_temps_results.ccdThermistor,mode='get',temp='ccd')
      self.ambtemp=cnvtemp(self.ccd_temps_results.ambientThermistor,mode='get',temp='amb')
    except Exception: pass
    return
  def take_dark(self):
    self.exposure_mode=0
    self.take_exposure_stat.set()
    return
  def take_image(self):
    self.exposure_mode=1
    self.take_exposure_stat.set()
    return
  def take_bias(self):
    self.exposure_mode=0
    self.read_out_stat.set()
    return

def cnvtemp(value,mode='get',temp='ccd'):
  '''cnvtemp
     <value>  is the value, <mode> 'get' or 'set', <temp> 'ccd' or 'amb'
     will convert AD units for ST-7 temperature depending on whether setting 
     or getting temperature, 'set' only works for 'ccd'
  '''
  T_o=25.0
  MAX_AD=4096.0
  R_RATIO_ccd=2.57
  R_BRIDGE_ccd=10.0
  DT_ccd=25.0
  R_o=3.0
  R_RATIO_ambient=7.791
  R_BRIDGE_ambient=3.0
  DT_ambient=45.0
  if mode=='get' and temp=='amb':
    r=R_BRIDGE_ambient/(MAX_AD/value-1.0)
    t=T_o-DT_ambient*(log(r/R_o)/log(R_RATIO_ambient))
  elif mode=='get' and temp=='ccd':
    r=R_BRIDGE_ccd/(MAX_AD/value-1.0)
    t=T_o-DT_ccd*(log(r/R_o)/log(R_RATIO_ccd))
  elif mode=='set' and temp=='ccd':
    r=R_o*exp((log(R_RATIO_ccd)*(T_o-value))/DT_ccd)
    t=MAX_AD/(R_BRIDGE_ccd/r+1.0)
    t=int(t)
    if t<0: t=0
    if t>MAX_AD-1: t=MAX_AD-1
  else:
    r,t=3.0,-999.0
  return t


