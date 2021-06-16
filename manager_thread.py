#! /usr/bin/env python manager_thread.py
#
import threading
import time,datetime
from numpy import array,all,cos
from camera import camera_thread,camera_prosilica,camera_sbig,camera_supercircuits
from dome import dome_thread
from imageprocs import image_proc_thread
from sourceprocs import source_cat_thread
from telescope import telescope_thread
from weather import weather_data_class 

from miscutilities.reset_moxa import reset_moxa
from miscutilities.ippower_cnt_gui import ippower
from common_parms import *

import test_code

PROS_LIST=['GX2750','GT1290']
MEAS_TIMEOUT=180.0

import sys
import os,os.path
import imp
import platform

progStat=True

def reinit():
  ''' reinit
        re-initializes all of the progStat variables for all of the modules.
        This is used in such cases as re-connecting to the telescope, camera, or
        dome.
  '''
  progStat=True
  #cth.progStat=True
  dome_thread.progStat=True
  #ipt.progStat=True
  #source_cat_thread.progStat=True
  telescope_thread.progStat=True
  return

if platform.linux_distribution()[0]=='debian':
  DIMM_SERVER=True
  DIMM_LOGGING=True
else:
  DIMM_SERVER=False
  DIMM_LOGGING=False

THREAD_MNG={'location':['source_cat_thread.LocationThread',{'name':'DIMM','lon':DIMLNG,'lat':DIMLAT,'elv':DIMELV}],\
            'starcat':['source_cat_thread.StarCatThread',{'location':'self.location','catname':None,'log':False}],\
            'dome':['dome_thread.DomeThread',{'name':'dome','prnt':False,'port':'-'}],\
            'telescope':['telescope_thread.TelesThread',{'name':'telescope','prnt':False,'log':False,\
              'port':'-','mount':'AP'}],\
            'camera':['CameraThread',{'prnt':False,'log':False,'camera_name':'Simulation'}],\
            #'camera':['CameraThread',{'prnt':False,'log':False,'camera_name':'GX2570'}],\
            'image':['image_proc_thread.Measurement_thread',{'name':'seeing'}],\
            'finder':['CameraThread',{'prnt':False,'log':False,'camera_name':'Simulation'}],\
            #'finder':['CameraThread',{'prnt':False,'log':False,'camera_name':'GT1290'}],\
            'imagefinder':['image_proc_thread.Measurement_thread',{'name':'finder'}]}

class Manager(threading.Thread):
  '''class Manager
       A class to manage all of the threads(sub-process).  It is responsible for the connections
       to the telescope, camera, finder, and dome.
  '''
  def __init__(self,sleeptime=MNG_THREAD_TIME,camera_name=THREAD_MNG['camera'][1]['camera_name'],\
    finder_name=THREAD_MNG['finder'][1]['camera_name'],prnt=False,log=False):
    '''__init__
       Parameters
         <sleeptime>  An update time rate for the managing thread
         <prnt>       A boolean set 'True' to print to the std.out, more for troubleshooting
         <log>        A boolean set 'True' produces a log file in the './logs/' directory.
    '''
    threading.Thread.__init__(self)
    self.setName('manager')
    self.sleeptime=sleeptime
    '''@ivar: The thread sleep time'''
    self.camera_name=camera_name
    '''@ivar: The type/name of the camera device, see the list in <common_parms.py>'''
    self.finder_name=finder_name
    '''@ivar: The type/name of the finder device, see the list in <common_parms.py>'''
    self.camera_session=None
    '''@ivar: For the Prosilica cameras a VIMBA session to be used for one or both Prosilica cameras'''
