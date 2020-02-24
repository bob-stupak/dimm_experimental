#! /usr/bin/env python telescope_thread.py
#
import threading
import time
import string
import re
import os
import os.path
import telescope_comms as tcomms
import ephem
from numpy import pi,radians,linspace

from common_parms import *

START_DATE,START_TIME=time.strftime(DTIME_FORMAT).split(',')

#Program status boolean, <True> if program is running
#                        <False> if program is finished
progStat=True


#TELE_PARMS is a list of dictionary keys that define the 
# necessary telescope parameters.  The dictionary keys are then
# defined as TelesThread attributes to be called for example
# 'TelesThread.localtime'
#
# The structure of each element in the list is as follows
# {'attrname':['get command','label','string value','set command']}
#
TELE_PARMS=[{'localdate':['GC','Local Date',START_DATE,'SC']},\
            {'localtime':['GL','Local Time',START_TIME,'SL']},\
            {'sidrtime':['GS','Local Sidereal Time','lst','SS']},\
            {'elevation':['GA','Elevation','00:00:00','Sa']},\
            {'azimuth':['GZ','Azimuth','000:00:00','Sz']},\
            {'rightasc':['GR','Right Ascension','ra','Sr']},\
            {'declination':['GD','Declination','dec','Sd']},\
            {'pierstat':['pS','Pier/Mount Side','n/a','#']},\
            {'sitelat':['Gt','Site Latitude','sitelat','St']},\
            {'sitelong':['Gg','Site Longitude','sitelong','Sg']}]

