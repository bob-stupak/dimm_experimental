#! /usr/bin/env python image_proc_gui.py

import resource

import sys
sys.path.append('..')

from numpy import *

import time
import os

from Tkinter import *
import Pmw as pmw
import guis.notebook as ntbk
import guis.frame_gui as fg
import guis.imagecanvasgui as icanv

import image_proc_thread as imthread
from camera import camera_thread,camera_prosilica,camera_sbig,camera_supercircuits
from image_proc_thread import SIM_IMAGE_NAME,IMG_DIR

from common_parms import *
import test as tst

def mem():
  mem_space='Memory usage: %2.2f MB' % round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024.0/1024.0,1)
  return mem_space


#12345######################
class MeasureGui(fg.FrameGUI):
  def __init__(self,root=None,parent=None,col=0,row=0,colspan=1,rowspan=1):
    self.parent=parent
    if root:
      self.root=root
    else:
      self.root=self.parent.interior()
    self.meas_manager=self.parent.process_manager
    self._mesBarList=[\
                      ['proc_mang_results','Process Manager Results',50,(0,20,15,1,'nsew')],\
                      ['proc_mang_mess','Process Manager Message',50,(0,21,15,1,'nsew')]]
    self._mesFrameList=[\
                       ['message_seeing','Last Seeing',['eps_lg','eps_tg','eps_lz','eps_tz'],(10,0,2,5,'nsew')],\
                       ['message_seeing','Last Seeing',['eps_lg','eps_tg','eps_lz','eps_tz'],(11,0,2,5,'nsew')],\
                       ['message_center','Last Center',['cur_center','delta_vec','drtheta','direct'],(9,5,2,4,'nsew')],\
                       ['message_focus','Last Focus',['width_x','width_y','height'],(9,0,2,4,'nsew')],\
                       ['message_midpnt','Last Midpoint',['midpoint','delta_vec','drtheta','direct'],(9,9,2,4,'nsew')],\
                       ['message_peaks0','Last Peak 1',['index','x_y','x_y_width','height'],(11,5,2,4,'nsew')],\
                       ['message_peaks1','Last Peak 2',['index','x_y','x_y_width','height'],(11,9,2,4,'nsew')]]
    self._entryframeList=[['proc_parms1','Processing',['seeing_number','box_size','east_dir','north_deg',\
                           'center_flag','coords'],(2,0,4,6,'nsew')],\
                          ['proc_parms2','Processing',['sigma','median_box_size','threshold'],\
                          (2,6,4,6,'nsew')]]
    self._optionList=[]
    self._indicatorList=[['proc_flags','Process Flags',['Main Thread','results_stat'],(0,0,2,3,'nsew')]]
    self._buttonList=[
      ['take_seeing_button','Test Seeing Measure','(lambda s=self: s.take_seeing())',(0,3,2,1,'nsew')],\
      ['take_one_button','One Measure','(lambda s=self: s.take_image())',(0,4,2,1,'nsew')],\
      ['take_center_button','Center Measure','(lambda s=self: s.take_center())',(0,5,2,1,'nsew')],\
      ['take_focus_button','Focus Measure','(lambda s=self: s.take_focus())',(0,6,2,1,'nsew')],\
      ['take_peak_button','Box Peak','(lambda s=self: s.take_box_peak())',(0,7,2,1,'nsew')],\
      ['take_mdpnt_button','Box Midpoint','(lambda s=self: s.take_box_midpoint())',(0,8,2,1,'nsew')],\
      ['continuous_button','Continuous','(lambda s=self: s.continuous())',(0,9,2,1,'nsew')],\
      ['setparms_button','Set Parameters','(lambda slf=self: slf.set_manager_parameters())',(0,10,2,1,'nsew')],\
      ['reset_meas_button','Reset Measure','(lambda slf=self: slf.reset_measure)',(0,11,2,1,'nsew')]]
    self._checkList=[]
    fg.FrameGUI.__init__(self,root=self.root,name='Measurements',col=col,row=row,colspan=colspan,rowspan=rowspan)
    #blank1=fg.BlankSpace(root=self.interior(),col=0,row=0,colspan=1,rowspan=1)
    self.set_parms_entries()
    self.check_update()
    return
  def take_seeing(self):
    self.meas_manager('seeing')
    return
  def take_image(self):
    self.meas_manager('image')
    return
  def take_center(self):
    self.meas_manager('centering')
    return
  def take_focus(self):
    self.meas_manager('focusing')
    return
  def take_box_peak(self):
    self.meas_manager('boxregion',center_type='peaks')
    return
  def take_box_midpoint(self):
    self.meas_manager('boxregion',center_type='midpoint')
    return
  def continuous(self):
    if self.meas_manager.process_thread.device.auto_sequence_stat.isSet():
      self.continuous_button.configure(bg='#d9d9d9')
      self.continuous_button.configure(text='Continuous')
    else:
      self.continuous_button.configure(bg='#efd0d0')
      self.continuous_button.configure(text='Stop')
    self.meas_manager.continuous()
    return
  def reset_measure(self):
    self.meas_manager.results_stat.set()
    self.meas_meanager.message='Measurment results bit reset'
    return
  def set_parms_entries(self):
    self.proc_parms1.seeing_number.set_entry(self.meas_manager.process_args['seeing_num'])
    self.proc_parms1.box_size.set_entry(self.meas_manager.process_args['box_size'])
    self.proc_parms1.east_dir.set_entry(self.meas_manager.process_args['east_dir'])
    self.proc_parms1.north_deg.set_entry(self.meas_manager.process_args['north_deg'])
    self.proc_parms1.center_flag.set_entry(str(self.meas_manager.process_args['center_flag']))
    self.proc_parms1.coords.set_entry(str(self.meas_manager.process_args['coords'][0])+','+\
      str(self.meas_manager.process_args['coords'][1]))
    self.proc_parms2.sigma.set_entry(self.meas_manager.process_args['sigma'])
    self.proc_parms2.median_box_size.set_entry(self.meas_manager.process_args['median_box_size'])
    self.proc_parms2.threshold.set_entry(self.meas_manager.process_args['threshold'])
    return
  def set_manager_parameters(self):
    self.meas_manager.process_args['seeing_num']=int(self.proc_parms1.seeing_number.get_entry())
    self.meas_manager.process_args['box_size']=int(self.proc_parms1.box_size.get_entry())
    self.meas_manager.process_args['east_dir']=self.proc_parms1.east_dir.get_entry()
    self.meas_manager.process_args['north_deg']=float(self.proc_parms1.north_deg.get_entry())
    cnt=self.proc_parms1.center_flag.get_entry()
    if cnt=='True' or cnt=='1' or cnt=='true': self.meas_manager.process_args['center_flag']=True
    else: self.meas_manager.process_args['center_flag']=False
    self.meas_manager.process_args['coords']=tuple([int(e) for e in self.proc_parms1.coords.get_entry().split(',')])
    self.meas_manager.process_args['sigma']=float(self.proc_parms2.sigma.get_entry())
    self.meas_manager.process_args['median_box_size']=int(self.proc_parms2.median_box_size.get_entry())
    self.meas_manager.process_args['threshold']=float(self.proc_parms2.threshold.get_entry())
    self.set_parms_entries()
    return
  def check_update(self):
    try:
      self.proc_flags.set_indicator('Main Thread',self.meas_manager.isAlive())
      self.proc_flags.set_indicator('results_stat',self.meas_manager.results_stat.isSet())
      self.proc_mang_mess.message('state','%s' % self.meas_manager.message)
      self.proc_mang_results.message('state','%r' % self.meas_manager.results)
      self.message_center.set_message('cur_center','(%7.2f,%7.2f)' % \
        (self.meas_manager.center[0][0],self.meas_manager.center[0][1]))
      self.message_center.set_message('delta_vec','(%7.2f,%7.2f,%7.2f)' % \
        (self.meas_manager.center[1][0],self.meas_manager.center[1][1],self.meas_manager.center[1][2]))
      self.message_center.set_message('drtheta','(%7.2f,%7.2f)' % \
        (self.meas_manager.center[2][0],self.meas_manager.center[2][1]))
      self.message_center.set_message('direct','%s' % self.meas_manager.center[3].capitalize())
      self.message_midpnt.set_message('midpoint','(%7.2f,%7.2f)' % \
        (self.meas_manager.midpoint[0][0],self.meas_manager.midpoint[0][1]))
      self.message_midpnt.set_message('delta_vec','(%7.2f,%7.2f,%7.2f)' % \
        (self.meas_manager.midpoint[1][0],self.meas_manager.midpoint[1][1],self.meas_manager.midpoint[1][2]))
      self.message_midpnt.set_message('drtheta','(%7.2f,%7.2f)' % \
        (self.meas_manager.midpoint[2][0],self.meas_manager.midpoint[2][1]))
      self.message_midpnt.set_message('direct','%s' % self.meas_manager.midpoint[3].capitalize())
      self.message_peaks0.set_message('index','%d' % self.meas_manager.peak_0[0])
      self.message_peaks0.set_message('x_y','(%7.3f,%7.3f)' % \
        (self.meas_manager.peak_0[1],self.meas_manager.peak_0[3]))
      self.message_peaks0.set_message('x_y_width','(%7.3f,%7.3f)' % \
        (self.meas_manager.peak_0[2],self.meas_manager.peak_0[4]))
      self.message_peaks0.set_message('height','%8.3f' % self.meas_manager.peak_0[5])
      self.message_peaks1.set_message('index','%d' % self.meas_manager.peak_1[0])
      self.message_peaks1.set_message('x_y','(%7.3f,%7.3f)' % \
        (self.meas_manager.peak_1[1],self.meas_manager.peak_1[3]))
      self.message_peaks1.set_message('x_y_width','(%7.3f,%7.3f)' % \
        (self.meas_manager.peak_1[2],self.meas_manager.peak_1[4]))
      self.message_peaks1.set_message('height','%8.3f' % self.meas_manager.peak_1[5])
      self.message_seeing.set_message('eps_lg','%8.3f' % self.meas_manager.seeing[0])
      self.message_seeing.set_message('eps_tg','%8.3f' % self.meas_manager.seeing[1])
      self.message_seeing.set_message('eps_lz','%8.3f' % self.meas_manager.seeing[2])
      self.message_seeing.set_message('eps_tz','%8.3f' % self.meas_manager.seeing[3])
      self.message_focus.set_message('width_x','%8.3f' % self.meas_manager.last_focus[0])
      self.message_focus.set_message('width_y','%8.3f' % self.meas_manager.last_focus[1])
      self.message_focus.set_message('height','%8.3f' % self.meas_manager.last_focus[2])
    except Exception as err:  pass
    self.after_id=self.after(10,self.check_update)
    return


