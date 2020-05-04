#! /usr/bin/env python image_proc_thread.py
#
#
'''
  <image_proc_thread.py>
  Version 4
  Date 18 April 2018

  Takes all images from the finder and seeing cameras for processing.  This module includes
  the processing, processing thread, and measurement thread classes.
  Version 4 separates the previously called PROCESS_ARGS_DICT module variable into CAMERA_PROC_DICT and
  FINDER_PROC_DICT.  Added '#' for all non-data comments for easier post-processing parsing of the log file.
  Also, added device_name into the <logfile_name> variable so as to get two separate log files for both processing
  methods.
'''
import sys
sys.path.append('..')

from numpy import *
from pylab import imsave
import threading
import Queue
import time,datetime
import os
import os.path
import platform
import imp
import pyfits
import scipy
import scipy.ndimage as ndimage
import scipy.ndimage.filters as filters
from scipy.ndimage.interpolation import shift
from scipy.optimize import leastsq as leastsq

import image_test_code 
import image_proc_file as imgfile
from camera import camera_thread,camera_prosilica,camera_sbig,camera_supercircuits
from common_parms import *

progStat=True

PROCESS_LIST=['background','pix2peaks','peaks','midpoint','fwhm']
MEASURE_LIST=['seeing','image','centering','boxregion','focusing','testing']

class ImageProcess(object):
  def __init__(self,*proc_events):
    if len(proc_events)==0:
      self.run_proc_event=threading.Event()
      self.run_proc_event.set()
      self.process_done=threading.Event()
      self.process_done.clear()
    else:
      self.run_proc_event=proc_events[0]
      self.process_done=proc_events[1]
    self.message=''
    self.func_type='background'
    self.func_return=None
    self.image=None
    self.data=zeros((1,1))  #Just some junk for initializing
    self.sigma=1.5
    '''@ivar: is the number of sigmas about the noise defining a background threshold'''
    self.median_box_size=5
    '''@ivar: is the box size of the median filter used to discriminate hot pixels'''
    self.threshold=0.0
    self.num_objects=0
    '''@ivar: is the number of flagged target regions in the image '''
    self.labelled_image=None
    '''@ivar: is the labelled image of flagged target regions in the image '''
    self.masked_data=None
    '''@ivar: is the masked data of original the image '''
    self.centers=None
    '''@ivar: are the centers since image data is reversed x,y '''
    self.peaks=[]
    '''@ivar: is a list of raw pixel data for each of the labeled regions '''
    self.background=0.0
    '''@ivar: is mean of the data for the un-labeled region '''
    self.bgnd_std=0.0
    '''@ivar: is standard deviation of the data for the un-labeled region '''
    return
  def __repr__(self):
    ss='<ImageProcess> class'
    ss='%s\n\n' % (ss)
    ss='%sLast Process Type: %s\n' % (ss,self.func_type)
    ss='%sLast Function Return: %r\n' % (ss,self.func_return)
    ss='%s\n' % (ss)
    ss='%sBackground: %10.5f\n' % (ss,self.background)
    ss='%sBackground STD: %10.5f\n' % (ss,self.bgnd_std)
    ss='%sThreshold: %10.5f\n' % (ss,self.threshold)
    ss='%sSigma: %7.4f\n' % (ss,self.sigma)
    ss='%sMedian Box Size: %d\n' % (ss,self.median_box_size)
    ss='%sNumber of Objects: %d\n' % (ss,self.num_objects)
    return ss
  def __call__(self,image,process,*args,**kwargs):
    self.func_type=process
    if not all(self.data==image.data): 
      self.reset()
      self.image=image
      self.data=image.data
    if hasattr(self,'find_'+process):
      proc_method=self.__getattribute__('find_'+process)
      if callable(proc_method):
        proc_method(*args,**kwargs)
    else:
      raise RuntimeError('Unexpected command "{}"; not found'.format(process))
    return self.func_return
  def config(self,**kwargs):
    for each in kwargs.keys():
      if hasattr(self,each):
        self.__dict__[each]=kwargs[each]
    return 
  def reset(self):
    self.image=None
    self.data=zeros((1,1))
    self.sigma=1.5
    self.median_box_size=5
    self.threshold=0.0
    self.num_objects=0
    self.labelled_image=None
    self.masked_data=None
    self.centers=None
    self.peaks=[]
    self.background=0.0
    self.bgnd_std=0.0
    self.func_return=[]
    return
  def _decorator(process):
    def proc_wrapper(self,*args,**kwargs):
      self.process_done.clear()
      self.message='Process started'
      process(self,*args,**kwargs)
      self.message='Process completed'
      self.process_done.set()
    return proc_wrapper
  @_decorator
  def find_pix2peaks(self,ind1=0,ind2=1,center_flag=False,coords=(-1,-1),north_deg=0.0,east_dir='cw',**kwargs):
    '''<find_pix2peaks>
       used to calculate the distances from one peak center to either another peak at <ind2>,
       the center of the image, or at some coordinate in the image plane.

       returns the indices of the peaks(or -1 for center or coords), dx, dy, ds in pixels
    '''
    if self.peaks==[]: self.find_peaks()
    coords=array(coords)
    if len(self.peaks)>0:
      xy1_center=array([self.peaks[ind1].abs_x_center,self.peaks[ind1].abs_y_center])
      if center_flag or not all(coords==-1):
        #if coords or center is being used for the calcuation
        ind2=-1
        if center_flag:
          xy2_center=array([self.data.shape[1]/2,self.data.shape[0]/2])
        else:
          #check to make sure coords are within the image size
          xy2_center=where(coords>=array(self.data.shape),array(self.data.shape),coords)
      elif (not center_flag or all(coords==-1)) and len(self.peaks)>=ind2:
        xy2_center=array([self.peaks[ind2].abs_x_center,self.peaks[ind2].abs_y_center])
      else:
        ind2=-1
        xy2_center=array([self.data.shape[1]/2,self.data.shape[0]/2])
