#!/usr/bin/env python generic_thread.py
#
#

import sys
sys.path.append('..')
import threading
import datetime
import time
import imp
import os
from os.path import isfile as fexists
from os.path import join as ospjoin
from os.path import exists as ospexists
from os import listdir,getcwd,makedirs
from filecmp import cmp as fcompare

try:
  from common_parms import *
  THREAD_LOGBASENAME='thread'
  #DTIME_FORMAT='%m/%d/%Y,%H:%M:%S'
  DTIME_FORMAT='%m/%d/%Y,%H:%M:%S.%f'  # Used with datetime formatting
except Exception as err:
  LOG_DIR='./'
  THREAD_LOGBASENAME='thread'
  #DTIME_FORMAT='%m/%d/%Y,%H:%M:%S'
  DTIME_FORMAT='%m/%d/%Y,%H:%M:%S.%f'  # Used with datetime formatting
  pass
THREAD_TIME=0.01

def _decorator(process):
  def proc_wrapper(cls,*args,**kwargs):
    cls.lock.acquire()
    cls.process_done.clear()
    cls.message='#Process started'
    ret=process(cls,*args,**kwargs)
    cls.message='#Process completed'
    cls.process_done.set()
    cls.lock.release()
    return ret
  return proc_wrapper

class generic_thread(threading.Thread):
  def __init__(self,name='thread-1',log=False,prnt=False,sleeptime=THREAD_TIME,utc_flag=False,logname=None):
    threading.Thread.__init__(self)
    self.setName(name)
    self.local_time,self.local_date=None,None
    ''' @ivar: String variables for the local time and date
    '''
    self.cur_loc_time=None
    ''' @ivar: The current local time as a <time.struct_time> object
    '''
    self.utc_flag=utc_flag
    self.get_time()
    self.sleeptime=sleeptime
    ''' @ivar: The defined sleeptime for cycling the thread
    '''
    self.message=''
    ''' @ivar: A message variable
    '''
    self.call_return=''
    ''' @ivar: The function return from a method
    '''
    self.stdout_flag=prnt
    ''' @ivar: A general boolean to indicate whether or not to print to stdoutthe camera parms to file.
    '''
    self.logging_flag=log
    ''' @ivar: A general boolean to indicate whether or not to log the camera parms to file.
    '''
    subdir1=os.path.join(LOG_DIR,time.strftime('%b%Y'))
    fullpath=os.path.join(subdir1,time.strftime('%B%d'))
    if self.logging_flag:
      if not os.path.exists(fullpath): os.makedirs(fullpath)
    if logname:
      self.logfile_name=os.path.join(fullpath,logname+'.'+time.strftime('%m.%d.%Y'))
      ''' @ivar: The logfile name given in the common_parms.py file in the home directory.
      '''
    else:
      self.logfile_name=os.path.join(fullpath,THREAD_LOGBASENAME+'.'+time.strftime('%m.%d.%Y'))
      ''' @ivar: The logfile name given in the common_parms.py file in the home directory.
      '''
    # The following are a set of events to be flagged for processing images
    self.prog_stat=True
    ''' @ivar: A general boolean to start and stop the thread.
    '''
    self.thread_stat=threading.Event()
    ''' @ivar: A threading.Event to start and stop the thread.
    '''
    self.thread_stat.set()
    self.run_proc_event=threading.Event()
    #Used to cancel process only.  It is 'clear' to cancel, 'set' to run
    self.run_proc_event.set()
    self.process_done=threading.Event()
    #Used to indicate that the process is finished
    self.process_done.set()
    self.lock=threading.Lock()
    ''' @ivar: A threading.lock to block the thread processes.
    '''
    self.set_message('%s opened and ready' % (self.name))
    return
  def __repr__(self):
    ss='\n%r in <module %r>' % (self.__class__,self.__module__)
    ss='%sclass isAlive: %r\n' % (ss,self.isAlive())
    return ss
