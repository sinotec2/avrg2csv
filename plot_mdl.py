#!/cluster/miniconda/bin/python
"""plot the hrly time series of pollutant at station(s)
    specHr.py -b 2071231 -e 20180101 -s PM2.5 -a plot -t wanli,xianxi,puzi,xiaogang """
import matplotlib.pyplot as plt
from pandas import *
import sys,os,datetime,subprocess
def getarg():
    """ read time period and station name from argument(std input)
    specHr.py -b 2071231 -e 20180101 -s PM2.5 -a plot -t wanli,xianxi,puzi,xiaogang """
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--FNAME", required = True, type=str,help = "ovm or ovd filename")
    ap.add_argument("-t", "--STNAM", required = True, type=str,help = "station name,sep by ,")
    ap.add_argument("-s", "--SPNAM", required = True, type=str,help = "spec name")
    ap.add_argument("-b", "--BEGD", required = True, type=int,help = "yyyymmdd")
    ap.add_argument("-e", "--ENDD", required = True, type=int,help = "yyyymmdd")
    ap.add_argument("-a", "--ACTION", required = True, type=str,help = "save or plot")    
    args = vars(ap.parse_args())
    return [args['FNAME'],args['STNAM'],args['SPNAM'],args['BEGD'],args['ENDD'],args['ACTION']]

def dt2int(dt):
    a=[int(i) for i in str(dt).split()[0].split('-')]
    return a[0]*100*100+a[1]*100+a[2]
def int2dt(idt):
    """idt=yyyymmdd"""
    return datetime.datetime(idt/100/100,idt/100%100,idt%100)
def bool_dt(x):
    if dt2int(int2dt(x)+datetime.timedelta(days=1)) in ymd or \
       dt2int(int2dt(x)+datetime.timedelta(days=0)) in ymd or \
       dt2int(int2dt(x)+datetime.timedelta(days=-1)) in ymd: 
       return True
    return False
def nstnam():
    import json
    fn=open('/home/backup/data/epa/pys/sta_list.json')
    d_nstnam=json.load(fn)
    d_namnst = {v: k for k, v in d_nstnam.iteritems()}
    return (d_nstnam,d_namnst)
(d_nstnam,d_namnst)=nstnam()
fname,stnam,SPNAM,begd,endd,act=getarg()
sGP=[47, 48, 49, 50, 51, 52, 53, 54, 56, 57, 58, 59, 60, 61]
if stnam=='*':
  nam=[d_nstnam[str(i)] for i in sGP]
else:
  nam=[i for i in stnam.split(',')]
  for stnam in nam:
    if stnam not in d_namnst:sys.exit("station name not right: "+stnam)
stn=[d_namnst[i] for i in nam]
stn=['0'*(2-len(i))+i for i in stn]

with open('/home/backup/data/epa/pys/item2.txt') as ftext:
#items of EPA monitoring stations
    itm=[line.strip('\n')for line in ftext]
SPNAMe=SPNAM
if SPNAMe=='O3e':SPNAMe='O3'
if SPNAMe not in itm:sys.exit('error in item_SPNAM: '+SPNAMe)
itx=itm.index(SPNAMe)

SPNAMs=['O3','PM10','PM2.5','PMc','NOx','SO2','CO','NMHC','WIND_SPEED','WIND_DIREC','AMB_TEMP']
SPNAMd=['OZN','PMT','P25','PMc','NOX','SO2','CMO','NMH','WSP','WDR','TMP']
d_s2d={i:j for i,j in zip(SPNAMs,SPNAMd)}

units=['ppb','ug/M3','ug/M3','ug/M3','PPB','PPB','PPM','PPM','m/s','deg','degC']
d_sp2un={i:j for i,j in zip(SPNAMs,units)}
if SPNAMe not in SPNAMs:sys.exit('error in unit_SPNAM: '+SPNAM)
unit=d_sp2un[SPNAMe]
bdate = datetime.datetime(begd/100/100,begd/100%100,begd%100)
edate = datetime.datetime(endd/100/100,endd/100%100,endd%100)
leng=int(str(edate-bdate).split()[0].split('-')[0])+1
ymd=[dt2int(bdate+datetime.timedelta(days=i)) for i in xrange(leng)]
yr=set([str(i/100/100) for i in ymd])
yrmn=set([str(i/100) for i in ymd])

