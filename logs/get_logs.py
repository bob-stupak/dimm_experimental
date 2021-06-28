#/usr/bin/env python get_logs.py
#
'''Usage:
     python get_logs.py -mon 3 -day 3 -year 2017
'''
from pylab import *
from numpy import *
import scipy
import scipy.stats
import ephem
import time
import datetime
import sys
import re
import os.path
import pylab as plt

import matplotlib.dates as mdates
from matplotlib import rc
rc('text',usetex=True)
rc('font',**{'family':'serif','serif':['Times']})

sys.path.append('../')
from common_parms import LOG_DIR,DIMLAT,DIMLNG,DIMELV

NOT_USED=[(12,17,2019),(12,12,2019),(10,29,2019),(7,25,2019),(6,28,2019),(5,25,2019),(1,8,2019),
          (12,29,2018),(12,12,2018),(10,11,2018),(7,6,2018)] #,(8,13,2018)]

def make_dates():
  mmlist=os.listdir(LOG_DIR)
  mm=[each for each in mmlist if 'seeing.dat' in each]
  mm=[(os.stat(LOG_DIR+each).st_mtime,each) for each in mm]
  mm.sort()
  mm=[each[1] for each in mm]
  mmre=re.compile('seeing.dat.(\d{2}).(\d{2}).(\d{4})')
  mymm=map(mmre.findall,iter(mm))
  mymm=[each[0] for each in mymm if each!=[]]
  mymm=map(lambda x: tuple((int(x[0]),int(x[1]),int(x[2]))),mymm)[::-1][:-1]
  mymm=dict(enumerate(mymm))
  mymm={value: key for key,value in mymm.viewitems()}
  map(lambda x: mymm.pop(x), NOT_USED)
  mymm={value: key for key,value in mymm.viewitems()}
  return mymm.values()
#
TABLE_DATES=make_dates()

def open_tele_log(fname='',mon=2,day=20,year=2017):
  if fname!='':
    telelog=fname
  else:
    telelog='telescope.log.%s.%s.%d' % (str(mon).zfill(2),str(day).zfill(2),year)
  fp=open(telelog)
  lnes=fp.readlines()
  fp.close()
  lnes=checklines(lnes)
  splnes=array(map(lambda x: x.split(','),lnes),dtype='|S13').transpose()
  dte=splnes[1]
  tme=splnes[0]
  hrs=map(ephem.hours,splnes[3])
  dec=map(lambda x: ephem.degrees(x.replace('*',':')),splnes[4])
  azm=map(lambda x: ephem.degrees(x.replace('*',':')),splnes[5])
  elv=map(lambda x: ephem.degrees(x.replace('*',':').replace('\n','')),splnes[6])
  cmdaz=map(ephem.hours,splnes[7])
  cmdel=map(lambda x: ephem.degrees(x.replace('*',':')),splnes[8])
  osource=[each.replace('\n','') for each in splnes[-1]]
  tme=map(lambda x:time.strptime(x[0]+' '+x[1].split('.')[0],'%m/%d/%y %H:%M:%S'),array((dte,tme)).transpose())
  tmes=map(lambda x: time.mktime(x),tme)
  nms=arange(len(tme))
  return array(tmes),array((hrs,dec)).transpose(),array((azm,elv)).transpose(),array((cmdaz,cmdel)).transpose(),\
    array(osource)

#time.strptime(dte[0]+' '+tme[0],'%m/%d/%y %H:%M:%S')
#zz=time.mktime(tme[0][0])
#qq=array(map(lambda x:time.mktime(x)-zz,mm[0]))

def checklines(lnes):
  badlines=[]
  for k in range(len(lnes)):
    zz=lnes[k].split(',')
    i=0
    for j in range(len(zz)):
      if '1111' in zz[j] or '    ' in zz[j] or '#' in zz[j]:
        badlines.append([k,i])
      else: pass
      if '0/0/0' in zz[j]: badlines.append([k,i])
      else: pass
      i+=1
  if len(badlines)>0:
    badindex=unique(array(badlines).transpose()[0])
    bdind=badindex[argsort(badindex)[::-1]]
    for each in bdind:
      lnes.pop(each)
  return lnes

