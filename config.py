
#!/usr/bin/python3

from forms import configWizard, samplespositionForm, intervalsForm, detectorsForm
from enum import Enum
from PyQt5 import QtWidgets, QtCore

#import SED
import json
import datetime
import sys
import subprocess
import csv
import re
import os
import epics
from epics import caget, caput 
from SEDSS.SEDSupport import readFile
from SEDSS.SEDSupplements import CLIMessage, UIMessage
from electronBindingEnergies import electronBindingEnergies


from  common import Common

class ConfigGUI:
	class WizardPages(Enum):
		ExperimentType = 0
		SED = 1
		CfgFile = 2
		LoadCfg = 3
		editCfg = 4
		startscan = 5

	def __init__(self,paths):
		self.Qwiz = QtWidgets.QWizard()
		#self.QCore =
		self.guiObj = configWizard.Ui_Wizard()
		self.guiObj.setupUi(self.Qwiz)

		self.paths = paths

		self.PVs = readFile("pvlist/xafs.json").readJSON()

		self.cfg = {}
		self.expType = "users"
		self.masterExpType = "proposal" #this is a master exp type to avoid overwriting by loading config file 

		self.IntervalsGUI   = IntervalGUI()
		self.SamplesGUI     = SamplePosGUI()
		self.DetectorsGUI   = DetectorsGUI()

		self.guiObj.ExpType.nextId = self.CheckExptype
		self.guiObj.SED.nextId = self.checkPropsalID
		self.guiObj.CfgFile.nextId = self.cfgfile
		self.guiObj.CfgPath.nextId = self.loadcfg
		self.guiObj.scan_params.nextId = self.checkConfig
		self.Qwiz.button(QtWidgets.QWizard.FinishButton).clicked.connect(self.start)
		self.Qwiz.button(QtWidgets.QWizard.CancelButton).clicked.connect(self.onClose)
		self.Qwiz.button(QtWidgets.QWizard.BackButton).clicked.connect(self.energyCalConstraintsCheck)
		self.Qwiz.button(QtWidgets.QWizard.NextButton).clicked.connect(self.energyCalConstraintsCheck)
		self.Qwiz.setWindowFlag(QtCore.Qt.CustomizeWindowHint) # Need to be set firstly before dealing with windows buttons
		self.Qwiz.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)

		self.guiObj.Browse.clicked.connect(self.BrowseCfgFile)
		self.guiObj.editIntrv.clicked.connect(self.editIntervals)
		self.guiObj.editSample.clicked.connect(self.editSamples)
		self.guiObj.configureDetectors.clicked.connect(self.Detectors)

		#self.guiObj.sampleName.textChanged.connect(self.getFoilElementEnergy(self.guiObj.edge.currentText(), self.guiObj.sampleName.text()))
		self.guiObj.sampleName.textChanged.connect(self.getFoilElementEnergy)
		self.guiObj.edge.currentTextChanged.connect(self.getFoilElementEnergy)

		self.Qwiz.exec_()
	def onClose(self): 
		CLIMessage("===========    Close the scanning tool    ===========","W")
		sys.exit()
	
	def energyCalConstraintsCheck(self): 
		"""
		This method applies some GUI settings when choosing energy calibration option
		"""
		if self.guiObj.EnergyCal.isChecked(): 
			
			self.guiObj.sampleName.setReadOnly(False)
			self.guiObj.sampleName.setStyleSheet("QLineEdit {background : orange;}")
			self.guiObj.energy.setStyleSheet("QLineEdit {background : orange;}")
			self.guiObj.Mono.setEnabled(True)
			self.guiObj.Mono.setStyleSheet("QComboBox {background : orange;}")

		else: 
			self.guiObj.sampleName.setReadOnly(False)
			self.guiObj.sampleName.setStyleSheet("QLineEdit {background : green;}")
			self.guiObj.sampleName.setText(caget(self.PVs["PV"]["ENGCAL:FoilElement"]["pvname"]))
			self.guiObj.energy.setStyleSheet("QLineEdit {background : green;}")
			self.guiObj.energy.setText(str(caget(self.PVs["PV"]["ENGCAL:RealFoilEng"]["pvname"])))
			self.guiObj.Mono.setEnabled(False)
			self.guiObj.Mono.setStyleSheet("QComboBox {background : green;}")
			self.guiObj.Mono.setCurrentText(caget(self.PVs["PV"]["BLSetup:Crystal"]["pvname"]))

		

	def CheckExptype(self):
		if self.guiObj.UsersExp.isChecked():
			self.expType = "proposal"
			self.masterExpType = "proposal"
			self.cfg["expType"] = self.expType
			return self.WizardPages.SED.value

		elif self.guiObj.EnergyCal.isChecked(): # when choosing energy calibration
			self.expType = "EnergyCalibration"
			self.masterExpType = "EnergyCalibration"
			self.cfg["expType"] = self.expType

			self.guiObj.sampleName.setEnabled(True)
			self.guiObj.Mono.setEnabled(True)
			return self.WizardPages.CfgFile.value # Go to load or enter a new config file 

		else:
			self.expType = "local"
			self.masterExpType = "local"
			self.cfg["expType"] = self.expType
			return self.WizardPages.CfgFile.value
	
	def getExpType(self):
		return self.masterExpType


	def checkPropsalID(self):
		proposal_ID = self.guiObj.PropsalID.text()
		if proposal_ID == '':
			return self.WizardPages.ExperimentType.value
		else:
			SedObj = SED()
			result = SedObj.init(proposal_ID)
			if result:
				self.cfg["proposalID"] = SedObj.proposalID
				return self.WizardPages.CfgFile.value
			else:
				return self.WizardPages.SED.value

	def cfgfile(self):
		if self.guiObj.Create.isChecked():
			self.cfg["loadedConfig"] = "No"
			return self.WizardPages.editCfg.value
			
		else:
			self.cfg["loadedConfig"] = "Yes"
			return self.WizardPages.LoadCfg.value
			

	def loadcfg(self):
		path = self.guiObj.filePath.text()
		if not path == "":
			self.cfg["loadedConfig"] = "Yes"
			return self.WizardPages.editCfg.value
			
		else:
			return self.WizardPages.LoadCfg.value

	def editIntervals(self):
		Nintrv = self.guiObj.setNumofIterv.text()
		if Common.regexvalidation("NIntervals", Nintrv):
			Nintrv = int(Nintrv)
			self.cfg["NIntervals"] = Nintrv
			self.IntervalsGUI.setIntervalsNumber(self.cfg)
			self.IntervalsGUI.intervalDialog.exec()				
		else:
			Common.show_message(QtWidgets.QMessageBox.Critical,
								"Please enter Number of Intervals",
								"XAFS/XRF scan tool", QtWidgets.QMessageBox.Ok)

	def Detectors(self):
		if "detectors" in self.cfg.keys():
			for Detector in self.cfg["detectors"]:
				det = getattr(self.DetectorsGUI.detectors_UI, Detector)
				det.setChecked(True)
		self.DetectorsGUI.detectorsDialog.exec_()
	
	def editSamples(self):
		Nsamples = self.guiObj.setNumofSamples.text()
		if Common.regexvalidation("Nsample", Nsamples):
			Nsamples = int(Nsamples)
			self.cfg["Nsamples"] = Nsamples
			self.SamplesGUI.setSamplesNumber(self.cfg)
			self.SamplesGUI.sampleDialog.exec_()
		else:
			Common.show_message(QtWidgets.QMessageBox.Critical,
								"Please enter Number of samples",
								"XAFS/XRF scan tool", QtWidgets.QMessageBox.Ok)

	def BrowseCfgFile(self):
		try:
			self.IntervalsGUI	= IntervalGUI()
			self.SamplesGUI		= SamplePosGUI()
			self.DetectorsGUI	= DetectorsGUI()
	
			self.cfgpath = QtWidgets.QFileDialog.getOpenFileName(self.Qwiz, "choose configuration file", "~","*.cfg")[0]
			try:
				self.guiObj.filePath.setText(self.cfgpath)
				self.cfg = self.loadcfgfile(self.cfgpath)
			except:
				CLIMessage("Could not locate the config file", "W")
				return self.WizardPages.editCfg.value
	
			try: 
				NIntervals = self.cfg["NIntervals"]
				Nsamples = self.cfg["Nsamples"]
				Nscans = self.cfg["Nscans"]
				settlingTime = self.cfg["settlingTime"]
			except:
				UIMessage("Error reading config file",
					"Unable to read from configration file", 
					"Try to load another file").showCritical()
				CLIMessage("Unable to read configuration file, scanning can not continue!!","E")
				sys.exit()
	
			self.guiObj.setNumofIterv.setText(str(NIntervals))
			self.guiObj.setNumofSamples.setText(str(Nsamples))
			self.guiObj.setNumofExafsScans.setText(str(Nscans))
			self.guiObj.settlingTime.setText(str(settlingTime))
			self.guiObj.setDataFileName.setText(self.cfg["DataFileName"])
			self.guiObj.edge.setCurrentText(str(self.cfg["ExpMetaData"][3]["edge"]))
			self.guiObj.sampleName.setText(str(self.cfg["ExpMetaData"][4]["sampleName"]))
			self.guiObj.energy.setText(self.cfg["ExpMetaData"][5]["energy"])
			self.guiObj.stoichiometry.setText(str(self.cfg["ExpMetaData"][6]["stoichiometry"]))
			self.guiObj.samplePrep.setText(str(self.cfg["ExpMetaData"][7]["samplePrep"]))
			self.guiObj.vcm.setCurrentText(str(self.cfg["ExpMetaData"][8]["vcm"]))
			self.guiObj.vfm.setCurrentText(str(self.cfg["ExpMetaData"][9]["vfm"]))
			self.guiObj.Mono.setCurrentText(str(self.cfg["ExpMetaData"][10]["Mono"]))
			self.guiObj.userCom.setText(str(self.cfg["ExpMetaData"][11]["userCom"]))
			self.guiObj.expCom.setText(str(self.cfg["ExpMetaData"][12]["expCom"]))
	
	
	
	
	
			self.DetectorsGUI.detectors_UI.IC1GasMix.setText(str(self.cfg["ExpMetaData"][0]["IC1GasMix"]))
			self.DetectorsGUI.detectors_UI.IC2GasMix.setText(str(self.cfg["ExpMetaData"][1]["IC2GasMix"]))
			self.DetectorsGUI.detectors_UI.IC3GasMix.setText(str(self.cfg["ExpMetaData"][2]["IC3GasMix"]))
	
	
			for interval in range(len(self.cfg["Intervals"])):
				self.IntervalsGUI.interval_UI.tableWidget.setItem(interval, IntervalGUI.IntervalCols.start.value,QtWidgets.QTableWidgetItem(str(self.cfg["Intervals"][interval]["Startpoint"]),0))
				self.IntervalsGUI.interval_UI.tableWidget.setItem(interval, IntervalGUI.IntervalCols.end.value,QtWidgets.QTableWidgetItem(str(self.cfg["Intervals"][interval]["Endpoint"]),0))
				self.IntervalsGUI.interval_UI.tableWidget.setItem(interval, IntervalGUI.IntervalCols.step.value,QtWidgets.QTableWidgetItem(str(self.cfg["Intervals"][interval]["Stepsize"]),0))
				self.IntervalsGUI.interval_UI.tableWidget.setItem(interval, IntervalGUI.IntervalCols.ICInt.value,QtWidgets.QTableWidgetItem(str(self.cfg["Intervals"][interval]["IcsIntTime"]),0))
	
				cbox = AcqTime(interval,self.cfg["Intervals"][interval]["DetIntTime"])
				self.IntervalsGUI.interval_UI.tableWidget.setCellWidget(interval, IntervalGUI.IntervalCols.DetInt.value,cbox)

				stepUnitCbox = AcqTime(interval,self.cfg["Intervals"][interval]["stepUnit"])
				self.IntervalsGUI.interval_UI.tableWidget.setCellWidget(interval, IntervalGUI.IntervalCols.stepUnit.value,stepUnitCbox)

				if "ExtTrig" in self.cfg["Intervals"][interval].keys():
					self.IntervalsGUI.interval_UI.tableWidget.setItem(interval,IntervalGUI.IntervalCols.ExtTrig.value,QtWidgets.QTableWidgetItem(str(self.cfg["Intervals"][interval]["ExtTrig"]), 0))
	
			for sample in range(len(self.cfg["Samplespositions"])):
				self.SamplesGUI.sample_UI.samplepositions.setItem(sample, SamplePosGUI.SampleCols.X.value,QtWidgets.QTableWidgetItem(str(self.cfg["Samplespositions"][sample]["Xposition"]), 0))
				self.SamplesGUI.sample_UI.samplepositions.setItem(sample, SamplePosGUI.SampleCols.Y.value,QtWidgets.QTableWidgetItem(str(self.cfg["Samplespositions"][sample]["Yposition"]), 0))
				self.SamplesGUI.sample_UI.samplepositions.setItem(sample, SamplePosGUI.SampleCols.Title.value,QtWidgets.QTableWidgetItem(str(self.cfg["Samplespositions"][sample]["sampleTitle"]), 0))
			
			if "FICUS" in self.cfg["detectors"]:
				detCheckbox = getattr(self.DetectorsGUI.detectors_UI, "FICUS")
				detCheckbox.setChecked(True)
			
			if "KETEK" in self.cfg["detectors"]:
				detCheckbox = getattr(self.DetectorsGUI.detectors_UI, "KETEK")
				detCheckbox.setChecked(True)

			self.cfg["expType"] = self.masterExpType # to avoid overwriting the choosen exp type when load a config file
		except:
			CLIMessage("Problem reading the config file. Try another one","E")
			return self.WizardPages.editCfg.value


	def checkConfig(self):
		expMetaData = []
		try:
			NIntervals = self.guiObj.setNumofIterv.text()
			#print(NIntervals, type(NIntervals), "<-")
			if NIntervals == '' or not Common.regexvalidation("NIntervals",NIntervals):
				CLIMessage("Please enter valid Number of intervals","W")
				return self.WizardPages.editCfg.value
			self.IntervalsGUI.setIntervalsNumber(self.cfg)
			Nsamples = self.guiObj.setNumofSamples.text()
			if Nsamples == '' or not Common.regexvalidation("Nsample", Nsamples):
				CLIMessage("Please enter valid number of Samples","W")
				return self.WizardPages.editCfg.value

			Nscans = self.guiObj.setNumofExafsScans.text()
			if Nscans == '' or not Common.regexvalidation("Nscans", Nscans):
				CLIMessage("Please enter valid number of scans","W")
				return self.WizardPages.editCfg.value

			DataFileName = self.guiObj.setDataFileName.text()
			if DataFileName == '' or not Common.regexvalidation("DataFileName", DataFileName):
				CLIMessage("Please enter a valid data file name", "W")
				return self.WizardPages.editCfg.value

			settlingTime = self.guiObj.settlingTime.text()
			if settlingTime == '' or not Common.regexvalidation("settlingTime", settlingTime):
				CLIMessage("Please enter valid settling time", "W")
				return self.WizardPages.editCfg.value



			intervals = [{} for i in range(int(NIntervals))]
			for interval in range(int(NIntervals)):#range(self.IntervalsGUI.interval_UI.tableWidget.rowCount()):
				"""
				without try and except, the script will try to check the linedit text before inisialization 
				and thus generat errors 
				"""
				try: 
					start = self.IntervalsGUI.interval_UI.tableWidget.item(interval, 0).text()
					if start == '' or not Common.validate("Startpoint", start, "Please enter valid start point"):
						CLIMessage("Please check/enter the start point for interval number {}".format(interval), "W") 
						return self.WizardPages.editCfg.value

				except: 
					CLIMessage("Please check/enter the start point for interval number {}".format(interval), "W") 

				try: 
					end = self.IntervalsGUI.interval_UI.tableWidget.item(interval,1).text()
					if end == '' or not Common.validate("Endpoint", end, "Please enter valid end point"):
						CLIMessage("Please check/enter the end point for interval number {}".format(interval), "W") 
						return self.WizardPages.editCfg.value
				except:
					CLIMessage("Please check/enter the end point for interval number {}".format(interval), "W") 

				try: 
					stepsize = self.IntervalsGUI.interval_UI.tableWidget.item(interval, 2).text()
					if stepsize == '' or not Common.validate("Stepsize", end, "Please enter valid step size"):
						CLIMessage("Please check/enter the step-size for interval number {}".format(interval), "W") 
						return self.WizardPages.editCfg.value
				except: 
					CLIMessage("Please check/enter the step-size for interval number {}".format(interval), "W") 

				try:
					IcIntTime = self.IntervalsGUI.interval_UI.tableWidget.item(interval, 3).text()
					if IcIntTime == '' or not Common.validate("IcsIntTime", end,"Please enter valid IC integration time for "\
						"interval number {}".format(interval)):
						CLIMessage("Please check/enter the ICs integration time for interval number {}".format(interval), "W") 
						return self.WizardPages.editCfg.value
				except: 
					CLIMessage("Please check/enter the ICs integration time for interval number {}".format(interval), "W") 

				#intervals[interval]["DetIntTime"] = self.IntervalsGUI._AcqTimes[interval]
				intervals[interval]["DetIntTime"] = self.IntervalsGUI.FicusIntTimeDic[interval]
				intervals[interval]["stepUnit"] = self.IntervalsGUI.stepUnitDic[interval]

				isExtTrigger = self.IntervalsGUI._AcqTimes[interval]
				if isExtTrigger == 15:
					ExtTriggerIntTime = self.IntervalsGUI.interval_UI.tableWidget.item(interval, 5).text()
					if ExtTriggerIntTime == '' or not Common.validate(
							"ExtTriggerIntTime", ExtTriggerIntTime,"Please enter valid External Trigger duration"):
						return self.WizardPages.editCfg.value

			SamplePositions = [{} for i in range(int(Nsamples))]
			for sample in range(self.SamplesGUI.sample_UI.samplepositions.rowCount()):
				try: 
					Xposition = self.SamplesGUI.sample_UI.samplepositions.item(sample, 0).text()
					if Xposition == '' or not Common.validate("Xposition", Xposition,"Please enter valid sample x position"):
						CLIMessage("Please check/enter (x) position for sample number {}".format(sample), "W") 
						return self.WizardPages.editCfg.value



					Yposition = self.SamplesGUI.sample_UI.samplepositions.item(sample, 1).text()
					if Yposition == '' or not Common.validate("Yposition", Yposition,"Please enter valid sample y position"):
						CLIMessage("Please check/enter (y) position for sample number {}".format(sample), "W") 
						return self.WizardPages.editCfg.value
				except: 
					CLIMessage("Please check/enter (x,y) position for sample number {}".format(sample), "W")

				try:
					sampleTitle = self.SamplesGUI.sample_UI.samplepositions.item(sample, 2).text()
					if sampleTitle == '' or not Common.validate("sampleTitle", sampleTitle,"Please enter valid sample name"):
						CLIMessage("Please check/enter sample name in the Samples dialog for the sameple number: {}".format(sample), "W") 
						return self.WizardPages.editCfg.value
				except:
					CLIMessage("Please check/enter the sample name in the Samples dialog", "W")
					return self.WizardPages.editCfg.value


			####################### Metadata section ##############################

			if self.DetectorsGUI.detectors_UI.IC1GasMix.text() == "":
				CLIMessage("Please enter the IC1 gas being used", "W")
				return self.WizardPages.editCfg.value
			else:
				expMetaData.append({"IC1GasMix":self.DetectorsGUI.detectors_UI.IC1GasMix.text()})

			if self.DetectorsGUI.detectors_UI.IC2GasMix.text() == "":
				CLIMessage("Please enter the IC2 gas being used", "W")
				return self.WizardPages.editCfg.value
			else:
				expMetaData.append({"IC2GasMix":self.DetectorsGUI.detectors_UI.IC2GasMix.text()})

			if self.DetectorsGUI.detectors_UI.IC3GasMix.text() == "":
				CLIMessage("Please enter the IC3 gas being used", "W")
				return self.WizardPages.editCfg.value
			else:
				expMetaData.append({"IC3GasMix":self.DetectorsGUI.detectors_UI.IC3GasMix.text()})

			if self.guiObj.edge.currentText() == "":
				CLIMessage("Please choose the element edge", "W")
				return self.WizardPages.editCfg.value
			else:
				#senderIndex = self.guiObj.edge.sender().index
				#print(senderIndex)
				expMetaData.append({"edge":self.guiObj.edge.currentText()})

			if self.guiObj.sampleName.text() == "":
				CLIMessage("Please enter the periodic element for this experiment", "W")
				return self.WizardPages.editCfg.value
			else:
				#if Common.regexvalidation("sampleName", self.guiObj.sampleName.text()):
				if electronBindingEnergies(self.guiObj.sampleName.text()).elementExist():
					
					self.getFoilElementEnergy()
					#elementEnergy = electronBindingEnergies(self.guiObj.sampleName.text()).getEdgeEnergy(self.guiObj.edge.currentText())	
					expMetaData.append({"sampleName":self.guiObj.sampleName.text()})
					caput(self.PVs["PV"]["ENGCAL:FoilElement"]["pvname"], self.guiObj.sampleName.text())
					caput(self.PVs["PV"]["ENGCAL:RealFoilEng"]["pvname"], self.guiObj.energy.text())
				else:
					Common.show_message(QtWidgets.QMessageBox.Critical,
						"""Enter a valid format of the foil element being used!! \n Allowed elements are: 
						H, He, Li, Be, B, C, N, O, F, Ne, Na, Mg, Al, Si, P, S, Cl, Ar, K, Ca, Sc, Ti
						V, Cr, Mn, Fe, Co, Ni, Cu, Zn, Ga, Ge, As, Se, Br, Kr, Rb, Sr, Y, Zr, Nb, Mo, Tc, 
						Ru, Rh, Pd, Ag, Cd, In, Sn, Sb, Te, I, Xe, Cs, Ba, La, Ce, Pr, Nd, Pm, Sm, Eu, Gd,
						Tb, Dy, Ho, Er, Tm, Yb, Lu, Hf, Ta, W, Re, Os, Ir, Pt, Au, Hg, Tl, Pb, Bi, Po, At,
						Rn, Fr, Ra, Ac, Th, Pa, U ""","XAFS/XRF Scan tool",
						QtWidgets.QMessageBox.Ok)
					return self.WizardPages.editCfg.value
			##################################
			energyVal = self.guiObj.energy.text()
			#print (energyVal, type(energyVal))
			if energyVal == "":
				CLIMessage("Please enter energy", "W")
				return self.WizardPages.editCfg.value
			else:
				if Common.regexvalidation("energy", energyVal):
					expMetaData.append({"energy":self.guiObj.energy.text()})
				else:
					Common.show_message(QtWidgets.QMessageBox.Critical,
						"Enter a valid energy please !!","XAFS/XRF Scan tool",
						QtWidgets.QMessageBox.Ok)
					return self.WizardPages.editCfg.value
			###################################

			if self.guiObj.stoichiometry.text() == "":
				expMetaData.append({"stoichiometry":"NONE"})
				#return self.WizardPages.editCfg.value
			else:
				expMetaData.append({"stoichiometry":self.guiObj.stoichiometry.text()})

			if self.guiObj.samplePrep.text() == "":
				CLIMessage("Please enter the sample preperation for this experiment", "W")
				return self.WizardPages.editCfg.value
			else:
				expMetaData.append({"samplePrep":self.guiObj.samplePrep.text()})

			if self.guiObj.vcm.currentText() == "":
				CLIMessage("Mirror coating | Please choose vcm element", "W")
				return self.WizardPages.editCfg.value
			else:
				expMetaData.append({"vcm":self.guiObj.vcm.currentText()})

			if self.guiObj.vfm.currentText() == "":
				CLIMessage("Mirror coating | Please choose vfm element", "W")
				return self.WizardPages.editCfg.value
			else:
				expMetaData.append({"vfm":self.guiObj.vfm.currentText()})

			if self.guiObj.Mono.currentText() == "":
				CLIMessage("Mirror coating | Please choose the Mono Crystal", "W")
				return self.WizardPages.editCfg.value
			else:
				expMetaData.append({"Mono":self.guiObj.Mono.currentText()})
				caput(self.PVs["PV"]["BLSetup:Crystal"]["pvname"], self.guiObj.Mono.currentText())

			if self.guiObj.userCom.text() == "":
				expMetaData.append({"userCom":"NONE"})
			else:
				expMetaData.append({"userCom":self.guiObj.userCom.text()})

			if self.guiObj.expCom.text() == "":
				expMetaData.append({"expCom":"NONE"})
			else:
				expMetaData.append({"expCom":self.guiObj.expCom.text()})

				
			detectors = []
			for d in self.DetectorsGUI.detectors:
				detCheckbox = getattr(self.DetectorsGUI.detectors_UI, d)
				if detCheckbox.isChecked():
					detectors.append(d)

			self.cfg["ExpMetaData"] = expMetaData

			if not detectors:
				return self.WizardPages.editCfg.value

			return self.WizardPages.startscan.value
		except:
			print ("Check config")
			return self.WizardPages.editCfg.value
			
	def getFoilElementEnergy(self):
		edge = self.guiObj.edge.currentText()
		foilElement = self.guiObj.sampleName.text()
		if edge == "":
			edge = "K" # goes to default 
		if foilElement == "":
			self.guiObj.energy.setText(None)
		elif electronBindingEnergies(foilElement).elementExist():
			elementEnergy = electronBindingEnergies(foilElement).getEdgeEnergy(edge)
			self.guiObj.energy.setText(str(elementEnergy)) 
		else: 
			self.guiObj.energy.setText(None)

	def start(self):
		NIntervals = self.guiObj.setNumofIterv.text()
		if NIntervals == '' or not Common.validate(
				"NIntervals", NIntervals,"Please enter valid Number of INtervals"):
			CLIMessage("Please enter valid Number of intervals", "W")
			return self.WizardPages.editCfg.value
		else:
			self.cfg["NIntervals"] = int(NIntervals)

		Nsamples = self.guiObj.setNumofSamples.text()
		if Nsamples == '' or not Common.validate("Nsample", Nsamples, "Please enter valid Number of Samples"):
			CLIMessage("Please enter a valid number of Samples, and, make sure to click on the Samples button to keep or change the default values","W")
			return self.WizardPages.editCfg.value
		else:
			self.cfg["Nsamples"] = int(Nsamples)

		Nscans = self.guiObj.setNumofExafsScans.text()
		if Nscans == '' or not Common.validate("Nscans", Nscans, "Please enter valid Number of scans"):
			CLIMessage("Pleae enter a valid number of scans", "W")
			return self.WizardPages.editCfg.value
		else:
			self.cfg["Nscans"] = int(Nscans)
		DataFileName = self.cfg["DataFileName"] = self.guiObj.setDataFileName.text()
		if DataFileName == '' or not Common.validate("DataFileName", DataFileName,"Please enter valid data file name"):
			CLIMessage("Please enter a valid data file name","W")
			return self.WizardPages.editCfg.value
		else:
			self.cfg["DataFileName"] = DataFileName

		settlingTime = self.guiObj.settlingTime.text()
		if settlingTime == '' or not Common.regexvalidation("settlingTime", settlingTime):
			CLIMessage("Please enter valid settling time", "W")
			return self.WizardPages.editCfg.value
		else:
			self.cfg["settlingTime"]=float(settlingTime)


		intervals = [{} for i in range(int(NIntervals))]
		for interval in range(self.IntervalsGUI.interval_UI.tableWidget.rowCount()):
			start = self.IntervalsGUI.interval_UI.tableWidget.item(interval, 0).text()
			if start == '' or not Common.validate("Startpoint", start, "Please enter valid start point"):
				CLIMessage("Intervals | Please enter a valid start point", "W")
				return self.WizardPages.editCfg.value
			else:
				intervals[interval]["Startpoint"] = float(start)

			end = self.IntervalsGUI.interval_UI.tableWidget.item(interval,1).text()
			if end == '' or not Common.validate("Endpoint", end, "Please enter valid end point"):
				CLIMessage("Intervals | Please enter a valid end point", "W")
				return self.WizardPages.editCfg.value
			else:
				intervals[interval]["Endpoint"] = float(end)

			stepsize = self.IntervalsGUI.interval_UI.tableWidget.item(interval, 2).text()
			if stepsize == '' or not Common.validate("Stepsize", end, "Please enter valid step size"):
				CLIMessage("Intervals | Please enter a valid step size","W")
				return self.WizardPages.editCfg.value
			else:
				intervals[interval]["Stepsize"] = float(stepsize)

			IcIntTime = self.IntervalsGUI.interval_UI.tableWidget.item(interval, 3).text()
			if IcIntTime == '' or not Common.validate("IcsIntTime", end,"Please enter valid IC integration time"):
				CLIMessage("Intervals | Please enter a valid IC integration time","W")
				return self.WizardPages.editCfg.value
			else:
				intervals[interval]["IcsIntTime"] = float(IcIntTime)

			#intervals[interval]["DetIntTime"] = self.IntervalsGUI._AcqTimes[interval]
			intervals[interval]["DetIntTime"] = self.IntervalsGUI.FicusIntTimeDic[interval]
			intervals[interval]["stepUnit"] = self.IntervalsGUI.stepUnitDic[interval]

			isExtTrigger = self.IntervalsGUI._AcqTimes[interval]
			if isExtTrigger == 15:
				ExtTriggerIntTime = self.IntervalsGUI.interval_UI.tableWidget.item(interval, 5).text()
				if ExtTriggerIntTime == '' or not Common.validate(
						"ExtTriggerIntTime", ExtTriggerIntTime,"Please enter valid External Trigger duration"):
					CLIMessage("Intervals | Please enter a valid External Trigger duration")
					return self.WizardPages.editCfg.value
				else:
					intervals[interval]["ExtTrig"] = float(ExtTriggerIntTime)

		SamplePositions = [{} for i in range(int(Nsamples))]
		for sample in range(self.SamplesGUI.sample_UI.samplepositions.rowCount()):
			Xposition = self.SamplesGUI.sample_UI.samplepositions.item(sample, 0).text()
			if Xposition == '' or not Common.validate("Xposition", Xposition,"Please enter valid sample x position"):
				CLIMessage("Samples | Please enter a valid sample X position")
				return self.WizardPages.editCfg.value
			else:
				SamplePositions[sample]["Xposition"] = Xposition
			Yposition = self.SamplesGUI.sample_UI.samplepositions.item(sample, 1).text()
			if Yposition == '' or not Common.validate("Yposition", Yposition,"Please enter valid sample y position"):
				CLIMessage("Samples | Please enter a valid sample Y position")
				return self.WizardPages.editCfg.value
			else:
				SamplePositions[sample]["Yposition"] = Yposition
			
			sampleTitle = self.SamplesGUI.sample_UI.samplepositions.item(sample, 2).text()
			if sampleTitle == '' or not Common.validate("sampleTitle", sampleTitle,"Please enter valid sample name in the Samples dialog"):
				CLIMessage("Samples | Please enter a valid sample name in the Samples dialog")
				return self.WizardPages.editCfg.value
			else:
				SamplePositions[sample]["sampleTitle"] = sampleTitle
				
		detectors = []
		for d in self.DetectorsGUI.detectors:
			detCheckbox = getattr(self.DetectorsGUI.detectors_UI, d)
			if detCheckbox.isChecked():
				detectors.append(d)
		



		self.cfg["detectors"] = detectors

		self.cfg["Intervals"] = intervals

		self.cfg["Samplespositions"] = SamplePositions
		print ("==========================================")

	def loadcfgfile(self, cfgfilename):
		try:
			with open(cfgfilename, 'r') as cfgfile:
				data = json.load(cfgfile)
				cfgfile.close()
				return data
		except Exception as e:
			print("cfgfile load error")
			print(e)
			sys.exit()