#     else:
#       #use the two peaks found from <self.find_peaks> method
#       xy2_center=array([self.peaks[ind2].abs_x_center,self.peaks[ind2].abs_y_center])
      dx,dy=xy2_center-xy1_center
      ds_vect=array([dx,dy])
      ds=sqrt(dot((dx,dy),(dx,dy)))
      drt=array([sqrt(dot(ds_vect,ds_vect)),rad2deg(arctan2(dy,dx))])
      # Note: d(theta) in drt is ALWAYS the angle from the positive X and Y directions of the image
      #The following will define the north/east directions orientations, the card_dir supplies the cardinal direction
      # Note North defined in 180.0 will get it incorrect, use -180.0 deg instead
      if east_dir=='cw': east=north_deg-90.0
      else: east=north_deg+90.0
      n_range=array([north_deg-90.0,north_deg+90.])
      e_range=array([east-90.0,east+90.0])
      #<card_dir> is the cardinal direction given NORTH and EAST
      if n_range[0]<drt[1] and drt[1]<n_range[1]: card_dir='n'
      else: card_dir='s'
      if e_range[0]<drt[1] and drt[1]<e_range[1]: card_dir+='e'
      else: card_dir+='w'
      self.func_return=[ind1,ind2,dx,dy,ds,xy1_center,xy2_center,ds_vect,drt,card_dir]
    else:
      self.func_return=[-1,-1,0.0,0.0,0.0,array([0.0,0.0]),array([0.0,0.0]),array([0.0,0.0]),array([0.0,0.0]),'n']
    return 
  @_decorator
  def find_background(self,**kwargs):
    '''<find_background> uses the scipy.ndimage label, median, and standard_deviation to define 
       the background and background std given a threshold that is defined by the data's 
       data.mean()+self.sigma*data.std()
       It also defines the self.masked_data, self.labelled_image, and self.num_objects variables
    '''
    data=copy(self.data)
    self.masked_data=copy(data)
    self.threshold=data.mean()+self.sigma*data.std()
    self.masked_data[self.masked_data<self.threshold]=0
    #dmedian=filters.median_filter(self.masked_data,self.median_box_size)
    ##dmedian=filters.median_filter(self.masked_data,footprint=ndimage.generate_binary_structure(2,1))
    #labeled_image,self.num_objects=ndimage.label(dmedian)
    self.labelled_image,self.num_objects=ndimage.label(self.masked_data)
    #self.background=ndimage.mean(data,labels=labeled_image,index=[0])[0]
    self.background=ndimage.median(data,labels=self.labelled_image,index=[0])[0]
    self.bgnd_std=ndimage.standard_deviation(data,labels=self.labelled_image,index=[0])[0]
    self.image.calc_background=self.background
    self.image.calc_bckgrnd_std=self.bgnd_std
    self.func_return=[self.background,self.bgnd_std]
    return
  @_decorator
  def find_peaks(self,**kwargs):
    '''<find_peaks> computes the background, defines the self.masked_data, self.labelled_image, 
       and self.num_objects variables, if this hasn't been done already.  Then, 
       uses the scipy.ndimage.filters.median_filter and scipy.ndimage label, find_objects, and center_of_mass
       to define regions of interest around all of the peaks.  For each peak, the self.peaks list is
       appended with a Class imgfile.RegionData.  This class contains the center and height information for
       each of the found peak objects.  The peaks list is then sorted by 'brightest' peak and the 
       self.centers array is defined which contains the absolute centers for all of the peaks in the image.
    '''
    self.centers=None
    self.peaks=[]
    data=copy(self.data)
    self.masked_data=copy(data)
    if self.background==0.0: self.find_background()
    else: pass
    ####
    ##  For two objects that are close and have a high background in between them, the <self.background> variable
    ##  needs to be raised in order to separate them as different peaks.  The <self.threshold> variable could
    ##  be used in the future to achieve this and should be used.  This has more influence than both the 
    ##  <self.median_box_size> and the <self.sigma> variables.
    ####
    #self.masked_data[self.masked_data<=self.background]=0
    self.masked_data[self.masked_data<=self.background*self.sigma]=0
    #self.masked_data[self.masked_data<=self.threshold]=0
    ###########
    seterr(all='ignore') ##########  NOT ELIGANT ##################
    dmedian=filters.median_filter(self.masked_data,self.median_box_size)
    #dmedian=filters.median_filter(self.masked_data,footprint=array([[0,1,0],[1,1,1],[0,1,0]]))
    self.labelled_image,self.num_objects=ndimage.label(dmedian)
    #####
    #slices=ndimage.find_objects(self.labelled_image)
    slices=ndimage.find_objects(self.labelled_image,max_label=50)
    centroids=ndimage.center_of_mass(self.masked_data,self.labelled_image,\
      arange(1,self.num_objects+1))
    #The following is a check to see if there are any infinite numbers in the centroids tuple
    # It will remove them in both the centroids and slices list along with subtracting from num_objects
    # If NaN is in the centroids array it would kill the processing thread.  NaN should be a rare event.
    # Added in on Thurs 22 June 2017
    nan_test=unique(where([isnan(each) for each in centroids])[0])
    if nan_test.size>0:
      for i in nan_test[::-1]:
        slices.pop(i)
        centroids.pop(i)
        self.num_objects-=1
    for i in range(self.num_objects):
      box_slices=slices[i]
      x1,x2=box_slices[0].start,box_slices[0].stop
      y1,y2=box_slices[1].start,box_slices[1].stop
      self.peaks.append(imgfile.RegionData(self.data[x1:x2,y1:y2],\
        box_slices,centroids[i],self.background))
#   brightestIndex=argsort(array([each.height for each in self.peaks]))[::-1]
    brightestIndex=argsort(array([each.int_flux_hm for each in self.peaks]))[::-1]
    ###########
    seterr(all='print') ##########  NOT ELIGANT ##################
    self.peaks=[self.peaks[i] for i in brightestIndex]
    self.centers=array([(each.abs_x_center,each.abs_y_center) for each in self.peaks])
    self.image.peaks=self.peaks
    self.image.centers=self.centers
    self.image.num_peaks=len(self.image.peaks)
    self.func_return=[self.num_objects,self.centers]
    #This does work for assigning these attributes to the image
    #self.image.num_objects,self.image.centers,self.image.peaks=self.num_objects,self.centers,self.peaks
    return
  @_decorator
  def find_midpoint(self,ind1=0,ind2=1,**kwargs):
    '''<find_midpoint> 
       A method used to find the midpoint, in pixels, between two peaks, indexed <ind1>,<ind2>.  This method can be
       used to box a region in an image.
    '''
    if self.peaks==[]: self.find_peaks()
    xy1_center=array([self.peaks[ind1].abs_x_center,self.peaks[ind1].abs_y_center])
    xy2_center=array([self.peaks[ind2].abs_x_center,self.peaks[ind2].abs_y_center])
    dx,dy=(xy2_center-xy1_center)/2.0
    ds_vect=array([dx,dy])
    self.func_return=xy1_center+ds_vect
    return 
  @_decorator
  def find_fwhm(self,ind1=0,**kwargs):
    '''<find_fwhm> 
       A method used to find the full width half max, in pixels, of a peak, index <ind>.  This method can be
       used to find the focus of an image.
    '''
    if self.peaks==[]: self.find_peaks()
    peak=self.peaks[ind1]
    self.func_return=array([peak.x_width,peak.y_width,peak.height])
    return