def new_open_tele_log(fname='',mon=11,day=16,year=2017):
  if fname!='':
    telelog=fname
  else:
    telelog='telescope.log.%s.%s.%d' % (str(mon).zfill(2),str(day).zfill(2),year)
  data=loadtxt(telelog,comments='#',delimiter=',',dtype='S').transpose()
  hrs=map(ephem.hours,data[3])
  dec=map(lambda x: float(ephem.degrees(x.replace('*',':')))*180.0/pi,data[4])
  azm=map(lambda x: float(ephem.degrees(x.replace('*',':')))*180.0/pi,data[5])
  elv=map(lambda x: float(ephem.degrees(x.replace('*',':').replace('\n','')))*180.0/pi,data[6])
  onsource=array([each.replace('\n','') for each in data[-1]])
  onsource[onsource=='True']=1
  onsource[onsource=='False']=0
  onsource=onsource.astype(int)
  time_array=map(lambda x,y: time.strptime(x.split('.')[0]+' '+y,'%H:%M:%S %m/%d/%y'),data[0],data[1])
  time_floats=array(map(time.mktime,time_array))
  time_zeroed=time_floats-time_floats[0]
  return time_zeroed,hrs,dec,azm,elv,onsource

def open_source_log(fname='',mon=2,day=20,year=2017):
  if fname!='':
    srcelog=fname
  else:
    srcelog='sources.log.%s.%s.%d' % (str(mon).zfill(2),str(day).zfill(2),year)
  fp=open(srcelog)
  lnes=fp.readlines()
  fp.close()
  lnes=checklines(lnes)
  splnes=array(map(lambda x: x.split(','),lnes)).transpose()
  dte=splnes[1]
  tme=splnes[0]
  names=splnes[2]
  hrs=map(ephem.hours,splnes[4])
  dec=map(lambda x: ephem.degrees(x.replace('*',':')),splnes[5])
  azm=map(lambda x: ephem.degrees(x.replace('*',':')),splnes[6])
  elv=map(lambda x: ephem.degrees(x.replace('*',':')),splnes[7])
  tme=map(lambda x:time.strptime(x[0]+' '+x[1].split('.')[0],'%m/%d/%Y %H:%M:%S'),array((dte,tme)).transpose())
  dtes=map(lambda x: time.strftime('%m/%d/%y %H:%M:%S',x),tme)
  tmes=map(lambda x: time.mktime(x),tme)
  nms=arange(len(tme))
  return array(tmes),array((hrs,dec)).transpose(),array((azm,elv)).transpose()

def open_seeing_log(fname='',mon=4,day=18,year=2018):
  if fname!='':
    seeinglog=fname
  else:
    seeinglog='seeing.dat.%s.%s.%d' % (str(mon).zfill(2),str(day).zfill(2),year)
  seeing=loadtxt(seeinglog,delimiter=',',dtype='S',comments='#').transpose()
  dtime_string=[seeing[1,i]+' '+seeing[0,i] for i in range(len(seeing[0]))]
  try:
    dt_time=array([datetime.datetime.strptime(each,'%m/%d/%Y %H:%M:%S') for each in dtime_string])
  except Exception as err: 
    dt_time=array([datetime.datetime.strptime(each,'%m/%d/%Y %H:%M:%S.%f') for each in dtime_string])
  airmass=seeing[10].astype('f')
  etz=seeing[-3].astype('f')
  elz=seeing[-5].astype('f')
  etg=seeing[-4].astype('f')
  elg=seeing[-6].astype('f')
  zdist=seeing[8].astype('f')
  epsilon=(etz+elz)/2.0
  eps_zcorr=epsilon*cos(zdist)**0.6
  return dt_time,airmass,zdist,epsilon,eps_zcorr,seeing

def open_weather_log(fname='',subdir='./',mon=4,day=18,year=2018,station='1'):
  if fname!='':
    weatherlog=os.path.join(LOG_DIR,subdir,fname)
  else:
    weatherlog=os.path.join(LOG_DIR,subdir,'weather.log.%s.%s.%d' % (str(mon).zfill(2),str(day).zfill(2),year))
  weath=loadtxt(weatherlog,delimiter=',',dtype='S',comments='#').transpose()
  recmp=re.compile('.*'+station+'$')
  srch_hits=map(lambda x:re.search(recmp,x),weath[0])
  station_indices=array([i for i in range(len(srch_hits)) if srch_hits[i]])
  weather=weath[:,station_indices]
  dtime_string=[each.rsplit(':',1)[0] for each in weather[0]]
  dt_time=array([datetime.datetime.strptime(each,'%m/%d/%Y %H:%M:%S') for each in dtime_string])
  air_temp=weather[2].astype('f')
  dew_point=weather[3].astype('f')
  pressure=weather[4].astype('f')
  humidity=weather[5].astype('f')
  windspeed=weather[7].astype('f')
  winddir=weather[8].astype('f')
  split=weather[11].astype('f')
  return array([dt_time,air_temp,dew_point,pressure,humidity,windspeed,winddir,split]),weather

