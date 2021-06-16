#! /usr/bin/env python frame_gui.py
###
###

from Tkinter import *
import Pmw as pmw
import platform as pf

EMPTYCMD='\'\''   #Use for <command> if no command is required in the configurations
try:
  if pf.linux_distribution()[0]=='debian':
    TEXT_FONT='Times -10'
    TEXT_LRG='Times -12'
    TEXT_BIG='Times -14'
    TEXT_BBOLD='Times -14 bold'
  else:
    TEXT_FONT='Times -14'
    TEXT_LRG='Times -16'
    TEXT_BIG='Times -18'
    TEXT_BBOLD='Times -18 bold'
except Exception:
  TEXT_FONT='Times -10'
  TEXT_LRG='Times -12'
  TEXT_BIG='Times -14'
  TEXT_BBOLD='Times -14 bold'

#To create a blank row or column use something like,
#>> blank1=Label(parent,text='',font=TEXT_FONT,width=9) # where <width> matches with of a button, say
#>> blank1.grid(column=col,row=row,columnspan=colspan,rowspan=rowspan,sticky='nsew')

class BlankSpace(Label):
  def __init__(self,root=None,col=0,row=0,colspan=1,rowspan=1):
    Label.__init__(self,root,text='',font=TEXT_FONT,width=9)
    self.grid(column=col,row=row,columnspan=colspan,rowspan=rowspan,sticky='nsew')
    return

class IndicatorButtons(LabelFrame):
  def __init__(self,root=None,frame_name='Indicators',items=[]):
    self.root=root
    self.frame_name=frame_name
    if self.frame_name:  self.frame_name=self.frame_name+':'
    LabelFrame.__init__(self,root)
    self.number=len(items)
    self.items_list=items
    self.button_list=[]
    self.vars_list=[]
    [self.vars_list.append(StringVar()) for i in range(self.number)]
    self.configure_frame()
    self.configure_indicators()
    self.grid()
    return
  def configure_frame(self):
    self.config(relief=GROOVE,width=28,bd=1,padx=0,pady=1)
    self.config(text=self.frame_name,font=TEXT_BBOLD)
    return
  def configure_indicators(self):
    for i in range(self.number):
      self.button_list.append(Checkbutton(self,text=self.items_list[i],font=TEXT_FONT,\
        variable=self.vars_list[i],onvalue=True,offvalue=False,command=eval('lambda x=self: x.set_value('+str(i)+')')))
      self.button_list[i].configure(selectcolor='gray75')
      self.button_list[i].pack(side=TOP,anchor=W,padx=0,pady=0)
      self.vars_list[i].set(False)
    return
  def set_indicator(self,item_name,value):
    index=self.items_list.index(item_name)
    if type(value)==bool or (type(value)==int and (value==0 or value==1)):
      self.vars_list[index].set(value)
      if value: self.button_list[index].configure(selectcolor='SpringGreen2')
      else: self.button_list[index].configure(selectcolor='firebrick2')  # or red2
    #elif type(value)==int and value==-1:
    else:
      self.vars_list[index].set(False)
      self.button_list[index].configure(selectcolor='gray75')
    return
  def set_value(self,index):
    value=int(self.vars_list[index].get())
    self.set_indicator(self.items_list[index],bool(value))
    return

class MessageFrame(LabelFrame):
  def __init__(self,root=None,frame_name='Messages',items=[]):
    self.root=root
    self.frame_name=frame_name
    if self.frame_name:  self.frame_name=self.frame_name+':'
    LabelFrame.__init__(self,root)
    self.items_list=items
    self.message_list=[]
    self.configure_frame()
    self.configure_messages()
    self.grid()
    return
  def configure_frame(self):
    self.config(relief=GROOVE,width=28,bd=1,padx=0,pady=1)
    self.config(text=self.frame_name,font=TEXT_BBOLD)
    return
  def configure_messages(self):
    # Where <name> is the label_text replacing spaces with '_' and all lowercase
    # For example,  label_text='Message 1 2', name='message_1_2'
    for each in self.items_list:
      name=each.replace(' ','_').lower()
      self.__dict__[name]=pmw.MessageBar(self,entry_width=20,\
        entry_relief='groove',labelpos='w',label_text=each+':')
      self.__dict__[name].component('label').configure(font=TEXT_FONT)
      self.__dict__[name].component('label').configure(width=20)
      self.__dict__[name].component('label').configure(anchor='w')
      self.__dict__[name].component('entry').configure(font=TEXT_FONT)
      self.__dict__[name].pack(side=TOP,anchor=W,padx=0,pady=0)
    return
  def set_message(self,tag,value):
    # Where <tag> is the label_text replacing spaces with '_' and all lowercase
    # For example,  label_text='Message 1 2', tag='message_1_2'
    if type(value)==str: formatted_value='%s' % value
    elif type(value)==float: formatted_value='%10.3f' % value
    else: formatted_value='%r' % value
    #self.__dict__[tag].resetmessages('state')  # Added to see if this will prevent the gui slowing down...
    try:
      self.__dict__[tag].message('state', formatted_value)
      self.__dict__[tag].component('label').update()
    except Exception as err:
      pass
    return