#
# def find_newfunction(self,*args,**kwargs):
#   '''Use this template to create a new process, method
#   '''
#   ...do_something....
#   self.func_return=[]   #Place to put the return of the method
#   return
#
class ProcessThread(threading.Thread):
  def __init__(self,name='image_proc_thread',device=None,device_name='file',sleeptime=IMG_PRC_THREADTIME,\
      log=False,prnt=False,save_img=False):
    threading.Thread.__init__(self)
    self.setName(name)
    self.local_date,self.local_time=None,None #time.strftime(DTIME_FORMAT).split(',')
    '''@ivar: The initial local date and time set by the local computer.
    '''
    self.get_time()
    # The following are a set of events to be flagged for processing images
    self.prog_stat=True
    ''' @ivar: A general boolean to start and stop the thread.
    '''
    self.thread_stat=threading.Event()
    self.thread_stat.set()
    self.run_proc_event=threading.Event()
    #Used to cancel process only.  It is 'clear' to cancel, 'set' to run
    self.run_proc_event.set()
    self.process_done=threading.Event()
    #Used to indicate that the process is finished
    self.process_done.set()
    self.processed_image_ready=threading.Event()
    #Used to indicate that the processed image is ready to be used
    self.processed_image_ready.clear()
    self.measure_done=threading.Event()
    #Used to indicate that the measurement, a number of processes<self.num_measures>, have finished
    self.measure_done.set()
    self.lock=threading.Lock()
    #A generic thread lock, if needed
    # The following are the rest of the instance variable definitions
    self.sleeptime=sleeptime
    '''@ivar: The defined sleeptime for cycling through the thread, see common_parms.py
    '''
    self.message=''
    ''' @ivar: A message variable
    '''
    self.count=0
    self.num_measures=1
    #self.measurement_count=0
    self.test_qualifier=self.local_time.replace(':','_')
    self.process_type='background'
    self.process_parameters=[[],{}]
    self.peaks_list=[] #################
    self.measurements=[]
    self.rejects=[]
    self.reject_flag=False
    self.process=ImageProcess(self.run_proc_event,self.process_done)
    self.image_count=0
    '''@ivar: The number of images processed from queue
    '''
    self.reject_count=0
    self.accept_count=0
    self.image=None
    '''@ivar: The image of type imgfile.ImageFile from above.
    '''
    self.image_hdr_parms={}
    self.image_queue=Queue.Queue()
    '''@ivar: Image processor image queue of imgfile.ImageFile type
    '''
    self.stdout_flag=prnt
    ''' @ivar: A general boolean to indicate whether or not to print to stdoutthe camera parms to file.
    '''
    subdir1=os.path.join(LOG_DIR,time.strftime('%b%Y'))
    fullpath=os.path.join(subdir1,time.strftime('%B%d'))
    if not os.path.exists(fullpath): os.makedirs(fullpath)
    self.logfile_name=os.path.join(fullpath,IMG_LOGBASENAME+'-'+self.name+'.'+time.strftime('%m.%d.%Y'))
    #self.logfile_name=LOG_DIR+IMG_LOGBASENAME+'-'+self.name+'.'+self.local_date.replace('/','.')
    '''@ivar: The logfile name given in the common_parms.py file in the home directory.
    '''
    self.logging_flag=log
    '''@ivar: A general boolean to indicate whether or not to log the image processing parms to file.
    '''
    self.save_img_flag=save_img
    ''' @ivar: A general boolean to indicate whether or not to save every image to fits file.
    '''
    if device!=None:
      self.device=device
      self.device_name=self.device.camera_name
    else:
      self.device_name=device_name
      self.set_device()
    return
  def __repr__(self):
    '''<__repr__>
       expresses the image processing thread status
    '''
    ss='\n<ProcessThread> class is Alive? %s\n' % (self.isAlive())
    ss='%s\n' % (ss)
    ss='%s\nprocess_type: %s\nprocess_parameters[0]: %r\nprocess_parameters[1]: %r\n' %\
      (ss,self.process_type,self.process_parameters[0],self.process_parameters[1])
    ss='%s\nprocess_type: %s\nnum_measures: %d\n' % (ss,self.process_type,self.num_measures)
    ss='%s\nimage_count: %d\naccept_count: %d\nreject_count: %d\nimage_queue.qsize: %d' %\
      (ss,self.image_count,self.accept_count,self.reject_count,self.image_queue.qsize())
    ss='%s\ndevice_exposure_count: %d\ndevice.data_queue.qsize: %d\n' % \
      (ss,self.device.exposure_count,self.device.data_queue.qsize())
    ss='%s\nLength of Measurement list: %d\n' % (ss,len(self.measurements))
    ss='%s\nLength of Rejects list: %d\n' % (ss,len(self.rejects))
    #ss='%s\nMeasurement list: %r\n' % (ss,self.measurements)
    ss='%s\nMessage: %s\n' % (ss,self.message)
    ss='%s\nProcesses and Measurement flags' % (ss)
    ss='%s\n' % (ss)
    ss='%s\nrun_proc_event: %r\nprocess_done: %r\nmeasure_done: %r\n' % (ss,self.run_proc_event.isSet(),\
      self.process_done.isSet(),self.measure_done.isSet())
    return ss
  def __call__(self,*args,**kwargs):
    run_measure=kwargs.pop('run',False)
    #self.measurement_count+=1
    self.test_qualifier=self.local_time.replace(':','_')
    if self.measure_done.isSet():
      self.reset_measure()
      self.process_type=kwargs.pop('process',self.process_type)
      self.num_measures=kwargs.pop('number',self.num_measures)
      if args: self.process_parameters[0]=list(args)
      if kwargs: self.process_parameters[1]=kwargs
      if run_measure:
        time.sleep(0.1)
        if self.num_measures>1: self.run_device_auto(True)
        else: self.take_new_image()
    if not run_measure and len(args)==0 and len(kwargs)==0:
      self.take_new_image()
    return
  def run(self):
    '''<run> upon a self.start execution, <run> will continually check
       to see if the image and image data is new.   This is accomplished by continually
       checking the device data queue.  If there is data get it and put it into 'self.image_queue'.
       Also, checks its own queue, 'self.image_queue', if there is something then process it with
       <self.process> method. 
    '''
    self.thread_stat.set()
    self.set_message('#Process Thread Started!!!')
    while self.prog_stat:
      time.sleep(self.sleeptime)
      self.count+=1
      if self.thread_stat.isSet():
        if hasattr(self,'device') and self.device!=None:
          if not self.device.data_queue.empty(): # and self.image_count<self.num_measures:
            if self.image_count<self.num_measures:
              #Device data queue has something to be processed, lock thread and get data from device
              self.measure_done.clear()
              self.process_done.clear()
              self.processed_image_ready.clear()
              self.set_message('#Run: Getting Data from camera queue for %s' % (self.process_type))
              image_data=copy(self.device.data_queue.get())
              self.image_count+=1
              self.set_message('#Run: Got data from camera queue, count:%d' %  (self.image_count))
              # use data to create an imgfile.ImageFile class, if device is a file just get data from file
              # this sets self.image 
              if self.device_name=='file':
                self.image=imgfile.ImageFile(fname=self.device.filename)
              else:
                self.image=imgfile.ImageFile(data=image_data)
                self.image.add2header(**self.image_hdr_parms)
                self.image.add2header(dateobs=self.local_date,timeobs=self.local_time,\
                  instrument=self.device_name,exptime=self.device.exptime,cgain=self.device.gain,\
                  xbinning=self.device.binning_x,ybinning=self.device.binning_y)
                self.image.header.set('COMMENT','Process Type:%r' % self.process_type)
                self.image.header.set('COMMENT','Process Parms:%r' % self.process_parameters)
                #if self.save_img_flag: self.image.write_new_image(test_qualifier=self.measurement_count)
                if self.save_img_flag: self.image.write_new_image(test_qualifier=self.test_qualifier)
              self.set_message('#Run: Data Ready to be processed')
              try:
                exec(\
                  'self.process(self.image,self.process_type,*self.process_parameters[0],**self.process_parameters[1])')
                self.set_message('#Run: GOOD MEASUREMENT for %s' % (self.process_type))
                self.accept_count+=1
              except Exception:
                self.reject_count+=1
                self.reject_flag=True
                self.set_message('#Run: REJECTED MEASUREMENT #%d' % self.reject_count)
                self.process_done.set()
              self.process_done.wait()
              self.processed_image_ready.set()
              if self.reject_flag:
                self.rejects.append(self.process.func_return)
                self.reject_flag=False
              else:
                self.measurements.append(self.process.func_return)
                try: 
                  self.peaks_list.append(self.process.image.peaks) #################
                  self.set_message(self.process.image.pprint_peaks())
                except IndexError: pass
                except AttributeError: pass
              self.set_message('#Run: %s: %r' % (self.process_type,self.process.func_return))
            if self.image_count==self.num_measures:
              self.process.message='#Run: Measurement %s done with %d processes!' % (self.process_type,self.num_measures)
              if self.device.auto_sequence_stat.isSet(): self.run_device_auto(onstat=False)
              self.clear_dev_queue()