# def _decorator(process):
#   def proc_wrapper(self,*args,**kwargs):
#     self.lock.acquire()
#     self.process_done.clear()
#     self.message='#Process started'
#     process(self,*args,**kwargs)
#     self.message='#Process completed'
#     self.process_done.set()
#     self.lock.release()
#   return proc_wrapper
  def __call__(self,*args,**kwargs):
    process=kwargs.pop('process',None)
    # where process is some instance method of this class
    if process:
      if hasattr(self,process):
        proc_method=self.__getattribute__(process)
        if callable(proc_method):
          proc_method(*args,**kwargs)
      else:
        raise RuntimeError('Unexpected command "{}"; not found'.format(process))
    return self.call_return
  def run(self):
    self.count=0
    self.thread_stat.set()
    while self.prog_stat:
      self.get_time()
      time.sleep(self.sleeptime)
      if self.thread_stat.isSet():# pass
        self.count+=1
      else: 
        self.count=0
    self.set_message('#Thread, %s, Finished' % (self.name))
    self.thread_stat.clear()
    return
  def pause(self):
    '''<pause> will pause the thread running
    '''
    self.thread_stat.clear()
    return
  def cont(self):
    '''<cont> will continue the thread running
    '''
    self.thread_stat.set()
    return
  def stop(self):
    '''<stop> will set the <self.thread_stat> variable to False and stop the thread.
    '''
    self.set_message('#Stopping %s thread!!!!' % (self.name))
    self.thread_stat.clear()
    self.prog_stat=False
    return
  @_decorator
  def module_test(self,*args,**kwargs):
    '''<module_test> can be used to write a test_function which resides in a file
                     called test_code.py.  This will be reloaded without having to re-instantiate 
                     the self object.
    '''
    try:
      fp,path,desc=imp.find_module('test_code')
      imp.load_module('test_code',fp,path,desc)
      ret_test=test_code.test_function(self)
    except Exception as err:
      pass
    return 
  def set_message(self,msg):
    ''' <set_message>
        Will set the message for display or for whatever else the message is 
        to be used, and will log to file if the <self.logging_flag> is True
    '''
    self.get_time()
    if msg[0]=='#': self.message='#%s %s:  %s' % (self.local_date,self.local_time,msg[1:])
    else: self.message='%s %s:  %s' % (self.local_date,self.local_time,msg)
    if self.logging_flag: self.write_to_log(self.message)
    if self.stdout_flag: sys.stdout.write('Message %s\n' % self.message)
    return
  def write_to_log(self,mess,f_basename=None,test_qualifier='-1'):
    ''' <write_to_log> creates/writes to either a log file in dated LOG_DIR subdirectory
        with the given filename,
        <fname>, with image array data, <data>, and the header information, <header>, or to a .jpg file.
        Note: 
        <test_qualifier> is the logfile subdirectory qualifier, if =='-1' will write to the dated LOG_DIR directly.
        if <fname>==None, a name will be defined based on time and date
        if <fmt>=='local' use local time, if <fmt>=='utc' use utc time for logfile time stamp
    '''
    self.get_time()
    fname_date=self.local_date.replace('/','.')
    subdir1=ospjoin(LOG_DIR,time.strftime('%b%Y',time.strptime(self.local_date+','+self.local_time,DTIME_FORMAT)))
    subdir2=ospjoin(subdir1,time.strftime('%B%d',time.strptime(self.local_date+','+self.local_time,DTIME_FORMAT)))
    if test_qualifier!='-1': test_subdir='test-'+str(test_qualifier)
    else: test_subdir=''
    fullpath=ospjoin(subdir2,test_subdir)
    if not ospexists(fullpath): makedirs(fullpath)
    if f_basename: fname='%s.%s.log' % (f_basename,fname_date)
    else: fname='%s.%s.log' % (THREAD_LOGBASENAME,fname_date)
    self.logfile_name=ospjoin(fullpath,fname)
    if ospexists(self.logfile_name): appendfile='a'
    else: appendfile='w'
    fp=open(self.logfile_name,appendfile)
    fp.write(mess+'\n')
    fp.close()
    return
  def get_time(self):
    ''' <get_time>
        A standard formatted time routine, format given in the common_parms.py file
    '''
    if not self.utc_flag:
      #self.local_date,self.local_time=time.strftime(DTIME_FORMAT).split(',') #Local time
      dt_string=datetime.datetime.strftime(datetime.datetime.now(),DTIME_FORMAT)[:-4]
      self.local_date,self.local_time=dt_string.split(',')
    else:
      self.local_date,self.local_time=time.strftime(DTIME_FORMAT,time.gmtime()).split(',') # UTC time
    return