#   self.local_date,self.local_time=time.strftime(DTIME_FORMAT).split(',')
    dt_string=datetime.datetime.strftime(datetime.datetime.now(),DTIME_FORMAT_FLT)[:-4]
    self.local_date,self.local_time=dt_string.split(',')
    '''@ivar: The local date and time set by the local computer'''
    self.procedure_type_flag=None  # See dictionary above
    self.proc_done_stat=threading.Event()
    '''@ivar: An event that indicates a procedure has started or finished'''
    self.proc_done_stat.set()
    self.manual_run_stat=threading.Event()
    '''@ivar: An event to indicate all processes are running or have stopped'''
    self.manual_run_stat.clear()
    self.weather_stat=threading.Event()
    '''@ivar: An event to indicate that the weather is good to run the dimm, IMPLEMENTATION LATER'''
    self.weather_stat.clear()
    self.work_time_stat=threading.Event()
    '''@ivar: An event to indicate that it is time to run the dimm, IMPL LATER.  Uses the location time_to_work funct'''
    self.work_time_stat.clear()
    self.auto_dimm_stat=threading.Event()
    '''@ivar: An event to indicate the DIMM is running in auto'''
    self.auto_dimm_stat.clear()
    self.last_dimm_measure_done=threading.Event()
    '''@ivar: An event to indicate the last DIMM measurement is complete'''
    self.last_dimm_measure_done.set()
    self.cancel_process_stat=threading.Event()
    '''@ivar: An event that indicates to cancel a process or procedure'''
    self.cancel_process_stat.clear()
    self.prog_stat=True
    '''@ivar: A general boolean flag to start or stop Thread'''
    self.dimm_is_running_flag=False
    '''@ivar: A boolean flag to indicate whether or not the dimm is currently opened and running'''
    self.all_running_flag=False
    '''@ivar: A general boolean flag to indicate whether or not all program threads are running'''
    self.stdout_flag=prnt
    '''@ivar: A general boolean flag to to indicate whether or not to print to stdout'''
    subdir1=os.path.join(LOG_DIR,time.strftime('%b%Y'))
    fullpath=os.path.join(subdir1,time.strftime('%B%d'))
    if not os.path.exists(fullpath): os.makedirs(fullpath)
    self.logfile_name=os.path.join(fullpath,MNG_LOGBASENAME+'.'+time.strftime('%m.%d.%Y'))
    '''@ivar: Log filename '''
    self.logging_flag=log
    '''@ivar: A general boolean flag to start or stop logging'''
    self.write_rose_flag=True
    '''@ivar: A general boolean flag to to indicate whether or not to report seeing to rose'''
    self.old_mess=''
    self.set_message('Starting DIMM Manager Program')
    self.recover_dict={'telecommand':[],'source':'','catname':''}
    '''@ivar: A dictionary of important recover variables '''
    self.dimm_measure_count_on_src=0
    self.chk_conditions_cnt=30000
    self.location=source_cat_thread.LocationThread(name='DIMM',lon=DIMLNG,lat=DIMLAT,elv=DIMELV)
    self.location.start()
    if DIMM_SERVER:
      self.weather=weather_data_class.weather_thread(loc=self.location,log=True)
      self.weather.start()
    else:
      self.weather=None
    self.start()
    return
  def __repr__(self):
    '''<__repr__>
       expresses the image processing thread status
    '''
    ss='\n'
    ss=ss+'<Manager> class is Alive?             %s\n' % (self.isAlive())
    ss=ss+'<Manager.location> class is Alive?    %s\n' % (self.location.isAlive())
    if DIMM_SERVER:
      ss=ss+'<Manager.weather> class is Alive?     %s\n' % (self.weather.isAlive())
    ss=ss+'          self.prog_stat:             %r\n' % (self.prog_stat)
    ss=ss+'          self.weather_stat:          %r\n' % (self.weather_stat.isSet())
    ss=ss+'          self.work_time_stat:        %r\n' % (self.work_time_stat.isSet())
    ss=ss+'          self.manual_run_stat:       %r\n' % (self.manual_run_stat.isSet())
    ss=ss+'          self.dimm_is_running_flag:  %r\n' % (self.dimm_is_running_flag)
    ss=ss+'          self.all_running_flag:      %r\n' % (self.all_running_flag)
    ss=ss+'\n'
    ss=ss+'          self.proc_done_stat:        %r\n' % (self.proc_done_stat.isSet())
    ss=ss+'\n'
    ss=ss+'Message:  %s' % (self.message)
    ss=ss+'\n'
    try:
      ss=ss+'\n'
      ss='%s<Manager.dome> class is Alive? %s\n' % (ss,self.dome.isAlive())
      ss='%s<Manager.starcat> class is Alive? %s\n' % (ss,self.starcat.isAlive())
      ss='%s<Manager.telescope> class is Alive? %s\n' % (ss,self.telescope.isAlive())
      ss='%s<Manager.camera> class is Alive? %s\n' % (ss,self.camera.isAlive())
      ss='%s<Manager.image> class is Alive? %s\n' % (ss,self.image.isAlive())
      ss='%s<Manager.finder> class is Alive? %s\n' % (ss,self.finder.isAlive())
      ss='%s<Manager.finderimage> class is Alive? %s\n' % (ss,self.finderimage.isAlive())
    except Exception: pass
    return ss
  def __call__(self,procedure,*args,**kwargs):
    #if self.weather_stat.isSet() or self.manual_run_stat.isSet():
    if self.work_time_stat.isSet() or self.manual_run_stat.isSet():
      if hasattr(self,procedure):
        proc=self.__getattribute__(procedure)
        if callable(proc):
          # This will run the procedure
          self.procedure_type_flag=procedure
        else:
          pass
      else: 
        pass
    else: 
      self.set_message('Weather or Running status Events are NOT set!!!!!!!')
    return
  def run(self):
    while self.prog_stat:
      self.check_all_running()
      time.sleep(self.sleeptime)
      if self.work_time_stat.isSet() or self.manual_run_stat.isSet():
        if self.procedure_type_flag:
          proc=self.__getattribute__(self.procedure_type_flag)
          proc()
          self.procedure_type_flag=None
        else: pass
        if self.auto_dimm_stat.isSet() and self.last_dimm_measure_done.isSet() and self.all_running_flag:
          #Run the DIMM method continuously
          self.procedure_type_flag='test_dimm'
      else: pass
      if self.work_time_stat.isSet() and not self.dimm_is_running_flag and not self.manual_run_stat.isSet():
        self.set_message('run process:  TIME TO OPEN AND WORK!!!')
        self.auto_start()
      elif not self.work_time_stat.isSet() and self.dimm_is_running_flag and not self.manual_run_stat.isSet():
        self.set_message('run process:  TIME TO CLOSE AND SHUTDONW!!!')
        self.auto_stop()
      else: pass
