#!/usr/bin/python3
"""
Continuous energy scan derived class
"""

import os
import time
import threading
import shutil
import numpy as np
import decimal
import log

from linearIntervals import LINEARINTERVALS
from xafs_xrf_cont import XAFS_XRFCONT
from SEDSS.CLIMessage import CLIMessage
from xdiWriter import XDIWriter
from SEDSS.SEDSupport import timeModule

class ENGSCANCONT(XAFS_XRFCONT):
	def __init__(self, paths, cfg, testingMode="No", accPlotting="No"):
		super().__init__(paths, cfg, testingMode, accPlotting)

		self.lock = 0
		self.linearInterval = LINEARINTERVALS(self.cfg)
		self.startScan()

	def MoveDCM(self, SP, speed, currentScanInfo=None):
		super().MoveDCM(SP, speed)
		time.sleep(2)
		while not self.motors["DCM:Energy:SP"].done_moving:
			if currentScanInfo == None:
				CLIMessage(f"DCM is moving to {SP:.4f}, RBV: {self.PVs['DCM:Energy:RBV'].get():.4f} ... ", "IG")
			else:
				CLIMessage(f"DCM is moving ... to {SP:.4f}, RBV: {self.PVs['DCM:Energy:RBV'].get():.4f} for Sample({currentScanInfo[0]['Sample']}), Scan({currentScanInfo[1]['Scan']}) and Interval({currentScanInfo[2]['Interval']})", "IG")
			time.sleep(0.005)

	def startScan(self):
		overAllPointsCounter = 0
		scanCounter = 0
		pauseCounter = 0
		startTime = time.time()

		self.clearPlot()

		log.info(f"Start data collection ...{self.userinfo}")
		point =	map(lambda intv: self.drange(intv["Startpoint"], intv["Endpoint"], intv["Stepsize"]), self.cfg["Intervals"])

		expData = {} # Experimental Data

		previousScan  = None
		index = 1
		for sample, scan, interval in self.generateScanPoints():
			log.info(f"Data collection: Sample# {sample}, Scan# {scan}, Interval# {interval}")
			self.checkPause()
			print ("#####################################################")
			CLIMessage(f"Scan# {scan}", "I")
			CLIMessage(f"Sample# {sample}", "I")
			CLIMessage(f"Interval# {interval}", "I")
			print ("#####################################################")

			if scan != previousScan:
				previousScan = scan
				log.info(f"Waiting {self.cfg['ScanToScanTime']} seconds between the scans")
				if int (self.cfg["ScanToScanTime"]) > 0 and scan != 1:
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
			stepsize = currentInterval["Stepsize"]
			ICsIntTime = currentInterval["IcsIntTime"]
			stepUnit = currentInterval["stepUnit"]

			if "KETEK" in self.cfg["detectors"]:
				log.info(f"prepare pulse block, width: {ICsIntTime} sec")
				self.pandaBox.pulse(1, ICsIntTime, 1)

			self.PVs["ketek_realtime"].put(ICsIntTime)
			self.PVs["ketek_erasestart"].put(1)

			linearIntervals = self.cfg['linearIntervals(LI)'][interval-1]
			linearIntervalsCounts = len(linearIntervals['linearIntervalValue'])
			for i, LI in enumerate(linearIntervals['linearIntervalValue']):
				log.info("#" * 50)
				startpoint = LI[0]
				endpoint = LI[-1]
				speed = linearIntervals['linearIntervalsSpeed'][i]

				log.info(f"Linear Interval #{index}: {LI}, Interval Speed: {speed} deg/s")

				newIntervalFlag = True
				if stepUnit == 1:
					points = self.drangeK(startpoint, endpoint, stepsize)
				else:
					points = self.drange(startpoint, endpoint, stepsize)

				theta = self.linearInterval.getThetaPosition(np.array(points))
				theta = theta if i+1 == linearIntervalsCounts else theta[:-1]

				theta2encoder = (theta + abs(self.PVs["DCM:Offset"].get())) / self.scanLimits["monoThetaResolution"]

				log.info(f"Energy Start: {startpoint}, Energy End: {endpoint}")
				log.info(f"Theta Start: {theta[0]}, Theta End: {theta[-1]}")
				log.info(f"Encoder Start: {int(theta2encoder[0])}, Encoder End: {int(theta2encoder[-1])}")

				log.info(f"prepare sequencer table, interval points: {len(points)}")
				self.pandaBox.sendTable(1, 1, 8, [int(val) for val in theta2encoder], 1, [1,0,0,0,0,0], 0, [0,0,0,0,0,0])

				log.warning("move DCM to start point at default speed")
				self.MoveDCM(startpoint, self.scanLimits["monoThetaDefaultSpeed"])

				log.info("prepare pandABlocks")
				self.pandaBox.disableBit("A")
				self.pandaBox.enableBit("A")

				log.info("go to end point ...")
				moveThread = threading.Thread(target=self.MoveDCM, args=(endpoint, speed,), daemon=True)
				moveThread.start()

				energyPoint = 0
				for val in theta2encoder:
					while True:
						encoderReadout = int(self.PVs["DCM:Encoder"].get())
						if encoderReadout <= int(val):
							log.info("-" * 50)
							log.info(f"encoder value (actual, RBV): ({int(val)}, {encoderReadout})")

							self.checkPause()

							currentScanInfo = []
							currentScanInfo.append({"Sample":sample})
							currentScanInfo.append({"Scan":scan})
							currentScanInfo.append({"Interval":interval})
							currentScanInfo.append({"RINGCurrent":self.PVs["RING:Current"].get()})
							currentScanInfo.append({"sampleTitle":self.cfg["Samplespositions"][sample-1]["sampleTitle"]})

							args = {}
							args["ICsIntTime"] = ICsIntTime
							args["startNewIntervalFlag"] = False

							if newIntervalFlag:
								args["startNewIntervalFlag"] = True
								newIntervalFlag = False

							ACQdata = {}
							detThreadList = []

							log.info("Prepare a parallel thread for each selected detector")
							for det in self.detectors:
								detThreading = threading.Thread(target=det.ACQCont, args=(args,), daemon=True)
								detThreadList.append(detThreading)

							log.info("Start detectors threads")
							log.info("Start collecting data from detectors")
							for thread in detThreadList:
								thread.start()

							log.info("Joining the detector threads")
							for thread in detThreadList:
								thread.join()
							log.info("collecting data from detectors is done")

							for det in self.detectors:
								ACQdata = {**ACQdata, **det.data}
								expData.update(ACQdata)

							log.info("Applying post acquisition for selected detectors if applicable")
							for det in self.detectors:
								det.postACQ(ACQdata)
								ACQdata = {**ACQdata, **det.data}
								expData.update(ACQdata)

							Energy = points[energyPoint]
							ACQdata["Sample#"] = sample
							ACQdata["Scan#"] = scan
							ACQdata["Interval"] = interval
							ACQdata["ENERGY-RBK"] =	Energy
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
							scanPaused = self.PVs["SCAN:pause"].get()
							if scanCounter in self.scanLimits["ScanPointsToBeIgnored"] or scanPaused == 1:
								pauseCounter = pauseCounter + 1
							else:
								XDIWriter(expData, self.localDataPath, self.detChosen, self.creationTime ,self.expStartTimeDF, self.cfg, currentScanInfo)

							"""
							Stop DCM in case scan paused
							"""
							if scanPaused == 1:
								self.PVs["DCM:Ctrl"].put(1)
								while self.PVs["SCAN:pause"].get() == 1:
									time.sleep(0.005)
								self.PVs["DCM:Ctrl"].put(3)
								self.motors["DCM:Energy:SP"].move(endpoint)

							overAllPointsCounter = overAllPointsCounter + 1
							scanCounter = scanCounter + 1
							break
						time.sleep(0.005)
					energyPoint = energyPoint + 1
				index = index + 1
				"""
				Transferring the data after each sub-interval
				"""
				self.dataTransfer()

		print("#########################################################################")
		scanTime = timeModule.timer(startTime)
		log.info(f"Scan is finished | actual scan time is: {str(scanTime)}, total number of points: {overAllPointsCounter}")
		if pauseCounter > 1:
			log.warning(f"Ignored points | total number: {pauseCounter}. Check the experiment log file to see what was caused the pausing")
		print("#########################################################################")
		log.info(f"Data file folder: {self.localDataPath}")
		CLIMessage(f"Data file folder: {self.localDataPath}", "M")
		print("#################################################")
		os.rename(f"SED_Scantool.log", f"SEDScanTool_{self.creationTime}.log")
		shutil.move(f"SEDScanTool_{self.creationTime}.log", f"{self.localDataPath}/SEDScanTool_{self.creationTime}.log")
		self.PVs["DCM:Speed"].put(float(self.scanLimits["monoThetaDefaultSpeed"]))
		self.dataTransfer()

	def drange(self, start, stop, step, prec=10):
		log.info("Calculating energy points")
		decimal.getcontext().prec = prec

		# (quantize(decimal.Decimal('1.0000')) solve floating points issue
		start = decimal.Decimal(start).quantize(decimal.Decimal('1.0000'))
		stop = decimal.Decimal(stop).quantize(decimal.Decimal('1.0000'))
		step = decimal.Decimal(step)

		points = []
		r = start

		while r <= stop:
			points.append(float(r))
			r += step

		return points

	def signal_handler(self, sig, frame):
		if self.lock != 2:
			self.lock = self.lock + 1
			log.warning("disable pandABlocks")
			self.pandaBox.disableBit("A")
			log.warning("stop DCM")
			self.PVs["DCM:Ctrl"].put(0)
			time.sleep(1)
			self.PVs["DCM:Ctrl"].put(3)
			self.PVs["DCM:Speed"].put(float(self.scanLimits["monoThetaDefaultSpeed"]))
			super().signal_handler(sig, frame)
