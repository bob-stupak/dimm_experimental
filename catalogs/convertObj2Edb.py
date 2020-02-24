#!/usr/bin/env python convertObj2Edb.py
#

import ephem

class objCatalogue:
  def __init__(self,fname=None):
    self.fname=fname+'.objects'
    self.cat_line_list=None
    self.cat_edb_string=None
    self.cat=None
    self.open_cat()
    self.make_cat()
    return
  def open_cat(self):
    fp=open(self.fname,'r')
    catlines=fp.readlines()
    fp.close()
    self.cat_line_list=[each.replace('\n','').split('|') for each in catlines]
    return 
  def make_cat(self):
    self.cat=[]
    self.cat_edb_string=''
    for each in self.cat_line_list:
      every=entryObject(each)
      self.cat.append(every)
      self.cat_edb_string=self.cat_edb_string+every.edb_string+'\n'
    return
  def write_cat(self):
    fp=open(self.fname.split('.')[0]+'.edb','w')
    fp.write(self.cat_edb_string)
    fp.close()
    return

class entryObject:
  def __init__(self,line):
    self.line=line
    self.name=''
    self.ra=''
    self.dec=''
    self.epoch=''
    self.magn=0.0
    self.alt_name=''
    self.edb_string=''
    self.retEDB()
    return
  def parseObj(self):
    self.name=self.line[0]
    self.alt_name=self.line[5]
    self.magn=float(self.line[4])
    self.epoch=float(self.line[3])
    self.ra=self.line[1]
    self.dec=self.line[2]
    return
  def retEDB(self):
    self.parseObj()
    edbstring=self.name.replace(' ','')+'-'+self.alt_name
    edbstring=edbstring+',f|S|B8,'+self.ra+','+self.dec
    self.edb_string=edbstring+','+str(self.magn)+','+str(self.epoch)
    return
