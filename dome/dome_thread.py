#! /usr/bin/env python dome_thread.py
###
###

import threading
import time
import dome_comms as dcomms
import weather.generic_thread as gth

from common_parms import *
#

DOME_MOTION_STATUS={
  '0':['stopped','stopped',False],
  '1':['closing','stopped',True],
  '2':['opening','stopped',True],
  '4':['stopped','closing',True],
  '8':['stopped','opening',True],
  'x':['unknown','unknown',False]
}
DOME_SWITCH_STATUS={
  '0':['unknown','unknown',False], ### Change to False for close_stat_bit
  '1':['closed','unknown',False], ### Change to False for close_stat_bit
  '2':['opened','unknown',False], ### Change to False for close_stat_bit
  '4':['unknown','closed',False], ### Change to False for close_stat_bit
  '5':['closed','closed',True],
  '6':['opened','closed',False],
  '8':['unknown','opened',False],
  '9':['closed','opened',False],
  'a':['opened','opened',False],
  'x':['unknown','unknown',False]
}
#DOME_THREADTIME=0.5

class DomeThread(gth.generic_thread):
  '''<DomeThread>  inherits the generic_thread.GenericThread class to be used in
     the background for reading and writing to the dome port.
  '''
  def __init__(self,name=None,sleeptime=DOME_THREADTIME,prnt=False,port='-',tty_id='0'):
    '''<__init__> constructs the DomeThread class with the name=<name>
       <sleeptime> is an update time rate, <prnt> is 'True' to print to the std.out,
       and <port> is the port(which could be the output of the function
       <returnSerial>.
    '''
    gth.generic_thread.__init__(self,name=name,log=False,sleeptime=DOME_THREADTIME,prnt=prnt)
    self.time_to_check=20  # The number of cycles to check the status
    self.time_check_cnt=0  # The count of cycles
    self.dome_closed_stat=threading.Event()  #Event to indicate the dome is closed
    '''@ivar: Status of the Dome, can be used to indicate the dome status to other threads '''
    self.dome_closed_stat.clear()
    self.dome_moving_stat=threading.Event()  #Event to indicate the dome is moving
    '''@ivar: Status of the Dome motion, is the dome currently opening or closing one of its leaves'''
    self.dome_moving_stat.clear()
    self.cmd_to_open_stat=threading.Event()  #Event to indicate the dome is supposed to open
    '''@ivar: Event for the Dome to open'''
    self.cmd_to_open_stat.clear()
    self.cmd_to_close_stat=threading.Event()  #Event to indicate the dome is supposed to close
    '''@ivar: Event for the Dome to close'''
    self.cmd_to_close_stat.clear()
    #self.prntOut=prnt
    #'''@ivar: For debugging from a python interpeter'''
    self.port=dcomms.return_port(port=port)
    '''@ivar: The communications port, can be IP, serial/usb, or simulation'''
    self.msg=''             #   for testing.  The msg and cmd are the returned
    '''@ivar: The last message response from the dome'''
    self.msg_list=[]
    '''@ivar: A list of the last fifty messages from the dome'''
    self.last_cmd=''             #   for testing.  The msg and cmd are the returned
    '''@ivar: The last command echo from the dome'''
    self.north_cur_status,self.south_cur_status,junk_bit=DOME_SWITCH_STATUS.get('x')
    self.north_mve_status,self.south_mve_status,junk_bit=DOME_MOTION_STATUS.get('0')
    self.open_close_cntr_str=0
    '''@ivar: Holds values of 0, 1, or 2 for opening and closing'''
    self.dome_status='None'
    #self.cmd=''             #   and the commanded messages from/to the serial port.
    #'''@ivar: The last sent command to the dome'''
    return
  def __repr__(self):
    '''__repr__
       expresses the dome status
    '''
    ss='\n'
    ss='%s<DomeThread> class is Alive? %s\n' % (ss,self.isAlive())
    ss=ss+'\n'
    ss='%sDome closed status:          %r\n' % (ss,self.dome_closed_stat.isSet())
    ss='%sDome moving status:          %r\n' % (ss,self.dome_moving_stat.isSet())
    ss=ss+'\n'
    ss='%sCmd to open status:          %r\n' % (ss,self.cmd_to_open_stat.isSet()) 
    ss='%sCmd to close status:          %r\n' % (ss,self.cmd_to_close_stat.isSet()) 
    ss='%sopen_close_cntr_st:          %d\n' % (ss,self.open_close_cntr_str)
    ss=ss+'\n'
    ss='%sNorth leaf current status:   %s\n' % (ss,self.north_cur_status.zfill(2))
    ss='%sSouth leaf current status:   %s\n' % (ss,self.south_cur_status.zfill(2))
    ss='%sNorth leaf moving status:    %s\n' % (ss,self.north_mve_status.zfill(2))
    ss='%sSouth leaf moving status:    %s\n' % (ss,self.south_mve_status.zfill(2))
    ss='%sMessage:         %r\n' % (ss,self.msg)
    return ss
  def run(self):
    '''run
       Starts the dome thread in the background, will continually monitor the dome
    '''
    self.thread_stat.set()                  # Set "thread_stat"
#   self.send_command('status')
    while self.prog_stat:
      time.sleep(self.sleeptime)       # Sleep for the refresh time
      if self.thread_stat.isSet():
        self.get_time()
        #print self.local_time,self.msg,self.north_mve_status,self.open_close_cntr_str,
          #'North leaf current status:   %s' % (self.north_cur_status.zfill(2))
        #print '>>>>',self.msg,self.south_mve_status,self.open_close_cntr_str,
          #'South leaf current status:   %s' % (self.south_cur_status.zfill(2))
        #self.set_message('%s %s %s %s %s %s %s %s %s' % (self.msg,self.cmd_to_open_stat.isSet(),
        #  self.cmd_to_close_stat.isSet(),self.open_close_cntr_str,self.dome_moving_stat.isSet(),
        #  self.north_mve_status,self.north_cur_status.zfill(2),self.south_mve_status,self.south_cur_status.zfill(2)))
