#! /usr/bin/env python test_code.py
#
#
''' test_code
    This module serves as a test function for scripting thing in the dimm.  Below,
    the <test_function> function can be rewritten and tested without having to stop the dimm program
    and restarting everything.
      NOTE that in the manager_thread.py code the python module <imp> is now imported and <find_module>
      and <load_module> are used (probably improperly) to reload this module.
'''
import time

from common_parms import *
from numpy import array

MEAS_TIMEOUT=30.0

def test_function2(mclass,*args,**kwargs):
  ''' <test_function> This function is used to create a sort of script so that the dimm manager thread
                      can reload load this module without having to close the main dimm program.
      @param mclass:  The calling class, in the case of the dimm manager it is <self> or <Manager>
      @param args:    Other arguments, if required
      @param kwargs:  Other keyword arguements, if required
  '''
  mclass.finder.set_binning(4,4)
  if all(mclass.finderimage.process_args['coords']==array([-1,-1])):
    mclass.finderimage.process_args['coords']=(FINDER_XCENTER,FINDER_YCENTER)
  mclass.finderimage.process_args['east_dir']='cw'
  mclass.finderimage.process_args['north_deg']=90.0
  #Finder
  mclass.finderimage('centering')
  mclass.finderimage.results_stat.clear()
  t_out_ret=mclass.finderimage.results_stat.wait(timeout=MEAS_TIMEOUT)
  if not t_out_ret:  mclass.finderimage.process_thread.stop_measure()
# cur_dx=mclass.finderimage.center[1][0]
# cur_dy=mclass.finderimage.center[1][1]
# cur_ds=mclass.finderimage.center[1][2]
# cur_dirt=mclass.finderimage.center[1][-1]
  print '\nFinder:  ',mclass.finderimage.center,'\n'
  try: print 'Finder:  ',mclass.finderimage.peak_0[1],mclass.finderimage.peak_0[3]
  except: print 'Finder:  NO PEAK 0'
  mclass.telescope.move_direction(direction='w',speed='center',rate=0)
  time.sleep(2.5)
  mclass.telescope.move_direction(direction='q')
  #Finder 2
  mclass.finderimage('centering')
  mclass.finderimage.results_stat.clear()
  t_out_ret=mclass.finderimage.results_stat.wait(timeout=MEAS_TIMEOUT)
  if not t_out_ret:  mclass.finderimage.process_thread.stop_measure()
  print '\nFinder:  ',mclass.finderimage.center,'\n'
  try: print 'Finder:  ',mclass.finderimage.peak_0[1],mclass.finderimage.peak_0[3]
  except: print 'Finder:  NO PEAK 0'
  #Camera
  mclass.camera.set_roi()
  mclass.camera.set_binning(4,4)
  mclass.image.process_args['coords']=(mclass.camera.chip_width/2,mclass.camera.chip_height/2)
  mclass.image.process_args['east_dir']='cw'
  mclass.image.process_args['north_deg']=90.0
  mclass.image('centering')
  mclass.image.results_stat.clear()
  t_out_ret=mclass.image.results_stat.wait(timeout=MEAS_TIMEOUT)
  if not t_out_ret:  mclass.image.process_thread.stop_measure()
  print '\nCamera:  ',mclass.image.center,'\n'
  if all(mclass.image.center[0]!=array([0.0,0.0])):
    try: print 'Camera:  ',mclass.image.peak_0[1],mclass.image.peak_0[3]
    except: print 'Camera:  NO PEAK 0'
  else:
    print 'Camera:  NO PEAKS IN IMAGE'
  #Finder 3
  mclass.finderimage('centering')
  mclass.finderimage.results_stat.clear()
  t_out_ret=mclass.finderimage.results_stat.wait(timeout=MEAS_TIMEOUT)
  if not t_out_ret:  mclass.finderimage.process_thread.stop_measure()
  print '\nFinder:  ',mclass.finderimage.center,'\n'
  try: print 'Finder:  ',mclass.finderimage.peak_0[1],mclass.finderimage.peak_0[3]
  except: print 'Finder:  NO PEAK 0'
  return