#             self.reset_measure()
              self.measure_done.set()
              self.processed_image_ready.clear()
#           try: self.peaks_list.append(self.process.image.peaks) #################
#           except IndexError: pass
#           except AttributeError: pass
            self.image_queue.put(self.process.image)
    self.set_message('#Run: Image Processing Thread Stopped!!')
    self.thread_stat.clear()
    return
  def reset_all(self):
    '''reset_all
         Method that will re-initialize the seeing variables, image counts,etc
         To be used when a DIMM measurement is finished
         NOTE clearing the queue in this manner is not technically correct!!!
    '''
    self.message=''
    self.count=0
    self.num_measures=1
    self.process_type='background'
    self.process_parameters=[[],{}]
    self.reset_measure()
    return
  def reset_measure(self):
    self.message='Resetting for next measurement'
    self.clear_dev_queue()
    self.image_count=0             
    self.accept_count=0
    self.reject_count=0
    self.measurements=[]
    self.rejects=[]
    self.peaks_list=[] ######################
    self.measure_done.set()
    self.process_done.set()
    return
  def clear_dev_queue(self):
    self.device.data_queue.queue.clear()
    return
  def flush_all_queues(self):
    self.image_queue.queue.clear()
    self.device.data_queue.queue.clear()
    return
  def set_device(self,dev_name=None,fname=None):
    ''' <set_device>
        Used to set the device from where the image processing data comes
        <dev_name> to set device by the name of a device
        <fname> file name for opening an image file
    '''
    self.thread_stat.clear()
    try:
    #if hasattr(self,'device'):
      self.device.close()
    except Exception: pass
    if dev_name:
      self.device_name=dev_name
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
    elif self.device_name=='file':
      self.device=imgfile.FileDevice(fname=fname)
      self.device.change_file(fname=fname)
    else: pass
    time.sleep(0.1)
    #self.device.seq_exp_list=SEQ_EXPTIMES
    #self.device.auto_delay=SEQ_DELAY
    self.device.start()
    self.reset_all()
    self.set_message('#Setting Device to %s' % self.device_name)
    self.thread_stat.set()
    return
  def run_device_auto(self,onstat=True):
    ''' <run_device_auto>
        Used to run the device in auto sequencing
    '''
    self.set_message('#Setting Device to Auto Run %s' % onstat)
    if onstat: self.device.auto_sequence_stat.set()
    else: self.device.auto_sequence_stat.clear()
    return
  def take_new_image(self):
    ''' <take_new_image>
        Used to take an image.
    '''
    self.device.acquire_image()
    return
  def set_message(self,msg):
    ''' <set_message>
        Will set the message for display or for whatever else the message is
        to be used, and will log to file if the <self.logging_flag> is True
    '''
    #self.local_date,self.local_time=time.strftime(DTIME_FORMAT).split(',')
    self.get_time()
    #self.message='%s %s, %s' % (self.local_date,self.local_time,msg)
    if msg[0]=='#': self.message='#%s %s:  %s' % (self.local_date,self.local_time,msg[1:])
    else: self.message='%s %s:  %s' % (self.local_date,self.local_time,msg)
    if self.logging_flag: self.write_to_log(self.message)
    if self.stdout_flag: sys.stdout.write('%d)Message %s\n' % (self.count,self.message))
    return
  def get_time(self):
    ''' <get_time>
        A standard formatted time routine, format given in the common_parms.py file
    '''
#   self.local_date,self.local_time=time.strftime(DTIME_FORMAT).split(',')
    dt_string=datetime.datetime.strftime(datetime.datetime.now(),DTIME_FORMAT_FLT)[:-4]
    self.local_date,self.local_time=dt_string.split(',')
    return
  def write_to_log(self,arg):
    '''<write_to_log>
          Will write the <arg> to the logfile
    '''
    cur_date=self.local_date.replace('/','.')
###
    subdir1=os.path.join(LOG_DIR,time.strftime('%b%Y'))
    fullpath=os.path.join(subdir1,time.strftime('%B%d'))
    if not os.path.exists(fullpath): os.makedirs(fullpath)
    if cur_date not in self.logfile_name:
      self.logfile_name=os.path.join(fullpath,IMG_LOGBASENAME+'-'+self.name+'.'+cur_date)
###
    #if cur_date not in self.logfile_name:
    #  self.logfile_name=LOG_DIR+IMG_LOGBASENAME+'-'+self.name+'.'+cur_date
    if os.path.exists(self.logfile_name): appendfile='a'
    else: appendfile='w'
    fp=open(self.logfile_name,appendfile)
    fp.write(arg+'\n')
    fp.close()
    return
  def stop(self):
    '''<stop> will set the <self.thread_stat> variable to False and stop the thread.
    '''
    self.set_message('#stop: Stopping device and thread!!!!')
    if self.device_name=='Video':
      self.device.session_driver.release()
    try: self.device.close()
    except Exception: pass
    #del self.device
    self.thread_stat.clear()
    self.prog_stat=False
    return
  def stop_measure(self):
    self.run_device_auto(onstat=False)  #Added 3 July 2018 in order to assure camera stops auto exposures
    self.set_message('#stop_measure: Stopping measurement!!!!')
    self.image_count=self.num_measures
    self.measure_done.set()
    return
  def change_sim_data(self):
    self.device.change_data=True
    return

FINDER_PROC_DICT={'ind1':0,'ind2':1,'center_flag':False,'coords':(FINDER_XCENTER,FINDER_YCENTER),'north_deg':90.0,\
        'east_dir':'ccw','sigma':1.5,'median_box_size':5,'threshold':0,'box_size':500,\
        'center_type':'peaks','seeing_num':SEEING_NUMBER}
CAMERA_PROC_DICT={'ind1':0,'ind2':1,'center_flag':False,'coords':(-1,-1),'north_deg':90.0,'east_dir':'ccw',\
        'sigma':1.5,'median_box_size':5,'threshold':0,'box_size':500,\
        'center_type':'peaks','seeing_num':SEEING_NUMBER}

class Measurement_thread(threading.Thread):
  def __init__(self,name='managing_thread',device=None,device_name='file',sleeptime=IMG_PRC_THREADTIME,\
    log=False,prnt=False,save_img=False):
    threading.Thread.__init__(self)
    self.setName(name)
    self.sleeptime=sleeptime
