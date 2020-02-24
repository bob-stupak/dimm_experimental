#! /usr/bin/env python source_cat_gui.py
#

'''Module source_cat_gui.py
'''

import sys
sys.path.append('..')

import os
from Tkinter import *
import Pmw as pmw
import ephem
import guis.frame_gui as fg
import source_cat_thread as srcthread
from numpy import pi,array,where

from common_parms import *

class LocationGUI(fg.FrameGUI):
  global hmeLat,hmeLng,hmeElv
  __module__='source_cat_gui'
  def __init__(self,root=None,col=0,row=0,colspan=1,rowspan=1,location=None):
    self._mesBarList=[['siteNameMess','Site Name',15,(0,0,3,1,'nsew')],\
      ['latMess','Latitude',15,(0,1,3,1,'nsew')],\
      ['longMess','Longitude',15,(0,2,3,1,'nsew')],\
      ['elvMess','Elevation',15,(0,3,3,1,'nsew')],\
      ['localDateMess','Local Date',15,(0,5,3,1,'nsew')],\
      ['localTimeMess','Local Time',15,(0,6,3,1,'nsew')],\
      ['utcDateMess','UTC Date',15,(0,7,3,1,'nsew')],\
      ['utcTimeMess','UTC Time',15,(0,8,3,1,'nsew')],\
      ['lstMess','LST',15,(0,10,3,1,'nsew')],\
      ['asttwilbegMess','Next Local Ast Twilight',20,(0,12,3,1,'nsew')],\
      ['civtwilbegMess','Next Local Civ Twilight',20,(0,13,3,1,'nsew')],\
      ['sunriseMess','Next Local Sunrise',20,(0,14,3,1,'nsew')],\
      ['sunsetMess','Next Local Sunset',20,(0,15,3,1,'nsew')],\
      ['civtwilendMess','Next Local Civ Twilight',20,(0,16,3,1,'nsew')],\
      ['asttwilendMess','Next Local Ast Twilight',20,(0,17,3,1,'nsew')],\
]
    fg.FrameGUI.__init__(self,root=root,name='Location Information',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    blank1=fg.BlankSpace(self.interior(),row=4,colspan=3)
    blank2=fg.BlankSpace(self.interior(),row=9,colspan=3)
    blank3=fg.BlankSpace(self.interior(),row=11,colspan=3)
    if location==None:
      self.location=srcthread.LocationThread(lon=DIMLNG,lat=DIMLAT,elv=DIMELV)
      self.location.start()
    else:
      self.location=location
    self.setMessages()
    self.check_update()
    return
  def setMessages(self):
    self.utcDateMess.message('state','%s' % self.location.utc_date)
    self.utcTimeMess.message('state','%s' % self.location.utc_time)
    self.localDateMess.message('state','%s' % self.location.local_date)
    self.localTimeMess.message('state','%s' % self.location.local_time)
    self.lstMess.message('state','%s' % str(self.location.lst_time))
    self.siteNameMess.message('state','%s' % str(self.location.name))
    self.latMess.message('state','%s' % str(self.location.lat))
    self.longMess.message('state','%s' % str(self.location.lon))
    self.elvMess.message('state','%sm' % str(self.location.elevation))
    self.asttwilbegMess.message('state','%s' % str(self.location.beg_astr_twilight).split('.')[0])
    self.civtwilbegMess.message('state','%s' % str(self.location.beg_civil_twilight).split('.')[0])
    self.sunriseMess.message('state','%s' % str(self.location.sunrise).split('.')[0])
    self.sunsetMess.message('state','%s' % str(self.location.sunset).split('.')[0])
    self.civtwilendMess.message('state','%s' % str(self.location.end_civil_twilight).split('.')[0])
    self.asttwilendMess.message('state','%s' % str(self.location.end_astr_twilight).split('.')[0])
    return
# def test(self):
#   return
  def check_update(self):
    self.setMessages()
    self.after(10,self.check_update)
    return
  def stopall(self):
    global progStat
    if not hasattr(self.root,'closeAll'):
      self.root.destroy()
    progStat=False
    return


class CatalogGUI(fg.FrameGUI):
  global hmeLat,hmeLng,hmeElv
  __module__='source_cat_gui'
  def __init__(self,root=None,col=0,row=0,colspan=1,rowspan=1,\
    catalogue=None,location=None):
    if location==None:
      self.location=srcthread.LocationThread()
      self.location.start()
    else:
      self.location=location
    if catalogue==None:
      self.catalogue=srcthread.StarCatThread(catname=CAT_DIR+CAT_NAME,\
        location=self.location)
    else:
      self.catalogue=catalogue
    self.starlist=self.catalogue.starlist
    self.starlistNames=self.catalogue.starlist_names
    self.candidates=self.catalogue.candidates
    self.star=self.candidates[0]
    self.magnlimit=self.catalogue.magnlimit     #Magnitude selection criterion
    self.magnlimitmax=self.catalogue.magnlimitmax  #Max magnitude selection criterion
    self.zdistlimit=self.catalogue.zdistlimit   #Zenith distance selection in degrees
    self.zdistminimum=self.catalogue.zdistminimum   #Zenith distance selection in degrees
    self._mesBarList=[
      ['catName','Catalog',15,(0,1,3,1,'nsew')],\
      ['catNumb','Number Sources',15,(0,2,3,1,'nsew')],\
      ['candNums','Number Candidates',15,(0,3,3,1,'nsew')],\
      ['starName','Name',15,(0,4,3,1,'nsew')],\
      ['starDec','Dec',15,(0,5,3,1,'nsew')],\
      ['starRA','RA',15,(0,6,3,1,'nsew')],\
      ['starEpoch','Epoch',15,(0,7,3,1,'nsew')],\
      ['starADec','Cur Dec',15,(0,8,3,1,'nsew')],\
      ['starARA','Cur RA',15,(0,9,3,1,'nsew')],\
      ['starel','Elevation',15,(0,10,3,1,'nsew')],\
      ['staraz','Azimuth',15,(0,11,3,1,'nsew')],\
      ['zenDist','Zenith Dist',15,(0,12,3,1,'nsew')],\
      ['airMass','Airmass',15,(0,13,3,1,'nsew')],\
      ['starmag','Magnitude',15,(0,14,3,1,'nsew')]]
    self._buttonList=[['catButton','Change Catalog','self.set_catalogue',(0,20,3,1,'ew')],\
                      ['newsrcButton',self.candidates[0].name,'self.get_source',(0,0,3,1,'ew')],\
                      ['nextsrcButton','Change Source','self.change_source',(0,18,3,1,'ew')]]
#   self._optionList=[['starNames','Star',self.candidates[0].name,[each.name for each in\
#     self.candidates],self.setStar,(0,0,3,1,'nw')]]
    self._entryList=[['entryZDist','Zdist limit',str(self.zdistlimit),\
                     {'validator':'real'},self.set_zd_limit,15,(0,15,3,1,'nsew')],\
                     ['entryZMin','Zdist Min',str(self.zdistminimum),\
                     {'validator':'real'},None,15,(0,16,3,1,'nsew')],\
                     ['entryMagn','Magn limit',str(self.magnlimit),\
                     {'validator':'real'},self.set_mg_limit,15,(0,17,3,1,'nsew')],\
                     ['entryMagnMax','Max Magn limit',str(self.magnlimitmax),\
                     {'validator':'real'},self.set_mg_limit,15,(0,18,3,1,'nsew')]]
    self._checkList=[['automanualStat','Auto Mode','horizontal','radiobutton',['Auto','Manual'],\
                     None,(0,19,3,1,'nsew')],\
                     ['loggingStat','Logging','horizontal','radiobutton',['False','True'],\
                     self.set_logging,(0,21,3,1,'nsew')]]
    fg.FrameGUI.__init__(self,root=root,name='Catalogue Information',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
#   self.select_source()
    self.automanualStat.setvalue('Auto')
    self.loggingStat.setvalue(str(self.catalogue.logging_flag))
#   self.starNames.setvalue(self.catalogue.source.name)
    self.newsrcButton.configure(text=self.catalogue.source.name)
    self.check_update()
    return
# def openCat(self,fname=CAT_DIR+CAT_NAME):
#   self.catalogue=srcthread.StarCatThread(catname=CAT_DIR+CAT_NAME,\
#     location=self.location)
#   self.catalogue.open_cat()
#   return
# def compLocation(self,location=None):
#   if location!=None:
#     self.location=location
#   if self.location!=None:
#     for each in self.starlist:
#       each.compute(self.location)
#   return
  def change_source(self):
    self.catalogue.change_source()
#   self.starNames.setvalue(self.catalogue.source.name)
    self.newsrcButton.configure(text=self.catalogue.source.name)
    return
  def set_logging(self,*tags):
    logging=self.loggingStat.getcurselection()
    if logging=='True': self.catalogue.logging_flag=True  #Set the boolean for logging
    else: self.catalogue.logging_flag=False
    return
  def setStar(self,var):
    self.starNames.var.set(self.starNames.getvalue())
    self.star=[each for each in self.candidates if \
      self.starNames.getvalue()==each.name][0]
    self.catalogue.change_source(name=self.star.name)
    return
  def get_source(self):
    self.dialog = pmw.SelectionDialog(self.root,
      title = 'Select Source',
      buttons = ('OK', 'Cancel'),
      defaultbutton = 'OK',
      scrolledlist_labelpos = 'n',
      label_text = 'Change Source Dialog',
      scrolledlist_items = [each.name for each in self.candidates],
      command = self.change_source_dialog)
    [each.configure(font=fg.TEXT_FONT) for each in \
      self.dialog.component('buttonbox').component('hull').children.values()]
    self.dialog.component('scrolledlist').component('listbox').configure(font=\
      fg.TEXT_FONT)
    self.dialog.component('label').configure(font=fg.TEXT_LRG)
    self.dialogentry=pmw.EntryField(self.dialog.component('dialogchildsite'))
    self.dialogentry.component('entry').configure(font=fg.TEXT_FONT)
    self.dialogentry.pack()
    self.check_string='+'
    self.update_dialog()
    return
  def change_source_dialog(self, result):
    sels = self.dialog.getcurselection()
    if len(sels)!= 0:
      self.newsrcButton.configure(text=sels[0])
      self.star=[each for each in self.candidates if \
        sels[0]==each.name][0]
      self.catalogue.change_source(name=self.star.name)
    self.dialog.withdraw()
    self.dialog.deactivate(result)
    self.after_cancel(self.ii)
    #del self.dialog,self.dialogentry
    return 
  def update_dialog(self):
    nn=self.dialogentry.getvalue()
    if nn!=self.check_string and self.check_string!='+':
      tmp=list(self.dialog.component('scrolledlist').get())
      rr=[each for each in tmp if nn in each]
      self.dialog.component('scrolledlist').setlist(rr)
    if nn=='' and self.check_string!='':
      self.dialog.component('scrolledlist').setlist([each.name for each in self.catalogue.candidates])
      self.check_string='+'
    self.check_string=nn
    self.ii=self.after(1,self.update_dialog)
    return
  def set_catalogue(self):
    self.dialog = pmw.SelectionDialog(self.root,
      title = 'Source Catalog Selection',
      buttons = ('OK', 'Cancel'),
      defaultbutton = 'OK',
      scrolledlist_labelpos = 'n',
      label_text = 'Change Catalog Dialog',
      scrolledlist_items = os.listdir(CAT_DIR),
      command = self.change_catalogue)
    [each.configure(font=fg.TEXT_FONT) for each in \
      self.dialog.component('buttonbox').component('hull').children.values()]
    self.dialog.component('scrolledlist').component('listbox').configure(font=\
      fg.TEXT_FONT)
    self.dialog.component('label').configure(font=fg.TEXT_LRG)
    #self.dialog.withdraw()
    return
  def change_catalogue(self, result):
    sels = self.dialog.getcurselection()
    if len(sels) == 0:
      self.dialog.withdraw()
      self.dialog.deactivate(result)
    else:
      if os.path.isdir(sels[0]):
        #os.chdir(sels[0])
        #self.dialog.component('scrolledlist').setlist(['../']+os.listdir('./'))
        pass
      else:
        self.catalogue.change_cat(sels[0][:-4])
#       self.catalogue.cat_name='./catalogs/'+sels[0]
#       self.catalogue.open_cat()
        self.entryZDist.setentry(45.0)
        self.set_zd_limit()
        self.entryMagn.setentry(10.0)
        self.entryMagnMax.setentry(-18.0)
        self.set_mg_limit()
#       self.select_source(once=True)
      self.dialog.withdraw()
      self.dialog.deactivate(result)
    return 
  def set_zd_limit(self):
    zd=self.entryZDist.component('entry').get()
    self.catalogue.zdistlimit=float(zd)
    self.zdistlimit=float(zd)       #Zenith distance selection in degrees
    self.entryZDist.var.set(zd)
    self.select_source(once=True)
#   self.starNames.var.set(self.candidates[0].name)
    self.newsrcButton.configure(text=self.candidates[0].name)
    return
  def set_mg_limit(self):
    mg=self.entryMagn.component('entry').get()
    mgmax=self.entryMagnMax.component('entry').get()
    self.catalogue.magnlimit=float(mg)
    self.catalogue.magnlimitmax=float(mgmax)
    self.magnlimit=float(mg)        #Magnitude selection criterion
    self.magnlimitmax=float(mgmax)  #Magnitude selection criterion
    self.entryMagn.var.set(mg)
    self.entryMagnMax.var.set(mgmax)
    self.select_source(once=True)
#   self.starNames.var.set(self.candidates[0].name)
    self.newsrcButton.configure(text=self.candidates[0].name)
    return
  def select_source(self,once=False):
    '''select_source
         This method will first compute the current star position in the sky
         from the current location, calculate the zenith distance for all of the
         stars in the catalog.  Then will find the candidate star indices in the
         self.starlist variable.  Then set the self.candidates list variable
         to the found stars.
    '''
    self.catalogue.select_candidates()
    self.star=self.catalogue.source
    self.starlist=self.catalogue.starlist
    self.starlistNames=self.catalogue.starlist_names
    self.candidates=self.catalogue.candidates
#   try:
#     ndx=[i for i in range(len(self.candidates)) if \
#       self.star.name==self.candidates[i].name][0]
#     self.starNames.setitems([each.name for each in self.candidates])
#     self.starNames.invoke(index=ndx)
#   except IndexError: pass
    ###Don't have a means to handle nothing in the candidates list YET!!!!
    ###  see in source_cat_thread.select_candidates method added if no
    ###  candidates available don't change list!!
    #The following for debugging
    #print 'New Candidates are'
    #for each in self.candidates:
    #  print each.name
    #print '\n'
#   if once==False:  
      # The <once> variable is used to not spawn this after command more than once
#     self.after(1000,self.select_source)  #Check every ten seconds
#     self.after(300000,self.select_source)  #Check every five minutes
    return
  def check_update(self):
    self.catName.message('state','%s' % self.catalogue.cat_name.split('/')[-1])
    self.catNumb.message('state','%d' %  len(self.catalogue.starlist_names))
    self.candNums.message('state','%d' % len(self.catalogue.candidates))
    self.newsrcButton.configure(text=self.catalogue.source.name)
    if self.automanualStat.getvalue()!='Manual':
      self.catButton.configure(state='disabled')
      self.newsrcButton.configure(state='disabled')
#     self.starNames.component('menubutton').configure(state='disabled')
      self.entryZDist.component('entry').configure(state='disabled')
      self.entryZMin.component('entry').configure(state='disabled')
      self.entryMagn.component('entry').configure(state='disabled')
      self.entryMagnMax.component('entry').configure(state='disabled')
      self.catalogue.auto_select=True
    else:
      self.catButton.configure(state='normal')
      self.newsrcButton.configure(state='normal')
#     self.starNames.component('menubutton').configure(state='normal')
      self.entryZDist.component('entry').configure(state='normal')
      self.entryZMin.component('entry').configure(state='disabled')
      self.entryMagn.component('entry').configure(state='normal')
      self.entryMagnMax.component('entry').configure(state='normal')
      self.catalogue.auto_select=False
    if self.star!=None:
#     self.star.compute(self.location)
      self.star=self.catalogue.source
#     zdist=ephem.separation((float(self.location.lst_time),float(self.location.lat)),\
#       (self.star.a_ra,self.star.a_dec))
      zdist,direction,airmass=self.catalogue.find_zdist(star=self.star)
      self.starName.message('state','%s' % self.star.name)
      self.starRA.message('state','%s' % self.star.ra)
      self.starDec.message('state','%s' % self.star.dec)
      try: self.starEpoch.message('state','%s' % str(self.star._epoch)[:4])
      except Exception: self.starEpoch.message('state','%s' % 'N/A')
      self.starARA.message('state','%s' % self.star.a_ra)
      self.starADec.message('state','%s' % self.star.a_dec)
      self.staraz.message('state','%s' % self.star.az)
      self.starel.message('state','%s' % self.star.alt)
      self.starmag.message('state','%s' % self.star.mag)
      if zdist>pi/2.0:
        self.zenDist.component('entry').configure(readonlybackground='Red')
      else:
        self.zenDist.component('entry').configure(readonlybackground='#d9d9d9')
      self.zenDist.message('state','%s %s' % (str(zdist),direction[0]))
      self.airMass.message('state','%10.6f' % (airmass))
      if self.catalogue.zdistlimit!=self.zdistlimit or \
        self.catalogue.magnlimit!=self.magnlimit or \
        self.catalogue.magnlimitmax!=self.magnlimitmax:
        self.entryZDist.setentry(self.catalogue.zdistlimit)
        self.entryMagn.setentry(self.catalogue.magnlimit)
        self.entryMagnMax.setentry(self.catalogue.magnlimitmax)
        self.set_zd_limit()
        self.set_mg_limit()
    self.after(10,self.check_update)
    return

class CatFrame(fg.FrameGUI):
  def __init__(self,root=None,col=0,row=0,colspan=1,rowspan=1,simMode=False,\
    thrd=None):
    fg.FrameGUI.__init__(self,root=root,name='Star Information',col=col,row=row,\
      colspan=colspan,rowspan=rowspan)
    self.starcatalogue=thrd
    self.location=self.starcatalogue.location
#   self.starcatalogue=srcthread.StarCatThread(catname=CAT_DIR+CAT_NAME,\
#     location=self.location)
    self.locGUI=LocationGUI(root=self.interior(),col=0,row=0,location=self.location)
    self.catGUI=CatalogGUI(root=self.interior(),col=1,row=0,location=self.location,\
      catalogue=self.starcatalogue)
    return
  def stopall(self):
    if not hasattr(self.root,'closeAll'):
      self.root.destroy()
    self.starcatalogue.stop()
    self.location.stop()
    #srcthread.progStat=False
    return
 
def stopProgs():
  ''' Will close the root window and kill all threads using the progStat variable '''
  global root,ggui
  if 'root' in globals():
    print 'Killing root GUI'
    root.destroy()
  ggui.starcatalogue.stop()
  ggui.location.stop()
  srcthread.progStat=False
  print 'Sucessfully exited'
  return

if __name__=='__main__':
  root=Tk()
  root.protocol('WM_DELETE_WINDOW',stopProgs)
# location=srcthread.LocationThread(lon=DIMLNG,lat=DIMLAT,elv=DIMELV)
# location.start()
  catalog_thread=srcthread.StarCatThread(log=False)
  ggui=CatFrame(root=root,col=0,row=1,thrd=catalog_thread)#location)
  xx=Button(root,text='Exit',font=fg.TEXT_FONT,command=stopProgs,\
    width=6,padx=0,pady=0)
  xx.grid(column=0,row=0,sticky='nw')
  root.mainloop()