#     self.check_all_running()
    return
  def _decorator(dimm_procedure):
    def procedure_wrapper(self,*args,**kwargs):
      self.procedure_type_flag=None
      self.proc_done_stat.clear()
      status=dimm_procedure(self,*args,**kwargs)
      self.proc_done_stat.set()
      return status
    return procedure_wrapper
  def stop(self):
    try:
      self.stop_all()
    except Exception:
      pass
    if DIMM_SERVER:
      self.weather.stop()
    self.location.stop()
    while self.all_running_flag: pass
    self.manual_run_stat.clear()
    self.weather_stat.clear()
    self.work_time_stat.clear()
    self.prog_stat=False
    return
  @_decorator
  def auto_start(self):
    self.proc_done_stat.clear()
    self.set_message('auto_start process:  Starting <start_dimm>...')
    self.start_dimm()
    self.proc_done_stat.wait()
    self.set_message('auto_start process:  Waiting for the processes to start and sleeping for 5sec.')
    time.sleep(5.0)
    self.set_message('auto_start process:  Setting <auto_dimm_stat> to true...')
    self.auto_dimm_stat.set()
    return
  @_decorator
  def auto_stop(self):
    #self.auto_dimm_stat.set()
    self.set_message('auto_stop process:  Setting <last_dimm_measure_done> to true and sleeping for 0.5 sec....')
    self.last_dimm_measure_done.set()
    time.sleep(0.5)
    self.set_message('auto_stop process:  Stopping dimm with <stop_dimm>...')
    self.stop_dimm()
    return
  @_decorator
  def reset_moxa(self):
    self.set_message('reset_moxa process:  Re-setting Telescope MOXA-box')
    reset_moxa(host=TELE_SOCK_HOST)
    self.set_message('reset_moxa process:  Re-setting Dome MOXA-box')
    reset_moxa(host=DOME_SOCK_HOST)
    time.sleep(0.5)
    self.set_message('reset_moxa process:  Re-setting MOXA-boxes complete')
    return
  @_decorator
  def start_all(self):
    self.set_message('start_all process:  Starting All Threads')
    self.set_message('start_all process:  Wait while setting camera session manager and finding all cameras')
    if self.camera_name in PROS_LIST or self.finder_name in PROS_LIST:
      if self.camera_name in PROS_LIST and self.finder_name in PROS_LIST:
        self.camera_session=camera_prosilica.return_vimba(num=2)
        '''@ivar: If two Prosilica camera are present will start a VIMBA session '''
      else:
        self.camera_session=camera_prosilica.return_vimba()
    else:
      self.camera_session=None
    self.set_message('start_all process:  Camera session manager started')
    #self.set_message('start_all process:  Resetting Moxa boxes')
    #self.reset_moxa()
    self.set_message('start_all process:  Initializing flags')
    reinit()
    self.set_message('start_all process:  Starting Source Thread')
    self.starcat=source_cat_thread.StarCatThread(location=self.location,catname=None,log=False)
    self.set_message('start_all process:  Starting Dome')
    self.dome=dome_thread.DomeThread(name='dome',prnt=False,port=THREAD_MNG['dome'][1]['port'])
    #self.dome=dome_thread.DomeThread(name='dome',prnt=False,port='-')
    self.dome.start()
    self.set_message('start_all process:  Starting Telescope Thread')
    self.telescope=telescope_thread.TelesThread(name='telescope',prnt=False,log=False,\
      port=THREAD_MNG['telescope'][1]['port'],mount=THREAD_MNG['telescope'][1]['mount'])
    self.telescope.start()
    #Sets the attribute self.camera
    self.set_message('start_all process:  Starting Camera and Camera Processing Thread')
    self.set_camera('camera',self.camera_name)
    self.image=image_proc_thread.Measurement_thread(name='seeing',device=self.camera)
    self.image.set_log_saveimg(log=True)
    #Sets the attribute self.finder
    self.set_message('start_all process:  Starting Finder and Finder Processing Thread')
    self.set_camera('finder',self.finder_name)
    self.finderimage=image_proc_thread.Measurement_thread(name='finder',device=self.finder)
    self.finderimage.set_log_saveimg(log=True)
    self.dimm_is_running_flag=True
    self.set_message('start_all process:  All Threads have Started')
    return
  @_decorator
  def stop_all(self):
    self.set_message('stop_all process:  Setting AUTO DIMM flags to be finished')
    self.auto_dimm_stat.clear()
    self.last_dimm_measure_done.set()
    self.set_message('stop_all process:  Saving Last State')
    self.set_recover_dict()
    self.set_message('stop_all process:  Stopping dome Thread')
    self.dome.stop()
    self.set_message('stop_all process:  Stopping starcat Thread')
    self.starcat.stop()
    self.set_message('stop_all process:  Stopping telescope Thread')
    self.telescope.close()
    self.set_message('stop_all process:  Stopping camera Thread')
    self.camera.close()
    self.set_message('stop_all process:  Stopping finder Thread')
    self.finder.close()
    self.set_message('stop_all process:  Stopping image Thread')
    self.image.stop()
    self.set_message('stop_all process:  Stopping finderimage Thread')
    self.finderimage.stop()
    self.set_message('stop_all process:  All threads have Stopped')
    del self.dome,self.starcat,self.telescope,self.camera,self.finder,self.image,self.finderimage
    self.dimm_is_running_flag=False
    self.cancel_process_stat.clear()
    return
  @_decorator
  def start_dimm(self):
    ippower(state=1)
    cnt=0
    self.set_message('start_dimm process:  Waiting for 5sec to power up!')
    while cnt<10:
      time.sleep(0.5)
      cnt+=1
    self.start_all()
    self.set_message('start_dimm process:  Opening Dome!')
    self.open_dome()
    self.set_message('start_dimm process:  Unparking Telescope!')
    self.unpark_telescope()
    return
  @_decorator
  def stop_dimm(self):
    self.set_message('stop_dimm process:  Parking Telescope')
    self.telescope.on_source_stat.clear()
    self.park_telescope()
    self.set_message('stop_dimm process:  Closing Dome')
    self.dome.dome_closed_stat.clear()
    self.close_dome()
    self.set_message('stop_dimm process:  Waiting for Park Position')
    self.telescope.on_source_stat.wait()
    self.set_message('stop_dimm process:  Waiting for Dome Closed Event')
    t_out_ret=self.dome.dome_closed_stat.wait(timeout=180.0)
    if not t_out_ret:
      self.set_message('stop_dimm process:  TIMEOUT waiting for dome_closed results')
    self.set_message('stop_dimm process:  Waiting for all processes to stop')
    self.stop_all()
    self.set_message('stop_dimm process:  Waiting for 2.0sec')
    time.sleep(2.0)
    self.set_message('stop_dimm process:  Powering down!')
    ippower(state=0)
    return
  def set_recover_dict(self):
    self.recover_dict['telecommand']=self.telescope.cmdposition
    self.recover_dict['source']=self.starcat.source.name
    self.recover_dict['catname']=self.starcat.cat_name.split('/')[-1].split('.')[0]
    return
  def get_recover_dict(self):
    self.starcat.recover_from(catname=self.recover_dict['catname'],source=self.recover_dict['source'])
    self.telescope.set_cmd_position(az_ra=str(self.starcat.source.a_ra),\
      elv_dec=str(self.starcat.source.a_dec),coords='radec')
    return
  def check_all_running(self):
    '''<check_all_running>
       Checks every 5 minutes to see if all processes are running, if it is time to work, and if DIMM is
       already working. (or 3000 cycles)
    '''
    #if hasattr(self,'location') and self.chk_conditions_cnt>=3000:
    if hasattr(self,'location') and hasattr(self,'weather') and self.chk_conditions_cnt>=3000:
      time_tmp=self.location.compare_times(time='civil',daytime=False)
      if DIMM_SERVER:
        wea_tmp=self.weather.weather_good
      else:
        wea_tmp=True
      if wea_tmp:  self.weather_stat.set()
      else:  self.weather_stat.clear()
      work_time=time_tmp & wea_tmp
      self.set_message('check_all_running process:  work_time(%r)=time_tmp(%r) & wea_tmp(%r)'% \
        (work_time,time_tmp,wea_tmp))
      if work_time: self.work_time_stat.set()
      else: self.work_time_stat.clear()
      self.set_message('check_all_running process:  weather_stat: %r, work_time_stat: %r, manual_run_stat: %r' % \
        (self.weather_stat.isSet(),self.work_time_stat.isSet(),self.manual_run_stat.isSet()))
      self.set_message('check_all_running process:  Work Time: %r, dimm_is_running_flag: %r, all_running_flag: %r' % \
        (self.work_time_stat.isSet(),self.dimm_is_running_flag,self.all_running_flag))
      try:
