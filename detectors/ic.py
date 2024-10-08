import time
from SEDSS.CLIMessage import CLIMessage
from SEDSS.SEDFileManager import readFile
from .base import Base

class IC(Base):
	def __init__(self,name,paths,cfg={}):
		#print ("----- IC name: ", name)
		super().__init__(name)
		self.loadPVS(name)
		self.scanLimits = readFile("configurations/limits.json").readJSON()

	def ACQ(self,args):
		#CLIMessage("IC-Start ACQ:: {}".format(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')), "E")
		intTime = args["ICsIntTime"]
		self.PVs["ICsAvrTime"].put(float(intTime))
		time.sleep(int(intTime) + self.scanLimits["ICsReadoutAvrageTime"])

		IC0avg = self.PVs["IC0AvrVolt"].get()
		#CLIMessage("IC1 ACQ Done:: {}".format(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')), "M")
		self.data["IC1[V]"]	=	IC0avg if IC0avg > 5e-10 else 1E-16

		IC1avg = self.PVs["IC1AvrVolt"].get()
		#CLIMessage("IC2 ACQ Done:: {}".format(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')), "M")
		self.data["IC2[V]"]	=	IC1avg if IC1avg > 5e-10 else 1E-16

		IC2avg = self.PVs["IC2AvrVolt"].get()
		#CLIMessage("IC3 ACQ Done:: {}".format(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')), "M")
		self.data["IC3[V]"]	=	IC2avg if IC2avg > 5e-10 else 1E-16

		if 1E-16 in {self.data["IC3[V]"], self.data["IC2[V]"], self.data["IC1[V]"]}:
			CLIMessage("Warning: Please check the IC Detector", "W")

		I0Dp	= self.data["IC1[V]"]
		ItDp	= self.data["IC2[V]"]
		It2Dp	= self.data["IC3[V]"]
		#IfDp	= self.data["If"]
		self.data["TRANS"]			=	self.trydiv(I0Dp,ItDp)
		self.data["TransRef"]		=	self.trydiv(ItDp,It2Dp)

	def ACQCont(self,args):
		#CLIMessage("IC-Start ACQ:: {}".format(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')), "E")
		intTime = args["ICsIntTime"]
		self.PVs["ICsAvrTime"].put(float(intTime))
		time.sleep(int(intTime) + self.scanLimits["ICsLatency"] + self.scanLimits["ICsReadoutAvrageTime"])

		IC0avg = self.PVs["IC0AvrVolt"].get()
		#CLIMessage("IC1 ACQ Done:: {}".format(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')), "M")
		self.data["IC1[V]"]	=	IC0avg if IC0avg > 5e-10 else 1E-16

		IC1avg = self.PVs["IC1AvrVolt"].get()
		#CLIMessage("IC2 ACQ Done:: {}".format(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')), "M")
		self.data["IC2[V]"]	=	IC1avg if IC1avg > 5e-10 else 1E-16

		IC2avg = self.PVs["IC2AvrVolt"].get()
		#CLIMessage("IC3 ACQ Done:: {}".format(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')), "M")
		self.data["IC3[V]"]	=	IC2avg if IC2avg > 5e-10 else 1E-16

		if 1E-16 in {self.data["IC3[V]"], self.data["IC2[V]"], self.data["IC1[V]"]}:
			CLIMessage("Warning: Please check the IC Detector", "W")

		I0Dp	= self.data["IC1[V]"]
		ItDp	= self.data["IC2[V]"]
		It2Dp	= self.data["IC3[V]"]
		#IfDp	= self.data["If"]
		self.data["TRANS"]			=	self.trydiv(I0Dp,ItDp)
		self.data["TransRef"]		=	self.trydiv(ItDp,It2Dp)