class SamplePosGUI:
	class SampleCols(Enum):
		X	=	0
		Y	=	1
		Title = 2

	def __init__(self):
		self.sampleDialog = QtWidgets.QDialog()
		self.sample_UI = samplespositionForm.Ui_Dialog()
		self.sample_UI.setupUi(self.sampleDialog)

	def setSamplesNumber(self, cfg):
		Nsamples = cfg["Nsamples"]
		self.sample_UI.samplepositions.setRowCount(Nsamples)

		"""
		bring default x and y positions 
		"""

		PVs = readFile("pvlist/xafs.json").readJSON()
		XpositionPV = PVs["Motors"]["SMP:X"]["pvname"]
		YpositionPV = PVs["Motors"]["SMP:Y"]["pvname"] 

		#print("cfg.keys", cfg.keys())


		if "Samplespositions" in cfg.keys():
			for sample in range(Nsamples):
				sampleTitle = ""
				Xposition = ""
				Yposition = ""

				if sample < len(cfg["Samplespositions"]):

					try:
						Xposition = self.sample_UI.samplepositions.item(sample, 0).text()
						Yposition = self.sample_UI.samplepositions.item(sample, 1).text()
						sampleTitle = self.sample_UI.samplepositions.item(sample, 2).text()
					except:
						print("")

					try:	

						if Xposition == "" or Yposition == "" or sampleTitle =="": # bring x and y values fro the first time from cfg file
							self.sample_UI.samplepositions.setItem(sample, SamplePosGUI.SampleCols.X.value,QtWidgets.QTableWidgetItem(str(cfg["Samplespositions"][sample]["Xposition"]), 0))
							self.sample_UI.samplepositions.setItem(sample, SamplePosGUI.SampleCols.Y.value,QtWidgets.QTableWidgetItem(str(cfg["Samplespositions"][sample]["Yposition"]), 0))
							self.sample_UI.samplepositions.setItem(sample, SamplePosGUI.SampleCols.Title.value,QtWidgets.QTableWidgetItem(str(cfg["Samplespositions"][sample]["sampleTitle"]), 0))
						
					except:
						CLIMessage("Unable to read x and y positions (or Sample Name) from the configuration file for "\
							"the sample number {}".format(sample), "W")

					#try: 
					#	
					#	if sampleTitle == "": 
					#		
					#except:
					#	CLIMessage("Unable to read the sample name for sample number {} from the config file".format(sample), "W")
		else: 
			CurentXPosition = caget(XpositionPV)
			CurentYPosition = caget(YpositionPV)
			
			try: # try to get text for the first interval, ... if not set the curent x y positions 
				XpositionInt0 = self.sample_UI.samplepositions.item(0, 0).text() # x position interval 0
				YpositionInt0 = self.sample_UI.samplepositions.item(0, 1).text() # y position interval 0 

				if XpositionInt0 == "": 
					self.sample_UI.samplepositions.setItem(0, SamplePosGUI.SampleCols.X.value,QtWidgets.QTableWidgetItem(str(CurentXPosition), 0))
				if YpositionInt0 == "":
					self.sample_UI.samplepositions.setItem(0, SamplePosGUI.SampleCols.Y.value,QtWidgets.QTableWidgetItem(str(CurentYPosition), 0))

			except:
				self.sample_UI.samplepositions.setItem(0, SamplePosGUI.SampleCols.X.value,QtWidgets.QTableWidgetItem(str(CurentXPosition), 0))
				self.sample_UI.samplepositions.setItem(0, SamplePosGUI.SampleCols.Y.value,QtWidgets.QTableWidgetItem(str(CurentYPosition), 0))