class ButtonFrame(LabelFrame):
  def __init__(self,root=None,frame_name='Button Frame',items=[]):
    if root: self.root=root
    else: self.root=Tk()
    LabelFrame.__init__(self,self.root)
    if frame_name: self.frame_name=frame_name+':'
    else: self.frame_name=''
    self._buttons=items
    self._button_list=[]
    self.configFrame()
    self.configButtons()
    self.grid()
    return
  def configFrame(self):
    self.config(relief=GROOVE,width=30,bd=1,padx=3,pady=1)
    self.config(text=self.frame_name,font=TEXT_BBOLD)
    return
  def configButtons(self):
    for each in self._buttons:
      name=each[0].replace(' ','_').lower()
      self._button_list.append(name)
      self.__dict__[name]=Button(self,text=each[0],font=TEXT_FONT,width=25,padx=0,pady=0)
        #command=eval(each[1]),width=15,padx=0,pady=0)
      self.__dict__[name].pack(side=TOP,anchor=W)
    return

class SingleEntry(Frame):
  def __init__(self,root=None,label_name='Entry'):
    self.root=root
    Frame.__init__(self,root)
    self.text_label=Label(self,text=label_name+':',font=TEXT_FONT,width=15)
    self.text_entry=Entry(self,width=10,font=TEXT_FONT)
    self.variable=None
    self.configFrame()
    self.gridSelf()
  def gridSelf(self):
    self.text_label.pack(side=LEFT,anchor=W)
    self.text_entry.pack(side=LEFT,anchor=W)
    return
  def configFrame(self):
    self.text_label.bind('<Double-Button-1>',self.toggle_state)
    self.text_label.config(fg='Black')
    self.text_entry.bind('<KeyPress-Return>',lambda x:self.set_entry(self.get_entry()))
    self.text_entry.bind('<KeyPress-Tab>',lambda x:self.set_entry(self.get_entry()))
    self.on=True
  def get_entry(self):
    return self.text_entry.get()
  def set_entry(self,entry):
    self.text_entry.delete(0,END)
    self.text_entry.insert(END,entry)
    self.variable=self.get_entry()
    return
  def toggle_state(self,event):
    if self.text_label['foreground']=='Black':
      self.text_label.config(foreground='Red')
      self.text_entry.config(state='disabled',disabledforeground='gray60')
      self.on=False
    else:
      self.text_label.config(foreground='Black')
      self.text_entry.config(state='normal')
      self.on=True
    return

class MultiSingleEntry(LabelFrame):
  def __init__(self,root=None,frame_name='Multi-Entry',items=[]):
    if root: self.root=root
    else: self.root=Tk()
    LabelFrame.__init__(self,self.root)
    if frame_name: self.frame_name=frame_name+':'
    else: self.frame_name=''
    self._entries=items
    self._entry_list=[]
    self.configFrame()
    self.configEntries()
    return
  def configFrame(self):
    self.config(relief=GROOVE,width=28,bd=1,padx=0,pady=1)
    self.config(text=self.frame_name,font=TEXT_BBOLD)
    return
  def configEntries(self):
    for each in self._entries:
      name=each.replace(' ','_').lower()
      self._entry_list.append(name)
      self.__dict__[name]=SingleEntry(root=self,label_name=each)
      self.__dict__[name].pack(side=TOP,fill=X)
    return

class ListBox(LabelFrame):
  def __init__(self,root=None,title=''):
    LabelFrame.__init__(self,root)
    self.scrollbar=Scrollbar(self,orient=VERTICAL)
