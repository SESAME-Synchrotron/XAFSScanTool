import math
import sys
import epics
from SEDSS.SEDSupplements import CLIMessage

sys.path.append("..")
from common import Common

class Base:
	def __init__(self,name):
		"""
		Added by MZ. 
		the follwoing elements are default as IC detector should be chosen all the time. 
		"""
		self.name = name
		self.data = {}
		self.data["Sample#"]		=	0
		self.data["Scan#"]			=	0
		self.data["Interval"]		=	0
		self.data["ENERGY-RBK"]		=	0
		self.data["IC1[V]"]			=	0
		self.data["IC2[V]"]			=	0
		self.data["IC3[V]"]			=	0
		self.data["TRANS"]			=	0
		self.data["TransRef"]		=	0
		if name == "KETEK": 
			self.data["KETEK-If"] = 0
			self.data["KETEK-FLUOR"] = 0
			self.data["KETEK-ROI_0[c/s]"] =	0
			self.data["KETEK-ROI_1[c/s]"] =	0
			self.data["KETEK-ROI_2[c/s]"] =	0
			self.data["KETEK-ROI_3[c/s]"] =	0
			self.data["KETEK-ROI_4[c/s]"] =	0
			self.data["KETEK-ROI_5[c/s]"] =	0
			self.data["KETEK-ROI_6[c/s]"] =	0
			self.data["KETEK-ROI_7[c/s]"] =	0
			self.data["KETEK-e-time[sec]"] = 0
			self.data["KETEK-DEADTIME[%]"] = 0
			self.data["KETEK-INT_TIME[sec]"] = 0
			self.data["KETEK-OCR"] = 0
			self.data["KETEK-ICR"] = 0
		
		elif name == "FICUS": 
			self.data["FICUS-If"] = 0
			self.data["FICUS-FLUOR"] = 0
			self.data["FICUS-ROI_0[c/s]"] =	0
			self.data["FICUS-ROI_1[c/s]"] =	0
			self.data["FICUS-ROI_2[c/s]"] =	0
			self.data["FICUS-ROI_3[c/s]"] =	0
			self.data["FICUS-ROI_4[c/s]"] =	0
			self.data["FICUS-ROI_5[c/s]"] =	0
			self.data["FICUS-ROI_6[c/s]"] =	0
			self.data["FICUS-ROI_7[c/s]"] =	0
			self.data["FICUS-e-time[sec]"] = 0
			self.data["FICUS-DEADTIME[%]"] = 0
			self.data["FICUS-INT_TIME[sec]"] = 0
			self.data["FICUS-OCR"] = 0
			self.data["FICUS-ICR"] = 0


	def loadPVS(self,name):
		JsonPVlist = Common.loadjson('pvlist/{}.json'.format(name))
		self.PVs = {}
		DisconnectedPvs = []
		for entry,pvname in JsonPVlist["PV"].items():
			pvname=pvname["pvname"]
			PVobj = epics.PV(pvname)

			#print ("DIR PVO:::", dir(PVobj))
			if PVobj.get() is None:
				#print("{} : is not connected\n".format(pvname))
				CLIMessage("{} : is not connected".format(pvname), "E")
				DisconnectedPvs.append("{}\n".format(pvname))
			else:
				#print("{} : is connected\n".format(pvname))
				CLIMessage("{} : is connected".format(pvname), "I")
				self.PVs[entry] = PVobj

	def preACQ(self,*args,**kwargs):
		print(self.name, " preACQ is not implemented")
	
	def ACQ(self,*args,**kwargs):
		print(self.name, " ACQ is not implemented")
	
	def postACQ(self,*args,**kwargs):
		pass
		#print(self.name, " postACQ is not implemented")

	
	def trydiv(self,val1,val2):
		try:
			return math.log(val1 / val2)
		except:
			return 0