class IntervalGUI:
	class IntervalCols(Enum):
		start	 =	0
		end		 =	1
		step	 =	2
		ICInt	 =	3
		DetInt	 =	4
		ExtTrig	 =	5
		stepUnit =  6

		GlobalCfg = {} 
		
	def __init__(self):
		self.intervalDialog = QtWidgets.QDialog()
		self.interval_UI = intervalsForm.Ui_Dialog()
		self.interval_UI.setupUi(self.intervalDialog)
		self._AcqTimes = [-1]
		self.FicusIntTimeDic = {}
		self.stepUnitDic = {}
		self._stepUnitItems = [-1]
		self.interval_UI.buttonBox.clicked.connect(self.saveIntervals)
		self.Intervals = []


	def saveIntervals(self):
		#print ("dffsdfsdfs", len(self.FicusIntTimeDic))
		global GlobalCfg
		#print (GlobalCfg)
		self.Intervals = [{} for i in range(int(len(self.FicusIntTimeDic)))]
		for interval in range(len(self.FicusIntTimeDic)): 
			#self.stepUnitDic[interval] = 0
			#print ("self.stepUnitDic[interval]", self.interval_UI.tableWidget.item(interval, 6).text())
			try:
				#print("FicusIntTimeDic::::::::::::", self.FicusIntTimeDic, "interval:::", interval)
				self.Intervals[interval]["Startpoint"] =   self.interval_UI.tableWidget.item(interval, 0).text()
				self.Intervals[interval]["Endpoint"]   =   self.interval_UI.tableWidget.item(interval, 1).text()
				self.Intervals[interval]["Stepsize"]   =   self.interval_UI.tableWidget.item(interval, 2).text()
				self.Intervals[interval]["IcsIntTime"] =   self.interval_UI.tableWidget.item(interval, 3).text()
				self.Intervals[interval]["DetIntTime"] =   self.FicusIntTimeDic[interval]
				"""
				For any given interval, if stepUnit combo box is not clicked, then the dectionary size 
				returnes error.. that's why we try to set withen the interval num. if this gives error 
				we go back to the default value 0. 
				"""
				try:
					stepUnitCbox2 = stepUnitItems(interval,self.stepUnitDic[interval])
				except:
					self.stepUnitDic[interval] = 0
					stepUnitCbox2 = stepUnitItems(interval,self.stepUnitDic[interval])
				stepUnitCbox2.currentIndexChanged.connect(self.stepUnitSaveIndex)
				self.interval_UI.tableWidget.setCellWidget(interval, IntervalGUI.IntervalCols.stepUnit.value,stepUnitCbox2)
				self.Intervals[interval]["stepUnit"]   =   self.stepUnitDic[interval]
			except:
				pass
				#if GlobalCfg ["loadedConfig"]=="No":
				#	pass
				#else: 
				#	Common.show_message(QtWidgets.QMessageBox.Critical,
				#		"Invalid interval(s) settings, "\
				#		"the the tool will quite now, re-run it again and please make sure that the intervals configrations are correct"
				#		,"XAFS/XRF scan tool",QtWidgets.QMessageBox.Ok)
				#	sys.exit()
	def setIntervalsNumber(self, cfg):
		
		NIntervals = cfg["NIntervals"]
		global GlobalCfg
		GlobalCfg = cfg

		#print ("xxxxx",cfg["Intervals"])
		self._AcqTimes = [-1 for i in range(NIntervals)] 
		self._stepUnitItems = [-1 for i in range(NIntervals)] 
		self.interval_UI.tableWidget.setRowCount(NIntervals)
		if "Intervals" in cfg.keys():
			if len(cfg["Intervals"]) > len(self.Intervals):
				self.Intervals = cfg["Intervals"]

			#print(Intervals)

			for interval in range(NIntervals): 
				try:
					self.Intervals[interval]["Startpoint"] = self.interval_UI.tableWidget.item(interval, 0).text()
					self.Intervals[interval]["Endpoint"] = self.interval_UI.tableWidget.item(interval, 1).text()
					self.Intervals[interval]["Stepsize"] = self.interval_UI.tableWidget.item(interval, 2).text()
					self.Intervals[interval]["IcsIntTime"] = self.interval_UI.tableWidget.item(interval, 3).text()
					self.Intervals[interval]["DetIntTime"] = self.FicusIntTimeDic[interval]
					self.Intervals[interval]["stepUnit"]	= self.stepUnitDic[interval]
				except:
					pass 



			self.interval_UI.tableWidget.clearContents()
			for interval in range(NIntervals):
				if interval < len(self.Intervals):
					if self.Intervals[interval]:
						self.interval_UI.tableWidget.setItem(interval, IntervalGUI.IntervalCols.start.value,QtWidgets.QTableWidgetItem(str(self.Intervals[interval]["Startpoint"]),0))
						self.interval_UI.tableWidget.setItem(interval, IntervalGUI.IntervalCols.end.value,QtWidgets.QTableWidgetItem(str(self.Intervals[interval]["Endpoint"]),0))
						self.interval_UI.tableWidget.setItem(interval, IntervalGUI.IntervalCols.step.value,QtWidgets.QTableWidgetItem(str(self.Intervals[interval]["Stepsize"]),0))
						self.interval_UI.tableWidget.setItem(interval, IntervalGUI.IntervalCols.ICInt.value,QtWidgets.QTableWidgetItem(str(self.Intervals[interval]["IcsIntTime"]),0))

						cbox = AcqTime(interval,self.Intervals[interval]["DetIntTime"])
						cbox.currentIndexChanged.connect(self.saveindex)
						self._AcqTimes[interval] = self.Intervals[interval]["DetIntTime"]
						self.FicusIntTimeDic[interval] = self.Intervals[interval]["DetIntTime"]
						self.interval_UI.tableWidget.setCellWidget(interval, IntervalGUI.IntervalCols.DetInt.value,cbox)
						
						stepUnitCbox = stepUnitItems(interval,self.Intervals[interval]["stepUnit"])
						stepUnitCbox.currentIndexChanged.connect(self.stepUnitSaveIndex)
						self._stepUnitItems[interval] = self.Intervals[interval]["stepUnit"]
						self.stepUnitDic[interval] = self.Intervals[interval]["stepUnit"]
						self.interval_UI.tableWidget.setCellWidget(interval, IntervalGUI.IntervalCols.stepUnit.value,stepUnitCbox)


						if "ExtTrig" in self.Intervals[interval].keys():
							self.interval_UI.tableWidget.setItem(interval,IntervalGUI.IntervalCols.ExtTrig.value,QtWidgets.QTableWidgetItem(str(self.Intervals[interval]["ExtTrig"]), 0))

				else:
					AcqCbox = AcqTime(interval,-1)
					AcqCbox.currentIndexChanged.connect(self.saveindex)
					self.interval_UI.tableWidget.setCellWidget(interval, IntervalGUI.IntervalCols.DetInt.value,AcqCbox)
					self._AcqTimes.append(-1)

					stepUnitCbox2 = stepUnitItems(interval,-1)
					stepUnitCbox2.currentIndexChanged.connect(self.stepUnitSaveIndex)
					self.interval_UI.tableWidget.setCellWidget(interval, IntervalGUI.IntervalCols.stepUnit.value,stepUnitCbox2)
					self._stepUnitItems.append(-1)

		else:
			if len(self.FicusIntTimeDic) == 0:
				for interval in range(NIntervals):
					AcqCbox = AcqTime(interval,-1)
					AcqCbox.currentIndexChanged.connect(self.saveindex)
					self.interval_UI.tableWidget.setCellWidget(interval, IntervalGUI.IntervalCols.DetInt.value,AcqCbox)
					self._AcqTimes.append(-1)

					stepUnitCbox2 = stepUnitItems(interval,-1)
					stepUnitCbox2.currentIndexChanged.connect(self.stepUnitSaveIndex)
					self.interval_UI.tableWidget.setCellWidget(interval, IntervalGUI.IntervalCols.stepUnit.value,stepUnitCbox2)
					self._stepUnitItems.append(-1)


			else:
				for interval in range(NIntervals):
					try:
						AcqCbox = AcqTime(interval,self.FicusIntTimeDic[interval])
						AcqCbox.currentIndexChanged.connect(self.saveindex)
						self.interval_UI.tableWidget.setCellWidget(interval, IntervalGUI.IntervalCols.DetInt.value,AcqCbox)

						stepUnitCbox2 = stepUnitItems(interval,self.stepUnitDic[interval])
						stepUnitCbox2.currentIndexChanged.connect(self.stepUnitSaveIndex)
						self.interval_UI.tableWidget.setCellWidget(interval, IntervalGUI.IntervalCols.stepUnit.value,stepUnitCbox2)

					except:
						AcqCbox = AcqTime(interval,-1)
						AcqCbox.currentIndexChanged.connect(self.saveindex)
						self.interval_UI.tableWidget.setCellWidget(interval, IntervalGUI.IntervalCols.DetInt.value,AcqCbox)
						self._AcqTimes.append(-1)

						stepUnitCbox2 = stepUnitItems(interval,-1)
						stepUnitCbox2.currentIndexChanged.connect(self.stepUnitSaveIndex)
						self.interval_UI.tableWidget.setCellWidget(interval, IntervalGUI.IntervalCols.stepUnit.value,stepUnitCbox2)
						self._stepUnitItems.append(-1)

	def saveindex(self,index):
		senderIndex = self.intervalDialog.sender().index
		self._AcqTimes[senderIndex] = index
		self.FicusIntTimeDic[senderIndex]=index

	def stepUnitSaveIndex(self,index):
		senderIndex = self.intervalDialog.sender().index
		self._stepUnitItems[senderIndex] = index
		self.stepUnitDic[senderIndex]=index