#       self.set_message('check_all_running process:  Next Civ Twilight: %s, Next Sunrise: %s, Next Sunset: %s, '+
#         'Next Civ Twighlight: %s' % (str(self.location.beg_civil_twilight),str(self.location.sunrise),
#         str(self.location.sunset),str(self.location.end_civil_twilight)))
        self.set_message('check_all_running process:  Location Times: %s' % (str(self.location)))
      except Exception as err:
        self.set_message('check_all_running process:  Location times NOT available, %s' % (err))
      self.chk_conditions_cnt=0
    else: self.chk_conditions_cnt+=1
    try:
      self.all_running_flag=self.dome.isAlive()&self.location.isAlive()&self.starcat.isAlive()&\
        self.telescope.isAlive()&self.camera.isAlive()&self.image.isAlive()&self.finder.isAlive()&\
        self.finderimage.isAlive()
    except Exception:
      self.all_running_flag=False
    return
  def set_camera(self,dev_type,dev_name):
    ''' <set_camera>  Sets either the camera or finder scope camera thread and names
        <dev_type>  either 'camera' or 'finder' and is the attribute name of the Manager (or self)
        <dev_name>  is one of the names of the camera devices in <common_parms.py> file
                    ie, CAMERA_LIST=['file','Simulation','GT1290','GX2750','SBIG','Video']
    '''
    self.__dict__[dev_type+'_name']=dev_name
    if dev_name=='Simulation':
      self.__dict__[dev_type]=camera_thread.CameraThread()
    elif dev_name=='GT1290':
      self.__dict__[dev_type]=camera_prosilica.CameraThread(session=self.camera_session,camera_name='GT1290',log=True)
    elif dev_name=='GX2750':
      self.__dict__[dev_type]=camera_prosilica.CameraThread(session=self.camera_session,camera_name='GX2750',log=True)
    elif dev_name=='SBIG':
      self.__dict__[dev_type]=camera_sbig.CameraThread(devmode='s')
    elif dev_name=='Video':
      self.__dict__[dev_type]=camera_supercircuits.CameraThread(channel=VIDEO_CHANNEL)
    else: pass
    if dev_name!='file':
      time.sleep(0.1)
      self.__dict__[dev_type].start()
    else: pass  # Maybe used one day for a 'file' device
    return
  #
  # In simulation mode use self.image.device.change_data=True
  # then self.image.take_new_image() to change the image without resetting exposure count
  # and then self.image.image.num_objects to assure yourself that peaks have been found
  #
  @_decorator
  def park_telescope(self):
    '''<park_telescope> Moves the telescope to the park position 1
    '''
    self.telescope.on_source_stat.clear()
    self.set_message('park_telescope:  Moving telescope to PARK')
    self.telescope.park_telescope()
    self.telescope.on_source_stat.wait()
    self.set_message('park_telescope:  Telescope is at the PARK position')
    return
  @_decorator
  def unpark_telescope(self):
    '''<unpark_telescope> Unparks the telescope and initializes the location and etc of the telescope.  It
                          is assumed that the telescope is currently parked at the park 1 position.
    '''
    self.set_message('unpark_telescope:  Unparking telescope')
    self.telescope.unpark_telescope()
    return
  @_decorator
  def open_dome(self):
    '''<open_dome> Opens the dome by calling the <open_dome> method of the <dome> instance.
    '''
    #self.dome.dome_status is the open/mixed/closed status
    if self.dome.dome_status!='Opened':
      self.set_message('open_dome:  Opening dome')
      self.dome.open_dome()
    else:
      self.set_message('open_dome:  Dome is Opened')
    return
  @_decorator
  def close_dome(self):
    '''<close_dome> Closes the dome by calling the <close_dome> method of the <dome> instance.
    '''
    #self.dome.dome_status is the open/mixed/closed status
    if self.dome.dome_status!='Closed':
      self.set_message('close_dome:  Closing dome')
      self.dome.close_dome()
    else:
      self.set_message('close_dome:  Dome is Closed')
    return
  @_decorator
  def move_to_source(self):
    '''<move_to_source> Sets the command position to that of the currently selected source.  Slews the
                        telescope to the source, clears the <on_source_stat> event bit, waits until the
                        telescope position is the source position, and sets the <on_source_stat> bit when
                        'on-source'.  Then, it sets the telscope tracking to sidereal rate.
    '''
    if self.camera_name=='Simulation':  self.camera.change_data=True  # for simulation mode
    self.set_message('move_to_source process:  MOVING TO SOURCE')
    self.telescope.set_cmd_position(az_ra=str(self.starcat.source.a_ra),\
      elv_dec=str(self.starcat.source.a_dec),coords='radec')
    self.set_message('move_to_source process:  Catalogue Source: %s' % (self.starcat.source.name))
    self.set_message('move_to_source process:  Moving to position: Ra=%s   Dec=%s' %\
      (str(self.starcat.source.ra),str(self.starcat.source.dec)))
    self.telescope.move_to_position()
    self.telescope.on_source_stat.clear()   #
    self.set_message('move_to_source process:  Waiting for telescope.on_source_stat bit')
    self.telescope.on_source_stat.wait()
    self.set_message('move_to_source process:  Setting tracking to sidereal')
    self.telescope.set_track(speed=2)
    self.set_message('move_to_source process:  Telescope ONSOURCE:%s'% (self.telescope.on_source_stat.isSet()))
    self.set_recover_dict()
    hdr=self.build_header()
    self.image.set_image_hdr_parms(**{i.lower():j for i,j in hdr.iteritems()})
    self.finderimage.set_image_hdr_parms(**{i.lower():j for i,j in hdr.iteritems()})
#   zdist,drctn,airmass=self.starcat.find_zdist(star=self.starcat.source)
#   self.image.set_image_hdr_parms(source=self.starcat.source.name,ra=str(self.starcat.source.ra),\
#     dec=str(self.starcat.source.dec),airmass=airmass,az=self.telescope.azimuth[2],\
#     zdist=zdist,magn=self.starcat.source.mag,\
#     elv=self.telescope.elevation[2])
#   self.finderimage.set_image_hdr_parms(source=self.starcat.source.name,ra=str(self.starcat.source.ra),\
#     dec=str(self.starcat.source.dec),airmass=airmass,az=self.telescope.azimuth[2],\
#     zdist=zdist,magn=self.starcat.source.mag,\
#     elv=self.telescope.elevation[2])
    return
  @_decorator
  def change_source(self):