class TelesThread(threading.Thread):
  '''class TelesThread 
     Inherits the threading.Thread class to be used in
     the background for reading and writing to the telescope mount port.
  '''
  def __init__(self,name=None,prnt=False,log=True,port='-',mount='Astro-physics'):
    '''__init__ 
       constructs the TelesThread class
       Parameters
         <name>         Name of the class instance
         <sleeptime>    An update time rate for the thread
         <prnt>         'True' to print to the std.out,
         <log>          'True' produces a log file in the './logs' directory
         <port>         The port as defined in above, defaults to simulation
         <mount>        The mount type, Astro-physics by default
    '''
    threading.Thread.__init__(self)
    self.thread_stat=threading.Event()
    '''@ivar: Status of the thread, can be used to pause the thread action'''
    self.on_source_stat=threading.Event()
    '''@ivar: The on-source event'''
    self.park_stat=threading.Event()
    '''@ivar: The park position status event'''
    self.park_stat.set()
    if name!=None:  self.setName(name)
    else:  self.setName('telescope_thread')
    self.stdout_flag=prnt
    '''@ivar: For debugging from a python interpeter'''
    self.sleeptime=TELE_THREAD_TIME
    '''@ivar: The thread sleep time'''
    self.port=tcomms.return_port(port)
    '''@ivar: The communications port, can be IP, serial/usb, or simulation'''
    self.mount_name=mount
    '''@ivar: The type of mount since initial testing of code was on the Meade'''
    self._parmsList=TELE_PARMS
    self.cmd='Cmd Send'
    '''@ivar: The last sent command to the telescope'''
    self.msg='Msg Recv'
    '''@ivar: The last message response from the telescope'''
    self.defineparms()
    self.postolerance=TELE_TOLERANCE
    '''@ivar: The position tolerance for the on-source event, in degrees'''
    self.on_source_stat.set()
    self.tele_location=['Home',str(ephem.degrees(DIMLAT/180.0*pi)).replace(':','*',1)[:-2].zfill(8),\
      str(ephem.degrees(abs(DIMLNG)/180.0*pi)).replace(':','*',1)[:-2].zfill(9),DIMELV]
    '''@ivar: The telescope site information, initialized to DIMM position, in form of [name,lat,long,elevation]'''
    self.cmdposition=[TELE_PARK_POS1[0],TELE_PARK_POS1[1],'azel']
    '''@ivar: The commanded position in azimuth and elevation or ra/dec'''
    subdir1=os.path.join(LOG_DIR,time.strftime('%b%Y'))
    fullpath=os.path.join(subdir1,time.strftime('%B%d'))
    if not os.path.exists(fullpath): os.makedirs(fullpath)
    self.logfile_name=os.path.join(fullpath,TELE_LOGBASENAME+'.'+time.strftime('%m.%d.%Y'))
    '''@ivar: Log filename '''
    self.logging_flag=log
    '''@ivar: Flag to start or stop logging'''
    self.count=0
    '''@ivar: Used by thread as a timer to write to the log files after self.log_time'''
    self.log_time=TELE_LOG_TIME
    '''@ivar: Used by thread when to write to the log files'''
    self.tele_speeds=TELE_SPEEDS
    '''@ivar: Are the four preset telescope rates [tracking,slew,guide,center]'''
    self.focus_speed=0
    '''@ivar: Is the telescope focus speed 0(slow) and 1(fast)'''
    #Initialize focus speed and start with no tracking
    self.move_focus(direction=0,speed=self.focus_speed)
    self.set_track(speed=9)
    return
  def __repr__(self):
    '''__repr__
       expresses the telescope status
    '''
    ss='\n'
    ss=ss+'<TelesThread> class is Alive? %s\n' % (self.isAlive())
    ss=ss+'\n'
    for each in self._parmsList:
      attr=self.__dict__[each.keys()[0]]
      ss=ss+attr[1]+': %s\n' %(attr[2])
    ss=ss+'Command Position: (%s,%s)\nCoordinates:%s\n' %\
      (self.cmdposition[0],self.cmdposition[1],self.cmdposition[2])
    ss=ss+'Tracking Speed:  %d\n' % (self.tele_speeds[0])
    ss=ss+'Slew Speed:      %d\n' % (self.tele_speeds[1])
    ss=ss+'Guide Rate:      %d\n' % (self.tele_speeds[2])
    ss=ss+'Centering Rate:  %d\n' % (self.tele_speeds[3])
    ss=ss+'Focus Speed:     %d\n' % (self.focus_speed)
    ss=ss+'On Source:       %s\n' %(self.on_source_stat.isSet())
    ss=ss+'Park Status:     %s\n' %(self.park_stat.isSet())
    return ss
  def run(self):
    '''run
       Starts the telescope thread in the background, will continually monitor
       the position and status of the telescope as long as progStat and thread_stat
       are set(True)
    '''
    i=0  #Temporary variable used to loop through parmsList
    strformat=re.compile('[+-]*\d*[\/:/*]\d*[\/:\']\d*') # Used to check that the get commands are of the right fmt
    dteformat=re.compile('\d*\/\d*\/\d*') # Used to check that the get commands are of the right fmt
    self.thread_stat.set()                      # Set "thread_stat"
    self.sendcommand('#')                    # Sends a clear buffer
    while progStat==True:                    # While the "progStat" var is true run thread
      time.sleep(self.sleeptime)             # Sleep for the refresh time
      if progStat==True and self.thread_stat.isSet():
        if i<len(self._parmsList):
          self.thread_stat.wait()             # This will assure that commands do not collide
          attr=self._parmsList[i].keys()[0]  # Sets attribute name
          cmd=self.__dict__[attr][0]
          #Sets the attribute GET command and parm response
###################
#         self.__dict__[attr][2]=self.sendcommand(self.__dict__[attr][0]) 
          tstring=self.sendcommand(cmd)
          # The following is a very clumsy/lazy/inefficient way to deal with the command responses that are not
          # the correct responses.  By using the format of what is expected from the strformat and dteformat
          # above, all of the monitor commands can be made.
          # By doing the following assures that necessary attributes, ie date time azimuth etc,
          # have a proper response and if not will re-issue the command.  The CM/CMR to the telescope
          # responses with a quite different reply than the other Meade commands.  The Clumsy/lazy/ineff
          # comment is that I am sure that there are a million better ways to run this thread, but this
          # on works.
          if cmd=='GC' and not re.match(dteformat,str(tstring)):
            #print 'GC command response ',tstring
            tstring=self.sendcommand(cmd)
            #print 'GC command reissued response ',tstring
          elif cmd=='pS': pass
          elif not re.match(strformat,str(tstring)):
            #print 'Not GC command response',tstring
            tstring=self.sendcommand(cmd)
            #print 'Not GC command reissued response',tstring
          else:
            pass
            #print cmd,'else:',tstring
          self.__dict__[attr][2]=tstring
