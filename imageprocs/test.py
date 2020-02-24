import image_proc_thread as ipt
import time
import thread

def retproc(device_name='GX2750'):
  mm=ipt.ProcessThread(device_name=device_name)
  mm.start()
  return mm

def two_cams():
  sess=ipt.camera_prosilica.return_vimba()
  cam1=ipt.camera_prosilica.CameraThread(session=sess,camera_name='GX2750')
  cam2=ipt.camera_prosilica.CameraThread(session=sess,camera_name='GT1290')
  cam1.start()
  cam2.start()
  proc1=ipt.ProcessThread(device=cam1)
  proc2=ipt.ProcessThread(device=cam2)
  proc1.start()
  proc2.start()
  return sess,cam1,cam2,proc1,proc2

def testing(proc,num,proc_num=1,sleep_time=0.5):
  for i in range(num):
    starttime=time.time()
    print 'Running Process %da <background> in %7.4f sec' % (i,time.time()-starttime)
    proc(number=proc_num,process='background',run=True)
#
    proc.measure_done.clear()
#   time.sleep(0.3)
    print 'Waiting for Process %da to finish in %7.4f sec' % (i,time.time()-starttime)
    proc.measure_done.wait()
#   time.sleep(sleep_time)
    print 'Printing results from process %da <background> in %7.4f sec' % (i,time.time()-starttime)
    print proc.measurements
    print 'Running Process %db <peaks> in %7.4f sec' % (i,time.time()-starttime)
    proc(number=proc_num,process='peaks',run=True)
#
    proc.measure_done.clear()
#   time.sleep(0.3)
    print 'Waiting for Process %db to finish in %7.4f sec' % (i,time.time()-starttime)
    proc.measure_done.wait()
#   time.sleep(sleep_time)
    print 'Printing results from process %db <peaks> in %7.4f sec' % (i,time.time()-starttime)
    print proc.measurements
#   time.sleep(sleep_time)
  return

def clearQ(proc):
  proc.image_queue.queue.clear()
  return

def tcm(proc,bnum=1,pnum=10,sleeptime=1.0,boxsize=150):
  thread.start_new_thread(test_cnt_meas,(proc,),({'sleep_time':sleeptime,'boxsize':boxsize,'pnum':pnum,'bnum':bnum}))
  return

def test_cnt_meas(proc,bnum=1,pnum=10,sleep_time=1.0,boxsize=150):
# for i in range(bnum):
    starttime=time.time()
    h,w=boxsize,boxsize
    proc.message='Setting binning to 4x4 at%7.4f sec' % (time.time()-starttime)
    proc.device.set_binning(4,4)
    proc.device.set_roi()
    time.sleep(sleep_time)
    proc.message='Setting ROI to %s at %7.4f sec' % (proc.device.message,time.time()-starttime)
    proc.message='Running Process <midpoint> at %7.4f sec' % (time.time()-starttime)
    proc(number=5,process='midpoint',run=True)
    proc.measure_done.clear()
    proc.measure_done.wait()
    proc.message='Running Process <midpoint> FINISHED at %7.4f sec' % (time.time()-starttime)
    time.sleep(sleep_time)
    proc.message='Printing results from process <midpoint> with data shaped %r, in %7.4f sec\n%r' % \
      (proc.process.image.data.shape,time.time()-starttime,proc.measurements)
    try:
      box_center=proc.measurements[0]
    except IndexError:
      box_center=int(proc.device.width/2),int(proc.device.height/2)
    offx,offy=int(box_center[0]-w/2),int(box_center[1]-h/2)
    proc.device.set_roi(h=h,w=h,offx=offx,offy=offy)
    proc.message='Setting ROI to %s at %7.4f sec' % (proc.device.message,time.time()-starttime)
    proc.message='Setting binning to 1x1 at%7.4f sec' % (time.time()-starttime)
    proc.device.set_binning(1,1)
    proc.message='Running Process <pix2peaks> at %7.4f sec' % (time.time()-starttime)
    proc(number=pnum,process='pix2peaks',run=True)
#
    proc.measure_done.clear()
    proc.measure_done.wait()
    proc.message='Running Process <pix2peaks> FINISHED at %7.4f sec' % (time.time()-starttime)
#   time.sleep(sleep_time)
    proc.message='Printing results from process <pix2peaks> with data shaped %r, in %7.4f sec\n%r' % \
      (proc.process.image.data.shape,time.time()-starttime,proc.measurements)
    proc.device.set_roi()
    time.sleep(sleep_time)
# return 
    return 
