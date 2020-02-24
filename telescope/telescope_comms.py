#! /usr/bin/env python telescope_comms.py
#
import sys
sys.path.append('..')
import thread
import threading
import socket
import serial
import select
import time
from sourceprocs.source_cat_thread import LocationThread
import miscutilities.reset_moxa as rmxa
import ephem
from numpy import pi,radians,linspace

from common_parms import *

progStat=True

class TeleSockPort(socket.socket):
  '''class TeleSockPort
       A client socket set up for the telescope communications
  '''
  def __init__(self,host=TELE_SOCK_HOST,port=TELE_SOCK_PORT,timeout=5.0):
    self.ihost,self.iport=host,port
    socket.socket.__init__(self,socket.AF_INET,socket.SOCK_STREAM)
    try:
      rmxa.reset_moxa(host=self.ihost)
      self.connect((self.ihost,self.iport))
      self.setblocking(0)
      self.settimeout(timeout)
    except Exception:
      print 'CONNECTION could NOT be established!!!'
    return
# def write_meade(self,cmd):
#   rd,wr,ex=select.select([self],[self],[],0)
#   if wr:  self.send(cmd)
#   else: pass
#   ret,b='',''
#   rd,wr,ex=select.select([self],[],[],0)
#   if rd: 
#     while b!='#':
#       b==self.recv(1)
#       ret=ret+b
#   else:
#     ret='0'
#   ret=ret.replace('#','')
#   return ret
  def writeport(self,cmd,size=1024):
    rd,wr,ex=select.select([self],[self],[],0)
    try:
      if wr:  self.send(cmd)
      else: pass
    except Exception as err:
      pass
    if size>=1:
      #ret=self.recv(size)
      rd,wr,ex=select.select([self],[],[],0.1)
      try:
        if rd: ret=self.recv(1024)
        else: ret='-1'
      except Exception as err:
        ret='0'
    else:
      ret='0'
    ret=ret.replace('#','')
    return ret
  def closedown(self):
    self.shutdown(socket.SHUT_RDWR)
    self.close()
    return



class TeleSerialPort(serial.Serial):
  '''class TeleSerialPort
       A serial port set up for the telescope communications
  '''
  def __init__(self,port='s',baud=TELE_SER_BAUD,timeout=0.1):
    # Unless the port is explicitly stated in the call the following
    # will define a port according to the operating system
    self.ihost,self.iport=None,port
    if port=='s':
      port=TELE_SER_PORT
    else:
      port=port
    serial.Serial.__init__(self,port,baud,timeout=timeout)
    return
  def writeport(self,cmd,size=0):
    self.write(cmd)
    if size>=1:
      ret=self.read(size=size)
    elif size==-1:
      ret,b='',''
      while b!='#':
        b=self.read(size=1)
        ret=ret+b
    else:
      ret='0'
    ret=ret.replace('#','')
    #print time.asctime(),cmd,'>>>',size,'>>>',ret
    return ret
  def closedown(self):
    self.shutdown(2)
    self.close()
    return
  def shutdown(self,arg):
    self.close()
    return