#########################
          #print time.asctime(),self.__dict__[attr][0],self.msg,self.__dict__[attr][2]
          i+=1
        else: i=0
        self.check_onsource()  # Checks to see if telescope is on source
        if self.stdout_flag: self.printout() # If "stdout_flag" true the print to std.out
        else: pass
        if self.count>=self.log_time:
          self.count=0
          if self.logging_flag: self.write_to_log()
          else: pass
        else: pass
        self.count+=1
    time.sleep(0.5)
    self.port.closedown()
    return
  def defineparms(self):
    '''defineparms
       Defines each of the key values in the TELE_PARMS dictionary as an attribute
    '''
    for each in self._parmsList:
      self.__dict__[each.keys()[0]]=each[each.keys()[0]]
    return
  def sendcommand(self,cmd):
    '''sendcommand
       The method is a very clunky at best function to send the command to the
       telescope.  It first pauses the continuous read in order to send the command
       so as to not jam the port.  There are many ways that this could be implemented
       for example a dictionary using lambda functions and formats.  This seems
       at the current time to be the easiest approach.
    '''
    #self.write_to_log(msgs='Sending Command:'+cmd)
    self.thread_stat.clear()
    junk=''
    self.msg=''
    self.cmd=cmd
    if type(cmd)==type('str'):
      # Makes sure that the command is of type string and not <None>
      if cmd=='quit':
        # quit will stop the telescope and close the telescope port
        self.msg=self.port.writeport(':Q#',size=0)
        time.sleep(0.3)
        self.port.closedown()
      elif cmd=='#':
        # clears the telescope port buffer
        self.msg=self.port.writeport('#',size=0)
      else:
        # Tack on the appropriate format characters to the command
        cmd=':'+cmd+'#'
        if cmd[1]=='G':
          # If a get command is sent, read response with writeport, which will get
          # the string response from the telescope
          if self.mount_name[0]!='M':
            self.msg=self.port.writeport(cmd,size=1024)
          else:
