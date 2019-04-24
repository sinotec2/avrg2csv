#!/cluster/miniconda/bin/python
import numpy as np
from pandas import *
from PseudoNetCDF.camxfiles.Memmaps import uamiv
from scipy import interpolate
import datetime, sys, json

def nstnam():
    """ input the dictionaries between AQ station ID and NAMEs"""
    import json
    fn=open('sta_list.json')
    d_nstnam=json.load(fn)
    d_namnst = {v: k for k, v in d_nstnam.iteritems()}
    return (d_nstnam,d_namnst)
(d_nstnam,d_namnst)=nstnam()

def dt2int(dt):
    a=[int(i) for i in str(dt).split()[0].split('-')]
    return a[0]*100*100+a[1]*100+a[2]
def getarg():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--FNAME", required = True, type=str,help = "ovm or ovd filename")
    args = vars(ap.parse_args())
    return args['FNAME']

fname=getarg()
con_file= uamiv(fname,'r')
v4=filter(lambda x:con_file.variables[x].ndim==4, [i for i in con_file.variables])
nt,nlay,nrow,ncol=(con_file.variables[v4[0]].shape[i] for i in xrange(4))

with open('sta_list.txt','r') as f:
  t=[line.strip('\n') for line in f]
t=[i.split() for i in t[1:]]
laq=len(t)
ID=[int(i[0]) for i in t]
xs,ys=([float(i[j]) for i in t] for j in [2,3])
name=[d_nstnam[i[0]] for i in t]
point=zip(xs,ys)
ij0=np.array([(int((x-con_file.XORIG)/con_file.XCELL),int((y-con_file.YORIG)/con_file.YCELL)) for x,y in point]*nt).reshape(nt,laq,2)
xy=np.array(zip((np.array(xs)-con_file.XORIG)/con_file.XCELL,(np.array(ys)-con_file.YORIG)/con_file.YCELL)*nt).reshape(nt,laq,2)
rxy=xy-ij0
i0,j0=ij0[:,:,0],ij0[:,:,1]
rx,ry=rxy[:,:,0],rxy[:,:,1]

bdat0=datetime.datetime(con_file.SDATE/1000,1,1)
begd=dt2int(bdat0+datetime.timedelta(days=con_file.SDATE%1000-1))
bdate = datetime.datetime(begd/100/100,begd/100%100,begd%100)
endd=dt2int(bdate+datetime.timedelta(days=nt/24+1))
edate = datetime.datetime(endd/100/100,endd/100%100,endd%100)
leng=int(str(edate-bdate).split()[0].split('-')[0])+1
ymd=[dt2int(bdate+datetime.timedelta(days=i)) for i in xrange(leng)]
jul=list(set(con_file.variables['TFLAG'][:,0,0]))
jul.sort()
if len(ymd)!=len(jul):sys.exit('len of dates not right')
jul2cal={i:j for i,j in zip(jul,ymd)}
ju=con_file.variables['TFLAG'][:,0,0]
hr=con_file.variables['TFLAG'][:,0,1]/10000
yjhr=[i*100+j for i,j in zip(ju,hr) for l in xrange(laq)]
CalDat=[jul2cal[i]*100+j for i,j in zip(ju,hr) for l in xrange(laq)]

df=DataFrame({'ID':[i for i in ID]*nt,'NAME':[i for i in name]*nt,'CalDat':CalDat,'JuliHr':yjhr})
for v in v4:
  aq=np.zeros(shape=(laq,nt))
  c=np.array(con_file.variables[v][:,0,:,:])
  cc=np.zeros(shape=(nt,laq,4))
  loc=0
  for j in [0,1]:
    for i in [0,1]:
      for s in xrange(laq):
        cc[:,s,loc]=[c[t,j0[t,s]+j,i0[t,s]+i] for t in xrange(nt)]
      loc=loc+1
  c1=cc[:,:,0]*(1.-rx)+cc[:,:,1]*rx
  c2=cc[:,:,2]*(1.-rx)+cc[:,:,3]*rx
  aq=(c1*(1-ry)+c2*ry)
  df[v]=aq.flatten()
    
df.set_index('ID').to_csv(fname+'.csv')

