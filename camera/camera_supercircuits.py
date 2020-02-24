#! /usr/bin/env python camera_supercircuits.py
# version 1, 4 May 2017
# Changelog:
# 
#

import sys
sys.path.append('..')
import cv2
import time
import threading
import pyfits

import camera_thread as cthread
from common_parms import *

progStat=True

class CameraThread(cthread.CameraThread):
  def __init__(self,channel=VIDEO_CHANNEL,sleeptime=0.1,log=False):
    cthread.CameraThread.__init__(self,camera_name='PC164C')
    self.session_driver = cv2.VideoCapture(channel)
    self.throw_aways=5
    self.success=False
    self.take_exposure()
    return
  def close_camera(self):
    if self.session_driver.isOpened(): self.session_driver.release()
    return
  def take_exposure(self):
    self.get_time()
    self.exposure_count+=1
    for i in range(self.throw_aways):
      suc,junk=self.session_driver.read()
    self.success,self.data = self.session_driver.read()
    self.data_queue.put(self.data[:,:,0])
    self.take_exposure_stat.clear()
    self.new_data_ready_stat.set()
    return