#           self.msg=self.port.write_meade(cmd)
            if self.port.ihost!=None:
              self.port.send(cmd)
              a,b='',''
              while b!='#':
                b=self.port.recv(1)
                a=a+b
              self.msg=a.replace('#','')
            else:
              self.msg=self.port.writeport(cmd,size=-1)
          self.msg=filter(lambda x: x in string.printable,self.msg)
          ## The following three lines are only for the Meade read back
          if cmd[1:3] in ['GZ','GA','GD','Gt','Gg'] and self.mount_name[0]=='M':
            tempstring=self.msg
            self.msg=tempstring[:3]+':'+tempstring[3:]
        else:
          # else the command is some other expecting different responses
          # See the protocol manual for command list
          if cmd[1] in ['B','F','M','h','H','I','K','P','Q','R','T','U','E','N']:
            if cmd[1:3] in ['Br','Bd','MA','QC','QW']:
              self.msg=self.port.writeport(cmd,size=1)
            elif cmd[1:3]=='MS':
              self.msg=self.port.writeport(cmd,size=1)
              if self.msg!='0': self.msg=self.port.writeport('#')
            else:
              self.msg=self.port.writeport(cmd,size=0)
          elif cmd[1]=='S':
            # The 'S' here is the set command
            if cmd[1:3] in ['SH','Sm','Sq','ST']:
              self.msg=self.port.writeport(cmd,size=0)
            elif cmd[1:3]=='SC':
              #Set date has a different format than the other set commands
              self.msg=self.port.writeport(cmd,size=100)
            else:
              self.msg=self.port.writeport(cmd,size=1)
              if cmd[1:3]=='Sz':  self.cmdposition[0]=cmd[3:-1]
              if cmd[1:3]=='Sa':  self.cmdposition[1]=cmd[3:-1]
              if cmd[1:3]=='Sr':  self.cmdposition[0]=cmd[3:-1]
              if cmd[1:3]=='Sd':  self.cmdposition[1]=cmd[3:-1]
          elif cmd[1:3] in ['pS','V#','CM']:
            if cmd[1]=='C':
              self.msg=self.port.writeport(cmd,size=100)
            elif cmd[1:3]=='pS' and self.mount_name[0]=='M':
              self.msg='N/A'
            else:
              self.msg=self.port.writeport(cmd,size=100)
          elif cmd[1]=='#':
            self.msg=self.port.writeport(cmd[1],size=0)
          else:
            self.cmd='NOT A CMD!!'
            self.msg='0'
    else: pass
    # set the thread_stat so that monitoring can resume
    #print time.asctime(),',',cmd,',',self.msg
    self.thread_stat.set()
    return self.msg
  def pauseread(self):
    '''pauseread
       will pause the thread, maybe needed in this application
    '''
    self.thread_stat.clear()
    return
  def contread(self):
    '''contread
       will continue running the thread, maybe needed in this application.
    '''
    self.thread_stat.set()
    return
  def close(self):
    '''close
       will simply stop the thread from running
    '''
    global progStat
    self.write_to_log(msgs='Thread closed/stopped')
    self.thread_stat.set()
    time.sleep(0.5)
    progStat=False
    tcomms.progStat=False
    return
  def check_onsource(self):
    '''check_onsource
    '''
    try:
      f=lambda x,y,z: float(x)+float(y)/60.0+float(z)/3600.0
      fmt=re.compile(r'(.?\d*).(\d+).(\d+).*')
      cmd0,cmd1=fmt.findall(self.cmdposition[0])[0],fmt.findall(self.cmdposition[1])[0]
      cmd0,cmd1=f(cmd0[0],cmd0[1],cmd0[2]),f(cmd1[0],cmd1[1],cmd1[2])
      if self.cmdposition[2]=='azelv':
        az_list,el_list=fmt.findall(self.azimuth[2])[0],fmt.findall(self.elevation[2])[0]
        az,el=f(az_list[0],az_list[1],az_list[2]),f(el_list[0],el_list[1],el_list[2])
        if (abs(cmd0-az+360.0)<self.postolerance or \
            abs(cmd0-az)<self.postolerance) and \
            abs(cmd1-el)<self.postolerance: 
          self.on_source_stat.set()
        else: 
          self.on_source_stat.clear()
      else:  #tele.cmdposition[2]=='radec'
        ra_list,dc_list=fmt.findall(self.rightasc[2])[0],\
          fmt.findall(self.declination[2])[0]
        ra,dc=f(ra_list[0],ra_list[1],ra_list[2]),f(dc_list[0],dc_list[1],dc_list[2])
        if (abs(cmd0-ra+24.0)<self.postolerance or \
            abs(cmd0-ra)<self.postolerance) and \
            abs(cmd1-dc)<self.postolerance: 
          self.on_source_stat.set()
        else: 
          self.on_source_stat.clear()
    except Exception: pass
    return 
  def change_site(self,location=None):
    '''change_site
         Will change the telescopes site information based on the given location information.
         Parameter:
           <location> is of type <source_cat_thread.LocationThread> or 
                    a list consisting of [latitude,longitude,elevation]
    '''
    if type(location)==LocationThread:
      self.tele_location[1]=str(location.lat)
      self.tele_location[2]=str(location.long)
      self.tele_location[3]=location.elevation
      self.init_telescope()   # This is done to send the telescope the lat and long
    elif type(location)==list: 
      self.tele_location[1]=location[0]
      self.tele_location[2]=location[1]
      self.tele_location[3]=location[2]
      self.init_telescope()   # This is done to send the telescope the lat and long
    elif type(location)==str:
      self.tele_location=['Home',str(ephem.degrees(DIMLAT/180.0*pi)).replace(':','*',1)[:-2].zfill(8),\
        str(ephem.degrees(abs(DIMLNG)/180.0*pi)).replace(':','*',1)[:-2].zfill(9),DIMELV]
      self.init_telescope()   # This is done to send the telescope the lat and long
    else:  pass   # Will do NOTHING if no location is given
    self.write_to_log(msgs='Location Changed')
    return
  def init_telescope(self):
    '''init_telescope
       Basically, sends the mount the site longitude, latitude, time, date, and
       UTC offset information.
    '''
    lat=self.tele_location[1]
    lng=self.tele_location[2]
    tme=time.strftime('%H:%M:%S')
    dte=time.strftime('%D')
    self.sendcommand('#')
    if self.mount_name[0]!='M':
      self.sendcommand('U')  #for Astrophysics mount to display high precision
      #self.command('Br00*00:00') #Set dec backlash compensation to DEFAULT
      #self.command('Bd00:00:00') #Set RA backlash compensation to DEFAULT
    self.sendcommand('SL'+tme)
    if dte.replace('0','')!=self.localdate:
      self.sendcommand('SC'+dte)
    self.sendcommand('St'+lat)
    self.sendcommand('Sg'+lng)
    self.sendcommand('SG+07')
    self.set_track(speed=9)
    self.write_to_log(msgs='Initialize command complete')
    return
  def move_to_position(self):
    '''move_to_position
         Moves the telescope to the commanded position and begins to track.
    '''
    self.on_source_stat.clear()
    self.init_telescope()
    self.set_cmd_position(az_ra=self.cmdposition[0],elv_dec=self.cmdposition[1],\
      coords=self.cmdposition[2])   # Added 10Jan17
    if self.mount_name[0]!='M': self.set_slew(speed=2) #for Astrophysics mount
    else: self.sendcommand('RS')   #for MEADE mount
    self.sendcommand('MS')
    if self.mount_name[0]!='M': self.set_track(speed=self.tele_speeds[0]) #for Astrophysics mount
    self.write_to_log(msgs='Moving to position complete')
    return
  def move_direction(self,direction=None,speed=None,rate=0):
    ''' Where direction is 'n','s','e','w','nw',etc
              speed is 'center','guide','slew'
              rate is 0,1,2,3
        This command can be used for the direction buttons or for centering,
        or guiding with the image processor.
    '''
    if speed=='guide':
      if rate>2: rate=2
      self.set_guiding(speed=rate)
    elif speed=='center':
      if rate>3: rate=3
      self.set_centering(speed=rate)
    elif speed=='slew':
      if rate>2: rate=2
      self.set_slew(speed=rate)
    else: pass
    if direction in ['n','s','e','w']:
      self.sendcommand('M'+direction)
    elif direction in ['ne','nw','se','sw']:
      self.sendcommand('M'+direction[0])
      self.sendcommand('M'+direction[1])
    elif direction in ['q','Q']: 
      self.sendcommand('Q')
    else: pass
    return
  def set_cmd_position(self,az_ra=None,elv_dec=None,coords=None):
    '''set_cmd_position
         Used to set the az/elv or ra/dec commanded positions self.cmdposition
         list parameters.
         Parameters
           <az_ra>   The commanded az or ra
           <elv_dec> The commanded elv or dec
           <coords>  The coordinate system either 'azelv' or 'radec'
    '''
    # Assures the format for az, elv, and dec to 'DD*MM\'SS' while ra set to 'HH:MM:SS'
    if az_ra and coords=='azelv': 
      az_ra=az_ra[:5].replace(':','*')+az_ra[5:].replace(':','\'')
    if elv_dec: elv_dec=elv_dec[:5].replace(':','*')+elv_dec[5:].replace(':','\'')
    # If the coordinates are az/elv set the appropiate coordinates, if any are None
    # this will set that variable to the current value.  This assures that both
    # directions are set concurrently.
    if coords=='azelv':
      if az_ra: self.cmdposition[0]=az_ra
      else: self.cmdposition[0]=self.azimuth[2]
      if elv_dec: self.cmdposition[1]=elv_dec
      else: self.cmdposition[1]=elv_dec=self.elevation[2]
      self.sendcommand('Sz'+self.cmdposition[0])
      self.sendcommand('Sa'+self.cmdposition[1])
      self.cmdposition[2]='azelv'
    elif coords=='radec':                      # Added 10Jan17
      if az_ra: self.cmdposition[0]=az_ra
      else: self.cmdposition[0]=self.rightasc[2]
      if elv_dec: self.cmdposition[1]=elv_dec
      else: self.cmdposition[1]=elv_dec=self.declination[2]
      self.sendcommand('Sr'+self.cmdposition[0])
      self.sendcommand('Sd'+self.cmdposition[1])
      self.cmdposition[2]='radec'
    else: pass                                 # Added 10Jan17
    self.write_to_log(msgs='Setting Command Position')
    return
  def set_track(self,speed=2):
    '''set_track
       Sets the tracking rate as follows
       Parameters
       <speed> is an integer defined as follows 
         0=Lunar, 1=Solar, 2=Sidereal, 9=Stop Tracking
    '''
    self.tele_speeds[0]=speed
    if self.mount_name[0]!='M':
      self.sendcommand('RT'+str(speed))
    else:
      pass
    self.write_to_log(msgs='Setting Track Speed to '+str(speed))
    return
  def set_slew(self,speed=2):
    '''set_slew
       Sets the slew rate as follows
       Parameters
       <speed> is an integer defined as follows 
         0= 600x, 1= 900x, 2= 1200x
    '''
    self.tele_speeds[1]=speed
    if self.mount_name[0]!='M':
      self.sendcommand('RS'+str(speed))
    else:
      self.sendcommand('RS')
    self.write_to_log(msgs='Setting Slew Speed to '+str(speed))
    return
  def set_centering(self,speed=1):
    '''set_centering
       Sets the centering rate as follows
       Parameters
       <speed> is an integer defined as follows 
         0= 12x, 1= 64x, 2= 600x, 3=1200x
    '''
    self.tele_speeds[3]=speed
    if self.mount_name[0]!='M':
      self.sendcommand('RC'+str(speed))
    else:
      self.sendcommand('RC')
    self.write_to_log(msgs='Setting Centering Speed to '+str(speed))
    return
  def set_guiding(self,speed=1):
    '''set_guiding
       Sets the guiding rate as follows
       Parameters
       <speed> is an integer defined as follows 
         0= 0.25x, 1= 0.5x, 2= 1.0x
    '''
    self.tele_speeds[2]=speed
    if self.mount_name[0]!='M':
      self.sendcommand('RG'+str(speed))
    else:
      self.sendcommand('RG')
    self.write_to_log(msgs='Setting Guiding Speed to '+str(speed))
    return
  def park_telescope(self):
    '''park_telescope
       First sends the date, time, and then sends the telescope to park 1
       position, west side of mount pointing north.
    '''
    self.init_telescope()
    self.write_to_log(msgs='Parking Telescope')
    self.sendcommand('Sz'+TELE_PARK_POS1[0])
    self.sendcommand('Sa'+TELE_PARK_POS1[1])
    self.cmdposition[2]='azelv'
    self.sendcommand('MS')
    self.sendcommand('KA')
    self.park_stat.set()
    return
  def unpark_telescope(self):
    '''unpark_telescope
       First sends the date, time, and then sets the telescope park 1
       position, west side of mount pointing north, calibrates(syncs), 'quits'
       any motion, and set the track rate to sidereal
    '''
    self.init_telescope()
    self.write_to_log(msgs='Unparking Telescope')
    self.sendcommand('Sz'+TELE_PARK_POS1[0])
    self.sendcommand('Sa'+TELE_PARK_POS1[1])
    self.cmdposition[2]='azelv'
    self.sendcommand('CM')
    self.sendcommand('Q')
    #self.sendcommand('RT2')
    self.park_stat.clear()
    return
  def re_calibrate(self):
    '''re_calibrate
         will re-set the RA/DEC and recalibrate the mount to that position
         only if the commanded position coordinates are 'radec'
    '''
    self.write_to_log(msgs='Recalibrating Telescope')
    if self.cmdposition[2]=='radec':
      self.sendcommand('Sr'+self.cmdposition[0])
      self.sendcommand('Sd'+self.cmdposition[1])
      self.sendcommand('CMR')
    else: pass
    return
  def move_focus(self,direction=0,speed=None):
    '''move_focus
         Sets and moves the focus 
         <speed> default to 0=slow, 1=fast
         <direction> is -1 for retract, 0 to stop, and +1 to advance
    '''
    if speed!=None: self.focus_speed=speed
    fspstr=['S','F'][self.focus_speed]
    fstr=['Q','+','-'][direction]
    self.sendcommand('F'+fspstr)
    self.sendcommand('F'+fstr)
    self.write_to_log(msgs='Moving Focus in '+fstr+' rate of '+fspstr)
    return
  def write_to_log(self,msgs=None):
    '''write_to_log
         will write to logfile after self.log_time has elapsed
    '''
    cur_date=time.strftime('%m.%d.%Y')
    subdir1=os.path.join(LOG_DIR,time.strftime('%b%Y'))
    fullpath=os.path.join(subdir1,time.strftime('%B%d'))
    if not os.path.exists(fullpath): os.makedirs(fullpath)
    if cur_date not in self.logfile_name:
      self.logfile_name=os.path.join(fullpath,TELE_LOGBASENAME+'.'+cur_date)
    if os.path.exists(self.logfile_name):
      apfile='a'
    else:
      apfile='w'
    fp=open(self.logfile_name,apfile)
    if apfile=='w':
      fp.write('#Telescope log for %s %s\n' %(self.localdate[2],self.localtime[2]))
      fp.write('#\n')
      fp.write('#%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % \
        ('Local Time','Local Date','Local LST','Right Ascension',\
        'Declination','Azimuth','Elevation','Command RA/Az','Command Dec/elv','OnSource'))
      fp.write('#\n')
    if msgs==None:
      fp.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % \
        (self.localtime[2],self.localdate[2],self.sidrtime[2],\
        self.rightasc[2],self.declination[2],self.azimuth[2],self.elevation[2],\
        self.cmdposition[0],self.cmdposition[1],self.on_source_stat.isSet()))
    else:
      fp.write('#%s %s: %s\n' % (self.localdate[2],self.localtime[2],msgs))
    fp.close()
    return
  def printout(self):
    '''printout
       helpful for testing by writing the port's output message to std.out
    '''
    clr='\x08'*57
    sys.stdout.write(clr)
    for each in self._parmsList:
      attr=self.__dict__[each.keys()[0]]
      sys.stdout.write(attr[1]+': %s\n' %(attr[2]))
    sys.stdout.write('Command Position: (%s,%s)\nCoordinates:%s\n' %\
      (self.cmdposition[0],self.cmdposition[1],self.cmdposition[2]))
    sys.stdout.write('On Source: %s\n' %(self.on_source_stat.isSet()))
    sys.stdout.write('Command: %s\n' %(self.cmd))
    sys.stdout.write('Message: %s\n' %(self.msg))
    sys.stdout.write('\n')
    sys.stdout.flush()
    return

