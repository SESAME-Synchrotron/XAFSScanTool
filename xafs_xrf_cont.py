"""
A derived class that inherits from XAFS_XRF class.
this class is to include all common continuous scan methods.
"""

import log
from pandabox import PandA
from xafs_xrf import XAFS_XRF
from SEDSS.SEDFileManager import readFile

class XAFS_XRFCONT(XAFS_XRF):
	def __init__(self, paths, cfg, testingMode, accPlotting):
		super().__init__(paths, cfg, testingMode, accPlotting)
		self.IPs = readFile("configurations/IPs.json").readJSON()
		self.pandaBox = PandA(self.IPs["PandA"])
		self.pandaBox.encoderSetp(int(self.PVs["DCM:Encoder"].get()))
		self.pandaBox.disableBit("B")

	def MoveDCM(self, SP, speed):
		self.PVs["DCM:Speed"].put(speed)
		log.info(f"Move DCM to target energy: {SP}")
		self.motors["DCM:Energy:SP"].move(SP)

		