class DetectorsGUI:		
	def __init__(self):
		self.detectors = ["IC1", "IC2", "IC3", "FICUS", "KETEK"]
		self.detectorsDialog = QtWidgets.QDialog()
		self.detectors_UI = detectorsForm.Ui_Dialog()
		self.detectors_UI.setupUi(self.detectorsDialog)

class AcqTime(QtWidgets.QComboBox):
   def __init__(self, index,value, parent = None):
	   super(AcqTime, self).__init__(parent)
	   self.addItem("5 ms")			#0
	   self.addItem("7.5 ms")		#1	
	   self.addItem("10 ms")		#2
	   self.addItem("25 ms")		#3
	   self.addItem("50 ms")		#4
	   self.addItem("75 ms")		#5
	   self.addItem("100 ms")		#6
	   self.addItem("250 ms")		#7
	   self.addItem("500 ms")		#8
	   self.addItem("750 ms")		#9
	   self.addItem("1 s")			#10
	   self.addItem("2.5 s")		#11
	   self.addItem("5 s")			#12
	   self.addItem("7.5 s")		#13
	   self.addItem("10 s")			#14
	   self.addItem("Ext Trigger")	#15
	   self.index = index
	   #print (self.index)
	   self.setCurrentIndex(value)

class stepUnitItems(QtWidgets.QComboBox):
   def __init__(self, index,value, parent = None):
	   super(stepUnitItems, self).__init__(parent)
	   self.addItem("eV")	    #0
	   self.addItem("K")		#1	
	   self.index = index

	   if value == -1:
	   	# add default value eV
	   	self.setCurrentIndex(0)
	   else:
	   	self.setCurrentIndex(value)

	   #self.setCurrentIndex(value)
	   #self.appExeCB.setCurrentIndex(self.items.keys().index('Maya Executable'))