# def change_and_go(self):
    '''<change_source> Originally, met to change the source and move to it.  But currently and probably will
                       remain, only changes the current source.
    '''
    self.set_message('change_source:  Changing SOURCE') # and going there')
    self.starcat.change_source()
    self.current_source=self.starcat.source
    self.set_message('change_source:  Changing SOURCE to %s' % self.current_source.name) 
    self.dimm_measure_count_on_src=0
    #self.move_to_source()
    return
  @_decorator
  def image_source(self):
    '''<image_source> Takes one image of the source through the telescope.  Additionally, it sets the image header
                      for the fits file.
    '''
    self.set_message('image_source:  Imaging source')
    hdr=self.build_header()
    self.image.set_image_hdr_parms(**{i.lower():j for i,j in hdr.iteritems()})
    #zdist,drctn,airmass=self.starcat.find_zdist(star=self.starcat.source)
    #self.image.set_image_hdr_parms(source=self.starcat.source.name,ra=str(self.starcat.source.ra),\
    #  dec=str(self.starcat.source.dec),airmass=airmass,az=self.telescope.azimuth[2],\
    #  zdist=zdist,magn=self.starcat.source.mag,\
    #  elv=self.telescope.elevation[2])
    self.image.process_thread.device.set_binning(4,4)
    self.image('image')
    self.set_message('image_source:  '+self.camera.message)
    self.image.results_stat.clear()
    #self.image.results_stat.wait()
    t_out_ret=self.image.results_stat.wait(timeout=MEAS_TIMEOUT)         #Timeout added 6June2018
    if not t_out_ret:
      self.image.process_thread.stop_measure()   #Timeout condition added 6June2018
      self.set_message('image_source:  TIMEOUT waiting for image results')
    self.set_message('image_source:  Number of objects found: %d' % (self.image.num_objects))
    return
  @_decorator
  def run_finder(self):
    '''<run_finder> Runs the finderscope camera with binning of 4x4, in continuous mode.
                    Basically, this only toggles the finder continuous mode.
    '''
    self.finder.set_binning(4,4)
    self.finderimage.continuous()
    return
  @_decorator
  def stop_finder(self):
    '''<stop_finder> Stops the finderscope camera from continuous mode.
                     Basically, this only toggles the finder continuous mode.
    '''
    self.finder.set_binning(4,4)
    self.finderimage.continuous()
    return
  @_decorator
  def set_finder_center(self,xcenter=FINDER_XCENTER,ycenter=FINDER_YCENTER):
    '''<set_finder_center>
       This method is used to center the finderscope camera and the seeing camera.  Once the star (or peak)
       is centered to a pre-defined position (xcenter,ycenter) in the finder, the main camera will
       center the star to the telescope/OTA optical center.  This will, then, redefine the finderscope's image
       center.
    '''
    # Set up the finder process arguments and run the centering routine.
    #self.finder.exptime=0.1
    self.finder.set_binning(4,4) #########NEW 23 Oct 2017
    #This following line may need to be added if the telescope north and east directions are swapped
    #self.finderimage.process_args['east_dir']='ccw'
    if all(self.finderimage.process_args['coords']==array([-1,-1])):
      self.finderimage.process_args['coords']=(xcenter,ycenter)
    self.finderimage.process_args['east_dir']='cw'
    self.finderimage.process_args['north_deg']=90.0
    self.move_to_center('finderimage')
    ####
    ## What to do if nothing is in the finderscope!!!!!!
    ##
    ## Check camera for a peak, if none re-center finder again
