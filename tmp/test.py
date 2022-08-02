import itertools
import json
import decimal

def drange(start,stop,step,prec=10):
	decimal.getcontext().prec = prec
	points = []
	r= decimal.Decimal(start)
	step = decimal.Decimal(step)
	while r <=stop:
		points.append(float(r))
		r += step
	return points

intervals = [{"Startpoint":0.0,"Endpoint":1.0,"Stepsize":0.1,"IcsIntTime":10.0,"DetIntTime":5},{"Startpoint":1.0,"Endpoint":2.0,"Stepsize":0.05,"IcsIntTime":5.0,"DetIntTime":11}]

for points in map(lambda interval: drange(interval["Startpoint"],interval["Endpoint"],interval["Stepsize"]),intervals):
		print(points)


'''
def generateScanPoints(*axes):
	return itertools.product(*axes)


x = range(1,3)
y = range(1,3)
z = {"X1":1,"Y1":2,"Z1":3}#range(1,105,5)



jf=open("/home/control/SESAME/XAFS/xafs-scan/tmp/example.cfg","r")
cfg = json.load(jf) 

samples     = dict(zip(range(cfg["Nsamples"]),range(cfg["Nsamples"])))
scans       = dict(zip(range(cfg["Nscans"]),range(cfg["Nscans"])))
Intervals   = cfg["Intervals"]
points		= drange(0,10,0.5)


for X,Y,Z,P in generateScanPoints(samples,scans,Intervals,points):
	print("{}|{}|{}|{}".format(X,Y,Z,P))
'''