class SED:
	Header = ['Proposal', 'Title', 'Proposer', 'Email', 'Beamline', 'Begin', 'End', 'Assigned shifts', 'Assigned hours', 'Semester', 'Experimental_Data_Path']

	def parsePropsalFile(self, filename):
		data = {}
		ProposalData = csv.reader(open(filename, 'r'))
		header = next(ProposalData)
		if not len(header) == len(SED.Header):
			print("invalid file: missing columns")
			Common.show_message(QtWidgets.QMessageBox.Critical,"Invalid Metadata file: missing columns","XAFS/XRF scan tool",QtWidgets.QMessageBox.Ok)
			sys.exit()

		for col_name in header:
			if not col_name in SED.Header:
				print("invalid file: unexpected column(s)")
				Common.show_message(QtWidgets.QMessageBox.Critical,"Invalid Metadata file: unexpected column(s)","XAFS/XRF scan tool",QtWidgets.QMessageBox.Ok)
				sys.exit()	

		for col in header:
			data[col] = None

		propsal = next(ProposalData)
		data = dict(zip(header, propsal))
		result , propsal_data = self.validatePropsalData(data)
		if result == True:
			return propsal_data
		else:
			Common.show_message(QtWidgets.QMessageBox.Critical,"Invalid Metadata file: metadata validation failed","XAFS/XRF scan tool",QtWidgets.QMessageBox.Ok)
			print(result)
			sys.exit()


	def validatePropsalData(self,propsal):
		propsal_data    = {}
		result = True
		for entry,value in propsal.items():
			if Common.regexvalidation(entry,value):
				propsal_data[entry] = value
			else:
				result = "vaildation error: {}|{}".format(entry,value)
				break
		return result,propsal_data

	def getPropsalData(self,proposal_ID):
		if Common.regexvalidation("Proposal", proposal_ID):
			proposal_ID = int(proposal_ID)
			propsal_data = self.parsePropsalFile("metadata/Scanning_Tool.csv")
			if int(propsal_data["Proposal"]) == proposal_ID:
				try:
					UsersinfoFile = open('configrations/userinfo.json','w')
					json.dump(propsal_data,UsersinfoFile, indent=2)
					UsersinfoFile.close()
					PathsFile = open('configrations/paths.json', 'r+')
					PathsFileData = json.load(PathsFile)
					PathsFileData["users_data_path"] = propsal_data["Experimental_Data_Path"]
					PathsFile.close()
					PathsFile = open('configrations/paths.json', 'w')
					json.dump(PathsFileData,PathsFile, indent=2)
					PathsFile.close()
					return True
				except Exception as e:
					Common.show_message(QtWidgets.QMessageBox.Critical,"local configuration files missing","XAFS/XRF scan tool",QtWidgets.QMessageBox.Ok)
				return False	
			else:
				Common.show_message(QtWidgets.QMessageBox.Critical,"wrong proposal ID or not scheduled","Proposal ID vedrification",QtWidgets.QMessageBox.Ok)
				return False
		else:
			Common.show_message(QtWidgets.QMessageBox.Critical,"invalid proposal ID","XAFS/XRF scan tool",QtWidgets.QMessageBox.Ok)
			return False

	def init(self, proposalID):
		self.proposalID = proposalID
		#FNULL = open(os.devnull, 'w')
		#getMetaDataResult = subprocess.call(["./get-metadata.sh"], stdout=FNULL)

		todayProposal = os.path.exists("metadata/Scanning_Tool.csv")
		if todayProposal:
			if self.getPropsalData(proposalID):
				return True
			else:
				return False
		else:
			UIMessage("Error reading today's metadata file",
					"Scanning_Tool.csv files is not exist", 
					"Try to start the experiment again, if the problem continues please contact the DCA Group").showCritical()
			CLIMessage("Error reading today's metadata file","E")
			#Common.show_message(QtWidgets.QMessageBox.Critical,"Metadata gathering error","XAFS/XRF scan tool",QtWidgets.QMessageBox.Ok)
			#sys.exit()

		#FNULL.close()
