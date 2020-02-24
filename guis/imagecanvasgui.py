#! /usr/bin/env python imagecanvasgui.py
#

import matplotlib
matplotlib.use('TkAgg')

import time
import Queue
import platform as pf
from numpy import *
from pylab import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.colors import Normalize,PowerNorm,LogNorm,SymLogNorm

from Tkinter import *
from Pmw import Group
import frame_gui as fg

try:
  if pf.linux_distribution()[0]=='debian':
    FIG_SIZE=(6.5,6.5)
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

class ImageCanvas(FigureCanvasTkAgg):
  def __init__(self,root=None,col=0,row=0,colspan=4,rowspan=4,imgdata=None):
    self.col,self.row=col,row
    self.cspan,self.rspan=colspan,rowspan
    if root==None:
      root=Tk()
      root.protocol('WM_DELETE_WINDOW',stopProgs)
    #if isinstance(root,Tk):
    #  root.title('Figure GUI')
    ###self.root can be found by using self.get_tk_widget().master
    self.root=root
    self.group=Group(root,tag_text='Image Display:')
    self.group.component('tag').configure(font=fg.TEXT_BBOLD)
    self.group.component('ring').configure(padx=10,pady=10)
    ###self.figure is inherited from FigureCanvasTkAgg
    self.figure=Figure(figsize=FIG_SIZE, dpi=100)
    self.figure.set_animated(True)
    self.figure.set_facecolor('#d9d9d9')
    FigureCanvasTkAgg.__init__(self,self.figure,self.group.interior())
    ###self._tkcanvas==self.get_tk_widget(), it is a tk canvas
    self.canvas=self.get_tk_widget()
    self.splot=self.figure.add_subplot(111)
#   self.splot.axis('off')
    self.imgaxis=None
    self.xlimits=self.splot.get_xlim()
    self.ylimits=self.splot.get_ylim()
