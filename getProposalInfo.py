import json
import sys
#import subprocess
import csv
import re
import os
from SEDSS.SEDSupport import readFile
from SEDSS.SEDSupplements import CLIMessage, UIMessage

from  common import Common
from PyQt5 import QtWidgets, QtCore

class SED:
	def __init__(self, proposalID):
		self.proposalID = proposalID
		#FNULL = open(os.devnull, 'w')
		#getMetaDataResult = subprocess.call(["./get-metadata.sh"], stdout=FNULL)

		todayProposal = os.path.exists("metadata/Scanning_Tool.csv")
		if todayProposal:
			self.getPropsalData(proposalID)
		else:
			UIMessage("Error reading today's metadata file",
					"Scanning_Tool.csv files is not exist", 
					"Try to start the experiment again, if the problem continues please contact the DCA Group").showCritical()
			CLIMessage("Error reading today's metadata file","E")
			#Common.show_message(QtWidgets.QMessageBox.Critical,"Metadata gathering error","XAFS/XRF scan tool",QtWidgets.QMessageBox.Ok)
			#sys.exit()

		#FNULL.close()
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