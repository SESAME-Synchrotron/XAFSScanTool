#! /usr/bin/python3

import json
import re
import sys
from PyQt5 import QtCore, QtGui, QtWidgets

class Common:
	@staticmethod
	def regexvalidation(entery,value):
		regExps = Common.loadjson("configrations/regex.json")
		return True if re.match(regExps[entery],value) else False

	@staticmethod
	def is_number(s):
		try:
			data = float(s)
			return True
		except:
			return False
	@staticmethod
	def validate(entery,value, message):
		if Common.regexvalidation(entery, value):
			return True
		else:
			show_message(QtWidgets.QMessageBox.Critical, message,"XAFS/XRF scan tool", QtWidgets.QMessageBox.Ok)
			return False
	@staticmethod
	def show_message(Icon,Text,WindowTitle,StandardButtons):
		msg = QtWidgets.QMessageBox()
		msg.setIcon(Icon)
		msg.setText(Text)
		msg.setWindowTitle(WindowTitle)
		msg.setStandardButtons(StandardButtons)
		msg.exec_()
		return msg

	@staticmethod
	def loadjson(path):
		try:
			with open(path, "r") as jsonfile:
				jsondata = json.load(jsonfile)
				jsonfile.close()
				return jsondata
		except Exception as e:
			print("{} load error".format(path))
			print(e)	