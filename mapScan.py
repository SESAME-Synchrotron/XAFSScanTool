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
				"Please rerun the DAQ and enter correct parameters").showCritical()
			log.error('Y resolution scan parameter is less that the Y axis motor resolution!!')
			sys.exit()

	def startScan(self): 
		"""
		this function is the main function to perform mapping scan
		"""
		xRange    = self.drange(self.ROIXStart, self.ROIXEnd, self.scanResX)
		yRange    = self.drange(self.ROIYStart, self.ROIYEnd, self.scanResY)
		log.info ('Scan range for X axis: {}'.format(xRange))
		log.info ('Scan range for Y axis: {}'.format(yRange))
				
		for y in yRange:
			log.info('Moving sample stage Y to: {}'.format(y))
			self.MoveSmpY(y)
			for x in xRange:
				log.info('Moving sample stage X to: {}'.format(x))
				self.MoveSmpX(x)				
				log.info('Collecting data for the scan point: ({},{})'.format(x,y))