#   self.image('centering')
#   self.set_message('move_to_center, %s: Waiting for image.results_stat bit, iteration %d' % (camera_string,i))
#   self.image.results_stat.clear()
#   t_out_ret=self.image.results_stat.wait(timeout=MEAS_TIMEOUT)        #Timeout added 6June2018
#   if not t_out_ret:  self.image.process_thread.stop_measure()  #Timeout condition added 6June2018
    ####
    # Now that finder is close, set up the main camera and center it.
    self.camera.set_roi()
    self.camera.set_binning(4,4) 
    self.image.process_args['coords']=(self.camera.chip_width/2,self.camera.chip_height/2)
    self.image.process_args['east_dir']='cw'
    self.image.process_args['north_deg']=90.0
    self.move_to_center('image')
    ####
    ## What to do if nothing is in the telescope!!!!!!
    ####
    # Re-imaging finder to set the new finder center
    self.finderimage('centering')
    self.set_message('set_finder_center:  Finder: Waiting for finderimage.results_stat bit')
    self.finderimage.results_stat.clear()
    #self.finderimage.results_stat.wait()
    t_out_ret=self.finderimage.results_stat.wait(timeout=MEAS_TIMEOUT)         #Timeout added 6June2018
    if not t_out_ret:  self.finderimage.process_thread.stop_measure()   #Timeout condition added 6June2018
    #Simple check to see if there is a peak in the main camera prior to re-defining the finderscope image center
    #   imgx,imgy=(int(self.image.peak_0[1]),int(self.image.peak_0[3]))
    #   if (imgx,imgy)!=(0,0) and (imgx,imgy)!=(-1,-1):
    if self.image.num_objects>=1:
      x,y=(int(self.finderimage.peak_0[1]),int(self.finderimage.peak_0[3]))
      if (x,y)!=(0,0) and (x,y)!=(-1,-1):
        self.finderimage.process_args['coords']=(x,y)
        self.finderimage.center[0]=array([x,y])
        #self.set_message('set_finder_center:  Source is Centered at finder coordinates (%d,%d)' % (x,y))
        # Only if all of the conditions are met do we want to re-calibrate the telescope's position.
        if DIMM_SERVER:
          self.telescope.re_calibrate()
          self.set_message('set_finder_center:  Recalibrating Telescope centered at finder coordinates (%d,%d)' % (x,y))
      else:
        self.set_message('set_finder_center:  Finder center coordinates (%d,%d) did not change' % \
          (self.finderimage.process_args['coords'][0],self.finderimage.process_args['coords'][1]))
    else:
        self.set_message('set_finder_center:  No peak in Image, finder center coordinates (%d,%d) will not change' % \
        (self.finderimage.process_args['coords'][0],self.finderimage.process_args['coords'][1]))
    return
  def move_to_center(self,proc_string):
    '''<move_to_center>
       Takes the center measurement and moves the telescope accordingly.  NOTE: if NO peak is
       found in image on which to center, there will be only one center measurement returning zeros.
       That means this method will not run through the while loop either.

       <proc_string> is either a string 'camera' or 'finder' reflecting which processing thread on which to act.
    '''
    if proc_string=='image': 
      camera_string='Camera'
      speed='guide'
      rate=2
      CENTER_MOVE_TIME=CAM_CTR_MV_TIME
      CENTER_MOVE_DIST=CAM_CTR_MV_DIST
      CENTER_MOVE_ITER=CAM_CTR_MV_ITER
    else: 
      camera_string='FINDER'
      speed='center'
      rate=0
      CENTER_MOVE_TIME=FND_CTR_MV_TIME
      CENTER_MOVE_DIST=FND_CTR_MV_DIST
      CENTER_MOVE_ITER=FND_CTR_MV_ITER
    i=0
    self.__dict__[proc_string]('centering')
    self.set_message('move_to_center, %s: Waiting for image.results_stat bit' % (camera_string))
    self.__dict__[proc_string].results_stat.clear()
    #self.__dict__[proc_string].results_stat.wait()
    t_out_ret=self.__dict__[proc_string].results_stat.wait(timeout=MEAS_TIMEOUT)        #Timeout added 6June2018
    if not t_out_ret:  self.__dict__[proc_string].process_thread.stop_measure()  #Timeout condition added 6June2018
    self.set_message('move_to_center, %s: Number of object found:%d' % (camera_string,self.__dict__[proc_string].num_objects))
    self.set_message('move_to_center, %s: Returned: %r' % (camera_string,self.__dict__[proc_string].center))
    cur_dx=self.__dict__[proc_string].center[1][0]  #This is the dx,dy from defined center
    cur_dy=self.__dict__[proc_string].center[1][1]  #This is the dx,dy from defined center
    cur_ds=self.__dict__[proc_string].center[1][2]  #This is the original distance from the defined center
    cur_dirt=self.__dict__[proc_string].center[-1] #This is the original direction from the defined center
    last_dirt=cur_dirt
    while cur_ds>CENTER_MOVE_DIST and not self.cancel_process_stat.isSet() and i<CENTER_MOVE_ITER:
      last_dx,last_dy,last_ds=cur_dx,cur_dy,cur_ds
      #The speed, rate, and sleep time may need to be changed!!!!!
      self.telescope.move_direction(direction=cur_dirt,speed=speed,rate=rate)
      self.set_message('move_to_center, %s: Sleeping for %5.3fsec while moving in \'%s\' direction, iteration %d' % \
        (camera_string,CENTER_MOVE_TIME,cur_dirt,i))
      time.sleep(CENTER_MOVE_TIME)
      #self.set_message('move_to_center, %s: Stopping move' % (camera_string))
      self.telescope.move_direction(direction='q')
      self.__dict__[proc_string]('centering')
      self.set_message('move_to_center, %s: Waiting for image.results_stat bit, iteration %d' % (camera_string,i))
      self.__dict__[proc_string].results_stat.clear()
      #self.__dict__[proc_string].results_stat.wait()
      t_out_ret=self.__dict__[proc_string].results_stat.wait(timeout=MEAS_TIMEOUT)        #Timeout added 6June2018
      if not t_out_ret:  self.__dict__[proc_string].process_thread.stop_measure()  #Timeout condition added 6June2018
      self.set_message('move_to_center, %s: Returned: %r' % (camera_string,self.__dict__[proc_string].center))
      cur_dx=self.__dict__[proc_string].center[1][0]  #This is the dx,dy from defined center
      cur_dy=self.__dict__[proc_string].center[1][1]  #This is the dx,dy from defined center
      cur_ds=self.__dict__[proc_string].center[1][2]  #This is the distance from the defined center
      if cur_ds<last_ds:
        self.set_message('move_to_center, %s: %s' % (camera_string,'Moving in the correct direction'))
      else:  
        if abs(cur_dx)>abs(last_dx):
          self.set_message('cmove_to_center, ur_dx: %r >last_dx: %r, %s' % (cur_dx,last_dx,'Moving wrong X direction'))
          if 'e' in last_dirt:
            #self.set_message('move_to_center, Switching e to w' )
            cur_dirt=last_dirt.replace('e','w')
          if 'w' in last_dirt:
            #self.set_message('move_to_center, Switching w to e' )
            cur_dirt=last_dirt.replace('w','e')
        if abs(cur_dy)>abs(last_dy):
          self.set_message('move_to_center, cur_dy: %r >last_dy %r, %s' % (cur_dy,last_dy,'Moving wrong Y direction'))
          if 'n' in last_dirt:
            #self.set_message('move_to_center, Switching n to s' )
            cur_dirt=last_dirt.replace('n','s')
          if 's' in last_dirt:
            #self.set_message('move_to_center, Switching s to n' )
            cur_dirt=last_dirt.replace('s','n')
      self.set_message('move_to_center, %s: Moving telescope towards %r from last direction %r' % \
        (camera_string,cur_dirt,last_dirt))
      last_dirt=cur_dirt
      i+=1
    self.set_message('move_to_center, %s: %s DONE centering at %r in %d iterations' % \
      (camera_string,camera_string,self.__dict__[proc_string].center,i))
    self.telescope.move_direction(direction='q')
    return
  @_decorator
  def run_seeing(self,number=SEEING_NUMBER):
    ''' <run_seeing>
        <number> Number of measurements
        Runs a seeing measurement.
    '''
#   self.image.process_thread.save_img_flag=True  # Uncomment to save all images from seeing measurements
    self.set_message('##Starting Seeing measurement')
    self.camera.set_binning(1,1)
    hdr=self.build_header()
    self.image.set_image_hdr_parms(**{i.lower():j for i,j in hdr.iteritems()})
    #zdist,drctn,airmass=self.starcat.find_zdist(star=self.starcat.source)
    #self.image.set_image_hdr_parms(source=self.starcat.source.name,ra=str(self.starcat.source.ra),\
    #  dec=str(self.starcat.source.dec),airmass=airmass,az=self.telescope.azimuth[2],\
    #  zdist=zdist,magn=self.starcat.source.mag,\
    #  elv=self.telescope.elevation[2])
    self.image('seeing')
    self.image.results_stat.clear()
    #self.image.results_stat.wait()
    t_out_ret=self.image.results_stat.wait(timeout=MEAS_TIMEOUT)         #Timeout added 6June2018
    if not t_out_ret:  self.image.process_thread.stop_measure()   #Timeout condition added 6June2018
    self.set_message('##Finished with Seeing measurement')
    self.set_message('##After %d accepted measurements, seeing measurement: %r' %\
      (self.image.process_thread.accept_count+self.image.process_thread.reject_count,self.image.seeing))
    self.write_seeing()
    self.camera.set_binning(4,4)