#12345######################
class ProcessGui(fg.FrameGUI):
  def __init__(self,root=None,parent=None,col=0,row=0,colspan=1,rowspan=1):
    self.parent=parent
    if root:
      self.root=root
    else:
      self.root=self.parent.interior()
    self._mesBarList=[['proc_message','Process Message',50,(0,7,22,1,'nsew')]]
    self._mesFrameList=[['message_frame1','Process Messages',['num_measures','image_queue_qsize','image_count',\
                         'reject_count','accept_count','process_type'],(4,0,3,5,'nsew')],\
                        ['message_frame2','Data Messages',['num_objects',\
                        'len_peaks_array'],(10,0,3,5,'nsew')]]
    self._entryframeList=[['num_meas_entry','',['Num of Procs'],(7,1,3,1,'nsew')]]
    self._optionList=[['proc_options','Process Options','background',imthread.PROCESS_LIST,\
      self.set_process,(7,0,3,1,'nsew')]]
    self._indicatorList=[['proc_flags','Process Flags',['Main Thread','run_proc_event','process_done',\
      'processed_image_ready','measure_done'],(0,0,3,5,'nsew')]]
    self._buttonList=[\
      ['take_measure_button','Take Measurement','(lambda s=self: s.take_measurement())',(7,2,1,1,'nsew')],\
      ['stop_measure_button','Stop Measurement','(lambda s=self: s.stop_measurement())',(7,3,1,1,'nsew')],\
      ['reset_measure_button','Reset Counts','(lambda s=self: s.reset_measurement())',(7,4,1,1,'nsew')]]
    self._checkList=[['loggingStat','Logging','horizontal','radiobutton',['False','True'],\
                      self.set_logging,(0,6,3,1,'nsew')],\
                     ['saveimgStat','Save Images','horizontal','radiobutton',['False','True'],\
                      self.set_saving,(6,6,3,1,'nsew')]]
    fg.FrameGUI.__init__(self,root=self.root,name='Processing',col=col,row=row,colspan=colspan,rowspan=rowspan)
    #blank1=fg.BlankSpace(root=self.interior(),col=0,row=0,colspan=1,rowspan=1)
    self.num_meas_entry.num_of_procs.set_entry(str(self.parent.imageproc.num_measures))
    self.loggingStat.setvalue(str(self.parent.imageproc.logging_flag))
    self.saveimgStat.setvalue(str(self.parent.imageproc.save_img_flag))
    self.check_update()
    return
  def set_process(self,var):
    self.parent.imageproc.process_type=var
    return
  def check_process(self):
    proc_type=self.proc_options.getcurselection()
    if proc_type!=self.parent.imageproc.process_type:
      self.proc_options.setvalue(str(self.parent.imageproc.process_type))
    return
  def take_measurement(self):
    process=self.proc_options.getvalue()
    num=int(self.num_meas_entry.num_of_procs.get_entry())
    self.parent.imageproc(number=num,process=process,run=True)
    self.num_meas_entry.num_of_procs.set_entry(num)
    return
  def set_logging(self,*tag):
    logging=self.loggingStat.getcurselection()
    if logging=='True': self.parent.imageproc.logging_flag=True
    else: self.parent.imageproc.logging_flag=False
    return
  def set_saving(self,*tag):
    saving=self.saveimgStat.getcurselection()
    if saving=='True': self.parent.imageproc.save_img_flag=True
    else: self.parent.imageproc.save_img_flag=False
    return
  def stop_measurement(self):
    self.parent.imageproc.stop_measure()
    return
  def reset_measurement(self):
    self.parent.imageproc.reset_measure()
    self.parent.reset_process()
    return
  def check_update(self):
    try:
      self.proc_message.message('state','%s' % self.parent.imageproc.message)
      self.message_frame1.set_message('num_measures',self.parent.imageproc.num_measures)
      self.message_frame1.set_message('image_queue_qsize',self.parent.imageproc.image_queue.qsize())
      self.message_frame1.set_message('image_count',self.parent.imageproc.image_count)
      self.message_frame1.set_message('reject_count',self.parent.imageproc.reject_count)
      self.message_frame1.set_message('accept_count',self.parent.imageproc.accept_count)
      self.message_frame1.set_message('process_type',self.parent.imageproc.process_type)
      self.message_frame2.set_message('num_objects',self.parent.imageproc.process.num_objects)
      self.message_frame2.set_message('len_peaks_array',len(self.parent.imageproc.process.peaks))
      self.proc_flags.set_indicator('Main Thread',self.parent.imageproc.isAlive())
      self.proc_flags.set_indicator('run_proc_event',self.parent.imageproc.run_proc_event.isSet())
      self.proc_flags.set_indicator('process_done',self.parent.imageproc.process_done.isSet())
      self.proc_flags.set_indicator('processed_image_ready',self.parent.imageproc.processed_image_ready.isSet())
      self.proc_flags.set_indicator('measure_done',self.parent.imageproc.measure_done.isSet())
      self.check_process()
    except Exception as err:  pass
    self.after_id=self.after(10,self.check_update)
    return
