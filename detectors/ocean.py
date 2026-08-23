import time

from .base import Base
from SEDSS.CLIMessage import CLIMessage
from SEDSS.SEDFileManager import readFile

class OCEAN(Base):
	def __init__(self, name, paths, cfg={}):
		super().__init__(name)

		self.loadPVS(name)
		self.paths = paths
		self.cfg = cfg
		self.scanLimits = readFile("configurations/limits.json").readJSON()

		self.PVs["ocean_acquire"].put(0)
		self.PVs["ocean_bkgEnable"].put(1)
		self.PVs["ocean_bkgClear"].put(1)

	def ACQ(self,args):

		mapScanFlag = False
		try:
			if args["scanTopology"] in ('Snake', 'Sequential', 'Diagonal'):
				FrameDuration = args["FrameDuration"]
				mapScanFlag = True
			else:
				FrameDuration = args["ICsIntTime"]
		except:
			FrameDuration = args["ICsIntTime"]
		
		self.PVs["ocean_intTime"].put(float(FrameDuration) * 1000)
		self.PVs["ocean_acquire"].put(1)
		time.sleep(float(FrameDuration) + self.scanLimits["OceanLatency"])
		self.PVs["ocean_acquire"].put(0)

		self.data["OCEAN_Spectrum"]	= self.PVs["ocean_spectrum"].get()
		if self.PVs["ocean_spectrumLength"].get() == 0:
			CLIMessage("Warning: Please check the OCEAN Detector!", "W")