def test_function(mclass,*args,**kwargs):
  ''' <test_function> This function is used to create a sort of script so that the dimm manager thread
                      can reload load this module without having to close the main dimm program.
      @param mclass:  The calling class, in the case of the dimm manager it is <self> or <Manager>
      @param args:    Other arguments, if required
      @param kwargs:  Other keyword arguements, if required
  '''
  # Save the images for both the finder and the image process
  mclass.image.process_thread.save_img_flag=True
  mclass.finderimage.process_thread.save_img_flag=True
  # Reset the camera to full frame and binning of 4x4
  mclass.camera.set_roi()
  mclass.camera.set_binning(4,4)
  # Take one exposure for file from header..
  mclass.camera.exptime=0.1
  mclass.camera.gain=0
  mclass.image_source()  # Note can use this since this method resets binning to 4x4
  try: tst=mclass.local_time.replace(':','_')
  except Exception as err: tst='00_00_00'
  try: src=mclass.image.process_thread.process.image.header['object'].replace(' ','').lower()
  except Exception as err: src='unknown'
  fp=open('%sapr2020_tests/%s-%s.dat' % (LOG_DIR,src,tst),'w')
  # Cycle through exposure time (xpt) and gain (gan) settings
  for xpt in [0.001,0.005,0.01,0.05,0.1]:
    if mclass.cancel_process_stat.isSet(): break#20apr2020 test
    for gan in [0,5,10,15]:
      if mclass.cancel_process_stat.isSet(): break#20apr2020 test
      mclass.camera.exptime=xpt
      mclass.camera.gain=gan
      mclass.image_source()  # Note can use this since this method resets binning to 4x4
#
###   try: print mclass.image.process_thread.process.image.header['object']
###   except Exception as err: print 'Header ERROR'
      try:
        for i in range(len(mclass.image.process_thread.process.image.peaks[:5])):
          fp.write('Exptime:%7.3f, Gain:%d, Peak:%d\nPeak Data Array:%s' % \
            (xpt,gan,i,array(mclass.image.process_thread.process.image.peaks[i])))
  #       print 'Exptime:%7.3f, Gain:%d, Peak:%d\nPeak Data Array:%s' % \
  #         (xpt,gan,i,array(mclass.image.process_thread.process.image.peaks[i]))
          #mclass.image.process_thread.process.image.peaks[i].make_fit_data()
          fp.write('\nFitted parms:%s' % (mclass.image.process_thread.process.image.peaks[i].fit_gaussian(
            mclass.image.process_thread.process.image.peaks[i].data)))
  #       print '\nFitted parms:%s' % (mclass.image.process_thread.process.image.peaks[i].fit_gaussian(
  #         mclass.image.process_thread.process.image.peaks[i].data))
          #print '\nFitted Data: %s' % (mclass.image.process_thread.process.image.peaks[i].fitted_data)
      except Exception as err:
        fp.write('NOT RIGHT!!!')
#       print 'NOT RIGHT!!!'
#
      # This next step reports the background and its std to a log.
      mclass.set_message('Testing Camera Gain: %d, Exposure Time: %7.3f, Background: %7.3f, Std: %7.3f' %\
        (gan,xpt,mclass.image.process_thread.process.background,mclass.image.process_thread.process.bgnd_std))
      #try:
      #  print 'Right!!!!'
      #except Exception:
      #  print 'NOT RIGHT!!!'
      time.sleep(1.0) 
  # Reset the camera exposure time and gain to 100msec and gain=0
  mclass.camera.exptime=0.1
  mclass.camera.gain=0
  try:
    #Set a boxed region around the midpoint of the two images in the seeing camera at 4x4 binning
    mclass.set_message('dimm process: Boxing region')
    fp.write('dimm process: Boxing region')
    mclass.image('boxregion',center_type='midpoint')
    mclass.set_message('dimm process: Waiting for results_stat event while boxing region')
    fp.write('dimm process: Waiting for results_stat event while boxing region')
    mclass.image.results_stat.clear()  #############NEW 23 Oct 2017
    t_out_ret=mclass.image.results_stat.wait(timeout=MEAS_TIMEOUT)         #Timeout added 6June2018
    if not t_out_ret:  
      mclass.image.process_thread.stop_measure()   #Timeout condition added 6June2018
      mclass.set_message('dimm process: results_stat event timed-out while boxing region')
      fp.write('dimm process: results_stat event timed-out while boxing region')
  except Exception as err:
    fp.write('Error from boxing region: %s' % err)
    mclass.set_message('Error from boxing region: %s' % err)
  time.sleep(0.2)  #Changed 8Nov2018
  #Set the binning back to 1x1 for a 500x500 box around the midpoint of the two star images
  mclass.camera.set_binning(1,1)