#   self.listbox=Listbox(self,width=60,height=10, \
#     font=TEXT_FONT ,yscrollcommand=self.scrollbar.set)
    self.listbox=Text(self,width=60,height=10,wrap=WORD, \
      font=TEXT_FONT ,yscrollcommand=self.scrollbar.set)
    self.configSelf(title)
    self.gridSelf()
    return
  def configSelf(self,title):
    self.config(font=TEXT_BBOLD,padx=1,pady=1,relief=GROOVE)
    self.config(text=title)
    self.scrollbar.config(command=self.listbox.yview)
    return
  def gridSelf(self):
    self.listbox.pack(side=LEFT,fill=Y,expand=TRUE)
    self.scrollbar.pack(side=LEFT,fill=Y,expand=TRUE)
    return
  def actOnSelected(self,event):
    #[self.listbox.itemconfig(x,fg='Black') for x in \
    #  range(self.listbox.size())]
    #curSel=self.listbox.curselection()
    #self.fileList=[self.listbox.get(each) for each in curSel]
    #[self.listbox.itemconfig(x,fg='Blue') for x in curSel]
    return

class EntryMessage(pmw.Group):
  def __init__(self,root=None,roottitle='',title='',col=0,row=0,colspan=1,rowspan=1):
    self.col,self.row=col,row  # GUI row and column in Tk root frame
    self.colspan,self.rowspan=colspan,rowspan  # GUI row and column spans in Tk root frame
    pmw.Group.__init__(self,root,tag_text=title+':')
    self.entries=0
    self.configSelf()
    self.gridSelf()
    return
  def configSelf(self):
    self.component('tag').configure(font=TEXT_BBOLD)
    self.component('ring').configure(padx=7,pady=7)
    return
  def gridSelf(self):
    self.grid(column=self.col,row=self.row,columnspan=self.colspan,\
      rowspan=self.rowspan,sticky='nsew')
    return
  def regridSelf(self):
    self.configSelf()
    self.gridSelf()
    return
  def createEntry(self,name='line',label='Label:',text='Return Message'):
    self.__dict__[name+'C']=pmw.EntryField(self.interior(),labelpos='w',label_text=label,\
      validate=None)
    self.__dict__[name+'L']=Label(self.interior(),text=text,justify=LEFT,\
      wraplength=100,width=50)
    self.__dict__[name+'C'].component('entry').configure(font=TEXT_FONT)
    self.__dict__[name+'C'].component('label').configure(font=TEXT_FONT)
    self.__dict__[name+'C'].component('entry').configure(width=20)
    self.__dict__[name+'C'].component('label').configure(width=20)
    #self.__dict__[name+'C'].component('entry').bind('<KeyPress-Return>',\
    #  lambda x:self.set_labels(name=name,text=self.get_entry(name)))
    #self.__dict__[name+'C'].component('entry').bind('<KeyPress-Tab>',\
    #  lambda x:self.set_labels(name=name,text=self.get_entry(name)))
    self.__dict__[name+'L'].configure(width=20)
    self.__dict__[name+'L'].configure(font=TEXT_FONT,relief='sunken',bd=1)
    self.__dict__[name+'C'].grid(column=0,row=self.entries,columnspan=1,sticky='nsew')
    self.__dict__[name+'L'].grid(column=1,row=self.entries,columnspan=1,sticky='nsew')
    self.entries+=1
    return
  def set_labels(self,name='line1',text=''):
    self.__dict__[name+'L'].configure(text=text)
    return
  def get_labels(self,name='line1'):
    txt=self.__dict__[name+'L']['text']
    return txt
  def set_entry(self,name='line1',text=''):
    self.__dict__[name+'C'].setvalue(text)
    return
  def get_entry(self,name='line1'):
    txt=self.__dict__[name+'C'].getvalue()
    return txt

