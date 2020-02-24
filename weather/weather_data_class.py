#!/usr/bin/env python weather_data_class.py
#
#

import sys
sys.path.append('..')

from numpy import *

import MySQLdb as mysql
#import redis
import os
import time
import datetime
import requests,urllib2

#import get_kpno_redis as gkr
import generic_thread as gth

import sourceprocs.source_cat_thread as sct

from threading import Lock
from common_parms import *

WEA_LOGBASENAME='weather.log'
KPNO_WEBSITE='http://www-kpno.kpno.noao.edu/weather.shtml'

MYSQL_CONN={'host':'rose.kpno.noao.edu','user':'oa','passwd':'kpweather','db':'KpnoWeather'}
QUERY_2M_A={'selections':['dew_point_time','air_temperature','dew_point','humidity','split'],\
          'table':'dew_points','where_clause':'where telescope_id=2'}
#QUERY_2M_B={'selections':['date_time','amb_temp','wind_speed','wind_direction'],\
#          'table':'2m_environment','where_clause':''}
QUERY_2M_B={'selections':['date_time','air_temp','wind_speed','wind_direction'],\
          'table':'2m_WXstation','where_clause':''}
QUERY_4M_A={'selections':['dew_point_time','air_temperature','dew_point','humidity','split'],\
          'table':'dew_points','where_clause':'where telescope_id=1'}
QUERY_4M_B={'selections':['date_time','wind_speed','wind_direction','bar_pressure'],\
            'table':'4m_WXstation','where_clause':''}
            #Can include 'bar_pressure' in selections for 4M_B query
QUERY_WN_A={'selections':['dew_point_time','air_temperature','dew_point','humidity','split'],\
          'table':'dew_points','where_clause':'where telescope_id=3'}
QUERY_WN_B={'selections':['date_time','windspeed','winddir','pressure'],'table':'wiyn_environment','where_clause':''}
            #Can include 'pressure' in selections for WN_B query

BASIC_QUERY='select dew_point_time,air_temperature,dew_point,humidity,split from dew_points where telescope_id=3 '+\
            'order by id desc limit 10'

class Sql_connection(object):
  def __init__(self,host=MYSQL_CONN['host'],user=MYSQL_CONN['user'],passwd=MYSQL_CONN['passwd'],db=MYSQL_CONN['db']):
    self.host=host
    self.user=user
    self.passwd=passwd
    self.db=db
    self.connection=mysql.connect(host=host,user=user,passwd=passwd,db=db)
    self.cursor=self.connection.cursor(mysql.cursors.DictCursor)
    self.connection_status=False
    self.connection_busy=Lock()
    self.check_db_status()
    return
  def query(self,query):
    # connection_busy lock added 25 Jan 2019 in order to prevent accessing db 
    self.connection_busy.acquire()
    self.cursor.execute(query)
    data_dict=self.cursor.fetchall()
    self.connection_busy.release()
    return data_dict
  def send(self,cmd_string):
    self.connection_busy.acquire()
    self.cursor.execute(cmd_string)
    self.connection_busy.release()
    return
  def check_db_status(self):
    if self.connection:
      try:
        self.connection.ping()
        self.connection_status=True
      except Exception:
        self.connection_status=False
    else:
      self.connection_status=False
    return
  def close(self):
    self.connection.close()
    self.cursor=None
    self.connection=None
    return
  def reconnect(self):
    self.close()
    self.connection=mysql.connect(host=self.host,user=self.user,passwd=self.passwd,db=self.db)
    self.cursor=self.connection.cursor(mysql.cursors.DictCursor)
    self.connection_status=False
    self.check_db_status()
    return

