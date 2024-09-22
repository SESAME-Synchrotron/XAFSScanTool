import sys
from tendo import singleton
from epics import PV
from pandabox import PandA
from SEDSS.SEDFileManager import readFile

try:
	me = singleton.SingleInstance()
except:
	sys.exit()

if __name__ == "__main__":
	IPs = readFile("/home/control/XAFSScanTool/configurations/IPs.json").readJSON()
	pandaBox = PandA(IPs["PandA"])
	pandaBox.encoderSetp(int(PV("D08R1-MO-MC2:OH-DCM-STP-ROTX1.RRBV").get()))