def ret_filtered(fname='',mon=4,day=18,year=2018,airmass=1.25,max_eps=10.0):
  if fname!='':
    seeinglog=fname
  else:
    seeinglog='seeing.dat.%s.%s.%d' % (str(mon).zfill(2),str(day).zfill(2),year)
  dt,am,zd,ep,ep_corr,seeing=open_seeing_log(fname=seeinglog)
  newdt=dt[where(ep<max_eps)]
  newam=am[where(ep<max_eps)]
  newep=ep[where(ep<max_eps)]
  newzd=zd[where(ep<max_eps)]
  newep_corr=ep_corr[where(ep<max_eps)]
  filter_dt=newdt[where(newam<airmass)]
  filter_am=newam[where(newam<airmass)]
  filter_ep=newep[where(newam<airmass)]
  filter_zd=newzd[where(newam<airmass)]
  filter_ep_corr=newep_corr[where(newam<airmass)]
  return filter_dt,filter_am,filter_zd,filter_ep,filter_ep_corr,seeing

def mk_tzero_array(dtes,tmes):
  time_array=map(lambda x,y: time.strptime(x.split('.')[0]+' '+y,'%H:%M:%S %m/%d/%Y'),tmes,dtes)
  time_floats=array(map(time.mktime,time_array))
  time_zeroed=time_floats-time_floats[0]
  return time_zeroed

def mk_utc_flt(tmes,utcoff=7):
  #Only for a 24 hour period, or one evening of observing
  mm=datetime.timedelta(seconds=3600*utcoff)
  times=tmes+mm
  t_array=map(lambda x: x.hour+x.minute/60.0+x.second/3600.0,times)
  return t_array

def perc_dark(mon=2,day=6,year=2020,hr=0,mn=0,sc=0):
  ''' <perc_dark> a function to return the percentage of nighttime given a datetime.
      -Can be used like this..
      >> x=[]
      >> for i in range(365):  x.append(glg.perc_dark(dte.datetime(2020,1,1,0,0,0)+dte.timedelta(i,0,0)))
      >> plot(range(365),array(x)*100.0,'r-')

  '''
  seeing=open_seeing_log(mon=mon,day=day,year=year)
  dtime=datetime.datetime(year,mon,day,hr,mn,sc)
  mm=ephem.Observer()
  mm.lon=str(DIMLNG)
  mm.lat=str(DIMLAT)
  mm.elevation=DIMELV
  perc=[]
  for dtime in seeing[0]:
    mm.date=dtime
    nextrise=ephem.localtime(mm.next_rising(ephem.Sun(),start=dtime))
    previousset=ephem.localtime(mm.previous_setting(ephem.Sun(),start=nextrise))
    total_night=nextrise-previousset
    perc.append(float((dtime-previousset).seconds)/float(total_night.seconds))
  return array(perc),seeing

# To plot seeing as a function of the percent of night time use the following:
#>>> m,n,o=glg.TABLE_DATES[6]
#>>> a,b=glg.perc_dark(mon=m,day=n,year=o)
#>>> plot(a,b[4],'k-')

def dt2hours(mon=2,day=6,year=2020):
  ##returns number of hours after opening dome and seeing.  Time is not the timestamp of the data.
  seeing=open_seeing_log(mon=mon,day=day,year=year)
  dt_array=seeing[0]
  ff=dt_array-dt_array[0]
  tofday=datetime.datetime(2020,2,6)+ff
  return array(tofday),seeing
def get_all_numbers(idx=4):
  #return  of open_seeing_log is idx=(0)dt_time,(1)airmass,(2)zdist,(3)epsilon,(4)eps_zcorr,(5)seeing
  ts_array=[]
  sg_array=[]
  for each in TABLE_DATES[:-9]:
    t,s=dt2hours(mon=each[0],day=each[1],year=each[2])
    ts_array.append(t)
    sg_array.append(array(s[idx]))
  ts_array=array(ts_array)
  sg_array=array(sg_array)
  xxx=ts_array.flatten()
  yyy=sg_array.flatten()
  return ts_array,sg_array,array([concatenate(xxx[:]),concatenate(yyy[:])])

