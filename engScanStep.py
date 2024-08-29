#!/usr/bin/python3
"""
Step energy scan derived class
"""
import time
import threading
import shutil
import os
import log
import glob
import epics

from xafs_xrf_step import XAFS_XRFSTEP
from SEDSS.CLIMessage import CLIMessage
from xdiWriter import XDIWriter
from SEDSS.SEDSupport import timeModule
from energyCalibration import energyCalibration

class ENGSCANSTEP(XAFS_XRFSTEP):
	def __init__(self, paths, cfg, testingMode = "No", accPlotting = "No"):
		super().__init__(paths, cfg, testingMode, accPlotting)

		self.startScan()

	def MoveDCM(self, SP, currentScanInfo=None):
		super().MoveDCM(SP)
		time.sleep(2)
		while not self.motors["DCM:Energy:SP"].done_moving:
			if currentScanInfo == None:
				CLIMessage(f"DCM is moving to {SP:.4f}, RBV: {self.PVs['DCM:Energy:RBV'].get():.4f} ... ", "IG")
			else:
				CLIMessage(f"DCM is moving ... to {SP:.4f} for Sample({currentScanInfo[0]['Sample']}), Scan({currentScanInfo[1]['Scan']}) and Interval({currentScanInfo[2]['Interval']})", "IG")
			time.sleep(0.005)
		time.sleep(self.cfg["settlingTime"])

	def startScan(self):
		overAllPointsCounter = 0
		scanCounter = 0
		pauseCounter = 0
		startTime = time.time()

		self.clearPlot()

		log.info("Start data collection ...{}".format(self.userinfo))
		points = map(lambda intv: self.drange(intv["Startpoint"], intv["Endpoint"], intv["Stepsize"]), self.cfg["Intervals"])

		# added by MZ on Aug 24, 2021
		expData = {} # Experimental Data
		previousScan  = None

		for sample, scan, interval in self.generateScanPoints():
			log.info("Data collection: Sample# {}, Scan# {}, Interval# {}".format(sample, scan, interval))
			self.checkPause()
			print("#####################################################")
			CLIMessage("Scan# {}".format(scan), "I")
			CLIMessage("Sample# {}".format(sample), "I")
			CLIMessage("Interval# {}".format(interval), "I")
			print("#####################################################")

			if scan != previousScan:
				previousScan = scan
				log.info("Waiting {} seconds between the scans".format(self.cfg["ScanToScanTime"]))
				if int(self.cfg["ScanToScanTime"]) > 0 and scan != 1:
					timeModule.waitWithProgressBar(int(self.cfg["ScanToScanTime"]))
				if self.accPlotting.strip().lower() != 'yes':
					self.clearPlot()

			# CSS GUI
			self.PVs["SCAN:Nsamples"].put(self.cfg["Nsamples"])
			self.PVs["SCAN:Nscans"].put(self.cfg["Nscans"])
			self.PVs["SCAN:NIntervals"].put(self.cfg["NIntervals"])
			self.PVs["SCAN:CurrentSample"].put(sample)
			self.PVs["SCAN:CurrentScan"].put(scan)
			self.PVs["SCAN:CurrentInterval"].put(interval)

			self.MoveSmpX(self.cfg["Samplespositions"][sample-1]["Xposition"]) # because sample starts from 1
			self.MoveSmpY(self.cfg["Samplespositions"][sample-1]["Yposition"]) # because sample starts from 1

			currentInterval = self.cfg["Intervals"][interval-1]
			startpoint = currentInterval["Startpoint"]
			endpoint = currentInterval["Endpoint"]
			stepsize = currentInterval["Stepsize"]
			FrameDuration = currentInterval["DetIntTime"]
			ICsIntTime = currentInterval["IcsIntTime"]
			stepUnit = currentInterval["stepUnit"]

			newIntervalFlag = True

			if stepUnit == 1:
				points = self.drangeK(startpoint, endpoint, stepsize)
			else:
				points = self.drange(startpoint, endpoint, stepsize)

			for point in points:
				self.checkPause()
				currentScanInfo = []
				currentScanInfo.append({"Sample":sample})
				currentScanInfo.append({"Scan":scan})
				currentScanInfo.append({"Interval":interval})
				currentScanInfo.append({"RINGCurrent":self.PVs["RING:Current"].get()})
				currentScanInfo.append({"sampleTitle":self.cfg["Samplespositions"][sample-1]["sampleTitle"]})

				self.MoveDCM(point, currentScanInfo)
				args = {}
				args["FrameDuration"] = FrameDuration
				args["ICsIntTime"] = ICsIntTime
				args["startNewIntervalFlag"] = False
				if newIntervalFlag:
					args["startNewIntervalFlag"] = True
					newIntervalFlag = False

				ACQdata = {}
				detThreadList = []

				log.info("Prepare a parallel thread for each selected detector")
				for det in self.detectors:
					detThreading = threading.Thread(target=det.ACQ, args=(args,), daemon=True)
					detThreadList.append(detThreading)

				log.info("Start detectors threads")
				for thread in detThreadList:
					thread.start()

				log.info("Joining the detector threads")
				for thread in detThreadList:
					thread.join()

				ACQdata={**ACQdata, **det.data}
				log.info("Collecting data from detectors")
				expData.update(ACQdata)

				log.info("Applying post acquisition for selected detectors if applicable")
				for det in self.detectors:
					det.postACQ(ACQdata)
					ACQdata={**ACQdata, **det.data}
					expData.update(ACQdata)

				Energy = self.PVs["DCM:Energy:RBV"].get()
				log.info("reading DCM energy")

				ACQdata["Sample#"] = sample
				ACQdata["Scan#"] = scan
				ACQdata["Interval"] = interval
				ACQdata["ENERGY-RBK"]	=	Energy
				expData.update(ACQdata)
				I0Dp					=	ACQdata["IC1[V]"]
				ItDp					=	ACQdata["IC2[V]"]
				It2Dp					=	ACQdata["IC3[V]"]
				AbsorptionTrDp			=	ACQdata["TRANS"]
				AbsorptionTr2Dp			=	ACQdata["TransRef"]

				"""
				the following two variables assigned to 0.0
				to avoid the error: local variable 'AbsorptionFluoDp' referenced before assignment
				"""

				IfDp = 0.0
				AbsorptionFluoDp = 0.0

				"""
				try except below has been added to retrieve detector-specific data.
				this is needed when more than one detector is chosen for the experiment
				"""

				try:
					IfDp					=	ACQdata["If"]
					AbsorptionFluoDp		=	ACQdata["FLUOR"]
					log.info("Retrieve If and FLUOR from IC")
				except:
					pass

				try:
					IfDp					=	ACQdata["KETEK-If"]
					AbsorptionFluoDp		=	ACQdata["KETEK-FLUOR"]
					log.info("Retrieve If and FLUOR from KETEK")
				except:
					pass

				try:
					IfDp					=	ACQdata["FICUS-If"]
					AbsorptionFluoDp		=	ACQdata["FICUS-FLUOR"]
					log.info("Retrieve If and FLUOR from FICUS")
				except:
					pass

				self.Energy.append(Energy)
				self.I0.append(I0Dp)
				self.It.append(ItDp)
				self.It2.append(It2Dp)
				self.AbsTr.append(AbsorptionTrDp)
				self.AbsTr2.append(AbsorptionTr2Dp)
				self.If.append(IfDp)
				self.AbsFlu.append(AbsorptionFluoDp)
				self.setPlotData()

				log.info("Writing data to xdi file")

				"""
				(A) Ignore writing points listed in ScanPointsToBeIgnored array in the limits.json file, and,
				(B) Ignore writing data during pausing (shutter stopped, current goes below the limits )
				"""
				if scanCounter in self.scanLimits["ScanPointsToBeIgnored"] or self.PVs["SCAN:pause"].get() == 1:
					pauseCounter = pauseCounter + 1
				else:
					XDIWriter(expData, self.localDataPath, self.detChosen, self.creationTime ,self.expStartTimeDF, self.cfg, currentScanInfo)

				overAllPointsCounter = overAllPointsCounter + 1
				scanCounter = scanCounter + 1
			"""
			Transferring the data after each scan
			"""
			self.dataTransfer()

		print("#########################################################################")
		scanTime = timeModule.timer(startTime)
		log.info("Scan is finished | actual scan time is: {}, total number of points: {}".format(str(scanTime), overAllPointsCounter))
		if pauseCounter > 1:
			log.warning("Ignored points | total number: {}. Check the experiment log file to see what was caused the pausing".format(pauseCounter))
		print("#########################################################################")
		log.info("Data file folder: {}".format(self.localDataPath))
		CLIMessage("Data file folder: {}".format(self.localDataPath), "M")
		print("#################################################")
		os.rename("SED_Scantool.log", "SEDScanTool_{}.log".format(self.creationTime))
		shutil.move("SEDScanTool_{}.log".format(self.creationTime), "{}/SEDScanTool_{}.log".format(self.localDataPath, self.creationTime))
		self.dataTransfer()
		epics.PV("D08-ES-SDD2:setTempMon").put(1)
		epics.PV("D08-ES-SDD2:getDetectorsTemperatures.SCAN").put("10 second")
		epics.PV("D08-ES-SDD2:getFPGAsTempreture.SCAN").put("10 second")
		epics.PV("D08-ES-SDD2:getLDOsTempreture.SCAN").put("10 second")
		epics.PV("D08-ES-SDD2:getADCsTempreture.SCAN").put("10 second")

		if self.cfg["expType"] == "EnergyCalibration":
			i = 0
			os.chdir(self.localDataPath)
			for file in glob.glob("*.xdi"):
				i = i+1

			if i == 1:
				CLIMessage("Calibration xdi file: {}".format(file), "I")
				log.info("Calibration xdi file: {}".format(file))
				x = energyCalibration(file)
			else:
				CLIMessage("More than one xdi files are found in the exp. folder, however only one is expected", "E")
				log.error("More than one xdi files are found in the exp. folder, however only one is expected")
