#! /usr/bin/env python manager_gui.py
#
import threading
#
import sys

from Tkinter import *
import Pmw as pmw
import guis.frame_gui as fg
import guis.imagecanvasgui as icanv
import sourceprocs.source_cat_gui as scgui
import manager_thread as mthread

from numpy import any,vstack
from telescope.telescope_gui import TelescopeGUI
from sourceprocs.source_cat_gui import CatFrame
from weather.weather_gui import WeatherClientGUI
from camera.camera_gui import CameraGUI

from imageprocs.image_proc_gui import ImageProcGUI
from dome.dome_gui import DomeGUI
from miscutilities.ippower_cnt_gui import PowerStatusGUI
from miscutilities.reset_moxa import reset_moxa

from common_parms import *

class TelescopeStatusGUI(fg.FrameGUI):
  def __init__(self,parent=None,col=0,row=0,colspan=1,rowspan=3):
    self.parent=parent
    self.root=parent.interior()
    self.tele_thread=parent.thread_manager.telescope
    self.source_thread=parent.thread_manager.starcat
    self.dome_thread=parent.thread_manager.dome
    self._mesBarList=[['dateStat','Date',15,(0,1,3,1,'nsew')],\
                      ['timeStat','Time',15,(0,2,3,1,'nsew')],\
                      ['lstimeStat','LST Time',15,(0,3,3,1,'nsew')],\
                      ['sourceStat','Source',15,(0,4,3,1,'nsew')],\
                      ['elStat','Elevation',15,(0,5,3,1,'nsew')],\
                      ['azStat','Azimuth',15,(0,6,3,1,'nsew')],\
                      ['dcStat','Declination',15,(0,7,3,1,'nsew')],\
                      ['raStat','Right Ascension',15,(0,8,3,1,'nsew')],\
                      ['elCmdStat','Cmd Elv/Dec',15,(0,9,3,1,'nsew')],\
                      ['azCmdStat','Cmd Ra/Az',15,(0,10,3,1,'nsew')],\
                      ['cdCmdStat','Cmd Coords',15,(0,11,3,1,'nsew')],\
                      ['teleTrackStat','Tracking',15,(0,22,3,1,'nsew')]]