# try:
  #Redo the exposure and gain testing
  for xpt in [0.001,0.005,0.01,0.05,0.1]:
    if mclass.cancel_process_stat.isSet(): break #20apr2020 test
    for gan in [0,5,10,15]:
      mclass.set_message('Gain:%d, Exposure:%7.4f' % (gan,xpt))
      if mclass.cancel_process_stat.isSet(): break ##20apr2020 test
      mclass.camera.exptime=xpt
      mclass.camera.gain=gan
      mclass.image.process_thread()
#
###   try: print mclass.image.process_thread.process.image.header['object']
###   except Exception as err: print 'Header ERROR'
      try:
        for i in range(len(mclass.image.process_thread.process.image.peaks[:5])):
          fp.write('Exptime:%7.3f, Gain:%d, Peak:%d\nPeak Data Array:%s' % \
            (xpt,gan,i,array(mclass.image.process_thread.process.image.peaks[i])))
          fp.write('\nFitted parms:%s' % (mclass.image.process_thread.process.image.peaks[i].fit_gaussian(
            mclass.image.process_thread.process.image.peaks[i].data)))
      except Exception as err:
        print 'IN TRY RANGE Something\'s NOT RIGHT!!!'
        fp.write('Error: %s' % err)
        mclass.set_message('Error: %s' % err)
#
      mclass.set_message('Testing Camera Gain: %d, Exposure Time: %7.3f, Background: %7.3f, Std: %7.3f' %\
        (gan,xpt,mclass.image.process_thread.process.background,mclass.image.process_thread.process.bgnd_std))
      #try:
      #  print 'Right!!!!'
      #except Exception:
      #  print 'NOT RIGHT!!!'
      time.sleep(1.0) 
  #Reset the box region, binning to 4x4, exposure time, and gain
  fp.write('Resetting region:')
  mclass.set_message('Resetting region:')
  mclass.image.reset_box=True
  mclass.image('boxregion')
  mclass.camera.set_binning(4,4)
  mclass.camera.exptime=0.1
  mclass.camera.gain=0
# except Exception as err:
#   print 'Something\'s NOT RIGHT!!!'
#   fp.write('Error: %s' % err)
#   mclass.set_message('Error: %s' % err)
  #Do the above test for the finderscope camera
  mclass.finder.set_roi()
  mclass.finder.set_binning(4,4)
  for xpt in [0.001,0.005,0.01,0.05,0.1]:
    if mclass.cancel_process_stat.isSet(): break #20apr2020 test
    for gan in [0,5,10,15]:
      if mclass.cancel_process_stat.isSet(): break #20apr2020 test
      mclass.finder.exptime=xpt
      mclass.finder.gain=gan
#
      try: mclass.finderimage.process_thread(process='peaks')
      except Exception as err: mclass.finderimage.process_thread()
###   try: print mclass.finderimage.process_thread.process.image.header['object']
###   except Exception as err: print 'Header ERROR'
###   try: print mclass.finderimage.process_thread.process.image.num_peaks
###   except Exception as err: print 'NUM_PEAKS ERROR'
      try:
        for i in range(len(mclass.finderimage.process_thread.process.image.peaks[:5])):
          fp.write('Exptime:%7.3f, Gain:%d, Peak:%d\nPeak Data Array:%s' % \
            (xpt,gan,i,array(mclass.finderimage.process_thread.process.image.peaks[i])))