#12345######################
class DeviceGui(fg.FrameGUI):
  def __init__(self,root=None,parent=None,num=1,col=0,row=0,colspan=1,rowspan=1):
    self.parent=parent
    if root:
      self.root=root
    else:
      self.root=self.parent.interior()
    self._optionList=[['device_select','Device',self.parent.device_name,CAMERA_LIST,\
                      self.parent.set_device,(4,0,3,1,'nsew')]]
    self._indicatorList=[['proc_flags','Process Flags',['Main Thread','take_exposure_stat','read_out_stat',\
      'new_data_ready_stat','auto_sequence_stat'],(0,0,3,5,'nsew')]]
    self._mesBarList=[['device_message','Device Message',50,(0,25,12,1,'nsew')]]
    self._mesFrameList=[['device_info','Device Information',['data_mean','data_std','region_width',\
                         'region_height','offset_x','offset_y','binning_x','binning_y'],(4,1,2,5,'nsew')],\
                        ['device_parms','Device Parameters',['exposure_count','data_queue_qsize','sequence_count'],\
                         (6,1,2,5,'nsew')],\
                        ['device_exps','Device Exposure',['exptime','auto_delay','seq_exp_list','gain'],\
                         (8,15,2,5,'nsew')],\
                        ['camera_info','Camera Information',['cam_maxh','cam_maxw','camera_height',\
                         'camera_width','binning_x','binning_y','offset_x','offset_y'],(9,1,2,5,'nsew')]]
    self._buttonList=[['boxButton','Set Region','(lambda slf=self: slf.set_region())',(0,15,2,1,'nsew')],\
                      ['binButton','Set Binning','(lambda slf=self: slf.set_binning())',(0,16,2,1,'nsew')],\
                      ['resetBoxButton','Reset Region','(lambda slf=self: slf.reset_region())',(0,17,2,1,'nsew')],\
                      ['boxPeakButton','Box Peak','(lambda slf=self: slf.box_peak())',(0,18,2,1,'nsew')],\
                      ['boxMidButton','Box Midpoint','(lambda slf=self: slf.box_midpoint())',(0,19,2,1,'nsew')],\
                      ['expSetButton','Set Exp Parms','(lambda slf=self: slf.set_dev_exposures())',(0,20,2,1,'nsew')]]
    self._entryframeList=[['region_entry','Region Info',['x width','y height','x offset','y offset',\
                           'binning_x','binning_y','box_size'],\
                           (3,15,2,10,'nsew')],\
                          ['exposure_entry','Exposure Info',['exptime','auto_delay','seq_exp_list',\
                           'sequence_total_number','gain'],(6,15,2,10,'nsew')]]
