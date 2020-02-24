#! /usr/bin/env python telescope_gui.py
#
'''Module telescope_gui.py
     This module supports the testing of the telescope mount communications.
'''
import sys
sys.path.append('..')

from Tkinter import *
import Pmw as pmw
import platform as pf
#import time
import guis.frame_gui as fg
#import telescope_meade as tthread
#import telescope_astrophysics as tthread
import telescope_thread as tthread

from common_parms import TELE_SLEW_SPEEDS,TELE_CENTER_SPEEDS,TELE_GUIDE_SPEEDS,\
  TELE_TRACK_SPEEDS,TELE_FOCUS_SPEEDS

class MiscFrame(fg.FrameGUI):
  def __init__(self,parent=None,col=0,row=0,colspan=1,rowspan=1):
    self.parent=parent
    self.root=parent.interior()
    self._checkList=[['loggingStat','Logging','horizontal','radiobutton',['False','True'],\
                     self.set_logging,(0,0,1,1,'nsew')]]
    self._emessList=[['emessCmd','',[['entrymessCmd','Manual Cmd/Resp','']],(0,1,3,1,'nsew')]]
    fg.FrameGUI.__init__(self,root=self.root,name='Misc Information',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    self.loggingStat.setvalue(str(self.parent.tele_thread.logging_flag))
    self.emessCmd.component('ring').configure(bd=0,pady=0,padx=0)
    self.emessCmd.component('tag').configure(text='',pady=0,padx=0)
    self.emessCmd.entrymessCmdL.configure(relief='sunken')
    self.emessCmd.entrymessCmdL.configure(wraplength=300)
    self.emessCmd.entrymessCmdC.configure(command=self.send_command)
    return
  def set_logging(self,*tags):
    logging=self.loggingStat.getcurselection()
    if logging=='True': self.parent.tele_thread.logging_flag=True  #Set the boolean for logging
    else: self.parent.tele_thread.logging_flag=False 
    return
  def send_command(self,*tags):
    cmd=self.emessCmd.get_entry('entrymessCmd')
    self.parent.tele_thread.sendcommand(cmd)
    mes=self.parent.tele_thread.msg
    self.emessCmd.set_labels('entrymessCmd',cmd+'>>>'+mes)
    return

class FocusFrame(fg.FrameGUI):
  def __init__(self,parent=None,col=0,row=0,colspan=1,rowspan=1):
    self.parent=parent
    self.root=parent.interior()
    self._optionList=[['focusRate','Focus Speed','Slow',TELE_FOCUS_SPEEDS,self.set_focus,(0,0,3,1,'nsew')]]
    self._buttonList=[['butMovFout','MovFocOut',\
                    '(lambda slf=self,cmd=\'F+\':slf.parent.send_commands(cmd))',(0,2,1,1,'nsew')],\
                    ['butStopF','StopFoc',\
                    '(lambda slf=self,cmd=\'FQ\':slf.parent.send_commands(cmd))',(1,2,1,1,'nsew')],\
                    ['butMovFin','MovFocIn',\
                    '(lambda slf=self,cmd=\'F-\':slf.parent.send_commands(cmd))',(2,2,1,1,'nsew')]]
    fg.FrameGUI.__init__(self,root=self.root,name='Focus Information',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    return
  def set_focus(self,cmd):
    i=TELE_FOCUS_SPEEDS.index(self.focusRate.getvalue())
    self.parent.tele_thread.move_focus(speed=i,direction=0)
    return

class LocationFrame(fg.FrameGUI):
  def __init__(self,parent=None,col=0,row=0,colspan=1,rowspan=1):
    self.parent=parent
    self.root=parent.interior()
    self._emessList=[['emessSite','Site',[['entrymessLAT','Latitude',''],\
                     ['entrymessLNG','Longitude',''],['entrymessELV','Elevation','']],(0,0,3,1,'nsew')]]
    self._buttonList=[['butChgSite','Change Site','(lambda slf=self:slf.set_location())',(0,3,1,1,'nsew')],\
                      ['butRstSite','Reset DIMM','(lambda slf=self:slf.reset_location())',(1,3,1,1,'nsew')]]
    fg.FrameGUI.__init__(self,root=self.root,name='Site Location Information',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    self.configSelf()
    return
  def configSelf(self):
    self.emessSite.component('ring').configure(bd=0,pady=0,padx=0)
    self.emessSite.component('tag').configure(text='',pady=0,padx=0)
    self.emessSite.entrymessLATL.configure(relief='sunken')
    self.emessSite.entrymessLNGL.configure(relief='sunken')
    self.emessSite.entrymessLATC.configure(command=self.set_location)
    self.emessSite.entrymessLNGC.configure(command=self.set_location)
    self.emessSite.entrymessLATC.configure(validate=self.pos_valid)
    self.emessSite.entrymessLNGC.configure(validate=self.pos_valid)
    self.emessSite.entrymessELVL.configure(relief='sunken')
    self.emessSite.entrymessELVC.configure(command=self.set_location)
    self.emessSite.entrymessELVC.configure(validate=self.pos_valid)
    return
  def pos_valid(self,text):
    try:
      temp=text.split(':')
      if len(temp)==3:
        t1=int(temp[0])
        t2=int(temp[1])
        t3=float(temp[2])
        if (t1<361 and t2<=60 and t3<=60.0 and t1>-20 and t2>=0 and t3>=0.0):
          return 1
        else:
          return -1
      else:
        return -1
    except Exception:
      return -1
    return
  def set_location(self,*tags):
    try:
      cmdlong=self.emessSite.get_entry('entrymessLNG')
      if not cmdlong:
        cmdlong=self.parent.tele_thread.tele_location[2]
      cmdlat=self.emessSite.get_entry('entrymessLAT')
      if not cmdlat:
        cmdlat=self.parent.tele_thread.tele_location[1]
      cmdelv=self.emessSite.get_entry('entrymessELV')
      if not cmdelv:
        cmdelv=self.parent.tele_thread.tele_location[3]
      self.parent.tele_thread.change_site(location=[cmdlat,cmdlong,cmdelv])
    except Exception: pass  # This condition is in case the entry is invalid
    return
  def reset_location(self,*tags):
    self.emessSite.set_entry(name='entrymessLNG',text='')
    self.emessSite.set_entry(name='entrymessLAT',text='')
    self.emessSite.set_entry(name='entrymessELV',text='')
    self.parent.tele_thread.change_site(location='reset')
    return

class PositionFrame(fg.FrameGUI):
  def __init__(self,parent=None,col=0,row=0,colspan=1,rowspan=1):
    self.parent=parent
    self.root=parent.interior()
    self._checkList=[['coordStat','Command Coords','horizontal','radiobutton',['Ra/Dec','Az/Elv'],\
                     self.set_coords,(0,1,3,1,'nsew')]]
    self._emessList=[['emessRaAz','Command Position',[['entrymessDcEl','Dec/Elv',''],
                     ['entrymessRaAz','Ra/Az','']],(0,0,3,1,'nsew')]]
    self._buttonList=[['butMovPos','MovToPos','(lambda slf=self:slf.move_to_source())',(0,3,1,1,'nsew')],\
                      ['butReCal','Recalibrate','(lambda slf=self:slf.recalibrate())',(1,3,1,1,'nsew')],\
                      ['butInit','Initialize','(lambda slf=self:slf.initialize())',(2,3,1,1,'nsew')]]
    fg.FrameGUI.__init__(self,root=self.root,name='Commanded Position Information',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    self.configSelf()
    return
  def configSelf(self):
    cmdcoord=self.parent.tele_thread.cmdposition[-1]
    if cmdcoord[0]=='a': self.coordStat.setvalue('Az/Elv')
    else: self.coordStat.setvalue('Ra/Dec')
    self.emessRaAz.component('ring').configure(bd=0,pady=0,padx=0)
    self.emessRaAz.component('tag').configure(text='',pady=0,padx=0)
    self.emessRaAz.entrymessDcElL.configure(relief='sunken')
    self.emessRaAz.entrymessRaAzL.configure(relief='sunken')
    self.emessRaAz.entrymessDcElC.configure(command=self.set_coords)
    self.emessRaAz.entrymessRaAzC.configure(command=self.set_coords)
    self.emessRaAz.entrymessDcElC.configure(validate=self.pos_valid)
    self.emessRaAz.entrymessRaAzC.configure(validate=self.pos_valid)
    return
  def pos_valid(self,text):
    try:
      temp=text.split(':')
      if len(temp)==3:
        t1=int(temp[0])
        t2=int(temp[1])
        t3=float(temp[2])
        if (t1<361 and t2<=60 and t3<=60.0 and t1>-20 and t2>=0 and t3>=0.0):
          return 1
        else:
          return -1
      else:
        return -1
    except Exception:
      return -1
    return
  def set_coords(self,*tags):
    try:
      cmdcoords=self.coordStat.getcurselection()
      if cmdcoords[0]=='R': cmdcoords='radec'
      else: cmdcoords='azelv'
      cmdazra=self.emessRaAz.get_entry('entrymessRaAz')
      if not cmdazra:
        cmdazra=self.emessRaAz.get_labels('entrymessRaAz')
      cmdeldc=self.emessRaAz.get_entry('entrymessDcEl')
      if not cmdeldc:
        cmdeldc=self.emessRaAz.get_labels('entrymessDcEl')
      self.parent.tele_thread.set_cmd_position(az_ra=cmdazra,elv_dec=cmdeldc,\
        coords=cmdcoords)
    except Exception: pass  # This condition is in case the entry is invalid
    return
  def move_to_source(self):
    self.parent.tele_thread.move_to_position()
    return
  def recalibrate(self):
    self.parent.tele_thread.re_calibrate()
    return
  def initialize(self):
    '''<initialize>
    '''
    #Note to self...  init_telescope(lat=<lat>,lng=<lng>,elv=<elv>)
    #  should be used in conjuction with the Location thread for current locations
    self.parent.tele_thread.init_telescope()
    return
class MountFrame(fg.FrameGUI):
  def __init__(self,parent=None,col=0,row=0,colspan=1,rowspan=1):
    self.parent=parent
    self.root=parent.interior()
    self._mesBarList=[['dateStat','Date',15,(0,0,3,1,'nsew')],\
                      ['timeStat','Time',15,(0,1,3,1,'nsew')],\
                      ['lstimeStat','LST Time',15,(0,2,3,1,'nsew')],\
                      ['latStat','Latitude',15,(0,3,3,1,'nsew')],\
                      ['longStat','Longitude',15,(0,4,3,1,'nsew')],\
                      ['elStat','Elevation',15,(0,6,3,1,'nsew')],\
                      ['azStat','Azimuth',15,(0,7,3,1,'nsew')],\
                      ['dcStat','Declination',15,(0,8,3,1,'nsew')],\
                      ['raStat','Right Ascension',15,(0,9,3,1,'nsew')],\
                      ['pierStat','Pier Side',15,(0,10,3,1,'nsew')]]
    self._checkList=[['onsourceStat','On Source','horizontal','radiobutton',\
                      ['On','Off'],None,(0,18,3,1,'nsew')]]
    fg.FrameGUI.__init__(self,root=self.root,name='Mount Information',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    blank1=fg.BlankSpace(self.interior(),row=5,colspan=3)
    return
class MoveFrame(fg.FrameGUI):
  def __init__(self,parent=None,col=0,row=0,colspan=1,rowspan=1):
    self.parent=parent
    self.root=parent.interior()
    self._buttonList=[['mvNWbutton','NW',\
                    '(lambda slf=self,cmd1=\'Mn\',cmd2=\'Mw\':slf.parent.send_commands(cmd1,cmd2))',(0,0,1,1,'nsew')],\
                    ['mvNbutton','N','(lambda slf=self,cmd=\'Mn\':slf.parent.send_commands(cmd))',(1,0,1,1,'nsew')],\
                    ['mvNEbutton','NE','(lambda slf=self,cmd1=\'Mn\',cmd2=\'Me\':slf.parent.send_commands(cmd1,cmd2))',\
                      (2,0,1,1,'nsew')],\
                    ['mvWbutton','W','(lambda slf=self,cmd=\'Mw\':slf.parent.send_commands(cmd))',(0,1,1,1,'nsew')],\
                    ['stopbutton','Stop','(lambda slf=self,cmd=\'Q\':slf.parent.send_commands(cmd))',(1,1,1,1,'nsew')],\
                    ['mvEbutton','E','(lambda slf=self,cmd=\'Me\':slf.parent.send_commands(cmd))',(2,1,1,1,'nsew')],\
                    ['mvSWbutton','SW','(lambda slf=self,cmd1=\'Ms\',cmd2=\'Mw\':slf.parent.send_commands(cmd1,cmd2))',\
                      (0,2,1,1,'nsew')],\
                    ['mvSbutton','S','(lambda slf=self,cmd=\'Ms\':slf.parent.send_commands(cmd))',(1,2,1,1,'nsew')],\
                    ['mvSEbutton','SE','(lambda slf=self,cmd1=\'Ms\',cmd2=\'Me\':slf.parent.send_commands(cmd1,cmd2))',\
                      (2,2,1,1,'nsew')],\
                    ['parkTele','Park','(lambda slf=self,cmd=1:slf.park_telescope(cmd))',(0,4,1,1,'sew')],\
                    ['unparkTele','UnPark','(lambda slf=self,cmd=0:slf.park_telescope(cmd))',(2,4,1,1,'ew')]]
    self._optionList=[['slewRate','Slew Rate','1200x',TELE_SLEW_SPEEDS,self.set_slew,(3,0,1,1,'nsew')],\
                      ['centerRate','Center Rate','12x',TELE_CENTER_SPEEDS,self.set_center,(3,1,1,1,'nsew')],\
                      ['guideRate','Guide Rate','0.5x',TELE_GUIDE_SPEEDS,self.set_guide,(3,2,1,1,'nsew')],\
                      ['trackRate','Tracking','Stop',TELE_TRACK_SPEEDS,self.set_track,(3,3,1,1,'nsew')],\
                      ['parkPos','Park Position','Park Pos 1',['Park Pos 1','Park Pos 2','Park Pos 3'],\
                        None,(3,4,1,1,'nsew')]]
    fg.FrameGUI.__init__(self,root=self.root,name='Motion Control',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    blank1=fg.BlankSpace(self.interior(),row=3,colspan=3)
    return
  def set_slew(self,cmd):
    i=TELE_SLEW_SPEEDS.index(self.slewRate.getvalue())
    self.parent.tele_thread.set_slew(speed=i)
    return
  def set_center(self,cmd):
    i=TELE_CENTER_SPEEDS.index(self.centerRate.getvalue())
    self.parent.tele_thread.set_centering(speed=i)
    return
  def set_guide(self,cmd):
    i=TELE_GUIDE_SPEEDS.index(self.guideRate.getvalue())
    self.parent.tele_thread.set_guiding(speed=i)
    return
  def set_track(self,cmd):
    i=TELE_TRACK_SPEEDS.index(self.trackRate.getvalue())
    if i==3:  i=9   # For NO Tracking
    self.parent.tele_thread.set_track(speed=i)
    return
  def park_telescope(self,*cmd):
    '''<park_telescope>
         Parks or Unparks telescope depending on the cmd.  Both buttons uses this command.  If
         a park command is issued (cmd==1), then the telescope will park.  If an unpark command
         is issued, the telescope will unpark.
    '''
    if cmd[0]: self.parent.tele_thread.park_telescope()
    else: self.parent.tele_thread.unpark_telescope()
    return
#parent=self.nametowidget(self.winfo_parent())

class TelescopeGUI(pmw.Group):
  def __init__(self,root=None,col=0,row=0,colspan=1,rowspan=1,thrd=None):
    self.root=root
    self.tele_thread=thrd
    pmw.Group.__init__(self,self.root,tag_text='Telescope Information:')
    self.component('tag').configure(font=fg.TEXT_BIG)
    self.component('ring').configure(padx=5,pady=5)
    self.mnt_frame=MountFrame(parent=self,colspan=2,rowspan=4)
    self.mve_frame=MoveFrame(parent=self,col=2,row=0,colspan=2,rowspan=2)
    self.pos_frame=PositionFrame(parent=self,col=2,row=2,colspan=2,rowspan=2)
    self.foc_frame=FocusFrame(parent=self,col=0,row=4,colspan=2,rowspan=1)
    self.msc_frame=MiscFrame(parent=self,col=2,row=4,colspan=2,rowspan=1)
#   self.loc_frame=LocationFrame(parent=self,col=0,row=5,colspan=2,rowspan=2)
    self.grid(column=col,row=row,columnspan=colspan,rowspan=rowspan,sticky='nsew')
#   self.get_move_rates()
    self.check_update()
    return
  def check_update(self):
    self.mnt_frame.timeStat.message('state','%s' % self.tele_thread.localtime[2])
    self.mnt_frame.dateStat.message('state','%s' % self.tele_thread.localdate[2])
    self.mnt_frame.lstimeStat.message('state','%s' % self.tele_thread.sidrtime[2])
    self.mnt_frame.latStat.message('state','%s' % self.tele_thread.sitelat[2])
    self.mnt_frame.longStat.message('state','%s' % self.tele_thread.sitelong[2])
    self.mnt_frame.elStat.message('state','%s' % self.tele_thread.elevation[2])
    self.mnt_frame.azStat.message('state','%s' % self.tele_thread.azimuth[2])
    self.mnt_frame.dcStat.message('state','%s' % self.tele_thread.declination[2])
    self.mnt_frame.raStat.message('state','%s' % self.tele_thread.rightasc[2])
    self.mnt_frame.pierStat.message('state','%s' % self.tele_thread.pierstat[2])
    self.pos_frame.emessRaAz.set_labels(name='entrymessRaAz',text=self.tele_thread.cmdposition[0])
    self.pos_frame.emessRaAz.set_labels(name='entrymessDcEl',text=self.tele_thread.cmdposition[1])
#   self.loc_frame.emessSite.set_labels(name='entrymessLAT',text='%s' % self.tele_thread.sitelat[2])
#   self.loc_frame.emessSite.set_labels(name='entrymessLNG',text='%s' % self.tele_thread.sitelong[2])
#   self.loc_frame.emessSite.set_labels(name='entrymessELV',text='%s' % self.tele_thread.tele_location[3])
    self.get_on_src_stat()
    self.get_park_stat()
    self.get_move_rates()
    self.after(10,self.check_update)
    return
  def get_on_src_stat(self):
    if self.tele_thread.on_source_stat.isSet():
      self.mnt_frame.onsourceStat.setvalue('On')
    else:
      self.mnt_frame.onsourceStat.setvalue('Off')
    return
  def get_park_stat(self):
    if self.tele_thread.park_stat.isSet():
      self.mve_frame.unparkTele.configure(state='normal')
    else:
      self.mve_frame.unparkTele.configure(state='disable')
    return
  def get_move_rates(self):
    self.mve_frame.guideRate.setvalue(TELE_GUIDE_SPEEDS[self.tele_thread.tele_speeds[2]])
    self.mve_frame.centerRate.setvalue(TELE_CENTER_SPEEDS[self.tele_thread.tele_speeds[3]])
    self.mve_frame.slewRate.setvalue(TELE_SLEW_SPEEDS[self.tele_thread.tele_speeds[1]])
    if self.tele_thread.tele_speeds[0]==9:
      self.mve_frame.trackRate.setvalue(TELE_TRACK_SPEEDS[3])
    else:
      self.mve_frame.trackRate.setvalue(TELE_TRACK_SPEEDS[self.tele_thread.tele_speeds[0]])
    self.foc_frame.focusRate.setvalue(TELE_FOCUS_SPEEDS[self.tele_thread.focus_speed])
    return
  def send_commands(self,*cmd):
    for each in cmd:
      self.tele_thread.sendcommand(each)
    return

def stopProgs():
  ''' Will close the root window and kill all threads using the progStat variable '''
  global root
  if 'root' in globals():
    print 'Killing root GUI'
    root.destroy()
  tthread.progStat=False
  tthread.tcomms.progStat=False
  print 'Sucessfully exited'
  return


if __name__=='__main__':
  #use -p <port> option 'h' or 'xxx.xxx.xxx.xxx:pppp' for network or 's' or '/dev/ttyUSB0'
  #for serial port, '-' for simulation mode,  '-' is default
  #use -m <mount> option for 'Meade' or 'Astro-physics', Astro-physics is default
  try:
    pindex=sys.argv.index('-p')+1
    port=sys.argv[pindex]
  except Exception:
    port='-'   #For simulation mode
  try:
    mindex=sys.argv.index('-m')+1
    mount=sys.argv[mindex]
  except Exception:
    mount='S'   #For simulation mode
  root=Tk()
  root.protocol('WM_DELETE_WINDOW',stopProgs)
  telethread=tthread.TelesThread(name='rdg',prnt=False,port=port,log=False,\
    mount=mount)
  telethread.start()
  tgui=TelescopeGUI(root=root,row=1,thrd=telethread)
  xx=Button(root,text='Exit',font=fg.TEXT_FONT,command=stopProgs,\
    width=6,padx=0,pady=0)
  xx.grid(column=0,row=0,sticky='nw')
  root.mainloop()