####
#
# Some notes about telescope moving
#
####
# To move to an azimuth and elevation at 600x slew and not track on that position use:
#>>> tele.sendcommand('RS0');tele.init_telescope();tele.sendcommand('Sa+45*00\'00')
#>>> tele.sendcommand('Sz190*00\'00');tele.sendcommand('MS');tele.sendcommand('RT9')
#
# To move to an azimuth and elevation at 1200x slew speed and track at sidereal rate use:
#>>> tele.sendcommand('RS2');tele.init_telescope();tele.sendcommand('Sa+45*00\'00')
#>>> tele.sendcommand('Sz190*00\'00');tele.sendcommand('MS');tele.sendcommand('RT2')
#
# To move to an RA and dec at 1200x slew speed and track at sidereal rate use:

#
# To move to an RA and dec at 1200x slew speed and track at sidereal rate use:
#>>> tele.sendcommand('RS2');tele.sendcommand('Sr21:00:00');
#>>> tele.sendcommand('Sd+15*00\'00');tele.sendcommand('MS');tele.sendcommand('RT2')
#
# To move north, south, east, or west use, using centering rate and resending the guide
# rate.  A ':Q#' terminates this command:
#>>> tele.sendcommand('RC2');tele.sendcommand('Ms');tele.sendcommand('RG2')
# If centering is required use the Ms, Mn, Me, Mw and the CMR command