#   self.image.process_thread.save_img_flag=False
    return
  def build_header(self):
    '''<build_header>
       Builds a 'fits' header for the images to include the object, ra, dec, etc...
    '''
    #self.local_date,self.local_time=time.strftime(DTIME_FORMAT).split(',')
    self.get_time()
    hdr=image_proc_thread.imgfile.create_fits_header()
    hdr.set('OBJECT',self.starcat.source.name)
    hdr.set('RA',self.starcat.source.ra)
    hdr.set('DEC',self.starcat.source.dec)
    hdr.set('MAGN',self.starcat.source.mag)
    zdist,drctn,airmass=self.starcat.find_zdist(star=self.starcat.source)
    hdr.set('AIRMASS',airmass)
    hdr.set('ZDIST',zdist)
    hdr.set('AZ',self.telescope.azimuth[2])
    hdr.set('ELV',self.telescope.elevation[2])
    hdr.set('DATE-OBS',self.local_date)
    hdr.set('TIME-OBS',self.local_time)
    return hdr
  def get_time(self):
    ''' <get_time>
        A standard formatted time routine, format given in the common_parms.py file
    '''
#   self.local_date,self.local_time=time.strftime(DTIME_FORMAT).split(',')
    dt_string=datetime.datetime.strftime(datetime.datetime.now(),DTIME_FORMAT_FLT)[:-4]
    self.local_date,self.local_time=dt_string.split(',')
    self.utc_date,self.utc_time=time.strftime(DTIME_FORMAT,time.gmtime()).split(',')
    return
  def set_message(self,msg):
    ''' <set_message>
        Will set the message for display or for whatever else the message is
        to be used, and will log to file if the <self.logging_flag> is True
    '''
    self.get_time()
    self.message='%s %s,  %s' % (self.local_date,self.local_time,msg)
    if self.logging_flag: self.write_to_log(self.message)
    if self.stdout_flag: sys.stdout.write('%s\n' % self.message)
    return
  def write_seeing(self):
    ''' <write_seeing>
          will write to the seeing.log file
    '''
    #seeingfilename=LOG_DIR+'seeing.dat.'+self.local_date.replace('/','.')
    seeingfilename=LOG_DIR+'seeing.dat.'+self.utc_date.replace('/','.')
    self.get_time()
    zdist,direction,airmass=self.starcat.find_zdist(star=self.starcat.source)
    seeing=self.local_time+','+self.local_date
    seeing='%s,%s' % (seeing,self.telescope.sidrtime[2])
    seeing='%s,%s,%s,%s,%s,%s' % (seeing,self.starcat.source.name,str(self.starcat.source.ra),\
      str(self.starcat.source.dec),str(self.telescope.azimuth[2]),str(self.telescope.elevation[2]))
    seeing='%s,%7.4f,%s,%8.5f' % (seeing,zdist,direction,airmass)
    seeing='%s,%7.4f,%7.4f' % (seeing,self.image.dst.mean(),self.image.dst.std())
    seeing='%s,%7.4f,%7.4f,%7.4f,%7.4f' % (seeing,self.image.seeing[0],self.image.seeing[1],\
      self.image.seeing[2],self.image.seeing[3])
    seeing='%s,%d' % (seeing,self.image.process_thread.accept_count)
    seeing='%s,%d\n' % (seeing,self.image.process_thread.reject_count)
    if os.path.exists(seeingfilename): apfile='a'
    else: apfile='w'
    fp=open(seeingfilename,apfile)
    if apfile=='w':
      fp.write('#Seeing log file for %s %s, UTC %s %s\n' % (self.local_time,self.local_date,\
        self.utc_time,self.utc_date))
      fp.write('#\n#\n')
      fp.write('#Local Time, Local Date, Local LST, Source Name, Source RA, Source Dec, Telescope Az, Telescope Elv, ')
      fp.write('Source ZD(rad), Source Airmass,pixel mean distance, pixel distance std,')
      fp.write('eps_long_g, eps_long_z, eps_trans_g, eps_trans_z, number of measurements, number of rejects\n')
      fp.write('#\n#\n')
    fp.write(seeing)#+'\n')
    fp.close()
    self.set_message(seeing)
    self.seeing=seeing
    if self.write_rose_flag: self.report_seeing_to_rose()  #Report measurement to rose.kpno.noao.edu if true
    else: pass
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
      self.logfile_name=os.path.join(fullpath,MNG_LOGBASENAME+'.'+cur_date)
    if os.path.exists(self.logfile_name): appendfile='a'
    else: appendfile='w'
    fp=open(self.logfile_name,appendfile)
    fp.write(arg+'\n')
    fp.close()
    return
  @_decorator
  def test_dimm(self): 
    '''<test_dimm>
       Ultimately, this will be the main running program.  It will set source, move telescope, center finder,
       center seeing camera, box the region, run a seeing measurement, etc...
    '''
    self.chk_conditions_cnt=3001
    self.check_all_running()
    self.last_dimm_measure_done.clear()
    if self.dimm_measure_count_on_src>=DIMM_MEAS_PER_SRC or self.starcat.src_out_status:
      self.set_message('dimm process: Changing Source')
      self.change_source()
    if self.dimm_measure_count_on_src==0:
      self.set_message('dimm process: Setting Finder binning to 4,4')
      self.set_message('dimm process: Running Finder')
      self.run_finder()
      self.set_message('dimm process: Moving to Source')
      self.move_to_source()
      self.stop_finder()
      time.sleep(0.2)
      self.set_message('dimm process: Centering SOURCE to the optical axis')
      self.set_finder_center()
      self.set_message('dimm process: Waiting for finder setting')
      self.proc_done_stat.wait()
    time.sleep(0.2)
    if DIMM_SERVER:
      self.image.process_thread.save_img_flag=True
    self.set_message('dimm process: Running Box Region')
    ### Somewhere in here after the box region, can put if number of objects >=2 then run seeing
    self.image('boxregion',center_type='midpoint')
    self.set_message('dimm process: Waiting for results_stat event')
    self.image.results_stat.clear()  #############NEW 23 Oct 2017
    #self.image.results_stat.wait()
    t_out_ret=self.image.results_stat.wait(timeout=MEAS_TIMEOUT)         #Timeout added 6June2018
    if not t_out_ret:
      self.image.process_thread.stop_measure()   #Timeout condition added 6June2018
      self.set_message('dimm process: TIMEOUT during box region!!')
      self.image.num_objects=0
    time.sleep(0.1)  #Changed back to 0.1sec 8Nov2018
    self.image.process_thread.save_img_flag=False
    if self.image.num_objects>=2:
      self.set_message('dimm process: Taking seeing measurement and waiting for measure_done event')
      self.run_seeing()
      self.proc_done_stat.wait()
    else:
      self.set_message('dimm process: NOT ENOUGH OBJECTS IN CAMERA FOR SEEING MEASUREMENT!!!')
      self.image.reset_box=True
      self.image('boxregion')
