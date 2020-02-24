#/usr/bin/env python reset_moxa.py
#
#

import telnetlib
import time
import argparse

HOST='169.254.95.100'

def read_moxa_ip_status(host=HOST):
  #This can be used to determine if the Moxa box is waiting for a HOST to connect
  #To read the moxa box menu 7-1 IP settings use the following
  try:
    tn=telnetlib.Telnet(host,0,2)
    time.sleep(0.1)
    tn.write('7\r')
    time.sleep(0.1)
    junk=tn.read_very_eager()
    tn.write('1\r')
    time.sleep(0.1)
    ip_info=tn.read_very_eager()
    time.sleep(0.1)
    tn.write('q\r')
    time.sleep(0.1)
    tn.write('q\r')
    tn.close()
    #return '%s\nFound IP:%d\nFound None:%d\n' % (ip_info,ip_info.count('169'),ip_info.count('Listen'))
    return ip_info.count('169'),ip_info.count('Listen')
  except Exception:
    print 'NO CONNECTION TO HOST ',host
    pass
  return

def reset_moxa(host=HOST):
  #To reset the moxa box
# tn=telnetlib.Telnet(HOST)
  try:
    tn=telnetlib.Telnet(host,0,2)
    time.sleep(0.1)
    tn.write('s\ry\r')
    time.sleep(0.1)
    tn.close()
  except Exception:
    print 'NO CONNECTION TO HOST ',host
    pass
  return

def parse_cmd_line():
  parser=argparse.ArgumentParser()
  parser.add_argument('--port','-p',default='telescope')
  return parser.parse_args()

if __name__=='__main__':
  cmd_args=parse_cmd_line()
  if cmd_args.port=='dome': host='169.254.95.102'
  else: host='169.254.95.100'
  reset_moxa(host=host)
