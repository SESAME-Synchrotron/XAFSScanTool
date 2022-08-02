import json
import decimal
import itertools

cfg = json.load(open("/home/control/xafs-scan2/DATA/SEM[1]/XAFS/20185101/configuration/exafs_20185101--2020-08-23 12:57:02.280955.cfg","r"))

def drange(start,stop,step,prec=10):
	decimal.getcontext().prec = prec
	points = []
	r= decimal.Decimal(start)
	step = decimal.Decimal(step)
	while r <=stop:
		points.append(float(r))
		r += step
	return points


Samples		=	range(cfg["Nsamples"])
Scans		=	range(cfg["Nscans"])
Intervals	=	range(cfg["NIntervals"])
Points		=	list(map(lambda intv: drange(intv["Startpoint"],intv["Endpoint"],intv["Stepsize"]),cfg["Intervals"]))

for sample,scan,interval, point in itertools.product(Samples,Scans,Intervals,Points):
    print("sample: {} | scan: {} | interval: {} | point: {}\n".format(sample,scan,interval, point))