class Mysql_weather_db_class(object):
  def __init__(self,connection=None,station=2,number_data=15):
    self.raw_data_array=array([])
    self.averages_array=array([])
    self.std_dev_array=array([])
    self.data_dict={}
    self.status_array=array([])
    self.station=station
    self.number_of_data=number_data
    if connection: self.connection=connection
    else: self.connection=Sql_connection()
    self.humidity_status=False
    self.wind_status=False
    self.split_status=False
    self.update_data()
    return
  def __str__(self):
    self.connection.check_db_status()
    if self.connection.connection:
      ss='\n%r in <module %r>\n' % (self.__class__,self.__module__)
      ss='%sConnection is connected: %r\n\n' % (ss,self.connection.connection_status)
      ss='%sAveraged over %d latest data points from station %d,' % (ss,self.number_of_data,self.station)
      ss='%s from %s\nuntil %s.\n' % (ss,self.data_dict['dew_point_time'][-1],self.data_dict['dew_point_time'][0])
      ss='%sAir Temperature:         %8.3f C\n' % (ss,self.data_dict['air_temperature'].mean())
      ss='%sDewpoint Temperature:    %8.3f C\n' % (ss,self.data_dict['dew_point'].mean())
      if self.data_dict.has_key('bar_pressure'):
        ss='%sBarimetric Pressure:     %8.3f mbar\n' % (ss,self.data_dict['bar_pressure'].mean())
      else:
        ss='%sBarimetric Pressure:     %8.3f mbar\n' % (ss,self.data_dict['pressure'].mean())
      ss='%sHumidity: %7.3f%%             Status: %s\n' % (ss,self.data_dict['humidity'].mean(),self.humidity_status)
      if self.data_dict.has_key('wind_speed'):
        ss='%sWind:     %7.3fmph@%7.3f   Status: %s\n' % (ss,self.data_dict['wind_speed'].mean(),\
          self.data_dict['wind_direction'].mean(),self.wind_status)
      else:
        ss='%sWind:     %7.3fmph@%7.3f   Status: %s\n' % (ss,self.data_dict['windspeed'].mean(),\
          self.data_dict['winddir'].mean(),self.wind_status)
      ss='%sSplit:    %7.3f C            Status: %s\n' % (ss,self.data_dict['split'].mean(),self.split_status)
    else: ss='CONNECTION CLOSED'
    return ss
  def make_string(self):
    self.connection.check_db_status()
    if self.connection.connection:
      ss='%d,%s,' % (self.station,self.data_dict['dew_point_time'][-1])
      ss='%s%8.3f,' % (ss,self.data_dict['air_temperature'].mean())
      ss='%s%8.3f,' % (ss,self.data_dict['dew_point'].mean())
      if self.data_dict.has_key('bar_pressure'):
        ss='%s%8.3f,' % (ss,self.data_dict['bar_pressure'].mean())
      else:
        ss='%s%8.3f,' % (ss,self.data_dict['pressure'].mean())
      ss='%s%7.3f,%s,' % (ss,self.data_dict['humidity'].mean(),self.humidity_status)
      if self.data_dict.has_key('wind_speed'):
        ss='%s%7.3f,%7.3f,%s,' % (ss,self.data_dict['wind_speed'].mean(),\
          self.data_dict['wind_direction'].mean(),self.wind_status)
      else:
        ss='%s%7.3f,%7.3f,%s,' % (ss,self.data_dict['windspeed'].mean(),\
          self.data_dict['winddir'].mean(),self.wind_status)
      ss='%s,%7.3f,%s' % (ss,self.data_dict['split'].mean(),self.split_status)
    else: ss='#CONNECTION CLOSED'
    return ss
  def get_data(self):
    if self.connection.connection:
      tmp_array=array([])
      data_dict_list=[]
      if self.station==3: qstring='QUERY_WN'
      elif self.station==2: qstring='QUERY_2M'
      elif self.station==1: qstring='QUERY_4M'
      else: qstring='QUERY_4M'
      for each in ['_A','_B']:
        QRY=eval(qstring+each)
        query='select '+','.join(QRY['selections'])+' from '+QRY['table']+' '+QRY['where_clause']+' order by id '+\
          'desc limit '+str(self.number_of_data)
        data_dict=self.connection.query(query)
        if qstring+each=='QUERY_2M_B':
          data_dict=[dict(each,**{'pressure':0.0}) for each in data_dict]
        data_dict_list.append(data_dict)
      data_dict_list=zip(*data_dict_list)
      data_dict_list=map(lambda x: dict(data_dict_list[x][0],**data_dict_list[x][1]),range(len(data_dict_list)))
      keys=data_dict_list[0].keys()
      for each in keys:
        tmp_array=array([every[each] for every in data_dict_list])
        self.data_dict[each]=tmp_array
    else: pass
    self.raw_data_array=self.data_dict['dew_point_time']
    names=['air_temperature','dew_point','split','humidity','wind_speed','wind_direction','bar_pressure']
    for each in names:
      if each=='wind_speed' and 'wind_speed' not in self.data_dict.keys(): each='windspeed'
      if each=='wind_direction' and 'wind_direction' not in self.data_dict.keys(): each='winddir'
      if each=='bar_pressure' and 'bar_pressure' not in self.data_dict.keys(): each='pressure'
      self.raw_data_array=vstack((self.raw_data_array,self.data_dict[each]))
    tstamp=array([self.raw_data_array[0][0]])
    avrs=self.raw_data_array[1:].mean(axis=1)
    stds=array([each.std() for each in self.raw_data_array[1:]])
    self.averages_array=self.stack_arrays(concatenate((tstamp,avrs)),self.averages_array)
    self.std_dev_array=self.stack_arrays(concatenate((tstamp,stds)),self.std_dev_array)
    return 
  def stack_arrays(self,new_array_data,stacked_array):
    if stacked_array.ndim>1:
      if new_array_data[0]!=stacked_array[-1,0]: new_array=vstack((stacked_array,new_array_data))
      else: new_array=stacked_array
    else:
      if stacked_array.size!=0:
        if new_array_data[0]!=stacked_array[0]: new_array=vstack((stacked_array,new_array_data))
        else: new_array=stacked_array
      else: new_array=new_array_data
    return new_array[-10:]
  def check_data(self):
    if self.connection.connection:
      # Check data to see if it is within tolerance to open
      if self.data_dict['humidity'].mean()<70.0:
        self.humidity_status=True
        #print 'Humidity is good at %7.3f%%' % (self.data_dict['humidity'].mean())
      else:
        self.humidity_status=False
        #print 'Humidity is not good enough at %7.3f%%' % (self.data_dict['humidity'].mean())
      if self.data_dict['split'].mean()>1.4:
        self.split_status=True
        #print 'Split is good at %7.3fC' % (self.data_dict['split'].mean())
      else:
        self.split_status=False
        #print 'Split is not good enough at %7.3fC' % (self.data_dict['split'].mean())
      if self.data_dict.has_key('wind_speed'):
        wind_key='wind_speed'
      elif self.data_dict.has_key('windspeed'):
        wind_key='windspeed'
      else:
        wind_key='wind_speed'
      if self.data_dict[wind_key].mean()<45.0:
        self.wind_status=True
        #print 'Wind is good at %7.3fmpg' % (self.data_dict[wind_key].mean())
      else:
        self.wind_status=False
        #print 'Wind is NOT good at %7.3fmpg' % (self.data_dict['wind_speed'].mean())
      self.status_array=self.stack_arrays(array([self.data_dict['dew_point_time'][0],self.humidity_status,\
        self.split_status,self.wind_status]),self.status_array)
    else: pass
    return
  def change_station(self,station=1):
    self.raw_data_array=array([])
    self.averages_array=array([])
    self.std_dev_array=array([])
    self.status_array=array([])
    self.data_dict={}
    self.station=station
    self.update_data()
    return
  def update_data(self):
    self.connection.check_db_status()
    self.get_data()
    self.check_data()
    return
  def close(self):
    self.connection.close()
    return
