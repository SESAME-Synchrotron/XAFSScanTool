#!/usr/bin/python3.9
import sys
import argparse
import energyCalibration
import config
from common import Common

try:
	import numpy as np
	import epics
	from PyQt5 import QtWidgets
except ImportError as error:
	print("Please ensure that the following packages are installed properly:\n ")
	print("pyepics\nnumpy\nPyQt5\n")
	sys.exit()

# import xafs
from engScan import ENGSCAN
from mapScan import MAPSCAN
app = QtWidgets.QApplication(sys.argv)

#########################################################
parser = argparse.ArgumentParser(description="XAFS/XRF Scanning Tool "\
 "is a software developed by DCA at SESAME to collect exprimintal data from XAFS / XRF Beamline at SESAME ")
parser.add_argument('--testingMode', type=str,default = "No" ,help="Yes/No, default is No")
parser.add_argument('--engCalib', type=str, default=None, help="Calibration data path (single xdi file)")
#########################################################
args = parser.parse_args()
tMode = args.testingMode
engCalib = args.engCalib 


if __name__ == "__main__":

	paths	= Common.loadjson("configrations/paths.json")
	cfg		= config.ConfigGUI(paths).cfg

	print(cfg)
	
	if engCalib != None:
		x = energyCalibration.energyCalibration(engCalib)
	elif cfg['scanType'] == 'stepEngScan':
		ENGSCAN(paths = paths, cfg = cfg, testingMode = tMode)
	elif cfg['scanType'] == 'stepMapScan':
		MAPSCAN(paths = paths, cfg = cfg, testingMode = tMode)
	
	sys.exit(app.exit())

	# if engCalib != None:
	# 	x = energyCalibration.energyCalibration(engCalib)
	# else:
	# 	xafs.XAFSSCAN(testingMode = tMode)
	# sys.exit(app.exit())
