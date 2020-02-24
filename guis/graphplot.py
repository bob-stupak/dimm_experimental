#!/usr/bin/env python graphplot.py

import matplotlib
matplotlib.use('TkAgg')

import time
import Queue
import platform as pf
import sys
from numpy import *
from pylab import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import *

from Tkinter import *
from Pmw import Group
import frame_gui as fg

try:
  if pf.linux_distribution()[0]=='debian':
    FIG_SIZE=(5.5,5.5)
  else:
    FIG_SIZE=(7.5,7.5)
except Exception:
  FIG_SIZE=(5.5,5.5)
FONTS = {'font.family':'serif',
         'legend.fontsize': 'small',
         'figure.figsize': (7.5,7.5),
         'axes.labelsize': 'small',
         'axes.titlesize':'small',
         'xtick.labelsize':'small',
         'ytick.labelsize':'small'}

matplotlib.pylab.rcParams.update(FONTS)

class FigCanvas(FigureCanvasTkAgg):
  def __init__(self,root=None,col=0,row=0,colspan=4,rowspan=4,polar=False):
    self.col,self.row=col,row
    self.cspan,self.rspan=colspan,rowspan
    if root==None:
      root=Tk()
      root.protocol('WM_DELETE_WINDOW',stopProgs)
#     if isinstance(root,Tk):
#       root.title('Figure GUI')
    ###self.root can be found by using self.get_tk_widget().master
    self.root=root 
    self.group=Group(root,tag_text='Plot Display:')
    self.group.component('tag').configure(font=fg.TEXT_BBOLD)
    self.group.component('ring').configure(padx=10,pady=10)
    ###self.figure is inherited from FigureCanvasTkAgg
    self.figure=Figure(figsize=FIG_SIZE, dpi=100)
    self.figure.set_animated(True)
    self.figure.set_facecolor('#d9d9d9')
    FigureCanvasTkAgg.__init__(self,self.figure,self.group.interior())
    ###self._tkcanvas==self.get_tk_widget(), it is a tk canvas
    self.canvas=self.get_tk_widget()
    ### self.splots and self.splotconfig are list of subplots and geomet
    self.splots=[]
    self.splotconfig=['111']
    self.lineprops=lineprops()
    self.addSubplot(polar=polar)
    self.plot_ready_flag=True
    self.data_queue=Queue.Queue()
    self.grid(column=self.col,row=self.row,columnspan=self.cspan,rowspan=self.rspan,\
      sticky=W+E)
    self.after_id=None
    self.check_update()
    return
  def grid(self, **args):
    self.group.grid(args)
    self.canvas.grid(column=0,row=0)
    return
  def winfo_id(self):
    self.canvas.winfo_id()
    return
  def clf(self):
    '''This method will clear the canvas '''
    self.figure.clf()
    self.splots=[]
    self.splotconfig='111'
    self.draw()
    return
  def destroy(self):
    self.clear_queue()
    self.stop_update()
    self.group.destroy()
    self.canvas.destroy()
    try: self.root.destroy()
    except Exception: pass
    return
  def stop_update(self):
    if self.after_id: self.canvas.after_cancel(self.after_id)
    else: pass
    return
  def clear_queue(self):
    self.data_queue.queue.clear()
    return
  def get_data(self,plot=0,line=0):
    return self.splots[plot].lines[line].get_data()
  def addSubplot(self,polar=False):
    ### Calculate the number of plots and locations
    ### store these in self.splotconfig list
    num=len(self.splots)
    if num!=0:
      if num<3:
        tmpconfig=str(num+1)+str(1)+'x'
      else:
        a=int(num/2)
        tmpconfig=str(a+1)+str(2)+'x'
    else:
      tmpconfig='11x'
    self.splotconfig=[tmpconfig.replace('x',str(i+1)) for i in range(num+1)]
    self.splots.append(self.figure.add_subplot(self.splotconfig[-1],polar=polar,autoscale_on=True))
    ### The next line will assign an attribute name to the splots listed
    self.__dict__['splot'+str(num+1)]=self.splots[-1]
    self.splots[-1].grid(True)
    ### The following rearranges the existing subplots using the self.splotconfig list
    for i in range(num):
      rows,columns,number=int(self.splotconfig[i][0]),int(self.splotconfig[i][1]),\
        int(self.splotconfig[i][2])
      self.splots[i].axes.change_geometry(rows,columns,number)
    ######## For setting up the title, xlabel, etc....
    ###self.splots[-1].set_title('Tk embedding',fontsize=10)
    ###self.splots[-1].set_xlabel('X axis label',fontsize=8)
    ###self.splots[-1].set_ylabel('Y label',fontsize=8)
    self.draw()
    return 
  def plotdata(self,subplt,xdata,ydata,**kargs):
    self.lineprops.set(**kargs)
    subplt.plot(xdata,ydata,color=self.lineprops.color,ls=self.lineprops.ls,\
      marker=self.lineprops.marker,ms=self.lineprops.ms,lw=self.lineprops.lw)
    subplt.set_xlim(xdata.min(),xdata.max())
    subplt.set_ylim(ydata.min(),ydata.max())
    subplt.grid(True)
    self.draw()
    return
  def clearlastline(self,subplt):
    if len(subplt.lines)>0:
      subplt.lines.pop(-1)
    self.draw()
    return
  def addpoints(self,subplt,x,y,**kargs):
    self.lineprops.set(**kargs)
    ### to ensure that a marker is set for points
    if self.lineprops.marker=='':
      self.lineprops.marker='o'
      self.lineprops.ms=0.5
    try:  x,y=float(x),float(y)
    except Exception: pass
    line=Line2D([],[],color=self.lineprops.color,ls=self.lineprops.ls,\
      marker=self.lineprops.marker,ms=self.lineprops.ms,lw=self.lineprops.lw)
    if len(subplt.lines)>0:
      xx=array(subplt.lines[-1].get_data())
      subplt.lines.pop()
      if type(x)==ndarray and type(y)==ndarray:
        new=concatenate((xx,array([x,y])),axis=1)
      elif type(x)==float and type(y)==float:
        new=array([append(xx[0],x),append(xx[1],y)])
      else:
        pass
      line.set_data(new[0],new[1])
    else:
      line.set_data(array([x,y]))
    subplt.add_line(line)
    new=array(subplt.lines[-1].get_data())
    subplt.set_xlim(new[0].min(),new[0].max())
    subplt.set_ylim(new[1].min(),new[1].max())
    subplt.grid(True)
    self.draw()
    return
  def check_update(self):
    self.after_id=self.canvas.after(5,self.check_update)
    return

