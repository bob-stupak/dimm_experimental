import numpy
import matplotlib.pyplot as plt

def autocorr1(x,lags):
  '''numpy.corrcoef, partial'''
  corr=[1. if i==0 else numpy.corrcoef(x[i:],x[:-i])[0][1] for i in lags]
  return numpy.array(corr)

def autocorr2(x,lags):
  '''manualy compute, non partial'''
  mean=numpy.mean(x)
  var=numpy.var(x)
  xp=x-mean
  corr=[1. if i==0 else numpy.sum(xp[i:]*xp[:-i])/len(x)/var for i in lags]
  return numpy.array(corr)

def autocorr3(x,lags):
  '''fft, pad 0s, non partial'''
  n=len(x)
  # pad 0s to 2n-1
  ext_size=2*n-1
  # nearest power of 2
  fsize=2**numpy.ceil(numpy.log2(ext_size)).astype('int')
  xp=x-numpy.mean(x)
  var=numpy.var(x)
  # do fft and ifft
  cf=numpy.fft.fft(xp,fsize)
  sf=cf.conjugate()*cf
  corr=numpy.fft.ifft(sf).real
  corr=corr/var/n
  return corr[:len(lags)]

def autocorr4(x,lags):
  '''fft, don't pad 0s, non partial'''
  mean=x.mean()
  var=numpy.var(x)
  xp=x-mean
  cf=numpy.fft.fft(xp)
  sf=cf.conjugate()*cf
  corr=numpy.fft.ifft(sf).real/var/len(x)
  return corr[:len(lags)]

def autocorr5(x,lags):
  '''numpy.correlate, non partial'''
  mean=x.mean()
  var=numpy.var(x)
  xp=x-mean
  corr=numpy.correlate(xp,xp,'full')[len(x)-1:]/var/len(x)
  return corr[:len(lags)]