#### t,s,mymm=get_all_numbers()
#### c,b,h=hist(mymm[1],50,range=(0.0,5.0)) for all seeing measurement histogram
#### cdf=cumsum(c)
#### plot(b[1:],cdf) # To plot cummulative distribution of the histsgram
### to compare different dates as a function of time of after opening use plot_date(t[0],s[0])
### to get hist of a certain day, use >>> c,b,h=hist(s[0],100,range=(0.0,5.0))

def all_hist_cdf_plot(maxlim=3.0,scale='lin'):
  t,s,mymm=get_all_numbers()
  x,y=TABLE_DATES[0],TABLE_DATES[-9]
  subplot(211)
  tt='Histogram and CDF for %d days of KPDIMM seeing measurements between' % (len(s))
  tt='%s\n%s and %s corrected for airmass, and clipped for an $\epsilon_{max}<%3.1f$.' % \
    (tt,datetime.datetime(y[2],y[0],y[1]).strftime('%d %b %Y'),
     datetime.datetime(x[2],x[0],x[1]).strftime('%d %b %Y'),maxlim)
  title(tt,size=20.0)
  c,b,h=hist(mymm[1],100,range=(0.0,maxlim))
  hist_axs=gca()
  hist_axs.grid(True)
  cdf=cumsum(c)
  hist_axs.set_xlabel('Corrected Seeing (\")',size=20)
  hist_axs.set_ylabel('Number',size=20)
  subplot(212)
  plot(b[1:],cdf)
  cdf_axs=gca()
  cdf_axs.grid(True)
  cdf_axs.set_xlabel('Corrected Seeing (\")',size=20)
  cdf_axs.set_ylabel('Number',size=20)
  textx=[2.0/3.0*maxlim]*5  # Linear text x-position
  texty=c.max()/array([1.520,1.725,2.0,2.3,2.9])  # Linear text y-position
  if scale=='ylog' or scale=='log':
    hist_axs.set_yscale('log')
    cdf_axs.set_yscale('log')
    texty=c.max()/array([log10(1.520)*10.0,log10(1.725)*15.0,log10(2.0)*25.0,log10(2.30)*35.0,log10(2.90)*50.0])
    if scale=='log':
      xmax=hist_axs.get_xlim()[1]
      if maxlim>=10.0: textx=[xmax/5.0]*5
      else: textx=[0.025]*5
      cdf_axs.set_xscale('log')
      hist_axs.set_xscale('log')
  mstr='$N_{Tot}=%d$' % (int(len(mymm[1])))
  hist_axs.text(textx[0],texty[0],mstr,size=20) 
  mstr='$\Sigma N_{(0.0<\epsilon<%3.1f)}=%d$' % (maxlim,int(c.sum()))
  hist_axs.text(textx[1],texty[1],mstr,size=20)
  mstr='$\Sigma N/N_{Tot}=%6.3f$' % (c.sum()/len(mymm[1]))
  hist_axs.text(textx[2],texty[2],mstr,size=20)
  mstr='$\mu\pm\sigma=$%5.4f$\pm$%5.4f' % (mymm[1][where(mymm[1]<maxlim)].mean(),\
    mymm[1][where(mymm[1]<maxlim)].std())
  hist_axs.text(textx[3],texty[3],mstr,size=20)
  mstr='$\\tilde{x}=$%5.4f' % (median(mymm[1][where(mymm[1]<maxlim)]))
  hist_axs.text(textx[4],texty[4],mstr,size=20)
  return

# Some fun and interesting seeing data analyisis:
def confid(i,perc=0.95,maxlim=3.0):
  '''<confid> will calculate the confidence interval for a normal distribution of the data
     <i> is the indexed measurement file, if i==-1 take all of seeing measurements
     <perc> is the percent confidence
     <maxlim> clips the corrected seeing data to that level
  '''
  y=scipy.stats.norm()
  a,b,cs=get_all_numbers()
  num_samples=array([len(b[k]) for k in range(len(b))])
  if i!=-1:
    bb=b[i][where(b[i]<maxlim)]
    tot_samples=num_samples[i]
  else:
    bb=cs[1][where(cs[1]<maxlim)]
    tot_samples=len(cs[1])
  num_bb,m,s,md=len(bb),bb.mean(),bb.std(),median(bb)
  cnf=y.interval(perc)[1]   # positive only
  k=cnf*s/num_bb**0.5
  ##Therefore, the probability that the population(actual) mean falls within range m-k and m+k is <perc> where
  ##<m> and <s> are the sample mean and sample standard deviation for <num_bb> number of samples.
  print '\nWith %i total samples clipped to a maximum seeing of %5.3f\":' % (tot_samples,maxlim)
  print '%i samples remain with a sample mean is %5.3f, a sample std of %5.3f, and a median of %5.3f.' % (num_bb,m,s,md)
  print 'The confidence interval is k=%5.3f for a gamma=%5.3f' % (k,perc)
  print '\nP(%5.3f<=%5.3f<=%5.3f)=%5.3f\n' % (m-k,m,m+k,perc)
  return m-k,m,m+k,s,k,num_bb
