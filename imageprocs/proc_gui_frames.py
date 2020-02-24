#!/usr/bin/env python proc_gui_frames.py

import sys
sys.path.append('..')

import time
import os

from Tkinter import *
import Pmw as pmw

import guis.frame_gui as fg
import guis.imagecanvasgui as icanv

import image_proc_thread as imthread
import image_proc_file as imfile

from common_parms import *

class ImageFrame(fg.FrameGUI):
  def __init__(self,name='File Frame',root=None,col=0,colspan=1,row=0,rowspan=1):
    if not root: self.root=Tk()
    elif hasattr(root,'interior'): self.root=root.interior()
    else: self.root=root
    self._mesFrameList=[['file_info','File Information',['Current Time','File Name','Observed Time'],\
                        (0,0,2,1,'nsew')]]
    self._buttonList=[['open','Open','self.open_image',(0,2,1,1,'nsew')],\
                      ['write','Write','self.write_image',(1,2,1,1,'nsew')],\
                      ['get_time','Get Time','self.get_current_time',(0,3,1,1,'nsew')],\
                      ['view_header','View Header','self.view_header_info',(1,3,1,1,'nsew')]]
    self._checkList=[['file_format','File Format','horizontal','radiobutton',['fits','jpg'],\
                      self.get_fileformat,(0,5,2,1,'nsew')]]
    self._entryList=[['filename_entry','File Name','',{'validator':None},self.set_filename,\
                     20,(0,4,2,1,'nsw')]]
    fg.FrameGUI.__init__(self,root=self.root,name=name,col=col,colspan=colspan,row=row,rowspan=rowspan)
    if hasattr(root,'_figure'): self._figure=root._figure
    else: self._figure=icanv.ImageCanvas(root=self.interior(),col=300,rowspan=300)
    self.file_format.setvalue('fits')
    self.imagefile=None
    self.current_dir=IMG_DIR
    self.after_id=None
    self.check_update()
    return
  def set_image(self,image):
    self.imagefile=image
    return
  def get_fileformat(self,*tags):
    fileformat=self.file_format.getcurselection()
    return fileformat
  def set_filename(self):
    fname=self.filename_entry.component('entry').get()
    if self.imagefile: self.imagefile.fname=fname
    return
  def get_current_time(self):
    if self.imagefile: self.imagefile.get_time()
    return
  def write_image(self):
    fileformat=self.get_fileformat()
    fname=self.filename_entry.component('entry').get()
    if self.imagefile:
      self.imagefile.write_new_image(fname=fname,fmt=fileformat)
    return
  def open_image(self):
    if self.current_dir!=IMG_DIR: itm_list=['../']+os.listdir(self.current_dir)
    else: itm_list=os.listdir(IMG_DIR)
    self.dialog=fg.SelectDialog(parent=self,title='File Selection',\
      command=self.change_image_file,select_items=itm_list)#os.listdir(self.current_dir))
    self.dialog.bind('<Double-Button-1>',self.change_image_file)
    return
  def change_image_file(self, result):
    sels = self.dialog.getcurselection()
    if len(sels)==0:
      self.dialog.withdraw()
      self.dialog.deactivate(result)
    else:
      if sels[0]!='../': fname=self.current_dir+sels[0]
      else: fname=self.current_dir+'/'+sels[0]
      if os.path.isdir(fname):
        os.chdir(fname)
        self.current_dir=fname+'/'
        self.dialog.component('scrolledlist').setlist(['../']+os.listdir('./'))
      elif os.path.isfile(fname):
        fname=fname.split('imgdata/')[1].rsplit('..//')[-1]
        self.set_image(imfile.ImageFile(fname=fname))
        self._figure.data_queue.put(self.imagefile.data)
        self.dialog.self_destroy(result)
        del self.dialog
      else: pass
    return
  def view_header_info(self):
    if self.imagefile:
      self.head_dialog=pmw.TextDialog(self.root,scrolledtext_labelpos='n',title='File Header Information',\
        defaultbutton=0,label_text='Header')
      self.head_dialog.insert('end',str(self.imagefile.header))
      self.head_dialog.configure(text_state='disabled')
    return
  def check_update(self):
    if self.imagefile:
      self.file_info.set_message('file_name',self.imagefile.fname)
      self.filename_entry.setentry(self.imagefile.fname)
      try:
        self.file_info.set_message('observed_time','%s %s' % (self.imagefile.header['LC-TIME'],\
          self.imagefile.header['LC-DATE']))
      except KeyError:
        self.file_info.set_message('observed_time','N/A')
      except Exception: pass
      self.file_info.set_message('current_time','%s %s' % (self.imagefile.local_time,self.imagefile.local_date))
    self.after_id=self.after(10,self.check_update)
    return
  def close_frame(self):
    self.stop_update()
    self.destroy()
    os.chdir(DIMM_DIR+'imageprocs/')
    return