class SelectDialog(pmw.SelectionDialog):
  def __init__(self,parent=None,title='Selection',command=None,select_items=[]):
    if parent:
      if hasattr(parent,'interior'): self.root=parent.interior()
      else: self.root=parent
    else: self.root=Tk()
    self.select_items=select_items
    if command: command=command
    else: command=self.change_selection_dialog
    pmw.SelectionDialog.__init__(self,self.root,
      title = title,
      buttons = ('OK', 'Cancel'),
      defaultbutton = 'OK',
      scrolledlist_labelpos = 'n',
      label_text = 'Selection Dialog',
      scrolledlist_items = select_items,
      command = command)
    [each.configure(font=TEXT_FONT) for each in \
      self.component('buttonbox').component('hull').children.values()]
    self.component('scrolledlist').component('listbox').configure(font=TEXT_FONT)
    self.component('label').configure(font=TEXT_LRG)
    self.dialogentry=SingleEntry(self.component('dialogchildsite'),label_name='Entry')
    self.dialogentry.pack(side=TOP,fill=X,anchor=W)
    self.check_string='+'
    self.update_dialog()
    return
  def change_selection_dialog(self, result):
    sels = self.getcurselection()
    self.withdraw()
    self.deactivate(result)
    self.after_cancel(self.update_id)
    return
  def update_dialog(self):
    nn=self.dialogentry.get_entry()
    if nn!=self.check_string and self.check_string!='+':
      tmp=list(self.component('scrolledlist').get())
      rr=[each for each in tmp if nn in each]
      self.component('scrolledlist').setlist(rr)
    if nn=='' and self.check_string!='':
      self.component('scrolledlist').setlist([each for each in self.select_items])
      self.check_string='+'
    self.check_string=nn
    self.update_id=self.after(1,self.update_dialog)
    return
  def self_destroy(self,result):
    self.withdraw()
    self.deactivate(result)
    self.after_cancel(self.update_id)
    self.destroy()
    return

class FrameGUI(pmw.Group):
  '''
  '''
  __module__='frame_gui'
  def __init__(self,root=None,roottitle='',name='',col=0,row=0,colspan=1,rowspan=1):
    self.col,self.row=col,row  # GUI row and column in Tk root frame
    self.colspan,self.rowspan=colspan,rowspan  # GUI row and column spans in Tk root frame
    if root==None: 
      root=Tk()
      root.protocol('WM_DELETE_WINDOW',stopProgs)
    if roottitle=='':
      if not isinstance(root,Frame):
        root.title(root.title())
      else: pass
    else:
      root.title(root.title())
    if isinstance(root,Tk):
      root.configure(width=500,height=500)
    self.root=root
    pmw.Group.__init__(self,self.root,tag_text=name+':',\
      hull_width=500,hull_height=500)
    self.component('tag').configure(font=TEXT_BBOLD)
    self.component('ring').configure(padx=7,pady=7)
    ## the following lists are the configuration of the message and button guis
    ## message frame gui: [<name>,<frame_name>,[items list],(col,row,cspan,rspan,sticky)]
    ## message gui: [<name>,<text label>,<entry_width>,(col,row,cspan,rspan,sticky)]
    ## button gui:  [<name>,<text label>,<command>,(col,row,cspan,rspan,sticky)]
    ## button frame gui:  [<name>,<frame name>,[items list],(col,row,cspan,rspan,sticky)]
    ##            where [items list] is [[<button label 1>,<command 1>],....]
    ## option menu gui: [<name>,<text label>,<default item>,<Menu item list>,<command>,
    ##                  (col,row,cspan,rspan,sticky)]
    ## ---Note the option menu variable is self.<name>.var
    ##
    ## entry gui: [<name>,<value>,<validate>,<command>,<width>,
    ##            (col,row,cspan,rspan,sticky)]
    ## check/radio gui: [<name>,<text label>,<orient>,<type>,<checkList>,<command>,
    ##            (col,row,cspan,rspan,sticky)]
    ## entry/message gui: [<name>,<label>,[entry list],(col,row,cspan,rowspan,sticky)]
    ##            where [entry list]  is a list of lists, as an example
    ##                  [[name1,label1,text1],[name2,label2,text2],...]
    ## indicator buttons gui: [<name>,<frame name>,[items list],(col,row,cspan,rspan,sticky)]
    ## entry frame gui: [<name>,<frame name>,[items list],(col,row,cspan,rspan,sticky)]
    ## listbox gui: [<name>,<text label>,<command>,(col,row,cspan,rspan,sticky)]
    if not hasattr(self,'_mesFrameList'):
      self._mesFrameList=[]
    if not hasattr(self,'_mesBarList'):
      self._mesBarList=[]
    if not hasattr(self,'_buttonList'):
      self._buttonList=[]
    if not hasattr(self,'_butFrameList'):
      self._butFrameList=[]
    if not hasattr(self,'_optionList'):
      self._optionList=[]
    if not hasattr(self,'_entryList'):
      self._entryList=[]
    if not hasattr(self,'_entryframeList'):
      self._entryframeList=[]
    if not hasattr(self,'_checkList'):
      self._checkList=[]
    if not hasattr(self,'_emessList'):
      self._emessList=[]
    if not hasattr(self,'_indicatorList'):
      self._indicatorList=[]
    if not hasattr(self,'_listboxList'):
      self._listboxList=[]
    self.configFrame()
    self.gridSelf()
    self.after_id=None