#Use errorbar(x,y,xerr=xerr,yerr=yerr,fmt='kx',ms=3)
#   
#  where x,y,xerr,yerr are arrays
#    x can be a datetime array
#
def samp_size(s,perc,length):
  '''<samp_size> will calculate the sample size for a confidence interval of a prescribed length
     <s> is the sampled standard deviation
     <perc> is the percent confidence
     <length> is the total length of the interval about the mean seeing
              for example for a mean seeing of 0.85 I want to know the number of samples
              required to achieve a 99% confidence that the mean will fall with my std
  '''
  y=scipy.stats.norm()
  cnf=y.interval(perc)[1]   # positive only
  ##In order to get the number of samples necessary for a confidence interal of a prescribed length, lnt=2*cnf is
  num_required=(2.0*cnf*s/length)**2.0  # Number of required samples for the given std and perc
  ss='\nThe number of samples necessary to acheive a %5.2f%s confidence interval\n' % (perc*100.0,'%')
  ss='%sof length %5.3f\" about a sampled mean seeing with std of %5.3f\" is %i.\n' % (ss,length,s,num_required)
  print ss
  return 

def see_analysis(maxseeing=5.0):
  a,b,am=get_all_numbers(idx=1)
  a,b,rs=get_all_numbers(idx=3)
  a,b,cs=get_all_numbers(idx=4)
  am[1]=am[1].astype('f')
  rs[1]=rs[1].astype('f')
  cs[1]=cs[1].astype('f')
  return am,rs,cs
# airmass=am[where(rs[1]<maxseeing)]
# rawseeing=rs[where(rs[1]<maxseeing)]
# corrseeing=cs[where(rs[1]<maxseeing)]
# return airmass,rawseeing,corrseeing
#m,b=polyfit(airmass[1],rawseeing[1],1)
#
#  This produces the first order polynomial fit for m and b of rawseeing vs airmass
#
#plot(arange(1.0,maxseeing,0.01),m*arange(1.0,maxseeing,0.01)+b,'-',color='Black')
#plot(airmass,rawseeing,'.',color='Purple')
#
#hist(rawseeing,100,)

#
# used as
#>>> from numpy import *
#>>> from pylab import *
#>>> a,b,c=open_seeing_log()
#>>> clf()
#>>> plot(a,c,'.',color='r',ms=3)
#>>> xlim(0,2)
#>>> ylim(0,2)
#>>> grid()
#>>> xlabel('Airmass')
#>>> ylabel('Seeing(\")')
#>>> title('Calculated Seeing as a Function of Airmass',size=10)
#>>> text(0.5,1.75,'Mean Seeing %8.4f+/-%8.4f' % (epsilon.mean(),epsilon.std()))
#>>> text(0.5,1.65,'Median Seeing %8.4f' % (median(epsilon)))

def compare_see(mon1=9,day1=13,year1=2018,mon2=9,day2=14,year2=2018):
  clf()
  myfmt=mdates.DateFormatter('%H:%M:%S')
  dt_func=datetime.datetime.strftime
  seeing1=open_seeing_log(mon=mon1,day=day1,year=year1)
  seeing2=open_seeing_log(mon=mon2,day=day2,year=year2)
  tstmp1=map(lambda i: seeing1[0][i].hour+seeing1[0][i].minute/60.0+seeing1[0][i].second/3600.0,range(len(seeing1[0])))
  tstmp2=map(lambda i: seeing2[0][i].hour+seeing2[0][i].minute/60.0+seeing2[0][i].second/3600.0,range(len(seeing2[0])))
  plot(tstmp1,seeing1[4],color='Violet',marker='d',ls='')
  plot(tstmp2,seeing2[4],color='ForestGreen',marker='d',ls='')
  grid(True)
  ylim(0.0,5.0)
  return

