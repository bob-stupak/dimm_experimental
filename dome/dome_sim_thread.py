#! /usr/bin/env python dome_sim_thread.py
###
###

import time
import threading

'''
The following are the NEW AstroHaven commands via RS-232 to the PLC for control
of the opening and closing of the dome.  This is the new protocol for the dome.
The old commands and replies are in parenthesis.

Lap top commands:
  'nclose'=moves LEFT shutter UP (A), Close North
  'nopen'=moves LEFT shutter DOWN (a), Open North
  'sclose'=moves RIGHT shutter UP (B), Close South
  'sopen'=moves RIGHT shutter DOWN (b), Open South
  'stop'=Stop the dome opening or closing either side, NEW added command to plc
  'status'=Dome Status, NEW added command to plc
The PLC responses issued on a status command from client, replies binary for the switches as follows:
<north open><north close><south open><south close>  for example
  0b0101  0x5  North is closed(top) and South is closed(top)
  0b1001  0x9  North is opened(bottom) and South is closed(top)
  0b0110  0x6  North is closed(top) and South is opened(bottom)
  0b1010  0xa  North is opened(bottom) and South is opened(bottom)

  Can use >>>hex(int('0x%s' % inp,16))  to return the hexnumber from a string character
          >>>bin(int('0x%s' % inp,16))  to return the binary number from a string character

NOTE!!!!: These bit for the switches and motion indication are reversed for the simulation code since
the PLC sends the binary bit with the least significant bit first.

Some things to note:

A note about serial port comms in Linux:
on Linux have to use from command line or put inside the file /etc/modules
 >> lsusb  # to get the BUS, DEVICE, and the ID
 >> sudo modprobe usbserial vendor=0x<vvvv> product=0x<pppp>
    ### where <vvvv> is the four digit vendor number
    ### and   <pppp> is the four digit product number
    ### for the XS8801 usb to serial cable <vvvv>=0402 and <pppp>=6001
### also the command 'dmesg' will give the device that the device is on ie. ttyUSB0
### also the command 'sudo chmod a+rwx /dev/ttyUSB0' will change the permissions

 to list all com ports use listP.comports()
 to define serial port use ser=serial.Serial('/dev/cu.usbserial-A7032WWB',\
  9600,timeout=1)
'''

