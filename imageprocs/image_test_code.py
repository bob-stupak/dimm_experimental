#! /usr/bin/env python image_test_code.py
#
#
''' image_test_code
    This module serves as a means of testing and changing a method in real time(that is not
    having to exit the dimm program' for the Measurment class in the image_proc_thread.py module.
    The <test_function> function 
'''
import sys
sys.path.append('..')

def test_function(mclass,*args,**kwargs):
  try:
    #print 'num_objects: %d' % (mclass.num_objects)
    print 'TESTING NOW %s' % (mclass.num_objects)
  except Exception as err:
    print '%s' % (err)
  return mclass.num_objects