#   time.sleep(0.1) #Added 8Nov2018
    self.camera.set_binning(4,4)
    self.camera.set_roi()
#   time.sleep(0.1) #Added 8Nov2018
    self.dimm_measure_count_on_src+=1
    self.last_dimm_measure_done.set()
    return
  @_decorator
  def test_focus(self):
    '''<test_focus>
       This method needs a lot of attention.  The following does not work and should be avoided.  Only after
       the rest of the code, will I be able to get to this.
    '''
    #self.last_dimm_measure_done.clear()
#   i=0
#   self.camera.set_roi()
#   self.camera.set_binning(4,4) 
#   self.set_message('focus process: Running Focus routine, iteration %d' % i)
#   self.image('focusing')
#   self.set_message('focus process: Waiting for results_stat event, iteration %d' % i)
#   self.image.results_stat.clear()
#   #self.image.results_stat.wait()
#   t_out_ret=self.image.results_stat.wait(timeout=MEAS_TIMEOUT)         #Timeout added 6June2018
#   if not t_out_ret:  self.image.process_thread.stop_measure()   #Timeout condition added 6June2018
#   last_xwid,last_ywid,last_ht=self.image.last_focus
#   last_avr_width=(last_xwid+last_ywid)/2.0
#   cur_xwid,cur_ywid,cur_ht=last_xwid,last_ywid,last_ht
#   cur_avr_width=(cur_xwid+cur_ywid)/2.0
#   cur_direction=-1  #To Retract the focus, +1 to advance
#   self.set_message('focus process %d: (x_w,y_w,ht)=(%7.3f,%7.3f,%7.3f)' % (i,cur_xwid,cur_ywid,cur_ht))
#   while cur_avr_width>=last_avr_width and not self.cancel_process_stat.isSet() and i<FOCUS_MOVE_ITER:
#     self.set_message('focus process: Moving telescope focus, iteration %d' % i)
#     #The speed, direction, and sleep time may need to be changed!!!!!
#     self.telescope.move_focus(direction=cur_direction,speed=0)
#     self.set_message('focus process: Sleeping for %5.3fsec while moving, iteration %d' % (FOCUS_MOVE_TIME,i))
#     time.sleep(FOCUS_MOVE_TIME)
#     self.telescope.move_focus(direction=0)
#     self.set_message('focus process: Stopping move')
#     last_xwid,last_ywid,last_ht=cur_xwid,cur_ywid,cur_ht
#     last_avr_width=(last_xwid+last_ywid)/2.0
#     self.set_message('focus process: Running image focus routine, iteration %d' % i)
#     self.image('focusing')
#     self.set_message('focus process: Waiting for results_stat event, iteration %d' % i)
#     self.image.results_stat.clear()
#     #self.image.results_stat.wait()
#     t_out_ret=self.image.results_stat.wait(timeout=MEAS_TIMEOUT)         #Timeout added 6June2018
#     if not t_out_ret:  self.image.process_thread.stop_measure()   #Timeout condition added 6June2018
#     cur_xwid,cur_ywid,cur_ht=self.image.last_focus
#     cur_avr_width=(cur_xwid+cur_ywid)/2.0
#     self.set_message('focus process %d: (x_w,y_w,ht)=(%7.3f,%7.3f,%7.3f)' % (i,cur_xwid,cur_ywid,cur_ht))
#     i+=1
    #self.last_dimm_measure_done.set()
    return
  def test_function(self):
    fp,path,desc=imp.find_module('test_code')
    imp.load_module('test_code',fp,path,desc)
    test_code.test_function(self)
    return
  def report_seeing_to_rose(self):
    ''' <report_seeing_to_rose> This methods attempts to write the seeing measurement to rose.kpno.noao.edu.
                                If it fails, it simply sets a message and ignores writeing to rose.
    '''
    try:
      bstrng='insert into dimm values(NULL,'
      see_list=self.seeing.split(',')
      date_list=see_list[1].split('/')
      rev_date='%s-%s-%s' % (date_list[2],date_list[0],date_list[1])
      see_list[1]=rev_date
      ut_time=time.strftime('%Y-%m-%d,%H:%M:%S',time.gmtime()).split(',')
      map(lambda x: see_list.insert(2,x),iter(ut_time))
      zcorr=cos(float(see_list[10]))**0.6   ###Coreection for the zenith distance, only for reporting to rose...
      fwhm='%7.4f' % ((float(see_list[-3])+float(see_list[-5]))/2.0*zcorr)
      flux='%10.2f' % (self.image.fluxes.mean())
      sstrng='\''+'\',\''.join(see_list)+'\',\''+fwhm+'\',\''+flux+'\''
      estrng=');'
      #The following three lines modified in order to prevent colliding connection access, 25Jan2019.
      self.set_message('Sending \'%s\' to ROSE!!!' % (bstrng+sstrng+estrng))
      if DIMM_SERVER:
        #self.weather.db_connection.cursor.execute(bstrng+sstrng+estrng)
        err=self.weather.db_connection.send(bstrng+sstrng+estrng)
        if err:  self.set_message(err)
      #
      self.set_message('Wrote the seeing measurement ROSE!!!')
    except Exception:
      if DIMM_SERVER:
        self.set_message('COULD NOT WRITE LAST SEEING MEASUREMENT TO ROSE, will try to reconnect  next measurement!!!')
        try: self.weather.db_connection.reconnect()
        except Exception: pass
      pass
    return

