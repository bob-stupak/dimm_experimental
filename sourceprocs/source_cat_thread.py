#! /usr/bin/env python source_cat_thread.py
#
#
from numpy import *
import ephem
import threading
import platform
import time
import datetime
import string
import os
import os.path

from common_parms import *

progStat=True

class LocationThread(ephem.Observer,threading.Thread):
  '''class LocationThread
     Sets up the Site location and starts a thread that will continually
     run to update the time and local LST.
  '''
  def __init__(self,name='Home',lon=DIMLNG,lat=DIMLAT,elv=DIMELV):
    '''__init__
         initializes the site information but does not start thread
       Parameter:
       <name> Name of location
       <lon>  Site longitude
       <lat>  Site latitude
       <elv>  Site elevation
    '''
    ephem.Observer.__init__(self)
    threading.Thread.__init__(self)
    self.sleeptime=SRC_THREAD_TIME 
    self.prog_stat=True
    self.thread_stat=threading.Event()
    self.name=name
    '''@ivar: Site name '''
    self.lon=str(lon)
    '''@ivar: Site longitude '''
    self.lat=str(lat)
    '''@ivar: Site latitude '''
    self.elevation=elv
    '''@ivar: Site elevation '''
    self.get_time()
    self.get_twilights()
    return
  def __repr__(self):
    ss='\n'
    ss=ss+'<class \'source_cat_thread.LocationThread\'> class is Alive? %s\n' % (self.isAlive())
    ss=ss+'\n'
    ss=ss+'Date: %s %s\n' % (self.local_date,self.local_time)
    ss=ss+'UTC:  %s %s\n' % (self.utc_date,self.utc_time)
    ss=ss+'LST:  %s\n' % (self.lst_time)
    ss=ss+'Site Name: %s\n' % (self.name)
    ss=ss+'Latitude:  %s     Longitude:  %s\n' % (self.lat,self.lon)
    ss=ss+'Elevation:  %s\n' % (self.elevation)
    ss=ss+'Astronomical Twilight: %s\n' % (self.beg_astr_twilight)
    ss=ss+'Nautical Twilight:     %s\n' % (self.beg_naut_twilight)
    ss=ss+'Civil Twilight:        %s\n' % (self.beg_civil_twilight)
    ss=ss+'Sunrise:               %s\n' % (self.sunrise)
    ss=ss+'Noon:                  %s\n' % (self.noon)
    ss=ss+'Sunset:                %s\n' % (self.sunset)
    ss=ss+'Civil Twilight:        %s\n' % (self.end_civil_twilight)
    ss=ss+'Nautical Twilight:     %s\n' % (self.end_naut_twilight)
    ss=ss+'Astronomical Twilight: %s\n' % (self.end_astr_twilight)
    return ss
  def get_time(self):
    '''get_time
         updates all time and date information
    '''
    self.date=ephem.now()
    '''@ivar: Current UTC as type <ephem.Date>, although this is redundant, it is necessary to have for the LST calc
              used by <self.sidereal_time()> in the <ephem.Observer> class of which this class inherits.'''
    self.cur_loc_time=time.localtime()
    '''@ivar: Current local time as type <time.struc_time>, can be changed to type <datetime.datetime> 
              by using datetime.datetime(*self.cur_loc_time[:6])> '''
    self.cur_utc_time=ephem.now()
    '''@ivar: Current UTC as type <ephem.Date>, can be changed to <datetime> date/time with it's <.datetime()> method'''
    tmp_utc=self.cur_utc_time.datetime()
    self.utc_date='%i/%i/%i' % (tmp_utc.month,tmp_utc.day,tmp_utc.year)
    '''@ivar: Current UTC date string'''
    self.utc_time='%i:%i:%s' % (tmp_utc.hour,tmp_utc.minute,str(tmp_utc.second).zfill(2))
    '''@ivar: Current UTC time string'''
    self.lst_time=self.sidereal_time()
    '''@ivar: Current LST time this is of type <ephem.Angle>, and is used for calculating HA and separations'''
    self.local_date,self.local_time=time.strftime(DTIME_FORMAT,self.cur_loc_time).split(',')
    return
  def set_location(self,name='home',lng=0.0,lat=0.0,elv=0.0):
    '''set_location
         sets a new site name, location, and gets local time information
         Parameters
         <name> is the name of the site
         <lng> is the longitude of the site, can be a decimal or in 'ddd:mm:ss' format
         <lat> is the latitude of the site, can be a decimal or in 'sdd:mm:ss' format
         <elv> is the elevation for the site as a decimal in meters
    '''
    self.name=name
    if lng!=0.0: self.lon=str(lng)
    if lat!=0.0: self.lat=str(lat)
    if elv!=0.0: self.elevation=elv
    self.get_time()
    self.get_twilights()
    return
  def get_twilights(self):
    '''get_twilights
         Uses pyephem Location with different horizons to calculate the sunrise,
         sunset, noon, and twilights (horizon=-6 (civil), -12 (nautical), -18(astron).

         This code was developed using the following webpage as a guide
         http://stackoverflow.com/questions/2637293/calculating-dawn-and-sunset-times-using-pyephem

         The following are all equivalent
         >>>ephem.localtime(self.date),datetime.datetime.now(),datetime.datetime.fromtimestamp(time.time())
         >>>ephem.localtime(self.cur_utc_time),datetime.datetime.now(),datetime.datetime.fromtimestamp(time.time())
         >>>datetime.datetime(*time.localtime()[:6]) #Returns a datetime structure from a time structure
         >>>datetime.datetime.today().timetuple()[:6]==time.localtime()[:6]  #Time structure representation
         >>>datetime.datetime.now().timetuple()[:6]==time.localtime()[:6]    #Time structure representation
    '''
    d=datetime.datetime(*self.cur_loc_time[:6])
    #d=ephem.now()
    self.horizon='-0:34'
    self.sunrise=ephem.localtime(self.next_rising(ephem.Sun(),start=d))
    self.noon=ephem.localtime(self.next_transit(ephem.Sun(),start=d))
    self.sunset=ephem.localtime(self.next_setting(ephem.Sun(),start=d))
    self.horizon='-18:00:00'
    self.beg_astr_twilight=ephem.localtime(self.next_rising(ephem.Sun(),use_center=True,start=d))
    self.end_astr_twilight=ephem.localtime(self.next_setting(ephem.Sun(),use_center=True,start=d))
    self.horizon='-12:00:00'
    self.beg_naut_twilight=ephem.localtime(self.next_rising(ephem.Sun(),use_center=True,start=d))
    self.end_naut_twilight=ephem.localtime(self.next_setting(ephem.Sun(),use_center=True,start=d))
    self.horizon='-6:00:00'
    self.beg_civil_twilight=ephem.localtime(self.next_rising(ephem.Sun(),use_center=True,start=d))
    self.end_civil_twilight=ephem.localtime(self.next_setting(ephem.Sun(),use_center=True,start=d))
    self.horizon='-0:34'
    return
  def compare_times(self,time='civil',daytime=False):
    '''compare_times
         Accepts <time> the type of twilight 'civil','naut', or 'astr' to compare the local time
         and determine whether observations can start
         The <daytime> variable is used for testing.
       returns True or False
    '''
    right_now=datetime.datetime(*self.cur_loc_time[:6])
    st=self.__dict__['beg_'+time+'_twilight']#.datetime()
    nd=self.__dict__['end_'+time+'_twilight']#.datetime()
    time_to_work=((right_now<st and right_now.date()==st.date()) or (right_now>nd and right_now.date()==nd.date()))
    #print 'rn<%s:%r, rn.date==st.date:%r, rn>%s:%r, rn.date==nd.date:%r, t2w:%r' %\
    #  (str(st)[5:-4],right_now<st,right_now.date()==st.date(),str(nd)[5:-4],right_now>nd,\
    #  right_now.date()==nd.date(),time_to_work)
    if daytime: time_to_work=not time_to_work
    return time_to_work
  def run(self):
    '''run
         the thread run(start) routine will continually update local time
         information every second while thread_stat is set and self.prog_stat is true.
    '''
    self.thread_stat.set()
    while self.prog_stat:
      if self.thread_stat.isSet():
        time.sleep(self.sleeptime)
        self.get_time()
        #if self.beg_astr_twilight.date()!=ephem.localtime(self.date).date():
        self.get_twilights()
      else: pass
    self.thread_stat.clear()
    return
  def stop(self):
    '''stop
         will hard stop the thread by setting the global variable self.prog_stat to FALSE.
         There mostlikely are better approaches to running threads but this method
         is convenient.
    '''
    self.prog_stat=False
    return

