# Usage 
# python tk_kpno_weather.py 
from Tkinter import *
import Pmw as pmw

import time
import sys
sys.path.append('..')

import guis.frame_gui as fg
import weather_data_class as wdc

EMPTYCMD='\'\''   #Use for <command> if no command is required in the configurations
TEXT_FONT='Times -16'
TEXT_LRG='Times -18'
TEXT_BIG='Times -20'

class WeatherClientGUI(fg.FrameGUI):
  def __init__(self,root=None,col=0,row=1,colspan=1,rowspan=1,thrd=None):
    if root: self.root=root
    else: self.root=Tk()
    if thrd:
      self.thread=thrd
    else:
      self.thread=wdc.weather_thread(prnt=False,log=False)
      self.thread.start()
    fg.FrameGUI.__init__(self,root=root,roottitle='Weather Information',name='Latest Weather Data',\
      col=col,row=row,colspan=colspan,rowspan=rowspan)
    self._mesBarList=[['date_time','Date and Time',20,(1,1,1,1,'nsew')],\
                      ['beg_civ_twilgt','Begin Civil Twilight',20,(1,2,1,1,'nsew')],\
                      ['end_civ_twilgt','End Civil Twilight',20,(1,3,1,1,'nsew')]]
    self._mesFrameList=[['mayall','Mayall Frame',['temperature','dewpoint','humidity',\
                         'windspeed','winddirection'],(0,5,1,1,'nsew')],\
                        ['wiyn','WIYN Frame',['temperature','dewpoint','humidity',\
                         'windspeed','winddirection'],(1,5,1,1,'nsew')],\
                        ['twometer','Two Meter Frame',['temperature','dewpoint','humidity',\
                         'windspeed','winddirection'],(2,5,1,1,'nsew')]]
    self._indicatorList=[['connections','Connections',['Rose-Connection','time_good','domes_opened',\
                          'weather_good'],(0,1,1,4,'nsew')]]
    self.regridSelf()
    self.check_update()
    return
  def check_update(self):
    self.connections.set_indicator('Rose-Connection',self.thread.db_connection.connection_status)
    self.connections.set_indicator('time_good',self.thread.time_good)
    self.connections.set_indicator('domes_opened',self.thread.domes_opened)
    self.connections.set_indicator('weather_good',self.thread.weather_good)
    self.date_time.message('state','%s %s' % (self.thread.local_date,self.thread.local_time))
    self.beg_civ_twilgt.message('state','%s' % (self.thread.location.beg_civil_twilight))
    self.end_civ_twilgt.message('state','%s' % (self.thread.location.end_civil_twilight))
    if self.thread.mayl.data_dict:
      self.mayall.set_message('temperature','%7.3f' % float(self.thread.mayl.data_dict['air_temperature'].mean()))
      self.mayall.set_message('dewpoint','%7.3f' % float(self.thread.mayl.data_dict['dew_point'].mean()))
      self.mayall.set_message('humidity','%7.3f' % float(self.thread.mayl.data_dict['humidity'].mean()))
      self.mayall.set_message('windspeed','%7.3f' % float(self.thread.mayl.data_dict['wind_speed'].mean()))
      self.mayall.set_message('winddirection','%7.3f' % float(self.thread.mayl.data_dict['wind_direction'].mean()))
    if self.thread.wiyn.data_dict:
      self.wiyn.set_message('temperature','%7.3f' % float(self.thread.wiyn.data_dict['air_temperature'].mean()))
      self.wiyn.set_message('humidity','%7.3f' % float(self.thread.wiyn.data_dict['humidity'].mean()))
      self.wiyn.set_message('windspeed','%7.3f' % float(self.thread.wiyn.data_dict['dew_point'].mean()))
      self.wiyn.set_message('dewpoint','%7.3f' % float(self.thread.wiyn.data_dict['windspeed'].mean()))
      self.wiyn.set_message('winddirection','%7.3f' % float(self.thread.wiyn.data_dict['winddir'].mean()))
    if self.thread.twom.data_dict:
      self.twometer.set_message('temperature','%7.3f' % float(self.thread.twom.data_dict['air_temperature'].mean()))
      self.twometer.set_message('humidity','%7.3f' % float(self.thread.twom.data_dict['humidity'].mean()))
      self.twometer.set_message('windspeed','%7.3f' % float(self.thread.twom.data_dict['dew_point'].mean()))
      self.twometer.set_message('dewpoint','%7.3f' % float(self.thread.twom.data_dict['wind_speed'].mean()))
      self.twometer.set_message('winddirection','%7.3f' % float(self.thread.twom.data_dict['wind_direction'].mean()))
    self.root.after(1,self.check_update)
    return

def stopall():
  global clientgui,root
  clientgui.thread.stop()
  root.destroy()
  sys.exit()
  return

if __name__=='__main__':
  root=Tk()
  xx=Button(root,text='Exit',font=TEXT_FONT,command=stopall,\
    width=6,padx=0,pady=0)
  xx.grid(column=0,row=0,sticky='nw')
  clientgui=WeatherClientGUI(root=root)#,row=1)
  root.mainloop()

