#!/usr/bin/env python notebook.py
#
__all__=['AppNoteBook']
from Tkinter import *
import Pmw as pmw
import platform as pf
from matplotlib import rc

class AppNoteBook(pmw.NoteBook):
  def __init__(self,*args,**parms):
    if len(args)!=0: self.master=args[0]
    else: self.master=Tk()
    self._pageList=['Measurements','Process','Device']
    self._number=1
    pmw.NoteBook.__init__(self,self.master,hull_width=1300,hull_height=600)
    self.configNoteBook()
    return
  def configNoteBook(self):
    for each in self._pageList:
      dName='page'+str(self._number)
      self.__dict__[dName]=self.add(each)
      self.tab(each).focus_set()
      self.component(each+'-tab').configure(font=\
        pmw.logicalfont('Times',size=8))
      self._number=self._number+1
    return

if __name__=='__main__':
  if pf.system()=='Linux':
    rc('text',usetex=True)
    rc('font',**{'family':'serif','serif':['Times']})
  else:
    rcParams['font.family']='serif'
    ion()
    show()
  mm=Tk()
  yy=AppNoteBook(mm)
  xx=Button(mm,text='Exit',font='Times -10',command=sys.exit,\
    width=6,padx=0,pady=0)
  xx.grid(column=0,row=0,sticky='nw')
  mm.mainloop()