#       if self.time_to_check>=self.time_check_cnt:
        self.read_port()
#         self.time_check_cnt=0
#       else:
#         self.time_check_cnt+=1
        if len(self.msg_list)>50:
          self.msg_list=[self.msg]
        if not self.dome_moving_stat.isSet():
          if self.cmd_to_open_stat.isSet() and self.north_mve_status=='stopped' and self.open_close_cntr_str==1 \
            and self.dome_status=='Mixed':
            self.send_command('sopen')
            self.cmd_to_open_stat.clear()
          if self.cmd_to_close_stat.isSet() and self.south_mve_status=='stopped' and self.open_close_cntr_str==1 \
            and self.dome_status=='Mixed':
            self.send_command('nclose')
            self.cmd_to_close_stat.clear()
        if not self.cmd_to_open_stat.isSet() and not self.cmd_to_close_stat.isSet(): 
          self.open_close_cntr_str=0
        #if self.prntOut: self.printout() # If "prntOut" true the print to std.out
    self.thread_stat.clear()                # Clear the "thread_stat" var at the prog end
    return
  def read_port(self):
    '''read_port
       Reads the port
    '''
#   self.lock.acquire()
    messg='%s' % self.port.read_all()  # Read the serial port message
    self.translate_message(messg)
#   if self.lock.locked():
#     self.lock.release()
    return
  def send_command(self,cmd='status'):
    '''send_command
       Sets the command lock and sends out the command to the dome
    '''
    if cmd in ['nopen','nclose','sopen','sclose'] and  self.dome_moving_stat.isSet():
      #To assure that two motions will not occur simultaneously.
      cmd='status'
    self.lock.acquire()
    self.port.write('%s\x0D\x0A' % cmd)
    if self.lock.locked():
      self.lock.release()
    self.lock.acquire()
    try:
      messg='%s' % self.port.read_all()  # Read the serial port message
    except Exception as err:
      messg=''
    self.translate_message(messg)
    if self.lock.locked():
      self.lock.release()
    if cmd=='stop':
      self.cmd_to_open_stat.clear()
      self.cmd_to_close_stat.clear()
    return
  def translate_message(self,msg):
    if msg!='': 
      msg=msg.translate(None,''.join(['\x02','\x00','\r','\n']))
      msg=msg.lower()
      if 'status' in msg:  msg=msg.replace('status','')
      self.msg_list.append(msg)
      if len(msg)==2:
        self.north_cur_status,self.south_cur_status,close_stat_bit=\
          DOME_SWITCH_STATUS.get(msg[1],DOME_SWITCH_STATUS['x'])
        if self.north_cur_status=='opened' and self.south_cur_status=='opened':
          self.dome_status='Opened'
        elif self.north_cur_status=='closed' and self.south_cur_status=='closed':
          self.dome_status='Closed'
        else:
          self.dome_status='Mixed'
        if close_stat_bit:  self.dome_closed_stat.set()
        else:  self.dome_closed_stat.clear()
        #####
        self.north_mve_status,self.south_mve_status,mve_stat_bit=\
          DOME_MOTION_STATUS.get(msg[0],DOME_MOTION_STATUS['x'])
        if mve_stat_bit:  self.dome_moving_stat.set()
        else:  self.dome_moving_stat.clear()
        self.msg=msg
      elif len(msg)>2:
        #Added this condition 21Aug2019, for serial readback having other messages.
        self.msg=self.msg
        self.last_cmd=self.msg_list[-1]
        #self.msg=self.msg_list[-1][-2:]
        self.msg_list=[]
      else:
        #Added this condition 21Aug2019, if serial readback is corrupted. 
        self.msg=self.msg
        self.msg_list=[]
#     else:
#       self.msg=self.msg_list[-1][-2:]
#       self.msg_list=[]
      if msg:  self.set_message('Last Command Echoed:%s   Last Message Received:%s' % (self.last_cmd,self.msg))
    return
  def open_dome(self):
    '''open_dome
       Opens both leafs of the dome
    '''
    self.cmd_to_open_stat.set()
    self.open_close_cntr_str=1
    self.send_command('nopen')
    self.north_mve_status='moving'
    return
  def close_dome(self):
    '''close_dome
       Closes both leafs of the dome
    '''
    self.cmd_to_close_stat.set()
    self.open_close_cntr_str=1
    self.send_command('sclose')
    self.south_mve_status='moving'
    return
  def stop_dome(self):
    '''stop_dome
       This will immediately stop the dome from moving
    '''
    self.send_command('stop')
    return
  def pauseread(self):
    '''pauseread
       will pause the thread, NOT used in this application
    '''
    self.thread_stat.clear()
    return
  def contread(self):
    '''contread
       will continue running the thread, NOT used in this application.
    '''
    self.thread_stat.set()
    return
  def stop(self):
    try: self.lock.release()
    except Exception as err: pass
    self.set_message('#Stopping Thread!!!!')
    self.thread_stat.clear()
    self.port.closedown()
    self.prog_stat=False
    return
  def change_port(self,port='-'):
    self.pauseread()
    self.port.closedown()
    del self.port
    self.port=dcomms.return_port(port=port)
    self.contread()
    return
# def printout(self):
#   '''printout
#      helpful for testing by writing the port's output message to std.out
#   '''
#   return

