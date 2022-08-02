import json
import epics
import common
import PyQt5
import sys
import time
from datetime import datetime 
from SEDSS.SEDSupplements import CLIMessage

from .base import Base

class KETEK(Base):
	def __init__(self,name,paths,cfg={}):
		super().__init__(name)

		#print ("pvname::::", name, "pvpath::::;", paths, "cfg::::", cfg)
		self.loadPVS(name)
		self.paths	= paths
		self.cfg = cfg

		self.PVs["ketek_status_rate"].put(9)
		self.PVs["ketek_data_rate"].put(9)
		self.PVs["ketek_realtime"].put(0.0)
		self.PVs["ketek_livetime"].put(0.0)

	def ACQ(self,args):
		#CLIMessage("KETEK-Start ACQ:: {}".format(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')), "E")
		FrameDuration = args["ICsIntTime"]
		#CLIMessage("KETEK FrameDuration:::: {}".format(FrameDuration), "E")
		self.PVs["ketek_realtime"].put(FrameDuration)
		
		#for tr in range(3):
		#	if self.PVs["ketek_ok"].get():
		#		self.PVs["ketek_stop"].put(1)
		#		#time.sleep(0.1)
		self.PVs["ketek_erasestart"].put(1, wait=True)
		#time.sleep(FrameDuration)
		
		#for tr in range(3):
		#	if self.PVs["ketek_ok"].get():
		#		self.PVs["ketek_stop"].put(1)
		#		#time.sleep(0.1)



		Elapsedtime					= 	self.data["KETEK-e-time[sec]"]	=	self.PVs["ketek_elapsedtime"].get()
		ROIsE						=	[self.PVs["ketek_ROI_0"].get() / Elapsedtime,self.PVs["ketek_ROI_1"].get() / Elapsedtime,self.PVs["ketek_ROI_2"].get() / Elapsedtime,self.PVs["ketek_ROI_3"].get() / Elapsedtime,self.PVs["ketek_ROI_4"].get() / Elapsedtime,self.PVs["ketek_ROI_5"].get() / Elapsedtime,self.PVs["ketek_ROI_6"].get() / Elapsedtime,self.PVs["ketek_ROI_7"].get() / Elapsedtime]
		self.data["KETEK-DEADTIME[%]"]	=	self.PVs["ketek_deadtime"].get()
		self.data["KETEK-INT_TIME[sec]"]	=	FrameDuration
		self.data["KETEK-If"]				=	ROIsE[0]
		self.data["KETEK-ROI_0[c/s]"]		=	self.PVs["ketek_ROI_0"].get()
		self.data["KETEK-ROI_1[c/s]"]		=	self.PVs["ketek_ROI_1"].get()
		self.data["KETEK-ROI_2[c/s]"]		=	self.PVs["ketek_ROI_2"].get()
		self.data["KETEK-ROI_3[c/s]"]		=	self.PVs["ketek_ROI_3"].get()
		self.data["KETEK-ROI_4[c/s]"]		=	self.PVs["ketek_ROI_4"].get()
		self.data["KETEK-ROI_5[c/s]"]		=	self.PVs["ketek_ROI_5"].get()
		self.data["KETEK-ROI_6[c/s]"]		=	self.PVs["ketek_ROI_6"].get()
		self.data["KETEK-ROI_7[c/s]"]		=	self.PVs["ketek_ROI_7"].get()
		self.data["KETEK-INT_TIME[sec]"]	=	self.PVs["ketek_livetime"].get()
		self.data["KETEK-OCR"]			=	self.PVs["ketek_dxp_OCR"].get()
		self.data["KETEK-ICR"]			=	self.PVs["ketek_dxp_ICR"].get()

		#print ("-----", self.data["KETEK-IF"])

		if self.data["KETEK-If"] == 0:
			CLIMessage("Warning: Please check the KETEK Detector", "W")
		#CLIMessage("KETEK-End ACQ:: {}".format(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')), "E")

	def postACQ(self,args):
		I0Dp	= self.data["IC1[V]"] = args["IC1[V]"]	
		ItDp	= self.data["IC2[V]"] = args["IC2[V]"]	
		It2Dp	= self.data["IC3[V]"] = args["IC3[V]"]	
		IfDp	= self.data["KETEK-If"]
		#print("I0Dp: ", I0Dp, "ItDp: ", ItDp, "It2Dp: ", It2Dp, "IfDp:", IfDp )
		self.data["TRANS"]			=	self.trydiv(I0Dp,ItDp)
		self.data["TransRef"]		=	self.trydiv(ItDp,It2Dp)
		#print ("Trans: ", self.data["TRANS"], "TransRef: ", self.data["TransRef"])
		#self.data["KETEK-FLUOR"]    =	self.trydiv(IfDp,I0Dp)
		self.data["KETEK-FLUOR"]    =	IfDp/I0Dp
