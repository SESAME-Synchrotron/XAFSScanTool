'''
Step mapping scan derived class

'''
import sys
import os 
import log
import time
import zmq
import threading
import numpy as np
import shutil
from epics import PV

from SEDSS.CLIMessage import CLIMessage
from SEDSS.UIMessage import UIMessage
from SEDSS.SEDFileManager import readFile
from SEDSS.SEDSupport import timeModule

from xafs_xrf_step import XAFS_XRFSTEP
from ZMQWriter import ZMQWriter

h5CfgFile = "configurations/XAFS_Writer.json"
class MAPSCAN (XAFS_XRFSTEP):
	def __init__(self, paths, cfg, testingMode="No", accPlotting="No"):
		super().__init__(paths, cfg, testingMode, accPlotting)

		self.ROIXStart     = self.cfg['ROIXStart']
		self.ROIXEnd       = self.cfg['ROIXEnd']
		self.ROIYStart     = self.cfg['ROIYStart']
		self.ROIYEnd       = self.cfg['ROIYEnd']
		self.scanResX      = self.cfg['ResX']
		self.scanResY      = self.cfg['ResY']
		self.rotStageAngle = self.cfg["ROIRot"]
		self.scanEnergy    = self.cfg['Energy']
		self.scanTopology  = self.cfg["ExpMetaData"][6]["mapScanTopology"]
		self.FrameDuration = self.cfg["IntTime"]

		""" read XAFS_writer cfg file"""
		self.h5cfg = readFile(h5CfgFile).readJSON()

		""" create zmq socket as publisher """
		ZMQSettings = self.h5cfg["ZMQSettings"]["ZMQSenderSettings"]
		ZMQSender = ZMQSettings["ZMQSender"]
		ZMQSPort = ZMQSettings["ZMQPort"]
		ZMQSProtocol = ZMQSettings["ZMQProtocol"]
		ZMQSender = ZMQSProtocol + "://" + ZMQSender + ":" + ZMQSPort
		self.numChannels = PV(self.h5cfg["EPICSandIOCs"]["KETEKNumChannels"]).get(timeout=1, use_monitor=False)
		context = zmq.Context()
		self.sock = context.socket(zmq.PUB)
		self.sock.connect(ZMQSender)  	# Connect instead of bind for the server

		self.writePVS()		# write the config data in PVs

		""" setup h5 file layout """
		h5Layout = threading.Thread(target=self.setupH5DXLayout, args=())
		h5Layout.start()
		h5Layout.join()		# waiting until finishing setup h5 layout

		self.checkMapScanPara()
		self.MoveDCM(self.scanEnergy)
		self.startScan()

	def MoveDCM(self, SP):
		super().MoveDCM(SP)
		log.info('Moving to start energy: {}'.format(SP))
		while not self.motors["DCM:Energy:SP"].done_moving:
			CLIMessage("DCM is moving to scan energy {}... ".format(SP), "IG")
			self.motors["DCM:Y"].put("stop_go",3)
			time.sleep(self.cfg["settlingTime"])

	def checkMapScanPara (self):
		if float(self.cfg['ResX']) < self.motors["SMP:X"].MRES:
			UIMessage("Not allowed settings",
				"X resolution scan parameter is less that the X axis motor resolution!!",
				"Please rerun the DAQ and enter correct parameters").showCritical()
			log.error('X resolution scan parameter is less that the X axis motor resolution!!')
			sys.exit()

		if float(self.cfg['ResY']) < self.motors["SMP:Y"].MRES:
			UIMessage("Not allowed settings",
				"Y resolution scan parameter is less that the Y axis motor resolution!!",
				"Please return the DAQ and enter correct parameters").showCritical()
			log.error('Y resolution scan parameter is less that the Y axis motor resolution!!')
			sys.exit()

	def diagonalScanPoints (self, xRange, yRange):
		"""
		A method to return the xArray and yArray to scan in diagonal shape.
		the method returns the follwoing:
		xArray: contains the positions for motor X
		yArray: contains the positions for motor y
		xIndex: snak matrix index for x motor
		yIndex: snak matrix index for y motor
		positionMatrix:  a numpy matrix includes all positions
		"""
		positionsMatrix = np.zeros((len(yRange), len(xRange), 2))

		for y in range(len(yRange)):
			for x in range(len(xRange)):
				positionsMatrix[y, x] = [xRange[x], yRange[y]]

		rows, cols, pair = positionsMatrix.shape
		xArrayPos   = []
		xArrayIndex = []
		yArrayPos   = []
		yArrayIndex = []

		for diag in range(rows + cols - 1):
			for i in range(max(0, diag - cols + 1), min(diag + 1, rows)):
				j = diag - i
				xArrayPos.append(positionsMatrix[i,j,0])
				xArrayIndex.append(j)
				yArrayPos.append(positionsMatrix[i,j,1])
				yArrayIndex.append(i)

		return xArrayPos, yArrayPos, xArrayIndex, yArrayIndex

	def snakeScanPoints(self, xRange, yRange):
		"""
		A method to return back the xArray and yArray to scan in snake shape
		xArray: contains the positions for motor X
		yArray: contains the positions for motor y
		xIndex: snak matrix index for x motor
		yIndex: snak matrix index for y motor
		"""

		xArray   = []
		yArray   = []
		xIndex   = []
		yIndex   = []
		xRevTemp = [] 

		positionsMatrix = np.zeros((len(yRange), len(xRange), 2))
		for y in range(len(yRange)):
			for x in range(len(xRange)):
				positionsMatrix[y, x] = [xRange[x], yRange[y]]

		for i in range(len(positionsMatrix)):
			if i % 2 == 0:
				for x in range (len(xRange)):
					xArray.append(positionsMatrix[i][x][0])
					xIndex.append(x)
					yArray.append(positionsMatrix[i][x][1])
					yIndex.append(i)
			else:
				inversedMatrixRow = positionsMatrix[i][::-1] # reverse the the row order
				xRevTemp.clear()
				for x in range (len(xRange)):
					xArray.append(inversedMatrixRow[x][0])
					xRevTemp.append(x)
					yArray.append(inversedMatrixRow[x][1])
					yIndex.append(i)
				xIndex = xIndex + xRevTemp[::-1] # reverse x index
				
		return xArray, yArray, xIndex, yIndex

	def startScan(self):
		"""
		this function is the main function to perform mapping scan
		"""

		startTime = time.time()
		mcaData = None
		self.xRange = self.drange(self.ROIXStart, self.ROIXEnd, self.scanResX)
		self.yRange = self.drange(self.ROIYStart, self.ROIYEnd, self.scanResY)
		log.info ('Scan range for X axis: {}'.format(self.xRange))
		log.info ('Scan range for Y axis: {}'.format(self.yRange))
		log.info('Scan Topology: {}'.format(self.scanTopology))

		self.MoveSmpRot(self.rotStageAngle)

		if self.scanTopology == 'Sequential':

			""" start zmq reciever socket """
			zmqRec = threading.Thread(target=self.startZMQ, args=(self.xRange, self.yRange,), daemon=True)		# run ZMQ reciever socket in background
			zmqRec.start()

			overAllPointsCounter = len(self.xRange) * len(self.yRange)
			for y in self.yRange:
				self.checkPause()
				log.info('Moving sample stage Y to: {}'.format(y))
				self.MoveSmpY(y)
				for x in self.xRange:
					self.checkPause()
					log.info('Moving sample stage X to: {}'.format(x))
					self.MoveSmpX(x)
					log.info('Collecting data for the scan point: ({},{})'.format(x,y))
					mcaData = self.getDetectorData()
					# print(mcaData)
					try:
						# self.sock.send_pyobj(list(range(0,2048)))
						self.sock.send_pyobj(list(mcaData[:self.numChannels]))		# send MCA data array with the dimension of #channels

					except:
						self.sock.send_pyobj("timeout")		# parse "timeout" if PV not acquired
			self.closeH5File()

		else:
			if self.scanTopology == 'Snake':
				xScanPoints, yScanPoints, xScanIndex, yScanIndex = self.snakeScanPoints(self.xRange,self.yRange)
			elif self.scanTopology == 'Diagonal':
				xScanPoints, yScanPoints, xScanIndex, yScanIndex = self.diagonalScanPoints(self.xRange,self.yRange)
			overAllPointsCounter = len(xScanPoints)

			""" start zmq reciever socket """
			zmqRec = threading.Thread(target=self.startZMQ, args=(self.xRange, self.yRange,self.scanTopology, xScanIndex, yScanIndex,), daemon=True)	# run ZMQ reciever socket in background
			zmqRec.start()

			for i in range (len(xScanPoints)):
				self.checkPause()
				log.info('Move sample X to: {}'.format(xScanPoints[i]))
				self.MoveSmpX(xScanPoints[i])
				log.info('Move sample Y to: {}'.format(yScanPoints[i]))
				self.MoveSmpY(yScanPoints[i])
				log.info('Collecting data for the scan point: ({},{})'.format(xScanPoints[i],yScanPoints[i]))
				mcaData = self.getDetectorData()
				# print(mcaData)
				try:
					# self.sock.send_pyobj(list(range(0,2048)))
					self.sock.send_pyobj(list(mcaData[:self.numChannels]))		# send MCA data array with the dimension of #channels

				except:
					self.sock.send_pyobj("timeout")		# parse "timeout" if PV not acquired
			self.closeH5File()

		time.sleep(1)
		print("#########################################################################")
		scanTime = timeModule.timer(startTime)
		log.info("Scan is fininshed | actual scan time is: {}, total number of points: {}".format(str(scanTime), overAllPointsCounter))
		print("#########################################################################")
		log.info("Data file folder: {}".format(self.localDataPath))
		CLIMessage("Data file folder: {}".format(self.localDataPath),"M")
		print("#################################################")
		os.rename("SED_Scantool.log", "SEDScanTool_{}.log".format(self.creationTime))
		shutil.move("SEDScanTool_{}.log".format(self.creationTime), "{}/SEDScanTool_{}.log".format(self.localDataPath, self.creationTime))
		self.dataTransfer()
	
	def getDetectorData(self):

		args 		  = {}
		ACQdata 	  = {}
		detThreadList = []
		expData 	  = {}
		
		args["FrameDuration"] = self.FrameDuration
		args["scanTopology"] = self.scanTopology

		log.info("Collecting data from choosen detectors")
		for det in self.detectors:
			detThreading = threading.Thread(target=det.ACQ, args=(args,), daemon=True)
			detThreadList.append(detThreading)

		log.info("Start detectors threads")
		for thread in detThreadList: 
			thread.start()

		log.info("Joining the detector threads") 
		for thread in detThreadList:
			thread.join()

		ACQdata={**ACQdata,**det.data}
		log.info("Collecting data from detectors")
		expData.update(ACQdata)

		return (expData["KETEK-MCA1"])

	def startZMQ(self, numPointsX, numPointsY, scanTopo = "seq", arrayIndexX = None, arrayIndexY=None):
		self.writer.createRawDatasets(numPointsX, numPointsY)
		self.writer.createDefaultDatasets(numPointsX, numPointsY)
		self.writer.receiveData(numPointsX, numPointsY, scanTopo, arrayIndexX, arrayIndexY)
		PV("XAFS:ScanEndTime").put(str(time.strftime('%Y-%m-%dT%H:%M:%S')), wait=True)

	def setupH5DXLayout(self):
		self.writer = ZMQWriter(self.h5FileName, self.BasePath, h5CfgFile)
		self.writer.createH5File()
		self.writer.setupH5DXLayout()

	def closeH5File(self):
		closeFile = threading.Thread(target=self.writer.closeFile(), args=())
		closeFile.start()
		closeFile.join()		# waiting until finishing closing file

	def signal_handler(self, sig, frame):
		self.sock.send_pyobj("scanAborted")		# parse scanAborted if the scan has been aborted
		PV("XAFS:ScanEndTime").put(str(time.strftime('%Y-%m-%dT%H:%M:%S')), wait=True)
		self.closeH5File()
		super().signal_handler(self, sig, frame)

	def writePVS(self):
		
		"""
		This method has been implemented to write metadata on PVs in order to dump them in h5
		file by the writer

		** this the only way to implement this case, beacuse the DAQ System for this beamline is not IOC based
		"""

		CLIMessage("writePVs...", "I")
		log.info("writePVs...")

		prefix = "XAFS:"
		PVs = self.h5cfg["writerPVs"]
		PV(prefix + PVs[PVs.index("ExperimentType")]).put(self.cfg['expType'], wait=True)
		PV(prefix + PVs[PVs.index("ExperimentalFileName")]).put(self.h5FileName, wait=True)
		PV(prefix + PVs[PVs.index("ExperimentalFilePath")]).put(self.BasePath, wait=True)

		if self.cfg["expType"] == "proposal":
			try: 
				self.propInfo = readFile("configurations/userinfo.json").readJSON()
				PV(prefix + PVs[PVs.index("ProposalID")]).put(self.propInfo["Proposal"], wait=True)
				PV(prefix + PVs[PVs.index("ProposalTittle")]).put(self.propInfo["Title"], wait=True)
				PV(prefix + PVs[PVs.index("PI")]).put(self.propInfo["Proposer"], wait=True)
				PV(prefix + PVs[PVs.index("PIEmail")]).put(self.propInfo["Email"], wait=True)
			except:
				CLIMessage("Can't generate porposal info","E") 
		else:
			PV(prefix + PVs[PVs.index("ProposalID")]).put("No Data", wait=True)
			PV(prefix + PVs[PVs.index("ProposalTittle")]).put("No Data", wait=True)
			PV(prefix + PVs[PVs.index("PI")]).put("No Data", wait=True)
			PV(prefix + PVs[PVs.index("PIEmail")]).put("No Data", wait=True)

		PV(prefix + PVs[PVs.index("ScanTopo")]).put(self.scanTopology, wait=True)
		# PV(prefix + PVs[PVs.index("ElementEdge")]).put(self.cfg['ExpMetaData'][0]['edge'], wait=True)
		PV(prefix + PVs[PVs.index("MonoName")]).put(self.cfg['ExpMetaData'][3]['Mono'], wait=True)

		if self.cfg['ExpMetaData'][3]['Mono'] == "Si 111":
			PV(prefix + PVs[PVs.index("MonoDSpacing")]).put(3.1356, wait=True)
		else:
			PV(prefix + PVs[PVs.index("MonoDSpacing")]).put(1.6374, wait=True)
			
		PV(prefix + PVs[PVs.index("MonoSettlingTime")]).put(self.cfg['settlingTime'], wait=True)
		PV(prefix + PVs[PVs.index("IntTime")]).put(self.FrameDuration, wait=True)
		PV(prefix + PVs[PVs.index("XStart")]).put(self.ROIXStart, wait=True)
		PV(prefix + PVs[PVs.index("YStart")]).put(self.ROIYStart, wait=True)
		PV(prefix + PVs[PVs.index("XEnd")]).put(self.ROIXEnd, wait=True)
		PV(prefix + PVs[PVs.index("YEnd")]).put(self.ROIYEnd, wait=True)
		# PV(prefix + PVs[PVs.index("Z")]).put(, wait=True)
		# PV(prefix + PVs[PVs.index("Rotation")]).put(, wait=True)
		PV(prefix + PVs[PVs.index("ResolutionX")]).put(self.scanResX, wait=True)
		PV(prefix + PVs[PVs.index("ResolutionY")]).put(self.scanResY, wait=True)
		PV(prefix + PVs[PVs.index("BeamlineCollimation")]).put("slits", wait=True)
		PV(prefix + PVs[PVs.index("BeamlineFocusing")]).put(0, wait=True)
		PV(prefix + PVs[PVs.index("MirrorCoatingVCM")]).put(self.cfg['ExpMetaData'][1]['vcm'], wait=True)
		PV(prefix + PVs[PVs.index("MirrorCoatingVFM")]).put(self.cfg['ExpMetaData'][2]['vfm'], wait=True)
		PV(prefix + PVs[PVs.index("ExpStartTime")]).put(self.expStartTimeDF, wait=True)
		PV(prefix + PVs[PVs.index("ScanStartTime")]).put(self.creationTime, wait=True)
		PV(prefix + PVs[PVs.index("ScanEnergy")]).put(self.cfg['Energy'], wait=True)
		# PV(prefix + PVs[PVs.index("ScanEdgeEnergy")]).put(, wait=True)
		# PV(prefix + PVs[PVs.index("EnergyMode")]).put(, wait=True)
		# PV(prefix + PVs[PVs.index("SampleStoichiometry")]).put(self.cfg['ExpMetaData'][2]['stoichiometry'], wait=True)
		# PV(prefix + PVs[PVs.index("SamplePreperation")]).put(self.cfg['ExpMetaData'][3]['samplePrep'], wait=True)
		PV(prefix + PVs[PVs.index("UserComments")]).put(self.cfg['ExpMetaData'][4]['userCom'], wait=True)
		PV(prefix + PVs[PVs.index("ExperimentComments")]).put(self.cfg['ExpMetaData'][5]['expCom'], wait=True)

		CLIMessage("Finishing writePVs...", "I")
		log.info("Finishing writePVs...")		
