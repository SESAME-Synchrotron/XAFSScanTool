import time

from .base import Base
from SEDSS.CLIMessage import CLIMessage
from SEDSS.SEDFileManager import readFile

class KETEK(Base):
	def __init__(self, name, paths, cfg={}):
		super().__init__(name)

		self.loadPVS(name)
		self.paths = paths
		self.cfg = cfg
		self.scanLimits = readFile("configurations/limits.json").readJSON()

		self.PVs["ketek_status_rate"].put(9)
		self.PVs["ketek_data_rate"].put(9)
		self.PVs["ketek_realtime"].put(0.0)
		self.PVs["ketek_livetime"].put(0.0)

	def ACQ(self,args):

		mapScanFlag = False
		try:
			if args["scanTopology"] in ('Snake', 'Sequential', 'Diagonal'):
				FrameDuration = args["FrameDuration"]
				mapScanFlag = True
			else:
				FrameDuration = args["ICsIntTime"]
		except:
			FrameDuration = args["ICsIntTime"]
		self.PVs["ketek_realtime"].put(FrameDuration)

		self.PVs["ketek_erasestart"].put(1, wait=True)

		if mapScanFlag:
			self.data["KETEK-MCA1"]			 = self.PVs["ketek_mca1"].get()
		else:
			Elapsedtime						 = self.data["KETEK-e-time[sec]"] =	self.PVs["ketek_elapsedtime"].get()
			ROIsE							 = [self.PVs["ketek_ROI_0"].get() / Elapsedtime,self.PVs["ketek_ROI_1"].get() / Elapsedtime,self.PVs["ketek_ROI_2"].get() / Elapsedtime,self.PVs["ketek_ROI_3"].get() / Elapsedtime,self.PVs["ketek_ROI_4"].get() / Elapsedtime,self.PVs["ketek_ROI_5"].get() / Elapsedtime,self.PVs["ketek_ROI_6"].get() / Elapsedtime,self.PVs["ketek_ROI_7"].get() / Elapsedtime]
			self.data["KETEK-DEADTIME[%]"]	 = self.PVs["ketek_deadtime"].get()
			self.data["KETEK-INT_TIME[sec]"] = FrameDuration
			self.data["KETEK-If"]			 = ROIsE[0]
			self.data["KETEK-ROI_0[c/s]"]	 = self.PVs["ketek_ROI_0"].get()
			self.data["KETEK-ROI_1[c/s]"]	 = self.PVs["ketek_ROI_1"].get()
			self.data["KETEK-ROI_2[c/s]"]	 = self.PVs["ketek_ROI_2"].get()
			self.data["KETEK-ROI_3[c/s]"]	 = self.PVs["ketek_ROI_3"].get()
			self.data["KETEK-ROI_4[c/s]"]	 = self.PVs["ketek_ROI_4"].get()
			self.data["KETEK-ROI_5[c/s]"]	 = self.PVs["ketek_ROI_5"].get()
			self.data["KETEK-ROI_6[c/s]"]	 = self.PVs["ketek_ROI_6"].get()
			self.data["KETEK-ROI_7[c/s]"]	 = self.PVs["ketek_ROI_7"].get()
			self.data["KETEK-INT_TIME[sec]"] = self.PVs["ketek_livetime"].get()
			self.data["KETEK-OCR"]			 = self.PVs["ketek_dxp_OCR"].get()
			self.data["KETEK-ICR"]			 = self.PVs["ketek_dxp_ICR"].get()

		if self.data["KETEK-If"] == 0:
			CLIMessage("Warning: Please check the KETEK Detector", "W")

	def ACQCont(self, args):

		time.sleep(args["ICsIntTime"] + self.scanLimits["KetekReadoutAvrageTime"])

		Elapsedtime						 = self.data["KETEK-e-time[sec]"] =	self.PVs["ketek_elapsedtime"].get()
		ROIsE							 = [self.PVs["ketek_ROI_0"].get() / Elapsedtime,self.PVs["ketek_ROI_1"].get() / Elapsedtime,self.PVs["ketek_ROI_2"].get() / Elapsedtime,self.PVs["ketek_ROI_3"].get() / Elapsedtime,self.PVs["ketek_ROI_4"].get() / Elapsedtime,self.PVs["ketek_ROI_5"].get() / Elapsedtime,self.PVs["ketek_ROI_6"].get() / Elapsedtime,self.PVs["ketek_ROI_7"].get() / Elapsedtime]
		self.data["KETEK-DEADTIME[%]"]	 = self.PVs["ketek_deadtime"].get()
		self.data["KETEK-INT_TIME[sec]"] = args["ICsIntTime"]
		self.data["KETEK-If"]			 = ROIsE[0]
		self.data["KETEK-ROI_0[c/s]"]	 = self.PVs["ketek_ROI_0"].get()
		self.data["KETEK-ROI_1[c/s]"]	 = self.PVs["ketek_ROI_1"].get()
		self.data["KETEK-ROI_2[c/s]"]	 = self.PVs["ketek_ROI_2"].get()
		self.data["KETEK-ROI_3[c/s]"]	 = self.PVs["ketek_ROI_3"].get()
		self.data["KETEK-ROI_4[c/s]"]	 = self.PVs["ketek_ROI_4"].get()
		self.data["KETEK-ROI_5[c/s]"]	 = self.PVs["ketek_ROI_5"].get()
		self.data["KETEK-ROI_6[c/s]"]	 = self.PVs["ketek_ROI_6"].get()
		self.data["KETEK-ROI_7[c/s]"]	 = self.PVs["ketek_ROI_7"].get()
		self.data["KETEK-INT_TIME[sec]"] = self.PVs["ketek_livetime"].get()
		self.data["KETEK-OCR"]			 = self.PVs["ketek_dxp_OCR"].get()
		self.data["KETEK-ICR"]			 = self.PVs["ketek_dxp_ICR"].get()
		self.PVs["ketek_erasestart"].put(1)

		if self.data["KETEK-If"] == 0:
			CLIMessage("Warning: Please check the KETEK Detector", "W")

	def postACQ(self,args):
		I0Dp	= self.data["IC1[V]"] = args["IC1[V]"]
		ItDp	= self.data["IC2[V]"] = args["IC2[V]"]
		It2Dp	= self.data["IC3[V]"] = args["IC3[V]"]
		IfDp	= self.data["KETEK-If"]
		self.data["TRANS"]			=	self.trydiv(I0Dp,ItDp)
		self.data["TransRef"]		=	self.trydiv(ItDp,It2Dp)
		#self.data["KETEK-FLUOR"]    =	self.trydiv(IfDp,I0Dp)
		self.data["KETEK-FLUOR"]    =	IfDp/I0Dp