#   self.local_date,self.local_time=time.strftime(DTIME_FORMAT).split(',')
    dt_string=datetime.datetime.strftime(datetime.datetime.now(),DTIME_FORMAT_FLT)[:-4]
    self.local_date,self.local_time=dt_string.split(',')
    '''@ivar: The local date and time set by the local computer.
    '''
    # The following are a set of events to be flagged for processing images
    self.prog_stat=True
    ''' @ivar: A general boolean to start and stop the thread.
    '''
    self.thread_stat=threading.Event()
    self.thread_stat.set()
    self.results_stat=threading.Event()
    self.results_stat.clear()
    self.process_thread=ProcessThread(name=self.name,device=device,device_name=device_name)
    self.process_thread.start()
    # Set the appropriate logging and verbose flags
    self.set_log_saveimg(prnt=prnt,log=log,save_img=save_img)
    # The following flag is used to identify and trigger the type and starting of the measurement
    # It can only be one of the listed strings in the MEASURE_LIST
    self.take_measure_type_flag=None #Where this variable is used to flage the start of a measurement
    self.results=None
    self.header_parms=None
    if name=='finder': self.process_args=FINDER_PROC_DICT
    else: self.process_args=CAMERA_PROC_DICT
    self.dst=None
    self.tha=None
    self.fluxes=None
    self.seeing=array([-1,-1,-1,-1])
    self.peak_0=array([0,0,0,0,0,0])#Where array([index,x,x_width,y,y_width,height])
    self.peak_1=array([0,0,0,0,0,0])#Where array([index,x,x_width,y,y_width,height])
    self.midpoint=[array([0,0]),array([0,0,0]),array([0,0]),'n']#[(midpt_x,midpt_y),(dx,dy,ds),(dr,dtheta),'direction']
    self.center=[array([0,0]),array([0,0,0]),array([0,0]),'n']#[(center_x,center_y),(dx,dy,ds),(dr,dtheta),'direction']
    self.num_objects=0
    self.centers=None
    self.last_focus=array([0.0,0.0,0.0])
    self.reset_box=False
    self.count=0
    self.message=''
    self.test_return=''
    self.start()
    return
  def __repr__(self):
    ss='\n<Measurement_thread> class is Alive? %s\n' % (self.isAlive())
    ss='%s\n' % (ss)
    ss='%s  self.count=%d\n' % (ss,self.count)
    ss='%s  process_args=%r\n' % (ss,self.process_args)
    ss='%s\n' % (ss)
    ss='%s %s\n' % (ss,self.process_thread)
    return ss
  def __call__(self,measure_type,**kwargs):
    for each in kwargs.keys():  self.process_args[each]=kwargs[each]
    if measure_type in MEASURE_LIST: 
      self.take_measure_type_flag=measure_type
    return
  def init_parms(self):
    self.peak_0=array([0,0,0,0,0,0])
    self.peak_1=array([0,0,0,0,0,0])
    self.midpoint=[array([0,0]),array([0,0,0]),array([0,0]),'n']
    self.center[1:]=[array([0,0,0]),array([0,0]),'n']
    return
  def run(self):
    self.thread_stat.set()
    self.set_message('#Measurement Thread Started!!!')
    while self.prog_stat:
      time.sleep(self.sleeptime)
      if self.take_measure_type_flag:
        if self.take_measure_type_flag=='seeing':
          self.set_message('#Seeing')
          #self.dst,self.fluxes,self.seeing=self.proc_seeing()
          self.dst,self.tha,self.fluxes,self.seeing=self.proc_seeing()
          self.set_message('%r, %r, %d, %d' % (self.seeing,self.dst,self.process_thread.accept_count,\
            self.process_thread.reject_count))
        if self.take_measure_type_flag=='centering':
          self.set_message('#Centering')
          self.center=self.proc_centering()
          self.set_message('%r' % self.center)
        if self.take_measure_type_flag=='image':
          self.set_message('#Imaging')
          self.num_objects,self.centers=self.proc_image()
          self.set_message('%r, %r' % (self.num_objects,self.centers))
        if self.take_measure_type_flag=='boxregion':
          self.set_message('#Box Region')
          self.proc_boxregion()
        if self.take_measure_type_flag=='focusing':
          self.set_message('#Focus')
          self.last_focus=self.proc_focusing()
        if self.take_measure_type_flag=='testing':
          self.set_message('#Testing')
          self.test_return=self.proc_testing()
      self.count+=1
    self.set_message('#Measurement Thread Stopped!!!')
    self.thread_stat.clear()
    return
  def _decorator(measurement):
    def meas_wrapper(self,*args,**kwargs):
      self.take_measure_type_flag=None
      self.process_thread.flush_all_queues()
      self.results_stat.clear()
      self.set_message('#Waiting Results.....')
      results=measurement(self,*args,**kwargs)
      self.set_message('#Measurement results are READY.....')
      self.results_stat.set()
      return results
    return meas_wrapper
  @_decorator
  def proc_seeing(self):
    ''' <proc_seeing>
        This is the procedure for measuring the seeing.  Prior to 28 Oct 2019, the reported seeing was
        inaccurate due to using only the dst array for calculating the eps_trans and eps_long.  The
        last versions (15 and 16) of the file image_proc_thread.py were attempts to correct this.  The
        following uses the mean theta and rotation matrix to compute the rotated centroids and use these
        variances for calculating the eps_trans and eps_long.  This file has all of the previous computations
        and comments removed.
    '''
    self.process_thread(number=self.process_args['seeing_num'],process='pix2peaks',center=False,coords=[-1,-1],run=True)
    self.process_thread.measure_done.clear()
    self.process_thread.measure_done.wait()
    self.results=self.process_thread.measurements
    fluxes=[]
    dxa,dya=abs(array([each[2] for each in self.results])),abs(array([each[3] for each in self.results]))
    dst=array([each[8][0] for each in self.results])
    tha=array([each[8][1] for each in self.results])
    #The following lines added 5 June 2018
    # where mean()~236 and std()~40 for normal
    # binned 1, GX2750, boxed region of 500x500 test measurement
    ### Somewhere in here use this above to count rejects and not give too high seeing measurements
    tmp_count=len(dst)
    keep_indices=where((dst<dst.mean()+3.0*dst.std()) & (dst>dst.mean()-3.0*dst.std()))
    tmp_peak_list=[]
    for each in self.process_thread.peaks_list:
      #### The below was added 13 December 2018 to correct, this may need a closer look later,
      #### but it might be a reasonable fix to the index error.
      try:
        tmp_peak_list.append(array([array(each[0]),array(each[1])]))
      except Exception as err:
        self.set_message('Appending <tmp_peak_list> index error: %s' % (err))
    #The following lines added 20 Dec 2018 in order to bypass errors in tmp_peak_list being []
    try:
      peak_array=array(tmp_peak_list)[keep_indices]
      fluxes=peak_array[:].transpose()[11].mean(axis=1)
    except Exception as err:
      self.set_message('<peak_array> index error by <keep_indices>: %s' % (err))
      fluxes=0.0
    dxx,dyy=dxa[keep_indices],dya[keep_indices]
    dst=dst[keep_indices]
    tha=tha[keep_indices]   # New 22 Oct 2019 to account for transverse seeing
    tha[where(tha<0)]=tha[where(tha<0)]+180.0   # New 22 Oct 2019 to account for transverse seeing
    self.process_thread.accept_count=len(dst)
    self.process_thread.reject_count=tmp_count-len(dst)+self.process_thread.reject_count
    ### 
    self.num_objects=self.process_thread.image.num_peaks
    try:
      theta_mean=tha.mean()
      dxprime=cos(-theta_mean*pi/180.0)*abs(dxx)-sin(-theta_mean*pi/180.0)*abs(dyy)
      dyprime=sin(-theta_mean*pi/180.0)*abs(dxx)+cos(-theta_mean*pi/180.0)*abs(dyy)
      stdlong,stdtrans=dxprime.std(),dyprime.std()
      ### The following four lines are to calculate the transverse and longitudinal pixel std and seeing
      seetran=array(calc_seeing(stdtrans,device_name=self.process_thread.device_name,\
        bin_x=self.process_thread.device.binning_x,bin_y=self.process_thread.device.binning_y))
      seelong=array(calc_seeing(stdlong,device_name=self.process_thread.device_name,\
        bin_x=self.process_thread.device.binning_x,bin_y=self.process_thread.device.binning_y))
      seeing=array([seelong[0],seelong[1],seetran[2],seetran[3]])
    except Exception:
      seeing=array([0,0,0,0])
    self.set_message('%r, %r, %d, %d' % (seeing,dst,self.process_thread.accept_count,self.process_thread.reject_count))
    return dst,tha,fluxes,seeing
  @_decorator
  def proc_centering(self):
    if self.process_args['coords']==(-1,-1):
      self.set_message('#proc_CENTERING, using chip center, coords==(-1,-1)')
      self.process_thread(number=1,process='pix2peaks',run=True,ind1=0,center=True,\
        north_deg=self.process_args['north_deg'],east_dir=self.process_args['east_dir'])
    else:
      self.set_message('#proc_CENTERING, using center coords, coords==%s)' % (str(self.process_args['coords'])))
      self.process_thread(number=1,process='pix2peaks',run=True,ind1=0,coords=self.process_args['coords'],\
        north_deg=self.process_args['north_deg'],east_dir=self.process_args['east_dir'])
    self.process_thread.measure_done.clear()
    self.process_thread.measure_done.wait()
    self.set_peak_array(0)
    self.set_peak_array(1)
    self.num_objects=self.process_thread.image.num_peaks
    try:
      meas=self.process_thread.measurements[0]
      dx,dy,ds,center_position,drt_vect,cardinal=meas[2],meas[3],meas[4],meas[6],meas[8],meas[9]
    except Exception: 
      dx,dy,ds,center_position,drt_vect,cardinal=0,0,0,self.process_args['coords'],array([0,0]),'n'
    center=[center_position,array([dx,dy,ds]),drt_vect,cardinal]
    self.set_message('#proc_CENTERING results, {center_pos,(dx,dy,ds),drt_vect,cardinal}: %r' % (center))
    #To assure that the process_args['coords'] variable will not be set to (0,0)
    if center_position[0]>1 and center_position[1]>1:
      self.process_args['coords']=tuple(center_position)
    self.set_message('#proc_CENTERING, setting process_args[\'coords\']= %s' % (str(center_position)))
    return center
  @_decorator
  def proc_boxregion(self,box_size=-1,center_type=None):
    if box_size>0: self.process_args['box_size']=box_size
    height,width=self.process_args['box_size'],self.process_args['box_size']
    if center_type:  self.process_args['center_type']=center_type
    self.set_message('#Processing BOX')
    self.set_message('#PROCESSING box, center_type= %s' % self.process_args['center_type'])
    if self.process_thread.device_name in ['GT1290','GX2750','Simulation']:
      if self.reset_box:
        self.process_thread.device.set_roi()
        self.reset_box=False
        self.set_message('#PROCESSING box, Resetting Box')
      else:
        self.process_thread(number=1,process=self.process_args['center_type'],run=True) 
        self.process_thread.measure_done.clear()
        self.process_thread.measure_done.wait()
        h,w=int(height/self.process_thread.device.binning_y),int(width/self.process_thread.device.binning_x)
        try:
          if self.process_args['center_type']=='midpoint': box_center=self.process_thread.measurements[0] # FOR MIDPOINT
          else: box_center=self.process_thread.measurements[0][1][0] # FOR PEAKS
          self.set_message('#proc_BOXREGION results: %s %r' % ('BOX CENTER:',box_center))
          offx,offy=int(box_center[0]-w/2),int(box_center[1]-h/2)
        except Exception:
          self.set_message('#proc_BOXREGION results:  NO BOX CENTER')
          offx,offy=0,0
        self.num_objects=self.process_thread.image.num_peaks
        self.process_thread.device.set_roi(h=h,w=w,offx=offx,offy=offy)
        self.set_message('h,w,offx,offy: %r, %r, %r, %r' % (h,w,offx,offy))
        self.process_thread(number=1,process='pix2peaks',run=True)
        self.process_thread.measure_done.clear()
        self.process_thread.measure_done.wait()
    return
  @_decorator
  def proc_image(self):
    self.process_thread(number=1,process='peaks',run=True)
    self.process_thread.measure_done.clear()
    self.process_thread.measure_done.wait()
    self.set_peak_array(0)
    self.set_peak_array(1)
    try:
      num_objects,centers=self.process_thread.measurements[0]
      self.set_message('#proc_IMAGE results: %r, %r' % (num_objects,centers))
    except Exception:
      num_objects,centers=0,array([])
      self.set_message('#proc_IMAGE:  NO measurement excepted, setting %r, %r' % (num_objects,centers))
    return num_objects,centers
  @_decorator
  def proc_focusing(self,ind=0):
    self.process_thread(number=1,process='fwhm',run=True)
    self.process_thread.measure_done.clear()
    self.process_thread.measure_done.wait()
    self.set_peak_array(ind)
    try: 
      focus=self.process_thread.measurements[0]
    except Exception:
      focus=array([0.0,0.0,0])
    self.set_message('#proc_FOCUSING results:%r' % focus)
    return focus
  @_decorator
  def proc_testing(self,*args,**kwargs):
    print 'Running Test'
    fp,path,desc=imp.find_module('image_test_code')
    imp.load_module('image_test_code',fp,path,desc)
    ret_test=image_test_code.test_function(self)
    return ret_test
  def continuous(self):
    if self.process_thread.device.auto_sequence_stat.isSet():
      self.process_thread.stop_measure()
      self.process_thread.reset_all()
    else:
      #self.process_thread(number=SEQ_TOTAL_NUM,process='background',run=True)
      self.process_thread(number=self.process_thread.device.sequence_total_number,process='background',run=True)
    return
  def set_image_hdr_parms(self,**kwargs):
    #Use like:
    #self.set_image_hdr_parms(source='ORI-A',ra='13:00:00',dec='-5:00:00',airmass=1.3,st='14:00:00')
    self.process_thread.image_hdr_parms=kwargs
    return
  def set_peak_array(self,ind):
    try:
      peak=self.process_thread.peaks_list[0][ind]
      self.__dict__['peak_'+str(ind)]=array([ind,peak.abs_x_center,peak.x_width,\
        peak.abs_y_center,peak.y_width,peak.height])
    except IndexError:
      self.__dict__['peak_',ind]=array([ind,-1,-1,-1,-1,0])
    return
  def stop(self):
    self.process_thread.stop()
    self.thread_stat.clear()
    self.prog_stat=False
    return
  def set_message(self,message):
    self.message=message
    self.process_thread.set_message(message)
    return
  def set_log_saveimg(self,prnt=False,log=False,save_img=False):
    # Set the appropriate logging and verbose flags
    self.process_thread.stdout_flag=prnt
    self.process_thread.logging_flag=log
    self.process_thread.save_img_flag=save_img
    return
