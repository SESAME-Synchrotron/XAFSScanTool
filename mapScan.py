'''
Step mappig scan derived class

'''
#from xafs import XAFS_XRF
from xafs_xrf_step import XAFS_XRFSTEP
from SEDSS.CLIMessage import CLIMessage
from SEDSS.UIMessage import UIMessage
import sys
import log
import time
import zmq
from BEATSH5Writer.ZMQ import ZMQWriter
import threading


class MAPSCAN (XAFS_XRFSTEP):
	def __init__(self, paths, cfg, testingMode = "No"):
		super().__init__(paths, cfg, testingMode)

		self.ROIXStart  = self.cfg['ROIXStart']
		self.ROIXEnd    = self.cfg['ROIXEnd']
		self.ROIYStart  = self.cfg['ROIYStart']
		self.ROIYEnd    = self.cfg['ROIYEnd']
		self.scanResX   = self.cfg['ResX']
		self.scanResY   = self.cfg['ResY']
		self.scanEnergy = self.cfg['Energy']

		context = zmq.Context()
		self.sock = context.socket(zmq.PUB)
		self.sock.connect("tcp://127.0.0.1:1919")  # Connect instead of bind as server

		x = threading.Thread(target=self.setupH5DXLayout, args=())
		x.start()
		x.join()

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
				"Please retrun the DAQ and enter correct parameters").showCritical()
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
		        
		return xArrayPos, yArrayPos, xArrayIndex, yArrayIndex, positionsMatrix

	def snakeScanPoints(xRange, yRange):
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
		xRange    = self.drange(self.ROIXStart, self.ROIXEnd, self.scanResX)
		yRange    = self.drange(self.ROIYStart, self.ROIYEnd, self.scanResY)
		log.info ('Scan range for X axis: {}'.format(xRange))
		log.info ('Scan range for Y axis: {}'.format(yRange))
		y = threading.Thread(target=self.startZMQ, args=(), daemon=True)
		y.start()
		for y in yRange:
			log.info('Moving sample stage Y to: {}'.format(y))
			self.MoveSmpY(y)
			for x in xRange:
				log.info('Moving sample stage X to: {}'.format(x))
				self.MoveSmpX(x)				
				log.info('Collecting data for the scan point: ({},{})'.format(x,y))
				self.sock.send_pyobj(list(range(0,10)))

	def startZMQ(self):
		self.writer.reciveData()
		self.writer.closeFile()

	def setupH5DXLayout(self):
		self.writer = ZMQWriter("test00", "/home/dev.control", "BEATSH5Writer/configurations/BEATS/BEATS_FLIR_MICOS_Cont.json", 10)
		self.writer.createH5File()
		self.writer.setupH5DXLayout()