def make_see_table(*dates,**kws):
  #Where dates arguments are (mon,day,year) tuples
  # and for a list to be passed use:  make_see_table(*TABLE_DATES)
  prnt_raw=kws.pop('raw',False)
  air_mass=kws.pop('airmass',4.0)
  if prnt_raw:
    ss='\n%s%s%s\n' % (' '*10,'Corrected for Zdist Seeing Measurements:'.ljust(62),'Raw/Uncorrected Seeing Measurements:'.ljust(62))
  else:
    ss='\n%s\n' % ('Corrected Seeing Measurements:'.ljust(62))
  ss=ss+'%s'*6 % ('date'.center(12),'min'.center(10),'mean'.center(10),'max'.center(10),\
    'std'.center(10),'median'.center(10))
  if prnt_raw:
    ss=ss+'%s'*5 % ('min'.center(10),'mean'.center(10),'max'.center(10),\
      'std'.center(10),'median'.center(10))
  ss=ss+'%s\n' % ('tot number'.center(10))
  num_days,num_meas=0,0
  if dates:
    for each in dates:
      try:
        seeing=ret_filtered(mon=each[0],day=each[1],year=each[2],airmass=air_mass)
        ss=ss+'%s/%s/%d'.ljust(12) % (str(each[0]).zfill(2),str(each[1]).zfill(2),each[2])
        ss=ss+'%6.4f    '*5 % (seeing[4].min(),seeing[4].mean(),seeing[4].max(),seeing[4].std(),median(seeing[4]))
        if prnt_raw:
          ss=ss+'%6.4f    '*5 % (seeing[3].min(),seeing[3].mean(),seeing[3].max(),seeing[3].std(),median(seeing[3]))
        ss=ss+'%d\n' % (len(seeing[-1][0]))
        num_days,num_meas=num_days+1,num_meas+len(seeing[-1][0])
      except Exception: ss=ss+'\n'
  else:
    dr='./dimmseeinglogs/'
    dd=os.listdir(dr)
    dd=sort([each for each in dd if '2018' in each])
    for each in dd:
      try:
        seeing=ret_filtered(fname=os.path.join(dr,each))
        mm=each.split('.')
        mon,day,year=mm[2],mm[3],mm[4]
        ss=ss+'%s/%s/%s'.ljust(12) % (mon,day,year)
        ss=ss+'%6.4f    '*5 % (seeing[4].min(),seeing[4].mean(),seeing[4].max(),seeing[4].std(),median(seeing[4]))
        if prnt_raw:
          ss=ss+'%6.4f    '*5 % (seeing[3].min(),seeing[3].mean(),seeing[3].max(),seeing[3].std(),median(seeing[3]))
        ss=ss+'%d\n' % (len(seeing[-2][0]))
        num_days,num_meas=num_days+1,num_meas+len(seeing[-1][0])
      except Exception: ss=ss+'\n'
  ss=ss+'\n       Total Number of Dates:%d      Total Number of Measurements:%d\n' % (num_days,num_meas)
  return ss

#Using the return from make_table, the following can be used to get numbers out of make_table return
#
#>>> ss=make_see_table(*TABLE_DATES)
#>>> mmss=ss.split('\n')
#>>> mymm=loadtxt(iter(mmss[3:-3]),dtype='S10,5>f8,int16',unpack=True)
#>>> mmmm=array(mymm[1]).transpose()
#>>> plot(range(len(mymm[0])),mmmm[1],'k-')
#>>> mmmdte=[datetime.datetime.strptime(each,'%m/%d/%Y') for each in mymm[0]]
#
#To count the measurements per month use
#>>> len([each for each in mymm[0] if each{:2]=='01'])
def cnt_per_mon(ss=None):
  if not ss:
    ss=make_see_table(*TABLE_DATES)
  mmss=ss.split('\n')
  mymm=loadtxt(iter(mmss[3:-3]),dtype='S10,5>f8,int16',unpack=True)
  for i in range(1,13):
    mst=str(i).zfill(2)
    print '%s: %d' % (datetime.date(2020,i,1).strftime('%B'),len([each for each in mymm[0] if each[:2]==mst]))
  print 'Total Number of days: %d' % (len(mymm[0]))
  return