#for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
#             ax.get_xticklabels() + ax.get_yticklabels()):
#    item.set_fontsize(20)
    self.data_queue=Queue.Queue()
    self.plot_ready_flag=True
    self.plot_count=0
    self.grid(column=self.col,row=self.row,columnspan=self.cspan,rowspan=self.rspan,\
      sticky=W+E)
    self.after_id=None
    self.check_update()
    return
  def grid(self, **args):
    self.group.grid(args)
    self.canvas.grid(column=0,row=0)
    return
  def clf(self):
    '''This method will clear the canvas '''
    self.figure.clf()
    self.splot=self.figure.add_subplot(111)
    self.splot.cla()
    self.imgaxis=None
    self.draw()
    return
  def set_scale(self,vmin=0.0,vmax=100000.0,cmap='gray'):
    # Where cmap can be 'gray','gray_r','jet','jet_r','autumn','Purples','hsv','hot','cool',etc
    if vmin>vmax: vmin=vmax
    if vmax<vmin: vmax=vmin
    self.imgaxis.set_clim(vmin=vmin)
    self.imgaxis.set_clim(vmax=vmax)
    self.imgaxis.set_cmap(cmap)
    self.draw()
    return
  def set_norm(self,norm):
    if norm=='n':
      self.imgaxis.set_norm(Normalize(vmin=0.0,vmax=100000.0))
    elif norm=='p':
      self.imgaxis.set_norm(PowerNorm(gamma=0.1))
    elif norm=='l':
      self.imgaxis.set_norm(LogNorm(vmin=1.0,vmax=100000.0))
    elif norm=='s':
      self.imgaxis.set_norm(SymLogNorm(linthresh=0.3,linscale=0.1,vmin=0.0,vmax=100000.0))
    else: pass
    self.draw()
    return
  def destroy(self):
    self.clear_queue()
    self.stop_update()
    self.group.destroy()
    self.canvas.destroy()
    return
  def stop_update(self):
    if self.after_id: self.canvas.after_cancel(self.after_id)
    else: pass
    return
  def change_image(self,imdata,title=None):
    self.plot_count+=1
    self.clear_labels()
    self.xlimits=(0,imdata.shape[1])
    self.ylimits=(0,imdata.shape[0])
    if len(self.splot.images)!=0:
      self.splot.images[0].set_data(imdata)
    else:
      #self.imgaxis=self.splot.imshow(imdata,origin='lower',cmap='gray',norm=PowerNorm(gamma=0.1),\
      #  vmin=imdata.min(),vmax=imdata.mean()*2.0,interpolation='none',animated=True)
      self.imgaxis=self.splot.imshow(imdata,origin='lower',cmap='gray',interpolation='none',animated=True)
    self.splot.set_xlim(self.xlimits)
    self.splot.set_ylim(self.ylimits)
    self.imgaxis.set_extent((self.xlimits[0],self.xlimits[1],self.ylimits[0],self.ylimits[1]))#####TEST
    self.imgaxis.set_clim(vmin=max(0,imdata.min()),vmax=imdata.mean())
    self.imgaxis.set_norm(PowerNorm(gamma=0.2))
    if title:
        self.splot.set_title('%s, %d, %s' % (time.strftime('%m/%d/%Y  %H:%M:%S'),self.plot_count,title),\
          family='serif',fontsize=10)
    else:
        self.splot.set_title('%s, Plot number:%d' % (time.strftime('%m/%d/%Y  %H:%M:%S'),self.plot_count),\
          family='serif',fontsize=10)
    return
  def plot_centers(self,centers,color='Red'):
    i=0
    #boxsize=50.0
    boxsize=0.033*self.xlimits[1]
    #color='red'
    self.clear_labels()
    try:
      # A cheap way to plot a point to be highlighted
      if centers[-1][0]<0: 
        coordcenter=centers[-1]*-1
        centers=centers[:-1]
        self.splot.plot(coordcenter[0],coordcenter[1],marker='x',ms=10,color='Green')
    except Exception: pass
    for xy in centers:
      try:
        self.splot.plot(xy[0],xy[1],marker='x',ms=10,color=color)
        x,y=xy[0]-boxsize/2.0,xy[1]-boxsize/2.0
        rect=Rectangle((x,y),boxsize,boxsize,fc='none',ec=color,lw=1)
        self.splot.add_patch(rect,)
        self.splot.text(x+boxsize,y+boxsize,str(i),color=color,fontsize=10)
        i+=1
      except Exception: pass #print 'NOT WORKING'
    try:
      if len(centers)>=2:
        self.splot.plot([centers[0][0],centers[1][0]],[centers[0][1],centers[1][1]],'-',color=color)
    except IndexError: pass
    except Exception: pass
    self.splot.set_xlim(self.xlimits)
    self.splot.set_ylim(self.ylimits)
    self.draw()
    return
  def plot_a_pnt(self,pnt,color='Green'):
    try:
      self.splot.plot(pnt[0],pnt[1],marker='x',ms=10,color=color)
    except Exception: pass #print 'NOT WORKING'
    self.splot.set_xlim(self.xlimits)
    self.splot.set_ylim(self.ylimits)
    self.draw()
    return
  def label_peaks(self,centers,color='Red'):
    i=0
    for each in centers:
      x,y=each[0],each[1]
      self.splot.plot(x,y,marker='x',ms=5,mew=2,color=color)
      self.splot.text(x,y,str(i),color=color,fontsize=10)
      i+=1
    self.splot.set_xlim(self.xlimits)
    self.splot.set_ylim(self.ylimits)
    self.draw()
    return
  def clear_labels(self):
    try:
      for i in range(len(self.splot.texts)):
        self.splot.texts.pop()
    except Exception: pass #print 'NOT WORKING'
    try:
      for i in range(len(self.splot.lines)):
        self.splot.lines.pop()
    except Exception: pass #print 'NOT WORKING'
    try:
      for i in range(len(self.splot.patches)):
        self.splot.patches.pop()
    except Exception: pass #print 'NOT WORKING'
    return
  def clear_queue(self):
    self.data_queue.queue.clear()
    return
  def check_update(self):
    if not self.data_queue.empty() and self.plot_ready_flag:
      self.plot_ready_flag=False
      image=self.data_queue.get()
      if type(image)==ndarray:
        self.change_image(image)
        #self.splot.set_title('%s' % (time.strftime('%m/%d/%Y  %H:%M:%S')),family='serif',fontsize=10)
        #self.draw()
      else:
        if image:
          self.change_image(image.data)
          #self.splot.set_title('%s, %s ' % (image.local_date,image.local_time),family='serif',fontsize=10)
          #self.draw()
          if hasattr(image,'centers'):
            if type(image.centers)==ndarray:
              if len(image.centers)>0:
                self.plot_centers(image.centers)
              else: pass
            else: pass
          else: pass
          #try: self.plot_centers(image.centers)
          #except Exception: print 'Exception in plotting image centers'
      self.draw()
      self.plot_ready_flag=True
    self.after_id=self.canvas.after(5,self.check_update)
    return

def stopProgs():
  return
