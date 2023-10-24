import time
import numpy as np
from SEDSS.CLIMessage import CLIMessage
from .base import Base
from SEDSS.SEDFileManager import readFile


class FICUS(Base):
	def __init__(self,name,paths,userinfo,cfg={}):
		super().__init__(name)
		self.loadPVS(name)
		self.paths	= paths
		self.cfg = cfg

		self.PVs["Ficus:Erase"].put(1)
		FicusBaseDir = self.paths["ficus_workstation_data_path"]
		self.PVs["Ficus:Basedir"].put(FicusBaseDir)
		self.PVs["Ficus_ExpID"].put(userinfo["Proposal"])
		self.scanLimites = readFile("configurations/limites.json").readJSON()
		self.FicusReadOutTime = self.scanLimites["FicusReadOutTime"] 
	
	def ACQ(self,args):
		#0: 5ms | 1: 7.5ms | 2: 10ms | 3: 25ms | 4: 50ms | 5: 75ms | 6: 100ms | 7: 250ms | 8: 500ms | 9: 750ms |
		# 10: 1s | 11: 2.5s | 12: 5s | 13: 7.5s | 14: 10s
		FrameDuration = args["FrameDuration"]
		self.PVs["Ficus:FrameDuration"].put(FrameDuration)
		self.PVs["Ficus:Start"].put(1)

		CLIMessage("Set frame duration = {}".format(FrameDuration), "W")
		# CLIMessage("Get frame duration = {}".format(epics.caget("D08-ES-SDD2:getFrameDuration")), "I")
		


		if FrameDuration == 0:
			FrameDuration = 0.005
		elif FrameDuration == 1:
			FrameDuration = 0.0075
		elif FrameDuration == 2:
			FrameDuration = 0.01
		elif FrameDuration == 3:
			FrameDuration = 0.025
		elif FrameDuration == 4:
			FrameDuration = 0.05
		elif FrameDuration == 5:
			FrameDuration = 0.075
		elif FrameDuration == 6: 
			FrameDuration = 0.1
		elif FrameDuration == 7: 
			FrameDuration = 0.25 
		elif FrameDuration ==8:
			FrameDuration = 0.5
		elif FrameDuration == 9:
			FrameDuration = 0.75 
		elif FrameDuration == 10: 
			FrameDuration = 1
		elif FrameDuration ==11:
			FrameDuration = 2.5
		elif FrameDuration == 12:
			FrameDuration = 5
		elif FrameDuration == 13:
			FrameDuration = 7.5
		elif FrameDuration ==14:
			FrameDuration = 10
		else:
			FrameDuration = 1

		CLIMessage("Set frame duration = {}".format(FrameDuration), "W")

		time.sleep(FrameDuration +self.FicusReadOutTime)
		#CLIMessage("Overall duration time : {}".format(FrameDuration+self.FicusReadOutTime))
	
		self.Elapsedtime							=	self.data["FICUS-e-time[sec]"]	=	self.PVs["Ficus:Elapsedtime"].get()
		ROIs								=	self.PVs['Ficus:ROIs'].get()
		ROIsE								= 	np.divide(ROIs,self.Elapsedtime)
		self.data["FICUS-DEADTIME[%]"]		=	np.mean(self.PVs["Ficus:Deadtime"].get())
		self.data["FICUS-INT_TIME[sec]"]	=	FrameDuration
		self.data["FICUS-If"]				=	ROIs[0]
		self.data["FICUS-ROI_0[c/s]"]		=	ROIs[0]
		self.data["FICUS-ROI_1[c/s]"]		=	ROIs[1]
		self.data["FICUS-ROI_2[c/s]"]		=	ROIs[2]
		self.data["FICUS-ROI_3[c/s]"]		=	ROIs[3]
		self.data["FICUS-ROI_4[c/s]"]		=	ROIs[4]
		self.data["FICUS-ROI_5[c/s]"]		=	ROIs[5]
		self.data["FICUS-ROI_6[c/s]"]		=	ROIs[6]
		self.data["FICUS-ROI_7[c/s]"]		=	ROIs[7]

	def postACQ(self,args):
		I0Dp	= self.data["IC1[V]"] = args["IC1[V]"]	
		ItDp	= self.data["IC2[V]"] = args["IC2[V]"]	
		It2Dp	= self.data["IC3[V]"] = args["IC3[V]"]	
		IfDp	= self.data["FICUS-If"]
		self.data["TRANS"]			=	self.trydiv(I0Dp,ItDp)
		self.data["TransRef"]		=	self.trydiv(ItDp,It2Dp)
		#self.data["FICUS-FLUOR"]			=	self.trydiv(IfDp,I0Dp)
		self.data["FICUS-FLUOR"] =	(IfDp/I0Dp)/self.Elapsedtime