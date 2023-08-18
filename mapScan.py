'''
Step mapping scan derived class

'''
import sys
import log
import time
import zmq
import threading
import numpy as np
from epics import PV

from SEDSS.CLIMessage import CLIMessage
from SEDSS.UIMessage import UIMessage
from SEDSS.SEDFileManager import readFile

#from xafs import XAFS_XRF
from xafs_xrf_step import XAFS_XRFSTEP
from ZMQWriter import ZMQWriter

h5CfgFile = "configurations/XAFS_Writer.json"
class MAPSCAN (XAFS_XRFSTEP):
	def __init__(self, paths, cfg, testingMode = "No"):
		super().__init__(paths, cfg, testingMode)

		self.ROIXStart    = self.cfg['ROIXStart']
		self.ROIXEnd      = self.cfg['ROIXEnd']
		self.ROIYStart    = self.cfg['ROIYStart']
		self.ROIYEnd      = self.cfg['ROIYEnd']
		self.scanResX     = self.cfg['ResX']
		self.scanResY     = self.cfg['ResY']
		self.scanEnergy   = self.cfg['Energy']
		self.scanTopology = self.cfg["ExpMetaData"][9]["mapScanTopology"]

		""" read XAFS_writer cfg file"""
		self.h5cfg = readFile(h5CfgFile).readJSON()

		""" create zmq socket as publisher """
		ZMQSettings = self.h5cfg["ZMQSettings"]["ZMQSenderSettings"]
		ZMQSender = ZMQSettings["ZMQSender"]
		ZMQSPort = ZMQSettings["ZMQPort"]
		ZMQSProtocol = ZMQSettings["ZMQProtocol"]
		ZMQSender = ZMQSProtocol + "://" + ZMQSender + ":" + ZMQSPort

		context = zmq.Context()
		self.sock = context.socket(zmq.PUB)
		self.sock.connect(ZMQSender)  	# Connect instead of bind for the server

		""" setup h5 file layout """
		h5Layout = threading.Thread(target=self.setupH5DXLayout, args=())
		h5Layout.start()
		h5Layout.join()

		self.checkMapScanPara()
		self.MoveDCM(self.scanEnergy)
		self.startScan()

	def MoveDCM(self,SP, curentScanInfo=None):
		super().MoveDCM(SP, curentScanInfo)
		log.info('Moving to start energy: {}'.format(SP))
		while not self.PVs["DCM:Energy:Moving"].get():
				CLIMessage("DCM is moving to scan energy {}... ".format(SP), "IG")
				self.motors["DCM:Theta"].put("stop_go",3)
				self.motors["DCM:Y"].put("stop_go",3)
				self.PVs["DCM:Move"].put(1, wait=True)
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
				xArrayIndex.append(i)
				yArrayPos.append(positionsMatrix[i,j,1])
				yArrayIndex.append(j)

		return xArrayPos, yArrayPos, xArrayIndex, yArrayIndex

	def snakeScanPoints(self, xRange, yRange):
		"""
		A method to return back the xArray and yArray to scan in snake shape
		xArray: contains the positions for motor X
		yArray: contains the positions for motor y
		xIndex: snak matrix index for x motor
		yIndex: snak matrix index for y motor
		"""

		xArray = []
		yArray = []
		xIndex = []
		yIndex = []

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
				for x in range (len(xRange)):
					xArray.append(inversedMatrixRow[x][0])
					xIndex.append(x)
					yArray.append(inversedMatrixRow[x][1])
					yIndex.append(i)

		return xArray, yArray, xIndex, yIndex

	def startScan(self):
		"""
		this function is the main function to perform mapping scan
		"""
		self.xRange = self.drange(self.ROIXStart, self.ROIXEnd, self.scanResX)
		self.yRange = self.drange(self.ROIYStart, self.ROIYEnd, self.scanResY)
		log.info ('Scan range for X axis: {}'.format(self.xRange))
		log.info ('Scan range for Y axis: {}'.format(self.yRange))

		""" start zmq reciever socket """
		zmqRec = threading.Thread(target=self.startZMQ, args=(), daemon=True)
		zmqRec.start()

		if self.scanTopology == 'Sequential': 
			for y in self.yRange:
				log.info('Moving sample stage Y to: {}'.format(y))
				self.MoveSmpY(y)
				for x in self.xRange:
					log.info('Moving sample stage X to: {}'.format(x))
					self.MoveSmpX(x)
					log.info('Collecting data for the scan point: ({},{})'.format(x,y))
					try:
						# self.sock.send_pyobj(list(range(0,2048)))
						self.sock.send_pyobj(PV(self.configFile["EPICSandIOCs"]["KETEKNumChannels"]).get())

					except:
						self.sock.send_pyobj("timeout")
		else: 
			if self.scanTopology == 'Snake': 
				xScanPoints, yScanPoints, xScanIndex, yScanIdex = self.snakeScanPoints(self.xRange,self.yRange)
			elif self.scanTopology == 'Diagonal': 
				xScanPoints, yScanPoints, xScanIndex, yScanIdex = self.diagonalScanPoints(self.xRange,self.yRange)

			for i in range (len(xScanPoints)): 
				log.info('Move sample X to: {}'.format(xScanPoints[i]))
				self.MoveSmpX(xScanPoints[i])
				log.info('Move sample Y to: {}'.format(yScanPoints[i]))
				self.MoveSmpY(yScanPoints[i])

	def startZMQ(self):
		self.writer.reciveData(len(self.xRange), len(self.yRange))
		self.writer.closeFile()

	def setupH5DXLayout(self):
		self.writer = ZMQWriter(self.h5FileName, self.BasePath, h5CfgFile)
		self.writer.createH5File()
		self.writer.setupH5DXLayout()

	def signal_handler(self, sig, frame):
		self.sock.send_pyobj("scanAborted")
		self.writer.closeFile()
		super().signal_handler(self, sig, frame)