class StarCatThread(threading.Thread):
  '''class StarCatThread
       A class to manage source catalogs and source selections actively.  The source
       selection can be achieved manually or automatically.  In auto mode, the
       source can be changed to the next available source with self.change_source()
       if necessary.
  '''
  def __init__(self,catname=None,location=None,log=True):
    '''__init__
       Parameters
         <catname>   The full path name of the catalog file
         <location>  Unless this is set to a LocationThread instance, the
                     locateion will be set to the global variables at the 
                     top of this file.
         <log>       A boolean set 'True' for writing to the log file in the './logs/' directory.
    '''
    threading.Thread.__init__(self)
    self.setName('catalogue_thread')
    self.prog_stat=True
    self.thread_stat=threading.Event()
    '''@ivar: Status of the thread, can be used to pause the thread action'''
    self.sleeptime=SRC_THREAD_TIME 
    '''@ivar: The sleeptime for the thread'''
    self.count=0
    '''@ivar: Used by thread as a timer to set the candidates list 
              update after self.after_count'''
    self.after_count=SRC_UPDATE_TIME
    '''@ivar: Used by thread to clock when to set the candidates list'''
    self.src_out_status=False
    '''@ivar: Status of the current source, whether it is within criterion'''
    self.auto_select=True
    '''@ivar: Boolean set to select candidate list and source automatically'''
    if catname==None:
      self.cat_name=CAT_DIR+CAT_NAME
      '''@ivar: Catalog name '''
    else:
      self.cat_name=catname
      '''@ivar: Catalog name '''
    if location==None:
      self.location=LocationThread()
      '''@ivar: Location thread '''
    else:
      self.location=location
      '''@ivar: Location thread '''
    #if location thread is not alive start it
    if not self.location.isAlive():
      self.location.start()
    subdir1=os.path.join(LOG_DIR,time.strftime('%b%Y',time.strptime(self.location.local_date+','+\
      self.location.local_time,DTIME_FORMAT)))
    fullpath=os.path.join(subdir1,time.strftime('%B%d',time.strptime(self.location.local_date+','+\
      self.location.local_time,DTIME_FORMAT)))
    if not os.path.exists(fullpath): os.makedirs(fullpath)
    self.logfile_name=os.path.join(fullpath,SRC_LOGBASENAME+'.'+self.location.local_date.replace('/','.'))
    '''@ivar: Log filename '''
    self.logging_flag=log
    '''@ivar: Logging Flag '''
    self.source=None
    '''@ivar: Selected of the <ephem> class initially of the brightest and nearest 
       to zenith from the self.candidates list but can be any source in starlist'''
    self.starlist=[]
    '''@ivar: A list of <ephem> fixed body classes for each object in catalog  '''
    self.starlist_names=[]
    '''@ivar: A list of corresponding names for the <self.starlist> list '''
    self.src_finished=[]
    '''@ivar: A list of source names that have already been done or tried'''
    self.zdistlimit=ZEN_LIMIT
    '''@ivar: Largest zenith distance criterion'''
    self.zdistminimum=ZEN_MINIMUM
    '''@ivar: Smallest zenith distance criterion'''
    self.magnlimit=MAG_LIMIT
    '''@ivar: Dimmest magnitude selection criterion'''
    self.magnlimitmax=MAG_LIMIT_MAX
    '''@ivar: Brightest magnitude selection criterion'''
    self.candidates=[]
    '''@ivar: A list of <ephem> fixed body classes candidates within 
       zdistlimit and magnlimit '''
    self.open_cat()
    self.start()
    return
  def __repr__(self):
    ''' __repr__
         expresses the thread status, source name, position, and site location 
         information.
    '''
    ss='\n'
    ss=ss+'<StarCatThread> class is Alive? %s\n' % (self.isAlive())
    ss=ss+'\n'
    ss=ss+'AutoSelection: %s \n' % (self.auto_select)
    ss=ss+'Catalog:       %s \n' % (self.cat_name)
    ss=ss+'Number of src: %d \n' % (len(self.starlist_names))
    ss=ss+'ZDIST max:     %7.3f \n' % (self.zdistlimit)
    ss=ss+'ZDIST mim:     %7.3f \n' % (self.zdistminimum)
    ss=ss+'Magn limit:    %7.3f \n' % (self.magnlimit)
    ss=ss+'Magn limit max:%7.3f \n' % (self.magnlimitmax)
    ss=ss+'Number of Cand:%d \n' % (len(self.candidates))
    ss=ss+'Number of src: %d \n' % (len(self.starlist_names))
    ss=ss+'\n'
    ss=ss+'Location:           %s \n' % (self.location.name)
    ss=ss+'Local Date Time:    %s,%s \n' % (self.location.local_date,self.location.local_time)
    ss=ss+'Local LST Time:     %s\n' % (self.location.lst_time)
    ss=ss+'Latitude,Longitude: %s,%s \n' % (self.location.lat,self.location.lon)
    ss=ss+'Elevation:          %7.3f \n' % (self.location.elevation)
    ss=ss+'\n'
    ss=ss+'Source:          %s\n' % (self.source.name)
    try: ss=ss+'RA,DEC,EPOCH:    %s,%s,%s\n' % (self.source.ra,self.source.dec,str(self.source._epoch)[:4])
    except Exception: ss=ss+'RA,DEC,EPOCH:    %s,%s,%s\n' % (self.source.ra,self.source.dec,'N/A')
    ss=ss+'CUR RA,CUR DEC:  %s,%s\n' % (self.source.a_ra,self.source.a_dec)
    ss=ss+'Az,Elv:          %s,%s\n' % (self.source.az,self.source.alt)
    ss=ss+'Magnitude:       %s\n' % (self.source.mag)
    ss=ss+'Zenith Distance: %s %s of meridian\nAirmass:       %10.6f\n' %\
      (self.find_zdist(self.source))
    return ss
  def run(self):
    '''run
         the thread run(start) routine will continually update the selected source
         information every self.sleeptime while self.thread_stat is set and self.prog_stat 
         is true.
    '''
    self.thread_stat.set()
    while self.prog_stat:
      time.sleep(self.sleeptime)
      if self.thread_stat.isSet():
        self.source.compute(self.location)
        # find the latest candidates given selection criterion after self.after_count
        if self.count>=self.after_count:
          self.write_to_log(msgs='Selecting candidates and checking source')
          self.select_candidates()
          self.check_source()
          self.count=0
        # if in auto mode and source is out of the selection criterion
        if self.auto_select and self.src_out_status:
          self.write_to_log(msgs='Auto Select on, changing, and checking source')
          self.change_source()
          self.check_source()
        self.count+=1
      else: pass
    self.thread_stat.clear()
    return
  def open_cat(self):
    '''open_cat
         Opens the catalog file and sets a list of ephem.FixedBody(stars),
         a list of star names, a list ephemFixedBody(stars) candidates, and a source
    '''
    fp=open(self.cat_name,'r')
    catlines=fp.readlines()
    fp.close()
    starlines=[each[:-1] for each in catlines if '#'!=each[0]]
    self.starlist=[ephem.readdb(each) for each in starlines]
    self.starlist_names=[each.name for each in self.starlist]
    self.change_source()
    self.write_to_log(msgs='Catalog Opened:'+self.cat_name)
    self.write_to_log()
    return
  def find_zdist(self,star=None):
    '''find_zdist
       Parameters
         if star==None the map/lambda function will compute the zenith distance
           of all of the stars in starlist
         else computes only the zenith distance of the star <star>
       Finds the zenith distance in degrees. 
       Returns
         zdist  <type 'ephem.Angle'>, which can be converted to radians
                which the type conversion <float(variable)>.
         direction
                E, W, Below Horizon if the star is east or west of the meridian
                or below the horzion
         airmass
    '''
    if star==None:
      junk=[each.compute(self.location) for each in self.starlist]
      zdist=array(map(lambda each:ephem.separation((float(self.location.lst_time),\
        float(self.location.lat)),(each.a_ra,each.a_dec)),self.starlist))
      ## Calculation fo airmass from zenith distance from Berry and Burnell, pg 250
      scnt=1.0/cos(zdist)
      airmass=scnt-0.0018167*(scnt-1.0)-0.002875*(scnt-1.0)**2.0-0.000808*(scnt-1.0)**3.0
      direction=''
    else:
      junk=star.compute(self.location)
      zdist=ephem.separation((float(self.location.lst_time),float(self.location.lat)),\
        (star.a_ra,star.a_dec))
      ## Calculation fo airmass from zenith distance from Berry and Burnell, pg 250
      scnt=1.0/cos(float(zdist))
      airmass=scnt-0.0018167*(scnt-1.0)-0.002875*(scnt-1.0)**2.0-0.000808*(scnt-1.0)**3.0
      if zdist>pi/2.0:
        direction='Below Horizon'
      else: 
        if star.az<ephem.degrees(pi):
          direction='E'
        else:
          direction='W'
    return zdist,direction,airmass
  def select_candidates(self):
    '''select_candidates
       Calculates and returns a list of candidates given the zdistlimit range and magnlimit
       between zdistlimit(max zdist) and zdistminimum(closest to zenith)
    '''
    self.write_to_log(msgs='Finding new candidates list with zdist= %7.3f and magn=%7.3f' %\
      (self.zdistlimit,self.magnlimit))
    zdist,direction,airmass=self.find_zdist()
    low_indices=where(zdist<pi/180.0*self.zdistlimit)[0]
    high_indices=where(zdist>pi/180.0*self.zdistminimum)[0]
    candid_indices=intersect1d(low_indices,high_indices)
    candidates_list=[self.starlist[int(x)] for x in candid_indices \
      if self.starlist[int(x)].mag<self.magnlimit and self.starlist[int(x)].mag>self.magnlimitmax]
    # If NO candidates, open up the zdist and magn criterion until candidates are found
    if len(candidates_list)>0:
      self.candidates=candidates_list
    else:
      self.zdistlimit=self.zdistlimit+5.0
      self.magnlimit=self.magnlimit+0.5
      self.select_candidates()
    return
  def select_brightest(self,starlist=None):
    '''select_brightest
       Parameters
         <starlist> A list of <type 'ephem.FixedBody'>  to find the brightest magnitude
                    star
         If None will find the brightest of the <self.candidates>
       Returns
         ephem.FixedBody type star
    '''
    self.write_to_log(msgs='Selecting Brightest')
    if starlist==None:
      self.select_candidates()
      starlist=self.candidates
    brightest=array([each.mag for each in starlist]).min()
    bindex=where(array([each.mag for each in starlist])==brightest)[0]
    #if len(bindex)>1: bindex=bindex[0]  #If two stars have the same magnitude
    bindex=bindex[0]
    return starlist[bindex]
  def check_source(self):
    '''check_source
         Checks to see if source is in the candidates list....
         ---Potentially can be used to check source against other criterion.
    '''
    # To check if source is still in candidates use
    check=[each.name for each in self.candidates if self.source.name==each.name]
    if len(check)>0:    #source is still in candidates list
      self.write_to_log(msgs='Source is within zdist and still in self.candidates list')
      self.src_out_status=False
    else:               #source not in list and a flag should be set
      self.write_to_log(msgs='Source no longer within zdist nor still in self.candidates list')
      self.src_out_status=True
    return
  def change_source(self,name=None):
    '''change_source
         In 'manual' mode (<self.auto_select>==False) <change_source> will 
         set the self.source to an ephem fixed body type with that name if that
         source is in the catalog.  Otherwise it will keep the last source.

         In auto mode, <change_source> will find the candidates that haven't been
         used already and set the source to the next source in the candidates list.
         If the <possibles> list variable has no elements, the <self.src_finished>
         list is reset to [], the source will be set to the brightest out of the 
         candidates list and process will be re-cycle through the candidates list again.
       Parameters:
         <name>  name of source
    '''
    # To manually set a source <self.auto_select> has to be 'False'
    self.write_to_log(msgs='Changing source--->')
    if not self.auto_select and name!=None:
      # set <possibles> to the ephem type from the starlist
      possibles=[each for each in self.starlist if name==each.name]
      if len(possibles)>0:
        # Choose the first possible and compute its position in the sky
        self.source=possibles[0]
        self.source.compute(self.location)
      else: 
        if name in PLANETS:
          self.source=eval('ephem.'+name+'(self.location)') #Set <self.source> to a planet
          self.starlist.append(self.source)  #Will add the planet to starlist,
          self.starlist_names.append(name)   #starlist_names, and checked to be candidate
        else:
          pass  #Source not found in catalog and <self.source> will remain unchanged
    else:
      #Casting the two list into type(<set>) for comparing the two lists and finding
      # the possible sources that haven't been done already
      possibles=list(set([each.name for each in self.candidates])-set(self.src_finished))
      if len(possibles)>0:
        self.source=[each for each in self.candidates if possibles[0]==each.name][0]
      else:
        #If nothing is possible set the source back to the brightest of the candidates list
        self.source=self.select_brightest()
        self.src_finished=[]
    #Append the <self.src_finished> list with the new source
    if self.source.name not in self.src_finished:
      self.src_finished.append(self.source.name)
    self.write_to_log()
    return 
  def change_cat(self,catname):
    '''change_cat
         will set the self.cat_name, open catalog file, and select source
    '''
    self.cat_name=CAT_DIR+catname+'.edb'
    self.open_cat()
    self.starlist=self.starlist+[eval('ephem.'+each+'(self.location)') for each in PLANETS]
    self.change_source()
    return
  def recover_from(self,catname='bsc5',source=''):
    '''recover_from
         Is used to recover the 'last state', given <catname> and <source> by name
    '''
    self.auto_select=False
    self.src_finished=[]
    self.change_cat(catname)
    self.change_source(name=source)
    self.auto_select=True
    return
  def write_to_log(self,msgs=None):
    '''write_to_log
         will write to logfile on source change
    '''
    cur_date=self.location.local_date.replace('/','.')
    subdir1=os.path.join(LOG_DIR,time.strftime('%b%Y',time.strptime(self.location.local_date+','+\
      self.location.local_time,DTIME_FORMAT)))
    fullpath=os.path.join(subdir1,time.strftime('%B%d',time.strptime(self.location.local_date+','+\
      self.location.local_time,DTIME_FORMAT)))
    if not os.path.exists(fullpath): os.makedirs(fullpath)
    if cur_date not in self.logfile_name:
      self.logfile_name=os.path.join(fullpath,SRC_LOGBASENAME+'.'+cur_date)
    if os.path.exists(self.logfile_name):
      apfile='a'
    else:
      apfile='w'
    fp=open(self.logfile_name,apfile)
    if apfile=='w':
      fp.write('#Source log for %s %s\n' %(self.location.local_date,\
        self.location.local_time))
      fp.write('#\n')
      fp.write('#%s,%s,%s,%s,%s,%s,%s,%s\n' % \
        ('Local Time','Local Date','Source Name','Local LST','Right Ascension',\
        'Declination','Azimuth','Elevation'))
      fp.write('#\n')
    if msgs==None:
      fp.write('%s,%s,%s,%s,%s,%s,%s,%s\n' % \
        (self.location.local_time,self.location.local_date,self.source.name,\
        self.location.lst_time,self.source.ra,self.source.dec,self.source.az,\
        self.source.alt))
    else:
      fp.write('#%s %s: %s\n' % (self.location.local_time,self.location.local_date,msgs))
    fp.close()
    return
  def print_selected(self,src='selected'):
    '''print_selected
       Used to print out or test the star candidates list of stars
       if src!='selected' print all of the candidates
       otherwise only print the self.source 
    '''
    print '\nFor an LST time of: %s' %(self.location.lst_time)
    print 'Within ZD limit top: %7.3f  bottom: %7.3f  Magn Range: %7.3f-%7.3f\n' % \
      (self.zdistlimit,self.zdistminimum,self.magnlimitmax,self.magnlimit)
    if src=='selected':
      zdist,direction,airmass=self.find_zdist(star=self.source)
      print 'The brightest source of the candidates is:'
      print 'Name:  %s\nZD:  %s%s\nRA:  %s\nDec:  %s\nMagn:  %s' %\
       (self.source.name.ljust(15),str(zdist).ljust(10),direction,\
        self.source.a_ra,self.source.a_dec,self.source.mag)
      print 'EL:  %s\nAz:  %s\n' % \
       (self.source.alt,self.source.az)
    else:
      if len(self.candidates)==0:
        self.change_source()
      print 'The list of source candidates is:'
      for each in self.candidates:
        zdist,direction,airmass=self.find_zdist(star=each)
        print 'Name:  %s, ZD:  %s%s, RA:  %s, Dec:  %s, Magn:  %s' %\
         (each.name.ljust(15),str(zdist).ljust(10),direction,\
         each.a_ra,each.a_dec,each.mag)
    print ''
    return
  def stop(self):
    '''stop
         Stops all threads within started through this module by setting the 
         global <prog_stat> to FALSE.
    '''
    #self.location.stop()
    self.write_to_log(msgs='Stopping Thread')
    self.prog_stat=False
    return