#
# To get seeing measurements use:
# >>> mm=ProcessThread();mm.start()
# >>> mm(number=100,process='pix2peaks',run=True)   # This produces the data
#
# when finished 
# 
# >>> dst=array([each[4] for each in mm.measurements])
# >>> seeing=array(calc_seeing(dst.std(),device_name=mm.device_name))
#
# this will produce the four transverse/longitudinal seeing calculations
#
#
#
#  For Boxing a region:
# >>> mm(number=1,process='midpoiint',run=True)
# >>> box_center=mm.measurements[0]
#
# >>> h,w=600,600
# >>> reset=False
#    '''box_device
#         This is used to center the brightest peak in a box on the detector or box the data for simulation.
#         <reset> flag will reset to the size of the detector
#    '''
# >>> if mm.device_name=='GT1290' or mm.device_name=='GX2750' or mm.device_name=='Simulation':
# >>>   if reset:
# >>>     mm.device.set_roi()
# >>>   else:
# >>>       h,w=h,w
# >>>       offx,offy=int(box_center[0]-w/2),int(box_center[1]-h/2)
# >>>       self.device.set_roi(h=h,w=w,offx=offx,offy=offy)
#
#
# To move telescope to the center of the optical axis
# 
# >>> mm(process='pix2peaks',center_flag=True,run=True)
# >>> dist,angle=mm.measurements[0][8]
# >>> direction=mm.measurements[0][9]
#
#
# Run the following as
# >>> import thread
# >>> thread.start_new_thread(testseeing,(),{'thrd':mm,'num':25})
# >>> mm.measure_done.wait();mm
#
# And to prematurely stop the <testseeing> function, use
#
# >>> for i in range(7): mm.stop_measure(); print 'Stopping'; time.sleep(1.0)
#
def testseeing(thrd=None,num=100,cycles=5,dev='Simulation'):
  measureslist=[]
  if thrd:
    mm=thrd
  else:
    mm=ProcessThread(device_name=dev)
    mm.start()
  print 'Pre-Measurement'
  mm(process='pix2peaks',number=1,center_flag=True,run=True)
  time.sleep(0.2)
  mm.measure_done.wait()
