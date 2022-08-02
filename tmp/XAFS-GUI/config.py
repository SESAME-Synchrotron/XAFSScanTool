
#!/usr/bin/python3

from forms import configWizard, samplespositionForm, intervalsForm, detectorsForm
from enum import Enum
from PyQt5 import QtWidgets

#import SED
import json
import datetime
import sys
import subprocess
import csv
import re
import os

import common

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
		self.guiObj = configWizard.Ui_Wizard()
		self.guiObj.setupUi(self.Qwiz)

		self.paths = paths

		self.cfg = {}
		self.expType = "users"

		self.IntervalsGUI   = IntervalGUI()
		self.SamplesGUI     = SamplePosGUI()
		self.DetectorsGUI   = DetectorsGUI()

		self.IntervalsGUI.intervalDialog.accepted.connect(self.saveIntervals)

		self.guiObj.ExpType.nextId = self.CheckExptype
		self.guiObj.SED.nextId = self.checkPropsalID
		self.guiObj.CfgFile.nextId = self.cfgfile
		self.guiObj.CfgPath.nextId = self.loadcfg
		self.guiObj.scan_params.nextId = self.chechConfig
		self.Qwiz.button(QtWidgets.QWizard.FinishButton).clicked.connect(self.start)

		self.guiObj.Browse.clicked.connect(self.BrowseCfgFile)
		self.guiObj.editIntrv.clicked.connect(self.editIntervals)
		self.guiObj.editSample.clicked.connect(self.editSamples)
		self.guiObj.configureDetectors.clicked.connect(self.Detectors)

		self.Qwiz.exec_()

	def CheckExptype(self):
		if self.guiObj.UsersExp.isChecked():
			return self.WizardPages.SED.value
		else:
			self.expType = "local"
			return self.WizardPages.CfgFile.value

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
			return self.WizardPages.editCfg.value
		else:
			return self.WizardPages.LoadCfg.value

	def loadcfg(self):
		path = self.guiObj.filePath.text()
		if not path == "":
			return self.WizardPages.editCfg.value
		else:
			return self.WizardPages.LoadCfg.value

	def editIntervals(self):
		Nintrv = self.guiObj.setNumofIterv.text()
		if common.regexvalidation("NIntervals", Nintrv):
			Nintrv = int(Nintrv)
			self.cfg["NIntervals"] = Nintrv
			self.IntervalsGUI.setIntervalsNumber(self.cfg)
			self.IntervalsGUI.intervalDialog.exec()				
		else:
			common.show_message(QtWidgets.QMessageBox.Critical,
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
		if common.regexvalidation("Nsample", Nsamples):
			Nsamples = int(Nsamples)
			self.cfg["Nsamples"] = Nsamples
			self.SamplesGUI.setSamplesNumber(self.cfg)
			self.SamplesGUI.sampleDialog.exec_()
		else:
			common.show_message(QtWidgets.QMessageBox.Critical,
								"Please enter Number of samples",
								"XAFS/XRF scan tool", QtWidgets.QMessageBox.Ok)
	
	def saveIntervals(self):
		intervals = [{} for i in range(int(self.cfg["NIntervals"]))]
		for interval in range(self.IntervalsGUI.interval_UI.tableWidget.rowCount()):
			start = self.IntervalsGUI.interval_UI.tableWidget.item(interval, 0).text()
			if start == '' or not common.validate("Startpoint", start, "Please enter valid start point"):
				return self.WizardPages.editCfg.value
			else:
				intervals[interval]["Startpoint"] = float(start)		
			end = self.IntervalsGUI.interval_UI.tableWidget.item(interval,1).text()
			if end == '' or not common.validate("Endpoint", end, "Please enter valid end point"):
				return self.WizardPages.editCfg.value
			else:
				intervals[interval]["Endpoint"] = float(end)		
			stepsize = self.IntervalsGUI.interval_UI.tableWidget.item(interval, 2).text()
			if stepsize == '' or not common.validate("Stepsize", stepsize, "Please enter valid step size"):
				return self.WizardPages.editCfg.value
			else:
				intervals[interval]["Stepsize"] = float(stepsize)		
			IcIntTime = self.IntervalsGUI.interval_UI.tableWidget.item(interval, 3).text()
			if IcIntTime == '' or not common.validate("IcsIntTime", IcIntTime,"Please enter valid IC integration time"):
				return self.WizardPages.editCfg.value
			else:
				intervals[interval]["IcsIntTime"] = float(IcIntTime)		
			intervals[interval]["DetIntTime"] = self.IntervalsGUI._AcqTimes[interval]		
			isExtTrigger = self.IntervalsGUI._AcqTimes[interval]
			if isExtTrigger == 15:
				ExtTriggerIntTime = self.IntervalsGUI.interval_UI.tableWidget.item(interval, 5).text()
				if ExtTriggerIntTime == '' or not common.validate(
						"ExtTriggerIntTime", ExtTriggerIntTime,"Please enter valid External Trigger duration"):
					return self.WizardPages.editCfg.value
				else:
					intervals[index]["ExtTrig"] = float(ExtTriggerIntTime)
		self.cfg["Intervals"] = intervals

	def BrowseCfgFile(self):
		self.IntervalsGUI	= IntervalGUI()
		self.SamplesGUI		= SamplePosGUI()
		self.DetectorsGUI	= DetectorsGUI()

		self.cfgpath = QtWidgets.QFileDialog.getOpenFileName(self.Qwiz, "choose configuration file", "~","*.cfg")[0]
		self.guiObj.filePath.setText(self.cfgpath)
		self.cfg = self.loadcfgfile(self.cfgpath)

		NIntervals = self.cfg["NIntervals"]
		Nsamples = self.cfg["Nsamples"]
		Nscans = self.cfg["Nscans"]

		self.guiObj.setNumofIterv.setText(str(NIntervals))
		self.guiObj.setNumofSamples.setText(str(Nsamples))
		self.guiObj.setNumofExafsScans.setText(str(Nscans))

		self.guiObj.setDataFileName.setText(self.cfg["DataFileName"])

		for interval in range(len(self.cfg["Intervals"])):
			self.IntervalsGUI.interval_UI.tableWidget.setItem(interval, IntervalGUI.IntervalCols.start.value,QtWidgets.QTableWidgetItem(str(self.cfg["Intervals"][interval]["Startpoint"]),0))
			self.IntervalsGUI.interval_UI.tableWidget.setItem(interval, IntervalGUI.IntervalCols.end.value,QtWidgets.QTableWidgetItem(str(self.cfg["Intervals"][interval]["Endpoint"]),0))
			self.IntervalsGUI.interval_UI.tableWidget.setItem(interval, IntervalGUI.IntervalCols.step.value,QtWidgets.QTableWidgetItem(str(self.cfg["Intervals"][interval]["Stepsize"]),0))
			self.IntervalsGUI.interval_UI.tableWidget.setItem(interval, IntervalGUI.IntervalCols.ICInt.value,QtWidgets.QTableWidgetItem(str(self.cfg["Intervals"][interval]["IcsIntTime"]),0))

			cbox = AcqTime(interval,self.cfg["Intervals"][interval]["DetIntTime"])
			self.IntervalsGUI.interval_UI.tableWidget.setCellWidget(interval, IntervalGUI.IntervalCols.DetInt.value,cbox)
			if "ExtTrig" in self.cfg["Intervals"][interval].keys():
				self.IntervalsGUI.interval_UI.tableWidget.setItem(interval,IntervalGUI.IntervalCols.ExtTrig.value,QtWidgets.QTableWidgetItem(str(self.cfg["Intervals"][interval]["ExtTrig"]), 0))

		for sample in range(len(self.cfg["Samplespositions"])):
			self.SamplesGUI.sample_UI.samplepositions.setItem(sample, SamplePosGUI.SampleCols.X.value,QtWidgets.QTableWidgetItem(str(self.cfg["Samplespositions"][sample]["Xposition"]), 0))
			self.SamplesGUI.sample_UI.samplepositions.setItem(sample, SamplePosGUI.SampleCols.Y.value,QtWidgets.QTableWidgetItem(str(self.cfg["Samplespositions"][sample]["Yposition"]), 0))
		
	def chechConfig(self):
		try:
			NIntervals = self.guiObj.setNumofIterv.text()
			if NIntervals == '' or not common.validate(
					"NIntervals", NIntervals,"Please enter valid Number of INtervals"):
				return self.WizardPages.editCfg.value

			Nsamples = self.guiObj.setNumofSamples.text()
			if Nsamples == '' or not common.validate("Nsample", Nsamples, "Please enter valid Number of Samples"):
				return self.WizardPages.editCfg.value

			Nscans = self.guiObj.setNumofExafsScans.text()
			if Nscans == '' or not common.validate("Nscans", Nscans, "Please enter valid Number of scans"):
				return self.WizardPages.editCfg.value

			DataFileName = self.guiObj.setDataFileName.text()
			if DataFileName == '' or not common.validate("DataFileName", DataFileName,"Please enter valid data file name"):
				return self.WizardPages.editCfg.value


			intervals = [{} for i in range(int(NIntervals))]
			for interval in range(self.IntervalsGUI.interval_UI.tableWidget.rowCount()):
				start = self.IntervalsGUI.interval_UI.tableWidget.item(interval, 0).text()
				if start == '' or not common.validate("Startpoint", start, "Please enter valid start point"):
					return self.WizardPages.editCfg.value

				end = self.IntervalsGUI.interval_UI.tableWidget.item(interval,1).text()
				if end == '' or not common.validate("Endpoint", end, "Please enter valid end point"):
					return self.WizardPages.editCfg.value

				stepsize = self.IntervalsGUI.interval_UI.tableWidget.item(interval, 2).text()
				if stepsize == '' or not common.validate("Stepsize", end, "Please enter valid step size"):
					return self.WizardPages.editCfg.value

				IcIntTime = self.IntervalsGUI.interval_UI.tableWidget.item(interval, 3).text()
				if IcIntTime == '' or not common.validate("IcsIntTime", end,"Please enter valid IC integration time"):
					return self.WizardPages.editCfg.value

				intervals[interval]["DetIntTime"] = self.IntervalsGUI._AcqTimes[interval]

				isExtTrigger = self.IntervalsGUI._AcqTimes[interval]
				if isExtTrigger == 15:
					ExtTriggerIntTime = self.IntervalsGUI.interval_UI.tableWidget.item(interval, 5).text()
					if ExtTriggerIntTime == '' or not common.validate(
							"ExtTriggerIntTime", ExtTriggerIntTime,"Please enter valid External Trigger duration"):
						return self.WizardPages.editCfg.value

			SamplePositions = [{} for i in range(int(Nsamples))]
			for sample in range(self.SamplesGUI.sample_UI.samplepositions.rowCount()):
				Xposition = self.SamplesGUI.sample_UI.samplepositions.item(sample, 0).text()
				if Xposition == '' or not common.validate("Xposition", Xposition,"Please enter valid sample x position"):
					return self.WizardPages.editCfg.value

				Yposition = self.SamplesGUI.sample_UI.samplepositions.item(sample, 1).text()
				if Yposition == '' or not common.validate("Yposition", Yposition,"Please enter valid sample y position"):
					return self.WizardPages.editCfg.value

			return self.WizardPages.startscan.value
		except:
			return self.WizardPages.editCfg.value

	def start(self):
		NIntervals = self.guiObj.setNumofIterv.text()
		if NIntervals == '' or not common.validate(
				"NIntervals", NIntervals,"Please enter valid Number of INtervals"):
			return self.WizardPages.editCfg.value
		else:
			self.cfg["NIntervals"] = int(NIntervals)

		Nsamples = self.guiObj.setNumofSamples.text()
		if Nsamples == '' or not common.validate("Nsample", Nsamples, "Please enter valid Number of Samples"):
			return self.WizardPages.editCfg.value
		else:
			self.cfg["Nsamples"] = int(Nsamples)

		Nscans = self.guiObj.setNumofExafsScans.text()
		if Nscans == '' or not common.validate("Nscans", Nscans, "Please enter valid Number of scans"):
			return self.WizardPages.editCfg.value
		else:
			self.cfg["Nscans"] = int(Nscans)
		DataFileName = self.cfg["DataFileName"] = self.guiObj.setDataFileName.text()
		if DataFileName == '' or not common.validate("DataFileName", DataFileName,"Please enter valid data file name"):
			return self.WizardPages.editCfg.value
		else:
			self.cfg["DataFileName"] = DataFileName

		SamplePositions = [{} for i in range(int(Nsamples))]
		for sample in range(self.SamplesGUI.sample_UI.samplepositions.rowCount()):
			Xposition = self.SamplesGUI.sample_UI.samplepositions.item(sample, 0).text()
			if Xposition == '' or not common.validate("Xposition", Xposition,"Please enter valid sample x position"):
				return self.WizardPages.editCfg.value
			else:
				SamplePositions[sample]["Xposition"] = Xposition
			Yposition = self.SamplesGUI.sample_UI.samplepositions.item(sample, 1).text()
			if Yposition == '' or not common.validate("Yposition", Yposition,"Please enter valid sample y position"):
				return self.WizardPages.editCfg.value
			else:
				SamplePositions[sample]["Yposition"] = Yposition
		detectors = []
		for d in self.DetectorsGUI.detectors:
			detCheckbox = getattr(self.DetectorsGUI.detectors_UI, d)
			if detCheckbox.isChecked():
				detectors.append(d)
		if not detectors:
			common.show_message(QtWidgets.QMessageBox.Critical,
								"Please select detector(s)",
								"XAFS/XRF scan tool", QtWidgets.QMessageBox.Ok)		
		else:
			self.cfg["detectors"] = detectors

		#self.cfg["Intervals"] = self.IntervalsGUI.getFormData()

		self.cfg["Samplespositions"] = SamplePositions

		#json.dump(self.cfg,open("{}/configuration/{}.cfg".format(self.paths["local_data_path"],str(datetime.datetime.now())),"w"), indent=2)

	def loadcfgfile(self, cfgfilename):
		try:
			with open("{}".format(cfgfilename), "r") as cfgfile:
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

	def __init__(self):
		self.sampleDialog = QtWidgets.QDialog()
		self.sample_UI = samplespositionForm.Ui_Dialog()
		self.sample_UI.setupUi(self.sampleDialog)
	
	def setSamplesNumber(self, cfg):
		Nsamples = cfg["Nsamples"]
		self.sample_UI.samplepositions.setRowCount(Nsamples)

		if "Samplespositions" in cfg.keys():
			for sample in range(Nsamples):
				if sample < len(cfg["Samplespositions"]):
					self.sample_UI.samplepositions.setItem(sample, SamplePosGUI.SampleCols.X.value,QtWidgets.QTableWidgetItem(str(cfg["Samplespositions"][sample]["Xposition"]), 0))
					self.sample_UI.samplepositions.setItem(sample, SamplePosGUI.SampleCols.Y.value,QtWidgets.QTableWidgetItem(str(cfg["Samplespositions"][sample]["Yposition"]), 0))

class IntervalGUI:
	class IntervalCols(Enum):
		start	=	0
		end		=	1
		step	=	2
		ICInt	=	3
		DetInt	=	4
		ExtTrig	=	5
		
	def __init__(self):
		self.intervalDialog = QtWidgets.QDialog()
		self.interval_UI = intervalsForm.Ui_Dialog()
		self.interval_UI.setupUi(self.intervalDialog)
		self._AcqTimes = []

	def setIntervalsNumber(self, cfg):
		NIntervals = cfg["NIntervals"]
		#self._AcqTimes = [10 for i in range(NIntervals)] 
		self.interval_UI.tableWidget.setRowCount(NIntervals)
		if "Intervals" in cfg.keys():
			Intervals = cfg["Intervals"]
			self.interval_UI.tableWidget.clearContents()
			for interval in range(NIntervals):
				if interval <= len(Intervals):
						try:
							if Intervals[interval]:
								self.interval_UI.tableWidget.setItem(interval, IntervalGUI.IntervalCols.start.value,QtWidgets.QTableWidgetItem(str(Intervals[interval]["Startpoint"]),0))
								self.interval_UI.tableWidget.setItem(interval, IntervalGUI.IntervalCols.end.value,QtWidgets.QTableWidgetItem(str(Intervals[interval]["Endpoint"]),0))
								self.interval_UI.tableWidget.setItem(interval, IntervalGUI.IntervalCols.step.value,QtWidgets.QTableWidgetItem(str(Intervals[interval]["Stepsize"]),0))
								self.interval_UI.tableWidget.setItem(interval, IntervalGUI.IntervalCols.ICInt.value,QtWidgets.QTableWidgetItem(str(Intervals[interval]["IcsIntTime"]),0))

								cbox = AcqTime(interval,Intervals[interval]["DetIntTime"])
								cbox.currentIndexChanged.connect(self.saveindex)
								self._AcqTimes[interval] = Intervals[interval]["DetIntTime"]
								self.interval_UI.tableWidget.setCellWidget(interval, IntervalGUI.IntervalCols.DetInt.value,cbox)
								if "ExtTrig" in Intervals[interval].keys():
									self.interval_UI.tableWidget.setItem(interval,IntervalGUI.IntervalCols.ExtTrig.value,QtWidgets.QTableWidgetItem(str(Intervals[interval]["ExtTrig"]), 0))
						except Exception as e:
							self.addDetIntMenu(interval,10)
				else:
					AcqCbox = AcqTime(interval,10)
					AcqCbox.currentIndexChanged.connect(self.saveindex)
					self.interval_UI.tableWidget.setCellWidget(interval, IntervalGUI.IntervalCols.DetInt.value,AcqCbox)
					self._AcqTimes.append(10)

		else:
			self._AcqTimes = []
			for interval in range(NIntervals):
				self.addDetIntMenu(interval,10)	
	
	def addDetIntMenu(self,interval,index):
		AcqCbox = AcqTime(interval,index)
		AcqCbox.currentIndexChanged.connect(self.saveindex)
		self.interval_UI.tableWidget.setCellWidget(interval, IntervalGUI.IntervalCols.DetInt.value,AcqCbox)
		self._AcqTimes.append(index)

	def saveindex(self,index):
		senderIndex = self.intervalDialog.sender().index
		self._AcqTimes[senderIndex] = index

class DetectorsGUI:		
	def __init__(self):
		self.detectors = ["IC1", "IC2", "IC3", "FICUS_ROI1", "FICUS_ROI2", "FICUS_ROI3", "FICUS_ROI4", "FICUS_ROI5", "FICUS_ROI6", "FICUS_ROI7", "FICUS_ROI8", "KETEK_ROI1", "KETEK_ROI2", "KETEK_ROI3", "KETEK_ROI4", "KETEK_ROI5", "KETEK_ROI6", "KETEK_ROI7", "KETEK_ROI8", "FICUS_SPECMODE", "KETEK_SPECMODE"]
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
	   self.setCurrentIndex(value)

class SED:
	Header = ['Proposal', 'Title', 'Proposer', 'Email', 'Beamline', 'Begin', 'End', 'Assigned shifts', 'Assigned hours', 'Semester', 'Experimental_Data_Path']

	def parsePropsalFile(self, filename):
		data = {}
		ProposalData = csv.reader(open(filename, 'r'))
		header = next(ProposalData)
		if not len(header) == len(SED.Header):
			print("invalid file: missing columns")
			common.show_message(QtWidgets.QMessageBox.Critical,"Invalid Metadata file: missing columns","XAFS/XRF scan tool",QtWidgets.QMessageBox.Ok)
			sys.exit()

		for col_name in header:
			if not col_name in SED.Header:
				print("invalid file: unexpected column(s)")
				common.show_message(QtWidgets.QMessageBox.Critical,"Invalid Metadata file: unexpected column(s)","XAFS/XRF scan tool",QtWidgets.QMessageBox.Ok)
				sys.exit()	

		for col in header:
			data[col] = None

		propsal = next(ProposalData)
		data = dict(zip(header, propsal))
		result , propsal_data = self.validatePropsalData(data)
		if result == True:
			return propsal_data
		else:
			common.show_message(QtWidgets.QMessageBox.Critical,"Invalid Metadata file: metadata validation failed","XAFS/XRF scan tool",QtWidgets.QMessageBox.Ok)
			print(result)
			sys.exit()


	def validatePropsalData(self,propsal):
		propsal_data    = {}
		result = True
		for entry,value in propsal.items():
			if common.regexvalidation(entry,value):
				propsal_data[entry] = value
			else:
				result = "vaildation error: {}|{}".format(entry,value)
				break
		return result,propsal_data

	def getPropsalData(self,proposal_ID):
		if common.regexvalidation("Proposal", proposal_ID):
			proposal_ID = int(proposal_ID)
			propsal_data = self.parsePropsalFile("metadata/Scanning_Tool.csv")
			if int(propsal_data["Proposal"]) == proposal_ID:
				try:
					UsersinfoFile = open('userinfo.json','w')
					json.dump(propsal_data,UsersinfoFile, indent=2)
					UsersinfoFile.close()
					PathsFile = open('paths.json', 'r+')
					PathsFileData = json.load(PathsFile)
					PathsFileData["users_data_path"] = propsal_data["Experimental_Data_Path"]
					PathsFile.close()
					PathsFile = open('paths.json', 'w')
					json.dump(PathsFileData,PathsFile, indent=2)
					PathsFile.close()
					return True
				except Exception as e:
					common.show_message(QtWidgets.QMessageBox.Critical,"local configuration files missing","XAFS/XRF scan tool",QtWidgets.QMessageBox.Ok)
				return False	
			else:
				common.show_message(QtWidgets.QMessageBox.Critical,"wrong proposal ID or not scheduled","Proposal ID vedrification",QtWidgets.QMessageBox.Ok)
				return False
		else:
			common.show_message(QtWidgets.QMessageBox.Critical,"invalid proposal ID","XAFS/XRF scan tool",QtWidgets.QMessageBox.Ok)
			return False

	def init(self, proposalID):
		self.proposalID = proposalID
		FNULL = open(os.devnull, 'w')
		getMetaDataResult = subprocess.call(["./get-metadata.sh"], stdout=FNULL)
		if getMetaDataResult == 0:
			if self.getPropsalData(proposalID):
				return True
			else:
				return False
		else:
			common.show_message(QtWidgets.QMessageBox.Critical,"Metadata gathering error","XAFS/XRF scan tool",QtWidgets.QMessageBox.Ok)
			sys.exit()

		FNULL.close()