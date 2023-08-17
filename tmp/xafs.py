#!/usr/bin/python3
"""
_AN: 

When installing at xafs/xrf bl: 
1. renable file transfer 
2. change fixed directory to experimint directory when finding xdi files
3. Add Offset PV 
"""
import datetime
import decimal
import json
import math
import os
import sys
import time
import itertools
from common import Common
from detectors.ficus import FICUS
from detectors.ketek import KETEK
from detectors.ic import IC
from SEDSS.CLIMessage import CLIMessage
from SEDSS.UIMessage import UIMessage
from SEDSS.SEDFileManager import readFile, path
from SEDSS.SEDTransfer import SEDTransfer
import threading
import log
import shutil 
import signal


try:
	import PyQt5
	import epics
	import numpy as np
except ImportError as e:
	print("Please make sure the following packages are installed:")
	print("PyQt5, epics, numpy")

class XAFS_XRF:
	def __init__(self, paths, cfg, testingMode):
		log.setup_custom_logger("./SED_Scantool.log")
		log.info("Start scanning tool")
		self.loadPVS("xafs")
		self.paths = paths
		self.cfg = cfg
		self.scanLimites = readFile("configurations/limites.json").readJSON()
		log.info("Experiment configurations: ({})".format(json.dumps(self.cfg, indent=2, sort_keys=True)))
		log.info("Experiment scan limites: ({})".format(json.dumps(self.scanLimites, indent=2, sort_keys=True)))
		CLIMessage("Configurations to be implemented: {}".format(self.cfg), "M")
		self.detChosen = None 
		self.userinfo	= Common.loadjson("configurations/userinfo.json")
		self.initPaths()
		self.initDCM()
		self.initDetectors()
		# Set ^C interrupt to abort the scan
		signal.signal(signal.SIGINT, self.signal_handler)
		if testingMode == "No":
			log.info("Testing mode: No")
			self.runPauseMonitor()
		else:
			log.info("Testing mode: Yes")

	def runPauseMonitor(self):
		log.info("start pause trigger monitor") 
		PauseMonitorThread = threading.Thread(target=self.pauseTrigger, args=(), daemon=True)
		PauseMonitorThread.start()
				
	def loadPVS(self,name):
		log.info("load PVs")
		JsonPVlist = Common.loadjson("pvlist/{}.json".format(name))
		self.PVs = {}
		self.motors = {}
		DisconnectedPvs = []
		for entry,pvname in JsonPVlist["PV"].items():
			pvname=pvname["pvname"]
			PVobj = epics.PV(pvname)
			if PVobj.get() is None:
				#print("{} : is not connected\n".format(pvname))
				CLIMessage("{} : is not connected".format(pvname), "E")
				DisconnectedPvs.append("{}\n".format(pvname))
			else:
				#print("{} : is connected\n".format(pvname))
				CLIMessage("{} : is connected".format(pvname), "I")
				self.PVs[entry] = PVobj

		for entry,mtrname in JsonPVlist["Motors"].items():
			pvname=mtrname["pvname"]
			MTRobj = epics.Motor(pvname)
			if MTRobj is None:
				#print("{} : is not connected\n".format(pvname))
				CLIMessage("{} : is not connected".format(pvname), "E")
				DisconnectedPvs.append("{}\n".format(pvname))
			else:
				#print("{} : is connected\n".format(pvname))
				CLIMessage("{} : is connected".format(pvname), "I")
				self.motors[entry] = MTRobj

		if len(DisconnectedPvs):
			log.error("Disconnected PVs: {}".format(DisconnectedPvs))
			Common.show_message(PyQt5.QtWidgets.QMessageBox.Critical,"The following PVs are disconnected:\n {}".format(" ".join(DisconnectedPvs)),"scan tool" ,PyQt5.QtWidgets.QMessageBox.Ok)
			sys.exit() 		
						
	def initPaths(self):
		log.info("Paths initialization")
		self.creationTime = str(time.strftime("%Y%m%dT%H%M%S"))
		self.BasePath			=	"{}/{}-{}".format(self.paths["local_data_path"],self.cfg["DataFileName"],self.creationTime)
		self.cfgfilepath		=	"{}/{}_config_{}.cfg".format(self.BasePath,self.cfg["DataFileName"],self.creationTime) 
		self.localDataPath		=   "{}".format(self.BasePath)

		if not os.path.exists(self.BasePath):
			log.info("Create base directory: {}".format(self.BasePath))
			os.makedirs(self.BasePath)
		
		with open(self.cfgfilepath,'w') as cfgfile:
			json.dump(self.cfg,cfgfile)
			cfgfile.close()

		self.dataFileName	=	"{}-{}.dat".format(self.cfg["DataFileName"], str(datetime.datetime.now()))
		self.dataFileFullPath		=	"{}/{}".format(self.localDataPath, self.dataFileName)
		self.expStartTimeDF = str(time.strftime("%Y-%m-%dT%H:%M:%S")) # to be added to xdi file as a content

		if not os.path.exists(self.localDataPath): 
			os.makedirs(self.localDataPath)

	def drange(self,start,stop,step,prec=10):
		log.info("Calculating energy points")
		decimal.getcontext().prec = prec
		points = []
		r= decimal.Decimal(start)
		step = decimal.Decimal(step)
		while r <=stop:
			points.append(float(r))
			r += step
		return points
	
	def drangeK(self,start,stop,step,prec=10):
		"""
		This function calculates energy in K
		
		Ec_K   : Calibrated Energy K
		
		"""
		try:
			log.info("Calculating energy points in K")
			Ec_K = int(self.cfg["ExpMetaData"][5]["energy"]) / 1000 # calibrated energy 
			nextEnergy = start
			decimal.getcontext().prec = prec
			points = []
			points.append(float(nextEnergy))

			while nextEnergy <= stop:
				deltaE = 4 * step * math.sqrt((nextEnergy - Ec_K)/1000)
				nextEnergy = deltaE + nextEnergy
				points.append(float(nextEnergy))
			
			return points
		except:
			log.error("Energy range is less that the element foil energy. Please rerun the DAQ and enter right parameters in the interval")
			UIMessage("sqrt of negative value!!", 
				"Energy range is less that the element foil energy!!",
				"Please rerun the DAQ and enter right parameters in the interval").showCritical()
			sys.exit()

	def generateScanPoints(self):
		log.info("Calculating samples, scans and Intervals")
		Samples		=	range(1,self.cfg["Nsamples"]+1)
		Scans		=	range(1,self.cfg["Nscans"]+1)
		Intervals	=	range(1,self.cfg["NIntervals"]+1)
		
		return itertools.product(Samples,Scans,Intervals)    	

	def initDCM(self):
		log.info("DCM initialization")
		self.PVs["SCAN:pause"].put(0, wait=True) # set pause flag to Fales 
		self.motors["DCM:Theta"].put("stop_go",0) # Stop
		time.sleep(0.1)
		self.motors["DCM:Theta"].put("stop_go",3) # Go
		time.sleep(0.1)

		self.motors["DCM:Y"].put("stop_go",0) # Stop
		time.sleep(0.1)
		self.motors["DCM:Y"].put("stop_go",3) # Go
		time.sleep(0.1)

		# self.energy0 = self.cfg["Intervals"][0]["Startpoint"]
		# log.info("Move DCM to initial energy ({})".format(self.energy0))
		# #self.MoveDCM(self.energy0)

	def MoveDCM(self,SP, curentScanInfo=None):
		self.motors["DCM:Theta"].put("stop_go",0, wait=True) # Stop
		#time.sleep(0.1)
		self.motors["DCM:Theta"].put("stop_go",3, wait=True) # Go
		#time.sleep(0.1)

		self.PVs["DCM:Energy:SP"].put(SP, wait=True)
		self.PVs["DCM:Move"].put(1, wait=True)
		#time.sleep(0.1) 

		log.info("Move DCM to energy: {}".format(SP))
		while not self.PVs["DCM:Energy:Moving"].get():
			#print("DCM moving ...")
			if curentScanInfo == None:
				CLIMessage("DCM is moving to start point ... ", "I")
			else:
				#print(curentScanInfo)
				CLIMessage("DCM is moving ... to {} for Sample({}), Scan({}) and Interval({})".format(SP, 
					curentScanInfo[0]["Sample"], curentScanInfo[1]["Scan"], curentScanInfo[2]["Interval"]), "IG")
			self.motors["DCM:Theta"].put("stop_go",3)
			self.motors["DCM:Y"].put("stop_go",3)
			self.PVs["DCM:Move"].put(1, wait=True)
			time.sleep(self.cfg["settlingTime"])
			
	def MoveSmpX(self,SP):
		log.info("Move sample X to: {}".format(SP))
		self.motors["SMP:X"].put("stop_go",3) # Go
		self.motors["SMP:X"].move(SP)
		time.sleep(1) 
		while not self.motors["SMP:X"].done_moving:
			CLIMessage("sample X moving ...", "IG")
			time.sleep(1)
	
	def MoveSmpY(self,SP):
		log.info("Move sample Y to: {}".format(SP))
		self.motors["SMP:Y"].put("stop_go",3) # Go
		self.motors["SMP:Y"].move(SP)
		time.sleep(1) 
		while not self.motors["SMP:Y"].done_moving:
			CLIMessage("sample Y moving ...", "IG")
			time.sleep(1)

	def clearPlot(self):
		log.info("Clear plots PVs and parameters")
		self.Energy	= []
		self.I0		= []
		self.It		= []
		self.It2	= []
		self.AbsTr	= []
		self.AbsTr2	= []
		self.If		= []
		self.AbsFlu	= []

		self.PVs["PLOT:Energy"].put(self.Energy)
		self.PVs["PLOT:I0"].put(self.I0)
		self.PVs["PLOT:It"].put(self.It)
		self.PVs["PLOT:It2"].put(self.It2)
		self.PVs["PLOT:AbsTr"].put(self.AbsTr)
		self.PVs["PLOT:AbsTr2"].put(self.AbsTr2)
		self.PVs["PLOT:If"].put(self.If)
		self.PVs["PLOT:AbsFlu"].put(self.AbsFlu)
	
	def setPlotData(self):
		log.info("Setting plots data")
		self.PVs["PLOT:Energy"].put(self.Energy)
		self.PVs["PLOT:I0"].put(self.I0)
		self.PVs["PLOT:It"].put(self.It)
		self.PVs["PLOT:It2"].put(self.It2)
		self.PVs["PLOT:AbsTr"].put(self.AbsTr)
		self.PVs["PLOT:AbsTr2"].put(self.AbsTr2)
		self.PVs["PLOT:If"].put(self.If)
		self.PVs["PLOT:AbsFlu"].put(self.AbsFlu)

	def checkPause(self):
		diffTime = 0 
		pauseFlag = 0 
		startTime = time.time()

		while self.PVs["SCAN:pause"].get():
			pauseFlag = 1
			diffTime = time.time() - startTime
			CLIMessage("Scan is paused | pausing time(sec): {}".format(diffTime), "IO")
			time.sleep(0.1)
		
		if pauseFlag == 1:
			log.warning("Scan was paused | pausing time(sec): %f ", diffTime)	
	
	def pauseTrigger(self): 
		currentOk = True
		shutter1Ok = True
		shutter2Ok = True
		stopperOk = True
		ICI0Ok = True
		KetekROI0Ok = True
		FicusROI0Ok = True

		# imported from limites.json 
		ringLowerCurrent = self.scanLimites["SRLowerCurrent"] 
		ringUpperCurrent = self.scanLimites["SRUpperCurrent"]
		ICI0LowerLimit = self.scanLimites["ICI0LowerLimit"]
		KetekROI0LowerLimit = self.scanLimites["KetekROI0LowerLimit"]
		FicusROI0LowerLimit = self.scanLimites["FicusROI0LowerLimit"]

		#reading detectors PVs
		
		ICsPVs = readFile("pvlist/IC.json").readJSON()
		ICI0Roi0PV = epics.PV(ICsPVs["PV"]["IC0AvrVolt"]["pvname"])
		
		KetekPVs = readFile("pvlist/KETEK.json").readJSON()
		ketekRoi0PV = epics.PV(KetekPVs["PV"]["ketek_ROI_0"]["pvname"])

		FicusPVs = readFile("pvlist/FICUS.json").readJSON()
		FicusRoisPV = epics.PV(FicusPVs["PV"]["Ficus:ROIs"]["pvname"])
		
		"""
		setup writing flages to avoid continues writing logs in the log file
		"""
		currentLogFlag = 0
		shutter1LogFlag = 0
		shutter2LogFlag = 0
		stopperLogFlag = 0
		ICI0LogFlag = 0
		KetekROI0LogFlag = 0
		FicusROI0LogFlag = 0

		while True:

			shutter1Status = self.PVs["SHUTTER1:Status"].get()
			shutter2Status = self.PVs["SHUTTER2:Status"].get()
			StopperStatus = self.PVs["STOPPER:Status"].get()
			currentCurrent = self.PVs["RING:Current"].get()			
			ICI0Readout = ICI0Roi0PV.get()
			KetekROI0Readout = ketekRoi0PV.get()
			FicusROI0Readout = FicusRoisPV.get()

			################### Check current parameters ###############
			if ringLowerCurrent <= currentCurrent <= ringUpperCurrent:
				currentOk = True
				if currentLogFlag == 1: 
					log.warning("SR current is returned to allowed limites, now it is: {} mA."
						.format(currentCurrent))
					currentLogFlag = 0
			else:
				currentOk = False
				if currentLogFlag == 0:
					log.warning("Scan is paused | SR current is: {} mA.".format(currentCurrent))
					currentLogFlag = 1

			################### Check Shutter1 parameters ###############
			#print (self.PVs["SHUTTER1:Status"].get())
			if shutter1Status == 3: # shutter is open 1, closed 0
				shutter1Ok = True
				if shutter1LogFlag == 1: 
					log.warning("Shutter1 status is returned to allowed limites, now it is: open")
					shutter1LogFlag = 0
			else:
				shutter1Ok = False
				if shutter1LogFlag == 0:
					log.warning("Scan is paused | Shutter1 status is: closed")
					shutter1LogFlag = 1

			################### Check Shutter2 parameters ###############
			if shutter2Status == 3: # shutter is open 1, closed 0
				shutter2Ok = True
				if shutter2LogFlag == 1: 
					log.warning("Shutter2 status is returned to allowed limites, now it is: open")
					shutter2LogFlag =0
			else:
				shutter2Ok = False
				if shutter2LogFlag == 0:
					log.warning("Scan is paused | Shutter2 status is: closed")
					shutter2LogFlag = 1
			################### Check stopper parameters ###############
			if StopperStatus == 3: # stopper is open 1, closed 0
				stopperOk = True
				if stopperLogFlag == 1: 
					log.warning("stopper status is returned to allowed limites, now it is: open")
					stopperLogFlag = 0 
			else:
				stopperOk = False
				if stopperLogFlag == 0:
					log.warning("Scan is paused | stopper status is: closed")
					stopperLogFlag = 1

			#################### Check ROIs if current, shutters and stopper are okay ###############
			if currentOk and shutter1Ok and shutter2Ok and stopperOk == True:
				#################### Check ICROI0 ####################
				if ICI0Readout >= ICI0LowerLimit:
					ICI0Ok = True
					if ICI0LogFlag == 1: 
						log.warning("ICI0 value is returned to allowed limites, it is now {}"
							.format(ICI0Readout))
						ICI0LogFlag = 0
				else:
					ICI0Ok = False
					if ICI0LogFlag == 0: 
						log.warning("Scan is paused | ICI0 readout({}) is below the allowed limit ({})"
							.format(ICI0Readout,ICI0LowerLimit))
						ICI0LogFlag = 1

				#################### Check KETEKROI0 ####################
				if "KETEK" in self.detChosen: 
					if KetekROI0Readout >= KetekROI0LowerLimit:
						KetekROI0Ok = True
						if KetekROI0LogFlag == 1: 
							log.warning("ketek_ROI_0 value is returned to allowed limites, it is now {}"
								.format(KetekROI0Readout))
							KetekROI0LogFlag = 0
					else:
						KetekROI0Ok = False
						if KetekROI0LogFlag == 0: 
							log.warning("Scan is paused | ketek_ROI_0 readout({}) is below the allowed limit ({})"
								.format(KetekROI0Readout,KetekROI0LowerLimit))
							KetekROI0LogFlag = 1

				#################### Check FICUSROI0 ####################
				if "FICUS" in self.detChosen:
					if FicusROI0Readout[0] >= FicusROI0LowerLimit:
						FicusROI0Ok = True
						if FicusROI0LogFlag == 1: 
							log.warning("FICUS_ROI_0 value is returned to allowed limites, it is now {}"
								.format(FicusROI0Readout))
							FicusROI0LogFlag = 0
					else:
						FicusROI0Ok = False
						if FicusROI0LogFlag == 0: 
							log.warning("Scan is paused | FICUS_ROI_0 readout({}) is below the allowed limit ({})"
								.format(FicusROI0Readout,FicusROI0LowerLimit))
							FicusROI0LogFlag = 1

			# if any of below is false, pause the scan 
			if False in (currentOk, shutter1Ok, shutter2Ok, stopperOk, 
				ICI0Ok, KetekROI0Ok, FicusROI0Ok): 
				self.PVs["SCAN:pause"].put(1) # 1 pause, 0 release 
			else:
				self.PVs["SCAN:pause"].put(0)

			time.sleep(self.scanLimites["checkLimitesEvery"]) # time in seconds 

	def initDetectors(self):
		#self.available_detectors = ["IC1","IC2","IC3","KETEK","FICUS"]
		log.info("Detectors initialization")
		self.available_detectors = ["IC","KETEK","FICUS"]

		self.Ingtime = [0.005, 0.0075, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10]
		self.detectors = []

		detlist = self.cfg["detectors"]
		log.info("Chosen detectors are {}".format(detlist))
		self.detChosen = detlist
		for det in detlist:
			if det in ("IC1", "IC2", "IC3"):
				cfg={}
				self.detectors.append(IC("IC", self.paths))
			elif det == "KETEK":
				self.detectors.append(KETEK("KETEK",self.paths))
			elif det == "FICUS":
				self.detectors.append(FICUS("FICUS",self.paths,self.userinfo))
			elif not det in self.available_detectors:
				raise Exception("Unknown detector")
				log.error("Unknown detector is Chosen")
	
	def getStepSizeK(self, currentEnergy_eV, stepSize_K):

		"""
		This function calculates the step size in eV 
		
		Ec_eV   : Calibrated Energy eV 
		Ek      : Energy in K(1/A)
		Etarget : Energy that we are going to. 

		Ek = sqrt ( (Etarget - Ec_eV) / 3.81 )
		E_eV = 3.81 * (E_K)^2 + Ec_eV
		"""

		log.info("Calculating step size in K(1/A)")
		Ec_eV = int(self.cfg["ExpMetaData"][5]["energy"]) / 1000 # calibrated energy 
		print ("Ec_eV:::", Ec_eV, "currentEnergy_eV ::::", currentEnergy_eV)
		Ek = math.sqrt((currentEnergy_eV - Ec_eV)/3.81) # energy in K(1/A)
		targetEnergy_K = Ek + stepSize_K
		targetEnergy_eV = 3.81 * ( targetEnergy_K**2 + Ec_eV/3.81 ) # convert back the target energy to eV. 
		stepSize_eV = targetEnergy_eV - currentEnergy_eV

		print("step size ev ::::",stepSize_eV)

		return stepSize_eV

	def dataTransfer(self):
		try:
			SEDTransfer(self.localDataPath, self.paths["AutoCopyDS"]).scp()
			if self.cfg["expType"] == "proposal":
				SEDTransfer(self.localDataPath, self.paths["DS"]+":"+self.userinfo["Experimental_Data_Path"]).scp()
			else: 
				IHPath = path(self.paths['SED_TOP'], beamline = 'XAFS').getIHPath()
				SEDTransfer(self.localDataPath, self.paths["DS"]+":"+IHPath).scp()
			log.info("Data transfer is done")
		except:
			log.error("Problem transfering the data")

	
	def signal_handler(self, sig, frame):
		"""Calls abort_scan when ^C is typed"""
		if sig == signal.SIGINT:
			log.warning("Ctrl + C (^C) has been pressed, runinig scan is terminated !!")
			os.rename("SED_Scantool.log", "SEDScanTool_{}.log".format(self.creationTime))
			shutil.move("SEDScanTool_{}.log".format(self.creationTime), "{}/SEDScanTool_{}.log".format(self.localDataPath, self.creationTime))
			self.dataTransfer()
			sys.exit()