#12345######################
REG_GUI_DICT={ 'height':'height',
               'intfluxhm':'int_flux_hm',
               'hmfluxbck':'reducd_flux',
               'xshape':'x_pixels',
               'xcenter':'x_center',
               'xwidth':'x_width',
               'absxcenter':'abs_x_center',
               'yshape':'y_pixels',
               'ycenter':'y_center',
               'ywidth':'y_width',
               'absycenter':'abs_y_center'}

class RegionFrame(fg.FrameGUI):
  def __init__(self,root=None,frame_name='Peak Processing Results',num=1,col=0,row=0,colspan=1,rowspan=1):
    if not root: self.root=Tk()
    elif hasattr(root,'interior'): self.root=root.interior()
    else: self.root=root
    self._mesBarList=[['height','Height',15,(0,0,1,1,'nse')],\
                      ['intfluxhm','Int Half Max',15,(0,1,1,1,'nsew')],\
                      ['hmfluxbck','Flux-Backg',15,(0,2,1,1,'nsew')],\
                      ['xshape','X Pixels',15,(1,0,1,1,'nsew')],\
                      ['xcenter','X Center',15,(1,1,1,1,'nsew')],\
                      ['xwidth','X Width',15,(1,2,1,1,'nsew')],\
                      ['absxcenter','Abs X Center',15,(1,3,1,1,'nsew')],\
                      ['yshape','Y Pixels',15,(2,0,1,1,'nsew')],\
                      ['ycenter','Y Center',15,(2,1,1,1,'nsew')],\
                      ['ywidth','Y Width',15,(2,2,1,1,'nsew')],\
                      ['absycenter','Abs Y Center',15,(2,3,1,1,'nsew')]]
    fg.FrameGUI.__init__(self,root=self.root,name=frame_name+str(num),col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    return
  def set(self,name,value):
    if type(value)!=str:
      self.__dict__[name].message('state','%10.3f' % value)
    else:
      self.__dict__[name].message('state','%s' % value)
    return
  def fill_values(self,region_info):
    ''' <fill_values>
        region_info is an instance of the class <image_proc_file.RegionData>
    '''
    for each in REG_GUI_DICT.keys():
      self.set(each,region_info.__dict__[REG_GUI_DICT[each]])
    return
  def close_frame(self):
    #self.stop_update()
    self.destroy()
    return

#
#Example of using the above, with Opening test_m47_5.0sec.fits image file
#
#>>> mmprc=nipt.ImageProcess()
#>>> reload(pgf);mymm=pgf.ImageFrame(row=0,col=1);mmreg=pgf.RegionFrame(root=mymm.interior(),row=10,colspan=4)
#<module 'proc_gui_frames' from 'proc_gui_frames.pyc'>
#>>> mmprc(mymm.imagefile,'peaks')
#[10, array([[ 271.86532345,  160.97602323],
#       [ 383.89769254,  368.45573909],
#       [ 375.46077548,  250.81579713],
#       [ 660.88226546,  427.92360622],
#       [ 403.86261882,   91.45358046],
#       [ 515.14747288,  243.65494663],
#       [ 594.54051405,  374.45663987],
#       [ 288.94480578,  386.50750903],
#       [ 672.61582605,  489.13841213],
#       [ 469.003615  ,  424.        ]])]
#>>> mmreg.fill_values(mmprc.peaks[0])
#
#12345######################

PROC_ARGS_LIST=['entry_ind1','entry_ind2','entry_center','entry_coords','entry_north_deg','entry_east_dir']

class ProcessingFrame(fg.FrameGUI):
  def __init__(self,root=None,frame_name='Processing Frame',col=0,row=0,colspan=1,rowspan=1):
    if not root: self.root=Tk()
    elif hasattr(root,'interior'): self.root=root.interior()
    else: self.root=root
    self.imageproc=imthread.ImageProcess()
    self.imagefile=self.imageproc.image
    self._mesFrameList=[['proc_variables','Process Variables',['Process Type','Number of Objects',\
                         'Background','Background STD'],(0,2,3,2,'nsew')],\
                        ['message_peaks0','Last Peak 1',['index','x_y','x_y_width','height'],(11,5,2,4,'nsew')]]
    self._mesBarList=[['proc_message','Process Message',30,(0,0,6,1,'nsew')],\
                      ['image_name','Image Name',30,(0,1,6,1,'nsew')]]
    self._buttonList=[['process_button','Process','(lambda s=self: s.process_image())',(1,7,1,1,'nsew')],\
                      ['reset_button','Reset','(lambda s=self: s.reset_all())',(0,7,1,1,'nsew')]]
    self._butFrameList=[]
    self._optionList=[['proc_options','Process Options',self.imageproc.func_type,imthread.PROCESS_LIST,
      self.set_proc_option,(2,7,3,1,'nsew')]]
    self._entryList=[]
    self._entryframeList=[]
    self._checkList=[]
    self._emessList=[['emess_settings','Settings',[['entry_sigma','Sigma',''],\
                     ['entry_median_box_size','Box Size',''],['entry_threshold','Threshold',''],\
                     ['entry_backgnd','Background','']],(0,4,3,2,'nsew')],\
                     ['emess_args','Parameters',[['entry_ind1','Index 1',''],\
                     ['entry_ind2','Index 2',''],['entry_center','Center',''],\
                     ['entry_coords','Coordinates',''],['entry_north_deg','North Angle',''],\
                     ['entry_east_dir','East Orientation',''],\
                     ],(0,8,3,2,'nsew')]]
    self._indicatorList=[['proc_flags','Process Indicators',['run_proc_event','process_done'],(0,10,3,2,'nsew')]]
    self._listboxList=[['return_listbox','Function Return',(0,12,3,6,'nsew')]]
    fg.FrameGUI.__init__(self,root=self.root,name=frame_name,col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    self.lastreturn=None
    self.args_params=[0,1,False,(-1,-1),0.0,'cw']
    self.after_id=None
    self.confg_guis()
    self.check_update()
    return
  def confg_guis(self):
    self.emess_settings.set_entry('entry_sigma',self.imageproc.sigma)
    self.emess_settings.set_entry('entry_median_box_size',self.imageproc.median_box_size)
    self.emess_settings.set_entry('entry_threshold',self.imageproc.threshold)
    self.emess_settings.set_entry('entry_backgnd',self.imageproc.background)
    self.emess_settings.entry_sigmaC.configure(command=self.set_parameters)
    self.emess_settings.entry_median_box_sizeC.configure(command=self.set_parameters)
    self.emess_settings.entry_thresholdC.configure(command=self.set_parameters)
    self.emess_settings.entry_backgndC.configure(command=self.set_parameters)
    for i in range(len(PROC_ARGS_LIST)):
      self.emess_args.__dict__[PROC_ARGS_LIST[i]+'C'].configure(command=self.set_argsparams)
      self.emess_args.set_entry(PROC_ARGS_LIST[i],str(self.args_params[i]))
      self.emess_args.set_labels(PROC_ARGS_LIST[i],str(self.args_params[i]))
    self.return_listbox.listbox.configure(height=5)
    return
  def reset_all(self):
    self.imageproc.reset()
    self.args_params=[0,1,False,(-1,-1),0.0,'cw']
    for i in range(len(PROC_ARGS_LIST)):
      self.emess_args.__dict__[PROC_ARGS_LIST[i]+'C'].configure(command=self.set_argsparams)
      self.emess_args.set_entry(PROC_ARGS_LIST[i],str(self.args_params[i]))
      self.emess_args.set_labels(PROC_ARGS_LIST[i],str(self.args_params[i]))
    self.emess_settings.set_entry('entry_sigma',self.imageproc.sigma)
    self.emess_settings.set_entry('entry_median_box_size',self.imageproc.median_box_size)
    self.emess_settings.set_entry('entry_threshold',self.imageproc.threshold)
    self.emess_settings.set_entry('entry_backgnd',self.imageproc.background)
    return
  def set_proc_option(self,tag):
    proc_type=self.proc_options.getcurselection()
    self.imageproc.func_type=proc_type
    return
  def set_parameters(self):
    sigma=float(self.emess_settings.entry_sigmaC.getvalue())
    medianboxsize=float(self.emess_settings.entry_median_box_sizeC.getvalue())
    threshold=float(self.emess_settings.entry_thresholdC.getvalue())
    background=float(self.emess_settings.entry_backgndC.getvalue())
    self.imageproc.config(sigma=sigma,median_box_size=medianboxsize,threshold=threshold,background=background)
    return
  def set_argsparams(self):
    templist=[]
    for i in range(len(PROC_ARGS_LIST)):
      value=self.emess_args.get_entry(PROC_ARGS_LIST[i])
      self.emess_args.set_labels(PROC_ARGS_LIST[i],value)
      if i==2:
        if value=='True' or value=='1': templist.append(True)
        elif value=='False' or value=='0': templist.append(False)
        else: templist.append(True)
      elif i==3:
        try: x,y=int(value.split(',')[0].replace('(','')),int(value.split(',')[1].replace(')',''))
        except Exception: x,y=-1,-1
        templist.append((x,y))
      elif i==4: templist.append(float(value))
      elif i==5: templist.append(str(value))
      else: templist.append(int(value))
    self.args_params=templist
    return 
  def set_image(self,image_file):
    self.imageproc.image=image_file
    self.imagefile=self.imageproc.image
    return
  def process_image(self):
    ind1,ind2,center,coords,ndeg,edir=self.args_params
    proc_type=self.proc_options.getcurselection()
    self.imageproc(self.imagefile,proc_type,ind1=ind1,ind2=ind2,\
      center=center,coords=coords,\
      north_deg=ndeg,east_dir=edir)
    return
  def check_update(self):
    if str(self.lastreturn)!=str(self.imageproc.func_return):
      self.lastreturn=str(self.imageproc.func_return)
      self.return_listbox.listbox.delete(1.0,index2=END)
      self.return_listbox.listbox.insert(1.0,str(self.lastreturn))
    self.proc_message.message('state','%s' % self.imageproc.message)
    if self.imagefile and self.imageproc.image:
      if hasattr(self.imagefile,'fname'):
        self.image_name.message('state','%s' % self.imageproc.image.fname)
    self.proc_flags.set_indicator('process_done',self.imageproc.process_done.isSet())
    self.proc_flags.set_indicator('run_proc_event',self.imageproc.run_proc_event.isSet())
    self.emess_settings.set_labels(name='entry_sigma',text='%s' % self.imageproc.sigma)
    self.emess_settings.set_labels(name='entry_median_box_size',text='%s' % self.imageproc.median_box_size)
    self.emess_settings.set_labels(name='entry_threshold',text='%s' % self.imageproc.threshold)
    self.emess_settings.set_labels(name='entry_backgnd',text='%s' % self.imageproc.background)
    self.proc_variables.set_message('process_type',self.imageproc.func_type)
    self.proc_variables.set_message('number_of_objects',self.imageproc.num_objects)
    self.proc_variables.set_message('background',self.imageproc.background)
    self.proc_variables.set_message('background_std',self.imageproc.bgnd_std)
    #self.message_peaks0.set_message('index','%d' % self.imagefile.peaks[0][0])
    if hasattr(self.imagefile,'peaks'):
      if len(self.imagefile.peaks)>0:
        self.message_peaks0.set_message('x_y','(%7.3f,%7.3f)' % \
          (self.imagefile.peaks[0].abs_x_center,self.imagefile.peaks[0].abs_y_center))
        self.message_peaks0.set_message('x_y_width','(%7.3f,%7.3f)' % \
          (self.imagefile.peaks[0].x_width,self.imagefile.peaks[0].y_width))
        self.message_peaks0.set_message('height','%8.3f' % self.imagefile.peaks[0].height)
    self.after_id=self.after(10,self.check_update)
    return
  def close_frame(self):
    self.stop_update()
    self.destroy()
    return


class ProcessThreadFrame(fg.FrameGUI):
  def __init__(self,root=None,frame_name='Process Thread Frame',col=0,row=0,colspan=1,rowspan=1,\
    device_name='file'):
    if not root: self.root=Tk()
    elif hasattr(root,'interior'): self.root=root.interior()
    else: self.root=root
    self.imageproc=imthread.ProcessThread(device_name=device_name)
    self._mesFrameList=[]
    self._mesBarList=[]
    self._buttonList=[]
    self._butFrameList=[]
    self._optionList=[]
    self._entryList=[]
    self._entryframeList=[]
    self._checkList=[]
    self._emessList=[]
    self._indicatorList=[]
    self._listboxList=[]
    return

import region_proc_test as rpt

class TopProcGUI(fg.FrameGUI):
  def __init__(self,root=None,frame_name='Processing Frame',col=0,row=1,colspan=2,rowspan=4):
    if not root: self.root=Tk()
    elif hasattr(root,'interior'): self.root=root.interior()
    else: self.root=root
    self._mesFrameList=[]
    self._mesBarList=[]
    self._buttonList=[['open','Open Image','self.set_image',(0,0,1,1,'nsew')],
                      ['labels','Plot Labels','self.plot_labels',(0,1,1,1,'nsew')],
                      ['replot','Replot','self.replot',(0,2,1,1,'nsew')]]
    self._butFrameList=[]
    self._optionList=[]
    self._entryList=[]
    self._entryframeList=[]
    self._checkList=[]
    self._emessList=[]
    self._indicatorList=[]
    self._listboxList=[]
    fg.FrameGUI.__init__(self,root=self.root,name=frame_name,col=col,row=row,colspan=colspan,rowspan=rowspan)
    self.img_gui=ImageFrame(root=self.root,row=1,col=6,colspan=4,rowspan=4)
    self.prc_gui=ProcessingFrame(root=self.root,row=1,col=2,colspan=4,rowspan=4)
    self.xit=Button(self.root,text='Exit',font=fg.TEXT_FONT,width=6,padx=0,pady=0,command=self.stop_all)
    self.xit.grid(column=0,row=0,sticky='nw')
    self.check_update()
    return
  def set_image(self):
    self.img_gui.open_image()
#   if not self.prc_gui.imagefile: pass
    self.prc_gui.set_image(self.img_gui.imagefile)
    print self.img_gui.imagefile.fname,self.prc_gui.imagefile.fname
    return
  def plot_labels(self):
    rpt.label_peaks(self.img_gui._figure.splot,self.prc_gui.imagefile,color='Red')#,big=False)
    self.img_gui._figure.draw()
    return
  def replot(self):
    self.img_gui._figure.data_queue.put(self.img_gui.imagefile.data)
    return
  def plot_a_peak(self):
    ind1,ind2,center,coords,ndeg,edir=self.prc_gui.args_params
    rpt.plot_a_peak(self.prc_gui.imageproc,ind1)
    return
  def check_update(self):
    self.after_id=self.after(10,self.check_update)
    return
  def stop_all(self):
    self.prc_gui.stop_update()
    self.img_gui.close_frame()
    self.prc_gui.close_frame()
    self.stop_update()
    self.destroy()
    try: self.root.destroy()
    except Exception: pass
    return

def stop_progs():
  global root
# global root,img_gui
# img_gui.close_frame()
  root.destroy()
  sys.exit()
  return

def open_main(root):
  img_gui=ImageFrame(root=root,row=1,col=4,colspan=4,rowspan=4)
  prc_gui=ProcessingFrame(root=root,row=1,col=0,colspan=4,rowspan=4)
  xx=Button(root,text='Exit',font=fg.TEXT_FONT,width=6,padx=0,pady=0)
  xx.grid(column=0,row=0,sticky='nw')
  return img_gui,prc_gui

if __name__=='__main__':
  root=Tk()
  root.attributes('-fullscreen',False)
  root.protocol('WM_DELETE_WINDOW',stop_progs)
  all_gui=TopProcGUI(root=root,frame_name='Processing Frame',col=0,row=0,colspan=1,rowspan=1)
# img_gui=ImageFrame(root=root,row=1,col=4,colspan=4,rowspan=4)
# prc_gui=ProcessingFrame(root=root,row=1,col=0,colspan=4,rowspan=4)
# xx=Button(root,text='Exit',font=fg.TEXT_FONT,command=stop_progs,width=6,padx=0,pady=0)
# xx.grid(column=0,row=0,sticky='nw')
  root.mainloop()