#                     ['pierStat','Pier Side',5,(0,13,3,1,'nsew')],\
#   self._emessList=[['az_el_status','Azimuth/Elevation',\
#                    [['azimuth_status','Azimuth',''],\
#                     ['elevation_status','Elevation','']],(0,11,3,1,'nsew')]]
    self._checkList=[['onsourceStat','On Source:','horizontal','radiobutton',\
                      ['On','Off'],None,(0,19,3,1,'nsew')],\
                     ['domeStat','Dome Status:','horizontal','radiobutton',\
                      ['Opened','Mixed','Closed'],None,(0,20,3,1,'nsew')]]
    fg.FrameGUI.__init__(self,root=self.root,name='Telescope Status',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    self.check_update()
    return
  def check_update(self):
    self.timeStat.message('state','%s' % self.tele_thread.localtime[2])
    self.dateStat.message('state','%s' % self.tele_thread.localdate[2])
    self.sourceStat.message('state','%s' % self.source_thread.source.name)
    self.lstimeStat.message('state','%s' % self.tele_thread.sidrtime[2])
    self.elStat.message('state','%s' % self.tele_thread.elevation[2])
    self.azStat.message('state','%s' % self.tele_thread.azimuth[2])
    self.dcStat.message('state','%s' % self.tele_thread.declination[2])
    self.raStat.message('state','%s' % self.tele_thread.rightasc[2])
    self.elCmdStat.message('state','%s' % self.tele_thread.cmdposition[1])
    self.azCmdStat.message('state','%s' % self.tele_thread.cmdposition[0])
    self.cdCmdStat.message('state','%s' % self.tele_thread.cmdposition[2])
#   self.pierStat.message('state','%s' % self.tele_thread.pierstat[2])
    self.get_track_speed()
    self.get_on_src_stat()
    self.get_dome_stat()
    self.after(15,self.check_update)
    return
  def get_on_src_stat(self):
    if self.tele_thread.on_source_stat.isSet():
      self.onsourceStat.setvalue('On')
    else:
      self.onsourceStat.setvalue('Off')
    return
  def get_dome_stat(self):
    try: self.domeStat.setvalue(self.dome_thread.dome_status)
    except Exception: pass
    return
  def get_track_speed(self):
    i=self.tele_thread.tele_speeds[0]
    if i==9:  i=3   # For NO Tracking
    self.teleTrackStat.message('state','%s' % TELE_TRACK_SPEEDS[i])
    return

class FlagsFrame(fg.FrameGUI):
  def __init__(self,root=None,col=0,row=0,colspan=1,rowspan=1,thrd=None):
    if root==None:
      self.root=Toplevel()
      self.root.title('Flag Status Eng GUI')
    else:
      self.root=root
    self.thread=thrd
    self.thread_list=['starcat','telescope','camera','image','finder','finderimage']
    self._managerlist=['Main Thread','weather_stat','work_time_stat','manual_run_stat','dimm_is_running_flag',\
      'all_running_flag','proc_done_stat','last_dimm_measure_done','auto_dimm_stat','cancel_process_stat',\
      'logging_flag','write_rose_flag','prog_stat']
    self._domelist=['Thread Alive','Opened','Mixed','Closed','dome_closed_stat','thread_stat']
    self._starcatlist=['Thread Alive','src_out_status','auto_select','logging_flag','thread_stat']
    self._telescopelist=['Thread Alive','on_source_stat','park_stat','logging_flag','thread_stat']
    self._cameralist=['Thread Alive','take_exposure_stat','read_out_stat','new_data_ready_stat','auto_sequence_stat',\
      'logging_flag','thread_stat']
    self._imagelist=['Thread Alive','run_proc_event','processed_image_ready','process_done','measure_done',\
      'logging_flag','thread_stat']
    self._finderlist=['Thread Alive','take_exposure_stat','read_out_stat','new_data_ready_stat','auto_sequence_stat',\
      'logging_flag','thread_stat']
    self._finderimagelist=['Thread Alive','run_proc_event','processed_image_ready','process_done','measure_done',\
      'logging_flag','thread_stat']
    self._indicatorList=[\
                         ['managerEvents','Manager events',self._managerlist,(0,1,3,1,'nsew')],\
                         ['domeEvents','Dome events',self._domelist,(4,1,3,1,'nsew')],\
                         ['telescopeEvents','Telescope events',self._telescopelist,(4,2,3,1,'nsew')],\
                         ['starcatEvents','Source events',self._starcatlist,(0,2,3,1,'nsew')],\
                         ['imageEvents','Image Proc events',self._imagelist,(0,3,3,1,'nsew')],\
                         ['cameraEvents','Camera events',self._cameralist,(4,3,3,1,'nsew')],\
                         ['finderimageEvents','Finder Proc events',self._finderimagelist,(0,4,3,1,'nsew')],\
                         ['finderEvents','Finder events',self._finderlist,(4,4,3,1,'nsew')],\
                        ]
    fg.FrameGUI.__init__(self,root=self.root,name='Flag Status',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    self.check_update()
    return
  def check_update(self):
    ###Could use eval('self.'+listitem[i]+list2item[j])
    ###   where listitem=['','att1.','att2.',...]
    ###     and list2item=['att1','att2',...]
    for i in range(self.managerEvents.number):
      if i==0:
        self.managerEvents.set_indicator('Main Thread',self.thread.isAlive())
      else:
        try:
          self.managerEvents.set_indicator(self._managerlist[i],self.thread.__dict__[self._managerlist[i]].isSet())
        except Exception:
          self.managerEvents.set_indicator(self._managerlist[i],self.thread.__dict__[self._managerlist[i]])
    if hasattr(self.thread,'dome'):
      if self.thread.dome.dome_status=='Opened': self.domeEvents.set_indicator('Opened',True)
      else: self.domeEvents.set_indicator('Opened',False)
      if self.thread.dome.dome_status=='Mixed': self.domeEvents.set_indicator('Mixed',True)
      else: self.domeEvents.set_indicator('Mixed',False)
      if self.thread.dome.dome_status=='Closed': self.domeEvents.set_indicator('Closed',True)
      else: self.domeEvents.set_indicator('Closed',False)
      self.domeEvents.set_indicator('thread_stat',self.thread.dome.thread_stat.isSet())
      self.domeEvents.set_indicator('dome_closed_stat',self.thread.dome.dome_closed_stat.isSet())
      self.domeEvents.set_indicator('Thread Alive',self.thread.dome.isAlive())
    else: #pass
      self.domeEvents.set_indicator('Opened',-1)
      self.domeEvents.set_indicator('Mixed',-1)
      self.domeEvents.set_indicator('Closed',-1)
      self.domeEvents.set_indicator('thread_stat',-1)
      self.domeEvents.set_indicator('dome_closed_stat',-1)
      self.domeEvents.set_indicator('Thread Alive',-1)
    for each in self.thread_list: 
      if 'image' in each: tag='process_thread'
      else: tag=None
      if hasattr(self.thread,each):
        try: self.__dict__[each+'Events'].set_indicator('Thread Alive',self.thread.__dict__[each].isAlive())
        except Exception: pass
        for i in range(1,self.__dict__[each+'Events'].number):
          try:
            if tag:
              self.__dict__[each+'Events'].set_indicator(self.__dict__['_'+each+'list'][i],\
                self.thread.__dict__[each].__dict__[tag].__dict__[self.__dict__['_'+each+'list'][i]].isSet())
            else:
              self.__dict__[each+'Events'].set_indicator(self.__dict__['_'+each+'list'][i],\
                self.thread.__dict__[each].__dict__[self.__dict__['_'+each+'list'][i]].isSet())
          except Exception:
            if tag:
              self.__dict__[each+'Events'].set_indicator(self.__dict__['_'+each+'list'][i],\
                self.thread.__dict__[each].__dict__[tag].__dict__[self.__dict__['_'+each+'list'][i]])
            else:
              self.__dict__[each+'Events'].set_indicator(self.__dict__['_'+each+'list'][i],\
                self.thread.__dict__[each].__dict__[self.__dict__['_'+each+'list'][i]])
      else:
        try:
          #Sometimes a KeyError occurs trying to update the flags after having stopped a process
          [self.__dict__[each+'Events'].set_indicator(self.__dict__['_'+each+'list'][i],-1) for i in \
            range(self.__dict__[each+'Events'].number)]
        except Exception: pass
    self.after(5,self.check_update)
    return

class SeeingMeasureGUI(fg.FrameGUI):
  def __init__(self,parent=None,col=0,row=0,colspan=1,rowspan=1):
    self.parent=parent
    self.root=parent.interior()
    self.thread=parent.thread_manager
    self._mesBarList=[\
                      ['srcName','Source Name',20,(0,0,3,1,'nsew')],\
                      ['locDate','Local Date',20,(0,1,3,1,'nsew')],\
                      ['locTime','Local Time',20,(0,2,3,1,'nsew')],\
                      ['locLST','Local LST',20,(0,3,3,1,'nsew')],\
                      ['srcRA','Source RA',20,(0,4,3,1,'nsew')],\
                      ['srcDC','Source Dec',20,(0,5,3,1,'nsew')],\
                      ['teleAz','Telescope Az',20,(0,6,3,1,'nsew')],\
                      ['teleEl','Telescope Elv',20,(0,7,3,1,'nsew')],\
                      ['srcZD','Zenith Distance',20,(0,8,3,1,'nsew')],\
                      ['srcAM','Airmass',20,(0,9,3,1,'nsew')],\
                      #['pixMean','Pixel Dist Mean',20,(0,10,3,1,'nsew')],\
                      #['pixStd','Pixel Dist Std',20,(0,11,3,1,'nsew')],\
                      #['epsLongG','Seeing Eps Long G',20,(0,20,3,1,'nsew')],\
                      ['epsLongZ','Seeing Eps Long Z',20,(0,21,3,1,'nsew')],\
                      #['epsTransG','Seeing Eps Trans G',20,(0,22,3,1,'nsew')],\
                      ['epsTransZ','Seeing Eps Trans Z',20,(0,23,3,1,'nsew')],\
                      ['measNumber','Number Measured',20,(0,30,3,1,'nsew')],\
                      ['rejNumber','Rejects',20,(0,31,3,1,'nsew')]]
    fg.FrameGUI.__init__(self,root=self.root,name='Seeing Measurement',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    self.check_update()
    return
  def check_update(self):
    if hasattr(self.thread,'seeing'):
      seeing_line=self.thread.seeing.split(',')
      self.locDate.message('state','%s' % seeing_line[1])
      self.locTime.message('state','%s' % seeing_line[0])
      self.locLST.message('state','%s' % seeing_line[2])
      self.srcName.message('state','%s' % seeing_line[3])
      self.srcRA.message('state','%s' % seeing_line[4])
      self.srcDC.message('state','%s' % seeing_line[5])
      self.teleAz.message('state','%s' % seeing_line[6])
      self.teleEl.message('state','%s' % seeing_line[7])
      self.srcZD.message('state','%s, %s' % (seeing_line[8],seeing_line[9]))
      self.srcAM.message('state','%s' % seeing_line[10])
      #self.pixMean.message('state','%s' % seeing_line[11])
      #self.pixStd.message('state','%s' % seeing_line[12])
      #self.epsLongG.message('state','%s' % seeing_line[13])
      self.epsLongZ.message('state','%s' % seeing_line[14])
      #self.epsTransG.message('state','%s' % seeing_line[15])
      self.epsTransZ.message('state','%s' % seeing_line[16])
      self.measNumber.message('state','%s' % seeing_line[17])
      self.rejNumber.message('state','%s' % seeing_line[18])
      pass
    self.after(15,self.check_update)
    return

PROC_BUTTON_LIST=['movetosourceButton','movetoparkButton','unparkButton','opendomeButton','closedomeButton',\
      'imagesourceButton','runseeingButton','testrunButton','boximageButton','setcameraFocusButton',\
      'finderviewButton','stopfinderButton','boximageButton','resetregionButton','testNewFuncButton',\
      'imagefinderButton','setfindercenterButton','chngsourceButton']
ENG_BUTTON_LIST=['finderEngButton','srcEngButton','teleEngButton','domeEngButton','cameraEngButton']

class ManagerGUI(fg.FrameGUI):
  def __init__(self,root=None,col=0,row=0,colspan=1,rowspan=1,verbose=True,log=True):
    if root==None: self.root=Tk()
    else: self.root=root
    self.thread_manager=mthread.Manager(camera_name=mthread.THREAD_MNG['camera'][1]['camera_name'],\
      finder_name=mthread.THREAD_MNG['finder'][1]['camera_name'],prnt=verbose,log=log)
#   self.thread_manager.manual_run_stat.set()
    #self.thread_manager.start_all()
#   self._figure=icanv.ImageCanvas(root=root,col=5,row=0,colspan=3,rowspan=7)
    self._mesBarList=[
      ['localDateMess','Local Date',15,(0,1,3,1,'nsew')],\
      ['localTimeMess','Local Time',15,(0,2,3,1,'nsew')],\
      ['civtwilbegMess','Next Local Civ Twilight',20,(0,3,3,1,'nsew')],\
      ['civtwilendMess','Next Local Civ Twilight',20,(0,4,3,1,'nsew')],\
      ['utcDateMess','UTC Date',15,(3,1,3,1,'nsew')],\
      ['utcTimeMess','UTC Time',15,(3,2,3,1,'nsew')],\
      ['lstMess','LST',15,(3,3,3,1,'nsew')],\
      ['domesOpenMess','Domes Opened',15,(3,4,3,1,'nsew')]]
#   self._checkList=[['logAllStat','Log All','horizontal','radiobutton',\
#                     ['On','Off'],self.set_log_auto,(0,8,2,1,'nsew')],\
#                     ['autodimmStat','Run as DIMM','horizontal','radiobutton',\
#                     ['On','Off'],self.set_run_dimm,(0,9,2,1,'nsew')]]
    self._buttonList=[
                      ['startDIMM','Start DIMM','(lambda slf=self: slf.thread_manager(\'start_dimm\'))',\
                        (0,10,2,1,'nsew')],\
                      ['runnDIMM','Run AutoDIMM','(lambda slf=self: slf.thread_manager.auto_dimm_stat.set())',\
                        (2,10,2,1,'nsew')],\
                      ['stopDIMM','Stop DIMM','(lambda slf=self: slf.thread_manager(\'stop_dimm\'))',\
                        (4,10,2,1,'nsew')],\
                      ['unrunnDIMM','Stop AutoDIMM','(lambda slf=self: slf.thread_manager.auto_dimm_stat.clear())',\
                        (2,11,2,1,'nsew')],\
                      ['manualDIMM','Set Manual','(lambda slf=self: slf.set_manual_mode())',\
                        (0,11,2,1,'nsew')],\
                      ['startProcs','Start processes','(lambda slf=self: slf.thread_manager(\'start_all\'))',\
                        (0,12,2,1,'nsew')],\
                      ['stopProcs','Stop processes','(lambda slf=self: slf.thread_manager(\'stop_all\'))',\
                        (2,12,2,1,'nsew')],\
                      #['stopTest','STOP','(lambda slf=self: slf.thread_manager.cancel_process_stat.set())',\
                      #(0,13,2,1,'nsew')],\
                      ['stopTest','STOP TEST','(lambda slf=self: slf.stop_measurement())',\
                      (0,13,2,1,'nsew')],\
                      ['writeROSE','Write2Rose','(lambda slf=self: slf.set_report_mode())',\
                        (4,11,2,1,'nsew')],\
                      ['resetProcs','Recover','(lambda slf=self: slf.thread_manager.get_recover_dict())',\
                      (4,13,2,1,'nsew')],\
                      ['setresetProcs','Set Recover','(lambda slf=self: slf.thread_manager.set_recover_dict())',\
                      (4,14,2,1,'nsew')],\
                      ['resetMoxaButton','Reset Moxa','(lambda slf=self: slf.reset_moxa())',(4,15,2,1,'nsew')],\
                      ['boximageButton','Box Region','(lambda slf=self: slf.box_camera())',\
                      (0,16,2,1,'nsew')],\
                      ['resetregionButton','Reset Region','(lambda slf=self: slf.reset_region())',\
                      (2,16,2,1,'nsew')],\
                      ['setcameraFocusButton','Focus Camera',\
                      '(lambda slf=self: slf.thread_manager(\'test_focus\'))',\
                      (2,14,2,1,'nsew')],\
                      ['testNewFuncButton','Test Function',\
                      '(lambda slf=self: slf.thread_manager(\'test_function\'))',\
                      (0,14,2,1,'nsew')],\
                      ['setfindercenterButton','Center Source',\
                      '(lambda slf=self: slf.thread_manager(\'set_finder_center\'))',\
                      (2,15,2,1,'nsew')],\
                      ['testrunButton','Test DIMM','(lambda slf=self: slf.testing_all())',\
                      (0,15,2,1,'nsew')],\
                      ['imagesourceButton','Image Source',\
                        '(lambda slf=self: slf.thread_manager(\'image_source\'))',\
                      (0,18,2,1,'nsew')],\
                      ['imagefinderButton','Image Finder',\
                      '(lambda slf=self: slf.thread_manager.finderimage.process_thread())',\
                      (0,20,2,1,'nsew')],\
                      ['runseeingButton','Run Seeing','(lambda slf=self: slf.thread_manager(\'run_seeing\'))',\
                      (2,18,2,1,'nsew')],\
                      ['finderviewButton','Finder View','(lambda slf=self: slf.thread_manager.run_finder())',\
                      (0,19,2,1,'nsew')],\
                      ['stopfinderButton','Stop Finder','(lambda slf=self: slf.thread_manager.stop_finder())',\
                      (2,19,2,1,'nsew')],\
                      ['movetosourceButton','Move to Source',
                      '(lambda slf=self: slf.thread_manager(\'move_to_source\'))',\
                      (0,21,2,1,'nsew')],\
                      #['chngandgoButton','Change and Go',
                      #'(lambda slf=self: slf.thread_manager(\'change_and_go\'))',\
                      ['chngsourceButton','Change Source',
                      '(lambda slf=self: slf.thread_manager(\'change_source\'))',\
                      (2,21,2,1,'nsew')],\
                      ['movetoparkButton','Move to Park',\
                      '(lambda slf=self: slf.thread_manager(\'park_telescope\'))',\
                      (0,23,2,1,'nsew')],\
                      ['unparkButton','UnPark',\
                      '(lambda slf=self: slf.thread_manager(\'unpark_telescope\'))',\
                      (2,23,2,1,'nsew')],\
                      ['opendomeButton','Open Dome',\
                      '(lambda slf=self: slf.thread_manager(\'open_dome\'))',\
                      (0,25,2,1,'nsew')],\
                      ['closedomeButton','Close Dome',\
                      '(lambda slf=self: slf.thread_manager(\'close_dome\'))',\
                      (2,25,2,1,'nsew')],\
                      ['IPpowerEngButton','IP Power',\
                      '(lambda slf=self: slf.open_ippower_gui())',\
                      (4,16,2,1,'nsew')],\
                      ['finderEngButton','Finder Camera',\
                      '(lambda slf=self: slf.open_finder_gui())',\
                      (4,23,2,1,'nsew')],\
                      ['srcEngButton','Source Info',\
                      '(lambda slf=self: slf.open_esrc_gui())',\
                      (4,19,2,1,'nsew')],\
                      ['teleEngButton','Telescope',\
                      '(lambda slf=self: slf.open_etele_gui())',\
                      (4,20,2,1,'nsew')],\
                      ['domeEngButton','Dome',\
                      '(lambda slf=self: slf.open_edome_gui())',\
                      (4,21,2,1,'nsew')],\
                      ['flagEngButton','Flag Status',\
                      '(lambda slf=self: slf.open_flag_stat_gui())',\
                      (4,22,2,1,'nsew')],\
                      ['WeatherButton','Weather Status',\
                      '(lambda slf=self: slf.open_weather_gui())',\
                      (4,17,2,1,'nsew')],\
                      ['cameraEngButton','Camera',\
                      '(lambda slf=self: slf.open_ecamera_gui())',\
                      (4,22,2,1,'nsew')]]
    self._entryList=[]
    self._listboxList=[['messagebox','Messages',(0,30,6,5,'nsew')]]
    fg.FrameGUI.__init__(self,root=root,name='DIMM Items',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    #self.logAllStat.setvalue('Off')
    self.mesg=''
    #blank1=fg.BlankSpace(self.interior(),row=22,colspan=6)
    self.stopProcs.configure(state='disabled')
    for each in PROC_BUTTON_LIST+ENG_BUTTON_LIST:
      self.__dict__[each].configure(state='disabled')
    self.messagebox.listbox.configure(height=1)
    self.mngr_last_running_flag=self.thread_manager.all_running_flag
    self.last_auto_dimm_flag=self.thread_manager.auto_dimm_stat.isSet()
    self.last_cancel_proc_flag=self.thread_manager.cancel_process_stat.isSet()
    self.thread_manager.write_rose_flag=False
    self.set_report_mode()
    self.check_update()
    return
  def check_update(self):
    cnt=0
    if self.mesg!=self.thread_manager.message:
      self.messagebox.listbox.delete(1.0,index2=END)
      self.messagebox.listbox.insert(END,self.thread_manager.message)
      self.mesg=self.thread_manager.message
    if hasattr(self,'thread_manager'):
      if hasattr(self.thread_manager,'image'):
        imgproc=self.thread_manager.image.process_thread
        if imgproc.num_measures==1 and not imgproc.image_queue.empty():
          data=imgproc.image_queue.get()
          self._figure.data_queue.put(data)
        elif imgproc.image_count!=imgproc.num_measures and not imgproc.image_queue.empty():
          data=imgproc.image_queue.get()
          self._figure.data_queue.put(data)
        else: pass
    if hasattr(self,'thread_manager'):
      if hasattr(self.thread_manager,'finderimage'):
        imgproc=self.thread_manager.finderimage.process_thread
        if imgproc.num_measures==1 and not imgproc.image_queue.empty():
          data=imgproc.image_queue.get()
          ##### a cheap way to add the finder current center to the plot
          try: data.centers=vstack((data.centers,-1*self.thread_manager.finderimage.center[0]))
          except Exception: pass
          self._figure.data_queue.put(data)
        elif imgproc.image_count!=imgproc.num_measures and not imgproc.image_queue.empty():
          data=imgproc.image_queue.get()
          ##### a cheap way to add the finder current center to the plot
          try: data.centers=vstack((data.centers,-1*self.thread_manager.finderimage.center[0]))
          except Exception: pass
          self._figure.data_queue.put(data)
        else: pass
#   if self.thread_manager.logging:
#     self.logAllStat.setvalue('On')
#   else:
#     self.logAllStat.setvalue('Off')
    if self.mngr_last_running_flag!=self.thread_manager.all_running_flag:
      #print 'Changing STATUS!!! From %r to %r and re-config gui!!!!' % \
        #(self.mngr_last_running_flag,self.thread_manager.all_running_flag)
      self.check_processes_status()
      self.mngr_last_running_flag=self.thread_manager.all_running_flag
    if self.last_auto_dimm_flag!=self.thread_manager.auto_dimm_stat.isSet() or \
      self.last_cancel_proc_flag!=self.thread_manager.cancel_process_stat.isSet():
      self.check_auto_dimm_running()
      self.last_auto_dimm_flag==self.thread_manager.auto_dimm_stat.isSet()
      self.last_cancel_proc_flag==self.thread_manager.cancel_process_stat.isSet()
    if hasattr(self,'thread_manager'):
      if hasattr(self.thread_manager,'location'):
        self.utcDateMess.message('state','%s' % self.thread_manager.location.utc_date)
        self.utcTimeMess.message('state','%s' % self.thread_manager.location.utc_time)
        self.localDateMess.message('state','%s' % self.thread_manager.location.local_date)
        self.localTimeMess.message('state','%s' % self.thread_manager.location.local_time)
        self.lstMess.message('state','%s' % str(self.thread_manager.location.lst_time))
        self.civtwilbegMess.message('state','%s' % str(self.thread_manager.location.beg_civil_twilight).split('.')[0])
        self.civtwilendMess.message('state','%s' % str(self.thread_manager.location.end_civil_twilight).split('.')[0])
        self.domesOpenMess.message('state','%s' % str(self.thread_manager.work_time_stat.isSet()))
    self.after(1,self.check_update)
    return
  def reset_moxa(self):
    reset_moxa(host=TELE_SOCK_HOST)
    reset_moxa(host=DOME_SOCK_HOST)
    return
  def stop_measurement(self):
    if self.thread_manager.cancel_process_stat.isSet():
      self.thread_manager.cancel_process_stat.clear()
      self.thread_manager.proc_done_stat.clear()
      self.stopTest.configure(text='STOP TEST')
      self.stopTest.configure(fg='black')
      self.stopTest.configure(bg='#d9d9d9')
    else:
      ###The following added 23 May 2019 to fully stop a measurement.
      if hasattr(self.thread_manager,'image'):
        self.thread_manager.image.process_thread.stop_measure()
      if hasattr(self.thread_manager,'finderimage'):
        self.thread_manager.finderimage.process_thread.stop_measure()
      self.thread_manager.cancel_process_stat.set()
      self.thread_manager.proc_done_stat.set()
      self.stopTest.configure(text='Re-Start TEST')
      self.stopTest.configure(fg='white')
      self.stopTest.configure(bg='red')
    return
  def set_manual_mode(self):
    if self.thread_manager.manual_run_stat.isSet():
      self.thread_manager.manual_run_stat.clear()
      self.manualDIMM.configure(text='Set Manual')
      self.manualDIMM.configure(fg='black')
      self.manualDIMM.configure(bg='#d9d9d9')
    else:
      self.thread_manager.manual_run_stat.set()
      self.manualDIMM.configure(text='Unset Manual')
      self.manualDIMM.configure(fg='white')
      self.manualDIMM.configure(bg='blue')
    return
  def set_report_mode(self):
    if self.thread_manager.write_rose_flag:
      self.thread_manager.write_rose_flag=False
      self.writeROSE.configure(text='Write2Rose')
      self.writeROSE.configure(fg='white')
      self.writeROSE.configure(bg='blue')
    else:
      self.thread_manager.write_rose_flag=True
      self.writeROSE.configure(text='DontWriteRose')
      self.writeROSE.configure(fg='black')
      self.writeROSE.configure(bg='#d9d9d9')
    return
  def check_processes_status(self):
    if self.thread_manager.all_running_flag:
      if not hasattr(self,'tele_status'): self.tele_status=TelescopeStatusGUI(parent=self,col=0,row=35,colspan=3)
      if not hasattr(self,'seeing_status'): self.seeing_status=SeeingMeasureGUI(parent=self,col=3,row=35,colspan=3)
      if not hasattr(self,'_figure'): self._figure=icanv.ImageCanvas(root=root,col=5,row=0,colspan=3,rowspan=7)
      for each in ENG_BUTTON_LIST:
        self.__dict__[each].configure(state='normal')
      self.stopProcs.configure(state='normal')
      self.stopDIMM.configure(state='normal')
      self.startProcs.configure(state='disabled')
      self.startDIMM.configure(state='disabled')
      if self.thread_manager.auto_dimm_stat.isSet():
        for each in PROC_BUTTON_LIST:
          self.__dict__[each].configure(state='disabled')
      else:
        for each in PROC_BUTTON_LIST:
          self.__dict__[each].configure(state='normal')
    else:
      if hasattr(self,'tele_status'):
        self.tele_status.grid_forget()
        del self.tele_status
      if hasattr(self,'seeing_status'):
        self.seeing_status.grid_forget()
        del self.seeing_status
      if hasattr(self,'_figure'):
        self._figure.destroy()
        del self._figure
      for each in PROC_BUTTON_LIST+ENG_BUTTON_LIST:
        self.__dict__[each].configure(state='disabled')
      self.stopProcs.configure(state='disabled')
      self.stopDIMM.configure(state='disabled')
      self.startProcs.configure(state='normal')
      self.startDIMM.configure(state='normal')
    return
  def check_auto_dimm_running(self):
    if self.thread_manager.cancel_process_stat.isSet():
      self.stopTest.configure(text='Re-Start TEST')
      self.stopTest.configure(fg='white')
      self.stopTest.configure(bg='red')
    else:
      self.stopTest.configure(text='STOP TEST')
      self.stopTest.configure(fg='black')
      self.stopTest.configure(bg='#d9d9d9')
    if self.thread_manager.auto_dimm_stat.isSet():
      self.unrunnDIMM.configure(state='normal')
      self.runnDIMM.configure(state='disabled')
    else:
      self.runnDIMM.configure(state='normal')
      self.unrunnDIMM.configure(state='disabled')
    return
  def stopAll(self):
    self.thread_manager.stop()
    mthread.progStat=False
    self.destroy()
    return
  def box_camera(self):
    self.thread_manager.image('boxregion',center_type='midpoint')
    return
  def reset_region(self):
    self.thread_manager.image.reset_box=True
    self.thread_manager.image('boxregion')
    return
  def testing_all(self):
    self.thread_manager('test_dimm')
    return
  def set_flags(self,*tags):
    exec(tags[0]+'='+str(tags[1]))
    return
  def set_log_auto(self,*tags):
    #if self.logAllStat.getvalue()=='On': self.thread_manager.log_all()
    #else: self.thread_manager.log_off()
    return
  def open_etele_gui(self):
    twind=Toplevel()
    twind.title('Telescope Eng GUI')
    tlevel=TelescopeGUI(root=twind,row=1,colspan=4,thrd=self.thread_manager.telescope)
    xButton=Button(twind,text='Exit',font=fg.TEXT_FONT,command=twind.destroy,width=6,padx=0,pady=0)
    xButton.grid(column=0,row=0,sticky='nsw')
    return
  def open_edome_gui(self):
    twind=Toplevel()
    twind.title('Dome Eng GUI')
    tlevel=DomeGUI(root=twind,row=1,colspan=4,thrd=self.thread_manager.dome)
    xButton=Button(twind,text='Exit',font=fg.TEXT_FONT,command=twind.destroy,width=6,padx=0,pady=0)
    xButton.grid(column=0,row=0,sticky='nsw')
    return
  def open_esrc_gui(self):
    twind=Toplevel()
    twind.title('Source/Catalog Eng GUI')
    tlevel=CatFrame(root=twind,col=0,row=1,colspan=4,thrd=self.thread_manager.starcat)
    xButton=Button(twind,text='Exit',font=fg.TEXT_FONT,command=twind.destroy,width=6,padx=0,pady=0)
    xButton.grid(column=0,row=0,sticky='nsw')
    return
  def open_ecamera_gui(self):
    twind=Toplevel()
    twind.title('Camera Eng GUI')
    #tlevel=CameraGUI(root=twind,parent=self,col=0,row=1,colspan=4,device=self.thread_manager.camera)
    tlevel=ImageProcGUI(root=twind,parent=self,col=0,row=2,colspan=4,\
      proc_thread=self.thread_manager.image,\
      device_name=self.thread_manager.image.process_thread.device_name)
    xButton=Button(twind,text='Exit',font=fg.TEXT_FONT,command=twind.destroy,width=6,padx=0,pady=0)
    xButton.grid(column=0,row=0,sticky='nsw')
    return
  def open_finder_gui(self):
    twind=Toplevel()
    twind.title('Finder Eng GUI')
#   tlevel=CameraGUI(root=twind,parent=self,col=0,row=1,colspan=4,device=self.thread_manager.finder)
    tlevel=ImageProcGUI(root=twind,parent=self,col=0,row=2,colspan=4,\
      proc_thread=self.thread_manager.finderimage,\
      device_name=self.thread_manager.finderimage.process_thread.device_name)
    tlevel.component('tag').configure(bg='RoyalBlue')
    tlevel.component('ring').configure(bg='RoyalBlue')
    tlevel.component('hull').configure(bg='RoyalBlue')
    tlevel.component('groupchildsite').configure(bg='RoyalBlue')
    xButton=Button(twind,text='Exit',font=fg.TEXT_FONT,command=twind.destroy,width=6,padx=0,pady=0)
    xButton.grid(column=0,row=0,sticky='nsw')
    return
  def open_flag_stat_gui(self):
    twind=Toplevel()
    twind.title('Flag Status Eng GUI')
    tlevel=FlagsFrame(root=twind,col=0,row=1,colspan=4,thrd=self.thread_manager)
    xButton=Button(twind,text='Exit',font=fg.TEXT_FONT,command=twind.destroy,width=6,padx=0,pady=0)
    xButton.grid(column=0,row=0,sticky='nsw')
    return
  def open_ippower_gui(self):
    twind=Toplevel()
    twind.title('IPPower Eng GUI')
    tlevel=PowerStatusGUI(root=twind,col=0,row=1,colspan=4)
    xButton=Button(twind,text='Exit',font=fg.TEXT_FONT,command=twind.destroy,width=6,padx=0,pady=0)
    xButton.grid(column=0,row=0,sticky='nsw')
    return
  def open_weather_gui(self):
    twind=Toplevel()
    twind.title('Latest Weather GUI')
    tlevel=WeatherClientGUI(root=twind,col=0,row=1,colspan=4,thrd=self.thread_manager.weather)
    xButton=Button(twind,text='Exit',font=fg.TEXT_FONT,command=twind.destroy,width=6,padx=0,pady=0)
    xButton.grid(column=0,row=0,sticky='nsw')
    return

 

def stopProgs():
  global root,mgui
  print 'Stopping All Manager Processes'
  mgui.stopAll()
  print 'DIMM Manager Sucessfully exited'
  try:  root.destroy()
  except Exception as err:  pass
  sys.exit()
  return

if __name__=='__main__':
  global root,mgui
  progStat=True
  try:
    vindex=sys.argv.index('-v')
    if vindex>0: verbose=True
    else: verbose=False
  except Exception:
    verbose=False   #For Verbose printing of Manager messages
  try:
    logindex=sys.argv.index('-l')
    if logindex>0: logging=False
    else: logging=True
  except Exception:
    logging=True   #For Logging everything to a log file
  try:
    dindex=sys.argv.index('-dport')+1
    dome_port=sys.argv[dindex]
  except Exception:
    dome_port='-'   #For Dome simulation mode
  try:
    pindex=sys.argv.index('-tport')+1
    tele_port=sys.argv[pindex]
  except Exception:
    tele_port='-'   #For Telescope simulation mode
  try:
    mindex=sys.argv.index('-tmount')+1
    mount=sys.argv[mindex]
  except Exception:
    mount='S'   #For Telescope mount simulation mode
  try:
    cindex=sys.argv.index('-cname')+1
    camera_name=sys.argv[cindex]
  except Exception:
    camera_name='Simulation' #For simulation mode
  try:
    findex=sys.argv.index('-fname')+1
    finder_name=sys.argv[findex]
  except Exception:
    finder_name='Simulation' #For simulation mode
  try:
    aindex=sys.argv.index('-all')
    camera_name='GX2750'   #For Camera GX2750
#   camera_name='Simulation'   #For Camera GX2750
#   camera_name='GT1290'   #For Camera GT1290
#   finder_name='Video'   #For Finder Video
    finder_name='GT1290'   #For Camera GT1290
#   finder_name='Simulation'   #For Camera GX2750
#   mount='Meade'   #For Telescope Meade mount
#   tele_port='s'   #For Telescope IP
    mount='Astro-Physics'   #For Telescope Meade mount
    tele_port='h'   #For Telescope IP
#   tele_port='-'   #For Telescope Simulation mode
    dome_port='h'   #For Dome IP
#   dome_port='-'   #For Dome simulation mode
  except Exception: pass
  mthread.THREAD_MNG['dome'][1]['port']=dome_port
  mthread.THREAD_MNG['telescope'][1]['port']=tele_port
  mthread.THREAD_MNG['telescope'][1]['mount']=mount
  mthread.THREAD_MNG['camera'][1]['camera_name']=camera_name
  mthread.THREAD_MNG['finder'][1]['camera_name']=finder_name
  root=Tk()
  root.protocol('WM_DELETE_WINDOW',stopProgs)
  pmw.initialise(root)
  fgui=fg.FrameGUI(root=root,name='Manager GUI',col=0,row=1,colspan=4)
  mgui=ManagerGUI(root=fgui.interior(),col=4,row=1,verbose=verbose,log=logging)
  xx=Button(root,text='Exit',font=fg.TEXT_FONT,command=stopProgs,\
    width=6,padx=0,pady=0)
  xx.grid(column=0,row=0,sticky='nw')
  root.mainloop()