#         print 'Exptime:%7.3f, Gain:%d, Peak:%d\nPeak Data Array:%s' % \
#           (xpt,gan,i,array(mclass.finderimage.process_thread.process.image.peaks[i]))
          #mclass.finderimage.process_thread.process.image.peaks[i].make_fit_data()
          fp.write('\nFitted parms:%s' % (mclass.finderimage.process_thread.process.image.peaks[i].fit_gaussian(
            mclass.finderimage.process_thread.process.image.peaks[i].data)))
#         print '\nFitted parms:%s' % (mclass.finderimage.process_thread.process.image.peaks[i].fit_gaussian(
#           mclass.finderimage.process_thread.process.image.peaks[i].data))
          #print '\nFitted Data: %s' % (mclass.finderimage.process_thread.process.image.peaks[i].fitted_data)
      except Exception as err:
        fp.write('NOT RIGHT!!!')
#       print 'NOT RIGHT!!!'
#
      mclass.set_message('Testing Finder Gain: %d, Exposure Time: %7.3f, Background: %7.3f, Std: %7.3f' %\
        (gan,xpt,mclass.finderimage.process_thread.process.background,mclass.finderimage.process_thread.process.bgnd_std))
#     try:
#       print 'Right!!!!'
#     except Exception:
#       print 'NOT RIGHT!!!'
      time.sleep(1.0) 
  mclass.finder.exptime=0.1
  mclass.finder.gain=0
  #Stop saving images
  mclass.image.process_thread.save_img_flag=False
  mclass.finderimage.process_thread.save_img_flag=False
  mclass.set_message('Test Function FINISHED!!')
  fp.close()
  return

def test_function1(mclass,*args,**kwargs):
  ''' <test_function> This function is used to create a sort of script so that the dimm manager thread
                      can reload load this module without having to close the main dimm program.
      @param mclass:  The calling class, in the case of the dimm manager it is <self> or <Manager>
      @param args:    Other arguments, if required
      @param kwargs:  Other keyword arguements, if required
  '''
  #mclass.image.process_thread.save_img_flag=True
  mclass.camera.exptime=0.1
  mclass.camera.gain=0
  mclass.image_source()
  try: print '1st Full Frame number of objects: ',mclass.image.num_objects
  except Exception: print '1st Full Frame NUM_OBJECTS none!!!'
  mclass.image('boxregion',center_type='midpoint')
  mclass.set_message('test_function process: Waiting for results_stat event')
  mclass.image.results_stat.clear()
  t_out_ret=mclass.image.results_stat.wait(timeout=MEAS_TIMEOUT) 
  if not t_out_ret:  mclass.image.process_thread.stop_measure()
  mclass.set_message('test_function process: Results_stat event set')
  try: print 'Boxed ROI Frame number of objects: ',mclass.image.num_objects
  except Exception: print 'NUM_OBJECTS none!!!'
  try:
    if mclass.image.num_objects>1:
      print 'PEAKS LIST',mclass.image.num_objects
      print mclass.image.process_thread.peaks_list #[0][0]
    else:  print 'No peaks found'
  except Exception: 
    print 'FAILED printing peaks_list'
  try:
    print 'Measurements: ',mclass.image.process_thread.measurements
  except Exception: 
    print 'FAILED printing measurements'
  time.sleep(0.2) 
  mclass.camera.set_binning(4,4)
  mclass.camera.set_roi()
  mclass.image_source()
  try: print '2nd Full Frame number of objects: ',mclass.image.num_objects
  except Exception: print '2nd Full Frame NUM_OBJECTS none!!!'
# mclass.camera.exptime=0.005
# mclass.image_source()
# mclass.camera.exptime=0.01
# mclass.image_source()
# mclass.camera.exptime=0.05
# mclass.image_source()
# mclass.camera.exptime=0.1
# mclass.image_source()
# mclass.camera.exptime=0.5
# mclass.image_source()
# t_out=mclass.image.results_stat.wait(timeout=3.0)
# if not t_out:  mclass.image.process_thread.stop_measure()
# print mclass.image.last_focus 
  #mclass.image.process_thread.save_img_flag=False
  return
