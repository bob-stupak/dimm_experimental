# Display webcam image, plus plasma diagnostics
# version 2, 2013-09-25
# Amar
# Changelog:
# v2: Very slight modification of http://matplotlib.org/examples/animation/dynamic_image.html
import sys
sys.path.append('..')
import numpy as np
import scipy.ndimage as ndimg
import cv2
import time
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import Pmw as pmw
try: import Tkinter as Tk
except ImportError: import tkinter as Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

import camera_supercircuits as camera
from common_parms import *

progStat=True

class FinderCameraGUI(FigureCanvasTkAgg):
  def __init__(self,root=None,camera=None,col=0,row=0,colspan=8,rowspan=4,imgdata=None):
    if camera==None:
      camera = CameraThread(channel=VIDEO_CHANNEL)
    self.camera=camera
    self.camera.start()
    self.col,self.row=col,row
    self.cspan,self.rspan=colspan,rowspan
    if root==None:
      root=Tk.Tk()
      root.protocol('WM_DELETE_WINDOW',stopProgs)
    ###self.root can be found by using self.get_tk_widget().master
    self.root=root
    self.group=pmw.Group(root,tag_text='USB Image Display:')
    self.group.component('tag').configure(font='Times -14')
    self.group.component('ring').configure(padx=10,pady=12)
    ###self.figure is inherited from FigureCanvasTkAgg
    self.figure=plt.Figure(figsize=(7.5,7.5),dpi=100)
    self.figure.set_animated(True)
    FigureCanvasTkAgg.__init__(self,self.figure,self.group.interior())
    self.grabimg=Tk.Button(self.group.interior(),text='Grab',font='Times -12',\
      command=self.grab_image,width=10,padx=0,pady=0)
    self.saveimg=Tk.Button(self.group.interior(),text='Save',font='Times -12',\
      command=self.save_image,width=10,padx=0,pady=0)
    self.canvas=self.get_tk_widget()
    self.splot1=self.figure.add_subplot(211)
    self.splot2=self.figure.add_subplot(212)
    self.maxLabel=Tk.Label(self.group.interior(),text='Max:',font='Times -12')
    self.minLabel=Tk.Label(self.group.interior(),text='Min:',font='Times -12')
    self.meanLabel=Tk.Label(self.group.interior(),text='Mean:',font='Times -12')
    self.grid(column=self.col,row=self.row,columnspan=self.cspan,rowspan=self.rspan,\
      sticky=Tk.W+Tk.E)
    self.camera.take_exposure_stat.set()
    self.camera.new_data_ready_stat.wait()
    self.video=self.splot1.imshow(self.camera.data[:,:,0],cmap='gray',animated=True)
    self.anim=animation.FuncAnimation(self.figure, self.updatefig, interval=80, blit=True)
    return
  def grid(self, **args):
    self.group.grid(args)
    self.canvas.grid(column=0,row=1,columnspan=self.cspan)
    self.grabimg.grid(column=0,row=0,sticky='nw')
    self.saveimg.grid(column=1,row=0,sticky='nw')
    self.maxLabel.grid(column=2,row=0,sticky='nw')
    self.minLabel.grid(column=3,row=0,sticky='nw')
    self.meanLabel.grid(column=4,row=0,sticky='nw')
    return
  def grab_image(self):
    data=self.camera.data
    self.splot2.clear()
    lvl=np.linspace(data.min(),data.max(),25)
    ymax,xmax,dmax=self.camera.data.shape
    mxpos,mnpos=ndimg.maximum_position(data),ndimg.minimum_position(data)
    self.splot2.contour(data[:,:,0],origin='upper',cmap='gray',levels=lvl)
    xxlimit,yylimit=self.splot2.get_xlim(),self.splot2.get_ylim()
    bxsize=50
    y1,x1=mnpos[0],mnpos[1]
    xo1,yo1=x1-bxsize/2.0,y1-bxsize/2.0
    y2,x2=mxpos[0],mxpos[1]
    xo2,yo2=x2-bxsize/2.0,y2-bxsize/2.0
    self.splot2.plot(x2,y2,marker='x',ms=10,mew=3,color='red')
    self.splot2.plot(x1,y1,marker='x',ms=10,mew=3,color='blue')
    rect1=Rectangle((xo1,yo1),bxsize,bxsize,fc='none',ec='blue',lw=3)
    rect2=Rectangle((xo2,yo2),bxsize,bxsize,fc='none',ec='red',lw=3)
    self.splot2.add_patch(rect1,)
    self.splot2.add_patch(rect2,)
    self.splot2.text(int(xmax/7),int(ymax*0.75),'Max: %7.3f(%7.3f,%7.3f)' % (self.camera.data.max(),\
      x2,y2),family='serif',fontsize=10,fontweight='bold',color='DarkRed')
    self.maxLabel.configure(text='Max: %7.3f(%7.3f,%7.3f)' % (self.camera.data.max(),x2,y2))
    self.splot2.text(int(xmax/7),int(ymax*0.75)-50,'Min: %7.3f(%7.3f,%7.3f)' % (self.camera.data.min(),\
      x1,y1),family='serif',fontsize=10,fontweight='bold',color='DarkRed')
    self.minLabel.configure(text='Min: %7.3f(%7.3f,%7.3f)' % (self.camera.data.min(),x1,y1))
    self.splot2.text(int(xmax/7),int(ymax*0.75)-100,'Mean: %7.3f' % (self.camera.data.mean()),family='serif',\
      fontsize=10,fontweight='bold',color='DarkRed')
    self.meanLabel.configure(text='Mean: %7.3f' % (self.camera.data.mean()))
    self.splot2.set_xlim(xxlimit)
    self.splot2.set_ylim(yylimit)
    self.canvas.update()
    self.draw()
    return
  def save_image(self):
    self.camera.save_image()
    return
  def updatefig(self,*args):
    self.camera.take_exposure()
    self.video.set_array(self.camera.data[:,:,0])
    return self.video,
  def stop(self):
    self.camera.close()
    self.root.destroy()
    return

def updatefig(*args):
  camera.take_exposure()
  im.set_array(camera.data[:,:,0])
  return im,

def stopProgs():
  camera.close()
  root.destroy()
  return

if __name__=='__main__':
  try:
    cindex=sys.argv.index('-ch')+1
    chan=sys.argv[cindex]
  except Exception:
    chan=0
  camera = camera.CameraThread(channel=int(chan))
  root=Tk.Tk()
# pmw.initialize(root)
  xx=Tk.Button(root,text='Exit',font='Times -10',command=stopProgs,\
    width=6,padx=0,pady=0)
  xx.grid(column=0,row=0,sticky='nw')
  figcanv=FinderCameraGUI(root=root,camera=camera,row=1,colspan=5)
  root.mainloop()
