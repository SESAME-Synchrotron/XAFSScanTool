import epics 
import os
import time
from SEDSS.SEDSupplements import CLIMessage
import fileinput
import sys
from SEDSS.SEDSupport import readFile, dataTransfer, timeModule 
import re 

class XDIWriter: 
	"""
	rawData: raw data recevied from the scanning tool
	filePath: file path 
	fileName: file name 
	detChosen: a list contains the detector chosen. 
	scanStartTime: Experiment start data and time to be part of the file name 

	"""
	def __init__(self, rawData, filePath, detChosen, scanStartTime, expStartTimeDF, cfg, curentScanInfo): 
		self.cfg = cfg
		self.curentScanInfo = curentScanInfo
		self.data = rawData
		self.fileName = self.cfg["DataFileName"]
		self.filePath = filePath 
		self.detChosen = detChosen
		self.scanNum = rawData["Scan#"]
		self.scanStartTime = scanStartTime
		self.expStartTimeDF = expStartTimeDF

		############ Meta Data collection from cfg ############

		self.numScans = self.cfg["Nscans"]
		self.numIntervals = self.cfg["NIntervals"]
		self.numSamples = self.cfg["Nsamples"]
		self.settlingTime = self.cfg["settlingTime"]
		self.stepUnit = self.cfg["stepUnit"]

		self.scanNum = self.curentScanInfo[1]["Scan"]
		self.intervalNum = self.curentScanInfo[2]["Interval"]
		self.sampleNum = self.curentScanInfo[0]["Sample"]
		self.sampleTitle = self.curentScanInfo[4]["sampleTitle"]



		self.IC1GasMix = self.cfg["ExpMetaData"][0]["IC1GasMix"]
		self.IC2GasMix = self.cfg["ExpMetaData"][1]["IC2GasMix"]
		self.IC3GasMix = self.cfg["ExpMetaData"][2]["IC3GasMix"]
		self.edge = self.cfg["ExpMetaData"][3]["edge"]
		self.sampleName = self.cfg["ExpMetaData"][4]["sampleName"]
		self.energy = self.cfg["ExpMetaData"][5]["energy"]
		self.stoichiometry = self.cfg["ExpMetaData"][6]["stoichiometry"]
		self.samplePrep = self.cfg["ExpMetaData"][7]["samplePrep"]
		self.vcm = self.cfg["ExpMetaData"][8]["vcm"]
		self.vfm = self.cfg["ExpMetaData"][9]["vfm"]
		self.Mono = self.cfg["ExpMetaData"][10]["Mono"]
		self.userCom = self.cfg["ExpMetaData"][11]["userCom"]
		self.expCom = self.cfg["ExpMetaData"][12]["expCom"]
		self.RINGCurrent = self.curentScanInfo[3]["RINGCurrent"]

		self.personalInfoFlage = 0

		
		if self.cfg["expType"] == "proposal":
			try: 
				self.propInfo = readFile("configrations/userinfo.json").readJSON()
				self.proposalID = self.propInfo["Proposal"]
				self.propTitle = self.propInfo["Title"]
				self.PI = self.propInfo["Proposer"]
				self.PIEmail = self.propInfo["Email"]
				self.personalInfoFlage = 1
			except: 
				pass

		self.d_spacing = 3.1356 if self.Mono == "Si 111" else 1.6374

		self.createXDIFile()

	def createXDIFile(self):
		"""
		this method does the follwoing: 
		- generats the file name 
		- creats xdi file in respect to the chosen detector
		"""
		self.fullFileName = self.filePath +"/" + self.fileName + "_" + self.sampleTitle + "_" + "Scan" + str(self.data["Scan#"]) + "_" + self.scanStartTime + ".xdi"
		#print (self.fullFileName)
		
		if "KETEK" in self.detChosen:
			if "FICUS" in self.detChosen:
				self.createICKFXDIFile()
				self.fillICKFDataTable()
			else: 
				self.createICKXDIFile() # creates IC Ketek XDI File
				self.fillICKDataTable() # Fill the created file 

		elif "FICUS" in self.detChosen:
			self.createICFXDIFile() 
			self.fillICFDataTable()
		else: 
			self.createICXDIFile()
			self.fillICDataTable()
		self.onClose()
	
	def createICKFXDIFile(self): # Create IC, Ketek and FICUS xdi file 

		if not os.path.exists(self.fullFileName): 
			f = open (self.fullFileName, "w")
			f.write("# XDI/1.0 SED_XAFS/0.9\n")
			if self.stepUnit == 1:
				f.write("# Column.1: energy (KeV)\n")
				f.write("# Column.1.1: energy (eV)\n")
			else:
				f.write("# Column.1: energy (eV)\n")
			f.write("# Column.2: I0\n")
			f.write("# Column.3: Itrans\n")
			f.write("# Column.4: Irefer\n")
			f.write("# Column.5: mutrans (log(I0/Itrans))\n")
			f.write("# Column.6: murefer (log(Itrans/Irefer))\n")
			f.write("# Column.7: KETEK-Ifluor\n")
			f.write("# Column.8: KETEK-mufluor\n")
			f.write("# Column.9: KETEK-ROI_0[c/s]\n")
			f.write("# Column.10: KETEK-ROI_1[c/s]\n")
			f.write("# Column.11: KETEK-ROI_2[c/s]\n")
			f.write("# Column.12: KETEK-e-time[sec]\n")
			f.write("# Column.13: KETEK-DEADTIME[%]\n")
			f.write("# Column.14: KETEK-INT_TIME[sec]\n")
			f.write("# Column.15: KETEK-OCR\n")
			f.write("# Column.16: KETEK-ICR\n")
			f.write("# Column.17: FICUS-Ifluor\n")
			f.write("# Column.18: FICUS-mufluor\n")
			f.write("# Column.19: FICUS-ROI_0[c/s]\n")
			f.write("# Column.20: FICUS-ROI_1[c/s]\n")
			f.write("# Column.21: FICUS-ROI_2[c/s]\n")
			f.write("# Column.22: FICUS-e-time[sec]\n")
			f.write("# Column.23: FICUS-DEADTIME[%]\n")
			f.write("# Column.24: FICUS-INT_TIME[sec]\n")
			if self.personalInfoFlage == 1:
				f.write("# Experiment.Type: Proposal\n")
				f.write("# Proposal.ID: {}\n".format(self.proposalID))
				f.write("# Proposal.title: {}\n".format(self.propTitle))
				f.write("# PI: {}\n".format(self.PI))
				f.write("# PI Email: {}\n".format(self.PIEmail))
			else: 
				f.write("# Experiment.Type: Local\n")
			f.write("# Base.file_name: {}\n".format(self.fileName))
			f.write("# Element.edge: {}\n".format(self.edge))
			f.write("# Mono.name: {}\n".format(self.Mono))
			f.write("# Mono.d_spacing: {}\n".format(self.d_spacing))
			f.write("# Mono.settling_time: {}\n".format(self.settlingTime))
			f.write("# Beamline.name: XAFS/XRF Beamline (08-BM)\n")
			f.write("# Beamline.collimation: slits\n")
			f.write("# Beamline.focusing: no\n")
			f.write("# Beamline.harmonic_rejection: mirror coating VCM: {}, VFM: {}\n".format(self.vcm, self.vfm))
			f.write("# Facility.name: SESAME Synchrotron-light\n")
			f.write("# Facility.energy: 2.50 GeV\n")
			f.write("# Facility.current: {}\n".format(self.RINGCurrent))
			f.write("# Facility.xray_source: SESAME Bending Magnet\n")
			f.write("# Exp.start_time: {}\n".format(str(self.expStartTimeDF) ))
			f.write("# Scan.start_time: {}\n".format(str(time.strftime("%Y-%m-%dT%H:%M:%S"))))
			f.write("# Scan.end_time: xxx\n")
			f.write("# Scan.edge_energy: {}\n".format(self.energy))
			f.write("# Scan.number: {}/{} -- intervals: {}, samples: {}\n".format(self.scanNum, self.numScans, self.numIntervals, self.numSamples))
			f.write("# Detector.IC1: 15cm  {}\n".format(self.IC1GasMix))
			f.write("# Detector.IC2: 30cm  {}\n".format(self.IC2GasMix))
			f.write("# Detector.IC3: 15cm  {}\n".format(self.IC3GasMix))
			f.write("# Detector.flour: KETEK\n")
			f.write("# Detector.flour: FICUS\n")
			f.write("# Element.symbol: {}\n".format(self.sampleName))
			f.write("# Sample.stoichiometry: {}\n".format(self.stoichiometry))
			f.write("# Sample.prep: {}\n".format(self.samplePrep))
			f.write("# ///\n")
			f.write("# Experiment comments and remarks: {}\n".format(self.expCom))
			f.write("# User comments and remarks: {}\n".format(self.userCom))
			f.write("#----\n")
			if self.stepUnit == 1: 
				f.write("#(1)energy (KeV)   (1.1)energy (eV)   (2)I0   (3)Itrans   (4)Irefer   (5)mutrans   (6)murefer   (7)KETEK-Ifluor   (8)KETEK-mufluor   (9)KETEK-ROI_0[c/s]   (10)KETEK-ROI_1[c/s]   (11)KETEK-ROI_2[c/s]   (12)KETEK-e-time[sec]   (13)KETEK-DEADTIME[%]   (14)KETEK-INT_TIME[sec]   (15)KETEK-OCR   (16)KETEK-ICR"\
				"   (17)FICUS-Ifluor   (18)FICUS-mufluor   (19)FICUS-ROI_0[c/s]   (20)FICUS-ROI_1[c/s]   (21)FICUS-ROI_2[c/s]   (22)FICUS-e-time[sec]   (23)FICUS-DEADTIME[%]   (24)FICUS-INT_TIME[sec]\n")
			else: 
				f.write("#(1)energy   (2)I0   (3)Itrans   (4)Irefer   (5)mutrans   (6)murefer   (7)KETEK-Ifluor   (8)KETEK-mufluor   (9)KETEK-ROI_0[c/s]   (10)KETEK-ROI_1[c/s]   (11)KETEK-ROI_2[c/s]   (12)KETEK-e-time[sec]   (13)KETEK-DEADTIME[%]   (14)KETEK-INT_TIME[sec]   (15)KETEK-OCR   (16)KETEK-ICR"\
				"   (17)FICUS-Ifluor   (18)FICUS-mufluor   (19)FICUS-ROI_0[c/s]   (20)FICUS-ROI_1[c/s]   (21)FICUS-ROI_2[c/s]   (22)FICUS-e-time[sec]   (23)FICUS-DEADTIME[%]   (24)FICUS-INT_TIME[sec]\n")
			f.close()

	def fillICKFDataTable(self): # Fill IC, Ketek and FICUS collected data. 
		f = open (self.fullFileName, "a")
		if self.stepUnit == 1: 
			f.write("%10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e \n" 
			%(float(self.data["ENERGY-RBK"]), float(self.data["ENERGY-RBK"])*1000 ,float(self.data["IC1[V]"]), float(self.data["IC2[V]"]), float(self.data["IC3[V]"]), 
				float(self.data["TRANS"]), float(self.data["TransRef"]), float(self.data["KETEK-If"]), float(self.data["KETEK-FLUOR"]), float(self.data["KETEK-ROI_0[c/s]"]), float(self.data["KETEK-ROI_1[c/s]"]), float(self.data["KETEK-ROI_2[c/s]"]),
				float(self.data["KETEK-e-time[sec]"]), float(self.data["KETEK-DEADTIME[%]"]),
				float(self.data["KETEK-INT_TIME[sec]"]), float(self.data["KETEK-OCR"]), float(self.data["KETEK-ICR"]),
				float(self.data["FICUS-If"]), float(self.data["FICUS-FLUOR"]), float(self.data["FICUS-ROI_0[c/s]"]), float(self.data["FICUS-ROI_1[c/s]"]), float(self.data["FICUS-ROI_2[c/s]"]),
				float(self.data["FICUS-e-time[sec]"]), float(self.data["FICUS-DEADTIME[%]"]), float(self.data["FICUS-INT_TIME[sec]"])  ))
		else:
			f.write("%10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e \n" 
			%(float(self.data["ENERGY-RBK"]), float(self.data["IC1[V]"]), float(self.data["IC2[V]"]), float(self.data["IC3[V]"]), 
				float(self.data["TRANS"]), float(self.data["TransRef"]), float(self.data["KETEK-If"]), float(self.data["KETEK-FLUOR"]), float(self.data["KETEK-ROI_0[c/s]"]), float(self.data["KETEK-ROI_1[c/s]"]), float(self.data["KETEK-ROI_2[c/s]"]),
				float(self.data["KETEK-e-time[sec]"]), float(self.data["KETEK-DEADTIME[%]"]),
				float(self.data["KETEK-INT_TIME[sec]"]), float(self.data["KETEK-OCR"]), float(self.data["KETEK-ICR"]),
				float(self.data["FICUS-If"]), float(self.data["FICUS-FLUOR"]), float(self.data["FICUS-ROI_0[c/s]"]), float(self.data["FICUS-ROI_1[c/s]"]), float(self.data["FICUS-ROI_2[c/s]"]),
				float(self.data["FICUS-e-time[sec]"]), float(self.data["FICUS-DEADTIME[%]"]), float(self.data["FICUS-INT_TIME[sec]"])  ))
		f.close()

	def createICKXDIFile(self):
		
		if not os.path.exists(self.fullFileName): 
			f = open (self.fullFileName, "w")
			f.write("# XDI/1.0 SED_XAFS/0.9\n")
			if self.stepUnit == 1:
				f.write("# Column.1: energy (KeV)\n")
				f.write("# Column.1.1: energy (eV)\n")
			else:
				f.write("# Column.1: energy (eV)\n")
			f.write("# Column.2: I0\n")
			f.write("# Column.3: Itrans\n")
			f.write("# Column.4: Irefer\n")
			f.write("# Column.5: mutrans (log(I0/Itrans))\n")
			f.write("# Column.6: murefer (log(Itrans/Irefer))\n")
			f.write("# Column.7: KETEK-Ifluor\n")
			f.write("# Column.8: KETEK-mufluor\n")
			f.write("# Column.9: KETEK-ROI_0[c/s]\n")
			f.write("# Column.10: KETEK-ROI_1[c/s]\n")
			f.write("# Column.11: KETEK-ROI_2[c/s]\n")
			f.write("# Column.12: KETEK-e-time[sec]\n")
			f.write("# Column.13: KETEK-DEADTIME[%]\n")
			f.write("# Column.14: KETEK-INT_TIME[sec]\n")
			f.write("# Column.15: KETEK-OCR\n")
			f.write("# Column.16: KETEK-ICR\n")
			if self.personalInfoFlage == 1:
				f.write("# Experiment.Type: Proposal\n")
				f.write("# Proposal.ID: {}\n".format(self.proposalID))
				f.write("# Proposal.title: {}\n".format(self.propTitle))
				f.write("# PI: {}\n".format(self.PI))
				f.write("# PI Email: {}\n".format(self.PIEmail))
			else: 
				f.write("# Experiment.Type: Local\n")
			f.write("# Base.file_name: {}\n".format(self.fileName))
			f.write("# Element.edge: {}\n".format(self.edge))
			f.write("# Mono.name: {}\n".format(self.Mono))
			f.write("# Mono.d_spacing: {}\n".format(self.d_spacing))
			f.write("# Mono.settling_time: {}\n".format(self.settlingTime))
			f.write("# Beamline.name: XAFS/XRF Beamline (08-BM)\n")
			f.write("# Beamline.collimation: slits\n")
			f.write("# Beamline.focusing: no\n")
			f.write("# Beamline.harmonic_rejection: mirror coating VCM: {}, VFM: {}\n".format(self.vcm, self.vfm))
			f.write("# Facility.name: SESAME Synchrotron-light\n")
			f.write("# Facility.energy: 2.50 GeV\n")
			f.write("# Facility.current: {}\n".format(self.RINGCurrent))
			f.write("# Facility.xray_source: SESAME Bending Magnet\n")
			f.write("# Exp.start_time: {}\n".format(str(self.expStartTimeDF) ))
			f.write("# Scan.start_time: {}\n".format(str(time.strftime("%Y-%m-%dT%H:%M:%S"))))
			f.write("# Scan.end_time: xxx\n")
			f.write("# Scan.edge_energy: {}\n".format(self.energy))
			f.write("# Scan.number: {}/{} -- intervals: {}, samples: {}\n".format(self.scanNum, self.numScans, self.numIntervals, self.numSamples))
			f.write("# Detector.IC1: 15cm  {}\n".format(self.IC1GasMix))
			f.write("# Detector.IC2: 30cm  {}\n".format(self.IC2GasMix))
			f.write("# Detector.IC3: 15cm  {}\n".format(self.IC3GasMix))
			f.write("# Detector.flour: KETEK\n")
			f.write("# Element.symbol: {}\n".format(self.sampleName))
			f.write("# Sample.stoichiometry: {}\n".format(self.stoichiometry))
			f.write("# Sample.prep: {}\n".format(self.samplePrep))
			f.write("# ///\n")
			f.write("# Experiment comments and remarks: {}\n".format(self.expCom))
			f.write("# User comments and remarks: {}\n".format(self.userCom))
			f.write("#----\n")
			if self.stepUnit == 1: 
				f.write("#(1)energy (KeV)   (1.1)energy (eV)   (2)I0   (3)Itrans   (4)Irefer   (5)mutrans   (6)murefer   (7)KETEK-Ifluor   (8)KETEK-mufluor   (9)KETEK-ROI_0[c/s]   (10)KETEK-ROI_1[c/s]   (11)KETEK-ROI_2[c/s]   (12)KETEK-e-time[sec]   (13)KETEK-DEADTIME[%]   (14)KETEK-INT_TIME[sec]   (15)KETEK-OCR   (16)KETEK-ICR\n")
			else:
				f.write("#(1)energy   (2)I0   (3)Itrans   (4)Irefer   (5)mutrans   (6)murefer   (7)KETEK-Ifluor   (8)KETEK-mufluor   (9)KETEK-ROI_0[c/s]   (10)KETEK-ROI_1[c/s]   (11)KETEK-ROI_2[c/s]   (12)KETEK-e-time[sec]   (13)KETEK-DEADTIME[%]   (14)KETEK-INT_TIME[sec]   (15)KETEK-OCR   (16)KETEK-ICR\n")
			f.close()

	def fillICKDataTable(self):
		f = open (self.fullFileName, "a")
		if self.stepUnit == 1: 
			f.write("%10.6e  %10.6e   %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e \n" 
			%(float(self.data["ENERGY-RBK"]), float(self.data["ENERGY-RBK"])*1000, float(self.data["IC1[V]"]), float(self.data["IC2[V]"]), float(self.data["IC3[V]"]), 
				float(self.data["TRANS"]), float(self.data["TransRef"]), float(self.data["KETEK-If"]), float(self.data["KETEK-FLUOR"]), float(self.data["KETEK-ROI_0[c/s]"]), float(self.data["KETEK-ROI_1[c/s]"]), float(self.data["KETEK-ROI_2[c/s]"]),
				float(self.data["KETEK-e-time[sec]"]), float(self.data["KETEK-DEADTIME[%]"]),
				float(self.data["KETEK-INT_TIME[sec]"]), float(self.data["KETEK-OCR"]), float(self.data["KETEK-ICR"])))
		else:
			f.write("%10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e \n" 
			%(float(self.data["ENERGY-RBK"]), float(self.data["IC1[V]"]), float(self.data["IC2[V]"]), float(self.data["IC3[V]"]), 
				float(self.data["TRANS"]), float(self.data["TransRef"]), float(self.data["KETEK-If"]), float(self.data["KETEK-FLUOR"]), float(self.data["KETEK-ROI_0[c/s]"]), float(self.data["KETEK-ROI_1[c/s]"]), float(self.data["KETEK-ROI_2[c/s]"]),
				float(self.data["KETEK-e-time[sec]"]), float(self.data["KETEK-DEADTIME[%]"]),
				float(self.data["KETEK-INT_TIME[sec]"]), float(self.data["KETEK-OCR"]), float(self.data["KETEK-ICR"])))
		f.close()

	def createICXDIFile(self):
		
		if not os.path.exists(self.fullFileName): 
			f = open (self.fullFileName, "w")
			f.write("# XDI/1.0 SED_XAFS/0.9\n")
			if self.stepUnit == 1:
				f.write("# Column.1: energy (KeV)\n")
				f.write("# Column.1.1: energy (eV)\n")
			else:
				f.write("# Column.1: energy (eV)\n")
			f.write("# Column.2: I0\n")
			f.write("# Column.3: Itrans\n")
			f.write("# Column.4: Irefer\n")
			f.write("# Column.5: mutrans (log(I0/Itrans))\n")
			f.write("# Column.6: murefer (log(Itrans/Irefer))\n")
			if self.personalInfoFlage == 1:
				f.write("# Experiment.Type: Proposal\n")
				f.write("# Proposal.ID: {}\n".format(self.proposalID))
				f.write("# Proposal.title: {}\n".format(self.propTitle))
				f.write("# PI: {}\n".format(self.PI))
				f.write("# PI Email: {}\n".format(self.PIEmail))
			else: 
				f.write("# Experiment.Type: Local\n")
			f.write("# Base.file_name: {}\n".format(self.fileName))
			f.write("# Element.edge: {}\n".format(self.edge))
			f.write("# Mono.name: {}\n".format(self.Mono))
			f.write("# Mono.d_spacing: {}\n".format(self.d_spacing))
			f.write("# Mono.settling_time: {}\n".format(self.settlingTime))
			f.write("# Beamline.name: XAFS/XRF Beamline (08-BM)\n")
			f.write("# Beamline.collimation: slits\n")
			f.write("# Beamline.focusing: no\n")
			f.write("# Beamline.harmonic_rejection: mirror coating VCM: {}, VFM: {}\n".format(self.vcm, self.vfm))
			f.write("# Facility.name: SESAME Synchrotron-light\n")
			f.write("# Facility.energy: 2.50 GeV\n")
			f.write("# Facility.current: {}\n".format(self.RINGCurrent))
			f.write("# Facility.xray_source: SESAME Bending Magnet\n")
			f.write("# Exp.start_time: {}\n".format(str(self.expStartTimeDF) ))
			f.write("# Scan.start_time: {}\n".format(str(time.strftime("%Y-%m-%dT%H:%M:%S"))))
			f.write("# Scan.end_time: xxx\n")
			f.write("# Scan.edge_energy: {}\n".format(self.energy))
			f.write("# Scan.number: {}/{} -- intervals: {}, samples: {}\n".format(self.scanNum, self.numScans, self.numIntervals, self.numSamples))
			f.write("# Detector.IC1: 15cm  {}\n".format(self.IC1GasMix))
			f.write("# Detector.IC2: 30cm  {}\n".format(self.IC2GasMix))
			f.write("# Detector.IC3: 15cm  {}\n".format(self.IC3GasMix))
			f.write("# Element.symbol: {}\n".format(self.sampleName))
			f.write("# Sample.stoichiometry: {}\n".format(self.stoichiometry))
			f.write("# Sample.prep: {}\n".format(self.samplePrep))
			f.write("# ///\n")
			f.write("# Experiment comments and remarks: {}\n".format(self.expCom))
			f.write("# User comments and remarks: {}\n".format(self.userCom))
			f.write("#----\n")
			if self.stepUnit == 1: 
				f.write("#(1)energy (KeV)  (1.1)energy (eV)   (2)I0   (3)Itrans   (4)Irefer   (5)mutrans   (6)murefer\n")
			else: 
				f.write("#(1)energy   (2)I0   (3)Itrans   (4)Irefer   (5)mutrans   (6)murefer\n")
			f.close()


	def fillICDataTable(self):
		f = open (self.fullFileName, "a")
		if self.stepUnit == 1: 
			f.write("%10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e \n" 
			%(float(self.data["ENERGY-RBK"]), float(self.data["ENERGY-RBK"])*1000, float(self.data["IC1[V]"]), float(self.data["IC2[V]"]), float(self.data["IC3[V]"]), 
				float(self.data["TRANS"]), float(self.data["TransRef"])))
		else:
			f.write("%10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e \n" 
			%(float(self.data["ENERGY-RBK"]), float(self.data["IC1[V]"]), float(self.data["IC2[V]"]), float(self.data["IC3[V]"]), 
				float(self.data["TRANS"]), float(self.data["TransRef"])))
		f.close()


	def createICFXDIFile(self): 
		if not os.path.exists(self.fullFileName): 
			f = open (self.fullFileName, "w")
			f.write("# XDI/1.0 SED_XAFS/0.9\n")
			if self.stepUnit == 1:
				f.write("# Column.1: energy (KeV)\n")
				f.write("# Column.1.1: energy (eV)\n")
			else:
				f.write("# Column.1: energy (eV)\n")
			f.write("# Column.2: I0\n")
			f.write("# Column.3: Itrans\n")
			f.write("# Column.4: Irefer\n")
			f.write("# Column.5: mutrans (log(I0/Itrans))\n")
			f.write("# Column.6: murefer (log(Itrans/Irefer))\n")
			f.write("# Column.7: FICUS-Ifluor\n")
			f.write("# Column.8: FICUS-mufluor\n")
			f.write("# Column.9: FICUS-ROI_0[c/s]\n")
			f.write("# Column.10: FICUS-ROI_1[c/s]\n")
			f.write("# Column.11: FICUS-ROI_2[c/s]\n")
			f.write("# Column.12: FICUS-e-time[sec]\n")
			f.write("# Column.13: FICUS-DEADTIME[%]\n")
			f.write("# Column.14: FICUS-INT_TIME[sec]\n")
			if self.personalInfoFlage == 1:
				f.write("# Experiment.Type: Proposal\n")
				f.write("# Proposal.ID: {}\n".format(self.proposalID))
				f.write("# Proposal.title: {}\n".format(self.propTitle))
				f.write("# PI: {}\n".format(self.PI))
				f.write("# PI Email: {}\n".format(self.PIEmail))
			else: 
				f.write("# Experiment.Type: Local\n")
			f.write("# Base.file_name: {}\n".format(self.fileName))
			f.write("# Element.edge: {}\n".format(self.edge))
			f.write("# Mono.name: {}\n".format(self.Mono))
			f.write("# Mono.d_spacing: {}\n".format(self.d_spacing))
			f.write("# Mono.settling_time: {}\n".format(self.settlingTime))
			f.write("# Beamline.name: XAFS/XRF Beamline (08-BM)\n")
			f.write("# Beamline.collimation: slits\n")
			f.write("# Beamline.focusing: no\n")
			f.write("# Beamline.harmonic_rejection: mirror coating VCM: {}, VFM: {}\n".format(self.vcm, self.vfm))
			f.write("# Facility.name: SESAME Synchrotron-light\n")
			f.write("# Facility.energy: 2.50 GeV\n")
			f.write("# Facility.current: {}\n".format(self.RINGCurrent))
			f.write("# Facility.xray_source: SESAME Bending Magnet\n")
			f.write("# Exp.start_time: {}\n".format(str(self.expStartTimeDF) ))
			f.write("# Scan.start_time: {}\n".format(str(time.strftime("%Y-%m-%dT%H:%M:%S"))))
			f.write("# Scan.end_time: xxx\n")
			f.write("# Scan.edge_energy: {}\n".format(self.energy))
			f.write("# Scan.number: {}/{} -- intervals: {}, samples: {}\n".format(self.scanNum, self.numScans, self.numIntervals, self.numSamples))
			f.write("# Detector.IC1: 15cm  {}\n".format(self.IC1GasMix))
			f.write("# Detector.IC2: 30cm  {}\n".format(self.IC2GasMix))
			f.write("# Detector.IC3: 15cm  {}\n".format(self.IC3GasMix))
			f.write("# Detector.flour: FICUS\n")
			f.write("# Element.symbol: {}\n".format(self.sampleName))
			f.write("# Sample.stoichiometry: {}\n".format(self.stoichiometry))
			f.write("# Sample.prep: {}\n".format(self.samplePrep))
			f.write("# ///\n")
			f.write("# Experiment comments and remarks: {}\n".format(self.expCom))
			f.write("# User comments and remarks: {}\n".format(self.userCom))
			f.write("#----\n")
			if self.stepUnit == 1: 
				f.write("#(1)energy (KeV)   (1.1)energy (eV)   (2)I0   (3)Itrans   (4)Irefer   (5)mutrans   (6)murefer   "\
					"(7)FICUS-Ifluor   (8)FICUS-mufluor (9)FICUS-ROI_0[c/s]   (10)FICUS-ROI_1[c/s]   (11)FICUS-ROI_2[c/s]   "\
					"(12)FICUS-e-time[sec]   (13)FICUS-DEADTIME[%]   (14)FICUS-INT_TIME[sec]\n")
			else:
				f.write("#(1)energy   (2)I0   (3)Itrans   (4)Irefer   (5)mutrans   (6)murefer   "\
					"(7)FICUS-Ifluor   (8)FICUS-mufluor (9)FICUS-ROI_0[c/s]   (10)FICUS-ROI_1[c/s]   (11)FICUS-ROI_2[c/s]   "\
					"(12)FICUS-e-time[sec]   (13)FICUS-DEADTIME[%]   (14)FICUS-INT_TIME[sec]\n")
			f.close()

	def fillICFDataTable(self): # create IC KETEk xdi data file 
		f = open (self.fullFileName, "a")
		if self.stepUnit == 1: 
			f.write("%10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e \n" 
			%(float(self.data["ENERGY-RBK"]),float(self.data["ENERGY-RBK"])*1000, float(self.data["IC1[V]"]), float(self.data["IC2[V]"]), float(self.data["IC3[V]"]), 
				float(self.data["TRANS"]), float(self.data["TransRef"]), 
				float(self.data["FICUS-If"]), float(self.data["FICUS-FLUOR"]), float(self.data["FICUS-ROI_0[c/s]"]), float(self.data["FICUS-ROI_1[c/s]"]), float(self.data["FICUS-ROI_2[c/s]"]),
				float(self.data["FICUS-e-time[sec]"]), float(self.data["FICUS-DEADTIME[%]"]), float(self.data["FICUS-INT_TIME[sec]"]) ))
		else:
			f.write("%10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e  %10.6e \n" 
			%(float(self.data["ENERGY-RBK"]), float(self.data["IC1[V]"]), float(self.data["IC2[V]"]), float(self.data["IC3[V]"]), 
				float(self.data["TRANS"]), float(self.data["TransRef"]), 
				float(self.data["FICUS-If"]), float(self.data["FICUS-FLUOR"]), float(self.data["FICUS-ROI_0[c/s]"]), float(self.data["FICUS-ROI_1[c/s]"]), float(self.data["FICUS-ROI_2[c/s]"]),
				float(self.data["FICUS-e-time[sec]"]), float(self.data["FICUS-DEADTIME[%]"]), float(self.data["FICUS-INT_TIME[sec]"]) ))
		f.close()

	def onClose(self): 
		#f = open (self.fullFileName, "a")
		scanEndTime = "# Scan.end_time: {}".format(str(time.strftime("%Y-%m-%dT%H:%M:%S")) )
		with open(self.fullFileName, "r") as file:
			contents = file.read()
			newContents = re.sub ("^# Scan.end_tim.*", scanEndTime,contents, flags = re.M)

		with open(self.fullFileName, "w") as updatedFile:
			updatedFile.write(newContents)

		
		# for line in fileinput.input(self.fullFileName, inplace=1):
		# 		line = line.replace("Scan.end_time: ", scanEndTime)
		# 		sys.stdout.write(line)