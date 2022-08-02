#!/usr/bin/python3

import collections
import csv
import config
import common
import datetime
import decimal
import json
import math
import os
import re
import subprocess
import sys
import time

import numpy as np
import epics
from PyQt5 import QtWidgets

class XAFSSCAN:
	def __init__(self):
		self.PVs = self.loadPVS()
		self.paths		= self.loadpathfile()
		self.cfg		= config.ConfigGUI(self.paths).cfg
		print(self.cfg)
		
		self.userinfo	= self.loaduserinfo()
		self.initPaths()
		self.initDCM()
		self.initFicus()
		self.initExperiment()

		self.start()
		
	def start(self):
		self.initPlot()

		for sample in range(self.cfg["Nsamples"]):
			self.MoveSmpX(self.cfg["positions"][sample]["X"])
			self.MoveSmpY(self.cfg["positions"][sample]["Y"])

			for scan in range(self.cfg["Nscans"]):
				self.datafile = self.initDatafile()
				self.clearPlot()
				
				for interval in range(self.cfg["NIntervals"]):
					IntervalObj = self.cfg["Intervals"][interval]

					Startpoint	 	=	IntervalObj["Startpoint"]
					Endpoint	 	=	IntervalObj["Endpoint"]
					Stepsize	 	=	IntervalObj["Stepsize"]
					FicusIntTime 	=	IntervalObj["FicusIntTime"]
					IcsIntTime	 	=	IntervalObj["IcsIntTime"]

					#SettlingTime 	=	self.cfg["SettlingTime"]

					FrameDuration	=	self.Ficus_Ingtime[FicusIntTime]

					scanpoints = self.drange(Startpoint, Endpoint, Stepsize)
					for point in scanpoints:
						self.MoveDCM(point)
						#time.sleep(SettlingTime)

						self.PVs["IC0:Npoints"].put(IcsIntTime)
						self.PVs["IC1:Npoints"].put(IcsIntTime)
						self.PVs["IC2:Npoints"].put(IcsIntTime)

						self.PVs["Ficus:FrameDuration"].put(FicusIntTime)

						self.PVs["Ficus:Start"].put(1)

						time.sleep(FrameDuration)

						Energy		=	float("{:0.4f}".format( self.PVs["DCM:Energy:RBV"].get()))
						Elapsedtime	=	self.PVs["Ficus:Elapsedtime"].get()
						ROIs		=	self.PVs['Ficus:ROIs'].get()
						ROIsE		=	np.divide(ROIs,Elapsedtime)

						I0Dp	= self.PVs["IC0:AvgCurrent"].get() if self.PVs["IC0:AvgCurrent"].get() > 5e-10 else 1E-16
						ItDp	= self.PVs["IC1:AvgCurrent"].get() if self.PVs["IC1:AvgCurrent"].get() > 5e-10 else 1E-16
						It2Dp	= self.PVs["IC2:AvgCurrent"].get() if self.PVs["IC2:AvgCurrent"].get() > 5e-10 else 1E-16
						
						AbsorptionTrDp		= math.log(I0Dp /ItDp)
						AbsorptionTr2Dp		= math.log(ItDp / It2Dp)
						IfDp				= ROIs[0]
						AbsorptionFluoDp	= math.log(IfDp /I0Dp)

						DeadTime			= np.mean(self.PVs["Ficus:Deadtime"].get())

						print("Sample# {} | Scan# {} | Interval {}".format(sample, scan, interval))
						print("Energy: {} | I0: {} | It: {} | It2: {} | AbsTr: {} | AbsTr2: {} | If: {} | AbsFlu: {}".format(Energy, I0Dp, ItDp, It2Dp, AbsorptionTrDp, AbsorptionTr2Dp, IfDp, AbsorptionFluoDp))

						self.Energy.append(Energy)
						self.I0.append(I0Dp)
						self.It.append(ItDp)
						self.It2.append(It2Dp)
						self.AbsTr.append(AbsorptionTrDp)
						self.AbsTr2.append(AbsorptionTr2Dp)
						self.If.append(IfDp)
						self.AbsFlu.append(AbsorptionFluoDp)

						self.setPlotData()

						Datapoint = {}

						Datapoint["Sample#"]		=	(sample+1)
						Datapoint["Scan#"]			=	(scan+1)
						Datapoint["Interval"]		=	(interval+1)
						Datapoint["ENERGY-RBK"]		=	Energy
						Datapoint["IC1[A]"]			=	I0Dp
						Datapoint["TRANS"]			=	AbsorptionTrDp
						Datapoint["FLUOR"]			=	AbsorptionFluoDp
						Datapoint["IC2[A]"]			=	ItDp
						Datapoint["IC3[A]"]			=	It2Dp
						Datapoint["ROI_0[c/s]"]		=	ROIsE[0]
						Datapoint["ROI_1[c/s]"]		=	ROIsE[1]
						Datapoint["ROI_2[c/s]"]		=	ROIsE[2]
						Datapoint["ROI_3[c/s]"]		=	ROIsE[3]
						Datapoint["ROI_4[c/s]"]		=	ROIsE[4]
						Datapoint["ROI_5[c/s]"]		=	ROIsE[5]
						Datapoint["ROI_6[c/s]"]		=	ROIsE[6]
						Datapoint["ROI_7[c/s]"]		=	ROIsE[7]
						Datapoint["INT_TIME[sec]"]	=	IcsIntTime
						Datapoint["e-time[sec]"]	=	FrameDuration
						Datapoint["DEADTIME[%]"]	=	DeadTime

						self.writeDataPoint(Datapoint)
					
	def loadPVS(self):
		def ContinueQuestion(PvName):
    			box = QtWidgets.QMessageBox()
			box.setIcon(QtWidgets.QMessageBox.Question)
			box.setText("{} : is not connected\n Do you want to continue?".format(PvName))
			box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
			box.setDefaultButton(QtWidgets.QMessageBox.No)
			buttonYes = box.button(QtWidgets.QMessageBox.Yes)
			buttonNo = box.button(QtWidgets.QMessageBox.No)
			box.exec_()
			if box.clickedButton() == buttonNo:
				sys.exit() 
			
		with open('pvlist/xafs.json', "r") as pvfile:
			pvlist = json.load(pvfile)
			PVS = {}
			DisconnectedPvs = []
			try:
				for PvEntry, PvName in pvlist.items():
					PvName = PvName["pvname"]
					PvObj = epics.PV(PvName)
					status = PvObj.get()					
					if status:
						print("{} : Connected".format(PvName))
						PVS[PvEntry] = PvObj
					else:
						print("{} : is not connected\n".format(PvName))
						DisconnectedPvs.append("{}\n".format(PvName))
						ContinueQuestion(PvName)
					
				pvfile.close()
				common.show_message(QtWidgets.QMessageBox.Critical,"The following PVs are disconnected:\n {}".format(" ".join(DisconnectedPvs)),"scan tool" ,QtWidgets.QMessageBox.Ok)

			except Exception as e:
				common.show_message(QtWidgets.QMessageBox.Critical,"PVs loading problem","scan tool" ,QtWidgets.QMessageBox.Ok)
				print(e)
				sys.exit()
				return
		
			return PVS

	def loadpathfile(self):
		try:
			with open('paths.json', "r") as pathfile:
				data = json.load(pathfile)
				pathfile.close()
				return data
		except Exception as e:
			print("path.json load error")
			print(e)
	
	def loaduserinfo(self):
		try:
			with open('userinfo.json', "r") as userinfofile:
				data = json.load(userinfofile)
				userinfofile.close()
				return data
		except Exception as e:
			print("userinfo.json load error")
			print(e)
	
	def initPaths(self):
		self.BasePath			=	"{}/SEM[{}]/XAFS/{}".format(self.paths['local_data_path'], self.userinfo["Semester"], self.userinfo['Proposal'])
		self.cfgdirpath			=	"{}/configuration".format(self.BasePath)
		self.cfgfilepath		=	"{}/exafs_{}--{}.cfg".format(self.cfgdirpath,self.userinfo['Proposal'],str(datetime.datetime.now())) 
		self.csvdatapath		=   "{}/data/csv".format(self.BasePath)

	def initDCM(self):
		self.PVs["DCM:Energy:Theta:Sync"].put(1)

		self.PVs["DCM:Theta:SPMG"].put(0) # Stop
		time.sleep(0.1)
		self.PVs["DCM:Theta:SPMG"].put(3) # Go
		time.sleep(0.1)

		self.PVs["DCM:Y:SPMG"].put(0) # Stop
		time.sleep(0.1)
		self.PVs["DCM:Y:SPMG"].put(3) # Go
		time.sleep(0.1)

		self.energy0 = self.cfg["Intervals"][0]["Startpoint"]
		self.MoveDCM(energy0)

	def MoveDCM(self,SP):
		self.PVs["DCM:Theta:SPMG"].put(0) # Stop
		time.sleep(0.1)
		self.PVs["DCM:Theta:SPMG"].put(3) # Go
		time.sleep(0.1)

		self.PVs["DCM:Energy:SP"].put(SP)
		self.PVs["DCM:Move"].put(1)
		time.sleep(0.1) 
		while not self.PVs["DCM:Energy:Moving"]:
			self.PVs["DCM:Move"].put(1)
			time.sleep(0.1)
	
	def initFicus(self):
		while True:
			if not self.PVs["Ficus:Connected"]:
				time.sleep(1)
				input("Ficus is not connect, Please connect it and press any key to retry")
			else:
				break
		
		self.PVs["Ficus:Erase"].put(1)
		self.Ficus_Ingtime = [0.005, 0.0075, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10]
	
	def initExperiment(self):
		FicusBaseDir = self.paths["ficus_workstation_data_path"]
		self.PVs["Ficus:Basedir"].put(FicusBaseDir)
		self.PVs["Ficus_ExpID"].put(self.userinfo["Proposal"])

		if not os.path.exists(self.cfgdirpath):
			os.makedirs(self.cfgdirpath)
		
		with open(self.cfgfilepath,'w') as cfgfile:
			json.dump(self.cfg,cfgfile)

		self.csvdatafilename	=	"{}-{}.dat".format(self.cfg["DataFileName"], datetime.datetime.now().strftime("%m/%d/%Y-%H:%M:%S"))
		self.csvfilepath		=	"{}/{}".format(self.csvdatapath, self.csvdatafilename)

		if not os.path.exists(self.csvdatapath): 
			os.makedirs(self.csvdatapath)

	def clearPlot(self):
		self.initPlotData()

		self.PVs["PLOT:Energy"].put(self.Energy)
		self.PVs["PLOT:I0"].put(self.I0)
		self.PVs["PLOT:It"].put(self.It)
		self.PVs["PLOT:It2"].put(self.It2)
		self.PVs["PLOT:AbsTr"].put(self.AbsTr)
		self.PVs["PLOT:AbsTr2"].put(self.AbsTr2)
		self.PVs["PLOT:If"].put(self.If)
		self.PVs["PLOT:AbsFlu"].put(self.AbsFlu)
	
	def setPlotData(self):
		self.PVs["PLOT:Energy"].put(self.Energy)
		self.PVs["PLOT:I0"].put(self.I0)
		self.PVs["PLOT:It"].put(self.It)
		self.PVs["PLOT:It2"].put(self.It2)
		self.PVs["PLOT:AbsTr"].put(self.AbsTr)
		self.PVs["PLOT:AbsTr2"].put(self.AbsTr2)
		self.PVs["PLOT:If"].put(self.If)
		self.PVs["PLOT:AbsFlu"].put(self.AbsFlu)

	def initPlot(self):
		self.initPlotData()
		self.clearPlot()
	
	def initPlotData(self):
		self.Energy	= []
		self.I0		= []
		self.It		= []
		self.It2	= []
		self.AbsTr	= []
		self.AbsTr2	= []
		self.If		= []
		self.AbsFlu	= []
	
	def drange(self,start,stop,step,prec=10):
		decimal.getcontext().prec = prec
		points = []
		r= decimal.Decimal(start)
		step = decimal.Decimal(step)
		while r <=stop:
			points.append(float(r))
			r += step
		return points
	
	def MoveSmpX(self,SP):
		self.PVs["SMP:X:SPMG"].put(3) # Go
		self.PVs["SMP:X:SP"].put(SP)
		time.sleep(0.1) 
		while not self.PVs["SMP:X:Moving"]:
			self.PVs["SMP:X:SP"].put(SP)
			time.sleep(0.2)
	
	def MoveSmpY(self,SP):
		self.PVs["SMP:Y:SPMG"].put(3) # Go
		self.PVs["SMP:Y:SP"].put(SP)
		time.sleep(0.1) 
		while not self.PVs["SMP:Y:Moving"]:
			self.PVs["SMP:Y:SP"].put(SP)
			time.sleep(0.2)
	
	def initDatafile(self):
		with open(self.csvfilepath, 'w') as datafile:
			header = ["Sample#", "Scan#", "Interval", "ENERGY-RBK", "IC1[A]", "TRANS", "FLUOR", "IC2[A]", "IC3[A]", "ROI_0[c/s]",  "ROI_1[c/s]", "ROI_2[c/s]", "ROI_3[c/s]", "ROI_4[c/s]", "ROI_5[c/s]", "ROI_6[c/s]", "ROI_7[c/s]",  "INT_TIME[sec]",  "e-time[sec]", "DEADTIME[%]"]
			csv.DictWriter(datafile, fieldnames=header)
	
	def writeDataPoint(self, dp):
		with open(self.csvfilepath, 'w') as datafile:
			datafile.writerow(dp)
			datafile.close()