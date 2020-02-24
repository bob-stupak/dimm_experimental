#! /usr/bin/env python dome_thread.py
###
###

import platform
import sys
import socket
import serial
import time

from common_parms import *
import select
import dome_sim_thread as dst
import miscutilities.reset_moxa as rmxa

'''
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

class DomeSockPort(socket.socket):
  '''<DomeSockPort> is a client socket set up for the telescope communications
  '''
  def __init__(self,host=DOME_SOCK_HOST,port=DOME_SOCK_PORT,timeout=5.0):
    self.ihost,self.iport=host,port
    socket.socket.__init__(self,socket.AF_INET,socket.SOCK_STREAM)
    try:
      rmxa.reset_moxa(host=self.ihost)
      self.connect((self.ihost,self.iport))
      self.settimeout(timeout)
    except Exception:
      print 'CONNECTION could NOT be established!!!'
    return
  def read_all(self):
    try:
      ret=self.recv(1024)
    except Exception as err:
      ret=''
    return ret
  def write(self,cmd,size=1):
    self.send(cmd)
    ret='o'
    return ret
  def closedown(self):
    self.shutdown(socket.SHUT_RDWR)
    self.close()
    return
class DomeSerialPort(serial.Serial):
  '''<TeleSerialPort> is a serial port set up for the telescope communications
  '''
  def __init__(self,port='s',baud=DOME_SER_BAUD,timeout=5.0):
    # Unless the port is explicitly stated in the call the following
    # will define a port according to the operating system
    self.ihost,self.iport=None,port
    if port=='s':
      if platform.system()=='Linux':
        port=DOME_SER_PORT_LINUX
      else:
        port=DOME_SER_PORT_MACOS
    else:
      port=port
    serial.Serial.__init__(self,port,baud,timeout=timeout)
    return
  def readport(self):
    ret=self.read()
    return ret
  def writeport(self,cmd,size=1):
    ret=self.write(cmd)
    return
  def closedown(self):
    self.shutdown(2)
    self.close()
    return
  def shutdown(self,arg):
    self.close()
    return

class DomeTestPort(dst.DomeTestPort):
  '''class:  DomeTestPort
       a class to mimic the DIMM dome behaviour.
  '''
  def __init__(self):
    ''' Initially sets dome to a closed position with both shutters
        Defines a list which represents the position of the shutters
        ie.  self.left=['x','0','1',....,'61','62','X']
    '''
    dst.DomeTestPort.__init__(self)
    self.ihost,self.iport=None,'-'
    self.cmd=''
    return
  def read_all(self):
    ''' returns the current status to simulate the serial return from the dome
    '''
    msg=self.readport()
    msg=msg.split('\'\'')
    ss='%s%s' % (msg[0].replace('0x','').replace('\'',''),msg[1].replace('0x','').replace('\'',''))
    return ss
  def write(self,cmd=''):
    ''' returns the command, the function will send one command to the move function
    '''
    return self.writeport(cmd)
  def closedown(self):
    self.stop_thread()
    return
  def close(self):
    self.stop_thread()
    return

def return_port(port):
  '''<port> is the port through which communications is to be established
            Can be </dev/ttyUSB*> or <s> for usb/serial
                   <xxx.xxx.xxx.xxx:966> or <h> for socket where have HOST:PORT
                   <filename.ext> for file i/o
                   <-> for a test class or simulation mode
    '''
  if port[:-1]=='/dev/ttyUSB' or port=='s':
    if port!='s':
      port=DomeSerialPort(port=port)
    else:
      port=DomeSerialPort(port='s')
  elif port=='-':
    port=DomeTestPort()
  else:
    if port!='h':
      sockhost,sockport=port.split(':')
      port=DomeSockPort(host=sockhost,port=int(sockport))
    else:
      port=DomeSockPort(host=DOME_SOCK_HOST,port=DOME_SOCK_PORT)
      #port=DomeSockPort(host='192.168.127.254',port=DOME_SOCK_PORT)
  return port