#   self.check_update()
    return
  def configFrame(self):
    if len(self._mesFrameList)>0:
      for each in self._mesFrameList:
        self.__dict__[each[0]]=MessageFrame(root=self.interior(),frame_name=each[1],items=each[2])
    if len(self._mesBarList)>0:
      for each in self._mesBarList:
        self.__dict__[each[0]]=pmw.MessageBar(self.interior(),entry_width=each[2],\
          entry_relief='groove',labelpos='w',label_text=each[1]+':')
        self.__dict__[each[0]].component('label').configure(font=TEXT_FONT)
        self.__dict__[each[0]].component('label').configure(width=each[2])
        self.__dict__[each[0]].component('entry').configure(font=TEXT_FONT)
    if len(self._buttonList)>0:
      for each in self._buttonList:
        self.__dict__[each[0]]=Button(self.interior(),text=each[1],font=TEXT_FONT,\
          command=eval(each[2]),width=9,padx=0,pady=0)
    if len(self._butFrameList)>0:
      for each in self._butFrameList:
        self.__dict__[each[0]]=ButtonFrame(root=self.interior(),frame_name=each[1],items=each[2])
        for every in each[2]:
          name=every[0].replace(' ','_').lower()
          self.__dict__[each[0]].__dict__[name].configure(command=eval(every[1]))
    if len(self._optionList)>0:
      for each in self._optionList:
        self.__dict__[each[0]]=pmw.OptionMenu(self.interior(),labelpos='w',\
          label_text=each[1]+':',menubutton_width=7,command=each[4])
        self.__dict__[each[0]].var=StringVar()
        self.__dict__[each[0]].var.set(each[2])
        self.__dict__[each[0]].component('menubutton').configure(textvariable=\
          self.__dict__[each[0]].var)
        self.__dict__[each[0]].setitems(each[3])
        self.__dict__[each[0]].component('label').configure(font=TEXT_FONT)
        self.__dict__[each[0]].component('label').configure(width=15,height=1,\
          padx=0,pady=0)
        self.__dict__[each[0]].component('menubutton').configure(font=TEXT_FONT)
        self.__dict__[each[0]].component('menubutton').configure(width=15,height=1,\
          padx=0,pady=0)
        self.__dict__[each[0]].component('menu').configure(font=TEXT_FONT)
    if len(self._entryList)>0:
      for each in self._entryList:
        self.__dict__[each[0]]=pmw.EntryField(self.interior(),\
          labelpos='w',label_text=each[1]+':',value=each[2],\
          validate=each[3],command=each[4])
        self.__dict__[each[0]].var=StringVar()
        self.__dict__[each[0]].var.set(each[2])
        self.__dict__[each[0]].component('label').configure(font=TEXT_FONT)
        self.__dict__[each[0]].component('label').configure(width=each[5])
        self.__dict__[each[0]].component('entry').configure(font=TEXT_FONT)
        self.__dict__[each[0]].component('entry').configure(width=each[5])
    if len(self._checkList)>0:
      for each in self._checkList:
        self.__dict__[each[0]]=pmw.RadioSelect(self.interior(),\
          label_text=each[1]+':',orient=each[2],buttontype=each[3],\
          command=each[5],hull_borderwidth=1,hull_relief='ridge',labelpos='w',\
          padx=0,pady=0)
        self.__dict__[each[0]].component('hull').configure(relief='flat')
        self.__dict__[each[0]].component('label').configure(font=TEXT_FONT)
        for every in each[4]:
          self.__dict__[each[0]].add(every)
          self.__dict__[each[0]].component(every).configure(font=TEXT_FONT)
    if len(self._emessList)>0:
      for each in self._emessList:
        self.__dict__[each[0]]=EntryMessage(self.interior(),title=each[1],\
          col=each[-1][0],row=each[-1][1],colspan=each[-1][2],rowspan=each[-1][3])
        #self.__dict__[each[0]].component('label').configure(font=TEXT_FONT)
        for every in each[2]:
          self.__dict__[each[0]].createEntry(name=every[0],label=every[1]+':',\
            text=every[2])
    if len(self._entryframeList)>0:
      for each in self._entryframeList:
        self.__dict__[each[0]]=MultiSingleEntry(root=self.interior(),items=each[2],frame_name=each[1])
    if len(self._indicatorList)>0:
      for each in self._indicatorList:
        self.__dict__[each[0]]=IndicatorButtons(root=self.interior(),items=each[2],frame_name=each[1])
    if len(self._listboxList)>0:
      for each in self._listboxList:
        self.__dict__[each[0]]=ListBox(root=self.interior(),title=each[1])
    return
  def gridSelf(self):
    for each in self._mesFrameList+self._mesBarList+self._buttonList+self._butFrameList+\
        self._optionList+self._entryList+self._entryframeList+self._checkList+\
        self._indicatorList+self._listboxList:
      self.__dict__[each[0]].grid(column=each[-1][0],row=each[-1][1],\
        columnspan=each[-1][2],rowspan=each[-1][3],sticky=each[-1][4])
    self.grid(column=self.col,row=self.row,columnspan=self.colspan,\
      rowspan=self.rowspan,sticky='nsew')
    return
  def regridSelf(self):
    self.configFrame()
    self.gridSelf()
    return
  def check_update(self):
    self.after_id=self.after(1,self.check_update)
    return
  def stop_update(self):
    if self.after_id: self.after_cancel(self.after_id)
    else: pass
    return
