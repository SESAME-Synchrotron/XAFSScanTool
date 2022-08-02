#! /usr/bin/python3

import json
import re
import sys
from PyQt5 import QtCore, QtGui, QtWidgets


def regexvalidation(entery,value):
	try:
		with open('regex.json', "r") as regexfile:
			regExps = json.load(regexfile)
			regexfile.close()
			return True if re.match(regExps[entery],value) else False
	except Exception as e:
		print("regex.json load error")
		print(e)
		sys.exit()

def is_number(s):
	try:
		data = float(s)
		return True
	except:
		return False
	
def validate(entery,value, message):
	if regexvalidation(entery, value):
		return True
	else:
		show_message(QtWidgets.QMessageBox.Critical, message,"XAFS/XRF scan tool", QtWidgets.QMessageBox.Ok)
		return False


def show_message(Icon,Text,WindowTitle,StandardButtons):
	msg = QtWidgets.QMessageBox()
	msg.setIcon(Icon)
	msg.setText(Text)
	msg.setWindowTitle(WindowTitle)
	msg.setStandardButtons(StandardButtons)
	msg.exec_()
	return msg