#   self._checkList=[['autoRunStat','Run Auto','horizontal','radiobutton',['Off','On'],\
#                     self.set_auto_sequence,(4,0,3,1,'nsew')]]
    fg.FrameGUI.__init__(self,root=self.root,name='Device Information',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    self.set_dev_entries()
    self.set_exp_entries()
    self.check_update()
    return
  def set_exp_entries(self):
    self.exposure_entry.exptime.set_entry(self.parent.imageproc.device.exptime)
    self.exposure_entry.auto_delay.set_entry(self.parent.imageproc.device.auto_delay)
    self.exposure_entry.seq_exp_list.set_entry(\
      str(self.parent.imageproc.device.seq_exp_list).replace(']','').replace('[',''))
    self.exposure_entry.sequence_total_number.set_entry(self.parent.imageproc.device.sequence_total_number)
    self.exposure_entry.gain.set_entry(self.parent.imageproc.device.gain)
    return
  def set_dev_exposures(self):
    self.parent.imageproc.device.exptime=float(self.exposure_entry.exptime.get_entry())
    self.parent.imageproc.device.auto_delay=float(self.exposure_entry.auto_delay.get_entry())
    self.parent.imageproc.device.sequence_total_number=float(self.exposure_entry.sequence_total_number.get_entry())
    self.parent.imageproc.device.gain=float(self.exposure_entry.gain.get_entry())
    xtimelist=self.exposure_entry.seq_exp_list.get_entry()
    self.parent.imageproc.device.seq_exp_list=[float(each) for each in xtimelist.split(',')]
    return
  def set_auto_sequence(self,tag):
    if self.parent.imageproc.device!=None and self.parent.imageproc.device!='file':
      if self.autoRunStat.getvalue()=='On':
        self.parent.imageproc.run_device_auto(onstat=True)
      else:
        self.parent.imageproc.run_device_auto(onstat=False)
    else: pass
    return
  def check_auto_sequence(self):
    if self.parent.imageproc.device!=None and self.parent.imageproc.device!='file':
      if self.parent.imageproc.device.auto_sequence_stat.isSet():
        self.autoRunStat.setvalue('On')
      else:
        self.autoRunStat.setvalue('Off')
    else: pass
    return
  def reset_region(self):
    self.parent.imageproc.device.set_binning()
    self.parent.imageproc.device.set_roi()
    self.set_dev_entries()
    self.device_message.component('label').configure(bg='#d9d9d9')
    return
  def set_dev_entries(self):
    self.region_entry.x_width.set_entry(self.parent.imageproc.device.width)
    self.region_entry.y_height.set_entry(self.parent.imageproc.device.height)
    self.region_entry.x_offset.set_entry(self.parent.imageproc.device.offset_x)
    self.region_entry.y_offset.set_entry(self.parent.imageproc.device.offset_y)
    self.region_entry.binning_x.set_entry(self.parent.imageproc.device.binning_x)
    self.region_entry.binning_y.set_entry(self.parent.imageproc.device.binning_y)
    box_size=self.region_entry.box_size.get_entry()
    if box_size: self.region_entry.box_size.set_entry(box_size)
    else: self.region_entry.box_size.set_entry(500)
    return
  def set_region(self):
    xrng=int(self.region_entry.x_width.get_entry())
    yrng=int(self.region_entry.y_height.get_entry())
    xoff=int(self.region_entry.x_offset.get_entry())
    yoff=int(self.region_entry.y_offset.get_entry())
    self.parent.imageproc.device.set_roi(h=yrng,w=xrng,offx=xoff,offy=yoff)
    self.set_dev_entries()
    return
  def set_binning(self):
    xbin=int(self.region_entry.binning_x.get_entry())
    ybin=int(self.region_entry.binning_y.get_entry())
    self.parent.imageproc.device.set_binning(hor=xbin,vert=ybin)
    self.set_dev_entries()
    return
  def box_peak(self):
    process=self.parent.process_manager
    process('boxregion',center_type='peaks')
    process.results_stat.clear()
    process.results_stat.wait()
    self.set_dev_entries()
    return
  def box_midpoint(self):
    process=self.parent.process_manager
    process('boxregion',center_type='midpoint')
    process.results_stat.clear()
    process.results_stat.wait()
    self.set_dev_entries()
    return
  def check_update(self):
    try:
      self.device_message.message('state','%s' % self.parent.imageproc.device.message)
      self.device_parms.set_message('exposure_count',self.parent.imageproc.device.exposure_count)
      self.device_parms.set_message('data_queue_qsize', self.parent.imageproc.device.data_queue.qsize())
      self.device_parms.set_message('sequence_count',self.parent.imageproc.device.sequence_count)
      self.device_exps.set_message('exptime',self.parent.imageproc.device.exptime)
      self.device_exps.set_message('auto_delay',self.parent.imageproc.device.auto_delay)
      self.device_exps.set_message('gain',self.parent.imageproc.device.gain)
      self.device_exps.set_message('seq_exp_list',\
        str(self.parent.imageproc.device.seq_exp_list).replace(']','').replace('[',''))
      self.device_info.set_message('region_height','%s' %self.parent.imageproc.device.height)
      self.device_info.set_message('region_width','%s' %self.parent.imageproc.device.width)
      self.device_info.set_message('binning_x','%s' %self.parent.imageproc.device.binning_x)
      self.device_info.set_message('binning_y','%s' %self.parent.imageproc.device.binning_y)
      self.device_info.set_message('offset_x','%s' %self.parent.imageproc.device.offset_x)
      self.device_info.set_message('offset_y','%s' %self.parent.imageproc.device.offset_y)
      self.device_info.set_message('data_mean','%10.5f' % self.parent.imageproc.device.data.mean())
      self.device_info.set_message('data_std','%10.5f' % self.parent.imageproc.device.data.std())
      if hasattr(self.parent.imageproc.device,'camera'):
        self.camera_info.set_message('cam_maxh','%s' %self.parent.imageproc.device.camera.HeightMax)
        self.camera_info.set_message('cam_maxw','%s' %self.parent.imageproc.device.camera.WidthMax)
        self.camera_info.set_message('camera_height','%s' %self.parent.imageproc.device.camera.Height)
        self.camera_info.set_message('camera_width','%s' %self.parent.imageproc.device.camera.Width)
        self.camera_info.set_message('binning_x','%s' %self.parent.imageproc.device.camera.BinningHorizontal)
        self.camera_info.set_message('binning_y','%s' %self.parent.imageproc.device.camera.BinningVertical)
        self.camera_info.set_message('offset_x','%s' %self.parent.imageproc.device.camera.OffsetX)
        self.camera_info.set_message('offset_y','%s' %self.parent.imageproc.device.camera.OffsetY)
      self.proc_flags.set_indicator('Main Thread',self.parent.imageproc.device.isAlive())
      self.proc_flags.set_indicator('take_exposure_stat',self.parent.imageproc.device.take_exposure_stat.isSet())
      self.proc_flags.set_indicator('read_out_stat',self.parent.imageproc.device.read_out_stat.isSet())
      self.proc_flags.set_indicator('new_data_ready_stat',self.parent.imageproc.device.new_data_ready_stat.isSet())
      self.proc_flags.set_indicator('auto_sequence_stat',self.parent.imageproc.device.auto_sequence_stat.isSet())
    except Exception as err:  pass
    self.after_id=self.after(10,self.check_update)
    return

class ImageProcGUI(fg.FrameGUI):
  def __init__(self,root=None,parent=None,col=0,row=1,colspan=1,rowspan=1,proc_thread=None,device_name='file'):
    self.parent=parent
    self.device_name=device_name
    self.fileformat='fits'
    self.filename='testimage.'+self.fileformat
    self._mesBarList=[['figure_number','Plot Number',50,(2,22,5,1,'nsew')],\
                      ['figure_data_queue_size','Plot Queue Size',50,(2,23,5,1,'nsew')],\
                      ['memory_size','Memory Size',50,(2,24,5,1,'nsew')]]
    self._buttonList=[
      ['test_sequence','Test Sequence','(lambda s=self: s.testsequence())',(4,20,1,1,'nsew')],\
      ['clr_plt_queue','Clear Plot Queue','(lambda s=self: s.clear_plot_queue())',(3,20,1,1,'nsew')]]
    self._indicatorList=[['proc_flags','Plotting Flags',['plotq_empty','plot_ready'],(0,20,2,7,'nsew')]]
#   self._indicatorList=[['proc_flags','Plotting Flags',['plotq_empty','plot_ready'],(0,0,8,1,'nw')]]
    #self._entryList=[[]]
    #self._optionList=[[]]
    #self._checkList=[[]]
    #self._listboxList=[[]]
    fg.FrameGUI.__init__(self,root=root,name='Image Processing Items',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    self.notebook=ntbk.AppNoteBook(self.interior())
    self.notebook.grid(row=2,column=0,columnspan=8,rowspan=3,sticky='nsew')
    self.notebook.component('hull').configure(width=1100,height=600)
    if self.parent==None:
      self._figure=icanv.ImageCanvas(root=root,col=col+colspan+1,row=row+rowspan-1)
      self.process_manager=imthread.Measurement_thread(device_name=device_name)
    else:
      self._figure=self.parent._figure
      self.process_manager=proc_thread #self.parent.thread_manager.__dict__[proc_thread]
    self.imageproc=self.process_manager.process_thread
    self.measure_gui=MeasureGui(root=self.notebook.page1,parent=self,col=0,row=2,colspan=6,rowspan=1)
    self.process_gui=ProcessGui(root=self.notebook.page2,parent=self,col=0,row=5,colspan=6,rowspan=1)
    self.device_gui=DeviceGui(root=self.notebook.page3,parent=self,col=0,row=10,colspan=6,rowspan=1)
    self.imgcount=0
    self.camcount=0
    self.check_update()
    return
  def set_device(self,var):
    self.device_name=var
    self.imageproc.set_device(dev_name=var)
#   if self.imageproc.device_name!='file':
#     self.device_gui.take_new.configure(state='normal')
#     self.device_gui.autoRunStat.component('On').configure(state='normal')
#     self.device_gui.autoRunStat.component('Off').configure(state='normal')
#   else:
#     self.device_gui.take_new.configure(state='disabled')
#     self.device_gui.autoRunStat.component('On').configure(state='disabled')
#     self.device_gui.autoRunStat.component('Off').configure(state='disabled')
#   if self.device_name=='GT1290' or self.device_name=='GX2750':
#     self.prosilica_frame=ProsilicaFrame(parent=self,col=0,row=20,colspan=6,rowspan=1)
#   else: pass
    self.reset_process()
    return
  def reset_process(self):
    self.imageproc.reset_measure()
    self.process_gui.num_meas_entry.num_of_procs.set_entry(str(self.imageproc.num_measures))
    self.device_gui.set_dev_entries()
#   try:
    self.imageproc.device.exposure_count=0
    self._figure.plot_count=0
#   except Exception: pass
    #self._figure.clf()
    return
  def testsequence(self):
    tst.tcm(self.process_manager.process_thread,bnum=10,pnum=100,sleeptime=1.0)
    return
  def clear_plot_queue(self):
    self._figure.clear_queue()
    self.plot_ready_flag=True
    return
  def stopAll(self):
    self._figure.destroy()
    self.process_gui.stop_update()
    self.measure_gui.stop_update()
#   self.device_gui.stop_update()
    self.stop_update()
    self.process_manager.stop()
    #self.imageproc.stop()
    try:
      self.device.close()
    except Exception: pass
    self.destroy()
    return
  def check_update(self):
    if self.imageproc.num_measures==1 and not self.imageproc.image_queue.empty():
      image=self.imageproc.image_queue.get()
      self._figure.data_queue.put(image)
    elif self.imageproc.image_count!=self.imageproc.num_measures and not self.imageproc.image_queue.empty():
      image=self.imageproc.image_queue.get()
      self._figure.data_queue.put(image)
    else: pass
    if self.imageproc.num_measures==self.imageproc.image_count:
      self.imageproc.image_queue.queue.clear()
    self.figure_number.message('state','%d' % self._figure.plot_count)
    self.figure_data_queue_size.message('state','%d' % self._figure.data_queue.qsize())
    self.memory_size.message('state','%s' % mem())
    self.proc_flags.set_indicator('plotq_empty',self._figure.data_queue.empty())
    self.proc_flags.set_indicator('plot_ready',self._figure.plot_ready_flag)
    self.after_id=self.after(5,self.check_update)
    return

def stopProgs():
  global root,progStat,ggui
  ggui.stopAll()
# progStat=False
  imthread.progStat=False
  print 'Killing root GUI'
  root.destroy()
  print 'Sucessfully exited'
  sys.exit()
  return

if __name__=='__main__':
  global root,ggui#,pause_read
  progStat=True
  try:
    mindex=sys.argv.index('-cname')+1
    cname=sys.argv[mindex]
  except Exception:
    cname='Simulation'
  root=Tk()
  root.attributes('-fullscreen',False)
  pmw.initialise(root,useTkOptionDb=True)
  root.protocol('WM_DELETE_WINDOW',stopProgs)
  xx=Button(root,text='Exit',font=fg.TEXT_FONT,command=stopProgs,\
    width=6,padx=0,pady=0)
  xx.grid(column=0,row=0,sticky='nw')
  fgui=fg.FrameGUI(root=root,name='Testing',col=0,row=1,colspan=4,rowspan=2)
  ggui=ImageProcGUI(root=fgui.interior(),device_name=cname)
  root.mainloop()