# print mm
  #yield mm
  mm.reset_all()
  mymm=mm.measurements
# mm(process='peaks',number=num)
  for i in range(cycles):
    print 'Measurement %d' % (i+1)
    mm.reset_measure()
    mm(process='pix2peaks',number=num,run=True)
    #mm.run_device_auto(True)
    time.sleep(1.0)
    mm.measure_done.wait()
    #print mm
    #yield mm
    measureslist.append(mm.measurements)
# mm.stop()
# del mm
  #dst=array([each[4] for each in mm.measurements])
  #seeing=array(nipt.calc_seeing(dst.std(),device_name=mm.device_name))
  dstd=array([[each[4] for each in every] for every in measureslist]).std(axis=1)
  seeing=calc_seeing(dstd,device_name=mm.device_name,bin_x=mm.device.binning_x,bin_y=mm.device.binning_y)
  print 'DONE!!!!'
  if not thrd:
    mm.stop()
    del mm
  return dstd,seeing
#
#
#
def addNoise(data):
  '''
    Will take the grid data and add noise and filter, rotate, and shift it.
  '''
  mm=copy(data)
  background=median(mm)
  mm2=ndimage.gaussian_filter(mm,random.normal(scale=10.0),cval=background)
  background=mean(mm2)
  newdata=ndimage.rotate(mm2,random.normal(scale=0.5),cval=background)
  background=median(newdata)
  newdata=shift(newdata,(random.random(2)-0.5)*25.0,cval=background)  # will shift data by dx and dy
  return newdata

def shift_image(imageclass,dx=0,dy=0,dr=0.0,dtheta=0.0):
  if dr!=0.0 and dtheta!=0.0:
    dx=dr*cos(deg2rad(dtheta))
    dy=dr*sin(deg2rad(dtheta))
  newimage=imgfile.ImageFile()
  newimage.header=imageclass.header
  newimage.fname=imageclass.fname
  newimage.background=imageclass.background
  newimage.data=shift(imageclass.data,(dy,dx),cval=imageclass.background)
  return newimage

def move_to_center(imageclass,peak_index,new_center=zeros((2)),offsets=zeros((2)),north=0.0,east_dir='cw',output=False):
  ''' move_to_center
      moves the peak, <peak_index>, to a new center of the image.
      <new_center> is the new center, defined center(optical axis of the telescope), or where to place the peak
      <offsets> is an array, array([dx,dy])
      if new_center is (0,0) the new center will be the center of the image plus the offset.
      <north> and <east> define the respective directions, always make north a position angle
      <output> if True will return an imgfile.ImageFile image with the shifted data
  '''
  imageclass.find_peaks()
  if all(new_center==zeros((2))):
    #if new_center is (0,0) use the center of the image data plus the offset
    center=array([imageclass.data.shape[1]/2,imageclass.data.shape[0]/2])
    center=center+offsets
  else:
    #else use the new_center parameter
    center=new_center
  xy=array([imageclass.peaks[peak_index].abs_x_center,imageclass.peaks[peak_index].abs_y_center])
  #<ds>=the distance in x and y from the defined center of the original image, ds=array([dx,dy])
  ds=center-xy
  #<drt>=the distance and angle of the original image peak to the defined center(optical axis)
  drt=array([sqrt(dot(ds,ds)),rad2deg(arctan2(ds[1],ds[0]))])
  if output:
    shifted=shift_image(imageclass,dx=ds[0],dy=ds[1])
    shifted.find_peaks()
    #newxy=(shifted.peaks[peak_index].abs_x_center,shifted.peaks[peak_index].abs_y_center)
  else: 
    shifted=None
  #The following will define the north/east directions orientations, the card_dir supplies the cardinal direction
  if east_dir=='cw': east=north-90.0
  else: east=north+90.0
  n_range=array([north-90.0,north+90.])
  e_range=array([east-90.0,east+90.0])
  #<card_dir> is the cardinal direction given NORTH and EAST
  if n_range[0]<drt[1] and drt[1]<n_range[1]: card_dir='n'
  else: card_dir='s'
  if e_range[0]<drt[1] and drt[1]<e_range[1]: card_dir+='e'
  else: card_dir+='w'
  return center,ds,drt,card_dir,shifted