class lineprops:
  '''
    CLASS lineprops
      A class used to set up line properties for plots
      This class can be added to for more line prop 
      attributes.
  '''
  def __init__(self):
    self.color='Black'
    self.ls='-'
    self.marker=''
    self.ms=1.0
    self.lw=1.0
    return
  def set(self,**kargs):
    if 'color' in kargs: self.color=kargs.pop('color')
    else: pass
    if 'ls' in kargs: self.ls=kargs.pop('ls')
    else: pass
    if 'marker' in kargs: self.marker=kargs.pop('marker')
    else: pass
    if 'ms' in kargs: self.ms=kargs.pop('ms')
    else: pass
    if 'lw' in kargs: self.lw=kargs.pop('lw')
    else: pass
    return
  def __repr__(self):
    s=''
    for each in self.__dict__:
      s=s+str(each)+':'+str(self.__dict__[each])+'\n'
    return s
  def __setitem__(self,item,element):
    if item in self.__dict__: self.__dict__[item]=element
    else: pass
    return
  def __getitem__(self,item):
    return self.__dict__[item]

def stopProgs():
  return
###
### Usage
###
#>>> x=arange(0.1,4.0*pi,0.01)
#>>> y=x**-.5*cos(x)
#>>> reload(tfg);del root,canv
#>>> root=tk.Tk();canv=tfg.FigCanvas(master=root)
#>>> canv.addpoints(canv.splots[0],0.0,0.0)
#>>> canv.addSubplot()
#>>> canv.plotdata(canv.splots[1],x,y,color='DarkRed')
#>>> canv.addSubplot()
#>>> canv.plotdata(canv.splots[-1],x,y,color='Purple')
#>>> canv.addSubplot()
#>>> canv.plotdata(canv.splots[-1],x,y,color='DarkGreen')
#>>> canv.addpoints(canv.splots[0],1.1,5.3,color='Red')
#>>> canv.addpoints(canv.splots[0],2.1,10.3,color='Green')
#>>> canv.splots[0].set_xlim(0.0,10.0);canv.draw()
#>>> canv.splots[0].set_ylim(0.0,20.0);canv.draw()
#>>> canv.splots[0].set_xlabel('X axis');canv.splots[0].set_ylabel('Y axis')
#>>> canv.draw()
if __name__=='__main__':
  import frame_gui as fg
  from Tkinter import *
  import sys
  root=Tk()
  xx=Button(root,text='Exit',font='Times -10',command=sys.exit,\
    width=6,padx=0,pady=0)
  xx.grid(column=0,row=0,sticky='nw')
  fgui=fg.FrameGUI(root=root,name='Testing',col=0,row=1)
  ggui=FigCanvas(root=fgui.interior())
# ggui.addSubplot()
  root.mainloop()
