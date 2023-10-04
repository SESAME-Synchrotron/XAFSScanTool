""" 
Start date: Jan 24, 2021
The " SED Writer" is used with many simple data writers at SESAME. 
it is used to create simple csv files and validate a given path and file name.

Copyright©
SESAME | DCA 
by Mustafa Alzubi, mostafa.zoubi@sesame.org.jo

==============
camelCase: 
camelCase is being used here with some deviations: 
==============
"""

import sys
import csv
from os import path, makedirs
from colorama import init, Fore, Back, Style
from SEDSS.UIMessage import UIMessage

init() # this is to this is to initiate colorama 

try: 
	import PyQt5 
except ImportError as error:
	print ("Please make sure that the following packages are installed:\n")
	print (Back.RED + "(1) PyQt5", Style.RESET_ALL, "\n")
	sys.exit()

class SEDWriter:

	def __init__(self, fName, fPath): # class constructor 
		self.fName = fName
		self.fPath = fPath
		self.pathValCrt()

		if self.fPath.endswith("/"):
			self.fPath=self.fPath[:-1]

	def getFName(self):
		return self.fName

	def getFPath(self):
		return self.fPath

	def pathValCrt(self): # Validate / create file location (path)
		_pathExist = self.pathExist()
		if not (_pathExist): 
			"""CLI Message | path not exist"""
			print("The path: " + Back.GREEN + self.fPath, Style.RESET_ALL, "is not exist")
			
			"""GUI Message  | path not exist"""
			msg = UIMessage("SED Writer","The path ({}) "\
				"is not exist.".format(self.fPath), "Would you like to "\
				"create it?")
			_reply = msg.showYNQuestion()
			if _reply:
				makedirs(self.fPath)
				msg = UIMessage("SED Writer", "SED Writer", "The path "\
					"has been successfully created")
				msg.showInformation(self.fPath)
			else: 
				sys.exit()
		else: 
			_fileExist = self.fileExist()
			if (_fileExist):
				"""CLI Message | file's path"""
				print("The path: " + Back.RED + self.fPath, Style.RESET_ALL, 
					"belongs to an alredy existed file "\
					"--it is file's path--. Please make "\
					"sure that you are providing the right path")
				
				"""GUI Message | file's path"""
				msg = UIMessage("SED Writer", "Wrong file name", "The path ({})"\
					" belongs to an already existed "\
					"file. Please make sure that you are "\
					"providing the right path".format(self.fPath))
				msg.showCritical()
				sys.exit()

	def pathExist(self): # check folder or file paths if exist?? 
		destFolderObj = path.exists(self.fPath)
		if not (destFolderObj):
			return False
		else: 
			return True

	def fileExist(self): 
		destFileObj = path.isfile(self.fPath)
		if not (destFileObj):
			return False
		else: 
			return True

class CSVWriter(SEDWriter): 

	def __init__ (self, fName, fPath, columns, data, fMode = "a", wMode = "D"): # class constructer 
		super().__init__(fName, fPath)

		self.fMode = fMode
		self.columns = columns
		self.data = data
		self.wMode = wMode

		print(wMode)

		#self.checkPath()

	def create(self):
		if self.wMode == "D":
			self.DCSVCreate()
		elif self.wMode == "R":
			print("Row by row")
			self.RCSVCreate()
		else: 
			print (Back.RED + "{}".format(self.wMode), Style.RESET_ALL,  \
				"is unknown writing technique")

			msg = UIMessage("CSV Writer", "Wrong writing technique", "the parameter ({})"\
					" is unknown. Please make sure that you are "\
					"providing the right parameter in the class CSVWriter".format(self.wMode))
			msg.showCritical()
			sys.exit()

	def DCSVCreate (self): # Dictionary based writing i.e. {'SN':1, 'Name':'Mustafa'}
		#print(self.fName, self.columns, self.data, self.fMode)
		try: 
			with open(self.fPath+'/'+self.fName+'.csv', self.fMode) as csvFile: 
				_writer = csv.DictWriter(csvFile, fieldnames=self.columns)
				_writer.writeheader()
				for rows in self.data: 
					_writer.writerow(rows)
			csvFile.close()
		except IOError:
			print ("DCSVWriter: I/O error")

	def RCSVCreate(self): # Row by row writing 
		try: 
			with open(self.fPath+'/'+self.fName+'.csv', self.fMode) as csvFile:
				#_writer = csv.writer(csvFile, lineterminator="\n", quoting=csv.QUOTE_NONNUMERIC)
				_writer = csv.writer(csvFile, quoting=csv.QUOTE_NONNUMERIC)
				_writer.writerow(self.columns)
				_writer.writerows(self.data)
				#for row in self.data: 
				#	_writer.writerow(row)
			csvFile.close()
		except IOError:
			print ("RCSVWriter: I/O error")