def plot_see_am(fname='',mon=TABLE_DATES[0][0],day=TABLE_DATES[0][1],year=TABLE_DATES[0][2]):
# from pylab import rc
# rc('font',**{'family':'sans-serif','serif':['Times']})
# rc('text',usetex=True)
  clf()
  myfmt=mdates.DateFormatter('%H:%M:%S')
  dt_func=datetime.datetime.strftime
  a=subplot(111)
  am_range_list=[5.0,1.4,1.3,1.2,1.1]
  #style_list=['x','s','d','o','.']
  #style_list=['*','*','*','*','*']
  style_list=[(8,2,45.0),(8,2,45.0),(8,2,45.0),(8,2,45.0),(8,2,45.0)]
  ms_list=[3,6,9,12,15]
  #color_list=['Black','DarkBlue','LightGreen','MediumVioletRed','AntiqueWhite']
  #color_list=['Black','Blue','Green','Red','AntiqueWhite']
  color_list=['Black','Red','Green','MediumBlue','AntiqueWhite']
  for i in range(len(am_range_list)):
    dt_time,airmass,zdist,epsilon,eps_zcorr,seeing=ret_filtered(fname,mon,day,year,airmass=am_range_list[i])
    a.plot_date(dt_time,epsilon,marker=style_list[i],color=color_list[i],ms=ms_list[i])
  a.xaxis.set_major_formatter(myfmt)
  a.tick_params(axis='both',which='major',labelsize=14)
  setp(a.xaxis.get_majorticklabels(),rotation=15)
  a.set_ylim(0,5)
  a.grid(True)
  a.set_title('Seeing as a function of time.  The smaller the marker the larger the airmass.  Data from %d/%d/%d' % \
    (mon,day,year),size=20)
  a.set_xlabel('Time',size=14)
  a.set_ylabel('Seeing(\")',size=14)
  return

def plot_seeing(fname='',mon=TABLE_DATES[0][0],day=TABLE_DATES[0][1],year=TABLE_DATES[0][2],fig=None):
# from pylab import rc
# rc('font',**{'family':'sans-serif','serif':['Times']})
# rc('text',usetex=True)
  if fig:  fig=fig
  else:  fig=figure()
  fig.clf()
  myfmt=mdates.DateFormatter('%H:%M:%S')
  dt_func=datetime.datetime.strftime
  dt_time,airmass,zdist,epsilon,epsilon_zcorr,seeing=open_seeing_log(fname,mon,day,year)
  #a=subplot(211)
  #b=subplot(212)
  a=fig.add_subplot(211)
  b=fig.add_subplot(212)
  indxs=intersect1d(where(epsilon>0),where(epsilon<10))
  dt_range=(dt_time.min(),dt_time.max())
  am_range=(airmass[indxs].min(),airmass[indxs].max())
# see_range=(epsilon[indxs].min(),epsilon[indxs].max())
# seeing_stats=(epsilon[indxs].mean(),epsilon[indxs].std(),median(epsilon[indxs]))
# num_obs=len(epsilon[indxs])
  ###The following are corrected for zenith distance.
  see_range=(epsilon_zcorr[indxs].min(),epsilon_zcorr[indxs].max())
  seeing_stats=(epsilon_zcorr[indxs].mean(),epsilon_zcorr[indxs].std(),median(epsilon_zcorr[indxs]))
  num_obs=len(epsilon_zcorr[indxs])
  a.plot_date(dt_time[indxs],epsilon[indxs],'d',color='r',ms=4)
  a.plot_date(dt_time[indxs],epsilon[indxs]*cos(zdist[indxs])**0.6,'d',color='b',ms=4)
  a.xaxis.set_major_formatter(myfmt)
  a.tick_params(axis='both',which='major',labelsize=14)
  setp(a.xaxis.get_majorticklabels(),rotation=15)
  a.set_ylim(0,5)
  a.grid(True)
  a.set_xlabel('Time',size=14)
  a.set_ylabel('Seeing(\")',size=14)
  a.set_title('Calculated Seeing as a Function of Time and Airmass between %s-%s on %d/%d/%d' % \
    (dt_func(dt_range[0],'%H:%M:%S'),dt_func(dt_range[1],'%H:%M:%S'),mon,day,year),size=20)
  a.text(dt_time[1],4.75,'Seeing Range:%8.4f"$<\epsilon<$%8.4f"' % (see_range[0],see_range[1]),size=18)
  a.text(dt_time[1],4.5,'Mean Seeing:%8.4f"+/-%8.4f"' % (seeing_stats[0],seeing_stats[1]),size=18)
  a.text(dt_time[1],4.25,'Median Seeing:%8.4f"' % (seeing_stats[2]),size=18)
  a.text(dt_time[1],4.0,'Airmass Range:%8.4f$<\\xi<$%8.4f' % (am_range[0],am_range[1]),size=18)
  a.text(dt_time[1],3.75,'Number of Measurements:%d' % (num_obs),size=18)
  b.plot(airmass[indxs],epsilon[indxs],'d',color='k',ms=4,ls='')
  b.set_ylim(0,5)
  b.grid(True)
  b.set_xlabel('Airmass',size=14)
  b.set_ylabel('Seeing(\")',size=14)
  return a,b

