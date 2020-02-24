#! /usr/bin/env python camera_gui.py

import sys
sys.path.append('..')

from Tkinter import *
from Pmw import Group
import guis.frame_gui as fg
import guis.imagecanvasgui as icanv
import time

import camera_sbig,camera_prosilica,camera_supercircuits,camera_thread

from common_parms import *

progStat=True

class GeneralFrame(fg.FrameGUI):
  def __init__(self,parent=None,col=0,row=0,colspan=1,rowspan=1):
    self.parent=parent
    self.root=parent.interior()
    self.fileformat='fits'
    self.filename='testimage'+'.'+self.fileformat
    self._mesBarList=[['dateMess','Local Date',15,(0,0,3,1,'nsew')],\
                      ['timeMess','Local Time',15,(0,1,3,1,'nsew')],\
                      ['heightMess','Height',15,(3,1,3,1,'nsew')],\
                      ['widthMess','Width',15,(3,2,3,1,'nsew')],\
                      ['messageMess','Message',25,(0,30,6,1,'nsew')]]
    self._buttonList=[['saveImageButton','Save Image',\
                      '(lambda slf=self: slf.save_image())',(1,20,1,1,'nsew')]]#,\
    self._checkList=[['loggingStat','Logging','horizontal','radiobutton',['False','True'],\
                      self.set_logging,(4,20,3,1,'nsew')],\
                     ['fileFormat','File Format','horizontal','radiobutton',['fits','jpg'],\
                      self.set_fileformat,(4,21,3,1,'nsew')]]
    self._optionList=[['device_select','Device',self.parent.device_name,CAMERA_LIST,\
                      self.set_device,(3,0,3,1,'nsew')]]
    self._entryList=[['filenameEntry','File Name',self.filename,\
                     {'validator':None},self.set_filename,20,(0,21,3,1,'nsw')]]
    fg.FrameGUI.__init__(self,root=self.root,name='General Parameters',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    self.fileFormat.setvalue(self.fileformat)
    self.set_device(self.parent.device_name)
    self.loggingStat.setvalue(str(self.parent.device.logging_flag))
    self.check_update()
    return
  def set_device(self,device_name):
    self.parent.device_name=device_name
    self.parent.set_device()
    return
  def save_image(self):
    self.parent.device.save_image(fname=self.filename.split('.')[0],fmt=self.fileformat)
    return
  def set_filename(self):
    self.filename=self.filenameEntry.component('entry').get()
    return
  def set_fileformat(self,*tags):
    self.fileformat=self.fileFormat.getcurselection()
    self.filename=self.filename.split('.')[0]+'.'+self.fileformat
    self.filenameEntry.var.set(self.filename)
    self.filenameEntry.set_entry(self.filename)
    return
  def set_logging(self,*tags):
    logging=self.loggingStat.getcurselection()
    if logging=='True':self.parent.device.logging_flag=True
    else: self.parent.device.logging_flag=False
    return
  def check_update(self):
    try:
      self.dateMess.message('state','%s' % self.parent.device.local_date)
      self.timeMess.message('state','%s' % self.parent.device.local_time)
      self.heightMess.message('state','%d' % self.parent.device.chip_height)
      self.widthMess.message('state','%d' % self.parent.device.chip_width)
      self.messageMess.message('state','%s' % self.parent.device.message)
    except Exception: pass
    self.after(250,self.check_update)
    return

class ExposureFrame(fg.FrameGUI):
  def __init__(self,parent=None,col=0,row=0,colspan=1,rowspan=1):
    self.parent=parent
    self.root=parent.interior()
    self._mesBarList=[['expcountStat','Exposure Count',15,(0,0,3,1,'nsew')],\
                      ['seqcountStat','Sequence Count',15,(0,1,3,1,'nsew')],\
                      ['queuecountStat','Queue Count',15,(0,2,3,1,'nsew')],\
                      ['numseqcountStat','Number of Seqs',15,(0,3,3,1,'nsew')],\
                      ['dataMean','Mean Data',15,(3,0,3,1,'nsew')],\
                      ['dataStd','Std Data',15,(3,1,3,1,'nsew')]]
    self._buttonList=[['startExpButton','Start Exposure',\
                      '(lambda slf=self: slf.start_exposure())',(1,11,1,1,'nsew')],\
                      ['resetCountButton','Reset Count',\
                      '(lambda slf=self: slf.reset_count())',(1,4,1,1,'nsew')]]
    self._entryList=[['expTime','Exposure time',str(self.parent.device.exptime),\
                     {'validator':'real'},self.set_exptime,15,(0,8,3,1,'nsew')],\
                     ['gainEntry','Gain',str(self.parent.device.gain),\
                     {'validator':'real'},self.set_gain,15,(3,8,3,1,'nsew')],\
                     ['expListEntry','Exposure Sequence',\
                     str(self.parent.device.seq_exp_list).replace(']','').replace('[',''),\
                     {'validator':None},self.set_explist,15,(0,9,3,1,'nsew')],\
                     ['seqtotEntry','Total Num Seq',str(self.parent.device.sequence_total_number),\
                     {'validator':'integer'},self.set_seq_total,15,(3,10,3,1,'nsew')],\
                     ['autoDelay','Auto Delay',str(self.parent.device.auto_delay),\
                     {'validator':'real'},self.set_autodelay,15,(4,9,3,1,'nsew')]]
    self._checkList=[['autoseqStat','Auto Sequence','horizontal','radiobutton',\
                      ['On','Off'],self.set_auto_sequence,(0,10,3,1,'nsew')]]
    fg.FrameGUI.__init__(self,root=self.root,name='Exposure Parameters',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    blank1=fg.BlankSpace(root=self.interior(),col=0,row=5,colspan=6)
    #blank2=fg.BlankSpace(root=self.interior(),col=0,row=3,colspan=6)
    self.check_update()
    return
  def reset_count(self):
    self.parent.device.exposure_count=0
    self.parent._figure.plot_count=0
    return
  def set_autodelay(self):
    xdelay=self.autoDelay.component('entry').get()
    self.expListEntry.var.set(xdelay)
    self.parent.device.auto_delay=float(xdelay)
    return
  def set_explist(self):
    xtmelist=self.expListEntry.component('entry').get()
    self.expListEntry.var.set(xtmelist)
    self.parent.device.seq_exp_list=[float(each) for each in xtmelist.split(',')]
    return
  def set_exptime(self):
    xtme=self.expTime.component('entry').get()
    self.expTime.var.set(xtme)
    self.parent.device.exptime=float(xtme)
    return
  def set_gain(self):
    gain=self.gainEntry.component('entry').get()
    self.gainEntry.var.set(gain)
    self.parent.device.gain=float(gain)
    return
  def set_seq_total(self):
    seqnumber=self.seqtotEntry.component('entry').get()
    self.seqtotEntry.var.set(seqnumber)
    self.parent.device.sequence_total_number=float(seqnumber)
    return
  def start_exposure(self):
    if self.parent.device!=None:
      self.parent.device.acquire_image()
    return
  def set_auto_sequence(self,tag):
    if self.autoseqStat.getvalue()=='On':
      self.parent.device.auto_sequence_stat.set()
    else:
      self.parent.device.auto_sequence_stat.clear()
    return
  def check_auto_sequence(self):
    if self.parent.device.auto_sequence_stat.isSet():
      self.autoseqStat.setvalue('On')
    else:
      self.autoseqStat.setvalue('Off')
    return
  def check_update(self):
    try:
      self.expcountStat.message('state','%d' % self.parent.device.exposure_count)
      self.seqcountStat.message('state','%d' % self.parent.device.auto_count)
      self.queuecountStat.message('state','%d' % self.parent.device.data_queue.qsize())
      self.numseqcountStat.message('state','%d' % self.parent.device.sequence_count)
      self.dataMean.message('state','%7.3f' % self.parent.device.data.mean())
      self.dataStd.message('state','%7.3f' % self.parent.device.data.std())
      self.check_auto_sequence()
      if self.parent.device.take_exposure_stat.isSet():   #For auto-sequencing update the exposure gui
        self.expTime.var.set(str(self.parent.device.exptime))
        self.expTime.set_entry(str(self.parent.device.exptime))
    except Exception: pass
    self.after(10,self.check_update)
    return

class ProsilicaFrame(fg.FrameGUI):
  def __init__(self,parent=None,col=0,row=0,colspan=1,rowspan=1):
    self.parent=parent
    self.root=parent.interior()
    self._mesBarList=[['heightNumb','Height',15,(0,0,3,1,'nsew')],\
                      ['widthNumb','Width',15,(0,1,3,1,'nsew')],\
                      ['offsetxNumb','Offset X',15,(0,3,3,1,'nsew')],\
                      ['offsetyNumb','Offset Y',15,(0,2,3,1,'nsew')],\
                      ['binXNumb','Binning X',15,(0,5,3,1,'nsew')],\
                      ['binYNumb','Binning Y',15,(0,4,3,1,'nsew')]]
    self._entryList=[['heightEntry','Height',str(self.parent.device.camera.Height),\
                     {'validator':'integer'},self.set_region,15,(4,0,3,1,'nsew')],\
                     ['widthEntry','Width',str(self.parent.device.camera.Width),\
                     {'validator':'integer'},self.set_region,15,(4,1,3,1,'nsew')],\
                     ['offxEntry','OffsetX',str(self.parent.device.camera.OffsetX),\
                     {'validator':'integer'},self.set_region,15,(4,3,3,1,'nsew')],\
                     ['offyEntry','OffsetY',str(self.parent.device.camera.OffsetY),\
                     {'validator':'integer'},self.set_region,15,(4,2,3,1,'nsew')],\
                     ['binxEntry','Binning X',str(self.parent.device.camera.BinningHorizontal),\
                     {'validator':'integer'},self.set_binning,15,(4,5,3,1,'nsew')],\
                     ['binyEntry','Binning Y',str(self.parent.device.camera.BinningVertical),\
                     {'validator':'integer'},self.set_binning,15,(4,4,3,1,'nsew')]]
    self._buttonList=[['resetButton','Reset',\
                      '(lambda slf=self: slf.reset_camera())',(1,12,1,1,'nsew')]]
    fg.FrameGUI.__init__(self,root=self.root,name='Prosilica Parameters',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    #blank1=fg.BlankSpace(root=self.interior(),col=0,row=3,colspan=6)
    #blank2=fg.BlankSpace(root=self.interior(),col=0,row=3,colspan=6)
    self.check_update()
    return
  def reset_camera(self):
    #self.parent.device.camera.binning_x=1
    #self.parent.device.camera.binning_y=1
    self.parent.device.offset_x=0
    self.parent.device.offset_y=0
    self.parent.device.height=self.parent.device.chip_height
    self.parent.device.width=self.parent.device.chip_width
    self.parent.device.init_gige_parms()
    self.heightNumb.message('state','%d' % self.parent.device.height)
    self.widthNumb.message('state','%d' % self.parent.device.width)
    self.offsetxNumb.message('state','%d' % self.parent.device.offset_x)
    self.offsetyNumb.message('state','%d' % self.parent.device.offset_y)
    self.binXNumb.message('state','%d' % self.parent.device.binning_x)
    self.binYNumb.message('state','%d' % self.parent.device.binning_y)
    self.heightEntry.setentry(self.parent.device.height)
    self.widthEntry.setentry(self.parent.device.width)
    self.offxEntry.setentry(self.parent.device.offset_x)
    self.offyEntry.setentry(self.parent.device.offset_y)
    return
  def set_region(self):
    h=int(self.heightEntry.component('entry').get())
    w=int(self.widthEntry.component('entry').get())
    offx=int(self.offxEntry.component('entry').get())
    offy=int(self.offyEntry.component('entry').get())
    self.parent.device.set_roi(h=h,w=w,offx=offx,offy=offy)
    return
  def set_binning(self):
    vert=int(self.binyEntry.component('entry').get())
    horz=int(self.binxEntry.component('entry').get())
    self.parent.device.set_binning(hor=horz,vert=vert)
    return
  def check_update(self):
    try:
      self.heightNumb.message('state','%d' % self.parent.device.height)
      self.widthNumb.message('state','%d' % self.parent.device.width)
      self.offsetxNumb.message('state','%d' % self.parent.device.offset_x)
      self.offsetyNumb.message('state','%d' % self.parent.device.offset_y)
      self.binXNumb.message('state','%d' % self.parent.device.binning_x)
      self.binYNumb.message('state','%d' % self.parent.device.binning_y)
    except Exception: pass
    self.after(250,self.check_update)
    return

class TempCntrFrame(fg.FrameGUI):
  def __init__(self,parent=None,col=0,row=0,colspan=1,rowspan=1):
    self.parent=parent
    self.root=parent.interior()
    self._mesBarList=[['setpntStat','Setpoint',15,(0,0,3,1,'nsew')],\
                      ['ccdtempStat','CCD Temperature',15,(0,1,3,1,'nsew')],\
                      ['ambtempStat','Amb Temperature',15,(3,0,3,1,'nsew')],\
                      ['powerStat','Control Power',15,(3,1,3,1,'nsew')]]
    self._entryList=[['setpntEntry','Set Point',str(self.parent.device.cmd_setpoint),\
                     {'validator':'real'},self.set_setpnt,15,(0,2,3,1,'nsew')]]
    self._checkList=[['regtempStat','Temperature Control','horizontal','radiobutton',\
                      ['On','Off'],self.tempReg,(0,5,3,1,'nsew')]]
    fg.FrameGUI.__init__(self,root=self.root,name='Temperature Parameters',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    blank1=fg.BlankSpace(root=self.interior(),col=0,row=3,colspan=6)
    #blank2=fg.BlankSpace(root=self.interior(),col=0,row=3,colspan=6)
    self.check_update()
    return
  def set_setpnt(self):
    self.parent.device.cmd_setpoint=float(self.setpntEntry.component('entry').get())
    return
  def tempReg(self,tag):
    if self.regtempStat.getvalue()=='On':
      self.set_setpnt()
      self.parent.device.temp_regulation(True)
    else:
      self.parent.device.temp_regulation(False)
    return
  def check_temp_reg(self):
    if self.parent.device.treg_enabled: self.regtempStat.setvalue('On')
    else: self.regtempStat.setvalue('Off')
    return
  def check_update(self):
    try:
      self.setpntStat.message('state','%7.3f' % self.parent.device.temp_setpoint)
      self.ccdtempStat.message('state','%7.3f' % self.parent.device.ccdtemp)
      self.ambtempStat.message('state','%7.3f' % self.parent.device.ambtemp)
      self.powerStat.message('state','%7.3f' % self.parent.device.power)
      if hasattr(self.parent.device,'treg_enabled'):
        self.check_temp_reg()
      else: pass
    except Exception: pass
    self.after(250,self.check_update)
    return
  
class CameraGUI(fg.FrameGUI):
  def __init__(self,root=None,parent=None,col=0,row=0,colspan=1,rowspan=1,device=None,device_name=None):
    self.parent=parent
    if device:
      self.device_name=device.camera_name
      self.device=device
    else:
      self.device_name=device_name
      self.device=None
      if device==None: self.set_device()
    fg.FrameGUI.__init__(self,root=root,name='Camera Items',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    self.general_frame=GeneralFrame(parent=self,col=0,row=0,colspan=1,rowspan=1)
    self.expose_frame=ExposureFrame(parent=self,col=0,row=1,colspan=1,rowspan=1)
#   if device==None: self.set_device()
    if self.parent==None:
      self._figure=icanv.ImageCanvas(root=self.interior(),col=1,row=0,rowspan=6)
    else:
      self._figure=self.parent._figure
    self.check_update()
    return
  def stopAll(self):
    try: self.device.close()
    except Exception: pass
    self.destroy()
    return
  def check_update(self):
    if hasattr(self,'device') and self.device!=None:
      if not self.device.data_queue.empty():
        data=self.device.data_queue.get()
        self.device.new_data_ready_stat.clear()
        self._figure.data_queue.put(data)
# The above was changed on 22May as a test with an imagecanvas data queue.
#       self._figure.change_image(data)
#       self._figure.splot.set_title('Exposure Count: %d, Exposure Time: %10.4f, Gain: %7.3f' % \
#         (self.device.exposure_count,self.device.exptime,self.device.gain),family='serif',fontsize=12)
        self._figure.draw()
    self.after(1,self.check_update)
    return
  def set_device(self):
    try:
      self.device.close()
      self.device=None
      self._figure.plot_count=0
    except Exception: pass
    if hasattr(self.parent,'tempct_frame'):
      self.tempct_frame.destroy()
      del self.tempct_frame
    else: pass
    if hasattr(self,'prosilica_frame'):
      self.prosilica_frame.destroy()
      del self.prosilica_frame
    else: pass
    if self.device_name=='Simulation':
      self.device=camera_thread.CameraThread()
    elif self.device_name=='GT1290':
      self.device=camera_prosilica.CameraThread(camera_name='GT1290')
    elif self.device_name=='GX2750':
      self.device=camera_prosilica.CameraThread(camera_name='GX2750')
    elif self.device_name=='SBIG':
      self.device=camera_sbig.CameraThread(devmode='s')
    elif self.device_name=='Video':
      self.device=camera_supercircuits.CameraThread(channel=VIDEO_CHANNEL)
    else: pass
    if self.device_name=='SBIG':
      self.tempct_frame=TempCntrFrame(parent=self,col=0,row=2,colspan=1,rowspan=1)
    else: pass
    if self.device_name=='GT1290' or self.device_name=='GX2750':
      self.prosilica_frame=ProsilicaFrame(parent=self,col=0,row=2,colspan=1,rowspan=1)
    else: pass
    if self.device_name!='file' and self.device_name!=None:
      time.sleep(0.1)
      self.device.start()
    else: pass  # Maybe used one day for a 'file' device
    return

##def start_dark(self):
##  self.camera.take_dark()
##  return
##def start_bias(self):
##  self.camera.take_bias()
##  return
# def set_dark_subtract(self,tag):
#   if self.darksubStat.getvalue()=='On':
#     self.take_dark_subt=True
#     print 'Setting Dark Subt'
#   else:
#     self.take_dark_subt=False
#     print 'Unsetting Dark Subt'
#   return

def stopProgs():
  global cgui
  print 'Stopping Camera Processes'
  cgui.stopAll()
  print 'Sucessfully exited'
  sys.exit()
  return

if __name__=='__main__':
  global root,cgui
  progStat=True
  try:
    mindex=sys.argv.index('-cname')+1
    cname=sys.argv[mindex]
  except Exception:
    cname='Simulation'   #For simulation mode
  root=Tk()
  root.protocol('WM_DELETE_WINDOW',stopProgs)
  fgui=fg.FrameGUI(root=root,name='Camera GUI',col=0,row=1,colspan=4)
  cgui=CameraGUI(root=fgui.interior(),col=4,row=1,device_name=cname)
  xx=Button(root,text='Exit',font=fg.TEXT_FONT,command=stopProgs,\
    width=6,padx=0,pady=0)
  xx.grid(column=0,row=0,sticky='nw')
  root.mainloop()
