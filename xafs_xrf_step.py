"""
A derived class that inherits from XAFS_XRF class. 
this class is to include all common step scan methods. 
"""

import log
from pandabox import PandA
from xafs_xrf import XAFS_XRF
from SEDSS.SEDFileManager import readFile

class XAFS_XRFSTEP(XAFS_XRF):
	def __init__(self, paths, cfg, testingMode, accPlotting):
		super().__init__(paths, cfg, testingMode, accPlotting)
		self.PVs["DCM:Speed"].put(0.14)
		self.pandaBox.disableBit("A")
		self.pandaBox.enableBit("B")
	
	def MoveDCM(self, SP):
		self.motors["DCM:Energy:SP"].move(SP)
		log.info("Move DCM to energy: {}".format(SP))