def plot_tele_src(tele_log,srce_log):
  qqq=[]
  for each in tele_log[-1]:
    if each=='True': qqq.append(1)
    else: qqq.append(0)
  qqq=array(qqq)
  az=subplot(221)
  elv=subplot(222,sharex=az)
  ra=subplot(223,sharex=az)
  dec=subplot(224,sharex=az)
  az.plot((tele_log[0]-tele_log[0][0])/3600.0,tele_log[-3].transpose()[0]*180.0/pi,'k-')
  az.plot((tele_log[0]-tele_log[0][0])/3600.0,qqq*360.0,'g-')
  elv.plot((tele_log[0]-tele_log[0][0])/3600.0,tele_log[-3].transpose()[1]*180.0/pi,'k-')
  elv.plot((tele_log[0]-tele_log[0][0])/3600.0,qqq*90.0,'g-')
  ra.plot((tele_log[0]-tele_log[0][0])/3600.0,tele_log[-4].transpose()[0],'k-')
  ra.plot((tele_log[0]-tele_log[0][0])/3600.0,qqq*24.0,'g-')
  dec.plot((tele_log[0]-tele_log[0][0])/3600.0,tele_log[-4].transpose()[1]*180.0/pi,'k-')
  dec.plot((tele_log[0]-tele_log[0][0])/3600.0,qqq*90.0,'g-')
  az.plot((srce_log[0]-tele_log[0][0])/3600.0,srce_log[-1].transpose()[0]*180.0/pi,'r.',ms=3)
  elv.plot((srce_log[0]-tele_log[0][0])/3600.0,srce_log[-1].transpose()[1]*180.0/pi,'r.',ms=3)
  ra.plot((srce_log[0]-tele_log[0][0])/3600.0,srce_log[-2].transpose()[0],'r.',ms=3)
  dec.plot((srce_log[0]-tele_log[0][0])/3600.0,srce_log[-2].transpose()[1]*180.0/pi,'r.',ms=3)
  az.set_title('Azimuth',size=10)
  elv.set_title('Elevation',size=10)
  ra.set_title('RightAscension',size=10)
  dec.set_title('Declination',size=10)
  az.grid(True)
  elv.grid(True)
  ra.grid(True)
  dec.grid(True)
  draw()
  return az,elv,ra,dec

def test_roi(w,h,offx,offy,binning):
  wtlims,htlims=2752,2200
  wlim,hlim=wtlims/binning,htlims/binning
  print 'width:  %d, offx: %d, w+o: %d, limit: %d' % (w,offx,w+offx,wlim)
  print 'height: %d, offy: %d, h+o: %d, limit: %d' % (h,offy,h+offy,hlim)
  return

def ret_px2pk_array(imglogfile):
  return 

if __name__=='__main__':
  if '-help' in sys.argv:
    print '\nget_logs.py\nA basic log viewer\nUsage: python get_logs.py -mon 3 -day 3 -year 2017\n'
  else:
    try:
      dayindex=sys.argv.index('-day')+1
      daynum=sys.argv[dayindex]
    except Exception:
      daynum=TABLE_DATES[0][1]
    try:
      monindex=sys.argv.index('-mon')+1
      monnum=sys.argv[monindex]
    except Exception:
      monnum=TABLE_DATES[0][0]
    try:
      yearindex=sys.argv.index('-year')+1
      yearnum=sys.argv[yearindex]
    except Exception:
      yearnum=TABLE_DATES[0][2]
#   mma=open_tele_log(mon=monnum,day=daynum,year=yearnum)
#   mmb=open_source_log(mon=monnum,day=daynum,year=yearnum)
    fig=plt.figure()
#   a,b,c,d=plot_tele_src(mma,mmb)
    a,b=plot_seeing(day=int(daynum),mon=int(monnum),year=int(yearnum),fig=fig)
    fig.show() 
    canvwidget=fig.canvas.get_tk_widget()
#   canvwidget.master.title('A Simple Log Viewer')
    canvwidget.master.mainloop()
    
