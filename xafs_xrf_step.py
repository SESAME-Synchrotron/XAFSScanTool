"""
A derived class that inherits from XAFS_XRF class. 
this class is to include all common step scan methods. 
"""

from xafs_xrf import XAFS_XRF
import log

class XAFS_XRFSTEP(XAFS_XRF):
	def __init__(self, paths, cfg, testingMode):
		super().__init__(paths, cfg, testingMode)
	
	def MoveDCM(self,SP, curentScanInfo):
			self.motors["DCM:Theta"].put("stop_go",0, wait=True) # Stop
			#time.sleep(0.1)
			self.motors["DCM:Theta"].put("stop_go",3, wait=True) # Go
			self.PVs["DCM:Energy:SP"].put(SP, wait=True)
			self.PVs["DCM:Move"].put(1, wait=True)
			log.info("Move DCM to energy: {}".format(SP))