df=read_csv(fname)
if len(df.columns)==27:
  df.columns=[ u'ID', u'NAME', u'JuliHr', u'CalDat', u'TMP', u'SO2',
        u'CMO', u'OZN', u'PMT', u'NOX', u'P25', u'NO2', u'THC', u'NMH', u'WSP',
        u'WDR', u'TMP.1', u'SO2.1', u'CMO.1', u'OZN.1', u'PMT.1', u'NOX.1',
        u'P25.1', u'NO2.1', u'NMH.1', u'THC.1', u'WSP.1', u'WDR.1']
  d_s2d={i:j+'.1' for i,j in zip(SPNAMs,SPNAMd)}

yr=list(df.CalDat)[0]/100/100/100
if yr==0:
  pwd=subprocess.check_output('pwd',shell=True).strip('\n').split('/')
  base_yr=[i[:4] for i in pwd if len(i)>=4 and i[0]=='2' and int(i[:4])>2000]
  if len(base_yr)==0:
    sys.exit('$PWD must contain year information')
  else:
    base_yr=int(base_yr[0])
else:
  base_yr=0
df['nam']=[d_nstnam[str(i)] for i in df.ID]
idx=df[df.nam.map(lambda x:x not in nam)].index
df=df.drop(idx).reset_index()
df['YMDH']=[base_yr*100*100*100+i for i in df.CalDat]
df['YMD']=[base_yr*100*100+int(i/100) for i in df.CalDat]
df.CalDat=df.YMD
df=df.sort_values(['nam','YMDH']).reset_index().clip(0);del df['index']
if SPNAM=='O3e':
  for stnam in nam:
    df1=df[df['nam']==stnam].reset_index();del df1['index'] 
    l=list(df1[SPNAM])
    l8=l
    l8[3:len(df1)-5]=[np.mean(l[i-3:i+5]) for i in xrange(3,len(df1)-5)]
    df.loc[df['nam']==stnam,'O3e']=l8

#time series plot
if len(nam)==len(sGP):
  nam=[[i] for i in nam]
  lp=len(sGP)
else:
  nam,lp=[nam],1
for ip in xrange(lp):
  nams=nam[ip]
  fig, ax = plt.subplots()
  plt.legend(loc=0)
  plt.xlabel(SPNAM+' from '+str(begd)+' to '+str(endd))
  plt.ylabel(SPNAM+"("+unit+")")
  if SPNAM=='WIND_DIREC':
    ax.set_yticks([i for i in xrange(0,361,45)])
  ints=[3,6,12,24,48,72,168]
  intv=3
#in case of hourly data
  hofd, DayOrHr,pHr=24,100,1
#daily-averaged data
  if fname[2]=='d':
    hofd, DayOrHr,pHr=1,1,0

  days=list(set(df.YMD)&set(ymd))
  days.sort()
  if begd<days[0]:sys.exit('begd too early:'+str(begd)+' vs '+str(days[0]))
  if endd>days[-1]:sys.exit('endd too late:'+str(endd)+' vs '+str(days[-1]))
  ldays=len(days)
  for i in xrange(6,-1,-1):
    if 5<=ldays*hofd/ints[i]  <=20: intv=ints[i]
  for stnam in nams:
    boo=(df['nam']==stnam) & (df['YMDH'].map(lambda x :x/100 in ymd))
    df1=df[boo].reset_index(drop=True)
    totalSeed = df1.index.tolist()
    ax.plot(totalSeed, df1.loc[:,d_s2d[SPNAM]], label = stnam+'_mdl')
    if stnam==nam[0]:
      CalDat,JuliHr=list(df1.CalDat),list(df1.JuliHr)
      CalDat.sort();JuliHr.sort()
      x=np.arange(ldays*hofd)      
      xticks=list(range(0,len(x),intv))
      xlabels=[(CalDat[i]-20000000)*DayOrHr+JuliHr[i]%100*pHr for i in xticks]
      xticks.append(len(totalSeed))
      xlabels.append(' ')#str(int(xlabels[-1])+intv))
      ax.set_xticks(xticks)
      ax.set_xticklabels(xlabels, rotation=40, fontsize=8)
#ax.plot(df['DDHH'], df[SPNAM], label = stn[0])
  ax.legend(loc=0, borderaxespad=0., fontsize=9,ncol=2)#len(nam)
  if act[0]=='plot'[0]:plt.show()
  if act[0]=='save'[0]:
    dir='pngs'
    os.system('if ! [ -e '+dir+' ];then  mkdir -p '+dir+' ;fi')
    name=SPNAM+'@'+str(begd)
    for i in nams:
      name=name+i
    plt.savefig(dir+'/'+name+'.png')