# def close_frame(self):
#   self.stop_update()
#   self.destroy()
#   return
if __name__=='__main__':
  root=Tk()
  #root.protocol('WM_DELETE_WINDOW',stopProgs)  #NOT NEEDED in this main
  xx=Button(root,text='Exit',font=TEXT_FONT,command=sys.exit,\
    width=6,padx=0,pady=0)
  xx.grid(column=0,row=0,sticky='nw')
  mymm=FrameGUI(root=root,roottitle='Test FrameGUI.py',name='Test GUIs',row=1)
  mymm._mesFrameList=[['frames1','MessageFrame 1',['Message 1','Message 2','Message 3'],(0,20,3,1,'nsew')],\
                      ['frames2','MessageFrame 2',['Message A','Message B','Message C'],(4,20,3,1,'nsew')]]
  mymm._mesBarList=[['mesbar1','Message 1',10,(0,1,3,1,'nsew')],\
                        ['mesbar2','Message 2',10,(0,2,3,1,'nsew')],\
                        ['mesbar3','Message 3',10,(0,3,3,1,'nsew')],\
                        ['mesbar4','Message 4',20,(0,4,3,1,'nsew')]]
  mymm._entryList=[['entry1','Entry 1','',{'validator':'alphanumeric'},\
    None,10,(0,5,3,1,'nsew')]]
  mymm._buttonList=[['button1','Button 1',\
                  EMPTYCMD,(1,6,1,1,'nsew')],\
                  ['button2','Button 2',\
                  EMPTYCMD,(0,7,1,1,'nsew')],\
                  ['button3','Button 3',\
                  EMPTYCMD,(2,7,1,1,'nsew')]]
  mymm._butFrameList=[['buttons1','Button 1',[['Test Button 1',EMPTYCMD],['Test Button 2',EMPTYCMD]],\
                      (0,25,1,1,'nsew')],['buttons2','Button 2',[['Test Button A',EMPTYCMD],\
                      ['Test Button B',EMPTYCMD]],(4,25,1,1,'nsew')]]
  mymm._optionList=[['option1','Options','a',['a','b','c','d','e'],None,(0,8,2,1,'nsew')]]
  mymm._checkList=[['check1','Check List','horizontal','checkbutton',['1','2','3','4'],None,\
                    (0,9,3,1,'nsew')]]
  mymm._indicatorList=[['indbuttons1','Indicators',['Indicator 1','Indicator 2','Indicator 3'],(4,10,3,1,'nsew')],\
                       ['indbuttons2','Other Indicators',['Event 1','Event 2','Event 3'],(4,11,3,1,'nsew')]]
  mymm._listboxList=[['listbox','Listbox test',(4,0,4,10,'nsew')]]
  mymm._emessList=[['emess1','EntryMessage',[['entrymess1','Entry 1','Message'],\
    ['entrymess2','Entry 2','Message 2']],(0,10,3,1,'nsew')]]
  mymm._entryframeList=[['multientry1','Entries A-C',['Entry A','Entry B','Entry C'],(0,11,2,1,'nsew')],\
                        ['multientry2','Entries 1-4',['Entry 1','Entry 2','Entry 3','Entry 4'],(2,11,1,1,'nsew')]]
  mymm.regridSelf()
  root.mainloop()