#
# The following is interesting about dictionaries
#
    #In order to concatenate two dictionaries use either
    #>>>a={'a':1,'b':2,'c':3}
    #>>>b={'z':10,'y':9,'x':8}
    #>>>c={}
    #To create a new dictionary:
    #>>>d=dict(dict(a,**b),**c)
    #Or to add to the original dictionary:
    #>>>a.update(b)
    #>>>a.update(c)

class weather_thread(gth.generic_thread):
  def __init__(self,*args,**kwargs):
    prnt=kwargs.get('prnt',False)
    log=kwargs.get('log',False)
    db_cnx=kwargs.get('db_cnx',None)
    loc_tion=kwargs.get('loc',None)
    self.sleeptime=kwargs.get('sleeptime',0.1)
    self.cycle_counts=0
    gth.generic_thread.__init__(self,prnt=prnt,log=log,sleeptime=self.sleeptime)
    subdir1=os.path.join(LOG_DIR,time.strftime('%b%Y'))
    fullpath=os.path.join(subdir1,time.strftime('%B%d'))
    if not os.path.exists(fullpath): os.makedirs(fullpath)
    self.logbasename=WEA_LOGBASENAME
    self.logfile_name=os.path.join(fullpath,WEA_LOGBASENAME+'.'+time.strftime('%m.%d.%Y'))
    #self.logfile_name=LOG_DIR+WEA_LOGBASENAME+'.'+self.local_date.replace('/','.')
    if not loc_tion:
      self.location=sct.LocationThread()
      self.location.start()
    else:
      self.location=loc_tion
      if not self.location.isAlive():
        self.location.start()
    if not db_cnx:
      self.db_connection=Sql_connection()
    else:
      self.db_connection=db_cnx
    self.wiyn=Mysql_weather_db_class(connection=self.db_connection,station=3)
    self.twom=Mysql_weather_db_class(connection=self.db_connection,station=2)
    self.mayl=Mysql_weather_db_class(connection=self.db_connection,station=1)
    self.weather_good=False
    self.time_good=False
    self.wiyn_good=False
    self.twom_good=False
    self.mayl_good=False
    self.domes_opened=False
    self.set_message('#Thread is opened and ready to queue data')
    ss='#Mayall weather,WIYN weather,Two M weather,Domes opened status,Time to open status,All ANDed'
    self.set_message(ss)
    return
  def __repr__(self):
    ss='Mayall:\n%r\n' % (self.mayl)
    ss='%sTwo Meter:\n%r\n' % (ss,self.twom)
    ss='%sWIYN:\n%r\n' % (ss,self.wiyn)
    ss='%sMayall weather good:%s\n' % (ss,self.mayl_good)
    ss='%sWIYN weather good:  %s\n' % (ss,self.wiyn_good)
    ss='%sTwo M weather good: %s\n' % (ss,self.twom_good)
    ss='%sDomes opened status:%s\n' % (ss,self.domes_opened)
    ss='%sTime to open status:%s\n' % (ss,self.time_good)
    ss='%sAll ANDed:          %s\n' % (ss,self.weather_good)
    return ss
  def run(self):
    self.thread_stat.set()
    while self.prog_stat:
      time.sleep(self.sleeptime)
      if self.db_connection.connection_status and self.cycle_counts>600:
        self.lock.acquire()
        self.get_check_data()
        self.lock.release()
        self.cycle_counts=0
      self.cycle_counts+=1
    self.set_message('#Thread has STOPPED!!!!')
    self.thread_stat.clear()
    return
  def get_check_data(self):
    self.wiyn.update_data()
    self.twom.update_data()
    self.mayl.update_data()
    try:
      self.domes_opened=get_kpno_dome_stat()[0]
      self.time_good=self.location.compare_times()
      self.wiyn_good=all(self.wiyn.status_array[-1,1:])
      self.twom_good=all(self.twom.status_array[-1,1:])
      self.mayl_good=all(self.mayl.status_array[-1,1:])
    except Exception: pass
    #self.weather_good=self.wiyn_good & self.twom_good & self.mayl_good & self.domes_opened & self.time_good
    self.weather_good=self.domes_opened & self.time_good
    ss='#%s,%s,%s,%s,%s,%s' % (self.mayl_good,self.wiyn_good,self.twom_good,self.domes_opened,\
      self.time_good,self.weather_good)
    self.set_message(ss)
    self.set_message(self.wiyn.make_string())
    self.set_message(self.twom.make_string())
    self.set_message(self.mayl.make_string())
    return
  def stop(self):
    self.location.stop()
    self.thread_stat.clear()
    self.prog_stat=False
    self.db_connection.close()
    self.set_message('#Stopping Thread!!!!')
    self.thread_stat.clear()
    self.prog_stat=False
    return

def get_kpno_dome_stat():
  try:
    f=urllib2.urlopen(KPNO_WEBSITE)
    dome_string=f.read()
    f.close()
    dome_string=dome_string.split('PRE')[1].split('<A HREF')[0].replace('\n','')[1:]
  except Exception:
    dome_string='NOT AVAILABLE'
  if 'OPEN' in dome_string: dome_stat=True
  elif 'CLOSED' in dome_string: dome_stat=False
  else: dome_stat=False
  return dome_stat,dome_string


if __name__=='__main__':
  mm=weather_thread(prnt=True,log=True)
  mm.start()
  while raw_input('To stop program type \'x\' and <return>')!='x':
    time.sleep(0.1)
    pass
  mm.stop()

