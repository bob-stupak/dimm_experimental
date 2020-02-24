#!/usr/bin/env python ippower_cnt.py
#
import sys
sys.path.append('..')

from Tkinter import *
import Pmw as pmw
import urllib
import urllib2
import guis.frame_gui as fg

IPPOWER_IPADDRESS='169.254.95.101'

###There is also a SetSchedulePower command for scheduling, see manual.
class PowerStatusGUI(fg.FrameGUI):
  def __init__(self,root=None,col=0,row=0,colspan=1,rowspan=1):
    self._checkList=[['Ch1Stat','MOXA box','horizontal','radiobutton',\
                     ['On','Off'],None,(0,0,3,1,'nsew')],\
                     ['Ch2Stat','Cameras','horizontal','radiobutton',\
                     ['On','Off'],None,(0,1,3,1,'nsew')],\
                     ['Ch3Stat','Nothing','horizontal','radiobutton',\
                     ['On','Off'],None,(0,2,3,1,'nsew')],\
                     ['Ch4Stat','Astrophysics','horizontal','radiobutton',\
                     ['On','Off'],None,(0,3,3,1,'nsew')]]
    self._buttonList=[['allonButton','All ON','self.all_on',(0,4,3,1,'nsew')],\
                      ['alloffButton','All OFF','self.all_off',(0,5,3,1,'nsew')]]
    fg.FrameGUI.__init__(self,root=root,name='Power Status',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    self.ipaddress=IPPOWER_IPADDRESS
    self.url_response=None
    self.channels=['0','0','0','0']
    self.send_to_ippwr('status')
    self.config_self()
    return
  def config_self(self):
    for each in self._checkList:
      ch=int(each[0][2])
      self.__dict__[each[0]].setvalue('%s' % (['Off','On'][int(self.channels[ch-1])]))
      self.__dict__[each[0]].component('label').configure(width=15)
      self.__dict__[each[0]].component('label').configure(anchor='w')
      self.__dict__[each[0]].configure(command=self.power_command)
      #for i in range(2):
      #  self.__dict__[each[0]].button(i).configure(state='disabled')
      #  self.__dict__[each[0]].button(i).configure(anchor='e')
      #  self.__dict__[each[0]].button(i).configure(disabledforeground='Black')
    return
  def all_on(self,*tag):
    for each in self._checkList:
      stat=self.__dict__[each[0]].setvalue('On')
    self.power_command()
    return
  def all_off(self,*tag):
    for each in self._checkList:
      stat=self.__dict__[each[0]].setvalue('Off')
    self.power_command()
    return
  def power_command(self,*tag):
    for each in self._checkList:
      ch=int(each[0][2])
      stat=self.__dict__[each[0]].getvalue()
      if stat=='Off': self.channels[ch-1]='0'
      else: self.channels[ch-1]='1'
    self.send_to_ippwr('set')
    return 
  def send_to_ippwr(self,status):
    if status=='status':
      req='http://admin:1"Fwhm@'+self.ipaddress+'/Set.cmd?CMD=GetPower'
    else:
      p1='P60='+self.channels[0]
      p2='P61='+self.channels[1]
      p3='P62='+self.channels[2]
      p4='P63='+self.channels[3]
      req='http://admin:1"Fwhm@'+self.ipaddress+'/Set.cmd?CMD=SetPower+'
      req=req+p1+'+'+p2+'+'+p3+'+'+p4
    try:  #If there is an established connection to the IPPower strip
      self.component('ring').configure(bg='lightgray')
      self.component('tag').configure(bg='lightgray')
#     self.url_response=urllib2.urlopen(req,timeout=99).read().replace('</html>','')
      self.url_response=urllib.urlopen(req).read().replace('</html>','')
      l_response=self.url_response.split('P')
      self.channels=map(lambda x: x.split('=')[1].replace(',','')[0],l_response[1:5])
    except Exception: #Exception, nothing happens and background set to red
      self.component('ring').configure(bg='red')
      self.component('tag').configure(bg='red')
    for each in self._checkList:
      ch=int(each[0][2])
      self.__dict__[each[0]].setvalue('%s' % (['Off','On'][int(self.channels[ch-1])]))
    return 

def ippower(chan=-1,state=0):
  ''' <ippower>
        This function will turn on or off all or a selected channel with arguments as follows

        Where <chan>=-1,1,2,3,4 and <state>=0,1
        <chan>=-1 indicates turning all on or off depending on <state>
        <chan>=1,2,3,4 will only turn that channel on or off depending on <state>
        <state>=0,1 is OFF,ON  integer boolean
  '''
  cmd='http://admin:1"Fwhm@'+IPPOWER_IPADDRESS+'/Set.cmd?CMD=SetPower'
  if chan>=1 and chan<=4:
    cmd_req='+P6'+str(chan-1)+'='+str(state)
    cmd=cmd+cmd_req
  elif chan==-1:
    for i in range(4):
      cmd_req='+P6'+str(i)+'='+str(state)
      cmd=cmd+cmd_req
  else: pass  #IP power doesn't have that channel number
# reply_from_cmd=urllib2.urlopen(cmd,timeout=99).read().replace('</html>','')
  try:
    reply_from_cmd=urllib.urlopen(cmd).read().replace('</html>','')
  except Exception:
    reply_from_cmd='NO NETWORK CONNECTION to IPPower unit'
  req='http://admin:1"Fwhm@'+IPPOWER_IPADDRESS+'/Set.cmd?CMD=GetPower'
# reply_status=urllib2.urlopen(req,timeout=99).read().replace('</html>','')
  try:
    reply_status=urllib.urlopen(req).read().replace('</html>','')
    chan_stat=[each[0] for each in reply_status.split('=')[1:5]]
  except Exception:
    reply_status='NO NETWORK CONNECTION to IPPower unit'
    chan_stat=['0','0','0','0']
  return chan_stat

if __name__=='__main__':
  mm=Tk()
  mm.title('Power Control GUI')
  pcntrl=PowerStatusGUI(root=mm,col=0,row=1)
  xButton=Button(mm,text='Exit',font='Times -10',command=mm.destroy,width=6,padx=0,pady=0)
  xButton.grid(column=0,row=0,sticky='nsw')
  mm.mainloop()