class DomeTestPort(threading.Thread):
  '''class:  DomeTestPort
       a class to mimic the DIMM dome behaviour.
  '''
  def __init__(self):
    ''' Initially sets dome to a closed position with both shutters
        Defines a list which represents the position of the shutters
        ie.  self.north=['x','0','1',....,'61','62','X']
    '''
    threading.Thread.__init__(self)
    self.ihost,self.iport=None,'-'
    self.cmd=''
    self.thread_stat=threading.Event()
    self.thread_stat.set()
    self.c_lock=threading.Lock()
    self.ihost,self.iport=None,'-'
    self.pmax=25  # The maximum number of positions along the shutter
    self.north=['x']+list(range(self.pmax))+['X']#the opened state is lowercase while the 
    self.n_position=self.pmax+1  # Initially the north shutter closed
    self.south=['y']+list(range(self.pmax))+['Y']#the opened state is lowercase while the 
    self.s_position=self.pmax+1
    self.position=str(self.north[self.n_position])+str(self.south[self.s_position]) #a position string
    self.north_opened_sw=False
    self.north_closed_sw=True
    self.south_opened_sw=False
    self.south_closed_sw=True
    self.north_opening_stat=False
    self.north_closing_stat=False
    self.south_opening_stat=False
    self.south_closing_stat=False
    self.send_status_count=0
    self.send_status_total=25
    self.start()
    return
  def __repr__(self):
    msg=self.status()
    ss='\n%r in <module %r>' % (self.__class__,self.__module__)
    ss='%sclass isAlive: %r\n' % (ss,self.isAlive())
    ss='%s\nthread_stat:%r, ihost:%s, iport:%r\n' % (ss,self.thread_stat.isSet(),self.ihost,self.iport)
    ss='%snorth:%r,n_position:%s\n' % (ss,self.north,self.n_position)
    ss='%ssouth:%r,s_position:%s\n' % (ss,self.south,self.s_position)
    ss='%sposition:%s\n' % (ss,self.position)
    ss='%snorth_opened_sw:%s\n' % (ss,self.north_opened_sw)
    ss='%snorth_closed_sw:%s\n' % (ss,self.north_closed_sw)
    ss='%ssouth_opened_sw:%s\n' % (ss,self.south_opened_sw)
    ss='%ssouth_closed_sw:%s\n' % (ss,self.south_closed_sw)
    ss='%snorth_opening:%s\n' % (ss,self.north_opening_stat)
    ss='%snorth_closing:%s\n' % (ss,self.north_closing_stat)
    ss='%ssouth_opening:%s\n' % (ss,self.south_opening_stat)
    ss='%ssouth_closing:%s\n' % (ss,self.south_closing_stat)
    if self.position=='XY': ss='%s\nDome Status: CLOSED' % ss
    elif self.position=='xy': ss='%s\nDome Status: OPENED' % ss
    else: ss='%s\nDome Status: MIXED' % ss
    ss='%s\nMessage: %r%r' % (ss,msg[0],msg[1])
    return ss
  def __call__(self,*args,**kwargs):
    if hasattr(self,args[0]):
      proc_method=self.__getattribute__(args[0])
      if callable(proc_method):
        retn=proc_method(*args[1:],**kwargs)
    else:
      raise RuntimeError('Unexpected command "{}"; not found'.format(args[0]))
    return retn
  def run(self):
    # This acts as the plc should.  The thread will run checking its on status (the switches and comms inputs).
    # If a command is received from the comms then it will execute the command.  If the command string <self.cmd>
    # is none, this simulation will only check its own status.  The status is only send out to comms if a 'ss'
    # command is received.
    while self.thread_stat.isSet():
      time.sleep(0.1)
      self.c_lock.acquire()
      if self.cmd:
        self.__call__(self.cmd)
      if self.send_status_count>=self.send_status_total:
        #print 'checking status'
        self.check_stat()
        self.send_status_count=0
      else: self.send_status_count+=1
      self.c_lock.release()
    return
  def stop_thread(self):
    self.thread_stat.clear()
    return
  def move(self,shutter='north',direction='O'):
    ''' move adjusts the self.n_position or self.s_position in the direction for the given shutter
        if the end or beginning of the list is hit (representing the closed or opened
        state, move will switch the current and last known switch states.
        tmpL and tmpR variables are list indices used to compare the previous position
        while lastL and lastR variables are the previous last switch state variables
    '''
    time.sleep(0.1)
    if shutter=='north':              # Left shutter
      if direction=='O':             # Open: list index down by one
        self.n_position-=1
        self.north_opening_stat=True
      elif direction=='C':
        self.n_position+=1                 # Close: move list index up by one
        self.north_closing_stat=True
      else: pass
      if self.n_position>=self.pmax+1:     # if n_position is greater than max set to max
        self.n_position=self.pmax+1
        self.north_closing_stat=False
      if self.n_position<=0:               # if n_position is less than 0 set to 0
        self.n_position=0
        self.north_opening_stat=False
    elif shutter=='south':
      if direction=='O':
        self.s_position-=1
        self.south_opening_stat=True
      elif direction=='C':
        self.s_position+=1
        self.south_closing_stat=True
      else: pass
      if self.s_position>=self.pmax+1:
        self.s_position=self.pmax+1
        self.south_closing_stat=False
      if self.s_position<=0:
        self.s_position=0
        self.south_opening_stat=False
    else: pass
    return
  def check_stat(self):
    self.position=str(self.north[self.n_position])+str(self.south[self.s_position]) #a position string
    #The North Switches inputed into the PLC simulation
    if self.position[0]=='X':
      self.north_closed_sw=True
      self.north_opened_sw=False
      if self.cmd:
        if self.cmd[1]=='n':
          self.cmd=''
    elif self.position[0]=='x':
      self.north_closed_sw=False
      self.north_opened_sw=True
      if self.cmd:
        if self.cmd[1]=='n':
          self.cmd=''
    else:
      self.north_closed_sw=False
      self.north_opened_sw=False
    #The South Switches inputed into the PLC simulation
    if self.position[-1]=='Y':
      self.south_closed_sw=True
      self.south_opened_sw=False
      if self.cmd:
        if self.cmd[1]=='s':
          self.cmd=''
    elif self.position[-1]=='y':
      self.south_closed_sw=False
      self.south_opened_sw=True
      if self.cmd:
        if self.cmd[1]=='s':
          self.cmd=''
    else:
      self.south_closed_sw=False
      self.south_opened_sw=False
    return
  def nopen(self):
    # Open north one step
    self.cmd='nopen'
    self.move(shutter='north',direction='O')
    return
  def nclose(self):
    # Close north one step
    self.cmd='nclose'
    self.move(shutter='north',direction='C')
    return
  def sopen(self):
    # Open south one step
    self.cmd='sopen'
    self.move(shutter='south',direction='O')
    return
  def sclose(self):
    # Close south one step
    self.cmd='sclose'
    self.move(shutter='south',direction='C')
    return
  def stop(self):
    # Stop any motion
    self.cmd=''
    self.north_opening_stat=False
    self.north_closing_stat=False
    self.south_opening_stat=False
    self.south_closing_stat=False
    return
  def status(self):
    # Get status and send out through comms
    self.check_stat()
    ret_str2=['0b','0','0','0','0']
    if self.north_closed_sw==True:  ret_str2[4]='1'
    if self.north_opened_sw==True:  ret_str2[3]='1'
    if self.south_closed_sw==True:  ret_str2[2]='1'
    if self.south_opened_sw==True:  ret_str2[1]='1'
    ret_str1=['0b','0','0','0','0']
    if self.north_opening_stat==True:  ret_str1[3]='1'
    if self.north_closing_stat==True:  ret_str1[4]='1'
    if self.south_opening_stat==True:  ret_str1[1]='1'
    if self.south_closing_stat==True:  ret_str1[2]='1'
    return hex(int(''.join(ret_str1),2)),hex(int(''.join(ret_str2),2)) #Need to return something for status check
  def readport(self):
    msg=self.status()
    return '%r%r' % msg 
    #msg=msg.split('\'\'')
    #ss='%s%s' % (msg[0].replace('0x','').replace('\'',''),msg[1].replace('0x','').replace('\'',''))
    #return ss
  def read_all(self):
    msg='%r%r' % self.status()
    return '%r%r' % msg 
    #msg=msg.split('\'\'')
    #ss='%s%s' % (msg[0].replace('0x','').replace('\'',''),msg[1].replace('0x','').replace('\'',''))
    #return ss
  def writeport(self,cmd):
    cmd=cmd.rstrip('\r\n')
    if cmd in ['nopen','nclose','sopen','sclose','stop','status']:
      self.__call__(cmd)
    return cmd
  def write(self,cmd):
    cmd=cmd.rstrip('\r\n')
    if cmd in ['nopen','nclose','sopen','sclose','stop','status']:
      self.__call__(cmd)
    return cmd
  def closedown(self):
    self.stop_thread()
    return
  def close(self):
    self.stop_thread()
    return
  def shutdown(self):
    return
