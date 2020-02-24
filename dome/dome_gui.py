#! /usr/bin/env python dome_gui.py
###
###

import sys
sys.path.append('..')

from Tkinter import *
import Pmw as pmw
import guis.frame_gui as fg
import dome_thread as dthread

'''
'''
DOME_COMMS_LIST=['network','serial','simulation']

class DomeGUI(fg.FrameGUI):
  ''' DomeGUI is the class that runs the dome control.  The serial port
      is an attribute of this class and runs in the background.  The class
      monitors the state of the switches along with sending the commands.
  '''
  __module__='dome_gui'
  mesLog=[]
  def __init__(self,root=None,col=0,row=0,colspan=1,rowspan=1,thrd=None):
    self.domethread=thrd
    self._mesBarList=[
      ['domeStatus','Dome Status',15,(0,1,3,1,'nsew')],\
      ['curNorthStatus','Cur North Pos',15,(0,10,3,1,'nsew')],\
      ['curSouthStatus','Cur South Pos',15,(0,11,3,1,'nsew')],\
      ['northMovingStatus','N Move Status',15,(0,12,3,1,'nsew')],\
      ['southMovingStatus','S Move Status',15,(0,13,3,1,'nsew')],\
      ['messageString','Message',15,(0,30,3,1,'nsew')],\
      ['OpenCloseString','open close',15,(0,29,3,1,'nsew')],\
#     ['msgListString','MsgList[-1]',15,(0,16,3,1,'nsew')],\
#     ['msgListString','MsgList[-1]',15,(0,16,3,1,'nsew')],\
#     ['msgListLenString','MsgListLen',15,(0,17,3,1,'nsew')],\
      ]
    self._buttonList=[
      ['openButton','Open','lambda s=self: s.openDome()',(0,22,1,1,'nw')],\
      ['closeButton','Close','lambda s=self: s.closeDome()',(2,22,1,1,'ne')],\
      ['openNorth','NOpen','lambda s=self: s.domethread.send_command(\'nopen\')',(0,20,1,1,'nw')],\
      ['closeNorth','NClose','lambda s=self: s.domethread.send_command(\'nclose\')',(2,20,1,1,'ne')],\
      ['openSouth','SOpen','lambda s=self: s.domethread.send_command(\'sopen\')',(0,21,1,1,'nw')],\
      ['closeSouth','SClose','lambda s=self: s.domethread.send_command(\'sclose\')',(2,21,1,1,'ne')],\
      ['stopButton','Stop','lambda s=self: s.domethread.send_command(\'stop\')',(1,26,1,1,'ne')],\
      ['cStatButton','Check Stat','lambda s=self: s.domethread.send_command(\'status\')',(1,25,1,1,'ne')]
      ]
    self._eventlist=['Thread Alive','thread_stat','dome_closed_stat','dome_moving_stat',\
      'cmd_to_open_stat','cmd_to_close_stat']
    if str(self.domethread.port.iport)=='-':  opt_dft='simulation'
    elif str(self.domethread.port.iport)=='s':  opt_dft='serial'
    else:  opt_dft='network'
    self._optionList=[['Comms','Port Type',opt_dft,DOME_COMMS_LIST,self.change_comms,(0,45,3,1,'nsew')]]
    self._indicatorList=[['allEvents','Dome Events',self._eventlist,(0,50,3,1,'nsew')]
                        ]
    fg.FrameGUI.__init__(self,root=root,name='Dome Control',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    self.messageString.component('entry').configure(relief='flat')
    if str(self.domethread.port.iport)=='-':  self.component('hull').configure(bg='Red')
    self.check_update()
    return
  def check_update(self):
    ''' check_update: updates the GUI to reflect the current status of the dome
    '''
    self.allEvents.set_indicator('Thread Alive',self.domethread.isAlive())
    self.allEvents.set_indicator('thread_stat',self.domethread.thread_stat.isSet())
    self.allEvents.set_indicator('dome_closed_stat',self.domethread.dome_closed_stat.isSet())
    self.allEvents.set_indicator('dome_moving_stat',self.domethread.dome_moving_stat.isSet())
    self.allEvents.set_indicator('cmd_to_open_stat',self.domethread.cmd_to_open_stat.isSet())
    self.allEvents.set_indicator('cmd_to_close_stat',self.domethread.cmd_to_close_stat.isSet())
    self.curNorthStatus.message('state','%s' %  self.domethread.north_cur_status.zfill(2))
    self.curSouthStatus.message('state','%s' %  self.domethread.south_cur_status.zfill(2))
    self.northMovingStatus.message('state','%s' %  self.domethread.north_mve_status.zfill(2))
    self.southMovingStatus.message('state','%s' %  self.domethread.south_mve_status.zfill(2))
    self.messageString.message('state','%s' %  self.domethread.msg)
    self.OpenCloseString.message('state','%d' %  self.domethread.open_close_cntr_str)
    self.domeStatus.message('state','%s' % self.domethread.dome_status)
#   self.msgListLenString.message('state','%d' %  len(self.domethread.msg_list))
#   if len(self.domethread.msg_list)>0:
#     self.msgListString.message('state','%s' %  self.domethread.msg_list[-1])
    self.after(1,self.check_update)
    return
  def openDome(self):
    self.domethread.open_dome()
    return
  def closeDome(self):
    self.domethread.close_dome()
    return
  def change_comms(self,event):
    i=DOME_COMMS_LIST.index(self.Comms.getvalue())
    if i==0:
      self.domethread.change_port(port='h')
      self.component('hull').configure(bg='#d9d9d9')
    elif i==1:
      self.domethread.change_port(port='s')
      self.component('hull').configure(bg='#d9d9d9')
    else:  
      self.domethread.change_port(port='-')
      self.component('hull').configure(bg='Red')
    return
  def writeLog(self):
    #fp=open('dome.log','w')
    #fp.write('\n'.join(self.mesLog))
    #fp.close()
    return
  def stopAll(self):
    self.domethread.stop()
    return

def stopProgs():
  ''' Will close the root window and kill all threads using the progStat variable '''
  global root,dgui
  if 'root' in globals():
    print 'Killing root GUI'
    root.destroy()
  dgui.stopAll()
  print 'Sucessfully exited'
  return

if __name__=='__main__':
  #use -p <port> option 'h' or 'xxx.xxx.xxx.xxx:pppp' for network or 's' or '/dev/ttyUSB0'
  #for serial port
  try:
    pindex=sys.argv.index('-p')+1
    port=sys.argv[pindex]
  except Exception:
    port='-'   #For simulation mode
  root=Tk()
  root.protocol('WM_DELETE_WINDOW',stopProgs)
  domethread=dthread.DomeThread(sleeptime=0.1,prnt=False,port=port)
  domethread.start()
  dgui=DomeGUI(root=root,row=1,colspan=3,thrd=domethread)
  xx=Button(root,text='Exit',font=fg.TEXT_FONT,command=stopProgs,\
    width=6,padx=0,pady=0)
  xx.grid(column=0,row=0,sticky='nw')
  root.mainloop()