class TeleTestPort(threading.Thread):
  '''class TeleTestPort
       Simply a dummy port set up for mock telescope communications
  '''
  def __init__(self):
    self.ihost,self.iport=None,'-'
    threading.Thread.__init__(self)
    self.thread_stat=threading.Event()
    self.observer=ephem.Observer()
    self.observer.name='Home'
    self.observer.lat=ephem.degrees(radians(DIMLAT))
    self.observer.lon=ephem.degrees(radians(DIMLNG))
    self.observer.elevation=DIMELV
    self.cur_az,self.cur_elv='359:30:00','+00:00:00'
    self.cur_ra,self.cur_dec=self.observer.radec_of(self.cur_az,self.cur_elv)
    self.tracking=threading.Event()
    self.tracking.clear()
    self.move_to_status=False
    self.cur_source=ephem.readdb(\
      'Commanded,f|S|M0,'+str(self.cur_ra)+','+str(self.cur_dec)+',0.0,2000.0')
    self.ra_dec()
    self.cmdposition=['359:30:00','+00:00:00','azelv']
    self.start()
    return
  def __repr__(self):
    ss='\nLocation:\n'
    ss=ss+'Name:       %s\n'%(self.observer.name)
    ss=ss+'Latitude:   %s\n'%(str(self.observer.lat))
    ss=ss+'Longitude:  %s\n'%(str(self.observer.lon))
    ss=ss+'Elevation:  %7.3f\n'%(self.observer.elevation)
    ss=ss+'\n'
    ss=ss+'Date/Time:            %s\n'%(self.observer.date)
    ss=ss+'Local Sidereal Time:  %s\n'%(self.observer.sidereal_time())
    ss=ss+'\n'
    ss=ss+'Tracking src/pos:    %s\n'%(str(self.tracking.isSet()))
    ss=ss+'\n'
    ss=ss+'Current Position:    self.cur###       self.cur_source.###\n'
    ss=ss+'Right Ascension:     %s  %s\n'%(str(self.cur_ra).ljust(20),str(self.cur_source.ra))
    ss=ss+'Declination:         %s  %s\n'%(str(self.cur_dec).ljust(20),str(self.cur_source.dec))
    ss=ss+'Azimuth:             %s  %s\n'%(str(self.cur_az).ljust(20),str(self.cur_source.az))
    ss=ss+'Elevation:           %s  %s\n'%(str(self.cur_elv).ljust(20),str(self.cur_source.alt))
    ss=ss+'\n'
    ss=ss+'Command Position:\n'
    ss=ss+'Ra/Az:               %s\n'%(self.cmdposition[0])
    ss=ss+'Dec/Elv:             %s\n'%(self.cmdposition[1])
    ss=ss+'Command Coords:      %s\n'%(self.cmdposition[2])
    return ss
  def run(self):
    self.thread_stat.set()
    while progStat or self.thread_stat.isSet():
      time.sleep(0.1)
      self.observer.date=ephem.now()
      self.cur_source.compute(self.observer)
      if self.tracking.isSet():
        self.ra_dec();self.az_elv()
      else:
        self.cur_ra,self.cur_dec=self.observer.radec_of(self.cur_az,self.cur_elv)
      if self.move_to_status:
        self.move_to_position()
    return
  def writeport(self,cmd,size=0):
    cmd=cmd.replace('*',':').replace('\'',':')
    if cmd[1:3]=='Sz':
      self.cmdposition[0]=cmd[3:-1] #ephem.degrees(cmd[3:-1])*180.0/pi
      self.cmdposition[2]='azelv'
    if cmd[1:3]=='Sa':
      self.cmdposition[1]=cmd[3:-1] #ephem.degrees(cmd[3:-1])*180.0/pi
      self.cmdposition[2]='azelv'
    if cmd[1:3]=='Sr':
      self.cmdposition[0]=cmd[3:-1] #ephem.degrees(cmd[3:-1])*180.0/pi
      self.cmdposition[2]='radec'
    if cmd[1:3]=='Sd':
      self.cmdposition[1]=cmd[3:-1] #ephem.degrees(cmd[3:-1])*180.0/pi
      self.cmdposition[2]='radec'
    if cmd[1:3]=='St':
      self.observer.lat=cmd[3:-1] # Set site latitude
    if cmd[1:3]=='Sg':
      self.observer.lon='-'+cmd[3:-1] # Set site longitude, west longitudes only
    if cmd[1:3]=='MS':  
      self.move_to_status=True
    if cmd[1:3]=='RT':
      if cmd[1:4]=='RT9': self.tracking.clear()
      else: self.tracking.set()
    cmd=cmd[1:3]
    self.observer.date=ephem.now()
    if cmd=='GC': ret=time.strftime('%m/%d/%y')
    elif cmd=='GL': ret=time.strftime('%H:%M:%S')
    elif cmd=='GS': ret=str(self.observer.sidereal_time())
    elif cmd=='GA': ret=str(self.cur_elv)
    elif cmd=='GZ': ret=str(self.cur_az)
    elif cmd=='GD': ret=str(self.cur_dec)
    elif cmd=='GR': ret=str(self.cur_ra)
    elif cmd=='Gt': ret=str(self.observer.lat)
    elif cmd=='Gg': ret=str(self.observer.lon)
    else: ret='1'
    return ret
  def close(self):
    self.thread_stat.clear()
    return
  def shutdown(self,arg):
    return
  def closedown(self):
    self.shutdown(socket.SHUT_RDWR)
    self.close()
    return
  def ra_dec(self):    #Sets the cmd_source to the ra/dec of the commanded pos
    tmplist=self.cur_source.writedb().split(',')
    tmplist[2],tmplist[3]=str(self.cur_ra),str(self.cur_dec)
    self.cur_source=ephem.readdb(','.join(tmplist))
    return
  def az_elv(self):    #Finds the az/elv of an ra/dec at current time
    self.observer.date=ephem.now()
    self.cur_source.compute(self.observer)
    self.cur_az,self.cur_elv=self.cur_source.az,self.cur_source.alt
    return
  def set_cmd_position(self,azra=None,elvdec=None,coords=None):
    if azra: self.cmdposition[0]=azra
    if elvdec: self.cmdposition[1]=elvdec
    if coords: self.cmdposition[2]=coords
    return
  def move_to_position(self):
    if self.cmdposition[2]=='azelv':
      cmd_1,cmd_2=float(ephem.degrees(self.cmdposition[0]))*180.0/pi,\
        float(ephem.degrees(self.cmdposition[1])*180.0/pi)
      cur_1,cur_2=float(ephem.degrees(self.cur_az))*180.0/pi,\
        float(ephem.degrees(self.cur_elv)*180.0/pi)
    if self.cmdposition[2]=='radec':
      cmd_1,cmd_2=float(ephem.hours(self.cmdposition[0]))*180.0/pi/15.0,\
        float(ephem.degrees(self.cmdposition[1])*180.0/pi)
      cur_1,cur_2=float(ephem.hours(self.cur_ra))*180.0/pi/15.0,\
        float(ephem.degrees(self.cur_dec)*180.0/pi)
    steps=10
    step1,step2=linspace(cur_1,cmd_1,steps),linspace(cur_2,cmd_2,steps)
    num=0
    while num<steps:
      if self.cmdposition[2]=='azelv':
        self.cur_az=str(ephem.degrees(radians(step1[num])))
        self.cur_elv=str(ephem.degrees(radians(step2[num])))
        self.cur_ra,self.cur_dec=self.observer.radec_of(self.cur_az,self.cur_elv)
      else:
        self.cur_ra=str(ephem.hours(radians(step1[num]*15.0)))
        self.cur_dec=str(ephem.degrees(radians(step2[num])))
        self.ra_dec();self.az_elv()
      num+=1
      time.sleep(0.5)
    self.move_to_status=False
    return

def return_port(port):
  '''return_port
     Parameters
       <port> is the port through which communications is to be established
              Can be </dev/ttyUSB*> or <s> for usb/serial
              <xxx.xxx.xxx.xxx:966> or <h> for socket where have HOST:PORT
              <filename.ext> for file i/o
              <-> for a test class or simulation mode
    '''
  if port[:-1]=='/dev/ttyUSB' or port=='s':
    if port!='s':
      #print 'Using COM on port: ',port
      port=TeleSerialPort(port=port)
    else:
      #print 'Using COM on port: ',TELE_SER_PORT_LINUX,' or ',TELE_SER_PORT_MACOS
      port=TeleSerialPort(port='s')
  elif port=='-':
    #print 'Using dummy port(testing class) TeleTestPort'
    port=TeleTestPort()
  else:
    if port!='h':
      sockhost,sockport=port.split(':')
      #print 'Using ethernet host, port',sockhost,':',sockport
      port=TeleSockPort(host=sockhost,port=int(sockport))
    else:
      #print 'Using ethernet host, port',SOCK_HOST,':',SOCK_PORT
      port=TeleSockPort(host=TELE_SOCK_HOST,port=TELE_SOCK_PORT)
  return port