#Examples of simulated images
# Cloudy or no sources:
# ss=ipt.make_image_data(xsize=2200,ysize=2200,height=10,minimum=100.0,rms=10.0,number=4)
#
# Clear strong sources
# ss=ipt.make_image_data(xsize=2200,ysize=2200,height=20000,minimum=100.0,rms=15.0,number=4)
#
# Test like this, where rpt=region_proc_test.py and ipt=image_proc_thread.py:
#>>> ss=ipt.make_image_data(xsize=2200,ysize=2200,height=20000,minimum=100.0,rms=15.0,number=4)
#>>> dd=imgfile.ImageFile(data=ss)

def make_image_data(xsize=765,ysize=510,height=2000,minimum=0,rms=10,number=20):
  '''
    Will return an image with random gaussians.  Stolen from some python website.
  '''
  def g(X,Y,xo,yo,amp=100,sigmax=4,sigmay=4):
    return  amp*exp(-(X-xo)**2/(2*sigmax**2) - (Y-yo)**2/(2*sigmay**2))
  x=linspace(0,xsize,xsize)
  y=linspace(0,ysize,ysize)
  X,Y=meshgrid(x,y)
  Z=X*0
  for xo,yo in (xsize+ysize)/2.0*random.rand(number,2):
    widthx=5+random.randn(1)
    widthy=5+random.randn(1)
    Z+=g(X,Y,xo,yo,amp=height*random.rand(),sigmax=widthx,sigmay=widthy)
  Z=Z+minimum+random.random((ysize,xsize))*rms
  return Z

def calc_seeing(stddev,device_name=None,bin_x=1,bin_y=1):
  #stddev is the standard deviation of the separation in pixels
  b=TELE_SUBSEPARATION  #Sub-aperture separation in [m]
  d=TELE_SUBAPERTURE    #Sub-aperture diameter in [m]
  tele_d=TELE_DIAM      #Telescope diameter [m]
  fratio=TELE_FRATIO    #Telescope fratio
  tele_f=fratio*tele_d  #Telescope focal length [m]
  #pix_size=CAMERA_PIXSIZE*1.0e-6 #Pixel size in [m], here is the average of the two, assuming square pixels???
  if device_name!=None and device_name in ['GT1290','GX2750','SBIG','Video']:
    pixsize_x=eval('CAMERA_'+device_name+'_X_PIXSIZE')*1.0e-6*bin_x
    pixsize_y=eval('CAMERA_'+device_name+'_Y_PIXSIZE')*1.0e-6*bin_y
#   pix_size=eval('CAMERA_'+device_name+'_PIXSIZE')*1.0e-6*bin_x
    pix_size=(pixsize_x+pixsize_y)/2.0
  else:
    pixsize_x=CAMERA_X_PIXSIZE*1.0e-6*bin_x
    pixsize_y=CAMERA_Y_PIXSIZE*1.0e-6*bin_y
#   pix_size=CAMERA_PIXSIZE*1.0e-6*bin_x
    pix_size=(pixsize_x+pixsize_y)/2.0
  arcsec_per_pixel=2.0*arctan(pix_size/(2.0*tele_f))*180.0/pi*3600.0
  radperpix=arcsec_per_pixel/3600.0*pi/180.0
  bdratio=b/d
# klg=0.358*(1.0-0.541*bdratio**(-1.0/3.0))
  klg=0.340*(1.0-0.570*bdratio**(-1.0/3.0)-0.040*bdratio**(-7.0/3.0))
  klz=0.364*(1.0-0.532*bdratio**(-1.0/3.0)-0.024*bdratio**(-7.0/3.0))
# ktg=0.358*(1.0-0.810*bdratio**(-1.0/3.0))
  ktg=0.340*(1.0-0.855*bdratio**(-1.0/3.0)-0.030*bdratio**(-7.0/3.0))
  ktz=0.364*(1.0-0.798*bdratio**(-1.0/3.0)-0.018*bdratio**(-7.0/3.0))
  var_rads=(stddev*radperpix)**2.0
  wavelen=0.5e-6
  ro_lg=((var_rads*d**(1.0/3.0))/(klg*wavelen**2.0))**(-3.0/5.0)
  ro_tg=((var_rads*d**(1.0/3.0))/(ktg*wavelen**2.0))**(-3.0/5.0)
  ro_lz=((var_rads*d**(1.0/3.0))/(klz*wavelen**2.0))**(-3.0/5.0)
  ro_tz=((var_rads*d**(1.0/3.0))/(ktz*wavelen**2.0))**(-3.0/5.0)
  eps_lg=0.98*wavelen/ro_lg*180.0/pi*3600.0  #arcsec fwhm seeing
  eps_tg=0.98*wavelen/ro_tg*180.0/pi*3600.0  #arcsec fwhm seeing
  eps_lz=0.98*wavelen/ro_lz*180.0/pi*3600.0  #arcsec fwhm seeing
  eps_tz=0.98*wavelen/ro_tz*180.0/pi*3600.0  #arcsec fwhm seeing
  res=1.22*wavelen/tele_d*180.0/pi*3600.0
  return eps_lg,eps_lz,eps_tg,eps_tz
 
def calc_ang_sep(pix_dist,device_name=None):
  #pix_dist is the separation in pixels
  b=TELE_SUBSEPARATION  #Sub-aperture separation in [m]
  d=TELE_SUBAPERTURE    #Sub-aperture diameter in [m]
  tele_d=TELE_DIAM      #Telescope diameter [m]
  fratio=TELE_FRATIO    #Telescope fratio
  tele_f=fratio*tele_d  #Telescope focal length [m]
  if device_name!=None and device_name in ['GT1290','GX2750','SBIG','Video']:
    pixsize_x=eval('CAMERA_'+device_name+'_X_PIXSIZE')*1.0e-6
    pixsize_y=eval('CAMERA_'+device_name+'_Y_PIXSIZE')*1.0e-6
    pix_size=eval('CAMERA_'+device_name+'_PIXSIZE')*1.0e-6
  else:
    pixsize_x=CAMERA_X_PIXSIZE*1.0e-6
    pixsize_y=CAMERA_Y_PIXSIZE*1.0e-6
    pix_size=CAMERA_PIXSIZE*1.0e-6
  arcsec_per_pixel=2.0*arctan(pix_size/(2.0*tele_f))*180.0/pi*3600.0
  radperpix=arcsec_per_pixel/3600.0*pi/180.0
  ang_dist=pix_dist*arcsec_per_pixel
  ret_string='With %10.5f "/pixel, the separation of %10.5f pixels is %10.5f"' % (arcsec_per_pixel,pix_dist,ang_dist)
  return ret_string
#
#>>> from pylab import *
#>>> import image_proc_thread as ipt
#>>> from matplotlib.patches import Rectangle as rect
#>>> reload(ipt);wimg=imgfile.ImageFile()
#>>> wimg.create_header();wimg.data=ipt.make_image_data(height=60000.0,number=20)
#>>> wimg.find_peaks()
#>>> imshow(wimg,origin='lower')
#>>> mm=gca()
#>>> for each in wimg.peaks:
#...   xyc=(each.abs_x_center-25,each.abs_y_center-25)
#...   r=rect(xyc,50,50,fc='none',ec='white',lw=1)
#...   mm.add_patch(r,)
#...   raw_input()
#... 
##### mm.patches.pop()
