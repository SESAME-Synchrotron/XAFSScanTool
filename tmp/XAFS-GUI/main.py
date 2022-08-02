#!/usr/bin/python3

import sys

try:
	import numpy as np
	import epics
	from PyQt5 import QtWidgets
except ImportError as error:
	print("Please ensure that the following packages are installed properly:\n ")
	print("pyepics\nnumpy\nPyQt5\n")
	sys.exit()

import xafs

app = QtWidgets.QApplication(sys.argv)

if __name__ == "__main__":
    xafsobj = xafs.XAFSSCAN()
    sys.exit(app.exit())
